"""GroundedAI FastAPI Application Entry Point.

Configures the application with CORS, middleware, router mounting,
and lifespan events for initializing FAISS and embedding models.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.logging_mw import LoggingMiddleware
from app.api.routes import documents, evaluate, health, metrics, query
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize resources on startup."""
    settings = get_settings()

    # Load FAISS index from disk
    logger.info("Loading FAISS index...")
    from app.vectorstore.faiss_store import get_faiss_store

    store = get_faiss_store()
    logger.info(f"FAISS ready: {store.total_vectors} vectors loaded")

    # Pre-load embedding model
    logger.info("Loading embedding model...")
    from app.embeddings.embedder import embed_query

    embed_query("warmup")
    logger.info("Embedding model ready")

    yield

    # Cleanup: save FAISS index on shutdown
    logger.info("Saving FAISS index on shutdown...")
    store.save()
    logger.info("FAISS index saved. Shutting down.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="GroundedAI",
        description=(
            "Production-Grade RAG System. "
            "Ground your LLM. Eliminate hallucinations. Trust your answers."
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware
    app.add_middleware(LoggingMiddleware)

    # Mount routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(
        documents.router, prefix="", tags=["Documents"]
    )
    app.include_router(query.router, prefix="", tags=["Query"])
    app.include_router(metrics.router, prefix="", tags=["Metrics"])
    app.include_router(evaluate.router, prefix="", tags=["Evaluation"])

    return app


app = create_app()
