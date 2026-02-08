"""Comprehensive tests for the re-ranking system.

This module tests all re-ranking components including:
- BaseReRanker with all 4 re-ranking strategies
- CrossEncoderReRanker with local cross-encoder models
- CohereReRanker with API-based re-ranking
- Integration tests for the complete re-ranking pipeline
"""

import asyncio
import time
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from src.core.exceptions import RateLimitError, RetrievalError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.reranking.base import (
    BaseReRanker,
    MockReRanker,
    ReRankingConfig,
    ReRankingResult,
    ReRankingStrategy,
)
from src.reranking.cohere_reranker import CohereConfig, CohereReRanker
from src.reranking.cross_encoder import CrossEncoderReRanker

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_document_chunks() -> List[DocumentChunk]:
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            document_id=uuid4(),
            content="Machine learning is a subset of artificial intelligence",
            index=0,
            metadata=Metadata(title="ML Basics"),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Deep learning uses neural networks with multiple layers",
            index=1,
            metadata=Metadata(title="Deep Learning"),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Natural language processing enables computers to understand text",
            index=2,
            metadata=Metadata(title="NLP"),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Computer vision allows machines to interpret visual information",
            index=3,
            metadata=Metadata(title="Computer Vision"),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Reinforcement learning trains agents through rewards and penalties",
            index=4,
            metadata=Metadata(title="RL"),
        ),
    ]


@pytest.fixture
def sample_search_results(sample_document_chunks) -> List[SearchResult]:
    """Create sample search results for testing."""
    return [
        SearchResult(
            chunk=chunk,
            score=0.9 - (i * 0.1),  # Descending scores: 0.9, 0.8, 0.7, 0.6, 0.5
            rank=i + 1,
            distance=0.1 + (i * 0.1),
        )
        for i, chunk in enumerate(sample_document_chunks)
    ]


@pytest.fixture
def reranking_config() -> ReRankingConfig:
    """Create default re-ranking configuration."""
    return ReRankingConfig(
        strategy=ReRankingStrategy.WEIGHTED,
        original_weight=0.3,
        reranker_weight=0.7,
        top_k=100,
        score_threshold=0.0,
        normalize_scores=True,
        batch_size=32,
        timeout_seconds=30,
    )


@pytest.fixture
def mock_reranker(reranking_config) -> MockReRanker:
    """Create a mock re-ranker for testing."""
    return MockReRanker(config=reranking_config)


@pytest.fixture
def cohere_config() -> CohereConfig:
    """Create Cohere configuration for testing."""
    return CohereConfig(
        api_key="test-api-key",
        model="rerank-english-v2.0",
        max_chunks_per_doc=10,
        return_documents=False,
        top_n=None,
        timeout_seconds=30,
        max_retries=3,
        retry_delay=1.0,
    )


# ============================================================================
# BaseReRanker Strategy Tests
# ============================================================================


