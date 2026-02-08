"""Embedding module for Advanced RAG System.

Provides embedding generation capabilities with support for
multiple providers, caching, and batch optimization.
"""

from src.embeddings.base import EmbeddingConfig, EmbeddingProvider
from src.embeddings.cache import EmbeddingCache
from src.embeddings.openai_provider import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "EmbeddingConfig",
    "OpenAIEmbeddingProvider",
    "EmbeddingCache",
]
