"""Advanced RAG patterns module.

This module provides advanced retrieval patterns:
- Self-querying: Query decomposition and metadata filtering
- Contextual compression: Reduce context size while preserving relevance

Example:
    ```python
    from src.retrieval.advanced import (
        SelfQueryingSearcher,
        ContextualCompressor,
        CompressionStrategy,
    )

    # Self-querying with decomposition
    sq_searcher = SelfQueryingSearcher(base_searcher)
    result = await sq_searcher.search(
        "What are the differences between product A and product B?"
    )

    # Contextual compression
    compressor = ContextualCompressor()
    compressed = await compressor.compress_results(
        results=search_results,
        query="Python benefits",
        strategy=CompressionStrategy.EXTRACTIVE,
    )
    ```
"""

from .contextual_compressor import (
    CompressedDocument,
    CompressionConfig,
    CompressionResult,
    CompressionStrategy,
    ContextualCompressor,
    EnhancedSearcher,
    ExtractiveCompressor,
    RelevanceScore,
    RelevanceScorer,
    ScoringMethod,
    TokenCounter,
)
from .self_querying import (
    DecomposedQuery,
    FilterOperator,
    MetadataFilter,
    QueryDecomposer,
    QueryOperator,
    SelfQueryingResult,
    SelfQueryingSearcher,
    SubQuery,
)

__all__ = [
    # Self-querying
    "SelfQueryingSearcher",
    "SelfQueryingResult",
    "QueryDecomposer",
    "DecomposedQuery",
    "SubQuery",
    "MetadataFilter",
    "FilterOperator",
    "QueryOperator",
    # Contextual compression
    "ContextualCompressor",
    "CompressionResult",
    "CompressionStrategy",
    "CompressedDocument",
    "CompressionConfig",
    "EnhancedSearcher",
    "ExtractiveCompressor",
    "RelevanceScore",
    "RelevanceScorer",
    "ScoringMethod",
    "TokenCounter",
]
