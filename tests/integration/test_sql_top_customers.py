"""
Integration test: SQL execution with a known seed   top customers query.

Full DB integration requires a live PostgreSQL instance seeded with test data.
The unit-level test below validates the execution service composition
using a mocked SQLRepository.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.state import SqlExecution
from app.services.sql import SQLExecutionService


@pytest.mark.asyncio
async def test_sql_execution_service_returns_execution_object() -> None:
    """SQLExecutionService.execute_query should return a SqlExecution model."""
    expected = SqlExecution(
        columns=("customer_id", "total_spent"),
        rows=((1, 5000), (2, 3200), (3, 2800)),
        row_count=3,
        truncated=False,
        elapsed_ms=15,
    )

    mock_repo = MagicMock()
    mock_repo.run_read_only = AsyncMock(return_value=expected)

    service = SQLExecutionService(sql_repo=mock_repo)
    result = await service.execute_query(
        "SELECT customer_id, SUM(total) FROM orders GROUP BY 1 LIMIT 3"
    )

    assert result.columns == ("customer_id", "total_spent")
    assert result.row_count == 3
    assert result.rows[0] == (1, 5000)


@pytest.mark.asyncio
async def test_sql_execution_service_propagates_db_error() -> None:
    """If the DB raises, execute_query should propagate the exception."""
    mock_repo = MagicMock()
    mock_repo.run_read_only = AsyncMock(side_effect=Exception("column not found"))

    service = SQLExecutionService(sql_repo=mock_repo)
    with pytest.raises(Exception, match="column not found"):
        await service.execute_query("SELECT bad_col FROM orders")


@pytest.mark.asyncio
async def test_execution_truncated_flag() -> None:
    """When the execution result is truncated, truncated=True must be set."""
    mock_execution = SqlExecution(
        columns=("id",),
        rows=tuple((i,) for i in range(500)),
        row_count=500,
        truncated=True,
        elapsed_ms=200,
    )

    mock_repo = MagicMock()
    mock_repo.run_read_only = AsyncMock(return_value=mock_execution)

    service = SQLExecutionService(sql_repo=mock_repo)
    result = await service.execute_query("SELECT id FROM orders LIMIT 500")

    assert result.truncated is True
    assert result.row_count == 500
