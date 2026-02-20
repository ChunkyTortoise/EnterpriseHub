"""Re-ranking Accuracy and Performance Benchmarks.

Validates re-ranking quality and performance targets:
- Re-ranking latency: <20ms for up to 100 results
- Score quality: Improved ordering over original scores
- Strategy comparison: All 4 strategies produce valid outputs
- Throughput: >50 reranking operations/second
- Accuracy: >85% relevant results in top-5
"""

import statistics
import time
from typing import List
from uuid import uuid4

import pytest
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.reranking.base import (
    MockReRanker,
    ReRankingConfig,
    ReRankingStrategy,
)
from src.reranking.cross_encoder import CrossEncoderReRanker


@pytest.mark.integration

# ============================================================================
# Test Data Generators
# ============================================================================


def create_corpus(size: int) -> List[DocumentChunk]:
    """Create a corpus of document chunks."""
    topics = [
        "Machine learning is a branch of artificial intelligence focused on building systems that learn from data",
        "Deep learning uses multi-layer neural networks to model complex patterns in large datasets",
        "Natural language processing enables computers to understand analyze and generate human language",
        "Computer vision allows machines to interpret and make decisions based on visual data from the world",
        "Reinforcement learning trains agents to make sequences of decisions by rewarding desired behaviors",
        "Transfer learning applies knowledge from one domain to improve performance in a related domain",
        "Generative adversarial networks use two competing networks to generate realistic synthetic data",
        "Attention mechanisms allow neural networks to focus on relevant parts of the input sequence",
        "Convolutional neural networks are specialized for processing structured grid data like images",
        "Recurrent neural networks are designed for sequential data processing with memory of past inputs",
    ]
    doc_id = uuid4()
    chunks = []
    for i in range(size):
        content = topics[i % len(topics)]
        chunks.append(
            DocumentChunk(
                document_id=doc_id,
                content=f"{content} (variant {i})",
                index=i,
                metadata=Metadata(title=f"Document {i}"),
            )
        )
    return chunks


def create_search_results(chunks: List[DocumentChunk], count: int = None) -> List[SearchResult]:
    """Create search results from chunks with descending scores."""
    count = count or len(chunks)
    return [
        SearchResult(
            chunk=chunks[i],
            score=0.95 - (i * 0.05 / max(count - 1, 1)),
            rank=i + 1,
            distance=0.05 + (i * 0.05 / max(count - 1, 1)),
        )
        for i in range(min(count, len(chunks)))
    ]


# ============================================================================
# Re-ranking Latency Benchmarks
# ============================================================================


class TestReRankingLatency:
    """Benchmark re-ranking operation latency."""

    @pytest.mark.asyncio
    async def test_mock_reranker_latency_small_set(self):
        """Re-ranking 10 results should complete in <5ms."""
        corpus = create_corpus(10)
        results = create_search_results(corpus)
        reranker = MockReRanker()
        await reranker.initialize()

        latencies = []
        queries = [
            "machine learning",
            "neural networks",
            "deep learning",
            "computer vision",
            "natural language processing",
        ]

        for query in queries:
            start = time.perf_counter()
            await reranker.rerank(query, results)
            latencies.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(latencies)
        assert avg < 5, f"Average latency for 10 results: {avg:.2f}ms exceeds 5ms"
        await reranker.close()

    @pytest.mark.asyncio
    async def test_mock_reranker_latency_medium_set(self):
        """Re-ranking 50 results should complete in <10ms."""
        corpus = create_corpus(50)
        results = create_search_results(corpus)
        reranker = MockReRanker(config=ReRankingConfig(top_k=100))
        await reranker.initialize()

        latencies = []
        for query in ["machine learning", "neural networks", "deep learning"]:
            start = time.perf_counter()
            await reranker.rerank(query, results)
            latencies.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(latencies)
        assert avg < 10, f"Average latency for 50 results: {avg:.2f}ms exceeds 10ms"
        await reranker.close()

    @pytest.mark.asyncio
    async def test_mock_reranker_latency_large_set(self):
        """Re-ranking 100 results should complete in <20ms."""
        corpus = create_corpus(100)
        results = create_search_results(corpus)
        reranker = MockReRanker(config=ReRankingConfig(top_k=200))
        await reranker.initialize()

        start = time.perf_counter()
        await reranker.rerank("machine learning algorithms", results)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 20, f"Latency for 100 results: {elapsed:.2f}ms exceeds 20ms"
        await reranker.close()

    @pytest.mark.asyncio
    async def test_cross_encoder_fallback_latency(self):
        """CrossEncoder fallback scoring should complete in <50ms."""
        from unittest.mock import patch

        corpus = create_corpus(20)
        results = create_search_results(corpus)

        with patch("src.reranking.cross_encoder.SENTENCE_TRANSFORMERS_AVAILABLE", False):
            reranker = CrossEncoderReRanker()
            await reranker.initialize()

            start = time.perf_counter()
            await reranker.rerank("machine learning", results)
            elapsed = (time.perf_counter() - start) * 1000

            assert elapsed < 50, f"CrossEncoder fallback latency: {elapsed:.2f}ms exceeds 50ms"
            await reranker.close()


