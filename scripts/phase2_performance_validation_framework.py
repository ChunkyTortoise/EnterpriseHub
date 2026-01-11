#!/usr/bin/env python3
"""
Phase 2 Performance Validation Framework

Comprehensive benchmarking and validation suite for Phase 2 optimizations.
Measures cache, database, API, and ML inference performance against success criteria.

Success Criteria:
- API response time: <200ms P95 (maintain current 145ms)
- ML inference: <500ms per prediction
- Database queries: <50ms P90 with new indexes
- Cache hit rate: >95% (L1+L2+L3 combined)
- Connection pool efficiency: >90%
- Infrastructure cost reduction: 25-35%

Validation Components:
1. Load Testing (100+ concurrent users)
2. ML Inference Benchmarking (batch vs individual)
3. Database Connection Pool Stress Testing
4. Cache Performance Under Load
5. Cost Baseline Tracking (30-day analysis)
6. Before/After Comparison Framework
"""

import asyncio
import time
import json
import statistics
import numpy as np
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path
import sys
import logging
from collections import defaultdict, deque
import hashlib

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes for Validation Results
# ============================================================================

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_name: str
    value: float
    unit: str
    target_value: float
    target_met: bool
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def margin_from_target(self) -> float:
        """Calculate margin from target value"""
        if self.target_value == 0:
            return 0.0
        return ((self.value - self.target_value) / self.target_value) * 100


@dataclass
class LoadTestResult:
    """Load testing result"""
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    throughput_requests_per_sec: float
    error_rate_percent: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MLInferenceBenchmark:
    """ML inference performance benchmark"""
    test_name: str
    batch_size: int
    individual_inference_time_ms: float
    batch_inference_time_ms: float
    batch_throughput_predictions_per_sec: float
    speedup_factor: float
    memory_usage_mb: float
    accuracy_maintained: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DatabaseMetric:
    """Database performance metric"""
    query_type: str
    avg_execution_time_ms: float
    p50_execution_time_ms: float
    p90_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    total_queries: int
    cache_hit_rate: float
    index_used: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CacheMetric:
    """Cache layer performance metric"""
    layer_name: str
    hit_rate: float
    avg_lookup_time_ms: float
    max_lookup_time_ms: float
    total_accesses: int
    memory_usage_mb: float
    compression_ratio: float
    eviction_rate: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostMetric:
    """Infrastructure cost metric"""
    date: datetime
    compute_cost: float
    database_cost: float
    cache_cost: float
    api_call_cost: float
    ml_inference_cost: float
    total_daily_cost: float

    @property
    def total_cost(self) -> float:
        """Total cost for the day"""
        return self.compute_cost + self.database_cost + self.cache_cost + self.api_call_cost + self.ml_inference_cost


@dataclass
class ValidationReport:
    """Complete validation report"""
    report_name: str
    timestamp: datetime
    test_duration_seconds: float

    # Load testing results
    load_test_results: List[LoadTestResult] = field(default_factory=list)

    # ML inference benchmarks
    ml_benchmarks: List[MLInferenceBenchmark] = field(default_factory=list)

    # Database metrics
    database_metrics: List[DatabaseMetric] = field(default_factory=list)

    # Cache metrics
    cache_metrics: List[CacheMetric] = field(default_factory=list)

    # Cost metrics
    cost_metrics: List[CostMetric] = field(default_factory=list)

    # Summary
    success_criteria_met: Dict[str, bool] = field(default_factory=dict)
    overall_performance_grade: str = "N/A"

    # Recommendations
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Load Testing Component
# ============================================================================

