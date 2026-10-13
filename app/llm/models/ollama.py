from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


def get_ollama_llm(
    model: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    """Returns a configured ChatOllama model instance."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model or settings.OLLAMA_LLM_MODEL,
        base_url=base_url or settings.OLLAMA_BASE_URL,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
    )


def get_ollama_embeddings(
    model: str | None = None,
    base_url: str | None = None,
) -> Embeddings:
    """Returns a configured OllamaEmbeddings instance."""
    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(
        model=model or settings.OLLAMA_EMBEDDING_MODEL,
        base_url=base_url or settings.OLLAMA_BASE_URL,
    )
