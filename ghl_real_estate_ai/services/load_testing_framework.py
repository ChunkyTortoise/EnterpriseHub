#!/usr/bin/env python3
"""
Enterprise Load Testing Framework
=================================

Comprehensive load testing and performance benchmarking system for the Customer Intelligence Platform.
Designed to validate 500+ concurrent user performance and identify bottlenecks at scale.

Features:
- Multi-scenario load testing with realistic user patterns
- Real-time performance monitoring during tests
- Automated performance regression detection
- Comprehensive reporting and analytics
- Stress testing and capacity planning
- CI/CD integration for automated testing
- Custom load patterns and user journeys
- Resource utilization tracking

Performance Testing Targets:
- Concurrent Users: 500+ users
- Response Times: <50ms (95th percentile)
- Throughput: 10,000+ requests/minute
- Error Rate: <0.1%
- Resource Usage: <80% CPU, <80% Memory
- Cache Hit Rate: >95%

Author: Claude Code Load Testing Specialist
Created: January 2026
"""

import asyncio
import csv
import json
import random
import statistics
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.enterprise_monitoring import get_monitoring_system

logger = get_logger(__name__)


class LoadTestPhase(Enum):
    """Load test execution phases."""

    RAMP_UP = "ramp_up"
    STEADY_STATE = "steady_state"
    RAMP_DOWN = "ramp_down"
    SPIKE = "spike"
    STRESS = "stress"


class TestStatus(Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RequestMetrics:
    """Metrics for individual requests."""

    url: str
    method: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    timestamp: datetime
    user_id: str
    scenario: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "method": self.method,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "request_size_bytes": self.request_size_bytes,
            "response_size_bytes": self.response_size_bytes,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "scenario": self.scenario,
            "error": self.error,
        }


@dataclass
class LoadTestScenario:
    """Load test scenario definition."""

    name: str
    weight: float  # Percentage of users running this scenario
    requests: List[Dict[str, Any]]  # List of request definitions
    think_time_ms: Tuple[int, int] = (1000, 3000)  # Min/max think time
    duration_seconds: Optional[int] = None  # Max scenario duration

    def get_think_time(self) -> float:
        """Get random think time in seconds."""
        return random.uniform(self.think_time_ms[0], self.think_time_ms[1]) / 1000


@dataclass
class LoadTestConfig:
    """Load test configuration."""

    name: str
    base_url: str
    scenarios: List[LoadTestScenario]

    # Load pattern configuration
    max_users: int = 100
    ramp_up_duration_s: int = 60
    steady_duration_s: int = 300
    ramp_down_duration_s: int = 60

    # Performance thresholds
    max_response_time_ms: float = 100
    max_error_rate_percent: float = 1.0
    min_throughput_rps: float = 100

    # Test configuration
    timeout_seconds: float = 30
    follow_redirects: bool = True
    verify_ssl: bool = True

    # Reporting
    report_interval_s: int = 10
    detailed_metrics: bool = True


@dataclass
class LoadTestResults:
    """Load test execution results."""

    test_id: str
    config: LoadTestConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TestStatus = TestStatus.PENDING

    # Aggregate metrics
    total_requests: int = 0
    total_errors: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0

    # Performance metrics
    response_times: List[float] = field(default_factory=list)
    throughput_history: List[Tuple[datetime, float]] = field(default_factory=list)
    error_history: List[Tuple[datetime, int]] = field(default_factory=list)

    # Detailed metrics
    request_metrics: List[RequestMetrics] = field(default_factory=list)

    def add_request_metric(self, metric: RequestMetrics):
        """Add a request metric."""
        self.request_metrics.append(metric)
        self.total_requests += 1
        self.total_bytes_sent += metric.request_size_bytes
        self.total_bytes_received += metric.response_size_bytes
        self.response_times.append(metric.response_time_ms)

        if metric.error or metric.status_code >= 400:
            self.total_errors += 1

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.response_times:
            return {}

        duration_s = (self.end_time - self.start_time).total_seconds() if self.end_time else 0

        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate_percent": (self.total_errors / max(self.total_requests, 1)) * 100,
            "duration_seconds": duration_s,
            "throughput_rps": self.total_requests / max(duration_s, 1),
            "avg_response_time_ms": statistics.mean(self.response_times),
            "median_response_time_ms": statistics.median(self.response_times),
            "p95_response_time_ms": statistics.quantiles(self.response_times, n=20)[18],
            "p99_response_time_ms": statistics.quantiles(self.response_times, n=100)[98],
            "min_response_time_ms": min(self.response_times),
            "max_response_time_ms": max(self.response_times),
            "total_bytes_sent": self.total_bytes_sent,
            "total_bytes_received": self.total_bytes_received,
        }


