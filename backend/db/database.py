"""
Async SQLAlchemy engine, session factory, declarative Base, and FastAPI dependency.
"""

import logging
from typing import AsyncGenerator, Dict, Tuple
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def prepare_asyncpg_url(url: str) -> Tuple[str, Dict]:
    """Make a libpq-style connection string safe for asyncpg.

    Managed Postgres providers (Neon, Supabase, Heroku) hand out URLs ending in
    `?sslmode=require`, often with `channel_binding` too. psycopg2 accepts those
    verbatim, so Alembic migrates happily — but asyncpg rejects them outright
    with `TypeError: connect() got an unexpected keyword argument 'sslmode'`.
    The result is a confusing split failure where migrations succeed and then
    the app won't boot on the very same URL.

    SQLAlchemy's asyncpg dialect forwards every query parameter as a keyword
    argument to `asyncpg.connect()`, which accepts almost none of libpq's — so
    anything not explicitly translated below is dropped rather than allowed to
    crash the boot. Dropping is the right trade here: these are tuning hints,
    and a failed deploy is far more costly than an unapplied one.
    """
    if "+asyncpg" not in url:
        return url, {}

    parts = urlsplit(url)
    connect_args: Dict = {}
    server_settings: Dict[str, str] = {}
    dropped = []

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            # asyncpg takes a bool/SSLContext via connect_args, not a URL param.
            if value not in ("disable", "allow"):
                connect_args["ssl"] = True
        elif key == "application_name":
            # asyncpg wants this under server_settings, not as a kwarg.
            server_settings["application_name"] = value
        elif key == "connect_timeout":
            try:
                connect_args["timeout"] = float(value)
            except ValueError:
                dropped.append(key)
        else:
            # channel_binding, target_session_attrs, ssl file paths, options…
            dropped.append(key)

    if server_settings:
        connect_args["server_settings"] = server_settings
    if dropped:
        logger.info(
            "Dropped libpq-only DATABASE_URL parameters unsupported by asyncpg: %s",
            ", ".join(sorted(set(dropped))),
        )

    cleaned = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "", parts.fragment)
    )
    return cleaned, connect_args


_db_url, _connect_args = prepare_asyncpg_url(settings.DATABASE_URL)

# ── Engine ────────────────────────────────────────────────────────────────────
# Pool sizing is tuned for the free tier: Neon caps concurrent connections and
# a Render free instance serves modest traffic, so 20+10 would burn the budget
# on idle connections (and can exhaust it outright across a redeploy overlap).
# pool_recycle keeps us under Neon's idle-connection timeout.
async_engine = create_async_engine(
    _db_url,
    echo=settings.APP_DEBUG,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=_connect_args,
)

# ── Session factory ───────────────────────────────────────────────────────────
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and ensure it is closed after use."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
