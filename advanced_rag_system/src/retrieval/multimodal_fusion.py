"""Multi-modal fusion algorithms for combining results from different modalities.

This module extends the hybrid fusion capabilities to support combining
results from text embeddings, image embeddings (CLIP), and structured data
queries into a unified ranked result set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from uuid import UUID

from src.core.types import SearchResult
from src.retrieval.hybrid.fusion import normalize_scores


@dataclass
class ModalityFusionConfig:
    """Configuration for multi-modal result fusion.

    Attributes:
        text_weight: Weight for text embedding results (default: 0.4)
        image_weight: Weight for image embedding results (default: 0.4)
        structured_weight: Weight for structured data results (default: 0.2)
        rrf_k: RRF parameter k for rank-based fusion (default: 60.0)
        max_results: Maximum number of results to return (default: 100)
        normalize_scores: Whether to normalize scores before fusion (default: True)
        min_score_threshold: Minimum score threshold for results (default: 0.0)
    """

    text_weight: float = 0.4
    image_weight: float = 0.4
    structured_weight: float = 0.2
    rrf_k: float = 60.0
    max_results: int = 100
    normalize_scores: bool = True
    min_score_threshold: float = 0.0

    def __post_init__(self):
        """Validate weights sum to approximately 1.0."""
        total = self.text_weight + self.image_weight + self.structured_weight
        if not (0.99 <= total <= 1.01):
            # Normalize weights if they don't sum to 1
            self.text_weight /= total
            self.image_weight /= total
            self.structured_weight /= total


class MultiModalFusion:
    """Multi-modal fusion for combining results from different modalities.

    This class implements algorithms to fuse search results from:
    - Text embeddings (dense retrieval)
    - Image embeddings (CLIP retrieval)
    - Structured data queries (SQL/Table search)

    The fusion supports both weighted score combination and reciprocal
    rank fusion (RRF) strategies.

    Example:
        ```python
        config = ModalityFusionConfig(
            text_weight=0.5,
            image_weight=0.3,
            structured_weight=0.2
        )
        fusion = MultiModalFusion(config)

        results = fusion.fuse_modalities(
            text_results=text_search_results,
            image_results=image_search_results,
            structured_results=structured_results,
            config=config
        )
        ```
    """

    def __init__(self, config: Optional[ModalityFusionConfig] = None):
        """Initialize multi-modal fusion.

        Args:
            config: Optional configuration for fusion parameters
        """
        self.config = config or ModalityFusionConfig()

    def fuse_modalities(
        self,
        text_results: Optional[List[SearchResult]] = None,
        image_results: Optional[List[SearchResult]] = None,
        structured_results: Optional[List[SearchResult]] = None,
        config: Optional[ModalityFusionConfig] = None,
    ) -> List[SearchResult]:
        """Fuse results from multiple modalities into a single ranked list.

        Args:
            text_results: Results from text embedding search
            image_results: Results from image embedding (CLIP) search
            structured_results: Results from structured data queries
            config: Optional override configuration

        Returns:
            List of fused search results ranked by combined score
        """
        fusion_config = config or self.config

        # Handle empty inputs
        text_results = text_results or []
        image_results = image_results or []
        structured_results = structured_results or []

        # If only one modality has results, return those
        total_results = len(text_results) + len(image_results) + len(structured_results)
        if total_results == 0:
            return []

        if len(text_results) == total_results:
            return text_results[: fusion_config.max_results]
        if len(image_results) == total_results:
            return image_results[: fusion_config.max_results]
        if len(structured_results) == total_results:
            return structured_results[: fusion_config.max_results]

        # Normalize scores if configured
        if fusion_config.normalize_scores:
            text_results = self._normalize_if_not_empty(text_results)
            image_results = self._normalize_if_not_empty(image_results)
            structured_results = self._normalize_if_not_empty(structured_results)

        # Apply modality weights
        weighted_text = self._apply_modality_weight(
            text_results, fusion_config.text_weight, "text"
        )
        weighted_image = self._apply_modality_weight(
            image_results, fusion_config.image_weight, "image"
        )
        weighted_structured = self._apply_modality_weight(
            structured_results, fusion_config.structured_weight, "structured"
        )

        # Combine using weighted score fusion
        fused_results = self._combine_weighted_results(
            weighted_text, weighted_image, weighted_structured, fusion_config
        )

        return fused_results[: fusion_config.max_results]

    def normalize_cross_modal_scores(
        self,
        text_results: List[SearchResult],
        image_results: List[SearchResult],
        structured_results: List[SearchResult],
    ) -> tuple[List[SearchResult], List[SearchResult], List[SearchResult]]:
        """Normalize scores across different modalities to comparable ranges.

        Different modalities may have different score distributions. This method
        normalizes scores from each modality to a 0-1 range independently, making
        them comparable for fusion.

        Args:
            text_results: Text embedding search results
            image_results: Image embedding search results
            structured_results: Structured data search results

        Returns:
            Tuple of normalized result lists (text, image, structured)
        """
        normalized_text = normalize_scores(text_results) if text_results else []
        normalized_image = normalize_scores(image_results) if image_results else []
        normalized_structured = (
            normalize_scores(structured_results) if structured_results else []
        )

        return normalized_text, normalized_image, normalized_structured

    def apply_modality_weights(
        self,
        text_results: List[SearchResult],
        image_results: List[SearchResult],
        structured_results: List[SearchResult],
        config: Optional[ModalityFusionConfig] = None,
    ) -> tuple[List[SearchResult], List[SearchResult], List[SearchResult]]:
        """Apply modality-specific weights to search results.

        Args:
            text_results: Text embedding search results
            image_results: Image embedding search results
            structured_results: Structured data search results
            config: Optional configuration with weights

        Returns:
            Tuple of weighted result lists (text, image, structured)
        """
        fusion_config = config or self.config

        weighted_text = self._apply_modality_weight(
            text_results, fusion_config.text_weight, "text"
        )
        weighted_image = self._apply_modality_weight(
            image_results, fusion_config.image_weight, "image"
        )
        weighted_structured = self._apply_modality_weight(
            structured_results, fusion_config.structured_weight, "structured"
        )

        return weighted_text, weighted_image, weighted_structured

    def fuse_with_rrf(
        self,
        text_results: Optional[List[SearchResult]] = None,
        image_results: Optional[List[SearchResult]] = None,
        structured_results: Optional[List[SearchResult]] = None,
        config: Optional[ModalityFusionConfig] = None,
    ) -> List[SearchResult]:
        """Fuse results using Reciprocal Rank Fusion (RRF).

        RRF combines results based on their ranks in each modality rather
        than scores, which can be more robust when score distributions differ.

        Args:
            text_results: Results from text embedding search
            image_results: Results from image embedding search
            structured_results: Results from structured data queries
            config: Optional configuration

        Returns:
            List of fused search results ranked by RRF score
        """
        fusion_config = config or self.config

        text_results = text_results or []
        image_results = image_results or []
        structured_results = structured_results or []

        # Create unified result map
        result_map: Dict[UUID, SearchResult] = {}
        rrf_scores: Dict[UUID, float] = {}
        modality_sources: Dict[UUID, Set[str]] = {}

        # Process text results
        for rank, result in enumerate(text_results, 1):
            chunk_id = result.chunk.id
            rrf_score = 1.0 / (fusion_config.rrf_k + rank)

            result_map[chunk_id] = result
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

            if chunk_id not in modality_sources:
                modality_sources[chunk_id] = set()
            modality_sources[chunk_id].add("text")

        # Process image results
        for rank, result in enumerate(image_results, 1):
            chunk_id = result.chunk.id
            rrf_score = 1.0 / (fusion_config.rrf_k + rank)

            if chunk_id not in result_map:
                result_map[chunk_id] = result

            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

            if chunk_id not in modality_sources:
                modality_sources[chunk_id] = set()
            modality_sources[chunk_id].add("image")

        # Process structured results
        for rank, result in enumerate(structured_results, 1):
            chunk_id = result.chunk.id
            rrf_score = 1.0 / (fusion_config.rrf_k + rank)

            if chunk_id not in result_map:
                result_map[chunk_id] = result

            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

            if chunk_id not in modality_sources:
                modality_sources[chunk_id] = set()
            modality_sources[chunk_id].add("structured")

        # Create fused results
        fused_results = []
        for rank, (chunk_id, fused_score) in enumerate(
            sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True), 1
        ):
            if rank > fusion_config.max_results:
                break

            original_result = result_map[chunk_id]
            sources = modality_sources.get(chunk_id, set())

            # Create new result with RRF score
            fused_result = SearchResult(
                chunk=original_result.chunk,
                score=min(fused_score, 1.0),
                rank=rank,
                distance=1.0 - min(fused_score, 1.0),
                explanation=f"RRF fusion score: {fused_score:.4f} "
                f"(sources: {', '.join(sorted(sources))})",
            )
            fused_results.append(fused_result)

        return fused_results

    def _normalize_if_not_empty(
        self, results: List[SearchResult]
    ) -> List[SearchResult]:
        """Normalize scores if results are not empty.

        Args:
            results: List of search results

        Returns:
            Normalized results or original if empty
        """
        if not results:
            return results
        return normalize_scores(results)

    def _apply_modality_weight(
        self,
        results: List[SearchResult],
        weight: float,
        modality: str,
    ) -> List[SearchResult]:
        """Apply weight to all results from a modality.

        Args:
            results: Results from a single modality
            weight: Weight to apply
            modality: Modality name for explanation

        Returns:
            Results with weighted scores
        """
        weighted_results = []
        for result in results:
            weighted_score = result.score * weight
            weighted_result = SearchResult(
                chunk=result.chunk,
                score=weighted_score,
                rank=result.rank,
                distance=1.0 - weighted_score,
                explanation=f"{result.explanation or ''} [{modality} weight={weight:.2f}]",
            )
            weighted_results.append(weighted_result)
        return weighted_results

    def _combine_weighted_results(
        self,
        text_results: List[SearchResult],
        image_results: List[SearchResult],
        structured_results: List[SearchResult],
        config: ModalityFusionConfig,
    ) -> List[SearchResult]:
        """Combine weighted results from all modalities.

        Args:
            text_results: Weighted text results
            image_results: Weighted image results
            structured_results: Weighted structured results
            config: Fusion configuration

        Returns:
            Combined and ranked results
        """
        # Create score maps for each modality
        text_map = {result.chunk.id: result for result in text_results}
        image_map = {result.chunk.id: result for result in image_results}
        structured_map = {result.chunk.id: result for result in structured_results}

        # Get all unique chunk IDs
        all_chunk_ids = (
            set(text_map.keys()) | set(image_map.keys()) | set(structured_map.keys())
        )

        # Calculate combined scores
        combined_results = []
        for chunk_id in all_chunk_ids:
            text_score = text_map.get(chunk_id, SearchResult(
                chunk=list(all_chunk_ids)[0], score=0.0, rank=0, distance=1.0
            )).score if chunk_id in text_map else 0.0
            image_score = image_map[chunk_id].score if chunk_id in image_map else 0.0
            structured_score = (
                structured_map[chunk_id].score if chunk_id in structured_map else 0.0
            )

            # Sum scores across modalities
            combined_score = text_score + image_score + structured_score

            # Get the source result with highest individual score for chunk data
            source_results = []
            if chunk_id in text_map:
                source_results.append((text_map[chunk_id], text_score))
            if chunk_id in image_map:
                source_results.append((image_map[chunk_id], image_score))
            if chunk_id in structured_map:
                source_results.append((structured_map[chunk_id], structured_score))

            source_results.sort(key=lambda x: x[1], reverse=True)
            source_result = source_results[0][0]

            # Build explanation
            score_parts = []
            if text_score > 0:
                score_parts.append(f"text={text_score:.3f}")
            if image_score > 0:
                score_parts.append(f"image={image_score:.3f}")
            if structured_score > 0:
                score_parts.append(f"structured={structured_score:.3f}")

            explanation = f"Multi-modal fusion: {', '.join(score_parts)}, total={combined_score:.3f}"

            combined_result = SearchResult(
                chunk=source_result.chunk,
                score=min(combined_score, 1.0),
                rank=0,  # Will be set after sorting
                distance=1.0 - min(combined_score, 1.0),
                explanation=explanation,
            )
            combined_results.append(combined_result)

        # Sort by combined score and assign ranks
        combined_results.sort(key=lambda x: x.score, reverse=True)

        # Filter by threshold and assign final ranks
        final_results = []
        for rank, result in enumerate(combined_results, 1):
            if result.score < config.min_score_threshold:
                continue

            ranked_result = SearchResult(
                chunk=result.chunk,
                score=result.score,
                rank=rank,
                distance=result.distance,
                explanation=result.explanation,
            )
            final_results.append(ranked_result)

        return final_results


def create_modality_fusion_config(
    text_weight: float = 0.4,
    image_weight: float = 0.4,
    structured_weight: float = 0.2,
    **kwargs,
) -> ModalityFusionConfig:
    """Create a ModalityFusionConfig with the specified weights.

    Args:
        text_weight: Weight for text results
        image_weight: Weight for image results
        structured_weight: Weight for structured data results
        **kwargs: Additional configuration parameters

    Returns:
        Configured ModalityFusionConfig
    """
    return ModalityFusionConfig(
        text_weight=text_weight,
        image_weight=image_weight,
        structured_weight=structured_weight,
        **kwargs,
    )
