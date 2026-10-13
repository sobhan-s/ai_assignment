from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from app.core.config import settings


def get_anthropic_llm(
    model: str | None = None,
    api_key: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """Returns a configured ChatAnthropic model instance."""
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(  # type: ignore[call-arg]
        model=model or settings.ANTHROPIC_LLM_MODEL,
        api_key=api_key or settings.ANTHROPIC_API_KEY,  # type: ignore[arg-type]
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        max_tokens=settings.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
    )
