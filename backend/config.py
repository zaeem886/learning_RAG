"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = _root / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_PERSIST_DIR = str(DATA_DIR / "vector_store")

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'rag_app.db'}")

# --- Groq LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key") or ""
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama-3.1-8b-instant")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# --- Embeddings ---
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "pdf_documents")

# --- CORS (for Vercel frontend and local dev) ---
_default_origins = ",".join(
    [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
