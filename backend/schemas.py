"""Pydantic request / response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ---- Documents ----

class DocumentOut(BaseModel):
    id: int
    filename: str
    original_name: str
    status: str
    chunk_count: int
    upload_time: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Chat ----

class ChatRequest(BaseModel):
    query: str
    document_id: Optional[int] = None
    session_id: Optional[int] = None
    top_k: int = 5

class SourceChunk(BaseModel):
    content: str
    source_file: str
    page: Optional[int] = None
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    session_id: int

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionOut(BaseModel):
    id: int
    title: str
    document_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CreateSessionRequest(BaseModel):
    title: str = "New Chat"
    document_id: Optional[int] = None
