from __future__ import annotations

from typing import Any

from app.domain.deltas import SynthesizeDelta
from app.domain.state import GraphState
from app.graph.adapters import apply_delta


async def refuse(state: GraphState) -> dict[str, Any]:
    """
    The strict refusal node. Hardcodes the response to prevent general knowledge hallucination.
    """
    msg = "I am an internal data assistant. I am only authorized to answer questions regarding our company databases and policies. I cannot fulfill this request."

    return apply_delta(SynthesizeDelta(final_answer=msg))
