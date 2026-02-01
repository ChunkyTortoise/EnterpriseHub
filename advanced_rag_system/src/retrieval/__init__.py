"""
Retrieval module for Advanced RAG System.

This module provides various retrieval strategies including:
- Dense retrieval using vector embeddings
- Sparse retrieval using BM25/TF-IDF
- Hybrid retrieval combining multiple methods
- Query expansion and enhancement
"""

from .dense import DenseRetriever
from .sparse import BM25Retriever, TFIDFRetriever
from .hybrid import HybridRetriever, RRFusion
from .query import QueryExpander, HyDEGenerator

__all__ = [
    "DenseRetriever",
    "BM25Retriever",
    "TFIDFRetriever",
    "HybridRetriever",
    "RRFusion",
    "QueryExpander",
    "HyDEGenerator",
]
