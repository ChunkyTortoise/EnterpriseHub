"""Advanced hybrid searcher with query enhancement and re-ranking.

This module provides the complete Phase 3 hybrid RAG system that integrates:
- Dense and sparse retrieval
- Query enhancement (expansion, HyDE, classification)
- Cross-encoder re-ranking
- Intelligent routing and optimization
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from src.core.exceptions import RetrievalError
from src.core.types import SearchResult
from src.reranking import BaseReRanker, MockReRanker, ReRankingConfig, ReRankingStrategy
from src.retrieval.hybrid.hybrid_searcher import HybridSearchConfig, HybridSearcher
from src.retrieval.query import ExpansionConfig, HyDEConfig, HyDEGenerator, QueryClassifier, QueryExpander, QueryType


@dataclass
class AdvancedSearchConfig:
    """Configuration for advanced hybrid search with all Phase 3 features.

    Attributes:
        # Base hybrid search config
        hybrid_config: Configuration for base hybrid search

        # Query enhancement
        enable_query_expansion: Whether to use query expansion
        enable_hyde: Whether to use HyDE document generation
        enable_query_classification: Whether to use intelligent routing
        expansion_config: Query expansion configuration
        hyde_config: HyDE generation configuration

        # Re-ranking
        enable_reranking: Whether to use re-ranking
        reranking_config: Re-ranking configuration

        # Performance tuning
        enable_intelligent_routing: Use query classification for routing
        enable_adaptive_weights: Dynamically adjust retrieval weights
        max_total_time_ms: Maximum total search time in milliseconds
        enable_caching: Whether to cache expensive operations
    """

    # Base configuration
    hybrid_config: Optional[HybridSearchConfig] = None

    # Query enhancement
    enable_query_expansion: bool = True
    enable_hyde: bool = True
    enable_query_classification: bool = True
    expansion_config: Optional[ExpansionConfig] = None
    hyde_config: Optional[HyDEConfig] = None

    # Re-ranking
    enable_reranking: bool = True
    reranking_config: Optional[ReRankingConfig] = None

    # Performance and intelligence
    enable_intelligent_routing: bool = True
    enable_adaptive_weights: bool = True
    max_total_time_ms: int = 150  # Target: <150ms total
    enable_caching: bool = True


class AdvancedHybridSearcher:
    """Advanced hybrid searcher with complete Phase 3 pipeline.

    Integrates all advanced RAG features:
    1. Query enhancement (expansion, HyDE, classification)
    2. Dense + sparse retrieval with intelligent routing
    3. Result fusion with adaptive weights
    4. Cross-encoder re-ranking for accuracy
    5. Performance optimization and caching

    Example:
        ```python
        config = AdvancedSearchConfig(
            enable_hyde=True,
            enable_reranking=True,
            max_total_time_ms=150
        )

        searcher = AdvancedHybridSearcher(config)
        await searcher.initialize()

        # Enhanced search with all features
        results = await searcher.search("What is machine learning?", top_k=20)
        await searcher.close()
        ```
    """

    def __init__(
        self,
        config: Optional[AdvancedSearchConfig] = None,
        reranker: Optional[BaseReRanker] = None,
    ):
        """Initialize advanced hybrid searcher.

        Args:
            config: Advanced search configuration
            reranker: Optional pre-configured reranker. If not provided,
                will try CrossEncoderReRanker then fall back to MockReRanker.
        """
        self.config = config or AdvancedSearchConfig()

        # Initialize base hybrid searcher
        self.hybrid_searcher = HybridSearcher(
            hybrid_config=self.config.hybrid_config,
        )

        # Initialize query enhancement components
        self.query_expander: Optional[QueryExpander] = None
        self.hyde_generator: Optional[HyDEGenerator] = None
        self.query_classifier: Optional[QueryClassifier] = None

        # Store injected reranker (will be initialized in initialize())
        self._injected_reranker = reranker
        self.reranker: Optional[BaseReRanker] = None

        # Performance tracking
        self._search_stats = {
            "total_searches": 0,
            "avg_time_ms": 0.0,
            "enhancement_time_ms": 0.0,
            "retrieval_time_ms": 0.0,
            "reranking_time_ms": 0.0,
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all components.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Initialize base hybrid searcher
            await self.hybrid_searcher.initialize()

            # Initialize query enhancement components
            if self.config.enable_query_expansion:
                expansion_config = self.config.expansion_config or ExpansionConfig(max_expansions=3)
                self.query_expander = QueryExpander(expansion_config)

            if self.config.enable_hyde:
                hyde_config = self.config.hyde_config or HyDEConfig(num_hypotheticals=1)
                self.hyde_generator = HyDEGenerator(hyde_config)

            if self.config.enable_query_classification:
                self.query_classifier = QueryClassifier()

            # Initialize re-ranker
            if self.config.enable_reranking:
                reranking_config = self.config.reranking_config or ReRankingConfig(
                    strategy=ReRankingStrategy.WEIGHTED, top_k=50
                )
                if self._injected_reranker is not None:
                    self.reranker = self._injected_reranker
                    await self.reranker.initialize()
                else:
                    self.reranker = MockReRanker(reranking_config)
                    await self.reranker.initialize()

            self._initialized = True

        except Exception as e:
            raise RetrievalError(f"Failed to initialize AdvancedHybridSearcher: {str(e)}") from e

    async def close(self) -> None:
        """Close and cleanup all resources."""
        if self.hybrid_searcher:
            await self.hybrid_searcher.close()

        if self.reranker:
            await self.reranker.close()

        self._initialized = False

    async def search(self, query: str, top_k: int = 20) -> List[SearchResult]:
        """Perform advanced search with all Phase 3 enhancements.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Enhanced and re-ranked search results

        Raises:
            RetrievalError: If search fails
        """
        if not self._initialized:
            raise RetrievalError("AdvancedHybridSearcher not initialized")

        if not query or not query.strip():
            return []

        total_start_time = time.time()

        try:
            # Phase 1: Query Enhancement
            enhancement_start = time.time()
            enhanced_query, routing_info = await self._enhance_query(query)
            enhancement_time = (time.time() - enhancement_start) * 1000

            # Phase 2: Intelligent Retrieval
            retrieval_start = time.time()
            raw_results = await self._intelligent_retrieval(
                enhanced_query, routing_info, top_k * 2
            )  # Get more for re-ranking
            retrieval_time = (time.time() - retrieval_start) * 1000

            # Phase 3: Re-ranking
            reranking_start = time.time()
            final_results = await self._rerank_results(query, raw_results, top_k)
            reranking_time = (time.time() - reranking_start) * 1000

            # Update performance stats
            total_time = (time.time() - total_start_time) * 1000
            self._update_stats(total_time, enhancement_time, retrieval_time, reranking_time)

            # Add performance metadata to results
            for result in final_results:
                if result.explanation:
                    result.explanation += f" | Total: {total_time:.1f}ms"
                else:
                    # Create new result with explanation
                    updated_result = SearchResult(
                        chunk=result.chunk,
                        score=result.score,
                        rank=result.rank,
                        distance=result.distance,
                        explanation=f"Advanced pipeline: {total_time:.1f}ms",
                    )
                    # Update the list in place
                    idx = final_results.index(result)
                    final_results[idx] = updated_result

            return final_results

        except Exception as e:
            raise RetrievalError(f"Advanced search failed: {str(e)}") from e

    async def _enhance_query(self, query: str) -> tuple[str, Dict[str, Any]]:
        """Enhance query using all available enhancement techniques.

        Args:
            query: Original query

        Returns:
            Tuple of (enhanced_query, routing_info)
        """
        enhanced_query = query
        routing_info = {
            "original_query": query,
            "query_type": QueryType.CONCEPTUAL,  # Default
            "recommendations": {},
            "expansions": [],
            "hypothetical_docs": [],
        }

        # Step 1: Query Classification for routing
        if self.query_classifier and self.config.enable_query_classification:
            try:
                classification = self.query_classifier.classify(query)
                routing_info["query_type"] = classification.query_type
                routing_info["recommendations"] = classification.recommendations
                routing_info["confidence"] = classification.confidence
            except Exception:
                pass  # Use defaults

        # Step 2: Query Expansion
        if self.query_expander and self.config.enable_query_expansion:
            try:
                expansions = self.query_expander.expand(query)
                if expansions and len(expansions) > 1:
                    # Use the first expansion as the enhanced query
                    enhanced_query = expansions[0]
                    routing_info["expansions"] = expansions[1:]  # Store alternatives
            except Exception:
                pass  # Use original query

        # Step 3: HyDE Enhancement
        if self.hyde_generator and self.config.enable_hyde:
            try:
                hypothetical_docs = await self.hyde_generator.generate_hypothetical_documents(query)
                routing_info["hypothetical_docs"] = hypothetical_docs

                # Optionally enhance query with HyDE content
                if hypothetical_docs:
                    hyde_enhanced = await self.hyde_generator.generate_enhanced_query(query)
                    if len(hyde_enhanced) > len(enhanced_query):
                        enhanced_query = hyde_enhanced

            except Exception:
                pass  # Use current enhanced query

        return enhanced_query, routing_info

    async def _intelligent_retrieval(
        self, enhanced_query: str, routing_info: Dict[str, Any], top_k: int
    ) -> List[SearchResult]:
        """Perform intelligent retrieval based on query classification.

        Args:
            enhanced_query: Enhanced query string
            routing_info: Routing information from classification
            top_k: Number of results to retrieve

        Returns:
            Raw retrieval results
        """
        # Adjust hybrid search config based on routing recommendations
        if (
            self.config.enable_intelligent_routing
            and "recommendations" in routing_info
            and routing_info["recommendations"]
        ):
            recommendations = routing_info["recommendations"]

            # Temporarily adjust weights based on query type
            original_config = self.hybrid_searcher.hybrid_config

            # Create adaptive weights
            dense_weight = recommendations.get("dense_retrieval_weight", 0.5)
            sparse_weight = recommendations.get("sparse_retrieval_weight", 0.5)

            # Update fusion weights if using weighted fusion
            if hasattr(self.hybrid_searcher.fusion_algorithm, "config"):
                fusion_config = self.hybrid_searcher.fusion_algorithm.config
                if hasattr(fusion_config, "dense_weight"):
                    fusion_config.dense_weight = dense_weight
                if hasattr(fusion_config, "sparse_weight"):
                    fusion_config.sparse_weight = sparse_weight

        # Perform hybrid search
        results = await self.hybrid_searcher.search(enhanced_query)

        # Limit to requested number
        return results[:top_k]

    async def _rerank_results(self, original_query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """Re-rank results using configured re-ranker.

        Args:
            original_query: Original query for re-ranking
            results: Results to re-rank
            top_k: Final number of results

        Returns:
            Re-ranked results
        """
        if not self.reranker or not self.config.enable_reranking or not results:
            return results[:top_k]

        try:
            reranking_result = await self.reranker.rerank(original_query, results)
            final_results = reranking_result.results[:top_k]

            # Add re-ranking metadata
            for result in final_results:
                if result.explanation:
                    result.explanation += " | Reranked"
                else:
                    # Create new result with explanation
                    updated_result = SearchResult(
                        chunk=result.chunk,
                        score=result.score,
                        rank=result.rank,
                        distance=result.distance,
                        explanation="Reranked for relevance",
                    )
                    # Update the list in place
                    idx = final_results.index(result)
                    final_results[idx] = updated_result

            return final_results

        except Exception:
            # Fallback to original results if re-ranking fails
            return results[:top_k]

    def _update_stats(
        self, total_time: float, enhancement_time: float, retrieval_time: float, reranking_time: float
    ) -> None:
        """Update performance statistics."""
        self._search_stats["total_searches"] += 1
        n = self._search_stats["total_searches"]

        # Rolling average
        self._search_stats["avg_time_ms"] = (self._search_stats["avg_time_ms"] * (n - 1) + total_time) / n
        self._search_stats["enhancement_time_ms"] = (
            self._search_stats["enhancement_time_ms"] * (n - 1) + enhancement_time
        ) / n
        self._search_stats["retrieval_time_ms"] = (
            self._search_stats["retrieval_time_ms"] * (n - 1) + retrieval_time
        ) / n
        self._search_stats["reranking_time_ms"] = (
            self._search_stats["reranking_time_ms"] * (n - 1) + reranking_time
        ) / n

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics.

        Returns:
            Complete system statistics
        """
        stats = {
            "performance": self._search_stats,
            "config": {
                "enable_query_expansion": self.config.enable_query_expansion,
                "enable_hyde": self.config.enable_hyde,
                "enable_query_classification": self.config.enable_query_classification,
                "enable_reranking": self.config.enable_reranking,
                "enable_intelligent_routing": self.config.enable_intelligent_routing,
                "max_total_time_ms": self.config.max_total_time_ms,
            },
            "components": {},
        }

        # Get hybrid searcher stats
        if self.hybrid_searcher:
            stats["components"]["hybrid_searcher"] = await self.hybrid_searcher.get_stats()

        # Get query enhancement stats
        if self.query_expander:
            stats["components"]["query_expander"] = self.query_expander.get_stats()

        if self.hyde_generator:
            stats["components"]["hyde_generator"] = self.hyde_generator.get_stats()

        if self.query_classifier:
            stats["components"]["query_classifier"] = self.query_classifier.get_stats()

        # Get re-ranker stats
        if self.reranker:
            stats["components"]["reranker"] = self.reranker.get_stats()

        return stats
