"""
Conversation Repository
Manages persistent chat history in PostgreSQL using asyncpg.
"""

from __future__ import annotations

import re

import asyncpg

from app.core.config import settings


class ConversationRepository:
    def __init__(self, *, postgres_url: str | None = None) -> None:
        raw_url = postgres_url or settings.POSTGRES_URL
        if raw_url.startswith("postgresql+asyncpg://"):
            raw_url = "postgresql://" + raw_url[len("postgresql+asyncpg://") :]
        self._url = raw_url

    async def save_message(self, thread_id: object, role: str, content: str) -> None:
        conn: asyncpg.Connection = await asyncpg.connect(self._url)
        try:
            await conn.execute(
                """
                INSERT INTO memory.messages (thread_id, role, content)
                VALUES ($1, $2, $3)
                """,
                str(thread_id),
                role,
                content,
            )
        finally:
            await conn.close()

    async def get_history(
        self, thread_id: object, *, limit: int = 6
    ) -> list[dict[str, str]]:
        conn: asyncpg.Connection = await asyncpg.connect(self._url)
        try:
            rows = await conn.fetch(
                """
                SELECT role, content
                FROM   memory.messages
                WHERE  thread_id = $1
                ORDER  BY created_at DESC
                LIMIT  $2
                """,
                str(thread_id),
                limit,
            )
        finally:
            await conn.close()

        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def __repr__(self) -> str:
        masked = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", self._url)
        return f"ConversationRepository(url={masked!r})"


default_conversation_repo = ConversationRepository()