class TestReRankingStrategies:
    """Test suite for all re-ranking strategies."""

    @pytest.mark.asyncio
    async def test_replace_strategy(self, sample_search_results):
        """Test REPLACE strategy replaces original scores completely."""
        config = ReRankingConfig(strategy=ReRankingStrategy.REPLACE)
        reranker = MockReRanker(config)
        await reranker.initialize()

        query = "machine learning"
        result = await reranker.rerank(query, sample_search_results)

        assert result.scores_changed is True
        assert len(result.results) == len(sample_search_results)
        # Scores should be different from originals
        for i, res in enumerate(result.results[:5]):
            if i < len(sample_search_results):
                assert res.score != sample_search_results[i].score

    @pytest.mark.asyncio
    async def test_weighted_strategy(self, sample_search_results):
        """Test WEIGHTED strategy combines scores with configured weights."""
        config = ReRankingConfig(strategy=ReRankingStrategy.WEIGHTED, original_weight=0.3, reranker_weight=0.7)
        reranker = MockReRanker(config)
        await reranker.initialize()

        query = "artificial intelligence"
        result = await reranker.rerank(query, sample_search_results)

        assert result.scores_changed is True
        assert len(result.results) == len(sample_search_results)
        # All scores should be in valid range
        for res in result.results:
            assert 0.0 <= res.score <= 1.0

    @pytest.mark.asyncio
    async def test_reciprocal_rank_strategy(self, sample_search_results):
        """Test RECIPROCAL_RANK strategy uses RRF formula."""
        config = ReRankingConfig(strategy=ReRankingStrategy.RECIPROCAL_RANK)
        reranker = MockReRanker(config)
        await reranker.initialize()

        query = "neural networks"
        result = await reranker.rerank(query, sample_search_results)

        assert result.scores_changed is True
        assert len(result.results) == len(sample_search_results)
        # Results should be reordered
        assert result.results != sample_search_results

    @pytest.mark.asyncio
    async def test_normalized_strategy(self, sample_search_results):
        """Test NORMALIZED strategy normalizes and combines scores."""
        config = ReRankingConfig(strategy=ReRankingStrategy.NORMALIZED, normalize_scores=True)
        reranker = MockReRanker(config)
        await reranker.initialize()

        query = "deep learning"
        result = await reranker.rerank(query, sample_search_results)

        assert result.scores_changed is True
        assert len(result.results) == len(sample_search_results)
        # Scores should be normalized
        for res in result.results:
            assert 0.0 <= res.score <= 1.0

    @pytest.mark.asyncio
    async def test_strategy_validation_invalid_strategy(self, sample_search_results):
        """Test that invalid strategy raises appropriate error."""
        config = ReRankingConfig()
        reranker = MockReRanker(config)
        await reranker.initialize()

        # Temporarily set an invalid strategy
        original_strategy = reranker.config.strategy
        reranker.config.strategy = "invalid_strategy"

        query = "test query"
        rerank_scores = [0.5] * len(sample_search_results)

        with pytest.raises((ValueError, AttributeError)):
            reranker._combine_scores(sample_search_results, rerank_scores)

        reranker.config.strategy = original_strategy


class TestBaseReRankerEdgeCases:
    """Test edge cases for BaseReRanker."""

    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Test handling of empty results list."""
        reranker = MockReRanker()
        await reranker.initialize()

        query = "test query"
        result = await reranker.rerank(query, [])

        assert result.results == []
        assert result.original_count == 0
        assert result.reranked_count == 0
        assert result.scores_changed is False
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_single_result(self, sample_document_chunks):
        """Test handling of single result."""
        single_result = [SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)]

        reranker = MockReRanker()
        await reranker.initialize()

        query = "machine learning"
        result = await reranker.rerank(query, single_result)

        assert len(result.results) == 1
        assert result.original_count == 1
        assert result.reranked_count == 1

    @pytest.mark.asyncio
    async def test_tied_scores(self, sample_document_chunks):
        """Test handling of results with tied scores."""
        tied_results = [
            SearchResult(
                chunk=chunk,
                score=0.8,  # All same score
                rank=i + 1,
                distance=0.2,
            )
            for i, chunk in enumerate(sample_document_chunks[:3])
        ]

        reranker = MockReRanker()
        await reranker.initialize()

        query = "artificial intelligence"
        result = await reranker.rerank(query, tied_results)

        assert len(result.results) == 3
        # Should still produce valid results
        for res in result.results:
            assert 0.0 <= res.score <= 1.0
            assert res.rank >= 1

    @pytest.mark.asyncio
    async def test_score_threshold_filtering(self, sample_search_results):
        """Test that score threshold filters results correctly."""
        config = ReRankingConfig(score_threshold=0.75)
        reranker = MockReRanker(config)
        await reranker.initialize()

        query = "test query"
        result = await reranker.rerank(query, sample_search_results)

        # Only results with score >= 0.75 should be reranked
        # Original scores: 0.9, 0.8, 0.7, 0.6, 0.5
        # So first 2 should be reranked
        assert result.reranked_count <= 2

    @pytest.mark.asyncio
    async def test_top_k_limiting(self, sample_search_results):
        """Test that top_k limits the number of results."""
        config = ReRankingConfig(top_k=3)
        reranker = MockReRanker(config)
        await reranker.initialize()

        query = "test query"
        result = await reranker.rerank(query, sample_search_results)

        # Should only process top 3 results
        assert result.reranked_count <= 3

    def test_normalize_scores(self, sample_search_results):
        """Test score normalization."""
        reranker = MockReRanker()

        # Modify scores to have a range
        modified_results = [
            SearchResult(
                chunk=r.chunk,
                score=0.5 + i * 0.1,  # 0.5, 0.6, 0.7, 0.8, 0.9
                rank=r.rank,
                distance=r.distance,
            )
            for i, r in enumerate(sample_search_results)
        ]

        normalized = reranker._normalize_scores(modified_results)

        # Check that scores are normalized to [0, 1]
        scores = [r.score for r in normalized]
        assert min(scores) == 0.0
        assert max(scores) == 1.0

    def test_normalize_scores_empty(self):
        """Test normalization of empty results."""
        reranker = MockReRanker()
        normalized = reranker._normalize_scores([])
        assert normalized == []

    def test_normalize_scores_same_values(self, sample_document_chunks):
        """Test normalization when all scores are the same."""
        reranker = MockReRanker()

        same_score_results = [
            SearchResult(chunk=chunk, score=0.5, rank=i + 1, distance=0.5)
            for i, chunk in enumerate(sample_document_chunks[:3])
        ]

        normalized = reranker._normalize_scores(same_score_results)

        # Should return original results unchanged
        assert len(normalized) == 3
        for res in normalized:
            assert res.score == 0.5


class TestReRankingConfig:
    """Test suite for ReRankingConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ReRankingConfig()

        assert config.strategy == ReRankingStrategy.WEIGHTED
        assert config.original_weight == 0.3
        assert config.reranker_weight == 0.7
        assert config.top_k == 100
        assert config.score_threshold == 0.0
        assert config.normalize_scores is True
        assert config.batch_size == 32
        assert config.timeout_seconds == 30

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ReRankingConfig(
            strategy=ReRankingStrategy.REPLACE,
            original_weight=0.5,
            reranker_weight=0.5,
            top_k=50,
            score_threshold=0.5,
            normalize_scores=False,
            batch_size=16,
            timeout_seconds=60,
        )

        assert config.strategy == ReRankingStrategy.REPLACE
        assert config.original_weight == 0.5
        assert config.reranker_weight == 0.5
        assert config.top_k == 50
        assert config.score_threshold == 0.5
        assert config.normalize_scores is False
        assert config.batch_size == 16
        assert config.timeout_seconds == 60


