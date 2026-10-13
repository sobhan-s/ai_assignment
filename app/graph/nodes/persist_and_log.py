from __future__ import annotations

import asyncio
from typing import Any

from app.domain.state import GraphState
from app.repositories import default_conversation_repo


async def persist_and_log(state: GraphState) -> dict[str, Any]:
    """
    Saves the user's original question and the AI's final answer to the database.
    """
    if not state.thread_id:
        return {}

    question = state.question
    answer = state.final_answer or "No answer generated."

    # Save both messages concurrently to speed up the final response
    await asyncio.gather(
        default_conversation_repo.save_message(state.thread_id, "user", question),
        default_conversation_repo.save_message(state.thread_id, "assistant", answer),
    )

    return {}
