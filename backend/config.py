"""
Application configuration loaded from environment variables via Pydantic Settings.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the Director AI backend.
    All values are loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://director:director_secret@localhost:5432/director_ai"

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── NVIDIA NIM (LLM – primary) ────────────────────────────────────
    NVIDIA_NIM_API_KEY: str = ""
    NVIDIA_NIM_DEFAULT_MODEL: str = "meta/llama-3.2-11b-vision-instruct"
    NVIDIA_NIM_API_URL: str = "https://integrate.api.nvidia.com/v1/chat/completions"

    # Legacy env names kept for backward compatibility during migration
    GROQ_API_KEY: str = ""
    GROQ_DEFAULT_MODEL: str = "meta/llama-3.2-11b-vision-instruct"

    # ── Gemini (LLM – fallback, disabled by default while testing NIM) ─
    GEMINI_ENABLED: bool = False
    GEMINI_API_KEY: str = ""
    GEMINI_DEFAULT_MODEL: str = "gemini-2.0-flash"

    # ── Firebase Auth ─────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"
    # JSON string of the service account (preferred in production). If set,
    # takes precedence over FIREBASE_CREDENTIALS_PATH.
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""

    # ── Object storage (any S3-compatible provider) ───────────────────────
    # Works with Cloudflare R2, Supabase Storage, Backblaze B2, MinIO, AWS S3 —
    # only the endpoint and region differ. See docs/deploy.md for per-provider
    # values.
    S3_ENDPOINT_URL: str = ""    # e.g. https://<account>.r2.cloudflarestorage.com
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""
    S3_PUBLIC_BASE_URL: str = ""  # public base for reads, e.g. https://pub-x.r2.dev
    S3_REGION: str = "auto"       # R2 uses "auto"; B2/Supabase want a real region

    # ── Plan limits ───────────────────────────────────────────────────────
    plan_free_analyses: int = 5
    plan_free_projects: int = 2

    # ── File uploads ──────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── App ───────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins, dropping blanks.

        An unset CORS_ORIGINS would otherwise yield [""] — a junk entry that
        matches nothing and makes a misconfiguration look like a CORS bug.
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        """Convert MB limit to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def database_configured(self) -> bool:
        """False while DATABASE_URL is still pointing at a local dev database."""
        url = self.DATABASE_URL
        return not ("localhost" in url or "127.0.0.1" in url)

    @property
    def storage_enabled(self) -> bool:
        """Storage is only usable if we can also build a public URL for the object.

        S3_PUBLIC_BASE_URL is part of the requirement: without it, uploads
        return a relative path that gets persisted to the database forever.
        """
        return bool(
            self.S3_ENDPOINT_URL
            and self.S3_ACCESS_KEY_ID
            and self.S3_BUCKET
            and self.S3_PUBLIC_BASE_URL
        )


def _env_presence_report() -> str:
    """Which expected variables the process can actually see, names only.

    Never reports values — most of these are secrets. The point is to separate
    "the platform passed nothing" from "the value is present but wrong", which
    the error message alone cannot distinguish.
    """
    expected = [
        "DATABASE_URL",
        "APP_ENV",
        "CORS_ORIGINS",
        "S3_ENDPOINT_URL",
        "S3_BUCKET",
        "NVIDIA_NIM_API_KEY",
        "FIREBASE_SERVICE_ACCOUNT_JSON",
    ]
    present = [n for n in expected if os.environ.get(n, "").strip()]
    missing = [n for n in expected if n not in present]
    return (
        f"Environment seen by this process — set: {', '.join(present) or '(none)'}; "
        f"empty or absent: {', '.join(missing) or '(none)'}."
    )


def verify_database_config(cfg: Settings) -> None:
    """Refuse to run against the local dev database default in production.

    Lives here rather than in main.py because Alembic hits the database first
    (the container runs `alembic upgrade head` before uvicorn), so the check
    has to be reachable from migrations/env.py too. Without it, an unset
    DATABASE_URL silently falls back to localhost and surfaces as a raw
    psycopg2 "connection refused" traceback, which reads like a broken image
    rather than a missing environment variable.
    """
    if not (cfg.is_production and not cfg.database_configured):
        return

    if not os.environ.get("DATABASE_URL", "").strip():
        detail = (
            "DATABASE_URL is not present in this container's environment at "
            "all. On Render it is declared `sync: false`, which means the "
            "Blueprint deliberately does not supply it — set it under "
            "Environment on the service itself, then redeploy."
        )
    else:
        detail = (
            "DATABASE_URL is present but still resolves to a local address, so "
            "it is likely a placeholder or a copy of the dev default."
        )

    raise RuntimeError(
        f"{detail} Expected a Neon connection string using the asyncpg driver, "
        "e.g. postgresql+asyncpg://user:pw@ep-xxx.neon.tech/dbname?sslmode=require\n"
        f"{_env_presence_report()}"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
