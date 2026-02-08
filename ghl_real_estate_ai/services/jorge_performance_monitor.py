#!/usr/bin/env python3
"""
🎯 Jorge Bot Real-Time Performance Monitor
===========================================

Enterprise-grade performance monitoring and alerting for Jorge's specialized
real estate AI bots with industry-leading metrics tracking.

Monitoring Capabilities:
- Real-time conversation performance (<500ms target)
- Stall detection accuracy tracking (91.3% target)
- Lead re-engagement rate monitoring (78.5% target)
- Property matching accuracy (89.7% target)
- Memory and resource usage optimization
- Business impact metrics (close rates, revenue attribution)
- Jorge methodology adherence scoring

Performance Dashboards:
- Executive summary with key KPIs
- Real-time conversation monitoring
- Accuracy trend analysis
- Resource utilization tracking
- Alert management and escalation

Author: Claude Code Assistant - Jorge Performance Engineering
Date: 2026-01-25
Version: 1.0.0
"""

import asyncio
import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class JorgeMetricType(Enum):
    """Performance metrics specific to Jorge bots"""

    # Response Performance
    CONVERSATION_LATENCY = "conversation_latency"
    STALL_DETECTION_LATENCY = "stall_detection_latency"
    QUALIFICATION_LATENCY = "qualification_latency"

    # Accuracy Metrics
    STALL_DETECTION_ACCURACY = "stall_detection_accuracy"
    LEAD_REENGAGEMENT_RATE = "lead_reengagement_rate"
    PROPERTY_MATCHING_ACCURACY = "property_matching_accuracy"
    CLOSE_RATE_IMPROVEMENT = "close_rate_improvement"

    # Business Metrics
    QUALIFIED_LEADS_PER_HOUR = "qualified_leads_per_hour"
    CONVERSION_FUNNEL_EFFICIENCY = "conversion_funnel_efficiency"
    REVENUE_ATTRIBUTION_ACCURACY = "revenue_attribution_accuracy"

    # Quality Metrics
    JORGE_METHODOLOGY_ADHERENCE = "jorge_methodology_adherence"
    CONVERSATION_COHERENCE = "conversation_coherence"
    COMPLIANCE_SCORE = "compliance_score"
    CUSTOMER_SATISFACTION = "customer_satisfaction"

    # System Performance
    CONCURRENT_CONVERSATIONS = "concurrent_conversations"
    MEMORY_PER_CONVERSATION = "memory_per_conversation"
    CPU_UTILIZATION = "cpu_utilization"
    CACHE_HIT_RATE = "cache_hit_rate"


