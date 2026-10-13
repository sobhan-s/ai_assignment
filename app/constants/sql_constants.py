"""
SQL Constants
Contains all policy definitions for the SQL Validator and Executor.
"""

from __future__ import annotations

ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "customers",
        "products",
        "orders",
        "order_items",
        "refunds",
    }
)

BLOCKED_FUNCTIONS: frozenset[str] = frozenset(
    {
        "pg_sleep",
        "pg_read_file",
        "pg_write_file",
        "dblink",
        "lo_import",
        "lo_export",
        "copy",
    }
)

BLOCKED_SCHEMAS: frozenset[str] = frozenset(
    {
        "pg_catalog",
        "information_schema",
        "pg_toast",
    }
)

MAX_SQL_LIMIT: int = 500
