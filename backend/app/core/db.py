from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=not settings.is_production,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db(session_id: UUID | None = None) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        if session_id is not None:
            await session.execute(
                # RLS: define o contexto de sessão para RLS policies
                __import__("sqlalchemy").text("SET LOCAL app.session_id = :sid"),
                {"sid": str(session_id)},
            )
        yield session
