from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


def get_openai_llm(
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """Returns a configured ChatOpenAI model instance."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(  # type: ignore[call-arg]
        model=model or settings.OPENAI_LLM_MODEL,
        api_key=api_key or settings.OPENAI_API_KEY,  # type: ignore[arg-type]
        base_url=base_url or settings.OPENAI_BASE_URL,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        max_tokens=settings.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
    )


def get_openai_embeddings(
    model: str | None = None,
    api_key: str | None = None,
) -> Embeddings:
    """Returns a configured OpenAIEmbeddings instance."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=model or settings.OPENAI_EMBEDDING_MODEL,
        api_key=api_key or settings.OPENAI_API_KEY,  # type: ignore[arg-type]
    )
