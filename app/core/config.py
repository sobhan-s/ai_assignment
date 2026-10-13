from __future__ import annotations

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GOOGLE = "google"


class EmbeddingProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"


class Settings(BaseSettings):
    """
    Strictly typed application settings loaded from environment variables.
    Fails instantly if required variables are missing or of the wrong type.
    """

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Execution environment")

    # FastAPI
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Local GenAI Data Assistant"

    # Database
    POSTGRES_USER: str = Field(..., description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    POSTGRES_URL: str = Field(..., description="PostgreSQL asyncpg connection string")

    # Qdrant
    QDRANT_URL: str = Field(
        default="http://localhost:6333", description="Qdrant vector DB URL"
    )
    QDRANT_COLLECTION_NAME: str = Field(
        default="documents", description="Qdrant collection name"
    )

    # LLM Provider Selection
    LLM_PROVIDER: LLMProvider = Field(
        default=LLMProvider.OLLAMA,
        description=(
            "LLM backend to use. Options: ollama | openai | anthropic | groq | google"
        ),
    )
    EMBEDDING_PROVIDER: EmbeddingProvider = Field(
        default=EmbeddingProvider.OLLAMA,
        description=(
            "Embedding backend to use. Options: ollama | openai | google | huggingface"
        ),
    )

    # Ollama (local)
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434", description="Ollama API base URL"
    )
    OLLAMA_LLM_MODEL: str = Field(
        default="llama3.2", description="Ollama model used for generation"
    )
    OLLAMA_EMBEDDING_MODEL: str = Field(
        default="nomic-embed-text", description="Ollama model used for embeddings"
    )

    # OpenAI 
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_BASE_URL: str | None = Field(
        default=None, description="Optional custom base URL (e.g. for OpenRouter)"
    )
    OPENAI_LLM_MODEL: str = Field(
        default="gpt-4o-mini", description="OpenAI chat model"
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )

    # Anthropic
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    ANTHROPIC_LLM_MODEL: str = Field(
        default="claude-3-5-haiku-20241022", description="Anthropic chat model"
    )

    # Groq
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    GROQ_LLM_MODEL: str = Field(
        default="llama-3.3-70b-versatile", description="Groq chat model"
    )

    # Google Generative AI
    GOOGLE_API_KEY: str = Field(default="", description="Google Generative AI API key")
    GOOGLE_LLM_MODEL: str = Field(
        default="gemini-2.0-flash", description="Google GenAI chat model"
    )
    GOOGLE_EMBEDDING_MODEL: str = Field(
        default="models/text-embedding-004", description="Google embedding model"
    )

    # HuggingFace (embeddings only)
    HUGGINGFACE_EMBEDDING_MODEL: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="HuggingFace sentence-transformers embedding model",
    )

    # LLM Generation Params
    LLM_TEMPERATURE: float = Field(
        default=0.0, ge=0.0, le=2.0, description="LLM temperature (0 = deterministic)"
    )
    LLM_MAX_TOKENS: int = Field(
        default=2048, ge=64, le=32768, description="Max tokens for LLM responses"
    )

    # Legacy shims (kept for backward compat with older code)
    @property
    def LLM_MODEL(self) -> str:  
        """Resolved model name based on active provider."""
        return {
            LLMProvider.OLLAMA: self.OLLAMA_LLM_MODEL,
            LLMProvider.OPENAI: self.OPENAI_LLM_MODEL,
            LLMProvider.ANTHROPIC: self.ANTHROPIC_LLM_MODEL,
            LLMProvider.GROQ: self.GROQ_LLM_MODEL,
            LLMProvider.GOOGLE: self.GOOGLE_LLM_MODEL,
        }[self.LLM_PROVIDER]

    @property
    def EMBEDDING_MODEL(self) -> str:  # noqa: N802
        """Resolved embedding model name based on active provider."""
        return {
            EmbeddingProvider.OLLAMA: self.OLLAMA_EMBEDDING_MODEL,
            EmbeddingProvider.OPENAI: self.OPENAI_EMBEDDING_MODEL,
            EmbeddingProvider.GOOGLE: self.GOOGLE_EMBEDDING_MODEL,
            EmbeddingProvider.HUGGINGFACE: self.HUGGINGFACE_EMBEDDING_MODEL,
        }[self.EMBEDDING_PROVIDER]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