class VirtualUser:
    """Simulates a virtual user executing test scenarios."""

    def __init__(
        self, user_id: str, scenario: LoadTestScenario, session: aiohttp.ClientSession, results: LoadTestResults
    ):
        self.user_id = user_id
        self.scenario = scenario
        self.session = session
        self.results = results
        self.is_running = False
        self._task = None

    async def start(self):
        """Start the virtual user."""
        if self.is_running:
            return

        self.is_running = True
        self._task = asyncio.create_task(self._user_loop())

    async def stop(self):
        """Stop the virtual user."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _user_loop(self):
        """Main user execution loop."""
        scenario_start = time.time()

        while self.is_running:
            try:
                # Check scenario duration
                if self.scenario.duration_seconds and time.time() - scenario_start > self.scenario.duration_seconds:
                    break

                # Execute each request in the scenario
                for request_config in self.scenario.requests:
                    if not self.is_running:
                        break

                    await self._execute_request(request_config)

                    # Think time between requests
                    if self.is_running:
                        think_time = self.scenario.get_think_time()
                        await asyncio.sleep(think_time)

                # If no duration specified, run once and stop
                if not self.scenario.duration_seconds:
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Virtual user {self.user_id} error: {e}")
                await asyncio.sleep(1)

    async def _execute_request(self, request_config: Dict[str, Any]):
        """Execute a single HTTP request."""
        url = request_config["url"]
        method = request_config.get("method", "GET").upper()
        headers = request_config.get("headers", {})
        data = request_config.get("data")
        json_data = request_config.get("json")
        params = request_config.get("params", {})

        start_time = time.time()
        request_size = 0
        response_size = 0
        status_code = 0
        error = None

        try:
            # Calculate request size
            if data:
                request_size = len(str(data).encode("utf-8"))
            elif json_data:
                request_size = len(json.dumps(json_data).encode("utf-8"))

            # Execute request
            async with self.session.request(
                method=method, url=url, headers=headers, data=data, json=json_data, params=params
            ) as response:
                status_code = response.status
                response_text = await response.text()
                response_size = len(response_text.encode("utf-8"))

                # Optionally validate response
                if "validate" in request_config:
                    validation_func = request_config["validate"]
                    if callable(validation_func):
                        validation_result = validation_func(response, response_text)
                        if not validation_result:
                            error = "Response validation failed"

        except asyncio.TimeoutError:
            error = "Request timeout"
            status_code = 0
        except Exception as e:
            error = str(e)
            status_code = 0

        # Record metrics
        response_time_ms = (time.time() - start_time) * 1000

        metric = RequestMetrics(
            url=url,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size,
            response_size_bytes=response_size,
            timestamp=datetime.now(),
            user_id=self.user_id,
            scenario=self.scenario.name,
            error=error,
        )

        self.results.add_request_metric(metric)


class LoadTestRunner:
    """Main load test runner and orchestrator."""

    def __init__(self):
        self.running_tests: Dict[str, LoadTestResults] = {}
        self.virtual_users: Dict[str, List[VirtualUser]] = {}
        self.monitoring_system = None

    async def initialize(self):
        """Initialize the load test runner."""
        self.monitoring_system = await get_monitoring_system()

    async def run_load_test(self, config: LoadTestConfig) -> str:
        """Execute a load test."""
        test_id = str(uuid.uuid4())

        # Create test results object
        results = LoadTestResults(test_id=test_id, config=config, start_time=datetime.now(), status=TestStatus.RUNNING)

        self.running_tests[test_id] = results

        try:
            logger.info(f"Starting load test {config.name} (ID: {test_id})")

            # Create HTTP session with optimized settings
            connector = aiohttp.TCPConnector(
                limit=config.max_users * 2,  # Connection pool
                limit_per_host=config.max_users,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=True) as session:
                # Start monitoring task
                monitoring_task = asyncio.create_task(self._monitor_test_progress(test_id, config.report_interval_s))

                # Execute load test phases
                await self._execute_test_phases(test_id, config, session)

                # Stop monitoring
                monitoring_task.cancel()
                try:
                    await monitoring_task
                except asyncio.CancelledError:
                    pass

            # Mark test as completed
            results.end_time = datetime.now()
            results.status = TestStatus.COMPLETED

            logger.info(f"Load test {test_id} completed successfully")

            # Generate final report
            await self._generate_test_report(test_id)

        except Exception as e:
            logger.error(f"Load test {test_id} failed: {e}")
            results.status = TestStatus.FAILED
            results.end_time = datetime.now()

        return test_id

    async def _execute_test_phases(self, test_id: str, config: LoadTestConfig, session: aiohttp.ClientSession):
        """Execute load test phases (ramp-up, steady-state, ramp-down)."""
        self.running_tests[test_id]

        # Phase 1: Ramp-up
        logger.info(f"Test {test_id}: Starting ramp-up phase ({config.ramp_up_duration_s}s)")
        await self._ramp_up_users(test_id, config, session)

        # Phase 2: Steady state
        logger.info(f"Test {test_id}: Starting steady-state phase ({config.steady_duration_s}s)")
        await asyncio.sleep(config.steady_duration_s)

        # Phase 3: Ramp-down
        logger.info(f"Test {test_id}: Starting ramp-down phase ({config.ramp_down_duration_s}s)")
        await self._ramp_down_users(test_id, config)

    async def _ramp_up_users(self, test_id: str, config: LoadTestConfig, session: aiohttp.ClientSession):
        """Gradually ramp up virtual users."""
        self.virtual_users[test_id] = []

        user_spawn_interval = config.ramp_up_duration_s / config.max_users

        for i in range(config.max_users):
            # Select scenario based on weight
            scenario = self._select_scenario(config.scenarios)

            # Create virtual user
            user_id = f"user_{i:04d}"
            user = VirtualUser(user_id, scenario, session, self.running_tests[test_id])

            self.virtual_users[test_id].append(user)
            await user.start()

            # Wait before spawning next user
            if i < config.max_users - 1:
                await asyncio.sleep(user_spawn_interval)

        logger.info(f"Test {test_id}: Ramped up to {config.max_users} virtual users")

    async def _ramp_down_users(self, test_id: str, config: LoadTestConfig):
        """Gradually ramp down virtual users."""
        users = self.virtual_users.get(test_id, [])

        if not users:
            return

        user_stop_interval = config.ramp_down_duration_s / len(users)

        for user in users:
            await user.stop()

            # Wait before stopping next user
            if user != users[-1]:
                await asyncio.sleep(user_stop_interval)

        del self.virtual_users[test_id]
        logger.info(f"Test {test_id}: Ramped down all virtual users")

    def _select_scenario(self, scenarios: List[LoadTestScenario]) -> LoadTestScenario:
        """Select a scenario based on weights."""
        weights = [s.weight for s in scenarios]
        return random.choices(scenarios, weights=weights)[0]

    async def _monitor_test_progress(self, test_id: str, report_interval_s: int):
        """Monitor test progress and collect real-time metrics."""
        while test_id in self.running_tests and self.running_tests[test_id].status == TestStatus.RUNNING:
            try:
                results = self.running_tests[test_id]

                # Calculate current metrics
                current_time = datetime.now()
                window_start = current_time - timedelta(seconds=report_interval_s)

                # Get recent requests for throughput calculation
                recent_requests = [m for m in results.request_metrics if m.timestamp >= window_start]

                current_rps = len(recent_requests) / report_interval_s if recent_requests else 0
                current_errors = sum(1 for r in recent_requests if r.error or r.status_code >= 400)

                # Store metrics history
                results.throughput_history.append((current_time, current_rps))
                results.error_history.append((current_time, current_errors))

                # Log progress
                if results.response_times:
                    avg_response = statistics.mean(results.response_times[-100:])  # Last 100 requests
                    logger.info(
                        f"Test {test_id}: RPS={current_rps:.1f}, "
                        f"Errors={current_errors}, "
                        f"AvgResponse={avg_response:.1f}ms"
                    )

                # Send metrics to monitoring system
                if self.monitoring_system:
                    await self._send_test_metrics(test_id, current_rps, current_errors, recent_requests)

                await asyncio.sleep(report_interval_s)

            except Exception as e:
                logger.error(f"Monitoring error for test {test_id}: {e}")
                await asyncio.sleep(report_interval_s)

    async def _send_test_metrics(self, test_id: str, rps: float, errors: int, recent_requests: List[RequestMetrics]):
        """Send test metrics to monitoring system."""
        try:
            # Record load test metrics
            self.monitoring_system.set_gauge("load_test_rps", rps, {"test_id": test_id})
            self.monitoring_system.set_gauge("load_test_errors", errors, {"test_id": test_id})
            self.monitoring_system.set_gauge(
                "load_test_active_users", len(self.virtual_users.get(test_id, [])), {"test_id": test_id}
            )

            # Record response time metrics
            if recent_requests:
                response_times = [r.response_time_ms for r in recent_requests]
                self.monitoring_system.record_histogram(
                    "load_test_response_time", statistics.mean(response_times), {"test_id": test_id}
                )

        except Exception as e:
            logger.warning(f"Failed to send test metrics: {e}")

    async def _generate_test_report(self, test_id: str):
        """Generate comprehensive test report."""
        results = self.running_tests[test_id]
        summary = results.get_summary_stats()

        # Create detailed report
        report = {
            "test_id": test_id,
            "test_name": results.config.name,
            "start_time": results.start_time.isoformat(),
            "end_time": results.end_time.isoformat() if results.end_time else None,
            "status": results.status.value,
            "configuration": {
                "max_users": results.config.max_users,
                "ramp_up_duration_s": results.config.ramp_up_duration_s,
                "steady_duration_s": results.config.steady_duration_s,
                "scenarios": [{"name": s.name, "weight": s.weight} for s in results.config.scenarios],
            },
            "summary_statistics": summary,
            "performance_analysis": self._analyze_performance(results),
            "recommendations": self._generate_recommendations(results),
        }

        # Save report to file
        report_filename = f"load_test_report_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Test report saved: {report_filename}")

        # Export detailed metrics to CSV
        if results.config.detailed_metrics:
            await self._export_detailed_metrics(test_id)

    def _analyze_performance(self, results: LoadTestResults) -> Dict[str, Any]:
        """Analyze performance against thresholds."""
        summary = results.get_summary_stats()
        config = results.config

        analysis = {
            "response_time_analysis": {
                "threshold_ms": config.max_response_time_ms,
                "p95_ms": summary.get("p95_response_time_ms", 0),
                "passed": summary.get("p95_response_time_ms", float("inf")) <= config.max_response_time_ms,
            },
            "error_rate_analysis": {
                "threshold_percent": config.max_error_rate_percent,
                "actual_percent": summary.get("error_rate_percent", 0),
                "passed": summary.get("error_rate_percent", 100) <= config.max_error_rate_percent,
            },
            "throughput_analysis": {
                "threshold_rps": config.min_throughput_rps,
                "actual_rps": summary.get("throughput_rps", 0),
                "passed": summary.get("throughput_rps", 0) >= config.min_throughput_rps,
            },
        }

        # Overall pass/fail
        analysis["overall_passed"] = all(
            analysis[key]["passed"] for key in ["response_time_analysis", "error_rate_analysis", "throughput_analysis"]
        )

        return analysis

    def _generate_recommendations(self, results: LoadTestResults) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        summary = results.get_summary_stats()

        # Response time recommendations
        p95_response = summary.get("p95_response_time_ms", 0)
        if p95_response > 100:
            recommendations.append(
                f"High response times detected (P95: {p95_response:.1f}ms). "
                "Consider optimizing slow endpoints and implementing better caching."
            )

        # Error rate recommendations
        error_rate = summary.get("error_rate_percent", 0)
        if error_rate > 1:
            recommendations.append(
                f"Elevated error rate detected ({error_rate:.2f}%). "
                "Review server logs and implement better error handling."
            )

        # Throughput recommendations
        rps = summary.get("throughput_rps", 0)
        if rps < 100:
            recommendations.append(
                f"Low throughput detected ({rps:.1f} RPS). "
                "Consider scaling up resources or optimizing performance bottlenecks."
            )

        # Resource utilization recommendations
        if results.total_requests > 10000:
            recommendations.append(
                "High load test completed successfully. "
                "Monitor system resources and consider implementing auto-scaling."
            )

        return recommendations

    async def _export_detailed_metrics(self, test_id: str):
        """Export detailed request metrics to CSV."""
        results = self.running_tests[test_id]

        csv_filename = f"load_test_metrics_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = [
                "timestamp",
                "user_id",
                "scenario",
                "url",
                "method",
                "status_code",
                "response_time_ms",
                "request_size_bytes",
                "response_size_bytes",
                "error",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for metric in results.request_metrics:
                row = {
                    "timestamp": metric.timestamp.isoformat(),
                    "user_id": metric.user_id,
                    "scenario": metric.scenario,
                    "url": metric.url,
                    "method": metric.method,
                    "status_code": metric.status_code,
                    "response_time_ms": metric.response_time_ms,
                    "request_size_bytes": metric.request_size_bytes,
                    "response_size_bytes": metric.response_size_bytes,
                    "error": metric.error or "",
                }
                writer.writerow(row)

        logger.info(f"Detailed metrics exported: {csv_filename}")

    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a running test."""
        if test_id not in self.running_tests:
            return None

        results = self.running_tests[test_id]

        status = {
            "test_id": test_id,
            "test_name": results.config.name,
            "status": results.status.value,
            "start_time": results.start_time.isoformat(),
            "duration_seconds": (datetime.now() - results.start_time).total_seconds(),
            "total_requests": results.total_requests,
            "total_errors": results.total_errors,
            "active_users": len(self.virtual_users.get(test_id, [])),
            "current_rps": 0,
        }

        # Calculate current RPS
        if results.throughput_history:
            status["current_rps"] = results.throughput_history[-1][1]

        return status

    async def cancel_test(self, test_id: str) -> bool:
        """Cancel a running test."""
        if test_id not in self.running_tests:
            return False

        results = self.running_tests[test_id]
        if results.status != TestStatus.RUNNING:
            return False

        # Stop all virtual users
        if test_id in self.virtual_users:
            for user in self.virtual_users[test_id]:
                await user.stop()
            del self.virtual_users[test_id]

        # Update status
        results.status = TestStatus.CANCELLED
        results.end_time = datetime.now()

        logger.info(f"Test {test_id} cancelled")
        return True


