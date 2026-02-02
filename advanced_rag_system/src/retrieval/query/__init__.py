"""Query enhancement module for advanced retrieval capabilities.

This module provides comprehensive query enhancement features including:
- Query expansion using synonyms and semantic similarity
- HyDE (Hypothetical Document Embedding) for improved semantic matching
- Query classification for intelligent routing and strategy selection
"""

from .expansion import QueryExpander, ExpansionConfig
from .hyde import HyDEGenerator, HyDEConfig, MockLLMProvider, LLMProvider
from .classifier import QueryClassifier, ClassifierConfig, QueryType, ClassificationResult

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