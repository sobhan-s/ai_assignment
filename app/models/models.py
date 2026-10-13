"""
SQLAlchemy ORM models for Documents, Chat Sessions, and Chat Messages.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    """Generates a string UUID hex representation."""
    return uuid.uuid4().hex


class DocumentModel(Base):
    """Stores metadata for uploaded files."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="indexed")
    chunks_indexed = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    sessions = relationship(
        "ChatSessionModel", back_populates="document", cascade="all, delete-orphan"
    )


class ChatSessionModel(Base):
    """Stores chat session records linked to a document (or global)."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_name = Column(String(255), nullable=False, default="New Chat Session")

    # Nullable because we might just chat without a document in COMBINED / SQL routes
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    document = relationship("DocumentModel", back_populates="sessions")
    messages = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageModel.timestamp",
    )


class ChatMessageModel(Base):
    """Stores individual user questions and AI responses for a session."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    session = relationship("ChatSessionModel", back_populates="messages")
