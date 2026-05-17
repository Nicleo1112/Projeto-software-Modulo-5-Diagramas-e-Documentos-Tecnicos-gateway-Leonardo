import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

AsyncSessionLocal = (
    async_sessionmaker(engine, expire_on_commit=False)
    if engine
    else None
)


async def init_db() -> None:
    if engine is None:
        return

    import app.models

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


def is_database_configured() -> bool:
    return engine is not None


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    if AsyncSessionLocal is None:
        yield None
        return

    async with AsyncSessionLocal() as session:
        yield session
