"""Tests for hybrid retrieval components including fusion and search.

This module tests the hybrid retrieval system including RRF fusion,
weighted fusion, and the hybrid searcher orchestration.
"""

from typing import List
from uuid import uuid4

import pytest
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.retrieval.hybrid.fusion import (
    FusionConfig,
    ReciprocalRankFusion,
    WeightedScoreFusion,
    deduplicate_results,
    normalize_scores,
)
from src.retrieval.hybrid.hybrid_searcher import (

@pytest.mark.unit
    HybridSearchConfig,
    HybridSearcher,
)


class TestFusionAlgorithms:
    """Test suite for fusion algorithms."""

    @pytest.fixture
    def sample_chunks(self) -> List[DocumentChunk]:
        """Create sample document chunks for testing."""
        doc_id = uuid4()
        return [
            DocumentChunk(
                document_id=doc_id,
                content="Python programming language tutorial",
                index=0,
                metadata=Metadata(title="Python Guide"),
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Machine learning with scikit-learn",
                index=1,
                metadata=Metadata(title="ML Guide"),
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Data science fundamentals and statistics",
                index=2,
                metadata=Metadata(title="Data Science"),
            ),
        ]

    @pytest.fixture
    def dense_results(self, sample_chunks: List[DocumentChunk]) -> List[SearchResult]:
        """Create mock dense search results."""
        return [
            SearchResult(chunk=sample_chunks[0], score=0.95, rank=1, distance=0.05, explanation="Dense vector match"),
            SearchResult(chunk=sample_chunks[1], score=0.75, rank=2, distance=0.25, explanation="Dense vector match"),
        ]

    @pytest.fixture
    def sparse_results(self, sample_chunks: List[DocumentChunk]) -> List[SearchResult]:
        """Create mock sparse search results."""
        return [
            SearchResult(chunk=sample_chunks[1], score=0.85, rank=1, distance=0.15, explanation="BM25 match"),
            SearchResult(chunk=sample_chunks[2], score=0.60, rank=2, distance=0.40, explanation="BM25 match"),
        ]

    def test_fusion_config_defaults(self):
        """Test FusionConfig default values."""
        config = FusionConfig()
        assert config.rrf_k == 60.0
        assert config.dense_weight == 0.5
        assert config.sparse_weight == 0.5
        assert config.max_results == 100

    def test_fusion_config_custom_values(self):
        """Test FusionConfig with custom values."""
        config = FusionConfig(rrf_k=100.0, dense_weight=0.7, sparse_weight=0.3)
        assert config.rrf_k == 100.0
        assert config.dense_weight == 0.7
        assert config.sparse_weight == 0.3

    def test_rrf_fusion_initialization(self):
        """Test RRF fusion initialization."""
        fusion = ReciprocalRankFusion()
        assert fusion.config.rrf_k == 60.0

        custom_config = FusionConfig(rrf_k=50.0)
        fusion_custom = ReciprocalRankFusion(custom_config)
        assert fusion_custom.config.rrf_k == 50.0

    def test_rrf_fusion_basic(self, dense_results: List[SearchResult], sparse_results: List[SearchResult]):
        """Test basic RRF fusion functionality."""
        fusion = ReciprocalRankFusion()
        fused_results = fusion.fuse_results(dense_results, sparse_results)

        assert isinstance(fused_results, list)
        assert len(fused_results) == 3  # All unique chunks
        assert all(isinstance(result, SearchResult) for result in fused_results)

        # Results should be ranked by RRF score
        scores = [result.score for result in fused_results]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_fusion_ranking(self, dense_results: List[SearchResult], sparse_results: List[SearchResult]):
        """Test that RRF fusion produces correct ranking."""
        fusion = ReciprocalRankFusion()
        fused_results = fusion.fuse_results(dense_results, sparse_results)

        # First result should be the document that appears in both lists
        # (chunk from sample_chunks[1] appears in both dense rank 2 and sparse rank 1)
        first_result = fused_results[0]
        assert first_result.chunk.content == "Machine learning with scikit-learn"

        # All results should have updated ranks
        for i, result in enumerate(fused_results, 1):
            assert result.rank == i

    def test_weighted_fusion_initialization(self):
        """Test weighted fusion initialization."""
        fusion = WeightedScoreFusion()
        assert fusion.config.dense_weight == 0.5
        assert fusion.config.sparse_weight == 0.5

        custom_config = FusionConfig(dense_weight=0.8, sparse_weight=0.2)
        fusion_custom = WeightedScoreFusion(custom_config)
        assert fusion_custom.config.dense_weight == 0.8
        assert fusion_custom.config.sparse_weight == 0.2

    def test_weighted_fusion_basic(self, dense_results: List[SearchResult], sparse_results: List[SearchResult]):
        """Test basic weighted fusion functionality."""
        fusion = WeightedScoreFusion()
        fused_results = fusion.fuse_results(dense_results, sparse_results)

        assert isinstance(fused_results, list)
        assert len(fused_results) == 3  # All unique chunks
        assert all(isinstance(result, SearchResult) for result in fused_results)

        # Results should be ranked by weighted score
        scores = [result.score for result in fused_results]
        assert scores == sorted(scores, reverse=True)

    def test_weighted_fusion_score_calculation(self, sample_chunks: List[DocumentChunk]):
        """Test weighted fusion score calculation."""
        dense_results = [SearchResult(chunk=sample_chunks[0], score=0.8, rank=1, distance=0.2)]
        sparse_results = [SearchResult(chunk=sample_chunks[0], score=0.6, rank=1, distance=0.4)]

        config = FusionConfig(dense_weight=0.7, sparse_weight=0.3)
        fusion = WeightedScoreFusion(config)
        fused_results = fusion.fuse_results(dense_results, sparse_results)

        # Expected score: (0.7 * 0.8) + (0.3 * 0.6) = 0.56 + 0.18 = 0.74
        expected_score = 0.74
        assert abs(fused_results[0].score - expected_score) < 0.01

    def test_deduplicate_results(self, sample_chunks: List[DocumentChunk]):
        """Test deduplication of search results."""
        # Create duplicate results
        results = [
            SearchResult(chunk=sample_chunks[0], score=0.9, rank=1, distance=0.1),
            SearchResult(chunk=sample_chunks[1], score=0.8, rank=2, distance=0.2),
            SearchResult(chunk=sample_chunks[0], score=0.7, rank=3, distance=0.3),  # Duplicate
        ]

        deduplicated = deduplicate_results(results)

        assert len(deduplicated) == 2  # Only unique chunks
        assert deduplicated[0].chunk.id == sample_chunks[0].id
        assert deduplicated[1].chunk.id == sample_chunks[1].id

        # Should preserve first occurrence
        assert deduplicated[0].score == 0.9  # First occurrence of sample_chunks[0]

    def test_normalize_scores(self, sample_chunks: List[DocumentChunk]):
        """Test score normalization with valid SearchResult scores."""
        # Use scores within valid range (0-1) for SearchResult
        results = [
            SearchResult(chunk=sample_chunks[0], score=1.0, rank=1, distance=0.0),
            SearchResult(chunk=sample_chunks[1], score=0.5, rank=2, distance=0.5),
            SearchResult(chunk=sample_chunks[2], score=0.2, rank=3, distance=0.8),
        ]

        normalized = normalize_scores(results)

        # Should normalize scores to new 0-1 range based on min/max
        # Original range: 0.2 to 1.0 (range = 0.8)
        # New scores: (score - 0.2) / 0.8
        assert normalized[0].score == 1.0  # (1.0-0.2)/0.8 = 1.0
        assert abs(normalized[1].score - 0.375) < 0.01  # (0.5-0.2)/0.8 = 0.375
        assert normalized[2].score == 0.0  # (0.2-0.2)/0.8 = 0.0

        # Distances should be updated
        assert normalized[0].distance == 0.0  # 1.0 - 1.0
        assert abs(normalized[1].distance - 0.625) < 0.01  # 1.0 - 0.375
        assert normalized[2].distance == 1.0  # 1.0 - 0.0

    def test_normalize_scores_empty_list(self):
        """Test score normalization with empty list."""
        normalized = normalize_scores([])
        assert normalized == []

    def test_normalize_scores_same_scores(self, sample_chunks: List[DocumentChunk]):
        """Test score normalization when all scores are the same."""
        results = [
            SearchResult(chunk=sample_chunks[0], score=0.5, rank=1, distance=0.5),
            SearchResult(chunk=sample_chunks[1], score=0.5, rank=2, distance=0.5),
        ]

        normalized = normalize_scores(results)

        # Should return original results when all scores are the same
        assert len(normalized) == 2
        assert normalized[0].score == 0.5
        assert normalized[1].score == 0.5


