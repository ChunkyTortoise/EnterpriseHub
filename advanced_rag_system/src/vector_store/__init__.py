"""Vector store module for Advanced RAG System.

Provides vector storage and retrieval capabilities with support
for multiple backends and metadata filtering.
"""

from src.vector_store.base import VectorStore, VectorStoreConfig, SearchOptions

# ChromaVectorStore import is optional due to chromadb compatibility issues
# with newer Python versions (3.14+)
try:
    from src.vector_store.chroma_store import ChromaVectorStore
    __all__ = [
        "VectorStore",
        "VectorStoreConfig",
        "SearchOptions",
        "ChromaVectorStore",
    ]
except ImportError:
    # ChromaDB not available - use base VectorStore only
    __all__ = [
        "VectorStore",
        "VectorStoreConfig",
        "SearchOptions",
    ]