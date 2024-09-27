from typing import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from server.config import get_database_url


Base = declarative_base()

def get_engine(database_url: str):
    """
    Creates an asynchronous SQLAlchemy engine for connecting to the database.

    Args:
        database_url (str): The URL for connecting to the database.

    Returns:
        AsyncEngine: The created asynchronous engine.
    """
    return create_async_engine(database_url, echo=True)


engine = get_engine(get_database_url())
AsyncSessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    Asynchronous generator for obtaining a database session.

    Uses a context manager to create and close the database session.

    Yields:
        AsyncSession: The active database session.

    Notes:
        The session is automatically closed after use.
    """
    async with AsyncSessionLocal() as session:
        yield session

