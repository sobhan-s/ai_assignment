"""
rag_retrieve node
Embeds the user's question and queries the VectorStore for the nearest chunks.
Uses VectorStore.search() from app.rag.vector_store (class-based API).
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.deltas import RagRetrieveDelta
from app.domain.state import Citation, GraphState, RetrievedChunk
from app.graph.adapters import apply_delta
from app.services import default_rag_service


async def rag_retrieve(state: GraphState) -> dict[str, Any]:
    """
    Embeds the user question and queries Qdrant for semantic matches.
    """
    question = (
        state.decision.document_subquestion
        if state.decision and state.decision.document_subquestion
        else state.question
    )

    # 1. Embed the question using the RAG service
    query_vector: list[float] = await default_rag_service.embed_query(question)

    # 2. Query Qdrant via the RAG service
    try:
        scored_points = await default_rag_service.search(query_vector, limit=5)
    except Exception as exc:
        # Log gracefully and return empty   rag_answer handles no-results case
        from app.core.logging import get_logger

        get_logger(__name__).warning("qdrant.search_failed", error=str(exc))
        scored_points = []

    # 3. Map Qdrant ScoredPoints → typed domain models
    retrieved: list[RetrievedChunk] = []
    for i, point in enumerate(scored_points):
        payload = point.payload or {}
        text = payload.get("page_content", "")
        metadata = payload.get("metadata", {})

        citation = Citation(
            document_id=uuid4(),
            filename=metadata.get("source", "unknown"),
            page=None,
            chunk_index=i,
            score=point.score,
            snippet=text[:400],
        )
        retrieved.append(RetrievedChunk(citation=citation, text=text))

    return apply_delta(RagRetrieveDelta(retrieved=tuple(retrieved)))
