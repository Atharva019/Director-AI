"""Quota enforcement at the HTTP boundary."""

import uuid

import pytest

from models.project import Project


@pytest.mark.asyncio
async def test_create_project_under_limit_succeeds(client):
    res = await client.post("/api/v1/projects/", json={"title": "First"})
    assert res.status_code == 201


@pytest.mark.asyncio
async def test_create_project_over_limit_returns_402(client, db_session, test_user):
    # Touch an authed route first so the user row is materialised.
    await client.get("/api/v1/projects/")
    for i in range(2):
        db_session.add(Project(id=uuid.uuid4(), user_id=test_user.id, title=f"P{i}"))
    await db_session.commit()

    res = await client.post("/api/v1/projects/", json={"title": "Third"})

    assert res.status_code == 402
    body = res.json()["detail"]
    assert body["error"] == "quota_exceeded"
    assert body["resource"] == "project"
    assert body["limit"] == 2
    assert body["used"] == 2


@pytest.mark.asyncio
async def test_usage_endpoint_reports_plan_and_counts(client):
    res = await client.get("/api/v1/auth/usage")
    assert res.status_code == 200
    body = res.json()
    assert body["plan"] == "free"
    assert body["analyses"] == {"used": 0, "limit": 5}
    assert body["projects"] == {"used": 0, "limit": 2}
