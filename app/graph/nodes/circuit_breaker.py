from __future__ import annotations

from typing import Any

from app.domain.deltas import SynthesizeDelta
from app.domain.state import GraphState
from app.graph.adapters import apply_delta


async def circuit_breaker(state: GraphState) -> dict[str, Any]:
    """
    Trips when an AI repair loop fails too many times.
    Gracefully handles the failure without crashing the server.
    """
    msg = "I'm sorry, I was unable to generate a valid SQL query to answer your question after several attempts. Please rephrase your question."

    return apply_delta(SynthesizeDelta(final_answer=msg))
