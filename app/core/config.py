from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

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
    POSTGRES_URL: str = Field(..., description="PostgreSQL connection string")

    # Qdrant
    QDRANT_URL: str = Field(default="http://localhost:6333", description="Qdrant vector DB URL")
    QDRANT_COLLECTION_NAME: str = Field(default="documents", description="Qdrant collection name")

    # Ollama
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama API URL")
    LLM_MODEL: str = Field(default="llama3", description="Model used for generation")
    EMBEDDING_MODEL: str = Field(default="nomic-embed-text", description="Model used for embeddings")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
