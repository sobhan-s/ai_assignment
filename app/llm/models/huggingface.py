from __future__ import annotations

from langchain_core.embeddings import Embeddings

from app.core.config import settings


def get_huggingface_embeddings(
    model_name: str | None = None,
) -> Embeddings:
    """Returns a configured HuggingFaceEmbeddings instance."""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model_name or settings.HUGGINGFACE_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
