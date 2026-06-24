"""
Async client for the Google Gemini REST API.

Completely model-agnostic – the caller decides which model to use,
falling back to GEMINI_DEFAULT_MODEL from config.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Thin async wrapper around the Gemini HTTP API."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 1.5  # seconds
    GENERATE_TIMEOUT = 120.0  # seconds

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

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=json_body)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
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

        Parameters
        ----------
        image_base64 : str
            Base64-encoded image bytes (no data-URI prefix).
        prompt : str
            Instruction prompt describing what to analyze.
        model : str, optional
            A vision-capable Gemini model. Falls back to default.

        Returns
        -------
        dict
            A dict mimicking the ollama interface: {"response": "<text>", "model": "<model>"}
        """
        # We need to guess the mime type. For safety we can use image/jpeg or image/png.
        # Since it's just base64 data, we'll tell Gemini it's a jpeg. 
        # Gemini is usually robust enough to parse the header signature itself if needed.
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4
            }
        }

        model_to_use = model or self.default_model
        raw_response = await self._request(model_to_use, body)

        try:
            # Extract the text from the Gemini response structure
            text_content = raw_response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error("Unexpected Gemini API response structure: %s", raw_response)
            raise ValueError(f"Failed to parse Gemini response: {e}")

        return {
            "response": text_content,
            "model": model_to_use
        }
