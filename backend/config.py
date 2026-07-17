"""
Application configuration loaded from environment variables via Pydantic Settings.
"""

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

    # ── Cloudflare R2 (S3-compatible object storage) ──────────────────────
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_BASE_URL: str = ""  # e.g. https://pub-xxxx.r2.dev or a custom domain

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
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        """Convert MB limit to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def r2_enabled(self) -> bool:
        return bool(self.R2_ACCOUNT_ID and self.R2_ACCESS_KEY_ID and self.R2_BUCKET)


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
