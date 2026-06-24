"""
Async client for the Groq REST API (OpenAI compatible).

Completely model-agnostic – the caller decides which model to use,
falling back to GROQ_DEFAULT_MODEL from config.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class GroqService:
    """Thin async wrapper around the Groq HTTP API."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 1.5  # seconds
    GENERATE_TIMEOUT = 30.0  # seconds (Groq is very fast, so 30s is plenty)

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key: str = settings.GROQ_API_KEY
        self.default_model: str = settings.GROQ_DEFAULT_MODEL

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _request(
        self,
        json_body: Dict[str, Any],
        timeout: float = GENERATE_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Send an HTTP request to Groq with retries and exponential backoff.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment.")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, json=json_body)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "Groq request attempt %d/%d failed: %s – retrying in %.1fs",
                        attempt, self.MAX_RETRIES, exc, wait,
                    )
                    await asyncio.sleep(wait)

        logger.error("Groq request failed after %d retries.", self.MAX_RETRIES)
        raise RuntimeError(
            f"Groq request failed after {self.MAX_RETRIES} retries: {last_exc}"
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
        Send an image (base64-encoded) to Groq for analysis.

        Parameters
        ----------
        image_base64 : str
            Base64-encoded image bytes (no data-URI prefix).
        prompt : str
            Instruction prompt describing what to analyze.
        model : str, optional
            A vision-capable Groq model. Falls back to default.

        Returns
        -------
        dict
            A dict mimicking the ollama interface: {"response": "<text>", "model": "<model>"}
        """
        model_to_use = model or self.default_model
        
        # Format the body exactly as expected by OpenAI / Groq Vision APIs
        body = {
            "model": model_to_use,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.4
        }

        raw_response = await self._request(body)

        try:
            text_content = raw_response["choices"][0]["message"]["content"]
            actual_model_used = raw_response.get("model", model_to_use)
        except (KeyError, IndexError) as e:
            logger.error("Unexpected Groq API response structure: %s", raw_response)
            raise ValueError(f"Failed to parse Groq response: {e}")

        return {
            "response": text_content,
            "model": actual_model_used
        }