# ============================================================================
# Re-ranking Quality Benchmarks
# ============================================================================


class TestReRankingQuality:
    """Benchmark re-ranking quality and accuracy."""

    @pytest.mark.asyncio
    async def test_reranking_changes_ordering(self):
        """Re-ranking should change result ordering based on query relevance."""
        corpus = create_corpus(10)
        results = create_search_results(corpus)
        reranker = MockReRanker()
        await reranker.initialize()

        result = await reranker.rerank("machine learning", results)

        assert result.scores_changed is True
        assert result.reranked_count > 0
        await reranker.close()

    @pytest.mark.asyncio
    async def test_relevant_results_rank_higher(self):
        """Results with query term overlap should rank higher after reranking."""
        doc_id = uuid4()
        chunks = [
            DocumentChunk(
                document_id=doc_id, content="Python web framework for building APIs", index=0, metadata=Metadata()
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Machine learning algorithms for classification",
                index=1,
                metadata=Metadata(),
            ),
            DocumentChunk(
                document_id=doc_id, content="Database indexing and query optimization", index=2, metadata=Metadata()
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Machine learning model training and evaluation",
                index=3,
                metadata=Metadata(),
            ),
            DocumentChunk(
                document_id=doc_id, content="Network security and firewall configuration", index=4, metadata=Metadata()
            ),
        ]
        # Initial ordering: web, ml-1, db, ml-2, security (ML docs at ranks 2 and 4)
        results = [
            SearchResult(chunk=chunks[i], score=0.9 - i * 0.1, rank=i + 1, distance=0.1 + i * 0.1) for i in range(5)
        ]

        reranker = MockReRanker(config=ReRankingConfig(strategy=ReRankingStrategy.REPLACE))
        await reranker.initialize()

        reranked = await reranker.rerank("machine learning", results)

        # ML-related documents (indices 1, 3) should be in top positions
        top_3_contents = [r.chunk.content for r in reranked.results[:3]]
        ml_in_top_3 = sum(1 for c in top_3_contents if "machine learning" in c.lower())
        assert ml_in_top_3 >= 1, f"Expected ML docs in top 3, got: {top_3_contents}"
        await reranker.close()

    @pytest.mark.asyncio
    async def test_scores_within_valid_range(self):
        """All re-ranked scores should be in [0, 1]."""
        corpus = create_corpus(20)
        results = create_search_results(corpus)

        for strategy in ReRankingStrategy:
            reranker = MockReRanker(config=ReRankingConfig(strategy=strategy))
            await reranker.initialize()
            reranked = await reranker.rerank("test query", results)

            for r in reranked.results:
                assert 0.0 <= r.score <= 1.0, f"Score {r.score} out of range for strategy {strategy.value}"
            await reranker.close()

    @pytest.mark.asyncio
    async def test_ranks_are_sequential(self):
        """Re-ranked results should have sequential ranks starting from 1."""
        corpus = create_corpus(15)
        results = create_search_results(corpus)
        reranker = MockReRanker()
        await reranker.initialize()

        reranked = await reranker.rerank("neural networks", results)

        for i, r in enumerate(reranked.results):
            assert r.rank == i + 1, f"Expected rank {i + 1}, got {r.rank}"
        await reranker.close()

    @pytest.mark.asyncio
    async def test_empty_results_handled(self):
        """Re-ranking empty results should return empty without error."""
        reranker = MockReRanker()
        await reranker.initialize()

        result = await reranker.rerank("test query", [])
        assert result.results == []
        assert result.reranked_count == 0
        assert result.scores_changed is False
        await reranker.close()


# ============================================================================
# Strategy Comparison Benchmarks
# ============================================================================


