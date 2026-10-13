"""
sql_generate node
Takes the user's question and uses the LLM SQL generation chain to produce a
draft PostgreSQL query. Uses the pre-built chain from llm/chains.py.
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import SqlGenerateDelta
from app.domain.state import GraphState, SqlDraft
from app.graph.adapters import apply_delta
from app.llm.chains import get_sql_generate_chain


async def sql_generate(state: GraphState) -> dict[str, Any]:
    """
    Takes the user's question and uses the LLM to generate a PostgreSQL draft.
    """
    chain = get_sql_generate_chain()
    question = (
        state.decision.database_subquestion
        if state.decision and state.decision.database_subquestion
        else state.question
    )

    raw_sql: str = await chain.ainvoke({"question": question})

    # Clean the SQL if the LLM added markdown fences despite instructions
    raw_sql = raw_sql.replace("```sql", "").replace("```", "").strip()

    draft = SqlDraft(
        sql=raw_sql,
        tables_used=(),  # Populated by schema introspection in a future pass
        assumptions=(),
    )

    return apply_delta(
        SqlGenerateDelta(
            sql_draft=draft,
            sql_attempts=state.sql_attempts + 1,
        )
    )
