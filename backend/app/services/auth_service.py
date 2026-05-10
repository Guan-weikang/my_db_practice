from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import TokenResponse


class AuthService:
    def issue_tokens(self, subject: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(subject),
            refresh_token=create_refresh_token(subject),
        )

