#!/usr/bin/env python3
"""
Service 6 Performance and Load Testing Framework
===============================================

Comprehensive performance testing for Service 6's critical business operations:

Performance Requirements Tested:
1. Lead Analysis Throughput: >10 leads/second sustained
2. Real-time Scoring Latency: <200ms p95, <500ms p99
3. Webhook Processing: >50 webhooks/minute with <2s response
4. Database Operations: <100ms for CRUD, <1s for analytics
5. Memory Usage: <2GB under normal load, <4GB under peak
6. CPU Utilization: <70% average, <90% peak

Load Testing Scenarios:
- Sustained Load: 1000 leads over 10 minutes
- Burst Load: 100 leads in 30 seconds
- Stress Test: 2x normal capacity
- Endurance Test: 24-hour continuous operation
- Failure Recovery: Performance after system failures

Business Impact Metrics:
- Lead-to-Response Time: <2 minutes for high-intent leads
- System Availability: 99.9% uptime requirement
- Data Consistency: 100% under all load conditions
- User Experience: <3s dashboard load times
"""

import asyncio
import gc
import json
import statistics
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import psutil
import pytest

from ghl_real_estate_ai.services.autonomous_followup_engine import AutonomousFollowUpEngine
from ghl_real_estate_ai.services.database_service import DatabaseService

# Import Service 6 components for performance testing
from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6AIConfig,
    Service6AIOrchestrator,
    Service6AIResponse,
)
from tests.fixtures.sample_data import LeadProfiles

# Import test utilities
from tests.mocks.external_services import (

    MockClaudeClient,
    MockDatabaseService,
    MockRedisClient,
    create_mock_service6_response,
    create_test_lead_data,
)


