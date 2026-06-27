"""
Sliding-window rate limiter with optional Redis backend.

Uses Redis sorted sets when available for precise per-minute sliding windows
that work across multiple workers. Falls back to a simple in-memory counter
when Redis is not installed or unreachable — suitable for single-process
deployments (e.g. Vercel, single-dyno Heroku).
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)

# Try to import redis — it's optional
try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.info("redis package not installed — using in-memory rate limiter.")


class RateLimiter:
    """Sliding-window rate limiter (Redis-backed or in-memory fallback)."""

    # Requests-per-minute limits per provider (with a small buffer below
    # the actual provider limits so we never slam the wall).
    DEFAULT_LIMITS: Dict[str, int] = {
        "groq": 28,    # Groq free tier = 30 RPM
        "gemini": 14,  # Gemini free tier = 15 RPM
    }

    def __init__(
        self,
        redis_url: Optional[str] = None,
        limits: Optional[Dict[str, int]] = None,
    ) -> None:
        settings = get_settings()
        self._redis_url = redis_url or settings.REDIS_URL
        self._limits = limits or self.DEFAULT_LIMITS
        self._redis: Optional[object] = None  # aioredis.Redis when available
        self._use_redis = HAS_REDIS and bool(self._redis_url)

        # In-memory fallback: {provider: [timestamp, timestamp, ...]}
        self._memory_store: Dict[str, List[float]] = defaultdict(list)

        if self._use_redis:
            logger.info("Rate limiter using Redis backend.")
        else:
            logger.info("Rate limiter using in-memory backend.")

    # ── Redis helpers ─────────────────────────────────────────────────────

    async def _get_redis(self):
        """Lazy-connect to Redis. Returns None if unavailable."""
        if not self._use_redis:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    self._redis_url, decode_responses=True
                )
                # Quick connectivity check
                await self._redis.ping()
            except Exception as e:
                logger.warning("Redis connect failed, falling back to in-memory: %s", e)
                self._use_redis = False
                self._redis = None
                return None
        return self._redis

    # ── In-memory helpers ─────────────────────────────────────────────────

    def _memory_trim(self, provider: str) -> None:
        """Remove entries older than 60s from the in-memory store."""
        cutoff = time.time() - 60
        self._memory_store[provider] = [
            t for t in self._memory_store[provider] if t > cutoff
        ]

    # ── Public API ────────────────────────────────────────────────────────

    async def can_proceed(self, provider: str) -> bool:
        """Return True if a request to *provider* won't exceed its RPM limit."""
        limit = self._limits.get(provider)
        if limit is None:
            return True  # No limit configured → allow

        # Try Redis path
        r = await self._get_redis()
        if r is not None:
            try:
                key = f"director_ai:ratelimit:{provider}"
                now = time.time()
                await r.zremrangebyscore(key, 0, now - 60)
                count = await r.zcard(key)
                return count < limit
            except Exception as e:
                logger.warning("Redis rate check error (falling back to memory): %s", e)
                self._use_redis = False

        # In-memory fallback
        self._memory_trim(provider)
        return len(self._memory_store[provider]) < limit

    async def record_request(self, provider: str) -> None:
        """Record that a request was made to *provider*."""
        # Try Redis path
        r = await self._get_redis()
        if r is not None:
            try:
                key = f"director_ai:ratelimit:{provider}"
                now = time.time()
                await r.zadd(key, {str(now): now})
                await r.expire(key, 120)
                return
            except Exception as e:
                logger.warning("Redis rate record error: %s", e)

        # In-memory fallback
        self._memory_store[provider].append(time.time())

    async def wait_for_slot(
        self, provider: str, timeout: float = 30.0
    ) -> bool:
        """
        Block until a rate-limit slot opens up for *provider*.
        Returns True if a slot was acquired before *timeout*.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if await self.can_proceed(provider):
                return True
            await asyncio.sleep(1.0)
        return False

    async def close(self) -> None:
        """Shut down the Redis connection gracefully."""
        if self._redis is not None and self._use_redis:
            try:
                await self._redis.close()
            except Exception:
                pass
            self._redis = None
