"""Multi-modal retrieval module for Advanced RAG System.

This module provides multi-modal search capabilities:
- Image retrieval using CLIP embeddings
- Structured data retrieval (CSV, JSON, tables)
- Unified orchestration across modalities
"""

from src.multimodal.image_retriever import (
    ImageRetriever,
    ImageRetrieverConfig,
    MockCLIPEmbeddingProvider,
)
from src.multimodal.structured_retriever import (
    StructuredQuery,
    StructuredRetriever,
    StructuredRetrieverConfig,
    TableSchema,
)
from src.multimodal.unified_retriever import (
    QueryModality,
    UnifiedRetriever,
    UnifiedRetrieverConfig,
    UnifiedSearchResult,
)

__all__ = [
    # Image retrieval
    "ImageRetriever",
    "ImageRetrieverConfig",
    "MockCLIPEmbeddingProvider",
    # Structured data retrieval
    "StructuredRetriever",
    "StructuredRetrieverConfig",
    "StructuredQuery",
    "TableSchema",
    # Unified retrieval
    "UnifiedRetriever",
    "UnifiedRetrieverConfig",
    "UnifiedSearchResult",
    "QueryModality",
]
