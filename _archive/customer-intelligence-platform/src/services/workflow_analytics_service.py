"""
Advanced Workflow Analytics Service

Provides comprehensive analytics, performance monitoring, and optimization
for the enhanced workflow automation system.

Features:
- Real-time workflow performance tracking
- A/B testing for workflow variants
- Conversion funnel analysis
- ROI and effectiveness metrics
- Predictive workflow optimization
- Anomaly detection in workflow performance
- Customer journey analytics
- Industry benchmarking
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np
from statistics import mean, median
import logging

from .enhanced_workflow_engine import (
    EnhancedWorkflowAction, WorkflowPriority, ActionType, 
    WorkflowStage, IndustryVertical, TriggerCondition
)
from ..core.event_bus import EventBus, EventType
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of workflow metrics."""
    CONVERSION_RATE = "conversion_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    RESPONSE_TIME = "response_time"
    ACTION_SUCCESS_RATE = "action_success_rate"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    ROI = "return_on_investment"
    CHURN_REDUCTION = "churn_reduction"
    REVENUE_ATTRIBUTION = "revenue_attribution"
    WORKFLOW_COMPLETION = "workflow_completion"
    TRIGGER_ACCURACY = "trigger_accuracy"


class TimeWindow(Enum):
    """Time windows for analytics."""
    REAL_TIME = "real_time"  # Last hour
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class WorkflowMetric:
    """Individual workflow metric data point."""
    metric_id: str
    workflow_id: str
    customer_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]
    industry: Optional[IndustryVertical] = None
    stage: Optional[WorkflowStage] = None
    action_type: Optional[ActionType] = None


@dataclass
class WorkflowPerformanceReport:
    """Comprehensive workflow performance report."""
    report_id: str
    time_window: TimeWindow
    start_time: datetime
    end_time: datetime
    
    # Overall metrics
    total_workflows: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    
    # Performance metrics
    average_completion_time: float
    success_rate: float
    conversion_rate: float
    customer_satisfaction: float
    
    # Financial metrics
    total_revenue_attributed: float
    roi_percentage: float
    cost_per_conversion: float
    
    # Detailed breakdowns
    metrics_by_stage: Dict[str, Dict[str, float]]
    metrics_by_industry: Dict[str, Dict[str, float]]
    metrics_by_action_type: Dict[str, Dict[str, float]]
    
    # Trends and insights
    trends: Dict[str, List[float]]
    insights: List[str]
    recommendations: List[str]


@dataclass
class ABTestResult:
    """A/B test results for workflow optimization."""
    test_id: str
    test_name: str
    start_date: datetime
    end_date: Optional[datetime]
    status: str  # "running", "completed", "paused"
    
    # Test configuration
    control_variant: str
    test_variants: List[str]
    traffic_allocation: Dict[str, float]
    
    # Results
    sample_sizes: Dict[str, int]
    conversion_rates: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    statistical_significance: Optional[float]
    winner: Optional[str]
    
    # Business impact
    revenue_impact: Dict[str, float]
    customer_impact: Dict[str, int]
    recommendations: List[str]


