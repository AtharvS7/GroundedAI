"""Pydantic models for the ingestion layer."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PageObject(BaseModel):
    """Represents a single page of a parsed document."""

    page_number: int
    raw_text: str
    word_count: int = 0

    def model_post_init(self, __context: object) -> None:
        if self.word_count == 0 and self.raw_text:
            self.word_count = len(self.raw_text.split())


class DocumentObject(BaseModel):
    """Represents a fully parsed document."""

    document_id: UUID = Field(default_factory=uuid4)
    source_filename: str
    file_type: Literal["pdf", "docx", "txt"]
    total_pages: int
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    pages: List[PageObject]

    @property
    def full_text(self) -> str:
        """Return concatenated text from all pages."""
        return "\n\n".join(p.raw_text for p in self.pages if p.raw_text)

    @property
    def total_words(self) -> int:
        """Return total word count across all pages."""
        return sum(p.word_count for p in self.pages)
