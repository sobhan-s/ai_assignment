import pytest

from app.services.sql import SQLValidationService


@pytest.fixture
def validator():
    return SQLValidationService()


def test_valid_select(validator):
    sql = "SELECT * FROM business.orders LIMIT 10"
    res = validator.validate(sql)
    assert res.ok is True
    assert res.violations == ()


def test_blocked_drop(validator):
    sql = "DROP TABLE business.customers"
    res = validator.validate(sql)
    assert res.ok is False
    assert "Only SELECT queries are permitted" in res.violations[0]


def test_blocked_functions(validator):
    sql = "SELECT pg_sleep(10)"
    res = validator.validate(sql)
    assert res.ok is False
    assert any("blocked" in v for v in res.violations)


def test_limit_injection(validator):
    sql = "SELECT * FROM business.orders"
    res = validator.validate(sql)
    assert res.ok is True
    # Should enforce MAX_SQL_LIMIT
    assert "LIMIT" in res.normalized_sql
