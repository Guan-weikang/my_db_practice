from fastapi import APIRouter

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/register")
async def register(payload: RegisterRequest) -> dict:
    return {"message": f"user {payload.username} registered (skeleton)"}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    return auth_service.issue_tokens(payload.username)


@router.post("/refresh", response_model=TokenResponse)
async def refresh() -> TokenResponse:
    return auth_service.issue_tokens("refresh-user")


@router.post("/logout")
async def logout() -> dict:
    return {"message": "logged out"}


@router.get("/me")
async def me() -> dict:
    return {"message": "current user placeholder"}

