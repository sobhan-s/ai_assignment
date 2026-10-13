"""
API Schemas (DTOs)
Pydantic models for all HTTP request/response bodies.
Domain models (Citation, Route, Outcome) are re-exported from domain/state.py.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.state import Citation, Outcome, Route


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4_000,
        description="The user's question.",
    )
    thread_id: UUID = Field(
        default_factory=uuid4,
        description="Session ID for conversation history.",
    )


class ChatResponse(BaseModel):
    """Successful chat response."""

    request_id: UUID
    thread_id: UUID
    answer: str
    route: Route | None = None
    outcome: Outcome | None = None
    citations: list[Citation] = Field(default_factory=list)
    executed_sql: str | None = None


class IngestResponse(BaseModel):
    """Returned after a successful document ingestion."""

    filename: str
    status: str = "success"
    chunks_indexed: int
