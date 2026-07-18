"""Public Pro-tier waitlist endpoint (no authentication).

One of only two unauthenticated surfaces in Phase 1 — the other is /health.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.waitlist import WaitlistEntry
from schemas.waitlist import WaitlistCreate, WaitlistResponse

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("", response_model=WaitlistResponse)
async def join_waitlist(
    payload: WaitlistCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> WaitlistResponse:
    """Register interest in the Pro tier.

    Idempotent: signing up twice with the same email returns the original entry
    with 200 rather than erroring, so the UI never has to special-case it.
    """
    existing = await db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == payload.email)
    )
    entry = existing.scalar_one_or_none()

    if entry is None:
        entry = WaitlistEntry(email=payload.email, source=payload.source)
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    return WaitlistResponse.model_validate(entry)