class PerformanceMetrics:
    """Performance metrics collection and analysis"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all metrics for new test"""
        self.response_times = []
        self.throughput_samples = []
        self.error_count = 0
        self.success_count = 0
        self.memory_usage = []
        self.cpu_usage = []
        self.start_time = None
        self.end_time = None

    def start_measurement(self):
        """Start performance measurement"""
        self.start_time = time.time()
        self._start_system_monitoring()

    def end_measurement(self):
        """End performance measurement"""
        self.end_time = time.time()
        self._stop_system_monitoring()

    def record_operation(self, start_time: float, end_time: float, success: bool = True):
        """Record individual operation performance"""
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        self.response_times.append(response_time)

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def record_throughput_sample(self, operations_count: int, time_window: float):
        """Record throughput sample (operations per second)"""
        throughput = operations_count / time_window
        self.throughput_samples.append(throughput)

    def _start_system_monitoring(self):
        """Start monitoring system resources"""
        self._monitor_resources = True
        self._monitoring_thread = threading.Thread(target=self._monitor_system_resources)
        self._monitoring_thread.start()

    def _stop_system_monitoring(self):
        """Stop monitoring system resources"""
        self._monitor_resources = False
        if hasattr(self, "_monitoring_thread"):
            self._monitoring_thread.join()

    def _monitor_system_resources(self):
        """Monitor CPU and memory usage"""
        while getattr(self, "_monitor_resources", False):
            self.cpu_usage.append(psutil.cpu_percent(interval=0.1))
            self.memory_usage.append(psutil.Process().memory_info().rss / 1024 / 1024)  # MB
            time.sleep(1)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.response_times:
            return {"error": "No data collected"}

        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0

        return {
            "response_times": {
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": self._percentile(self.response_times, 95),
                "p99": self._percentile(self.response_times, 99),
                "min": min(self.response_times),
                "max": max(self.response_times),
                "std_dev": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0,
            },
            "throughput": {
                "mean_ops_per_sec": statistics.mean(self.throughput_samples) if self.throughput_samples else 0,
                "peak_ops_per_sec": max(self.throughput_samples) if self.throughput_samples else 0,
            },
            "reliability": {
                "success_count": self.success_count,
                "error_count": self.error_count,
                "success_rate": self.success_count / (self.success_count + self.error_count)
                if (self.success_count + self.error_count) > 0
                else 0,
                "total_operations": self.success_count + self.error_count,
            },
            "system_resources": {
                "avg_memory_mb": statistics.mean(self.memory_usage) if self.memory_usage else 0,
                "peak_memory_mb": max(self.memory_usage) if self.memory_usage else 0,
                "avg_cpu_percent": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                "peak_cpu_percent": max(self.cpu_usage) if self.cpu_usage else 0,
            },
            "duration": {"total_seconds": total_time, "total_minutes": total_time / 60},
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class TestLeadAnalysisPerformance:
    """Test lead analysis performance under various loads"""

    @pytest.fixture
    async def performance_orchestrator(self):
        """Create high-performance orchestrator for testing"""
        config = Service6AIConfig(
            max_concurrent_operations=200,
            default_cache_ttl_seconds=300,
            enable_advanced_ml_scoring=True,
            enable_predictive_analytics=True,
            enable_realtime_inference=True,
        )

        orchestrator = Service6AIOrchestrator(config)

        # Mock AI companion with realistic latencies
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()

        async def mock_analysis(lead_id, lead_data, **kwargs):
            # Simulate realistic AI processing time (50-200ms)
            await asyncio.sleep(0.05 + (hash(lead_id) % 150) / 1000)
            return create_mock_service6_response(lead_id)

        orchestrator.ai_companion.comprehensive_lead_analysis = mock_analysis

        await orchestrator.initialize()
        return orchestrator

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sustained_lead_analysis_throughput(self, performance_orchestrator):
        """Test sustained lead analysis throughput: >10 leads/second"""
        metrics = PerformanceMetrics()
        metrics.start_measurement()

        # Generate test leads
        test_leads = []
        for i in range(100):  # 100 leads for sustained test
            lead_data = create_test_lead_data({"lead_id": f"PERF_LEAD_{i:03d}", "email": f"perf{i}@example.com"})
            test_leads.append((lead_data["lead_id"], lead_data))

        # Process leads with controlled concurrency
        semaphore = asyncio.Semaphore(20)  # Limit concurrent operations

        async def process_lead_with_timing(lead_id, lead_data):
            async with semaphore:
                start_time = time.time()
                try:
                    result = await performance_orchestrator.analyze_lead(lead_id, lead_data)
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=True)
                    return result
                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    raise e

        # Execute sustained load test
        start_time = time.time()
        tasks = [process_lead_with_timing(lead_id, lead_data) for lead_id, lead_data in test_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        metrics.end_measurement()

        # Calculate throughput
        total_time = end_time - start_time
        throughput = len(test_leads) / total_time
        metrics.record_throughput_sample(len(test_leads), total_time)

        # Validate performance requirements
        summary = metrics.get_summary()

        assert throughput >= 10.0, f"Throughput {throughput:.2f} leads/sec should be >=10/sec"
        assert summary["response_times"]["p95"] <= 300, (
            f"P95 latency {summary['response_times']['p95']:.1f}ms should be <=300ms"
        )
        assert summary["reliability"]["success_rate"] >= 0.99, (
            f"Success rate {summary['reliability']['success_rate']:.3f} should be >=99%"
        )

        # Verify system resource usage
        assert summary["system_resources"]["peak_memory_mb"] <= 2048, "Peak memory should be <=2GB"
        assert summary["system_resources"]["avg_cpu_percent"] <= 70, "Average CPU should be <=70%"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_burst_load_handling(self, performance_orchestrator):
        """Test burst load handling: 100 leads in 30 seconds"""
        metrics = PerformanceMetrics()

        # Generate burst of leads
        burst_leads = []
        for i in range(100):
            lead_data = create_test_lead_data(
                {
                    "lead_id": f"BURST_LEAD_{i:03d}",
                    "email": f"burst{i}@example.com",
                    "priority": "high",  # High priority burst
                }
            )
            burst_leads.append((lead_data["lead_id"], lead_data))

        metrics.start_measurement()

        # Execute burst load (all at once)
        async def process_burst_lead(lead_id, lead_data):
            start_time = time.time()
            try:
                result = await performance_orchestrator.analyze_lead(lead_id, lead_data)
                end_time = time.time()
                metrics.record_operation(start_time, end_time, success=True)
                return result
            except Exception as e:
                end_time = time.time()
                metrics.record_operation(start_time, end_time, success=False)
                raise e

        start_time = time.time()
        tasks = [process_burst_lead(lead_id, lead_data) for lead_id, lead_data in burst_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        metrics.end_measurement()

        # Validate burst handling
        total_time = end_time - start_time
        summary = metrics.get_summary()

        assert total_time <= 35.0, f"Burst processing took {total_time:.1f}s, should be <=35s"
        assert summary["reliability"]["success_rate"] >= 0.95, "Burst success rate should be >=95%"
        assert summary["response_times"]["p99"] <= 1000, "P99 latency during burst should be <=1000ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_real_time_scoring_latency(self, performance_orchestrator):
        """Test real-time scoring latency: <200ms p95, <500ms p99"""
        metrics = PerformanceMetrics()

        # Mock real-time scoring with realistic latencies
        async def mock_realtime_scoring(lead_id, features, priority="normal"):
            # Simulate optimized real-time processing (10-100ms)
            await asyncio.sleep(0.01 + (hash(lead_id) % 90) / 1000)

            from ghl_real_estate_ai.services.service6_ai_integration import InferenceResponse

            return InferenceResponse(
                request_id=f"rt_{int(time.time() * 1000)}",
                lead_id=lead_id,
                model_id="realtime_scorer",
                model_version="1.0",
                scores={"primary": 85.5},
                primary_score=85.5,
                confidence=0.92,
                prediction_class="high_value",
                feature_importance=None,
                reasoning=["High engagement"],
                risk_factors=[],
                opportunities=["Quick timeline"],
                processed_at=datetime.now(),
                processing_time_ms=50.0,
                model_latency_ms=25.0,
                cache_hit=False,
                data_quality_score=0.95,
                prediction_uncertainty=0.08,
                requires_human_review=False,
            )

        performance_orchestrator.ai_companion.realtime_lead_scoring = mock_realtime_scoring

        metrics.start_measurement()

        # Test real-time scoring under load
        scoring_tasks = []
        for i in range(500):  # 500 real-time scoring requests
            features = {
                "email_open_rate": 0.75 + (i % 25) / 100,
                "response_time_hours": 1.0 + (i % 10) / 10,
                "budget": 500000 + (i % 200000),
            }

            async def score_with_timing(lead_id, features):
                start_time = time.time()
                try:
                    result = await performance_orchestrator.score_lead_realtime(lead_id, features)
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=True)
                    return result
                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    raise e

            task = score_with_timing(f"RT_LEAD_{i:03d}", features)
            scoring_tasks.append(task)

        # Execute real-time scoring tests
        results = await asyncio.gather(*scoring_tasks, return_exceptions=True)

        metrics.end_measurement()
        summary = metrics.get_summary()

        # Validate real-time scoring performance
        assert summary["response_times"]["p95"] <= 200, (
            f"RT scoring P95 {summary['response_times']['p95']:.1f}ms should be <=200ms"
        )
        assert summary["response_times"]["p99"] <= 500, (
            f"RT scoring P99 {summary['response_times']['p99']:.1f}ms should be <=500ms"
        )
        assert summary["response_times"]["mean"] <= 100, (
            f"RT scoring mean {summary['response_times']['mean']:.1f}ms should be <=100ms"
        )
        assert summary["reliability"]["success_rate"] >= 0.999, "RT scoring should have 99.9% success rate"

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_endurance_performance(self, performance_orchestrator):
        """Test endurance performance: 2-hour continuous operation"""
        metrics = PerformanceMetrics()

        # Endurance test parameters
        test_duration_seconds = 30  # Shortened for CI/CD (normally would be 7200 = 2 hours)
        leads_per_minute = 10
        total_expected_leads = int((test_duration_seconds / 60) * leads_per_minute)

        metrics.start_measurement()

        processed_leads = []
        start_time = time.time()

        # Continuous lead processing simulation
        while (time.time() - start_time) < test_duration_seconds:
            batch_start = time.time()

            # Process batch of leads
            batch_tasks = []
            for i in range(leads_per_minute):
                lead_data = create_test_lead_data(
                    {
                        "lead_id": f"ENDURANCE_LEAD_{int(time.time())}_{i}",
                        "email": f"endurance_{int(time.time())}_{i}@example.com",
                    }
                )

                async def process_endurance_lead(lead_id, lead_data):
                    op_start = time.time()
                    try:
                        result = await performance_orchestrator.analyze_lead(lead_id, lead_data)
                        op_end = time.time()
                        metrics.record_operation(op_start, op_end, success=True)
                        return result
                    except Exception as e:
                        op_end = time.time()
                        metrics.record_operation(op_start, op_end, success=False)
                        return None

                task = process_endurance_lead(lead_data["lead_id"], lead_data)
                batch_tasks.append(task)

            # Process batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            processed_leads.extend([r for r in batch_results if r is not None])

            # Maintain target rate (sleep if processing was too fast)
            batch_duration = time.time() - batch_start
            if batch_duration < 60:  # If batch took less than 1 minute
                await asyncio.sleep(60 - batch_duration)

        metrics.end_measurement()
        summary = metrics.get_summary()

        # Validate endurance performance
        assert len(processed_leads) >= total_expected_leads * 0.9, "Should process >=90% of expected leads"
        assert summary["reliability"]["success_rate"] >= 0.95, "Endurance success rate should be >=95%"

        # Performance should not degrade significantly over time
        early_response_times = metrics.response_times[: len(metrics.response_times) // 3]
        late_response_times = metrics.response_times[2 * len(metrics.response_times) // 3 :]

        if early_response_times and late_response_times:
            early_avg = statistics.mean(early_response_times)
            late_avg = statistics.mean(late_response_times)
            degradation_ratio = late_avg / early_avg

            assert degradation_ratio <= 1.5, f"Performance degradation {degradation_ratio:.2f}x should be <=1.5x"


class TestDatabasePerformance:
    """Test database performance under load"""

    @pytest.fixture
    async def performance_database(self):
        """Create database service for performance testing"""
        db_service = MockDatabaseService()

        # Simulate realistic database latencies
        original_save_lead = db_service.save_lead
        original_get_lead = db_service.get_lead
        original_update_lead_score = db_service.update_lead_score

        async def timed_save_lead(*args, **kwargs):
            await asyncio.sleep(0.01 + (hash(str(args)) % 50) / 1000)  # 10-60ms
            return await original_save_lead(*args, **kwargs)

        async def timed_get_lead(*args, **kwargs):
            await asyncio.sleep(0.005 + (hash(str(args)) % 25) / 1000)  # 5-30ms
            return await original_get_lead(*args, **kwargs)

        async def timed_update_score(*args, **kwargs):
            await asyncio.sleep(0.015 + (hash(str(args)) % 35) / 1000)  # 15-50ms
            return await original_update_lead_score(*args, **kwargs)

        db_service.save_lead = timed_save_lead
        db_service.get_lead = timed_get_lead
        db_service.update_lead_score = timed_update_score

        return db_service

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_crud_performance(self, performance_database):
        """Test database CRUD operations performance: <100ms average"""
        metrics = PerformanceMetrics()
        metrics.start_measurement()

        # Test CREATE operations
        create_tasks = []
        for i in range(200):
            lead_data = create_test_lead_data({"lead_id": f"DB_PERF_LEAD_{i:03d}", "email": f"dbperf{i}@example.com"})

            async def create_with_timing(lead_id, lead_data):
                start_time = time.time()
                try:
                    result = await performance_database.save_lead(lead_id, lead_data)
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=result)
                    return result
                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    raise e

            task = create_with_timing(lead_data["lead_id"], lead_data)
            create_tasks.append(task)

        # Execute CREATE operations
        create_results = await asyncio.gather(*create_tasks)

        # Test READ operations
        read_tasks = []
        for i in range(200):
            lead_id = f"DB_PERF_LEAD_{i:03d}"

            async def read_with_timing(lead_id):
                start_time = time.time()
                try:
                    result = await performance_database.get_lead(lead_id)
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=result is not None)
                    return result
                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    raise e

            task = read_with_timing(lead_id)
            read_tasks.append(task)

        # Execute READ operations
        read_results = await asyncio.gather(*read_tasks)

        # Test UPDATE operations
        update_tasks = []
        for i in range(200):
            lead_id = f"DB_PERF_LEAD_{i:03d}"
            score = 70.0 + (i % 30)

            async def update_with_timing(lead_id, score):
                start_time = time.time()
                try:
                    result = await performance_database.update_lead_score(lead_id, score, {"test": "performance_test"})
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=result)
                    return result
                except Exception as e:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    raise e

            task = update_with_timing(lead_id, score)
            update_tasks.append(task)

        # Execute UPDATE operations
        update_results = await asyncio.gather(*update_tasks)

        metrics.end_measurement()
        summary = metrics.get_summary()

        # Validate database performance
        assert summary["response_times"]["mean"] <= 100, (
            f"DB avg latency {summary['response_times']['mean']:.1f}ms should be <=100ms"
        )
        assert summary["response_times"]["p95"] <= 200, (
            f"DB P95 latency {summary['response_times']['p95']:.1f}ms should be <=200ms"
        )
        assert summary["reliability"]["success_rate"] >= 0.99, "DB operations should have 99% success rate"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, performance_database):
        """Test database performance under high concurrency"""
        metrics = PerformanceMetrics()
        metrics.start_measurement()

        # Simulate mixed workload with high concurrency
        all_tasks = []

        # 50% READ operations
        for i in range(100):

            async def concurrent_read(lead_id):
                start_time = time.time()
                try:
                    result = await performance_database.get_lead(lead_id)
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=True)
                    return result
                except Exception:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    return None

            task = concurrent_read(f"CONCURRENT_LEAD_{i % 20:03d}")  # Access subset of leads
            all_tasks.append(task)

        # 30% WRITE operations
        for i in range(60):
            lead_data = create_test_lead_data(
                {"lead_id": f"CONCURRENT_NEW_{i:03d}", "email": f"concurrent{i}@example.com"}
            )

            async def concurrent_write(lead_id, lead_data):
                start_time = time.time()
                try:
                    result = await performance_database.save_lead(lead_id, lead_data)
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=result)
                    return result
                except Exception:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    return None

            task = concurrent_write(lead_data["lead_id"], lead_data)
            all_tasks.append(task)

        # 20% UPDATE operations
        for i in range(40):

            async def concurrent_update(lead_id, score):
                start_time = time.time()
                try:
                    result = await performance_database.update_lead_score(lead_id, score, {"concurrent_test": True})
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=result)
                    return result
                except Exception:
                    end_time = time.time()
                    metrics.record_operation(start_time, end_time, success=False)
                    return None

            task = concurrent_update(f"CONCURRENT_LEAD_{i % 20:03d}", 80.0 + i)
            all_tasks.append(task)

        # Execute all operations concurrently
        start_time = time.time()
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        end_time = time.time()

        metrics.end_measurement()
        summary = metrics.get_summary()

        # Calculate concurrent throughput
        total_ops = len(all_tasks)
        total_time = end_time - start_time
        concurrent_throughput = total_ops / total_time

        # Validate concurrent database performance
        assert concurrent_throughput >= 50, (
            f"Concurrent DB throughput {concurrent_throughput:.1f} ops/sec should be >=50/sec"
        )
        assert summary["response_times"]["p95"] <= 250, (
            f"Concurrent DB P95 {summary['response_times']['p95']:.1f}ms should be <=250ms"
        )
        assert summary["reliability"]["success_rate"] >= 0.95, "Concurrent DB success rate should be >=95%"


