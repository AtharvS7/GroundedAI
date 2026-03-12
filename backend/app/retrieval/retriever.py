"""Hybrid retriever: FAISS vector search + BM25 lexical search + score fusion.

Optionally applies cross-encoder reranking for improved precision.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional
from uuid import UUID

import numpy as np
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

from app.config import get_settings
from app.database.supabase_client import get_chunks_by_ids, get_all_chunks
from app.embeddings.embedder import embed_query
from app.vectorstore.faiss_store import get_faiss_store

logger = logging.getLogger(__name__)


class RetrievedChunk(BaseModel):
    """A chunk retrieved by the hybrid retrieval pipeline."""

    chunk_id: str
    document_id: str
    source_filename: str
    page_number: int
    text: str
    vector_score: float = 0.0
    bm25_score: float = 0.0
    fusion_score: float = 0.0
    rank: int = 0


def retrieve(
    query: str,
    top_k: int = 5,
    use_reranking: bool = False,
    user_id: Optional[str] = None,
) -> tuple[List[RetrievedChunk], int]:
    """Run the full hybrid retrieval pipeline.

    Steps:
        1. Embed the query
        2. FAISS top-(k*2) vector search
        3. BM25 lexical search
        4. Score fusion (weighted combination)
        5. Optional cross-encoder reranking
        6. Fetch full chunk data from Supabase

    Args:
        query: User query string.
        top_k: Number of final results to return.
        use_reranking: Whether to apply cross-encoder reranking.
        user_id: User ID for scoped chunk retrieval.

    Returns:
        Tuple of (list of RetrievedChunk, retrieval_time_ms).
    """
    start = time.perf_counter()
    settings = get_settings()
    alpha = settings.hybrid_alpha  # 0.7 vector, 0.3 bm25

    # Step 1: Embed the query
    query_vector = embed_query(query)

    # Step 2: FAISS vector search (get more candidates for fusion)
    faiss_store = get_faiss_store()
    vector_results = faiss_store.search(query_vector, top_k=top_k * 2)

    if not vector_results:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return [], elapsed_ms

    # Step 3: BM25 search
    # Fetch all chunks for BM25 corpus
    all_chunks = get_all_chunks(user_id or "")
    if not all_chunks:
        # Fall back to vector-only results
        chunk_ids = [cid for cid, _ in vector_results[:top_k]]
        chunks_data = get_chunks_by_ids(chunk_ids)
        results = _build_results(chunks_data, dict(vector_results), {}, alpha)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return results[:top_k], elapsed_ms

    # Build BM25 index
    corpus_texts = [c["text"] for c in all_chunks]
    corpus_ids = [c["id"] for c in all_chunks]
    tokenized_corpus = [text.lower().split() for text in corpus_texts]
    bm25 = BM25Okapi(tokenized_corpus)

    # Get BM25 scores
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # Build BM25 score map (normalize to 0-1)
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    bm25_map = {}
    for i, score in enumerate(bm25_scores):
        if score > 0:
            bm25_map[corpus_ids[i]] = float(score / max_bm25)

    # Step 4: Score fusion
    # Collect all candidate chunk IDs (union of vector + top BM25)
    vector_map = dict(vector_results)

    # Get top BM25 results
    bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
    bm25_top_ids = set(corpus_ids[i] for i in bm25_top_indices if bm25_scores[i] > 0)

    # Union of candidates
    all_candidate_ids = set(vector_map.keys()) | bm25_top_ids

    # Compute fusion scores
    fusion_scores = {}
    for cid in all_candidate_ids:
        v_score = vector_map.get(cid, 0.0)
        b_score = bm25_map.get(cid, 0.0)
        fusion_scores[cid] = alpha * v_score + (1 - alpha) * b_score

    # Sort by fusion score
    sorted_ids = sorted(fusion_scores, key=fusion_scores.get, reverse=True)[:top_k]

    # Fetch full chunk data
    chunks_data = get_chunks_by_ids(sorted_ids)

    # Step 5: Optional reranking
    if use_reranking and chunks_data:
        try:
            sorted_ids, fusion_scores = _rerank(
                query, chunks_data, sorted_ids, fusion_scores
            )
        except Exception as e:
            logger.warning(f"Reranking failed, using fusion scores: {e}")

    results = _build_results(chunks_data, vector_map, bm25_map, alpha, fusion_scores)

    # Sort by fusion score and assign ranks
    results.sort(key=lambda r: r.fusion_score, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        f"Retrieved {len(results)} chunks in {elapsed_ms}ms "
        f"(reranked={use_reranking})"
    )
    return results[:top_k], elapsed_ms


def _build_results(
    chunks_data: list,
    vector_map: dict,
    bm25_map: dict,
    alpha: float,
    fusion_scores: dict | None = None,
) -> List[RetrievedChunk]:
    """Build RetrievedChunk objects from database records."""
    results = []
    for chunk in chunks_data:
        cid = chunk["id"]
        v_score = vector_map.get(cid, 0.0)
        b_score = bm25_map.get(cid, 0.0)

        if fusion_scores and cid in fusion_scores:
            f_score = fusion_scores[cid]
        else:
            f_score = alpha * v_score + (1 - alpha) * b_score

        # Get filename from joined documents data
        filename = ""
        if "documents" in chunk and chunk["documents"]:
            filename = chunk["documents"].get("filename", "")

        results.append(
            RetrievedChunk(
                chunk_id=cid,
                document_id=chunk.get("document_id", ""),
                source_filename=filename,
                page_number=chunk.get("page_number", 1),
                text=chunk.get("text", ""),
                vector_score=v_score,
                bm25_score=b_score,
                fusion_score=f_score,
            )
        )
    return results


def _rerank(
    query: str,
    chunks_data: list,
    sorted_ids: list,
    fusion_scores: dict,
) -> tuple:
    """Apply cross-encoder reranking to rescore chunks."""
    from sentence_transformers import CrossEncoder

    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Build pairs
    chunk_text_map = {c["id"]: c["text"] for c in chunks_data}
    pairs = []
    valid_ids = []
    for cid in sorted_ids:
        if cid in chunk_text_map:
            pairs.append([query, chunk_text_map[cid]])
            valid_ids.append(cid)

    if not pairs:
        return sorted_ids, fusion_scores

    # Rerank
    rerank_scores = reranker.predict(pairs)

    # Normalize rerank scores to 0-1
    min_s = float(min(rerank_scores))
    max_s = float(max(rerank_scores))
    range_s = max_s - min_s if max_s > min_s else 1.0

    for i, cid in enumerate(valid_ids):
        normalized = (float(rerank_scores[i]) - min_s) / range_s
        fusion_scores[cid] = normalized

    sorted_ids = sorted(valid_ids, key=lambda x: fusion_scores[x], reverse=True)
    return sorted_ids, fusion_scores
