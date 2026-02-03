"""Fusion algorithms for hybrid retrieval.

This module implements various fusion strategies to combine results
from different retrieval methods (dense, sparse, etc.) into a single
ranked list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from uuid import UUID

from src.core.types import SearchResult


@dataclass
class FusionConfig:
    """Configuration for result fusion algorithms.

    Attributes:
        rrf_k: RRF parameter k (default: 60)
        dense_weight: Weight for dense retrieval results (default: 0.5)
        sparse_weight: Weight for sparse retrieval results (default: 0.5)
        max_results: Maximum number of results to return (default: 100)
    """

    rrf_k: float = 60.0
    dense_weight: float = 0.5
    sparse_weight: float = 0.5
    max_results: int = 100


class ReciprocalRankFusion:
    """Reciprocal Rank Fusion (RRF) algorithm implementation.

    RRF combines multiple ranked lists by giving each document a score
    based on the reciprocal of its rank in each list, providing a
    simple but effective fusion method.
    """

    def __init__(self, config: Optional[FusionConfig] = None):
        """Initialize RRF fusion.

        Args:
            config: Optional configuration for fusion parameters
        """
        self.config = config or FusionConfig()

    def fuse_results(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult],
    ) -> List[SearchResult]:
        """Fuse dense and sparse search results using RRF.

        Args:
            dense_results: Results from dense (vector) retrieval
            sparse_results: Results from sparse (BM25) retrieval

        Returns:
            List of fused search results ranked by RRF score
        """
        # Create unified result map
        result_map: Dict[UUID, SearchResult] = {}
        rrf_scores: Dict[UUID, float] = {}

        # Process dense results
        for rank, result in enumerate(dense_results, 1):
            chunk_id = result.chunk.id
            rrf_score = 1.0 / (self.config.rrf_k + rank)

            result_map[chunk_id] = result
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

        # Process sparse results
        for rank, result in enumerate(sparse_results, 1):
            chunk_id = result.chunk.id
            rrf_score = 1.0 / (self.config.rrf_k + rank)

            if chunk_id not in result_map:
                result_map[chunk_id] = result

            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

        # Create fused results
        fused_results = []
        for rank, (chunk_id, fused_score) in enumerate(
            sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True), 1
        ):
            if rank > self.config.max_results:
                break

            original_result = result_map[chunk_id]

            # Create new result with RRF score
            fused_result = SearchResult(
                chunk=original_result.chunk,
                score=min(fused_score, 1.0),  # Ensure score is bounded to 0-1
                rank=rank,
                distance=1.0 - min(fused_score, 1.0),
                explanation=f"RRF fusion score: {fused_score:.4f} "
                          f"(from dense: {chunk_id in [r.chunk.id for r in dense_results]}, "
                          f"sparse: {chunk_id in [r.chunk.id for r in sparse_results]})"
            )
            fused_results.append(fused_result)

        return fused_results


class WeightedScoreFusion:
    """Weighted score fusion algorithm.

    This fusion method combines results by taking a weighted average
    of the normalized scores from different retrieval methods.
    """

    def __init__(self, config: Optional[FusionConfig] = None):
        """Initialize weighted fusion.

        Args:
            config: Optional configuration for fusion parameters
        """
        self.config = config or FusionConfig()

    def fuse_results(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult],
    ) -> List[SearchResult]:
        """Fuse dense and sparse results using weighted score fusion.

        Args:
            dense_results: Results from dense (vector) retrieval
            sparse_results: Results from sparse (BM25) retrieval

        Returns:
            List of fused search results ranked by weighted score
        """
        # Normalize weights
        total_weight = self.config.dense_weight + self.config.sparse_weight
        dense_weight = self.config.dense_weight / total_weight
        sparse_weight = self.config.sparse_weight / total_weight

        # Create result maps
        dense_map = {result.chunk.id: result for result in dense_results}
        sparse_map = {result.chunk.id: result for result in sparse_results}

        # Get all unique document IDs
        all_chunk_ids = set(dense_map.keys()) | set(sparse_map.keys())

        # Calculate weighted scores
        weighted_results = []
        for chunk_id in all_chunk_ids:
            dense_score = dense_map[chunk_id].score if chunk_id in dense_map else 0.0
            sparse_score = sparse_map[chunk_id].score if chunk_id in sparse_map else 0.0

            # Calculate weighted score
            weighted_score = (dense_weight * dense_score) + (sparse_weight * sparse_score)

            # Use the first available result for chunk data
            source_result = dense_map.get(chunk_id) or sparse_map.get(chunk_id)
            assert source_result is not None, f"Chunk {chunk_id} not found in either result set"

            weighted_result = SearchResult(
                chunk=source_result.chunk,
                score=weighted_score,
                rank=1,  # Temporary rank, will be updated after sorting
                distance=1.0 - weighted_score,
                explanation=f"Weighted fusion: dense={dense_score:.3f} "
                          f"(w={dense_weight:.2f}), sparse={sparse_score:.3f} "
                          f"(w={sparse_weight:.2f}), final={weighted_score:.3f}"
            )
            weighted_results.append(weighted_result)

        # Sort by weighted score and assign ranks
        weighted_results.sort(key=lambda x: x.score, reverse=True)

        # Limit results and update ranks
        final_results = []
        for rank, result in enumerate(weighted_results[:self.config.max_results], 1):
            # Create new result with updated rank
            final_result = SearchResult(
                chunk=result.chunk,
                score=result.score,
                rank=rank,
                distance=result.distance,
                explanation=result.explanation
            )
            final_results.append(final_result)

        return final_results


def deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results based on chunk ID.

    Args:
        results: List of search results potentially containing duplicates

    Returns:
        List of deduplicated results preserving the first occurrence
    """
    seen_ids: Set[UUID] = set()
    deduplicated = []

    for result in results:
        if result.chunk.id not in seen_ids:
            seen_ids.add(result.chunk.id)
            deduplicated.append(result)

    return deduplicated


def normalize_scores(results: List[SearchResult]) -> List[SearchResult]:
    """Normalize scores in search results to 0-1 range.

    Args:
        results: List of search results with potentially unnormalized scores

    Returns:
        List of results with normalized scores
    """
    if not results:
        return results

    # Find score range
    scores = [result.score for result in results]
    max_score = max(scores)
    min_score = min(scores)
    score_range = max_score - min_score

    if score_range == 0:
        # All scores are the same
        return results

    # Normalize scores
    normalized_results = []
    for result in results:
        normalized_score = (result.score - min_score) / score_range

        normalized_result = SearchResult(
            chunk=result.chunk,
            score=normalized_score,
            rank=result.rank,
            distance=1.0 - normalized_score,
            explanation=result.explanation
        )
        normalized_results.append(normalized_result)

    return normalized_results