import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.database import Base, get_db
from auth.middleware import get_current_user
from main import app
from models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def test_user():
    return User(
        id=uuid.uuid4(),
        firebase_uid="test_uid",
        email="test@example.com",
        display_name="Test User",
    )

@pytest_asyncio.fixture(scope="function")
async def client(db_session, test_user):
    async def override_get_db():
        yield db_session

    persisted = False

    async def override_get_current_user():
        # Persist on the first call only. Re-adding an already-persistent user
        # cascades into its relationships, and after a request that deleted one
        # of its projects that cascade tries to resurrect a deleted instance.
        nonlocal persisted
        if not persisted:
            db_session.add(test_user)
            await db_session.commit()
            persisted = True
        # Refresh every call: a preceding commit in the test body expires the
        # instance, and the route reads user.plan for the quota check.
        await db_session.refresh(test_user)
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
