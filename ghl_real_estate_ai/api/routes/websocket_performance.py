"""
WebSocket Performance Monitoring API

Real-time performance metrics and optimization tracking for Jorge's AI Platform WebSocket infrastructure.
Provides comprehensive latency tracking, throughput monitoring, and optimization validation.

Target: <10ms event delivery latency validation and monitoring
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.optimized_event_publisher import (
    get_optimized_event_publisher,
    get_real_time_performance_metrics,
)
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/websocket-performance", tags=["WebSocket Performance"])


@router.get("/latency-metrics")
async def get_latency_metrics() -> Dict[str, Any]:
    """
    Get comprehensive WebSocket latency metrics for performance monitoring.

    Returns:
        Real-time latency statistics including percentiles, compliance, and trends
    """
    try:
        performance_report = await get_real_time_performance_metrics()

        if performance_report.get("status") == "no_data":
            return {
                "status": "initializing",
                "message": "Performance monitoring is initializing. Please wait for event data.",
                "recommendations": [
                    "Generate some test events to begin performance tracking",
                    "Check that optimized event publisher is properly started",
                ],
            }

        # Add additional computed metrics
        performance_summary = performance_report.get("performance_summary", {})
        compliance_metrics = performance_report.get("compliance_metrics", {})

        # Calculate optimization effectiveness
        optimization_effectiveness = {
            "latency_improvement": _calculate_improvement_vs_baseline(performance_summary.get("avg_latency_ms", 0)),
            "target_achievement": {
                "10ms_compliance": compliance_metrics.get("events_under_10ms_percentage", 0),
                "1ms_compliance": compliance_metrics.get("events_under_1ms_percentage", 0),
                "grade": _get_performance_grade(compliance_metrics.get("events_under_10ms_percentage", 0)),
            },
            "optimization_status": performance_report.get("compliance_metrics", {}).get("target_compliance_10ms", "❌"),
        }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "optimization_level": "enterprise_micro_batching",
            **performance_report,
            "optimization_effectiveness": optimization_effectiveness,
        }

    except Exception as e:
        logger.error(f"Failed to get latency metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/throughput-metrics")
async def get_throughput_metrics() -> Dict[str, Any]:
    """
    Get real-time WebSocket throughput and connection metrics.

    Returns:
        Throughput statistics, connection health, and capacity utilization
    """
    try:
        websocket_manager = get_websocket_manager()
        publisher = get_optimized_event_publisher()

        # WebSocket connection metrics
        connection_metrics = websocket_manager.get_metrics()

        # Publisher performance metrics
        performance_report = await get_real_time_performance_metrics()
        throughput_metrics = performance_report.get("throughput_metrics", {})
        queue_status = performance_report.get("queue_status", {})

        # Calculate capacity utilization
        max_theoretical_throughput = 10000  # events/second (enterprise target)
        current_throughput = throughput_metrics.get("current_events_per_second", 0)

        capacity_utilization = {
            "current_load_percentage": min(100, (current_throughput / max_theoretical_throughput) * 100),
            "peak_load_percentage": min(
                100, (throughput_metrics.get("peak_events_per_second", 0) / max_theoretical_throughput) * 100
            ),
            "remaining_capacity": max(0, max_theoretical_throughput - current_throughput),
            "status": _get_capacity_status(current_throughput, max_theoretical_throughput),
        }

        # Queue health analysis
        total_queued = sum(queue_status.values()) if queue_status else 0
        queue_health = {
            "total_events_queued": total_queued,
            "queue_distribution": queue_status,
            "queue_health_status": "healthy" if total_queued < 100 else "warning" if total_queued < 500 else "critical",
            "processing_lag_estimated_ms": _estimate_processing_lag(queue_status),
        }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "connection_metrics": {
                "active_connections": connection_metrics.get("active_connections", 0),
                "active_connections_by_role": connection_metrics.get("active_connections_by_role", {}),
                "connection_health": _assess_connection_health(connection_metrics),
            },
            "throughput_metrics": {
                **throughput_metrics,
                "theoretical_max_throughput": max_theoretical_throughput,
                "efficiency_score": _calculate_efficiency_score(throughput_metrics, connection_metrics),
            },
            "capacity_utilization": capacity_utilization,
            "queue_health": queue_health,
        }

    except Exception as e:
        logger.error(f"Failed to get throughput metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/connection-health")
async def get_connection_health() -> Dict[str, Any]:
    """
    Get detailed WebSocket connection health and quality metrics.

    Returns:
        Connection quality, latency per connection, and health recommendations
    """
    try:
        websocket_manager = get_websocket_manager()
        connections_info = websocket_manager.get_connection_info()

        # Analyze connection health
        healthy_connections = 0
        degraded_connections = 0
        total_connections = len(connections_info)

        connection_details = []

        for conn_info in connections_info:
            connection_id = conn_info["connection_id"]

            # Get connection-specific latency if available
            connection_latency = websocket_manager.connection_latencies.get(connection_id, 0)

            health_status = "healthy"
            if connection_latency > 50:
                health_status = "degraded"
                degraded_connections += 1
            elif connection_latency > 100:
                health_status = "critical"
                degraded_connections += 1
            else:
                healthy_connections += 1

            connection_details.append(
                {
                    "connection_id": connection_id,
                    "user_role": conn_info.get("role"),
                    "connected_duration": _calculate_connection_duration(conn_info.get("connected_at")),
                    "latency_ms": connection_latency,
                    "health_status": health_status,
                    "last_activity": conn_info.get("last_heartbeat"),
                }
            )

        # Overall health assessment
        health_percentage = (healthy_connections / max(1, total_connections)) * 100
        overall_health = (
            "excellent"
            if health_percentage > 95
            else "good"
            if health_percentage > 80
            else "warning"
            if health_percentage > 60
            else "critical"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": {
                "status": overall_health,
                "health_percentage": round(health_percentage, 1),
                "healthy_connections": healthy_connections,
                "degraded_connections": degraded_connections,
                "total_connections": total_connections,
            },
            "connection_statistics": {
                "average_latency_ms": _calculate_average_connection_latency(connection_details),
                "max_latency_ms": max([conn["latency_ms"] for conn in connection_details], default=0),
                "connections_by_health": _group_connections_by_health(connection_details),
            },
            "connection_details": connection_details,
            "recommendations": _generate_health_recommendations(overall_health, connection_details),
        }

    except Exception as e:
        logger.error(f"Failed to get connection health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/optimization-status")
async def get_optimization_status() -> Dict[str, Any]:
    """
    Get current optimization status and recommendations for improving performance.

    Returns:
        Optimization effectiveness, recommendations, and configuration status
    """
    try:
        performance_report = await get_real_time_performance_metrics()

        if performance_report.get("status") == "no_data":
            return {
                "status": "not_optimized",
                "message": "Optimization system is not active or has no performance data",
                "recommendations": [
                    "Migrate to optimized event publisher using migrate_to_optimized_publisher()",
                    "Generate test events to establish baseline performance",
                    "Verify WebSocket connections are active",
                ],
            }

        compliance = performance_report.get("compliance_metrics", {})
        performance = performance_report.get("performance_summary", {})

        # Determine optimization effectiveness
        avg_latency = performance.get("avg_latency_ms", 1000)
        p95_latency = performance.get("p95_latency_ms", 1000)
        compliance_10ms = compliance.get("events_under_10ms_percentage", 0)

        optimization_grade = _get_optimization_grade(avg_latency, p95_latency, compliance_10ms)

        recommendations = _generate_optimization_recommendations(
            avg_latency, p95_latency, compliance_10ms, performance_report.get("queue_status", {})
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "optimization_status": {
                "grade": optimization_grade,
                "target_achievement": "✅ ACHIEVED"
                if compliance_10ms >= 95
                else "🎯 IN PROGRESS"
                if compliance_10ms >= 80
                else "❌ NEEDS WORK",
                "performance_vs_baseline": f"{_calculate_improvement_vs_baseline(avg_latency):.1f}x improvement",
                "optimization_level": performance_report.get("optimization_level", "standard"),
            },
            "current_performance": {
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "target_compliance_percentage": compliance_10ms,
                "events_processed": performance.get("total_events_processed", 0),
            },
            "recommendations": recommendations,
            "next_optimization_phases": _get_next_optimization_phases(optimization_grade, compliance_10ms),
        }

    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/live-metrics-stream")
async def get_live_metrics_stream():
    """
    Server-Sent Events stream for real-time performance monitoring.

    Returns:
        Streaming response with live performance updates every 2 seconds
    """

    async def event_stream():
        try:
            while True:
                # Gather latest metrics
                performance_data = await get_real_time_performance_metrics()

                # Format as SSE event
                data = {"timestamp": datetime.utcnow().isoformat(), "type": "performance_update", **performance_data}

                yield f"data: {json.dumps(data)}\n\n"

                await asyncio.sleep(2)  # Update every 2 seconds

        except Exception as e:
            logger.error(f"Live metrics stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Access-Control-Allow-Origin": "*"},
    )


@router.post("/trigger-performance-test")
async def trigger_performance_test(
    event_count: int = 1000, background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    Trigger a controlled performance test to validate optimization effectiveness.

    Args:
        event_count: Number of test events to generate (default: 1000)

    Returns:
        Test execution status and expected completion time
    """
    if event_count > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10,000 test events allowed")

    # Schedule background performance test
    background_tasks.add_task(_run_performance_test, event_count)

    estimated_duration_seconds = (event_count / 1000) * 10  # Rough estimate

    return {
        "test_id": f"perf_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "status": "scheduled",
        "event_count": event_count,
        "estimated_duration_seconds": estimated_duration_seconds,
        "monitoring_endpoint": "/api/v1/websocket-performance/latency-metrics",
        "message": f"Performance test with {event_count} events has been scheduled",
    }


