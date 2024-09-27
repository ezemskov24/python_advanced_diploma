import os
from datetime import datetime
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from server.main import app
from server.api.models import User
from server.database.db_connection import Base, get_db
from server.config import get_database_url

os.environ["ENV"] = "test"

DATABASE_URL_TEST = get_database_url()

test_engine = create_async_engine(DATABASE_URL_TEST, echo=True)
TestingSessionLocal = sessionmaker(
    bind=test_engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db) -> AsyncGenerator:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    test_user = User(
        username="testuser",
        api_key="testapikey",
        name="Test User",
        email="testuser@example.com",
        created_at=datetime.utcnow(),
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    return test_user


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator:
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
