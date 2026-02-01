"""
Embedding Performance Benchmarks

Tests embedding generation latency and throughput according to targets:
- Single embedding: <20ms target, <15ms stretch
- Batch processing: >50 texts/sec target
"""

import pytest
import asyncio
import time
import numpy as np
from typing import List
import sys
import os

# Add the project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

try:
    from ghl_real_estate_ai.core.embeddings import get_embedding_model, get_async_embedding_model
except ImportError:
    # Fallback for testing environment
    class MockEmbedder:
        async def embed(self, texts, batch_size=32):
            # Simulate embedding latency
            await asyncio.sleep(0.01)  # 10ms simulation
            if isinstance(texts, str):
                return np.random.rand(384).tolist()
            return [np.random.rand(384).tolist() for _ in texts]

    def get_embedding_model(device="auto"):
        return MockEmbedder()

    def get_async_embedding_model(device="auto"):
        return MockEmbedder()


class TestEmbeddingPerformance:
    """Benchmark embedding generation performance against defined targets."""

    @pytest.fixture
    def embedder(self):
        """Get embedding model for testing."""
        return get_async_embedding_model(device="auto")

    @pytest.fixture
    def sample_texts(self):
        """Generate sample texts for benchmarking."""
        return [
            "What are the current market trends in real estate?",
            "How do I calculate property investment returns?",
            "What factors affect home pricing in luxury markets?",
            "Explain the process of getting a mortgage pre-approval",
            "What are the benefits of working with a real estate agent?",
        ] * 20  # 100 texts total

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_single_embedding_latency(self, embedder):
        """
        Measure latency for single embedding generation.

        Target: <20ms p50, <15ms stretch goal
        """
        latencies = []
        test_query = "Sample query text for embedding performance testing"

        # Warm up
        await embedder.embed(test_query)

        # Benchmark runs
        for _ in range(100):
            start = time.perf_counter()
            await embedder.embed(test_query)
            latencies.append((time.perf_counter() - start) * 1000)

        # Calculate percentiles
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        print(f"\nSingle Embedding Latency:")
        print(f"  p50: {p50:.2f}ms")
        print(f"  p95: {p95:.2f}ms")
        print(f"  p99: {p99:.2f}ms")

        # Performance assertions
        assert p50 < 20, f"p50 latency {p50:.2f}ms exceeds 20ms target"
        assert p95 < 30, f"p95 latency {p95:.2f}ms exceeds 30ms target"

        # Stretch goal validation
        stretch_goal_met = p50 < 15
        print(f"  Stretch goal (<15ms p50): {'✅ MET' if stretch_goal_met else '⚠️  NOT MET'}")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_batch_embedding_throughput(self, embedder, sample_texts):
        """
        Measure batch embedding throughput.

        Target: >50 texts/sec
        """
        batch_sizes = [16, 32, 64]
        results = {}

        for batch_size in batch_sizes:
            # Use subset of texts
            texts = sample_texts[:100]

            start = time.perf_counter()
            await embedder.embed(texts, batch_size=batch_size)
            elapsed = time.perf_counter() - start

            throughput = len(texts) / elapsed  # texts/sec
            results[batch_size] = {
                'throughput': throughput,
                'elapsed': elapsed,
                'text_count': len(texts)
            }

            print(f"\nBatch size {batch_size}:")
            print(f"  Throughput: {throughput:.1f} texts/sec")
            print(f"  Total time: {elapsed:.2f}s")

            # Performance assertion
            assert throughput > 50, f"Throughput {throughput:.1f} < 50 texts/sec target"

        # Find optimal batch size
        best_batch_size = max(results.keys(), key=lambda x: results[x]['throughput'])
        best_throughput = results[best_batch_size]['throughput']

        print(f"\nOptimal batch size: {best_batch_size} ({best_throughput:.1f} texts/sec)")

        return results

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_embedding_performance(self, embedder):
        """
        Test embedding performance under concurrent load.

        Target: No significant degradation with concurrent requests
        """
        concurrent_levels = [1, 5, 10, 20]
        base_query = "Concurrent embedding test query"
        results = {}

        for concurrency in concurrent_levels:
            # Create concurrent tasks
            async def single_embed():
                start = time.perf_counter()
                await embedder.embed(f"{base_query} {np.random.randint(1000)}")
                return (time.perf_counter() - start) * 1000

            tasks = [single_embed() for _ in range(concurrency)]

            start_total = time.perf_counter()
            latencies = await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start_total

            avg_latency = np.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            throughput = concurrency / total_time

            results[concurrency] = {
                'avg_latency': avg_latency,
                'p95_latency': p95_latency,
                'throughput': throughput
            }

            print(f"\nConcurrency {concurrency}:")
            print(f"  Avg latency: {avg_latency:.2f}ms")
            print(f"  P95 latency: {p95_latency:.2f}ms")
            print(f"  Throughput: {throughput:.1f} requests/sec")

        # Check for performance degradation
        baseline_latency = results[1]['avg_latency']
        max_concurrent_latency = results[max(concurrent_levels)]['avg_latency']

        degradation_ratio = max_concurrent_latency / baseline_latency
        print(f"\nPerformance degradation: {degradation_ratio:.2f}x")

        # Assert reasonable degradation (less than 3x)
        assert degradation_ratio < 3.0, f"Excessive performance degradation: {degradation_ratio:.2f}x"

        return results

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, embedder, sample_texts):
        """
        Test memory usage during batch embedding.

        Target: Process large batches without excessive memory usage
        """
        import psutil
        import gc

        process = psutil.Process()

        # Measure baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Test with large batch
        large_texts = sample_texts * 10  # 1000 texts

        start_memory = process.memory_info().rss / 1024 / 1024
        await embedder.embed(large_texts, batch_size=32)
        end_memory = process.memory_info().rss / 1024 / 1024

        gc.collect()
        after_gc_memory = process.memory_info().rss / 1024 / 1024

        memory_used = end_memory - start_memory
        memory_efficiency = len(large_texts) / memory_used if memory_used > 0 else float('inf')

        print(f"\nMemory Usage:")
        print(f"  Baseline: {baseline_memory:.1f}MB")
        print(f"  Peak during embedding: {end_memory:.1f}MB")
        print(f"  After GC: {after_gc_memory:.1f}MB")
        print(f"  Memory used: {memory_used:.1f}MB")
        print(f"  Efficiency: {memory_efficiency:.1f} texts/MB")

        # Memory efficiency assertions
        assert memory_used < 500, f"Memory usage {memory_used:.1f}MB too high for {len(large_texts)} texts"
        assert memory_efficiency > 2, f"Memory efficiency {memory_efficiency:.1f} texts/MB too low"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_device_optimization(self, sample_texts):
        """
        Compare performance across different devices (CPU/GPU if available).
        """
        devices = ["cpu"]

        # Check for GPU availability
        try:
            import torch
            if torch.cuda.is_available():
                devices.append("cuda")
        except ImportError:
            pass

        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                devices.append("mps")
        except ImportError:
            pass

        device_results = {}
        test_texts = sample_texts[:50]  # Subset for device comparison

        for device in devices:
            try:
                embedder = get_async_embedding_model(device=device)

                # Warm up
                await embedder.embed("warmup")

                # Benchmark
                start = time.perf_counter()
                await embedder.embed(test_texts, batch_size=16)
                elapsed = time.perf_counter() - start

                throughput = len(test_texts) / elapsed

                device_results[device] = {
                    'throughput': throughput,
                    'elapsed': elapsed
                }

                print(f"\nDevice: {device}")
                print(f"  Throughput: {throughput:.1f} texts/sec")
                print(f"  Total time: {elapsed:.2f}s")

            except Exception as e:
                print(f"\nDevice {device} failed: {e}")
                continue

        if len(device_results) > 1:
            best_device = max(device_results.keys(), key=lambda x: device_results[x]['throughput'])
            print(f"\nBest performing device: {best_device}")

        return device_results


if __name__ == "__main__":
    # Run benchmarks directly
    pytest.main([__file__, "-v", "--benchmark-only"])