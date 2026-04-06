import os
from typing import Optional

import redis.asyncio as aioredis

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        _redis = await aioredis.from_url(redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
