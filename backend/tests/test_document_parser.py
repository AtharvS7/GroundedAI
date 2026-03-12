"""Tests for the document parser module."""

import pytest
from app.ingestion.document_parser import (
    ParseError,
    UnsupportedFormatError,
    parse_document,
)


class TestDocumentParser:
    """Test suite for document parsing across formats."""

    def test_parse_pdf(self, sample_pdf_bytes):
        """Test PDF parsing extracts text and metadata."""
        result = parse_document("test.pdf", sample_pdf_bytes)
        assert result.file_type == "pdf"
        assert result.source_filename == "test.pdf"
        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert "test PDF document" in result.pages[0].raw_text

    def test_parse_txt(self, sample_txt_bytes):
        """Test TXT parsing with UTF-8 content."""
        result = parse_document("test.txt", sample_txt_bytes)
        assert result.file_type == "txt"
        assert result.total_pages == 1
        assert "GroundedAI" in result.pages[0].raw_text

    def test_parse_docx(self, sample_docx_bytes):
        """Test DOCX parsing extracts paragraphs."""
        result = parse_document("test.docx", sample_docx_bytes)
        assert result.file_type == "docx"
        assert result.total_pages == 1
        assert "test DOCX document" in result.pages[0].raw_text

    def test_unsupported_format(self):
        """Test that unsupported formats raise UnsupportedFormatError."""
        with pytest.raises(UnsupportedFormatError):
            parse_document("test.xyz", b"content", file_type="xyz")

    def test_auto_detect_file_type(self, sample_txt_bytes):
        """Test automatic file type detection from extension."""
        result = parse_document("readme.txt", sample_txt_bytes)
        assert result.file_type == "txt"

    def test_document_object_properties(self, sample_txt_bytes):
        """Test DocumentObject computed properties."""
        result = parse_document("test.txt", sample_txt_bytes)
        assert result.total_words > 0
        assert len(result.full_text) > 0

    def test_empty_pdf(self):
        """Test parsing an empty PDF."""
        import fitz
        doc = fitz.open()
        doc.new_page()
        pdf_bytes = doc.tobytes()
        doc.close()
        result = parse_document("empty.pdf", pdf_bytes)
        assert result.total_pages == 1
