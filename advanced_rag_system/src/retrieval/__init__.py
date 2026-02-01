"""
Retrieval module for Advanced RAG System.

This module provides various retrieval strategies including:
- Dense retrieval using vector embeddings
- Sparse retrieval using BM25/TF-IDF
- Hybrid retrieval combining multiple methods
- Query expansion and enhancement
"""

# Phase 2 imports - sparse retrieval
from .sparse import BM25Index, BM25Config, TextPreprocessor

# Phase 2 imports - hybrid retrieval
from .hybrid import (
    HybridSearcher,
    HybridSearchConfig,
    FusionConfig,
    ReciprocalRankFusion,
    WeightedScoreFusion,
    deduplicate_results,
    normalize_scores,
)

# Planned imports for future phases (commented out until implemented)
# from .dense import DenseRetriever
# from .query import QueryExpander, HyDEGenerator

__all__ = [
    "BM25Index",
    "BM25Config",
    "TextPreprocessor",
    "HybridSearcher",
    "HybridSearchConfig",
    "FusionConfig",
    "ReciprocalRankFusion",
    "WeightedScoreFusion",
    "deduplicate_results",
    "normalize_scores",
    # Future exports:
    # "DenseRetriever",
    # "QueryExpander",
    # "HyDEGenerator",
]
