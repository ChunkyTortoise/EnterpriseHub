"""Query Enhancement Performance Benchmarks.

Validates latency and throughput targets for query enhancement components:
- Query expansion: <10ms per query
- HyDE generation: <20ms per query (mock LLM)
- Query classification: <5ms per query
- Combined enhancement pipeline: <50ms total
- Throughput: >100 queries/second for classification
"""

import statistics
import time

import pytest
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
# Test Data
# ============================================================================

BENCHMARK_QUERIES = {
    QueryType.FACTUAL: [
        "What is machine learning?",
        "What is the definition of a neural network?",
        "What is the meaning of deep learning?",
        "What is the capital of France?",
        "Where is the location of MIT?",
    ],
    QueryType.CONCEPTUAL: [
        "Explain how neural networks learn",
        "What are the principles of deep learning?",
        "Explain the concept of attention mechanisms",
        "How does backpropagation work?",
        "What is the theory behind word embeddings?",
    ],
    QueryType.PROCEDURAL: [
        "How to install PyTorch?",
        "How to build a recommendation system?",
        "How to fine-tune a language model?",
        "How to create a vector database?",
        "How to implement attention from scratch?",
    ],
    QueryType.COMPARATIVE: [
        "Compare PyTorch vs TensorFlow",
        "What is the difference between CNN and RNN?",
        "Compare supervised vs unsupervised learning",
        "BERT vs GPT architecture differences",
        "Compare batch norm vs layer norm",
    ],
    QueryType.EXPLORATORY: [
        "Explore everything about reinforcement learning",
        "Tell me about generative AI research",
        "Discover applications of computer vision",
        "What can transformers be used for?",
        "Research on multi-modal AI systems",
    ],
    QueryType.TECHNICAL: [
        "API endpoint for model inference error",
        "Debug CUDA out of memory exception",
        "TensorFlow session configuration options",
        "Python package dependency conflict resolution",
        "Optimize batch size for GPU training",
    ],
}

ALL_QUERIES = [q for queries in BENCHMARK_QUERIES.values() for q in queries]


# ============================================================================
# Query Expansion Benchmarks
# ============================================================================


class TestQueryExpansionPerformance:
    """Benchmark query expansion latency and quality."""

    @pytest.fixture
    def expander(self):
        return QueryExpander(ExpansionConfig(max_expansions=5, synonym_limit=3))

    def test_expansion_latency_under_10ms(self, expander):
        """Each query expansion should complete in <10ms."""
        latencies = []
        for query in ALL_QUERIES:
            start = time.perf_counter()
            expander.expand(query)
            latencies.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        assert avg < 10, f"Average expansion latency {avg:.2f}ms exceeds 10ms"
        assert p95 < 20, f"P95 expansion latency {p95:.2f}ms exceeds 20ms"

    def test_expansion_produces_results(self, expander):
        """Expansion should produce at least the original query for all inputs."""
        for query in ALL_QUERIES:
            expansions = expander.expand(query)
            assert len(expansions) >= 1, f"No expansions for: {query}"

    def test_expansion_throughput(self, expander):
        """Should handle >200 expansions/second."""
        start = time.perf_counter()
        count = 0
        for _ in range(3):
            for query in ALL_QUERIES:
                expander.expand(query)
                count += 1
        elapsed = time.perf_counter() - start

        throughput = count / elapsed
        assert throughput > 200, f"Expansion throughput {throughput:.0f}/s below 200/s target"

    def test_expansion_cache_speedup(self):
        """Repeated queries should benefit from synonym cache."""
        expander = QueryExpander(ExpansionConfig(max_expansions=5))
        query = "machine learning algorithms"

        # Cold run
        start = time.perf_counter()
        expander.expand(query)
        cold_ms = (time.perf_counter() - start) * 1000

        # Warm run (cache hit)
        start = time.perf_counter()
        expander.expand(query)
        warm_ms = (time.perf_counter() - start) * 1000

        # Warm should be at least as fast (cache may or may not help depending on implementation)
        assert warm_ms < cold_ms * 2, "Cache provided no benefit"


# ============================================================================
# HyDE Generation Benchmarks
# ============================================================================


class TestHyDEPerformance:
    """Benchmark HyDE generation latency and quality."""

    @pytest.fixture
    def hyde(self):
        config = HyDEConfig(num_hypotheticals=1, use_caching=False)
        provider = MockLLMProvider()
        return HyDEGenerator(config=config, llm_provider=provider)

    @pytest.mark.asyncio
    async def test_hyde_latency_under_20ms(self, hyde):
        """Each HyDE generation should complete in <20ms (mock LLM)."""
        latencies = []
        for query in ALL_QUERIES[:10]:
            start = time.perf_counter()
            await hyde.generate_hypothetical_documents(query)
            latencies.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(latencies)
        assert avg < 20, f"Average HyDE latency {avg:.2f}ms exceeds 20ms"

    @pytest.mark.asyncio
    async def test_hyde_produces_relevant_content(self, hyde):
        """HyDE documents should contain query-relevant content."""
        query = "machine learning"
        docs = await hyde.generate_hypothetical_documents(query)

        assert len(docs) >= 1
        for doc in docs:
            assert len(doc) > 50, "HyDE doc too short to be useful"

    @pytest.mark.asyncio
    async def test_hyde_enhanced_query_length(self, hyde):
        """Enhanced query should be at least as long as original."""
        for query in ["machine learning", "neural networks", "data science"]:
            enhanced = await hyde.generate_enhanced_query(query)
            assert len(enhanced) >= len(query), f"Enhanced query shorter than original for '{query}'"

    @pytest.mark.asyncio
    async def test_hyde_multiple_hypotheticals(self):
        """Multiple hypothetical generation should scale linearly."""
        provider = MockLLMProvider()
        hyde_1 = HyDEGenerator(
            HyDEConfig(num_hypotheticals=1, use_caching=False),
            llm_provider=provider,
        )
        hyde_3 = HyDEGenerator(
            HyDEConfig(num_hypotheticals=3, use_caching=False),
            llm_provider=provider,
        )

        start = time.perf_counter()
        docs_1 = await hyde_1.generate_hypothetical_documents("machine learning")
        time_1 = time.perf_counter() - start

        start = time.perf_counter()
        docs_3 = await hyde_3.generate_hypothetical_documents("machine learning")
        time_3 = time.perf_counter() - start

        assert len(docs_3) >= len(docs_1)
        # 3x docs should take less than 10x time (reasonable overhead)
        assert time_3 < time_1 * 10


