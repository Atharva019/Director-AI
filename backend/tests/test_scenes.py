import pytest
import pytest_asyncio
from httpx import AsyncClient

@pytest_asyncio.fixture
async def test_project(client: AsyncClient):
    response = await client.post(
        "/api/v1/projects",
        json={"title": "Scene Test Project", "genre": "Drama"}
    )
    return response.json()

@pytest.mark.asyncio
async def test_create_scene(client: AsyncClient, test_project):
    project_id = test_project["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "scene_number": 1,
            "title": "Opening Scene",
            "location_type": "interior",
            "time_of_day": "day"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Opening Scene"
    assert data["scene_number"] == 1

@pytest.mark.asyncio
async def test_list_scenes(client: AsyncClient, test_project):
    project_id = test_project["id"]
    await client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "scene_number": 1,
            "title": "Opening Scene",
            "location_type": "interior",
            "time_of_day": "day"
        }
    )
    response = await client.get(f"/api/v1/projects/{project_id}/scenes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Opening Scene"

@pytest.mark.asyncio
async def test_update_scene(client: AsyncClient, test_project):
    project_id = test_project["id"]
    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "scene_number": 1,
            "title": "Opening Scene",
            "location_type": "interior",
            "time_of_day": "day"
        }
    )
    scene_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/scenes/{scene_id}",
        json={"title": "Updated Opening Scene"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Opening Scene"

@pytest.mark.asyncio
async def test_delete_scene(client: AsyncClient, test_project):
    project_id = test_project["id"]
    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "scene_number": 1,
            "title": "Opening Scene",
            "location_type": "interior",
            "time_of_day": "day"
        }
    )
    scene_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/scenes/{scene_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/scenes/{scene_id}")
    assert get_resp.status_code == 404
