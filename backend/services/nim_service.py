"""
Async client for the NVIDIA NIM REST API (OpenAI compatible).

Used for vision-language scene analysis via integrate.api.nvidia.com.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


def _normalize_api_key(raw_key: str) -> str:
    """Strip accidental 'Bearer ' prefix from env values."""
    key = raw_key.strip()
    if key.lower().startswith("bearer "):
        return key[7:].strip()
    return key


class NimService:
    """Thin async wrapper around the NVIDIA NIM HTTP API."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 1.5  # seconds
    GENERATE_TIMEOUT = 60.0  # seconds (VLMs can be slower than text-only models)

    def __init__(self) -> None:
        settings = get_settings()
        raw_key = settings.NVIDIA_NIM_API_KEY or settings.GROQ_API_KEY
        self.api_key: str = _normalize_api_key(raw_key)
        self.default_model: str = (
            settings.NVIDIA_NIM_DEFAULT_MODEL or settings.GROQ_DEFAULT_MODEL
        )
        self.api_url: str = settings.NVIDIA_NIM_API_URL

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _request(
        self,
        json_body: Dict[str, Any],
        timeout: float = GENERATE_TIMEOUT,
    ) -> Dict[str, Any]:
        """Send an HTTP request to NVIDIA NIM with retries and exponential backoff."""
        if not self.api_key:
            raise ValueError(
                "NVIDIA NIM API key is not set. "
                "Set NVIDIA_NIM_API_KEY (or GROQ_API_KEY) in the environment."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        self.api_url, headers=headers, json=json_body
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                err_detail = f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"
                last_exc = Exception(err_detail)
                logger.warning(
                    "NIM attempt %d/%d — HTTP %d: %s",
                    attempt,
                    self.MAX_RETRIES,
                    exc.response.status_code,
                    exc.response.text[:200],
                )
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    await asyncio.sleep(wait)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "NIM attempt %d/%d — %s: %s",
                    attempt,
                    self.MAX_RETRIES,
                    type(exc).__name__,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    await asyncio.sleep(wait)

        logger.error(
            "NVIDIA NIM request failed after %d retries. Last error: %s",
            self.MAX_RETRIES,
            last_exc,
        )
        raise RuntimeError(
            f"NVIDIA NIM request failed after {self.MAX_RETRIES} retries: {last_exc}"
        )

    # ── Public API ────────────────────────────────────────────────────────

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an image (base64-encoded) to a vision-capable NIM model.

        Returns a dict: {"response": "<text>", "model": "<model>"}
        """
        model_to_use = model or self.default_model

        body = {
            "model": model_to_use,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.4,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},
        }

        raw_response = await self._request(body)

        try:
            text_content = raw_response["choices"][0]["message"]["content"]
            actual_model_used = raw_response.get("model", model_to_use)
        except (KeyError, IndexError) as e:
            logger.error("Unexpected NVIDIA NIM response structure: %s", raw_response)
            raise ValueError(f"Failed to parse NVIDIA NIM response: {e}")

        return {
            "response": text_content,
            "model": actual_model_used,
        }
