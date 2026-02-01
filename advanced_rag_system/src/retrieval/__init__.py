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

# Planned imports for future phases (commented out until implemented)
# from .dense import DenseRetriever
# from .hybrid import HybridRetriever, RRFusion
# from .query import QueryExpander, HyDEGenerator

__all__ = [
    "BM25Index",
    "BM25Config",
    "TextPreprocessor",
    # Future exports:
    # "DenseRetriever",
    # "HybridRetriever",
    # "RRFusion",
    # "QueryExpander",
    # "HyDEGenerator",
]
