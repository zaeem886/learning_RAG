"""SQLAlchemy ORM models."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)          # stored name on disk
    original_name = Column(String(255), nullable=False)     # user-facing name
    status = Column(String(50), default="uploading")        # uploading | processing | ready | error
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    upload_time = Column(DateTime, default=_utcnow)

    chat_sessions = relationship("ChatSession", back_populates="document", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=_utcnow)

    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)   # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)       # JSON string of source citations
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("ChatSession", back_populates="messages")
