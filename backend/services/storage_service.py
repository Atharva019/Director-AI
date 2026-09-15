"""Object storage via the S3 API (boto3).

Free-tier hosts give us an ephemeral disk — anything written locally is gone on
the next redeploy — so uploaded images live in object storage and we persist
only the URL.

Provider-agnostic on purpose: Cloudflare R2, Supabase Storage, Backblaze B2,
MinIO and AWS S3 all speak this API, so switching providers is a change of
S3_ENDPOINT_URL / S3_REGION and nothing else. That matters because R2 requires
a card on file, which is a hard blocker in some countries.
"""

import logging
import uuid
from functools import lru_cache

import boto3
from botocore.config import Config

from config import get_settings

logger = logging.getLogger(__name__)


def build_object_key(ext: str) -> str:
    """Non-guessable object key under the analyses/ prefix.

    The bucket is public-read, so the key is the only thing standing between an
    object and the world — it must not be enumerable.
    """
    return f"analyses/{uuid.uuid4().hex}{ext}"


class StorageService:
    """Uploads image bytes to an S3-compatible bucket and returns a public URL."""

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.S3_BUCKET
        self._public_base_url = settings.S3_PUBLIC_BASE_URL.rstrip("/")
        # Empty endpoint means "no provider configured". Passing None here would
        # silently target real AWS S3, so keep it falsy and let the startup
        # guard in main.py refuse to boot instead.
        self._endpoint = settings.S3_ENDPOINT_URL or None
        self._access_key = settings.S3_ACCESS_KEY_ID
        self._secret_key = settings.S3_SECRET_ACCESS_KEY
        self._region = settings.S3_REGION or "auto"
        self._client = None  # lazy — never built during tests

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
                region_name=self._region,
            )
        return self._client

    def upload_bytes(self, data: bytes, ext: str, content_type: str) -> str:
        key = build_object_key(ext)
        try:
            self._get_client().put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )
        except Exception as exc:
            err_msg = str(exc)
            if hasattr(exc, "response") and isinstance(exc.response, dict):
                err_code = exc.response.get("Error", {}).get("Code", "")
                err_detail = exc.response.get("Error", {}).get("Message", "")
                status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", "")
                parts = [p for p in [f"HTTP {status_code}" if status_code else "", err_code, err_detail or str(exc)] if p]
                err_msg = " | ".join(parts)
            logger.error("Failed to upload object %s to bucket %s: %s", key, self._bucket, err_msg)
            raise RuntimeError(f"Storage upload failed for bucket '{self._bucket}': {err_msg}") from exc
        logger.info("Uploaded object to storage: %s", key)
        return f"{self._public_base_url}/{key}"


class LocalStorageService:
    """Dev-only fallback: saves image bytes to the local UPLOAD_DIR.

    Returns a relative ``/uploads/analyses/<filename>`` URL that the FastAPI
    dev server serves via a StaticFiles mount (configured in main.py).  This
    lets thumbnails appear in the history page without any S3 / cloud-storage
    setup.

    **Never use in production** — the ephemeral disk means files are lost on
    every redeploy.
    """

    def __init__(self) -> None:
        from pathlib import Path

        settings = get_settings()
        self._upload_dir = Path(settings.UPLOAD_DIR).resolve()
        self._analyses_dir = self._upload_dir / "analyses"
        self._analyses_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(
            "LocalStorageService active — images are saved to %s. "
            "Configure S3_* env vars for production.",
            self._upload_dir,
        )

    def upload_bytes(self, data: bytes, ext: str, content_type: str) -> str:
        key = f"{uuid.uuid4().hex}{ext}"
        dest = self._analyses_dir / key
        dest.write_bytes(data)
        logger.info("Saved upload locally: %s", dest)
        # Return a path that the /uploads StaticFiles mount will resolve.
        return f"/uploads/analyses/{key}"


@lru_cache()
def get_storage_service():
    """Return the appropriate storage backend.

    Uses S3-compatible object storage when fully configured; falls back to
    local disk in development so thumbnails still render without any cloud
    credentials.
    """
    settings = get_settings()
    if settings.storage_enabled:
        return StorageService()
    logger.info(
        "S3 storage not configured (storage_enabled=False). "
        "Using LocalStorageService for dev."
    )
    return LocalStorageService()
