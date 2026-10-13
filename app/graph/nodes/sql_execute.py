"""
sql_execute node
Executes the AST-validated SQL query against the read-only Postgres connection.
Uses SqlExecutor (from app.sql.executor) which owns all connection/timeout logic.

On success  → SqlExecutionSuccessDelta (routes to sql_answer)
On failure  → SqlExecuteFailDelta       (routes to sql_repair or circuit_breaker)
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import (
    NodeFailureDelta,
    SqlExecuteFailDelta,
    SqlExecutionSuccessDelta,
)
from app.domain.state import FailureKind, GraphState, NodeFailure
from app.graph.adapters import apply_delta
from app.services import default_sql_execution_service


async def sql_execute(state: GraphState) -> dict[str, Any]:
    """
    Executes the strictly validated SQL string against the Postgres database.
    """
    if not state.sql_validation or not state.sql_validation.ok:
        fail = NodeFailure(
            node="sql_execute",
            kind=FailureKind.EXECUTION,
            detail="Cannot execute invalid SQL.",
        )
        return apply_delta(NodeFailureDelta(failures=(fail,)))

    sql_to_run = state.sql_validation.normalized_sql
    assert sql_to_run is not None  # guaranteed by SqlValidation.ok=True

    try:
        # SQLExecutionService owns all connection / timeout / row-cap logic
        execution = await default_sql_execution_service.execute_query(sql_to_run)
        return apply_delta(SqlExecutionSuccessDelta(sql_execution=execution))

    except Exception as exc:
        # Postgres rejected the query (column doesn't exist, type mismatch, etc.)
        # We store the error in state so route_after_execute can send it to sql_repair.
        return apply_delta(SqlExecuteFailDelta(sql_last_error=str(exc)))
