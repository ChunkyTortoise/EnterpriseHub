"""
Enhanced Workflow Performance Analytics

Advanced analytics on workflow, trigger, and automation performance with:
- Real-time performance monitoring
- Predictive analytics and insights
- Advanced segmentation and cohort analysis
- Revenue attribution and ROI tracking
- A/B test integration and optimization recommendations
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics for analysis"""

    EXECUTION = "execution"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    REVENUE = "revenue"
    PERFORMANCE = "performance"


class SegmentType(Enum):
    """Segmentation types for analysis"""

    LEAD_SOURCE = "lead_source"
    LEAD_SCORE = "lead_score"
    PROPERTY_TYPE = "property_type"
    BUDGET_RANGE = "budget_range"
    GEOGRAPHY = "geography"
    TIMELINE = "timeline"


@dataclass
class WorkflowMetrics:
    """Enhanced metrics for a single workflow"""

    workflow_id: str
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_completion_time_minutes: float = 0
    conversion_count: int = 0
    revenue_generated: float = 0
    time_period_days: int = 30

    # Enhanced metrics
    engagement_rate: float = 0.0
    drop_off_rate: float = 0.0
    cost_per_acquisition: float = 0.0
    lifetime_value: float = 0.0
    step_completion_rates: Dict[str, float] = field(default_factory=dict)
    segment_performance: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class ChannelMetrics:
    """Enhanced metrics for a communication channel"""

    channel_name: str
    messages_sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    responded: int = 0
    unsubscribed: int = 0
    cost: float = 0

    # Enhanced metrics
    peak_engagement_hours: List[int] = field(default_factory=list)
    sentiment_scores: List[float] = field(default_factory=list)
    response_time_minutes: List[float] = field(default_factory=list)
    conversion_attribution: float = 0.0


@dataclass
class PerformanceInsight:
    """Performance insight or recommendation"""

    insight_type: str
    title: str
    description: str
    impact_level: str  # "high", "medium", "low"
    recommendation: str
    expected_improvement: str
    data_supporting: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0


@dataclass
class CohortAnalysis:
    """Cohort analysis results"""

    cohort_name: str
    cohort_size: int
    time_periods: List[str]
    retention_rates: List[float]
    conversion_rates: List[float]
    revenue_per_cohort: List[float]
    avg_time_to_conversion: float = 0.0