# Helper Functions


def _calculate_improvement_vs_baseline(current_latency_ms: float) -> float:
    """Calculate improvement factor vs original 500ms baseline."""
    baseline_latency = 500  # Original batch interval
    if current_latency_ms <= 0:
        return float("inf")
    return baseline_latency / current_latency_ms


def _get_performance_grade(compliance_percentage: float) -> str:
    """Get performance grade based on <10ms compliance percentage."""
    if compliance_percentage >= 99:
        return "A+ (Exceptional)"
    elif compliance_percentage >= 95:
        return "A (Excellent)"
    elif compliance_percentage >= 90:
        return "B+ (Very Good)"
    elif compliance_percentage >= 80:
        return "B (Good)"
    elif compliance_percentage >= 70:
        return "C+ (Acceptable)"
    elif compliance_percentage >= 60:
        return "C (Needs Improvement)"
    else:
        return "D (Poor - Optimization Required)"


def _get_capacity_status(current_throughput: float, max_throughput: float) -> str:
    """Determine capacity utilization status."""
    utilization = (current_throughput / max_throughput) * 100

    if utilization < 50:
        return "optimal"
    elif utilization < 70:
        return "moderate"
    elif utilization < 85:
        return "high"
    else:
        return "near_capacity"


def _estimate_processing_lag(queue_status: Dict[str, int]) -> float:
    """Estimate processing lag based on queue sizes and typical processing rates."""
    if not queue_status:
        return 0.0

    # Estimated processing rates per priority lane (events/second)
    processing_rates = {
        "critical_queue_size": 10000,  # Immediate processing
        "high_queue_size": 2000,  # 5ms micro-batching
        "normal_queue_size": 1000,  # 10ms micro-batching
        "low_queue_size": 200,  # 50ms bulk batching
    }

    total_lag = 0.0
    for queue_name, queue_size in queue_status.items():
        if queue_size > 0:
            processing_rate = processing_rates.get(queue_name, 100)
            lag_seconds = queue_size / processing_rate
            total_lag += lag_seconds * 1000  # Convert to milliseconds

    return round(total_lag, 2)


