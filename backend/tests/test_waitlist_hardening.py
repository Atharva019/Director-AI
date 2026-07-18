"""Waitlist is the only public write endpoint — it needs abuse and race guards."""


import pytest

from services import ip_rate_limiter


@pytest.fixture(autouse=True)
def _reset_limiter():
    ip_rate_limiter.reset()
    yield
    ip_rate_limiter.reset()


@pytest.mark.asyncio
async def test_lost_insert_race_returns_200_not_500(client, db_session, monkeypatch):
    """Check-then-insert is not atomic — the loser must not surface as a 500.

    True concurrency isn't reachable through the test client (the fixture
    shares one session across requests, whereas production gets one session per
    request). So this drives the recovery branch directly: the pre-check reports
    "no such email" while the row in fact exists, exactly as the losing request
    of a real race observes it. The seed is committed so the route's rollback
    doesn't discard it — in production the winning request has committed too.
    """
    from models.waitlist import WaitlistEntry

    db_session.add(WaitlistEntry(email="race@b.com", source="seed"))
    await db_session.commit()

    from routers import waitlist as waitlist_router

    real_fetch = waitlist_router._fetch
    calls = {"n": 0}

    async def fetch_blind_once(db, email):
        # First call = the pre-check, forced to miss. Later calls (the recovery
        # lookup) behave normally.
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return await real_fetch(db, email)

    monkeypatch.setattr(waitlist_router, "_fetch", fetch_blind_once)

    res = await client.post("/api/v1/waitlist", json={"email": "race@b.com"})

    assert res.status_code == 200, res.text
    assert res.json()["email"] == "race@b.com"


@pytest.mark.asyncio
async def test_waitlist_rate_limited_per_ip(client):
    """An unauthenticated write endpoint on a free tier must not be spammable."""
    limit = ip_rate_limiter.WAITLIST_PER_HOUR

    for i in range(limit):
        res = await client.post("/api/v1/waitlist", json={"email": f"ok{i}@b.com"})
        assert res.status_code in (200, 201), f"request {i} -> {res.status_code}"

    blocked = await client.post("/api/v1/waitlist", json={"email": "toomany@b.com"})
    assert blocked.status_code == 429


def test_rate_limiter_allows_after_window_expires():
    ip_rate_limiter.reset()
    for _ in range(ip_rate_limiter.WAITLIST_PER_HOUR):
        assert ip_rate_limiter.allow("1.2.3.4", "waitlist") is True
    assert ip_rate_limiter.allow("1.2.3.4", "waitlist") is False

    # A different caller is unaffected.
    assert ip_rate_limiter.allow("5.6.7.8", "waitlist") is True


def test_rate_limiter_is_per_ip():
    ip_rate_limiter.reset()
    for _ in range(ip_rate_limiter.WAITLIST_PER_HOUR):
        ip_rate_limiter.allow("1.1.1.1", "waitlist")
    assert ip_rate_limiter.allow("1.1.1.1", "waitlist") is False
    assert ip_rate_limiter.allow("2.2.2.2", "waitlist") is True
