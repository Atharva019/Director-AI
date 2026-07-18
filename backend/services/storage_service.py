"""Cloudflare R2 object storage (S3-compatible) via boto3.

Free-tier hosts give us an ephemeral disk — anything written locally is gone on
the next redeploy — so uploaded images live in R2 and we persist only the URL.
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
    """Uploads image bytes to Cloudflare R2 and returns a public URL."""

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.R2_BUCKET
        self._public_base_url = settings.R2_PUBLIC_BASE_URL.rstrip("/")
        self._endpoint = (
            f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            if settings.R2_ACCOUNT_ID
            else None
        )
        self._access_key = settings.R2_ACCESS_KEY_ID
        self._secret_key = settings.R2_SECRET_ACCESS_KEY
        self._client = None  # lazy — never built during tests

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
        return self._client

    def upload_bytes(self, data: bytes, ext: str, content_type: str) -> str:
        key = build_object_key(ext)
        self._get_client().put_object(
            Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
        )
        logger.info("Uploaded object to R2: %s", key)
        return f"{self._public_base_url}/{key}"


@lru_cache()
def get_storage_service() -> StorageService:
    return StorageService()
