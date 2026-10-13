"""
SQL Services
Orchestrates SQL validation and execution.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from app.constants import (
    ALLOWED_TABLES,
    BLOCKED_FUNCTIONS,
    BLOCKED_SCHEMAS,
    MAX_SQL_LIMIT,
)
from app.domain.state import SqlExecution, SqlValidation
from app.repositories import SqlRepository, default_sql_repo


class SQLValidationService:
    def validate(self, sql: str) -> SqlValidation:
        violations: list[str] = []

        try:
            statements = sqlglot.parse(sql, read="postgres")
        except sqlglot.errors.ParseError as exc:
            return SqlValidation(ok=False, violations=(f"SQL parse error: {exc}",))

        if len(statements) != 1:
            return SqlValidation(
                ok=False,
                violations=(f"Expected 1 statement, got {len(statements)}.",),
            )

        ast = statements[0]
        if ast is None:
            return SqlValidation(ok=False, violations=("Empty SQL statement.",))

        if not isinstance(ast, exp.Select):
            return SqlValidation(
                ok=False,
                violations=(
                    "Only SELECT queries are permitted. "
                    "INSERT / UPDATE / DELETE / DROP are blocked.",
                ),
            )

        for cte in ast.find_all(exp.CTE):
            if not isinstance(cte.this, exp.Select):
                violations.append(
                    f"CTE '{cte.alias}' must contain a SELECT (no writes in CTEs)."
                )

        for func in ast.find_all(exp.Func):
            if func.name.lower() in BLOCKED_FUNCTIONS:
                violations.append(
                    f"Function '{func.name}' is blocked for security reasons."
                )

        for table in ast.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name not in ALLOWED_TABLES:
                violations.append(
                    f"Table '{table_name}' is not in the allowed table list."
                )
            if table.db and table.db.lower() in BLOCKED_SCHEMAS:
                violations.append(f"Schema '{table.db}' is forbidden.")

        if violations:
            return SqlValidation(ok=False, violations=tuple(violations))

        limit_node = ast.args.get("limit")
        if not limit_node:
            ast = ast.limit(MAX_SQL_LIMIT)
        else:
            try:
                val = int(limit_node.expression.this)
                if val > MAX_SQL_LIMIT:
                    ast.set(
                        "limit",
                        exp.Limit(expression=sqlglot.parse_one(str(MAX_SQL_LIMIT))),
                    )
            except Exception:
                pass

        normalized = ast.sql(dialect="postgres")
        return SqlValidation(ok=True, normalized_sql=normalized, violations=())


class SQLExecutionService:
    def __init__(self, *, sql_repo: SqlRepository | None = None) -> None:
        self._repo = sql_repo or default_sql_repo

    async def execute_query(self, sql: str) -> SqlExecution:
        return await self._repo.run_read_only(sql)


default_sql_validation_service = SQLValidationService()
default_sql_execution_service = SQLExecutionService()