def _assess_connection_health(connection_metrics: Dict[str, Any]) -> str:
    """Assess overall connection health status."""
    active_connections = connection_metrics.get("active_connections", 0)

    if active_connections == 0:
        return "no_connections"
    elif active_connections < 10:
        return "low_volume"
    elif active_connections < 100:
        return "normal"
    elif active_connections < 500:
        return "high_volume"
    else:
        return "enterprise_scale"


def _calculate_efficiency_score(throughput_metrics: Dict[str, Any], connection_metrics: Dict[str, Any]) -> float:
    """Calculate overall system efficiency score (0-100)."""
    events_per_second = throughput_metrics.get("current_events_per_second", 0)
    active_connections = connection_metrics.get("active_connections", 1)

    # Calculate events per connection per second
    events_per_connection = events_per_second / max(1, active_connections)

    # Normalize to 0-100 scale (10 events/connection/second = 100%)
    efficiency = min(100, (events_per_connection / 10) * 100)

    return round(efficiency, 1)


def _calculate_connection_duration(connected_at: str) -> str:
    """Calculate human-readable connection duration."""
    try:
        connect_time = datetime.fromisoformat(connected_at.replace("Z", "+00:00"))
        duration = datetime.utcnow().replace(tzinfo=connect_time.tzinfo) - connect_time

        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    except ValueError: # Changed bare except to specific ValueError
        return "unknown"


def _calculate_average_connection_latency(connection_details: List[Dict[str, Any]]) -> float:
    """Calculate average latency across all connections."""
    if not connection_details:
        return 0.0

    latencies = [conn["latency_ms"] for conn in connection_details if conn["latency_ms"] > 0]
    return round(sum(latencies) / len(latencies), 2) if latencies else 0.0


def _group_connections_by_health(connection_details: List[Dict[str, Any]]) -> Dict[str, int]:
    """Group connections by health status."""
    health_groups = {"healthy": 0, "degraded": 0, "critical": 0}

    for conn in connection_details:
        status = conn.get("health_status", "unknown")
        if status in health_groups:
            health_groups[status] += 1

    return health_groups


