"""
sql_answer node
Takes the raw rows from the Postgres database and uses the LLM summarize chain
to format them into a human-readable answer.
Prompt lives in app/prompts/sql_summarize.py, chain in llm/chains.py.
"""

from __future__ import annotations

from typing import Any

from app.domain.deltas import BranchResultDelta
from app.domain.state import BranchResult, GraphState, SqlResult
from app.graph.adapters import apply_delta
from app.llm.chains import get_sql_summarize_chain


async def sql_answer(state: GraphState) -> dict[str, Any]:
    """
    Takes the raw rows from the Postgres database and formats them into
    a human-readable answer via the LLM.
    """
    # If execution failed or wasn't provided, return a fallback
    if not state.sql_execution:
        res = SqlResult(
            answer="SQL execution failed or no data was retrieved.",
            executed_sql=(
                state.sql_validation.normalized_sql if state.sql_validation else ""
            )
            or "",
            execution=None,
        )
        return apply_delta(
            BranchResultDelta(branch_results=(BranchResult(branch="sql", sql=res),))
        )

    execution = state.sql_execution
    question = (
        state.decision.database_subquestion
        if state.decision and state.decision.database_subquestion
        else state.question
    )

    chain = get_sql_summarize_chain()

    # Only send a capped sample of rows to the LLM to avoid context limits
    answer: str = await chain.ainvoke(
        {
            "columns": str(execution.columns),
            "rows": str(execution.rows[:10]),  # First 10 rows only
            "question": question,
        }
    )

    res = SqlResult(
        answer=answer,
        executed_sql=(
            state.sql_validation.normalized_sql if state.sql_validation else ""
        )
        or "",
        execution=execution,
    )

    return apply_delta(
        BranchResultDelta(branch_results=(BranchResult(branch="sql", sql=res),))
    )
