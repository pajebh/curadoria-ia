from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlparse, urlencode, urlunparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _parse_db_url(url: str) -> tuple[str, dict]:
    """Strip sslmode from URL and return (clean_url, connect_args).

    asyncpg doesn't accept sslmode as a query param; SSL must be passed
    via connect_args instead.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = params.pop("sslmode", [None])[0]
    params.pop("channel_binding", None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))
    connect_args: dict = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = True
    return clean_url, connect_args


_db_url, _connect_args = _parse_db_url(settings.database_url)

engine = create_async_engine(
    _db_url,
    connect_args=_connect_args,
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
                __import__("sqlalchemy").text(f"SET LOCAL app.session_id = '{session_id}'")
            )
        yield session
