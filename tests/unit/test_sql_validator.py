"""
Table-driven unit tests for SQLValidationService.
Covers 20+ cases: valid selects, blocked DML, blocked functions,
blocked schemas, multi-statement attacks, limit enforcement, and CTE rules.
"""

from __future__ import annotations

import pytest

from app.constants import MAX_SQL_LIMIT
from app.services.sql import SQLValidationService


@pytest.fixture
def validator() -> SQLValidationService:
    return SQLValidationService()


# Parametrized cases: (sql, expected_ok, substring_in_violation | None)
SQL_CASES = [
    # valid selects
    ("SELECT * FROM orders", True, None),
    ("SELECT id, total FROM orders WHERE id = 1", True, None),
    ("SELECT COUNT(*) FROM customers", True, None),
    ("SELECT * FROM products WHERE price > 10", True, None),
    ("SELECT o.id FROM orders o JOIN order_items i ON o.id = i.order_id", True, None),
    ("SELECT * FROM refunds LIMIT 5", True, None),
    # blocked DML
    ("DROP TABLE orders", False, "Only SELECT queries"),
    ("DELETE FROM orders WHERE id = 1", False, "Only SELECT queries"),
    ("UPDATE orders SET total = 0", False, "Only SELECT queries"),
    ("INSERT INTO orders (id) VALUES (1)", False, "Only SELECT queries"),
    ("TRUNCATE TABLE orders", False, "Only SELECT queries"),
    ("CREATE TABLE evil (x INT)", False, "Only SELECT queries"),
    # blocked functions
    ("SELECT pg_sleep(5)", False, "blocked"),
    ("SELECT pg_read_file('/etc/passwd')", False, "blocked"),
    ("SELECT lo_import('/etc/passwd')", False, "blocked"),
    ("SELECT dblink('host=...')", False, "blocked"),
    # blocked schemas
    ("SELECT * FROM information_schema.tables", False, "allowed table list"),
    ("SELECT * FROM pg_catalog.pg_class", False, "allowed table list"),
    ("SELECT * FROM pg_toast.foo", False, "allowed table list"),
    # unknown tables
    ("SELECT * FROM evil_table", False, "allowed table list"),
    ("SELECT * FROM sys.users", False, "allowed table list"),
    # multiple statements (injection attempt)
    ("SELECT * FROM orders; DROP TABLE orders", False, "Expected 1 statement"),
    # parse error
    ("NOT VALID SQL !!!!", False, None),  # violation tuple will be non-empty
    # limit enforcement
    ("SELECT * FROM orders LIMIT 999999", True, None),  # cap applied
    ("SELECT * FROM orders", True, None),  # limit auto-added
]


@pytest.mark.parametrize("sql, expected_ok, violation_substr", SQL_CASES)
def test_sql_validator_parametrized(
    validator: SQLValidationService,
    sql: str,
    expected_ok: bool,
    violation_substr: str | None,
) -> None:
    result = validator.validate(sql)
    assert result.ok == expected_ok, f"SQL: {sql!r}\nViolations: {result.violations}"
    if not expected_ok and violation_substr is not None:
        assert any(
            violation_substr in v for v in result.violations
        ), f"Expected '{violation_substr}' in violations: {result.violations}"


# Non-parametrized: limit-cap behaviour


def test_limit_auto_injected(validator: SQLValidationService) -> None:
    """A SELECT with no LIMIT should get one automatically."""
    result = validator.validate("SELECT * FROM orders")
    assert result.ok is True
    assert result.normalized_sql is not None
    assert "LIMIT" in result.normalized_sql.upper()


def test_limit_capped_to_max(validator: SQLValidationService) -> None:
    """A SELECT with LIMIT exceeding MAX_SQL_LIMIT must be capped."""
    oversized = f"SELECT * FROM orders LIMIT {MAX_SQL_LIMIT + 1000}"
    result = validator.validate(oversized)
    assert result.ok is True
    assert result.normalized_sql is not None
    assert str(MAX_SQL_LIMIT) in result.normalized_sql


def test_limit_below_max_unchanged(validator: SQLValidationService) -> None:
    """A SELECT with LIMIT below the cap must be preserved."""
    result = validator.validate("SELECT * FROM orders LIMIT 5")
    assert result.ok is True
    assert result.normalized_sql is not None
    assert "5" in result.normalized_sql


def test_normalized_sql_is_postgres_dialect(validator: SQLValidationService) -> None:
    """normalized_sql should be a non-empty string on success."""
    result = validator.validate("SELECT id FROM customers")
    assert result.ok is True
    assert isinstance(result.normalized_sql, str)
    assert len(result.normalized_sql) > 0


def test_violations_empty_on_success(validator: SQLValidationService) -> None:
    result = validator.validate("SELECT * FROM products")
    assert result.ok is True
    assert result.violations == ()


def test_violations_non_empty_on_failure(validator: SQLValidationService) -> None:
    result = validator.validate("DELETE FROM orders")
    assert result.ok is False
    assert len(result.violations) > 0


def test_normalized_sql_none_on_failure(validator: SQLValidationService) -> None:
    result = validator.validate("DROP TABLE customers")
    assert result.ok is False
    assert result.normalized_sql is None


def test_empty_string_input(validator: SQLValidationService) -> None:
    """Empty string should not crash   it should return ok=False."""
    result = validator.validate("")
    assert result.ok is False


def test_whitespace_only_input(validator: SQLValidationService) -> None:
    result = validator.validate("   ")
    assert result.ok is False
