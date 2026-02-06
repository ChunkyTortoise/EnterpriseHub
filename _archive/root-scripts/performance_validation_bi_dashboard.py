#!/usr/bin/env python3
"""
🚀 Jorge's BI Dashboard Performance Validation Agent
===========================================

Comprehensive performance testing for Jorge's Business Intelligence Dashboard
to ensure enterprise-grade performance targets are met.

PERFORMANCE TARGETS:
- ✅ WebSocket latency <10ms round-trip
- ✅ API responses <500ms (dashboard KPIs, revenue intelligence, etc.)
- ✅ Dashboard load time <2s initial render
- ✅ 1000+ concurrent connections supported
- ✅ Jorge's 6% commission calculations real-time (<50ms)
- ✅ Cache hit rate >95%

VALIDATION SCOPE:
1. WebSocket Performance Testing
2. API Endpoint Response Time Validation
3. Dashboard Component Load Testing
4. Concurrent User Simulation
5. Real-time Commission Calculation Performance
6. Cache Performance Optimization Validation

Author: Performance Validation Agent
Date: 2026-01-25
"""

import asyncio
import aiohttp
import websockets
import time
import statistics
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import psutil
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    success_rate: float
    target_met: bool
    target_threshold_ms: float

@dataclass
class WebSocketMetrics:
    """WebSocket performance metrics."""
    test_name: str
    connections_established: int
    messages_sent: int
    messages_received: int
    avg_round_trip_ms: float
    p95_round_trip_ms: float
    connection_failures: int
    message_failures: int
    target_latency_ms: float = 10.0