# ============================================================================
# CrossEncoderReRanker Tests
# ============================================================================


class TestCrossEncoderReRankerInitialization:
    """Test CrossEncoderReRanker initialization."""

    def test_initialization_defaults(self):
        """Test initialization with default parameters."""
        reranker = CrossEncoderReRanker()

        assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert reranker.max_length == 512
        assert reranker.device in ["cpu", "cuda", "mps"]
        assert reranker.model is None
        assert reranker._initialized is False

    def test_initialization_custom_params(self):
        """Test initialization with custom parameters."""
        config = ReRankingConfig(top_k=50)
        reranker = CrossEncoderReRanker(model_name="custom-model", config=config, device="cpu", max_length=256)

        assert reranker.model_name == "custom-model"
        assert reranker.max_length == 256
        assert reranker.device == "cpu"
        assert reranker.config.top_k == 50

    def test_get_device(self):
        """Test device selection logic."""
        reranker = CrossEncoderReRanker()
        device = reranker._get_device()

        # Should return a valid device string
        assert device in ["cpu", "cuda", "mps"]

    def test_get_model_info_uninitialized(self):
        """Test getting model info before initialization."""
        reranker = CrossEncoderReRanker()
        info = reranker.get_model_info()

        assert info["name"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert info["type"] == "cross-encoder"
        assert info["initialized"] is False
        assert "sentence_transformers_available" in info


class TestCrossEncoderReRankerFunctionality:
    """Test CrossEncoderReRanker functionality."""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful initialization."""
        reranker = CrossEncoderReRanker()

        with patch("src.reranking.cross_encoder.SENTENCE_TRANSFORMERS_AVAILABLE", False):
            await reranker.initialize()
            assert reranker._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test initialization when already initialized."""
        reranker = CrossEncoderReRanker()
        reranker._initialized = True

        # Should not raise error
        await reranker.initialize()
        assert reranker._initialized is True

    @pytest.mark.asyncio
    async def test_close(self):
        """Test cleanup of resources."""
        reranker = CrossEncoderReRanker()
        reranker._initialized = True

        await reranker.close()

        assert reranker.model is None
        assert reranker._initialized is False

    @pytest.mark.asyncio
    async def test_rerank_not_initialized(self, sample_search_results):
        """Test reranking before initialization raises error."""
        reranker = CrossEncoderReRanker()

        with pytest.raises(RetrievalError) as exc_info:
            await reranker.rerank("query", sample_search_results)

        assert "not initialized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rerank_empty_results(self):
        """Test reranking with empty results."""
        reranker = CrossEncoderReRanker()
        await reranker.initialize()

        result = await reranker.rerank("query", [])

        assert result.results == []
        assert result.original_count == 0
        assert result.reranked_count == 0
        assert result.scores_changed is False

    @pytest.mark.asyncio
    async def test_rerank_with_results(self, sample_search_results):
        """Test reranking with valid results."""
        reranker = CrossEncoderReRanker()
        await reranker.initialize()

        query = "machine learning"
        result = await reranker.rerank(query, sample_search_results)

        assert len(result.results) == len(sample_search_results)
        assert result.original_count == len(sample_search_results)
        assert result.processing_time_ms >= 0
        assert result.model_info["type"] == "cross-encoder"

    @pytest.mark.asyncio
    async def test_fallback_scoring(self, sample_search_results):
        """Test fallback scoring when model is unavailable."""
        reranker = CrossEncoderReRanker()
        await reranker.initialize()

        query = "machine learning"
        scores = await reranker._fallback_scoring(query, sample_search_results)

        assert len(scores) == len(sample_search_results)
        # All scores should be in [0, 1] range
        for score in scores:
            assert 0.0 <= score <= 1.0

    def test_batch_size_recommendation(self):
        """Test batch size recommendations."""
        reranker_cpu = CrossEncoderReRanker(device="cpu")
        reranker_cuda = CrossEncoderReRanker(device="cuda")
        reranker_other = CrossEncoderReRanker(device="mps")

        assert reranker_cpu.batch_size_recommendation(100) <= 16
        assert reranker_cuda.batch_size_recommendation(100) <= 32
        assert reranker_other.batch_size_recommendation(100) <= 24

    def test_score_batch_fallback(self):
        """Test batch scoring fallback on failure."""
        reranker = CrossEncoderReRanker()
        reranker.model = Mock()
        reranker.model.predict = Mock(side_effect=Exception("Model error"))

        pairs = [["query", "doc1"], ["query", "doc2"]]
        scores = reranker._score_batch(pairs)

        # Should return neutral scores on failure
        assert len(scores) == len(pairs)
        for score in scores:
            assert score == 0.5


# ============================================================================
# CohereReRanker Tests
# ============================================================================


class TestCohereReRankerInitialization:
    """Test CohereReRanker initialization."""

    def test_initialization_defaults(self):
        """Test initialization with default parameters."""
        with patch.dict("os.environ", {"COHERE_API_KEY": "test-key"}):
            reranker = CohereReRanker()

            assert reranker.cohere_config.model == "rerank-english-v2.0"
            assert reranker.cohere_config.max_chunks_per_doc == 10
            assert reranker.cohere_config.max_retries == 3
            assert reranker.client is None
            assert reranker._initialized is False

    def test_initialization_custom_config(self, cohere_config):
        """Test initialization with custom config."""
        reranker = CohereReRanker(cohere_config=cohere_config)

        assert reranker.cohere_config.api_key == "test-api-key"
        assert reranker.cohere_config.model == "rerank-english-v2.0"
        assert reranker.cohere_config.max_retries == 3

    def test_get_api_key_from_config(self, cohere_config):
        """Test getting API key from config."""
        reranker = CohereReRanker(cohere_config=cohere_config)
        api_key = reranker._get_api_key()

        assert api_key == "test-api-key"

    def test_get_api_key_from_environment(self):
        """Test getting API key from environment variable."""
        with patch.dict("os.environ", {"COHERE_API_KEY": "env-api-key"}):
            reranker = CohereReRanker()
            api_key = reranker._get_api_key()

            assert api_key == "env-api-key"

    def test_get_api_key_missing(self):
        """Test error when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            reranker = CohereReRanker()

            with pytest.raises(RetrievalError) as exc_info:
                reranker._get_api_key()

            assert "not found" in str(exc_info.value).lower()

    def test_get_model_info(self):
        """Test getting model information."""
        reranker = CohereReRanker()
        info = reranker.get_model_info()

        assert info["type"] == "cohere-api"
        assert info["provider"] == "Cohere"
        assert "max_chunks_per_doc" in info


class TestCohereReRankerFunctionality:
    """Test CohereReRanker functionality."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, cohere_config):
        """Test successful initialization."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", False):
            reranker = CohereReRanker(cohere_config=cohere_config)
            await reranker.initialize()
            assert reranker._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, cohere_config):
        """Test initialization when already initialized."""
        reranker = CohereReRanker(cohere_config=cohere_config)
        reranker._initialized = True

        # Should not raise error
        await reranker.initialize()
        assert reranker._initialized is True

    @pytest.mark.asyncio
    async def test_close(self, cohere_config):
        """Test cleanup of resources."""
        reranker = CohereReRanker(cohere_config=cohere_config)
        reranker._initialized = True
        reranker.client = Mock()

        await reranker.close()

        assert reranker.client is None
        assert reranker._initialized is False

    @pytest.mark.asyncio
    async def test_rerank_not_initialized(self, sample_search_results, cohere_config):
        """Test reranking before initialization raises error."""
        reranker = CohereReRanker(cohere_config=cohere_config)

        with pytest.raises(RetrievalError) as exc_info:
            await reranker.rerank("query", sample_search_results)

        assert "not initialized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rerank_empty_results(self, cohere_config):
        """Test reranking with empty results."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", False):
            reranker = CohereReRanker(cohere_config=cohere_config)
            await reranker.initialize()

            result = await reranker.rerank("query", [])

            assert result.results == []
            assert result.original_count == 0
            assert result.reranked_count == 0
            assert result.scores_changed is False

    @pytest.mark.asyncio
    async def test_rerank_with_results(self, sample_search_results, cohere_config):
        """Test reranking with valid results."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", False):
            reranker = CohereReRanker(cohere_config=cohere_config)
            await reranker.initialize()

            query = "machine learning"
            result = await reranker.rerank(query, sample_search_results)

            assert len(result.results) == len(sample_search_results)
            assert result.original_count == len(sample_search_results)
            assert result.processing_time_ms >= 0
            assert result.model_info["type"] == "cohere-api"

    @pytest.mark.asyncio
    async def test_fallback_scoring(self, sample_search_results, cohere_config):
        """Test fallback scoring when API is unavailable."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", False):
            reranker = CohereReRanker(cohere_config=cohere_config)
            await reranker.initialize()

            query = "machine learning"
            scores = await reranker._fallback_scoring(query, sample_search_results)

            assert len(scores) == len(sample_search_results)
            # All scores should be in [0, 1] range
            for score in scores:
                assert 0.0 <= score <= 1.0


