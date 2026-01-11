#!/usr/bin/env python3
"""
Claude Services Performance Benchmarking Tool

Comprehensive performance benchmarking and load testing for Claude services
to measure throughput, latency, resource utilization, and scalability.

Usage:
    python scripts/benchmark_claude_services.py --load-test --duration 300
    python scripts/benchmark_claude_services.py --latency-test --samples 1000
    python scripts/benchmark_claude_services.py --stress-test --concurrent 50
    python scripts/benchmark_claude_services.py --full-benchmark

Created: January 2026
Author: Enterprise Development Team
"""

import asyncio
import argparse
import logging
import sys
import json
import time
import statistics
import psutil
import gc
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid
import concurrent.futures
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ghl_real_estate_ai.services.claude_agent_orchestrator import (
    ClaudeAgentOrchestrator, AgentRole, TaskPriority
)
from ghl_real_estate_ai.services.claude_enterprise_intelligence import (
    ClaudeEnterpriseIntelligence
)
from ghl_real_estate_ai.services.claude_business_intelligence_automation import (
    ClaudeBusinessIntelligenceAutomation
)
from ghl_real_estate_ai.services.claude_management_orchestration import (
    ClaudeManagementOrchestration
)

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during benchmarking
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetric:
    """Performance benchmark metric."""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = None

@dataclass
class BenchmarkResult:
    """Benchmark test result."""
    test_name: str
    duration: float
    metrics: List[BenchmarkMetric]
    success_rate: float
    error_count: int
    resource_usage: Dict[str, float]
    summary: str

