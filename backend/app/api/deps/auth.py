from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db_session
from app.core.cache import RedisResponseCache
from app.core.config import settings
from app.core.exceptions import token_invalid, unauthorized, user_disabled
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.core.token_store import RedisRefreshTokenStore
from app.models.user_account import UserAccount
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_redis_client: Redis | None = None
_refresh_token_store: RedisRefreshTokenStore | None = None
_response_cache: RedisResponseCache | None = None


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis_client


def get_refresh_token_store() -> RedisRefreshTokenStore:
    global _refresh_token_store
    if _refresh_token_store is None:
        _refresh_token_store = RedisRefreshTokenStore(get_redis_client())
    return _refresh_token_store


def get_response_cache() -> RedisResponseCache:
    global _response_cache
    if _response_cache is None:
        _response_cache = RedisResponseCache(get_redis_client())
    return _response_cache


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> UserAccount:
    if not token:
        raise unauthorized("Not authenticated")
    payload = decode_token(token, token_type=ACCESS_TOKEN_TYPE)
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise token_invalid("Token subject is invalid") from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise token_invalid("User account not found for token")
    if user.status != "active":
        raise user_disabled()
    return user


async def get_current_active_user(user: UserAccount = Depends(get_current_user)) -> UserAccount:
    return user
