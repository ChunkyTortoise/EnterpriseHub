"""Vector store module for Advanced RAG System.

Provides vector storage and retrieval capabilities with support
for multiple backends and metadata filtering.
"""

from src.vector_store.base import VectorStore, VectorStoreConfig, SearchOptions
from src.vector_store.chroma_store import ChromaVectorStore

__all__ = [
    "VectorStore",
    "VectorStoreConfig",
    "SearchOptions",
    "ChromaVectorStore",
]