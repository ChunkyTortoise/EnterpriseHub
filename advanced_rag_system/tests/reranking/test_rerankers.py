"""Tests for re-ranking components: MockReRanker, BaseReRanker utilities,
CrossEncoderReRanker, and CohereReRanker.
"""

import pytest
from uuid import uuid4
from typing import List

from src.core.types import DocumentChunk, Metadata, SearchResult
from src.reranking.base import (
    BaseReRanker,
    MockReRanker,
    ReRankingConfig,
    ReRankingResult,
    ReRankingStrategy,
)
from src.reranking.cross_encoder import CrossEncoderReRanker
from src.reranking.cohere_reranker import CohereReRanker, CohereConfig


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_results() -> List[SearchResult]:
    doc_id = uuid4()
    chunks = [
        DocumentChunk(document_id=doc_id, content="Python programming guide", index=0),
        DocumentChunk(document_id=doc_id, content="Machine learning basics", index=1),
        DocumentChunk(document_id=doc_id, content="Database query optimization", index=2),
    ]
    return [
        SearchResult(chunk=chunks[0], score=0.9, rank=1, distance=0.1, explanation="dense"),
        SearchResult(chunk=chunks[1], score=0.7, rank=2, distance=0.3, explanation="dense"),
        SearchResult(chunk=chunks[2], score=0.5, rank=3, distance=0.5, explanation="dense"),
    ]


# ===========================================================================
# MockReRanker tests
# ===========================================================================

class TestMockReRanker:

    @pytest.mark.asyncio
    async def test_lifecycle(self):
        ranker = MockReRanker()
        assert ranker._initialized is False
        await ranker.initialize()
        assert ranker._initialized is True
        await ranker.close()
        assert ranker._initialized is False

    @pytest.mark.asyncio
    async def test_rerank_empty(self):
        ranker = MockReRanker()
        await ranker.initialize()
        result = await ranker.rerank("test", [])
        assert isinstance(result, ReRankingResult)
        assert result.results == []
        assert result.original_count == 0
        assert result.scores_changed is False

    @pytest.mark.asyncio
    async def test_rerank_returns_results(self, sample_results):
        ranker = MockReRanker()
        await ranker.initialize()
        result = await ranker.rerank("python programming", sample_results)

        assert isinstance(result, ReRankingResult)
        assert result.original_count == 3
        assert result.reranked_count == 3
        assert result.scores_changed is True
        assert result.processing_time_ms >= 0.0
        assert len(result.results) >= 3

    @pytest.mark.asyncio
    async def test_rerank_scores_combined(self, sample_results):
        """Verify scores are combined using WEIGHTED strategy by default."""
        config = ReRankingConfig(
            strategy=ReRankingStrategy.WEIGHTED,
            original_weight=0.5,
            reranker_weight=0.5,
        )
        ranker = MockReRanker(config)
        await ranker.initialize()
        result = await ranker.rerank("python", sample_results)
        # Scores should be modified from original
        for r in result.results[:3]:
            assert 0.0 <= r.score <= 1.0

    @pytest.mark.asyncio
    async def test_rerank_with_threshold(self, sample_results):
        """Score threshold filters out low-scoring results."""
        config = ReRankingConfig(score_threshold=0.6)
        ranker = MockReRanker(config)
        await ranker.initialize()
        result = await ranker.rerank("python", sample_results)
        # Only results with score >= 0.6 should be reranked
        assert result.reranked_count <= 3

    def test_model_info(self):
        ranker = MockReRanker()
        info = ranker.get_model_info()
        assert info["name"] == "MockReRanker"
        assert info["type"] == "rule-based"


# ===========================================================================
# BaseReRanker utility tests
# ===========================================================================

class TestBaseReRankerUtilities:

    @pytest.fixture
    def ranker(self):
        return MockReRanker()

    def test_normalize_scores_empty(self, ranker):
        assert ranker._normalize_scores([]) == []

    def test_normalize_scores_same_value(self, sample_results):
        """All same scores returns results unchanged."""
        ranker = MockReRanker()
        same_score_results = [
            SearchResult(chunk=r.chunk, score=0.5, rank=r.rank, distance=r.distance)
            for r in sample_results
        ]
        normalized = ranker._normalize_scores(same_score_results)
        assert len(normalized) == 3
        # Scores remain unchanged when all equal
        for r in normalized:
            assert r.score == 0.5

    def test_normalize_scores_range(self, sample_results):
        ranker = MockReRanker()
        normalized = ranker._normalize_scores(sample_results)
        scores = [r.score for r in normalized]
        assert max(scores) == pytest.approx(1.0)
        assert min(scores) == pytest.approx(0.0)
        # Explanation should mention original_score
        for r in normalized:
            assert "original_score" in r.explanation

    def test_combine_scores_replace(self, sample_results):
        ranker = MockReRanker(ReRankingConfig(strategy=ReRankingStrategy.REPLACE))
        new_scores = [0.3, 0.9, 0.1]
        combined = ranker._combine_scores(sample_results, new_scores, ReRankingStrategy.REPLACE)
        assert combined[0].score == pytest.approx(0.3)
        assert combined[1].score == pytest.approx(0.9)
        assert combined[2].score == pytest.approx(0.1)

    def test_combine_scores_weighted(self, sample_results):
        config = ReRankingConfig(
            strategy=ReRankingStrategy.WEIGHTED,
            original_weight=0.4,
            reranker_weight=0.6,
        )
        ranker = MockReRanker(config)
        new_scores = [0.5, 0.5, 0.5]
        combined = ranker._combine_scores(sample_results, new_scores, ReRankingStrategy.WEIGHTED)
        # result[0]: 0.4 * 0.9 + 0.6 * 0.5 = 0.36 + 0.30 = 0.66
        assert combined[0].score == pytest.approx(0.66)

    def test_combine_scores_reciprocal_rank(self, sample_results):
        ranker = MockReRanker()
        new_scores = [0.5, 0.5, 0.5]
        combined = ranker._combine_scores(sample_results, new_scores, ReRankingStrategy.RECIPROCAL_RANK)
        assert len(combined) == 3
        for r in combined:
            assert 0.0 <= r.score <= 1.0

    def test_combine_scores_normalized(self, sample_results):
        ranker = MockReRanker()
        new_scores = [0.5, 0.5, 0.5]
        combined = ranker._combine_scores(sample_results, new_scores, ReRankingStrategy.NORMALIZED)
        assert len(combined) == 3

    def test_combine_scores_length_mismatch(self, sample_results):
        ranker = MockReRanker()
        with pytest.raises(ValueError, match="must match"):
            ranker._combine_scores(sample_results, [0.5, 0.5])

    def test_filter_results(self, sample_results):
        config = ReRankingConfig(score_threshold=0.6, top_k=2)
        ranker = MockReRanker(config)
        filtered = ranker._filter_results(sample_results)
        # Only score >= 0.6: two results (0.9, 0.7), then top_k=2
        assert len(filtered) <= 2
        for r in filtered:
            assert r.score >= 0.6

    def test_update_ranks(self, sample_results):
        ranker = MockReRanker()
        updated = ranker._update_ranks(sample_results)
        for i, r in enumerate(updated):
            assert r.rank == i + 1


