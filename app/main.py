"""
FastAPI Application Entry Point
Wires up middleware, exception handlers, routers, and lifespan events.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import chat, documents
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import SecurityMiddleware
from app.exceptions import (
    BaseAppException,
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
    request_validation_handler,
)

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Application startup / shutdown lifecycle."""
    configure_logging()
    log.info(
        "startup",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        llm_provider=settings.LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        llm_model=settings.LLM_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    yield
    log.info("shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "A highly secure, zero-defect RAG and SQL assistant. "
        "Supports multiple LLM providers: Ollama, OpenAI, Anthropic, Groq, Google."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(SecurityMiddleware)

# Exception Handlers
app.add_exception_handler(BaseAppException, app_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, request_validation_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, global_exception_handler)

# Routers
app.include_router(chat.router)
app.include_router(documents.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Returns 200 OK with provider info if the API is running."""
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
    }
