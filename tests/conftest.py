"""
Global test fixtures shared across unit, graph, integration, and api tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from langchain_core.language_models import FakeListChatModel
from langchain_core.messages import AIMessage

from app.domain.state import (
    BranchResult,
    ChatMessage,
    Citation,
    GraphState,
    RagResult,
    RetrievedChunk,
    Role,
    Route,
    RouteDecision,
    SqlDraft,
    SqlExecution,
    SqlResult,
)

# Fake LLM helpers


class GenericFakeChatModel(FakeListChatModel):
    """A FakeListChatModel that no-ops bind_tools / with_structured_output."""

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> Any:
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
        return self


@pytest.fixture
def fake_llm() -> GenericFakeChatModel:
    """Single-response fake LLM."""
    return GenericFakeChatModel(responses=[AIMessage(content="fake response")])


@pytest.fixture
def fake_llm_multi() -> GenericFakeChatModel:
    """Multi-response fake LLM   cycles through responses in order."""
    return GenericFakeChatModel(
        responses=[
            AIMessage(content="SELECT * FROM orders LIMIT 10"),
            AIMessage(content="SELECT * FROM customers LIMIT 10"),
            AIMessage(content="repaired query"),
        ]
    )


# Domain object factories


@pytest.fixture
def base_state() -> GraphState:
    """Minimal valid GraphState with no decisions made yet."""
    return GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="What is the total revenue last month?",
    )


@pytest.fixture
def state_with_db_route(base_state: GraphState) -> GraphState:
    return GraphState(
        thread_id=base_state.thread_id,
        request_id=base_state.request_id,
        question=base_state.question,
        decision=RouteDecision(
            route=Route.DATABASE,
            confidence=0.95,
            database_subquestion="What is the total revenue last month?",
            rationale="Requires SQL aggregation",
        ),
    )


@pytest.fixture
def state_with_rag_route(base_state: GraphState) -> GraphState:
    return GraphState(
        thread_id=base_state.thread_id,
        request_id=base_state.request_id,
        question="What is our refund policy?",
        decision=RouteDecision(
            route=Route.DOCUMENTS,
            confidence=0.9,
            document_subquestion="What is our refund policy?",
            rationale="Policy question answered from docs",
        ),
    )


@pytest.fixture
def state_with_combined_route(base_state: GraphState) -> GraphState:
    return GraphState(
        thread_id=base_state.thread_id,
        request_id=base_state.request_id,
        question="What is the refund policy and how many refunds last month?",
        decision=RouteDecision(
            route=Route.COMBINED,
            confidence=0.85,
            document_subquestion="What is the refund policy?",
            database_subquestion="How many refunds occurred last month?",
            rationale="Needs both doc and db",
        ),
    )


@pytest.fixture
def valid_sql_draft() -> SqlDraft:
    return SqlDraft(
        sql="SELECT * FROM orders LIMIT 10",
        tables_used=("orders",),
        assumptions=(),
    )


@pytest.fixture
def sample_citation() -> Citation:
    return Citation(
        document_id=uuid4(),
        filename="policy.pdf",
        page=1,
        chunk_index=0,
        score=0.92,
        snippet="Our refund policy allows returns within 30 days.",
    )


@pytest.fixture
def sample_retrieved_chunk(sample_citation: Citation) -> RetrievedChunk:
    return RetrievedChunk(
        citation=sample_citation,
        text="Our refund policy allows returns within 30 days of purchase.",
    )


@pytest.fixture
def sample_sql_execution() -> SqlExecution:
    return SqlExecution(
        columns=("id", "total"),
        rows=((1, 500), (2, 300)),
        row_count=2,
        truncated=False,
        elapsed_ms=42,
    )


@pytest.fixture
def rag_branch_result() -> BranchResult:
    return BranchResult(
        branch="rag",
        rag=RagResult(
            answer="Our refund policy allows 30 day returns.",
            citations=(),
            grounded=True,
        ),
    )


@pytest.fixture
def sql_branch_result() -> BranchResult:
    return BranchResult(
        branch="sql",
        sql=SqlResult(
            answer="There were 42 refunds last month.",
            executed_sql="SELECT COUNT(*) FROM refunds WHERE ...",
        ),
    )


@pytest.fixture
def sample_chat_message() -> ChatMessage:
    return ChatMessage(
        role=Role.USER,
        content="Hello!",
        at=datetime.now(tz=UTC),
    )
