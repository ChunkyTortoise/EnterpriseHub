"""Dense retrieval module using vector embeddings and similarity search.

This module provides dense (semantic) retrieval capabilities using
vector embeddings and similarity search through ChromaDB.
"""

import logging

from .dense_retriever_mock import MockDenseRetriever

logger = logging.getLogger(__name__)

# Try importing production DenseRetriever, fallback to mock on ImportError only
try:
    from .dense_retriever import DenseRetriever
except ImportError as e:
    logger.warning("Production DenseRetriever unavailable (missing dependency: %s). Using MockDenseRetriever.", e)
    DenseRetriever = MockDenseRetriever  # type: ignore[misc,assignment]

__all__ = ["DenseRetriever", "MockDenseRetriever"]
