"""
Integration test: read-only SQL role enforcement.

Verifies that the SQL validator blocks all DML statements and that only
SELECT queries can pass through the validation layer.
This mirrors what a read-only DB role would enforce at the database level.
"""

from __future__ import annotations

import pytest

from app.services.sql import SQLValidationService


@pytest.fixture
def validator() -> SQLValidationService:
    return SQLValidationService()


# Only SELECT queries are permitted by the validator (mimicking ro role)


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE orders",
        "DELETE FROM customers WHERE id = 1",
        "UPDATE orders SET total = 0 WHERE id = 1",
        "INSERT INTO orders (id, total) VALUES (999, 100)",
        "TRUNCATE TABLE refunds",
        "CREATE TABLE hacked (x TEXT)",
        "ALTER TABLE orders ADD COLUMN hack TEXT",
    ],
)
def test_write_statements_are_blocked(
    validator: SQLValidationService, sql: str
) -> None:
    """Every DML / DDL statement should be rejected by the validator."""
    result = validator.validate(sql)
    assert result.ok is False, f"Expected {sql!r} to be blocked"
    assert len(result.violations) > 0


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM orders",
        "SELECT id, total FROM customers LIMIT 10",
        "SELECT COUNT(*) FROM refunds",
        "SELECT o.id, i.product_id FROM orders o JOIN order_items i ON o.id = i.order_id",
    ],
)
def test_select_statements_are_allowed(
    validator: SQLValidationService, sql: str
) -> None:
    """Plain SELECT queries against allowed tables should pass validation."""
    result = validator.validate(sql)
    assert (
        result.ok is True
    ), f"Expected {sql!r} to be allowed. Violations: {result.violations}"


def test_blocked_function_is_rejected(validator: SQLValidationService) -> None:
    """pg_sleep and similar dangerous functions must be blocked."""
    result = validator.validate("SELECT pg_sleep(10)")
    assert result.ok is False
    assert any("blocked" in v for v in result.violations)


def test_information_schema_access_is_blocked(validator: SQLValidationService) -> None:
    """Queries targeting information_schema must be blocked."""
    result = validator.validate("SELECT * FROM information_schema.tables")
    assert result.ok is False


def test_pg_catalog_access_is_blocked(validator: SQLValidationService) -> None:
    result = validator.validate("SELECT * FROM pg_catalog.pg_class")
    assert result.ok is False
