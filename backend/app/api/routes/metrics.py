"""Metrics endpoint — aggregated evaluation data."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user
from app.database.supabase_client import get_evaluations, get_queries

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    """Fetch aggregated evaluation metrics for the current user."""
    user_id = user["id"]

    queries = get_queries(user_id, limit=limit, offset=offset)
    evaluations = get_evaluations(user_id, limit=limit, offset=offset)

    # Compute aggregates
    total_queries = len(queries)
    avg_confidence = 0.0
    if queries:
        scores = [q.get("confidence_score", 0) or 0 for q in queries]
        avg_confidence = sum(scores) / len(scores) if scores else 0

    avg_rouge = 0.0
    avg_bleu = 0.0
    avg_faithfulness = 0.0
    avg_hallucination_delta = 0.0
    if evaluations:
        avg_rouge = sum(e.get("rouge_l", 0) or 0 for e in evaluations) / len(
            evaluations
        )
        avg_bleu = sum(e.get("bleu_4", 0) or 0 for e in evaluations) / len(
            evaluations
        )
        avg_faithfulness = sum(
            e.get("faithfulness", 0) or 0 for e in evaluations
        ) / len(evaluations)
        avg_hallucination_delta = sum(
            e.get("hallucination_delta", 0) or 0 for e in evaluations
        ) / len(evaluations)

    return {
        "data": {
            "summary": {
                "total_queries": total_queries,
                "avg_confidence": round(avg_confidence, 4),
                "avg_rouge_l": round(avg_rouge, 4),
                "avg_bleu_4": round(avg_bleu, 4),
                "avg_faithfulness": round(avg_faithfulness, 4),
                "avg_hallucination_delta": round(avg_hallucination_delta, 4),
            },
            "queries": queries,
            "evaluations": evaluations,
        },
        "error": None,
    }