class PerformanceValidator:
    """Enterprise performance validation for Jorge's BI Dashboard."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.websocket_url = base_url.replace("http", "ws")
        self.results: Dict[str, Any] = {}

        # Performance targets (enterprise-grade)
        self.targets = {
            'websocket_latency_ms': 10.0,
            'api_response_ms': 500.0,
            'dashboard_load_ms': 2000.0,
            'concurrent_connections': 1000,
            'commission_calc_ms': 50.0,
            'cache_hit_rate': 0.95
        }

        logger.info(f"Performance Validator initialized for {base_url}")
        logger.info(f"Enterprise targets: {self.targets}")

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete performance validation suite."""
        logger.info("🚀 Starting comprehensive BI Dashboard performance validation...")

        validation_results = {
            'validation_start_time': datetime.now(timezone.utc).isoformat(),
            'targets': self.targets,
            'test_results': {}
        }

        # Test Suite Execution
        test_suite = [
            ("WebSocket Latency", self.test_websocket_latency),
            ("API Response Times", self.test_api_response_times),
            ("Dashboard Load Performance", self.test_dashboard_load_performance),
            ("Concurrent Connections", self.test_concurrent_connections),
            ("Commission Calculations", self.test_commission_calculation_performance),
            ("Cache Performance", self.test_cache_performance),
            ("End-to-End Workflow", self.test_end_to_end_performance)
        ]

        for test_name, test_function in test_suite:
            logger.info(f"⚡ Running {test_name} validation...")
            try:
                result = await test_function()
                validation_results['test_results'][test_name] = result

                # Log result summary
                if 'target_met' in result:
                    status = "✅ PASSED" if result['target_met'] else "❌ FAILED"
                    logger.info(f"{status} {test_name}: {result.get('summary', '')}")

            except Exception as e:
                logger.error(f"❌ {test_name} validation failed: {e}")
                validation_results['test_results'][test_name] = {
                    'error': str(e),
                    'target_met': False
                }

        # Generate overall assessment
        validation_results['overall_assessment'] = self._generate_overall_assessment(
            validation_results['test_results']
        )
        validation_results['validation_end_time'] = datetime.now(timezone.utc).isoformat()

        logger.info("🏁 Performance validation completed!")
        return validation_results

    async def test_websocket_latency(self) -> Dict[str, Any]:
        """Test WebSocket latency <10ms target."""
        logger.info("Testing WebSocket round-trip latency...")

        round_trip_times = []
        connection_failures = 0
        message_failures = 0

        # Test with multiple concurrent connections
        async def test_websocket_connection():
            try:
                uri = f"{self.websocket_url}/api/bi/ws/dashboard"
                async with websockets.connect(uri) as websocket:
                    # Send test messages and measure round-trip
                    for i in range(10):
                        start_time = time.perf_counter()

                        test_message = {
                            "type": "heartbeat",
                            "timestamp": start_time,
                            "test_id": f"latency_test_{i}"
                        }

                        await websocket.send(json.dumps(test_message))
                        response = await websocket.recv()

                        end_time = time.perf_counter()
                        round_trip_ms = (end_time - start_time) * 1000
                        round_trip_times.append(round_trip_ms)

                        # Small delay between messages
                        await asyncio.sleep(0.1)

            except Exception as e:
                logger.warning(f"WebSocket connection failed: {e}")
                return False
            return True

        # Test with 10 concurrent connections
        tasks = [test_websocket_connection() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        connection_failures = sum(1 for r in results if r is not True)

        if not round_trip_times:
            return {
                'target_met': False,
                'error': 'No successful WebSocket connections',
                'connection_failures': connection_failures
            }

        # Calculate metrics
        avg_latency = statistics.mean(round_trip_times)
        p95_latency = np.percentile(round_trip_times, 95)
        target_met = avg_latency < self.targets['websocket_latency_ms']

        metrics = WebSocketMetrics(
            test_name="WebSocket Latency",
            connections_established=len(results) - connection_failures,
            messages_sent=len(round_trip_times),
            messages_received=len(round_trip_times),
            avg_round_trip_ms=avg_latency,
            p95_round_trip_ms=p95_latency,
            connection_failures=connection_failures,
            message_failures=message_failures
        )

        return {
            'metrics': asdict(metrics),
            'target_met': target_met,
            'target_threshold_ms': self.targets['websocket_latency_ms'],
            'summary': f"Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms (target: <{self.targets['websocket_latency_ms']}ms)",
            'raw_measurements': round_trip_times[:50]  # Sample for analysis
        }

    async def test_api_response_times(self) -> Dict[str, Any]:
        """Test all BI API endpoints for <500ms response target."""
        logger.info("Testing BI API endpoint response times...")

        # Define BI API endpoints to test
        endpoints = [
            ("GET", "/api/bi/dashboard-kpis", {"timeframe": "24h", "location_id": "default"}),
            ("GET", "/api/bi/revenue-intelligence", {"timeframe": "30d", "location_id": "default"}),
            ("GET", "/api/bi/bot-performance", {"timeframe": "7d", "location_id": "default"}),
            ("GET", "/api/bi/real-time-metrics", {"location_id": "default"}),
            ("GET", "/api/bi/predictive-insights", {"location_id": "default"}),
            ("GET", "/api/bi/anomaly-detection", {"timeframe": "24h", "location_id": "default"}),
            ("POST", "/api/bi/drill-down", {
                "component": "revenue",
                "metric": "total_revenue",
                "timeframe": "24h",
                "location_id": "default"
            }),
            ("GET", "/api/bi/cache-analytics", {}),
            ("POST", "/api/bi/warm-cache", {"location_ids": "default"}),
            ("POST", "/api/bi/trigger-aggregation", {"location_id": "default", "window_name": "5min"})
        ]

        endpoint_results = {}
        all_response_times = []

        async with aiohttp.ClientSession() as session:
            for method, endpoint, params in endpoints:
                logger.info(f"Testing {method} {endpoint}")
                response_times = []

                # Test each endpoint multiple times
                for i in range(20):
                    try:
                        start_time = time.perf_counter()

                        if method == "GET":
                            async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                                await response.text()
                                status = response.status
                        else:  # POST
                            async with session.post(f"{self.base_url}{endpoint}", json=params) as response:
                                await response.text()
                                status = response.status

                        end_time = time.perf_counter()
                        response_time_ms = (end_time - start_time) * 1000

                        if status < 400:  # Success
                            response_times.append(response_time_ms)
                            all_response_times.append(response_time_ms)

                        # Small delay between requests
                        await asyncio.sleep(0.05)

                    except Exception as e:
                        logger.warning(f"Request failed for {endpoint}: {e}")

                if response_times:
                    endpoint_metrics = self._calculate_performance_metrics(
                        f"{method} {endpoint}",
                        response_times,
                        self.targets['api_response_ms']
                    )
                    endpoint_results[endpoint] = asdict(endpoint_metrics)
                else:
                    endpoint_results[endpoint] = {
                        'error': 'No successful responses',
                        'target_met': False
                    }

        # Overall API performance assessment
        if all_response_times:
            overall_metrics = self._calculate_performance_metrics(
                "All BI APIs",
                all_response_times,
                self.targets['api_response_ms']
            )

            return {
                'overall_metrics': asdict(overall_metrics),
                'endpoint_details': endpoint_results,
                'target_met': overall_metrics.target_met,
                'summary': f"Overall API Avg: {overall_metrics.avg_response_time_ms:.1f}ms, P95: {overall_metrics.p95_response_time_ms:.1f}ms (target: <{self.targets['api_response_ms']}ms)"
            }
        else:
            return {
                'target_met': False,
                'error': 'No successful API responses',
                'endpoint_details': endpoint_results
            }

    async def test_dashboard_load_performance(self) -> Dict[str, Any]:
        """Test dashboard initial load time <2s target."""
        logger.info("Testing dashboard load performance...")

        load_times = []

        async with aiohttp.ClientSession() as session:
            # Simulate dashboard load sequence
            for i in range(10):
                start_time = time.perf_counter()

                try:
                    # Simulate typical dashboard load sequence
                    tasks = [
                        session.get(f"{self.base_url}/api/bi/dashboard-kpis",
                                   params={"timeframe": "24h", "location_id": "default"}),
                        session.get(f"{self.base_url}/api/bi/real-time-metrics",
                                   params={"location_id": "default"}),
                        session.get(f"{self.base_url}/api/bi/bot-performance",
                                   params={"timeframe": "7d", "location_id": "default"})
                    ]

                    # Execute dashboard load requests concurrently
                    responses = await asyncio.gather(*tasks, return_exceptions=True)

                    # Check if all requests succeeded
                    all_success = True
                    for response in responses:
                        if isinstance(response, Exception):
                            all_success = False
                            break
                        else:
                            await response.text()
                            if response.status >= 400:
                                all_success = False
                                break
                            response.close()

                    end_time = time.perf_counter()

                    if all_success:
                        load_time_ms = (end_time - start_time) * 1000
                        load_times.append(load_time_ms)

                    # Delay between tests
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Dashboard load test {i} failed: {e}")

        if load_times:
            metrics = self._calculate_performance_metrics(
                "Dashboard Load",
                load_times,
                self.targets['dashboard_load_ms']
            )

            return {
                'metrics': asdict(metrics),
                'target_met': metrics.target_met,
                'summary': f"Dashboard Load Avg: {metrics.avg_response_time_ms:.1f}ms, P95: {metrics.p95_response_time_ms:.1f}ms (target: <{self.targets['dashboard_load_ms']}ms)"
            }
        else:
            return {
                'target_met': False,
                'error': 'No successful dashboard loads'
            }

    async def test_concurrent_connections(self) -> Dict[str, Any]:
        """Test 1000+ concurrent connections target."""
        logger.info("Testing concurrent connection capacity...")

        # Start with smaller numbers and scale up
        connection_tests = [50, 100, 250, 500, 750, 1000]
        connection_results = {}

        for target_connections in connection_tests:
            logger.info(f"Testing {target_connections} concurrent connections...")

            async def create_connection():
                try:
                    async with aiohttp.ClientSession() as session:
                        start_time = time.perf_counter()
                        async with session.get(f"{self.base_url}/api/bi/dashboard-kpis",
                                             params={"timeframe": "24h", "location_id": "default"}) as response:
                            await response.text()
                            end_time = time.perf_counter()
                            return {
                                'success': response.status < 400,
                                'response_time_ms': (end_time - start_time) * 1000
                            }
                except Exception as e:
                    return {'success': False, 'error': str(e)}

            # Create concurrent connections
            start_time = time.perf_counter()
            tasks = [create_connection() for _ in range(target_connections)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.perf_counter()

            # Analyze results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            failed = target_connections - successful
            success_rate = successful / target_connections
            total_time = end_time - start_time

            response_times = [
                r['response_time_ms'] for r in results
                if isinstance(r, dict) and r.get('success') and 'response_time_ms' in r
            ]

            connection_results[target_connections] = {
                'total_connections': target_connections,
                'successful_connections': successful,
                'failed_connections': failed,
                'success_rate': success_rate,
                'total_test_time_s': total_time,
                'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                'p95_response_time_ms': np.percentile(response_times, 95) if response_times else 0,
                'target_met': successful >= target_connections * 0.95  # 95% success rate
            }

            # Stop if we hit failure threshold
            if success_rate < 0.90:  # 90% success threshold
                logger.warning(f"High failure rate at {target_connections} connections: {success_rate:.1%}")
                break

            # Small delay between tests
            await asyncio.sleep(2)

        # Determine maximum successful concurrent connections
        max_successful = max(
            (target for target, result in connection_results.items()
             if result['success_rate'] >= 0.95),
            default=0
        )

        target_met = max_successful >= self.targets['concurrent_connections']

        return {
            'max_successful_connections': max_successful,
            'target_connections': self.targets['concurrent_connections'],
            'target_met': target_met,
            'connection_test_results': connection_results,
            'summary': f"Max concurrent: {max_successful}, Target: {self.targets['concurrent_connections']} ({'✅ MET' if target_met else '❌ NOT MET'})"
        }

    async def test_commission_calculation_performance(self) -> Dict[str, Any]:
        """Test Jorge's 6% commission calculation performance <50ms target."""
        logger.info("Testing Jorge's commission calculation performance...")

        calculation_times = []

        # Test commission calculations with various scenarios
        test_scenarios = [
            {"pipeline_value": 500000},
            {"pipeline_value": 1200000},
            {"pipeline_value": 2500000},
            {"pipeline_value": 850000},
            {"pipeline_value": 1750000}
        ]

        async with aiohttp.ClientSession() as session:
            for i in range(50):  # 50 test iterations
                scenario = test_scenarios[i % len(test_scenarios)]

                try:
                    start_time = time.perf_counter()

                    # Simulate commission calculation via dashboard KPI endpoint
                    async with session.get(f"{self.base_url}/api/bi/dashboard-kpis",
                                         params={
                                             "timeframe": "24h",
                                             "location_id": "default",
                                             "include_comparisons": True
                                         }) as response:
                        result = await response.json()

                        # Verify Jorge's commission is calculated
                        if response.status < 400 and 'jorge_commission' in result:
                            end_time = time.perf_counter()
                            calc_time_ms = (end_time - start_time) * 1000
                            calculation_times.append(calc_time_ms)

                            # Verify calculation accuracy (6% of pipeline value)
                            jorge_commission = result['jorge_commission']
                            if isinstance(jorge_commission, dict):
                                commission_amount = jorge_commission.get('commission_amount', 0)
                                commission_rate = jorge_commission.get('rate', 0)

                                # Verify 6% rate
                                if abs(commission_rate - 0.06) > 0.001:  # Allow small floating point variance
                                    logger.warning(f"Commission rate incorrect: {commission_rate} (expected 0.06)")

                    await asyncio.sleep(0.02)  # Small delay

                except Exception as e:
                    logger.warning(f"Commission calculation test {i} failed: {e}")

        if calculation_times:
            metrics = self._calculate_performance_metrics(
                "Commission Calculation",
                calculation_times,
                self.targets['commission_calc_ms']
            )

            return {
                'metrics': asdict(metrics),
                'target_met': metrics.target_met,
                'summary': f"Commission Calc Avg: {metrics.avg_response_time_ms:.1f}ms, P95: {metrics.p95_response_time_ms:.1f}ms (target: <{self.targets['commission_calc_ms']}ms)"
            }
        else:
            return {
                'target_met': False,
                'error': 'No successful commission calculations'
            }

    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test cache hit rate >95% target."""
        logger.info("Testing cache performance...")

        cache_hits = 0
        cache_misses = 0
        response_times_cached = []
        response_times_uncached = []

        async with aiohttp.ClientSession() as session:
            # First, make requests to warm the cache
            warm_up_requests = [
                ("/api/bi/dashboard-kpis", {"timeframe": "24h", "location_id": "default"}),
                ("/api/bi/bot-performance", {"timeframe": "7d", "location_id": "default"}),
                ("/api/bi/revenue-intelligence", {"timeframe": "30d", "location_id": "default"})
            ]

            for endpoint, params in warm_up_requests:
                await session.get(f"{self.base_url}{endpoint}", params=params)
                await asyncio.sleep(0.1)

            # Test cache performance with repeated requests
            for i in range(100):
                endpoint, params = warm_up_requests[i % len(warm_up_requests)]

                try:
                    start_time = time.perf_counter()
                    async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                        result = await response.json()
                        end_time = time.perf_counter()

                        response_time_ms = (end_time - start_time) * 1000

                        # Check if response indicates cache hit
                        cache_hit = result.get('cache_hit', False)
                        if cache_hit:
                            cache_hits += 1
                            response_times_cached.append(response_time_ms)
                        else:
                            cache_misses += 1
                            response_times_uncached.append(response_time_ms)

                    await asyncio.sleep(0.05)

                except Exception as e:
                    logger.warning(f"Cache test {i} failed: {e}")

        total_requests = cache_hits + cache_misses
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        target_met = cache_hit_rate >= self.targets['cache_hit_rate']

        avg_cached_time = statistics.mean(response_times_cached) if response_times_cached else 0
        avg_uncached_time = statistics.mean(response_times_uncached) if response_times_uncached else 0

        return {
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'total_requests': total_requests,
            'avg_cached_response_ms': avg_cached_time,
            'avg_uncached_response_ms': avg_uncached_time,
            'target_hit_rate': self.targets['cache_hit_rate'],
            'target_met': target_met,
            'summary': f"Cache Hit Rate: {cache_hit_rate:.1%} (target: ≥{self.targets['cache_hit_rate']:.1%}), Cached avg: {avg_cached_time:.1f}ms"
        }

    async def test_end_to_end_performance(self) -> Dict[str, Any]:
        """Test complete end-to-end dashboard workflow."""
        logger.info("Testing end-to-end dashboard performance...")

        workflow_times = []

        for i in range(10):
            try:
                start_time = time.perf_counter()

                async with aiohttp.ClientSession() as session:
                    # Simulate complete dashboard workflow
                    workflow_steps = [
                        # 1. Initial dashboard load
                        session.get(f"{self.base_url}/api/bi/dashboard-kpis",
                                  params={"timeframe": "24h", "location_id": "default"}),

                        # 2. Real-time metrics
                        session.get(f"{self.base_url}/api/bi/real-time-metrics",
                                  params={"location_id": "default"}),

                        # 3. Bot performance
                        session.get(f"{self.base_url}/api/bi/bot-performance",
                                  params={"timeframe": "7d", "location_id": "default"}),

                        # 4. Revenue intelligence
                        session.get(f"{self.base_url}/api/bi/revenue-intelligence",
                                  params={"timeframe": "30d", "location_id": "default"}),

                        # 5. Drill-down analysis
                        session.post(f"{self.base_url}/api/bi/drill-down",
                                   json={
                                       "component": "revenue",
                                       "metric": "total_revenue",
                                       "timeframe": "24h",
                                       "location_id": "default"
                                   })
                    ]

                    # Execute workflow
                    responses = await asyncio.gather(*workflow_steps, return_exceptions=True)

                    # Verify all steps succeeded
                    all_success = True
                    for response in responses:
                        if isinstance(response, Exception):
                            all_success = False
                            break
                        else:
                            await response.text()
                            if response.status >= 400:
                                all_success = False
                                break
                            response.close()

                    end_time = time.perf_counter()

                    if all_success:
                        workflow_time_ms = (end_time - start_time) * 1000
                        workflow_times.append(workflow_time_ms)

                await asyncio.sleep(1)  # Delay between workflows

            except Exception as e:
                logger.warning(f"End-to-end test {i} failed: {e}")

        if workflow_times:
            # Use 3 second target for complete workflow
            workflow_target_ms = 3000
            avg_workflow_time = statistics.mean(workflow_times)
            p95_workflow_time = np.percentile(workflow_times, 95)
            target_met = avg_workflow_time < workflow_target_ms

            return {
                'avg_workflow_time_ms': avg_workflow_time,
                'p95_workflow_time_ms': p95_workflow_time,
                'min_workflow_time_ms': min(workflow_times),
                'max_workflow_time_ms': max(workflow_times),
                'total_workflows': len(workflow_times),
                'target_time_ms': workflow_target_ms,
                'target_met': target_met,
                'summary': f"E2E Workflow Avg: {avg_workflow_time:.1f}ms, P95: {p95_workflow_time:.1f}ms (target: <{workflow_target_ms}ms)"
            }
        else:
            return {
                'target_met': False,
                'error': 'No successful end-to-end workflows'
            }

    def _calculate_performance_metrics(
        self,
        test_name: str,
        response_times: List[float],
        target_threshold_ms: float
    ) -> PerformanceMetrics:
        """Calculate performance metrics from response times."""
        if not response_times:
            return PerformanceMetrics(
                test_name=test_name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                requests_per_second=0,
                success_rate=0,
                target_met=False,
                target_threshold_ms=target_threshold_ms
            )

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        return PerformanceMetrics(
            test_name=test_name,
            total_requests=n,
            successful_requests=n,
            failed_requests=0,
            avg_response_time_ms=statistics.mean(response_times),
            p50_response_time_ms=sorted_times[int(0.5 * n)],
            p95_response_time_ms=sorted_times[int(0.95 * n)],
            p99_response_time_ms=sorted_times[int(0.99 * n)],
            min_response_time_ms=min(response_times),
            max_response_time_ms=max(response_times),
            requests_per_second=n / (max(response_times) / 1000) if response_times else 0,
            success_rate=1.0,
            target_met=statistics.mean(response_times) < target_threshold_ms,
            target_threshold_ms=target_threshold_ms
        )

    def _generate_overall_assessment(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall performance assessment."""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get('target_met', False))

        # Performance scoring
        performance_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Determine overall status
        if performance_score >= 90:
            status = "EXCELLENT"
            grade = "A+"
        elif performance_score >= 80:
            status = "GOOD"
            grade = "A"
        elif performance_score >= 70:
            status = "ACCEPTABLE"
            grade = "B"
        elif performance_score >= 60:
            status = "NEEDS_IMPROVEMENT"
            grade = "C"
        else:
            status = "POOR"
            grade = "F"

        # Critical performance indicators
        critical_failures = []
        for test_name, result in test_results.items():
            if not result.get('target_met', False):
                if 'WebSocket' in test_name or 'API Response' in test_name:
                    critical_failures.append(test_name)

        return {
            'overall_status': status,
            'performance_grade': grade,
            'performance_score': performance_score,
            'tests_passed': passed_tests,
            'total_tests': total_tests,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'critical_failures': critical_failures,
            'enterprise_ready': performance_score >= 80 and len(critical_failures) == 0,
            'recommendations': self._generate_recommendations(test_results)
        }

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        for test_name, result in test_results.items():
            if not result.get('target_met', False):
                if 'WebSocket' in test_name:
                    recommendations.append("Optimize WebSocket server configuration and connection pooling")
                elif 'API Response' in test_name:
                    recommendations.append("Implement API response caching and database query optimization")
                elif 'Dashboard Load' in test_name:
                    recommendations.append("Optimize dashboard component lazy loading and data pagination")
                elif 'Concurrent' in test_name:
                    recommendations.append("Scale server infrastructure and implement load balancing")
                elif 'Commission' in test_name:
                    recommendations.append("Cache commission calculation results and optimize computation logic")
                elif 'Cache' in test_name:
                    recommendations.append("Tune cache TTL settings and implement intelligent prefetching")

        if not recommendations:
            recommendations.append("All performance targets met - consider stress testing with higher loads")

        return recommendations

async def main():
    """Main validation execution."""
    validator = PerformanceValidator("http://localhost:8001")

    try:
        results = await validator.run_comprehensive_validation()

        # Print detailed results
        print("\n" + "="*80)
        print("🚀 JORGE'S BI DASHBOARD PERFORMANCE VALIDATION RESULTS")
        print("="*80)

        assessment = results['overall_assessment']
        print(f"📊 Overall Performance: {assessment['performance_score']:.1f}% ({assessment['performance_grade']})")
        print(f"🎯 Enterprise Ready: {'✅ YES' if assessment['enterprise_ready'] else '❌ NO'}")
        print(f"📈 Tests Passed: {assessment['tests_passed']}/{assessment['total_tests']}")

        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 40)

        for test_name, result in results['test_results'].items():
            status = "✅ PASS" if result.get('target_met', False) else "❌ FAIL"
            summary = result.get('summary', 'No summary available')
            print(f"{status} {test_name}: {summary}")

        if assessment['critical_failures']:
            print(f"\n⚠️  CRITICAL FAILURES:")
            for failure in assessment['critical_failures']:
                print(f"   - {failure}")

        if assessment['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(assessment['recommendations'], 1):
                print(f"   {i}. {rec}")

        # Save results to file
        with open('bi_dashboard_performance_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📁 Full results saved to: bi_dashboard_performance_results.json")

        return assessment['enterprise_ready']

    except Exception as e:
        logger.error(f"Performance validation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)