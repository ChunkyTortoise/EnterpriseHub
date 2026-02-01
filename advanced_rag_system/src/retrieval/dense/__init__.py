"""Dense retrieval module using vector embeddings and similarity search.

This module provides dense (semantic) retrieval capabilities using
vector embeddings and similarity search through ChromaDB.
"""

# Try importing production DenseRetriever, fallback to mock
try:
    from .dense_retriever import DenseRetriever
    __all__ = ["DenseRetriever"]
except Exception:
    # Fallback to mock version
    from .dense_retriever_mock import MockDenseRetriever as DenseRetriever
    __all__ = ["DenseRetriever"]
    print("⚠️  Dense retrieval module using mock implementation")