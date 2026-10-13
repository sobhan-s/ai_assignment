"""
sql_repair node
Called when SQL validation or execution fails.
Asks the LLM to repair the query based on the error message.
Uses the pre-built chain from llm/chains.py (prompt lives in app/prompts/sql_repair.py).
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import SqlRepairDelta
from app.domain.state import GraphState, SqlDraft
from app.graph.adapters import apply_delta
from app.llm.chains import get_sql_repair_chain


async def sql_repair(state: GraphState) -> dict[str, Any]:
    """
    Called when SQL validation or execution fails.
    Asks the LLM to repair the query based on the error.
    """
    error = state.sql_last_error or (
        state.sql_validation.violations[0]
        if state.sql_validation and state.sql_validation.violations
        else "Unknown error"
    )
    old_sql = state.sql_draft.sql if state.sql_draft else ""

    chain = get_sql_repair_chain()
    new_sql: str = await chain.ainvoke({"sql": old_sql, "error": error})

    # Strip markdown code fences if the LLM added them despite instructions
    new_sql = new_sql.replace("```sql", "").replace("```", "").strip()

    draft = SqlDraft(
        sql=new_sql,
        tables_used=(),
        assumptions=(),
    )

    # Crucial: Increment sql_attempts so we eventually trip the circuit breaker!
    return apply_delta(
        SqlRepairDelta(
            sql_draft=draft,
            sql_attempts=state.sql_attempts + 1,
        )
    )
