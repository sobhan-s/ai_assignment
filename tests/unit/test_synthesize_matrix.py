"""
Matrix tests for the synthesize node covering all partial-failure combinations:
  - 0 branch results (fallback)
  - 1 RAG only result
  - 1 SQL only result
  - Both results present
  - Node failures present (hard failure path)
  - final_answer already set for non-combined routes
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.state import (
    BranchResult,
    FailureKind,
    GraphState,
    NodeFailure,
    RagResult,
    Route,
    RouteDecision,
    SqlResult,
)
from app.graph.nodes.synthesize import synthesize


def _make_state(**kwargs) -> GraphState:
    return GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test question",
        **kwargs,
    )


@pytest.mark.asyncio
async def test_combined_waits_when_only_rag_present() -> None:
    """COMBINED with 1/2 branches → empty dict (wait signal)."""
    state = _make_state(
        decision=RouteDecision(route=Route.COMBINED, confidence=1.0, rationale="r"),
        branch_results=(
            BranchResult(
                branch="rag",
                rag=RagResult(answer="rag answer", citations=(), grounded=True),
            ),
        ),
    )
    result = await synthesize(state)
    assert result == {}


@pytest.mark.asyncio
async def test_combined_waits_when_only_sql_present() -> None:
    """COMBINED with 1/2 branches (sql only) → empty dict."""
    state = _make_state(
        decision=RouteDecision(route=Route.COMBINED, confidence=1.0, rationale="r"),
        branch_results=(
            BranchResult(
                branch="sql",
                sql=SqlResult(answer="sql answer", executed_sql="SELECT 1"),
            ),
        ),
    )
    result = await synthesize(state)
    assert result == {}


@pytest.mark.asyncio
async def test_combined_waits_when_no_results() -> None:
    """COMBINED with 0 branches → empty dict."""
    state = _make_state(
        decision=RouteDecision(route=Route.COMBINED, confidence=1.0, rationale="r"),
    )
    result = await synthesize(state)
    assert result == {}


# Single-branch routes   pass-through


@pytest.mark.asyncio
async def test_rag_only_result_passes_through() -> None:
    """RAG-only branch result should populate final_answer."""
    state = _make_state(
        decision=RouteDecision(route=Route.DOCUMENTS, confidence=0.9, rationale="r"),
        branch_results=(
            BranchResult(
                branch="rag",
                rag=RagResult(answer="RAG answer text", citations=(), grounded=True),
            ),
        ),
    )
    result = await synthesize(state)
    assert "final_answer" in result
    assert "RAG answer text" in result["final_answer"]


@pytest.mark.asyncio
async def test_sql_only_result_passes_through() -> None:
    """SQL-only branch result should populate final_answer."""
    state = _make_state(
        decision=RouteDecision(route=Route.DATABASE, confidence=0.9, rationale="r"),
        branch_results=(
            BranchResult(
                branch="sql",
                sql=SqlResult(answer="SQL answer text", executed_sql="SELECT 1"),
            ),
        ),
    )
    result = await synthesize(state)
    assert "final_answer" in result
    assert "SQL answer text" in result["final_answer"]


# Hard failure path


@pytest.mark.asyncio
async def test_node_failure_overrides_answer() -> None:
    """When failures are present, synthesize should emit a failure message."""
    failure = NodeFailure(
        node="sql_execute", kind=FailureKind.EXECUTION, detail="column not found"
    )
    state = _make_state(failures=(failure,))
    result = await synthesize(state)
    assert "final_answer" in result
    # The failure node name and detail should appear in the answer
    assert (
        "sql_execute" in result["final_answer"]
        or "column not found" in result["final_answer"]
    )


@pytest.mark.asyncio
async def test_multiple_failures_all_reported() -> None:
    failures = (
        NodeFailure(
            node="rag_retrieve", kind=FailureKind.RETRIEVAL, detail="qdrant timeout"
        ),
        NodeFailure(
            node="sql_execute", kind=FailureKind.EXECUTION, detail="bad column"
        ),
    )
    state = _make_state(failures=failures)
    result = await synthesize(state)
    assert "final_answer" in result
    answer = result["final_answer"]
    assert "rag_retrieve" in answer or "qdrant timeout" in answer


# No branch results   fallback


@pytest.mark.asyncio
async def test_no_branches_fallback_message() -> None:
    """With no branch results and no failures, a fallback message is returned."""
    state = _make_state(
        decision=RouteDecision(route=Route.DOCUMENTS, confidence=0.9, rationale="r"),
    )
    result = await synthesize(state)
    assert "final_answer" in result
    assert result["final_answer"]  # non-empty


# final_answer already set (non-combined short-circuit)


@pytest.mark.asyncio
async def test_final_answer_already_set_returns_empty() -> None:
    """If a node (e.g., circuit_breaker) already set final_answer, synthesize is a no-op."""
    state = _make_state(
        decision=RouteDecision(route=Route.DATABASE, confidence=1.0, rationale="r"),
        final_answer="Pre-set answer from circuit_breaker.",
    )
    result = await synthesize(state)
    # Should be empty dict   state already has an answer
    assert result == {}