def _generate_health_recommendations(overall_health: str, connection_details: List[Dict[str, Any]]) -> List[str]:
    """Generate health improvement recommendations."""
    recommendations = []

    if overall_health in ["warning", "critical"]:
        recommendations.append("⚠️ Multiple degraded connections detected - investigate network quality")
        recommendations.append("🔧 Consider increasing heartbeat frequency for problematic connections")

    high_latency_connections = [c for c in connection_details if c["latency_ms"] > 100]
    if high_latency_connections:
        recommendations.append(
            f"🌐 {len(high_latency_connections)} connections with >100ms latency - check client networks"
        )

    if len(connection_details) > 1000:
        recommendations.append("📈 High connection count - monitor for scaling opportunities")

    if not recommendations:
        recommendations.append("✅ All connections healthy - excellent performance!")

    return recommendations


def _get_optimization_grade(avg_latency: float, p95_latency: float, compliance_10ms: float) -> str:
    """Get overall optimization grade based on multiple metrics."""

    # Weighted scoring
    avg_score = 100 if avg_latency < 5 else 80 if avg_latency < 10 else 60 if avg_latency < 25 else 40
    p95_score = 100 if p95_latency < 10 else 80 if p95_latency < 25 else 60 if p95_latency < 50 else 40
    compliance_score = compliance_10ms

    # Weighted average (compliance is most important)
    overall_score = (compliance_score * 0.5) + (avg_score * 0.3) + (p95_score * 0.2)

    if overall_score >= 95:
        return "A+ (Enterprise Excellence)"
    elif overall_score >= 90:
        return "A (Production Ready)"
    elif overall_score >= 80:
        return "B+ (Good Performance)"
    elif overall_score >= 70:
        return "B (Acceptable)"
    elif overall_score >= 60:
        return "C+ (Needs Optimization)"
    else:
        return "C- (Requires Immediate Attention)"


def _generate_optimization_recommendations(
    avg_latency: float, p95_latency: float, compliance_10ms: float, queue_status: Dict[str, int]
) -> List[str]:
    """Generate specific optimization recommendations."""
    recommendations = []

    if compliance_10ms < 95:
        recommendations.append(f"🎯 Target: Improve <10ms compliance from {compliance_10ms:.1f}% to 95%+")

    if avg_latency > 10:
        recommendations.append(f"⚡ Reduce average latency from {avg_latency:.1f}ms to <10ms")
        recommendations.append("🔧 Consider reducing micro-batch intervals further")

    if p95_latency > 25:
        recommendations.append(f"📊 Optimize P95 latency from {p95_latency:.1f}ms to <25ms")
        recommendations.append("🚀 Implement priority lane optimizations")

    total_queued = sum(queue_status.values()) if queue_status else 0
    if total_queued > 100:
        recommendations.append(f"📦 High queue depth ({total_queued} events) - increase processing capacity")

    if not recommendations:
        recommendations.append("🏆 Excellent performance! Consider further micro-optimizations for 99%+ compliance")

    return recommendations


def _get_next_optimization_phases(grade: str, compliance: float) -> List[str]:
    """Get next recommended optimization phases."""
    phases = []

    if compliance < 95:
        phases.append("Phase 1: Micro-batch interval reduction (10ms → 5ms)")
        phases.append("Phase 2: Enhanced priority lane processing")

    if "A" not in grade:
        phases.append("Phase 3: Connection-specific optimization")
        phases.append("Phase 4: Intelligent event aggregation tuning")

    if compliance >= 95:
        phases.append("Phase 5: Mobile performance optimization")
        phases.append("Phase 6: Enterprise scale testing (10k+ connections)")

    return phases


async def _run_performance_test(event_count: int):
    """Background task to run controlled performance test."""
    logger.info(f"🧪 Starting performance test with {event_count} events")

    publisher = get_optimized_event_publisher()

    from ghl_real_estate_ai.services.websocket_server import EventType, RealTimeEvent

    start_time = time.time()

    for i in range(event_count):
        # Create test event
        test_event = RealTimeEvent(
            event_type=EventType.PERFORMANCE_UPDATE,
            data={
                "test_sequence": i,
                "test_batch": event_count,
                "metric_name": "performance_test",
                "metric_value": i / event_count,
            },
            timestamp=datetime.now(timezone.utc),
            priority="normal" if i % 10 != 0 else "high",  # 10% high priority
        )

        # Publish test event
        await publisher.publish_event_optimized(test_event)

        # Small delay to simulate realistic event generation
        if i % 100 == 0:
            await asyncio.sleep(0.001)  # 1ms pause every 100 events

    duration = time.time() - start_time
    logger.info(
        f"✅ Performance test completed: {event_count} events in {duration:.2f}s ({event_count / duration:.0f} events/sec)"
    )


import time
from datetime import timezone
