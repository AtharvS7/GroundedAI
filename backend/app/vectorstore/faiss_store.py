"""FAISS vector store with persistence.

Uses IndexFlatIP (inner product on L2-normalized vectors = cosine similarity).
Maintains a chunk_id mapping for translating FAISS internal indices to UUIDs.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from app.config import get_settings
from app.embeddings.embedder import get_embedding_dimension

logger = logging.getLogger(__name__)


class FAISSStore:
    """FAISS vector store with persistence and ID mapping."""

    def __init__(self, index_path: Optional[str] = None):
        """Initialize the FAISS store.

        Args:
            index_path: Directory to persist the index and ID map.
        """
        self.index_path = index_path or get_settings().faiss_index_path
        self.dimension = get_embedding_dimension()
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)
        self.chunk_ids: List[str] = []
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create the index directory if it doesn't exist."""
        Path(self.index_path).mkdir(parents=True, exist_ok=True)

    @property
    def index_file(self) -> str:
        return os.path.join(self.index_path, "index.faiss")

    @property
    def id_map_file(self) -> str:
        return os.path.join(self.index_path, "chunk_ids.json")

    @property
    def total_vectors(self) -> int:
        """Return the number of vectors in the index."""
        return self.index.ntotal

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: np.ndarray,
    ) -> int:
        """Add vectors to the index with corresponding chunk IDs.

        Args:
            chunk_ids: List of chunk UUID strings.
            embeddings: np.ndarray of shape (n, dimension).

        Returns:
            Total number of vectors in the index after addition.
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Expected dimension {self.dimension}, "
                f"got {embeddings.shape[1]}"
            )

        self.index.add(embeddings.astype(np.float32))
        self.chunk_ids.extend(chunk_ids)

        logger.info(
            f"Added {len(chunk_ids)} vectors. "
            f"Total: {self.total_vectors}"
        )
        return self.total_vectors

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Search for the top-k most similar vectors.

        Args:
            query_vector: np.ndarray of shape (1, dimension).
            top_k: Number of results to return.

        Returns:
            List of (chunk_id, score) tuples sorted by relevance.
        """
        if self.total_vectors == 0:
            return []

        # Clamp top_k to the number of vectors available
        k = min(top_k, self.total_vectors)
        query = query_vector.astype(np.float32)

        if query.ndim == 1:
            query = query.reshape(1, -1)

        scores, indices = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunk_ids):
                results.append((self.chunk_ids[idx], float(score)))

        return results

    def delete_by_document_id(
        self,
        document_chunk_ids: List[str],
    ) -> int:
        """Remove vectors for specific chunk IDs (by rebuilding the index).

        Since FAISS IndexFlatIP doesn't support deletion, we rebuild.

        Args:
            document_chunk_ids: Chunk IDs to remove.

        Returns:
            Number of vectors removed.
        """
        if not document_chunk_ids:
            return 0

        remove_set = set(document_chunk_ids)
        keep_indices = []
        new_chunk_ids = []

        for i, cid in enumerate(self.chunk_ids):
            if cid not in remove_set:
                keep_indices.append(i)
                new_chunk_ids.append(cid)

        removed_count = len(self.chunk_ids) - len(new_chunk_ids)

        if removed_count == 0:
            return 0

        # Rebuild the index with remaining vectors
        if keep_indices:
            remaining_vectors = np.array(
                [self.index.reconstruct(i) for i in keep_indices]
            )
            new_index = faiss.IndexFlatIP(self.dimension)
            new_index.add(remaining_vectors.astype(np.float32))
            self.index = new_index
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

        self.chunk_ids = new_chunk_ids

        logger.info(
            f"Removed {removed_count} vectors. "
            f"Remaining: {self.total_vectors}"
        )
        return removed_count

    def save(self) -> None:
        """Persist the index and ID map to disk."""
        self._ensure_directory()
        faiss.write_index(self.index, self.index_file)
        with open(self.id_map_file, "w") as f:
            json.dump(self.chunk_ids, f)
        logger.info(
            f"Saved FAISS index ({self.total_vectors} vectors) to {self.index_path}"
        )

    def load(self) -> bool:
        """Load the index and ID map from disk.

        Returns:
            True if loaded successfully, False if files don't exist.
        """
        if not os.path.exists(self.index_file) or not os.path.exists(
            self.id_map_file
        ):
            logger.info("No existing FAISS index found, starting fresh")
            return False

        self.index = faiss.read_index(self.index_file)
        with open(self.id_map_file, "r") as f:
            self.chunk_ids = json.load(f)

        logger.info(
            f"Loaded FAISS index ({self.total_vectors} vectors) from {self.index_path}"
        )
        return True

    def rebuild(
        self,
        chunk_ids: List[str],
        embeddings: np.ndarray,
    ) -> int:
        """Full rebuild of the index from scratch.

        Args:
            chunk_ids: All chunk IDs.
            embeddings: All corresponding embeddings.

        Returns:
            Total vectors in rebuilt index.
        """
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunk_ids = []
        return self.add_chunks(chunk_ids, embeddings)


# ─── Singleton ────────────────────────────────────────────────

_store: Optional[FAISSStore] = None


def get_faiss_store() -> FAISSStore:
    """Return singleton FAISS store instance."""
    global _store
    if _store is None:
        _store = FAISSStore()
        _store.load()
    return _store
