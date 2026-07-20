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


# ── Routing behind the proxy ─────────────────────────────────────────────────


def test_no_route_ends_in_trailing_slash():
    """A trailing-slash route is unreachable behind the Vercel proxy.

    Next strips the trailing slash before proxying, so the browser can never
    hit a "/"-suffixed route; FastAPI would 307 it cross-origin to the raw
    backend host, which fails CORS as "Failed to fetch". Keep every route
    slash-less so the browser reaches it directly.
    """
    from fastapi.routing import APIRoute

    from main import app

    offenders = [
        r.path
        for r in app.routes
        if isinstance(r, APIRoute) and r.path != "/" and r.path.endswith("/")
    ]
    assert offenders == [], f"routes end in '/': {offenders}"


def test_slash_redirect_is_disabled():
    """redirect_slashes off = a mismatch is a loud 404, not a silent
    cross-origin 307."""
    from main import app

    assert app.router.redirect_slashes is False


# ── Schema management ────────────────────────────────────────────────────────


def test_create_all_disabled_in_production():
    """Alembic owns the production schema; create_all would mask drift."""
    from main import should_create_all

    assert should_create_all(Settings(APP_ENV="production")) is False
    assert should_create_all(Settings(APP_ENV="development")) is True


# ── Database URL handling ────────────────────────────────────────────────────


def test_database_configured_detects_local_default():
    assert Settings().database_configured is False
    assert Settings(DATABASE_URL="postgresql+asyncpg://u:p@127.0.0.1/db").database_configured is False
    assert Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@ep-x.neon.tech/db"
    ).database_configured is True


def test_production_startup_rejects_unset_database_url():
    """An unset DATABASE_URL otherwise surfaces as a psycopg2 traceback."""
    from config import verify_database_config

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        verify_database_config(Settings(APP_ENV="production"))


def test_development_tolerates_local_database_url():
    from config import verify_database_config

    verify_database_config(Settings(APP_ENV="development"))  # no raise


def test_neon_sslmode_is_stripped_for_asyncpg():
    """psycopg2 accepts ?sslmode=require; asyncpg raises TypeError on it."""
    from db.database import prepare_asyncpg_url

    url, args = prepare_asyncpg_url(
        "postgresql+asyncpg://u:p@ep-x.neon.tech/db"
        "?sslmode=require&channel_binding=require"
    )
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert args == {"ssl": True}


def test_sslmode_disable_does_not_force_tls():
    from db.database import prepare_asyncpg_url

    _, args = prepare_asyncpg_url("postgresql+asyncpg://u:p@h/db?sslmode=disable")
    assert args == {}


def test_application_name_moves_to_server_settings():
    """asyncpg rejects application_name as a kwarg; it belongs in
    server_settings. Verified against a live connection, not just in theory."""
    from db.database import prepare_asyncpg_url

    url, args = prepare_asyncpg_url(
        "postgresql+asyncpg://u:p@h/db?sslmode=require&application_name=director"
    )
    assert "application_name" not in url
    assert args["server_settings"] == {"application_name": "director"}
    assert args["ssl"] is True


def test_unknown_libpq_params_are_dropped_not_forwarded():
    """Forwarding an unrecognised param crashes asyncpg at connect time, which
    on Render reads as a failed deploy. Dropping degrades gracefully instead."""
    from db.database import prepare_asyncpg_url

    url, args = prepare_asyncpg_url(
        "postgresql+asyncpg://u:p@h/db"
        "?target_session_attrs=read-write&sslrootcert=/etc/ca.pem&options=-c%20geqo%3Doff"
    )
    assert "?" not in url
    assert args == {}


def test_connect_timeout_is_translated():
    from db.database import prepare_asyncpg_url

    _, args = prepare_asyncpg_url("postgresql+asyncpg://u:p@h/db?connect_timeout=15")
    assert args == {"timeout": 15.0}


def test_provider_scheme_is_normalized_to_asyncpg():
    """Neon/Supabase hand out postgresql://, Heroku the legacy postgres://.

    Requiring a hand-edit produced "The asyncio extension requires an async
    driver" — an error naming neither the variable nor the fix. Whatever the
    provider gives, the app engine must end up on asyncpg.
    """
    from db.database import prepare_asyncpg_url

    for given in [
        "postgresql://u:p@ep-x.neon.tech/db?sslmode=require",
        "postgres://u:p@ep-x.neon.tech/db?sslmode=require",
        "postgresql+asyncpg://u:p@ep-x.neon.tech/db?sslmode=require",
        "postgresql+psycopg2://u:p@ep-x.neon.tech/db?sslmode=require",
    ]:
        url, args = prepare_asyncpg_url(given)
        assert url.startswith("postgresql+asyncpg://"), given
        assert "sslmode" not in url, given
        assert args == {"ssl": True}, given


def test_sync_url_normalizes_to_psycopg2_and_keeps_params():
    """Alembic runs sync and psycopg2 needs sslmode kept."""
    from db.database import prepare_sync_url

    for given in [
        "postgresql+asyncpg://u:p@ep-x.neon.tech/db?sslmode=require",
        "postgres://u:p@ep-x.neon.tech/db?sslmode=require",
        "postgresql://u:p@ep-x.neon.tech/db?sslmode=require",
    ]:
        url = prepare_sync_url(given)
        assert url.startswith("postgresql://"), given
        assert "+asyncpg" not in url, given
        assert "sslmode=require" in url, given


def test_non_postgres_urls_are_untouched():
    """The SQLite test URL must survive both helpers unchanged."""
    from db.database import prepare_asyncpg_url, prepare_sync_url

    sqlite = "sqlite+aiosqlite:///:memory:"
    assert prepare_asyncpg_url(sqlite) == (sqlite, {})
    assert prepare_sync_url(sqlite) == sqlite


def test_database_host_is_parsed_not_substring_matched():
    """A password containing 'localhost' must not trip the local-address check."""
    cfg = Settings(
        DATABASE_URL="postgresql+asyncpg://user:localhost127.0.0.1pw@ep-x.neon.tech/db"
    )
    assert cfg.database_host == "ep-x.neon.tech"
    assert cfg.database_configured is True


def test_database_host_detects_each_local_form():
    for host in ("localhost", "127.0.0.1"):
        cfg = Settings(DATABASE_URL=f"postgresql+asyncpg://u:p@{host}:5432/db")
        assert cfg.database_configured is False, host


def test_database_error_names_the_offending_host_not_the_password():
    """The message goes into deploy logs — it must never echo credentials."""
    from config import verify_database_config

    cfg = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+asyncpg://admin:hunter2secret@localhost:5432/db",
    )
    with pytest.raises(RuntimeError) as exc:
        verify_database_config(cfg)

    assert "localhost" in str(exc.value)
    assert "hunter2secret" not in str(exc.value)
    assert "admin" not in str(exc.value)
