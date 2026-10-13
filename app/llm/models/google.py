from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


def get_google_llm(
    model: str | None = None,
    api_key: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """Returns a configured ChatGoogleGenerativeAI model instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model or settings.GOOGLE_LLM_MODEL,
        google_api_key=api_key or settings.GOOGLE_API_KEY,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        max_output_tokens=settings.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
    )


def get_google_embeddings(
    model: str | None = None,
    api_key: str | None = None,
) -> Embeddings:
    """Returns a configured GoogleGenerativeAIEmbeddings instance."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
        model=model or settings.GOOGLE_EMBEDDING_MODEL,
        google_api_key=api_key or settings.GOOGLE_API_KEY,
    )
