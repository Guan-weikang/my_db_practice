from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

