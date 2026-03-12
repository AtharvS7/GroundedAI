"""Tests for the FAISS vector store."""

import os
import shutil
import tempfile

import numpy as np
import pytest

from app.vectorstore.faiss_store import FAISSStore


@pytest.fixture
def temp_store():
    """Create a FAISS store with a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    store = FAISSStore(index_path=tmpdir)
    yield store
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_vectors():
    """Generate sample L2-normalized vectors."""
    rng = np.random.RandomState(42)
    vectors = rng.randn(10, 384).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / norms


class TestFAISSStore:
    """Test suite for the FAISS vector store."""

    def test_add_and_search(self, temp_store, sample_vectors):
        """Test adding vectors and searching."""
        ids = [f"chunk_{i}" for i in range(10)]
        temp_store.add_chunks(ids, sample_vectors)

        assert temp_store.total_vectors == 10

        results = temp_store.search(sample_vectors[0:1], top_k=3)
        assert len(results) == 3
        # First result should be the query itself
        assert results[0][0] == "chunk_0"
        assert results[0][1] > 0.9

    def test_save_and_load(self, temp_store, sample_vectors):
        """Test index persistence."""
        ids = [f"chunk_{i}" for i in range(5)]
        temp_store.add_chunks(ids, sample_vectors[:5])
        temp_store.save()

        # Create new store and load
        loaded_store = FAISSStore(index_path=temp_store.index_path)
        assert loaded_store.load()
        assert loaded_store.total_vectors == 5

    def test_delete_by_document_id(self, temp_store, sample_vectors):
        """Test deleting vectors by chunk IDs."""
        ids = [f"chunk_{i}" for i in range(10)]
        temp_store.add_chunks(ids, sample_vectors)
        assert temp_store.total_vectors == 10

        removed = temp_store.delete_by_document_id(["chunk_0", "chunk_1"])
        assert removed == 2
        assert temp_store.total_vectors == 8

    def test_empty_search(self, temp_store):
        """Test searching an empty index returns nothing."""
        query = np.random.randn(1, 384).astype(np.float32)
        results = temp_store.search(query, top_k=5)
        assert len(results) == 0

    def test_rebuild(self, temp_store, sample_vectors):
        """Test full index rebuild."""
        ids = [f"chunk_{i}" for i in range(10)]
        temp_store.add_chunks(ids, sample_vectors)
        assert temp_store.total_vectors == 10

        new_ids = [f"new_{i}" for i in range(5)]
        total = temp_store.rebuild(new_ids, sample_vectors[:5])
        assert total == 5
        assert temp_store.total_vectors == 5

    def test_load_nonexistent_returns_false(self, temp_store):
        """Test loading from nonexistent files returns False."""
        assert not temp_store.load()
