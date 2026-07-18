"""Guards that only matter in production — misconfiguration must fail loudly.

Every one of these covers a way the app could boot "successfully" and then
corrupt data or serve broken responses.
"""

import pytest

from config import Settings


# ── Object storage configuration ─────────────────────────────────────────────


def _storage_settings(**overrides):
    base = dict(
        S3_ENDPOINT_URL="https://acct.r2.cloudflarestorage.com",
        S3_ACCESS_KEY_ID="key",
        S3_SECRET_ACCESS_KEY="secret",
        S3_BUCKET="bucket",
        S3_PUBLIC_BASE_URL="https://pub-x.r2.dev",
    )
    base.update(overrides)
    return Settings(**base)


def test_storage_enabled_requires_public_base_url():
    """A bucket we can write to but not link to is useless — the URL is what
    we persist."""
    assert _storage_settings(S3_PUBLIC_BASE_URL="").storage_enabled is False


def test_storage_enabled_requires_endpoint():
    """An empty endpoint makes boto3 target real AWS S3."""
    assert _storage_settings(S3_ENDPOINT_URL="").storage_enabled is False


def test_storage_enabled_when_fully_configured():
    assert _storage_settings().storage_enabled is True


def test_storage_config_is_provider_agnostic():
    """Any S3-compatible endpoint works — R2 is not special-cased."""
    for endpoint, region in [
        ("https://acct.r2.cloudflarestorage.com", "auto"),
        ("https://proj.supabase.co/storage/v1/s3", "us-east-1"),
        ("https://s3.us-west-004.backblazeb2.com", "us-west-004"),
    ]:
        cfg = _storage_settings(S3_ENDPOINT_URL=endpoint, S3_REGION=region)
        assert cfg.storage_enabled is True
        assert cfg.S3_REGION == region


@pytest.mark.asyncio
async def test_production_startup_rejects_missing_storage():
    """Without this, uploads persist relative paths like /analyses/x.png."""
    from main import verify_storage_config

    bad = Settings(APP_ENV="production", S3_ENDPOINT_URL="", S3_BUCKET="")
    with pytest.raises(RuntimeError, match="S3_ENDPOINT_URL"):
        verify_storage_config(bad)


@pytest.mark.asyncio
async def test_development_startup_tolerates_missing_storage():
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
