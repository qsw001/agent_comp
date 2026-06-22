"""
Redis 客户端
"""
from __future__ import annotations

from redis.asyncio import Redis

from app.config import settings

_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """获取共享 Redis 客户端。"""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    """关闭共享 Redis 客户端。"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
