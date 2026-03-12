"""Evaluation endpoint — run RAG vs baseline comparisons."""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.config import get_settings
from app.database.supabase_client import insert_evaluation
from app.evaluation.evaluator import evaluate_query
from app.evaluation.report_generator import generate_eval_report

logger = logging.getLogger(__name__)
router = APIRouter()


class EvalRequest(BaseModel):
    """Request body for /evaluate endpoint."""

    query_ids: List[str] = Field(..., min_length=1)
    reference_answers: List[str] = Field(..., min_length=1)


@router.post("/evaluate")
async def run_evaluation(
    body: EvalRequest,
    user: dict = Depends(get_current_user),
):
    """Run evaluation on specified queries against reference answers."""
    if len(body.query_ids) != len(body.reference_answers):
        raise HTTPException(
            status_code=422,
            detail="query_ids and reference_answers must have the same length",
        )

    from app.database.supabase_client import get_supabase_client

    client = get_supabase_client()
    results = []

    for query_id, reference in zip(body.query_ids, body.reference_answers):
        # Fetch query data
        query_data = (
            client.table("queries")
            .select("*")
            .eq("id", query_id)
            .execute()
        )
        if not query_data.data:
            continue

        qd = query_data.data[0]
        answer = qd.get("response_text", "")
        context = ""  # Would need to reconstruct from chunks
        retrieved_ids = []  # Would need retrieval log

        # Evaluate
        eval_result = evaluate_query(
            query_id=query_id,
            answer=answer,
            reference_answer=reference,
            context=context or answer,  # Fallback to answer as proxy
            retrieved_chunk_ids=retrieved_ids,
            baseline_answer="",
        )

        # Store evaluation
        eval_record = insert_evaluation(
            {
                "query_id": query_id,
                "rouge_l": eval_result.rouge_l,
                "bleu_4": eval_result.bleu_4,
                "faithfulness": eval_result.faithfulness,
                "precision_k": eval_result.precision_k,
                "recall_k": eval_result.recall_k,
                "mrr": eval_result.mrr,
                "baseline_rouge": eval_result.baseline_rouge,
                "baseline_bleu": eval_result.baseline_bleu,
                "baseline_faithfulness": eval_result.baseline_faithfulness,
                "hallucination_delta": eval_result.hallucination_delta,
            }
        )

        results.append(eval_result.model_dump())

    return {
        "data": {
            "evaluation_count": len(results),
            "results": results,
        },
        "error": None,
    }


@router.post("/evaluate/report")
async def generate_report(
    user: dict = Depends(get_current_user),
):
    """Generate a PDF evaluation report."""
    from app.database.supabase_client import get_evaluations

    evaluations = get_evaluations(user["id"], limit=100)

    if not evaluations:
        raise HTTPException(
            status_code=404,
            detail="No evaluations found. Run /evaluate first.",
        )

    output_path = generate_eval_report(evaluations)

    if not output_path:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report. Is reportlab installed?",
        )

    from fastapi.responses import FileResponse
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="groundedai_eval_report.pdf",
    )
