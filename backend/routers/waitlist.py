"""Public Pro-tier waitlist endpoint (no authentication).

One of only two unauthenticated surfaces in Phase 1 — the other is /health.
Being public and write-capable, it carries both an abuse guard and a race
guard.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.waitlist import WaitlistEntry
from schemas.waitlist import WaitlistCreate, WaitlistResponse
from services import ip_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


def _client_ip(request: Request) -> str:
    """Best-effort caller IP.

    Render and Vercel both terminate TLS upstream, so the socket peer is a
    proxy — the real caller is the first entry of X-Forwarded-For. That header
    is client-controllable, so this is a speed bump against casual abuse, not
    an access control.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _fetch(db: AsyncSession, email: str) -> WaitlistEntry | None:
    result = await db.execute(select(WaitlistEntry).where(WaitlistEntry.email == email))
    return result.scalar_one_or_none()


@router.post("", response_model=WaitlistResponse)
async def join_waitlist(
    payload: WaitlistCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> WaitlistResponse:
    """Register interest in the Pro tier.

    Idempotent: signing up twice with the same email returns the original entry
    with 200 rather than erroring, so the UI never has to special-case it.
    """
    if not ip_rate_limiter.allow(_client_ip(request), "waitlist"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signups from this address. Try again later.",
        )

    entry = await _fetch(db, payload.email)
    if entry is not None:
        response.status_code = status.HTTP_200_OK
        return WaitlistResponse.model_validate(entry)

    # The check above is not atomic with the insert. Two concurrent signups for
    # the same address both see None, and one loses on the unique index — treat
    # that as the idempotent case rather than a 500.
    try:
        entry = WaitlistEntry(email=payload.email, source=payload.source)
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
    except IntegrityError:
        await db.rollback()
        entry = await _fetch(db, payload.email)
        if entry is None:  # pragma: no cover — unique violation implies a row
            raise
        response.status_code = status.HTTP_200_OK
        return WaitlistResponse.model_validate(entry)

    response.status_code = status.HTTP_201_CREATED
    return WaitlistResponse.model_validate(entry)
