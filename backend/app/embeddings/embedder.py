"""Embedding engine using sentence-transformers.

Provides a singleton embedding model (all-MiniLM-L6-v2) that loads once
at application startup. All vectors are L2-normalized for cosine similarity
via inner product in FAISS.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Load the sentence-transformer model (singleton)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded successfully")
    return _model


def embed_texts(
    texts: List[str],
    batch_size: int = 64,
    normalize: bool = True,
) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.
        batch_size: Batch size for encoding.
        normalize: Whether to L2-normalize vectors.

    Returns:
        np.ndarray of shape (n_texts, 384) with float32 vectors.
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    if normalize:
        # L2 normalize so inner product = cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings = embeddings / norms

    return embeddings.astype(np.float32)


def embed_query(query: str, normalize: bool = True) -> np.ndarray:
    """Generate embedding for a single query string.

    Args:
        query: Query text string.
        normalize: Whether to L2-normalize the vector.

    Returns:
        np.ndarray of shape (1, 384) with float32 vector.
    """
    return embed_texts([query], normalize=normalize)


def get_embedding_dimension() -> int:
    """Return the embedding dimension (384 for all-MiniLM-L6-v2)."""
    return 384
