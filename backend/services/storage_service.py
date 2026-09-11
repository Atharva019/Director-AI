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
                config=Config(signature_version="s3v4"),
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
            logger.error("Failed to upload object %s to bucket %s: %s", key, self._bucket, exc)
            raise RuntimeError(f"Storage upload failed for bucket '{self._bucket}': {exc}") from exc
        logger.info("Uploaded object to storage: %s", key)
        return f"{self._public_base_url}/{key}"


@lru_cache()
def get_storage_service() -> StorageService:
    return StorageService()