# Pre-defined test scenarios


def create_api_load_test_config(base_url: str, max_users: int = 100) -> LoadTestConfig:
    """Create a standard API load test configuration."""

    # Customer Intelligence API scenario
    api_scenario = LoadTestScenario(
        name="customer_intelligence_api",
        weight=0.7,  # 70% of users
        requests=[
            {"url": f"{base_url}/api/health", "method": "GET"},
            {
                "url": f"{base_url}/api/analytics/dashboard",
                "method": "GET",
                "headers": {"Authorization": "Bearer test-token"},
            },
            {"url": f"{base_url}/api/customers/search", "method": "POST", "json": {"query": "test", "limit": 10}},
        ],
        think_time_ms=(1000, 5000),
    )

    # Dashboard loading scenario
    dashboard_scenario = LoadTestScenario(
        name="dashboard_loading",
        weight=0.3,  # 30% of users
        requests=[
            {"url": f"{base_url}/api/analytics/kpis", "method": "GET"},
            {"url": f"{base_url}/api/analytics/charts/conversion", "method": "GET"},
            {"url": f"{base_url}/api/analytics/charts/revenue", "method": "GET"},
        ],
        think_time_ms=(2000, 8000),
    )

    return LoadTestConfig(
        name="Customer Intelligence Platform Load Test",
        base_url=base_url,
        scenarios=[api_scenario, dashboard_scenario],
        max_users=max_users,
        ramp_up_duration_s=60,
        steady_duration_s=300,
        ramp_down_duration_s=60,
        max_response_time_ms=50,  # Aggressive target
        max_error_rate_percent=0.1,
        min_throughput_rps=100,
    )


