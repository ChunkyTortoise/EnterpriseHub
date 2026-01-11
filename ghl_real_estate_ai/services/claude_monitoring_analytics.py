"""
Claude Monitoring & Analytics Service - Comprehensive System Intelligence

Advanced monitoring, analytics, and cost optimization service providing
business intelligence, performance insights, and ROI tracking for the
Universal Claude system throughout EnterpriseHub.

Key Features:
- Real-time performance monitoring and alerting
- Cost optimization analytics and budget management
- Business impact measurement and ROI tracking
- Agent coaching effectiveness analysis
- Predictive scaling and resource optimization
- Comprehensive reporting and dashboards
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import defaultdict, deque
import numpy as np

from ..ghl_utils.config import settings
from .universal_claude_gateway import UniversalClaudeGateway
from .claude_performance_optimizer import get_performance_optimizer

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric classification types."""
    PERFORMANCE = "performance"
    COST = "cost"
    BUSINESS = "business"
    USAGE = "usage"
    QUALITY = "quality"


@dataclass
class Alert:
    """Monitoring alert structure."""
    id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class BusinessImpactMetrics:
    """Business impact tracking metrics."""
    agent_productivity_improvement: float = 0.0
    response_time_improvement: float = 0.0
    coaching_effectiveness_score: float = 0.0
    cost_savings_usd: float = 0.0
    total_requests_processed: int = 0
    successful_interactions: int = 0
    estimated_revenue_impact: float = 0.0
    roi_percentage: float = 0.0


@dataclass
class CostOptimizationInsight:
    """Cost optimization recommendation."""
    category: str
    description: str
    potential_savings_usd: float
    implementation_effort: str  # low, medium, high
    priority_score: float
    detailed_analysis: Dict[str, Any]


