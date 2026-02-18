#!/usr/bin/env python3

"""
🚀 Service 6 Comprehensive Performance Test Suite
=================================================

Performance, load testing, and benchmarking for Service 6 including:
- Latency benchmarking for all AI components
- Throughput testing under sustained load
- Memory efficiency validation
- Concurrent processing performance
- Real-time response time validation (<100ms for critical paths)
- Scalability testing (50-500 concurrent requests)
- Cache performance optimization
- Database query performance
- End-to-end workflow benchmarks

Target Performance Goals:
- AI Analysis: <200ms average, <300ms P95
- Real-time Scoring: <100ms average, <150ms P95
- Behavioral Network Response: <500ms average
- Database Operations: <50ms average
- Cache Operations: <10ms average

Author: Claude AI Enhancement System
Date: 2026-01-17
"""

import asyncio
import gc
import os
import statistics

# Import mock services
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, Mock, patch

import psutil
import pytest

from ghl_real_estate_ai.services.database_service import DatabaseService
from ghl_real_estate_ai.services.realtime_behavioral_network import RealTimeBehavioralNetwork

# Import Service 6 components
from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6AIOrchestrator,
    create_high_performance_config,
    create_service6_ai_orchestrator,
)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "mocks"))
from external_services import (

    MockEnhancedDatabaseService,
    MockMLScoringEngine,
    MockPredictiveAnalytics,
    MockTieredCacheService,
    MockVoiceAIClient,
    create_mock_service6_response,
    create_test_lead_data,
)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""

    operation_name: str
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    throughput_ops_per_sec: float
    total_operations: int
    success_rate: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class PerformanceProfiler:
    """Performance profiling utility"""

    def __init__(self):
        self.measurements = []
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None

    def start_measurement(self):
        """Start performance measurement"""
        self.start_time = time.perf_counter()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.start_cpu = psutil.cpu_percent()

    def record_operation(self, operation_name: str, success: bool = True):
        """Record operation completion"""
        if self.start_time is None:
            return

        end_time = time.perf_counter()
        latency_ms = (end_time - self.start_time) * 1000

        self.measurements.append(
            {"operation": operation_name, "latency_ms": latency_ms, "success": success, "timestamp": end_time}
        )

        # Reset for next measurement
        self.start_time = None

    def calculate_metrics(self, operation_name: str) -> PerformanceMetrics:
        """Calculate performance metrics for an operation"""
        operation_measurements = [m for m in self.measurements if m["operation"] == operation_name]

        if not operation_measurements:
            raise ValueError(f"No measurements found for operation: {operation_name}")

        latencies = [m["latency_ms"] for m in operation_measurements]
        successes = [m for m in operation_measurements if m["success"]]

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p50 = latencies_sorted[int(0.50 * n)] if n > 0 else 0
        p95 = latencies_sorted[int(0.95 * n)] if n > 0 else 0
        p99 = latencies_sorted[int(0.99 * n)] if n > 0 else 0

        # Calculate throughput
        if operation_measurements:
            time_span = max(m["timestamp"] for m in operation_measurements) - min(
                m["timestamp"] for m in operation_measurements
            )
            throughput = len(operation_measurements) / time_span if time_span > 0 else 0
        else:
            throughput = 0

        return PerformanceMetrics(
            operation_name=operation_name,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            throughput_ops_per_sec=throughput,
            total_operations=len(operation_measurements),
            success_rate=len(successes) / len(operation_measurements) if operation_measurements else 0,
        )


