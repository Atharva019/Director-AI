"""
Async client for the Google Gemini REST API.

Provides the same interface as GroqService so that the AIProvider
can swap between them transparently.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Thin async wrapper around the Gemini HTTP API."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 1.5  # seconds
    GENERATE_TIMEOUT = 60.0  # Gemini can be slower than Groq

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key: str = settings.GEMINI_API_KEY
        self.default_model: str = settings.GEMINI_DEFAULT_MODEL

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _request(
        self,
        model: str,
        json_body: Dict[str, Any],
        timeout: float = GENERATE_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Send an HTTP request to Gemini with retries and exponential backoff.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent"
        )
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url, params=params, headers=headers, json=json_body
                    )
                    response.raise_for_status()
                    return response.json()
            except (
                httpx.HTTPStatusError,
                httpx.RequestError,
                httpx.TimeoutException,
            ) as exc:
                err_detail = str(exc)
                if isinstance(exc, httpx.HTTPStatusError):
                    err_detail += f" | Response: {exc.response.text}"
                last_exc = Exception(err_detail)

                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "Gemini request attempt %d/%d failed: %s – retrying in %.1fs",
                        attempt, self.MAX_RETRIES, exc, wait,
                    )
                    await asyncio.sleep(wait)

        logger.error("Gemini request failed after %d retries.", self.MAX_RETRIES)
        raise RuntimeError(
            f"Gemini request failed after {self.MAX_RETRIES} retries: {last_exc}"
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
        Send an image (base64-encoded) to Gemini for analysis.

        Returns a dict matching the GroqService interface:
            {"response": "<text>", "model": "<model>"}
        """
        model_to_use = model or self.default_model

        body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            },
        }

        raw_response = await self._request(model_to_use, body)

        try:
            text_content = raw_response["candidates"][0]["content"]["parts"][0]["text"]
            actual_model = raw_response.get("modelVersion", model_to_use)
        except (KeyError, IndexError) as e:
            logger.error("Unexpected Gemini API response structure: %s", raw_response)
            raise ValueError(f"Failed to parse Gemini response: {e}")

        return {
            "response": text_content,
            "model": actual_model,
        }