class AlertLevel(Enum):
    """Alert severity levels for Jorge performance"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BUSINESS_IMPACT = "business_impact"


@dataclass
class JorgePerformanceAlert:
    """Performance alert for Jorge bots"""

    alert_id: str
    alert_level: AlertLevel
    metric_type: JorgeMetricType
    current_value: float
    threshold_value: float
    message: str
    bot_type: str  # "seller", "lead", "buyer"
    conversation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class JorgePerformanceThresholds:
    """Performance thresholds for Jorge bot alerting"""

    # Response Time Thresholds (milliseconds)
    conversation_latency_warning: float = 300.0
    conversation_latency_critical: float = 500.0
    stall_detection_latency_warning: float = 150.0
    stall_detection_latency_critical: float = 250.0

    # Accuracy Thresholds
    stall_detection_accuracy_warning: float = 0.85
    stall_detection_accuracy_critical: float = 0.80
    lead_reengagement_rate_warning: float = 0.70
    lead_reengagement_rate_critical: float = 0.65
    property_matching_accuracy_warning: float = 0.85
    property_matching_accuracy_critical: float = 0.80

    # Business Impact Thresholds
    qualified_leads_per_hour_warning: float = 5.0
    qualified_leads_per_hour_critical: float = 3.0
    close_rate_improvement_warning: float = 0.60
    close_rate_improvement_critical: float = 0.50

    # System Performance Thresholds
    max_concurrent_conversations: int = 100
    memory_per_conversation_warning_mb: float = 40.0
    memory_per_conversation_critical_mb: float = 50.0
    cpu_utilization_warning: float = 70.0
    cpu_utilization_critical: float = 85.0


@dataclass
class ConversationMetrics:
    """Metrics for individual conversations"""

    conversation_id: str
    bot_type: str
    start_time: datetime
    total_turns: int = 0
    avg_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    stalls_detected: int = 0
    interventions_deployed: int = 0
    qualification_score: Optional[float] = None
    memory_usage_mb: float = 0.0
    completed: bool = False
    completion_time: Optional[datetime] = None


class JorgePerformanceMonitor:
    """Real-time performance monitoring for Jorge bots"""

    def __init__(self, thresholds: Optional[JorgePerformanceThresholds] = None):
        self.thresholds = thresholds or JorgePerformanceThresholds()

        # Metrics storage (thread-safe)
        self._lock = threading.RLock()
        self.metrics = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 measurements
        self.active_conversations = {}  # Active conversation tracking
        self.active_alerts = {}  # Current alerts
        self.alert_history = deque(maxlen=500)  # Alert history

        # Performance aggregates
        self.hourly_aggregates = defaultdict(lambda: defaultdict(list))
        self.daily_aggregates = defaultdict(lambda: defaultdict(list))

        # Callback handlers
        self.alert_handlers: List[Callable] = []
        self.metric_handlers: List[Callable] = []

        # Background monitoring
        self._monitoring_active = False
        self._monitoring_task = None

    async def start_monitoring(self):
        """Start background performance monitoring"""
        if self._monitoring_active:
            logger.warning("Performance monitoring already active")
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Jorge performance monitoring started")

    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Jorge performance monitoring stopped")

    def record_conversation_start(self, conversation_id: str, bot_type: str) -> None:
        """Record the start of a conversation"""
        with self._lock:
            self.active_conversations[conversation_id] = ConversationMetrics(
                conversation_id=conversation_id, bot_type=bot_type, start_time=datetime.now()
            )

    def record_conversation_turn(
        self,
        conversation_id: str,
        response_time_ms: float,
        stall_detected: bool = False,
        intervention_deployed: bool = False,
    ) -> None:
        """Record a conversation turn with performance metrics"""
        with self._lock:
            if conversation_id not in self.active_conversations:
                logger.warning(f"Recording turn for unknown conversation: {conversation_id}")
                return

            metrics = self.active_conversations[conversation_id]
            metrics.total_turns += 1

            # Update response time metrics
            if metrics.total_turns == 1:
                metrics.avg_response_time_ms = response_time_ms
            else:
                metrics.avg_response_time_ms = (
                    metrics.avg_response_time_ms * (metrics.total_turns - 1) + response_time_ms
                ) / metrics.total_turns

            metrics.max_response_time_ms = max(metrics.max_response_time_ms, response_time_ms)

            if stall_detected:
                metrics.stalls_detected += 1
            if intervention_deployed:
                metrics.interventions_deployed += 1

            # Record system-wide metrics
            self._record_metric(
                JorgeMetricType.CONVERSATION_LATENCY,
                response_time_ms,
                {"conversation_id": conversation_id, "bot_type": metrics.bot_type, "turn": metrics.total_turns},
            )

            # Check for performance alerts
            self._check_response_time_alerts(conversation_id, response_time_ms, metrics.bot_type)

    def record_stall_detection(self, conversation_id: str, detection_time_ms: float, accuracy_score: float) -> None:
        """Record stall detection performance"""
        with self._lock:
            # Record metrics
            self._record_metric(
                JorgeMetricType.STALL_DETECTION_LATENCY, detection_time_ms, {"conversation_id": conversation_id}
            )
            self._record_metric(
                JorgeMetricType.STALL_DETECTION_ACCURACY, accuracy_score, {"conversation_id": conversation_id}
            )

            # Check alerts
            if detection_time_ms > self.thresholds.stall_detection_latency_warning:
                self._create_alert(
                    AlertLevel.WARNING
                    if detection_time_ms < self.thresholds.stall_detection_latency_critical
                    else AlertLevel.CRITICAL,
                    JorgeMetricType.STALL_DETECTION_LATENCY,
                    detection_time_ms,
                    self.thresholds.stall_detection_latency_warning,
                    f"Stall detection latency high: {detection_time_ms:.1f}ms",
                    "seller",
                    conversation_id,
                )

    def record_lead_reengagement(self, success: bool, lead_type: str, days_since_contact: int) -> None:
        """Record lead re-engagement attempt and success"""
        with self._lock:
            # Calculate weighted success rate based on lead type and recency
            success_value = 1.0 if success else 0.0

            # Weight based on lead difficulty (cold leads success worth more)
            weight_multiplier = {"hot": 1.0, "warm": 1.2, "cold": 1.5}.get(lead_type, 1.0)

            weighted_success = success_value * weight_multiplier

            self._record_metric(
                JorgeMetricType.LEAD_REENGAGEMENT_RATE,
                weighted_success,
                {"lead_type": lead_type, "days_since_contact": days_since_contact, "success": success},
            )

    def record_property_match(
        self, match_accuracy: float, buyer_preferences: Dict[str, Any], property_features: Dict[str, Any]
    ) -> None:
        """Record property matching accuracy"""
        with self._lock:
            self._record_metric(
                JorgeMetricType.PROPERTY_MATCHING_ACCURACY,
                match_accuracy,
                {
                    "buyer_bedrooms": buyer_preferences.get("bedrooms"),
                    "buyer_budget": buyer_preferences.get("budget"),
                    "property_bedrooms": property_features.get("bedrooms"),
                    "property_price": property_features.get("price"),
                },
            )

    def record_qualification_completion(
        self, conversation_id: str, qualification_score: float, methodology_adherence_score: float
    ) -> None:
        """Record completion of lead qualification"""
        with self._lock:
            if conversation_id in self.active_conversations:
                metrics = self.active_conversations[conversation_id]
                metrics.qualification_score = qualification_score
                metrics.completed = True
                metrics.completion_time = datetime.now()

                # Calculate conversation duration
                duration = (metrics.completion_time - metrics.start_time).total_seconds()

                # Record business metrics
                self._record_metric(
                    JorgeMetricType.JORGE_METHODOLOGY_ADHERENCE,
                    methodology_adherence_score,
                    {"conversation_id": conversation_id, "bot_type": metrics.bot_type, "duration_seconds": duration},
                )

                # Move to completed conversations
                del self.active_conversations[conversation_id]

    def record_business_outcome(self, conversation_id: str, outcome_type: str, revenue_attributed: float = 0.0) -> None:
        """Record business outcome from conversation"""
        with self._lock:
            outcome_value = {
                "qualified": 1.0,
                "appointment_set": 2.0,
                "showing_booked": 3.0,
                "offer_made": 5.0,
                "deal_closed": 10.0,
            }.get(outcome_type, 0.0)

            self._record_metric(
                JorgeMetricType.CONVERSION_FUNNEL_EFFICIENCY,
                outcome_value,
                {
                    "conversation_id": conversation_id,
                    "outcome_type": outcome_type,
                    "revenue_attributed": revenue_attributed,
                },
            )

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time performance metrics"""
        with self._lock:
            current_time = datetime.now()

            # Calculate current performance
            metrics = {
                "timestamp": current_time.isoformat(),
                "active_conversations": len(self.active_conversations),
                "system_performance": self._calculate_system_performance(),
                "accuracy_metrics": self._calculate_accuracy_metrics(),
                "business_metrics": self._calculate_business_metrics(),
                "alert_summary": self._get_alert_summary(),
                "trend_analysis": self._calculate_trend_analysis(),
            }

            return metrics

    def get_conversation_performance(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a specific conversation"""
        with self._lock:
            if conversation_id not in self.active_conversations:
                return None

            metrics = self.active_conversations[conversation_id]
            return {
                "conversation_id": conversation_id,
                "bot_type": metrics.bot_type,
                "duration_seconds": (datetime.now() - metrics.start_time).total_seconds(),
                "total_turns": metrics.total_turns,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "max_response_time_ms": metrics.max_response_time_ms,
                "stalls_detected": metrics.stalls_detected,
                "interventions_deployed": metrics.interventions_deployed,
                "qualification_score": metrics.qualification_score,
                "memory_usage_mb": metrics.memory_usage_mb,
            }

    def get_performance_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            summary = {
                "time_period_hours": hours_back,
                "response_time_performance": self._summarize_response_times(cutoff_time),
                "accuracy_performance": self._summarize_accuracy_metrics(cutoff_time),
                "business_performance": self._summarize_business_metrics(cutoff_time),
                "system_performance": self._summarize_system_metrics(cutoff_time),
                "alert_summary": self._summarize_alerts(cutoff_time),
                "performance_score": self._calculate_overall_performance_score(cutoff_time),
            }

            return summary

    def add_alert_handler(self, handler: Callable[[JorgePerformanceAlert], None]) -> None:
        """Add alert handler callback"""
        self.alert_handlers.append(handler)

    def add_metric_handler(self, handler: Callable[[JorgeMetricType, float, Dict], None]) -> None:
        """Add metric recording handler callback"""
        self.metric_handlers.append(handler)

    # Private methods
    def _record_metric(self, metric_type: JorgeMetricType, value: float, context: Dict[str, Any]) -> None:
        """Record a metric value with context"""
        metric_entry = {"value": value, "timestamp": datetime.now(), "context": context}

        self.metrics[metric_type].append(metric_entry)

        # Trigger metric handlers
        for handler in self.metric_handlers:
            try:
                handler(metric_type, value, context)
            except Exception as e:
                logger.error(f"Error in metric handler: {e}")

    def _create_alert(
        self,
        level: AlertLevel,
        metric_type: JorgeMetricType,
        current_value: float,
        threshold_value: float,
        message: str,
        bot_type: str,
        conversation_id: Optional[str] = None,
    ) -> None:
        """Create and process a performance alert"""
        alert_id = f"{metric_type.value}_{int(time.time())}"

        alert = JorgePerformanceAlert(
            alert_id=alert_id,
            alert_level=level,
            metric_type=metric_type,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            bot_type=bot_type,
            conversation_id=conversation_id,
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        logger.warning(f"Jorge Performance Alert [{level.value}]: {message}")

        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def _check_response_time_alerts(self, conversation_id: str, response_time_ms: float, bot_type: str) -> None:
        """Check if response time triggers alerts"""
        if response_time_ms > self.thresholds.conversation_latency_warning:
            level = (
                AlertLevel.CRITICAL
                if response_time_ms > self.thresholds.conversation_latency_critical
                else AlertLevel.WARNING
            )

            self._create_alert(
                level,
                JorgeMetricType.CONVERSATION_LATENCY,
                response_time_ms,
                self.thresholds.conversation_latency_warning,
                f"Conversation response time high: {response_time_ms:.1f}ms",
                bot_type,
                conversation_id,
            )

    def _calculate_system_performance(self) -> Dict[str, Any]:
        """Calculate current system performance metrics"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = psutil.cpu_percent()

            return {
                "memory_usage_mb": memory_mb,
                "cpu_utilization_percent": cpu_percent,
                "active_conversations": len(self.active_conversations),
                "memory_per_conversation_mb": (
                    memory_mb / len(self.active_conversations) if self.active_conversations else 0
                ),
            }
        except Exception as e:
            logger.error(f"Error calculating system performance: {e}")
            return {}

    def _calculate_accuracy_metrics(self) -> Dict[str, Any]:
        """Calculate current accuracy metrics"""
        recent_cutoff = datetime.now() - timedelta(hours=1)

        # Get recent accuracy measurements
        stall_accuracy = self._get_recent_metric_average(JorgeMetricType.STALL_DETECTION_ACCURACY, recent_cutoff)
        reengagement_rate = self._get_recent_metric_average(JorgeMetricType.LEAD_REENGAGEMENT_RATE, recent_cutoff)
        matching_accuracy = self._get_recent_metric_average(JorgeMetricType.PROPERTY_MATCHING_ACCURACY, recent_cutoff)

        return {
            "stall_detection_accuracy": stall_accuracy,
            "lead_reengagement_rate": reengagement_rate,
            "property_matching_accuracy": matching_accuracy,
            "target_stall_detection": 0.913,
            "target_reengagement": 0.785,
            "target_matching": 0.897,
        }

    def _calculate_business_metrics(self) -> Dict[str, Any]:
        """Calculate current business performance metrics"""
        recent_cutoff = datetime.now() - timedelta(hours=1)

        qualified_leads = len(
            [
                m
                for m in self.metrics[JorgeMetricType.CONVERSION_FUNNEL_EFFICIENCY]
                if m["timestamp"] >= recent_cutoff and m["context"].get("outcome_type") == "qualified"
            ]
        )

        return {
            "qualified_leads_last_hour": qualified_leads,
            "conversion_efficiency": self._get_recent_metric_average(
                JorgeMetricType.CONVERSION_FUNNEL_EFFICIENCY, recent_cutoff
            ),
            "methodology_adherence": self._get_recent_metric_average(
                JorgeMetricType.JORGE_METHODOLOGY_ADHERENCE, recent_cutoff
            ),
        }

    def _get_recent_metric_average(self, metric_type: JorgeMetricType, cutoff_time: datetime) -> Optional[float]:
        """Get average value for a metric since cutoff time"""
        recent_metrics = [m["value"] for m in self.metrics[metric_type] if m["timestamp"] >= cutoff_time]

        return statistics.mean(recent_metrics) if recent_metrics else None

    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts"""
        active_alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]

        alert_counts = defaultdict(int)
        for alert in active_alerts:
            alert_counts[alert.alert_level.value] += 1

        return {
            "total_active_alerts": len(active_alerts),
            "critical_alerts": alert_counts["critical"],
            "warning_alerts": alert_counts["warning"],
            "info_alerts": alert_counts["info"],
            "business_impact_alerts": alert_counts["business_impact"],
        }

    def _calculate_trend_analysis(self) -> Dict[str, Any]:
        """Calculate performance trends"""
        hour_ago = datetime.now() - timedelta(hours=1)
        day_ago = datetime.now() - timedelta(days=1)

        response_time_trend = self._calculate_metric_trend(JorgeMetricType.CONVERSATION_LATENCY, hour_ago, day_ago)

        accuracy_trend = self._calculate_metric_trend(JorgeMetricType.STALL_DETECTION_ACCURACY, hour_ago, day_ago)

        return {
            "response_time_trend": response_time_trend,
            "accuracy_trend": accuracy_trend,
            "trend_direction": "improving" if response_time_trend < 0 and accuracy_trend > 0 else "declining",
        }

    def _calculate_metric_trend(
        self, metric_type: JorgeMetricType, recent_cutoff: datetime, baseline_cutoff: datetime
    ) -> float:
        """Calculate trend for a metric (positive = improving, negative = declining)"""
        recent_values = [m["value"] for m in self.metrics[metric_type] if recent_cutoff <= m["timestamp"]]

        baseline_values = [
            m["value"] for m in self.metrics[metric_type] if baseline_cutoff <= m["timestamp"] < recent_cutoff
        ]

        if not recent_values or not baseline_values:
            return 0.0

        recent_avg = statistics.mean(recent_values)
        baseline_avg = statistics.mean(baseline_values)

        # For response time metrics, lower is better (negative trend is improvement)
        # For accuracy metrics, higher is better (positive trend is improvement)
        if metric_type in [JorgeMetricType.CONVERSATION_LATENCY, JorgeMetricType.STALL_DETECTION_LATENCY]:
            return baseline_avg - recent_avg  # Lower recent = positive trend
        else:
            return recent_avg - baseline_avg  # Higher recent = positive trend

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                # Update system metrics
                system_metrics = self._calculate_system_performance()

                # Record system performance
                if system_metrics:
                    self._record_metric(
                        JorgeMetricType.CONCURRENT_CONVERSATIONS, system_metrics["active_conversations"], {}
                    )
                    self._record_metric(
                        JorgeMetricType.MEMORY_PER_CONVERSATION, system_metrics["memory_per_conversation_mb"], {}
                    )
                    self._record_metric(JorgeMetricType.CPU_UTILIZATION, system_metrics["cpu_utilization_percent"], {})

                # Check for system performance alerts
                if (
                    system_metrics.get("memory_per_conversation_mb", 0)
                    > self.thresholds.memory_per_conversation_warning_mb
                ):
                    self._create_alert(
                        AlertLevel.WARNING,
                        JorgeMetricType.MEMORY_PER_CONVERSATION,
                        system_metrics["memory_per_conversation_mb"],
                        self.thresholds.memory_per_conversation_warning_mb,
                        f"High memory usage per conversation: {system_metrics['memory_per_conversation_mb']:.1f}MB",
                        "system",
                    )

                # Clean up old metrics and alerts
                await self._cleanup_old_data()

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _cleanup_old_data(self):
        """Clean up old metrics and resolved alerts"""
        cutoff_time = datetime.now() - timedelta(days=7)  # Keep 7 days of data

        with self._lock:
            # Clean up old metrics (deque automatically limits size, but we can clean context)
            for metric_type in self.metrics:
                # Filter out very old entries
                self.metrics[metric_type] = deque(
                    [m for m in self.metrics[metric_type] if m["timestamp"] > cutoff_time], maxlen=1000
                )

            # Clean up resolved alerts older than 24 hours
            alert_cutoff = datetime.now() - timedelta(hours=24)
            resolved_alerts = [
                alert_id
                for alert_id, alert in self.active_alerts.items()
                if alert.resolved and alert.resolution_time and alert.resolution_time < alert_cutoff
            ]

            for alert_id in resolved_alerts:
                del self.active_alerts[alert_id]

    def _summarize_response_times(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Summarize response time performance"""
        response_times = [
            m["value"] for m in self.metrics[JorgeMetricType.CONVERSATION_LATENCY] if m["timestamp"] >= cutoff_time
        ]

        if not response_times:
            return {}

        return {
            "avg_response_time_ms": statistics.mean(response_times),
            "p50_response_time_ms": statistics.median(response_times),
            "p95_response_time_ms": np.percentile(response_times, 95),
            "p99_response_time_ms": np.percentile(response_times, 99),
            "max_response_time_ms": max(response_times),
            "total_requests": len(response_times),
            "target_met_percentage": (
                sum(1 for t in response_times if t < self.thresholds.conversation_latency_warning)
                / len(response_times)
                * 100
            ),
        }

    def _summarize_accuracy_metrics(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Summarize accuracy performance"""
        return {
            "stall_detection_accuracy": self._get_recent_metric_average(
                JorgeMetricType.STALL_DETECTION_ACCURACY, cutoff_time
            ),
            "reengagement_rate": self._get_recent_metric_average(JorgeMetricType.LEAD_REENGAGEMENT_RATE, cutoff_time),
            "property_matching_accuracy": self._get_recent_metric_average(
                JorgeMetricType.PROPERTY_MATCHING_ACCURACY, cutoff_time
            ),
            "methodology_adherence": self._get_recent_metric_average(
                JorgeMetricType.JORGE_METHODOLOGY_ADHERENCE, cutoff_time
            ),
        }

    def _summarize_business_metrics(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Summarize business performance"""
        conversions = [
            m for m in self.metrics[JorgeMetricType.CONVERSION_FUNNEL_EFFICIENCY] if m["timestamp"] >= cutoff_time
        ]

        qualified_leads = sum(1 for m in conversions if m["context"].get("outcome_type") == "qualified")

        closed_deals = sum(1 for m in conversions if m["context"].get("outcome_type") == "deal_closed")

        return {
            "qualified_leads": qualified_leads,
            "closed_deals": closed_deals,
            "conversion_rate": closed_deals / max(qualified_leads, 1),
            "total_revenue_attributed": sum(m["context"].get("revenue_attributed", 0) for m in conversions),
        }

    def _summarize_system_metrics(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Summarize system performance"""
        return {
            "avg_memory_per_conversation": self._get_recent_metric_average(
                JorgeMetricType.MEMORY_PER_CONVERSATION, cutoff_time
            ),
            "avg_cpu_utilization": self._get_recent_metric_average(JorgeMetricType.CPU_UTILIZATION, cutoff_time),
            "max_concurrent_conversations": max(
                (
                    m["value"]
                    for m in self.metrics[JorgeMetricType.CONCURRENT_CONVERSATIONS]
                    if m["timestamp"] >= cutoff_time
                ),
                default=0,
            ),
        }

    def _summarize_alerts(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Summarize alert activity"""
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]

        return {
            "total_alerts": len(recent_alerts),
            "critical_alerts": sum(1 for a in recent_alerts if a.alert_level == AlertLevel.CRITICAL),
            "warning_alerts": sum(1 for a in recent_alerts if a.alert_level == AlertLevel.WARNING),
            "avg_resolution_time_minutes": statistics.mean(
                [
                    (a.resolution_time - a.timestamp).total_seconds() / 60
                    for a in recent_alerts
                    if a.resolved and a.resolution_time
                ]
            )
            if any(a.resolved for a in recent_alerts)
            else None,
        }

    def _calculate_overall_performance_score(self, cutoff_time: datetime) -> float:
        """Calculate overall performance score (0-100)"""
        scores = []

        # Response time score (30% weight)
        response_times = [
            m["value"] for m in self.metrics[JorgeMetricType.CONVERSATION_LATENCY] if m["timestamp"] >= cutoff_time
        ]
        if response_times:
            avg_response = statistics.mean(response_times)
            response_score = max(0, min(100, 100 - (avg_response - 200) / 3))  # 200ms = 100%, 500ms = 0%
            scores.append((response_score, 0.30))

        # Accuracy score (40% weight)
        accuracy_metrics = [
            self._get_recent_metric_average(JorgeMetricType.STALL_DETECTION_ACCURACY, cutoff_time),
            self._get_recent_metric_average(JorgeMetricType.LEAD_REENGAGEMENT_RATE, cutoff_time),
            self._get_recent_metric_average(JorgeMetricType.PROPERTY_MATCHING_ACCURACY, cutoff_time),
        ]
        accuracy_metrics = [a for a in accuracy_metrics if a is not None]
        if accuracy_metrics:
            avg_accuracy = statistics.mean(accuracy_metrics)
            accuracy_score = avg_accuracy * 100
            scores.append((accuracy_score, 0.40))

        # System performance score (20% weight)
        memory_usage = self._get_recent_metric_average(JorgeMetricType.MEMORY_PER_CONVERSATION, cutoff_time)
        cpu_usage = self._get_recent_metric_average(JorgeMetricType.CPU_UTILIZATION, cutoff_time)
        if memory_usage and cpu_usage:
            memory_score = max(0, 100 - (memory_usage - 20) * 2)  # 20MB = 100%, 50MB = 40%
            cpu_score = max(0, 100 - (cpu_usage - 20))  # 20% = 100%, 70% = 50%
            system_score = (memory_score + cpu_score) / 2
            scores.append((system_score, 0.20))

        # Alert penalty (10% weight)
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
        alert_penalty = min(50, len(recent_alerts) * 5)  # Each alert reduces score
        alert_score = 100 - alert_penalty
        scores.append((alert_score, 0.10))

        # Calculate weighted average
        if scores:
            weighted_sum = sum(score * weight for score, weight in scores)
            total_weight = sum(weight for score, weight in scores)
            return weighted_sum / total_weight

        return 50.0  # Default neutral score


# Example usage and testing
if __name__ == "__main__":

    async def demo_jorge_monitoring():
        """Demonstration of Jorge performance monitoring"""

        # Create monitor
        monitor = JorgePerformanceMonitor()

        # Add alert handler
        def handle_alert(alert: JorgePerformanceAlert):
            print(f"🚨 ALERT [{alert.alert_level.value}]: {alert.message}")

        monitor.add_alert_handler(handle_alert)

        # Start monitoring
        await monitor.start_monitoring()

        print("🎯 Jorge Performance Monitor Demo")
        print("=" * 50)

        # Simulate conversation activity
        conversation_id = "demo_conversation_001"
        monitor.record_conversation_start(conversation_id, "seller")

        # Simulate conversation turns
        for turn in range(5):
            response_time = 150 + (turn * 50)  # Increasing response time
            stall_detected = turn == 3  # Stall detected on turn 3
            intervention = turn == 4  # Intervention on turn 4

            monitor.record_conversation_turn(conversation_id, response_time, stall_detected, intervention)

            print(f"Turn {turn + 1}: {response_time}ms response time")

            await asyncio.sleep(0.1)  # Small delay

        # Record stall detection
        monitor.record_stall_detection(conversation_id, 125.0, 0.92)

        # Record qualification completion
        monitor.record_qualification_completion(conversation_id, 8.5, 0.95)

        # Get real-time metrics
        metrics = monitor.get_real_time_metrics()
        print(f"\n📊 Real-time Metrics:")
        print(f"Active Conversations: {metrics['active_conversations']}")
        print(f"System Performance: {metrics['system_performance']}")
        print(f"Accuracy Metrics: {metrics['accuracy_metrics']}")

        # Get performance summary
        summary = monitor.get_performance_summary(1)  # Last hour
        print(f"\n📈 Performance Summary:")
        print(f"Performance Score: {summary['performance_score']:.1f}/100")
        print(f"Response Time Performance: {summary['response_time_performance']}")

        # Stop monitoring
        await monitor.stop_monitoring()
        print("\n✅ Demo completed")

    # Run demo
    asyncio.run(demo_jorge_monitoring())
