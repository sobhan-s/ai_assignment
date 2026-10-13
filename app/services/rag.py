"""
RAG Service
Orchestrates embedding creation, Qdrant upserts, and vector search.
"""

from __future__ import annotations

import uuid

from langchain_core.documents import Document
from qdrant_client.http.models import PointStruct, ScoredPoint

from app.llm.factory import get_embeddings
from app.repositories import VectorRepository, default_vector_repo


class RAGService:
    def __init__(self, *, vector_repo: VectorRepository | None = None) -> None:
        self._repo = vector_repo or default_vector_repo

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embedder = get_embeddings()
        return await embedder.aembed_documents(texts)

    async def embed_query(self, query: str) -> list[float]:
        embedder = get_embeddings()
        return await embedder.aembed_query(query)

    async def upsert_documents(
        self, docs: list[Document], vectors: list[list[float]]
    ) -> None:
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload={
                    "page_content": docs[i].page_content,
                    "metadata": docs[i].metadata,
                },
            )
            for i in range(len(docs))
        ]
        await self._repo.upsert(points)

    async def search(
        self, query_vector: list[float], *, limit: int = 5
    ) -> list[ScoredPoint]:
        return await self._repo.search(query_vector, limit=limit)

    async def bootstrap_collection(self, vector_size: int) -> None:
        await self._repo.bootstrap(vector_size=vector_size)


default_rag_service = RAGService()
