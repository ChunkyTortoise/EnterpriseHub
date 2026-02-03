"""Dense retrieval module using vector embeddings and similarity search.

This module provides dense (semantic) retrieval capabilities using
vector embeddings and similarity search.

When ChromaDB is available (pydantic v1 / Python <3.14), the production
DenseRetriever uses ChromaDB + OpenAI embeddings. When ChromaDB is
unavailable, MockDenseRetriever provides an in-memory fallback that
works without external API dependencies.

The production DenseRetriever can always be imported directly from
src.retrieval.dense.dense_retriever for explicit use with InMemoryVectorStore.
"""

import logging

from .dense_retriever_mock import MockDenseRetriever

logger = logging.getLogger(__name__)

# Use production DenseRetriever only when ChromaDB is fully functional.
# This preserves the original fallback behavior: tests and dev environments
# without working ChromaDB use MockDenseRetriever automatically.
try:
    import chromadb  # noqa: F401 — triggers pydantic BaseSettings check
    from .dense_retriever import DenseRetriever
except (ImportError, Exception) as e:
    logger.warning(
        "Production DenseRetriever unavailable (ChromaDB dependency issue: %s). "
        "Using MockDenseRetriever.",
        e,
    )
    DenseRetriever = MockDenseRetriever  # type: ignore[misc,assignment]

__all__ = ["DenseRetriever", "MockDenseRetriever"]
