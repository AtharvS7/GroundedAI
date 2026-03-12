"""Recursive token-based text chunker.

Splits document text into chunks of configurable token size with overlap.
Uses tiktoken for accurate token counting. Preserves page number metadata.
"""

from __future__ import annotations

import logging
from typing import List

import tiktoken

from app.ingestion.models import DocumentObject
from app.preprocessing.models import ChunkObject
from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_tokenizer() -> tiktoken.Encoding:
    """Get the cl100k_base tokenizer."""
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in a text string."""
    enc = _get_tokenizer()
    return len(enc.encode(text))


def chunk_document(
    document: DocumentObject,
    chunk_size_tokens: int | None = None,
    overlap_tokens: int | None = None,
    min_chunk_size_chars: int = 100,
) -> List[ChunkObject]:
    """Split a document into token-based chunks with overlap.

    Args:
        document: Parsed DocumentObject with pages.
        chunk_size_tokens: Max tokens per chunk (default from config).
        overlap_tokens: Overlap tokens between chunks (default from config).
        min_chunk_size_chars: Minimum chunk size in characters.

    Returns:
        List of ChunkObject with metadata.
    """
    settings = get_settings()
    chunk_size = chunk_size_tokens or settings.chunk_size_tokens
    overlap = overlap_tokens or settings.chunk_overlap_tokens

    enc = _get_tokenizer()
    chunks: List[ChunkObject] = []
    chunk_index = 0

    for page in document.pages:
        text = page.raw_text.strip()
        if not text or len(text) < min_chunk_size_chars:
            # If the page text is very short, treat it as a single chunk
            if text:
                tokens = enc.encode(text)
                chunks.append(
                    ChunkObject(
                        document_id=document.document_id,
                        chunk_index=chunk_index,
                        text=text,
                        token_count=len(tokens),
                        source_filename=document.source_filename,
                        page_number=page.page_number,
                    )
                )
                chunk_index += 1
            continue

        # Tokenize the full page text
        tokens = enc.encode(text)

        # Slide a window over the token array
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = enc.decode(chunk_tokens).strip()

            if len(chunk_text) >= min_chunk_size_chars or start + chunk_size >= len(tokens):
                chunks.append(
                    ChunkObject(
                        document_id=document.document_id,
                        chunk_index=chunk_index,
                        text=chunk_text,
                        token_count=len(chunk_tokens),
                        source_filename=document.source_filename,
                        page_number=page.page_number,
                    )
                )
                chunk_index += 1

            # Move window forward by (chunk_size - overlap)
            step = chunk_size - overlap
            if step <= 0:
                step = chunk_size  # Safety: prevent infinite loop
            start += step

    logger.info(
        f"Chunked '{document.source_filename}' into {len(chunks)} chunks "
        f"(chunk_size={chunk_size}, overlap={overlap})"
    )
    return chunks
