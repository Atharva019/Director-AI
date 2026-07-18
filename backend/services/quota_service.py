"""Free-tier usage limits, enforced against Postgres (no Redis).

Counting rows IS the counter — there is no separate usage tally to drift out of
sync with reality. Enforcement is server-side only; the frontend's usage meter
is a convenience, never the gate.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.analysis import SceneAnalysis
from models.project import Project
from models.user import User

UPGRADE_COPY = "Join the Pro waitlist for unlimited access."


def _month_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def count_analyses_this_month(db: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(SceneAnalysis)
        .where(
            SceneAnalysis.user_id == user_id,
            SceneAnalysis.created_at >= _month_start(),
        )
    )
    return int((await db.execute(stmt)).scalar_one())


async def count_projects(db: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Project).where(Project.user_id == user_id)
    return int((await db.execute(stmt)).scalar_one())


def _quota_error(resource: str, limit: int, used: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "error": "quota_exceeded",
            "resource": resource,
            "limit": limit,
            "used": used,
            "message": (
                f"You've reached the free limit of {limit} {resource}s. {UPGRADE_COPY}"
            ),
        },
    )


async def enforce_analysis_quota(db: AsyncSession, user: User) -> None:
    if user.plan == "pro":
        return
    limit = get_settings().plan_free_analyses
    used = await count_analyses_this_month(db, user.id)
    if used >= limit:
        raise _quota_error("analysis", limit, used)


async def enforce_project_quota(db: AsyncSession, user: User) -> None:
    if user.plan == "pro":
        return
    limit = get_settings().plan_free_projects
    used = await count_projects(db, user.id)
    if used >= limit:
        raise _quota_error("project", limit, used)


async def usage_summary(db: AsyncSession, user: User) -> dict:
    """Feeds the frontend usage meter. Display only — never the gate."""
    settings = get_settings()
    return {
        "plan": user.plan,
        "analyses": {
            "used": await count_analyses_this_month(db, user.id),
            "limit": settings.plan_free_analyses,
        },
        "projects": {
            "used": await count_projects(db, user.id),
            "limit": settings.plan_free_projects,
        },
    }