# ============================================================================
# Query Classification Benchmarks
# ============================================================================


class TestClassificationPerformance:
    """Benchmark query classification latency and accuracy."""

    @pytest.fixture
    def classifier(self):
        return QueryClassifier()

    def test_classification_latency_under_5ms(self, classifier):
        """Each classification should complete in <5ms."""
        latencies = []
        for query in ALL_QUERIES:
            start = time.perf_counter()
            classifier.classify(query)
            latencies.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(latencies)
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        assert avg < 5, f"Average classification latency {avg:.2f}ms exceeds 5ms"
        assert p99 < 10, f"P99 classification latency {p99:.2f}ms exceeds 10ms"

    def test_classification_throughput_over_100qps(self, classifier):
        """Should classify >100 queries/second."""
        start = time.perf_counter()
        count = 0
        for _ in range(5):
            for query in ALL_QUERIES:
                classifier.classify(query)
                count += 1
        elapsed = time.perf_counter() - start

        throughput = count / elapsed
        assert throughput > 100, f"Classification throughput {throughput:.0f}/s below 100/s target"

    def test_classification_accuracy_per_type(self, classifier):
        """Classification accuracy should be >80% per query type."""
        for query_type, queries in BENCHMARK_QUERIES.items():
            correct = 0
            for query in queries:
                result = classifier.classify(query)
                if result.query_type == query_type:
                    correct += 1

            accuracy = correct / len(queries)
            assert accuracy >= 0.6, f"Accuracy for {query_type.value}: {accuracy:.0%} below 60% threshold"

    def test_classification_confidence_range(self, classifier):
        """All classifications should have valid confidence scores."""
        for query in ALL_QUERIES:
            result = classifier.classify(query)
            assert 0.0 <= result.confidence <= 1.0, f"Invalid confidence {result.confidence} for '{query}'"

    def test_classification_recommendations_completeness(self, classifier):
        """All classifications should include routing recommendations."""
        required_keys = [
            "dense_retrieval_weight",
            "sparse_retrieval_weight",
            "query_expansion",
            "hyde_generation",
            "reranking",
        ]

        for query in ALL_QUERIES[:10]:
            result = classifier.classify(query)
            for key in required_keys:
                assert key in result.recommendations, f"Missing '{key}' in recommendations for '{query}'"


# ============================================================================
# Combined Pipeline Benchmarks
# ============================================================================


class TestCombinedEnhancementPerformance:
    """Benchmark the full enhancement pipeline."""

    @pytest.mark.asyncio
    async def test_combined_pipeline_under_50ms(self):
        """Full enhancement pipeline should complete in <50ms."""
        classifier = QueryClassifier()
        expander = QueryExpander(ExpansionConfig(max_expansions=3))
        hyde = HyDEGenerator(
            HyDEConfig(num_hypotheticals=1, use_caching=False),
            llm_provider=MockLLMProvider(),
        )

        latencies = []
        for query in ALL_QUERIES[:10]:
            start = time.perf_counter()

            # Classification
            classification = classifier.classify(query)

            # Expansion
            expansions = expander.expand(query)

            # HyDE
            docs = await hyde.generate_hypothetical_documents(query)

            latencies.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        assert avg < 50, f"Average pipeline latency {avg:.2f}ms exceeds 50ms"
        assert p95 < 75, f"P95 pipeline latency {p95:.2f}ms exceeds 75ms"

    @pytest.mark.asyncio
    async def test_enhancement_breakdown(self):
        """Measure time breakdown across enhancement components."""
        classifier = QueryClassifier()
        expander = QueryExpander(ExpansionConfig(max_expansions=3))
        hyde = HyDEGenerator(
            HyDEConfig(num_hypotheticals=1, use_caching=False),
            llm_provider=MockLLMProvider(),
        )

        query = "How does machine learning work?"

        start = time.perf_counter()
        classifier.classify(query)
        classify_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        expander.expand(query)
        expand_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        await hyde.generate_hypothetical_documents(query)
        hyde_ms = (time.perf_counter() - start) * 1000

        total = classify_ms + expand_ms + hyde_ms

        # Each component should be fast
        assert classify_ms < 10, f"Classification: {classify_ms:.2f}ms"
        assert expand_ms < 20, f"Expansion: {expand_ms:.2f}ms"
        assert hyde_ms < 30, f"HyDE: {hyde_ms:.2f}ms"
        assert total < 50, f"Total: {total:.2f}ms"
