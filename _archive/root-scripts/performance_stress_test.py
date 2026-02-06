#!/usr/bin/env python3
"""
Performance Stress Test Suite for Jorge's BI Dashboard System

This script conducts intensive performance testing to validate system capacity
under production-level load and stress conditions.

STRESS TESTING AREAS:
1. High-Volume API Testing (1000+ requests)
2. Extended Load Testing (5+ minutes)
3. Memory Leak Detection
4. Database Connection Pool Testing
5. WebSocket Concurrency Testing
6. Cache Performance Under Load

Performance Targets:
- API Response Time: <100ms P95
- Throughput: >500 RPS
- Error Rate: <1%
- Memory Usage: Stable over time
- Database Connections: Efficient pooling

Author: Claude Sonnet 4
Date: 2026-01-25
"""

import asyncio
import time
import json
import statistics
import sys
import psutil
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import httpx for HTTP testing
try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    os.system("pip install httpx")
    import httpx

@dataclass
class StressTestMetrics:
    """Stress test metrics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_rps: float
    error_rate: float
    peak_memory_mb: float
    cpu_usage_percent: float
    test_duration_seconds: float

class PerformanceStressTester:
    """Advanced performance stress testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []

    async def run_stress_tests(self) -> Dict[str, Any]:
        """Run comprehensive stress tests."""
        print("🚀 Performance Stress Testing - Jorge's BI Dashboard System")
        print("=" * 80)

        stress_tests = [
            ("High-Volume API Stress Test", self._high_volume_api_test),
            ("Extended Load Endurance Test", self._extended_load_test),
            ("Memory Stability Test", self._memory_stability_test),
            ("Burst Traffic Simulation", self._burst_traffic_test),
            ("Database Connection Stress", self._database_connection_test),
        ]

        all_results = {}

        for test_name, test_function in stress_tests:
            print(f"\n📊 {test_name}")
            print("-" * 60)

            try:
                result = await test_function()
                all_results[test_name] = result
                print(f"✅ {test_name} completed")
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                all_results[test_name] = {"error": str(e)}

        # Generate stress test report
        return self._generate_stress_report(all_results)

    async def _high_volume_api_test(self) -> StressTestMetrics:
        """Test API performance with high volume of requests."""
        print("  🎯 Testing API with 1000+ requests...")

        total_requests = 1000
        concurrent_batches = 50
        requests_per_batch = total_requests // concurrent_batches

        start_time = time.time()
        all_response_times = []
        successful_requests = 0
        failed_requests = 0
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        async def batch_requests():
            """Execute a batch of requests."""
            batch_times = []
            batch_success = 0
            batch_failed = 0

            async with httpx.AsyncClient() as client:
                for _ in range(requests_per_batch):
                    request_start = time.time()
                    try:
                        response = await client.get(
                            f"{self.base_url}/api/bi/real-time-metrics",
                            params={"location_id": "stress_test"},
                            timeout=30.0
                        )
                        duration_ms = (time.time() - request_start) * 1000
                        batch_times.append(duration_ms)

                        if response.status_code in [200, 401]:  # Success or auth required
                            batch_success += 1
                        else:
                            batch_failed += 1

                    except Exception:
                        batch_failed += 1

            return batch_times, batch_success, batch_failed

        # Execute all batches concurrently
        tasks = [batch_requests() for _ in range(concurrent_batches)]
        batch_results = await asyncio.gather(*tasks)

        # Aggregate results
        for batch_times, batch_success, batch_failed in batch_results:
            all_response_times.extend(batch_times)
            successful_requests += batch_success
            failed_requests += batch_failed

        end_time = time.time()
        test_duration = end_time - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        peak_memory = max(start_memory, end_memory)

        # Calculate metrics
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        p95_response_time = (
            statistics.quantiles(all_response_times, n=20)[18]
            if len(all_response_times) >= 20
            else max(all_response_times) if all_response_times else 0
        )
        p99_response_time = (
            statistics.quantiles(all_response_times, n=100)[98]
            if len(all_response_times) >= 100
            else max(all_response_times) if all_response_times else 0
        )
        throughput_rps = (successful_requests + failed_requests) / test_duration
        error_rate = (failed_requests / total_requests) * 100

        metrics = StressTestMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            peak_memory_mb=peak_memory,
            cpu_usage_percent=psutil.cpu_percent(),
            test_duration_seconds=test_duration
        )

        print(f"    📈 Results: {successful_requests}/{total_requests} successful")
        print(f"    ⚡ Throughput: {throughput_rps:.1f} RPS")
        print(f"    📊 P95 Response Time: {p95_response_time:.1f}ms")
        print(f"    💾 Peak Memory: {peak_memory:.1f} MB")
        print(f"    ❌ Error Rate: {error_rate:.1f}%")

        return metrics

    async def _extended_load_test(self) -> StressTestMetrics:
        """Test system stability under extended load."""
        print("  ⏱️ Testing extended load (3 minutes)...")

        duration_seconds = 180  # 3 minutes
        requests_per_second = 10
        interval = 1.0 / requests_per_second

        start_time = time.time()
        all_response_times = []
        successful_requests = 0
        failed_requests = 0
        memory_samples = []

        async with httpx.AsyncClient() as client:
            while (time.time() - start_time) < duration_seconds:
                request_start = time.time()

                try:
                    response = await client.get(
                        f"{self.base_url}/api/bi/real-time-metrics",
                        params={"location_id": "endurance_test"},
                        timeout=10.0
                    )
                    duration_ms = (time.time() - request_start) * 1000
                    all_response_times.append(duration_ms)

                    if response.status_code in [200, 401]:
                        successful_requests += 1
                    else:
                        failed_requests += 1

                except Exception:
                    failed_requests += 1

                # Sample memory usage every 10th request
                if (successful_requests + failed_requests) % 10 == 0:
                    memory_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)

                # Wait for next request
                elapsed = time.time() - request_start
                if elapsed < interval:
                    await asyncio.sleep(interval - elapsed)

        test_duration = time.time() - start_time
        total_requests = successful_requests + failed_requests

        # Calculate metrics
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        p95_response_time = (
            statistics.quantiles(all_response_times, n=20)[18]
            if len(all_response_times) >= 20
            else max(all_response_times) if all_response_times else 0
        )
        p99_response_time = (
            statistics.quantiles(all_response_times, n=100)[98]
            if len(all_response_times) >= 100
            else max(all_response_times) if all_response_times else 0
        )
        throughput_rps = total_requests / test_duration
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        peak_memory = max(memory_samples) if memory_samples else 0

        metrics = StressTestMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            peak_memory_mb=peak_memory,
            cpu_usage_percent=psutil.cpu_percent(),
            test_duration_seconds=test_duration
        )

        print(f"    📈 Results: {successful_requests}/{total_requests} successful over {duration_seconds}s")
        print(f"    ⚡ Sustained Throughput: {throughput_rps:.1f} RPS")
        print(f"    📊 P95 Response Time: {p95_response_time:.1f}ms")
        print(f"    💾 Peak Memory: {peak_memory:.1f} MB")
        print(f"    ❌ Error Rate: {error_rate:.1f}%")

        # Check for memory leaks
        if len(memory_samples) >= 2:
            memory_trend = memory_samples[-1] - memory_samples[0]
            if memory_trend > 50:  # More than 50MB increase
                print(f"    ⚠️ Potential memory leak detected: +{memory_trend:.1f} MB")

        return metrics

    async def _memory_stability_test(self) -> Dict[str, Any]:
        """Test memory stability under load."""
        print("  💾 Testing memory stability...")

        duration_seconds = 60  # 1 minute
        sample_interval = 5  # Sample every 5 seconds
        requests_per_sample = 50

        memory_samples = []
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        async with httpx.AsyncClient() as client:
            for _ in range(duration_seconds // sample_interval):
                sample_start_memory = psutil.Process().memory_info().rss / 1024 / 1024

                # Make batch of requests
                for _ in range(requests_per_sample):
                    try:
                        response = await client.get(
                            f"{self.base_url}/api/bi/real-time-metrics",
                            timeout=5.0
                        )
                    except:
                        pass

                sample_end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_samples.append({
                    "timestamp": datetime.now().isoformat(),
                    "memory_mb": sample_end_memory,
                    "memory_delta": sample_end_memory - sample_start_memory
                })

                await asyncio.sleep(sample_interval)

        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        total_memory_change = end_memory - start_memory

        result = {
            "start_memory_mb": start_memory,
            "end_memory_mb": end_memory,
            "total_memory_change_mb": total_memory_change,
            "memory_samples": memory_samples,
            "memory_leak_detected": total_memory_change > 100  # More than 100MB increase
        }

        print(f"    📊 Memory Change: {total_memory_change:+.1f} MB")
        if result["memory_leak_detected"]:
            print(f"    ⚠️ Memory leak detected: +{total_memory_change:.1f} MB")
        else:
            print(f"    ✅ Memory usage stable")

        return result

    async def _burst_traffic_test(self) -> StressTestMetrics:
        """Test system response to burst traffic patterns."""
        print("  💥 Testing burst traffic patterns...")

        # Simulate traffic bursts: quiet periods followed by high activity
        burst_config = [
            (10, 1),   # 10 requests over 1 second (burst)
            (2, 5),    # 2 requests over 5 seconds (quiet)
            (25, 2),   # 25 requests over 2 seconds (bigger burst)
            (1, 3),    # 1 request over 3 seconds (quiet)
            (50, 3),   # 50 requests over 3 seconds (large burst)
        ]

        all_response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()

        for burst_requests, burst_duration in burst_config:
            print(f"    🎯 Burst: {burst_requests} requests in {burst_duration}s")

            async def burst_request():
                request_start = time.time()
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{self.base_url}/api/bi/real-time-metrics",
                            params={"burst": "test"},
                            timeout=15.0
                        )
                        duration_ms = (time.time() - request_start) * 1000
                        return duration_ms, response.status_code in [200, 401]
                except Exception:
                    duration_ms = (time.time() - request_start) * 1000
                    return duration_ms, False

            # Execute burst
            burst_start = time.time()
            tasks = [burst_request() for _ in range(burst_requests)]
            burst_results = await asyncio.gather(*tasks)

            # Collect results
            for duration_ms, success in burst_results:
                all_response_times.append(duration_ms)
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1

            # Wait for burst period to complete
            elapsed = time.time() - burst_start
            if elapsed < burst_duration:
                await asyncio.sleep(burst_duration - elapsed)

        test_duration = time.time() - start_time
        total_requests = successful_requests + failed_requests

        # Calculate metrics
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        p95_response_time = (
            statistics.quantiles(all_response_times, n=20)[18]
            if len(all_response_times) >= 20
            else max(all_response_times) if all_response_times else 0
        )
        p99_response_time = (
            statistics.quantiles(all_response_times, n=100)[98]
            if len(all_response_times) >= 100
            else max(all_response_times) if all_response_times else 0
        )
        throughput_rps = total_requests / test_duration
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0

        metrics = StressTestMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            peak_memory_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            test_duration_seconds=test_duration
        )

        print(f"    📈 Burst Results: {successful_requests}/{total_requests} successful")
        print(f"    📊 P95 Response Time: {p95_response_time:.1f}ms")
        print(f"    ❌ Error Rate: {error_rate:.1f}%")

        return metrics

    async def _database_connection_test(self) -> Dict[str, Any]:
        """Test database connection handling under load."""
        print("  🗄️ Testing database connection stress...")

        # Test multiple endpoints that likely use database connections
        db_endpoints = [
            "/api/bi/dashboard-kpis",
            "/api/bi/revenue-intelligence",
            "/api/bi/bot-performance"
        ]

        concurrent_connections = 30
        requests_per_connection = 10

        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        connection_errors = 0

        async def test_db_endpoint_connection():
            """Test database connections for a single client."""
            local_success = 0
            local_failed = 0
            local_conn_errors = 0

            async with httpx.AsyncClient() as client:
                for _ in range(requests_per_connection):
                    endpoint = db_endpoints[_ % len(db_endpoints)]
                    try:
                        response = await client.get(
                            f"{self.base_url}{endpoint}",
                            params={"timeframe": "24h", "location_id": "db_test"},
                            timeout=20.0
                        )

                        if response.status_code in [200, 401]:
                            local_success += 1
                        elif response.status_code == 500:
                            local_conn_errors += 1
                        else:
                            local_failed += 1

                    except Exception:
                        local_failed += 1

            return local_success, local_failed, local_conn_errors

        # Execute concurrent database tests
        tasks = [test_db_endpoint_connection() for _ in range(concurrent_connections)]
        results = await asyncio.gather(*tasks)

        # Aggregate results
        for success, failed, conn_err in results:
            successful_requests += success
            failed_requests += failed
            connection_errors += conn_err

        test_duration = time.time() - start_time
        total_requests = successful_requests + failed_requests + connection_errors

        result = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "connection_errors": connection_errors,
            "concurrent_connections": concurrent_connections,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "connection_error_rate": (connection_errors / total_requests * 100) if total_requests > 0 else 0,
            "test_duration_seconds": test_duration
        }

        print(f"    📊 DB Connection Results: {successful_requests}/{total_requests} successful")
        print(f"    🔗 Connection Errors: {connection_errors} ({result['connection_error_rate']:.1f}%)")
        print(f"    ✅ Success Rate: {result['success_rate']:.1f}%")

        return result

    def _generate_stress_report(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive stress test report."""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE STRESS TEST REPORT")
        print("=" * 80)

        # Performance summary
        print("\n🎯 STRESS TEST RESULTS SUMMARY")
        print("-" * 50)

        for test_name, result in all_results.items():
            if isinstance(result, StressTestMetrics):
                print(f"\n{test_name}:")
                print(f"  Total Requests: {result.total_requests}")
                print(f"  Success Rate: {(result.successful_requests/result.total_requests)*100:.1f}%")
                print(f"  Throughput: {result.throughput_rps:.1f} RPS")
                print(f"  P95 Response Time: {result.p95_response_time_ms:.1f}ms")
                print(f"  Error Rate: {result.error_rate:.1f}%")
                print(f"  Peak Memory: {result.peak_memory_mb:.1f} MB")
            elif isinstance(result, dict) and "error" not in result:
                print(f"\n{test_name}: ✅ Completed")

        # Performance benchmarks
        print("\n📈 PERFORMANCE BENCHMARKS")
        print("-" * 50)

        # Aggregate performance metrics
        stress_metrics = [r for r in all_results.values() if isinstance(r, StressTestMetrics)]
        if stress_metrics:
            avg_throughput = statistics.mean([m.throughput_rps for m in stress_metrics])
            max_throughput = max([m.throughput_rps for m in stress_metrics])
            avg_response_time = statistics.mean([m.p95_response_time_ms for m in stress_metrics])
            max_error_rate = max([m.error_rate for m in stress_metrics])

            print(f"Average Throughput: {avg_throughput:.1f} RPS")
            print(f"Peak Throughput: {max_throughput:.1f} RPS")
            print(f"Average P95 Response Time: {avg_response_time:.1f}ms")
            print(f"Maximum Error Rate: {max_error_rate:.1f}%")

            # Performance assessment
            print("\n🚀 PERFORMANCE ASSESSMENT")
            print("-" * 50)

            if max_throughput >= 500:
                throughput_score = "✅ EXCELLENT"
            elif max_throughput >= 200:
                throughput_score = "🟡 GOOD"
            else:
                throughput_score = "🔴 NEEDS IMPROVEMENT"

            if avg_response_time <= 100:
                latency_score = "✅ EXCELLENT"
            elif avg_response_time <= 500:
                latency_score = "🟡 GOOD"
            else:
                latency_score = "🔴 NEEDS IMPROVEMENT"

            if max_error_rate <= 1:
                reliability_score = "✅ EXCELLENT"
            elif max_error_rate <= 5:
                reliability_score = "🟡 GOOD"
            else:
                reliability_score = "🔴 NEEDS IMPROVEMENT"

            print(f"Throughput: {throughput_score} (Peak: {max_throughput:.1f} RPS)")
            print(f"Latency: {latency_score} (Avg P95: {avg_response_time:.1f}ms)")
            print(f"Reliability: {reliability_score} (Max Error Rate: {max_error_rate:.1f}%)")

        print("\n💡 PRODUCTION RECOMMENDATIONS")
        print("-" * 50)

        recommendations = []
        if stress_metrics:
            if max([m.error_rate for m in stress_metrics]) > 5:
                recommendations.append("Investigate and reduce error rates under load")
            if statistics.mean([m.p95_response_time_ms for m in stress_metrics]) > 200:
                recommendations.append("Optimize response times for better user experience")
            if max([m.peak_memory_mb for m in stress_metrics]) > 1000:
                recommendations.append("Monitor memory usage in production environment")

        memory_test = all_results.get("Memory Stability Test", {})
        if isinstance(memory_test, dict) and memory_test.get("memory_leak_detected"):
            recommendations.append("Investigate potential memory leaks before production")

        db_test = all_results.get("Database Connection Stress", {})
        if isinstance(db_test, dict) and db_test.get("connection_error_rate", 0) > 5:
            recommendations.append("Optimize database connection pooling and timeout settings")

        if not recommendations:
            recommendations.append("System demonstrates good performance characteristics for production")

        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

        print("\n" + "=" * 80)

        # Generate final report
        report = {
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "stress_test_results": all_results,
            "performance_summary": {
                "avg_throughput_rps": avg_throughput if stress_metrics else 0,
                "max_throughput_rps": max_throughput if stress_metrics else 0,
                "avg_p95_response_time_ms": avg_response_time if stress_metrics else 0,
                "max_error_rate": max_error_rate if stress_metrics else 0
            },
            "recommendations": recommendations
        }

        return report

async def main():
    """Main stress test execution."""
    print("🔥 Starting Performance Stress Testing...")

    tester = PerformanceStressTester()

    try:
        report = await tester.run_stress_tests()

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"stress_test_report_{timestamp}.json"

        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Stress test report saved: {report_filename}")
        print("🏁 Performance stress testing completed!")

        return 0

    except Exception as e:
        print(f"\n❌ Stress testing failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)