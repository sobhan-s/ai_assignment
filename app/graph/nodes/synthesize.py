"""
synthesize node
The terminal merge node. For COMBINED routes, calls the LLM to weave both
RAG and SQL answers together. For single-branch routes, it simply passes
the existing answer through.

Prompt lives in llm/prompts/synthesize.py, chain in llm/chains.py.
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import SynthesizeDelta
from app.domain.state import GraphState
from app.graph.adapters import apply_delta
from app.llm.chains import get_synthesize_chain


async def synthesize(state: GraphState) -> dict[str, Any]:
    """
    The final node. Merges RAG and SQL answers, or simply passes them through.
    For COMBINED routes, uses LLM synthesis to produce a coherent answer.
    """
    # Hard failure path   circuit breaker or node failures
    if state.failures:
        failure_msgs = [f"Failed at {f.node}: {f.detail}" for f in state.failures]
        return apply_delta(SynthesizeDelta(final_answer="\n".join(failure_msgs)))

    # If a previous terminal node already set the answer (e.g., refuse, circuit_breaker), keep it.
    if state.final_answer and state.decision and state.decision.route != "combined":
        return {}

    # Wait for BOTH branches if the route is COMBINED
    if state.decision and state.decision.route == "combined":
        if len(state.branch_results) < 2:
            # Not all branches have reported in yet; do nothing and wait for the next trigger.
            return {}

    # Collect branch results
    if state.branch_results:
        rag_answer_text: str | None = None
        sql_answer_text: str | None = None
        executed_sql: str | None = None

        for br in state.branch_results:
            if br.branch == "rag" and br.rag:
                rag_answer_text = br.rag.answer
            elif br.branch == "sql" and br.sql:
                sql_answer_text = br.sql.answer
                executed_sql = br.sql.executed_sql

        # COMBINED route   use LLM to merge both answers
        if rag_answer_text and sql_answer_text:
            chain = get_synthesize_chain()
            merged: str = await chain.ainvoke(
                {
                    "rag_answer": rag_answer_text,
                    "sql_answer": sql_answer_text,
                    "question": state.question,
                }
            )
            return apply_delta(
                SynthesizeDelta(final_answer=merged, executed_sql=executed_sql)
            )

        # Single-branch   pass through whichever answer exists
        final_text = rag_answer_text or sql_answer_text or "No data processed."
        return apply_delta(
            SynthesizeDelta(final_answer=final_text, executed_sql=executed_sql)
        )

    # Fallback if no branches were taken
    return apply_delta(SynthesizeDelta(final_answer="No data processed."))
