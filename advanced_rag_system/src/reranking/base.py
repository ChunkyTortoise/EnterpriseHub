"""Base interface and utilities for re-ranking systems.

This module defines the common interface for all re-rankers and provides
shared utilities for improving retrieval result ranking accuracy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.types import SearchResult


class ReRankingStrategy(Enum):
    """Enumeration of re-ranking strategies.

    Different strategies for combining and weighting scores:
    - REPLACE: Replace original scores with reranker scores
    - WEIGHTED: Weighted combination of original and reranker scores
    - RECIPROCAL_RANK: Use reciprocal rank fusion approach
    - NORMALIZED: Normalize and combine scores
    """

    REPLACE = "replace"
    WEIGHTED = "weighted"
    RECIPROCAL_RANK = "reciprocal_rank"
    NORMALIZED = "normalized"


@dataclass
class ReRankingConfig:
    """Configuration for re-ranking operations.

    Attributes:
        strategy: Re-ranking strategy to use
        original_weight: Weight for original retrieval scores (0.0-1.0)
        reranker_weight: Weight for re-ranker scores (0.0-1.0)
        top_k: Maximum number of results to re-rank
        score_threshold: Minimum score threshold for re-ranking
        normalize_scores: Whether to normalize scores to [0,1] range
        batch_size: Batch size for processing large result sets
        timeout_seconds: Timeout for re-ranking operations
    """

    strategy: ReRankingStrategy = ReRankingStrategy.WEIGHTED
    original_weight: float = 0.3
    reranker_weight: float = 0.7
    top_k: int = 100
    score_threshold: float = 0.0
    normalize_scores: bool = True
    batch_size: int = 32
    timeout_seconds: int = 30


@dataclass
class ReRankingResult:
    """Result of a re-ranking operation.

    Attributes:
        results: Re-ranked search results
        original_count: Number of input results
        reranked_count: Number of results that were re-ranked
        processing_time_ms: Time taken for re-ranking in milliseconds
        model_info: Information about the re-ranking model used
        scores_changed: Whether any scores were modified
    """

    results: List[SearchResult]
    original_count: int
    reranked_count: int
    processing_time_ms: float
    model_info: Dict[str, Any]
    scores_changed: bool


class BaseReRanker(ABC):
    """Abstract base class for all re-ranking implementations.

    This class defines the common interface that all re-rankers must implement,
    ensuring consistency across different re-ranking approaches.
    """

    def __init__(self, config: Optional[ReRankingConfig] = None):
        """Initialize the re-ranker.

        Args:
            config: Re-ranking configuration
        """
        self.config = config or ReRankingConfig()

    @abstractmethod
    async def rerank(self, query: str, results: List[SearchResult]) -> ReRankingResult:
        """Re-rank search results for improved relevance.

        Args:
            query: Original search query
            results: Search results to re-rank

        Returns:
            Re-ranking result with improved ordering

        Raises:
            RetrievalError: If re-ranking fails
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the re-ranking model.

        Returns:
            Dictionary with model information
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the re-ranker (load models, establish connections, etc.).

        Raises:
            RetrievalError: If initialization fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources used by the re-ranker."""
        pass

    def _filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Filter results based on configuration criteria.

        Args:
            results: Input search results

        Returns:
            Filtered results
        """
        # Apply score threshold
        filtered = [r for r in results if r.score >= self.config.score_threshold]

        # Apply top-k limit
        return filtered[: self.config.top_k]

    def _normalize_scores(self, results: List[SearchResult]) -> List[SearchResult]:
        """Normalize scores to [0, 1] range.

        Args:
            results: Results with scores to normalize

        Returns:
            Results with normalized scores
        """
        if not results:
            return results

        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            # All scores are the same
            return results

        # Normalize to [0, 1]
        score_range = max_score - min_score
        normalized_results = []

        for result in results:
            normalized_score = (result.score - min_score) / score_range
            # Create new result with normalized score
            original_explanation = result.explanation or ""
            normalized_result = SearchResult(
                chunk=result.chunk,
                score=normalized_score,
                rank=result.rank,
                distance=result.distance,
                explanation=f"{original_explanation} | original_score={result.score:.4f}".strip(" |"),
            )
            normalized_results.append(normalized_result)

        return normalized_results

    def _combine_scores(
        self,
        original_results: List[SearchResult],
        reranked_scores: List[float],
        strategy: Optional[ReRankingStrategy] = None,
    ) -> List[SearchResult]:
        """Combine original scores with re-ranking scores.

        Args:
            original_results: Original search results
            reranked_scores: New scores from re-ranking
            strategy: Strategy for combining scores

        Returns:
            Results with combined scores
        """
        strategy = strategy or self.config.strategy

        if len(original_results) != len(reranked_scores):
            raise ValueError("Number of results and scores must match")

        combined_results = []

        for i, (result, rerank_score) in enumerate(zip(original_results, reranked_scores)):
            original_score = result.score

            if strategy == ReRankingStrategy.REPLACE:
                # Replace with reranker score
                final_score = rerank_score

            elif strategy == ReRankingStrategy.WEIGHTED:
                # Weighted combination
                final_score = self.config.original_weight * original_score + self.config.reranker_weight * rerank_score

            elif strategy == ReRankingStrategy.RECIPROCAL_RANK:
                # Use reciprocal rank fusion
                original_rank = i + 1  # 1-based ranking
                rrf_score = 1.0 / (60 + original_rank)  # RRF with k=60
                rerank_rank_score = 1.0 / (60 + (len(reranked_scores) - i))  # Higher rerank score = better rank
                final_score = (rrf_score + rerank_rank_score) / 2

            elif strategy == ReRankingStrategy.NORMALIZED:
                # Normalize both scores and combine
                if self.config.normalize_scores:
                    # Scores should already be normalized
                    final_score = (original_score + rerank_score) / 2
                else:
                    # Min-max normalize on the fly
                    final_score = (original_score + rerank_score) / 2

            else:
                raise ValueError(f"Unknown re-ranking strategy: {strategy}")

            # Create new result with combined score
            combined_result = SearchResult(
                chunk=result.chunk,
                score=final_score,
                rank=i + 1,  # Will be updated after sorting
                distance=result.distance,
                explanation=f"Reranked with {strategy.value} strategy",
            )
            combined_results.append(combined_result)

        return combined_results

    def _update_ranks(self, results: List[SearchResult]) -> List[SearchResult]:
        """Update rank fields based on current order.

        Args:
            results: Results to update ranks for

        Returns:
            Results with updated ranks
        """
        updated_results = []
        for i, result in enumerate(results):
            updated_result = SearchResult(
                chunk=result.chunk,
                score=result.score,
                rank=i + 1,
                distance=result.distance,
                explanation=result.explanation,
            )
            updated_results.append(updated_result)

        return updated_results

    def get_stats(self) -> Dict[str, Any]:
        """Get re-ranker statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "config": {
                "strategy": self.config.strategy.value,
                "original_weight": self.config.original_weight,
                "reranker_weight": self.config.reranker_weight,
                "top_k": self.config.top_k,
                "score_threshold": self.config.score_threshold,
                "normalize_scores": self.config.normalize_scores,
                "batch_size": self.config.batch_size,
                "timeout_seconds": self.config.timeout_seconds,
            },
            "model_info": self.get_model_info(),
        }


class MockReRanker(BaseReRanker):
    """Mock re-ranker for development and testing.

    This provides a simple re-ranking implementation that doesn't require
    external dependencies or model downloads. Useful for testing integration.
    """

    def __init__(self, config: Optional[ReRankingConfig] = None):
        """Initialize mock re-ranker."""
        super().__init__(config)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize mock re-ranker."""
        self._initialized = True

    async def close(self) -> None:
        """Clean up mock re-ranker."""
        self._initialized = False

    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information."""
        return {
            "name": "MockReRanker",
            "version": "1.0.0",
            "type": "rule-based",
            "description": "Mock re-ranker for testing",
        }

    async def rerank(self, query: str, results: List[SearchResult]) -> ReRankingResult:
        """Mock re-ranking using simple heuristics.

        Args:
            query: Search query
            results: Results to re-rank

        Returns:
            Re-ranking result
        """
        import time

        start_time = time.time()

        if not results:
            return ReRankingResult(
                results=[],
                original_count=0,
                reranked_count=0,
                processing_time_ms=0.0,
                model_info=self.get_model_info(),
                scores_changed=False,
            )

        # Filter results
        filtered_results = self._filter_results(results)
        original_count = len(results)
        working_count = len(filtered_results)

        if not filtered_results:
            return ReRankingResult(
                results=results,
                original_count=original_count,
                reranked_count=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                model_info=self.get_model_info(),
                scores_changed=False,
            )

        # Simple mock re-ranking based on text matching
        query_words = set(query.lower().split())
        rerank_scores = []

        for result in filtered_results:
            content_words = set(result.chunk.content.lower().split())
            # Calculate overlap score
            overlap = len(query_words.intersection(content_words))
            total_query_words = len(query_words)

            if total_query_words > 0:
                overlap_score = overlap / total_query_words
            else:
                overlap_score = 0.0

            # Add some randomness and content length bias
            length_bonus = min(len(result.chunk.content) / 1000, 0.2)  # Max 20% bonus
            mock_score = min(overlap_score + length_bonus, 1.0)

            rerank_scores.append(mock_score)

        # Combine scores using configured strategy
        combined_results = self._combine_scores(filtered_results, rerank_scores)

        # Sort by final score (descending)
        combined_results.sort(key=lambda x: x.score, reverse=True)

        # Update ranks
        final_results = self._update_ranks(combined_results)

        # Add back any results that were filtered out (at the end)
        if len(filtered_results) < len(results):
            remaining_results = results[len(filtered_results) :]
            final_results.extend(remaining_results)

        processing_time = (time.time() - start_time) * 1000

        return ReRankingResult(
            results=final_results,
            original_count=original_count,
            reranked_count=working_count,
            processing_time_ms=processing_time,
            model_info=self.get_model_info(),
            scores_changed=working_count > 0,
        )
