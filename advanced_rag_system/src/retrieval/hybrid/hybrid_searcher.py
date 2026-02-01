"""Hybrid search orchestrator combining dense and sparse retrieval.

This module provides the main HybridSearcher class that coordinates
dense vector search and sparse BM25 search, fusing results using
various fusion algorithms.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Union

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult
from src.retrieval.sparse.bm25_index import BM25Index, BM25Config
from src.retrieval.hybrid.fusion import (
    FusionConfig,
    ReciprocalRankFusion,
    WeightedScoreFusion,
    deduplicate_results,
)


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search.

    Attributes:
        fusion_method: Fusion algorithm to use ('rrf' or 'weighted')
        enable_dense: Whether to use dense (vector) retrieval
        enable_sparse: Whether to use sparse (BM25) retrieval
        parallel_execution: Whether to run retrievers in parallel
        top_k_dense: Number of results to get from dense retrieval
        top_k_sparse: Number of results to get from sparse retrieval
        top_k_final: Number of results to return after fusion
        dense_threshold: Minimum score threshold for dense results
        sparse_threshold: Minimum score threshold for sparse results
    """

    fusion_method: str = "rrf"  # 'rrf' or 'weighted'
    enable_dense: bool = True
    enable_sparse: bool = True
    parallel_execution: bool = True
    top_k_dense: int = 50
    top_k_sparse: int = 50
    top_k_final: int = 20
    dense_threshold: float = 0.0
    sparse_threshold: float = 0.0


class DenseRetrieverStub:
    """Stub for dense retrieval - to be replaced with actual implementation.

    This is a placeholder that will be replaced when dense retrieval
    is implemented in a later phase.
    """

    def __init__(self):
        """Initialize stub dense retriever."""
        self._documents: List[DocumentChunk] = []

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add documents to the stub index.

        Args:
            chunks: List of document chunks to index
        """
        self._documents.extend(chunks)

    async def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Stub search method - returns empty results.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Empty list (stub implementation)
        """
        # Simulate processing delay
        await asyncio.sleep(0.01)
        return []

    def clear(self) -> None:
        """Clear the stub index."""
        self._documents.clear()

    @property
    def document_count(self) -> int:
        """Get number of documents in stub index."""
        return len(self._documents)


