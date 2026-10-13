"""
Ingestion Service
Orchestrates Document parsing/chunking and RAG embedding/upserting.
"""

from __future__ import annotations

from fastapi import UploadFile

from app.services.document import DocumentService, default_document_service
from app.services.rag import RAGService, default_rag_service


class IngestReport:
    """Lightweight result object returned after a successful ingestion."""

    __slots__ = ("filename", "chunks_indexed", "vector_size")

    def __init__(self, filename: str, chunks_indexed: int, vector_size: int) -> None:
        self.filename = filename
        self.chunks_indexed = chunks_indexed
        self.vector_size = vector_size


class IngestionService:
    def __init__(
        self,
        *,
        document_service: DocumentService | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self._doc_service = document_service or default_document_service
        self._rag_service = rag_service or default_rag_service

    async def ingest(self, file: UploadFile, content: bytes) -> IngestReport:
        filename = file.filename or "unknown"

        raw_text = self._doc_service.parse(filename, content)
        docs = self._doc_service.chunk(raw_text, source=filename)

        vectors = await self._rag_service.embed_documents(
            [d.page_content for d in docs]
        )
        vector_size = len(vectors[0]) if vectors else 0

        await self._rag_service.bootstrap_collection(vector_size=vector_size)
        await self._rag_service.upsert_documents(docs, vectors)

        return IngestReport(
            filename=filename,
            chunks_indexed=len(docs),
            vector_size=vector_size,
        )


default_ingestion_service = IngestionService()
