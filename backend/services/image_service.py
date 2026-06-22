"""
Image upload handling – validates type & size, resizes if needed, and
saves to the configured upload directory with a UUID filename.
"""

import logging
import uuid
from pathlib import Path
from typing import Set

from fastapi import UploadFile
from PIL import Image

from config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}

MAX_DIMENSION = 1920  # px – longest side


class ImageService:
    """Handles image validation, resizing, and persistent storage."""

    def __init__(self) -> None:
        settings = get_settings()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_bytes = settings.max_upload_bytes
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> str:
        """
        Validate, optionally resize, and persist an uploaded image.

        Parameters
        ----------
        file : UploadFile
            The incoming file from a multipart form.

        Returns
        -------
        str
            The relative path (from project root) to the saved image.

        Raises
        ------
        ValueError
            If the file type is unsupported or the file exceeds the size limit.
        """
        # ── 1. Validate content type ─────────────────────────────────────
        content_type = file.content_type or ""
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Unsupported image type '{content_type}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            )

        # ── 2. Validate extension ────────────────────────────────────────
        original_name = file.filename or "upload"
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # ── 3. Read bytes and validate size ──────────────────────────────
        contents = await file.read()
        if len(contents) > self.max_bytes:
            raise ValueError(
                f"File size ({len(contents) / 1024 / 1024:.1f} MB) exceeds "
                f"the {self.max_bytes / 1024 / 1024:.0f} MB limit."
            )

        # ── 4. Open with Pillow, resize if needed ────────────────────────
        from io import BytesIO

        img = Image.open(BytesIO(contents))
        img = self._ensure_rgb(img)

        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
            logger.info("Resized image to %s", img.size)

        # ── 5. Save with a UUID filename ─────────────────────────────────
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = self.upload_dir / unique_name

        # Save in the original format
        fmt = self._pil_format(ext)
        img.save(str(save_path), format=fmt, quality=90)
        logger.info("Saved uploaded image to %s", save_path)

        return str(save_path)

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _ensure_rgb(img: Image.Image) -> Image.Image:
        """Convert RGBA / palette images to RGB for JPEG compatibility."""
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
            return background
        if img.mode != "RGB":
            return img.convert("RGB")
        return img

    @staticmethod
    def _pil_format(ext: str) -> str:
        """Map file extension to Pillow save format string."""
        return {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP",
        }.get(ext, "JPEG")
