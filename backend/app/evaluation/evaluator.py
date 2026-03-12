"""Evaluation engine for RAG pipeline quality metrics.

Computes retrieval metrics (Precision@k, Recall@k, MRR) and
generation metrics (ROUGE-L, BLEU-4, Faithfulness).
Includes baseline comparison for hallucination delta measurement.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EvalResult(BaseModel):
    """Evaluation result for a single query."""

    query_id: str
    rouge_l: float = 0.0
    bleu_4: float = 0.0
    faithfulness: float = 0.0
    precision_k: float = 0.0
    recall_k: float = 0.0
    mrr: float = 0.0
    baseline_rouge: float = 0.0
    baseline_bleu: float = 0.0
    baseline_faithfulness: float = 0.0
    hallucination_delta: float = 0.0


def compute_rouge_l(hypothesis: str, reference: str) -> float:
    """Compute ROUGE-L F1 score between hypothesis and reference."""
    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference, hypothesis)
        return float(scores["rougeL"].fmeasure)
    except Exception as e:
        logger.warning(f"ROUGE-L computation failed: {e}")
        return 0.0


def compute_bleu_4(hypothesis: str, reference: str) -> float:
    """Compute BLEU-4 score with smoothing."""
    try:
        from nltk.translate.bleu_score import (
            SmoothingFunction,
            sentence_bleu,
        )

        ref_tokens = reference.lower().split()
        hyp_tokens = hypothesis.lower().split()

        if not ref_tokens or not hyp_tokens:
            return 0.0

        smoothie = SmoothingFunction().method1
        return float(
            sentence_bleu(
                [ref_tokens],
                hyp_tokens,
                weights=(0.25, 0.25, 0.25, 0.25),
                smoothing_function=smoothie,
            )
        )
    except Exception as e:
        logger.warning(f"BLEU-4 computation failed: {e}")
        return 0.0


def compute_faithfulness(
    answer: str, context: str
) -> float:
    """Compute faithfulness as cosine similarity between answer and context embeddings."""
    try:
        from app.embeddings.embedder import embed_texts

        answer_emb = embed_texts([answer])[0]
        context_emb = embed_texts([context])[0]

        # Cosine similarity (vectors are already L2-normalized)
        similarity = float(np.dot(answer_emb, context_emb))
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        logger.warning(f"Faithfulness computation failed: {e}")
        return 0.0


def compute_precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: List[str],
    k: int = 5,
) -> float:
    """Compute Precision@k."""
    if not retrieved_ids or not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for rid in top_k if rid in relevant_set)
    return hits / len(top_k)


def compute_recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: List[str],
    k: int = 5,
) -> float:
    """Compute Recall@k."""
    if not retrieved_ids or not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    hits = sum(1 for rid in top_k if rid in relevant_set)
    return hits / len(relevant_set)


def compute_mrr(
    retrieved_ids: List[str],
    relevant_ids: List[str],
) -> float:
    """Compute Mean Reciprocal Rank."""
    if not retrieved_ids or not relevant_ids:
        return 0.0
    relevant_set = set(relevant_ids)
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def evaluate_query(
    query_id: str,
    answer: str,
    reference_answer: str,
    context: str,
    retrieved_chunk_ids: List[str],
    relevant_chunk_ids: Optional[List[str]] = None,
    baseline_answer: str = "",
    k: int = 5,
) -> EvalResult:
    """Run full evaluation for a single query.

    Args:
        query_id: UUID of the query being evaluated.
        answer: RAG-generated answer.
        reference_answer: Ground truth reference answer.
        context: Concatenated retrieved context.
        retrieved_chunk_ids: IDs of retrieved chunks.
        relevant_chunk_ids: IDs of truly relevant chunks (if known).
        baseline_answer: Baseline LLM answer (without RAG).
        k: Top-k for retrieval metrics.

    Returns:
        EvalResult with all metrics computed.
    """
    # Generation metrics
    rouge_l = compute_rouge_l(answer, reference_answer)
    bleu_4 = compute_bleu_4(answer, reference_answer)
    faithfulness = compute_faithfulness(answer, context)

    # Retrieval metrics
    rel_ids = relevant_chunk_ids or []
    precision_k = compute_precision_at_k(retrieved_chunk_ids, rel_ids, k)
    recall_k = compute_recall_at_k(retrieved_chunk_ids, rel_ids, k)
    mrr = compute_mrr(retrieved_chunk_ids, rel_ids)

    # Baseline comparison
    baseline_rouge = 0.0
    baseline_bleu = 0.0
    baseline_faithfulness = 0.0
    if baseline_answer:
        baseline_rouge = compute_rouge_l(baseline_answer, reference_answer)
        baseline_bleu = compute_bleu_4(baseline_answer, reference_answer)
        baseline_faithfulness = compute_faithfulness(baseline_answer, context)

    # Hallucination delta: positive = RAG is better
    hallucination_delta = faithfulness - baseline_faithfulness

    return EvalResult(
        query_id=query_id,
        rouge_l=round(rouge_l, 4),
        bleu_4=round(bleu_4, 4),
        faithfulness=round(faithfulness, 4),
        precision_k=round(precision_k, 4),
        recall_k=round(recall_k, 4),
        mrr=round(mrr, 4),
        baseline_rouge=round(baseline_rouge, 4),
        baseline_bleu=round(baseline_bleu, 4),
        baseline_faithfulness=round(baseline_faithfulness, 4),
        hallucination_delta=round(hallucination_delta, 4),
    )
