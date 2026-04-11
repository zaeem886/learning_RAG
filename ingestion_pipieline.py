import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import chromadb

load_dotenv()

# ChromaDB HTTP server settings (client-server mode)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "documents")

def load_documents(docs_path="docs"):
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"The specified path '{docs_path}' does not exist.")
    
    loader=DirectoryLoader(
        path=docs_path,
        glob="*.txt",
        loader_cls=TextLoader
    )

    documents=loader.load()

    if len(documents) == 0:
        raise ValueError(f"No documents found in the specified path '{docs_path}'. Please ensure there are .txt files in the directory.")
    
    for i, doc in enumerate(documents[:2]):  # Show first 2 documents
        print(f"\nDocument {i+1}:")
        print(f"  Source: {doc.metadata['source']}")
        print(f"  Content length: {len(doc.page_content)} characters")
        print(f"  Content preview: {doc.page_content[:100]}...")
        print(f"  metadata: {doc.metadata}")

    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=0):
    """Split documents into smaller chunks with overlap"""
    print("Splitting documents into chunks...")
    
    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    
    chunks = text_splitter.split_documents(documents)
    
    if chunks:
    
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Source: {chunk.metadata['source']}")
            print(f"Length: {len(chunk.page_content)} characters")
            print(f"Content:")
            print(chunk.page_content)
            print("-" * 50)
        
        if len(chunks) > 5:
            print(f"\n... and {len(chunks) - 5} more chunks")
    
    return chunks

def create_vector_store(chunks):
    """Create and store embeddings in ChromaDB running as an HTTP server (client-server mode)"""
    print(f"Connecting to ChromaDB HTTP server at {CHROMA_HOST}:{CHROMA_PORT} ...")

    # Connect to the running ChromaDB HTTP server
    chroma_client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT
    )

    chroma_client.heartbeat()
    print(f"Successfully connected to ChromaDB server.")

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("--- Creating vector store ---")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        client=chroma_client,
        collection_name=CHROMA_COLLECTION,
        collection_metadata={"hnsw:space": "cosine"}
    )
    print("--- Finished creating vector store ---")

    print(f"Vector store created in ChromaDB server collection: '{CHROMA_COLLECTION}'")
    return vectorstore


def main():

    print("Starting the ingestion pipeline...")
    print(f"ChromaDB server: {CHROMA_HOST}:{CHROMA_PORT}  |  Collection: {CHROMA_COLLECTION}")
    documents=load_documents(docs_path="docs")
    chunks=split_documents(documents)
    vector_store=create_vector_store(chunks)


if __name__=="__main__":
    main()