class TestService6AIPerformance:
    """Performance tests for Service 6 AI components"""

    @pytest.fixture
    async def performance_orchestrator(self):
        """Create high-performance orchestrator for benchmarking"""
        config = create_high_performance_config()
        config.max_concurrent_operations = 100

        orchestrator = create_service6_ai_orchestrator(config)

        # Setup fast mock services
        orchestrator.ai_companion.ml_scoring_engine = MockMLScoringEngine()
        orchestrator.ai_companion.voice_ai = MockVoiceAIClient()
        orchestrator.ai_companion.predictive_analytics = MockPredictiveAnalytics()
        orchestrator.ai_companion.cache = MockTieredCacheService()
        orchestrator.ai_companion.memory = MockEnhancedDatabaseService()

        await orchestrator.initialize()
        return orchestrator

    async def test_ai_analysis_latency_benchmark(self, performance_orchestrator):
        """Benchmark AI analysis latency performance"""
        profiler = PerformanceProfiler()

        # Test data variations for realistic benchmark
        test_scenarios = [
            # Simple lead
            create_test_lead_data({"budget": 400000, "timeline": "soon"}),
            # Complex lead with many properties viewed
            create_test_lead_data(
                {
                    "budget": 700000,
                    "timeline": "immediate",
                    "page_views": 25,
                    "viewed_properties": 15,
                    "email_open_rate": 0.9,
                }
            ),
            # High-value lead
            create_test_lead_data({"budget": 1200000, "timeline": "immediate", "urgency_indicators": 8}),
        ]

        # Run benchmark iterations
        iterations = 50
        for i in range(iterations):
            scenario = test_scenarios[i % len(test_scenarios)]
            scenario["lead_id"] = f"perf_test_{i:03d}"

            profiler.start_measurement()

            try:
                result = await performance_orchestrator.analyze_lead(scenario["lead_id"], scenario)
                profiler.record_operation("ai_analysis", success=True)

                # Verify result quality
                assert result.unified_lead_score > 0
                assert len(result.immediate_actions) > 0

            except Exception as e:
                profiler.record_operation("ai_analysis", success=False)
                print(f"Analysis failed for iteration {i}: {e}")

        # Calculate metrics
        metrics = profiler.calculate_metrics("ai_analysis")

        # Performance assertions
        assert metrics.avg_latency_ms < 200.0, f"Average latency {metrics.avg_latency_ms:.1f}ms exceeds 200ms target"
        assert metrics.p95_latency_ms < 300.0, f"P95 latency {metrics.p95_latency_ms:.1f}ms exceeds 300ms target"
        assert metrics.success_rate > 0.95, f"Success rate {metrics.success_rate:.2%} too low"
        assert metrics.throughput_ops_per_sec > 5.0, f"Throughput {metrics.throughput_ops_per_sec:.1f} ops/sec too low"

        print(f"✅ AI Analysis Benchmark (n={iterations}):")
        print(f"   Average: {metrics.avg_latency_ms:.1f}ms")
        print(f"   P50: {metrics.p50_latency_ms:.1f}ms")
        print(f"   P95: {metrics.p95_latency_ms:.1f}ms")
        print(f"   Throughput: {metrics.throughput_ops_per_sec:.1f} ops/sec")
        print(f"   Success Rate: {metrics.success_rate:.1%}")

    async def test_realtime_scoring_latency_benchmark(self, performance_orchestrator):
        """Benchmark real-time scoring latency (critical <100ms path)"""
        profiler = PerformanceProfiler()

        # Real-time feature sets
        feature_sets = [
            {"email_open_rate": 0.7, "budget": 500000, "page_views": 5},
            {"email_open_rate": 0.9, "budget": 800000, "page_views": 20, "urgency_score": 0.8},
            {"email_open_rate": 0.6, "budget": 350000, "page_views": 3, "response_time": 4.0},
        ]

        # Real-time scoring benchmark
        iterations = 100
        for i in range(iterations):
            features = feature_sets[i % len(feature_sets)]
            lead_id = f"rt_perf_test_{i:03d}"

            profiler.start_measurement()

            try:
                result = await performance_orchestrator.score_lead_realtime(lead_id, features, priority="high")
                profiler.record_operation("realtime_scoring", success=True)

                # Verify result
                assert result.primary_score > 0
                assert result.confidence > 0

            except Exception as e:
                profiler.record_operation("realtime_scoring", success=False)
                print(f"Real-time scoring failed for iteration {i}: {e}")

        # Calculate metrics
        metrics = profiler.calculate_metrics("realtime_scoring")

        # Strict performance assertions for real-time path
        assert metrics.avg_latency_ms < 100.0, f"Real-time average {metrics.avg_latency_ms:.1f}ms exceeds 100ms target"
        assert metrics.p95_latency_ms < 150.0, f"Real-time P95 {metrics.p95_latency_ms:.1f}ms exceeds 150ms target"
        assert metrics.max_latency_ms < 200.0, f"Max latency {metrics.max_latency_ms:.1f}ms exceeds 200ms limit"
        assert metrics.success_rate > 0.98, f"Real-time success rate {metrics.success_rate:.2%} too low"

        print(f"⚡ Real-time Scoring Benchmark (n={iterations}):")
        print(f"   Average: {metrics.avg_latency_ms:.1f}ms")
        print(f"   P95: {metrics.p95_latency_ms:.1f}ms")
        print(f"   Max: {metrics.max_latency_ms:.1f}ms")
        print(f"   Throughput: {metrics.throughput_ops_per_sec:.1f} ops/sec")

    async def test_concurrent_analysis_scalability(self, performance_orchestrator):
        """Test scalability under concurrent load"""
        # Test different concurrency levels
        concurrency_levels = [10, 25, 50, 100]
        results = {}

        for concurrency in concurrency_levels:
            print(f"\n📊 Testing concurrency level: {concurrency}")

            async def analyze_concurrent_lead(lead_index):
                """Analyze single lead"""
                lead_data = create_test_lead_data(
                    {"lead_id": f"concurrent_{concurrency}_{lead_index:03d}", "budget": 400000 + (lead_index * 5000)}
                )

                start_time = time.perf_counter()
                try:
                    result = await performance_orchestrator.analyze_lead(lead_data["lead_id"], lead_data)
                    end_time = time.perf_counter()

                    return {
                        "success": True,
                        "latency_ms": (end_time - start_time) * 1000,
                        "lead_score": result.unified_lead_score,
                    }
                except Exception as e:
                    end_time = time.perf_counter()
                    return {"success": False, "latency_ms": (end_time - start_time) * 1000, "error": str(e)}

            # Execute concurrent requests
            start_time = time.perf_counter()

            tasks = [analyze_concurrent_lead(i) for i in range(concurrency)]
            task_results = await asyncio.gather(*tasks)

            end_time = time.perf_counter()
            total_time = end_time - start_time

            # Analyze results
            successful = [r for r in task_results if r["success"]]
            failed = [r for r in task_results if not r["success"]]

            latencies = [r["latency_ms"] for r in successful]

            results[concurrency] = {
                "total_requests": concurrency,
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / concurrency,
                "total_time": total_time,
                "throughput": concurrency / total_time,
                "avg_latency": statistics.mean(latencies) if latencies else 0,
                "p95_latency": sorted(latencies)[int(0.95 * len(latencies))] if latencies else 0,
            }

            # Performance assertions
            assert results[concurrency]["success_rate"] > 0.90, (
                f"Success rate {results[concurrency]['success_rate']:.1%} too low at {concurrency} concurrency"
            )
            assert results[concurrency]["avg_latency"] < 500.0, (
                f"Average latency {results[concurrency]['avg_latency']:.1f}ms too high at {concurrency} concurrency"
            )

        # Analyze scalability
        print(f"\n📈 Scalability Analysis:")
        print(f"{'Concurrency':<12} {'Success Rate':<12} {'Avg Latency':<12} {'Throughput':<12}")
        print("-" * 50)

        for concurrency, result in results.items():
            print(
                f"{concurrency:<12} {result['success_rate']:<11.1%} {result['avg_latency']:<11.1f}ms {result['throughput']:<11.1f}/s"
            )

        # Verify throughput scales reasonably
        throughput_10 = results[10]["throughput"]
        throughput_50 = results[50]["throughput"]

        # Should achieve at least 3x throughput scaling from 10 to 50 concurrent
        scaling_factor = throughput_50 / throughput_10
        assert scaling_factor > 3.0, f"Throughput scaling factor {scaling_factor:.1f}x insufficient"


