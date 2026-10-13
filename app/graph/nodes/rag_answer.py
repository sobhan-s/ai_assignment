"""
rag_answer node
Generates an answer grounded strictly in the retrieved document chunks.
Uses the pre-built chain from llm/chains.py (prompt in app/prompts/rag_answer.py).
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import BranchResultDelta
from app.domain.state import BranchResult, GraphState, RagResult
from app.graph.adapters import apply_delta
from app.llm.chains import get_rag_answer_chain


async def rag_answer(state: GraphState) -> dict[str, Any]:
    """
    Generates an answer based exclusively on the retrieved chunks.
    """
    if not state.retrieved:
        # No evidence found in vector DB   skip the LLM call entirely to save tokens
        res = RagResult(
            answer="I could not find any information regarding that in our internal documents.",
            citations=(),
            grounded=False,
        )
        branch = BranchResult(branch="rag", rag=res)
        return apply_delta(BranchResultDelta(branch_results=(branch,)))

    # Format the context strictly with chunk index and source attribution
    context_str = "\n\n".join(
        f"[Source: {c.citation.filename}]\n{c.text}" for c in state.retrieved
    )

    question = (
        state.decision.document_subquestion
        if state.decision and state.decision.document_subquestion
        else state.question
    )

    chain = get_rag_answer_chain()
    answer: str = await chain.ainvoke({"context": context_str, "question": question})

    # Extract citations used (one per retrieved chunk)
    used_citations = tuple(c.citation for c in state.retrieved)

    res = RagResult(
        answer=answer,
        citations=used_citations,
        grounded=True,
    )
    branch = BranchResult(branch="rag", rag=res)

    return apply_delta(BranchResultDelta(branch_results=(branch,)))
