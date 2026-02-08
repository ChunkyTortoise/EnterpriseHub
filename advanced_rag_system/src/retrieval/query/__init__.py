"""Query enhancement module for advanced retrieval capabilities.

This module provides comprehensive query enhancement features including:
- Query expansion using synonyms and semantic similarity
- HyDE (Hypothetical Document Embedding) for improved semantic matching
- Query classification for intelligent routing and strategy selection
"""

from .classifier import ClassificationResult, ClassifierConfig, QueryClassifier, QueryType
from .expansion import ExpansionConfig, QueryExpander
from .hyde import HyDEConfig, HyDEGenerator, LLMProvider, MockLLMProvider

__all__ = [
    # Query Expansion
    "QueryExpander",
    "ExpansionConfig",
    # HyDE (Hypothetical Document Embedding)
    "HyDEGenerator",
    "HyDEConfig",
    "MockLLMProvider",
    "LLMProvider",
    # Query Classification
    "QueryClassifier",
    "ClassifierConfig",
    "QueryType",
    "ClassificationResult",
]
