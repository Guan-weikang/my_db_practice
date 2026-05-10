from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def create_token(subject: str, secret: str, expires_delta: timedelta, extra_claims: dict[str, Any] | None = None) -> str:
    expire_at = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {"sub": subject, "exp": expire_at}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm="HS256")


def create_access_token(subject: str) -> str:
    return create_token(
        subject=subject,
        secret=settings.jwt_secret_key,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> str:
    return create_token(
        subject=subject,
        secret=settings.jwt_refresh_secret_key,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )

