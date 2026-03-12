"""LLM generation via Ollama with streaming, confidence checks, and citation extraction.

Calls the local Ollama endpoint to generate grounded answers from retrieved context.
Includes confidence thresholding to refuse when context is insufficient.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import AsyncGenerator, List, Optional

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings
from app.generation.prompt_templates import (
    REFUSAL_RESPONSE,
    build_grounded_prompt,
)
from app.retrieval.retriever import RetrievedChunk

logger = logging.getLogger(__name__)


class CitationObject(BaseModel):
    """A single citation reference in the generated answer."""

    source_filename: str
    page_number: int
    chunk_preview: str = ""
    relevance_score: float = 0.0


class GenerationResponse(BaseModel):
    """Complete response from the generation pipeline."""

    answer: str
    citations: List[CitationObject] = Field(default_factory=list)
    confidence_score: float = 0.0
    model_used: str = ""
    retrieval_time_ms: int = 0
    generation_time_ms: int = 0
    chunks_used: int = 0
    refusal: bool = False


async def generate(
    query: str,
    retrieved_chunks: List[RetrievedChunk],
    retrieval_time_ms: int = 0,
    conversation_context: str = "",
) -> GenerationResponse:
    """Generate a grounded answer from retrieved chunks via Ollama.

    Args:
        query: The user's question.
        retrieved_chunks: Ranked chunks from the retrieval pipeline.
        retrieval_time_ms: Time taken for retrieval (for logging).
        conversation_context: Previous conversation context (if any).

    Returns:
        GenerationResponse with answer, citations, and metadata.
    """
    settings = get_settings()

    # Confidence check: if average fusion score is below threshold, refuse
    if retrieved_chunks:
        avg_score = sum(c.fusion_score for c in retrieved_chunks) / len(
            retrieved_chunks
        )
    else:
        avg_score = 0.0

    if avg_score < settings.confidence_threshold or not retrieved_chunks:
        logger.info(
            f"Low confidence ({avg_score:.3f} < {settings.confidence_threshold}), "
            "returning refusal"
        )
        return GenerationResponse(
            answer=REFUSAL_RESPONSE,
            confidence_score=avg_score,
            model_used=settings.ollama_model,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=0,
            chunks_used=0,
            refusal=True,
        )

    # Build the grounded prompt
    prompt = build_grounded_prompt(query, retrieved_chunks)

    # Prepend conversation context if available
    if conversation_context:
        prompt = f"Previous conversation:\n{conversation_context}\n\n{prompt}"

    # Call Ollama
    start = time.perf_counter()
    answer = await _call_ollama(prompt, settings)
    generation_ms = int((time.perf_counter() - start) * 1000)

    # Extract citations from the answer
    citations = _extract_citations(answer, retrieved_chunks)

    return GenerationResponse(
        answer=answer,
        citations=citations,
        confidence_score=avg_score,
        model_used=settings.ollama_model,
        retrieval_time_ms=retrieval_time_ms,
        generation_time_ms=generation_ms,
        chunks_used=len(retrieved_chunks),
        refusal=False,
    )


async def generate_stream(
    query: str,
    retrieved_chunks: List[RetrievedChunk],
    conversation_context: str = "",
) -> AsyncGenerator[str, None]:
    """Stream the generated answer token by token.

    Yields JSON strings with partial answer tokens.
    """
    settings = get_settings()

    # Confidence check
    if retrieved_chunks:
        avg_score = sum(c.fusion_score for c in retrieved_chunks) / len(
            retrieved_chunks
        )
    else:
        avg_score = 0.0

    if avg_score < settings.confidence_threshold or not retrieved_chunks:
        yield json.dumps({"token": REFUSAL_RESPONSE, "done": True})
        return

    prompt = build_grounded_prompt(query, retrieved_chunks)
    if conversation_context:
        prompt = f"Previous conversation:\n{conversation_context}\n\n{prompt}"

    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "num_ctx": 8192,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        done = data.get("done", False)
                        yield json.dumps({"token": token, "done": done})
                    except json.JSONDecodeError:
                        continue


async def _call_ollama(prompt: str, settings) -> str:
    """Make a non-streaming call to Ollama and return the full response."""
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 8192,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()


def _extract_citations(
    answer: str,
    chunks: List[RetrievedChunk],
) -> List[CitationObject]:
    """Extract citation references from the generated answer.

    Looks for patterns like [filename, p.N] or [Source N: filename, p.N].
    """
    citations = []
    seen = set()

    # Match patterns like [filename.pdf, p.3] or [some doc, p.12]
    pattern = r"\[([^,\]]+),\s*p\.(\d+)\]"
    matches = re.findall(pattern, answer)

    for filename, page_str in matches:
        filename = filename.strip()
        page = int(page_str)

        # Remove "Source N:" prefix if present
        if ":" in filename:
            filename = filename.split(":", 1)[-1].strip()

        key = (filename, page)
        if key in seen:
            continue
        seen.add(key)

        # Find the matching chunk for relevance score
        relevance = 0.0
        preview = ""
        for chunk in chunks:
            if (
                chunk.source_filename == filename
                and chunk.page_number == page
            ):
                relevance = chunk.fusion_score
                preview = chunk.text[:150] + "..." if len(chunk.text) > 150 else chunk.text
                break

        citations.append(
            CitationObject(
                source_filename=filename,
                page_number=page,
                chunk_preview=preview,
                relevance_score=relevance,
            )
        )

    # Also include chunk sources that may not have been explicitly cited
    for chunk in chunks:
        key = (chunk.source_filename, chunk.page_number)
        if key not in seen:
            citations.append(
                CitationObject(
                    source_filename=chunk.source_filename,
                    page_number=chunk.page_number,
                    chunk_preview=(
                        chunk.text[:150] + "..."
                        if len(chunk.text) > 150
                        else chunk.text
                    ),
                    relevance_score=chunk.fusion_score,
                )
            )

    return citations


async def check_ollama_health() -> bool:
    """Check if Ollama is running and responsive."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.ollama_base_url}/api/tags"
            )
            return response.status_code == 200
    except Exception:
        return False
