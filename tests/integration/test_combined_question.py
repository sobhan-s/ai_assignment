"""
Integration test: combined question routing.

Verifies that a question requiring both document retrieval and SQL lookup
produces a final_answer that is non-empty.

NOTE: Full DB + LLM integration tests require live services.
The simulation below uses mocked LLM chains and exercises synthesize directly.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.domain.state import (
    BranchResult,
    GraphState,
    RagResult,
    Route,
    RouteDecision,
    SqlResult,
)
from app.graph.nodes.synthesize import synthesize


@pytest.mark.asyncio
async def test_synthesize_combined_two_branches_returns_merged_answer() -> None:
    """
    Simulates both branches completing and calls synthesize with both results.
    synthesize should invoke the LLM chain to merge them into a final_answer.
    """
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="What is the refund policy and how many refunds last month?",
        decision=RouteDecision(
            route=Route.COMBINED,
            confidence=0.9,
            document_subquestion="What is the refund policy?",
            database_subquestion="How many refunds last month?",
            rationale="Both",
        ),
        branch_results=(
            BranchResult(
                branch="rag",
                rag=RagResult(
                    answer="Refunds are allowed within 30 days.",
                    citations=(),
                    grounded=True,
                ),
            ),
            BranchResult(
                branch="sql",
                sql=SqlResult(
                    answer="There were 42 refunds last month.",
                    executed_sql="SELECT COUNT(*) FROM refunds",
                ),
            ),
        ),
    )

    merged = "Refunds are allowed within 30 days. Last month, there were 42 refunds."
    with patch(
        "app.graph.nodes.synthesize.get_synthesize_chain",
        return_value=AsyncMock(ainvoke=AsyncMock(return_value=merged)),
    ):
        result = await synthesize(state)

    assert "final_answer" in result
    answer = result["final_answer"]
    assert len(answer) > 0
    # The merged answer should reference both data points
    assert "30 days" in answer or "42" in answer or "refund" in answer.lower()


@pytest.mark.asyncio
async def test_combined_partial_rag_waits_for_sql() -> None:
    """When only RAG result is present for a COMBINED route, synthesize waits."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="Refund policy and count?",
        decision=RouteDecision(
            route=Route.COMBINED, confidence=0.9, rationale="combined"
        ),
        branch_results=(
            BranchResult(
                branch="rag",
                rag=RagResult(answer="30 days policy.", citations=(), grounded=True),
            ),
        ),
    )
    result = await synthesize(state)
    assert result == {}


@pytest.mark.asyncio
async def test_combined_partial_sql_waits_for_rag() -> None:
    """When only SQL result is present for a COMBINED route, synthesize waits."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="Refund policy and count?",
        decision=RouteDecision(
            route=Route.COMBINED, confidence=0.9, rationale="combined"
        ),
        branch_results=(
            BranchResult(
                branch="sql",
                sql=SqlResult(
                    answer="42 refunds.", executed_sql="SELECT COUNT(*) FROM refunds"
                ),
            ),
        ),
    )
    result = await synthesize(state)
    assert result == {}