class TestMemoryAndResourceManagement:
    """Test memory usage and resource management"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage remains within limits under load"""
        # Monitor memory before test
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create service with memory monitoring
        config = Service6AIConfig(max_concurrent_operations=100)
        orchestrator = Service6AIOrchestrator(config)

        # Mock AI companion
        orchestrator.ai_companion = MagicMock()
        orchestrator.ai_companion.initialize = AsyncMock()
        orchestrator.ai_companion.comprehensive_lead_analysis = AsyncMock(
            side_effect=lambda lead_id, data, **kwargs: create_mock_service6_response(lead_id)
        )

        await orchestrator.initialize()

        # Process large number of leads to test memory usage
        memory_samples = []
        lead_count = 500

        for batch in range(10):  # 10 batches of 50 leads each
            batch_tasks = []

            for i in range(50):
                lead_data = create_test_lead_data(
                    {
                        "lead_id": f"MEMORY_TEST_BATCH_{batch}_LEAD_{i:03d}",
                        "email": f"memory_test_{batch}_{i}@example.com",
                    }
                )

                task = orchestrator.analyze_lead(lead_data["lead_id"], lead_data)
                batch_tasks.append(task)

            # Process batch and measure memory
            await asyncio.gather(*batch_tasks)

            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)

            # Force garbage collection
            gc.collect()

            # Small delay between batches
            await asyncio.sleep(0.1)

        # Analyze memory usage
        peak_memory = max(memory_samples)
        avg_memory = statistics.mean(memory_samples)
        memory_growth = memory_samples[-1] - memory_samples[0]

        # Memory usage validation
        assert peak_memory <= 2048, f"Peak memory {peak_memory:.1f}MB should be <=2048MB"
        assert avg_memory <= 1536, f"Average memory {avg_memory:.1f}MB should be <=1536MB"
        assert memory_growth <= 500, f"Memory growth {memory_growth:.1f}MB should be <=500MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_garbage_collection_efficiency(self):
        """Test garbage collection efficiency"""
        import gc

        # Enable garbage collection monitoring
        gc.set_debug(gc.DEBUG_STATS)

        # Initial garbage collection
        initial_objects = len(gc.get_objects())
        gc.collect()

        # Create and process leads that should be garbage collected
        for round_num in range(5):
            temp_leads = []

            # Create temporary lead objects
            for i in range(100):
                lead_data = create_test_lead_data(
                    {
                        "lead_id": f"GC_TEST_ROUND_{round_num}_LEAD_{i:03d}",
                        "email": f"gc_test_{round_num}_{i}@example.com",
                        "large_data": "x" * 10000,  # 10KB of data per lead
                    }
                )
                temp_leads.append(lead_data)

            # Process leads (simulated)
            for lead in temp_leads:
                # Simulate processing
                result = create_mock_service6_response(lead["lead_id"])
                # Result goes out of scope
                del result

            # Clear references
            del temp_leads

            # Force garbage collection
            collected = gc.collect()

            # Measure objects after collection
            current_objects = len(gc.get_objects())

        # Validate garbage collection efficiency
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Object count should not grow excessively
        assert object_growth <= 1000, f"Object growth {object_growth} should be <=1000 objects"

        # Disable debug mode
        gc.set_debug(0)


# Test configuration
pytest_plugins = ["pytest_asyncio"]

# Performance test markers
pytestmark = pytest.mark.performance


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "-m",
            "performance",
            "--cov=ghl_real_estate_ai.services",
            "--cov-report=html",
            "--cov-report=term-missing",
        ]
    )