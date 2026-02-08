"""Core type definitions for Advanced RAG System.

This module defines the fundamental data structures used throughout
the RAG system, including documents, queries, and search results.
All types are Pydantic v2 models with strict validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentType(str, Enum):
    """Enumeration of supported document types."""

    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CODE = "code"


class QueryType(str, Enum):
    """Enumeration of query types for routing optimization."""

    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    PROCEDURAL = "procedural"
    EXPLORATORY = "exploratory"


class Metadata(BaseModel):
    """Metadata for documents and chunks.

    Attributes:
        source: Original source identifier (e.g., file path, URL)
        title: Document title
        author: Document author/creator
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        language: ISO 639-1 language code
        tags: List of tags/categories
        custom: Additional custom metadata fields
    """

    model_config = ConfigDict(extra="allow")

    source: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")
    tags: List[str] = Field(default_factory=list)
    custom: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("tags", mode="before")
    @classmethod
    def _validate_tags(cls, v: Optional[Union[List[str], str]]) -> List[str]:
        """Ensure tags is always a list of strings."""
        if v is None:
            return []
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return [str(tag) for tag in v]


class DocumentChunk(BaseModel):
    """A chunk of a document with embedding support.

    Attributes:
        id: Unique identifier for the chunk
        document_id: Reference to parent document
        content: Text content of the chunk
        embedding: Optional vector embedding
        metadata: Chunk-specific metadata
        index: Position of chunk within document
        token_count: Number of tokens in chunk
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str = Field(..., min_length=1)
    embedding: Optional[List[float]] = None
    metadata: Metadata = Field(default_factory=Metadata)
    index: int = Field(default=0, ge=0)
    token_count: int = Field(default=0, ge=0)

    @field_validator("content")
    @classmethod
    def _validate_content(cls, v: str) -> str:
        """Validate and clean content."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Content cannot be empty or whitespace only")
        return cleaned

    @field_validator("embedding")
    @classmethod
    def _validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding vector if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("Embedding vector cannot be empty")
        return v


class Document(BaseModel):
    """A complete document with chunks.

    Attributes:
        id: Unique identifier for the document
        content: Full document content
        chunks: List of document chunks
        metadata: Document metadata
        doc_type: Type of document
        embedding: Optional document-level embedding
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., min_length=1)
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Metadata = Field(default_factory=Metadata)
    doc_type: DocumentType = Field(default=DocumentType.TEXT)
    embedding: Optional[List[float]] = None

    @field_validator("content")
    @classmethod
    def _validate_content(cls, v: str) -> str:
        """Validate document content."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Document content cannot be empty")
        return cleaned

    def add_chunk(
        self,
        content: str,
        index: int = 0,
        metadata: Optional[Metadata] = None,
        embedding: Optional[List[float]] = None,
    ) -> DocumentChunk:
        """Add a new chunk to the document.

        Args:
            content: Chunk content
            index: Position index
            metadata: Optional chunk metadata
            embedding: Optional pre-computed embedding

        Returns:
            The created DocumentChunk
        """
        chunk = DocumentChunk(
            document_id=self.id,
            content=content,
            index=index,
            metadata=metadata or Metadata(),
            embedding=embedding,
        )
        self.chunks.append(chunk)
        return chunk

    def get_chunk_count(self) -> int:
        """Return the number of chunks in the document."""
        return len(self.chunks)


class Query(BaseModel):
    """A search query with routing information.

    Attributes:
        id: Unique query identifier
        text: Query text
        query_type: Type of query for routing
        metadata: Query metadata
        filters: Optional metadata filters
        top_k: Number of results to return
        threshold: Minimum similarity threshold
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    text: str = Field(..., min_length=1)
    query_type: QueryType = Field(default=QueryType.FACTUAL)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("text")
    @classmethod
    def _validate_text(cls, v: str) -> str:
        """Validate query text."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Query text cannot be empty")
        return cleaned


class SearchRequest(BaseModel):
    """Complete search request with all parameters.

    Attributes:
        query: The search query
        collection: Vector store collection name
        include_metadata: Whether to include metadata in results
        include_embeddings: Whether to include embeddings in results
        rerank: Whether to apply re-ranking
        hybrid_search: Whether to use hybrid search
    """

    model_config = ConfigDict(extra="forbid")

    query: Query
    collection: str = Field(default="default", min_length=1)
    include_metadata: bool = True
    include_embeddings: bool = False
    rerank: bool = False
    hybrid_search: bool = False


class SearchResult(BaseModel):
    """Single search result with relevance scoring.

    Attributes:
        chunk: The matched document chunk
        score: Similarity score (0-1)
        rank: Result rank position
        distance: Raw vector distance
        explanation: Optional explanation of match
    """

    model_config = ConfigDict(extra="forbid")

    chunk: DocumentChunk
    score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1)
    distance: float = Field(..., ge=0.0)
    explanation: Optional[str] = None


class SearchResponse(BaseModel):
    """Complete search response with results and metadata.

    Attributes:
        request_id: Unique request identifier
        query: Original query
        results: List of search results
        total_results: Total number of results found
        search_time_ms: Search execution time in milliseconds
        metadata: Response metadata
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(default_factory=uuid4)
    query: Query
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = Field(default=0, ge=0)
    search_time_ms: float = Field(default=0.0, ge=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_top_k(self, k: int = 5) -> List[SearchResult]:
        """Get top k results.

        Args:
            k: Number of results to return

        Returns:
            List of top k search results
        """
        return self.results[:k]

    def get_high_confidence_results(self, threshold: float = 0.8) -> List[SearchResult]:
        """Filter results by confidence threshold.

        Args:
            threshold: Minimum score threshold

        Returns:
            List of results above threshold
        """
        return [r for r in self.results if r.score >= threshold]