class TestCohereAPIInteraction:
    """Test Cohere API interaction with mocking."""

    @pytest.mark.asyncio
    async def test_call_cohere_with_retry_success(self, cohere_config):
        """Test successful API call with retry logic."""
        mock_response = Mock()
        mock_response.results = [
            Mock(index=0, relevance_score=0.9),
            Mock(index=1, relevance_score=0.8),
        ]

        mock_client = Mock()
        mock_client.rerank = Mock(return_value=mock_response)

        reranker = CohereReRanker(cohere_config=cohere_config)
        reranker.client = mock_client

        documents = ["doc1", "doc2"]
        response = await reranker._call_cohere_with_retry("query", documents)

        assert response == mock_response
        mock_client.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_cohere_with_retry_rate_limit(self, cohere_config):
        """Test rate limit error handling."""
        mock_client = Mock()
        mock_client.rerank = Mock(side_effect=Exception("rate limit exceeded (429)"))

        reranker = CohereReRanker(cohere_config=cohere_config)
        reranker.client = mock_client

        documents = ["doc1"]

        with pytest.raises(RateLimitError) as exc_info:
            await reranker._call_cohere_with_retry("query", documents)

        assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_call_cohere_with_retry_exhausted(self, cohere_config):
        """Test retry exhaustion."""
        mock_client = Mock()
        mock_client.rerank = Mock(side_effect=Exception("API error"))

        # Set short retry config for faster test
        cohere_config.max_retries = 2
        cohere_config.retry_delay = 0.01

        reranker = CohereReRanker(cohere_config=cohere_config)
        reranker.client = mock_client

        documents = ["doc1"]

        with pytest.raises(RetrievalError) as exc_info:
            await reranker._call_cohere_with_retry("query", documents)

        assert "failed after" in str(exc_info.value).lower()
        assert mock_client.rerank.call_count == 2

    def test_extract_scores_from_response(self, cohere_config):
        """Test score extraction from Cohere response."""
        reranker = CohereReRanker(cohere_config=cohere_config)

        mock_response = Mock()
        mock_response.results = [
            Mock(index=0, relevance_score=0.95),
            Mock(index=2, relevance_score=0.85),
        ]

        scores = reranker._extract_scores_from_response(mock_response, 3)

        assert len(scores) == 3
        assert scores[0] == 0.95
        assert scores[1] == 0.1  # Default for missing
        assert scores[2] == 0.85

    def test_extract_scores_no_results(self, cohere_config):
        """Test score extraction when response has no results."""
        reranker = CohereReRanker(cohere_config=cohere_config)

        mock_response = Mock()
        del mock_response.results  # Remove results attribute

        scores = reranker._extract_scores_from_response(mock_response, 3)

        assert len(scores) == 3
        # Should return neutral scores
        for score in scores:
            assert score == 0.5

    def test_extract_scores_clamping(self, cohere_config):
        """Test that scores are clamped to [0, 1] range."""
        reranker = CohereReRanker(cohere_config=cohere_config)

        mock_response = Mock()
        mock_response.results = [
            Mock(index=0, relevance_score=1.5),  # Above 1
            Mock(index=1, relevance_score=-0.5),  # Below 0
        ]

        scores = reranker._extract_scores_from_response(mock_response, 2)

        assert scores[0] == 1.0  # Clamped to 1
        # Negative scores are clamped to 0.0, then the fallback assigns 0.1 to any remaining 0.0 scores
        # Since the logic sets 0.0 first, then replaces with 0.1 for any == 0.0,
        # the -0.5 score gets clamped to 0.0, then replaced with 0.1 by the fallback
        assert scores[1] == 0.1  # Clamped to 0, then replaced with fallback 0.1

    def test_estimate_cost(self, cohere_config):
        """Test cost estimation."""
        reranker = CohereReRanker(cohere_config=cohere_config)

        cost_estimate = reranker.estimate_cost(1000)

        assert "search_units" in cost_estimate
        assert "estimated_cost_usd" in cost_estimate
        assert cost_estimate["search_units"] == 1000
        assert cost_estimate["estimated_cost_usd"] > 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestReRankingPipeline:
    """Integration tests for the complete re-ranking pipeline."""

    @pytest.mark.asyncio
    async def test_mock_reranker_full_pipeline(self, sample_search_results):
        """Test complete pipeline with MockReRanker."""
        reranker = MockReRanker()
        await reranker.initialize()

        query = "artificial intelligence and machine learning"
        result = await reranker.rerank(query, sample_search_results)

        # Verify result structure
        assert isinstance(result, ReRankingResult)
        assert len(result.results) == len(sample_search_results)
        assert result.original_count == len(sample_search_results)
        assert result.reranked_count > 0
        assert result.processing_time_ms >= 0
        assert result.scores_changed is True

        # Verify result ordering and scores
        for i, res in enumerate(result.results):
            assert res.rank == i + 1
            assert 0.0 <= res.score <= 1.0

        await reranker.close()

    @pytest.mark.asyncio
    async def test_cross_encoder_full_pipeline(self, sample_search_results):
        """Test complete pipeline with CrossEncoderReRanker."""
        reranker = CrossEncoderReRanker()
        await reranker.initialize()

        query = "neural networks deep learning"
        result = await reranker.rerank(query, sample_search_results)

        # Verify result structure
        assert isinstance(result, ReRankingResult)
        assert len(result.results) == len(sample_search_results)

        await reranker.close()

    @pytest.mark.asyncio
    async def test_cohere_full_pipeline(self, sample_search_results, cohere_config):
        """Test complete pipeline with CohereReRanker."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", False):
            reranker = CohereReRanker(cohere_config=cohere_config)
            await reranker.initialize()

            query = "natural language processing"
            result = await reranker.rerank(query, sample_search_results)

            # Verify result structure
            assert isinstance(result, ReRankingResult)
            assert len(result.results) == len(sample_search_results)

            await reranker.close()

    @pytest.mark.asyncio
    async def test_multiple_rerankers_sequence(self, sample_search_results):
        """Test using multiple re-rankers in sequence."""
        # First re-ranker
        mock_reranker = MockReRanker(config=ReRankingConfig(strategy=ReRankingStrategy.WEIGHTED))
        await mock_reranker.initialize()

        query = "machine learning algorithms"
        result1 = await mock_reranker.rerank(query, sample_search_results)

        # Second re-ranker processes first's output
        cross_encoder = CrossEncoderReRanker(config=ReRankingConfig(strategy=ReRankingStrategy.REPLACE))
        await cross_encoder.initialize()

        result2 = await cross_encoder.rerank(query, result1.results)

        # Verify pipeline worked
        assert len(result2.results) == len(sample_search_results)
        assert result2.processing_time_ms >= result1.processing_time_ms

        await mock_reranker.close()
        await cross_encoder.close()

    @pytest.mark.asyncio
    async def test_reranker_statistics(self, sample_search_results):
        """Test getting statistics from re-ranker."""
        reranker = MockReRanker()
        await reranker.initialize()

        stats = reranker.get_stats()

        assert "config" in stats
        assert "model_info" in stats
        assert stats["config"]["strategy"] == ReRankingStrategy.WEIGHTED.value
        assert "original_weight" in stats["config"]

        await reranker.close()


class TestReRankingPerformance:
    """Performance-related tests for re-ranking."""

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, sample_search_results):
        """Test that processing time is accurately tracked."""
        reranker = MockReRanker()
        await reranker.initialize()

        start = time.time()
        result = await reranker.rerank("test query", sample_search_results)
        end = time.time()

        actual_time_ms = (end - start) * 1000

        # Reported time should be reasonable
        assert result.processing_time_ms >= 0
        assert result.processing_time_ms < actual_time_ms * 2  # Allow some margin

        await reranker.close()

    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, sample_document_chunks):
        """Test handling of larger result sets."""
        # Create many results
        many_results = []
        for i in range(50):
            chunk = DocumentChunk(
                document_id=uuid4(),
                content=f"Document content number {i} about machine learning",
                index=i,
                metadata=Metadata(),
            )
            many_results.append(
                SearchResult(chunk=chunk, score=0.9 - (i * 0.01), rank=i + 1, distance=0.1 + (i * 0.01))
            )

        reranker = MockReRanker(config=ReRankingConfig(top_k=100))
        await reranker.initialize()

        result = await reranker.rerank("machine learning", many_results)

        assert len(result.results) == 50
        assert result.reranked_count == 50

        await reranker.close()

    @pytest.mark.asyncio
    async def test_batch_processing(self, sample_document_chunks):
        """Test batch processing of results."""
        # Create results that would require batching
        batch_results = []
        for i in range(64):  # More than default batch size
            chunk = DocumentChunk(document_id=uuid4(), content=f"Content {i}", index=i, metadata=Metadata())
            batch_results.append(SearchResult(chunk=chunk, score=0.8, rank=i + 1, distance=0.2))

        reranker = CrossEncoderReRanker(config=ReRankingConfig(batch_size=32))
        await reranker.initialize()

        result = await reranker.rerank("query", batch_results)

        assert len(result.results) == 64

        await reranker.close()


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling across re-rankers."""

    @pytest.mark.asyncio
    async def test_cross_encoder_load_failure(self):
        """Test handling of cross-encoder model loading failure."""
        with patch("src.reranking.cross_encoder.SENTENCE_TRANSFORMERS_AVAILABLE", False):
            reranker = CrossEncoderReRanker()

            # Should not raise during initialize when ST not available
            await reranker.initialize()
            assert reranker._initialized is True
            assert reranker.model is None

    @pytest.mark.asyncio
    async def test_cohere_connection_test_failure(self, cohere_config):
        """Test handling of Cohere connection test failure."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", True):
            reranker = CohereReRanker(cohere_config=cohere_config)

            with patch.object(reranker, "_test_connection", side_effect=Exception("Connection failed")):
                with pytest.raises(RetrievalError):
                    await reranker.initialize()

    @pytest.mark.asyncio
    async def test_score_pairs_exception_handling(self, sample_search_results):
        """Test exception handling in _score_pairs."""
        reranker = CrossEncoderReRanker()
        await reranker.initialize()

        # Force an exception by making model raise
        reranker.model = Mock()
        reranker.model.predict = Mock(side_effect=Exception("Prediction failed"))

        # Should fallback to fallback_scoring
        scores = await reranker._score_pairs("query", sample_search_results)

        assert len(scores) == len(sample_search_results)
        # Should have fallback scores
        for score in scores:
            assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_cohere_rerank_exception_handling(self, sample_search_results, cohere_config):
        """Test exception handling in Cohere rerank."""
        with patch("src.reranking.cohere_reranker.COHERE_AVAILABLE", False):
            reranker = CohereReRanker(cohere_config=cohere_config)
            await reranker.initialize()

            # Should handle exceptions gracefully
            with patch.object(reranker, "_cohere_rerank", side_effect=Exception("API failed")):
                with pytest.raises(RetrievalError):
                    await reranker.rerank("query", sample_search_results)


# ============================================================================
# CohereConfig Tests
# ============================================================================


class TestCohereConfig:
    """Test suite for CohereConfig."""

    def test_default_config(self):
        """Test default Cohere configuration."""
        config = CohereConfig()

        assert config.api_key is None
        assert config.model == "rerank-english-v2.0"
        assert config.max_chunks_per_doc == 10
        assert config.return_documents is False
        assert config.top_n is None
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_custom_config(self):
        """Test custom Cohere configuration."""
        config = CohereConfig(
            api_key="custom-key",
            model="rerank-multilingual-v2.0",
            max_chunks_per_doc=5,
            return_documents=True,
            top_n=10,
            timeout_seconds=60,
            max_retries=5,
            retry_delay=2.0,
        )

        assert config.api_key == "custom-key"
        assert config.model == "rerank-multilingual-v2.0"
        assert config.max_chunks_per_doc == 5
        assert config.return_documents is True
        assert config.top_n == 10
        assert config.timeout_seconds == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0


# ============================================================================
# MockReRanker Tests
# ============================================================================


class TestMockReRanker:
    """Test suite for MockReRanker."""

    @pytest.mark.asyncio
    async def test_mock_reranker_initialization(self):
        """Test MockReRanker initialization."""
        reranker = MockReRanker()
        assert reranker._initialized is False

        await reranker.initialize()
        assert reranker._initialized is True

    @pytest.mark.asyncio
    async def test_mock_reranker_model_info(self):
        """Test MockReRanker model info."""
        reranker = MockReRanker()
        info = reranker.get_model_info()

        assert info["name"] == "MockReRanker"
        assert info["type"] == "rule-based"
        assert "version" in info

    @pytest.mark.asyncio
    async def test_mock_reranker_text_matching(self, sample_search_results):
        """Test that MockReRanker uses text matching for scoring."""
        reranker = MockReRanker()
        await reranker.initialize()

        # Query with words that appear in results
        query = "machine learning neural networks"
        result = await reranker.rerank(query, sample_search_results)

        # Results should be reordered based on text matching
        assert result.scores_changed is True

        await reranker.close()

    @pytest.mark.asyncio
    async def test_mock_reranker_close(self):
        """Test MockReRanker cleanup."""
        reranker = MockReRanker()
        await reranker.initialize()
        assert reranker._initialized is True

        await reranker.close()
        assert reranker._initialized is False
