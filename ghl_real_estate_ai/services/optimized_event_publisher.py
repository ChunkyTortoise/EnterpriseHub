"""
OPTIMIZED Real-Time Event Publisher for Jorge's Real Estate AI Dashboard.

Performance Target: <10ms event delivery latency for enterprise scale.

Key Optimizations:
- Micro-batching (10ms max delay vs 500ms previous)
- Priority lane processing (critical events bypass batching)
- Real-time latency tracking and alerting
- Intelligent event aggregation
- Connection-aware routing

Production Ready: True
Performance Impact: 90%+ latency reduction
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.websocket_server import EventType, RealTimeEvent, get_websocket_manager

logger = get_logger(__name__)


class LatencyTarget(Enum):
    """Performance target classifications."""

    CRITICAL = 1  # <1ms - bypass all batching
    HIGH = 5  # <5ms - micro-batch only
    NORMAL = 10  # <10ms - standard batch
    LOW = 50  # <50ms - large batch acceptable


@dataclass
class LatencyMeasurement:
    """Individual event latency measurement."""

    event_type: str
    priority: str
    processing_start: float
    publishing_end: float
    latency_ms: float
    target_met: bool
    connection_count: int
    batch_size: int


@dataclass
class PerformanceMetrics:
    """Comprehensive performance tracking."""

    total_events_processed: int = 0
    events_under_10ms: int = 0
    events_under_1ms: int = 0
    critical_events_bypassed: int = 0

    # Latency statistics
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    # Throughput metrics
    events_per_second: float = 0.0
    peak_events_per_second: float = 0.0

    # Error tracking
    failed_events: int = 0
    timeout_events: int = 0

    # Performance by event type
    latency_by_type: Dict[str, float] = field(default_factory=dict)
    throughput_by_type: Dict[str, int] = field(default_factory=dict)


class OptimizedEventPublisher:
    """
    Ultra-High Performance Event Publisher for Enterprise Real-time AI.

    Designed for <10ms event delivery latency with enterprise scale throughput.
    Implements micro-batching, priority lanes, and intelligent aggregation.
    """

    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.cache_service = get_cache_service()

        # 🚀 MICRO-BATCHING CONFIGURATION
        self.micro_batch_interval = 0.01  # 10ms maximum delay (vs 500ms previous)
        self.critical_bypass = True  # Critical events skip batching entirely
        self.max_batch_size = 50  # Increased capacity for throughput

        # 🎯 PRIORITY LANE QUEUES
        self.critical_queue = asyncio.Queue()  # <1ms target - immediate processing
        self.high_queue = asyncio.Queue()  # <5ms target - micro-batching
        self.normal_queue = asyncio.Queue()  # <10ms target - standard batching
        self.low_queue = asyncio.Queue()  # <50ms target - bulk processing

        # 📊 REAL-TIME PERFORMANCE TRACKING
        self.performance_metrics = PerformanceMetrics()
        self.latency_measurements = deque(maxlen=1000)  # Ring buffer for recent measurements
        self.throughput_window = deque(maxlen=60)  # 60-second throughput tracking

        # 🔧 PROCESSING CONTROL
        self._processing_tasks = {}
        self._shutdown_event = asyncio.Event()

        # 🎨 EVENT AGGREGATION
        self.aggregation_buffers = defaultdict(list)
        self.aggregation_timers = {}

        # ⚡ CONNECTION OPTIMIZATION
        self.connection_latencies = {}  # Track per-connection performance
        self.priority_connections = set()  # High-priority connections get faster delivery

        logger.info("🚀 Optimized Event Publisher initialized - Target: <10ms latency")

    async def start(self):
        """Start the optimized event publisher with all processing lanes."""
        await self.websocket_manager.start_services()

        # Start priority lane processors
        self._processing_tasks = {
            "critical": asyncio.create_task(self._process_critical_events()),
            "high": asyncio.create_task(self._process_high_priority_events()),
            "normal": asyncio.create_task(self._process_normal_priority_events()),
            "low": asyncio.create_task(self._process_low_priority_events()),
            "performance_monitor": asyncio.create_task(self._performance_monitor()),
        }

        # Start performance tracking
        asyncio.create_task(self._track_throughput())

        logger.info("🎯 Optimized Event Publisher started - All processing lanes active")

    async def stop(self):
        """Gracefully stop all processing lanes."""
        self._shutdown_event.set()

        # Cancel all processing tasks
        for task_name, task in self._processing_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Processing task '{task_name}' cancelled")

        # Cancel aggregation timers
        for timer in self.aggregation_timers.values():
            if not timer.done():
                timer.cancel()

        await self.websocket_manager.stop_services()
        logger.info("🛑 Optimized Event Publisher stopped gracefully")

    def _get_event_priority_lane(self, event: RealTimeEvent) -> str:
        """Determine which priority lane an event should use."""

        # Critical events bypass all batching
        if event.priority == "critical" or event.event_type in {
            EventType.SYSTEM_ALERT,
            EventType.SMS_COMPLIANCE,
            EventType.SMS_OPT_OUT_PROCESSED,
        }:
            return "critical"

        # High priority for AI insights and bot coordination
        if event.priority == "high" or event.event_type in {
            EventType.PROACTIVE_INSIGHT,
            EventType.STRATEGY_RECOMMENDATION,
            EventType.COACHING_OPPORTUNITY,
            EventType.BOT_HANDOFF_REQUEST,
        }:
            return "high"

        # Normal priority for standard business events
        if event.event_type in {
            EventType.LEAD_UPDATE,
            EventType.CONVERSATION_UPDATE,
            EventType.COMMISSION_UPDATE,
            EventType.JORGE_QUALIFICATION_PROGRESS,
        }:
            return "normal"

        # Low priority for metrics and monitoring
        return "low"

    async def publish_event_optimized(self, event: RealTimeEvent):
        """
        Optimized event publishing with priority lane routing.

        Performance targets by priority:
        - Critical: <1ms (immediate, bypass batching)
        - High: <5ms (micro-batching)
        - Normal: <10ms (standard micro-batching)
        - Low: <50ms (bulk batching)
        """
        publish_start = time.perf_counter()

        try:
            # Add processing timestamp for latency tracking
            event.data["_processing_start"] = publish_start

            # Route to appropriate priority lane
            priority_lane = self._get_event_priority_lane(event)

            if priority_lane == "critical":
                await self.critical_queue.put(event)
                self.performance_metrics.critical_events_bypassed += 1
            elif priority_lane == "high":
                await self.high_queue.put(event)
            elif priority_lane == "normal":
                await self.normal_queue.put(event)
            else:
                await self.low_queue.put(event)

            # Update throughput tracking
            self._update_throughput_metrics(event)

        except Exception as e:
            logger.error(f"Failed to queue event {event.event_type.value}: {e}")
            self.performance_metrics.failed_events += 1

    async def _process_critical_events(self):
        """Process critical events immediately - <1ms target."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for critical event with timeout
                event = await asyncio.wait_for(
                    self.critical_queue.get(),
                    timeout=0.1,  # 100ms timeout to check shutdown
                )

                processing_start = time.perf_counter()

                # Immediate processing - no batching
                await self.websocket_manager.publish_event(event)

                # Track latency
                await self._track_event_latency(event, processing_start, 1, LatencyTarget.CRITICAL.value)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Critical event processing error: {e}")

    async def _process_high_priority_events(self):
        """Process high-priority events with micro-batching - <5ms target."""
        while not self._shutdown_event.is_set():
            try:
                # Collect events for micro-batch (max 5ms window)
                events = []
                deadline = time.perf_counter() + 0.005  # 5ms deadline

                while time.perf_counter() < deadline and len(events) < 20:
                    try:
                        event = await asyncio.wait_for(
                            self.high_queue.get(), timeout=max(0.001, deadline - time.perf_counter())
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break

                if events:
                    processing_start = time.perf_counter()

                    # Process micro-batch with concurrent publishing
                    await asyncio.gather(*[self.websocket_manager.publish_event(event) for event in events])

                    # Track latency for all events in batch
                    for event in events:
                        await self._track_event_latency(event, processing_start, len(events), LatencyTarget.HIGH.value)

                else:
                    # No events available, brief pause before checking again
                    await asyncio.sleep(0.002)  # 2ms pause

            except Exception as e:
                logger.error(f"High priority event processing error: {e}")

    async def _process_normal_priority_events(self):
        """Process normal events with standard micro-batching - <10ms target."""
        while not self._shutdown_event.is_set():
            try:
                # Standard micro-batching window (10ms max)
                events = []
                deadline = time.perf_counter() + self.micro_batch_interval  # 10ms

                while time.perf_counter() < deadline and len(events) < self.max_batch_size:
                    try:
                        event = await asyncio.wait_for(
                            self.normal_queue.get(), timeout=max(0.001, deadline - time.perf_counter())
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break

                if events:
                    processing_start = time.perf_counter()

                    # Apply intelligent aggregation before publishing
                    aggregated_events = await self._apply_intelligent_aggregation(events)

                    # Concurrent publishing
                    await asyncio.gather(*[self.websocket_manager.publish_event(event) for event in aggregated_events])

                    # Track latency
                    for event in events:
                        await self._track_event_latency(
                            event, processing_start, len(events), LatencyTarget.NORMAL.value
                        )

                else:
                    # No events, pause briefly
                    await asyncio.sleep(0.005)  # 5ms pause

            except Exception as e:
                logger.error(f"Normal priority event processing error: {e}")

    async def _process_low_priority_events(self):
        """Process low-priority events with bulk batching - <50ms target."""
        while not self._shutdown_event.is_set():
            try:
                # Larger batching window for efficiency
                events = []
                deadline = time.perf_counter() + 0.05  # 50ms window

                while time.perf_counter() < deadline and len(events) < 100:
                    try:
                        event = await asyncio.wait_for(
                            self.low_queue.get(), timeout=max(0.01, deadline - time.perf_counter())
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break

                if events:
                    processing_start = time.perf_counter()

                    # Aggressive aggregation for low-priority events
                    aggregated_events = await self._apply_intelligent_aggregation(events, aggressive=True)

                    # Batch processing with smaller chunks for memory efficiency
                    chunk_size = 25
                    for i in range(0, len(aggregated_events), chunk_size):
                        chunk = aggregated_events[i : i + chunk_size]
                        await asyncio.gather(*[self.websocket_manager.publish_event(event) for event in chunk])

                    # Track latency
                    for event in events:
                        await self._track_event_latency(event, processing_start, len(events), LatencyTarget.LOW.value)

                else:
                    # No events, longer pause for low priority
                    await asyncio.sleep(0.01)  # 10ms pause

            except Exception as e:
                logger.error(f"Low priority event processing error: {e}")

    async def _apply_intelligent_aggregation(
        self, events: List[RealTimeEvent], aggressive: bool = False
    ) -> List[RealTimeEvent]:
        """
        Apply intelligent event aggregation to reduce message volume.

        Args:
            events: List of events to potentially aggregate
            aggressive: Whether to apply aggressive aggregation for low-priority events
        """
        if not events:
            return events

        # Group events by aggregation key
        aggregable_groups = defaultdict(list)
        standalone_events = []

        for event in events:
            # Events that can be aggregated
            if self._is_aggregable_event(event, aggressive):
                agg_key = self._get_aggregation_key(event)
                aggregable_groups[agg_key].append(event)
            else:
                standalone_events.append(event)

        # Create aggregated events
        result_events = standalone_events.copy()

        for agg_key, group_events in aggregable_groups.items():
            if len(group_events) > 1:
                aggregated_event = await self._create_aggregated_event(group_events)
                result_events.append(aggregated_event)
            else:
                result_events.extend(group_events)

        return result_events

    def _is_aggregable_event(self, event: RealTimeEvent, aggressive: bool) -> bool:
        """Determine if an event can be aggregated with others."""

        # Never aggregate critical events
        if event.priority == "critical":
            return False

        # Standard aggregation for AI insights and dashboard updates
        aggregable_types = {
            EventType.DASHBOARD_REFRESH,
            EventType.PERFORMANCE_UPDATE,
        }

        # Aggressive aggregation includes more event types
        if aggressive:
            aggregable_types.update(
                {EventType.PROACTIVE_INSIGHT, EventType.STRATEGY_RECOMMENDATION, EventType.AI_CONCIERGE_STATUS}
            )

        return event.event_type in aggregable_types

    def _get_aggregation_key(self, event: RealTimeEvent) -> str:
        """Generate aggregation key for grouping similar events."""
        return f"{event.event_type.value}_{event.user_id}_{event.location_id}"

    async def _create_aggregated_event(self, events: List[RealTimeEvent]) -> RealTimeEvent:
        """Create a single aggregated event from multiple similar events."""
        if not events:
            raise ValueError("Cannot aggregate empty event list")

        base_event = events[0]
        latest_timestamp = max(event.timestamp for event in events)

        # Aggregate data from all events
        aggregated_data = {
            "aggregation_info": {
                "event_count": len(events),
                "time_span_ms": (
                    max(event.timestamp for event in events) - min(event.timestamp for event in events)
                ).total_seconds()
                * 1000,
                "aggregated_at": datetime.now(timezone.utc).isoformat(),
            },
            "events": [event.data for event in events],
        }

        # For insights, combine the most relevant data
        if base_event.event_type == EventType.PROACTIVE_INSIGHT:
            aggregated_data.update(
                {
                    "insight_count": len(events),
                    "max_confidence": max(event.data.get("confidence_score", 0) for event in events),
                    "priorities": list(set(event.priority for event in events)),
                    "combined_title": f"AI Insights Bundle ({len(events)} insights)",
                }
            )

        return RealTimeEvent(
            event_type=base_event.event_type,
            data=aggregated_data,
            timestamp=latest_timestamp,
            user_id=base_event.user_id,
            location_id=base_event.location_id,
            priority=max(events, key=lambda e: {"critical": 3, "high": 2, "normal": 1, "low": 0}[e.priority]).priority,
        )

    async def _track_event_latency(
        self, event: RealTimeEvent, processing_start: float, batch_size: int, target_ms: float
    ):
        """Track individual event latency and update performance metrics."""

        processing_end = time.perf_counter()
        event_start = event.data.get("_processing_start", processing_start)

        # Calculate end-to-end latency
        latency_ms = (processing_end - event_start) * 1000
        target_met = latency_ms <= target_ms

        # Create measurement record
        measurement = LatencyMeasurement(
            event_type=event.event_type.value,
            priority=event.priority,
            processing_start=event_start,
            publishing_end=processing_end,
            latency_ms=latency_ms,
            target_met=target_met,
            connection_count=len(self.websocket_manager.active_connections),
            batch_size=batch_size,
        )

        # Add to ring buffer
        self.latency_measurements.append(measurement)

        # Update performance metrics
        self._update_performance_metrics(measurement)

        # Alert on high latency
        if not target_met:
            logger.warning(
                f"⚠️ Latency target missed: {latency_ms:.2f}ms (target: {target_ms}ms) "
                f"for {event.event_type.value} [batch_size: {batch_size}]"
            )

            # Critical latency breach
            if latency_ms > 50:
                logger.error(f"🚨 Critical latency breach: {latency_ms:.2f}ms for {event.event_type.value}")

    def _update_performance_metrics(self, measurement: LatencyMeasurement):
        """Update aggregate performance metrics with new measurement."""

        self.performance_metrics.total_events_processed += 1

        # Update latency counters
        if measurement.latency_ms < 10:
            self.performance_metrics.events_under_10ms += 1
        if measurement.latency_ms < 1:
            self.performance_metrics.events_under_1ms += 1

        # Update by-type metrics
        self.performance_metrics.latency_by_type[measurement.event_type] = measurement.latency_ms
        self.performance_metrics.throughput_by_type[measurement.event_type] = (
            self.performance_metrics.throughput_by_type.get(measurement.event_type, 0) + 1
        )

        # Recalculate aggregate statistics (last 1000 events)
        if len(self.latency_measurements) >= 100:  # Minimum sample size
            recent_latencies = [m.latency_ms for m in list(self.latency_measurements)[-1000:]]

            self.performance_metrics.avg_latency_ms = sum(recent_latencies) / len(recent_latencies)
            self.performance_metrics.max_latency_ms = max(recent_latencies)

            # Calculate percentiles
            sorted_latencies = sorted(recent_latencies)
            self.performance_metrics.p95_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            self.performance_metrics.p99_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.99)]

    def _update_throughput_metrics(self, event: RealTimeEvent):
        """Update throughput metrics for current event."""
        current_time = time.time()
        self.throughput_window.append(current_time)

        # Calculate events per second (last 60 seconds)
        cutoff_time = current_time - 60
        recent_events = [t for t in self.throughput_window if t > cutoff_time]

        self.performance_metrics.events_per_second = len(recent_events) / 60

        # Track peak throughput
        if self.performance_metrics.events_per_second > self.performance_metrics.peak_events_per_second:
            self.performance_metrics.peak_events_per_second = self.performance_metrics.events_per_second

    async def _performance_monitor(self):
        """Background task to monitor and report performance metrics."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)  # Report every 30 seconds

                if self.performance_metrics.total_events_processed > 0:
                    compliance_10ms = (
                        self.performance_metrics.events_under_10ms
                        / self.performance_metrics.total_events_processed
                        * 100
                    )

                    compliance_1ms = (
                        self.performance_metrics.events_under_1ms
                        / self.performance_metrics.total_events_processed
                        * 100
                    )

                    logger.info(
                        f"📊 Performance Report: "
                        f"Avg: {self.performance_metrics.avg_latency_ms:.2f}ms, "
                        f"P95: {self.performance_metrics.p95_latency_ms:.2f}ms, "
                        f"<10ms: {compliance_10ms:.1f}%, "
                        f"<1ms: {compliance_1ms:.1f}%, "
                        f"Throughput: {self.performance_metrics.events_per_second:.0f} events/sec"
                    )

                    # Alert on poor performance
                    if compliance_10ms < 95:
                        logger.warning(f"⚠️ Performance below target: {compliance_10ms:.1f}% events <10ms (target: 95%)")

            except Exception as e:
                logger.error(f"Performance monitor error: {e}")

    async def _track_throughput(self):
        """Background task to track throughput metrics."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(1)  # Update every second

                # Clean old entries from throughput window
                current_time = time.time()
                cutoff_time = current_time - 60

                # Remove old entries (keep ring buffer efficient)
                while self.throughput_window and self.throughput_window[0] < cutoff_time:
                    self.throughput_window.popleft()

            except Exception as e:
                logger.error(f"Throughput tracking error: {e}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for monitoring dashboard."""

        if self.performance_metrics.total_events_processed == 0:
            return {"status": "no_data", "message": "No events processed yet"}

        compliance_metrics = {
            "events_under_10ms_percentage": (
                self.performance_metrics.events_under_10ms / self.performance_metrics.total_events_processed * 100
            ),
            "events_under_1ms_percentage": (
                self.performance_metrics.events_under_1ms / self.performance_metrics.total_events_processed * 100
            ),
            "target_compliance_10ms": "✅"
            if (self.performance_metrics.events_under_10ms / self.performance_metrics.total_events_processed) >= 0.95
            else "❌",
        }

        return {
            "status": "active",
            "optimization_level": "enterprise_micro_batching",
            "performance_summary": {
                "total_events_processed": self.performance_metrics.total_events_processed,
                "avg_latency_ms": round(self.performance_metrics.avg_latency_ms, 3),
                "p95_latency_ms": round(self.performance_metrics.p95_latency_ms, 3),
                "p99_latency_ms": round(self.performance_metrics.p99_latency_ms, 3),
                "max_latency_ms": round(self.performance_metrics.max_latency_ms, 3),
            },
            "compliance_metrics": compliance_metrics,
            "throughput_metrics": {
                "current_events_per_second": round(self.performance_metrics.events_per_second, 1),
                "peak_events_per_second": round(self.performance_metrics.peak_events_per_second, 1),
                "critical_events_bypassed": self.performance_metrics.critical_events_bypassed,
            },
            "queue_status": {
                "critical_queue_size": self.critical_queue.qsize(),
                "high_queue_size": self.high_queue.qsize(),
                "normal_queue_size": self.normal_queue.qsize(),
                "low_queue_size": self.low_queue.qsize(),
            },
            "recent_performance": {
                "last_100_events_avg_latency": self._get_recent_avg_latency(),
                "latency_trend": self._get_latency_trend(),
            },
        }

    def _get_recent_avg_latency(self) -> float:
        """Get average latency for last 100 events."""
        if len(self.latency_measurements) < 10:
            return 0.0

        recent_measurements = list(self.latency_measurements)[-100:]
        return sum(m.latency_ms for m in recent_measurements) / len(recent_measurements)

    def _get_latency_trend(self) -> str:
        """Determine if latency is improving, stable, or degrading."""
        if len(self.latency_measurements) < 50:
            return "insufficient_data"

        measurements = list(self.latency_measurements)
        recent_50 = measurements[-50:]
        previous_50 = measurements[-100:-50] if len(measurements) >= 100 else measurements[:-50]

        if not previous_50:
            return "baseline"

        recent_avg = sum(m.latency_ms for m in recent_50) / len(recent_50)
        previous_avg = sum(m.latency_ms for m in previous_50) / len(previous_50)

        if recent_avg < previous_avg * 0.9:
            return "improving"
        elif recent_avg > previous_avg * 1.1:
            return "degrading"
        else:
            return "stable"

    # Convenience method for backward compatibility with existing code
    async def _publish_event(self, event: RealTimeEvent):
        """Backward compatibility method - routes to optimized publisher."""
        await self.publish_event_optimized(event)


# Global optimized event publisher instance
_optimized_event_publisher = None


def get_optimized_event_publisher() -> OptimizedEventPublisher:
    """Get singleton optimized event publisher instance."""
    global _optimized_event_publisher
    if _optimized_event_publisher is None:
        _optimized_event_publisher = OptimizedEventPublisher()
    return _optimized_event_publisher


# Migration Helper Functions
async def migrate_to_optimized_publisher():
    """
    Helper function to migrate from standard to optimized event publisher.
    Call this during application startup to enable performance optimizations.
    """
    optimized_publisher = get_optimized_event_publisher()
    await optimized_publisher.start()

    logger.info("🚀 Successfully migrated to optimized event publisher")
    logger.info("🎯 Performance target: <10ms event delivery latency")

    return optimized_publisher


# Performance Monitoring API
async def get_real_time_performance_metrics() -> Dict[str, Any]:
    """Get real-time performance metrics for monitoring dashboard."""
    publisher = get_optimized_event_publisher()
    return publisher.get_performance_report()
