"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.database.supabase_client import check_supabase_health
from app.generation.generator import check_ollama_health
from app.vectorstore.faiss_store import get_faiss_store

router = APIRouter()


@router.get("/health")
async def health_check():
    """System health check — no auth required.

    Checks connectivity to Ollama, FAISS index status, and Supabase.
    """
    settings = get_settings()
    faiss_store = get_faiss_store()

    ollama_ok = await check_ollama_health()
    supabase_ok = check_supabase_health()

    return {
        "data": {
            "status": "healthy" if (ollama_ok and supabase_ok) else "degraded",
            "ollama": ollama_ok,
            "faiss": {
                "loaded": True,
                "total_vectors": faiss_store.total_vectors,
            },
            "supabase": supabase_ok,
            "version": settings.app_version,
        },
        "error": None,
        "metadata": {
            "request_id": None,
            "timestamp": None,
            "duration_ms": 0,
        },
    }
