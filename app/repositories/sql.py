"""
SQL Repository
Encapsulates all asyncpg database execution logic for raw SQL.
"""

from __future__ import annotations

import time

import asyncpg

from app.core.config import settings
from app.domain.state import SqlExecution


class SqlRepository:
    def __init__(
        self,
        *,
        statement_timeout_ms: int = 5_000,
        row_cap: int = 500,
        search_path: str = "business, public",
    ) -> None:
        self.statement_timeout_ms = statement_timeout_ms
        self.row_cap = row_cap
        self.search_path = search_path

    async def run_read_only(self, sql: str) -> SqlExecution:
        start = time.perf_counter()
        conn: asyncpg.Connection = await asyncpg.connect(settings.POSTGRES_URL)

        try:
            async with conn.transaction(isolation="read_committed", readonly=True):
                await conn.execute(
                    f"SET statement_timeout = '{self.statement_timeout_ms}ms'"
                )
                await conn.execute(f"SET search_path TO {self.search_path}")
                records = await conn.fetch(sql)
        finally:
            await conn.close()

        elapsed_ms = int((time.perf_counter() - start) * 1_000)

        if not records:
            return SqlExecution(
                columns=(),
                rows=(),
                row_count=0,
                truncated=False,
                elapsed_ms=elapsed_ms,
            )

        columns = tuple(records[0].keys())
        all_rows = tuple(tuple(r.values()) for r in records)

        truncated = len(all_rows) > self.row_cap
        capped_rows = all_rows[: self.row_cap]

        return SqlExecution(
            columns=columns,
            rows=capped_rows,
            row_count=len(capped_rows),
            truncated=truncated,
            elapsed_ms=elapsed_ms,
        )


default_sql_repo = SqlRepository()
