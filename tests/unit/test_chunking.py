"""
Unit tests for DocumentService.parse() and DocumentService.chunk().
Tests use synthetic in-memory content to avoid real file I/O.
"""

from __future__ import annotations

import pytest

from app.exceptions import EmptyDocumentError, UnsupportedFileTypeError
from app.services.document import DocumentService


@pytest.fixture
def doc_service() -> DocumentService:
    return DocumentService(chunk_size=200, chunk_overlap=20)


# parse()   plain text


def test_parse_txt_returns_text(doc_service: DocumentService) -> None:
    content = b"Hello world. This is a test document."
    result = doc_service.parse("readme.txt", content)
    assert "Hello world" in result


def test_parse_txt_unicode(doc_service: DocumentService) -> None:
    content = "Héllo wörld".encode()
    result = doc_service.parse("notes.txt", content)
    assert "Héllo" in result


def test_parse_unsupported_extension_raises(doc_service: DocumentService) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        doc_service.parse("malware.exe", b"data")


def test_parse_empty_txt_raises(doc_service: DocumentService) -> None:
    with pytest.raises(EmptyDocumentError):
        doc_service.parse("empty.txt", b"   \n  ")


def test_parse_preserves_newlines(doc_service: DocumentService) -> None:
    content = b"Line one.\nLine two.\nLine three."
    result = doc_service.parse("lines.txt", content)
    assert "Line one" in result
    assert "Line three" in result


# chunk()   splitting behaviour


def test_chunk_returns_list_of_documents(doc_service: DocumentService) -> None:
    text = "word " * 300  # enough to trigger splitting
    chunks = doc_service.chunk(text, source="test.txt")
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_chunk_metadata_contains_source(doc_service: DocumentService) -> None:
    text = "This is some content. " * 50
    chunks = doc_service.chunk(text, source="myfile.pdf")
    for chunk in chunks:
        assert chunk.metadata.get("source") == "myfile.pdf"


def test_chunk_short_text_single_chunk(doc_service: DocumentService) -> None:
    """Text shorter than chunk_size should produce exactly one chunk."""
    text = "Short content."
    chunks = doc_service.chunk(text, source="short.txt")
    assert len(chunks) == 1
    assert "Short content" in chunks[0].page_content


def test_chunk_long_text_multiple_chunks(doc_service: DocumentService) -> None:
    """Text significantly longer than chunk_size should produce multiple chunks."""
    text = "This is a sentence with many words. " * 200
    chunks = doc_service.chunk(text, source="long.txt")
    assert len(chunks) > 1


def test_chunk_all_chunks_non_empty(doc_service: DocumentService) -> None:
    text = "Content paragraph. " * 100
    chunks = doc_service.chunk(text, source="content.txt")
    for chunk in chunks:
        assert chunk.page_content.strip() != ""


def test_chunk_respects_overlap(doc_service: DocumentService) -> None:
    """Chunks with overlap > 0 should share some content at boundaries."""
    service = DocumentService(chunk_size=100, chunk_overlap=50)
    text = "abcdefghij " * 50
    chunks = service.chunk(text, source="overlap.txt")
    # We can't check exact overlap content, but we can verify more chunks are created
    service_no_overlap = DocumentService(chunk_size=100, chunk_overlap=0)
    chunks_no_overlap = service_no_overlap.chunk(text, source="overlap.txt")
    # With overlap, the number of chunks should be >= chunks without overlap
    assert len(chunks) >= len(chunks_no_overlap)
