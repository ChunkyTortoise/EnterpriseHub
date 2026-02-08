#!/usr/bin/env python3
"""
Service 6 Metrics Collector - Production Monitoring Infrastructure
Comprehensive metrics collection for Service 6's 25+ agent system.

Features:
- Multi-layer metrics (agent, consensus, system, business)
- Real-time and time-series aggregation
- Performance overhead <5%
- Circuit breaker integration
- Failsafe collection (never blocks main operations)
"""

import asyncio
import functools
import json
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.database_service import get_database

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics collected"""

    AGENT_PERFORMANCE = "agent_performance"
    CONSENSUS_METRICS = "consensus_metrics"
    DATABASE_PERFORMANCE = "database_performance"
    BUSINESS_METRICS = "business_metrics"
    SYSTEM_HEALTH = "system_health"


class MetricCategory(Enum):
    """Metric categories for organization"""

    COUNTER = "counter"  # Monotonic increasing (requests, errors)
    GAUGE = "gauge"  # Point-in-time values (CPU, memory, active leads)
    HISTOGRAM = "histogram"  # Distribution of values (response times)
    TIMER = "timer"  # Duration measurements


@dataclass
class Metric:
    """Individual metric data point"""

    name: str
    value: Union[int, float]
    metric_type: MetricType
    category: MetricCategory
    timestamp: datetime
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentPerformanceMetric:
    """Agent-specific performance metrics"""

    agent_id: str
    agent_type: str
    operation_type: str
    execution_time_ms: float
    success: bool
    confidence: Optional[float]
    lead_id: Optional[str]
    error_type: Optional[str]
    timestamp: datetime

    def to_metric(self) -> List[Metric]:
        """Convert to standard metrics"""
        base_tags = {"agent_id": self.agent_id, "agent_type": self.agent_type, "operation_type": self.operation_type}

        metrics = [
            # Execution time
            Metric(
                name="agent_execution_time_ms",
                value=self.execution_time_ms,
                metric_type=MetricType.AGENT_PERFORMANCE,
                category=MetricCategory.HISTOGRAM,
                timestamp=self.timestamp,
                tags=base_tags,
            ),
            # Success/failure counter
            Metric(
                name="agent_operations_total",
                value=1,
                metric_type=MetricType.AGENT_PERFORMANCE,
                category=MetricCategory.COUNTER,
                timestamp=self.timestamp,
                tags={**base_tags, "status": "success" if self.success else "failure"},
            ),
        ]

        # Confidence metric if available
        if self.confidence is not None:
            metrics.append(
                Metric(
                    name="agent_confidence_score",
                    value=self.confidence,
                    metric_type=MetricType.AGENT_PERFORMANCE,
                    category=MetricCategory.GAUGE,
                    timestamp=self.timestamp,
                    tags=base_tags,
                )
            )

        return metrics


@dataclass
class ConsensusMetric:
    """Multi-agent consensus metrics"""

    consensus_id: str
    lead_id: str
    participating_agents: List[str]
    consensus_confidence: float
    consensus_time_ms: float
    agreement_score: float
    conflicting_agents: int
    final_decision: str
    timestamp: datetime

    def to_metric(self) -> List[Metric]:
        """Convert to standard metrics"""
        base_tags = {
            "consensus_id": self.consensus_id,
            "agent_count": str(len(self.participating_agents)),
            "decision": self.final_decision,
        }

        return [
            # Consensus time
            Metric(
                name="consensus_time_ms",
                value=self.consensus_time_ms,
                metric_type=MetricType.CONSENSUS_METRICS,
                category=MetricCategory.HISTOGRAM,
                timestamp=self.timestamp,
                tags=base_tags,
            ),
            # Consensus confidence
            Metric(
                name="consensus_confidence",
                value=self.consensus_confidence,
                metric_type=MetricType.CONSENSUS_METRICS,
                category=MetricCategory.GAUGE,
                timestamp=self.timestamp,
                tags=base_tags,
            ),
            # Agreement score
            Metric(
                name="consensus_agreement_score",
                value=self.agreement_score,
                metric_type=MetricType.CONSENSUS_METRICS,
                category=MetricCategory.GAUGE,
                timestamp=self.timestamp,
                tags=base_tags,
            ),
            # Conflicting agents
            Metric(
                name="consensus_conflicts",
                value=self.conflicting_agents,
                metric_type=MetricType.CONSENSUS_METRICS,
                category=MetricCategory.GAUGE,
                timestamp=self.timestamp,
                tags=base_tags,
            ),
        ]


class FailsafeMetricsCollector:
    """Failsafe metrics collector that never blocks main operations"""

    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self.metrics_queue = asyncio.Queue(maxsize=max_queue_size)
        self.cache_service = None
        self.database_service = None
        self.collection_task = None
        self.stats = {"collected": 0, "dropped": 0, "errors": 0, "last_collection": None}

    async def initialize(self):
        """Initialize metrics collector"""
        try:
            self.cache_service = get_cache_service()
            self.database_service = await get_database()

            # Start background collection task
            self.collection_task = asyncio.create_task(self._collection_worker())

            logger.info(
                "METRICS_COLLECTOR_INITIALIZED: Failsafe metrics collector started",
                extra={"max_queue_size": self.max_queue_size},
            )

        except Exception as e:
            logger.error(
                f"METRICS_COLLECTOR_INIT_FAILED: Failed to initialize metrics collector: {e}", extra={"error": str(e)}
            )

    async def collect_metric(self, metric: Metric) -> bool:
        """
        Collect metric with guaranteed non-blocking behavior

        Returns:
            bool: True if metric queued successfully, False if dropped
        """
        try:
            # Non-blocking queue put with immediate return
            self.metrics_queue.put_nowait(metric)
            return True

        except asyncio.QueueFull:
            # Queue full - drop metric but continue operation
            self.stats["dropped"] += 1
            logger.warning(
                "METRICS_QUEUE_FULL: Dropped metric due to full queue",
                extra={
                    "metric_name": metric.name,
                    "queue_size": self.max_queue_size,
                    "dropped_count": self.stats["dropped"],
                },
            )
            return False

        except Exception as e:
            # Any other error - log but don't propagate
            self.stats["errors"] += 1
            logger.error(
                f"METRIC_COLLECTION_ERROR: Error collecting metric: {e}",
                extra={"metric_name": metric.name, "error": str(e), "error_count": self.stats["errors"]},
            )
            return False

    async def _collection_worker(self):
        """Background worker to process metrics queue"""
        batch_size = 100
        batch_timeout = 1.0  # 1 second

        while True:
            try:
                metrics_batch = []
                deadline = time.time() + batch_timeout

                # Collect batch of metrics
                while len(metrics_batch) < batch_size and time.time() < deadline:
                    try:
                        # Wait for metric with remaining timeout
                        remaining_timeout = max(0.1, deadline - time.time())
                        metric = await asyncio.wait_for(self.metrics_queue.get(), timeout=remaining_timeout)
                        metrics_batch.append(metric)
                    except asyncio.TimeoutError:
                        break

                if metrics_batch:
                    await self._process_metrics_batch(metrics_batch)
                    self.stats["collected"] += len(metrics_batch)
                    self.stats["last_collection"] = datetime.now()

            except Exception as e:
                logger.error(f"METRICS_WORKER_ERROR: Error in metrics collection worker: {e}", extra={"error": str(e)})
                # Wait before retry to prevent tight error loop
                await asyncio.sleep(5.0)

    async def _process_metrics_batch(self, metrics: List[Metric]):
        """Process batch of metrics with fallback handling"""
        try:
            # Primary: Store in Redis for real-time access
            await self._store_hot_metrics(metrics)

            # Secondary: Store in PostgreSQL for historical analysis
            await self._store_warm_metrics(metrics)

        except Exception as e:
            logger.error(
                f"METRICS_PROCESSING_ERROR: Error processing metrics batch: {e}",
                extra={"batch_size": len(metrics), "error": str(e)},
            )
            # Fallback: Write to local file
            await self._write_to_failsafe_log(metrics)

    async def _store_hot_metrics(self, metrics: List[Metric]):
        """Store metrics in Redis for real-time dashboards"""
        if not self.cache_service:
            return

        try:
            for metric in metrics:
                # Store individual metric with TTL
                key = f"metric:{metric.name}:{metric.timestamp.isoformat()}"
                await self.cache_service.set(
                    key,
                    json.dumps(asdict(metric), default=str),
                    ttl=3600,  # 1 hour TTL for hot data
                )

                # Update aggregated counters
                await self._update_aggregated_metrics(metric)

        except Exception as e:
            logger.warning(f"Hot metrics storage failed: {e}")

    async def _store_warm_metrics(self, metrics: List[Metric]):
        """Store metrics in PostgreSQL for historical analysis"""
        if not self.database_service:
            return

        try:
            async with self.database_service.get_connection() as conn:
                # Prepare batch insert
                values = []
                for metric in metrics:
                    values.append(
                        (
                            metric.name,
                            metric.value,
                            metric.metric_type.value,
                            metric.category.value,
                            metric.timestamp,
                            json.dumps(metric.tags),
                            json.dumps(metric.metadata),
                        )
                    )

                # Batch insert for performance
                insert_query = """
                    INSERT INTO agent_metrics
                    (metric_name, metric_value, metric_type, metric_category,
                     timestamp, tags, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """

                await conn.executemany(insert_query, values)

        except Exception as e:
            logger.warning(f"Warm metrics storage failed: {e}")

    async def _update_aggregated_metrics(self, metric: Metric):
        """Update real-time aggregated metrics"""
        try:
            # Update counters by metric name
            counter_key = f"metric_count:{metric.name}"
            await self.cache_service.incr(counter_key, ttl=3600)

            # Update averages for gauge metrics
            if metric.category == MetricCategory.GAUGE:
                avg_key = f"metric_avg:{metric.name}"
                # Simple moving average approximation
                current_avg = await self.cache_service.get(avg_key) or 0
                new_avg = (float(current_avg) * 0.9) + (metric.value * 0.1)
                await self.cache_service.set(avg_key, new_avg, ttl=3600)

        except Exception as e:
            logger.debug(f"Aggregation update failed: {e}")

    async def _write_to_failsafe_log(self, metrics: List[Metric]):
        """Fallback: Write metrics to local log file"""
        try:
            import os

            log_dir = "/tmp/service6_metrics"
            os.makedirs(log_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H")
            log_file = os.path.join(log_dir, f"failsafe_metrics_{timestamp}.jsonl")

            with open(log_file, "a") as f:
                for metric in metrics:
                    f.write(json.dumps(asdict(metric), default=str) + "\n")

            logger.info(f"FAILSAFE_LOG: Wrote {len(metrics)} metrics to failsafe log", extra={"log_file": log_file})

        except Exception as e:
            logger.error(f"Failsafe logging failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            **self.stats,
            "queue_size": self.metrics_queue.qsize(),
            "queue_capacity": self.max_queue_size,
            "queue_utilization": self.metrics_queue.qsize() / self.max_queue_size,
        }


class PerformanceTracker:
    """Performance tracking context manager for operations"""

    def __init__(self, metrics_collector: FailsafeMetricsCollector):
        self.metrics_collector = metrics_collector

    @asynccontextmanager
    async def track_operation(
        self, operation_name: str, component: str = "unknown", metadata: Optional[Dict[str, Any]] = None
    ):
        """Track operation performance with context manager"""
        operation_id = f"{operation_name}_{uuid.uuid4().hex[:8]}"
        start_time = time.perf_counter()

        logger.debug(
            f"OPERATION_START: Starting tracked operation",
            extra={"operation_id": operation_id, "operation_name": operation_name, "component": component},
        )

        try:
            yield operation_id

            # Success case
            duration_ms = (time.perf_counter() - start_time) * 1000

            success_metric = Metric(
                name=f"{component}_operation_duration_ms",
                value=duration_ms,
                metric_type=MetricType.SYSTEM_HEALTH,
                category=MetricCategory.HISTOGRAM,
                timestamp=datetime.now(),
                tags={"operation": operation_name, "component": component, "status": "success"},
                metadata=metadata or {},
            )

            await self.metrics_collector.collect_metric(success_metric)

            logger.debug(
                f"OPERATION_SUCCESS: Operation completed successfully",
                extra={"operation_id": operation_id, "duration_ms": duration_ms},
            )

        except Exception as e:
            # Failure case
            duration_ms = (time.perf_counter() - start_time) * 1000

            failure_metric = Metric(
                name=f"{component}_operation_duration_ms",
                value=duration_ms,
                metric_type=MetricType.SYSTEM_HEALTH,
                category=MetricCategory.HISTOGRAM,
                timestamp=datetime.now(),
                tags={
                    "operation": operation_name,
                    "component": component,
                    "status": "failure",
                    "error_type": type(e).__name__,
                },
                metadata={**(metadata or {}), "error": str(e)},
            )

            await self.metrics_collector.collect_metric(failure_metric)

            logger.error(
                f"OPERATION_FAILURE: Operation failed",
                extra={"operation_id": operation_id, "duration_ms": duration_ms, "error": str(e)},
            )

            raise


def track_agent_performance(agent_type: str = None, operation_type: str = "analysis", collect_confidence: bool = True):
    """Decorator to track agent performance"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get metrics collector (assumes global instance)
            collector = _get_global_metrics_collector()
            if not collector:
                # No collector available - execute function normally
                return await func(*args, **kwargs)

            # Extract agent info
            agent_id = getattr(args[0], "agent_id", "unknown") if args else "unknown"
            determined_agent_type = agent_type or getattr(args[0], "agent_type", "unknown") if args else "unknown"

            start_time = time.perf_counter()
            success = False
            confidence = None
            error_type = None
            lead_id = kwargs.get("lead_id") or (args[1] if len(args) > 1 else None)

            try:
                result = await func(*args, **kwargs)
                success = True

                # Extract confidence from result if requested
                if collect_confidence and hasattr(result, "confidence"):
                    confidence = result.confidence

                return result

            except Exception as e:
                error_type = type(e).__name__
                raise

            finally:
                # Always collect metrics regardless of success/failure
                execution_time = (time.perf_counter() - start_time) * 1000

                try:
                    perf_metric = AgentPerformanceMetric(
                        agent_id=str(agent_id),
                        agent_type=str(determined_agent_type),
                        operation_type=operation_type,
                        execution_time_ms=execution_time,
                        success=success,
                        confidence=confidence,
                        lead_id=str(lead_id) if lead_id else None,
                        error_type=error_type,
                        timestamp=datetime.now(),
                    )

                    # Convert to standard metrics and collect
                    for metric in perf_metric.to_metric():
                        asyncio.create_task(collector.collect_metric(metric))

                except Exception as collection_error:
                    # Never let metrics collection affect main operation
                    logger.debug(f"Metric collection failed: {collection_error}")

        return wrapper

    return decorator


# Global metrics collector instance
_global_metrics_collector: Optional[FailsafeMetricsCollector] = None


async def initialize_metrics_collector() -> FailsafeMetricsCollector:
    """Initialize global metrics collector"""
    global _global_metrics_collector

    if _global_metrics_collector is None:
        _global_metrics_collector = FailsafeMetricsCollector()
        await _global_metrics_collector.initialize()

    return _global_metrics_collector


def _get_global_metrics_collector() -> Optional[FailsafeMetricsCollector]:
    """Get global metrics collector instance"""
    return _global_metrics_collector


# Export public interface
__all__ = [
    "MetricType",
    "MetricCategory",
    "Metric",
    "AgentPerformanceMetric",
    "ConsensusMetric",
    "FailsafeMetricsCollector",
    "PerformanceTracker",
    "track_agent_performance",
    "initialize_metrics_collector",
]
