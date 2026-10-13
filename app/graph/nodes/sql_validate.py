"""
sql_validate node
Passes the LLM's SQL draft through the deterministic SqlValidator.
Never calls an LLM   pure AST logic.
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import SqlValidateDelta
from app.domain.state import GraphState, SqlValidation
from app.graph.adapters import apply_delta
from app.services import default_sql_validation_service


async def sql_validate(state: GraphState) -> dict[str, Any]:
    """
    Takes the LLM's generated SQL draft and passes it through the AST validator.
    Never uses an LLM. Pure deterministic logic.
    """
    if not state.sql_draft:
        err_val = SqlValidation(ok=False, violations=("No SQL draft provided.",))
        return apply_delta(SqlValidateDelta(sql_validation=err_val))

    # SQLValidationService.validate() returns a SqlValidation directly
    val: SqlValidation = default_sql_validation_service.validate(state.sql_draft.sql)
    return apply_delta(SqlValidateDelta(sql_validation=val))
