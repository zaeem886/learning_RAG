# RAG Document Chat Application

This project is a full-stack Retrieval-Augmented Generation (RAG) system built with FastAPI, ChromaDB, LangChain utilities, Groq LLM, and a React + Vite frontend.

It lets you upload PDF documents, automatically chunk and index them into a vector database, and ask natural-language questions grounded in your uploaded content.

The backend is designed to answer from retrieved context and return source chunks so responses are traceable.

## Features

- PDF upload with validation (type and size)
- Background ingestion pipeline (load -> chunk -> embed -> store)
- Persistent vector search with ChromaDB
- RAG-based question answering with Groq
- Source chunk citations returned with answers
- Chat sessions and message history stored in SQLite
- Document-scoped querying (single document or all documents)
- React dashboard for document management
- React chat UI with session history and document filter

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Vector DB: ChromaDB (persistent local storage)
- Retrieval/Chunking: LangChain community loaders + text splitters
- LLM: Groq via langchain-groq
- Embeddings: Chroma default embedding function (ONNX-backed all-MiniLM-L6-v2)
- Frontend: React, Vite, React Router
- Database: SQLite (default)

## Project Structure

```text
learning_RAG/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Env/config loading and paths
│   ├── database.py                # SQLAlchemy engine/session/base
│   ├── models.py                  # ORM models (Document, ChatSession, Message)
│   ├── schemas.py                 # Request/response schemas
│   ├── requirements.txt           # Backend dependencies
│   ├── routers/
│   │   ├── documents_router.py    # Upload/list/get/delete document APIs
│   │   └── chat_router.py         # Ask question + sessions/messages APIs
│   └── services/
│       ├── ingestion_service.py   # PDF ingestion + chunking + vector storage
│       └── rag_service.py         # Retrieval + LLM answer generation
├── frontend/
│   ├── src/
│   │   ├── api/client.js          # API client and endpoint wrappers
│   │   ├── pages/DashboardPage.jsx# Document upload/list/delete UI
│   │   └── pages/ChatPage.jsx     # Chat UI with history and filters
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── uploads/                   # Uploaded PDF files
│   └── vector_store/              # ChromaDB persistence directory
├── docs/                          # Place source PDFs here if needed
├── ingestion_pipeline.py          # Standalone ingestion experiment script
├── retrieval.py                   # Standalone retrieval test script
├── rag_pipeline.py                # Standalone CLI RAG pipeline script
├── render.yaml                    # Render deployment config (backend)
├── .env.example
└── README.md
```

## How the RAG Flow Works

1. Upload PDF
- Frontend sends file to backend upload endpoint.
- Backend stores the file in data/uploads and creates a document record.

2. Background ingestion
- A FastAPI background task loads PDF pages.
- Text is split into overlapping chunks.
- Chunks and metadata are stored in ChromaDB.
- Document status changes to ready when ingestion completes.

3. Question answering
- User asks a question from chat UI.
- Backend retrieves top-k semantically relevant chunks from ChromaDB.
- Retrieved context is sent to Groq LLM with strict grounding prompt.
- API returns final answer and source chunks.

4. Session persistence
- Chat sessions and messages are saved to SQLite.
- Frontend can load past sessions and message history.

## Environment Variables

Create a root .env file (copy from .env.example):

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=change-me-in-production-please

# Optional overrides
# DATABASE_URL=sqlite:///data/rag_app.db
# CHROMA_PERSIST_DIR=data/vector_store
# LLM_MODEL_NAME=llama-3.1-8b-instant
# ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.com
```

Frontend (optional, for production/custom backend URL):

```env
# frontend/.env
VITE_API_URL=http://localhost:8000
```

## Local Development Setup

### 1. Clone and enter project

```bash
git clone <your-repo-url>
cd learning_RAG
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

## Running the Project

Open two terminals.

### Terminal A: Run backend

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload
```

Backend URLs:
- API base: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

### Terminal B: Run frontend

```bash
cd frontend
npm run dev
```

Frontend URL:
- http://localhost:5173

## API Overview

### Documents

- POST /api/documents/upload
  - Upload one PDF file
  - Validates .pdf extension and max size 50 MB

- GET /api/documents
  - List uploaded documents with status and chunk_count

- GET /api/documents/{document_id}
  - Get one document

- DELETE /api/documents/{document_id}
  - Delete document, local file, and vector chunks (best effort)

### Chat

- POST /api/chat
  - Ask a question
  - Supports optional document_id filter and optional session_id
  - Returns answer, sources, and session_id

- GET /api/chat/sessions
  - List chat sessions

- POST /api/chat/sessions
  - Create new chat session

- GET /api/chat/sessions/{session_id}/messages
  - Get full message history for a session

## Important Behavior

- Answers are generated from retrieved document context.
- If no relevant context is found, the API returns a fallback response.
- Source chunks are included in the response payload for transparency.

## Deployment

This repository includes render.yaml for backend deployment on Render.

Configured service:
- Runtime: Python
- Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
- Root directory: backend

Set these environment variables in Render:
- GROQ_API_KEY
- SECRET_KEY
- ALLOWED_ORIGINS
- CHROMA_PERSIST_DIR (already set in render.yaml)
- DATABASE_URL (already set in render.yaml)

## Standalone Scripts (Optional)

Root scripts are available for experimentation and learning:

- ingestion_pipeline.py
- retrieval.py
- rag_pipeline.py

These are useful for understanding the RAG pipeline independently of the FastAPI app.

## Use Cases

- Private PDF knowledge assistant
- Course and research Q and A
- Internal documentation chat
- Team knowledge retrieval interface

## License

For educational and learning purposes.