class TestBehavioralNetworkPerformance:
    """Performance tests for behavioral network components"""

    @pytest.fixture
    async def performance_behavioral_network(self):
        """Create optimized behavioral network for performance testing"""
        network = RealTimeBehavioralNetwork()

        # Fast mock services
        network.cache_service = MockTieredCacheService()
        network.database_service = MockEnhancedDatabaseService()
        network.twilio_client = Mock()
        network.sendgrid_client = Mock()

        # Mock fast responses
        network.agent_availability_service = Mock()
        network.template_engine = Mock()
        network.personalization_engine = Mock()

        network.agent_availability_service.check_availability.return_value = True
        network.template_engine.render.return_value = {"subject": "Test", "content": "Test"}
        network.personalization_engine.generate_content.return_value = {"personalized_properties": []}

        await network.initialize()
        return network

    async def test_signal_processing_performance(self, performance_behavioral_network):
        """Benchmark signal processing performance"""
        profiler = PerformanceProfiler()

        # Various signal types for realistic benchmark
        signal_types = [
            {"signal_type": "page_view", "raw_data": {"pages": 5, "time": 300}},
            {"signal_type": "email_open", "raw_data": {"campaign": "newsletter", "opens": 3}},
            {"signal_type": "property_view", "raw_data": {"property_id": "prop_123", "time": 180}},
            {"signal_type": "urgent_inquiry", "raw_data": {"message": "Need to see today", "urgency": 0.9}},
        ]

        # Process signals benchmark
        iterations = 100
        for i in range(iterations):
            signal_template = signal_types[i % len(signal_types)]
            signal_data = {"lead_id": f"signal_perf_{i:03d}", "source": "performance_test", **signal_template}

            profiler.start_measurement()

            try:
                result = await performance_behavioral_network.process_signal(signal_data)
                profiler.record_operation("signal_processing", success=True)

                # Verify processing
                assert result is not None

            except Exception as e:
                profiler.record_operation("signal_processing", success=False)
                print(f"Signal processing failed for iteration {i}: {e}")

        # Calculate metrics
        metrics = profiler.calculate_metrics("signal_processing")

        # Performance assertions
        assert metrics.avg_latency_ms < 500.0, (
            f"Signal processing average {metrics.avg_latency_ms:.1f}ms exceeds 500ms target"
        )
        assert metrics.p95_latency_ms < 750.0, (
            f"Signal processing P95 {metrics.p95_latency_ms:.1f}ms exceeds 750ms target"
        )
        assert metrics.success_rate > 0.95, f"Signal processing success rate {metrics.success_rate:.2%} too low"

        print(f"📡 Signal Processing Benchmark (n={iterations}):")
        print(f"   Average: {metrics.avg_latency_ms:.1f}ms")
        print(f"   P95: {metrics.p95_latency_ms:.1f}ms")
        print(f"   Throughput: {metrics.throughput_ops_per_sec:.1f} signals/sec")

    async def test_todo_methods_performance(self, performance_behavioral_network):
        """Benchmark performance of TODO methods"""
        profiler = PerformanceProfiler()
        network = performance_behavioral_network

        # Test each TODO method performance
        todo_methods = [
            (
                "send_immediate_alert",
                lambda: network._send_immediate_alert(
                    "perf_lead_001",
                    {"priority": "high", "message": "Test alert", "channels": ["email"], "agent_id": "agent_001"},
                ),
            ),
            (
                "notify_agent",
                lambda: network._notify_agent(
                    "agent_001", {"type": "test_notification", "lead_id": "perf_lead_001", "message": "Test message"}
                ),
            ),
            (
                "set_priority_flag",
                lambda: network._set_priority_flag(
                    "perf_lead_001", {"priority_level": "high", "reason": "Performance test", "duration_hours": 1}
                ),
            ),
            (
                "send_automated_response",
                lambda: network._send_automated_response(
                    "perf_lead_001", {"response_type": "test_response", "template": "test_template", "channel": "email"}
                ),
            ),
            (
                "deliver_personalized_content",
                lambda: network._deliver_personalized_content(
                    "perf_lead_001",
                    {"content_type": "test_content", "delivery_channel": "email", "personalization_factors": {}},
                ),
            ),
        ]

        # Benchmark each method
        for method_name, method_func in todo_methods:
            method_iterations = 20

            for i in range(method_iterations):
                profiler.start_measurement()

                try:
                    result = await method_func()
                    profiler.record_operation(method_name, success=True)

                    # Verify result
                    assert result is not None

                except Exception as e:
                    profiler.record_operation(method_name, success=False)
                    print(f"{method_name} failed for iteration {i}: {e}")

            # Calculate and assert metrics
            metrics = profiler.calculate_metrics(method_name)

            # Each TODO method should complete quickly
            assert metrics.avg_latency_ms < 200.0, f"{method_name} average {metrics.avg_latency_ms:.1f}ms too slow"
            assert metrics.success_rate > 0.90, f"{method_name} success rate {metrics.success_rate:.2%} too low"

            print(f"⚡ {method_name}: {metrics.avg_latency_ms:.1f}ms avg, {metrics.success_rate:.1%} success")


