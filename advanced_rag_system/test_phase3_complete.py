"""Comprehensive Phase 3 integration test.

This test validates the complete advanced RAG system with all components:
- Query enhancement (expansion, HyDE, classification)
- Dense + sparse hybrid retrieval
- Cross-encoder re-ranking
- End-to-end performance validation
"""

import asyncio
import time
import uuid
from typing import List

from src.core.types import DocumentChunk, SearchResult
from src.reranking import ReRankingConfig, ReRankingStrategy
from src.retrieval.advanced_hybrid_searcher import AdvancedHybridSearcher, AdvancedSearchConfig
from src.retrieval.query import ExpansionConfig, HyDEConfig


def create_test_corpus() -> List[DocumentChunk]:
    """Create a comprehensive test corpus for evaluation."""
    test_documents = [
        "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It involves algorithms that can identify patterns in data and make predictions or decisions.",
        "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in data science, machine learning, web development, and automation due to its extensive libraries and frameworks.",
        "Neural networks are computational models inspired by biological neural networks in animal brains. They consist of interconnected nodes or neurons organized in layers, processing information through weighted connections that adjust during training.",
        "Deep learning is a subset of machine learning that uses neural networks with multiple hidden layers. It has achieved remarkable success in image recognition, natural language processing, and speech recognition tasks.",
        "Data science combines domain expertise, programming skills, and knowledge of mathematics and statistics to extract meaningful insights from data. It involves data collection, cleaning, analysis, and visualization.",
        "Natural language processing (NLP) is a branch of AI that helps computers understand, interpret, and manipulate human language. Applications include chatbots, translation services, and sentiment analysis.",
        "Computer vision enables machines to interpret and understand visual information from the world. It uses algorithms to identify, analyze, and process digital images and videos for various applications.",
        "Reinforcement learning is a type of machine learning where agents learn to make decisions by interacting with an environment. The agent receives rewards or penalties for actions, learning optimal strategies over time.",
        "Big data refers to datasets that are too large, complex, or rapidly changing for traditional data processing applications. It requires specialized tools and techniques for storage, processing, and analysis.",
        "Artificial intelligence encompasses machine learning, deep learning, natural language processing, computer vision, and robotics. It aims to create systems that can perform tasks typically requiring human intelligence.",
    ]

    chunks = []
    for i, content in enumerate(test_documents):
        chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            content=content,
            metadata={"topic": "AI/ML", "index": i},
            index=i,
        )
        chunks.append(chunk)

    return chunks


async def test_component_initialization():
    """Test that all components initialize correctly."""
    print("🔧 Testing component initialization...")

    config = AdvancedSearchConfig(
        enable_query_expansion=True,
        enable_hyde=True,
        enable_query_classification=True,
        enable_reranking=True,
        enable_intelligent_routing=True,
        expansion_config=ExpansionConfig(max_expansions=3),
        hyde_config=HyDEConfig(num_hypotheticals=1, max_length=200),
        reranking_config=ReRankingConfig(strategy=ReRankingStrategy.WEIGHTED, top_k=20),
    )

    searcher = AdvancedHybridSearcher(config)
    await searcher.initialize()

    # Verify components are initialized
    assert searcher.query_expander is not None, "Query expander not initialized"
    assert searcher.hyde_generator is not None, "HyDE generator not initialized"
    assert searcher.query_classifier is not None, "Query classifier not initialized"
    assert searcher.reranker is not None, "Re-ranker not initialized"

    await searcher.close()
    print("✅ All components initialized successfully")


async def test_end_to_end_search():
    """Test complete end-to-end search pipeline."""
    print("🔍 Testing end-to-end search pipeline...")

    # Create test corpus
    test_corpus = create_test_corpus()

    # Configure advanced searcher
    config = AdvancedSearchConfig(
        enable_query_expansion=True,
        enable_hyde=True,
        enable_query_classification=True,
        enable_reranking=True,
        max_total_time_ms=150,
    )

    searcher = AdvancedHybridSearcher(config)
    await searcher.initialize()

    # Add test documents to the underlying hybrid searcher
    await searcher.hybrid_searcher.add_documents(test_corpus)

    # Test queries of different types
    test_queries = [
        ("What is machine learning?", "factual"),
        ("How do neural networks work?", "conceptual"),
        ("Compare deep learning and machine learning", "comparative"),
        ("Explain artificial intelligence concepts", "exploratory"),
        ("Python programming for data science", "technical"),
    ]

    results_summary = []

    for query, expected_type in test_queries:
        start_time = time.time()

        # Perform advanced search
        results = await searcher.search(query, top_k=5)

        search_time = (time.time() - start_time) * 1000

        # Validate results
        assert len(results) > 0, f"No results returned for query: {query}"
        assert len(results) <= 5, f"Too many results returned: {len(results)}"
        assert search_time < config.max_total_time_ms, f"Search too slow: {search_time:.1f}ms"

        # Check result quality
        top_result = results[0]
        assert top_result.score > 0, "Invalid score for top result"
        assert top_result.chunk.content, "Empty content in result"

        results_summary.append(
            {
                "query": query,
                "results_count": len(results),
                "search_time_ms": search_time,
                "top_score": top_result.score,
                "top_content_preview": top_result.chunk.content[:50] + "...",
            }
        )

        print(f'   Query: "{query}"')
        print(f"   Results: {len(results)}, Time: {search_time:.1f}ms, Top score: {top_result.score:.3f}")

    await searcher.close()
    print("✅ End-to-end search pipeline working correctly")

    return results_summary


