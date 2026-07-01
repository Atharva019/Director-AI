"""
Director AI – FastAPI application entry-point.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from db.database import Base, async_engine

# Import all models so they are registered on Base.metadata
import models  # noqa: F401

from auth.firebase import initialize_firebase
from routers import (
    auth_router,
    projects_router,
    scenes_router,
    shots_router,
    analysis_router,
)


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG if get_settings().APP_DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

settings = get_settings()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""

    # ── Startup ───────────────────────────────────────────────────────────
    logger.info("Starting Director AI API [env=%s]", settings.APP_ENV)

    # 1. Create database tables (dev convenience – use Alembic in production)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")

    # 2. Initialize Firebase Admin SDK
    initialize_firebase()

    # 3. Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory ready: %s", upload_dir.resolve())

    # 4. Verify AI provider configuration
    providers = []
    nim_api_key = settings.NVIDIA_NIM_API_KEY or settings.GROQ_API_KEY
    if nim_api_key:
        model = settings.NVIDIA_NIM_DEFAULT_MODEL or settings.GROQ_DEFAULT_MODEL
        providers.append(f"NVIDIA NIM (model={model})")
    else:
        logger.info("NVIDIA NIM API key not set — primary provider disabled.")

    if settings.GEMINI_ENABLED and settings.GEMINI_API_KEY:
        providers.append(f"Gemini (model={settings.GEMINI_DEFAULT_MODEL})")
    elif settings.GEMINI_API_KEY:
        logger.info("GEMINI_ENABLED=false — Gemini fallback disabled.")
    else:
        logger.info("GEMINI_API_KEY not set — Gemini fallback disabled.")

    if providers:
        logger.info("AI provider chain: %s", " → ".join(providers))
    else:
        logger.warning(
            "No AI provider configured! Set NVIDIA_NIM_API_KEY and/or enable GEMINI_ENABLED. "
            "Image analysis will fail."
        )

    yield  # ← application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────
    await async_engine.dispose()
    logger.info("Database connections closed. Goodbye.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Director AI API",
    description="AI-powered filmmaking assistant – cinematography analysis, project management, and shot planning.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://.*" if settings.APP_ENV == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Routers (all under /api/v1) ──────────────────────────────────────────────

API_V1 = "/api/v1"

app.include_router(auth_router, prefix=API_V1)
app.include_router(projects_router, prefix=API_V1)
app.include_router(scenes_router, prefix=API_V1)
app.include_router(shots_router, prefix=API_V1)
app.include_router(analysis_router, prefix=API_V1)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Basic liveness probe."""
    return {
        "status": "healthy",
        "service": "Director AI API",
        "version": "0.1.0",
    }


# ── Exception handlers ───────────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Turn ValueError into a 422 response."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    """Turn PermissionError into a 403 response."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    """Turn FileNotFoundError into a 404 response."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    """Turn RuntimeError into a 500 response."""
    logger.error("Unhandled RuntimeError: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for any unhandled Exception."""
    logger.error("Unhandled Exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again later."},
    )

