from __future__ import annotations

import logging
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class ResponseCache(Protocol):
    async def get_json(self, key: str) -> str | None: ...

    async def set_json(self, key: str, value: str, *, ttl_seconds: int) -> None: ...

    async def delete_pattern(self, pattern: str) -> None: ...


class RedisResponseCache:
    def __init__(self, redis_client: Redis, *, prefix: str = "cache:v1") -> None:
        self.redis_client = redis_client
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get_json(self, key: str) -> str | None:
        try:
            value = await self.redis_client.get(self._key(key))
        except RedisError as exc:
            logger.warning("cache_get_failed key=%s error=%s", key, exc)
            return None
        return str(value) if value is not None else None

    async def set_json(self, key: str, value: str, *, ttl_seconds: int) -> None:
        try:
            await self.redis_client.set(self._key(key), value, ex=ttl_seconds)
        except RedisError as exc:
            logger.warning("cache_set_failed key=%s error=%s", key, exc)

    async def delete_pattern(self, pattern: str) -> None:
        try:
            keys = [key async for key in self.redis_client.scan_iter(self._key(pattern))]
            if keys:
                await self.redis_client.delete(*keys)
        except RedisError as exc:
            logger.warning("cache_delete_pattern_failed pattern=%s error=%s", pattern, exc)
