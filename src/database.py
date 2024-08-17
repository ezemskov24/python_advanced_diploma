from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost/twitter_clone_db"

Base = declarative_base()


def get_engine(database_url: str):
    return create_async_engine(database_url, echo=True)


def get_session(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


engine = get_engine(DATABASE_URL)
AsyncSessionLocal = get_session(engine)
