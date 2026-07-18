"""Per-IP sliding-window limiter for public, unauthenticated endpoints.

Distinct from services/rate_limiter.py, which throttles our OUTBOUND calls to AI
providers. This one throttles INBOUND abuse of the endpoints that need no login.

ponytail: in-process dict, so the window is per-instance. Correct on Render's
free tier (a single instance). If the API is ever scaled past one instance,
move this to Redis or Cloudflare — the limit becomes N x looser per added
instance, it does not break.
"""

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

# Signups per IP per hour. Generous for a human, useless for a script.
WAITLIST_PER_HOUR = 5

_WINDOWS: Dict[str, int] = {"waitlist": 3600}

_hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _limit_for(bucket: str) -> int:
    return {"waitlist": WAITLIST_PER_HOUR}.get(bucket, WAITLIST_PER_HOUR)


def allow(client_ip: str, bucket: str) -> bool:
    """Record a hit and report whether it is within the limit."""
    window = _WINDOWS.get(bucket, 3600)
    limit = _limit_for(bucket)
    now = time.time()
    cutoff = now - window
    key = (client_ip, bucket)

    with _lock:
        hits = _hits[key]
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


def reset() -> None:
    """Clear all state. For tests."""
    with _lock:
        _hits.clear()