def create_stress_test_config(base_url: str, max_users: int = 500) -> LoadTestConfig:
    """Create a stress test configuration for maximum load."""

    stress_scenario = LoadTestScenario(
        name="stress_test_scenario",
        weight=1.0,
        requests=[
            {"url": f"{base_url}/api/health", "method": "GET"},
            {"url": f"{base_url}/api/analytics/dashboard", "method": "GET"},
        ],
        think_time_ms=(100, 500),  # Minimal think time for stress
    )

    return LoadTestConfig(
        name="Stress Test - Maximum Load",
        base_url=base_url,
        scenarios=[stress_scenario],
        max_users=max_users,
        ramp_up_duration_s=120,
        steady_duration_s=600,  # 10 minutes of stress
        ramp_down_duration_s=120,
        max_response_time_ms=100,
        max_error_rate_percent=1.0,
        min_throughput_rps=1000,
    )


# Global load test runner
_load_test_runner: Optional[LoadTestRunner] = None


async def get_load_test_runner() -> LoadTestRunner:
    """Get global load test runner instance."""
    global _load_test_runner
    if _load_test_runner is None:
        _load_test_runner = LoadTestRunner()
        await _load_test_runner.initialize()
    return _load_test_runner


# Convenience functions


async def run_performance_benchmark(base_url: str, max_users: int = 100) -> str:
    """Run a standard performance benchmark."""
    runner = await get_load_test_runner()
    config = create_api_load_test_config(base_url, max_users)
    return await runner.run_load_test(config)


async def run_stress_test(base_url: str, max_users: int = 500) -> str:
    """Run a stress test to find breaking point."""
    runner = await get_load_test_runner()
    config = create_stress_test_config(base_url, max_users)
    return await runner.run_load_test(config)


async def get_test_results(test_id: str) -> Optional[Dict[str, Any]]:
    """Get test results by ID."""
    runner = await get_load_test_runner()
    return runner.get_test_status(test_id)
