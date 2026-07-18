"""
Async SQLAlchemy engine, session factory, declarative Base, and FastAPI dependency.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# Pool sizing is tuned for the free tier: Neon caps concurrent connections and
# a Render free instance serves modest traffic, so 20+10 would burn the budget
# on idle connections (and can exhaust it outright across a redeploy overlap).
# pool_recycle keeps us under Neon's idle-connection timeout.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
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