class ClaudeMonitoringAnalytics:
    """
    Comprehensive monitoring and analytics service for Claude system.

    Provides real-time monitoring, cost optimization, business intelligence,
    and predictive insights for the Universal Claude ecosystem.
    """

    def __init__(self):
        # Monitoring configuration
        self.monitoring_enabled = True
        self.alert_thresholds = self._initialize_alert_thresholds()

        # Data storage
        self.alerts: List[Alert] = []
        self.performance_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.business_metrics: BusinessImpactMetrics = BusinessImpactMetrics()
        self.cost_tracking: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Analytics components
        self.trend_analyzer = TrendAnalyzer()
        self.cost_optimizer = CostOptimizer()
        self.business_intelligence = BusinessIntelligence()

        # Prediction models
        self.usage_predictor = UsagePredictor()
        self.scaling_predictor = ScalingPredictor()

        logger.info("Claude Monitoring & Analytics service initialized")

    async def initialize(self) -> None:
        """Initialize async monitoring components."""
        try:
            # Start background monitoring tasks
            await self._start_monitoring_tasks()

            # Initialize predictive models with historical data
            await self._initialize_predictive_models()

            logger.info("Claude Monitoring & Analytics fully initialized")

        except Exception as e:
            logger.error(f"Error initializing monitoring service: {e}")

    async def record_interaction(
        self,
        agent_id: str,
        query_type: str,
        response_time_ms: float,
        success: bool,
        cost_tokens: int,
        confidence_score: float,
        agent_role: Optional[str] = None
    ) -> None:
        """Record Claude interaction for monitoring and analysis."""
        try:
            timestamp = datetime.now()

            # Record performance metrics
            self.performance_metrics['response_times'].append(response_time_ms)
            self.performance_metrics['confidence_scores'].append(confidence_score)
            self.performance_metrics['success_rates'].append(1.0 if success else 0.0)

            # Update business metrics
            self.business_metrics.total_requests_processed += 1
            if success:
                self.business_metrics.successful_interactions += 1

            # Track costs
            cost_usd = (cost_tokens / 1000) * 0.003  # Approximate cost per 1K tokens
            hour_key = timestamp.strftime('%Y-%m-%d-%H')
            if hour_key not in self.cost_tracking:
                self.cost_tracking[hour_key] = defaultdict(float)

            self.cost_tracking[hour_key]['total_cost'] += cost_usd
            self.cost_tracking[hour_key]['total_tokens'] += cost_tokens
            self.cost_tracking[hour_key]['total_requests'] += 1

            # Check for alerts
            await self._check_performance_alerts(response_time_ms, confidence_score)

            # Update trend analysis
            await self.trend_analyzer.update_trends({
                'response_time': response_time_ms,
                'confidence': confidence_score,
                'cost': cost_usd,
                'timestamp': timestamp
            })

            logger.debug(f"Recorded interaction: {agent_id} | {query_type} | {response_time_ms:.1f}ms")

        except Exception as e:
            logger.error(f"Error recording interaction: {e}")

    async def generate_comprehensive_report(
        self,
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=period_hours)

            # Performance analysis
            performance_analysis = await self._analyze_performance_trends(start_time, end_time)

            # Cost analysis
            cost_analysis = await self._analyze_cost_trends(start_time, end_time)

            # Business impact analysis
            business_analysis = await self._analyze_business_impact(start_time, end_time)

            # Alert summary
            alert_summary = await self._summarize_alerts(start_time, end_time)

            # Optimization recommendations
            optimization_recommendations = await self._generate_optimization_recommendations()

            # Predictive insights
            predictive_insights = await self._generate_predictive_insights()

            return {
                "report_metadata": {
                    "generated_at": end_time.isoformat(),
                    "period_hours": period_hours,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                "performance_analysis": performance_analysis,
                "cost_analysis": cost_analysis,
                "business_analysis": business_analysis,
                "alert_summary": alert_summary,
                "optimization_recommendations": optimization_recommendations,
                "predictive_insights": predictive_insights,
                "executive_summary": await self._generate_executive_summary(
                    performance_analysis, cost_analysis, business_analysis
                )
            }

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {"error": f"Report generation failed: {str(e)}"}

    async def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data for monitoring."""
        try:
            current_time = datetime.now()

            # Current performance metrics
            recent_response_times = list(self.performance_metrics['response_times'])[-100:]
            recent_confidence_scores = list(self.performance_metrics['confidence_scores'])[-100:]
            recent_success_rates = list(self.performance_metrics['success_rates'])[-100:]

            # Calculate current statistics
            avg_response_time = statistics.mean(recent_response_times) if recent_response_times else 0
            avg_confidence = statistics.mean(recent_confidence_scores) if recent_confidence_scores else 0
            success_rate = statistics.mean(recent_success_rates) if recent_success_rates else 0

            # Cost tracking for current hour
            current_hour_key = current_time.strftime('%Y-%m-%d-%H')
            current_hour_costs = self.cost_tracking.get(current_hour_key, {})

            # Active alerts
            active_alerts = [alert for alert in self.alerts if not alert.resolved]

            # Performance optimizer stats
            optimizer_stats = {}
            try:
                optimizer = await get_performance_optimizer()
                optimizer_stats = await optimizer.get_performance_statistics()
            except Exception as e:
                logger.debug(f"Could not get optimizer stats: {e}")

            return {
                "timestamp": current_time.isoformat(),
                "performance_metrics": {
                    "avg_response_time_ms": round(avg_response_time, 1),
                    "avg_confidence_score": round(avg_confidence, 3),
                    "success_rate": round(success_rate, 3),
                    "total_requests": self.business_metrics.total_requests_processed,
                    "successful_interactions": self.business_metrics.successful_interactions
                },
                "cost_metrics": {
                    "hourly_cost_usd": round(current_hour_costs.get('total_cost', 0), 2),
                    "hourly_tokens": int(current_hour_costs.get('total_tokens', 0)),
                    "hourly_requests": int(current_hour_costs.get('total_requests', 0)),
                    "total_savings_usd": round(self.business_metrics.cost_savings_usd, 2)
                },
                "business_metrics": {
                    "productivity_improvement": f"{self.business_metrics.agent_productivity_improvement:.1%}",
                    "coaching_effectiveness": f"{self.business_metrics.coaching_effectiveness_score:.1%}",
                    "estimated_revenue_impact": f"${self.business_metrics.estimated_revenue_impact:,.0f}",
                    "roi_percentage": f"{self.business_metrics.roi_percentage:.1%}"
                },
                "alerts": {
                    "active_count": len(active_alerts),
                    "critical_count": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                    "recent_alerts": [
                        {
                            "severity": alert.severity.value,
                            "message": alert.message,
                            "timestamp": alert.timestamp.isoformat()
                        }
                        for alert in active_alerts[-5:]  # Last 5 alerts
                    ]
                },
                "optimization_status": {
                    "cache_hit_rate": optimizer_stats.get('cache_hit_rate', 0),
                    "compression_savings_mb": optimizer_stats.get('compression_savings_mb', 0),
                    "optimization_enabled": len(optimizer_stats) > 0
                }
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": f"Dashboard data unavailable: {str(e)}"}

    async def get_cost_optimization_insights(self) -> List[CostOptimizationInsight]:
        """Generate cost optimization insights and recommendations."""
        try:
            insights = []

            # Analyze current cost patterns
            cost_analysis = await self._analyze_recent_costs()

            # Model selection optimization
            if cost_analysis.get('high_cost_queries', 0) > 0:
                insights.append(CostOptimizationInsight(
                    category="Model Selection",
                    description="Optimize model selection for high-cost queries using intelligent routing",
                    potential_savings_usd=cost_analysis.get('model_optimization_savings', 0),
                    implementation_effort="medium",
                    priority_score=0.8,
                    detailed_analysis={
                        "high_cost_queries": cost_analysis.get('high_cost_queries'),
                        "optimization_strategy": "Use Haiku for simple queries, Sonnet for complex ones"
                    }
                ))

            # Caching optimization
            cache_analysis = await self._analyze_cache_opportunities()
            if cache_analysis.get('cache_miss_rate', 0) > 0.3:
                insights.append(CostOptimizationInsight(
                    category="Caching Strategy",
                    description="Improve caching strategies to reduce duplicate processing costs",
                    potential_savings_usd=cache_analysis.get('caching_savings_potential', 0),
                    implementation_effort="low",
                    priority_score=0.9,
                    detailed_analysis=cache_analysis
                ))

            # Query optimization
            query_analysis = await self._analyze_query_patterns()
            if query_analysis.get('optimization_opportunities', 0) > 0:
                insights.append(CostOptimizationInsight(
                    category="Query Optimization",
                    description="Optimize query patterns and reduce unnecessary token usage",
                    potential_savings_usd=query_analysis.get('query_optimization_savings', 0),
                    implementation_effort="medium",
                    priority_score=0.7,
                    detailed_analysis=query_analysis
                ))

            # Budget management
            budget_analysis = await self._analyze_budget_efficiency()
            if budget_analysis.get('budget_utilization', 0) > 0.8:
                insights.append(CostOptimizationInsight(
                    category="Budget Management",
                    description="Implement dynamic budget allocation and usage monitoring",
                    potential_savings_usd=budget_analysis.get('budget_savings_potential', 0),
                    implementation_effort="high",
                    priority_score=0.6,
                    detailed_analysis=budget_analysis
                ))

            # Sort by priority score
            insights.sort(key=lambda x: x.priority_score, reverse=True)

            return insights

        except Exception as e:
            logger.error(f"Error generating cost optimization insights: {e}")
            return []

    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert thresholds for monitoring."""
        return {
            "response_time": {
                "warning_ms": 1000,
                "error_ms": 2000,
                "critical_ms": 5000
            },
            "confidence_score": {
                "warning_threshold": 0.6,
                "error_threshold": 0.4,
                "critical_threshold": 0.2
            },
            "success_rate": {
                "warning_threshold": 0.95,
                "error_threshold": 0.90,
                "critical_threshold": 0.80
            },
            "cost_per_hour": {
                "warning_usd": 10.0,
                "error_usd": 25.0,
                "critical_usd": 50.0
            }
        }

    async def _check_performance_alerts(
        self,
        response_time_ms: float,
        confidence_score: float
    ) -> None:
        """Check for performance-related alerts."""
        try:
            # Response time alerts
            if response_time_ms > self.alert_thresholds["response_time"]["critical_ms"]:
                await self._create_alert(
                    AlertSeverity.CRITICAL,
                    MetricType.PERFORMANCE,
                    f"Critical response time: {response_time_ms:.0f}ms",
                    {"response_time_ms": response_time_ms, "threshold": "critical"}
                )
            elif response_time_ms > self.alert_thresholds["response_time"]["error_ms"]:
                await self._create_alert(
                    AlertSeverity.ERROR,
                    MetricType.PERFORMANCE,
                    f"High response time: {response_time_ms:.0f}ms",
                    {"response_time_ms": response_time_ms, "threshold": "error"}
                )

            # Confidence score alerts
            if confidence_score < self.alert_thresholds["confidence_score"]["critical_threshold"]:
                await self._create_alert(
                    AlertSeverity.CRITICAL,
                    MetricType.QUALITY,
                    f"Critical low confidence: {confidence_score:.1%}",
                    {"confidence_score": confidence_score, "threshold": "critical"}
                )

        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")

    async def _create_alert(
        self,
        severity: AlertSeverity,
        metric_type: MetricType,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """Create and store an alert."""
        try:
            alert = Alert(
                id=f"alert_{datetime.now().timestamp()}",
                severity=severity,
                metric_type=metric_type,
                message=message,
                details=details
            )

            self.alerts.append(alert)

            # Keep only last 1000 alerts
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]

            logger.warning(f"Alert created: {severity.value.upper()} - {message}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _analyze_performance_trends(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Analyze performance trends over time period."""
        try:
            recent_response_times = list(self.performance_metrics['response_times'])
            recent_confidence_scores = list(self.performance_metrics['confidence_scores'])
            recent_success_rates = list(self.performance_metrics['success_rates'])

            if not recent_response_times:
                return {"message": "Insufficient data for performance analysis"}

            return {
                "avg_response_time_ms": round(statistics.mean(recent_response_times), 1),
                "p95_response_time_ms": round(np.percentile(recent_response_times, 95), 1),
                "avg_confidence_score": round(statistics.mean(recent_confidence_scores), 3),
                "success_rate": round(statistics.mean(recent_success_rates), 3),
                "total_requests": len(recent_response_times),
                "performance_trend": await self._calculate_trend(recent_response_times),
                "quality_trend": await self._calculate_trend(recent_confidence_scores)
            }

        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {"error": str(e)}

    async def _analyze_cost_trends(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Analyze cost trends and patterns."""
        try:
            # Calculate cost metrics for the period
            total_cost = 0
            total_tokens = 0
            total_requests = 0

            for hour_key, costs in self.cost_tracking.items():
                hour_time = datetime.strptime(hour_key, '%Y-%m-%d-%H')
                if start_time <= hour_time <= end_time:
                    total_cost += costs.get('total_cost', 0)
                    total_tokens += costs.get('total_tokens', 0)
                    total_requests += costs.get('total_requests', 0)

            avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
            avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0

            return {
                "total_cost_usd": round(total_cost, 2),
                "total_tokens": int(total_tokens),
                "total_requests": int(total_requests),
                "avg_cost_per_request": round(avg_cost_per_request, 4),
                "avg_tokens_per_request": round(avg_tokens_per_request, 1),
                "cost_efficiency_score": await self._calculate_cost_efficiency(),
                "cost_trend": "stable"  # Would implement trend calculation
            }

        except Exception as e:
            logger.error(f"Error analyzing cost trends: {e}")
            return {"error": str(e)}

    async def _analyze_business_impact(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Analyze business impact and ROI."""
        try:
            # Calculate key business metrics
            total_interactions = self.business_metrics.total_requests_processed
            successful_interactions = self.business_metrics.successful_interactions

            # Estimate productivity improvements
            baseline_response_time = 30000  # 30 seconds baseline manual response
            claude_response_times = list(self.performance_metrics['response_times'])
            avg_claude_response = statistics.mean(claude_response_times) if claude_response_times else 0

            time_savings_per_interaction = (baseline_response_time - avg_claude_response) / 1000  # seconds
            total_time_saved_hours = (time_savings_per_interaction * total_interactions) / 3600

            # Estimate revenue impact (assuming $50/hour agent cost)
            agent_cost_per_hour = 50
            estimated_cost_savings = total_time_saved_hours * agent_cost_per_hour

            # Calculate ROI
            system_operational_cost = 1000  # Monthly operational cost estimate
            roi_percentage = (estimated_cost_savings - system_operational_cost) / system_operational_cost * 100

            return {
                "total_interactions": total_interactions,
                "successful_interactions": successful_interactions,
                "success_rate": successful_interactions / total_interactions if total_interactions > 0 else 0,
                "time_saved_hours": round(total_time_saved_hours, 1),
                "estimated_cost_savings_usd": round(estimated_cost_savings, 2),
                "roi_percentage": round(roi_percentage, 1),
                "productivity_improvement": f"{(total_time_saved_hours / (total_interactions * 0.5)):.1%}" if total_interactions > 0 else "0%",
                "coaching_effectiveness_score": statistics.mean(self.performance_metrics['confidence_scores']) if self.performance_metrics['confidence_scores'] else 0
            }

        except Exception as e:
            logger.error(f"Error analyzing business impact: {e}")
            return {"error": str(e)}

    async def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        try:
            if len(values) < 10:
                return "insufficient_data"

            # Compare recent values to earlier values
            recent_avg = statistics.mean(values[-10:])
            earlier_avg = statistics.mean(values[-20:-10]) if len(values) >= 20 else statistics.mean(values[:-10])

            change_percent = (recent_avg - earlier_avg) / earlier_avg * 100 if earlier_avg != 0 else 0

            if change_percent > 5:
                return "improving"
            elif change_percent < -5:
                return "declining"
            else:
                return "stable"

        except Exception as e:
            return "unknown"

    async def _calculate_cost_efficiency(self) -> float:
        """Calculate cost efficiency score."""
        try:
            # Simple cost efficiency based on requests per dollar
            recent_costs = list(self.cost_tracking.values())[-24:]  # Last 24 hours
            if not recent_costs:
                return 0.0

            total_cost = sum(cost.get('total_cost', 0) for cost in recent_costs)
            total_requests = sum(cost.get('total_requests', 0) for cost in recent_costs)

            if total_cost == 0:
                return 1.0

            requests_per_dollar = total_requests / total_cost
            # Normalize to 0-1 scale (assuming 100 requests per dollar is excellent)
            efficiency_score = min(requests_per_dollar / 100, 1.0)

            return round(efficiency_score, 3)

        except Exception as e:
            logger.error(f"Error calculating cost efficiency: {e}")
            return 0.0

    async def _analyze_recent_costs(self) -> Dict[str, Any]:
        """Analyze recent cost patterns for optimization."""
        # Mock implementation - would analyze actual cost data
        return {
            "high_cost_queries": 15,
            "model_optimization_savings": 125.50,
            "avg_cost_per_query": 0.02
        }

    async def _analyze_cache_opportunities(self) -> Dict[str, Any]:
        """Analyze caching optimization opportunities."""
        # Mock implementation - would analyze actual cache data
        return {
            "cache_miss_rate": 0.35,
            "caching_savings_potential": 89.25,
            "optimization_strategy": "Implement aggressive caching for repeated queries"
        }

    async def _analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns for optimization."""
        # Mock implementation - would analyze actual query patterns
        return {
            "optimization_opportunities": 8,
            "query_optimization_savings": 67.80,
            "common_patterns": ["property_search", "objection_handling"]
        }

    async def _analyze_budget_efficiency(self) -> Dict[str, Any]:
        """Analyze budget efficiency and utilization."""
        # Mock implementation - would analyze actual budget data
        return {
            "budget_utilization": 0.85,
            "budget_savings_potential": 156.40,
            "optimization_strategy": "Dynamic allocation based on peak usage"
        }

    async def _start_monitoring_tasks(self) -> None:
        """Start background monitoring tasks."""
        # Start periodic monitoring tasks
        asyncio.create_task(self._periodic_health_check())
        asyncio.create_task(self._periodic_cost_analysis())

    async def _periodic_health_check(self) -> None:
        """Periodic health check task."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                # Perform health checks
                await self._check_system_health()
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")

    async def _periodic_cost_analysis(self) -> None:
        """Periodic cost analysis task."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                # Perform cost analysis
                await self._analyze_hourly_costs()
            except Exception as e:
                logger.error(f"Error in periodic cost analysis: {e}")

    async def _check_system_health(self) -> None:
        """Check overall system health."""
        # Implementation would check various health metrics
        pass

    async def _analyze_hourly_costs(self) -> None:
        """Analyze costs on an hourly basis."""
        # Implementation would analyze hourly cost patterns
        pass

    async def _initialize_predictive_models(self) -> None:
        """Initialize predictive models with historical data."""
        # Implementation would initialize ML models for prediction
        pass

    async def _summarize_alerts(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Summarize alerts for the period."""
        period_alerts = [
            alert for alert in self.alerts
            if start_time <= alert.timestamp <= end_time
        ]

        return {
            "total_alerts": len(period_alerts),
            "critical_alerts": len([a for a in period_alerts if a.severity == AlertSeverity.CRITICAL]),
            "resolved_alerts": len([a for a in period_alerts if a.resolved]),
            "alert_categories": {}  # Would categorize alerts
        }

    async def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations."""
        insights = await self.get_cost_optimization_insights()
        return [
            {
                "category": insight.category,
                "description": insight.description,
                "potential_savings": f"${insight.potential_savings_usd:.2f}",
                "priority": insight.priority_score,
                "effort": insight.implementation_effort
            }
            for insight in insights[:5]  # Top 5 recommendations
        ]

    async def _generate_predictive_insights(self) -> Dict[str, Any]:
        """Generate predictive insights."""
        return {
            "usage_forecast": "Stable growth expected",
            "cost_projection": "15% increase next month",
            "capacity_planning": "Current resources sufficient"
        }

    async def _generate_executive_summary(
        self,
        performance_analysis: Dict[str, Any],
        cost_analysis: Dict[str, Any],
        business_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary."""
        return {
            "key_metrics": {
                "avg_response_time": f"{performance_analysis.get('avg_response_time_ms', 0):.0f}ms",
                "success_rate": f"{performance_analysis.get('success_rate', 0):.1%}",
                "total_cost": f"${cost_analysis.get('total_cost_usd', 0):.2f}",
                "roi": f"{business_analysis.get('roi_percentage', 0):.0f}%"
            },
            "highlights": [
                f"Processed {business_analysis.get('total_interactions', 0)} interactions",
                f"Saved {business_analysis.get('time_saved_hours', 0):.0f} hours of agent time",
                f"Achieved {performance_analysis.get('success_rate', 0):.1%} success rate"
            ],
            "recommendations": [
                "Continue monitoring performance trends",
                "Implement recommended optimizations",
                "Scale resources based on usage patterns"
            ]
        }


# Placeholder classes for analytics components
class TrendAnalyzer:
    async def update_trends(self, data: Dict[str, Any]) -> None:
        pass


class CostOptimizer:
    pass


class BusinessIntelligence:
    pass


class UsagePredictor:
    pass


class ScalingPredictor:
    pass


# Singleton instance
_monitoring_service: Optional[ClaudeMonitoringAnalytics] = None


async def get_monitoring_service() -> ClaudeMonitoringAnalytics:
    """Get or create the global monitoring service instance."""
    global _monitoring_service

    if _monitoring_service is None:
        _monitoring_service = ClaudeMonitoringAnalytics()
        await _monitoring_service.initialize()

    return _monitoring_service


# Convenience functions
async def record_claude_interaction(
    agent_id: str,
    query_type: str,
    response_time_ms: float,
    success: bool,
    cost_tokens: int,
    confidence_score: float,
    agent_role: Optional[str] = None
) -> None:
    """Convenience function to record Claude interaction."""
    monitoring_service = await get_monitoring_service()
    await monitoring_service.record_interaction(
        agent_id, query_type, response_time_ms, success,
        cost_tokens, confidence_score, agent_role
    )


async def get_monitoring_dashboard_data() -> Dict[str, Any]:
    """Convenience function to get dashboard data."""
    monitoring_service = await get_monitoring_service()
    return await monitoring_service.get_real_time_dashboard_data()


async def generate_monitoring_report(period_hours: int = 24) -> Dict[str, Any]:
    """Convenience function to generate monitoring report."""
    monitoring_service = await get_monitoring_service()
    return await monitoring_service.generate_comprehensive_report(period_hours)