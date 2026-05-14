import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    email_already_exists,
    invalid_credentials,
    token_revoked,
    user_disabled,
    username_already_exists,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    REFRESH_TOKEN_TYPE,
)
from app.core.token_store import RefreshTokenStore
from app.models.user_account import UserAccount
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthSessionResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession, refresh_token_store: RefreshTokenStore) -> None:
        self.session = session
        self.refresh_token_store = refresh_token_store
        self.user_repository = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> AuthSessionResponse:
        if await self.user_repository.get_by_username(payload.username):
            logger.warning("register_failed reason=username_exists username=%s", payload.username)
            raise username_already_exists()
        if payload.email and await self.user_repository.get_by_email(payload.email):
            logger.warning("register_failed reason=email_exists username=%s", payload.username)
            raise email_already_exists()

        user = await self.user_repository.create(
            username=payload.username,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            email=payload.email,
        )
        await self.session.commit()
        await self.session.refresh(user)
        logger.info("register_success user_id=%s username=%s", user.user_id, user.username)
        return await self._build_auth_session(user)

    async def login(self, payload: LoginRequest) -> AuthSessionResponse:
        user = await self.user_repository.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.password_hash):
            logger.warning("login_failed reason=invalid_credentials username=%s", payload.username)
            raise invalid_credentials()
        if user.status != "active":
            logger.warning("login_failed reason=user_disabled user_id=%s username=%s", user.user_id, user.username)
            raise user_disabled()
        logger.info("login_success user_id=%s username=%s", user.user_id, user.username)
        return await self._build_auth_session(user)

    async def refresh(self, refresh_token: str) -> AuthSessionResponse:
        payload = decode_token(refresh_token, token_type=REFRESH_TOKEN_TYPE)
        user_id = int(payload["sub"])
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            logger.warning("refresh_failed reason=missing_jti user_id=%s", user_id)
            raise token_revoked("Refresh token is missing token id")
        if not await self.refresh_token_store.is_token_active(user_id=user_id, jti=jti):
            logger.warning("refresh_failed reason=token_revoked user_id=%s", user_id)
            raise token_revoked()

        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            logger.warning("refresh_failed reason=user_not_found user_id=%s", user_id)
            raise invalid_credentials("User account no longer exists")
        if user.status != "active":
            logger.warning("refresh_failed reason=user_disabled user_id=%s username=%s", user.user_id, user.username)
            raise user_disabled()

        await self.refresh_token_store.revoke_token(user_id=user_id, jti=jti)
        logger.info("refresh_success user_id=%s username=%s", user.user_id, user.username)
        return await self._build_auth_session(user)

    async def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, token_type=REFRESH_TOKEN_TYPE)
        user_id = int(payload["sub"])
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            logger.warning("logout_failed reason=missing_jti user_id=%s", user_id)
            raise token_revoked("Refresh token is missing token id")
        if not await self.refresh_token_store.is_token_active(user_id=user_id, jti=jti):
            logger.warning("logout_failed reason=token_revoked user_id=%s", user_id)
            raise token_revoked()
        await self.refresh_token_store.revoke_token(user_id=user_id, jti=jti)
        logger.info("logout_success user_id=%s", user_id)

    async def _build_auth_session(self, user: UserAccount) -> AuthSessionResponse:
        access_token = create_access_token(str(user.user_id))
        refresh_token = create_refresh_token(str(user.user_id))
        await self.refresh_token_store.store_token(
            user_id=user.user_id,
            jti=refresh_token.jti or "",
            expires_in=refresh_token.expires_in,
        )
        return AuthSessionResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token.token,
            refresh_token=refresh_token.token,
            token_type="bearer",
            expires_in=access_token.expires_in,
        )
