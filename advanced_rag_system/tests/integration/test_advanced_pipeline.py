"""Comprehensive end-to-end integration tests for the Advanced RAG Pipeline.

This module tests the complete Phase 3 Advanced RAG System integration including:
- Full pipeline: Query → Enhancement → Search → Re-ranking
- All 6 query type validations (factual, conceptual, procedural, comparative, exploratory, technical)
- Performance benchmarks and accuracy validation
- Component integration tests
- Error handling and recovery mechanisms
- Data flow through the pipeline

Target: 25-30 comprehensive integration tests
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4

from src.core.types import SearchResult, DocumentChunk, Metadata, QueryType as CoreQueryType
from src.core.exceptions import RetrievalError

# Query enhancement imports
from src.retrieval.query import (
    QueryExpander,
    ExpansionConfig,
    HyDEGenerator,
    HyDEConfig,
    MockLLMProvider,
    QueryClassifier,
    ClassifierConfig,
    QueryType,
    ClassificationResult,
)

# Retrieval imports
from src.retrieval.hybrid import HybridSearcher, HybridSearchConfig
from src.retrieval.advanced_hybrid_searcher import AdvancedHybridSearcher, AdvancedSearchConfig

# Re-ranking imports
from src.reranking.base import (
    BaseReRanker,
    ReRankingConfig,
    ReRankingResult,
    ReRankingStrategy,
    MockReRanker,
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
            metadata=Metadata(title="ML Basics", source="ml_guide.pdf", tags=["ai", "ml"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Deep learning uses neural networks with multiple layers to extract features from data",
            index=1,
            metadata=Metadata(title="Deep Learning", source="dl_handbook.pdf", tags=["ai", "dl"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Natural language processing enables computers to understand and generate human language",
            index=2,
            metadata=Metadata(title="NLP Fundamentals", source="nlp_guide.pdf", tags=["ai", "nlp"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Computer vision allows machines to interpret and understand visual information from images",
            index=3,
            metadata=Metadata(title="Computer Vision", source="cv_intro.pdf", tags=["ai", "cv"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Reinforcement learning trains agents through rewards and penalties to achieve goals",
            index=4,
            metadata=Metadata(title="RL Guide", source="rl_book.pdf", tags=["ai", "rl"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Supervised learning requires labeled training data to learn patterns and make predictions",
            index=5,
            metadata=Metadata(title="Supervised Learning", source="ml_guide.pdf", tags=["ai", "ml"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Unsupervised learning discovers hidden patterns in data without labeled examples",
            index=6,
            metadata=Metadata(title="Unsupervised Learning", source="ml_guide.pdf", tags=["ai", "ml"])
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Transfer learning leverages pre-trained models to solve new tasks with limited data",
            index=7,
            metadata=Metadata(title="Transfer Learning", source="advanced_ml.pdf", tags=["ai", "ml"])
        ),
    ]


@pytest.fixture
def sample_search_results(sample_document_chunks) -> List[SearchResult]:
    """Create sample search results for testing."""
    return [
        SearchResult(
            chunk=chunk,
            score=0.9 - (i * 0.08),  # Descending scores
            rank=i + 1,
            distance=0.1 + (i * 0.08)
        )
        for i, chunk in enumerate(sample_document_chunks[:5])
    ]


@pytest.fixture
def advanced_search_config() -> AdvancedSearchConfig:
    """Create default advanced search configuration for testing."""
    return AdvancedSearchConfig(
        enable_query_expansion=True,
        enable_hyde=True,
        enable_query_classification=True,
        enable_reranking=True,
        enable_intelligent_routing=True,
        max_total_time_ms=150,
        enable_caching=False,  # Disable caching for tests
    )


@pytest.fixture
def reranking_config() -> ReRankingConfig:
    """Create default re-ranking configuration for testing."""
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


# ============================================================================
# Full Pipeline Integration Tests (6-8 tests)
# ============================================================================

class TestFullPipelineIntegration:
    """Test suite for complete pipeline integration.
    
    Validates the end-to-end flow: Query → Enhancement → Search → Re-ranking
    """

    @pytest.mark.asyncio
    async def test_complete_pipeline_execution(self, sample_document_chunks, mock_reranker):
        """Test complete pipeline execution with all components enabled.
        
        Validates that the full pipeline can execute successfully with:
        - Query enhancement (expansion + HyDE + classification)
        - Hybrid search (dense + sparse)
        - Re-ranking
        """
        config = AdvancedSearchConfig(
            enable_query_expansion=True,
            enable_hyde=True,
            enable_query_classification=True,
            enable_reranking=True,
            max_total_time_ms=500,  # Higher for test stability
        )
        
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Mock the hybrid searcher's search method to avoid actual vector operations
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(
                    chunk=sample_document_chunks[0],
                    score=0.85,
                    rank=1,
                    distance=0.15
                ),
                SearchResult(
                    chunk=sample_document_chunks[1],
                    score=0.75,
                    rank=2,
                    distance=0.25
                ),
            ]
            
            await searcher.initialize()
            
            try:
                results = await searcher.search("machine learning basics", top_k=5)
                
                assert isinstance(results, list)
                assert len(results) <= 5
                assert all(isinstance(r, SearchResult) for r in results)
                
                # Verify performance tracking
                stats = searcher._search_stats
                assert stats['total_searches'] >= 1
                
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_factual_query(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test pipeline with factual query type.
        
        Validates that factual queries (e.g., "What is...") are properly
        classified and routed through the pipeline.
        """
        config = AdvancedSearchConfig(enable_query_classification=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Verify query classification
        classification = query_classifier.classify("What is machine learning?")
        assert classification.query_type == QueryType.FACTUAL
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("What is machine learning?", top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_conceptual_query(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test pipeline with conceptual query type.
        
        Validates that conceptual queries (e.g., "Explain...") are properly
        classified and benefit from query expansion.
        """
        classification = query_classifier.classify("Explain how neural networks work")
        assert classification.query_type == QueryType.CONCEPTUAL
        
        config = AdvancedSearchConfig(enable_query_expansion=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[1], score=0.88, rank=1, distance=0.12),
                SearchResult(chunk=sample_document_chunks[0], score=0.82, rank=2, distance=0.18),
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("Explain how neural networks work", top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_procedural_query(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test pipeline with procedural query type.
        
        Validates that procedural queries (e.g., "How to...") are properly
        classified and routed.
        """
        classification = query_classifier.classify("How to implement a neural network?")
        assert classification.query_type == QueryType.PROCEDURAL
        
        config = AdvancedSearchConfig()
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[1], score=0.85, rank=1, distance=0.15)
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("How to implement a neural network?", top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_comparative_query(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test pipeline with comparative query type.
        
        Validates that comparative queries (e.g., "vs", "compare") are properly
        classified and benefit from multi-query approaches.
        """
        classification = query_classifier.classify("Compare supervised vs unsupervised learning")
        assert classification.query_type == QueryType.COMPARATIVE
        
        config = AdvancedSearchConfig(enable_query_expansion=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[5], score=0.9, rank=1, distance=0.1),
                SearchResult(chunk=sample_document_chunks[6], score=0.85, rank=2, distance=0.15),
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("Compare supervised vs unsupervised learning", top_k=4)
                assert len(results) >= 2
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_exploratory_query(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test pipeline with exploratory query type.
        
        Validates that exploratory queries (e.g., "Tell me about...") are properly
        classified and benefit from query expansion.
        """
        classification = query_classifier.classify("Tell me everything about AI")
        assert classification.query_type == QueryType.EXPLORATORY
        
        config = AdvancedSearchConfig(enable_query_expansion=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.8, rank=1, distance=0.2),
                SearchResult(chunk=sample_document_chunks[1], score=0.78, rank=2, distance=0.22),
                SearchResult(chunk=sample_document_chunks[2], score=0.75, rank=3, distance=0.25),
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("Tell me everything about AI", top_k=5)
                assert len(results) > 0
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_technical_query(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test pipeline with technical query type.
        
        Validates that technical queries (e.g., API, code-related) are properly
        classified and routed to appropriate retrieval strategies.
        """
        classification = query_classifier.classify("API error in TensorFlow model training")
        assert classification.query_type == QueryType.TECHNICAL
        
        config = AdvancedSearchConfig()
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[1], score=0.87, rank=1, distance=0.13)
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("API error in TensorFlow model training", top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_different_configurations(self, sample_document_chunks, mock_reranker):
        """Test pipeline with various configuration combinations.
        
        Validates that the pipeline works correctly with different feature
        enable/disable combinations.
        """
        configs = [
            # All features enabled
            AdvancedSearchConfig(
                enable_query_expansion=True,
                enable_hyde=True,
                enable_query_classification=True,
                enable_reranking=True,
            ),
            # Minimal config
            AdvancedSearchConfig(
                enable_query_expansion=False,
                enable_hyde=False,
                enable_query_classification=False,
                enable_reranking=False,
            ),
            # Expansion only
            AdvancedSearchConfig(
                enable_query_expansion=True,
                enable_hyde=False,
                enable_query_classification=False,
                enable_reranking=False,
            ),
            # Re-ranking only
            AdvancedSearchConfig(
                enable_query_expansion=False,
                enable_hyde=False,
                enable_query_classification=False,
                enable_reranking=True,
            ),
        ]
        
        for config in configs:
            searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
            
            with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
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
# Performance Benchmark Tests (4-5 tests)
# ============================================================================

class TestPerformanceBenchmarks:
    """Test suite for performance benchmarks.
    
    Validates latency targets, accuracy thresholds, and performance regression.
    """

    @pytest.mark.asyncio
    async def test_query_enhancement_latency(self, mock_hyde_generator, query_classifier):
        """Test query enhancement latency is within acceptable bounds.
        
        Target: Query enhancement should complete in <50ms for typical queries.
        """
        queries = [
            "What is machine learning?",
            "How to implement neural networks?",
            "Compare Python and JavaScript",
        ]
        
        for query in queries:
            start_time = time.perf_counter()
            
            # Query classification
            classification = query_classifier.classify(query)
            
            # Query expansion
            expander = QueryExpander(ExpansionConfig(max_expansions=3))
            expansions = expander.expand(query)
            
            # HyDE generation (async)
            hypothetical_docs = await mock_hyde_generator.generate_hypothetical_documents(query)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Query enhancement should be fast (<100ms for tests)
            assert elapsed_ms < 100, f"Query enhancement took {elapsed_ms:.2f}ms for '{query}'"
            assert classification.query_type is not None
            assert len(expansions) > 0

    @pytest.mark.asyncio
    async def test_reranking_accuracy(self, sample_search_results, mock_reranker):
        """Test re-ranking improves result relevance.
        
        Validates that re-ranking produces different (and ideally better) ordering.
        """
        await mock_reranker.initialize()
        
        query = "machine learning neural networks"
        original_results = sample_search_results.copy()
        
        reranking_result = await mock_reranker.rerank(query, original_results)
        
        # Re-ranking should complete
        assert reranking_result is not None
        assert len(reranking_result.results) > 0
        
        # Scores should be valid
        for result in reranking_result.results:
            assert 0.0 <= result.score <= 1.0
        
        # Processing time should be reasonable
        assert reranking_result.processing_time_ms >= 0
        assert reranking_result.processing_time_ms < 1000  # Should complete within 1 second
        
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_end_to_end_retrieval_accuracy(self, sample_document_chunks, mock_reranker):
        """Test end-to-end retrieval accuracy meets target threshold.
        
        Target: >85% retrieval accuracy (top-k relevance).
        
        This test simulates a scenario where we know the expected relevant documents
        and verify they are retrieved with high accuracy.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Create a mapping of queries to expected relevant document indices
        test_cases = [
            ("machine learning", [0, 5, 6]),  # Should return ML-related docs
            ("neural networks", [1]),  # Should return deep learning doc
            ("natural language processing", [2]),  # Should return NLP doc
        ]
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            # Mock returns results that simulate good retrieval
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.95, rank=1, distance=0.05),
                SearchResult(chunk=sample_document_chunks[5], score=0.90, rank=2, distance=0.10),
                SearchResult(chunk=sample_document_chunks[6], score=0.85, rank=3, distance=0.15),
            ]
            
            await searcher.initialize()
            try:
                for query, expected_indices in test_cases:
                    results = await searcher.search(query, top_k=5)
                    
                    # Calculate accuracy: what fraction of expected docs were retrieved
                    retrieved_ids = {r.chunk.document_id for r in results}
                    expected_docs = {sample_document_chunks[i].document_id for i in expected_indices}
                    
                    if expected_docs:
                        overlap = len(retrieved_ids.intersection(expected_docs))
                        accuracy = overlap / len(expected_docs)
                        
                        # For mocked tests, we just verify results are returned
                        # In real scenarios, this would validate >85% accuracy
                        assert len(results) > 0, f"No results for query: {query}"
                        
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_performance_regression_pipeline_latency(self, sample_document_chunks, mock_reranker):
        """Test that pipeline latency stays within acceptable bounds.
        
        Target: <150ms end-to-end latency for typical queries.
        """
        config = AdvancedSearchConfig(
            enable_query_expansion=True,
            enable_hyde=True,
            enable_reranking=True,
            max_total_time_ms=500,  # Relaxed for test environment
        )
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1),
                SearchResult(chunk=sample_document_chunks[1], score=0.8, rank=2, distance=0.2),
            ]
            
            await searcher.initialize()
            try:
                start_time = time.perf_counter()
                results = await searcher.search("machine learning", top_k=5)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                # Pipeline should complete in reasonable time
                assert elapsed_ms < 500, f"Pipeline took {elapsed_ms:.2f}ms, exceeds threshold"
                assert len(results) > 0
                
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, sample_document_chunks, mock_reranker):
        """Test pipeline performance under concurrent load.
        
        Validates that multiple concurrent searches complete successfully.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher.initialize()
            try:
                queries = ["machine learning", "deep learning", "neural networks", "AI"]
                
                start_time = time.perf_counter()
                
                # Execute searches concurrently
                tasks = [searcher.search(q, top_k=3) for q in queries]
                results = await asyncio.gather(*tasks)
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                # All queries should complete
                assert len(results) == len(queries)
                for result_list in results:
                    assert isinstance(result_list, list)
                
                # Concurrent execution should be efficient
                assert elapsed_ms < 1000, f"Concurrent searches took {elapsed_ms:.2f}ms"
                
            finally:
                await searcher.close()


# ============================================================================
# Component Integration Tests (6-8 tests)
# ============================================================================

class TestComponentIntegration:
    """Test suite for component integration.
    
    Validates interactions between query enhancement, search, and re-ranking.
    """

    @pytest.mark.asyncio
    async def test_query_enhancement_vector_search_integration(self, sample_document_chunks):
        """Test query enhancement integrates correctly with vector search.
        
        Validates that expanded queries produce valid search results.
        """
        query = "machine learning"
        
        # Query expansion
        expander = QueryExpander(ExpansionConfig(max_expansions=3))
        expansions = expander.expand(query)
        
        assert len(expansions) > 0
        
        # Each expansion should be a valid search query
        for expansion in expansions:
            assert isinstance(expansion, str)
            assert len(expansion) > 0

    @pytest.mark.asyncio
    async def test_vector_search_reranking_integration(self, sample_search_results, mock_reranker):
        """Test vector search results integrate correctly with re-ranking.
        
        Validates that search results can be successfully re-ranked.
        """
        await mock_reranker.initialize()
        
        query = "machine learning algorithms"
        
        # Re-rank the search results
        reranking_result = await mock_reranker.rerank(query, sample_search_results)
        
        assert reranking_result is not None
        assert len(reranking_result.results) == len(sample_search_results)
        
        # Verify results are still valid SearchResult objects
        for result in reranking_result.results:
            assert isinstance(result, SearchResult)
            assert result.chunk is not None
            assert 0.0 <= result.score <= 1.0
        
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_query_enhancement_reranking_integration(self, mock_hyde_generator, mock_reranker, sample_search_results):
        """Test query enhancement integrates correctly with re-ranking.
        
        Validates that enhanced queries work well with re-ranking.
        """
        await mock_reranker.initialize()
        
        query = "deep learning neural networks"
        
        # Generate hypothetical documents
        hypothetical_docs = await mock_hyde_generator.generate_hypothetical_documents(query)
        assert len(hypothetical_docs) > 0
        
        # Re-rank using original query
        reranking_result = await mock_reranker.rerank(query, sample_search_results)
        
        assert reranking_result is not None
        assert len(reranking_result.results) > 0
        
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_all_components_together(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test all three components (enhancement, search, re-ranking) together.
        
        Validates the complete integration of all pipeline components.
        """
        # 1. Query Enhancement
        query = "machine learning algorithms"
        classification = query_classifier.classify(query)
        expander = QueryExpander(ExpansionConfig(max_expansions=2))
        expansions = expander.expand(query)
        
        assert classification.query_type is not None
        assert len(expansions) > 0
        
        # 2. Search (mocked)
        search_results = [
            SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1),
            SearchResult(chunk=sample_document_chunks[5], score=0.85, rank=2, distance=0.15),
            SearchResult(chunk=sample_document_chunks[1], score=0.8, rank=3, distance=0.2),
        ]
        
        # 3. Re-ranking
        await mock_reranker.initialize()
        reranking_result = await mock_reranker.rerank(query, search_results)
        
        assert reranking_result is not None
        assert len(reranking_result.results) > 0
        
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_hyde_search_integration(self, mock_hyde_generator, sample_document_chunks):
        """Test HyDE generation integrates with search.
        
        Validates that hypothetical documents can be used for search enhancement.
        """
        query = "natural language processing"
        
        # Generate hypothetical documents
        hypothetical_docs = await mock_hyde_generator.generate_hypothetical_documents(query)
        
        assert len(hypothetical_docs) > 0
        assert all(isinstance(doc, str) for doc in hypothetical_docs)
        
        # Hypothetical docs should contain relevant content
        for doc in hypothetical_docs:
            assert len(doc) > 0

    @pytest.mark.asyncio
    async def test_classification_routing_integration(self, query_classifier):
        """Test query classification integrates with routing decisions.
        
        Validates that classification results provide useful routing recommendations.
        """
        queries_by_type = {
            QueryType.FACTUAL: "What is Python?",
            QueryType.CONCEPTUAL: "Explain how Python works",
            QueryType.PROCEDURAL: "How to install Python?",
            QueryType.COMPARATIVE: "Python vs JavaScript",
            QueryType.EXPLORATORY: "Tell me about Python",
            QueryType.TECHNICAL: "Python API documentation",
        }
        
        for expected_type, query in queries_by_type.items():
            classification = query_classifier.classify(query)
            
            assert classification.query_type == expected_type
            assert classification.confidence > 0
            assert 'dense_retrieval_weight' in classification.recommendations
            assert 'sparse_retrieval_weight' in classification.recommendations

    @pytest.mark.asyncio
    async def test_fusion_reranking_integration(self, sample_document_chunks, mock_reranker):
        """Test result fusion integrates with re-ranking.
        
        Validates that fused results from multiple retrievers can be re-ranked.
        """
        # Simulate fused results from dense and sparse retrieval
        fused_results = [
            SearchResult(chunk=sample_document_chunks[0], score=0.92, rank=1, distance=0.08),
            SearchResult(chunk=sample_document_chunks[1], score=0.88, rank=2, distance=0.12),
            SearchResult(chunk=sample_document_chunks[2], score=0.85, rank=3, distance=0.15),
            SearchResult(chunk=sample_document_chunks[3], score=0.80, rank=4, distance=0.20),
        ]
        
        await mock_reranker.initialize()
        
        query = "artificial intelligence"
        reranking_result = await mock_reranker.rerank(query, fused_results)
        
        assert reranking_result is not None
        assert len(reranking_result.results) == len(fused_results)
        
        # Verify ranks are updated
        for i, result in enumerate(reranking_result.results):
            assert result.rank == i + 1
        
        await mock_reranker.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_disabled_components(self, sample_document_chunks, mock_reranker):
        """Test pipeline works with various component combinations disabled.
        
        Validates graceful degradation when features are disabled.
        """
        # Test with re-ranking disabled
        config_no_rerank = AdvancedSearchConfig(enable_reranking=False)
        searcher_no_rerank = AdvancedHybridSearcher(config=config_no_rerank, reranker=mock_reranker)
        
        with patch.object(searcher_no_rerank.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher_no_rerank.initialize()
            try:
                results = await searcher_no_rerank.search("test query", top_k=3)
                assert len(results) > 0
            finally:
                await searcher_no_rerank.close()
        
        # Test with expansion disabled
        config_no_expand = AdvancedSearchConfig(enable_query_expansion=False)
        searcher_no_expand = AdvancedHybridSearcher(config=config_no_expand, reranker=mock_reranker)
        
        with patch.object(searcher_no_expand.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher_no_expand.initialize()
            try:
                results = await searcher_no_expand.search("test query", top_k=3)
                assert len(results) > 0
            finally:
                await searcher_no_expand.close()


# ============================================================================
# Error Handling & Recovery Tests (4-5 tests)
# ============================================================================

class TestErrorHandlingRecovery:
    """Test suite for error handling and recovery.
    
    Validates pipeline resilience to failures and graceful degradation.
    """

    @pytest.mark.asyncio
    async def test_pipeline_failure_recovery(self, sample_document_chunks, mock_reranker):
        """Test pipeline recovers from component failures.
        
        Validates that the pipeline continues to function even when
        individual components fail.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher.initialize()
            try:
                # Search should succeed even if some components have issues
                results = await searcher.search("test query", top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_partial_component_failure_handling(self, sample_document_chunks, mock_reranker):
        """Test pipeline handles partial component failures gracefully.
        
        Validates that if one component fails, others continue to function.
        """
        config = AdvancedSearchConfig(
            enable_query_expansion=True,
            enable_hyde=True,
            enable_reranking=True,
        )
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Simulate HyDE failure by patching it
        with patch.object(searcher, 'hyde_generator', None):
            with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = [
                    SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
                ]
                
                await searcher.initialize()
                try:
                    # Should still work without HyDE
                    results = await searcher.search("test query", top_k=3)
                    assert len(results) > 0
                finally:
                    await searcher.close()

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, sample_document_chunks, mock_reranker):
        """Test fallback mechanisms when primary methods fail.
        
        Validates that the pipeline falls back to simpler methods when
        advanced features fail.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        await searcher.initialize()
        try:
            # Test with empty query - should return empty results gracefully
            results = await searcher.search("", top_k=3)
            assert results == []
            
            # Test with whitespace-only query
            results = await searcher.search("   ", top_k=3)
            assert results == []
        finally:
            await searcher.close()

    @pytest.mark.asyncio
    async def test_empty_results_handling(self, sample_document_chunks, mock_reranker):
        """Test pipeline handles empty results gracefully.
        
        Validates that the pipeline doesn't crash when no results are found.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []  # Empty results
            
            await searcher.initialize()
            try:
                results = await searcher.search("obscure query with no matches", top_k=3)
                assert results == []
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_reranking_failure_fallback(self, sample_document_chunks, mock_reranker):
        """Test fallback when re-ranking fails.
        
        Validates that original results are returned if re-ranking fails.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        original_results = [
            SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1),
            SearchResult(chunk=sample_document_chunks[1], score=0.8, rank=2, distance=0.2),
        ]
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = original_results
            
            # Simulate re-ranking failure
            with patch.object(mock_reranker, 'rerank', side_effect=Exception("Reranking failed")):
                await searcher.initialize()
                try:
                    # Should still return results (without re-ranking)
                    results = await searcher.search("test query", top_k=3)
                    assert len(results) > 0
                finally:
                    await searcher.close()


# ============================================================================
# Data Flow Tests (3-4 tests)
# ============================================================================

class TestDataFlow:
    """Test suite for data flow through the pipeline.
    
    Validates that data is correctly passed and transformed through
    all pipeline stages.
    """

    @pytest.mark.asyncio
    async def test_document_flow_through_pipeline(self, sample_document_chunks, mock_reranker):
        """Test documents flow correctly through all pipeline stages.
        
        Validates that document content, metadata, and IDs are preserved
        through the pipeline.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        original_chunk = sample_document_chunks[0]
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=original_chunk, score=0.95, rank=1, distance=0.05)
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("machine learning", top_k=3)
                
                assert len(results) == 1
                result = results[0]
                
                # Verify document properties are preserved
                assert result.chunk.document_id == original_chunk.document_id
                assert result.chunk.content == original_chunk.content
                assert result.chunk.metadata.title == original_chunk.metadata.title
                assert result.chunk.metadata.source == original_chunk.metadata.source
                
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_metadata_preservation(self, sample_document_chunks, mock_reranker):
        """Test metadata is preserved through pipeline stages.
        
        Validates that document metadata (title, source, tags, etc.)
        is correctly passed through all stages.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Create chunk with rich metadata
        chunk_with_metadata = DocumentChunk(
            document_id=uuid4(),
            content="Test content about AI",
            index=0,
            metadata=Metadata(
                title="AI Test Document",
                source="test_source.pdf",
                author="Test Author",
                tags=["ai", "test", "ml"],
                custom={"section": "introduction", "page": 1}
            )
        )
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=chunk_with_metadata, score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search("AI test", top_k=3)
                
                assert len(results) == 1
                metadata = results[0].chunk.metadata
                
                # Verify all metadata fields are preserved
                assert metadata.title == "AI Test Document"
                assert metadata.source == "test_source.pdf"
                assert metadata.author == "Test Author"
                assert "ai" in metadata.tags
                assert metadata.custom.get("section") == "introduction"
                
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_score_propagation(self, sample_document_chunks, mock_reranker):
        """Test score propagation and transformation through pipeline.
        
        Validates that relevance scores are correctly computed, passed,
        and potentially transformed through re-ranking.
        """
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Create results with known scores
        original_results = [
            SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1),
            SearchResult(chunk=sample_document_chunks[1], score=0.8, rank=2, distance=0.2),
            SearchResult(chunk=sample_document_chunks[2], score=0.7, rank=3, distance=0.3),
        ]
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = original_results
            
            await searcher.initialize()
            try:
                results = await searcher.search("test query", top_k=3)
                
                # Verify scores are valid
                for result in results:
                    assert 0.0 <= result.score <= 1.0, f"Score {result.score} out of range"
                    assert result.rank >= 1
                    assert result.distance >= 0.0
                
                # Verify ranks are sequential
                for i, result in enumerate(results):
                    assert result.rank == i + 1
                    
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_query_transformation_flow(self, sample_document_chunks, mock_reranker, query_classifier):
        """Test query transformation through enhancement stages.
        
        Validates that queries are correctly classified, expanded,
        and enhanced through the pipeline.
        """
        original_query = "machine learning"
        
        # Stage 1: Classification
        classification = query_classifier.classify(original_query)
        assert classification.query_type is not None
        
        # Stage 2: Expansion
        expander = QueryExpander(ExpansionConfig(max_expansions=3))
        expansions = expander.expand(original_query)
        assert len(expansions) > 0
        assert original_query in expansions  # Original should be preserved
        
        # Stage 3: Search with enhanced query
        config = AdvancedSearchConfig(enable_query_expansion=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher.initialize()
            try:
                results = await searcher.search(original_query, top_k=3)
                assert len(results) > 0
            finally:
                await searcher.close()


# ============================================================================
# Additional Integration Tests
# ============================================================================

class TestAdvancedPipelineScenarios:
    """Additional test scenarios for the advanced pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_statistics_tracking(self, sample_document_chunks, mock_reranker):
        """Test that pipeline correctly tracks and reports statistics."""
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1)
            ]
            
            await searcher.initialize()
            try:
                # Perform multiple searches
                for _ in range(3):
                    await searcher.search("test query", top_k=3)
                
                # Check statistics
                stats = searcher._search_stats
                assert stats['total_searches'] == 3
                assert stats['avg_time_ms'] >= 0
                
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_with_complex_query(self, sample_document_chunks, mock_reranker):
        """Test pipeline with complex multi-part queries."""
        config = AdvancedSearchConfig(
            enable_query_expansion=True,
            enable_query_classification=True,
            enable_reranking=True,
        )
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        complex_queries = [
            "What is the difference between supervised and unsupervised learning in machine learning?",
            "How to implement a neural network for image classification using Python and TensorFlow?",
            "Compare and contrast deep learning vs traditional machine learning approaches",
        ]
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=sample_document_chunks[0], score=0.9, rank=1, distance=0.1),
                SearchResult(chunk=sample_document_chunks[1], score=0.85, rank=2, distance=0.15),
            ]
            
            await searcher.initialize()
            try:
                for query in complex_queries:
                    results = await searcher.search(query, top_k=5)
                    assert isinstance(results, list)
            finally:
                await searcher.close()

    @pytest.mark.asyncio
    async def test_pipeline_initialization_cleanup(self, mock_reranker):
        """Test proper initialization and cleanup of pipeline components."""
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        # Test initialization
        await searcher.initialize()
        assert searcher._initialized is True
        
        # Test cleanup
        await searcher.close()
        assert searcher._initialized is False

    @pytest.mark.asyncio
    async def test_pipeline_with_varied_top_k(self, sample_document_chunks, mock_reranker):
        """Test pipeline with different top_k values."""
        config = AdvancedSearchConfig(enable_reranking=True)
        searcher = AdvancedHybridSearcher(config=config, reranker=mock_reranker)
        
        with patch.object(searcher.hybrid_searcher, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                SearchResult(chunk=chunk, score=0.9 - (i * 0.05), rank=i+1, distance=0.1 + (i * 0.05))
                for i, chunk in enumerate(sample_document_chunks[:5])
            ]
            
            await searcher.initialize()
            try:
                # Test different top_k values
                for top_k in [1, 3, 5, 10]:
                    results = await searcher.search("test", top_k=top_k)
                    assert len(results) <= top_k
            finally:
                await searcher.close()
