"""
Unit tests for Citation and related domain models.
Tests validation constraints, field limits, and model behaviour.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.state import Citation, RagResult, RetrievedChunk


def test_citation_valid_construction() -> None:
    c = Citation(
        document_id=uuid4(),
        filename="policy.pdf",
        page=1,
        chunk_index=0,
        score=0.95,
        snippet="Our policy is clear.",
    )
    assert c.filename == "policy.pdf"
    assert c.score == 0.95


def test_citation_snippet_max_400_chars() -> None:
    with pytest.raises(ValidationError):
        Citation(
            document_id=uuid4(),
            filename="doc.pdf",
            page=1,
            chunk_index=0,
            score=0.5,
            snippet="x" * 401,  # exceeds max_length=400
        )


def test_citation_page_optional() -> None:
    c = Citation(
        document_id=uuid4(),
        filename="doc.txt",
        page=None,
        chunk_index=2,
        score=0.7,
        snippet="Some text here.",
    )
    assert c.page is None


def test_citation_is_frozen() -> None:
    c = Citation(
        document_id=uuid4(),
        filename="doc.pdf",
        page=1,
        chunk_index=0,
        score=0.8,
        snippet="Text.",
    )
    with pytest.raises((TypeError, ValidationError)):
        c.score = 0.0  # type: ignore[misc]


def test_citation_score_bounds() -> None:
    """Score can be any float   domain doesn't constrain it."""
    c = Citation(
        document_id=uuid4(),
        filename="doc.pdf",
        page=None,
        chunk_index=0,
        score=1.5,  # qdrant can return >1 with some distance metrics
        snippet="Some text.",
    )
    assert c.score == 1.5


# RetrievedChunk


def test_retrieved_chunk_holds_citation_and_text() -> None:
    citation = Citation(
        document_id=uuid4(),
        filename="leave_policy.pdf",
        page=3,
        chunk_index=1,
        score=0.88,
        snippet="You are entitled to 20 days of annual leave.",
    )
    chunk = RetrievedChunk(citation=citation, text="Full text of the chunk here.")
    assert chunk.citation.filename == "leave_policy.pdf"
    assert "Full text" in chunk.text


def test_retrieved_chunk_is_frozen() -> None:
    citation = Citation(
        document_id=uuid4(),
        filename="doc.pdf",
        page=None,
        chunk_index=0,
        score=0.9,
        snippet="snippet",
    )
    chunk = RetrievedChunk(citation=citation, text="original text")
    with pytest.raises((TypeError, ValidationError)):
        chunk.text = "modified"  # type: ignore[misc]


# RagResult


def test_rag_result_with_no_citations() -> None:
    res = RagResult(answer="I found nothing.", citations=(), grounded=False)
    assert res.grounded is False
    assert res.citations == ()


def test_rag_result_with_multiple_citations(sample_citation: Citation) -> None:
    c2 = Citation(
        document_id=uuid4(),
        filename="addendum.pdf",
        page=2,
        chunk_index=1,
        score=0.75,
        snippet="Additional clause.",
    )
    res = RagResult(
        answer="Based on the documents...",
        citations=(sample_citation, c2),
        grounded=True,
    )
    assert len(res.citations) == 2
    assert res.grounded is True
