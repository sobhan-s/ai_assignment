from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.config import EmbeddingProvider, LLMProvider, settings


def get_llm() -> BaseChatModel:
    """
    Returns a configured chat model instance for the active LLM_PROVIDER.

    Provider priority / recommended options:
      - ollama    → free, fully local, good for dev/air-gapped environments
      - groq      → fastest free-tier cloud inference (LLaMA 3.3 70B)
      - openai    → GPT-4o-mini is cost-effective; GPT-4o for best quality
      - anthropic → Claude 3.5 Haiku is fast; Sonnet for reasoning tasks
      - google    → Gemini 2.0 Flash, generous free tier
    """
    provider = settings.LLM_PROVIDER
    temperature = settings.LLM_TEMPERATURE
    max_tokens = settings.LLM_MAX_TOKENS

    if provider == LLMProvider.OLLAMA:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
        )

    if provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(  # type: ignore[call-arg]
            model=settings.OPENAI_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,  # type: ignore[arg-type]
            base_url=settings.OPENAI_BASE_URL,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(  # type: ignore[call-arg]
            model=settings.ANTHROPIC_LLM_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == LLMProvider.GROQ:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.GROQ_LLM_MODEL,
            api_key=settings.GROQ_API_KEY,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == LLMProvider.GOOGLE:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.GOOGLE_LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    from app.exceptions import LLMProviderError

    raise LLMProviderError(f"Unsupported LLM provider: {provider!r}")


def get_embeddings() -> Embeddings:
    """
    Returns a configured embeddings instance for the active EMBEDDING_PROVIDER.

    Provider recommendations:
      - ollama      → local, free, moderate quality (nomic-embed-text)
      - openai      → text-embedding-3-small is cheap + high quality
      - google      → text-embedding-004, generous free quota
      - huggingface → BAAI/bge-small-en-v1.5 runs locally, no API key needed
    """
    provider = settings.EMBEDDING_PROVIDER

    if provider == EmbeddingProvider.OLLAMA:
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

    if provider == EmbeddingProvider.OPENAI:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,  # type: ignore[arg-type]
        )

    if provider == EmbeddingProvider.GOOGLE:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
            model=settings.GOOGLE_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    if provider == EmbeddingProvider.HUGGINGFACE:
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=settings.HUGGINGFACE_EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    from app.exceptions import LLMProviderError

    raise LLMProviderError(f"Unsupported embedding provider: {provider!r}")
