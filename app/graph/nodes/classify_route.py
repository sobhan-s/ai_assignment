"""
classify_route node
Uses the LLM router chain to analyse the user's question and classify intent
into one of: documents, database, combined, chitchat, refuse.
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import ClassifyDelta
from app.domain.state import GraphState, RouteDecision
from app.graph.adapters import apply_delta
from app.llm.chains import get_router_chain


async def classify_route(state: GraphState) -> dict[str, Any]:
    """
    Uses the LLM to analyze the user's question and classify the intent.
    """
    question = state.standalone_question or state.question

    chain = get_router_chain()
    decision: RouteDecision = await chain.ainvoke({"question": question})

    return apply_delta(ClassifyDelta(decision=decision))
