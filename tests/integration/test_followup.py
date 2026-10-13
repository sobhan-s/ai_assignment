"""
Integration test: rag_answer node produces a no-evidence reply when retrieved is empty.
Tests the no-evidence path that skips the LLM call entirely.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.state import Citation, GraphState, RetrievedChunk, Route, RouteDecision
from app.graph.nodes.rag_answer import rag_answer


@pytest.mark.asyncio
async def test_rag_answer_no_chunks_returns_no_evidence() -> None:
    """When no chunks are retrieved, rag_answer should skip LLM and return a fallback."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="What is the leave policy for part-time employees?",
        decision=RouteDecision(
            route=Route.DOCUMENTS,
            confidence=0.85,
            document_subquestion="Leave policy part-time?",
            rationale="doc",
        ),
        retrieved=(),
    )
    result = await rag_answer(state)
    assert "branch_results" in result
    branch = result["branch_results"][0]
    # apply_delta uses model_dump()   branch may be a BranchResult or a dict
    if hasattr(branch, "branch"):
        assert branch.branch == "rag"
        assert branch.rag is not None
        assert branch.rag.grounded is False
        assert len(branch.rag.answer) > 0
    else:
        assert branch["branch"] == "rag"
        rag = branch["rag"]
        assert rag["grounded"] is False
        assert len(rag["answer"]) > 0


@pytest.mark.asyncio
async def test_rag_answer_with_chunks_marks_grounded() -> None:
    """When chunks are present, rag_answer should call LLM and mark grounded=True."""
    from unittest.mock import AsyncMock, patch

    citation = Citation(
        document_id=uuid4(),
        filename="leave.pdf",
        page=1,
        chunk_index=0,
        score=0.9,
        snippet="Part-time employees get 10 days annual leave.",
    )
    chunk = RetrievedChunk(
        citation=citation,
        text="Part-time employees get 10 days annual leave per year.",
    )
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="What is the leave policy for part-time employees?",
        decision=RouteDecision(
            route=Route.DOCUMENTS,
            confidence=0.9,
            document_subquestion="Leave policy part-time?",
            rationale="doc",
        ),
        retrieved=(chunk,),
    )

    with patch(
        "app.graph.nodes.rag_answer.get_rag_answer_chain",
        return_value=AsyncMock(
            ainvoke=AsyncMock(return_value="Part-time employees receive 10 days.")
        ),
    ):
        result = await rag_answer(state)

    branch = result["branch_results"][0]
    # apply_delta uses model_dump()   handle both dict and model access patterns
    if hasattr(branch, "rag"):
        assert branch.rag is not None
        assert branch.rag.grounded is True
        assert "10 days" in branch.rag.answer
    else:
        rag = branch["rag"]
        assert rag["grounded"] is True
        assert "10 days" in rag["answer"]


@pytest.mark.asyncio
async def test_followup_rag_answer_uses_subquestion() -> None:
    """When decision has document_subquestion, rag_answer should use it."""
    from unittest.mock import AsyncMock, patch

    citation = Citation(
        document_id=uuid4(),
        filename="policy.pdf",
        page=1,
        chunk_index=0,
        score=0.88,
        snippet="Part-time employees get 10 days.",
    )
    chunk = RetrievedChunk(citation=citation, text="Part-time employees get 10 days.")

    captured = {}

    async def capture_invoke(inputs: dict) -> str:
        captured.update(inputs)
        return "10 days for part-time."

    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="leave policy?",
        decision=RouteDecision(
            route=Route.DOCUMENTS,
            confidence=0.9,
            document_subquestion="Leave policy for part-time employees?",
            rationale="doc",
        ),
        retrieved=(chunk,),
    )

    with patch(
        "app.graph.nodes.rag_answer.get_rag_answer_chain",
        return_value=AsyncMock(ainvoke=AsyncMock(side_effect=capture_invoke)),
    ):
        await rag_answer(state)

    # The subquestion should be passed to the chain, not the original question
    assert captured.get("question") == "Leave policy for part-time employees?"
