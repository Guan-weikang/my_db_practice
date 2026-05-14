import logging
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import router as api_router
from app.core.logging import configure_logging
from app.core.config import settings
from app.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str, details: object | None = None) -> JSONResponse:
    payload = ErrorResponse(code=code, message=message, details=details)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.exception(
                "request_failed method=%s path=%s duration_ms=%s",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request_completed method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and {"code", "message", "details"} <= set(detail.keys()):
            return JSONResponse(status_code=exc.status_code, content=detail)
        return _error_response(exc.status_code, "HTTP_ERROR", str(detail), None)

    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and {"code", "message", "details"} <= set(detail.keys()):
            return JSONResponse(status_code=exc.status_code, content=detail)
        return _error_response(exc.status_code, "HTTP_ERROR", str(detail), None)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(422, "VALIDATION_ERROR", "Request validation failed", exc.errors())

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception: %s", exc)
        return _error_response(500, "INTERNAL_SERVER_ERROR", "Internal server error")

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    logger.info("application_created app_name=%s env=%s", settings.app_name, settings.app_env)
    return app


app = create_app()
