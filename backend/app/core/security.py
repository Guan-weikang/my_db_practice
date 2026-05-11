from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import ExpiredSignatureError, JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import token_expired, token_invalid

password_hash = PasswordHash.recommended()
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


@dataclass(frozen=True, slots=True)
class IssuedToken:
    token: str
    expires_in: int
    jti: str | None = None


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def create_token(
    subject: str,
    *,
    secret: str,
    expires_delta: timedelta,
    token_type: str,
    extra_claims: dict[str, Any] | None = None,
) -> IssuedToken:
    issued_at = datetime.now(timezone.utc)
    expire_at = issued_at + expires_delta
    jti = str(uuid4())
    expires_in = int(expires_delta.total_seconds())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": expire_at,
        "jti": jti,
    }
    if extra_claims:
        payload.update(extra_claims)
    return IssuedToken(
        token=jwt.encode(payload, secret, algorithm="HS256"),
        expires_in=expires_in,
        jti=jti,
    )


def create_access_token(subject: str) -> IssuedToken:
    return create_token(
        subject=subject,
        secret=settings.jwt_secret_key,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type=ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(subject: str) -> IssuedToken:
    return create_token(
        subject=subject,
        secret=settings.jwt_refresh_secret_key,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type=REFRESH_TOKEN_TYPE,
    )


def decode_token(token: str, *, token_type: str) -> dict[str, Any]:
    secret = settings.jwt_secret_key if token_type == ACCESS_TOKEN_TYPE else settings.jwt_refresh_secret_key
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise token_expired() from exc
    except JWTError as exc:
        raise token_invalid() from exc

    if payload.get("type") != token_type:
        raise token_invalid("Token type is invalid")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise token_invalid("Token subject is invalid")

    return payload