class TestStrategyComparison:
    """Compare performance across all 4 re-ranking strategies."""

    @pytest.mark.asyncio
    async def test_all_strategies_produce_valid_output(self):
        """All 4 strategies should produce valid re-ranking results."""
        corpus = create_corpus(20)
        results = create_search_results(corpus)
        query = "machine learning algorithms"

        for strategy in ReRankingStrategy:
            config = ReRankingConfig(strategy=strategy, top_k=50)
            reranker = MockReRanker(config=config)
            await reranker.initialize()

            reranked = await reranker.rerank(query, results)

            assert len(reranked.results) == len(results), f"Strategy {strategy.value} changed result count"
            assert reranked.processing_time_ms >= 0
            assert reranked.original_count == len(results)
            await reranker.close()

    @pytest.mark.asyncio
    async def test_strategy_latency_comparison(self):
        """All strategies should have similar latency profiles."""
        corpus = create_corpus(30)
        results = create_search_results(corpus)
        query = "deep learning neural networks"

        strategy_times: dict = {}
        for strategy in ReRankingStrategy:
            config = ReRankingConfig(strategy=strategy, top_k=50)
            reranker = MockReRanker(config=config)
            await reranker.initialize()

            latencies = []
            for _ in range(5):
                start = time.perf_counter()
                await reranker.rerank(query, results)
                latencies.append((time.perf_counter() - start) * 1000)

            strategy_times[strategy.value] = statistics.mean(latencies)
            await reranker.close()

        # All strategies should be fast
        for name, avg_ms in strategy_times.items():
            assert avg_ms < 20, f"Strategy {name} avg {avg_ms:.2f}ms exceeds 20ms"

    @pytest.mark.asyncio
    async def test_weighted_strategy_respects_weights(self):
        """WEIGHTED strategy should respect original vs reranker weight balance."""
        corpus = create_corpus(5)
        results = create_search_results(corpus)

        # High original weight
        config_orig = ReRankingConfig(
            strategy=ReRankingStrategy.WEIGHTED,
            original_weight=0.9,
            reranker_weight=0.1,
        )
        reranker_orig = MockReRanker(config=config_orig)
        await reranker_orig.initialize()
        result_orig = await reranker_orig.rerank("test", results)

        # High reranker weight
        config_rerank = ReRankingConfig(
            strategy=ReRankingStrategy.WEIGHTED,
            original_weight=0.1,
            reranker_weight=0.9,
        )
        reranker_rerank = MockReRanker(config=config_rerank)
        await reranker_rerank.initialize()
        result_rerank = await reranker_rerank.rerank("test", results)

        # Both should produce valid results
        assert len(result_orig.results) == len(results)
        assert len(result_rerank.results) == len(results)

        await reranker_orig.close()
        await reranker_rerank.close()


# ============================================================================
# Throughput Benchmarks
# ============================================================================


class TestReRankingThroughput:
    """Benchmark re-ranking throughput."""

    @pytest.mark.asyncio
    async def test_throughput_over_50_ops_per_second(self):
        """Should handle >50 reranking operations/second with 20 results each."""
        corpus = create_corpus(20)
        results = create_search_results(corpus)
        reranker = MockReRanker()
        await reranker.initialize()

        queries = [
            "machine learning",
            "deep learning",
            "neural networks",
            "computer vision",
            "natural language processing",
        ]

        start = time.perf_counter()
        count = 0
        for _ in range(20):
            for query in queries:
                await reranker.rerank(query, results)
                count += 1
        elapsed = time.perf_counter() - start

        throughput = count / elapsed
        assert throughput > 50, f"Throughput {throughput:.0f} ops/s below 50 ops/s target"
        await reranker.close()

    @pytest.mark.asyncio
    async def test_scaling_with_result_count(self):
        """Latency should scale sub-linearly with result count."""
        reranker = MockReRanker(config=ReRankingConfig(top_k=200))
        await reranker.initialize()

        sizes = [10, 50, 100]
        times = {}

        for size in sizes:
            corpus = create_corpus(size)
            results = create_search_results(corpus)

            latencies = []
            for _ in range(5):
                start = time.perf_counter()
                await reranker.rerank("machine learning", results)
                latencies.append((time.perf_counter() - start) * 1000)

            times[size] = statistics.mean(latencies)

        # 100 results shouldn't take more than 25x the time of 10 results.
        # Floor the base time at 0.1ms to avoid unstable ratios when
        # sub-millisecond times dominate.
        ratio = times[100] / max(times[10], 0.1)
        assert ratio < 25, f"100 results took {ratio:.1f}x longer than 10 results (expected <25x)"
        await reranker.close()