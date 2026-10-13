"""
Integration test: RAG ingest and ask flow.

Tests the document ingestion path → vector storage → RAG retrieval chain.
Full integration requires Qdrant and an embedding service.
The unit-level test here validates the service composition logic
using mocked dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ingestion import IngestionService, IngestReport


@pytest.mark.asyncio
async def test_ingest_service_returns_report() -> None:
    """IngestionService.ingest should return an IngestReport on success."""
    mock_doc_service = MagicMock()
    mock_doc_service.parse.return_value = "Full document text content."
    mock_doc_service.chunk.return_value = [
        MagicMock(page_content="chunk1", metadata={"source": "policy.txt"}),
        MagicMock(page_content="chunk2", metadata={"source": "policy.txt"}),
    ]

    mock_rag_service = MagicMock()
    mock_rag_service.embed_documents = AsyncMock(
        return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    )
    mock_rag_service.bootstrap_collection = AsyncMock()
    mock_rag_service.upsert_documents = AsyncMock()

    service = IngestionService(
        document_service=mock_doc_service,
        rag_service=mock_rag_service,
    )

    mock_file = MagicMock()
    mock_file.filename = "policy.txt"

    report = await service.ingest(mock_file, b"Full document text content.")

    assert isinstance(report, IngestReport)
    assert report.filename == "policy.txt"
    assert report.chunks_indexed == 2
    assert report.vector_size == 3


@pytest.mark.asyncio
async def test_ingest_calls_bootstrap_and_upsert() -> None:
    """IngestionService must call bootstrap_collection and upsert_documents."""
    mock_doc_service = MagicMock()
    mock_doc_service.parse.return_value = "content"
    mock_doc_service.chunk.return_value = [
        MagicMock(page_content="c1", metadata={"source": "f.txt"}),
    ]

    mock_rag_service = MagicMock()
    mock_rag_service.embed_documents = AsyncMock(return_value=[[0.1, 0.2]])
    mock_rag_service.bootstrap_collection = AsyncMock()
    mock_rag_service.upsert_documents = AsyncMock()

    service = IngestionService(
        document_service=mock_doc_service,
        rag_service=mock_rag_service,
    )

    mock_file = MagicMock()
    mock_file.filename = "f.txt"
    await service.ingest(mock_file, b"content")

    mock_rag_service.bootstrap_collection.assert_awaited_once()
    mock_rag_service.upsert_documents.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_fallback_filename_when_none() -> None:
    """If file.filename is None, IngestionService should use 'unknown'."""
    mock_doc_service = MagicMock()
    mock_doc_service.parse.return_value = "content"
    mock_doc_service.chunk.return_value = [
        MagicMock(page_content="c1", metadata={"source": "unknown"}),
    ]

    mock_rag_service = MagicMock()
    mock_rag_service.embed_documents = AsyncMock(return_value=[[0.1]])
    mock_rag_service.bootstrap_collection = AsyncMock()
    mock_rag_service.upsert_documents = AsyncMock()

    service = IngestionService(
        document_service=mock_doc_service,
        rag_service=mock_rag_service,
    )

    mock_file = MagicMock()
    mock_file.filename = None

    report = await service.ingest(mock_file, b"content")
    assert report.filename == "unknown"