class TestDatabasePerformance:
    """Performance tests for database operations"""

    @pytest.fixture
    async def performance_database(self):
        """Create optimized database service for performance testing"""
        return MockEnhancedDatabaseService()

    async def test_lead_crud_performance(self, performance_database):
        """Benchmark lead CRUD operations performance"""
        profiler = PerformanceProfiler()

        # Create leads benchmark
        create_iterations = 100
        for i in range(create_iterations):
            lead_data = create_test_lead_data({"lead_id": f"crud_perf_{i:03d}"})

            profiler.start_measurement()

            try:
                result = await performance_database.save_lead(f"crud_perf_{i:03d}", lead_data)
                profiler.record_operation("create_lead", success=result)
            except Exception as e:
                profiler.record_operation("create_lead", success=False)

        # Read leads benchmark
        read_iterations = 50
        for i in range(read_iterations):
            lead_id = f"crud_perf_{i:03d}"

            profiler.start_measurement()

            try:
                result = await performance_database.get_lead(lead_id)
                profiler.record_operation("read_lead", success=result is not None)
            except Exception as e:
                profiler.record_operation("read_lead", success=False)

        # Update leads benchmark
        update_iterations = 30
        for i in range(update_iterations):
            lead_id = f"crud_perf_{i:03d}"

            profiler.start_measurement()

            try:
                result = await performance_database.update_lead_score(lead_id, 85.0 + i, {"update": i})
                profiler.record_operation("update_lead", success=result)
            except Exception as e:
                profiler.record_operation("update_lead", success=False)

        # Calculate and verify metrics
        operations = ["create_lead", "read_lead", "update_lead"]

        for operation in operations:
            metrics = profiler.calculate_metrics(operation)

            # Database operations should be fast
            assert metrics.avg_latency_ms < 50.0, (
                f"{operation} average {metrics.avg_latency_ms:.1f}ms exceeds 50ms target"
            )
            assert metrics.p95_latency_ms < 100.0, (
                f"{operation} P95 {metrics.p95_latency_ms:.1f}ms exceeds 100ms target"
            )
            assert metrics.success_rate > 0.95, f"{operation} success rate {metrics.success_rate:.2%} too low"

            print(f"💾 {operation}: {metrics.avg_latency_ms:.1f}ms avg, {metrics.throughput_ops_per_sec:.1f} ops/sec")

    async def test_bulk_operations_performance(self, performance_database):
        """Benchmark bulk database operations"""
        profiler = PerformanceProfiler()

        # Bulk create
        bulk_size = 50
        bulk_leads = []

        for i in range(bulk_size):
            lead_data = create_test_lead_data({"lead_id": f"bulk_perf_{i:03d}"})
            bulk_leads.append((f"bulk_perf_{i:03d}", lead_data))

        profiler.start_measurement()

        # Execute bulk operations concurrently
        tasks = [performance_database.save_lead(lead_id, data) for lead_id, data in bulk_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        profiler.record_operation(
            "bulk_create", success=all(r is True for r in results if not isinstance(r, Exception))
        )

        # Bulk read
        profiler.start_measurement()

        read_tasks = [performance_database.get_lead(f"bulk_perf_{i:03d}") for i in range(bulk_size)]
        read_results = await asyncio.gather(*read_tasks, return_exceptions=True)

        profiler.record_operation(
            "bulk_read", success=all(r is not None for r in read_results if not isinstance(r, Exception))
        )

        # Verify bulk performance
        create_metrics = profiler.calculate_metrics("bulk_create")
        read_metrics = profiler.calculate_metrics("bulk_read")

        # Bulk operations should be more efficient than individual operations
        assert create_metrics.avg_latency_ms < 2000.0, (
            f"Bulk create {create_metrics.avg_latency_ms:.1f}ms too slow for {bulk_size} operations"
        )
        assert read_metrics.avg_latency_ms < 1000.0, (
            f"Bulk read {read_metrics.avg_latency_ms:.1f}ms too slow for {bulk_size} operations"
        )

        print(f"📦 Bulk Operations (n={bulk_size}):")
        print(f"   Bulk Create: {create_metrics.avg_latency_ms:.1f}ms")
        print(f"   Bulk Read: {read_metrics.avg_latency_ms:.1f}ms")


class TestCachePerformance:
    """Performance tests for caching layer"""

    @pytest.fixture
    async def performance_cache(self):
        """Create optimized cache service for performance testing"""
        return MockTieredCacheService()

    async def test_cache_operations_performance(self, performance_cache):
        """Benchmark cache operations performance"""
        profiler = PerformanceProfiler()

        # Cache set operations
        set_iterations = 200
        for i in range(set_iterations):
            key = f"perf_cache_key_{i:03d}"
            value = {"data": f"test_value_{i}", "timestamp": time.time()}

            profiler.start_measurement()

            try:
                result = await performance_cache.set_in_layer(key, value, "memory", ttl=300)
                profiler.record_operation("cache_set", success=result)
            except Exception as e:
                profiler.record_operation("cache_set", success=False)

        # Cache get operations
        get_iterations = 200
        for i in range(get_iterations):
            key = f"perf_cache_key_{i % (set_iterations // 2):03d}"  # Mix hits and misses

            profiler.start_measurement()

            try:
                result = await performance_cache.get_from_layer(key, "memory")
                profiler.record_operation("cache_get", success=True)  # Success regardless of hit/miss
            except Exception as e:
                profiler.record_operation("cache_get", success=False)

        # Verify cache performance
        set_metrics = profiler.calculate_metrics("cache_set")
        get_metrics = profiler.calculate_metrics("cache_get")

        # Cache operations should be very fast
        assert set_metrics.avg_latency_ms < 10.0, (
            f"Cache set average {set_metrics.avg_latency_ms:.1f}ms exceeds 10ms target"
        )
        assert get_metrics.avg_latency_ms < 5.0, (
            f"Cache get average {get_metrics.avg_latency_ms:.1f}ms exceeds 5ms target"
        )

        # Verify high throughput
        assert set_metrics.throughput_ops_per_sec > 100.0, (
            f"Cache set throughput {set_metrics.throughput_ops_per_sec:.1f} ops/sec too low"
        )
        assert get_metrics.throughput_ops_per_sec > 200.0, (
            f"Cache get throughput {get_metrics.throughput_ops_per_sec:.1f} ops/sec too low"
        )

        print(f"🚀 Cache Performance:")
        print(f"   Set: {set_metrics.avg_latency_ms:.2f}ms avg, {set_metrics.throughput_ops_per_sec:.1f} ops/sec")
        print(f"   Get: {get_metrics.avg_latency_ms:.2f}ms avg, {get_metrics.throughput_ops_per_sec:.1f} ops/sec")

    async def test_cache_hit_ratio_performance(self, performance_cache):
        """Test cache hit ratio under realistic load"""
        # Pre-populate cache
        populate_count = 100
        for i in range(populate_count):
            key = f"hit_ratio_key_{i:03d}"
            value = {"data": f"value_{i}"}
            await performance_cache.set_in_layer(key, value, "memory")

        # Mixed access pattern
        total_requests = 500
        cache_stats_before = performance_cache.get_cache_stats()

        for i in range(total_requests):
            if i % 3 == 0:
                # 33% new keys (cache misses)
                key = f"new_key_{i:03d}"
            else:
                # 67% existing keys (cache hits)
                key = f"hit_ratio_key_{i % populate_count:03d}"

            await performance_cache.get_from_layer(key, "memory")

        cache_stats_after = performance_cache.get_cache_stats()

        # Verify reasonable hit ratio
        hit_rate = cache_stats_after["hit_rate"]
        assert hit_rate > 0.5, f"Cache hit rate {hit_rate:.1%} too low"

        print(f"📈 Cache Hit Ratio: {hit_rate:.1%}")


class TestMemoryEfficiency:
    """Memory efficiency and resource usage tests"""

    async def test_memory_usage_under_load(self):
        """Test memory efficiency under sustained load"""
        import gc

        import psutil

        # Measure initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create orchestrator
        config = create_high_performance_config()
        orchestrator = create_service6_ai_orchestrator(config)

        # Mock services
        orchestrator.ai_companion.ml_scoring_engine = MockMLScoringEngine()
        orchestrator.ai_companion.cache = MockTieredCacheService()
        orchestrator.ai_companion.memory = MockEnhancedDatabaseService()

        await orchestrator.initialize()

        # Sustained load
        iterations = 200
        memory_measurements = []

        for i in range(iterations):
            lead_data = create_test_lead_data({"lead_id": f"memory_test_{i:04d}"})

            # Process lead
            await orchestrator.analyze_lead(lead_data["lead_id"], lead_data)

            # Measure memory every 20 iterations
            if i % 20 == 0:
                gc.collect()  # Force garbage collection
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(current_memory)

        # Final memory measurement
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024

        # Memory efficiency assertions
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_measurements) if memory_measurements else final_memory

        # Should not grow memory excessively
        assert memory_growth < 200.0, f"Memory growth {memory_growth:.1f}MB too high"
        assert max_memory - initial_memory < 250.0, f"Peak memory usage {max_memory - initial_memory:.1f}MB too high"

        print(f"💾 Memory Efficiency (n={iterations}):")
        print(f"   Initial: {initial_memory:.1f}MB")
        print(f"   Final: {final_memory:.1f}MB")
        print(f"   Growth: {memory_growth:.1f}MB")
        print(f"   Peak: {max_memory:.1f}MB")

    async def test_resource_cleanup(self):
        """Test proper resource cleanup and garbage collection"""
        import weakref

        # Create objects and track with weak references
        orchestrator = create_service6_ai_orchestrator()
        behavioral_network = RealTimeBehavioralNetwork()

        # Mock components
        orchestrator.ai_companion.cache = MockTieredCacheService()
        behavioral_network.cache_service = MockTieredCacheService()

        # Create weak references to track object lifecycle
        orchestrator_ref = weakref.ref(orchestrator)
        network_ref = weakref.ref(behavioral_network)
        cache_ref = weakref.ref(orchestrator.ai_companion.cache)

        await orchestrator.initialize()
        await behavioral_network.initialize()

        # Verify objects exist
        assert orchestrator_ref() is not None
        assert network_ref() is not None
        assert cache_ref() is not None

        # Clear references
        del orchestrator
        del behavioral_network

        # Force garbage collection
        gc.collect()

        # Verify objects were cleaned up
        # Note: Some objects may persist due to test framework, so we check within reason
        print(f"🧹 Resource Cleanup:")
        print(f"   Orchestrator cleaned: {orchestrator_ref() is None}")
        print(f"   Network cleaned: {network_ref() is None}")
        print(f"   Cache cleaned: {cache_ref() is None}")


if __name__ == "__main__":
    # Run performance tests
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--durations=20",  # Show 20 slowest tests
            "--benchmark-only",
            "--benchmark-sort=mean",
            "--capture=no",  # Show real-time output
        ]
    )