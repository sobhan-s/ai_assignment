"""
Deterministic graph routing tests using GenericFakeChatModel.
Verifies that all routing functions produce the correct node names
without making any actual LLM calls.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.state import GraphState, Route, RouteDecision, SqlValidation
from app.graph.routers import (
    route_after_classify,
    route_after_execute,
    route_after_validate,
)

# route_after_classify


@pytest.mark.parametrize(
    "route, expected",
    [
        (Route.DOCUMENTS, "rag_retrieve"),
        (Route.DATABASE, "sql_generate"),
        (Route.CHITCHAT, "direct_reply"),
        (Route.REFUSE, "refuse"),
    ],
)
def test_single_branch_routes(route: Route, expected: str) -> None:
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        decision=RouteDecision(route=route, confidence=1.0, rationale="test"),
    )
    result = route_after_classify(state)
    assert result == expected


def test_combined_route_produces_two_sends() -> None:
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        decision=RouteDecision(route=Route.COMBINED, confidence=1.0, rationale="test"),
    )
    result = route_after_classify(state)
    assert isinstance(result, list)
    assert len(result) == 2
    nodes = {s.node for s in result}
    assert nodes == {"rag_retrieve", "sql_generate"}


def test_missing_decision_routes_to_refuse() -> None:
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    assert route_after_classify(state) == "refuse"


# route_after_validate


@pytest.mark.parametrize(
    "ok, attempts, expected",
    [
        (True, 0, "sql_execute"),
        (True, 2, "sql_execute"),
        (True, 3, "sql_execute"),
        (False, 0, "sql_repair"),
        (False, 1, "sql_repair"),
        (False, 2, "sql_repair"),
        (False, 3, "circuit_breaker"),
    ],
)
def test_route_after_validate_matrix(ok: bool, attempts: int, expected: str) -> None:
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_validation=SqlValidation(ok=ok, violations=() if ok else ("error",)),
        sql_attempts=attempts,
    )
    assert route_after_validate(state) == expected


# route_after_execute


@pytest.mark.parametrize(
    "error, attempts, expected",
    [
        (None, 1, "sql_answer"),
        (None, 3, "sql_answer"),
        ("column missing", 1, "sql_repair"),
        ("column missing", 2, "sql_repair"),
        ("column missing", 3, "circuit_breaker"),
    ],
)
def test_route_after_execute_matrix(
    error: str | None, attempts: int, expected: str
) -> None:
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_last_error=error,
        sql_attempts=attempts,
    )
    assert route_after_execute(state) == expected
