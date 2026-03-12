"""Tests for the text chunker module."""

import pytest
from app.ingestion.document_parser import parse_document
from app.preprocessing.chunker import chunk_document, count_tokens


class TestChunker:
    """Test suite for recursive token-based chunking."""

    def test_chunk_short_text(self, sample_txt_bytes):
        """Test chunking a short text produces reasonable chunks."""
        document = parse_document("test.txt", sample_txt_bytes)
        chunks = chunk_document(document, chunk_size_tokens=50, overlap_tokens=10)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.text
            assert chunk.token_count > 0
            assert chunk.source_filename == "test.txt"

    def test_chunk_preserves_metadata(self, sample_pdf_bytes):
        """Test that chunk metadata matches document."""
        document = parse_document("doc.pdf", sample_pdf_bytes)
        chunks = chunk_document(document, chunk_size_tokens=50, overlap_tokens=10)
        for chunk in chunks:
            assert str(chunk.document_id) == str(document.document_id)
            assert chunk.source_filename == "doc.pdf"
            assert chunk.page_number >= 1

    def test_chunk_indices_sequential(self, sample_txt_bytes):
        """Test that chunk indices are sequential."""
        document = parse_document("test.txt", sample_txt_bytes)
        chunks = chunk_document(document, chunk_size_tokens=20, overlap_tokens=5)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_count_tokens(self):
        """Test token counting utility."""
        token_count = count_tokens("Hello world, this is a test.")
        assert token_count > 0

    def test_large_text_produces_multiple_chunks(self):
        """Test that large text is split into multiple chunks."""
        big_text = " ".join(["The quick brown fox jumps over the lazy dog."] * 100)
        from app.ingestion.models import DocumentObject, PageObject
        document = DocumentObject(
            source_filename="big.txt",
            file_type="txt",
            total_pages=1,
            pages=[PageObject(page_number=1, raw_text=big_text)],
        )
        chunks = chunk_document(document, chunk_size_tokens=50, overlap_tokens=10)
        assert len(chunks) > 1

    def test_empty_document_produces_no_chunks(self):
        """Test that empty documents produce no chunks."""
        from app.ingestion.models import DocumentObject, PageObject
        document = DocumentObject(
            source_filename="empty.txt",
            file_type="txt",
            total_pages=1,
            pages=[PageObject(page_number=1, raw_text="")],
        )
        chunks = chunk_document(document)
        assert len(chunks) == 0
