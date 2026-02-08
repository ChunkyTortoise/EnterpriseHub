"""Cohere API re-ranker for cloud-based re-ranking service.

This module provides re-ranking using Cohere's Rerank API, which offers
high-quality relevance scoring without requiring local model downloads.
"""

from __future__ import annotations

import asyncio
import time
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.config import get_settings
from src.core.exceptions import RateLimitError, RetrievalError
from src.core.types import SearchResult

from .base import BaseReRanker, ReRankingConfig, ReRankingResult

# Optional import for Cohere client
try:
    import cohere

    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    cohere = None


@dataclass
class CohereConfig:
    """Configuration for Cohere re-ranker.

    Attributes:
        api_key: Cohere API key (if not provided, will use environment variable)
        model: Cohere rerank model to use
        max_chunks_per_doc: Maximum chunks per document to send
        return_documents: Whether to return documents in response
        top_n: Top N results to return from Cohere (None for all)
        timeout_seconds: Request timeout in seconds
        max_retries: Maximum number of retries for failed requests
        retry_delay: Base delay between retries in seconds
    """

    api_key: Optional[str] = None
    model: str = "rerank-english-v2.0"
    max_chunks_per_doc: int = 10
    return_documents: bool = False
    top_n: Optional[int] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class CohereReRanker(BaseReRanker):
    """Cohere API re-ranker using cloud-based ranking service.

    Provides high-quality re-ranking using Cohere's specialized rerank models
    without requiring local model downloads or GPU resources.

    Example:
        ```python
        cohere_config = CohereConfig(model='rerank-english-v2.0')
        config = ReRankingConfig(top_k=50)

        reranker = CohereReRanker(cohere_config=cohere_config, config=config)
        await reranker.initialize()

        # Re-rank search results
        reranked = await reranker.rerank(query, search_results)
        await reranker.close()
        ```
    """

    def __init__(self, cohere_config: Optional[CohereConfig] = None, config: Optional[ReRankingConfig] = None):
        """Initialize Cohere re-ranker.

        Args:
            cohere_config: Cohere-specific configuration
            config: General re-ranking configuration
        """
        super().__init__(config)
        self.cohere_config = cohere_config or CohereConfig()

        self.client: Optional[cohere.Client] = None
        self._initialized = False

        # Check availability
        if not COHERE_AVAILABLE:
            warnings.warn("cohere package not available. CohereReRanker will use fallback implementation.", UserWarning)

    def _get_api_key(self) -> str:
        """Get Cohere API key from config or environment.

        Returns:
            API key string

        Raises:
            RetrievalError: If API key is not found
        """
        api_key = self.cohere_config.api_key

        if not api_key:
            # Try to get from environment via settings
            settings = get_settings()
            api_key = getattr(settings, "cohere_api_key", None)

        if not api_key:
            # Try common environment variable names
            import os

            api_key = os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY")

        if not api_key:
            raise RetrievalError(
                "Cohere API key not found. Set COHERE_API_KEY environment variable or provide in config.",
                error_code="MISSING_API_KEY",
            )

        return api_key

    async def initialize(self) -> None:
        """Initialize the Cohere client.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        try:
            if COHERE_AVAILABLE:
                api_key = self._get_api_key()
                self.client = cohere.Client(api_key=api_key, timeout=self.cohere_config.timeout_seconds)

                # Test the connection with a simple request
                await self._test_connection()
            else:
                # Fallback mode - no client
                self.client = None

            self._initialized = True

        except Exception as e:
            raise RetrievalError(f"Failed to initialize Cohere client: {str(e)}") from e

    async def _test_connection(self) -> None:
        """Test the Cohere API connection.

        Raises:
            RetrievalError: If connection test fails
        """
        if not self.client:
            return

        try:
            # Make a minimal rerank request to test the connection
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.rerank(
                    query="test", documents=["test document"], model=self.cohere_config.model, top_n=1
                ),
            )
        except Exception as e:
            raise RetrievalError(f"Cohere API connection test failed: {str(e)}") from e

    async def close(self) -> None:
        """Clean up resources."""
        self.client = None
        self._initialized = False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Cohere model.

        Returns:
            Dictionary with model information
        """
        return {
            "name": self.cohere_config.model,
            "type": "cohere-api",
            "provider": "Cohere",
            "max_chunks_per_doc": self.cohere_config.max_chunks_per_doc,
            "initialized": self._initialized,
            "cohere_available": COHERE_AVAILABLE,
        }

    async def rerank(self, query: str, results: List[SearchResult]) -> ReRankingResult:
        """Re-rank search results using Cohere API.

        Args:
            query: Search query
            results: Search results to re-rank

        Returns:
            Re-ranking result with improved ordering

        Raises:
            RetrievalError: If re-ranking fails
        """
        if not self._initialized:
            raise RetrievalError("CohereReRanker not initialized. Call initialize() first.")

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

            # Get relevance scores from Cohere
            rerank_scores = await self._cohere_rerank(query, filtered_results)

            # Combine scores using configured strategy
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
            raise RetrievalError(f"Cohere re-ranking failed: {str(e)}") from e

    async def _cohere_rerank(self, query: str, results: List[SearchResult]) -> List[float]:
        """Use Cohere API to rerank results.

        Args:
            query: Search query
            results: Search results

        Returns:
            List of relevance scores
        """
        if not results:
            return []

        # Fallback scoring if Cohere not available
        if not self.client or not COHERE_AVAILABLE:
            return await self._fallback_scoring(query, results)

        try:
            # Prepare documents for Cohere
            documents = []
            for result in results:
                # Cohere expects string documents
                content = result.chunk.content

                # Truncate if too long (Cohere has input limits)
                if len(content) > 2000:  # Conservative limit
                    content = content[:2000] + "..."

                documents.append(content)

            # Call Cohere rerank API with retry logic
            cohere_response = await self._call_cohere_with_retry(query, documents)

            # Extract scores from response
            scores = self._extract_scores_from_response(cohere_response, len(results))

            return scores

        except Exception as e:
            # Fallback to simple scoring if Cohere fails
            warnings.warn(f"Cohere API failed, using fallback scoring: {e}")
            return await self._fallback_scoring(query, results)

    async def _call_cohere_with_retry(self, query: str, documents: List[str]) -> Any:
        """Call Cohere API with retry logic.

        Args:
            query: Search query
            documents: List of documents to rerank

        Returns:
            Cohere rerank response

        Raises:
            RetrievalError: If all retries fail
        """
        last_exception = None

        for attempt in range(self.cohere_config.max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.rerank(
                        query=query,
                        documents=documents,
                        model=self.cohere_config.model,
                        top_n=self.cohere_config.top_n,
                        return_documents=self.cohere_config.return_documents,
                        max_chunks_per_doc=self.cohere_config.max_chunks_per_doc,
                    ),
                )
                return response

            except Exception as e:
                last_exception = e

                # Check for rate limiting
                if "rate limit" in str(e).lower() or "429" in str(e):
                    raise RateLimitError(f"Cohere API rate limit exceeded: {e}")

                # Exponential backoff for retries
                if attempt < self.cohere_config.max_retries - 1:
                    delay = self.cohere_config.retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

        # All retries failed
        raise RetrievalError(
            f"Cohere API failed after {self.cohere_config.max_retries} retries: {last_exception}"
        ) from last_exception

    def _extract_scores_from_response(self, response: Any, expected_count: int) -> List[float]:
        """Extract normalized scores from Cohere response.

        Args:
            response: Cohere rerank response
            expected_count: Expected number of scores

        Returns:
            List of normalized relevance scores
        """
        try:
            # Cohere returns results with relevance scores
            if not hasattr(response, "results"):
                # Fallback to neutral scores
                return [0.5] * expected_count

            results = response.results
            scores = [0.0] * expected_count  # Initialize with zeros

            # Map Cohere results back to original positions
            for result in results:
                index = result.index
                relevance_score = result.relevance_score

                if 0 <= index < expected_count:
                    # Cohere relevance scores are typically in [0, 1] but can exceed
                    # Clamp to [0, 1] range
                    normalized_score = max(0.0, min(1.0, relevance_score))
                    scores[index] = normalized_score

            # For any documents not returned by Cohere (if top_n was used),
            # assign a small positive score to maintain relative ordering
            for i, score in enumerate(scores):
                if score == 0.0:
                    scores[i] = 0.1  # Small positive score

            return scores

        except Exception as e:
            warnings.warn(f"Failed to extract scores from Cohere response: {e}")
            return [0.5] * expected_count

    async def _fallback_scoring(self, query: str, results: List[SearchResult]) -> List[float]:
        """Fallback scoring method when Cohere is not available.

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

            # Calculate TF-IDF-like score
            overlap = len(query_words.intersection(content_words))
            query_coverage = overlap / len(query_words) if query_words else 0

            # Consider document length as quality signal
            content_length = len(result.chunk.content)
            length_score = min(content_length / 500, 1.0)  # Normalize by 500 chars

            # Combine scores
            final_score = 0.8 * query_coverage + 0.2 * length_score

            scores.append(min(final_score, 1.0))

        return scores

    def estimate_cost(self, num_results: int) -> Dict[str, float]:
        """Estimate API cost for re-ranking operation.

        Args:
            num_results: Number of results to rerank

        Returns:
            Dictionary with cost estimates
        """
        # Cohere pricing is typically per 1000 search units
        # This is a rough estimate - check current Cohere pricing

        search_units = num_results
        cost_per_1000_units = 0.002  # Approximate cost in USD

        estimated_cost = (search_units / 1000) * cost_per_1000_units

        return {
            "search_units": search_units,
            "estimated_cost_usd": estimated_cost,
            "cost_per_1000_units": cost_per_1000_units,
            "currency": "USD",
            "note": "Estimate based on approximate pricing - check current Cohere rates",
        }
