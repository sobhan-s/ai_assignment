"""
Structured JSON Logging
Configures structlog for JSON-formatted structured logging with request_id binding.
Use `get_logger()` in every module instead of the stdlib `logging` module.
"""

from __future__ import annotations

import logging
import sys
import typing

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """
    Call once at application startup (in main.py lifespan).
    Sets up structlog with JSON rendering and stdlib integration.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Returns a structlog bound logger. Prefer this over logging.getLogger()."""
    return typing.cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def bind_request_id(request_id: str) -> None:
    """Binds a request_id to the current async context for log correlation."""
    structlog.contextvars.bind_contextvars(request_id=request_id)


def clear_request_context() -> None:
    """Clears the async context after a request completes."""
    structlog.contextvars.clear_contextvars()
