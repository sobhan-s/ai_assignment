from __future__ import annotations

import operator
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Route(StrEnum):
    DOCUMENTS = "documents"
    DATABASE = "database"
    COMBINED = "combined"
    CHITCHAT = "chitchat"
    REFUSE = "refuse"


class Outcome(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    NO_EVIDENCE = "no_evidence"
    CIRCUIT_OPEN = "circuit_open"
    UNSAFE = "unsafe"
    INTERNAL_ERROR = "internal_error"


class FailureKind(StrEnum):
    VALIDATION = "sql_validation"
    EXECUTION = "sql_execution"
    GENERATION = "generation"
    RETRIEVAL = "retrieval"
    TIMEOUT = "timeout"


# ---- Messages & conversation ----
class ChatMessage(Frozen):
    role: Role
    content: str = Field(min_length=1, max_length=8_000)
    at: datetime


# ---- LLM structured outputs ----
class RouteDecision(Frozen):
    route: Route
    confidence: float = Field(ge=0.0, le=1.0)
    document_subquestion: str | None = None
    database_subquestion: str | None = None
    rationale: str = Field(max_length=300)


class CondensedQuestion(Frozen):
    standalone_question: str = Field(min_length=1, max_length=1_000)


class SqlDraft(Frozen):
    sql: str = Field(min_length=1, max_length=4_000)
    tables_used: tuple[str, ...]
    assumptions: tuple[str, ...] = ()


# ---- RAG ----
class Citation(Frozen):
    document_id: UUID
    filename: str
    page: int | None = None
    chunk_index: int
    score: float
    snippet: str = Field(max_length=400)


class RetrievedChunk(Frozen):
    citation: Citation
    text: str


class RagResult(Frozen):
    answer: str
    citations: tuple[Citation, ...]
    grounded: bool


# ---- SQL ----
class SqlValidation(Frozen):
    ok: bool
    normalized_sql: str | None = None
    violations: tuple[str, ...] = ()


# Using a type alias for cell values
CellValue = str | int | float | bool | None | datetime | date | Decimal


class SqlExecution(Frozen):
    columns: tuple[str, ...]
    rows: tuple[tuple[CellValue, ...], ...]
    row_count: int
    truncated: bool
    elapsed_ms: int


class SqlResult(Frozen):
    answer: str
    executed_sql: str
    execution: SqlExecution | None = None


# ---- Errors ----
class NodeFailure(Frozen):
    node: str
    kind: FailureKind
    detail: str = Field(max_length=500)


class BranchResult(Frozen):
    branch: Literal["rag", "sql"]
    rag: RagResult | None = None
    sql: SqlResult | None = None
    failure: NodeFailure | None = None


# ---- Global graph state ----
MAX_SQL_ATTEMPTS = 3
MAX_GENERATION_ATTEMPTS = 2


class GraphState(BaseModel):
    """Nodes NEVER mutate this directly; they return a Delta mapping."""

    model_config = ConfigDict(extra="forbid")

    # identity
    thread_id: UUID
    request_id: UUID

    # conversation (append-only reducer)
    history: Annotated[tuple[ChatMessage, ...], operator.add] = ()
    question: str
    standalone_question: str | None = None

    # routing
    decision: RouteDecision | None = None

    # RAG branch
    retrieved: tuple[RetrievedChunk, ...] = ()

    # SQL branch
    sql_draft: SqlDraft | None = None
    sql_validation: SqlValidation | None = None
    sql_execution: SqlExecution | None = None
    sql_attempts: int = Field(default=0, ge=0, le=MAX_SQL_ATTEMPTS)
    sql_last_error: str | None = None

    # fan-in (append-only)
    branch_results: Annotated[tuple[BranchResult, ...], operator.add] = ()
    failures: Annotated[tuple[NodeFailure, ...], operator.add] = ()

    # terminal
    outcome: Outcome | None = None
    final_answer: str | None = None
    final_citations: tuple[Citation, ...] = ()
    executed_sql: str | None = None
