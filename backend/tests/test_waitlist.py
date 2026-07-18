"""Public waitlist endpoint — no authentication required."""

import pytest


@pytest.mark.asyncio
async def test_join_waitlist_creates_entry(client):
    res = await client.post(
        "/api/v1/waitlist", json={"email": "a@b.com", "source": "landing"}
    )
    assert res.status_code == 201
    assert res.json()["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_join_waitlist_is_idempotent(client):
    await client.post("/api/v1/waitlist", json={"email": "dup@b.com"})
    res = await client.post("/api/v1/waitlist", json={"email": "dup@b.com"})
    assert res.status_code in (200, 201)
    assert res.json()["email"] == "dup@b.com"


@pytest.mark.asyncio
async def test_join_waitlist_rejects_bad_email(client):
    res = await client.post("/api/v1/waitlist", json={"email": "not-an-email"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_join_waitlist_defaults_source(client):
    res = await client.post("/api/v1/waitlist", json={"email": "nosource@b.com"})
    assert res.status_code == 201
