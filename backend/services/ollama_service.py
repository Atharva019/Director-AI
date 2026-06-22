"""
Async client for the Ollama REST API.

Completely model-agnostic – the caller decides which model to use,
falling back to OLLAMA_DEFAULT_MODEL from config.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Thin async wrapper around the Ollama HTTP API."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 1.5  # seconds
    GENERATE_TIMEOUT = 120.0  # seconds
    DEFAULT_TIMEOUT = 30.0  # seconds

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url: str = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model: str = settings.OLLAMA_DEFAULT_MODEL

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Send an HTTP request to Ollama with retries and exponential backoff.

        Returns the parsed JSON response body.
        """
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(
                        method, url, json=json_body
                    )
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "Ollama request %s %s attempt %d/%d failed: %s – retrying in %.1fs",
                        method, path, attempt, self.MAX_RETRIES, exc, wait,
                    )
                    await asyncio.sleep(wait)

        logger.error("Ollama request %s %s failed after %d retries.", method, path, self.MAX_RETRIES)
        raise RuntimeError(
            f"Ollama request failed after {self.MAX_RETRIES} retries: {last_exc}"
        )

    # ── Public API ────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a text completion.

        Parameters
        ----------
        prompt : str
            The user prompt.
        model : str, optional
            Ollama model name. Falls back to the configured default.
        system : str, optional
            Optional system prompt.
        options : dict, optional
            Extra Ollama generation options (temperature, top_p, etc.).

        Returns
        -------
        dict
            Parsed JSON response from Ollama.
        """
        body: Dict[str, Any] = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            body["system"] = system
        if options:
            body["options"] = options

        return await self._request("POST", "/api/generate", json_body=body, timeout=self.GENERATE_TIMEOUT)

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an image (base64-encoded) to a multimodal model for analysis.

        Parameters
        ----------
        image_base64 : str
            Base64-encoded image bytes (no data-URI prefix).
        prompt : str
            Instruction prompt describing what to analyze.
        model : str, optional
            A vision-capable Ollama model. Falls back to default.

        Returns
        -------
        dict
            Parsed JSON response containing the model's analysis.
        """
        body: Dict[str, Any] = {
            "model": model or self.default_model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
        }
        return await self._request("POST", "/api/generate", json_body=body, timeout=self.GENERATE_TIMEOUT)

    async def list_models(self) -> List[Dict[str, Any]]:
        """Return the list of models available on the Ollama server."""
        resp = await self._request("GET", "/api/tags")
        return resp.get("models", [])

    async def health_check(self) -> bool:
        """
        Check whether the Ollama server is reachable.

        Returns True if the server responds, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
