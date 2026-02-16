"""Document contracts — shared across RAG and ingestion products."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Supported document types for ingestion."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CODE = "code"
    CSV = "csv"
    DOCX = "docx"


class DocumentChunk(BaseModel):
    """A chunk of a document with optional embedding."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    doc_id: str | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class DocumentMetadata(BaseModel):
    """Extensible metadata for documents."""

    model_config = ConfigDict(extra="allow")

    source: str | None = None
    title: str | None = None
    author: str | None = None
    doc_type: DocumentType = DocumentType.TEXT
    created_at: datetime | None = None
    language: str = "en"
