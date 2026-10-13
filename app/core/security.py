
from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.exceptions import InputTooLongError, RateLimitError

# Constants
MAX_REQUEST_BODY_BYTES: int = 50 * 1024 * 1024  # 50 MB (document uploads)
MAX_QUESTION_LENGTH: int = 4_000  
RATE_LIMIT_REQUESTS: int = 60  
RATE_LIMIT_WINDOW_SECONDS: int = 60  

_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    """Raises RateLimitError if the client has exceeded the rate limit."""
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    timestamps = _rate_store[client_ip]

    # Evict old timestamps outside the window
    _rate_store[client_ip] = [t for t in timestamps if t > window_start]

    if len(_rate_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise RateLimitError(
            f"Rate limit exceeded: max {RATE_LIMIT_REQUESTS} requests "
            f"per {RATE_LIMIT_WINDOW_SECONDS}s."
        )

    _rate_store[client_ip].append(now)


# Input validation helpers


def validate_question_length(question: str) -> None:
    """Raises InputTooLongError if the question exceeds the character limit."""
    if len(question) > MAX_QUESTION_LENGTH:
        raise InputTooLongError(
            f"Question too long: {len(question)} chars (max {MAX_QUESTION_LENGTH})."
        )


def sanitise_filename(filename: str) -> str:
    """Strips path traversal characters from an uploaded filename."""
    return Path(filename).name  # strips directory components


def assert_path_contained(base_dir: Path, target: Path) -> None:
    """
    Ensures `target` is within `base_dir`.
    Prevents path traversal attacks (e.g. ../../etc/passwd).
    """
    try:
        target.resolve().relative_to(base_dir.resolve())
    except ValueError as exc:
        raise PermissionError(
            f"Path traversal detected: {target} is not within {base_dir}"
        ) from exc


# Starlette middleware


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Applies rate limiting and body size checks on every inbound request.
    Register this in main.py: app.add_middleware(SecurityMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Rate limiting by client IP
        client_ip = request.client.host if request.client else "unknown"
        _check_rate_limit(client_ip)

        # Body size check (only for requests with a body)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large."},
            )

        response: Response = await call_next(request)
        return response
