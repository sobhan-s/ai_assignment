"""
Tests for the circuit_breaker graph node.
Verifies that:
  - The circuit breaker emits a graceful final_answer message
  - It does NOT raise exceptions
  - route_after_validate correctly trips the circuit at max attempts
  - route_after_execute correctly trips the circuit at max attempts
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.state import GraphState, SqlValidation
from app.graph.nodes.circuit_breaker import circuit_breaker
from app.graph.routers import route_after_execute, route_after_validate


@pytest.mark.asyncio
async def test_circuit_breaker_returns_final_answer() -> None:
    """circuit_breaker must set final_answer to a non-empty user-friendly string."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_attempts=3,
    )
    result = await circuit_breaker(state)
    assert "final_answer" in result
    answer = result["final_answer"]
    assert isinstance(answer, str)
    assert len(answer) > 0


@pytest.mark.asyncio
async def test_circuit_breaker_does_not_raise() -> None:
    """circuit_breaker must never raise an exception, even with an empty state."""
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    try:
        result = await circuit_breaker(state)
    except Exception as exc:
        pytest.fail(f"circuit_breaker raised an unexpected exception: {exc}")
    assert result is not None


@pytest.mark.asyncio
async def test_circuit_breaker_answer_mentions_rephrasing() -> None:
    """The graceful answer should guide the user to rephrase."""
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    result = await circuit_breaker(state)
    answer = result["final_answer"].lower()
    # The message should contain some indication the user should try differently
    assert any(kw in answer for kw in ["rephrase", "unable", "sorry", "attempt"])


@pytest.mark.asyncio
async def test_circuit_breaker_does_not_include_raw_sql() -> None:
    """The graceful answer should not leak raw SQL to the user."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=None,
    )
    result = await circuit_breaker(state)
    assert "SELECT" not in result["final_answer"]
    assert "DROP" not in result["final_answer"]


# circuit_breaker tripped via router (3 failed attempts simulation)


def test_route_after_validate_trips_at_attempt_3() -> None:
    """After 3 failed validation attempts, router must choose circuit_breaker."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_validation=SqlValidation(ok=False, violations=("blocked function",)),
        sql_attempts=3,
    )
    assert route_after_validate(state) == "circuit_breaker"


def test_route_after_validate_still_repairs_at_attempt_2() -> None:
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_validation=SqlValidation(ok=False, violations=("error",)),
        sql_attempts=2,
    )
    assert route_after_validate(state) == "sql_repair"


def test_route_after_execute_trips_at_attempt_3() -> None:
    """After 3 failed execution attempts, router must choose circuit_breaker."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_last_error="relation does not exist",
        sql_attempts=3,
    )
    assert route_after_execute(state) == "circuit_breaker"


def test_circuit_breaker_full_journey_three_failures() -> None:
    """
    Simulates 3 consecutive failures through the router:
    attempt 1 → sql_repair, attempt 2 → sql_repair, attempt 3 → circuit_breaker
    """

    def simulate_attempt(attempts: int) -> str:
        state = GraphState(
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            sql_validation=SqlValidation(ok=False, violations=("error",)),
            sql_attempts=attempts,
        )
        return route_after_validate(state)

    assert simulate_attempt(1) == "sql_repair"
    assert simulate_attempt(2) == "sql_repair"
    assert simulate_attempt(3) == "circuit_breaker"