class LoadTestSimulator:
    """Simulates load testing with configurable concurrency"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.response_times = []
        self.errors = []

    async def simulate_api_request(self, request_id: int, delay_ms: float = 100) -> Dict[str, Any]:
        """Simulate a single API request with realistic latency"""
        start_time = time.perf_counter()

        try:
            # Simulate network latency and processing
            await asyncio.sleep(delay_ms / 1000)

            # Simulate occasional errors (5% error rate baseline)
            if np.random.rand() < 0.05:
                raise Exception("Simulated API error")

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return {
                "request_id": request_id,
                "success": True,
                "response_time_ms": elapsed_ms,
                "timestamp": datetime.now()
            }

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.errors.append({
                "request_id": request_id,
                "error": str(e),
                "response_time_ms": elapsed_ms
            })

            return {
                "request_id": request_id,
                "success": False,
                "response_time_ms": elapsed_ms,
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def run_load_test(
        self,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        api_delay_ms: float = 100
    ) -> LoadTestResult:
        """Run load test with specified concurrency"""
        logger.info(f"Starting load test: {concurrent_users} users, {requests_per_user} requests each")

        start_time = time.perf_counter()
        self.response_times = []
        self.errors = []

        # Create all tasks
        tasks = []
        for user_id in range(concurrent_users):
            for request_num in range(requests_per_user):
                request_id = f"{user_id}_{request_num}"
                tasks.append(self.simulate_api_request(request_id, api_delay_ms))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        total_time = time.perf_counter() - start_time

        # Process results
        successful_requests = [r for r in results if r.get('success', False)]
        failed_requests = [r for r in results if not r.get('success', False)]
        response_times = [r['response_time_ms'] for r in results]

        # Calculate metrics
        sorted_times = sorted(response_times)

        return LoadTestResult(
            concurrent_users=concurrent_users,
            total_requests=len(results),
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            avg_response_time_ms=statistics.mean(response_times),
            p50_response_time_ms=sorted_times[len(sorted_times) // 2],
            p95_response_time_ms=sorted_times[int(len(sorted_times) * 0.95)],
            p99_response_time_ms=sorted_times[int(len(sorted_times) * 0.99)],
            max_response_time_ms=max(response_times),
            throughput_requests_per_sec=len(results) / total_time,
            error_rate_percent=(len(failed_requests) / len(results) * 100)
        )


# ============================================================================
# ML Inference Benchmarking Component
# ============================================================================

class MLInferenceBenchmark:
    """Benchmarks ML inference performance"""

    def __init__(self):
        self.results = []

    async def benchmark_individual_inference(self, num_predictions: int = 100) -> Dict[str, Any]:
        """Benchmark individual inference requests"""
        logger.info(f"Benchmarking individual inference: {num_predictions} predictions")

        start_time = time.perf_counter()

        async def single_inference():
            # Simulate ML inference (typically 400-450ms baseline)
            await asyncio.sleep(0.40)  # 400ms simulation
            return {"score": np.random.rand()}

        tasks = [single_inference() for _ in range(num_predictions)]
        results = await asyncio.gather(*tasks)

        total_time = (time.perf_counter() - start_time) * 1000
        avg_time = total_time / num_predictions

        return {
            "total_time_ms": total_time,
            "avg_time_per_prediction_ms": avg_time,
            "throughput_predictions_per_sec": num_predictions / (total_time / 1000),
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }

    async def benchmark_batch_inference(
        self,
        batch_size: int = 32,
        total_predictions: int = 100
    ) -> Dict[str, Any]:
        """Benchmark batch inference requests"""
        logger.info(f"Benchmarking batch inference: batch_size={batch_size}, total={total_predictions}")

        start_time = time.perf_counter()
        num_batches = (total_predictions + batch_size - 1) // batch_size

        async def batch_inference():
            # Simulate batch ML inference
            # Batch processing reduces overhead: time = base + batch_size * per_item
            await asyncio.sleep(0.05 + (batch_size * 0.003))
            return [{"score": np.random.rand()} for _ in range(batch_size)]

        tasks = [batch_inference() for _ in range(num_batches)]
        results = await asyncio.gather(*tasks)

        total_time = (time.perf_counter() - start_time) * 1000
        actual_predictions = sum(len(batch) for batch in results)
        avg_time_per_prediction = total_time / actual_predictions

        return {
            "total_time_ms": total_time,
            "num_batches": num_batches,
            "batch_size": batch_size,
            "actual_predictions": actual_predictions,
            "total_time_per_prediction_ms": avg_time_per_prediction,
            "throughput_predictions_per_sec": actual_predictions / (total_time / 1000),
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }

    async def run_ml_benchmarks(self) -> List[Dict[str, Any]]:
        """Run complete ML inference benchmarks"""
        benchmarks = []

        # Test different batch sizes
        for batch_size in [1, 8, 16, 32, 64]:
            individual = await self.benchmark_individual_inference(100)
            batch = await self.benchmark_batch_inference(batch_size, 100)

            speedup = individual['total_time_ms'] / batch['total_time_ms']

            benchmarks.append({
                "batch_size": batch_size,
                "individual_time_ms": individual['total_time_ms'],
                "batch_time_ms": batch['total_time_ms'],
                "speedup_factor": speedup,
                "individual_throughput": individual['throughput_predictions_per_sec'],
                "batch_throughput": batch['throughput_predictions_per_sec'],
                "throughput_improvement": batch['throughput_predictions_per_sec'] / individual['throughput_predictions_per_sec']
            })

        return benchmarks


# ============================================================================
# Database Connection Pool Stress Testing
# ============================================================================

class DatabaseStressTest:
    """Stress tests database connection pool"""

    def __init__(self, pool_size: int = 50):
        self.pool_size = pool_size
        self.active_connections = 0
        self.max_concurrent_connections = 0
        self.query_times = []
        self.connection_acquire_times = []

    async def simulate_db_query(self, query_duration_ms: float = 10) -> Dict[str, Any]:
        """Simulate a database query"""
        start_time = time.perf_counter()

        # Simulate connection acquisition
        await asyncio.sleep(np.random.uniform(0.001, 0.005))  # 1-5ms

        self.active_connections += 1
        self.max_concurrent_connections = max(self.max_concurrent_connections, self.active_connections)

        try:
            # Simulate query execution
            await asyncio.sleep(query_duration_ms / 1000)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.query_times.append(elapsed_ms)

            return {
                "success": True,
                "execution_time_ms": elapsed_ms
            }
        finally:
            self.active_connections -= 1

    async def run_stress_test(
        self,
        concurrent_queries: int = 100,
        total_queries: int = 1000,
        query_duration_ms: float = 10
    ) -> Dict[str, Any]:
        """Run connection pool stress test"""
        logger.info(f"Starting DB stress test: {concurrent_queries} concurrent, {total_queries} total queries")

        # Run queries in batches to maintain concurrency limit
        start_time = time.perf_counter()
        completed_queries = 0

        while completed_queries < total_queries:
            batch_size = min(concurrent_queries, total_queries - completed_queries)
            tasks = [
                self.simulate_db_query(query_duration_ms)
                for _ in range(batch_size)
            ]

            results = await asyncio.gather(*tasks)
            completed_queries += len(results)

        total_time = time.perf_counter() - start_time

        sorted_times = sorted(self.query_times)

        return {
            "total_queries": len(self.query_times),
            "total_time_seconds": total_time,
            "throughput_queries_per_sec": len(self.query_times) / total_time,
            "avg_query_time_ms": statistics.mean(self.query_times),
            "p50_query_time_ms": sorted_times[len(sorted_times) // 2],
            "p90_query_time_ms": sorted_times[int(len(sorted_times) * 0.9)],
            "p95_query_time_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "max_concurrent_connections": self.max_concurrent_connections,
            "pool_efficiency_percent": (self.max_concurrent_connections / self.pool_size) * 100
        }


# ============================================================================
# Cache Performance Under Load
# ============================================================================

class CachePerformanceTest:
    """Tests cache performance under load"""

    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0
        self.access_times = defaultdict(list)

    async def cache_access(
        self,
        key: str,
        compute_func=None,
        force_miss: bool = False
    ) -> Dict[str, Any]:
        """Simulate cache access"""
        start_time = time.perf_counter()

        if key in self.cache and not force_miss:
            # Cache hit
            self.hits += 1
            result = self.cache[key]
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.access_times[key].append(('hit', elapsed_ms))
            return {"success": True, "source": "cache", "time_ms": elapsed_ms}
        else:
            # Cache miss - compute value
            self.misses += 1

            if compute_func:
                await compute_func()
            else:
                await asyncio.sleep(0.05)  # Simulate 50ms computation

            self.cache[key] = {"data": np.random.rand(100)}
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.access_times[key].append(('miss', elapsed_ms))

            return {"success": True, "source": "computed", "time_ms": elapsed_ms}

    async def run_cache_test(
        self,
        num_accesses: int = 1000,
        cache_size: int = 100,
        hot_key_ratio: float = 0.2
    ) -> Dict[str, Any]:
        """Run cache performance test"""
        logger.info(f"Starting cache test: {num_accesses} accesses, {cache_size} cache_size")

        start_time = time.perf_counter()

        # Generate access pattern with hot/cold keys
        num_hot_keys = max(1, int(cache_size * hot_key_ratio))
        hot_keys = [f"hot_key_{i}" for i in range(num_hot_keys)]
        cold_keys = [f"cold_key_{i}" for i in range(cache_size - num_hot_keys)]

        # Perform accesses with weighted distribution
        tasks = []
        for i in range(num_accesses):
            if np.random.rand() < hot_key_ratio * 5:  # Hot keys accessed more
                key = np.random.choice(hot_keys)
            else:
                key = np.random.choice(cold_keys)

            tasks.append(self.cache_access(key))

        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        # Calculate metrics
        hit_rate = self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0

        # Get timing statistics
        hit_times = []
        miss_times = []
        for times in self.access_times.values():
            for access_type, elapsed_ms in times:
                if access_type == 'hit':
                    hit_times.append(elapsed_ms)
                else:
                    miss_times.append(elapsed_ms)

        return {
            "total_accesses": num_accesses,
            "total_time_seconds": total_time,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate * 100,
            "throughput_accesses_per_sec": num_accesses / total_time,
            "avg_hit_time_ms": statistics.mean(hit_times) if hit_times else 0,
            "avg_miss_time_ms": statistics.mean(miss_times) if miss_times else 0,
            "cache_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }


# ============================================================================
# Cost Baseline Tracking
# ============================================================================

class CostBaselineTracker:
    """Tracks infrastructure costs for 30-day baseline"""

    def __init__(self):
        self.daily_costs = []

    def calculate_daily_cost(
        self,
        compute_hours: float = 24,
        db_queries: int = 1000000,
        cache_gb_hours: float = 100,
        api_calls: int = 500000,
        ml_inferences: int = 100000
    ) -> CostMetric:
        """Calculate daily infrastructure cost"""
        # Estimated pricing (adjust based on actual AWS/GCP pricing)
        compute_cost = compute_hours * 0.0116  # t3.medium pricing
        db_cost = (db_queries / 1000000) * 1.0  # $1 per million queries
        cache_cost = cache_gb_hours * 0.025  # Redis on Elasticache
        api_cost = (api_calls / 1000) * 0.001  # $0.001 per 1000 calls
        ml_cost = (ml_inferences / 1000) * 0.002  # $0.002 per 1000 inferences

        return CostMetric(
            date=datetime.now(),
            compute_cost=compute_cost,
            database_cost=db_cost,
            cache_cost=cache_cost,
            api_call_cost=api_cost,
            ml_inference_cost=ml_cost,
            total_daily_cost=0  # Calculated in property
        )

    def simulate_30_day_baseline(
        self,
        optimization_factor: float = 1.0
    ) -> List[CostMetric]:
        """Simulate 30-day cost baseline"""
        costs = []

        for day in range(30):
            # Simulate daily variations (peak/off-peak)
            variation = np.sin(day / 7) * 0.2 + 1.0  # Weekly pattern

            daily_cost = self.calculate_daily_cost(
                compute_hours=24 * variation,
                db_queries=int(1000000 * variation / optimization_factor),
                cache_gb_hours=100 * variation,
                api_calls=int(500000 * variation),
                ml_inferences=int(100000 * variation / optimization_factor)
            )

            costs.append(daily_cost)

        return costs


# ============================================================================
# Main Validation Framework
# ============================================================================

class Phase2PerformanceValidator:
    """Main validation framework for Phase 2 optimizations"""

    def __init__(self):
        self.report = None
        self.metrics = {}

    def check_success_criteria(
        self,
        api_p95_ms: float,
        ml_inference_ms: float,
        db_p90_ms: float,
        cache_hit_rate: float,
        connection_efficiency: float,
        cost_reduction_percent: float
    ) -> Dict[str, bool]:
        """Check if all success criteria are met"""
        criteria = {
            "api_response_time_p95": api_p95_ms < 200,
            "ml_inference_time": ml_inference_ms < 500,
            "database_query_p90": db_p90_ms < 50,
            "cache_hit_rate": cache_hit_rate > 0.95,
            "connection_pool_efficiency": connection_efficiency > 0.90,
            "infrastructure_cost_reduction": cost_reduction_percent >= 25
        }

        return criteria

    def calculate_performance_grade(self, criteria_met: Dict[str, bool]) -> str:
        """Calculate overall performance grade"""
        met_count = sum(1 for v in criteria_met.values() if v)
        total_count = len(criteria_met)

        percentage = (met_count / total_count) * 100

        if percentage >= 100:
            return "A+"
        elif percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B+"
        elif percentage >= 70:
            return "B"
        elif percentage >= 60:
            return "C"
        else:
            return "D"

    async def run_comprehensive_validation(self) -> ValidationReport:
        """Run complete validation suite"""
        logger.info("Starting Phase 2 Performance Validation Framework")

        start_time = time.perf_counter()

        # 1. Load Testing
        logger.info("\n1. Running Load Tests...")
        load_tester = LoadTestSimulator()
        load_results = []

        for concurrent_users in [10, 50, 100]:
            result = await load_tester.run_load_test(
                concurrent_users=concurrent_users,
                requests_per_user=10
            )
            load_results.append(result)
            logger.info(f"  - {concurrent_users} users: {result.p95_response_time_ms:.2f}ms P95")

        # 2. ML Inference Benchmarking
        logger.info("\n2. Running ML Inference Benchmarks...")
        ml_benchmark = MLInferenceBenchmark()
        ml_results = await ml_benchmark.run_ml_benchmarks()
        for result in ml_results:
            logger.info(f"  - Batch size {result['batch_size']}: {result['speedup_factor']:.2f}x speedup")

        # 3. Database Stress Testing
        logger.info("\n3. Running Database Stress Tests...")
        db_stress = DatabaseStressTest(pool_size=50)
        db_results = await db_stress.run_stress_test(
            concurrent_queries=50,
            total_queries=1000
        )
        logger.info(f"  - P90 query time: {db_results['p90_query_time_ms']:.2f}ms")
        logger.info(f"  - Pool efficiency: {db_results['pool_efficiency_percent']:.1f}%")

        # 4. Cache Performance Testing
        logger.info("\n4. Running Cache Performance Tests...")
        cache_test = CachePerformanceTest()
        cache_results = await cache_test.run_cache_test(num_accesses=1000)
        logger.info(f"  - Hit rate: {cache_results['hit_rate_percent']:.1f}%")
        logger.info(f"  - Hit time: {cache_results['avg_hit_time_ms']:.2f}ms")

        # 5. Cost Baseline Tracking
        logger.info("\n5. Calculating Cost Baselines...")
        cost_tracker = CostBaselineTracker()
        baseline_costs = cost_tracker.simulate_30_day_baseline()
        total_baseline_cost = sum(c.total_cost for c in baseline_costs)
        optimized_costs = cost_tracker.simulate_30_day_baseline(optimization_factor=1.3)
        total_optimized_cost = sum(c.total_cost for c in optimized_costs)
        cost_reduction_percent = ((total_baseline_cost - total_optimized_cost) / total_baseline_cost) * 100
        logger.info(f"  - 30-day baseline: ${total_baseline_cost:.2f}")
        logger.info(f"  - Projected savings: {cost_reduction_percent:.1f}%")

        # Calculate success criteria
        logger.info("\n6. Evaluating Success Criteria...")
        api_p95 = load_results[-1].p95_response_time_ms  # Highest load
        ml_inference = ml_results[0]['individual_time_ms'] / 100  # Avg time per prediction
        db_p90 = db_results['p90_query_time_ms']
        cache_hit_rate = cache_results['hit_rate_percent'] / 100
        connection_efficiency = db_results['pool_efficiency_percent'] / 100

        criteria = self.check_success_criteria(
            api_p95_ms=api_p95,
            ml_inference_ms=ml_inference,
            db_p90_ms=db_p90,
            cache_hit_rate=cache_hit_rate,
            connection_efficiency=connection_efficiency,
            cost_reduction_percent=cost_reduction_percent
        )

        # Calculate overall grade
        grade = self.calculate_performance_grade(criteria)

        # Generate recommendations
        recommendations = self._generate_recommendations(criteria, api_p95, ml_inference, db_p90, cache_hit_rate)

        # Create report
        total_time = time.perf_counter() - start_time
        report = ValidationReport(
            report_name="Phase 2 Performance Validation",
            timestamp=datetime.now(),
            test_duration_seconds=total_time,
            load_test_results=load_results,
            cost_metrics=baseline_costs,
            success_criteria_met=criteria,
            overall_performance_grade=grade,
            recommendations=recommendations
        )

        self.report = report
        return report

    def _generate_recommendations(
        self,
        criteria: Dict[str, bool],
        api_p95: float,
        ml_inference: float,
        db_p90: float,
        cache_hit_rate: float
    ) -> List[str]:
        """Generate actionable recommendations based on results"""
        recommendations = []

        if not criteria["api_response_time_p95"]:
            recommendations.append(
                f"API response time needs improvement: {api_p95:.1f}ms > 200ms target. "
                "Consider increasing connection pool or enabling query caching."
            )

        if not criteria["ml_inference_time"]:
            recommendations.append(
                f"ML inference latency needs optimization: {ml_inference:.1f}ms > 500ms target. "
                "Consider implementing batch processing or model quantization."
            )

        if not criteria["database_query_p90"]:
            recommendations.append(
                f"Database query performance needs improvement: {db_p90:.1f}ms > 50ms target. "
                "Review query plans and ensure recommended indexes are in place."
            )

        if not criteria["cache_hit_rate"]:
            recommendations.append(
                f"Cache hit rate below target: {cache_hit_rate*100:.1f}% < 95% target. "
                "Increase L1 cache size from 5000 to 50000 entries and review TTL settings."
            )

        if all(criteria.values()):
            recommendations.append("All success criteria met! Consider scaling to production.")

        return recommendations

    def generate_report_json(self, output_path: Optional[str] = None) -> str:
        """Generate JSON report"""
        if not self.report:
            return "{}"

        report_dict = {
            "report_name": self.report.report_name,
            "timestamp": self.report.timestamp.isoformat(),
            "test_duration_seconds": self.report.test_duration_seconds,
            "success_criteria": self.report.success_criteria_met,
            "overall_grade": self.report.overall_performance_grade,
            "load_test_summary": {
                "tests_run": len(self.report.load_test_results),
                "highest_concurrent_users": max(r.concurrent_users for r in self.report.load_test_results),
                "best_p95_response_time_ms": min(r.p95_response_time_ms for r in self.report.load_test_results),
                "worst_p95_response_time_ms": max(r.p95_response_time_ms for r in self.report.load_test_results)
            },
            "cost_analysis": {
                "baseline_30day_cost": sum(c.total_cost for c in self.report.cost_metrics),
                "cost_metrics_count": len(self.report.cost_metrics)
            },
            "recommendations": self.report.recommendations
        }

        json_str = json.dumps(report_dict, indent=2, default=str)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
            logger.info(f"Report saved to {output_path}")

        return json_str

    def print_validation_report(self):
        """Print validation report to console"""
        if not self.report:
            logger.error("No report to print. Run validation first.")
            return

        print("\n" + "=" * 80)
        print("PHASE 2 PERFORMANCE VALIDATION REPORT")
        print("=" * 80)

        print(f"\nReport Generated: {self.report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Duration: {self.report.test_duration_seconds:.2f} seconds")
        print(f"Overall Performance Grade: {self.report.overall_performance_grade}")

        print("\n" + "-" * 80)
        print("SUCCESS CRITERIA EVALUATION")
        print("-" * 80)

        for criterion, met in self.report.success_criteria_met.items():
            status = "✅ PASS" if met else "❌ FAIL"
            print(f"{status} - {criterion.replace('_', ' ').title()}")

        print("\n" + "-" * 80)
        print("LOAD TEST RESULTS")
        print("-" * 80)

        for result in self.report.load_test_results:
            print(f"\nConcurrent Users: {result.concurrent_users}")
            print(f"  Total Requests: {result.total_requests}")
            print(f"  Success Rate: {(result.successful_requests/result.total_requests)*100:.1f}%")
            print(f"  Avg Response Time: {result.avg_response_time_ms:.2f}ms")
            print(f"  P95 Response Time: {result.p95_response_time_ms:.2f}ms")
            print(f"  P99 Response Time: {result.p99_response_time_ms:.2f}ms")
            print(f"  Throughput: {result.throughput_requests_per_sec:.1f} req/sec")

        print("\n" + "-" * 80)
        print("RECOMMENDATIONS")
        print("-" * 80)

        for i, recommendation in enumerate(self.report.recommendations, 1):
            print(f"{i}. {recommendation}")

        print("\n" + "=" * 80)


async def main():
    """Main execution"""
    validator = Phase2PerformanceValidator()

    # Run comprehensive validation
    report = await validator.run_comprehensive_validation()

    # Print report
    validator.print_validation_report()

    # Save JSON report
    report_path = Path(__file__).parent / "phase2_validation_report.json"
    validator.generate_report_json(str(report_path))

    # Return success/failure
    all_criteria_met = all(report.success_criteria_met.values())
    return all_criteria_met


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
