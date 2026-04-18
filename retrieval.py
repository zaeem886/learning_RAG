"""RAG retrieval module.

Add your retrieval pipeline code here.
"""

import os
import logging
import warnings
from typing import Any, Dict, List, Protocol

import chromadb
from sentence_transformers import SentenceTransformer

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


class VectorStoreLike(Protocol):
    """Minimal shape required from a vector store for retrieval."""

    collection: Any


class EmbeddingManagerLike(Protocol):
    """Minimal shape required from an embedding manager for retrieval."""

    def generate_embeddings(self, texts: List[str]) -> Any:
        ...


class RAGRetriever:
    """Handles query-based retrieval from the vector store"""
    
    def __init__(self, vector_store: VectorStoreLike, embedding_manager: EmbeddingManagerLike):
        """
        Initialize the retriever
        
        Args:
            vector_store: Vector store containing document embeddings
            embedding_manager: Manager for generating query embeddings
        """
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: The search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of dictionaries containing retrieved documents and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_manager.generate_embeddings([query])[0]
        
        # Search in vector store
        try:
            results = self.vector_store.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            # Process results
            retrieved_docs = []
            
            if results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                ids = results['ids'][0]
                
                for i, (doc_id, document, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1 - distance
                    
                    if similarity_score >= score_threshold:
                        retrieved_docs.append({
                            'id': doc_id,
                            'content': document,
                            'metadata': metadata,
                            'similarity_score': similarity_score,
                            'distance': distance,
                            'rank': i + 1
                        })
                
            return retrieved_docs
            
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []


class EmbeddingManager:
    """Loads a sentence-transformers model and creates embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str]) -> Any:
        return self.model.encode(texts, show_progress_bar=False)


class VectorStore:
    """Creates a Chroma collection handle from a persistent directory."""

    def __init__(self, collection_name: str = "pdf_documents", persist_directory: str = "../data/vector_store"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)


def main() -> None:
    vectorstore = VectorStore(collection_name="pdf_documents", persist_directory="../data/vector_store")
    embedding_manager = EmbeddingManager(model_name="all-MiniLM-L6-v2")

    rag_retriever = RAGRetriever(vectorstore, embedding_manager)
    query = "What is attention is all you need"
    results = rag_retriever.retrieve(query, top_k=5)

    if not results:
        print("No results found")
        return

    for item in results:
        print(f"Rank: {item['rank']}")
        print(f"Score: {item['similarity_score']:.4f}")
        print(f"Source: {item['metadata'].get('source_file', 'unknown')}")
        print(f"Preview: {item['content'][:220].replace(chr(10), ' ')}")
        print("-" * 60)


if __name__ == "__main__":
    main()

