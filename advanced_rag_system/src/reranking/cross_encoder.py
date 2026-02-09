"""Cross-encoder re-ranker using sentence-transformers models.

This module provides re-ranking using pre-trained cross-encoder models
that can directly score query-document pairs for improved relevance ranking.
"""

from __future__ import annotations

import asyncio
import time
import warnings
from typing import Any, Dict, List, Optional

from src.core.exceptions import RetrievalError
from src.core.types import SearchResult

from .base import BaseReRanker, ReRankingConfig, ReRankingResult

# Optional imports for cross-encoder functionality
try:
    import torch
    from sentence_transformers import CrossEncoder

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    CrossEncoder = None
    torch = None


class CrossEncoderReRanker(BaseReRanker):
    """Cross-encoder re-ranker using sentence-transformers.

    Uses pre-trained cross-encoder models that can directly score
    query-document pairs for improved relevance ranking. These models
    are specifically designed for ranking tasks and often provide
    better results than bi-encoder approaches.

    Example:
        ```python
        config = ReRankingConfig(top_k=50)
        reranker = CrossEncoderReRanker(
            model_name='ms-marco-MiniLM-L-6-v2',
            config=config
        )
        await reranker.initialize()

        # Re-rank search results
        reranked = await reranker.rerank(query, search_results)
        await reranker.close()
        ```
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        config: Optional[ReRankingConfig] = None,
        device: Optional[str] = None,
        max_length: int = 512,
    ):
        """Initialize cross-encoder re-ranker.

        Args:
            model_name: Name of the cross-encoder model to use
            config: Re-ranking configuration
            device: Device to run the model on ('cpu', 'cuda', 'auto')
            max_length: Maximum input sequence length
        """
        super().__init__(config)
        self.model_name = model_name
        self.max_length = max_length
        self.device = device or self._get_device()

        self.model: Optional[CrossEncoder] = None
        self._initialized = False

        # Check availability
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            warnings.warn(
                "sentence-transformers not available. CrossEncoderReRanker will use fallback implementation.",
                UserWarning,
            )

    def _get_device(self) -> str:
        """Determine the best device to use.

        Returns:
            Device string ('cpu', 'cuda', or specific GPU)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE or torch is None:
            return "cpu"

        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"  # Apple Silicon
        else:
            return "cpu"

    async def initialize(self) -> None:
        """Initialize the cross-encoder model.

        Raises:
            RetrievalError: If model loading fails
        """
        if self._initialized:
            return

        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Load model in executor to avoid blocking
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(None, self._load_model)
            else:
                # Fallback to mock implementation
                self.model = None

            self._initialized = True

        except Exception as e:
            raise RetrievalError(f"Failed to initialize CrossEncoder: {str(e)}") from e

    def _load_model(self) -> Optional[CrossEncoder]:
        """Load the cross-encoder model synchronously.

        Returns:
            Loaded CrossEncoder model or None if not available
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return None

        try:
            model = CrossEncoder(self.model_name, max_length=self.max_length, device=self.device)
            return model
        except Exception as e:
            warnings.warn(f"Failed to load CrossEncoder model {self.model_name}: {e}")
            return None

    async def close(self) -> None:
        """Clean up resources."""
        if self.model is not None and hasattr(self.model, "to"):
            # Move model to CPU to free GPU memory
            self.model.to("cpu")

        self.model = None
        self._initialized = False

        # Clear CUDA cache if available
        if SENTENCE_TRANSFORMERS_AVAILABLE and torch and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the cross-encoder model.

        Returns:
            Dictionary with model information
        """
        info = {
            "name": self.model_name,
            "type": "cross-encoder",
            "max_length": self.max_length,
            "device": self.device,
            "initialized": self._initialized,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
        }

        if self.model is not None and hasattr(self.model, "config"):
            try:
                info.update(
                    {
                        "model_config": str(self.model.config),
                        "tokenizer_vocab_size": getattr(self.model.config, "vocab_size", "unknown"),
                    }
                )
            except Exception:
                pass

        return info

    async def rerank(self, query: str, results: List[SearchResult]) -> ReRankingResult:
        """Re-rank search results using cross-encoder.

        Args:
            query: Search query
            results: Search results to re-rank

        Returns:
            Re-ranking result with improved ordering

        Raises:
            RetrievalError: If re-ranking fails
        """
        if not self._initialized:
            raise RetrievalError("CrossEncoderReRanker not initialized. Call initialize() first.")

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

        original_count = len(results)

        try:
            # Filter results based on configuration
            filtered_results = self._filter_results(results)
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

            # Get relevance scores
            rerank_scores = await self._score_pairs(query, filtered_results)

            # Combine scores
            combined_results = self._combine_scores(filtered_results, rerank_scores)

            # Sort by final score (descending)
            combined_results.sort(key=lambda x: x.score, reverse=True)

            # Update ranks
            final_results = self._update_ranks(combined_results)

            # Add back any results that were filtered out
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

        except Exception as e:
            raise RetrievalError(f"Cross-encoder re-ranking failed: {str(e)}") from e

    async def _score_pairs(self, query: str, results: List[SearchResult]) -> List[float]:
        """Score query-document pairs using the cross-encoder.

        Args:
            query: Search query
            results: Search results to score

        Returns:
            List of relevance scores
        """
        if not results:
            return []

        # Fallback to simple scoring if model not available
        if self.model is None or not SENTENCE_TRANSFORMERS_AVAILABLE:
            return await self._fallback_scoring(query, results)

        try:
            # Prepare query-document pairs
            pairs = []
            for result in results:
                # Truncate document if too long
                content = result.chunk.content
                if len(content) > 1000:  # Simple character-based truncation
                    content = content[:1000] + "..."

                pairs.append([query, content])

            # Process in batches to manage memory
            all_scores = []
            batch_size = self.config.batch_size

            for i in range(0, len(pairs), batch_size):
                batch_pairs = pairs[i : i + batch_size]

                # Run scoring in executor to avoid blocking
                loop = asyncio.get_event_loop()
                batch_scores = await loop.run_in_executor(None, self._score_batch, batch_pairs)

                all_scores.extend(batch_scores)

                # Small delay between batches to prevent overwhelming
                if i + batch_size < len(pairs):
                    await asyncio.sleep(0.01)

            return all_scores

        except Exception as e:
            # Fallback to simple scoring if cross-encoder fails
            warnings.warn(f"Cross-encoder scoring failed, using fallback: {e}")
            return await self._fallback_scoring(query, results)

    def _score_batch(self, pairs: List[List[str]]) -> List[float]:
        """Score a batch of query-document pairs synchronously.

        Args:
            pairs: List of [query, document] pairs

        Returns:
            List of relevance scores
        """
        try:
            scores = self.model.predict(pairs)

            # Convert to list and ensure scores are in reasonable range
            if hasattr(scores, "tolist"):
                scores = scores.tolist()

            # Normalize scores to [0, 1] range using sigmoid
            import math

            normalized_scores = []
            for score in scores:
                # Apply sigmoid to normalize to [0, 1]
                normalized = 1 / (1 + math.exp(-score))
                normalized_scores.append(float(normalized))

            return normalized_scores

        except Exception as e:
            # Return neutral scores if batch scoring fails
            warnings.warn(f"Batch scoring failed: {e}")
            return [0.5] * len(pairs)

    async def _fallback_scoring(self, query: str, results: List[SearchResult]) -> List[float]:
        """Fallback scoring method when cross-encoder is not available.

        Args:
            query: Search query
            results: Search results

        Returns:
            List of relevance scores
        """
        scores = []
        query_words = set(query.lower().split())

        for result in results:
            content_words = set(result.chunk.content.lower().split())

            # Calculate word overlap
            overlap = len(query_words.intersection(content_words))
            total_words = len(query_words.union(content_words))

            if total_words > 0:
                jaccard_score = overlap / total_words
            else:
                jaccard_score = 0.0

            # Add content quality heuristics
            content_length = len(result.chunk.content)
            length_score = min(content_length / 1000, 1.0)  # Prefer longer content up to 1000 chars

            # Combine scores
            final_score = 0.7 * jaccard_score + 0.3 * length_score

            scores.append(min(final_score, 1.0))

        return scores

    def batch_size_recommendation(self, num_results: int) -> int:
        """Recommend optimal batch size based on number of results and device.

        Args:
            num_results: Number of results to process

        Returns:
            Recommended batch size
        """
        if self.device == "cpu":
            return min(16, num_results)
        elif "cuda" in self.device:
            return min(32, num_results)
        else:
            return min(24, num_results)


# Alias for easier imports
CrossEncoderReranker = CrossEncoderReRanker
