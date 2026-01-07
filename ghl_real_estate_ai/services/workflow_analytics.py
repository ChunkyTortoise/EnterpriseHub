"""
Workflow Performance Analytics
Deep analytics on workflow, trigger, and automation performance

Feature 13: Workflow Performance Analytics
Track, measure, and optimize all automation workflows.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow"""

    workflow_id: str
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_completion_time_minutes: float = 0
    conversion_count: int = 0
    revenue_generated: float = 0
    time_period_days: int = 30


@dataclass
class ChannelMetrics:
    """Metrics for a communication channel"""

    channel_name: str
    messages_sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    responded: int = 0
    unsubscribed: int = 0
    cost: float = 0


class WorkflowAnalyticsService:
    """Service for workflow performance analytics"""

    def __init__(self):
        self.workflow_executions: Dict[str, List[Dict]] = defaultdict(list)
        self.channel_stats: Dict[str, ChannelMetrics] = {}
        self.trigger_performance: Dict[str, Dict] = defaultdict(
            lambda: {"true_positives": 0, "false_positives": 0, "total_triggers": 0}
        )
        self.ab_test_results: List[Dict] = []

    def track_workflow_execution(
        self,
        workflow_id: str,
        workflow_name: str,
        success: bool,
        completion_time_minutes: float,
        converted: bool = False,
        revenue: float = 0,
    ):
        """Track a workflow execution"""

        execution = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "success": success,
            "completion_time_minutes": completion_time_minutes,
            "converted": converted,
            "revenue": revenue,
        }

        self.workflow_executions[workflow_id].append(execution)

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
        recent_executions = [
            e for e in executions if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        if not recent_executions:
            return WorkflowMetrics(
                workflow_id=workflow_id, workflow_name="Unknown", time_period_days=days
            )

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
                "delivery_rate": (
                    f"{(metrics.delivered / sent * 100):.1f}%" if sent > 0 else "0%"
                ),
                "open_rate": (
                    f"{(metrics.opened / sent * 100):.1f}%" if sent > 0 else "0%"
                ),
                "click_rate": (
                    f"{(metrics.clicked / sent * 100):.1f}%" if sent > 0 else "0%"
                ),
                "response_rate": (
                    f"{(metrics.responded / sent * 100):.1f}%" if sent > 0 else "0%"
                ),
                "unsubscribe_rate": (
                    f"{(metrics.unsubscribed / sent * 100):.2f}%" if sent > 0 else "0%"
                ),
                "cost": f"${metrics.cost:.2f}",
                "cost_per_response": (
                    f"${(metrics.cost / metrics.responded):.2f}"
                    if metrics.responded > 0
                    else "N/A"
                ),
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
    print(
        f"   Success rate: {(metrics.successful_executions/metrics.total_executions*100):.1f}%"
    )
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
