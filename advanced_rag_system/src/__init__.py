"""Advanced RAG System - Phase 1 Implementation.

This package provides the foundation for an enterprise-grade
Retrieval-Augmented Generation system with type safety,
performance optimization, and production-ready architecture.

Author: Principal AI Engineer Portfolio Project
Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "Principal AI Engineer"

from src.core.types import Document, DocumentChunk, Metadata, Query, SearchRequest, SearchResult
from src.core.config import Settings, get_settings
from src.core.exceptions import RAGException, EmbeddingError, VectorStoreError

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
]