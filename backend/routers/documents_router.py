"""Document router — upload, list, detail, delete."""

from __future__ import annotations

import shutil
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from fastapi import Depends

from config import UPLOAD_DIR
from database import get_db
from models import Document
from schemas import DocumentOut
from services.ingestion_service import run_ingestion

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

    # Validate file size (max 50 MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 50 MB)")

    # Save file to disk
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / stored_name
    with open(file_path, "wb") as f:
        f.write(contents)

    # Create DB record
    doc = Document(
        filename=stored_name,
        original_name=file.filename,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Kick off background ingestion
    background_tasks.add_task(run_ingestion, doc.id, str(file_path))

    return DocumentOut.model_validate(doc)


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    docs = (
        db.query(Document)
        .order_by(Document.upload_time.desc())
        .all()
    )
    return [DocumentOut.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Delete file from disk
    file_path = UPLOAD_DIR / doc.filename
    if file_path.exists():
        file_path.unlink()

    # Delete chunks from ChromaDB
    try:
        import chromadb
        from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        results = collection.get(where={"document_id": document_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
    except Exception:
        pass  # Non-critical — best-effort cleanup

    db.delete(doc)
    db.commit()
