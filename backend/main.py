"""
Director AI – FastAPI application entry-point.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    waitlist_router,
)


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG if get_settings().APP_DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

settings = get_settings()


# ── Startup configuration guards ─────────────────────────────────────────────
#
# A production misconfiguration must crash the boot, not serve broken data.
# Each of these previously had a silent-failure mode.


def should_create_all(cfg) -> bool:
    """create_all is for local dev and the SQLite test suite only.

    In production Alembic owns the schema — running create_all there would
    silently paper over a model that has no migration, so prod and the
    migration history could drift apart without anyone noticing.
    """
    return not cfg.is_production


def verify_storage_config(cfg) -> None:
    """Refuse to start in production without a complete R2 configuration.

    Without this the uploader falls back to an empty public base URL and
    persists relative paths like `/analyses/abc.png` into scene_analyses —
    unrecoverable once written, because the object key is all we keep.
    """
    if cfg.is_production and not cfg.r2_enabled:
        raise RuntimeError(
            "R2 storage is not fully configured (need R2_ACCOUNT_ID, "
            "R2_ACCESS_KEY_ID, R2_BUCKET, R2_PUBLIC_BASE_URL). Refusing to "
            "start: uploads would be persisted as unusable relative paths."
        )


def verify_cors_config(cfg) -> None:
    """Refuse to start in production without explicit, non-wildcard origins.

    The app sends credentials, so a wildcard origin would hand any site the
    user's session.
    """
    if not cfg.is_production:
        return
    origins = cfg.cors_origin_list
    if not origins:
        raise RuntimeError(
            "CORS_ORIGINS is empty in production. Set it to your exact "
            "frontend origin (e.g. https://your-app.vercel.app)."
        )
    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS contains '*' while credentials are enabled. Set it "
            "to exact origins instead."
        )


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""

    # ── Startup ───────────────────────────────────────────────────────────
    logger.info("Starting Director AI API [env=%s]", settings.APP_ENV)

    # 0. Fail fast on a production misconfiguration, before serving anything.
    verify_storage_config(settings)
    verify_cors_config(settings)

    # 1. Create database tables (dev/test only — Alembic owns prod).
    if should_create_all(settings):
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured (create_all, non-production).")
    else:
        logger.info("Production: schema managed by Alembic, skipping create_all.")

    # 2. Initialize Firebase Admin SDK
    initialize_firebase()

    # 3. Verify AI provider configuration
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
    allow_origin_regex=r"https?://.*" if not settings.is_production else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded images are served straight from Cloudflare R2, not from this app —
# free-tier hosts have an ephemeral disk, so there is nothing local to mount.

# ── Routers (all under /api/v1) ──────────────────────────────────────────────

API_V1 = "/api/v1"

app.include_router(auth_router, prefix=API_V1)
app.include_router(projects_router, prefix=API_V1)
app.include_router(scenes_router, prefix=API_V1)
app.include_router(shots_router, prefix=API_V1)
app.include_router(analysis_router, prefix=API_V1)
app.include_router(waitlist_router, prefix=API_V1)


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