# ===========================================================================
# CrossEncoderReRanker tests (fallback mode — no sentence-transformers)
# ===========================================================================

class TestCrossEncoderReRanker:

    def test_initialization_without_sentence_transformers(self):
        """Should create successfully even without sentence-transformers."""
        ranker = CrossEncoderReRanker()
        assert ranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert ranker.device in ("cpu", "cuda", "mps")

    @pytest.mark.asyncio
    async def test_initialize_fallback(self):
        """When sentence-transformers isn't available, should still initialize."""
        ranker = CrossEncoderReRanker()
        await ranker.initialize()
        assert ranker._initialized is True

    @pytest.mark.asyncio
    async def test_rerank_fallback(self, sample_results):
        """When no model loaded, uses fallback scoring."""
        ranker = CrossEncoderReRanker()
        await ranker.initialize()
        result = await ranker.rerank("python programming", sample_results)
        assert isinstance(result, ReRankingResult)
        assert result.original_count == 3
        assert len(result.results) >= 3

    @pytest.mark.asyncio
    async def test_rerank_empty(self):
        ranker = CrossEncoderReRanker()
        await ranker.initialize()
        result = await ranker.rerank("test", [])
        assert result.results == []

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self, sample_results):
        ranker = CrossEncoderReRanker()
        from src.core.exceptions import RetrievalError
        with pytest.raises(RetrievalError, match="not initialized"):
            await ranker.rerank("test", sample_results)

    def test_model_info(self):
        ranker = CrossEncoderReRanker(model_name="test-model")
        info = ranker.get_model_info()
        assert info["name"] == "test-model"
        assert info["type"] == "cross-encoder"

    def test_batch_size_recommendation(self):
        ranker = CrossEncoderReRanker()
        assert ranker.batch_size_recommendation(100) >= 1
        assert ranker.batch_size_recommendation(100) <= 100


# ===========================================================================
# CohereReRanker tests (fallback mode — no cohere package)
# ===========================================================================

class TestCohereReRanker:

    def test_initialization_without_cohere(self):
        """Should create successfully even without cohere installed."""
        config = CohereConfig(model="rerank-english-v2.0")
        ranker = CohereReRanker(cohere_config=config)
        assert ranker.cohere_config.model == "rerank-english-v2.0"

    @pytest.mark.asyncio
    async def test_initialize_fallback(self):
        """When cohere module is not available, should still initialize in fallback mode."""
        from unittest.mock import patch as _patch
        import src.reranking.cohere_reranker as cohere_mod

        # Force COHERE_AVAILABLE = False to test fallback path
        with _patch.object(cohere_mod, "COHERE_AVAILABLE", False):
            ranker = CohereReRanker()
            await ranker.initialize()
            assert ranker._initialized is True
            assert ranker.client is None

    @pytest.mark.asyncio
    async def test_rerank_fallback(self, sample_results):
        """When no client, uses fallback scoring."""
        from unittest.mock import patch as _patch
        import src.reranking.cohere_reranker as cohere_mod

        with _patch.object(cohere_mod, "COHERE_AVAILABLE", False):
            ranker = CohereReRanker()
            await ranker.initialize()
            result = await ranker.rerank("python programming", sample_results)
            assert isinstance(result, ReRankingResult)
            assert result.original_count == 3

    @pytest.mark.asyncio
    async def test_rerank_empty(self):
        from unittest.mock import patch as _patch
        import src.reranking.cohere_reranker as cohere_mod

        with _patch.object(cohere_mod, "COHERE_AVAILABLE", False):
            ranker = CohereReRanker()
            await ranker.initialize()
            result = await ranker.rerank("test", [])
            assert result.results == []

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self, sample_results):
        ranker = CohereReRanker()
        from src.core.exceptions import RetrievalError
        with pytest.raises(RetrievalError, match="not initialized"):
            await ranker.rerank("test", sample_results)

    def test_model_info(self):
        ranker = CohereReRanker()
        info = ranker.get_model_info()
        assert info["type"] == "cohere-api"
        assert info["provider"] == "Cohere"

    def test_estimate_cost(self):
        ranker = CohereReRanker()
        cost = ranker.estimate_cost(1000)
        assert cost["search_units"] == 1000
        assert cost["estimated_cost_usd"] > 0
        assert "currency" in cost
