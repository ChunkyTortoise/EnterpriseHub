#!/usr/bin/env python3
"""
🚀 BI Dashboard Load Testing Script
====================================

Quick load testing utility for Jorge's BI Dashboard performance monitoring.
Can be used for continuous integration, monitoring, and regression testing.

Usage:
    python bi_dashboard_load_test.py --users 100 --duration 60
    python bi_dashboard_load_test.py --mock --users 1000 --duration 30

Author: Performance Validation Agent
Date: 2026-01-25
"""

import asyncio
import aiohttp
import time
import argparse
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    """Load test result summary."""
    test_duration_s: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    error_rate: float

class BIDashboardLoadTester:
    """Load testing utility for BI Dashboard."""

    def __init__(self, base_url: str = "http://localhost:8001", mock_mode: bool = False):
        self.base_url = base_url
        self.mock_mode = mock_mode
        self.test_endpoints = [
            "/api/bi/dashboard-kpis",
            "/api/bi/revenue-intelligence",
            "/api/bi/bot-performance",
            "/api/bi/real-time-metrics"
        ]

    async def run_load_test(
        self,
        concurrent_users: int = 100,
        duration_seconds: int = 60,
        endpoint_weights: Dict[str, float] = None
    ) -> LoadTestResult:
        """
        Run load test with specified parameters.

        Args:
            concurrent_users: Number of concurrent virtual users
            duration_seconds: Test duration in seconds
            endpoint_weights: Distribution weights for endpoints
        """
        logger.info(f"🚀 Starting load test:")
        logger.info(f"   Users: {concurrent_users}")
        logger.info(f"   Duration: {duration_seconds}s")
        logger.info(f"   Target: {self.base_url}")
        logger.info(f"   Mode: {'Mock' if self.mock_mode else 'Live'}")

        # Default endpoint weights (simulate realistic usage)
        if endpoint_weights is None:
            endpoint_weights = {
                "/api/bi/dashboard-kpis": 0.4,      # 40% - Most common
                "/api/bi/real-time-metrics": 0.3,   # 30% - Frequent updates
                "/api/bi/bot-performance": 0.2,     # 20% - Regular monitoring
                "/api/bi/revenue-intelligence": 0.1  # 10% - Periodic analysis
            }

        # Shared data for concurrent tasks
        test_data = {
            'response_times': [],
            'error_count': 0,
            'request_count': 0,
            'start_time': time.time(),
            'duration': duration_seconds
        }

        # Create user tasks
        user_tasks = []
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_user(user_id, test_data, endpoint_weights)
            )
            user_tasks.append(task)

        logger.info(f"⚡ Running load test with {concurrent_users} virtual users...")

        # Wait for test completion
        await asyncio.gather(*user_tasks, return_exceptions=True)

        # Calculate results
        end_time = time.time()
        actual_duration = end_time - test_data['start_time']

        result = self._calculate_results(test_data, actual_duration)

        self._log_results(result)
        return result

    async def _simulate_user(
        self,
        user_id: int,
        test_data: Dict[str, Any],
        endpoint_weights: Dict[str, float]
    ):
        """Simulate a single user's behavior."""
        async with aiohttp.ClientSession() as session:
            while time.time() - test_data['start_time'] < test_data['duration']:
                try:
                    # Select endpoint based on weights
                    import random
                    endpoint = random.choices(
                        list(endpoint_weights.keys()),
                        weights=list(endpoint_weights.values())
                    )[0]

                    await self._make_request(session, endpoint, test_data)

                    # Random delay between requests (0.1-2.0 seconds)
                    await asyncio.sleep(random.uniform(0.1, 2.0))

                except Exception as e:
                    test_data['error_count'] += 1
                    logger.warning(f"User {user_id} request failed: {e}")

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        test_data: Dict[str, Any]
    ):
        """Make a single request and record metrics."""
        if self.mock_mode:
            # Simulate request with mock response time
            delay = random.uniform(0.02, 0.08)  # 20-80ms
            await asyncio.sleep(delay)
            test_data['response_times'].append(delay * 1000)
            test_data['request_count'] += 1
            return

        # Real request
        start_time = time.perf_counter()

        # Default parameters for BI endpoints
        params = {
            "location_id": "default",
            "timeframe": "24h"
        }

        try:
            url = f"{self.base_url}{endpoint}"
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                await response.text()

                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000

                test_data['response_times'].append(response_time_ms)
                test_data['request_count'] += 1

                if response.status >= 400:
                    test_data['error_count'] += 1

        except Exception as e:
            test_data['error_count'] += 1
            # Don't record response time for failed requests
            raise

    def _calculate_results(self, test_data: Dict[str, Any], duration: float) -> LoadTestResult:
        """Calculate load test results."""
        response_times = test_data['response_times']
        total_requests = test_data['request_count']
        failed_requests = test_data['error_count']
        successful_requests = total_requests - failed_requests

        if not response_times:
            return LoadTestResult(
                test_duration_s=duration,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=failed_requests,
                requests_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                error_rate=1.0 if total_requests > 0 else 0
            )

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        return LoadTestResult(
            test_duration_s=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=total_requests / duration,
            avg_response_time_ms=statistics.mean(response_times),
            p95_response_time_ms=sorted_times[int(0.95 * n)] if n > 1 else sorted_times[0],
            p99_response_time_ms=sorted_times[int(0.99 * n)] if n > 1 else sorted_times[0],
            min_response_time_ms=min(response_times),
            max_response_time_ms=max(response_times),
            error_rate=failed_requests / total_requests if total_requests > 0 else 0
        )

    def _log_results(self, result: LoadTestResult):
        """Log test results in a formatted way."""
        logger.info("🏁 Load test completed!")
        logger.info("=" * 50)
        logger.info(f"📊 RESULTS SUMMARY:")
        logger.info(f"   Duration: {result.test_duration_s:.1f}s")
        logger.info(f"   Total Requests: {result.total_requests}")
        logger.info(f"   Successful: {result.successful_requests}")
        logger.info(f"   Failed: {result.failed_requests}")
        logger.info(f"   Requests/sec: {result.requests_per_second:.1f}")
        logger.info(f"   Error Rate: {result.error_rate:.1%}")
        logger.info("")
        logger.info(f"⚡ PERFORMANCE METRICS:")
        logger.info(f"   Avg Response: {result.avg_response_time_ms:.1f}ms")
        logger.info(f"   P95 Response: {result.p95_response_time_ms:.1f}ms")
        logger.info(f"   P99 Response: {result.p99_response_time_ms:.1f}ms")
        logger.info(f"   Min Response: {result.min_response_time_ms:.1f}ms")
        logger.info(f"   Max Response: {result.max_response_time_ms:.1f}ms")
        logger.info("=" * 50)

        # Performance assessment
        if result.error_rate < 0.01 and result.avg_response_time_ms < 500:
            logger.info("✅ EXCELLENT PERFORMANCE")
        elif result.error_rate < 0.05 and result.avg_response_time_ms < 1000:
            logger.info("✅ GOOD PERFORMANCE")
        elif result.error_rate < 0.10 and result.avg_response_time_ms < 2000:
            logger.info("⚠️  ACCEPTABLE PERFORMANCE")
        else:
            logger.info("❌ POOR PERFORMANCE - NEEDS OPTIMIZATION")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="BI Dashboard Load Testing")

    parser.add_argument("--users", "-u", type=int, default=50,
                       help="Number of concurrent users (default: 50)")

    parser.add_argument("--duration", "-d", type=int, default=30,
                       help="Test duration in seconds (default: 30)")

    parser.add_argument("--url", type=str, default="http://localhost:8001",
                       help="Base URL for testing (default: http://localhost:8001)")

    parser.add_argument("--mock", action="store_true",
                       help="Use mock mode for testing")

    parser.add_argument("--output", "-o", type=str,
                       help="Save results to JSON file")

    parser.add_argument("--quick", "-q", action="store_true",
                       help="Quick test: 10 users for 15 seconds")

    args = parser.parse_args()

    # Quick test mode
    if args.quick:
        args.users = 10
        args.duration = 15

    async def run_test():
        tester = BIDashboardLoadTester(args.url, args.mock)
        result = await tester.run_load_test(args.users, args.duration)

        # Save results if requested
        if args.output:
            result_dict = {
                'timestamp': datetime.now().isoformat(),
                'test_config': {
                    'users': args.users,
                    'duration': args.duration,
                    'url': args.url,
                    'mock_mode': args.mock
                },
                'results': {
                    'test_duration_s': result.test_duration_s,
                    'total_requests': result.total_requests,
                    'successful_requests': result.successful_requests,
                    'failed_requests': result.failed_requests,
                    'requests_per_second': result.requests_per_second,
                    'avg_response_time_ms': result.avg_response_time_ms,
                    'p95_response_time_ms': result.p95_response_time_ms,
                    'p99_response_time_ms': result.p99_response_time_ms,
                    'min_response_time_ms': result.min_response_time_ms,
                    'max_response_time_ms': result.max_response_time_ms,
                    'error_rate': result.error_rate
                }
            }

            with open(args.output, 'w') as f:
                json.dump(result_dict, f, indent=2)

            logger.info(f"📁 Results saved to: {args.output}")

        return result.error_rate < 0.05 and result.avg_response_time_ms < 1000

    # Run the test
    success = asyncio.run(run_test())
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    import random

    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⏹️  Load test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Load test failed: {e}")
        sys.exit(1)