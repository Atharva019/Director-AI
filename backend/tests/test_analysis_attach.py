import pytest
import uuid
from httpx import AsyncClient
from models.analysis import SceneAnalysis
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_attach_analysis_to_scene(client: AsyncClient, db_session: AsyncSession, test_user):
    # 1. Create a project and scene
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"title": "Attach Test Project", "genre": "Drama"}
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    scene_resp = await client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "scene_number": 1,
            "title": "Scene 1",
            "location_type": "interior",
            "time_of_day": "day"
        }
    )
    assert scene_resp.status_code == 201
    scene_id = scene_resp.json()["id"]

    # 2. Directly insert an unattached SceneAnalysis for test_user
    analysis_id = uuid.uuid4()
    analysis = SceneAnalysis(
        id=analysis_id,
        user_id=test_user.id,
        image_path="https://storage.example.com/test.jpg",
        analysis_result={"overall_mood": "Tense"},
        model_used="test-model",
        confidence_score=0.95,
    )
    db_session.add(analysis)
    await db_session.commit()

    # 3. Call attach endpoint
    attach_resp = await client.post(f"/api/v1/analyses/{analysis_id}/attach/{scene_id}")
    assert attach_resp.status_code == 200
    data = attach_resp.json()
    assert data["id"] == str(analysis_id)
    assert data["scene_id"] == scene_id
    assert data["scene"]["id"] == scene_id
    assert data["scene"]["title"] == "Scene 1"
