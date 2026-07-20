import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    response = await client.post(
        "/api/v1/projects",
        json={"title": "Test Project", "genre": "Action"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["genre"] == "Action"

@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await client.post(
        "/api/v1/projects",
        json={"title": "Test Project", "genre": "Action"}
    )
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Project"

@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/projects",
        json={"title": "Test Project", "genre": "Action"}
    )
    project_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id

@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/projects",
        json={"title": "Test Project", "genre": "Action"}
    )
    project_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"title": "Updated Project"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Project"

@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/projects",
        json={"title": "Test Project", "genre": "Action"}
    )
    project_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404
