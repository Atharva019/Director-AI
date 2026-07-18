"""Guards that only matter in production — misconfiguration must fail loudly.

Every one of these covers a way the app could boot "successfully" and then
corrupt data or serve broken responses.
"""

import pytest

from config import Settings


# ── R2 configuration ─────────────────────────────────────────────────────────


def test_r2_enabled_requires_public_base_url():
    """A bucket we can write to but not link to is useless — the URL is what
    we persist."""
    partial = Settings(
        R2_ACCOUNT_ID="acct",
        R2_ACCESS_KEY_ID="key",
        R2_BUCKET="bucket",
        R2_PUBLIC_BASE_URL="",
    )
    assert partial.r2_enabled is False


def test_r2_enabled_when_fully_configured():
    full = Settings(
        R2_ACCOUNT_ID="acct",
        R2_ACCESS_KEY_ID="key",
        R2_SECRET_ACCESS_KEY="secret",
        R2_BUCKET="bucket",
        R2_PUBLIC_BASE_URL="https://pub-x.r2.dev",
    )
    assert full.r2_enabled is True


@pytest.mark.asyncio
async def test_production_startup_rejects_missing_r2():
    """Without this, uploads persist relative paths like /analyses/x.png."""
    from main import verify_storage_config

    bad = Settings(APP_ENV="production", R2_ACCOUNT_ID="", R2_BUCKET="")
    with pytest.raises(RuntimeError, match="R2"):
        verify_storage_config(bad)


@pytest.mark.asyncio
async def test_development_startup_tolerates_missing_r2():
    from main import verify_storage_config

    verify_storage_config(Settings(APP_ENV="development"))  # no raise


# ── CORS configuration ───────────────────────────────────────────────────────


def test_cors_origin_list_drops_empty_entries():
    """An unset CORS_ORIGINS previously yielded [''], a junk origin."""
    assert Settings(CORS_ORIGINS="").cors_origin_list == []
    assert Settings(CORS_ORIGINS="https://a.com, ,https://b.com").cors_origin_list == [
        "https://a.com",
        "https://b.com",
    ]


def test_production_startup_rejects_empty_cors():
    from main import verify_cors_config

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        verify_cors_config(Settings(APP_ENV="production", CORS_ORIGINS=""))


def test_production_startup_rejects_wildcard_cors():
    """allow_credentials=True plus a wildcard origin is a credential leak."""
    from main import verify_cors_config

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        verify_cors_config(Settings(APP_ENV="production", CORS_ORIGINS="*"))


# ── Schema management ────────────────────────────────────────────────────────


def test_create_all_disabled_in_production():
    """Alembic owns the production schema; create_all would mask drift."""
    from main import should_create_all

    assert should_create_all(Settings(APP_ENV="production")) is False
    assert should_create_all(Settings(APP_ENV="development")) is True
