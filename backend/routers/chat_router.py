"""Chat router — ask questions, manage sessions."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import ChatSession, Document, Message
from schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    CreateSessionRequest,
    MessageOut,
    SourceChunk,
)
from services.rag_service import answer_question

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask_question_endpoint(
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    # Validate document if specified
    if body.document_id:
        doc = db.query(Document).filter(Document.id == body.document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        if doc.status != "ready":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is still processing")

    # Get or create session
    session = None
    if body.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == body.session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    else:
        title = body.query[:60] + "..." if len(body.query) > 60 else body.query
        session = ChatSession(
            document_id=body.document_id,
            title=title,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Call RAG pipeline
    result = answer_question(
        query=body.query,
        document_id=body.document_id,
        top_k=body.top_k,
    )

    sources_data = [s.model_dump() for s in result["sources"]]

    # Save user message
    user_msg = Message(session_id=session.id, role="user", content=body.query)
    db.add(user_msg)

    # Save assistant message
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(sources_data),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session.id,
    )


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_sessions(db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [ChatSessionOut.model_validate(s) for s in sessions]


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
):
    session = ChatSession(
        document_id=body.document_id,
        title=body.title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionOut.model_validate(session)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [MessageOut.model_validate(m) for m in messages]
