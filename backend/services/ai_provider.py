"""
Multi-provider AI chain with automatic fallback and rate limiting.

Provider priority:  NVIDIA NIM (primary) → Gemini (optional fallback).
If the primary is rate-limited or errors out, the next provider is tried
transparently — the caller never knows the difference.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from config import get_settings
from services.nim_service import NimService
from services.gemini_service import GeminiService
from services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Type alias for a (name, client) pair
_ProviderEntry = Tuple[str, Any]


class AIProvider:
    """
    Unified AI interface that chains multiple providers with rate limiting.

    Usage::

        provider = AIProvider()
        result = await provider.analyze_image(base64_img, prompt)
        # result["provider"] tells you which backend was used
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._providers: List[_ProviderEntry] = []

        # Build provider chain in priority order
        nim_api_key = settings.NVIDIA_NIM_API_KEY or settings.GROQ_API_KEY
        if nim_api_key:
            self._providers.append(("nim", NimService()))
            model = settings.NVIDIA_NIM_DEFAULT_MODEL or settings.GROQ_DEFAULT_MODEL
            logger.info("AI provider chain: NVIDIA NIM registered (primary, model=%s)", model)

        if settings.GEMINI_ENABLED and settings.GEMINI_API_KEY:
            self._providers.append(("gemini", GeminiService()))
            logger.info("AI provider chain: Gemini registered (fallback)")
        elif settings.GEMINI_API_KEY and not settings.GEMINI_ENABLED:
            logger.info("GEMINI_API_KEY is set but GEMINI_ENABLED=false — Gemini skipped.")

        if not self._providers:
            raise ValueError(
                "No AI provider configured. "
                "Set NVIDIA_NIM_API_KEY (or GROQ_API_KEY) and/or enable GEMINI_ENABLED."
            )

        self._rate_limiter = RateLimiter()

    # ── Public API ────────────────────────────────────────────────────────

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze an image using the first available provider.

        Falls back through the chain on rate limits or errors.
        The returned dict always includes a ``"provider"`` key indicating
        which backend served the request.
        """
        last_error: Optional[Exception] = None

        for provider_name, client in self._providers:
            # ── Rate limit check ──────────────────────────────────────
            if not await self._rate_limiter.can_proceed(provider_name):
                logger.info(
                    "Provider '%s' is rate-limited, trying next…",
                    provider_name,
                )
                continue

            # ── Attempt the request ───────────────────────────────────
            try:
                await self._rate_limiter.record_request(provider_name)

                # Don't pass NIM-specific model names to Gemini
                provider_model = model
                if provider_name == "gemini" and model and "/" in model:
                    provider_model = None  # use Gemini's own default

                result = await client.analyze_image(
                    image_base64=image_base64,
                    prompt=prompt,
                    model=provider_model,
                )

                # Tag which provider fulfilled the request
                result["provider"] = provider_name
                logger.info(
                    "Analysis completed via %s (model=%s)",
                    provider_name,
                    result.get("model"),
                )
                return result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Provider '%s' failed: %s — trying next…",
                    provider_name,
                    exc,
                )
                continue

        # All providers exhausted
        raise RuntimeError(
            f"All AI providers failed. Last error: {last_error}"
        )

    async def close(self) -> None:
        """Release resources held by the rate limiter."""
        await self._rate_limiter.close()
