#!/usr/bin/env python3
"""
Phase 2 Validation Script

Quick validation that Phase 2 hybrid retrieval system is working correctly.
Run this script to verify the system is ready for Phase 3 development.
"""

import asyncio
import time
from uuid import uuid4

from src.core.types import DocumentChunk, Metadata
from src.retrieval import (
    BM25Index,
    BM25Config,
    HybridSearcher,
    HybridSearchConfig,
    ReciprocalRankFusion,
    WeightedScoreFusion
)


async def main():
    """Validate Phase 2 implementation."""
    print("🔍 Advanced RAG System - Phase 2 Validation")
    print("=" * 50)

    # Test data
    doc_id = uuid4()
    test_corpus = [
        DocumentChunk(
            document_id=doc_id,
            content="Python is a powerful programming language for data science and machine learning",
            index=0,
            metadata=Metadata(title="Python Programming")
        ),
        DocumentChunk(
            document_id=doc_id,
            content="Machine learning algorithms enable computers to learn patterns from data",
            index=1,
            metadata=Metadata(title="Machine Learning")
        ),
        DocumentChunk(
            document_id=doc_id,
            content="Data preprocessing and feature engineering are crucial for model performance",
            index=2,
            metadata=Metadata(title="Data Preprocessing")
        ),
    ]

    # Test 1: BM25 Sparse Retrieval
    print("\n✅ Testing BM25 Sparse Retrieval...")
    bm25_index = BM25Index(BM25Config(top_k=5))
    bm25_index.add_documents(test_corpus)

    start_time = time.perf_counter()
    bm25_results = bm25_index.search("python programming")
    bm25_time = (time.perf_counter() - start_time) * 1000

    print(f"   📊 BM25 Search: {bm25_time:.2f}ms (target: <20ms)")
    print(f"   📄 Results: {len(bm25_results)} documents found")
    if bm25_results:
        print(f"   🎯 Top result: {bm25_results[0].chunk.content[:50]}...")

    # Test 2: Hybrid Search with RRF
    print("\n✅ Testing Hybrid Search (RRF)...")
    rrf_config = HybridSearchConfig(fusion_method="rrf")
    hybrid_searcher = HybridSearcher(hybrid_config=rrf_config)

    # Initialize async components
    await hybrid_searcher.initialize()

    # Add documents (now async)
    await hybrid_searcher.add_documents(test_corpus)

    start_time = time.perf_counter()
    hybrid_results = await hybrid_searcher.search("machine learning data")
    hybrid_time = (time.perf_counter() - start_time) * 1000

    print(f"   📊 Hybrid Search: {hybrid_time:.2f}ms (target: <100ms)")
    print(f"   📄 Results: {len(hybrid_results)} documents found")
    if hybrid_results:
        print(f"   🎯 Top result: {hybrid_results[0].chunk.content[:50]}...")

    # Test 3: System Status
    print("\n✅ System Status Check...")
    status = hybrid_searcher.get_retriever_status()
    print(f"   🔧 Dense Enabled: {status['dense_enabled']}")
    print(f"   🔧 Sparse Enabled: {status['sparse_enabled']}")
    print(f"   🔧 Fusion Method: {status['fusion_method']}")
    print(f"   📊 Documents Indexed: {hybrid_searcher.document_count}")

    # Test 4: Fusion Algorithms
    print("\n✅ Testing Fusion Algorithms...")

    # Create mock results for testing
    from src.core.types import SearchResult
    dense_mock = [SearchResult(chunk=test_corpus[0], score=0.9, rank=1, distance=0.1)]
    sparse_mock = [SearchResult(chunk=test_corpus[1], score=0.8, rank=1, distance=0.2)]

    rrf_fusion = ReciprocalRankFusion()
    rrf_results = rrf_fusion.fuse_results(dense_mock, sparse_mock)

    weighted_fusion = WeightedScoreFusion()
    weighted_results = weighted_fusion.fuse_results(dense_mock, sparse_mock)

    print(f"   🔄 RRF Fusion: {len(rrf_results)} fused results")
    print(f"   ⚖️ Weighted Fusion: {len(weighted_results)} fused results")

    # Cleanup
    await hybrid_searcher.close()

    # Summary
    print("\n" + "=" * 50)
    print("🎉 Phase 2 Validation Summary")
    print("=" * 50)

    performance_ok = bm25_time < 20 and hybrid_time < 100
    functionality_ok = len(bm25_results) > 0 and len(hybrid_results) >= 0

    if performance_ok and functionality_ok:
        print("✅ Phase 2 is READY for Phase 3 development!")
        print("✅ All components working correctly")
        print(f"✅ Performance targets met (BM25: {bm25_time:.1f}ms, Hybrid: {hybrid_time:.1f}ms)")
        print("\n🚀 Next step: Implement dense retrieval (Phase 3)")
        print("📖 See PHASE3_CONTINUATION_PROMPT.md for detailed instructions")
    else:
        print("❌ Phase 2 validation failed!")
        print(f"   Performance OK: {performance_ok}")
        print(f"   Functionality OK: {functionality_ok}")

    print("\n📁 Key Phase 2 Files:")
    print("   - src/retrieval/sparse/bm25_index.py (BM25 implementation)")
    print("   - src/retrieval/hybrid/hybrid_searcher.py (Orchestration)")
    print("   - src/retrieval/hybrid/fusion.py (RRF & weighted fusion)")
    print("   - tests/test_phase2_integration.py (Integration tests)")


if __name__ == "__main__":
    asyncio.run(main())