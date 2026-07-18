import uuid
import pytest
from models.analysis import SceneAnalysis
from models.user import User


@pytest.mark.asyncio
async def test_cannot_read_other_users_analysis(client, db_session, test_user):
    other = User(id=uuid.uuid4(), firebase_uid="other_uid", email="other@example.com")
    db_session.add(other)
    await db_session.flush()

    foreign_id = uuid.uuid4()
    foreign = SceneAnalysis(
        id=foreign_id, user_id=other.id, image_path="https://r2/x.jpg",
        analysis_result={}, model_used="test", confidence_score=0.5,
    )
    db_session.add(foreign)
    await db_session.commit()

    # foreign_id captured before commit: AsyncSession expires ORM attributes
    # on commit, and re-reading foreign.id here would trigger a lazy-load
    # outside the greenlet context (MissingGreenlet).
    res = await client.get(f"/api/v1/analyses/{foreign_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_analyses_only_returns_own(client, db_session, test_user):
    other = User(id=uuid.uuid4(), firebase_uid="other2", email="o2@example.com")
    db_session.add(other)
    await db_session.flush()
    db_session.add(SceneAnalysis(
        id=uuid.uuid4(), user_id=other.id, image_path="https://r2/y.jpg",
        analysis_result={}, model_used="test", confidence_score=0.5,
    ))
    await db_session.commit()

    res = await client.get("/api/v1/analyses")
    assert res.status_code == 200
    assert res.json() == []