class HybridSearcher:
    """Hybrid search engine combining dense and sparse retrieval.

    This class orchestrates multiple retrieval methods and fuses their
    results to provide comprehensive search capabilities.
    """

    def __init__(
        self,
        hybrid_config: Optional[HybridSearchConfig] = None,
        bm25_config: Optional[BM25Config] = None,
        fusion_config: Optional[FusionConfig] = None,
    ):
        """Initialize hybrid searcher.

        Args:
            hybrid_config: Configuration for hybrid search behavior
            bm25_config: Configuration for BM25 sparse retrieval
            fusion_config: Configuration for result fusion
        """
        self.hybrid_config = hybrid_config or HybridSearchConfig()
        self.bm25_config = bm25_config or BM25Config()
        self.fusion_config = fusion_config or FusionConfig()

        # Initialize retrievers
        self.dense_retriever = DenseRetrieverStub() if self.hybrid_config.enable_dense else None
        self.sparse_retriever = BM25Index(self.bm25_config) if self.hybrid_config.enable_sparse else None

        # Initialize fusion algorithm
        if self.hybrid_config.fusion_method == "rrf":
            self.fusion_algorithm = ReciprocalRankFusion(self.fusion_config)
        elif self.hybrid_config.fusion_method == "weighted":
            self.fusion_algorithm = WeightedScoreFusion(self.fusion_config)
        else:
            raise ValueError(f"Unknown fusion method: {self.hybrid_config.fusion_method}")

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add documents to both dense and sparse indices.

        Args:
            chunks: List of document chunks to index

        Raises:
            RetrievalError: If document indexing fails
        """
        if not chunks:
            return

        try:
            # Add to dense index
            if self.dense_retriever:
                self.dense_retriever.add_documents(chunks)

            # Add to sparse index
            if self.sparse_retriever:
                self.sparse_retriever.add_documents(chunks)

        except Exception as e:
            raise RetrievalError(
                message=f"Failed to add documents to hybrid index: {str(e)}",
                error_code="HYBRID_INDEX_ERROR"
            ) from e

    async def search(self, query: str) -> List[SearchResult]:
        """Perform hybrid search combining dense and sparse retrieval.

        Args:
            query: Search query string

        Returns:
            List of fused search results ranked by relevance

        Raises:
            ValueError: If query is empty
            RetrievalError: If search operation fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            start_time = time.perf_counter()

            # Execute retrievers
            if self.hybrid_config.parallel_execution:
                dense_results, sparse_results = await self._search_parallel(query)
            else:
                dense_results, sparse_results = await self._search_sequential(query)

            # Filter results by thresholds
            dense_results = [
                r for r in dense_results
                if r.score >= self.hybrid_config.dense_threshold
            ]
            sparse_results = [
                r for r in sparse_results
                if r.score >= self.hybrid_config.sparse_threshold
            ]

            # Fuse results
            if dense_results and sparse_results:
                # Both retrievers have results - fuse them
                fused_results = self.fusion_algorithm.fuse_results(dense_results, sparse_results)
            elif dense_results:
                # Only dense results
                fused_results = dense_results[:self.hybrid_config.top_k_final]
            elif sparse_results:
                # Only sparse results
                fused_results = sparse_results[:self.hybrid_config.top_k_final]
            else:
                # No results from either retriever
                fused_results = []

            # Deduplicate and limit results
            final_results = deduplicate_results(fused_results)
            final_results = final_results[:self.hybrid_config.top_k_final]

            # Update search metadata
            search_time_ms = (time.perf_counter() - start_time) * 1000
            for result in final_results:
                if result.explanation:
                    result.explanation += f", search_time: {search_time_ms:.2f}ms"

            return final_results

        except Exception as e:
            raise RetrievalError(
                message=f"Hybrid search failed: {str(e)}",
                error_code="HYBRID_SEARCH_ERROR"
            ) from e

    async def _search_parallel(self, query: str) -> tuple[List[SearchResult], List[SearchResult]]:
        """Execute dense and sparse search in parallel.

        Args:
            query: Search query string

        Returns:
            Tuple of (dense_results, sparse_results)
        """
        tasks = []

        # Dense search task
        if self.dense_retriever:
            dense_task = self.dense_retriever.search(query, self.hybrid_config.top_k_dense)
            tasks.append(dense_task)
        else:
            tasks.append(self._create_empty_results_task())

        # Sparse search task
        if self.sparse_retriever:
            # Wrap synchronous BM25 search in async
            sparse_task = asyncio.create_task(self._async_sparse_search(query))
            tasks.append(sparse_task)
        else:
            tasks.append(self._create_empty_results_task())

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        dense_results = results[0] if not isinstance(results[0], Exception) else []
        sparse_results = results[1] if not isinstance(results[1], Exception) else []

        return dense_results, sparse_results

    async def _search_sequential(self, query: str) -> tuple[List[SearchResult], List[SearchResult]]:
        """Execute dense and sparse search sequentially.

        Args:
            query: Search query string

        Returns:
            Tuple of (dense_results, sparse_results)
        """
        dense_results = []
        sparse_results = []

        # Dense search
        if self.dense_retriever:
            dense_results = await self.dense_retriever.search(query, self.hybrid_config.top_k_dense)

        # Sparse search
        if self.sparse_retriever:
            sparse_results = await self._async_sparse_search(query)

        return dense_results, sparse_results

    async def _async_sparse_search(self, query: str) -> List[SearchResult]:
        """Wrap synchronous sparse search in async.

        Args:
            query: Search query string

        Returns:
            List of sparse search results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.sparse_retriever.search,
            query,
            self.hybrid_config.top_k_sparse
        )

    async def _create_empty_results_task(self) -> List[SearchResult]:
        """Create an async task that returns empty results.

        Returns:
            Empty list of search results
        """
        return []

    def clear(self) -> None:
        """Clear all indices."""
        if self.dense_retriever:
            self.dense_retriever.clear()

        if self.sparse_retriever:
            self.sparse_retriever.clear()

    @property
    def document_count(self) -> int:
        """Get the total number of documents indexed.

        Returns:
            Number of indexed documents
        """
        count = 0
        if self.sparse_retriever:
            count = max(count, self.sparse_retriever.document_count)
        if self.dense_retriever:
            count = max(count, self.dense_retriever.document_count)
        return count

    def get_retriever_status(self) -> dict:
        """Get status information about the retrievers.

        Returns:
            Dictionary with retriever status information
        """
        return {
            "dense_enabled": self.hybrid_config.enable_dense,
            "sparse_enabled": self.hybrid_config.enable_sparse,
            "dense_document_count": self.dense_retriever.document_count if self.dense_retriever else 0,
            "sparse_document_count": self.sparse_retriever.document_count if self.sparse_retriever else 0,
            "fusion_method": self.hybrid_config.fusion_method,
            "parallel_execution": self.hybrid_config.parallel_execution,
        }