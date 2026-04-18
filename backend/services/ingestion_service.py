"""Ingestion service — PDF loading, chunking, embedding, and ChromaDB storage.

Runs as a background task triggered by the upload endpoint.
"""

from __future__ import annotations

import traceback
import uuid
from typing import List

import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME
from database import SessionLocal
from models import Document

# Module-level singletons (loaded once, reused across background tasks)
_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.PersistentClient | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def _get_chroma_collection():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _chroma_client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "PDF document embeddings for RAG"},
    )


def run_ingestion(document_id: int, file_path: str) -> None:
    """Background task: ingest a PDF into ChromaDB.

    Updates the Document record's status and chunk_count when done.
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = "processing"
        db.commit()

        # 1. Load PDF
        loader = PyPDFLoader(file_path)
        pages = loader.load()

        if not pages:
            doc.status = "error"
            doc.error_message = "No content could be extracted from the PDF"
            db.commit()
            return

        # 2. Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_documents(pages)

        if not chunks:
            doc.status = "error"
            doc.error_message = "PDF produced no text chunks"
            db.commit()
            return

        # 3. Embed
        model = _get_embedding_model()
        texts = [c.page_content for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=False)

        # 4. Store in ChromaDB
        collection = _get_chroma_collection()

        ids: List[str] = []
        metadatas: List[dict] = []
        documents_text: List[str] = []
        embeddings_list: List[list] = []

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"doc{document_id}_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(chunk_id)

            meta = {
                "document_id": document_id,
                "source_file": doc.original_name,
                "page": chunk.metadata.get("page", 0),
                "chunk_index": i,
                "content_length": len(chunk.page_content),
            }
            metadatas.append(meta)
            documents_text.append(chunk.page_content)
            embeddings_list.append(emb.tolist())

        # ChromaDB has a batch limit; add in batches of 500
        batch_size = 500
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            collection.add(
                ids=ids[start:end],
                embeddings=embeddings_list[start:end],
                metadatas=metadatas[start:end],
                documents=documents_text[start:end],
            )

        # 5. Update DB record
        doc.status = "ready"
        doc.chunk_count = len(chunks)
        db.commit()

    except Exception as e:
        traceback.print_exc()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "error"
                doc.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
