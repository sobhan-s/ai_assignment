from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.config import EmbeddingProvider, LLMProvider, settings
from app.exceptions import LLMProviderError


def get_llm() -> BaseChatModel:
    """
    Returns a configured chat model instance for the active LLM_PROVIDER.

    Delegates instantiation directly to the dedicated provider module in app.llm.models.
    """
    provider = settings.LLM_PROVIDER

    if provider == LLMProvider.OLLAMA:
        from app.llm.models.ollama import get_ollama_llm

        return get_ollama_llm()

    if provider == LLMProvider.OPENAI:
        from app.llm.models.openai import get_openai_llm

        return get_openai_llm()

    if provider == LLMProvider.ANTHROPIC:
        from app.llm.models.anthropic import get_anthropic_llm

        return get_anthropic_llm()

    if provider == LLMProvider.GROQ:
        from app.llm.models.groq import get_groq_llm

        return get_groq_llm()

    if provider == LLMProvider.GOOGLE:
        from app.llm.models.google import get_google_llm

        return get_google_llm()

    raise LLMProviderError(f"Unsupported LLM provider: {provider!r}")


def get_embeddings() -> Embeddings:
    """
    Returns a configured embeddings instance for the active EMBEDDING_PROVIDER.

    Delegates instantiation directly to the dedicated provider module in app.llm.models.
    """
    provider = settings.EMBEDDING_PROVIDER

    if provider == EmbeddingProvider.OLLAMA:
        from app.llm.models.ollama import get_ollama_embeddings

        return get_ollama_embeddings()

    if provider == EmbeddingProvider.OPENAI:
        from app.llm.models.openai import get_openai_embeddings

        return get_openai_embeddings()

    if provider == EmbeddingProvider.GOOGLE:
        from app.llm.models.google import get_google_embeddings

        return get_google_embeddings()

    if provider == EmbeddingProvider.HUGGINGFACE:
        from app.llm.models.huggingface import get_huggingface_embeddings

        return get_huggingface_embeddings()

    raise LLMProviderError(f"Unsupported embedding provider: {provider!r}")
