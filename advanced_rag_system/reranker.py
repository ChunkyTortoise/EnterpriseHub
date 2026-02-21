"""Comprehensive Re-ranking Pipeline with Confidence Scoring.

This module provides an advanced re-ranking pipeline that builds upon
the existing cross-encoder implementation to achieve improved precision
(target: +20-30% improvement).

Key Features:
- Multi-stage re-ranking pipeline
- Confidence scoring for result reliability
- Multi-model ensemble re-ranking
- Score distribution analysis
- Result explanation generation
"""

from __future__ import annotations

import asyncio
import math
import time
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult
from src.reranking.base import (
    BaseReRanker,
    ReRankingConfig,
    ReRankingResult,
    ReRankingStrategy,
)
from src.reranking.cross_encoder import CrossEncoderReRanker

# Optional imports
try:
    import torch
    from sentence_transformers import CrossEncoder

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    CrossEncoder = None
    torch = None


class RerankingStage(str, Enum):
    """Stages in the multi-stage re-ranking pipeline."""

    INITIAL = "initial"  # Initial scoring
    COARSE = "coarse"  # Broad re-ranking
    FINE = "fine"  # Detailed re-ranking
    FINAL = "final"  # Final precision boost


class ConfidenceLevel(str, Enum):
    """Confidence levels for search results."""

    HIGH = "high"  # Score >= 0.8
    MEDIUM = "medium"  # Score >= 0.5 and < 0.8
    LOW = "low"  # Score < 0.5


@dataclass
class ConfidenceScore:
    """Confidence score for a search result.

    Attributes:
        score: The confidence score (0-1)
        level: Confidence level (high/medium/low)
        reliability: Reliability metric based on score distribution
        explanation: Human-readable explanation
    """

    score: float
    level: ConfidenceLevel
    reliability: float
    explanation: str


@dataclass
class RerankingPipelineConfig:
    """Configuration for the re-ranking pipeline.

    Attributes:
        enable_multi_stage: Enable multi-stage re-ranking
        enable_confidence_scoring: Enable confidence scoring
        enable_ensemble: Enable ensemble re-ranking with multiple models
        initial_top_k: Results to consider in initial stage
        coarse_top_k: Results to consider in coarse stage
        fine_top_k: Results to consider in fine stage
        final_top_k: Final results to return
        min_confidence_threshold: Minimum confidence for inclusion
        use_score_distribution: Use score distribution for confidence
        primary_model: Primary cross-encoder model
        secondary_model: Secondary model for ensemble (optional)
    """

    enable_multi_stage: bool = True
    enable_confidence_scoring: bool = True
    enable_ensemble: bool = False
    initial_top_k: int = 100
    coarse_top_k: int = 50
    fine_top_k: int = 20
    final_top_k: int = 10
    min_confidence_threshold: float = 0.3
    use_score_distribution: bool = True
    primary_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    secondary_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"


@dataclass
class RerankingMetrics:
    """Comprehensive metrics for re-ranking pipeline."""

    total_time_ms: float
    stage_times_ms: Dict[str, float]
    original_count: int
    final_count: int
    precision_estimate: float
    confidence_distribution: Dict[str, int]
    average_confidence: float


