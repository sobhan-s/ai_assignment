"""
Tests for the SQL repair loop:
- sql_repair node increments sql_attempts
- sql_repair node replaces sql_draft with a new draft
- sql_repair correctly picks up error from sql_last_error or sql_validation.violations
- apply_delta returns the expected keys
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.domain.state import GraphState, SqlDraft, SqlValidation
from app.graph.nodes.sql_repair import sql_repair
from app.graph.nodes.sql_validate import sql_validate

# sql_repair node


@pytest.mark.asyncio
async def test_sql_repair_increments_sql_attempts() -> None:
    """sql_repair must increment sql_attempts by 1."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=SqlDraft(sql="SELECT bad_col FROM orders", tables_used=("orders",)),
        sql_validation=SqlValidation(
            ok=False, violations=("column bad_col does not exist",)
        ),
        sql_attempts=1,
    )

    repaired_sql = "SELECT id FROM orders LIMIT 500"
    with patch(
        "app.graph.nodes.sql_repair.get_sql_repair_chain",
        return_value=AsyncMock(ainvoke=AsyncMock(return_value=repaired_sql)),
    ):
        result = await sql_repair(state)

    assert result.get("sql_attempts") == 2


@pytest.mark.asyncio
async def test_sql_repair_replaces_sql_draft() -> None:
    """sql_repair must produce a new sql_draft."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=SqlDraft(sql="SELECT bad FROM orders", tables_used=("orders",)),
        sql_validation=SqlValidation(
            ok=False, violations=("column bad does not exist",)
        ),
        sql_attempts=1,
    )

    repaired_sql = "SELECT id, total FROM orders LIMIT 500"
    with patch(
        "app.graph.nodes.sql_repair.get_sql_repair_chain",
        return_value=AsyncMock(ainvoke=AsyncMock(return_value=repaired_sql)),
    ):
        result = await sql_repair(state)

    assert "sql_draft" in result
    # apply_delta uses model_dump(), so sql_draft is a dict
    draft = result["sql_draft"]
    sql_text = draft.sql if hasattr(draft, "sql") else draft["sql"]
    assert sql_text == repaired_sql


@pytest.mark.asyncio
async def test_sql_repair_strips_markdown_fences() -> None:
    """sql_repair must strip ```sql fences if the LLM adds them."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=SqlDraft(sql="bad", tables_used=()),
        sql_validation=SqlValidation(ok=False, violations=("error",)),
        sql_attempts=1,
    )

    raw_with_fences = "```sql\nSELECT id FROM orders\n```"
    with patch(
        "app.graph.nodes.sql_repair.get_sql_repair_chain",
        return_value=AsyncMock(ainvoke=AsyncMock(return_value=raw_with_fences)),
    ):
        result = await sql_repair(state)

    draft = result["sql_draft"]
    sql_text = draft.sql if hasattr(draft, "sql") else draft["sql"]
    assert "```" not in sql_text


@pytest.mark.asyncio
async def test_sql_repair_uses_sql_last_error_if_present() -> None:
    """sql_repair should prefer sql_last_error over validation violations."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=SqlDraft(sql="SELECT * FROM orders", tables_used=("orders",)),
        sql_validation=SqlValidation(ok=False, violations=("validation violation",)),
        sql_last_error="DB execution error: relation does not exist",
        sql_attempts=1,
    )

    captured_invocation = {}

    async def capture_invoke(inputs: dict) -> str:
        captured_invocation.update(inputs)
        return "SELECT id FROM orders LIMIT 500"

    with patch(
        "app.graph.nodes.sql_repair.get_sql_repair_chain",
        return_value=AsyncMock(ainvoke=AsyncMock(side_effect=capture_invoke)),
    ):
        await sql_repair(state)

    # The error passed to the chain should be the sql_last_error
    assert "DB execution error" in captured_invocation.get("error", "")


# sql_validate node


@pytest.mark.asyncio
async def test_sql_validate_no_draft_returns_failure() -> None:
    """If state has no sql_draft, validation returns ok=False."""
    state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
    result = await sql_validate(state)
    assert "sql_validation" in result
    # apply_delta returns model_dump() so sql_validation may be a dict or model instance
    val = result["sql_validation"]
    ok = val.ok if hasattr(val, "ok") else val["ok"]
    assert ok is False


@pytest.mark.asyncio
async def test_sql_validate_with_valid_draft_returns_ok() -> None:
    """A valid SQL draft should produce ok=True."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=SqlDraft(sql="SELECT * FROM orders", tables_used=("orders",)),
    )
    result = await sql_validate(state)
    val = result["sql_validation"]
    ok = val.ok if hasattr(val, "ok") else val["ok"]
    assert ok is True


@pytest.mark.asyncio
async def test_sql_validate_with_blocked_sql_returns_failure() -> None:
    """A DROP statement should produce ok=False."""
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_draft=SqlDraft(sql="DROP TABLE orders", tables_used=("orders",)),
    )
    result = await sql_validate(state)
    val = result["sql_validation"]
    ok = val.ok if hasattr(val, "ok") else val["ok"]
    violations = val.violations if hasattr(val, "violations") else val["violations"]
    assert ok is False
    assert len(violations) > 0
