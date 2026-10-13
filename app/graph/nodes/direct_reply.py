from __future__ import annotations

from typing import Any

from app.domain.deltas import SynthesizeDelta
from app.domain.state import GraphState, Route
from app.graph.adapters import apply_delta


async def direct_reply(state: GraphState) -> dict[str, Any]:
    """
    Handles CHITCHAT and REFUSE routes without using RAG or SQL.
    Returns a fast, static reply.
    """
    route = state.decision.route if state.decision else None

    if route == Route.CHITCHAT:
        reply = "Hello! I am your internal company data assistant. How can I help you today?"
    elif route == Route.REFUSE:
        reply = "I am an internal data assistant. I am only authorized to answer questions regarding our company databases and internal documents."
    else:
        reply = "I am unable to process that request."

    return apply_delta(SynthesizeDelta(final_answer=reply))