class PerformanceBenchmark:
    """Performance benchmarking for Claude services."""

    def __init__(self):
        self.services = {}
        self.results: List[BenchmarkResult] = []
        self.start_time = None

    async def initialize_services(self):
        """Initialize Claude services for benchmarking."""
        print("🔧 Initializing Claude services for benchmarking...")

        self.services = {
            'orchestrator': ClaudeAgentOrchestrator(),
            'intelligence': ClaudeEnterpriseIntelligence(),
            'business': ClaudeBusinessIntelligenceAutomation(),
            'management': ClaudeManagementOrchestration()
        }

        for service_name, service in self.services.items():
            if hasattr(service, 'initialize'):
                await service.initialize()

        print(f"✅ {len(self.services)} services initialized")

    async def run_latency_benchmark(self, samples: int = 1000) -> BenchmarkResult:
        """Benchmark service latency with multiple samples."""
        print(f"⚡ Running latency benchmark ({samples} samples)...")

        start_time = time.time()
        metrics = []
        errors = 0

        # Test orchestrator latency
        print("  📊 Testing Agent Orchestrator latency...")
        orchestrator_latencies = []

        for i in range(samples // 4):  # Divide samples among services
            try:
                sample_start = time.time()
                task_id = await self.services['orchestrator'].submit_task(
                    task_type=f"latency_test_{i}",
                    description="Latency benchmark task",
                    context={"benchmark": True, "sample": i},
                    agent_role=AgentRole.PERFORMANCE_ENGINEER,
                    priority=TaskPriority.NORMAL
                )
                latency = (time.time() - sample_start) * 1000  # ms
                orchestrator_latencies.append(latency)

                if i % 100 == 0:
                    print(f"    Progress: {i}/{samples//4} samples")

            except Exception as e:
                errors += 1
                logger.warning(f"Orchestrator latency test error: {e}")

        # Calculate orchestrator metrics
        if orchestrator_latencies:
            metrics.extend([
                BenchmarkMetric("orchestrator_latency_mean", statistics.mean(orchestrator_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("orchestrator_latency_median", statistics.median(orchestrator_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("orchestrator_latency_p95", self._percentile(orchestrator_latencies, 95), "ms", datetime.utcnow()),
                BenchmarkMetric("orchestrator_latency_p99", self._percentile(orchestrator_latencies, 99), "ms", datetime.utcnow()),
                BenchmarkMetric("orchestrator_latency_min", min(orchestrator_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("orchestrator_latency_max", max(orchestrator_latencies), "ms", datetime.utcnow()),
            ])

        # Test intelligence service latency
        print("  🧠 Testing Enterprise Intelligence latency...")
        intelligence_latencies = []

        for i in range(samples // 4):
            try:
                sample_start = time.time()
                analysis = await self.services['intelligence'].analyze_system_health()
                latency = (time.time() - sample_start) * 1000
                intelligence_latencies.append(latency)

                if i % 25 == 0:  # Less frequent progress updates for slower operations
                    print(f"    Progress: {i}/{samples//4} samples")

            except Exception as e:
                errors += 1
                logger.warning(f"Intelligence latency test error: {e}")

        # Calculate intelligence metrics
        if intelligence_latencies:
            metrics.extend([
                BenchmarkMetric("intelligence_latency_mean", statistics.mean(intelligence_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("intelligence_latency_median", statistics.median(intelligence_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("intelligence_latency_p95", self._percentile(intelligence_latencies, 95), "ms", datetime.utcnow()),
                BenchmarkMetric("intelligence_latency_p99", self._percentile(intelligence_latencies, 99), "ms", datetime.utcnow()),
            ])

        # Test business intelligence latency
        print("  📈 Testing Business Intelligence latency...")
        business_latencies = []

        for i in range(samples // 4):
            try:
                sample_start = time.time()
                insights = await self.services['business'].generate_real_time_insights()
                latency = (time.time() - sample_start) * 1000
                business_latencies.append(latency)

                if i % 50 == 0:
                    print(f"    Progress: {i}/{samples//4} samples")

            except Exception as e:
                errors += 1
                logger.warning(f"Business intelligence latency test error: {e}")

        # Calculate business intelligence metrics
        if business_latencies:
            metrics.extend([
                BenchmarkMetric("business_latency_mean", statistics.mean(business_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("business_latency_median", statistics.median(business_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("business_latency_p95", self._percentile(business_latencies, 95), "ms", datetime.utcnow()),
                BenchmarkMetric("business_latency_p99", self._percentile(business_latencies, 99), "ms", datetime.utcnow()),
            ])

        # Test management orchestration latency
        print("  🎛️ Testing Management Orchestration latency...")
        management_latencies = []

        for i in range(samples // 4):
            try:
                sample_start = time.time()
                status = await self.services['management'].get_system_status()
                latency = (time.time() - sample_start) * 1000
                management_latencies.append(latency)

                if i % 100 == 0:
                    print(f"    Progress: {i}/{samples//4} samples")

            except Exception as e:
                errors += 1
                logger.warning(f"Management latency test error: {e}")

        # Calculate management metrics
        if management_latencies:
            metrics.extend([
                BenchmarkMetric("management_latency_mean", statistics.mean(management_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("management_latency_median", statistics.median(management_latencies), "ms", datetime.utcnow()),
                BenchmarkMetric("management_latency_p95", self._percentile(management_latencies, 95), "ms", datetime.utcnow()),
                BenchmarkMetric("management_latency_p99", self._percentile(management_latencies, 99), "ms", datetime.utcnow()),
            ])

        duration = time.time() - start_time
        successful_samples = samples - errors
        success_rate = (successful_samples / samples) * 100 if samples > 0 else 0

        # Get resource usage
        resource_usage = self._get_resource_usage()

        return BenchmarkResult(
            test_name="Latency Benchmark",
            duration=duration,
            metrics=metrics,
            success_rate=success_rate,
            error_count=errors,
            resource_usage=resource_usage,
            summary=f"Completed {successful_samples}/{samples} samples in {duration:.2f}s"
        )

    async def run_throughput_benchmark(self, duration: int = 60) -> BenchmarkResult:
        """Benchmark service throughput over time."""
        print(f"🚀 Running throughput benchmark ({duration}s duration)...")

        start_time = time.time()
        end_time = start_time + duration

        metrics = []
        completed_operations = 0
        errors = 0

        # Track operations per service
        service_ops = {
            'orchestrator': 0,
            'intelligence': 0,
            'business': 0,
            'management': 0
        }

        print("  📊 Measuring sustained throughput...")

        while time.time() < end_time:
            batch_start = time.time()
            batch_tasks = []

            # Create a batch of operations across all services
            for i in range(10):  # Batch size of 10
                # Rotate through services
                if i % 4 == 0:
                    task = self._submit_orchestrator_task(completed_operations + i)
                    batch_tasks.append(('orchestrator', task))
                elif i % 4 == 1:
                    task = self._analyze_intelligence()
                    batch_tasks.append(('intelligence', task))
                elif i % 4 == 2:
                    task = self._generate_business_insights()
                    batch_tasks.append(('business', task))
                else:
                    task = self._get_management_status()
                    batch_tasks.append(('management', task))

            # Execute batch concurrently
            try:
                results = await asyncio.gather(*[task for _, task in batch_tasks], return_exceptions=True)

                for i, result in enumerate(results):
                    service_name = batch_tasks[i][0]
                    if isinstance(result, Exception):
                        errors += 1
                        logger.warning(f"Throughput test error in {service_name}: {result}")
                    else:
                        completed_operations += 1
                        service_ops[service_name] += 1

            except Exception as e:
                errors += len(batch_tasks)
                logger.error(f"Batch execution error: {e}")

            # Print progress
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0 and elapsed > 0:
                current_throughput = completed_operations / elapsed
                print(f"    Progress: {elapsed:.0f}s, Throughput: {current_throughput:.1f} ops/s")

            # Small delay to prevent overwhelming
            await asyncio.sleep(0.1)

        test_duration = time.time() - start_time
        total_operations = completed_operations + errors
        success_rate = (completed_operations / total_operations) * 100 if total_operations > 0 else 0

        # Calculate throughput metrics
        overall_throughput = completed_operations / test_duration
        metrics.extend([
            BenchmarkMetric("overall_throughput", overall_throughput, "ops/s", datetime.utcnow()),
            BenchmarkMetric("orchestrator_throughput", service_ops['orchestrator'] / test_duration, "ops/s", datetime.utcnow()),
            BenchmarkMetric("intelligence_throughput", service_ops['intelligence'] / test_duration, "ops/s", datetime.utcnow()),
            BenchmarkMetric("business_throughput", service_ops['business'] / test_duration, "ops/s", datetime.utcnow()),
            BenchmarkMetric("management_throughput", service_ops['management'] / test_duration, "ops/s", datetime.utcnow()),
            BenchmarkMetric("total_operations", completed_operations, "count", datetime.utcnow()),
        ])

        # Get resource usage
        resource_usage = self._get_resource_usage()

        return BenchmarkResult(
            test_name="Throughput Benchmark",
            duration=test_duration,
            metrics=metrics,
            success_rate=success_rate,
            error_count=errors,
            resource_usage=resource_usage,
            summary=f"Achieved {overall_throughput:.2f} ops/s over {test_duration:.2f}s"
        )

    async def run_stress_test(self, concurrent_users: int = 50, duration: int = 120) -> BenchmarkResult:
        """Run stress test with concurrent operations."""
        print(f"💪 Running stress test ({concurrent_users} concurrent operations, {duration}s duration)...")

        start_time = time.time()
        metrics = []
        total_operations = 0
        errors = 0

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(concurrent_users)

        async def stress_worker(worker_id: int) -> Tuple[int, int]:
            """Individual stress test worker."""
            worker_operations = 0
            worker_errors = 0

            end_time = start_time + duration

            while time.time() < end_time:
                async with semaphore:
                    try:
                        # Randomly select operation type
                        operation_type = worker_id % 4

                        if operation_type == 0:
                            await self._submit_orchestrator_task(worker_operations)
                        elif operation_type == 1:
                            await self._analyze_intelligence()
                        elif operation_type == 2:
                            await self._generate_business_insights()
                        else:
                            await self._get_management_status()

                        worker_operations += 1

                    except Exception as e:
                        worker_errors += 1
                        logger.debug(f"Stress test error in worker {worker_id}: {e}")

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)

            return worker_operations, worker_errors

        print(f"  🔄 Starting {concurrent_users} concurrent workers...")

        # Create and run workers
        workers = [stress_worker(i) for i in range(concurrent_users)]

        # Monitor progress
        monitor_task = asyncio.create_task(self._monitor_stress_test(start_time, duration))

        # Run workers and monitor concurrently
        worker_results, _ = await asyncio.gather(
            asyncio.gather(*workers, return_exceptions=True),
            monitor_task
        )

        # Aggregate results
        for result in worker_results:
            if isinstance(result, Exception):
                errors += 1
                logger.error(f"Worker failed: {result}")
            else:
                ops, errs = result
                total_operations += ops
                errors += errs

        test_duration = time.time() - start_time
        success_rate = (total_operations / (total_operations + errors)) * 100 if (total_operations + errors) > 0 else 0

        # Calculate stress test metrics
        throughput = total_operations / test_duration
        errors_per_second = errors / test_duration

        metrics.extend([
            BenchmarkMetric("stress_throughput", throughput, "ops/s", datetime.utcnow()),
            BenchmarkMetric("stress_errors_per_second", errors_per_second, "errors/s", datetime.utcnow()),
            BenchmarkMetric("concurrent_users", concurrent_users, "count", datetime.utcnow()),
            BenchmarkMetric("stress_total_operations", total_operations, "count", datetime.utcnow()),
        ])

        # Get resource usage
        resource_usage = self._get_resource_usage()

        return BenchmarkResult(
            test_name="Stress Test",
            duration=test_duration,
            metrics=metrics,
            success_rate=success_rate,
            error_count=errors,
            resource_usage=resource_usage,
            summary=f"Handled {throughput:.2f} ops/s with {concurrent_users} concurrent users"
        )

    async def run_scalability_test(self) -> BenchmarkResult:
        """Test service scalability with increasing load."""
        print("📈 Running scalability test...")

        start_time = time.time()
        metrics = []
        errors = 0

        # Test with increasing concurrent load
        load_levels = [1, 5, 10, 25, 50]
        throughput_results = []

        for load_level in load_levels:
            print(f"  🎯 Testing with {load_level} concurrent operations...")

            # Run mini throughput test at this load level
            load_start = time.time()
            load_operations = 0
            load_errors = 0

            # Run for 30 seconds at this load level
            end_time = load_start + 30

            async def load_worker():
                worker_ops = 0
                worker_errors = 0
                while time.time() < end_time:
                    try:
                        await self._submit_orchestrator_task(worker_ops)
                        worker_ops += 1
                    except Exception:
                        worker_errors += 1
                    await asyncio.sleep(0.1)
                return worker_ops, worker_errors

            # Create workers for this load level
            workers = [load_worker() for _ in range(load_level)]
            results = await asyncio.gather(*workers, return_exceptions=True)

            # Aggregate results
            for result in results:
                if isinstance(result, Exception):
                    load_errors += 1
                else:
                    ops, errs = result
                    load_operations += ops
                    load_errors += errs

            load_duration = time.time() - load_start
            load_throughput = load_operations / load_duration

            throughput_results.append((load_level, load_throughput))
            metrics.append(BenchmarkMetric(
                f"throughput_at_{load_level}_concurrent",
                load_throughput,
                "ops/s",
                datetime.utcnow()
            ))

            errors += load_errors
            print(f"    Throughput at {load_level} concurrent: {load_throughput:.2f} ops/s")

        # Calculate scalability metrics
        if len(throughput_results) >= 2:
            # Linear scalability would maintain same throughput per concurrent user
            initial_throughput_per_user = throughput_results[0][1] / throughput_results[0][0]
            final_throughput_per_user = throughput_results[-1][1] / throughput_results[-1][0]
            scalability_efficiency = (final_throughput_per_user / initial_throughput_per_user) * 100

            metrics.append(BenchmarkMetric(
                "scalability_efficiency",
                scalability_efficiency,
                "percent",
                datetime.utcnow()
            ))

        test_duration = time.time() - start_time
        resource_usage = self._get_resource_usage()

        return BenchmarkResult(
            test_name="Scalability Test",
            duration=test_duration,
            metrics=metrics,
            success_rate=100.0,  # Scalability is about throughput, not failure rate
            error_count=errors,
            resource_usage=resource_usage,
            summary=f"Tested scalability from {load_levels[0]} to {load_levels[-1]} concurrent operations"
        )

    async def _monitor_stress_test(self, start_time: float, duration: int):
        """Monitor stress test progress."""
        while time.time() < start_time + duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            print(f"    Progress: {elapsed:.0f}s elapsed, {remaining:.0f}s remaining")
            await asyncio.sleep(10)

    async def _submit_orchestrator_task(self, task_id: int):
        """Submit task to orchestrator."""
        return await self.services['orchestrator'].submit_task(
            task_type=f"benchmark_task_{task_id}",
            description="Benchmark test task",
            context={"benchmark": True, "task_id": task_id},
            agent_role=AgentRole.PERFORMANCE_ENGINEER,
            priority=TaskPriority.NORMAL
        )

    async def _analyze_intelligence(self):
        """Run intelligence analysis."""
        return await self.services['intelligence'].analyze_system_health()

    async def _generate_business_insights(self):
        """Generate business insights."""
        return await self.services['business'].generate_real_time_insights()

    async def _get_management_status(self):
        """Get management status."""
        return await self.services['management'].get_system_status()

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        if f == len(sorted_data) - 1:
            return sorted_data[f]
        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c

    def _get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io_bytes': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            }
        except Exception as e:
            logger.warning(f"Failed to get resource usage: {e}")
            return {'error': str(e)}

    def generate_benchmark_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return {"error": "No benchmark results available"}

        total_duration = sum(result.duration for result in self.results)
        avg_success_rate = statistics.mean(result.success_rate for result in self.results)
        total_errors = sum(result.error_count for result in self.results)

        # SLA compliance check
        sla_targets = {
            "orchestrator_latency_p95": 1000,  # 1 second
            "intelligence_latency_p95": 10000,  # 10 seconds
            "business_latency_p95": 5000,  # 5 seconds
            "management_latency_p95": 2000,  # 2 seconds
            "overall_throughput": 10,  # 10 ops/s minimum
        }

        sla_compliance = {}
        for result in self.results:
            for metric in result.metrics:
                if metric.metric_name in sla_targets:
                    target = sla_targets[metric.metric_name]
                    if "throughput" in metric.metric_name:
                        compliance = metric.value >= target
                    else:
                        compliance = metric.value <= target
                    sla_compliance[metric.metric_name] = {
                        "compliant": compliance,
                        "actual": metric.value,
                        "target": target,
                        "unit": metric.unit
                    }

        report = {
            "benchmark_summary": {
                "total_tests": len(self.results),
                "total_duration": total_duration,
                "average_success_rate": avg_success_rate,
                "total_errors": total_errors,
                "timestamp": datetime.utcnow().isoformat()
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "duration": result.duration,
                    "success_rate": result.success_rate,
                    "error_count": result.error_count,
                    "summary": result.summary,
                    "metrics": [asdict(metric) for metric in result.metrics],
                    "resource_usage": result.resource_usage
                }
                for result in self.results
            ],
            "sla_compliance": sla_compliance,
            "performance_grade": self._calculate_performance_grade(sla_compliance, avg_success_rate)
        }

        return report

    def _calculate_performance_grade(self, sla_compliance: Dict, success_rate: float) -> str:
        """Calculate overall performance grade."""
        compliant_count = sum(1 for comp in sla_compliance.values() if comp["compliant"])
        total_slas = len(sla_compliance)

        if total_slas == 0:
            sla_percentage = 100
        else:
            sla_percentage = (compliant_count / total_slas) * 100

        # Grade based on SLA compliance and success rate
        if sla_percentage >= 90 and success_rate >= 95:
            return "A+"
        elif sla_percentage >= 80 and success_rate >= 90:
            return "A"
        elif sla_percentage >= 70 and success_rate >= 85:
            return "B+"
        elif sla_percentage >= 60 and success_rate >= 80:
            return "B"
        elif sla_percentage >= 50 and success_rate >= 70:
            return "C+"
        elif sla_percentage >= 40 and success_rate >= 60:
            return "C"
        else:
            return "F"

    async def cleanup_services(self):
        """Cleanup services after benchmarking."""
        for service in self.services.values():
            if hasattr(service, 'shutdown'):
                try:
                    await service.shutdown()
                except Exception as e:
                    logger.warning(f"Error during service cleanup: {e}")

async def main():
    """Main benchmark script entry point."""
    parser = argparse.ArgumentParser(description="Claude Services Performance Benchmark")
    parser.add_argument("--latency-test", action="store_true", help="Run latency benchmark")
    parser.add_argument("--load-test", action="store_true", help="Run throughput/load benchmark")
    parser.add_argument("--stress-test", action="store_true", help="Run stress test")
    parser.add_argument("--scalability-test", action="store_true", help="Run scalability test")
    parser.add_argument("--full-benchmark", action="store_true", help="Run all benchmark tests")

    parser.add_argument("--samples", type=int, default=1000, help="Number of samples for latency test")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds for load/stress tests")
    parser.add_argument("--concurrent", type=int, default=50, help="Concurrent operations for stress test")
    parser.add_argument("--output", help="Output file for benchmark report")

    args = parser.parse_args()

    if not any([args.latency_test, args.load_test, args.stress_test, args.scalability_test, args.full_benchmark]):
        args.latency_test = True  # Default test

    benchmark = PerformanceBenchmark()

    try:
        await benchmark.initialize_services()

        if args.full_benchmark:
            # Run all tests
            print("🎯 Running full benchmark suite...")

            benchmark.results.append(await benchmark.run_latency_benchmark(args.samples))
            gc.collect()  # Clean up between tests

            benchmark.results.append(await benchmark.run_throughput_benchmark(args.duration))
            gc.collect()

            benchmark.results.append(await benchmark.run_stress_test(args.concurrent, args.duration))
            gc.collect()

            benchmark.results.append(await benchmark.run_scalability_test())

        else:
            if args.latency_test:
                benchmark.results.append(await benchmark.run_latency_benchmark(args.samples))

            if args.load_test:
                benchmark.results.append(await benchmark.run_throughput_benchmark(args.duration))

            if args.stress_test:
                benchmark.results.append(await benchmark.run_stress_test(args.concurrent, args.duration))

            if args.scalability_test:
                benchmark.results.append(await benchmark.run_scalability_test())

        # Generate report
        report = benchmark.generate_benchmark_report()

        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Benchmark report saved to {args.output}")
        else:
            print("\n📊 Benchmark Report:")
            print(json.dumps(report, indent=2))

        # Print summary
        summary = report["benchmark_summary"]
        grade = report["performance_grade"]

        print(f"\n🎯 Benchmark Summary:")
        print(f"   Performance Grade: {grade}")
        print(f"   Tests: {summary['total_tests']}")
        print(f"   Success Rate: {summary['average_success_rate']:.1f}%")
        print(f"   Duration: {summary['total_duration']:.2f}s")
        print(f"   Total Errors: {summary['total_errors']}")

        # Exit code based on performance grade
        if grade in ['A+', 'A']:
            sys.exit(0)
        elif grade in ['B+', 'B']:
            sys.exit(1)
        else:
            sys.exit(2)

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        print(f"❌ Benchmark failed: {e}")
        sys.exit(3)

    finally:
        await benchmark.cleanup_services()

if __name__ == "__main__":
    asyncio.run(main())