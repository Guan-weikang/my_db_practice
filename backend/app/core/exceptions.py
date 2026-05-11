from fastapi import HTTPException, status


class ApiError(HTTPException):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details,
            },
        )


def bad_request(message: str, details: object | None = None) -> ApiError:
    return ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="BAD_REQUEST", message=message, details=details)


def unauthorized(message: str = "Authentication required") -> ApiError:
    return ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="AUTHENTICATION_REQUIRED", message=message)


def forbidden(message: str = "Permission denied") -> ApiError:
    return ApiError(status_code=status.HTTP_403_FORBIDDEN, code="PERMISSION_DENIED", message=message)


def not_found(message: str) -> ApiError:
    return ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message=message)


def conflict(message: str) -> ApiError:
    return ApiError(status_code=status.HTTP_409_CONFLICT, code="CONFLICT", message=message)


def invalid_credentials(message: str = "Invalid username or password") -> ApiError:
    return ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="INVALID_CREDENTIALS", message=message)


def token_invalid(message: str = "Token is invalid") -> ApiError:
    return ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="TOKEN_INVALID", message=message)


def token_expired(message: str = "Token has expired") -> ApiError:
    return ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="TOKEN_EXPIRED", message=message)


def token_revoked(message: str = "Token has been revoked") -> ApiError:
    return ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="TOKEN_REVOKED", message=message)


def user_disabled(message: str = "User account is disabled") -> ApiError:
    return ApiError(status_code=status.HTTP_403_FORBIDDEN, code="USER_DISABLED", message=message)


def username_already_exists(message: str = "Username already exists") -> ApiError:
    return ApiError(status_code=status.HTTP_409_CONFLICT, code="USERNAME_ALREADY_EXISTS", message=message)


def email_already_exists(message: str = "Email already exists") -> ApiError:
    return ApiError(status_code=status.HTTP_409_CONFLICT, code="EMAIL_ALREADY_EXISTS", message=message)
