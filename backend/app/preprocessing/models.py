"""Pydantic models for the preprocessing (chunking) layer."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChunkObject(BaseModel):
    """Represents a text chunk from a processed document."""

    chunk_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    chunk_index: int
    text: str
    token_count: int
    source_filename: str
    page_number: int = 1
