"""Tests for the embedding module."""

import numpy as np
import pytest


class TestEmbedder:
    """Test suite for the sentence-transformer embedder."""

    def test_embed_single_text(self):
        """Test embedding a single text returns correct shape."""
        from app.embeddings.embedder import embed_texts
        result = embed_texts(["Hello world"])
        assert result.shape == (1, 384)
        assert result.dtype == np.float32

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts returns batch results."""
        from app.embeddings.embedder import embed_texts
        texts = ["First text", "Second text", "Third text"]
        result = embed_texts(texts)
        assert result.shape == (3, 384)

    def test_embeddings_are_normalized(self):
        """Test that embeddings are L2-normalized."""
        from app.embeddings.embedder import embed_texts
        result = embed_texts(["Test normalization"])
        norm = np.linalg.norm(result[0])
        assert abs(norm - 1.0) < 1e-5

    def test_embed_query(self):
        """Test the single-query embedding function."""
        from app.embeddings.embedder import embed_query
        result = embed_query("What is RAG?")
        assert result.shape == (1, 384)

    def test_similar_texts_have_high_similarity(self):
        """Test that semantically similar texts have high cosine similarity."""
        from app.embeddings.embedder import embed_texts
        texts = [
            "Machine learning is a subset of AI",
            "ML is part of artificial intelligence",
            "The weather is sunny today",
        ]
        embeddings = embed_texts(texts)
        # Cosine similarity (already normalized, so just dot product)
        sim_related = np.dot(embeddings[0], embeddings[1])
        sim_unrelated = np.dot(embeddings[0], embeddings[2])
        assert sim_related > sim_unrelated

    def test_get_embedding_dimension(self):
        """Test embedding dimension constant."""
        from app.embeddings.embedder import get_embedding_dimension
        assert get_embedding_dimension() == 384
