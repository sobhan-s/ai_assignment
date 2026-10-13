"""
Documents Route
POST /documents/ingest   upload a document to the vector store.
Uses IngestionPipeline (class-based, DI-friendly) for processing.
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.api.schemas import IngestResponse
from app.core.logging import get_logger
from app.services import default_ingestion_service

router = APIRouter(prefix="/documents", tags=["documents"])
log = get_logger(__name__)

# Single pipeline instance   VectorStore and splitter configured here.
# Override in tests by injecting a different IngestionPipeline.
_pipeline = default_ingestion_service


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def upload_document(file: UploadFile = File(...)) -> IngestResponse:
    """
    Upload a PDF, DOCX, TXT, or MD file.
    The file will be parsed, chunked, embedded, and stored in Qdrant.
    """
    content = await file.read()
    filename = file.filename or "unknown"

    log.info("documents.ingest.start", filename=filename, size_bytes=len(content))

    report = await _pipeline.ingest(file, content)

    log.info(
        "documents.ingest.done",
        filename=filename,
        chunks=report.chunks_indexed,
    )

    return IngestResponse(
        filename=report.filename,
        status="success",
        chunks_indexed=report.chunks_indexed,
    )
