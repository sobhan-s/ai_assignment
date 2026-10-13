"""
File and Document Constants
Contains allowed file types and limits for document processing.
"""

from __future__ import annotations

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt", ".md"})
