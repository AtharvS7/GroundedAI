"""Query endpoint — the main RAG pipeline entry point."""

from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.api.middleware.injection import validate_query_text
from app.config import get_settings
from app.database.supabase_client import insert_query
from app.generation.generator import generate, generate_stream
from app.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    query: str = Field(..., max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)
    use_reranking: bool = False
    conversation_id: Optional[str] = None


@router.post("/query")
async def query_endpoint(
    body: QueryRequest,
    user: dict = Depends(get_current_user),
):
    """Run the full RAG query pipeline.

    Pipeline: injection check → retrieve → generate → log → respond.
    """
    # Step 1: Injection check
    validate_query_text(body.query)

    settings = get_settings()
    user_id = user["id"]

    try:
        # Step 2: Retrieve
        chunks, retrieval_ms = retrieve(
            query=body.query,
            top_k=body.top_k,
            use_reranking=body.use_reranking,
            user_id=user_id,
        )

        # Step 3: Build conversation context from Redis (future)
        conversation_context = ""

        # Step 4: Generate
        response = await generate(
            query=body.query,
            retrieved_chunks=chunks,
            retrieval_time_ms=retrieval_ms,
            conversation_context=conversation_context,
        )

        # Step 5: Log to Supabase
        query_record = insert_query(
            {
                "user_id": user_id,
                "conversation_id": body.conversation_id,
                "query_text": body.query,
                "response_text": response.answer,
                "confidence_score": response.confidence_score,
                "model_used": response.model_used,
                "retrieval_ms": response.retrieval_time_ms,
                "generation_ms": response.generation_time_ms,
                "top_k": body.top_k,
                "refusal": response.refusal,
            }
        )

        return {
            "data": response.model_dump(),
            "error": None,
            "metadata": {
                "query_id": query_record.get("id"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@router.post("/query/stream")
async def query_stream_endpoint(
    body: QueryRequest,
    user: dict = Depends(get_current_user),
):
    """Stream the RAG query response token by token."""
    validate_query_text(body.query)

    try:
        chunks, _ = retrieve(
            query=body.query,
            top_k=body.top_k,
            use_reranking=body.use_reranking,
            user_id=user["id"],
        )

        return StreamingResponse(
            generate_stream(
                query=body.query,
                retrieved_chunks=chunks,
            ),
            media_type="text/event-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stream failed: {e}")
