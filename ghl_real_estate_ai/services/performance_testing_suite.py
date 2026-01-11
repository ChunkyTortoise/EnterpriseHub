"""
Performance Testing and Validation Suite
========================================

Comprehensive performance testing framework for validating the Agent Enhancement
System optimizations with load testing, stress testing, and performance regression
detection.
"""

import asyncio
import logging
import time
import random
import json
import statistics
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiofiles
import psutil

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of performance tests"""
    LOAD_TEST = "load_test"              # Normal expected load
    STRESS_TEST = "stress_test"          # Beyond normal capacity
    SPIKE_TEST = "spike_test"            # Sudden load spikes
    VOLUME_TEST = "volume_test"          # Large data volumes
    ENDURANCE_TEST = "endurance_test"    # Extended duration
    BASELINE_TEST = "baseline_test"      # Performance baseline


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TestConfiguration:
    """Configuration for a performance test"""
    name: str
    test_type: TestType
    duration_seconds: int
    concurrent_users: int
    requests_per_second: float
    ramp_up_seconds: int = 60
    ramp_down_seconds: int = 60
    test_data: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, float] = field(default_factory=dict)


@dataclass
class TestMetric:
    """Individual test metric measurement"""
    timestamp: datetime
    operation: str
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    payload_size: int = 0
    user_id: int = 0


@dataclass
class TestResult:
    """Results from a performance test"""
    test_config: TestConfiguration
    start_time: datetime
    end_time: datetime
    status: TestStatus
    metrics: List[TestMetric] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class LoadGenerator:
    """
    Generates realistic load patterns for performance testing
    """

    def __init__(self):
        self.active_users: Dict[int, Dict] = {}
        self.test_scenarios: Dict[str, Callable] = {}

    def register_scenario(self, name: str, scenario_func: Callable) -> None:
        """Register a test scenario"""
        self.test_scenarios[name] = scenario_func
        logger.info(f"Registered test scenario: {name}")

    async def generate_load(self,
                          config: TestConfiguration,
                          progress_callback: Optional[Callable] = None) -> List[TestMetric]:
        """Generate load according to test configuration"""

        metrics = []
        tasks = []

        logger.info(f"Starting load generation: {config.name}")
        logger.info(f"Target: {config.concurrent_users} users, {config.requests_per_second} RPS")

        try:
            # Calculate timing parameters
            total_requests = int(config.requests_per_second * config.duration_seconds)
            request_interval = 1.0 / config.requests_per_second if config.requests_per_second > 0 else 1.0

            # Ramp up phase
            if config.ramp_up_seconds > 0:
                await self._ramp_up_phase(config, metrics, progress_callback)

            # Main load phase
            start_time = time.time()
            request_count = 0

            while (time.time() - start_time) < config.duration_seconds:
                # Create batch of concurrent requests
                batch_size = min(config.concurrent_users, total_requests - request_count)

                if batch_size <= 0:
                    break

                batch_tasks = []
                for user_id in range(batch_size):
                    task = asyncio.create_task(
                        self._simulate_user_request(config, user_id, metrics)
                    )
                    batch_tasks.append(task)

                # Execute batch
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                request_count += batch_size

                # Progress reporting
                if progress_callback:
                    progress = (time.time() - start_time) / config.duration_seconds
                    await progress_callback(progress, len(metrics))

                # Control request rate
                await asyncio.sleep(request_interval)

            # Ramp down phase
            if config.ramp_down_seconds > 0:
                await self._ramp_down_phase(config, metrics, progress_callback)

        except Exception as e:
            logger.error(f"Load generation error: {e}")
            raise

        logger.info(f"Load generation completed: {len(metrics)} requests processed")
        return metrics

    async def _ramp_up_phase(self,
                           config: TestConfiguration,
                           metrics: List[TestMetric],
                           progress_callback: Optional[Callable]) -> None:
        """Gradual ramp up of load"""
        logger.info(f"Ramp up phase: {config.ramp_up_seconds} seconds")

        ramp_steps = min(config.ramp_up_seconds, config.concurrent_users)
        users_per_step = config.concurrent_users / ramp_steps
        step_duration = config.ramp_up_seconds / ramp_steps

        for step in range(ramp_steps):
            current_users = int((step + 1) * users_per_step)

            # Generate requests for current user count
            tasks = []
            for user_id in range(current_users):
                task = asyncio.create_task(
                    self._simulate_user_request(config, user_id, metrics)
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            if progress_callback:
                progress = (step + 1) / ramp_steps * 0.1  # 10% of total for ramp up
                await progress_callback(progress, len(metrics))

            await asyncio.sleep(step_duration)

    async def _ramp_down_phase(self,
                             config: TestConfiguration,
                             metrics: List[TestMetric],
                             progress_callback: Optional[Callable]) -> None:
        """Gradual ramp down of load"""
        logger.info(f"Ramp down phase: {config.ramp_down_seconds} seconds")

        ramp_steps = min(config.ramp_down_seconds, config.concurrent_users)
        step_duration = config.ramp_down_seconds / ramp_steps

        for step in range(ramp_steps):
            # Gradually reduce load
            remaining_fraction = (ramp_steps - step) / ramp_steps
            current_users = int(config.concurrent_users * remaining_fraction)

            if current_users > 0:
                tasks = []
                for user_id in range(current_users):
                    task = asyncio.create_task(
                        self._simulate_user_request(config, user_id, metrics)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(step_duration)

    async def _simulate_user_request(self,
                                   config: TestConfiguration,
                                   user_id: int,
                                   metrics: List[TestMetric]) -> None:
        """Simulate a single user request"""

        start_time = time.time()
        success = True
        error_message = None
        operation = "unknown"

        try:
            # Select scenario to execute
            scenario_name = config.test_data.get("scenario", "default")
            scenario_func = self.test_scenarios.get(scenario_name, self._default_scenario)

            # Execute scenario
            operation, result = await scenario_func(config, user_id)

            if isinstance(result, dict) and result.get("error"):
                success = False
                error_message = result["error"]

        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"User {user_id} request failed: {e}")

        # Record metric
        response_time = (time.time() - start_time) * 1000
        metric = TestMetric(
            timestamp=datetime.now(),
            operation=operation,
            response_time_ms=response_time,
            success=success,
            error_message=error_message,
            user_id=user_id
        )

        metrics.append(metric)

    async def _default_scenario(self, config: TestConfiguration, user_id: int) -> tuple[str, Any]:
        """Default test scenario"""
        # Simulate some work
        await asyncio.sleep(random.uniform(0.1, 0.5))
        return "default_operation", {"status": "completed", "user_id": user_id}


class PerformanceValidator:
    """
    Validates performance test results against criteria and baselines
    """

    def __init__(self):
        self.baseline_results: Dict[str, TestResult] = {}
        self.performance_thresholds: Dict[str, Dict[str, float]] = {
            "response_time": {
                "p95_ms": 1000,
                "p99_ms": 2000,
                "avg_ms": 500
            },
            "throughput": {
                "min_rps": 10,
                "target_rps": 50
            },
            "error_rate": {
                "max_percent": 5.0
            },
            "resource_usage": {
                "max_cpu_percent": 80,
                "max_memory_percent": 85
            }
        }

    def validate_results(self, test_result: TestResult) -> Dict[str, Any]:
        """Validate test results against criteria"""

        validation_report = {
            "test_name": test_result.test_config.name,
            "overall_pass": True,
            "validations": {},
            "performance_improvements": {},
            "recommendations": []
        }

        # Calculate performance statistics
        stats = self._calculate_performance_stats(test_result.metrics)
        test_result.summary_stats = stats

        # Validate response times
        response_time_validation = self._validate_response_times(stats)
        validation_report["validations"]["response_time"] = response_time_validation

        if not response_time_validation["pass"]:
            validation_report["overall_pass"] = False

        # Validate error rates
        error_rate_validation = self._validate_error_rates(stats)
        validation_report["validations"]["error_rate"] = error_rate_validation

        if not error_rate_validation["pass"]:
            validation_report["overall_pass"] = False

        # Validate throughput
        throughput_validation = self._validate_throughput(stats, test_result.test_config)
        validation_report["validations"]["throughput"] = throughput_validation

        if not throughput_validation["pass"]:
            validation_report["overall_pass"] = False

        # Compare against baseline if available
        baseline_comparison = self._compare_against_baseline(test_result)
        if baseline_comparison:
            validation_report["performance_improvements"] = baseline_comparison

        # Generate recommendations
        validation_report["recommendations"] = self._generate_recommendations(stats, test_result)

        return validation_report

    def _calculate_performance_stats(self, metrics: List[TestMetric]) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics"""

        if not metrics:
            return {}

        response_times = [m.response_time_ms for m in metrics]
        successful_requests = [m for m in metrics if m.success]
        failed_requests = [m for m in metrics if not m.success]

        # Calculate response time statistics
        response_times.sort()
        total_requests = len(metrics)

        stats = {
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "error_rate_percent": (len(failed_requests) / total_requests) * 100 if total_requests > 0 else 0,

            # Response time metrics
            "response_time": {
                "min_ms": min(response_times) if response_times else 0,
                "max_ms": max(response_times) if response_times else 0,
                "avg_ms": statistics.mean(response_times) if response_times else 0,
                "median_ms": statistics.median(response_times) if response_times else 0,
                "p95_ms": self._percentile(response_times, 95) if response_times else 0,
                "p99_ms": self._percentile(response_times, 99) if response_times else 0,
                "stddev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        }

        # Calculate throughput
        if metrics:
            duration = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
            stats["throughput_rps"] = total_requests / max(duration, 1)
        else:
            stats["throughput_rps"] = 0

        # Operation breakdown
        operation_stats = {}
        for metric in metrics:
            if metric.operation not in operation_stats:
                operation_stats[metric.operation] = {
                    "count": 0,
                    "avg_response_time": 0,
                    "error_rate": 0
                }

            op_stats = operation_stats[metric.operation]
            op_stats["count"] += 1

            # Update running average
            current_avg = op_stats["avg_response_time"]
            new_avg = current_avg + (metric.response_time_ms - current_avg) / op_stats["count"]
            op_stats["avg_response_time"] = new_avg

            if not metric.success:
                op_stats["error_rate"] = (op_stats["error_rate"] * (op_stats["count"] - 1) + 100) / op_stats["count"]
            else:
                op_stats["error_rate"] = op_stats["error_rate"] * (op_stats["count"] - 1) / op_stats["count"]

        stats["operations"] = operation_stats

        return stats

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0

        data_sorted = sorted(data)
        index = (percentile / 100) * (len(data_sorted) - 1)

        if index.is_integer():
            return data_sorted[int(index)]
        else:
            lower = data_sorted[int(index)]
            upper = data_sorted[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def _validate_response_times(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response time metrics"""

        response_time_stats = stats.get("response_time", {})
        thresholds = self.performance_thresholds["response_time"]

        validation = {
            "pass": True,
            "details": {},
            "failures": []
        }

        # Check average response time
        avg_ms = response_time_stats.get("avg_ms", 0)
        if avg_ms > thresholds["avg_ms"]:
            validation["pass"] = False
            validation["failures"].append(f"Average response time {avg_ms:.1f}ms exceeds threshold {thresholds['avg_ms']}ms")

        # Check P95 response time
        p95_ms = response_time_stats.get("p95_ms", 0)
        if p95_ms > thresholds["p95_ms"]:
            validation["pass"] = False
            validation["failures"].append(f"P95 response time {p95_ms:.1f}ms exceeds threshold {thresholds['p95_ms']}ms")

        # Check P99 response time
        p99_ms = response_time_stats.get("p99_ms", 0)
        if p99_ms > thresholds["p99_ms"]:
            validation["pass"] = False
            validation["failures"].append(f"P99 response time {p99_ms:.1f}ms exceeds threshold {thresholds['p99_ms']}ms")

        validation["details"] = {
            "avg_ms": avg_ms,
            "p95_ms": p95_ms,
            "p99_ms": p99_ms,
            "thresholds": thresholds
        }

        return validation

    def _validate_error_rates(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Validate error rate metrics"""

        error_rate = stats.get("error_rate_percent", 0)
        threshold = self.performance_thresholds["error_rate"]["max_percent"]

        validation = {
            "pass": error_rate <= threshold,
            "details": {
                "error_rate_percent": error_rate,
                "threshold_percent": threshold,
                "total_errors": stats.get("failed_requests", 0),
                "total_requests": stats.get("total_requests", 0)
            },
            "failures": []
        }

        if not validation["pass"]:
            validation["failures"].append(f"Error rate {error_rate:.2f}% exceeds threshold {threshold}%")

        return validation

    def _validate_throughput(self, stats: Dict[str, Any], config: TestConfiguration) -> Dict[str, Any]:
        """Validate throughput metrics"""

        actual_rps = stats.get("throughput_rps", 0)
        target_rps = config.requests_per_second
        min_rps = self.performance_thresholds["throughput"]["min_rps"]

        validation = {
            "pass": actual_rps >= min_rps,
            "details": {
                "actual_rps": actual_rps,
                "target_rps": target_rps,
                "min_rps": min_rps,
                "efficiency_percent": (actual_rps / target_rps) * 100 if target_rps > 0 else 0
            },
            "failures": []
        }

        if actual_rps < min_rps:
            validation["pass"] = False
            validation["failures"].append(f"Throughput {actual_rps:.2f} RPS below minimum {min_rps} RPS")

        return validation

    def _compare_against_baseline(self, test_result: TestResult) -> Optional[Dict[str, Any]]:
        """Compare results against baseline performance"""

        test_name = test_result.test_config.name
        baseline_key = f"{test_name}_baseline"

        if baseline_key not in self.baseline_results:
            return None

        baseline = self.baseline_results[baseline_key]
        current_stats = test_result.summary_stats
        baseline_stats = baseline.summary_stats

        comparison = {
            "baseline_date": baseline.start_time.isoformat(),
            "improvements": {},
            "regressions": {}
        }

        # Compare response times
        current_avg = current_stats["response_time"]["avg_ms"]
        baseline_avg = baseline_stats["response_time"]["avg_ms"]

        if current_avg < baseline_avg:
            improvement_percent = ((baseline_avg - current_avg) / baseline_avg) * 100
            comparison["improvements"]["response_time"] = {
                "metric": "average_response_time_ms",
                "improvement_percent": improvement_percent,
                "current": current_avg,
                "baseline": baseline_avg
            }
        elif current_avg > baseline_avg:
            regression_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
            comparison["regressions"]["response_time"] = {
                "metric": "average_response_time_ms",
                "regression_percent": regression_percent,
                "current": current_avg,
                "baseline": baseline_avg
            }

        # Compare throughput
        current_rps = current_stats["throughput_rps"]
        baseline_rps = baseline_stats["throughput_rps"]

        if current_rps > baseline_rps:
            improvement_percent = ((current_rps - baseline_rps) / baseline_rps) * 100
            comparison["improvements"]["throughput"] = {
                "metric": "throughput_rps",
                "improvement_percent": improvement_percent,
                "current": current_rps,
                "baseline": baseline_rps
            }
        elif current_rps < baseline_rps:
            regression_percent = ((baseline_rps - current_rps) / baseline_rps) * 100
            comparison["regressions"]["throughput"] = {
                "metric": "throughput_rps",
                "regression_percent": regression_percent,
                "current": current_rps,
                "baseline": baseline_rps
            }

        return comparison

    def _generate_recommendations(self, stats: Dict[str, Any], test_result: TestResult) -> List[str]:
        """Generate optimization recommendations based on test results"""

        recommendations = []

        # Response time recommendations
        response_time_stats = stats.get("response_time", {})
        avg_response_time = response_time_stats.get("avg_ms", 0)

        if avg_response_time > 1000:
            recommendations.append("Consider implementing request caching to reduce response times")
            recommendations.append("Review database query optimization opportunities")

        if avg_response_time > 500:
            recommendations.append("Implement connection pooling for external API calls")

        # Error rate recommendations
        error_rate = stats.get("error_rate_percent", 0)
        if error_rate > 2:
            recommendations.append("Implement circuit breakers to handle service failures")
            recommendations.append("Add retry logic with exponential backoff")

        if error_rate > 5:
            recommendations.append("Review system capacity and scaling requirements")

        # Throughput recommendations
        throughput = stats.get("throughput_rps", 0)
        target_throughput = test_result.test_config.requests_per_second

        if throughput < target_throughput * 0.8:  # Less than 80% of target
            recommendations.append("Consider horizontal scaling to increase throughput")
            recommendations.append("Review async processing opportunities")

        # Resource utilization recommendations
        system_metrics = test_result.system_metrics
        if system_metrics.get("max_cpu_percent", 0) > 80:
            recommendations.append("High CPU usage detected - consider CPU optimization")

        if system_metrics.get("max_memory_percent", 0) > 80:
            recommendations.append("High memory usage detected - review memory leaks and caching")

        return recommendations

    def set_baseline(self, test_result: TestResult) -> None:
        """Set test result as baseline for future comparisons"""
        baseline_key = f"{test_result.test_config.name}_baseline"
        self.baseline_results[baseline_key] = test_result
        logger.info(f"Set baseline for test: {test_result.test_config.name}")


class SystemResourceMonitor:
    """
    Monitors system resources during performance tests
    """

    def __init__(self):
        self.monitoring_active = False
        self.resource_history: List[Dict[str, Any]] = []

    async def start_monitoring(self, interval_seconds: int = 5) -> None:
        """Start monitoring system resources"""
        self.monitoring_active = True
        self.resource_history = []

        logger.info("Starting system resource monitoring")

        while self.monitoring_active:
            try:
                # Collect current resource metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                net_io = psutil.net_io_counters()

                resource_snapshot = {
                    "timestamp": datetime.now(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "network_bytes_sent": net_io.bytes_sent,
                    "network_bytes_recv": net_io.bytes_recv
                }

                self.resource_history.append(resource_snapshot)

                # Keep history size manageable
                if len(self.resource_history) > 1000:
                    self.resource_history = self.resource_history[-1000:]

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(interval_seconds)

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return resource summary"""
        self.monitoring_active = False

        if not self.resource_history:
            return {}

        # Calculate resource usage statistics
        cpu_usage = [r["cpu_percent"] for r in self.resource_history]
        memory_usage = [r["memory_percent"] for r in self.resource_history]

        summary = {
            "duration_minutes": (self.resource_history[-1]["timestamp"] -
                               self.resource_history[0]["timestamp"]).total_seconds() / 60,
            "cpu": {
                "min_percent": min(cpu_usage),
                "max_percent": max(cpu_usage),
                "avg_percent": statistics.mean(cpu_usage),
                "p95_percent": self._percentile(cpu_usage, 95)
            },
            "memory": {
                "min_percent": min(memory_usage),
                "max_percent": max(memory_usage),
                "avg_percent": statistics.mean(memory_usage),
                "p95_percent": self._percentile(memory_usage, 95)
            },
            "samples_collected": len(self.resource_history)
        }

        logger.info(f"Resource monitoring stopped. Collected {len(self.resource_history)} samples")
        return summary

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0

        data_sorted = sorted(data)
        index = (percentile / 100) * (len(data_sorted) - 1)

        if index.is_integer():
            return data_sorted[int(index)]
        else:
            lower = data_sorted[int(index)]
            upper = data_sorted[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class PerformanceTestingSuite:
    """
    Main performance testing orchestrator
    """

    def __init__(self):
        self.load_generator = LoadGenerator()
        self.validator = PerformanceValidator()
        self.resource_monitor = SystemResourceMonitor()
        self.test_history: List[TestResult] = []

    async def run_test(self,
                      config: TestConfiguration,
                      progress_callback: Optional[Callable] = None) -> TestResult:
        """Run a complete performance test"""

        logger.info(f"Starting performance test: {config.name}")

        test_result = TestResult(
            test_config=config,
            start_time=datetime.now(),
            end_time=datetime.now(),
            status=TestStatus.RUNNING
        )

        try:
            # Start system resource monitoring
            monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())

            # Generate load and collect metrics
            test_result.metrics = await self.load_generator.generate_load(config, progress_callback)

            # Stop monitoring and get system metrics
            system_metrics = self.resource_monitor.stop_monitoring()
            test_result.system_metrics = system_metrics
            monitor_task.cancel()

            test_result.end_time = datetime.now()
            test_result.status = TestStatus.COMPLETED

            # Store in test history
            self.test_history.append(test_result)

            logger.info(f"Performance test completed: {config.name}")

        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.errors.append(str(e))
            test_result.end_time = datetime.now()
            logger.error(f"Performance test failed: {config.name} - {e}")

        return test_result

    async def run_validation_suite(self) -> Dict[str, Any]:
        """Run comprehensive validation test suite"""

        logger.info("Starting comprehensive performance validation suite")

        validation_results = {
            "suite_start_time": datetime.now(),
            "tests": {},
            "overall_pass": True,
            "performance_summary": {}
        }

        # Test configurations
        test_configs = [
            TestConfiguration(
                name="baseline_load_test",
                test_type=TestType.BASELINE_TEST,
                duration_seconds=300,  # 5 minutes
                concurrent_users=10,
                requests_per_second=20,
                ramp_up_seconds=60,
                test_data={"scenario": "agent_workflow_optimization"}
            ),
            TestConfiguration(
                name="stress_test",
                test_type=TestType.STRESS_TEST,
                duration_seconds=180,  # 3 minutes
                concurrent_users=50,
                requests_per_second=100,
                ramp_up_seconds=30,
                test_data={"scenario": "high_load_operations"}
            ),
            TestConfiguration(
                name="spike_test",
                test_type=TestType.SPIKE_TEST,
                duration_seconds=120,  # 2 minutes
                concurrent_users=100,
                requests_per_second=200,
                ramp_up_seconds=10,
                test_data={"scenario": "sudden_load_spike"}
            )
        ]

        # Run all tests
        for config in test_configs:
            try:
                test_result = await self.run_test(config)
                validation_report = self.validator.validate_results(test_result)

                validation_results["tests"][config.name] = {
                    "test_result": test_result,
                    "validation_report": validation_report
                }

                if not validation_report["overall_pass"]:
                    validation_results["overall_pass"] = False

                # Set baseline if it's a baseline test
                if config.test_type == TestType.BASELINE_TEST:
                    self.validator.set_baseline(test_result)

            except Exception as e:
                logger.error(f"Validation test failed: {config.name} - {e}")
                validation_results["overall_pass"] = False
                validation_results["tests"][config.name] = {
                    "error": str(e),
                    "status": "failed"
                }

        # Calculate performance improvement summary
        validation_results["performance_summary"] = self._calculate_performance_summary(validation_results)
        validation_results["suite_end_time"] = datetime.now()

        logger.info(f"Validation suite completed. Overall pass: {validation_results['overall_pass']}")

        return validation_results

    def _calculate_performance_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance improvement summary"""

        summary = {
            "total_tests": len(validation_results["tests"]),
            "passed_tests": 0,
            "failed_tests": 0,
            "average_response_time_improvement": 0.0,
            "average_throughput_improvement": 0.0,
            "system_reliability_score": 0.0
        }

        improvements = []
        throughput_improvements = []

        for test_name, test_data in validation_results["tests"].items():
            if "validation_report" in test_data:
                validation_report = test_data["validation_report"]

                if validation_report["overall_pass"]:
                    summary["passed_tests"] += 1
                else:
                    summary["failed_tests"] += 1

                # Collect performance improvements
                perf_improvements = validation_report.get("performance_improvements", {})

                if "response_time" in perf_improvements:
                    improvements.append(perf_improvements["response_time"]["improvement_percent"])

                if "throughput" in perf_improvements:
                    throughput_improvements.append(perf_improvements["throughput"]["improvement_percent"])

        # Calculate averages
        if improvements:
            summary["average_response_time_improvement"] = statistics.mean(improvements)

        if throughput_improvements:
            summary["average_throughput_improvement"] = statistics.mean(throughput_improvements)

        # Calculate reliability score
        summary["system_reliability_score"] = (summary["passed_tests"] / summary["total_tests"]) * 100

        return summary

    async def save_test_report(self, test_result: TestResult, filepath: str) -> None:
        """Save detailed test report to file"""

        report_data = {
            "test_config": {
                "name": test_result.test_config.name,
                "test_type": test_result.test_config.test_type.value,
                "duration_seconds": test_result.test_config.duration_seconds,
                "concurrent_users": test_result.test_config.concurrent_users,
                "requests_per_second": test_result.test_config.requests_per_second
            },
            "execution": {
                "start_time": test_result.start_time.isoformat(),
                "end_time": test_result.end_time.isoformat(),
                "status": test_result.status.value,
                "duration_seconds": (test_result.end_time - test_result.start_time).total_seconds()
            },
            "summary_stats": test_result.summary_stats,
            "system_metrics": test_result.system_metrics,
            "validation_report": self.validator.validate_results(test_result),
            "errors": test_result.errors
        }

        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(report_data, indent=2, default=str))

        logger.info(f"Test report saved: {filepath}")


# Test scenario implementations
async def agent_workflow_optimization_scenario(config: TestConfiguration, user_id: int) -> tuple[str, Any]:
    """Test scenario for agent workflow optimization"""

    # Simulate agent task creation and optimization
    operations = [
        ("create_task", 0.2),
        ("optimize_workflow", 0.5),
        ("get_ai_recommendations", 0.3),
        ("update_performance_metrics", 0.1)
    ]

    operation, delay = random.choice(operations)
    await asyncio.sleep(delay + random.uniform(0, 0.1))

    # Simulate occasional failures
    if random.random() < 0.05:  # 5% failure rate
        return operation, {"error": "Simulated service failure"}

    return operation, {"status": "success", "operation": operation, "user_id": user_id}


async def high_load_operations_scenario(config: TestConfiguration, user_id: int) -> tuple[str, Any]:
    """Test scenario for high load operations"""

    # Simulate intensive operations
    operations = [
        ("database_query", 0.3),
        ("api_call", 0.4),
        ("cache_lookup", 0.1),
        ("data_processing", 0.6)
    ]

    operation, delay = random.choice(operations)
    await asyncio.sleep(delay + random.uniform(0, 0.2))

    # Higher failure rate under load
    if random.random() < 0.10:  # 10% failure rate
        return operation, {"error": "Service overloaded"}

    return operation, {"status": "success", "operation": operation, "load_factor": "high"}


async def sudden_load_spike_scenario(config: TestConfiguration, user_id: int) -> tuple[str, Any]:
    """Test scenario for sudden load spikes"""

    # Simulate spike conditions
    operations = [
        ("burst_request", 0.1),
        ("priority_task", 0.2),
        ("emergency_operation", 0.15)
    ]

    operation, delay = random.choice(operations)
    await asyncio.sleep(delay)

    # Even higher failure rate during spikes
    if random.random() < 0.15:  # 15% failure rate
        return operation, {"error": "System overwhelmed"}

    return operation, {"status": "success", "operation": operation, "spike_handled": True}


# Global performance testing suite instance
performance_suite = PerformanceTestingSuite()

# Register test scenarios
performance_suite.load_generator.register_scenario("agent_workflow_optimization", agent_workflow_optimization_scenario)
performance_suite.load_generator.register_scenario("high_load_operations", high_load_operations_scenario)
performance_suite.load_generator.register_scenario("sudden_load_spike", sudden_load_spike_scenario)