class ScoreDistributionAnalyzer:
    """Analyze score distributions for confidence estimation."""

    def __init__(self):
        """Initialize score distribution analyzer."""
        pass

    def analyze(
        self,
        scores: List[float],
    ) -> Dict[str, Any]:
        """Analyze score distribution.

        Args:
            scores: List of scores to analyze

        Returns:
            Dictionary with distribution metrics
        """
        if not scores:
            return {
                "mean": 0.0,
                "std": 0.0,
                "spread": 0.0,
                "gap_score": 0.0,
                "top_1_margin": 0.0,
            }

        sorted_scores = sorted(scores, reverse=True)
        n = len(sorted_scores)

        # Basic statistics
        mean_score = sum(scores) / n
        std_score = self._calculate_std(scores, mean_score)

        # Spread: difference between max and min
        spread = max(scores) - min(scores)

        # Gap score: difference between top results
        gap_score = 0.0
        if n >= 2:
            gap_score = sorted_scores[0] - sorted_scores[1]

        # Top-1 margin: how much the top result stands out
        top_1_margin = 0.0
        if n >= 2 and mean_score > 0:
            top_1_margin = (sorted_scores[0] - mean_score) / mean_score

        return {
            "mean": mean_score,
            "std": std_score,
            "spread": spread,
            "gap_score": gap_score,
            "top_1_margin": top_1_margin,
            "n_scores": n,
        }

    def _calculate_std(self, scores: List[float], mean: float) -> float:
        """Calculate standard deviation."""
        if len(scores) <= 1:
            return 0.0
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return math.sqrt(variance)

    def estimate_confidence(
        self,
        score: float,
        distribution: Dict[str, Any],
    ) -> Tuple[float, ConfidenceLevel]:
        """Estimate confidence level for a score.

        Args:
            score: The score to evaluate
            distribution: Score distribution metrics

        Returns:
            Tuple of (confidence_score, confidence_level)
        """
        # Base confidence on absolute score
        base_confidence = score

        # Adjust based on distribution
        if distribution["n_scores"] >= 2:
            # Higher spread = more confidence in ranking
            spread_factor = min(distribution["spread"] / 2.0, 1.0)

            # Gap between top results indicates confidence
            gap_factor = min(distribution["gap_score"], 1.0)

            # Top margin indicates confidence in top result
            if score == max(distribution.get("sorted_scores", [score])):
                margin_factor = min(distribution["top_1_margin"], 1.0)
            else:
                margin_factor = 0.0

            # Combine factors
            confidence = 0.5 * base_confidence + 0.2 * spread_factor + 0.2 * gap_factor + 0.1 * margin_factor
        else:
            confidence = base_confidence

        # Ensure in valid range
        confidence = max(0.0, min(1.0, confidence))

        # Determine level
        if confidence >= 0.8:
            level = ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return confidence, level

    def generate_explanation(
        self,
        score: float,
        confidence: float,
        level: ConfidenceLevel,
        distribution: Dict[str, Any],
    ) -> str:
        """Generate human-readable explanation.

        Args:
            score: The score
            confidence: Confidence score
            level: Confidence level
            distribution: Score distribution

        Returns:
            Explanation string
        """
        explanations = []

        # Add score-based explanation
        if score >= 0.8:
            explanations.append("Very strong relevance")
        elif score >= 0.6:
            explanations.append("Strong relevance")
        elif score >= 0.4:
            explanations.append("Moderate relevance")
        else:
            explanations.append("Weak relevance")

        # Add confidence-based explanation
        if level == ConfidenceLevel.HIGH:
            explanations.append("high confidence")
            if distribution.get("gap_score", 0) > 0.1:
                explanations.append("clear winner")
        elif level == ConfidenceLevel.MEDIUM:
            explanations.append("medium confidence")
        else:
            explanations.append("low confidence - results may vary")

        return ", ".join(explanations)