class WorkflowAnalyticsService:
    """Enhanced service for workflow performance analytics"""

    def __init__(self, ab_testing_service=None, state_manager=None):
        # Core data stores
        self.workflow_executions: Dict[str, List[Dict]] = defaultdict(list)
        self.channel_stats: Dict[str, ChannelMetrics] = {}
        self.trigger_performance: Dict[str, Dict] = defaultdict(
            lambda: {"true_positives": 0, "false_positives": 0, "total_triggers": 0}
        )
        self.ab_test_results: List[Dict] = []

        # Enhanced data stores
        self.step_analytics: Dict[str, Dict] = defaultdict(dict)  # workflow_id -> step_id -> metrics
        self.lead_journey_data: Dict[str, List[Dict]] = defaultdict(list)  # lead_id -> journey steps
        self.revenue_attribution: Dict[str, Dict] = defaultdict(dict)  # workflow_id -> attribution data
        self.segment_analytics: Dict[str, Dict] = defaultdict(dict)  # segment -> metrics
        self.predictive_models: Dict[str, Any] = {}

        # External services
        self.ab_testing_service = ab_testing_service
        self.state_manager = state_manager

        # Cache for expensive calculations
        self._insights_cache: Dict[str, Tuple[datetime, List[PerformanceInsight]]] = {}
        self._cache_expiry = timedelta(hours=1)

    def track_workflow_execution(
        self,
        workflow_id: str,
        workflow_name: str,
        success: bool,
        completion_time_minutes: float,
        converted: bool = False,
        revenue: float = 0,
        lead_data: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None,
    ):
        """Track a workflow execution with enhanced data"""

        execution = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "success": success,
            "completion_time_minutes": completion_time_minutes,
            "converted": converted,
            "revenue": revenue,
            "lead_data": lead_data or {},
            "execution_context": execution_context or {},
        }

        self.workflow_executions[workflow_id].append(execution)

        # Track segmented analytics if lead data available
        if lead_data:
            self._update_segment_analytics(workflow_id, lead_data, execution)

        # Track revenue attribution
        if revenue > 0:
            self._update_revenue_attribution(workflow_id, revenue, execution)

    def track_step_execution(
        self,
        workflow_id: str,
        step_id: str,
        step_name: str,
        success: bool,
        execution_time_seconds: float,
        lead_id: str,
        engagement_data: Optional[Dict[str, Any]] = None,
    ):
        """Track individual step execution"""

        if workflow_id not in self.step_analytics:
            self.step_analytics[workflow_id] = {}

        if step_id not in self.step_analytics[workflow_id]:
            self.step_analytics[workflow_id][step_id] = {
                "step_name": step_name,
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0,
                "engagement_events": [],
                "drop_off_count": 0,
            }

        step_metrics = self.step_analytics[workflow_id][step_id]
        step_metrics["total_executions"] += 1
        step_metrics["total_execution_time"] += execution_time_seconds

        if success:
            step_metrics["successful_executions"] += 1
        else:
            step_metrics["failed_executions"] += 1

        # Track lead journey
        journey_step = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "step_id": step_id,
            "step_name": step_name,
            "success": success,
            "execution_time_seconds": execution_time_seconds,
            "engagement_data": engagement_data or {},
        }

        self.lead_journey_data[lead_id].append(journey_step)

    def _update_segment_analytics(self, workflow_id: str, lead_data: Dict[str, Any], execution: Dict[str, Any]):
        """Update analytics by lead segments"""

        segments = self._identify_lead_segments(lead_data)

        for segment_type, segment_value in segments.items():
            segment_key = f"{segment_type}:{segment_value}"

            if segment_key not in self.segment_analytics:
                self.segment_analytics[segment_key] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "conversions": 0,
                    "revenue": 0.0,
                    "avg_completion_time": 0.0,
                    "completion_times": [],
                }

            segment_data = self.segment_analytics[segment_key]
            segment_data["total_executions"] += 1

            if execution["success"]:
                segment_data["successful_executions"] += 1

            if execution["converted"]:
                segment_data["conversions"] += 1

            segment_data["revenue"] += execution["revenue"]
            segment_data["completion_times"].append(execution["completion_time_minutes"])
            segment_data["avg_completion_time"] = statistics.mean(segment_data["completion_times"])

    def _identify_lead_segments(self, lead_data: Dict[str, Any]) -> Dict[str, str]:
        """Identify lead segments from lead data"""

        segments = {}

        # Lead source segmentation
        if "source" in lead_data:
            segments["lead_source"] = lead_data["source"]

        # Lead score segmentation
        lead_score = lead_data.get("lead_score", 0)
        if lead_score >= 80:
            segments["lead_score"] = "hot"
        elif lead_score >= 60:
            segments["lead_score"] = "warm"
        elif lead_score >= 40:
            segments["lead_score"] = "cool"
        else:
            segments["lead_score"] = "cold"

        # Property type segmentation
        if "property_interest" in lead_data:
            segments["property_type"] = lead_data["property_interest"]

        # Budget segmentation
        budget_max = lead_data.get("budget_max", 0)
        if budget_max >= 1000000:
            segments["budget_range"] = "luxury"
        elif budget_max >= 500000:
            segments["budget_range"] = "premium"
        elif budget_max >= 300000:
            segments["budget_range"] = "mid_market"
        else:
            segments["budget_range"] = "entry_level"

        # Geographic segmentation
        if "location_preference" in lead_data:
            segments["geography"] = lead_data["location_preference"]

        # Timeline segmentation
        timeline = lead_data.get("timeline", "").lower()
        if "asap" in timeline or "immediate" in timeline:
            segments["timeline"] = "immediate"
        elif "month" in timeline or "30" in timeline:
            segments["timeline"] = "short_term"
        elif "quarter" in timeline or "90" in timeline:
            segments["timeline"] = "medium_term"
        else:
            segments["timeline"] = "long_term"

        return segments

    def _update_revenue_attribution(self, workflow_id: str, revenue: float, execution: Dict[str, Any]):
        """Update revenue attribution data"""

        if workflow_id not in self.revenue_attribution:
            self.revenue_attribution[workflow_id] = {
                "total_revenue": 0.0,
                "revenue_events": [],
                "avg_revenue_per_conversion": 0.0,
                "conversion_count": 0,
            }

        attribution_data = self.revenue_attribution[workflow_id]
        attribution_data["total_revenue"] += revenue
        attribution_data["conversion_count"] += 1
        attribution_data["revenue_events"].append(
            {
                "timestamp": execution["timestamp"],
                "revenue": revenue,
                "completion_time": execution["completion_time_minutes"],
            }
        )

        # Calculate average revenue per conversion
        attribution_data["avg_revenue_per_conversion"] = (
            attribution_data["total_revenue"] / attribution_data["conversion_count"]
        )

    def track_channel_activity(self, channel: str, activity_type: str, cost: float = 0):
        """Track channel activity"""

        if channel not in self.channel_stats:
            self.channel_stats[channel] = ChannelMetrics(channel_name=channel)

        metrics = self.channel_stats[channel]

        if activity_type == "sent":
            metrics.messages_sent += 1
            metrics.cost += cost
        elif activity_type == "delivered":
            metrics.delivered += 1
        elif activity_type == "opened":
            metrics.opened += 1
        elif activity_type == "clicked":
            metrics.clicked += 1
        elif activity_type == "responded":
            metrics.responded += 1
        elif activity_type == "unsubscribed":
            metrics.unsubscribed += 1

    def track_trigger_performance(self, trigger_id: str, correct_trigger: bool):
        """Track trigger accuracy"""

        stats = self.trigger_performance[trigger_id]
        stats["total_triggers"] += 1

        if correct_trigger:
            stats["true_positives"] += 1
        else:
            stats["false_positives"] += 1

    def get_workflow_metrics(self, workflow_id: str, days: int = 30) -> WorkflowMetrics:
        """Get metrics for a specific workflow"""

        executions = self.workflow_executions.get(workflow_id, [])

        # Filter by date range
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_executions = [e for e in executions if datetime.fromisoformat(e["timestamp"]) > cutoff]

        if not recent_executions:
            return WorkflowMetrics(workflow_id=workflow_id, workflow_name="Unknown", time_period_days=days)

        total = len(recent_executions)
        successful = len([e for e in recent_executions if e["success"]])
        failed = total - successful
        conversions = len([e for e in recent_executions if e.get("converted")])
        revenue = sum(e.get("revenue", 0) for e in recent_executions)
        avg_time = sum(e["completion_time_minutes"] for e in recent_executions) / total

        return WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_name=recent_executions[0]["workflow_name"],
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            avg_completion_time_minutes=avg_time,
            conversion_count=conversions,
            revenue_generated=revenue,
            time_period_days=days,
        )

    def get_top_performing_workflows(self, limit: int = 5) -> List[Dict]:
        """Get top performing workflows by conversion rate"""

        workflow_scores = []

        for workflow_id in self.workflow_executions.keys():
            metrics = self.get_workflow_metrics(workflow_id)

            if metrics.total_executions > 0:
                conversion_rate = metrics.conversion_count / metrics.total_executions
                success_rate = metrics.successful_executions / metrics.total_executions

                score = {
                    "workflow_id": workflow_id,
                    "workflow_name": metrics.workflow_name,
                    "conversion_rate": conversion_rate,
                    "success_rate": success_rate,
                    "revenue": metrics.revenue_generated,
                    "executions": metrics.total_executions,
                }
                workflow_scores.append(score)

        # Sort by conversion rate
        workflow_scores.sort(key=lambda x: x["conversion_rate"], reverse=True)
        return workflow_scores[:limit]

    def get_channel_performance(self) -> Dict[str, Dict]:
        """Get performance metrics for all channels"""

        performance = {}

        for channel, metrics in self.channel_stats.items():
            sent = metrics.messages_sent

            performance[channel] = {
                "messages_sent": sent,
                "delivery_rate": (f"{(metrics.delivered / sent * 100):.1f}%" if sent > 0 else "0%"),
                "open_rate": (f"{(metrics.opened / sent * 100):.1f}%" if sent > 0 else "0%"),
                "click_rate": (f"{(metrics.clicked / sent * 100):.1f}%" if sent > 0 else "0%"),
                "response_rate": (f"{(metrics.responded / sent * 100):.1f}%" if sent > 0 else "0%"),
                "unsubscribe_rate": (f"{(metrics.unsubscribed / sent * 100):.2f}%" if sent > 0 else "0%"),
                "cost": f"${metrics.cost:.2f}",
                "cost_per_response": (f"${(metrics.cost / metrics.responded):.2f}" if metrics.responded > 0 else "N/A"),
            }

        return performance

    def get_trigger_accuracy(self) -> Dict[str, Dict]:
        """Get accuracy metrics for triggers"""

        accuracy = {}

        for trigger_id, stats in self.trigger_performance.items():
            total = stats["total_triggers"]
            if total > 0:
                accuracy[trigger_id] = {
                    "total_triggers": total,
                    "accuracy": f"{(stats['true_positives'] / total * 100):.1f}%",
                    "false_positive_rate": f"{(stats['false_positives'] / total * 100):.1f}%",
                }

        return accuracy

    def calculate_roi(self, workflow_id: str, days: int = 30) -> Dict:
        """Calculate ROI for a workflow"""

        metrics = self.get_workflow_metrics(workflow_id, days)

        # Estimate costs (simplified)
        message_cost = metrics.total_executions * 0.01  # $0.01 per execution
        time_cost = (metrics.avg_completion_time_minutes / 60) * 50  # $50/hour
        total_cost = message_cost + time_cost

        revenue = metrics.revenue_generated
        roi = ((revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0

        return {
            "workflow_id": workflow_id,
            "workflow_name": metrics.workflow_name,
            "revenue": f"${revenue:,.2f}",
            "costs": f"${total_cost:,.2f}",
            "profit": f"${(revenue - total_cost):,.2f}",
            "roi": f"{roi:.1f}%",
            "time_period_days": days,
        }

    async def generate_performance_insights(
        self, workflow_id: Optional[str] = None, force_refresh: bool = False
    ) -> List[PerformanceInsight]:
        """Generate intelligent performance insights and recommendations"""

        # Check cache
        cache_key = workflow_id or "global"
        if not force_refresh and cache_key in self._insights_cache:
            cached_time, cached_insights = self._insights_cache[cache_key]
            if datetime.utcnow() - cached_time < self._cache_expiry:
                return cached_insights

        insights = []

        if workflow_id:
            # Workflow-specific insights
            insights.extend(await self._analyze_workflow_performance(workflow_id))
            insights.extend(await self._analyze_step_bottlenecks(workflow_id))
            insights.extend(await self._analyze_segment_performance(workflow_id))
        else:
            # Global insights
            insights.extend(await self._analyze_cross_workflow_performance())
            insights.extend(await self._analyze_channel_optimization())
            insights.extend(await self._analyze_timing_patterns())

        # Sort by impact and confidence
        insights.sort(key=lambda x: (x.impact_level == "high", x.confidence_score), reverse=True)

        # Cache results
        self._insights_cache[cache_key] = (datetime.utcnow(), insights[:10])  # Top 10 insights

        return insights[:10]

    async def _analyze_workflow_performance(self, workflow_id: str) -> List[PerformanceInsight]:
        """Analyze individual workflow performance"""

        insights = []
        metrics = self.get_workflow_metrics(workflow_id)

        if metrics.total_executions == 0:
            return insights

        # Low conversion rate insight
        conversion_rate = metrics.conversion_count / metrics.total_executions
        if conversion_rate < 0.1:  # Less than 10%
            insights.append(
                PerformanceInsight(
                    insight_type="performance",
                    title="Low Conversion Rate Detected",
                    description=f"Workflow '{metrics.workflow_name}' has a {conversion_rate:.1%} conversion rate",
                    impact_level="high",
                    recommendation="Review workflow messaging, timing, and targeting criteria",
                    expected_improvement="Potential 2-3x increase in conversions",
                    data_supporting={"current_rate": conversion_rate, "executions": metrics.total_executions},
                    confidence_score=0.9,
                )
            )

        # High completion time insight
        if metrics.avg_completion_time_minutes > 60:  # More than 1 hour
            insights.append(
                PerformanceInsight(
                    insight_type="efficiency",
                    title="Long Workflow Duration",
                    description=f"Average completion time is {metrics.avg_completion_time_minutes:.1f} minutes",
                    impact_level="medium",
                    recommendation="Consider reducing delays or splitting into shorter sequences",
                    expected_improvement="15-25% faster lead progression",
                    data_supporting={"avg_time": metrics.avg_completion_time_minutes},
                    confidence_score=0.8,
                )
            )

        # High failure rate insight
        failure_rate = metrics.failed_executions / metrics.total_executions
        if failure_rate > 0.2:  # More than 20% failures
            insights.append(
                PerformanceInsight(
                    insight_type="reliability",
                    title="High Failure Rate",
                    description=f"Workflow fails {failure_rate:.1%} of the time",
                    impact_level="high",
                    recommendation="Review error logs and add retry mechanisms for failed steps",
                    expected_improvement="Reduce failures by 50-70%",
                    data_supporting={"failure_rate": failure_rate, "failed_count": metrics.failed_executions},
                    confidence_score=0.95,
                )
            )

        return insights

    async def _analyze_step_bottlenecks(self, workflow_id: str) -> List[PerformanceInsight]:
        """Analyze step-level bottlenecks"""

        insights = []

        if workflow_id not in self.step_analytics:
            return insights

        steps = self.step_analytics[workflow_id]

        # Find steps with high failure rates
        for step_id, step_data in steps.items():
            if step_data["total_executions"] < 10:  # Skip steps with low volume
                continue

            failure_rate = step_data["failed_executions"] / step_data["total_executions"]
            if failure_rate > 0.3:  # More than 30% failure
                insights.append(
                    PerformanceInsight(
                        insight_type="bottleneck",
                        title=f"Step Bottleneck: {step_data['step_name']}",
                        description=f"Step '{step_data['step_name']}' fails {failure_rate:.1%} of the time",
                        impact_level="high",
                        recommendation="Review step configuration and add error handling",
                        expected_improvement="Improve overall workflow success rate by 10-20%",
                        data_supporting={
                            "step_id": step_id,
                            "failure_rate": failure_rate,
                            "executions": step_data["total_executions"],
                        },
                        confidence_score=0.85,
                    )
                )

        return insights

    async def _analyze_segment_performance(self, workflow_id: str) -> List[PerformanceInsight]:
        """Analyze performance by lead segments"""

        insights = []

        # Find segments with significantly different performance
        segment_performances = []

        for segment_key, segment_data in self.segment_analytics.items():
            if segment_data["total_executions"] < 5:  # Skip low-volume segments
                continue

            conversion_rate = segment_data["conversions"] / segment_data["total_executions"]
            revenue_per_lead = segment_data["revenue"] / segment_data["total_executions"]

            segment_performances.append(
                {
                    "segment": segment_key,
                    "conversion_rate": conversion_rate,
                    "revenue_per_lead": revenue_per_lead,
                    "total_executions": segment_data["total_executions"],
                }
            )

        if len(segment_performances) < 2:
            return insights

        # Sort by conversion rate
        segment_performances.sort(key=lambda x: x["conversion_rate"], reverse=True)

        best_segment = segment_performances[0]
        worst_segment = segment_performances[-1]

        # Significant performance gap
        if best_segment["conversion_rate"] > worst_segment["conversion_rate"] * 2:
            insights.append(
                PerformanceInsight(
                    insight_type="segmentation",
                    title="High-Performing Segment Identified",
                    description=f"Segment '{best_segment['segment']}' converts {best_segment['conversion_rate']:.1%} vs {worst_segment['conversion_rate']:.1%}",
                    impact_level="high",
                    recommendation=f"Focus more resources on '{best_segment['segment']}' segment characteristics",
                    expected_improvement="20-40% increase in overall conversion rates",
                    data_supporting={"best_segment": best_segment, "worst_segment": worst_segment},
                    confidence_score=0.8,
                )
            )

        return insights

    async def _analyze_cross_workflow_performance(self) -> List[PerformanceInsight]:
        """Analyze performance across all workflows"""

        insights = []

        # Get all workflow metrics
        workflow_performances = []
        for workflow_id in self.workflow_executions.keys():
            metrics = self.get_workflow_metrics(workflow_id)
            if metrics.total_executions > 0:
                workflow_performances.append(
                    {
                        "workflow_id": workflow_id,
                        "workflow_name": metrics.workflow_name,
                        "conversion_rate": metrics.conversion_count / metrics.total_executions,
                        "revenue_per_execution": metrics.revenue_generated / metrics.total_executions,
                        "success_rate": metrics.successful_executions / metrics.total_executions,
                    }
                )

        if len(workflow_performances) < 2:
            return insights

        # Find underperforming workflows
        avg_conversion = statistics.mean([w["conversion_rate"] for w in workflow_performances])
        underperformers = [w for w in workflow_performances if w["conversion_rate"] < avg_conversion * 0.5]

        for workflow in underperformers:
            insights.append(
                PerformanceInsight(
                    insight_type="optimization",
                    title=f"Underperforming Workflow: {workflow['workflow_name']}",
                    description=f"Conversion rate {workflow['conversion_rate']:.1%} is below average {avg_conversion:.1%}",
                    impact_level="medium",
                    recommendation="Review workflow design, messaging, and targeting",
                    expected_improvement="Align performance with top-performing workflows",
                    data_supporting={"workflow_performance": workflow, "average_conversion": avg_conversion},
                    confidence_score=0.7,
                )
            )

        return insights

    async def _analyze_channel_optimization(self) -> List[PerformanceInsight]:
        """Analyze channel performance for optimization"""

        insights = []

        channel_performances = []
        for channel, metrics in self.channel_stats.items():
            if metrics.messages_sent > 0:
                response_rate = metrics.responded / metrics.messages_sent
                cost_per_response = metrics.cost / metrics.responded if metrics.responded > 0 else float("inf")

                channel_performances.append(
                    {
                        "channel": channel,
                        "response_rate": response_rate,
                        "cost_per_response": cost_per_response,
                        "total_sent": metrics.messages_sent,
                    }
                )

        if len(channel_performances) < 2:
            return insights

        # Find most and least efficient channels
        channel_performances.sort(key=lambda x: x["response_rate"], reverse=True)
        best_channel = channel_performances[0]
        worst_channel = channel_performances[-1]

        if best_channel["response_rate"] > worst_channel["response_rate"] * 2:
            insights.append(
                PerformanceInsight(
                    insight_type="channel_optimization",
                    title=f"Channel Performance Gap",
                    description=f"{best_channel['channel']} outperforms {worst_channel['channel']} significantly",
                    impact_level="medium",
                    recommendation=f"Shift budget from {worst_channel['channel']} to {best_channel['channel']}",
                    expected_improvement="10-30% improvement in overall response rates",
                    data_supporting={"best_channel": best_channel, "worst_channel": worst_channel},
                    confidence_score=0.75,
                )
            )

        return insights

    async def _analyze_timing_patterns(self) -> List[PerformanceInsight]:
        """Analyze timing patterns for optimization"""

        insights = []

        # Analyze execution times across workflows
        all_completion_times = []
        for workflow_executions in self.workflow_executions.values():
            times = [e["completion_time_minutes"] for e in workflow_executions if e["success"]]
            all_completion_times.extend(times)

        if len(all_completion_times) < 10:
            return insights

        avg_time = statistics.mean(all_completion_times)
        median_time = statistics.median(all_completion_times)

        # If average is much higher than median, there are some very slow executions
        if avg_time > median_time * 1.5:
            insights.append(
                PerformanceInsight(
                    insight_type="timing",
                    title="Inconsistent Workflow Timing",
                    description=f"Average time ({avg_time:.1f}min) significantly higher than median ({median_time:.1f}min)",
                    impact_level="medium",
                    recommendation="Investigate and optimize slow-running workflow instances",
                    expected_improvement="More consistent lead experience and faster conversions",
                    data_supporting={
                        "avg_time": avg_time,
                        "median_time": median_time,
                        "sample_size": len(all_completion_times),
                    },
                    confidence_score=0.6,
                )
            )

        return insights

    def get_cohort_analysis(self, cohort_definition: str = "monthly", period_count: int = 6) -> List[CohortAnalysis]:
        """Perform cohort analysis on leads"""

        cohorts = []

        # Group leads by cohort (simplified - by month for demo)
        lead_cohorts = defaultdict(list)

        for lead_id, journey in self.lead_journey_data.items():
            if not journey:
                continue

            first_step = journey[0]
            cohort_month = datetime.fromisoformat(first_step["timestamp"]).strftime("%Y-%m")
            lead_cohorts[cohort_month].append(lead_id)

        # Analyze each cohort
        for cohort_name, lead_ids in lead_cohorts.items():
            if len(lead_ids) < 5:  # Skip small cohorts
                continue

            cohort_analysis = self._analyze_cohort(cohort_name, lead_ids, period_count)
            if cohort_analysis:
                cohorts.append(cohort_analysis)

        return sorted(cohorts, key=lambda x: x.cohort_name, reverse=True)

    def _analyze_cohort(self, cohort_name: str, lead_ids: List[str], period_count: int) -> Optional[CohortAnalysis]:
        """Analyze individual cohort"""

        cohort_start = datetime.strptime(cohort_name, "%Y-%m")
        periods = []
        retention_rates = []
        conversion_rates = []
        revenue_per_cohort = []

        for i in range(period_count):
            period_start = cohort_start + timedelta(days=30 * i)
            period_end = period_start + timedelta(days=30)
            period_name = f"Month {i + 1}"

            # Count active leads in this period
            active_leads = 0
            converted_leads = 0
            period_revenue = 0.0

            for lead_id in lead_ids:
                lead_journey = self.lead_journey_data.get(lead_id, [])

                # Check if lead was active in this period
                period_activity = [
                    step
                    for step in lead_journey
                    if period_start <= datetime.fromisoformat(step["timestamp"]) < period_end
                ]

                if period_activity:
                    active_leads += 1

                    # Check for conversions
                    conversions = [
                        step for step in period_activity if step.get("engagement_data", {}).get("converted", False)
                    ]

                    if conversions:
                        converted_leads += 1
                        # Add revenue logic here

            periods.append(period_name)
            retention_rates.append(active_leads / len(lead_ids))
            conversion_rates.append(converted_leads / len(lead_ids))
            revenue_per_cohort.append(period_revenue)

        return CohortAnalysis(
            cohort_name=cohort_name,
            cohort_size=len(lead_ids),
            time_periods=periods,
            retention_rates=retention_rates,
            conversion_rates=conversion_rates,
            revenue_per_cohort=revenue_per_cohort,
        )

    def get_predictive_insights(self, workflow_id: str) -> Dict[str, Any]:
        """Generate predictive insights using simple heuristics"""

        metrics = self.get_workflow_metrics(workflow_id)

        if metrics.total_executions < 20:
            return {"error": "Insufficient data for predictions"}

        # Simple trend analysis
        recent_executions = self.workflow_executions.get(workflow_id, [])[-10:]
        older_executions = self.workflow_executions.get(workflow_id, [])[-20:-10]

        if not recent_executions or not older_executions:
            return {"error": "Insufficient historical data"}

        recent_conversion_rate = len([e for e in recent_executions if e["converted"]]) / len(recent_executions)
        older_conversion_rate = len([e for e in older_executions if e["converted"]]) / len(older_executions)

        trend = "improving" if recent_conversion_rate > older_conversion_rate else "declining"
        change_percentage = abs(recent_conversion_rate - older_conversion_rate) / older_conversion_rate * 100

        return {
            "trend": trend,
            "trend_strength": "strong" if change_percentage > 20 else "moderate" if change_percentage > 10 else "weak",
            "recent_conversion_rate": recent_conversion_rate,
            "historical_conversion_rate": older_conversion_rate,
            "predicted_next_period": recent_conversion_rate * 1.1
            if trend == "improving"
            else recent_conversion_rate * 0.9,
            "confidence": "low",  # Simple heuristic model has low confidence
        }

    def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's metrics
        today_executions = []
        for workflow_executions in self.workflow_executions.values():
            today_executions.extend(
                [e for e in workflow_executions if datetime.fromisoformat(e["timestamp"]) >= today_start]
            )

        total_today = len(today_executions)
        successful_today = len([e for e in today_executions if e["success"]])
        conversions_today = len([e for e in today_executions if e["converted"]])
        revenue_today = sum(e["revenue"] for e in today_executions)

        # Channel activity today
        channel_activity = {}
        for channel, metrics in self.channel_stats.items():
            # This would need timestamp tracking in real implementation
            channel_activity[channel] = {
                "messages_sent": metrics.messages_sent,  # This should be filtered by today
                "response_rate": f"{(metrics.responded / metrics.messages_sent * 100):.1f}%"
                if metrics.messages_sent > 0
                else "0%",
            }

        # Recent insights
        for workflow_id in list(self.workflow_executions.keys())[:3]:  # Top 3 workflows
            asyncio.create_task(self.generate_performance_insights(workflow_id))
            # In real implementation, this would be handled differently for async

        return {
            "today_metrics": {
                "total_executions": total_today,
                "successful_executions": successful_today,
                "success_rate": f"{(successful_today / total_today * 100):.1f}%" if total_today > 0 else "0%",
                "conversions": conversions_today,
                "conversion_rate": f"{(conversions_today / total_today * 100):.1f}%" if total_today > 0 else "0%",
                "revenue": f"${revenue_today:,.2f}",
            },
            "channel_activity": channel_activity,
            "top_workflows": self.get_top_performing_workflows(3),
            "alert_count": len([i for i in self._get_cached_insights() if i.impact_level == "high"]),
        }

    def _get_cached_insights(self) -> List[PerformanceInsight]:
        """Get cached insights for quick access"""
        insights = []
        for cached_insights in self._insights_cache.values():
            insights.extend(cached_insights[1])
        return insights

    def export_analytics_report(
        self, workflow_id: Optional[str] = None, include_insights: bool = True, include_segments: bool = True
    ) -> Dict[str, Any]:
        """Export comprehensive analytics report"""

        if workflow_id:
            # Workflow-specific report
            metrics = self.get_workflow_metrics(workflow_id)
            report = {
                "report_type": "workflow_specific",
                "workflow_id": workflow_id,
                "workflow_name": metrics.workflow_name,
                "metrics": asdict(metrics),
                "roi_analysis": self.calculate_roi(workflow_id),
                "generated_at": datetime.utcnow().isoformat(),
            }

            if include_insights:
                # This would need to be handled with proper async in real implementation
                report["insights"] = []  # Placeholder

            if include_segments:
                workflow_segments = {
                    k: v
                    for k, v in self.segment_analytics.items()
                    # Filter for relevant segments
                }
                report["segment_analysis"] = workflow_segments

        else:
            # Global report
            report = {
                "report_type": "global",
                "summary": {
                    "total_workflows": len(self.workflow_executions),
                    "total_executions": sum(len(execs) for execs in self.workflow_executions.values()),
                    "active_channels": len(self.channel_stats),
                },
                "top_performers": self.get_top_performing_workflows(),
                "channel_performance": self.get_channel_performance(),
                "trigger_accuracy": self.get_trigger_accuracy(),
                "generated_at": datetime.utcnow().isoformat(),
            }

        return report


def demo_workflow_analytics():
    """Demonstrate workflow analytics"""
    service = WorkflowAnalyticsService()

    print("📊 Workflow Performance Analytics Demo\n")

    # Simulate some workflow executions
    for i in range(10):
        service.track_workflow_execution(
            workflow_id="wf_001",
            workflow_name="Welcome Sequence",
            success=True,
            completion_time_minutes=15.5,
            converted=(i % 3 == 0),
            revenue=5000 if (i % 3 == 0) else 0,
        )

    # Track channel activity
    for _ in range(20):
        service.track_channel_activity("sms", "sent", cost=0.01)
        service.track_channel_activity("sms", "delivered")

    for _ in range(15):
        service.track_channel_activity("sms", "responded")

    # Get metrics
    metrics = service.get_workflow_metrics("wf_001")
    print(f"📈 Workflow Metrics (Welcome Sequence):")
    print(f"   Total executions: {metrics.total_executions}")
    print(f"   Success rate: {(metrics.successful_executions / metrics.total_executions * 100):.1f}%")
    print(f"   Conversions: {metrics.conversion_count}")
    print(f"   Revenue: ${metrics.revenue_generated:,.2f}")

    # Channel performance
    print(f"\n📱 Channel Performance:")
    channel_perf = service.get_channel_performance()
    for channel, stats in channel_perf.items():
        print(f"   {channel.upper()}:")
        print(f"      Response rate: {stats['response_rate']}")
        print(f"      Cost per response: {stats['cost_per_response']}")

    # ROI
    roi = service.calculate_roi("wf_001")
    print(f"\n💰 ROI Analysis:")
    print(f"   Revenue: {roi['revenue']}")
    print(f"   ROI: {roi['roi']}")


if __name__ == "__main__":
    demo_workflow_analytics()
