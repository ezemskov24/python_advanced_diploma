from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from server.config import (
    DB_USER,
    DB_PASS,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()


def get_engine(database_url: str):
    return create_async_engine(database_url, echo=True)


def get_session(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


engine = get_engine(DATABASE_URL)
AsyncSessionLocal = get_session(engine)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
