"""
Tests that GraphState and all Frozen domain models are truly immutable.
Also verifies field-level validation rules (e.g., sql_attempts range).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.state import (
    MAX_SQL_ATTEMPTS,
    ChatMessage,
    Citation,
    GraphState,
    Role,
    Route,
    RouteDecision,
    SqlDraft,
)

# GraphState field forbids extra attributes


def test_graph_state_rejects_extra_fields() -> None:
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    with pytest.raises((ValueError, ValidationError)):
        state.new_field = 123  # type: ignore[attr-defined]


def test_graph_state_creation_with_extra_key_raises() -> None:
    with pytest.raises(ValidationError):
        GraphState(  # type: ignore[call-arg]
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            unknown_field="boom",
        )


# Frozen base-class models are immutable


def test_frozen_chat_message_rejects_mutation() -> None:
    msg = ChatMessage(
        role=Role.USER,
        content="Hello!",
        at=datetime.now(tz=UTC),
    )
    with pytest.raises((TypeError, ValidationError)):
        msg.content = "Mutated!"  # type: ignore[misc]


def test_frozen_route_decision_rejects_mutation() -> None:
    decision = RouteDecision(route=Route.DATABASE, confidence=0.9, rationale="r")
    with pytest.raises((TypeError, ValidationError)):
        decision.route = Route.DOCUMENTS  # type: ignore[misc]


def test_frozen_sql_draft_rejects_mutation() -> None:
    draft = SqlDraft(sql="SELECT 1", tables_used=("orders",))
    with pytest.raises((TypeError, ValidationError)):
        draft.sql = "DROP TABLE orders"  # type: ignore[misc]


def test_frozen_citation_rejects_mutation(sample_citation: Citation) -> None:
    with pytest.raises((TypeError, ValidationError)):
        sample_citation.filename = "evil.pdf"  # type: ignore[misc]


# Field-level validation constraints


def test_sql_attempts_cannot_exceed_max() -> None:
    with pytest.raises(ValidationError):
        GraphState(
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            sql_attempts=MAX_SQL_ATTEMPTS + 1,
        )


def test_sql_attempts_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        GraphState(
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            sql_attempts=-1,
        )


def test_chat_message_content_min_length() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(
            role=Role.USER,
            content="",  # min_length=1
            at=datetime.now(tz=UTC),
        )


def test_chat_message_content_max_length() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(
            role=Role.USER,
            content="x" * 8001,  # max_length=8000
            at=datetime.now(tz=UTC),
        )


def test_route_decision_confidence_min() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(route=Route.DATABASE, confidence=-0.1, rationale="r")


def test_route_decision_confidence_max() -> None:
    with pytest.raises(ValidationError):
        RouteDecision(route=Route.DATABASE, confidence=1.1, rationale="r")


# History reducer appends (immutable tuple semantics)


def test_graph_state_history_is_tuple() -> None:
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    assert isinstance(state.history, tuple)


def test_graph_state_history_default_empty() -> None:
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    assert state.history == ()


def test_graph_state_branch_results_default_empty() -> None:
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    assert state.branch_results == ()
    assert state.failures == ()
