"""
Domain Exceptions & Global Handlers
Defines BaseAppException and global exception handlers to return standardized
JSON responses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


# Domain Exceptions


class BaseAppException(Exception):
    """Base domain exception for the application."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Any | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class UnsupportedFileTypeError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="UNSUPPORTED_FILE_TYPE",
            details=details,
        )


class EmptyDocumentError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="EMPTY_DOCUMENT",
            details=details,
        )


class VectorStoreError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="VECTOR_STORE_UNAVAILABLE",
            details=details,
        )


class SqlValidationError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="SQL_VALIDATION_FAILED",
            details=details,
        )


class SqlExecutionError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="SQL_EXECUTION_FAILED",
            details=details,
        )


class RateLimitError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


class InputTooLongError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="INPUT_TOO_LONG",
            details=details,
        )


class LLMProviderError(BaseAppException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="LLM_PROVIDER_ERROR",
            details=details,
        )


# FastAPI Exception Handlers


async def app_exception_handler(
    request: Request, exc: BaseAppException
) -> JSONResponse:
    """Global handler for domain-specific BaseAppException instances."""
    logger.warning(
        "handled_app_exception",
        method=request.method,
        path=request.url.path,
        error_code=exc.error_code,
        message=exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Global handler for standard Starlette/FastAPI HTTPExceptions."""
    logger.warning(
        "http_exception",
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": "HTTP_ERROR",
            "message": str(exc.detail),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Global handler for Pydantic request validation errors."""
    logger.warning(
        "validation_error",
        method=request.method,
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": 422,
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed",
            "details": exc.errors(),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled internal server exceptions."""
    logger.error(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
