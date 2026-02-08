"""
Retrieval module for Advanced RAG System.

This module provides various retrieval strategies including:
- Dense retrieval using vector embeddings
- Sparse retrieval using BM25/TF-IDF
- Hybrid retrieval combining multiple methods
- Query expansion and enhancement
"""

# Phase 2 imports - sparse retrieval
# Phase 2/3 imports - dense retrieval
from .dense import DenseRetriever

# Phase 2 imports - hybrid retrieval
from .hybrid import (
    FusionConfig,
    HybridSearchConfig,
    HybridSearcher,
    ReciprocalRankFusion,
    WeightedScoreFusion,
    deduplicate_results,
    normalize_scores,
)

# Phase 3 imports - query enhancement
from .query import HyDEGenerator, QueryExpander
from .sparse import BM25Config, BM25Index, TextPreprocessor

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
    "DenseRetriever",
    "QueryExpander",
    "HyDEGenerator",
]