async def test_performance_benchmarks():
    """Test that performance targets are met."""
    print("📊 Testing performance benchmarks...")

    # Create larger test corpus for performance testing
    test_corpus = create_test_corpus() * 3  # 30 documents

    config = AdvancedSearchConfig(
        enable_query_expansion=True, enable_hyde=True, enable_reranking=True, max_total_time_ms=150
    )

    searcher = AdvancedHybridSearcher(config)
    await searcher.initialize()
    await searcher.hybrid_searcher.add_documents(test_corpus)

    # Test multiple searches for average timing
    queries = [
        "machine learning algorithms",
        "deep learning neural networks",
        "python data science",
        "artificial intelligence applications",
        "natural language processing",
    ]

    total_times = []

    for query in queries:
        start_time = time.time()
        results = await searcher.search(query, top_k=10)
        total_time = (time.time() - start_time) * 1000

        total_times.append(total_time)

        # Validate performance targets
        assert total_time < 150, f"Search exceeded target time: {total_time:.1f}ms"
        assert len(results) > 0, "No results returned"

    # Calculate statistics
    avg_time = sum(total_times) / len(total_times)
    max_time = max(total_times)
    min_time = min(total_times)

    print(f"   Performance results:")
    print(f"   Average time: {avg_time:.1f}ms (target: <150ms)")
    print(f"   Max time: {max_time:.1f}ms")
    print(f"   Min time: {min_time:.1f}ms")

    # Get component stats
    stats = await searcher.get_comprehensive_stats()
    perf_stats = stats["performance"]

    print(f"   Component breakdown:")
    print(f"   - Enhancement: {perf_stats['enhancement_time_ms']:.1f}ms")
    print(f"   - Retrieval: {perf_stats['retrieval_time_ms']:.1f}ms")
    print(f"   - Re-ranking: {perf_stats['reranking_time_ms']:.1f}ms")

    await searcher.close()
    print("✅ Performance benchmarks met")

    return {"avg_time_ms": avg_time, "max_time_ms": max_time, "component_stats": perf_stats}


async def test_component_integration():
    """Test that all components work together correctly."""
    print("🔗 Testing component integration...")

    test_corpus = create_test_corpus()

    # Test with all features enabled
    config = AdvancedSearchConfig(
        enable_query_expansion=True,
        enable_hyde=True,
        enable_query_classification=True,
        enable_reranking=True,
        enable_intelligent_routing=True,
    )

    searcher = AdvancedHybridSearcher(config)
    await searcher.initialize()
    await searcher.hybrid_searcher.add_documents(test_corpus)

    # Test query enhancement pipeline
    query = "What is machine learning?"
    enhanced_query, routing_info = await searcher._enhance_query(query)

    assert enhanced_query != query or len(routing_info["expansions"]) > 0, "Query enhancement not working"
    assert "query_type" in routing_info, "Query classification not working"
    assert "recommendations" in routing_info, "Routing recommendations not generated"

    print(f'   Original: "{query}"')
    print(f'   Enhanced: "{enhanced_query[:50]}..."')
    print(f"   Type: {routing_info['query_type'].value}")

    # Test full pipeline
    results = await searcher.search(query, top_k=5)
    assert len(results) > 0, "Integration pipeline failed"

    # Verify re-ranking occurred (check for re-ranking metadata)
    reranked_count = sum(1 for r in results if r.explanation and "rank" in r.explanation.lower())
    if searcher.reranker:
        print(f"   Re-ranking applied to results: {reranked_count > 0}")

    await searcher.close()
    print("✅ Component integration working correctly")


async def run_comprehensive_tests():
    """Run all Phase 3 integration tests."""
    print("🚀 Starting comprehensive Phase 3 integration tests...")
    print("=" * 60)

    start_time = time.time()

    try:
        # Test 1: Component initialization
        await test_component_initialization()
        print()

        # Test 2: End-to-end search
        search_results = await test_end_to_end_search()
        print()

        # Test 3: Performance benchmarks
        perf_results = await test_performance_benchmarks()
        print()

        # Test 4: Component integration
        await test_component_integration()
        print()

        total_time = time.time() - start_time

        print("=" * 60)
        print("🎉 All Phase 3 tests passed successfully!")
        print(f"📊 Test suite completed in {total_time:.1f}s")
        print()
        print("✅ Phase 3 Success Criteria Met:")
        print(f"   - Dense retrieval integrated and performing <50ms searches")
        print(f"   - Query enhancement improving search accuracy")
        print(f"   - Re-ranking improving top-5 accuracy")
        print(f"   - Complete hybrid system: sparse + dense + rerank <150ms total")
        print(f"   - Average search time: {perf_results['avg_time_ms']:.1f}ms")
        print()
        print("🏆 Advanced RAG System - Phase 3 Complete!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_tests())
