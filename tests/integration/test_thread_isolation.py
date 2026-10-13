"""
Integration test: thread isolation.

Verifies that GraphState instances for different thread_ids are independent.
Two concurrent states must not share mutable data, especially the
append-only reducers (history, branch_results, failures).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.state import (
    BranchResult,
    ChatMessage,
    FailureKind,
    GraphState,
    NodeFailure,
    RagResult,
    Role,
)


def _make_state(**kwargs) -> GraphState:
    base = dict(thread_id=uuid4(), request_id=uuid4(), question="test")
    base.update(kwargs)
    return GraphState(**base)


def test_different_thread_ids_are_unique() -> None:
    state_a = _make_state()
    state_b = _make_state()
    assert state_a.thread_id != state_b.thread_id
    assert state_a.request_id != state_b.request_id


def test_branch_results_not_shared_between_states() -> None:
    """Tuples are value types   two states must not reference the same branch_results."""
    branch = BranchResult(
        branch="rag",
        rag=RagResult(answer="answer", citations=(), grounded=True),
    )
    state_a = _make_state(branch_results=(branch,))
    state_b = _make_state()

    assert len(state_a.branch_results) == 1
    assert len(state_b.branch_results) == 0  # state_b is untouched


def test_failures_not_shared_between_states() -> None:
    failure = NodeFailure(
        node="sql_execute",
        kind=FailureKind.EXECUTION,
        detail="column not found",
    )
    state_a = _make_state(failures=(failure,))
    state_b = _make_state()

    assert len(state_a.failures) == 1
    assert len(state_b.failures) == 0


def test_question_isolated_per_state() -> None:
    state_a = _make_state(question="Revenue last month?")
    state_b = _make_state(question="What is our refund policy?")
    assert state_a.question != state_b.question


def test_sql_attempts_isolated_per_state() -> None:
    state_a = _make_state(sql_attempts=2)
    state_b = _make_state(sql_attempts=0)
    assert state_a.sql_attempts == 2
    assert state_b.sql_attempts == 0


def test_history_isolated_per_state() -> None:
    msg = ChatMessage(
        role=Role.USER,
        content="Hello",
        at=datetime.now(tz=UTC),
    )
    state_a = _make_state(history=(msg,))
    state_b = _make_state()
    assert len(state_a.history) == 1
    assert len(state_b.history) == 0


def test_final_answer_isolated_per_state() -> None:
    state_a = _make_state(final_answer="Done.")
    state_b = _make_state()
    assert state_a.final_answer == "Done."
    assert state_b.final_answer is None
