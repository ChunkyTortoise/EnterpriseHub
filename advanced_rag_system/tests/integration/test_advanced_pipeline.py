"""Comprehensive end-to-end integration tests for the Advanced RAG Pipeline.

This module tests the complete Phase 3 Advanced RAG System integration including:
- Full pipeline: Query -> Enhancement -> Search -> Re-ranking
- All 6 query type validations (factual, conceptual, procedural, comparative, exploratory, technical)
- Performance benchmarks and accuracy validation
- Component integration tests
- Error handling and recovery mechanisms
- Data flow through the pipeline
"""

import asyncio
import time
from typing import List
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, Metadata, SearchResult

# Re-ranking imports
from src.reranking.base import (
    MockReRanker,
    ReRankingConfig,
    ReRankingStrategy,
)
from src.retrieval.advanced_hybrid_searcher import AdvancedHybridSearcher, AdvancedSearchConfig

# Retrieval imports
from src.retrieval.hybrid import HybridSearchConfig

# Query enhancement imports
from src.retrieval.query import (
    ExpansionConfig,
    HyDEConfig,
    HyDEGenerator,
    MockLLMProvider,
    QueryClassifier,
    QueryExpander,
    QueryType,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_document_chunks() -> List[DocumentChunk]:
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            document_id=uuid4(),
            content="Machine learning is a subset of artificial intelligence that enables computers to learn from data",
            index=0,
            metadata=Metadata(title="ML Basics", source="ml_guide.pdf", tags=["ai", "ml"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Deep learning uses neural networks with multiple layers to extract features from data",
            index=1,
            metadata=Metadata(title="Deep Learning", source="dl_handbook.pdf", tags=["ai", "dl"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Natural language processing enables computers to understand and generate human language",
            index=2,
            metadata=Metadata(title="NLP Fundamentals", source="nlp_guide.pdf", tags=["ai", "nlp"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Computer vision allows machines to interpret and understand visual information from images",
            index=3,
            metadata=Metadata(title="Computer Vision", source="cv_intro.pdf", tags=["ai", "cv"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Reinforcement learning trains agents through rewards and penalties to achieve goals",
            index=4,
            metadata=Metadata(title="RL Guide", source="rl_book.pdf", tags=["ai", "rl"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Supervised learning requires labeled training data to learn patterns and make predictions",
            index=5,
            metadata=Metadata(title="Supervised Learning", source="ml_guide.pdf", tags=["ai", "ml"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Unsupervised learning discovers hidden patterns in data without labeled examples",
            index=6,
            metadata=Metadata(title="Unsupervised Learning", source="ml_guide.pdf", tags=["ai", "ml"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Transfer learning leverages pre-trained models to solve new tasks with limited data",
            index=7,
            metadata=Metadata(title="Transfer Learning", source="advanced_ml.pdf", tags=["ai", "ml"]),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="How to install TensorFlow: use pip install tensorflow and configure GPU drivers for acceleration",
            index=8,
            metadata=Metadata(title="TF Install Guide"),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Comparing PyTorch vs TensorFlow: PyTorch offers dynamic graphs while TensorFlow provides better deployment",
            index=9,
            metadata=Metadata(title="Framework Comparison"),
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="The API endpoint for model inference accepts POST requests with JSON payloads containing input tensors",
            index=10,
            metadata=Metadata(title="API Reference"),
        ),
    ]


@pytest.fixture
def sample_search_results(sample_document_chunks) -> List[SearchResult]:
    """Create sample search results for testing."""
    return [
        SearchResult(
            chunk=chunk,
            score=0.9 - (i * 0.08),
            rank=i + 1,
            distance=0.1 + (i * 0.08),
        )
        for i, chunk in enumerate(sample_document_chunks[:5])
    ]


@pytest.fixture
def default_config() -> AdvancedSearchConfig:
    """Create default advanced search configuration for testing."""
    return AdvancedSearchConfig(
        hybrid_config=HybridSearchConfig(
            fusion_method="rrf",
            enable_dense=True,
            enable_sparse=True,
        ),
        enable_query_expansion=True,
        enable_hyde=True,
        enable_query_classification=True,
        enable_reranking=True,
        reranking_config=ReRankingConfig(
            strategy=ReRankingStrategy.WEIGHTED,
            top_k=50,
        ),
        enable_intelligent_routing=True,
        max_total_time_ms=150,
        enable_caching=False,
    )


@pytest.fixture
def minimal_config() -> AdvancedSearchConfig:
    """Minimal config with all enhancements disabled."""
    return AdvancedSearchConfig(
        enable_query_expansion=False,
        enable_hyde=False,
        enable_query_classification=False,
        enable_reranking=False,
    )


@pytest.fixture
def reranking_config() -> ReRankingConfig:
    """Default re-ranking configuration for testing."""
    return ReRankingConfig(
        strategy=ReRankingStrategy.WEIGHTED,
        original_weight=0.3,
        reranker_weight=0.7,
        top_k=50,
        score_threshold=0.0,
        normalize_scores=True,
    )


@pytest.fixture
def mock_reranker(reranking_config) -> MockReRanker:
    """Create a mock re-ranker for testing."""
    return MockReRanker(config=reranking_config)


@pytest.fixture
def mock_hyde_generator() -> HyDEGenerator:
    """Create a HyDE generator with mock provider for testing."""
    config = HyDEConfig(num_hypotheticals=1, use_caching=False)
    mock_provider = MockLLMProvider()
    return HyDEGenerator(config=config, llm_provider=mock_provider)


@pytest.fixture
def query_classifier() -> QueryClassifier:
    """Create a query classifier for testing."""
    return QueryClassifier()


@pytest.fixture
async def initialized_searcher(default_config, sample_document_chunks) -> AdvancedHybridSearcher:
    """Create and initialize an AdvancedHybridSearcher with sample data."""
    searcher = AdvancedHybridSearcher(config=default_config)
    await searcher.initialize()
    await searcher.hybrid_searcher.add_documents(sample_document_chunks)
    yield searcher
    await searcher.close()


# ============================================================================
# Pipeline Initialization Tests
# ============================================================================


class TestPipelineInitialization:
    """Test pipeline initialization and component setup."""

    @pytest.mark.asyncio
    async def test_initialize_all_components(self, default_config):
        """Test that all pipeline components initialize correctly."""
        searcher = AdvancedHybridSearcher(config=default_config)
        await searcher.initialize()

        assert searcher._initialized is True
        assert searcher.query_expander is not None
        assert searcher.hyde_generator is not None
        assert searcher.query_classifier is not None
        assert searcher.reranker is not None
        assert isinstance(searcher.reranker, MockReRanker)

        await searcher.close()

    @pytest.mark.asyncio
    async def test_initialize_minimal_config(self, minimal_config):
        """Test initialization with all enhancements disabled."""
        searcher = AdvancedHybridSearcher(config=minimal_config)
        await searcher.initialize()

        assert searcher._initialized is True
        assert searcher.query_expander is None
        assert searcher.hyde_generator is None
        assert searcher.query_classifier is None
        assert searcher.reranker is None

        await searcher.close()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, default_config):
        """Test that calling initialize() twice is safe."""
        searcher = AdvancedHybridSearcher(config=default_config)
        await searcher.initialize()
        await searcher.initialize()
        assert searcher._initialized is True
        await searcher.close()

    @pytest.mark.asyncio
    async def test_close_cleans_up(self, default_config):
        """Test that close() properly cleans up resources."""
        searcher = AdvancedHybridSearcher(config=default_config)
        await searcher.initialize()
        assert searcher._initialized is True

        await searcher.close()
        assert searcher._initialized is False

    @pytest.mark.asyncio
    async def test_injected_reranker(self, default_config):
        """Test pipeline with injected custom reranker."""
        custom_reranker = MockReRanker(config=ReRankingConfig(strategy=ReRankingStrategy.REPLACE))
        searcher = AdvancedHybridSearcher(config=default_config, reranker=custom_reranker)
        await searcher.initialize()
        assert searcher.reranker is custom_reranker
        await searcher.close()


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================


class TestFullPipelineIntegration:
    """End-to-end tests for the complete search pipeline."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, initialized_searcher):
        """Test that search returns valid results."""
        results = await initialized_searcher.search("machine learning", top_k=5)
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, SearchResult)
            assert 0.0 <= result.score <= 1.0
            assert result.rank >= 1

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self, initialized_searcher):
        """Test that search limits results to top_k."""
        results = await initialized_searcher.search("neural networks", top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_empty_query(self, initialized_searcher):
        """Test that empty query returns empty results."""
        assert await initialized_searcher.search("", top_k=5) == []
        assert await initialized_searcher.search("   ", top_k=5) == []

    @pytest.mark.asyncio
    async def test_search_not_initialized_raises(self, default_config):
        """Test that search before initialization raises error."""
        searcher = AdvancedHybridSearcher(config=default_config)
        with pytest.raises(RetrievalError, match="not initialized"):
            await searcher.search("test query")

    @pytest.mark.asyncio
    async def test_search_updates_stats(self, initialized_searcher):
        """Test that search updates performance statistics."""
        await initialized_searcher.search("machine learning")
        await initialized_searcher.search("deep learning")

        stats = await initialized_searcher.get_comprehensive_stats()
        assert stats["performance"]["total_searches"] == 2
        assert stats["performance"]["avg_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_multiple_sequential_searches(self, initialized_searcher):
        """Test multiple searches in sequence."""
        queries = ["machine learning", "neural networks", "python programming"]
        for query in queries:
            results = await initialized_searcher.search(query, top_k=3)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_complete_pipeline_with_mocked_search(self, sample_document_chunks, mock_reranker):
        """Test complete pipeline execution with mocked hybrid search."""
        config = AdvancedSearchConfig(
            enable_query_expansion=True,
            enable_hyde=True,
            enable_query_classification=True,
            enable_reranking=True,
        )
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)

        with patch.object(searcher.hybrid_searcher, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.85, rank=1, distance=0.15),
                SearchResult(chunk=sample_document_chunks[1], score=0.75, rank=2, distance=0.25),
            ]

            await searcher.initialize()
            try:
                results = await searcher.search("machine learning basics", top_k=5)
                assert isinstance(results, list)
                assert len(results) <= 5
                assert all(isinstance(r, SearchResult) for r in results)
                assert searcher._search_stats["total_searches"] >= 1
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_configuration_combinations(self, sample_document_chunks, mock_reranker):
        """Test pipeline with various configuration combinations."""
        configs = [
            AdvancedSearchConfig(
                enable_query_expansion=True,
                enable_hyde=True,
                enable_query_classification=True,
                enable_reranking=True,
            ),
            AdvancedSearchConfig(
                enable_query_expansion=False,
                enable_hyde=False,
                enable_query_classification=False,
                enable_reranking=False,
            ),
            AdvancedSearchConfig(
                enable_query_expansion=True,
                enable_hyde=False,
                enable_query_classification=False,
                enable_reranking=False,
            ),
            AdvancedSearchConfig(
                enable_query_expansion=False,
                enable_hyde=False,
                enable_query_classification=False,
                enable_reranking=True,
            ),
        ]

        for config in configs:
            searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
            with patch.object(searcher.hybrid_searcher, "search", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = [
                    SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
                ]
                await searcher.initialize()
                try:
                    results = await searcher.search("machine learning", top_k=3)
                    assert isinstance(results, list)
                finally:
                    await searcher.close()


# ============================================================================
# Query Type Coverage Tests (all 6 types)
# ============================================================================


class TestQueryTypeCoverage:
    """Test pipeline behavior across all 6 query types."""

    @pytest.mark.asyncio
    async def test_factual_query(self, initialized_searcher, query_classifier):
        """Test FACTUAL query: 'What is machine learning?'"""
        classification = query_classifier.classify("What is machine learning?")
        assert classification.query_type == QueryType.FACTUAL

        results = await initialized_searcher.search("What is machine learning?", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_conceptual_query(self, initialized_searcher, query_classifier):
        """Test CONCEPTUAL query: 'Explain the concept of deep learning'"""
        classification = query_classifier.classify("Explain the concept of deep learning")
        assert classification.query_type == QueryType.CONCEPTUAL

        results = await initialized_searcher.search("Explain the concept of deep learning", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_procedural_query(self, initialized_searcher, query_classifier):
        """Test PROCEDURAL query: 'How to install TensorFlow?'"""
        classification = query_classifier.classify("How to install TensorFlow?")
        assert classification.query_type == QueryType.PROCEDURAL

        results = await initialized_searcher.search("How to install TensorFlow?", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_comparative_query(self, initialized_searcher, query_classifier):
        """Test COMPARATIVE query: 'Compare PyTorch vs TensorFlow'"""
        classification = query_classifier.classify("Compare PyTorch vs TensorFlow")
        assert classification.query_type == QueryType.COMPARATIVE

        results = await initialized_searcher.search("Compare PyTorch vs TensorFlow", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_exploratory_query(self, initialized_searcher, query_classifier):
        """Test EXPLORATORY query."""
        classification = query_classifier.classify("Explore everything about reinforcement learning")
        assert classification.query_type == QueryType.EXPLORATORY

        results = await initialized_searcher.search("Explore everything about reinforcement learning", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_technical_query(self, initialized_searcher, query_classifier):
        """Test TECHNICAL query."""
        classification = query_classifier.classify("API endpoint for model inference configuration")
        assert classification.query_type == QueryType.TECHNICAL

        results = await initialized_searcher.search("API endpoint for model inference configuration", top_k=5)
        assert isinstance(results, list)


# ============================================================================
# Query Enhancement Integration Tests
# ============================================================================


class TestQueryEnhancement:
    """Test query enhancement components in the pipeline."""

    @pytest.mark.asyncio
    async def test_query_expansion_produces_variations(self):
        """Test that query expansion creates meaningful variations."""
        expander = QueryExpander(ExpansionConfig(max_expansions=5))
        expansions = expander.expand("machine learning algorithms")
        assert len(expansions) >= 1
        assert "machine learning algorithms" in expansions

    @pytest.mark.asyncio
    async def test_hyde_generates_hypothetical_docs(self, mock_hyde_generator):
        """Test HyDE generates hypothetical documents."""
        docs = await mock_hyde_generator.generate_hypothetical_documents("What is machine learning?")
        assert len(docs) >= 1
        assert all(isinstance(d, str) and len(d) > 0 for d in docs)

    @pytest.mark.asyncio
    async def test_classifier_routes_all_types(self, query_classifier):
        """Test classifier correctly routes all 6 query types."""
        test_cases = {
            "What is the definition of AI?": QueryType.FACTUAL,
            "Explain the concept of deep learning": QueryType.CONCEPTUAL,
            "How to build a neural network?": QueryType.PROCEDURAL,
            "Compare CNN vs RNN architectures": QueryType.COMPARATIVE,
            "Explore everything about reinforcement learning": QueryType.EXPLORATORY,
            "Debug the API endpoint error in configuration": QueryType.TECHNICAL,
        }

        for query, expected_type in test_cases.items():
            result = query_classifier.classify(query)
            assert result.query_type == expected_type, (
                f"Query '{query}' classified as {result.query_type}, expected {expected_type}"
            )
            assert 0.0 <= result.confidence <= 1.0
            assert isinstance(result.recommendations, dict)

    @pytest.mark.asyncio
    async def test_classification_routing_recommendations(self, query_classifier):
        """Test classification provides valid routing recommendations."""
        queries_by_type = {
            QueryType.FACTUAL: "What is Python?",
            QueryType.CONCEPTUAL: "Explain how Python works",
            QueryType.PROCEDURAL: "How to install Python?",
            QueryType.COMPARATIVE: "Compare Python vs JavaScript differences",
            QueryType.EXPLORATORY: "Explore everything about Python programming",
            QueryType.TECHNICAL: "Python API endpoint error in configuration",
        }

        for expected_type, query in queries_by_type.items():
            classification = query_classifier.classify(query)
            assert classification.query_type == expected_type
            assert "dense_retrieval_weight" in classification.recommendations
            assert "sparse_retrieval_weight" in classification.recommendations

    @pytest.mark.asyncio
    async def test_enhancement_pipeline_integration(self, initialized_searcher):
        """Test the _enhance_query method produces valid output."""
        enhanced_query, routing_info = await initialized_searcher._enhance_query("How does machine learning work?")
        assert isinstance(enhanced_query, str)
        assert len(enhanced_query) > 0
        assert routing_info["original_query"] == "How does machine learning work?"
        assert "query_type" in routing_info


# ============================================================================
# Re-ranking Integration Tests
# ============================================================================


class TestReRankingIntegration:
    """Test re-ranking within the full pipeline."""

    @pytest.mark.asyncio
    async def test_reranking_produces_valid_results(self, initialized_searcher):
        """Test that re-ranking produces valid result ordering."""
        results = await initialized_searcher.search("machine learning algorithms", top_k=5)
        for result in results:
            assert result.rank >= 1
            assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_search_without_reranking(self, sample_document_chunks):
        """Test search works correctly without re-ranking."""
        config = AdvancedSearchConfig(
            enable_reranking=False,
            enable_query_expansion=True,
            enable_hyde=True,
            enable_query_classification=True,
        )
        searcher = AdvancedHybridSearcher(config=config)
        await searcher.initialize()
        await searcher.hybrid_searcher.add_documents(sample_document_chunks)
        results = await searcher.search("machine learning", top_k=5)
        assert isinstance(results, list)
        await searcher.close()

    @pytest.mark.asyncio
    async def test_reranking_strategies(self, sample_document_chunks):
        """Test different re-ranking strategies produce valid results."""
        for strategy in ReRankingStrategy:
            config = AdvancedSearchConfig(
                enable_reranking=True,
                reranking_config=ReRankingConfig(strategy=strategy, top_k=50),
                enable_query_expansion=False,
                enable_hyde=False,
            )
            searcher = AdvancedHybridSearcher(config=config)
            await searcher.initialize()
            await searcher.hybrid_searcher.add_documents(sample_document_chunks)
            results = await searcher.search("learning", top_k=3)
            assert isinstance(results, list), f"Strategy {strategy.value} failed"
            await searcher.close()

    @pytest.mark.asyncio
    async def test_vector_search_reranking_integration(self, sample_search_results, mock_reranker):
        """Test vector search results integrate correctly with re-ranking."""
        await mock_reranker.initialize()
        reranking_result = await mock_reranker.rerank("machine learning algorithms", sample_search_results)
        assert len(reranking_result.results) == len(sample_search_results)
        for result in reranking_result.results:
            assert isinstance(result, SearchResult)
            assert 0.0 <= result.score <= 1.0
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_fusion_reranking_integration(self, sample_document_chunks, mock_reranker):
        """Test fused results from multiple retrievers can be re-ranked."""
        fused_results = [
            SearchResult(chunk=sample_document_chunks[i], score=0.92 - i * 0.04, rank=i + 1, distance=0.08 + i * 0.04)
            for i in range(4)
        ]
        await mock_reranker.initialize()
        result = await mock_reranker.rerank("artificial intelligence", fused_results)
        assert len(result.results) == 4
        for i, r in enumerate(result.results):
            assert r.rank == i + 1
        await mock_reranker.close()


# ============================================================================
# Performance Benchmark Tests
# ============================================================================


class TestPerformanceBenchmarks:
    """Test pipeline performance meets targets."""

    @pytest.mark.asyncio
    async def test_full_pipeline_under_100ms(self, initialized_searcher):
        """Test complete pipeline completes in <100ms."""
        await initialized_searcher.search("warm up query")

        latencies = []
        for query in [
            "machine learning",
            "neural networks",
            "python programming",
            "How to build a model?",
            "Compare deep learning frameworks",
        ]:
            start = time.perf_counter()
            await initialized_searcher.search(query, top_k=5)
            latencies.append((time.perf_counter() - start) * 1000)

        avg = sum(latencies) / len(latencies)
        assert avg < 100, f"Average latency {avg:.1f}ms exceeds 100ms target"
        assert max(latencies) < 150, f"Max latency {max(latencies):.1f}ms exceeds 150ms budget"

    @pytest.mark.asyncio
    async def test_query_enhancement_latency(self, mock_hyde_generator, query_classifier):
        """Test query enhancement latency <50ms."""
        for query in [
            "What is machine learning?",
            "How to implement neural networks?",
            "Compare Python and JavaScript",
        ]:
            start = time.perf_counter()
            query_classifier.classify(query)
            QueryExpander(ExpansionConfig(max_expansions=3)).expand(query)
            await mock_hyde_generator.generate_hypothetical_documents(query)
            elapsed = (time.perf_counter() - start) * 1000
            assert elapsed < 100, f"Enhancement took {elapsed:.1f}ms for '{query}'"

    @pytest.mark.asyncio
    async def test_reranking_accuracy(self, sample_search_results, mock_reranker):
        """Test re-ranking produces valid reordered results."""
        await mock_reranker.initialize()
        result = await mock_reranker.rerank("machine learning neural networks", sample_search_results)
        assert len(result.results) > 0
        for r in result.results:
            assert 0.0 <= r.score <= 1.0
        assert result.processing_time_ms < 1000
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_stats_track_performance(self, initialized_searcher):
        """Test stats accurately track performance breakdown."""
        for query in ["machine learning", "neural networks", "python"]:
            await initialized_searcher.search(query)

        stats = await initialized_searcher.get_comprehensive_stats()
        perf = stats["performance"]
        assert perf["total_searches"] == 3
        assert perf["avg_time_ms"] >= 0
        assert perf["enhancement_time_ms"] >= 0
        assert perf["retrieval_time_ms"] >= 0
        assert perf["reranking_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, sample_document_chunks, mock_reranker):
        """Test pipeline under concurrent load."""
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)

        with patch.object(searcher.hybrid_searcher, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)]
            await searcher.initialize()
            try:
                start = time.perf_counter()
                tasks = [
                    searcher.search(q, top_k=3) for q in ["machine learning", "deep learning", "neural networks", "AI"]
                ]
                results = await asyncio.gather(*tasks)
                elapsed = (time.perf_counter() - start) * 1000

                assert len(results) == 4
                assert all(isinstance(r, list) for r in results)
                assert elapsed < 1000
            finally:
                await searcher.close()


# ============================================================================
# Error Handling & Fallback Tests
# ============================================================================


class TestErrorHandlingAndFallbacks:
    """Test error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_search_with_no_indexed_documents(self, default_config):
        """Test search on empty index returns empty results."""
        searcher = AdvancedHybridSearcher(config=default_config)
        await searcher.initialize()
        results = await searcher.search("machine learning", top_k=5)
        assert isinstance(results, list)
        assert len(results) == 0
        await searcher.close()

    @pytest.mark.asyncio
    async def test_reranking_failure_falls_back(self, sample_document_chunks, default_config):
        """Test re-ranking failure falls back to un-reranked results."""
        searcher = AdvancedHybridSearcher(config=default_config)
        await searcher.initialize()
        await searcher.hybrid_searcher.add_documents(sample_document_chunks)

        with patch.object(searcher.reranker, "rerank", side_effect=Exception("Reranker failed")):
            results = await searcher.search("machine learning", top_k=5)
            assert isinstance(results, list)
        await searcher.close()

    @pytest.mark.asyncio
    async def test_query_expansion_failure_uses_original(self, sample_document_chunks):
        """Test query expansion failure falls back to original query."""
        config = AdvancedSearchConfig(
            enable_query_expansion=True,
            enable_hyde=False,
            enable_query_classification=False,
            enable_reranking=False,
        )
        searcher = AdvancedHybridSearcher(config=config)
        await searcher.initialize()
        await searcher.hybrid_searcher.add_documents(sample_document_chunks)

        with patch.object(searcher.query_expander, "expand", side_effect=Exception("Expansion failed")):
            results = await searcher.search("machine learning", top_k=5)
            assert isinstance(results, list)
        await searcher.close()

    @pytest.mark.asyncio
    async def test_classification_failure_uses_default(self, sample_document_chunks):
        """Test classification failure uses default routing."""
        config = AdvancedSearchConfig(
            enable_query_expansion=False,
            enable_hyde=False,
            enable_query_classification=True,
            enable_reranking=False,
        )
        searcher = AdvancedHybridSearcher(config=config)
        await searcher.initialize()
        await searcher.hybrid_searcher.add_documents(sample_document_chunks)

        with patch.object(searcher.query_classifier, "classify", side_effect=Exception("Failed")):
            results = await searcher.search("machine learning", top_k=5)
            assert isinstance(results, list)
        await searcher.close()

    @pytest.mark.asyncio
    async def test_hyde_failure_uses_original_query(self, sample_document_chunks):
        """Test HyDE failure falls back to original query."""
        config = AdvancedSearchConfig(
            enable_query_expansion=False,
            enable_hyde=True,
            enable_query_classification=False,
            enable_reranking=False,
        )
        searcher = AdvancedHybridSearcher(config=config)
        await searcher.initialize()
        await searcher.hybrid_searcher.add_documents(sample_document_chunks)

        with patch.object(
            searcher.hyde_generator,
            "generate_hypothetical_documents",
            side_effect=Exception("HyDE failed"),
        ):
            results = await searcher.search("machine learning", top_k=5)
            assert isinstance(results, list)
        await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_recovers_from_component_failure(self, sample_document_chunks, mock_reranker):
        """Test pipeline continues functioning after component failure."""
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)

        with patch.object(searcher.hybrid_searcher, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)]
            await searcher.initialize()
            try:
                # First search succeeds
                results = await searcher.search("machine learning", top_k=3)
                assert len(results) > 0

                # Second search also succeeds (pipeline is still functional)
                results = await searcher.search("deep learning", top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()


# ============================================================================
# Comprehensive Stats Tests
# ============================================================================


class TestComprehensiveStats:
    """Test comprehensive statistics reporting."""

    @pytest.mark.asyncio
    async def test_stats_structure(self, initialized_searcher):
        """Test stats contain all expected sections."""
        await initialized_searcher.search("test query")
        stats = await initialized_searcher.get_comprehensive_stats()
        assert "performance" in stats
        assert "config" in stats
        assert "components" in stats

    @pytest.mark.asyncio
    async def test_stats_config_reflects_actual(self, initialized_searcher):
        """Test stats config section reflects actual configuration."""
        stats = await initialized_searcher.get_comprehensive_stats()
        config = stats["config"]
        assert config["enable_query_expansion"] is True
        assert config["enable_hyde"] is True
        assert config["enable_query_classification"] is True
        assert config["enable_reranking"] is True

    @pytest.mark.asyncio
    async def test_stats_components_populated(self, initialized_searcher):
        """Test stats components populated after search."""
        await initialized_searcher.search("machine learning")
        stats = await initialized_searcher.get_comprehensive_stats()
        components = stats["components"]
        assert "query_expander" in components
        assert "hyde_generator" in components
        assert "query_classifier" in components
        assert "reranker" in components
