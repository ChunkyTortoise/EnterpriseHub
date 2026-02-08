"""Core module for Advanced RAG System.

Provides fundamental types, configuration, and exceptions
used throughout the system.
"""

from src.core.config import Settings, get_settings
from src.core.exceptions import (
    CacheError,
    ConfigurationError,
    EmbeddingError,
    RAGException,
    ValidationError,
    VectorStoreError,
)
from src.core.types import Document, DocumentChunk, Metadata, Query, SearchRequest, SearchResult

__all__ = [
    "Document",
    "DocumentChunk",
    "Metadata",
    "Query",
    "SearchRequest",
    "SearchResult",
    "Settings",
    "get_settings",
    "RAGException",
    "EmbeddingError",
    "VectorStoreError",
    "ConfigurationError",
    "ValidationError",
    "CacheError",
]
