from __future__ import annotations

from typing import Any

from app.domain.state import Frozen


def apply_delta(delta: Frozen) -> dict[str, Any]:
    """
    The ONLY place in the entire codebase where a dictionary is allowed.
    Converts a strictly typed Pydantic Delta model into a dictionary
    so LangGraph can apply it to the State.
    """
    # exclude_unset ensures we don't overwrite state fields with None accidentally
    return delta.model_dump(exclude_unset=True)
