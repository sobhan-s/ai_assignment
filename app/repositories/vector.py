"""
Vector Repository
Wraps QdrantClient for collection bootstrap, upsert, and search.
"""

from __future__ import annotations

import asyncio

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, ScoredPoint, VectorParams

from app.core.config import settings


class VectorRepository:
    def __init__(
        self,
        *,
        collection_name: str | None = None,
        qdrant_url: str | None = None,
        distance: Distance = Distance.COSINE,
    ) -> None:
        self._collection = collection_name or settings.QDRANT_COLLECTION_NAME
        self._client = QdrantClient(url=qdrant_url or settings.QDRANT_URL)
        self._distance = distance

    async def bootstrap(self, vector_size: int) -> None:
        exists = await asyncio.to_thread(
            self._client.collection_exists, self._collection
        )
        if not exists:
            await asyncio.to_thread(
                self._client.create_collection,
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=self._distance),
            )

    async def upsert(self, points: list[PointStruct]) -> None:
        await asyncio.to_thread(
            self._client.upsert,
            collection_name=self._collection,
            points=points,
        )

    async def search(
        self,
        query_vector: list[float],
        *,
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> list[ScoredPoint]:
        result = await asyncio.to_thread(
            self._client.query_points,
            collection_name=self._collection,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold if score_threshold > 0 else None,
        )
        return result.points

    @property
    def collection_name(self) -> str:
        return self._collection

    def __repr__(self) -> str:
        return (
            f"VectorRepository(collection={self._collection!r}, "
            f"url={self._client._client.rest_uri!r})"  # type: ignore[attr-defined]
        )


default_vector_repo = VectorRepository()
