"""
condense_question node
Retrieves chat history and rephrases the question into a fully standalone form
if it contains pronoun references to previous turns.
"""

from __future__ import annotations

from typing import Any

from app.domain.state import GraphState
from app.llm.chains import get_condense_chain
from app.repositories import default_conversation_repo


async def condense_question(state: GraphState) -> dict[str, Any]:
    """
    Retrieves chat history and rephrases the question if it depends on past context.
    """
    if not state.thread_id:
        return {}

    # 1. Fetch recent history
    history = await default_conversation_repo.get_history(state.thread_id, limit=4)

    if not history:
        return {}  # No history   question is already standalone

    # Format history as a readable string for the prompt
    history_str = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in history]
    )

    # 2. Run LLM chain to rewrite question
    chain = get_condense_chain()
    standalone_question: str = await chain.ainvoke(
        {
            "chat_history": history_str,
            "question": state.question,
        }
    )

    # Replace the original question with the standalone one in the state
    return {"question": standalone_question.strip()}
