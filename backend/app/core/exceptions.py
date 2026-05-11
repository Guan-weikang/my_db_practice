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
    return ApiError(status_code=status.HTTP_401_UNAUTHORIZED, code="UNAUTHORIZED", message=message)


def forbidden(message: str = "Permission denied") -> ApiError:
    return ApiError(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message=message)


def not_found(message: str) -> ApiError:
    return ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message=message)


def conflict(message: str) -> ApiError:
    return ApiError(status_code=status.HTTP_409_CONFLICT, code="CONFLICT", message=message)
