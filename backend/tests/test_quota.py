"""Free-tier quota enforcement — service level."""

import uuid

import pytest
from fastapi import HTTPException

from models.analysis import SceneAnalysis
from models.project import Project
from models.user import User
from services import quota_service


async def _make_user(db, plan="free"):
    u = User(
        id=uuid.uuid4(),
        firebase_uid=f"u{uuid.uuid4().hex[:6]}",
        email=f"{uuid.uuid4().hex[:6]}@t.com",
        plan=plan,
    )
    db.add(u)
    await db.flush()
    return u


def _analysis(user_id):
    return SceneAnalysis(
        id=uuid.uuid4(),
        user_id=user_id,
        image_path="https://r2/x.jpg",
        analysis_result={},
        model_used="t",
        confidence_score=0.1,
    )


@pytest.mark.asyncio
async def test_free_user_under_limit_passes(db_session):
    u = await _make_user(db_session)
    await quota_service.enforce_analysis_quota(db_session, u)  # no raise


@pytest.mark.asyncio
async def test_free_user_at_analysis_limit_raises_402(db_session):
    u = await _make_user(db_session)
    for _ in range(5):
        db_session.add(_analysis(u.id))
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await quota_service.enforce_analysis_quota(db_session, u)

    assert exc.value.status_code == 402
    assert exc.value.detail["error"] == "quota_exceeded"
    assert exc.value.detail["resource"] == "analysis"
    assert exc.value.detail["limit"] == 5
    assert exc.value.detail["used"] == 5
    assert "waitlist" in exc.value.detail["message"].lower()


@pytest.mark.asyncio
async def test_pro_user_bypasses_limit(db_session):
    u = await _make_user(db_session, plan="pro")
    for _ in range(10):
        db_session.add(_analysis(u.id))
    await db_session.flush()

    await quota_service.enforce_analysis_quota(db_session, u)  # no raise


@pytest.mark.asyncio
async def test_analysis_quota_counts_only_own_rows(db_session):
    """Another user's analyses must not consume this user's quota."""
    mine = await _make_user(db_session)
    theirs = await _make_user(db_session)
    for _ in range(5):
        db_session.add(_analysis(theirs.id))
    await db_session.flush()

    await quota_service.enforce_analysis_quota(db_session, mine)  # no raise


@pytest.mark.asyncio
async def test_free_user_at_project_limit_raises_402(db_session):
    u = await _make_user(db_session)
    for i in range(2):
        db_session.add(Project(id=uuid.uuid4(), user_id=u.id, title=f"P{i}"))
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await quota_service.enforce_project_quota(db_session, u)

    assert exc.value.status_code == 402
    assert exc.value.detail["resource"] == "project"
    assert exc.value.detail["limit"] == 2