class WorkflowAnalyticsCollector:
    """Collects and processes workflow analytics data."""
    
    def __init__(self):
        self.metrics_buffer: List[WorkflowMetric] = []
        self.buffer_size = 1000
        self.flush_interval = 300  # 5 minutes
        
        # In-memory storage for real-time analytics
        self.recent_metrics: Dict[str, List[WorkflowMetric]] = defaultdict(list)
        self.retention_hours = 24
        
    async def record_metric(
        self,
        workflow_id: str,
        customer_id: str,
        metric_type: MetricType,
        value: float,
        metadata: Dict[str, Any] = None,
        industry: Optional[IndustryVertical] = None,
        stage: Optional[WorkflowStage] = None,
        action_type: Optional[ActionType] = None
    ) -> None:
        """Record a workflow metric."""
        
        metric = WorkflowMetric(
            metric_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            customer_id=customer_id,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            industry=industry,
            stage=stage,
            action_type=action_type
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Add to recent metrics for real-time analytics
        key = f"{metric_type.value}_{workflow_id}"
        self.recent_metrics[key].append(metric)
        
        # Maintain retention window
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        self.recent_metrics[key] = [
            m for m in self.recent_metrics[key]
            if m.timestamp > cutoff_time
        ]
        
        # Flush buffer if needed
        if len(self.metrics_buffer) >= self.buffer_size:
            await self._flush_metrics_buffer()
        
        logger.debug(
            f"Recorded workflow metric: {metric_type.value} = {value}",
            extra={
                "workflow_id": workflow_id,
                "customer_id": customer_id,
                "metric_type": metric_type.value
            }
        )
    
    async def _flush_metrics_buffer(self) -> None:
        """Flush metrics buffer to persistent storage."""
        if not self.metrics_buffer:
            return
        
        # In a real implementation, this would write to a time-series database
        # For now, we'll just log the flush
        logger.info(f"Flushing {len(self.metrics_buffer)} workflow metrics to storage")
        
        # Clear buffer
        self.metrics_buffer.clear()
    
    def get_recent_metrics(
        self,
        metric_type: MetricType,
        workflow_id: Optional[str] = None,
        time_window_hours: int = 1
    ) -> List[WorkflowMetric]:
        """Get recent metrics for analysis."""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        if workflow_id:
            key = f"{metric_type.value}_{workflow_id}"
            metrics = self.recent_metrics.get(key, [])
        else:
            # Get all metrics of this type
            metrics = []
            for key, metric_list in self.recent_metrics.items():
                if key.startswith(f"{metric_type.value}_"):
                    metrics.extend(metric_list)
        
        # Filter by time window
        return [m for m in metrics if m.timestamp > cutoff_time]


class WorkflowPerformanceAnalyzer:
    """Analyzes workflow performance and generates insights."""
    
    def __init__(self, collector: WorkflowAnalyticsCollector):
        self.collector = collector
        
        # Performance thresholds
        self.thresholds = {
            MetricType.CONVERSION_RATE: 0.15,  # 15% minimum
            MetricType.SUCCESS_RATE: 0.85,     # 85% minimum
            MetricType.RESPONSE_TIME: 1800,    # 30 minutes maximum
            MetricType.CUSTOMER_SATISFACTION: 7.0,  # 7/10 minimum
            MetricType.ROI: 2.0                # 200% minimum
        }
    
    async def generate_performance_report(
        self,
        time_window: TimeWindow,
        industry: Optional[IndustryVertical] = None
    ) -> WorkflowPerformanceReport:
        """Generate comprehensive performance report."""
        
        # Calculate time range
        end_time = datetime.utcnow()
        
        if time_window == TimeWindow.HOURLY:
            start_time = end_time - timedelta(hours=1)
        elif time_window == TimeWindow.DAILY:
            start_time = end_time - timedelta(days=1)
        elif time_window == TimeWindow.WEEKLY:
            start_time = end_time - timedelta(weeks=1)
        elif time_window == TimeWindow.MONTHLY:
            start_time = end_time - timedelta(days=30)
        elif time_window == TimeWindow.QUARTERLY:
            start_time = end_time - timedelta(days=90)
        else:  # REAL_TIME
            start_time = end_time - timedelta(hours=1)
        
        # Collect metrics for time window
        all_metrics = []
        for metric_type in MetricType:
            metrics = self.collector.get_recent_metrics(
                metric_type,
                time_window_hours=int((end_time - start_time).total_seconds() / 3600)
            )
            all_metrics.extend(metrics)
        
        # Filter by industry if specified
        if industry:
            all_metrics = [m for m in all_metrics if m.industry == industry]
        
        # Calculate overall metrics
        workflow_ids = set(m.workflow_id for m in all_metrics)
        total_workflows = len(workflow_ids)
        
        # Calculate success rate
        success_metrics = [m for m in all_metrics if m.metric_type == MetricType.ACTION_SUCCESS_RATE]
        success_rate = mean([m.value for m in success_metrics]) if success_metrics else 0.0
        
        # Calculate conversion rate
        conversion_metrics = [m for m in all_metrics if m.metric_type == MetricType.CONVERSION_RATE]
        conversion_rate = mean([m.value for m in conversion_metrics]) if conversion_metrics else 0.0
        
        # Calculate customer satisfaction
        satisfaction_metrics = [m for m in all_metrics if m.metric_type == MetricType.CUSTOMER_SATISFACTION]
        customer_satisfaction = mean([m.value for m in satisfaction_metrics]) if satisfaction_metrics else 0.0
        
        # Calculate financial metrics
        revenue_metrics = [m for m in all_metrics if m.metric_type == MetricType.REVENUE_ATTRIBUTION]
        total_revenue_attributed = sum([m.value for m in revenue_metrics])
        
        roi_metrics = [m for m in all_metrics if m.metric_type == MetricType.ROI]
        roi_percentage = mean([m.value for m in roi_metrics]) if roi_metrics else 0.0
        
        # Calculate breakdowns
        metrics_by_stage = self._calculate_stage_breakdown(all_metrics)
        metrics_by_industry = self._calculate_industry_breakdown(all_metrics)
        metrics_by_action_type = self._calculate_action_type_breakdown(all_metrics)
        
        # Generate trends
        trends = await self._calculate_trends(all_metrics, time_window)
        
        # Generate insights and recommendations
        insights = self._generate_insights(all_metrics)
        recommendations = self._generate_recommendations(all_metrics)
        
        return WorkflowPerformanceReport(
            report_id=str(uuid.uuid4()),
            time_window=time_window,
            start_time=start_time,
            end_time=end_time,
            total_workflows=total_workflows,
            active_workflows=total_workflows,  # Simplified
            completed_workflows=int(total_workflows * success_rate),
            failed_workflows=int(total_workflows * (1 - success_rate)),
            average_completion_time=1800.0,  # Placeholder
            success_rate=success_rate,
            conversion_rate=conversion_rate,
            customer_satisfaction=customer_satisfaction,
            total_revenue_attributed=total_revenue_attributed,
            roi_percentage=roi_percentage,
            cost_per_conversion=100.0,  # Placeholder
            metrics_by_stage=metrics_by_stage,
            metrics_by_industry=metrics_by_industry,
            metrics_by_action_type=metrics_by_action_type,
            trends=trends,
            insights=insights,
            recommendations=recommendations
        )
    
    def _calculate_stage_breakdown(self, metrics: List[WorkflowMetric]) -> Dict[str, Dict[str, float]]:
        """Calculate metrics breakdown by workflow stage."""
        breakdown = defaultdict(lambda: defaultdict(list))
        
        for metric in metrics:
            if metric.stage:
                breakdown[metric.stage.value][metric.metric_type.value].append(metric.value)
        
        # Calculate averages
        result = {}
        for stage, stage_metrics in breakdown.items():
            result[stage] = {}
            for metric_type, values in stage_metrics.items():
                result[stage][metric_type] = mean(values) if values else 0.0
        
        return result
    
    def _calculate_industry_breakdown(self, metrics: List[WorkflowMetric]) -> Dict[str, Dict[str, float]]:
        """Calculate metrics breakdown by industry."""
        breakdown = defaultdict(lambda: defaultdict(list))
        
        for metric in metrics:
            if metric.industry:
                breakdown[metric.industry.value][metric.metric_type.value].append(metric.value)
        
        # Calculate averages
        result = {}
        for industry, industry_metrics in breakdown.items():
            result[industry] = {}
            for metric_type, values in industry_metrics.items():
                result[industry][metric_type] = mean(values) if values else 0.0
        
        return result
    
    def _calculate_action_type_breakdown(self, metrics: List[WorkflowMetric]) -> Dict[str, Dict[str, float]]:
        """Calculate metrics breakdown by action type."""
        breakdown = defaultdict(lambda: defaultdict(list))
        
        for metric in metrics:
            if metric.action_type:
                breakdown[metric.action_type.value][metric.metric_type.value].append(metric.value)
        
        # Calculate averages
        result = {}
        for action_type, action_metrics in breakdown.items():
            result[action_type] = {}
            for metric_type, values in action_metrics.items():
                result[action_type][metric_type] = mean(values) if values else 0.0
        
        return result
    
    async def _calculate_trends(
        self,
        metrics: List[WorkflowMetric],
        time_window: TimeWindow
    ) -> Dict[str, List[float]]:
        """Calculate trends for key metrics."""
        trends = {}
        
        # Group metrics by type and time buckets
        for metric_type in MetricType:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if not type_metrics:
                trends[metric_type.value] = []
                continue
            
            # Create time buckets
            if time_window == TimeWindow.DAILY:
                bucket_hours = 1  # Hourly buckets for daily view
            elif time_window == TimeWindow.WEEKLY:
                bucket_hours = 24  # Daily buckets for weekly view
            elif time_window == TimeWindow.MONTHLY:
                bucket_hours = 24 * 7  # Weekly buckets for monthly view
            else:
                bucket_hours = 1
            
            # Calculate trend values
            trend_values = []
            current_time = min(m.timestamp for m in type_metrics)
            end_time = max(m.timestamp for m in type_metrics)
            
            while current_time < end_time:
                bucket_end = current_time + timedelta(hours=bucket_hours)
                bucket_metrics = [
                    m for m in type_metrics
                    if current_time <= m.timestamp < bucket_end
                ]
                
                if bucket_metrics:
                    trend_values.append(mean([m.value for m in bucket_metrics]))
                else:
                    trend_values.append(0.0)
                
                current_time = bucket_end
            
            trends[metric_type.value] = trend_values
        
        return trends
    
    def _generate_insights(self, metrics: List[WorkflowMetric]) -> List[str]:
        """Generate actionable insights from metrics."""
        insights = []
        
        # Analyze performance against thresholds
        for metric_type, threshold in self.thresholds.items():
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if not type_metrics:
                continue
            
            avg_value = mean([m.value for m in type_metrics])
            
            if avg_value < threshold:
                insights.append(
                    f"{metric_type.value.replace('_', ' ').title()} is below threshold: "
                    f"{avg_value:.2f} vs {threshold:.2f}"
                )
            else:
                insights.append(
                    f"{metric_type.value.replace('_', ' ').title()} is performing well: "
                    f"{avg_value:.2f}"
                )
        
        # Industry-specific insights
        industries = set(m.industry for m in metrics if m.industry)
        if len(industries) > 1:
            insights.append(f"Performance varies across {len(industries)} industries")
        
        # Action type insights
        action_types = set(m.action_type for m in metrics if m.action_type)
        if action_types:
            insights.append(f"Using {len(action_types)} different action types")
        
        return insights
    
    def _generate_recommendations(self, metrics: List[WorkflowMetric]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Performance-based recommendations
        conversion_metrics = [m for m in metrics if m.metric_type == MetricType.CONVERSION_RATE]
        if conversion_metrics:
            avg_conversion = mean([m.value for m in conversion_metrics])
            if avg_conversion < 0.1:
                recommendations.append(
                    "Consider improving conversion rates through better targeting and personalization"
                )
        
        satisfaction_metrics = [m for m in metrics if m.metric_type == MetricType.CUSTOMER_SATISFACTION]
        if satisfaction_metrics:
            avg_satisfaction = mean([m.value for m in satisfaction_metrics])
            if avg_satisfaction < 6.0:
                recommendations.append(
                    "Customer satisfaction is low - review message tone and timing"
                )
        
        # Response time recommendations
        response_metrics = [m for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]
        if response_metrics:
            avg_response_time = mean([m.value for m in response_metrics])
            if avg_response_time > 3600:  # 1 hour
                recommendations.append(
                    "Response times are high - consider increasing automation priority levels"
                )
        
        # General recommendations
        recommendations.extend([
            "Implement A/B testing for workflow variations",
            "Increase personalization based on customer behavior patterns",
            "Monitor industry-specific performance differences",
            "Consider implementing machine learning for trigger optimization"
        ])
        
        return recommendations


class ABTestingManager:
    """Manages A/B tests for workflow optimization."""
    
    def __init__(self, analytics_collector: WorkflowAnalyticsCollector):
        self.collector = analytics_collector
        self.active_tests: Dict[str, ABTestResult] = {}
        
    async def create_ab_test(
        self,
        test_name: str,
        control_variant: str,
        test_variants: List[str],
        traffic_allocation: Dict[str, float] = None
    ) -> str:
        """Create a new A/B test."""
        
        test_id = str(uuid.uuid4())
        
        # Default equal traffic allocation
        if not traffic_allocation:
            all_variants = [control_variant] + test_variants
            equal_share = 1.0 / len(all_variants)
            traffic_allocation = {variant: equal_share for variant in all_variants}
        
        test = ABTestResult(
            test_id=test_id,
            test_name=test_name,
            start_date=datetime.utcnow(),
            end_date=None,
            status="running",
            control_variant=control_variant,
            test_variants=test_variants,
            traffic_allocation=traffic_allocation,
            sample_sizes={},
            conversion_rates={},
            confidence_intervals={},
            statistical_significance=None,
            winner=None,
            revenue_impact={},
            customer_impact={},
            recommendations=[]
        )
        
        self.active_tests[test_id] = test
        
        logger.info(
            f"Created A/B test: {test_name}",
            extra={
                "test_id": test_id,
                "variants": [control_variant] + test_variants,
                "traffic_allocation": traffic_allocation
            }
        )
        
        return test_id
    
    def assign_variant(self, test_id: str, customer_id: str) -> str:
        """Assign customer to test variant."""
        
        test = self.active_tests.get(test_id)
        if not test or test.status != "running":
            return test.control_variant if test else "default"
        
        # Simple hash-based assignment for consistency
        import hashlib
        hash_input = f"{test_id}_{customer_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16) / (2**128)
        
        # Assign based on traffic allocation
        cumulative_probability = 0.0
        for variant, allocation in test.traffic_allocation.items():
            cumulative_probability += allocation
            if hash_value <= cumulative_probability:
                return variant
        
        return test.control_variant
    
    async def record_test_conversion(
        self,
        test_id: str,
        variant: str,
        customer_id: str,
        converted: bool,
        revenue: float = 0.0
    ) -> None:
        """Record a conversion event for A/B test."""
        
        test = self.active_tests.get(test_id)
        if not test or test.status != "running":
            return
        
        # Initialize variant data if needed
        if variant not in test.sample_sizes:
            test.sample_sizes[variant] = 0
            test.conversion_rates[variant] = 0.0
            test.revenue_impact[variant] = 0.0
            test.customer_impact[variant] = 0
        
        # Update metrics
        test.sample_sizes[variant] += 1
        test.customer_impact[variant] += 1
        
        if converted:
            current_conversions = test.conversion_rates[variant] * (test.sample_sizes[variant] - 1)
            new_conversions = current_conversions + 1
            test.conversion_rates[variant] = new_conversions / test.sample_sizes[variant]
            test.revenue_impact[variant] += revenue
        
        # Check for statistical significance
        if test.sample_sizes[variant] >= 100:  # Minimum sample size
            await self._calculate_statistical_significance(test_id)
    
    async def _calculate_statistical_significance(self, test_id: str) -> None:
        """Calculate statistical significance for A/B test."""
        
        test = self.active_tests.get(test_id)
        if not test:
            return
        
        control_rate = test.conversion_rates.get(test.control_variant, 0.0)
        control_size = test.sample_sizes.get(test.control_variant, 0)
        
        if control_size < 100:  # Minimum sample size
            return
        
        # Calculate significance for each test variant
        max_significance = 0.0
        potential_winner = test.control_variant
        
        for variant in test.test_variants:
            if variant not in test.conversion_rates:
                continue
            
            variant_rate = test.conversion_rates[variant]
            variant_size = test.sample_sizes[variant]
            
            if variant_size < 100:
                continue
            
            # Simplified z-test for proportions
            pooled_rate = (control_rate * control_size + variant_rate * variant_size) / (control_size + variant_size)
            se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_size + 1/variant_size))
            
            if se > 0:
                z_score = abs(variant_rate - control_rate) / se
                # Convert to approximate p-value (simplified)
                p_value = 2 * (1 - 0.5 * (1 + np.tanh(z_score / np.sqrt(2))))
                significance = 1 - p_value
                
                if significance > max_significance:
                    max_significance = significance
                    if variant_rate > control_rate:
                        potential_winner = variant
        
        test.statistical_significance = max_significance
        
        # Declare winner if significance > 95%
        if max_significance > 0.95:
            test.winner = potential_winner
            test.status = "completed"
            test.end_date = datetime.utcnow()
            
            # Generate recommendations
            winner_rate = test.conversion_rates[potential_winner]
            control_rate = test.conversion_rates[test.control_variant]
            improvement = ((winner_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0
            
            test.recommendations = [
                f"Implement {potential_winner} variant for {improvement:.1f}% conversion improvement",
                f"Statistical significance: {max_significance:.1%}",
                f"Estimated revenue impact: ${test.revenue_impact.get(potential_winner, 0):,.2f}"
            ]
            
            logger.info(
                f"A/B test completed with winner: {potential_winner}",
                extra={
                    "test_id": test_id,
                    "significance": max_significance,
                    "improvement": improvement
                }
            )
    
    def get_test_results(self, test_id: str) -> Optional[ABTestResult]:
        """Get results for specific A/B test."""
        return self.active_tests.get(test_id)
    
    def get_active_tests(self) -> List[ABTestResult]:
        """Get all active A/B tests."""
        return [test for test in self.active_tests.values() if test.status == "running"]


class WorkflowOptimizer:
    """Optimizes workflows based on performance analytics."""
    
    def __init__(
        self,
        analytics_collector: WorkflowAnalyticsCollector,
        performance_analyzer: WorkflowPerformanceAnalyzer
    ):
        self.collector = analytics_collector
        self.analyzer = performance_analyzer
        
    async def optimize_workflow_triggers(
        self,
        workflow_id: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """Optimize trigger conditions based on performance data."""
        
        # Get recent metrics for the workflow
        metrics = []
        for metric_type in MetricType:
            recent_metrics = self.collector.get_recent_metrics(
                metric_type,
                workflow_id,
                time_window_hours=time_window_days * 24
            )
            metrics.extend(recent_metrics)
        
        if not metrics:
            return {"status": "insufficient_data", "recommendations": []}
        
        # Analyze trigger accuracy
        trigger_metrics = [m for m in metrics if m.metric_type == MetricType.TRIGGER_ACCURACY]
        if trigger_metrics:
            avg_accuracy = mean([m.value for m in trigger_metrics])
        else:
            avg_accuracy = 0.5  # Default assumption
        
        # Generate optimization recommendations
        recommendations = []
        
        if avg_accuracy < 0.7:
            recommendations.extend([
                "Consider increasing confidence thresholds for triggers",
                "Review and refine trigger conditions based on false positives",
                "Implement machine learning models for better trigger prediction"
            ])
        
        # Analyze conversion rates by trigger type
        conversion_by_trigger = defaultdict(list)
        for metric in metrics:
            if metric.metric_type == MetricType.CONVERSION_RATE:
                trigger_type = metric.metadata.get("trigger_type")
                if trigger_type:
                    conversion_by_trigger[trigger_type].append(metric.value)
        
        # Find best and worst performing triggers
        trigger_performance = {}
        for trigger_type, conversions in conversion_by_trigger.items():
            trigger_performance[trigger_type] = mean(conversions)
        
        if trigger_performance:
            best_trigger = max(trigger_performance, key=trigger_performance.get)
            worst_trigger = min(trigger_performance, key=trigger_performance.get)
            
            recommendations.extend([
                f"Best performing trigger: {best_trigger} ({trigger_performance[best_trigger]:.2%} conversion)",
                f"Worst performing trigger: {worst_trigger} ({trigger_performance[worst_trigger]:.2%} conversion)",
                f"Consider expanding use of {best_trigger} trigger patterns"
            ])
        
        return {
            "status": "optimized",
            "trigger_accuracy": avg_accuracy,
            "trigger_performance": trigger_performance,
            "recommendations": recommendations,
            "optimization_timestamp": datetime.utcnow().isoformat()
        }
    
    async def optimize_action_timing(
        self,
        workflow_id: str,
        action_type: ActionType
    ) -> Dict[str, Any]:
        """Optimize action timing based on performance data."""
        
        # Get metrics for specific action type
        metrics = self.collector.get_recent_metrics(
            MetricType.CONVERSION_RATE,
            workflow_id,
            time_window_hours=24 * 30  # 30 days
        )
        
        action_metrics = [
            m for m in metrics
            if m.action_type == action_type
        ]
        
        if not action_metrics:
            return {"status": "insufficient_data"}
        
        # Analyze timing patterns
        timing_performance = defaultdict(list)
        
        for metric in action_metrics:
            delay_minutes = metric.metadata.get("delay_minutes", 0)
            timing_bucket = self._get_timing_bucket(delay_minutes)
            timing_performance[timing_bucket].append(metric.value)
        
        # Find optimal timing
        optimal_timing = None
        best_conversion = 0.0
        
        timing_results = {}
        for timing, conversions in timing_performance.items():
            avg_conversion = mean(conversions)
            timing_results[timing] = {
                "average_conversion": avg_conversion,
                "sample_size": len(conversions)
            }
            
            if avg_conversion > best_conversion and len(conversions) >= 10:
                best_conversion = avg_conversion
                optimal_timing = timing
        
        recommendations = []
        if optimal_timing:
            recommendations.append(
                f"Optimal timing for {action_type.value}: {optimal_timing} "
                f"({best_conversion:.2%} conversion rate)"
            )
        
        return {
            "status": "optimized",
            "action_type": action_type.value,
            "timing_analysis": timing_results,
            "optimal_timing": optimal_timing,
            "best_conversion_rate": best_conversion,
            "recommendations": recommendations
        }
    
    def _get_timing_bucket(self, delay_minutes: int) -> str:
        """Categorize timing into buckets."""
        if delay_minutes < 30:
            return "immediate"
        elif delay_minutes < 60:
            return "30min"
        elif delay_minutes < 240:
            return "1-4hours"
        elif delay_minutes < 1440:
            return "4-24hours"
        elif delay_minutes < 10080:
            return "1-7days"
        else:
            return "7days+"
    
    async def generate_optimization_report(self, workflow_id: str) -> Dict[str, Any]:
        """Generate comprehensive optimization report for workflow."""
        
        # Get performance report
        performance_report = await self.analyzer.generate_performance_report(
            TimeWindow.MONTHLY
        )
        
        # Get trigger optimizations
        trigger_optimization = await self.optimize_workflow_triggers(workflow_id)
        
        # Get action timing optimizations for common action types
        timing_optimizations = {}
        for action_type in [ActionType.SEND_EMAIL, ActionType.SCHEDULE_CALL, ActionType.SEND_SMS]:
            timing_opt = await self.optimize_action_timing(workflow_id, action_type)
            timing_optimizations[action_type.value] = timing_opt
        
        return {
            "workflow_id": workflow_id,
            "report_generated": datetime.utcnow().isoformat(),
            "performance_summary": {
                "success_rate": performance_report.success_rate,
                "conversion_rate": performance_report.conversion_rate,
                "roi_percentage": performance_report.roi_percentage
            },
            "trigger_optimization": trigger_optimization,
            "timing_optimizations": timing_optimizations,
            "overall_recommendations": [
                "Implement A/B testing for major workflow changes",
                "Monitor performance metrics daily",
                "Adjust trigger thresholds based on accuracy metrics",
                "Optimize action timing based on conversion data",
                "Consider industry-specific customizations"
            ]
        }


class WorkflowAnalyticsService:
    """
    Comprehensive workflow analytics service.
    
    Provides real-time analytics, performance monitoring, A/B testing,
    and optimization recommendations for workflow automation.
    """
    
    def __init__(self):
        self.collector = WorkflowAnalyticsCollector()
        self.analyzer = WorkflowPerformanceAnalyzer(self.collector)
        self.ab_testing = ABTestingManager(self.collector)
        self.optimizer = WorkflowOptimizer(self.collector, self.analyzer)
        self.event_bus = EventBus()
        
        # Background tasks
        self.running = False
        self.background_tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """Start the analytics service."""
        if self.running:
            return
        
        self.running = True
        
        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._periodic_flush(), name="metrics_flush"),
            asyncio.create_task(self._periodic_analysis(), name="periodic_analysis"),
            asyncio.create_task(self._ab_test_monitor(), name="ab_test_monitor")
        ]
        
        logger.info("Workflow analytics service started")
    
    async def stop(self) -> None:
        """Stop the analytics service."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        
        logger.info("Workflow analytics service stopped")
    
    async def record_workflow_event(
        self,
        event_type: str,
        workflow_id: str,
        customer_id: str,
        value: float,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Record a workflow event for analytics."""
        
        # Map event types to metric types
        event_metric_map = {
            "workflow_started": MetricType.WORKFLOW_COMPLETION,
            "workflow_completed": MetricType.WORKFLOW_COMPLETION,
            "action_executed": MetricType.ACTION_SUCCESS_RATE,
            "conversion": MetricType.CONVERSION_RATE,
            "customer_response": MetricType.ENGAGEMENT_RATE,
            "satisfaction_feedback": MetricType.CUSTOMER_SATISFACTION,
            "revenue_attributed": MetricType.REVENUE_ATTRIBUTION
        }
        
        metric_type = event_metric_map.get(event_type, MetricType.ENGAGEMENT_RATE)
        
        await self.collector.record_metric(
            workflow_id=workflow_id,
            customer_id=customer_id,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        # Publish analytics event
        await self.event_bus.publish(
            EventType.ANALYTICS_EVENT_PROCESSED,
            {
                "event_type": event_type,
                "workflow_id": workflow_id,
                "customer_id": customer_id,
                "metric_type": metric_type.value,
                "value": value
            }
        )
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data."""
        
        # Get recent performance report
        performance_report = await self.analyzer.generate_performance_report(
            TimeWindow.DAILY
        )
        
        # Get active A/B tests
        active_tests = self.ab_testing.get_active_tests()
        
        # Get real-time metrics
        real_time_metrics = {}
        for metric_type in MetricType:
            recent_metrics = self.collector.get_recent_metrics(metric_type, time_window_hours=1)
            if recent_metrics:
                real_time_metrics[metric_type.value] = mean([m.value for m in recent_metrics])
            else:
                real_time_metrics[metric_type.value] = 0.0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance_summary": {
                "total_workflows": performance_report.total_workflows,
                "success_rate": performance_report.success_rate,
                "conversion_rate": performance_report.conversion_rate,
                "customer_satisfaction": performance_report.customer_satisfaction,
                "roi_percentage": performance_report.roi_percentage
            },
            "real_time_metrics": real_time_metrics,
            "active_ab_tests": len(active_tests),
            "trends": performance_report.trends,
            "top_insights": performance_report.insights[:5],
            "key_recommendations": performance_report.recommendations[:3]
        }
    
    async def _periodic_flush(self) -> None:
        """Periodically flush metrics buffer."""
        while self.running:
            try:
                await self.collector._flush_metrics_buffer()
                await asyncio.sleep(300)  # 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_analysis(self) -> None:
        """Periodically generate performance analysis."""
        while self.running:
            try:
                # Generate daily performance report
                report = await self.analyzer.generate_performance_report(TimeWindow.DAILY)
                
                # Publish analytics insights
                await self.event_bus.publish(
                    EventType.ANALYTICS_JOURNEY_PREDICTED,
                    {
                        "report_id": report.report_id,
                        "total_workflows": report.total_workflows,
                        "success_rate": report.success_rate,
                        "insights_count": len(report.insights)
                    }
                )
                
                await asyncio.sleep(3600)  # 1 hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                await asyncio.sleep(300)
    
    async def _ab_test_monitor(self) -> None:
        """Monitor A/B tests for completion."""
        while self.running:
            try:
                for test_id, test in self.ab_testing.active_tests.items():
                    if test.status == "running":
                        # Check if test should be completed based on sample size or duration
                        total_samples = sum(test.sample_sizes.values())
                        test_duration = datetime.utcnow() - test.start_date
                        
                        if total_samples >= 1000 or test_duration.days >= 30:
                            await self.ab_testing._calculate_statistical_significance(test_id)
                
                await asyncio.sleep(3600)  # 1 hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in A/B test monitor: {e}")
                await asyncio.sleep(300)


# Factory function
def create_workflow_analytics_service() -> WorkflowAnalyticsService:
    """Create and configure workflow analytics service."""
    return WorkflowAnalyticsService()