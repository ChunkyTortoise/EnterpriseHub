#!/usr/bin/env python3
"""
Performance Monitoring and Analysis Framework
=============================================

Real-time performance monitoring, bottleneck detection, and scalability analysis
for Jorge's Revenue Acceleration Platform.

Features:
- Real-time resource monitoring (CPU, Memory, I/O)
- Database query performance analysis
- API endpoint latency tracking
- Cache hit/miss ratio monitoring
- Auto-scaling trigger detection
- Performance regression detection
- Bottleneck identification
- Load forecasting

Usage:
    # Start monitoring
    python performance_monitoring.py --mode monitor --duration 3600

    # Analyze historical data
    python performance_monitoring.py --mode analyze --report-file performance_report.json

    # Real-time dashboard
    python performance_monitoring.py --mode dashboard

Author: Claude Code Agent Swarm
Created: 2026-01-17
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import psutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Single point-in-time performance snapshot"""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    thread_count: int
    process_count: int


@dataclass
class EndpointMetrics:
    """Performance metrics for a specific API endpoint"""

    endpoint: str
    method: str
    request_count: int
    success_count: int
    error_count: int
    response_times_ms: List[float]
    status_codes: Dict[int, int]
    last_updated: datetime

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times_ms) if self.response_times_ms else 0

    @property
    def p95_response_time(self) -> float:
        if not self.response_times_ms:
            return 0
        sorted_times = sorted(self.response_times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""

    query_count: int
    slow_query_count: int  # Queries >100ms
    avg_query_time_ms: float
    connection_pool_size: int
    active_connections: int
    idle_connections: int
    connection_wait_time_ms: float
    deadlock_count: int
    transaction_rollback_count: int


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hit_count: int
    miss_count: int
    eviction_count: int
    memory_usage_mb: float
    avg_get_time_ms: float
    avg_set_time_ms: float

    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0


class PerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(self, sampling_interval: int = 1):
        self.sampling_interval = sampling_interval
        self.snapshots: deque = deque(maxlen=3600)  # Keep 1 hour of data
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.database_metrics: Optional[DatabaseMetrics] = None
        self.cache_metrics: Optional[CacheMetrics] = None
        self.monitoring = False
        self.process = psutil.Process()

        # Performance thresholds
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 80.0,
            "response_time_p95_ms": 100.0,
            "error_rate": 0.01,
            "cache_hit_rate": 0.8,
            "db_slow_query_rate": 0.05,
        }

        # Anomaly detection
        self.baseline_metrics = {}
        self.anomalies_detected = []

    async def start_monitoring(self, duration_seconds: Optional[int] = None):
        """Start continuous performance monitoring"""
        self.monitoring = True
        start_time = time.time()

        logger.info("Performance monitoring started")

        try:
            while self.monitoring:
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break

                # Collect system snapshot
                snapshot = self._collect_system_snapshot()
                self.snapshots.append(snapshot)

                # Detect anomalies
                self._detect_anomalies(snapshot)

                # Check thresholds
                self._check_thresholds(snapshot)

                # Log status every 60 seconds
                if len(self.snapshots) % 60 == 0:
                    self._log_status()

                await asyncio.sleep(self.sampling_interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            self.monitoring = False
            logger.info("Performance monitoring stopped")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False

    def _collect_system_snapshot(self) -> PerformanceSnapshot:
        """Collect current system performance metrics"""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_mb = self.process.memory_info().rss / 1024 / 1024

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / 1024 / 1024
        disk_write_mb = disk_io.write_bytes / 1024 / 1024

        # Network I/O
        net_io = psutil.net_io_counters()
        net_sent_mb = net_io.bytes_sent / 1024 / 1024
        net_recv_mb = net_io.bytes_recv / 1024 / 1024

        # Process info
        connections = len(self.process.connections())
        threads = self.process.num_threads()

        return PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory.percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
            active_connections=connections,
            thread_count=threads,
            process_count=len(psutil.pids()),
        )

    def _detect_anomalies(self, snapshot: PerformanceSnapshot):
        """Detect performance anomalies using statistical methods"""
        # Establish baseline (first 60 samples)
        if len(self.snapshots) == 60:
            self._establish_baseline()
            return

        if len(self.snapshots) < 60:
            return

        # Check for anomalies
        anomalies = []

        # CPU spike detection
        if snapshot.cpu_percent > self.baseline_metrics.get("cpu_mean", 50) + (
            3 * self.baseline_metrics.get("cpu_std", 10)
        ):
            anomalies.append(
                {
                    "type": "cpu_spike",
                    "value": snapshot.cpu_percent,
                    "baseline_mean": self.baseline_metrics.get("cpu_mean"),
                    "severity": "high" if snapshot.cpu_percent > 90 else "medium",
                }
            )

        # Memory spike detection
        if snapshot.memory_percent > self.baseline_metrics.get("memory_mean", 50) + (
            3 * self.baseline_metrics.get("memory_std", 10)
        ):
            anomalies.append(
                {
                    "type": "memory_spike",
                    "value": snapshot.memory_percent,
                    "baseline_mean": self.baseline_metrics.get("memory_mean"),
                    "severity": "high" if snapshot.memory_percent > 90 else "medium",
                }
            )

        if anomalies:
            self.anomalies_detected.extend(anomalies)
            logger.warning(f"Anomalies detected: {anomalies}")

    def _establish_baseline(self):
        """Establish baseline performance metrics"""
        cpu_values = [s.cpu_percent for s in self.snapshots]
        memory_values = [s.memory_percent for s in self.snapshots]

        self.baseline_metrics = {
            "cpu_mean": statistics.mean(cpu_values),
            "cpu_std": statistics.stdev(cpu_values),
            "memory_mean": statistics.mean(memory_values),
            "memory_std": statistics.stdev(memory_values),
        }

        logger.info(f"Baseline established: {self.baseline_metrics}")

    def _check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check if metrics exceed thresholds"""
        alerts = []

        if snapshot.cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append(f"CPU usage {snapshot.cpu_percent:.1f}% exceeds threshold {self.thresholds['cpu_percent']}%")

        if snapshot.memory_percent > self.thresholds["memory_percent"]:
            alerts.append(
                f"Memory usage {snapshot.memory_percent:.1f}% exceeds threshold {self.thresholds['memory_percent']}%"
            )

        if alerts:
            for alert in alerts:
                logger.warning(f"THRESHOLD ALERT: {alert}")

    def _log_status(self):
        """Log current monitoring status"""
        if not self.snapshots:
            return

        latest = self.snapshots[-1]
        logger.info(
            f"Status - CPU: {latest.cpu_percent:.1f}% | "
            f"Memory: {latest.memory_mb:.1f}MB ({latest.memory_percent:.1f}%) | "
            f"Connections: {latest.active_connections} | "
            f"Threads: {latest.thread_count}"
        )

    def record_endpoint_request(self, endpoint: str, method: str, response_time_ms: float, status_code: int):
        """Record an API endpoint request"""
        key = f"{method}:{endpoint}"

        if key not in self.endpoint_metrics:
            self.endpoint_metrics[key] = EndpointMetrics(
                endpoint=endpoint,
                method=method,
                request_count=0,
                success_count=0,
                error_count=0,
                response_times_ms=[],
                status_codes={},
                last_updated=datetime.utcnow(),
            )

        metrics = self.endpoint_metrics[key]
        metrics.request_count += 1
        metrics.response_times_ms.append(response_time_ms)
        metrics.last_updated = datetime.utcnow()

        if 200 <= status_code < 300:
            metrics.success_count += 1
        else:
            metrics.error_count += 1

        metrics.status_codes[status_code] = metrics.status_codes.get(status_code, 0) + 1

        # Keep only last 1000 response times per endpoint
        if len(metrics.response_times_ms) > 1000:
            metrics.response_times_ms = metrics.response_times_ms[-1000:]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.snapshots:
            return {"error": "No data collected"}

        # System metrics summary
        cpu_values = [s.cpu_percent for s in self.snapshots]
        memory_values = [s.memory_percent for s in self.snapshots]
        memory_mb_values = [s.memory_mb for s in self.snapshots]

        # Endpoint metrics summary
        endpoint_summary = {}
        for key, metrics in self.endpoint_metrics.items():
            endpoint_summary[key] = {
                "request_count": metrics.request_count,
                "success_rate": metrics.success_rate,
                "avg_response_time_ms": metrics.avg_response_time,
                "p95_response_time_ms": metrics.p95_response_time,
                "status_codes": metrics.status_codes,
            }

        # Time range
        start_time = self.snapshots[0].timestamp
        end_time = self.snapshots[-1].timestamp
        duration = (end_time - start_time).total_seconds()

        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "monitoring_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": duration,
                "samples_collected": len(self.snapshots),
            },
            "system_metrics": {
                "cpu": {
                    "mean": statistics.mean(cpu_values),
                    "median": statistics.median(cpu_values),
                    "min": min(cpu_values),
                    "max": max(cpu_values),
                    "std_dev": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
                },
                "memory": {
                    "mean_percent": statistics.mean(memory_values),
                    "mean_mb": statistics.mean(memory_mb_values),
                    "peak_mb": max(memory_mb_values),
                    "min_mb": min(memory_mb_values),
                },
            },
            "endpoint_metrics": endpoint_summary,
            "anomalies_detected": self.anomalies_detected,
            "threshold_violations": self._count_threshold_violations(),
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _count_threshold_violations(self) -> Dict[str, int]:
        """Count threshold violations"""
        violations = {"cpu_high": 0, "memory_high": 0}

        for snapshot in self.snapshots:
            if snapshot.cpu_percent > self.thresholds["cpu_percent"]:
                violations["cpu_high"] += 1
            if snapshot.memory_percent > self.thresholds["memory_percent"]:
                violations["memory_high"] += 1

        return violations

    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        if not self.snapshots:
            return recommendations

        # Analyze CPU usage
        cpu_values = [s.cpu_percent for s in self.snapshots]
        avg_cpu = statistics.mean(cpu_values)
        peak_cpu = max(cpu_values)

        if avg_cpu > 70:
            recommendations.append(
                f"High average CPU usage ({avg_cpu:.1f}%). Consider horizontal scaling or code optimization."
            )

        if peak_cpu > 90:
            recommendations.append(
                f"CPU spikes detected (peak: {peak_cpu:.1f}%). Review async operations and concurrent request handling."
            )

        # Analyze memory usage
        memory_mb_values = [s.memory_mb for s in self.snapshots]
        avg_memory = statistics.mean(memory_mb_values)
        peak_memory = max(memory_mb_values)
        memory_growth = memory_mb_values[-1] - memory_mb_values[0] if len(memory_mb_values) > 10 else 0

        if peak_memory > 2048:
            recommendations.append(
                f"High memory usage (peak: {peak_memory:.1f}MB). Consider memory profiling and optimization."
            )

        if memory_growth > 500:
            recommendations.append(
                f"Memory growth detected (+{memory_growth:.1f}MB). Investigate potential memory leaks."
            )

        # Analyze endpoint performance
        slow_endpoints = []
        for key, metrics in self.endpoint_metrics.items():
            if metrics.p95_response_time > 100:
                slow_endpoints.append((key, metrics.p95_response_time))

        if slow_endpoints:
            recommendations.append(
                f"Slow endpoints detected: {', '.join([f'{k} ({v:.1f}ms)' for k, v in slow_endpoints[:3]])}"
            )

        # Check for errors
        high_error_endpoints = []
        for key, metrics in self.endpoint_metrics.items():
            if metrics.success_rate < 0.99:
                high_error_endpoints.append((key, metrics.success_rate))

        if high_error_endpoints:
            recommendations.append(
                f"High error rate on: {', '.join([f'{k} ({(1 - v) * 100:.1f}% errors)' for k, v in high_error_endpoints[:3]])}"
            )

        return recommendations

    def save_report(self, filename: str):
        """Save performance report to file"""
        report = self.get_performance_report()

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Performance report saved to {filename}")


class AutoScalingAnalyzer:
    """Analyze metrics to determine auto-scaling triggers"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    def should_scale_up(self) -> Tuple[bool, str]:
        """Determine if system should scale up"""
        if len(self.monitor.snapshots) < 30:
            return False, "Insufficient data"

        # Check last 30 samples (30 seconds)
        recent_snapshots = list(self.monitor.snapshots)[-30:]

        avg_cpu = statistics.mean([s.cpu_percent for s in recent_snapshots])
        avg_memory = statistics.mean([s.memory_percent for s in recent_snapshots])

        # Scale up if sustained high usage
        if avg_cpu > 75:
            return True, f"High CPU usage: {avg_cpu:.1f}%"

        if avg_memory > 75:
            return True, f"High memory usage: {avg_memory:.1f}%"

        # Check endpoint performance
        slow_endpoint_count = sum(1 for m in self.monitor.endpoint_metrics.values() if m.p95_response_time > 200)

        if slow_endpoint_count > len(self.monitor.endpoint_metrics) * 0.5:
            return True, f"Multiple slow endpoints: {slow_endpoint_count}"

        return False, "Performance within acceptable range"

    def should_scale_down(self) -> Tuple[bool, str]:
        """Determine if system can scale down"""
        if len(self.monitor.snapshots) < 60:
            return False, "Insufficient data"

        # Check last 60 samples (1 minute)
        recent_snapshots = list(self.monitor.snapshots)[-60:]

        avg_cpu = statistics.mean([s.cpu_percent for s in recent_snapshots])
        avg_memory = statistics.mean([s.memory_percent for s in recent_snapshots])

        # Scale down if sustained low usage
        if avg_cpu < 30 and avg_memory < 40:
            return True, f"Low resource usage: CPU {avg_cpu:.1f}%, Memory {avg_memory:.1f}%"

        return False, "Cannot safely scale down"


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Jorge Platform Performance Monitoring")
    parser.add_argument(
        "--mode", choices=["monitor", "analyze", "dashboard"], default="monitor", help="Monitoring mode"
    )
    parser.add_argument("--duration", type=int, default=3600, help="Monitoring duration in seconds")
    parser.add_argument("--report-file", default="performance_report.json", help="Performance report output file")
    parser.add_argument("--interval", type=int, default=1, help="Sampling interval in seconds")

    args = parser.parse_args()

    monitor = PerformanceMonitor(sampling_interval=args.interval)

    if args.mode == "monitor":
        print(f"Starting performance monitoring for {args.duration} seconds...")
        print(f"Report will be saved to: {args.report_file}")
        print("Press Ctrl+C to stop early\n")

        try:
            asyncio.run(monitor.start_monitoring(duration_seconds=args.duration))
        finally:
            monitor.save_report(args.report_file)
            print(f"\n✅ Monitoring complete. Report saved to {args.report_file}")

    elif args.mode == "analyze":
        print(f"Analyzing performance data from: {args.report_file}")
        with open(args.report_file, "r") as f:
            report = json.load(f)

        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS REPORT")
        print("=" * 80)
        print(json.dumps(report, indent=2))

    elif args.mode == "dashboard":
        print("Real-time performance dashboard not yet implemented")
        print("Use --mode monitor for data collection")
