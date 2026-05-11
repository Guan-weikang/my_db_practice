from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from redis.asyncio import Redis


class RefreshTokenStore(Protocol):
    async def store_token(self, *, user_id: int, jti: str, expires_in: int) -> None: ...

    async def is_token_active(self, *, user_id: int, jti: str) -> bool: ...

    async def revoke_token(self, *, user_id: int, jti: str) -> None: ...


class RedisRefreshTokenStore:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    def _key(self, *, user_id: int, jti: str) -> str:
        return f"auth:refresh:{user_id}:{jti}"

    async def store_token(self, *, user_id: int, jti: str, expires_in: int) -> None:
        await self.redis_client.set(self._key(user_id=user_id, jti=jti), "1", ex=expires_in)

    async def is_token_active(self, *, user_id: int, jti: str) -> bool:
        return bool(await self.redis_client.exists(self._key(user_id=user_id, jti=jti)))

    async def revoke_token(self, *, user_id: int, jti: str) -> None:
        await self.redis_client.delete(self._key(user_id=user_id, jti=jti))


@dataclass(slots=True)
class _InMemoryTokenRecord:
    expires_at: datetime


class InMemoryRefreshTokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, _InMemoryTokenRecord] = {}

    def _key(self, *, user_id: int, jti: str) -> str:
        return f"{user_id}:{jti}"

    def _cleanup(self) -> None:
        now = datetime.now(timezone.utc)
        expired_keys = [key for key, record in self._tokens.items() if record.expires_at <= now]
        for key in expired_keys:
            self._tokens.pop(key, None)

    async def store_token(self, *, user_id: int, jti: str, expires_in: int) -> None:
        self._cleanup()
        self._tokens[self._key(user_id=user_id, jti=jti)] = _InMemoryTokenRecord(
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        )

    async def is_token_active(self, *, user_id: int, jti: str) -> bool:
        self._cleanup()
        return self._key(user_id=user_id, jti=jti) in self._tokens

    async def revoke_token(self, *, user_id: int, jti: str) -> None:
        self._tokens.pop(self._key(user_id=user_id, jti=jti), None)
