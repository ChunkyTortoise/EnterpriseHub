"""Re-ranking module for improving retrieval result relevance.

This module provides comprehensive re-ranking capabilities including:
- Base re-ranker interface and utilities
- Cross-encoder re-ranking using sentence-transformers models
- Cohere API re-ranking using cloud-based service
- Mock re-ranker for development and testing
"""

from .base import BaseReRanker, MockReRanker, ReRankingConfig, ReRankingResult, ReRankingStrategy
from .cohere_reranker import CohereConfig, CohereReRanker
from .cross_encoder import CrossEncoderReRanker

__all__ = [
    # Base classes and utilities
    "BaseReRanker",
    "ReRankingConfig",
    "ReRankingResult",
    "ReRankingStrategy",
    "MockReRanker",
    # Cross-encoder re-ranker
    "CrossEncoderReRanker",
    # Cohere API re-ranker
    "CohereReRanker",
    "CohereConfig",
]
