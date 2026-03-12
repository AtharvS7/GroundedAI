"""Tests for the evaluation module."""

import pytest
from app.evaluation.evaluator import (
    compute_bleu_4,
    compute_mrr,
    compute_precision_at_k,
    compute_recall_at_k,
    compute_rouge_l,
)


class TestEvaluator:
    """Test suite for evaluation metrics."""

    def test_rouge_l_identical(self):
        """Test ROUGE-L returns 1.0 for identical strings."""
        score = compute_rouge_l("hello world", "hello world")
        assert score > 0.99

    def test_rouge_l_different(self):
        """Test ROUGE-L returns low score for different strings."""
        score = compute_rouge_l("hello world", "foo bar baz")
        assert score < 0.5

    def test_bleu_4_identical(self):
        """Test BLEU-4 returns high score for identical strings."""
        text = "the cat sat on the mat in the sun"
        score = compute_bleu_4(text, text)
        assert score > 0.5

    def test_bleu_4_empty(self):
        """Test BLEU-4 returns 0 for empty strings."""
        assert compute_bleu_4("", "") == 0.0

    def test_precision_at_k(self):
        """Test Precision@k calculation."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "c", "f"]
        assert compute_precision_at_k(retrieved, relevant, 5) == 0.4

    def test_recall_at_k(self):
        """Test Recall@k calculation."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "c", "f"]
        result = compute_recall_at_k(retrieved, relevant, 5)
        assert abs(result - 2 / 3) < 1e-5

    def test_mrr(self):
        """Test MRR calculation."""
        # First relevant at position 3 (0-indexed: 2)
        retrieved = ["x", "y", "a", "b"]
        relevant = ["a"]
        assert abs(compute_mrr(retrieved, relevant) - 1 / 3) < 1e-5

    def test_mrr_first_position(self):
        """Test MRR when relevant is at first position."""
        retrieved = ["a", "b", "c"]
        relevant = ["a"]
        assert compute_mrr(retrieved, relevant) == 1.0

    def test_mrr_empty(self):
        """Test MRR returns 0 for empty inputs."""
        assert compute_mrr([], ["a"]) == 0.0
        assert compute_mrr(["a"], []) == 0.0