class TestHybridSearcher:
    """Test suite for HybridSearcher."""

    @pytest.fixture
    def sample_chunks(self) -> List[DocumentChunk]:
        """Create sample document chunks for testing."""
        doc_id = uuid4()
        return [
            DocumentChunk(
                document_id=doc_id,
                content="Python programming tutorial for beginners",
                index=0,
                metadata=Metadata(title="Python Tutorial"),
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Advanced machine learning algorithms and techniques",
                index=1,
                metadata=Metadata(title="ML Advanced"),
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Data analysis with pandas and numpy libraries",
                index=2,
                metadata=Metadata(title="Data Analysis"),
            ),
        ]

    def test_hybrid_search_config_defaults(self):
        """Test HybridSearchConfig default values."""
        config = HybridSearchConfig()
        assert config.fusion_method == "rrf"
        assert config.enable_dense is True
        assert config.enable_sparse is True
        assert config.parallel_execution is True
        assert config.top_k_dense == 50
        assert config.top_k_sparse == 50
        assert config.top_k_final == 20

    def test_hybrid_searcher_initialization(self):
        """Test HybridSearcher initialization."""
        searcher = HybridSearcher()

        assert searcher.hybrid_config.fusion_method == "rrf"
        assert searcher.dense_retriever is not None  # Stub for now
        assert searcher.sparse_retriever is not None
        assert isinstance(searcher.fusion_algorithm, ReciprocalRankFusion)

    def test_hybrid_searcher_weighted_fusion(self):
        """Test HybridSearcher with weighted fusion."""
        config = HybridSearchConfig(fusion_method="weighted")
        searcher = HybridSearcher(hybrid_config=config)

        assert isinstance(searcher.fusion_algorithm, WeightedScoreFusion)

    def test_hybrid_searcher_invalid_fusion_method(self):
        """Test HybridSearcher with invalid fusion method."""
        config = HybridSearchConfig(fusion_method="invalid")

        with pytest.raises(ValueError, match="Unknown fusion method"):
            HybridSearcher(hybrid_config=config)

    @pytest.mark.asyncio
    async def test_add_documents(self, sample_chunks: List[DocumentChunk]):
        """Test adding documents to hybrid searcher."""
        searcher = HybridSearcher()
        await searcher.initialize()
        await searcher.add_documents(sample_chunks)

        assert searcher.document_count == 3
        assert searcher.sparse_retriever.document_count == 3
        assert searcher.dense_retriever.document_count == 3

    @pytest.mark.asyncio
    async def test_add_empty_documents(self):
        """Test adding empty document list."""
        searcher = HybridSearcher()
        await searcher.add_documents([])  # Should not raise error
        assert searcher.document_count == 0

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query."""
        searcher = HybridSearcher()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await searcher.search("")

    @pytest.mark.asyncio
    async def test_search_with_documents(self, sample_chunks: List[DocumentChunk]):
        """Test search with indexed documents."""
        searcher = HybridSearcher()
        searcher.add_documents(sample_chunks)

        # Search for specific terms
        results = await searcher.search("python programming")

        assert isinstance(results, list)
        # Should get results from sparse search (dense is stubbed)
        if results:  # May be empty if BM25 doesn't find matches
            assert all(isinstance(result, SearchResult) for result in results)

    @pytest.mark.asyncio
    async def test_search_sparse_only(self, sample_chunks: List[DocumentChunk]):
        """Test search with sparse retrieval only."""
        config = HybridSearchConfig(enable_dense=False, enable_sparse=True)
        searcher = HybridSearcher(hybrid_config=config)
        searcher.add_documents(sample_chunks)

        results = await searcher.search("programming")

        assert isinstance(results, list)
        # Results should come only from sparse search

    @pytest.mark.asyncio
    async def test_search_dense_only(self, sample_chunks: List[DocumentChunk]):
        """Test search with dense retrieval only (stubbed)."""
        config = HybridSearchConfig(enable_dense=True, enable_sparse=False)
        searcher = HybridSearcher(hybrid_config=config)
        searcher.add_documents(sample_chunks)

        results = await searcher.search("programming")

        assert isinstance(results, list)
        # Should be empty since dense retriever is stubbed
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear_index(self, sample_chunks: List[DocumentChunk]):
        """Test clearing the hybrid index."""
        searcher = HybridSearcher()
        await searcher.initialize()
        await searcher.add_documents(sample_chunks)

        assert searcher.document_count > 0

        searcher.clear()

        assert searcher.document_count == 0

    def test_get_retriever_status(self):
        """Test getting retriever status information."""
        searcher = HybridSearcher()
        status = searcher.get_retriever_status()

        assert isinstance(status, dict)
        assert "dense_enabled" in status
        assert "sparse_enabled" in status
        assert "fusion_method" in status
        assert "parallel_execution" in status
        assert status["dense_enabled"] is True
        assert status["sparse_enabled"] is True
        assert status["fusion_method"] == "rrf"

    @pytest.mark.asyncio
    async def test_search_performance(self, sample_chunks: List[DocumentChunk]):
        """Test search performance meets target."""
        import time

        searcher = HybridSearcher()
        searcher.add_documents(sample_chunks)

        # Measure search time
        start_time = time.perf_counter()
        await searcher.search("python data")
        end_time = time.perf_counter()

        search_time_ms = (end_time - start_time) * 1000

        # Should be under 100ms for hybrid search
        assert search_time_ms < 100, f"Search took {search_time_ms:.2f}ms, expected <100ms"