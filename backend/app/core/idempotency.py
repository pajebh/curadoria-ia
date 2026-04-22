from uuid import UUID

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None  # type: ignore[type-arg]


def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def idempotency_check(key: str, session_id: UUID) -> UUID | None:
    r = get_redis()
    val = await r.get(f"idem:{session_id}:{key}")
    return UUID(str(val)) if val else None


async def idempotency_store(key: str, session_id: UUID, plan_id: UUID) -> None:
    r = get_redis()
    await r.set(f"idem:{session_id}:{key}", str(plan_id), ex=3600)
