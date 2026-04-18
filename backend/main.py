"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from database import Base, engine
from routers import documents_router, chat_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG Document Chat API",
    description="Upload PDFs and chat with your documents using AI",
    version="1.0.0",
)

# CORS — allow the Vite dev server and Vercel production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents_router.router)
app.include_router(chat_router.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
