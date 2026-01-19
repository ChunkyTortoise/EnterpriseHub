#!/usr/bin/env python3
"""
Performance Benchmark Suite for Jorge's Revenue Acceleration Platform
====================================================================

Comprehensive performance testing and comparison reporting for:
- API response times (<100ms target)
- Golden Lead Detection (<50ms target)
- Cache hit rates (>90% target)
- Database queries (<50ms target)
- Concurrent request handling (1000+ req/sec target)

Author: Claude Code Performance Optimization Agent
Created: 2026-01-17
"""

import asyncio
import aiohttp
import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import sys
import os
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Performance benchmark result"""
    test_name: str
    target_metric: str
    target_value: float
    actual_value: float
    unit: str
    passed: bool
    samples: int
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
        self.session: aiohttp.ClientSession = None

        # Performance targets
        self.targets = {
            'api_response_p95_ms': 100,
            'api_response_p99_ms': 200,
            'golden_lead_detection_ms': 50,
            'cache_hit_rate_percent': 90,
            'db_query_p95_ms': 50,
            'throughput_req_per_sec': 1000,
        }

    async def setup(self):
        """Initialize benchmark environment"""
        print("🔧 Setting up performance benchmark...")
        timeout = aiohttp.ClientTimeout(total=300)
        self.session = aiohttp.ClientSession(timeout=timeout)

        # Wait for API to be ready
        retries = 10
        for i in range(retries):
            try:
                async with self.session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        print("✓ API is ready")
                        return
            except Exception as e:
                if i == retries - 1:
                    raise Exception(f"API not ready after {retries} attempts: {e}")
                await asyncio.sleep(2)

    async def teardown(self):
        """Cleanup benchmark environment"""
        if self.session:
            await self.session.close()
        print("✓ Benchmark cleanup complete")

    async def benchmark_api_response_times(self):
        """Benchmark API response times"""
        print("\n📊 Benchmarking API Response Times...")

        endpoints = [
            "/",
            "/health",
            "/api/pricing/analytics/test-location?days=7",
            "/api/golden-leads/health",
        ]

        response_times = []
        samples = 100

        for endpoint in endpoints:
            for _ in range(samples // len(endpoints)):
                start = time.time()
                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as resp:
                        await resp.text()
                        duration_ms = (time.time() - start) * 1000
                        response_times.append(duration_ms)
                except Exception as e:
                    print(f"  ⚠️  Request failed for {endpoint}: {e}")

        if response_times:
            p95 = self._percentile(response_times, 95)
            p99 = self._percentile(response_times, 99)
            avg = statistics.mean(response_times)

            print(f"  Response Times: Avg={avg:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms")

            # Record P95 result
            self.results.append(BenchmarkResult(
                test_name="API Response Time (P95)",
                target_metric="p95_response_time",
                target_value=self.targets['api_response_p95_ms'],
                actual_value=p95,
                unit="ms",
                passed=p95 <= self.targets['api_response_p95_ms'],
                samples=len(response_times),
                timestamp=datetime.now().isoformat()
            ))

            # Record P99 result
            self.results.append(BenchmarkResult(
                test_name="API Response Time (P99)",
                target_metric="p99_response_time",
                target_value=self.targets['api_response_p99_ms'],
                actual_value=p99,
                unit="ms",
                passed=p99 <= self.targets['api_response_p99_ms'],
                samples=len(response_times),
                timestamp=datetime.now().isoformat()
            ))

    async def benchmark_golden_lead_detection(self):
        """Benchmark Golden Lead Detection performance"""
        print("\n🎯 Benchmarking Golden Lead Detection...")

        detection_times = []
        samples = 50

        # Mock lead data
        test_lead_data = {
            "lead_id": "BENCH_TEST_001",
            "contact_id": "contact_test_001",
            "lead_data": {
                "id": "BENCH_TEST_001",
                "extracted_preferences": {
                    "budget": 750000,
                    "location": "Seattle downtown",
                    "timeline": "next month",
                    "bedrooms": 3
                },
                "conversation_history": [
                    {"role": "user", "content": "Looking for a home"},
                    {"role": "assistant", "content": "I can help!"}
                ]
            }
        }

        # Note: This test requires authentication - would need to implement JWT token
        print("  ⚠️  Golden Lead Detection requires authentication (skipping for now)")
        print("  ℹ️  In production, use authenticated requests with valid JWT token")

        # Placeholder result
        self.results.append(BenchmarkResult(
            test_name="Golden Lead Detection",
            target_metric="detection_latency",
            target_value=self.targets['golden_lead_detection_ms'],
            actual_value=0,  # Would be actual measurement
            unit="ms",
            passed=False,  # Requires authentication
            samples=0,
            timestamp=datetime.now().isoformat()
        ))

    async def benchmark_concurrent_throughput(self):
        """Benchmark concurrent request throughput"""
        print("\n🚀 Benchmarking Concurrent Throughput...")

        concurrent_requests = 100
        duration = 10  # seconds

        successful_requests = 0
        failed_requests = 0
        start_time = time.time()

        async def make_request():
            nonlocal successful_requests, failed_requests
            try:
                async with self.session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1
            except Exception:
                failed_requests += 1

        # Run concurrent requests for specified duration
        end_time = start_time + duration
        while time.time() < end_time:
            tasks = [make_request() for _ in range(concurrent_requests)]
            await asyncio.gather(*tasks, return_exceptions=True)

        actual_duration = time.time() - start_time
        throughput = successful_requests / actual_duration

        print(f"  Throughput: {throughput:.2f} req/sec")
        print(f"  Successful: {successful_requests}, Failed: {failed_requests}")

        self.results.append(BenchmarkResult(
            test_name="Concurrent Throughput",
            target_metric="requests_per_second",
            target_value=self.targets['throughput_req_per_sec'],
            actual_value=throughput,
            unit="req/sec",
            passed=throughput >= self.targets['throughput_req_per_sec'],
            samples=successful_requests + failed_requests,
            timestamp=datetime.now().isoformat()
        ))

    async def benchmark_cache_performance(self):
        """Benchmark cache hit rate"""
        print("\n💾 Benchmarking Cache Performance...")

        # Make repeated requests to same endpoint to test caching
        endpoint = "/api/pricing/analytics/test-location?days=7"
        samples = 50
        cache_hits = 0

        for _ in range(samples):
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as resp:
                    cache_status = resp.headers.get('X-Cache-Status', 'MISS')
                    if cache_status in ('HIT', 'UPDATING'):
                        cache_hits += 1
            except Exception:
                pass

        cache_hit_rate = (cache_hits / samples) * 100 if samples > 0 else 0

        print(f"  Cache Hit Rate: {cache_hit_rate:.2f}%")

        self.results.append(BenchmarkResult(
            test_name="Cache Hit Rate",
            target_metric="cache_hit_rate",
            target_value=self.targets['cache_hit_rate_percent'],
            actual_value=cache_hit_rate,
            unit="%",
            passed=cache_hit_rate >= self.targets['cache_hit_rate_percent'],
            samples=samples,
            timestamp=datetime.now().isoformat()
        ))

    async def benchmark_database_queries(self):
        """Benchmark database query performance"""
        print("\n🗄️  Benchmarking Database Query Performance...")

        # This would require database access endpoints
        # Placeholder for now
        print("  ⚠️  Direct database benchmarking requires database access")
        print("  ℹ️  Database performance is indirectly measured via API response times")

        # Placeholder result
        self.results.append(BenchmarkResult(
            test_name="Database Query Performance",
            target_metric="db_query_p95",
            target_value=self.targets['db_query_p95_ms'],
            actual_value=0,
            unit="ms",
            passed=False,  # Requires database access
            samples=0,
            timestamp=datetime.now().isoformat()
        ))

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)

        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'targets': self.targets,
            'results': [r.to_dict() for r in self.results],
            'performance_grade': self._calculate_performance_grade(),
            'recommendations': self._generate_recommendations()
        }

        return report

    def _calculate_performance_grade(self) -> str:
        """Calculate overall performance grade"""
        if not self.results:
            return 'N/A'

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        success_rate = (passed / total) * 100

        if success_rate >= 90:
            return 'A+'
        elif success_rate >= 80:
            return 'A'
        elif success_rate >= 70:
            return 'B'
        elif success_rate >= 60:
            return 'C'
        else:
            return 'D'

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        for result in self.results:
            if not result.passed:
                if 'response_time' in result.target_metric.lower():
                    recommendations.append(
                        f"⚠️  {result.test_name}: Consider implementing additional caching "
                        f"or optimizing slow operations. Current: {result.actual_value:.2f}{result.unit}, "
                        f"Target: {result.target_value:.2f}{result.unit}"
                    )
                elif 'cache' in result.target_metric.lower():
                    recommendations.append(
                        f"⚠️  {result.test_name}: Improve cache hit rate through TTL optimization "
                        f"or cache warming. Current: {result.actual_value:.2f}{result.unit}, "
                        f"Target: {result.target_value:.2f}{result.unit}"
                    )
                elif 'throughput' in result.target_metric.lower():
                    recommendations.append(
                        f"⚠️  {result.test_name}: Consider horizontal scaling or optimizing "
                        f"concurrent request handling. Current: {result.actual_value:.2f}{result.unit}, "
                        f"Target: {result.target_value:.2f}{result.unit}"
                    )

        if not recommendations:
            recommendations.append("✅ All performance targets met! System is performing optimally.")

        return recommendations

    def print_report(self, report: Dict[str, Any]):
        """Print formatted benchmark report"""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK REPORT")
        print("=" * 80)

        # Summary
        summary = report['summary']
        print(f"\n📊 Summary")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ✓")
        print(f"  Failed: {summary['failed']} ✗")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Performance Grade: {report['performance_grade']}")

        # Results
        print(f"\n📈 Detailed Results")
        for result in report['results']:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"\n  {result['test_name']}: {status}")
            print(f"    Target: {result['target_value']:.2f} {result['unit']}")
            print(f"    Actual: {result['actual_value']:.2f} {result['unit']}")
            print(f"    Samples: {result['samples']}")

        # Recommendations
        print(f"\n💡 Recommendations")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print("\n" + "=" * 80)

    async def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("🚀 Starting Performance Benchmark Suite")
        print(f"Target URL: {self.base_url}")
        print("=" * 80)

        await self.setup()

        try:
            await self.benchmark_api_response_times()
            await self.benchmark_concurrent_throughput()
            await self.benchmark_cache_performance()
            await self.benchmark_golden_lead_detection()
            await self.benchmark_database_queries()

        finally:
            await self.teardown()

        # Generate and print report
        report = self.generate_report()
        self.print_report(report)

        # Save report to file
        report_path = Path(__file__).parent.parent / 'performance_benchmark_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Full report saved to: {report_path}")

        return report


async def main():
    """Main benchmark entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Performance Benchmark Suite')
    parser.add_argument('--url', default='http://localhost:8000',
                        help='Base URL of API to benchmark (default: http://localhost:8000)')
    args = parser.parse_args()

    benchmark = PerformanceBenchmark(base_url=args.url)
    report = await benchmark.run_all_benchmarks()

    # Exit with error code if benchmarks failed
    if report['summary']['failed'] > 0:
        print("\n⚠️  Some benchmarks failed. Review recommendations above.")
        sys.exit(1)
    else:
        print("\n✅ All benchmarks passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