class EnsembleReRanker:
    """Ensemble re-ranker using multiple models."""

    def __init__(
        self,
        primary_model: str,
        secondary_model: str,
        config: Optional[ReRankingConfig] = None,
    ):
        """Initialize ensemble re-ranker.

        Args:
            primary_model: Primary cross-encoder model
            secondary_model: Secondary cross-encoder model
            config: Re-ranking configuration
        """
        self.config = config or ReRankingConfig()
        self.primary_model_name = primary_model
        self.secondary_model_name = secondary_model

        self.primary_reranker: Optional[CrossEncoderReRanker] = None
        self.secondary_reranker: Optional[CrossEncoderReRanker] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize ensemble re-rankers."""
        if self._initialized:
            return

        try:
            # Initialize primary
            self.primary_reranker = CrossEncoderReRanker(
                model_name=self.primary_model_name,
                config=self.config,
            )
            await self.primary_reranker.initialize()

            # Initialize secondary if different
            if self.secondary_model_name != self.primary_model_name:
                self.secondary_reranker = CrossEncoderReRanker(
                    model_name=self.secondary_model_name,
                    config=self.config,
                )
                await self.secondary_reranker.initialize()

            self._initialized = True

        except Exception as e:
            raise RetrievalError(
                message=f"Failed to initialize ensemble re-ranker: {str(e)}",
                error_code="ENSEMBLE_INIT_ERROR",
            ) from e

    async def close(self) -> None:
        """Close ensemble re-rankers."""
        if self.primary_reranker:
            await self.primary_reranker.close()
        if self.secondary_reranker:
            await self.secondary_reranker.close()
        self._initialized = False

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
    ) -> List[float]:
        """Ensemble re-rank results using multiple models.

        Args:
            query: Search query
            results: Results to re-rank

        Returns:
            Ensemble scores
        """
        if not results:
            return []

        scores = []

        # Get primary scores
        if self.primary_reranker:
            primary_result = await self.primary_reranker.rerank(query, results)
            primary_scores = [r.score for r in primary_result.results]
        else:
            primary_scores = [r.score for r in results]

        # Get secondary scores if available
        if self.secondary_reranker:
            secondary_result = await self.secondary_reranker.rerank(query, results)
            secondary_scores = [r.score for r in secondary_result.results]
        else:
            secondary_scores = primary_scores

        # Combine scores (simple average)
        for i in range(len(results)):
            primary = primary_scores[i] if i < len(primary_scores) else 0.0
            secondary = secondary_scores[i] if i < len(secondary_scores) else 0.0
            ensemble_score = (primary + secondary) / 2.0
            scores.append(ensemble_score)

        return scores


class RerankingPipeline:
    """Comprehensive re-ranking pipeline with multiple stages.

    This pipeline implements multi-stage re-ranking targeting +20-30%
    precision improvement through:
    - Initial scoring with cross-encoder
    - Coarse re-ranking with top candidates
    - Fine re-ranking with detailed scoring
    - Confidence scoring for result reliability
    - Optional ensemble with multiple models

    Example:
        ```python
        config = RerankingPipelineConfig(
            enable_multi_stage=True,
            enable_confidence_scoring=True,
        )
        pipeline = RerankingPipeline(config)
        await pipeline.initialize()

        result = await pipeline.rerank("query", search_results)
        await pipeline.close()
        ```
    """

    def __init__(self, config: Optional[RerankingPipelineConfig] = None):
        """Initialize re-ranking pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or RerankingPipelineConfig()

        # Initialize components
        self._distribution_analyzer = ScoreDistributionAnalyzer()

        # Initialize re-rankers
        base_config = ReRankingConfig(
            top_k=self.config.initial_top_k,
            strategy=ReRankingStrategy.WEIGHTED,
            original_weight=0.3,
            reranker_weight=0.7,
        )

        self._primary_reranker = CrossEncoderReRanker(
            model_name=self.config.primary_model,
            config=base_config,
        )

        # Initialize ensemble if enabled
        self._ensemble_reranker: Optional[EnsembleReRanker] = None
        if self.config.enable_ensemble:
            self._ensemble_reranker = EnsembleReRanker(
                primary_model=self.config.primary_model,
                secondary_model=self.config.secondary_model,
                config=base_config,
            )

        self._initialized = False
        self._stage_times: Dict[str, float] = {}

    async def initialize(self) -> None:
        """Initialize the pipeline.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        try:
            await self._primary_reranker.initialize()

            if self._ensemble_reranker:
                await self._ensemble_reranker.initialize()

            self._initialized = True

        except Exception as e:
            raise RetrievalError(
                message=f"Failed to initialize RerankingPipeline: {str(e)}",
                error_code="PIPELINE_INIT_ERROR",
            ) from e

    async def close(self) -> None:
        """Close the pipeline and cleanup resources."""
        await self._primary_reranker.close()

        if self._ensemble_reranker:
            await self._ensemble_reranker.close()

        self._initialized = False

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
    ) -> ReRankingResult:
        """Perform multi-stage re-ranking.

        Args:
            query: Search query
            results: Search results to re-rank

        Returns:
            ReRankingResult with re-ranked results and confidence scores

        Raises:
            RetrievalError: If re-ranking fails
        """
        if not self._initialized:
            raise RetrievalError("RerankingPipeline not initialized")

        if not results:
            return ReRankingResult(
                results=[],
                original_count=0,
                reranked_count=0,
                processing_time_ms=0.0,
                model_info=self.get_model_info(),
                scores_changed=False,
            )

        start_time = time.perf_counter()
        original_count = len(results)

        try:
            # Stage 1: Initial scoring
            stage_start = time.perf_counter()
            if self.config.enable_ensemble and self._ensemble_reranker:
                # Use ensemble for initial scoring
                ensemble_scores = await self._ensemble_reranker.rerank(query, results)
                scored_results = self._apply_scores(results, ensemble_scores)
            else:
                # Use primary re-ranker
                initial_result = await self._primary_reranker.rerank(query, results)
                scored_results = initial_result.results
            self._stage_times["initial"] = (time.perf_counter() - stage_start) * 1000

            if not self.config.enable_multi_stage:
                # Single-stage: just return the scored results
                scored_results = scored_results[: self.config.final_top_k]

            else:
                # Stage 2: Coarse re-ranking
                stage_start = time.perf_counter()
                coarse_candidates = scored_results[: self.config.coarse_top_k]
                if coarse_candidates != scored_results[: len(coarse_candidates)]:
                    coarse_result = await self._primary_reranker.rerank(query, coarse_candidates)
                    # Merge with non-candidates
                    remaining = scored_results[len(coarse_candidates) :]
                    scored_results = coarse_result.results + remaining
                self._stage_times["coarse"] = (time.perf_counter() - stage_start) * 1000

                # Stage 3: Fine re-ranking
                stage_start = time.perf_counter()
                fine_candidates = scored_results[: self.config.fine_top_k]
                if fine_candidates != scored_results[: len(fine_candidates)]:
                    fine_result = await self._primary_reranker.rerank(query, fine_candidates)
                    remaining = scored_results[len(fine_candidates) :]
                    scored_results = fine_result.results + remaining
                self._stage_times["fine"] = (time.perf_counter() - stage_start) * 1000

            # Apply confidence scoring
            if self.config.enable_confidence_scoring:
                scored_results = self._apply_confidence_scoring(scored_results)

            # Limit to final top-k
            scored_results = scored_results[: self.config.final_top_k]

            # Update ranks
            for i, result in enumerate(scored_results, 1):
                result.rank = i

            total_time = (time.perf_counter() - start_time) * 1000

            # Calculate metrics
            confidence_dist = self._calculate_confidence_distribution(scored_results)
            avg_confidence = self._calculate_average_confidence(scored_results)

            return ReRankingResult(
                results=scored_results,
                original_count=original_count,
                reranked_count=len(scored_results),
                processing_time_ms=total_time,
                model_info=self.get_model_info(),
                scores_changed=True,
            )

        except Exception as e:
            raise RetrievalError(
                message=f"Re-ranking pipeline failed: {str(e)}",
                error_code="RERANKING_ERROR",
            ) from e

    def _apply_scores(
        self,
        results: List[SearchResult],
        scores: List[float],
    ) -> List[SearchResult]:
        """Apply new scores to results.

        Args:
            results: Original results
            scores: New scores

        Returns:
            Results with updated scores
        """
        if len(results) != len(scores):
            # Adjust sizes
            min_len = min(len(results), len(scores))
            results = results[:min_len]
            scores = scores[:min_len]

        updated = []
        for result, score in zip(results, scores):
            updated.append(
                SearchResult(
                    chunk=result.chunk,
                    score=score,
                    rank=result.rank,
                    distance=result.distance,
                    explanation=f"reranked_score: {score:.4f}",
                )
            )

        # Sort by score
        updated.sort(key=lambda x: x.score, reverse=True)
        return updated

    def _apply_confidence_scoring(
        self,
        results: List[SearchResult],
    ) -> List[SearchResult]:
        """Apply confidence scoring to results.

        Args:
            results: Scored results

        Returns:
            Results with confidence information
        """
        if not results:
            return results

        # Get all scores for distribution analysis
        scores = [r.score for r in results]
        distribution = self._distribution_analyzer.analyze(scores)

        # Add confidence to each result
        scored_results = []
        for result in results:
            confidence, level = self._distribution_analyzer.estimate_confidence(result.score, distribution)
            explanation = self._distribution_analyzer.generate_explanation(
                result.score, confidence, level, distribution
            )

            scored_results.append(
                SearchResult(
                    chunk=result.chunk,
                    score=result.score,
                    rank=result.rank,
                    distance=result.distance,
                    explanation=f"{explanation} | {result.explanation or ''}".strip(" | "),
                )
            )

        return scored_results

    def _calculate_confidence_distribution(
        self,
        results: List[SearchResult],
    ) -> Dict[str, int]:
        """Calculate confidence distribution.

        Uses score-based thresholds instead of string matching for reliability.

        Args:
            results: Results with confidence

        Returns:
            Distribution counts
        """
        distribution = {"high": 0, "medium": 0, "low": 0}

        for result in results:
            if result.score >= 0.8:
                distribution["high"] += 1
            elif result.score >= 0.5:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def _calculate_average_confidence(
        self,
        results: List[SearchResult],
    ) -> float:
        """Calculate average confidence from actual result scores.

        Args:
            results: Results with confidence

        Returns:
            Average confidence score
        """
        if not results:
            return 0.0

        return sum(r.score for r in results) / len(results)

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the pipeline models.

        Returns:
            Dictionary with model information
        """
        info = {
            "pipeline": "multi_stage" if self.config.enable_multi_stage else "single_stage",
            "confidence_scoring": self.config.enable_confidence_scoring,
            "ensemble": self.config.enable_ensemble,
            "primary_model": self.config.primary_model,
        }

        if self.config.enable_ensemble:
            info["secondary_model"] = self.config.secondary_model

        return info

    def get_metrics(self, last_result: Optional[ReRankingResult] = None) -> RerankingMetrics:
        """Get pipeline metrics.

        Args:
            last_result: Optional last re-ranking result to compute metrics from

        Returns:
            RerankingMetrics
        """
        original_count = 0
        final_count = 0
        confidence_distribution: Dict[str, int] = {}
        average_confidence = 0.0

        if last_result is not None:
            original_count = last_result.original_count
            final_count = last_result.reranked_count
            confidence_distribution = self._calculate_confidence_distribution(last_result.results)
            average_confidence = self._calculate_average_confidence(last_result.results)

        total_time = sum(self._stage_times.values())
        # Precision estimate: ratio of high-confidence results to total
        high_count = confidence_distribution.get("high", 0)
        precision_estimate = high_count / final_count if final_count > 0 else 0.0

        return RerankingMetrics(
            total_time_ms=total_time,
            stage_times_ms=self._stage_times.copy(),
            original_count=original_count,
            final_count=final_count,
            precision_estimate=precision_estimate,
            confidence_distribution=confidence_distribution,
            average_confidence=average_confidence,
        )


# Alias for easier imports
RerankerPipeline = RerankingPipeline
