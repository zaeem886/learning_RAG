"""RAG service — retrieval + Groq LLM answer generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer

from config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL_NAME,
    GROQ_API_KEY,
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
)
from schemas import SourceChunk

# Module-level singletons
_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.PersistentClient | None = None
_llm: ChatGroq | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def _get_chroma_collection():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=LLM_MODEL_NAME,
            temperature=LLM_TEMPERATURE,
            api_key=GROQ_API_KEY,
        )
    return _llm


def answer_question(
    query: str,
    document_id: Optional[int] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Retrieve relevant chunks and generate an LLM answer.

    Returns dict with keys: answer (str), sources (list[SourceChunk]).
    """
    model = _get_embedding_model()
    collection = _get_chroma_collection()
    llm = _get_llm()

    # Embed query
    query_embedding = model.encode([query], show_progress_bar=False)[0]

    # Build metadata filter if a specific document is selected
    where_filter = None
    if document_id is not None:
        where_filter = {"document_id": document_id}

    # Retrieve
    query_kwargs = {
        "query_embeddings": [query_embedding.tolist()],
        "n_results": top_k,
    }
    if where_filter:
        query_kwargs["where"] = where_filter

    results = collection.query(**query_kwargs)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "answer": "I couldn't find any relevant information in your documents to answer this question.",
            "sources": [],
        }

    # Build source chunks
    sources: List[SourceChunk] = []
    context_parts: List[str] = []
    for i, (doc_text, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        score = 1 - float(dist)
        sources.append(
            SourceChunk(
                content=doc_text[:500],
                source_file=meta.get("source_file", "unknown"),
                page=meta.get("page"),
                score=round(score, 4),
            )
        )
        context_parts.append(
            f"[Source {i}] {meta.get('source_file', 'unknown')} (page {meta.get('page', '?')})\n"
            f"Score: {score:.4f}\n"
            f"Content: {doc_text}\n"
        )

    context = "\n".join(context_parts)

    prompt = f"""You are a helpful assistant that answers questions based on the user's uploaded documents.
Answer the question using ONLY the provided context. If the answer is not in the context, say you don't know.
Always mention which source(s) you used in your answer.

Context:
{context}

Question: {query}

Answer:"""

    response = llm.invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    return {"answer": answer, "sources": sources}
