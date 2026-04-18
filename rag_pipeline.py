"""Basic vector DB + LLM RAG pipeline.

This file is a starter setup for:
- loading environment variables
- retrieving context from ChromaDB
- generating an answer with Groq
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List

import chromadb
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer


load_dotenv()

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def get_groq_api_key() -> str | None:
    """Return the Groq API key from either uppercase or lowercase env names."""
    return os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key")


@dataclass
class RetrievedChunk:
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    distance: float


class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]):
        return self.model.encode(texts, show_progress_bar=False)


class VectorStore:
    def __init__(self, collection_name: str = "pdf_documents", persist_directory: str = "../data/vector_store") -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)


class RAGPipeline:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_manager: EmbeddingManager,
        model_name: str = "llama-3.1-8b-instant",
    ) -> None:
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
        api_key = get_groq_api_key()
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.2,
            api_key=api_key,
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        query_embedding = self.embedding_manager.embed_texts([query])[0]
        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
        )

        chunks: List[RetrievedChunk] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            chunks.append(
                RetrievedChunk(
                    id=doc_id,
                    content=document,
                    metadata=metadata,
                    score=1 - float(distance),
                    distance=float(distance),
                )
            )

        return chunks

    def build_context(self, chunks: List[RetrievedChunk]) -> str:
        parts: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source_file", "unknown")
            parts.append(
                f"[Source {index}] {source}\n"
                f"Score: {chunk.score:.4f}\n"
                f"Content: {chunk.content}\n"
            )
        return "\n".join(parts)

    def answer(self, query: str, top_k: int = 5) -> str:
        chunks = self.retrieve(query, top_k=top_k)
        if not chunks:
            return "No relevant context found in the vector database."

        context = self.build_context(chunks)
        prompt = f"""You are a helpful assistant.
Answer the question using only the provided context.
If the answer is not in the context, say you do not know.

Context:
{context}

Question: {query}

Answer:"""

        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RAG pipeline from the terminal.")
    parser.add_argument("query", nargs="*", help="Question to ask the retriever and LLM")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks to use")
    parser.add_argument("--interactive", action="store_true", help="Keep prompting for questions until you exit")
    args = parser.parse_args()

    if not get_groq_api_key():
        print("Missing GROQ_API_KEY or groq_api_key in environment. Put it in .env first.")
        sys.exit(1)

    vector_store = VectorStore()
    embedding_manager = EmbeddingManager()
    pipeline = RAGPipeline(vector_store, embedding_manager)

    def run_query(query: str) -> None:
        query = query.strip()
        if not query:
            return

        print(f"\nQuery: {query}")
        chunks = pipeline.retrieve(query, top_k=args.top_k)
        if not chunks:
            print("No relevant context found in the vector database.")
            return

        print("Retrieved context:")
        for chunk in chunks:
            print(f"- {chunk.metadata.get('source_file', 'unknown')} | score={chunk.score:.4f}")

        print("\nLLM answer:\n")
        print(pipeline.answer(query, top_k=args.top_k))

    if args.interactive:
        print("Enter your questions. Type 'exit' or press Enter on an empty line to quit.")
        while True:
            try:
                query = input("\nQuestion> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not query or query.lower() in {"exit", "quit"}:
                break

            run_query(query)
        return

    query = " ".join(args.query).strip()
    if not query:
        query = input("Enter your question: ").strip()

    if not query:
        print("No query provided.")
        return

    run_query(query)


if __name__ == "__main__":
    main()
