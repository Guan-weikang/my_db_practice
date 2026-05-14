from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user, get_refresh_token_store
from app.api.deps.db import get_db_session
from app.core.token_store import RefreshTokenStore
from app.models.user_account import UserAccount
from app.schemas.auth import (
    AuthSessionResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


def _auth_service(session: AsyncSession, refresh_token_store: RefreshTokenStore) -> AuthService:
    return AuthService(session=session, refresh_token_store=refresh_token_store)


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
) -> AuthSessionResponse:
    return await _auth_service(session, refresh_token_store).register(payload)


@router.post("/login", response_model=AuthSessionResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
) -> AuthSessionResponse:
    return await _auth_service(session, refresh_token_store).login(payload)


@router.post("/refresh", response_model=AuthSessionResponse)
async def refresh(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
) -> AuthSessionResponse:
    return await _auth_service(session, refresh_token_store).refresh(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
) -> MessageResponse:
    await _auth_service(session, refresh_token_store).logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserAccount = Depends(get_current_active_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
