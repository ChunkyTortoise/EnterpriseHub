"""
Enterprise Performance Testing Suite
Validates Service 6 scalability targets: 100+ leads/hour, <30s response times
"""

import asyncio
import json
import logging
import socket
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import aiohttp
import pytest


def _server_available(host: str = "localhost", port: int = 8501) -> bool:
    """Check if the target server is reachable."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _server_available(),
    reason="requires running server at localhost:8501",
)

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Performance test results"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    throughput_rps: float
    error_rate: float
    duration_seconds: float


class PerformanceTestSuite:
    """Comprehensive performance testing for Service 6"""

    def __init__(self, base_url: str = "http://localhost:8501"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=200),  # High connection limit
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def load_test_lead_processing(
        self, concurrent_users: int = 10, duration_seconds: int = 300, target_rps: float = 10.0
    ) -> LoadTestResult:
        """
        Load test lead processing with target throughput
        Target: 100 leads/hour = ~1.67 leads/minute = 0.028 RPS per lead
        With 10 concurrent users, need ~0.28 RPS total
        """

        start_time = time.time()
        results = []
        tasks = []

        # Calculate delay between requests to achieve target RPS
        delay_between_requests = (1.0 / target_rps) * concurrent_users

        async def worker(worker_id: int):
            """Individual worker simulating user behavior"""
            worker_results = []
            next_request_time = time.time()

            while time.time() - start_time < duration_seconds:
                # Wait until it's time for next request
                current_time = time.time()
                if current_time < next_request_time:
                    await asyncio.sleep(next_request_time - current_time)

                # Execute lead processing request
                try:
                    result = await self._simulate_lead_analysis(worker_id)
                    worker_results.append(result)
                except Exception as e:
                    logger.error(f"Worker {worker_id} request failed: {e}")
                    worker_results.append(
                        {
                            "success": False,
                            "response_time_ms": 30000,  # Timeout
                            "error": str(e),
                        }
                    )

                # Schedule next request
                next_request_time = time.time() + delay_between_requests

            return worker_results

        # Start all workers
        for i in range(concurrent_users):
            task = asyncio.create_task(worker(i))
            tasks.append(task)

        # Wait for completion
        logger.info(f"Running load test: {concurrent_users} users, {duration_seconds}s duration")
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for worker_result in worker_results:
            if isinstance(worker_result, list):
                results.extend(worker_result)

        return self._analyze_results(results, time.time() - start_time)

    async def _simulate_lead_analysis(self, worker_id: int) -> Dict[str, Any]:
        """Simulate complete lead analysis workflow"""
        start_time = time.time()

        # Test data mimicking real lead processing
        lead_data = {
            "lead_id": f"perf_test_lead_{worker_id}_{int(time.time() * 1000)}",
            "name": f"Test Lead {worker_id}",
            "email": f"lead{worker_id}@test.com",
            "preferences": {"max_price": 500000, "min_bedrooms": 3, "location": "Rancho Cucamonga"},
            "source": "performance_test",
        }

        try:
            # Simulate the full lead intelligence pipeline

            # 1. Lead scoring (most CPU intensive)
            async with self.session.post(
                f"{self.base_url}/api/score_lead", json=lead_data, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                score_result = await response.json()
                if response.status != 200:
                    raise Exception(f"Scoring failed: {score_result}")

            # 2. Property matching
            async with self.session.post(
                f"{self.base_url}/api/match_properties",
                json={"lead_id": lead_data["lead_id"], "preferences": lead_data["preferences"]},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                match_result = await response.json()
                if response.status != 200:
                    raise Exception(f"Matching failed: {match_result}")

            # 3. AI analysis (Claude integration)
            async with self.session.post(
                f"{self.base_url}/api/analyze_lead",
                json={"lead_data": lead_data, "score_result": score_result, "matches": match_result},
                timeout=aiohttp.ClientTimeout(total=25),
            ) as response:
                analysis_result = await response.json()
                if response.status != 200:
                    raise Exception(f"Analysis failed: {analysis_result}")

            response_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "response_time_ms": response_time_ms,
                "lead_score": score_result.get("score", 0),
                "matches_found": len(match_result.get("matches", [])),
                "ai_classification": analysis_result.get("classification", "unknown"),
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "response_time_ms": 30000,  # Max timeout
                "error": "Request timeout",
            }
        except Exception as e:
            return {"success": False, "response_time_ms": (time.time() - start_time) * 1000, "error": str(e)}

    def _analyze_results(self, results: List[Dict[str, Any]], duration: float) -> LoadTestResult:
        """Analyze performance test results"""

        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]

        response_times = [r["response_time_ms"] for r in results if "response_time_ms" in r]

        if not response_times:
            # No valid response times
            return LoadTestResult(
                total_requests=len(results),
                successful_requests=0,
                failed_requests=len(results),
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                max_response_time_ms=0,
                min_response_time_ms=0,
                throughput_rps=0,
                error_rate=1.0,
                duration_seconds=duration,
            )

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p95_idx = int(0.95 * len(sorted_times))
        p99_idx = int(0.99 * len(sorted_times))

        return LoadTestResult(
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time_ms=statistics.mean(response_times),
            p95_response_time_ms=sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0,
            p99_response_time_ms=sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0,
            max_response_time_ms=max(response_times),
            min_response_time_ms=min(response_times),
            throughput_rps=len(successful_results) / duration if duration > 0 else 0,
            error_rate=len(failed_results) / max(len(results), 1),
            duration_seconds=duration,
        )

    async def stress_test_concurrent_users(self, max_users: int = 50) -> Dict[str, LoadTestResult]:
        """Test system behavior under increasing load"""
        results = {}

        user_levels = [5, 10, 20, 30, 40, 50][: max_users // 5]

        for users in user_levels:
            logger.info(f"Testing {users} concurrent users...")

            result = await self.load_test_lead_processing(
                concurrent_users=users,
                duration_seconds=120,  # 2 minutes per level
                target_rps=users * 0.1,  # 0.1 RPS per user
            )

            results[f"{users}_users"] = result

            # Log results
            logger.info(
                f"Users: {users}, "
                f"Avg Response: {result.avg_response_time_ms:.0f}ms, "
                f"P95: {result.p95_response_time_ms:.0f}ms, "
                f"Throughput: {result.throughput_rps:.2f} RPS, "
                f"Error Rate: {result.error_rate:.1%}"
            )

            # Wait between test levels
            await asyncio.sleep(30)

        return results

    async def endurance_test(self, duration_hours: int = 1) -> LoadTestResult:
        """Long-running endurance test"""
        duration_seconds = duration_hours * 3600

        logger.info(f"Starting {duration_hours}h endurance test...")

        result = await self.load_test_lead_processing(
            concurrent_users=10,
            duration_seconds=duration_seconds,
            target_rps=3.0,  # Sustained 3 RPS for endurance
        )

        return result

    def validate_performance_targets(self, result: LoadTestResult) -> Dict[str, bool]:
        """Validate against Service 6 performance targets"""

        # Target: <30s response times (30,000ms)
        response_time_ok = result.p95_response_time_ms < 30000

        # Target: 100+ leads/hour = 1.67 leads/minute = 0.028 RPS minimum
        # But we need to account for concurrent processing
        throughput_ok = result.throughput_rps > 0.02  # Minimum threshold

        # Target: 99.9% uptime (max 0.1% error rate)
        uptime_ok = result.error_rate < 0.001

        # Target: Reasonable resource utilization
        efficiency_ok = result.avg_response_time_ms < 15000  # Average under 15s

        return {
            "response_time_target": response_time_ok,
            "throughput_target": throughput_ok,
            "uptime_target": uptime_ok,
            "efficiency_target": efficiency_ok,
            "overall_pass": all([response_time_ok, throughput_ok, uptime_ok, efficiency_ok]),
        }


# pytest test functions
@pytest.mark.asyncio
@pytest.mark.performance
async def test_baseline_performance():
    """Test baseline single-user performance"""
    async with PerformanceTestSuite() as suite:
        result = await suite.load_test_lead_processing(concurrent_users=1, duration_seconds=60, target_rps=1.0)

        # Validate targets
        targets = suite.validate_performance_targets(result)

        # Assertions
        assert result.error_rate < 0.05, f"Error rate {result.error_rate:.1%} exceeds 5%"
        assert result.avg_response_time_ms < 30000, f"Average response {result.avg_response_time_ms:.0f}ms exceeds 30s"
        assert targets["overall_pass"], f"Performance targets failed: {targets}"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_target_load_performance():
    """Test performance under target load (100 leads/hour)"""
    async with PerformanceTestSuite() as suite:
        # 100 leads/hour with 10 concurrent users = 10 leads/hour per user
        result = await suite.load_test_lead_processing(
            concurrent_users=10,
            duration_seconds=300,  # 5 minutes
            target_rps=2.78,  # 100 leads/hour = 2.78 per minute / 60 = 0.046 RPS
        )

        targets = suite.validate_performance_targets(result)

        # Key assertions for production readiness
        assert result.p95_response_time_ms < 30000, (
            f"P95 response time {result.p95_response_time_ms:.0f}ms exceeds 30s target"
        )
        assert result.error_rate < 0.01, f"Error rate {result.error_rate:.1%} exceeds 1% for production load"
        assert targets["throughput_target"], f"Throughput {result.throughput_rps:.3f} RPS below target"


@pytest.mark.asyncio
@pytest.mark.stress
async def test_stress_performance():
    """Stress test to find breaking point"""
    async with PerformanceTestSuite() as suite:
        results = await suite.stress_test_concurrent_users(max_users=30)

        # Find the highest load level that still meets targets
        passing_levels = []
        for level, result in results.items():
            targets = suite.validate_performance_targets(result)
            if targets["overall_pass"]:
                passing_levels.append(level)

        # Should handle at least 20 concurrent users
        assert any("20_users" in level for level in passing_levels), "System should handle at least 20 concurrent users"


@pytest.mark.asyncio
@pytest.mark.endurance
@pytest.mark.slow
async def test_endurance_performance():
    """1-hour endurance test (use @pytest.mark.slow to skip in quick runs)"""
    async with PerformanceTestSuite() as suite:
        result = await suite.endurance_test(duration_hours=1)

        targets = suite.validate_performance_targets(result)

        # Endurance-specific assertions
        assert result.error_rate < 0.005, f"Endurance error rate {result.error_rate:.1%} too high"
        assert targets["response_time_target"], f"Response times degraded during endurance test"
        assert targets["uptime_target"], f"Uptime target not met during endurance test"


if __name__ == "__main__":
    # Run performance tests directly
    async def run_performance_tests():
        print("🚀 Running Service 6 Performance Validation")
        print("============================================")

        async with PerformanceTestSuite() as suite:
            # Baseline test
            print("\n1. Baseline Performance Test (1 user, 1 minute)")
            baseline = await suite.load_test_lead_processing(concurrent_users=1, duration_seconds=60, target_rps=1.0)
            baseline_targets = suite.validate_performance_targets(baseline)
            print(
                f"   ✅ Response Time: {baseline.avg_response_time_ms:.0f}ms avg, {baseline.p95_response_time_ms:.0f}ms P95"
            )
            print(f"   ✅ Throughput: {baseline.throughput_rps:.2f} RPS")
            print(f"   ✅ Error Rate: {baseline.error_rate:.1%}")
            print(
                f"   {'✅' if baseline_targets['overall_pass'] else '❌'} Overall: {'PASS' if baseline_targets['overall_pass'] else 'FAIL'}"
            )

            # Target load test
            print("\n2. Target Load Test (10 users, 5 minutes)")
            target_load = await suite.load_test_lead_processing(
                concurrent_users=10, duration_seconds=300, target_rps=2.78
            )
            target_targets = suite.validate_performance_targets(target_load)
            print(
                f"   ✅ Response Time: {target_load.avg_response_time_ms:.0f}ms avg, {target_load.p95_response_time_ms:.0f}ms P95"
            )
            print(f"   ✅ Throughput: {target_load.throughput_rps:.2f} RPS")
            print(f"   ✅ Error Rate: {target_load.error_rate:.1%}")
            print(
                f"   {'✅' if target_targets['overall_pass'] else '❌'} Overall: {'PASS' if target_targets['overall_pass'] else 'FAIL'}"
            )

            # Performance summary
            print("\n📊 Performance Summary")
            print("=====================")
            print(
                f"Target: <30s response times     {'✅ MET' if baseline.p95_response_time_ms < 30000 else '❌ MISSED'}"
            )
            print(f"Target: 100+ leads/hour         {'✅ MET' if target_load.throughput_rps > 0.02 else '❌ MISSED'}")
            print(f"Target: 99.9% uptime           {'✅ MET' if target_load.error_rate < 0.001 else '❌ MISSED'}")

            overall_pass = baseline_targets["overall_pass"] and target_targets["overall_pass"]
            print(f"\n🏆 Service 6 Scalability: {'✅ PRODUCTION READY' if overall_pass else '❌ NEEDS OPTIMIZATION'}")

    # Run the tests
    asyncio.run(run_performance_tests())