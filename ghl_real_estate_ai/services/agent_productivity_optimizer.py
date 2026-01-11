"""
Agent Productivity Optimization Service

AI-powered service that analyzes agent performance data and provides personalized
recommendations to improve productivity, efficiency, and success rates.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
import statistics
import logging

logger = logging.getLogger(__name__)


class ProductivityMetric(Enum):
    """Key productivity metrics tracked for agents."""
    LEAD_RESPONSE_TIME = "lead_response_time"
    CONVERSION_RATE = "conversion_rate"
    FOLLOW_UP_CONSISTENCY = "follow_up_consistency"
    DEAL_CYCLE_TIME = "deal_cycle_time"
    CLIENT_SATISFACTION = "client_satisfaction"
    ACTIVITY_VOLUME = "activity_volume"
    REVENUE_PER_TRANSACTION = "revenue_per_transaction"
    TIME_MANAGEMENT = "time_management"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    COMMUNICATION_EFFECTIVENESS = "communication_effectiveness"


class OptimizationType(Enum):
    """Types of optimization recommendations."""
    WORKFLOW_IMPROVEMENT = "workflow_improvement"
    SKILL_DEVELOPMENT = "skill_development"
    TECHNOLOGY_UTILIZATION = "technology_utilization"
    TIME_MANAGEMENT = "time_management"
    COMMUNICATION_ENHANCEMENT = "communication_enhancement"
    LEAD_NURTURING = "lead_nurturing"
    CLIENT_RELATIONSHIP = "client_relationship"
    AUTOMATION_OPPORTUNITY = "automation_opportunity"
    TRAINING_RECOMMENDATION = "training_recommendation"
    PROCESS_OPTIMIZATION = "process_optimization"


class Priority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactLevel(Enum):
    """Expected impact levels for optimizations."""
    TRANSFORMATIONAL = "transformational"  # >50% improvement
    SIGNIFICANT = "significant"           # 25-50% improvement
    MODERATE = "moderate"                # 10-25% improvement
    INCREMENTAL = "incremental"          # <10% improvement


@dataclass
class PerformanceData:
    """Agent performance data structure."""
    agent_id: str
    metric: ProductivityMetric
    value: float
    benchmark_value: Optional[float] = None
    measurement_date: datetime = field(default_factory=datetime.utcnow)
    period: str = "daily"  # daily, weekly, monthly, quarterly
    data_source: str = "system"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Productivity optimization recommendation."""
    id: str
    agent_id: str
    optimization_type: OptimizationType
    priority: Priority
    impact_level: ImpactLevel
    title: str
    description: str
    problem_analysis: str
    recommended_actions: List[str]
    expected_improvement: str
    implementation_effort: str
    time_to_impact: str
    success_metrics: List[str]
    related_metrics: List[ProductivityMetric]
    automation_potential: float  # 0.0-1.0
    roi_estimate: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, dismissed
    created_date: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    feedback_score: Optional[float] = None
    actual_improvement: Optional[float] = None


@dataclass
class ProductivityBenchmark:
    """Performance benchmarks for comparison."""
    metric: ProductivityMetric
    team_average: float
    top_performer: float
    industry_standard: float
    target_value: float
    measurement_unit: str
    calculation_method: str
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProductivityInsight:
    """AI-generated insight about agent performance."""
    id: str
    agent_id: str
    insight_type: str  # trend, pattern, opportunity, risk
    title: str
    description: str
    supporting_data: Dict[str, Any]
    confidence_level: float  # 0.0-1.0
    actionable: bool
    related_recommendations: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowAnalysis:
    """Analysis of agent workflow efficiency."""
    agent_id: str
    analysis_date: datetime
    workflow_efficiency_score: float
    time_allocation: Dict[str, float]
    bottlenecks: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]
    technology_usage: Dict[str, float]
    communication_patterns: Dict[str, Any]
    peak_performance_hours: List[int]
    suggestions: List[str]


@dataclass
class AgentProductivityProfile:
    """Comprehensive productivity profile for an agent."""
    agent_id: str
    overall_score: float
    strengths: List[str]
    improvement_areas: List[str]
    performance_trends: Dict[str, List[float]]
    benchmark_comparisons: Dict[str, float]
    active_recommendations: List[str]
    completed_optimizations: List[str]
    productivity_rank: Optional[int] = None
    last_assessment: datetime = field(default_factory=datetime.utcnow)


class AgentProductivityOptimizer:
    """Service for analyzing agent performance and generating optimization recommendations."""

    def __init__(self):
        """Initialize the productivity optimizer."""
        self.performance_data: Dict[str, List[PerformanceData]] = {}
        self.recommendations: Dict[str, OptimizationRecommendation] = {}
        self.benchmarks: Dict[ProductivityMetric, ProductivityBenchmark] = {}
        self.insights: Dict[str, List[ProductivityInsight]] = {}
        self.workflow_analyses: Dict[str, List[WorkflowAnalysis]] = {}
        self.agent_profiles: Dict[str, AgentProductivityProfile] = {}

        # Initialize default benchmarks
        self._initialize_performance_benchmarks()

    def _initialize_performance_benchmarks(self):
        """Initialize default performance benchmarks."""
        benchmarks = [
            ProductivityBenchmark(
                metric=ProductivityMetric.LEAD_RESPONSE_TIME,
                team_average=45.0,  # minutes
                top_performer=15.0,
                industry_standard=60.0,
                target_value=30.0,
                measurement_unit="minutes",
                calculation_method="average response time to new leads"
            ),
            ProductivityBenchmark(
                metric=ProductivityMetric.CONVERSION_RATE,
                team_average=0.15,  # 15%
                top_performer=0.25,
                industry_standard=0.12,
                target_value=0.20,
                measurement_unit="percentage",
                calculation_method="leads converted to clients / total leads"
            ),
            ProductivityBenchmark(
                metric=ProductivityMetric.FOLLOW_UP_CONSISTENCY,
                team_average=0.70,  # 70%
                top_performer=0.95,
                industry_standard=0.60,
                target_value=0.85,
                measurement_unit="percentage",
                calculation_method="follow-ups completed / follow-ups scheduled"
            ),
            ProductivityBenchmark(
                metric=ProductivityMetric.DEAL_CYCLE_TIME,
                team_average=45.0,  # days
                top_performer=30.0,
                industry_standard=60.0,
                target_value=35.0,
                measurement_unit="days",
                calculation_method="average days from lead to close"
            ),
            ProductivityBenchmark(
                metric=ProductivityMetric.CLIENT_SATISFACTION,
                team_average=4.2,  # out of 5
                top_performer=4.8,
                industry_standard=4.0,
                target_value=4.5,
                measurement_unit="rating (1-5)",
                calculation_method="average client satisfaction rating"
            ),
            ProductivityBenchmark(
                metric=ProductivityMetric.ACTIVITY_VOLUME,
                team_average=25.0,  # activities per day
                top_performer=40.0,
                industry_standard=20.0,
                target_value=30.0,
                measurement_unit="activities per day",
                calculation_method="calls, emails, meetings per day"
            ),
            ProductivityBenchmark(
                metric=ProductivityMetric.TECHNOLOGY_ADOPTION,
                team_average=0.75,  # 75%
                top_performer=0.95,
                industry_standard=0.65,
                target_value=0.85,
                measurement_unit="percentage",
                calculation_method="available tools actively used"
            )
        ]

        for benchmark in benchmarks:
            self.benchmarks[benchmark.metric] = benchmark

    async def record_performance_data(
        self,
        agent_id: str,
        metric: ProductivityMetric,
        value: float,
        period: str = "daily",
        context: Optional[Dict[str, Any]] = None
    ):
        """Record performance data for an agent."""
        try:
            # Get benchmark for comparison
            benchmark = self.benchmarks.get(metric)
            benchmark_value = benchmark.team_average if benchmark else None

            performance_data = PerformanceData(
                agent_id=agent_id,
                metric=metric,
                value=value,
                benchmark_value=benchmark_value,
                period=period,
                context=context or {}
            )

            if agent_id not in self.performance_data:
                self.performance_data[agent_id] = []

            self.performance_data[agent_id].append(performance_data)

            # Trigger analysis if enough data
            await self._trigger_analysis_if_needed(agent_id)

            logger.info(f"Recorded performance data for agent {agent_id}: {metric.value} = {value}")

        except Exception as e:
            logger.error(f"Error recording performance data: {str(e)}")
            raise

    async def analyze_agent_performance(
        self,
        agent_id: str,
        analysis_period_days: int = 30
    ) -> AgentProductivityProfile:
        """Analyze agent performance and generate comprehensive profile."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)

            # Get recent performance data
            agent_data = [
                data for data in self.performance_data.get(agent_id, [])
                if data.measurement_date >= cutoff_date
            ]

            if not agent_data:
                # Create basic profile for new agent
                profile = AgentProductivityProfile(
                    agent_id=agent_id,
                    overall_score=0.0,
                    strengths=[],
                    improvement_areas=["Insufficient data for analysis"],
                    performance_trends={},
                    benchmark_comparisons={},
                    active_recommendations=[]
                )
                self.agent_profiles[agent_id] = profile
                return profile

            # Calculate metrics
            metric_values = {}
            benchmark_comparisons = {}

            for metric in ProductivityMetric:
                metric_data = [d.value for d in agent_data if d.metric == metric]
                if metric_data:
                    avg_value = statistics.mean(metric_data)
                    metric_values[metric.value] = avg_value

                    # Compare to benchmark
                    benchmark = self.benchmarks.get(metric)
                    if benchmark:
                        comparison_ratio = avg_value / benchmark.team_average
                        benchmark_comparisons[metric.value] = comparison_ratio

            # Calculate overall score (weighted average)
            overall_score = await self._calculate_overall_score(metric_values, benchmark_comparisons)

            # Identify strengths and improvement areas
            strengths, improvement_areas = await self._identify_strengths_and_improvements(
                benchmark_comparisons
            )

            # Calculate trends
            performance_trends = await self._calculate_performance_trends(agent_data)

            # Get active recommendations
            active_recommendations = [
                rec.id for rec in self.recommendations.values()
                if rec.agent_id == agent_id and rec.status in ["pending", "in_progress"]
            ]

            # Create profile
            profile = AgentProductivityProfile(
                agent_id=agent_id,
                overall_score=overall_score,
                strengths=strengths,
                improvement_areas=improvement_areas,
                performance_trends=performance_trends,
                benchmark_comparisons=benchmark_comparisons,
                active_recommendations=active_recommendations,
                completed_optimizations=[]
            )

            self.agent_profiles[agent_id] = profile

            # Generate new recommendations if needed
            await self._generate_recommendations_for_agent(agent_id, profile)

            logger.info(f"Completed performance analysis for agent {agent_id}")
            return profile

        except Exception as e:
            logger.error(f"Error analyzing agent performance: {str(e)}")
            raise

    async def generate_optimization_recommendations(
        self,
        agent_id: str,
        max_recommendations: int = 5
    ) -> List[OptimizationRecommendation]:
        """Generate personalized optimization recommendations for an agent."""
        try:
            # Get agent profile
            profile = await self.analyze_agent_performance(agent_id)

            recommendations = []

            # Analyze improvement areas
            for area in profile.improvement_areas[:3]:  # Top 3 areas
                recommendation = await self._create_improvement_recommendation(
                    agent_id, area, profile
                )
                if recommendation:
                    recommendations.append(recommendation)

            # Look for automation opportunities
            automation_rec = await self._identify_automation_opportunities(agent_id, profile)
            if automation_rec:
                recommendations.append(automation_rec)

            # Technology adoption recommendations
            tech_rec = await self._generate_technology_recommendations(agent_id, profile)
            if tech_rec:
                recommendations.append(tech_rec)

            # Sort by priority and impact
            recommendations.sort(
                key=lambda x: (x.priority.value, x.impact_level.value),
                reverse=False
            )

            # Store recommendations
            for rec in recommendations[:max_recommendations]:
                self.recommendations[rec.id] = rec

            logger.info(f"Generated {len(recommendations)} recommendations for agent {agent_id}")
            return recommendations[:max_recommendations]

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise

    async def get_productivity_insights(
        self,
        agent_id: str,
        insight_types: Optional[List[str]] = None
    ) -> List[ProductivityInsight]:
        """Generate AI-powered productivity insights for an agent."""
        try:
            insights = []

            # Get performance data
            agent_data = self.performance_data.get(agent_id, [])
            if not agent_data:
                return insights

            # Trend analysis
            trend_insights = await self._analyze_performance_trends(agent_id, agent_data)
            insights.extend(trend_insights)

            # Pattern recognition
            pattern_insights = await self._identify_performance_patterns(agent_id, agent_data)
            insights.extend(pattern_insights)

            # Opportunity identification
            opportunity_insights = await self._identify_opportunities(agent_id, agent_data)
            insights.extend(opportunity_insights)

            # Risk assessment
            risk_insights = await self._assess_performance_risks(agent_id, agent_data)
            insights.extend(risk_insights)

            # Filter by requested types
            if insight_types:
                insights = [i for i in insights if i.insight_type in insight_types]

            # Store insights
            if agent_id not in self.insights:
                self.insights[agent_id] = []

            self.insights[agent_id].extend(insights)

            # Keep only recent insights (last 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            self.insights[agent_id] = [
                i for i in self.insights[agent_id]
                if i.created_date >= cutoff_date
            ]

            logger.info(f"Generated {len(insights)} insights for agent {agent_id}")
            return insights

        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            raise

    async def perform_workflow_analysis(
        self,
        agent_id: str,
        analysis_period_days: int = 7
    ) -> WorkflowAnalysis:
        """Analyze agent workflow for efficiency optimization."""
        try:
            # Get recent activity data (simulated)
            cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)

            # Time allocation analysis
            time_allocation = {
                "prospecting": 0.25,
                "lead_follow_up": 0.30,
                "client_meetings": 0.20,
                "administrative": 0.15,
                "training": 0.05,
                "other": 0.05
            }

            # Identify bottlenecks
            bottlenecks = [
                {
                    "activity": "lead_response",
                    "average_time": 45,  # minutes
                    "target_time": 15,
                    "impact": "high",
                    "frequency": "daily"
                },
                {
                    "activity": "client_communication",
                    "average_time": 120,  # minutes per client
                    "target_time": 90,
                    "impact": "medium",
                    "frequency": "weekly"
                }
            ]

            # Optimization opportunities
            optimization_opportunities = [
                {
                    "area": "Email templates",
                    "potential_time_savings": 60,  # minutes per week
                    "implementation_effort": "low",
                    "impact": "medium"
                },
                {
                    "area": "Automated follow-up sequences",
                    "potential_time_savings": 180,  # minutes per week
                    "implementation_effort": "medium",
                    "impact": "high"
                }
            ]

            # Technology usage analysis
            technology_usage = {
                "crm_system": 0.85,
                "claude_ai": 0.60,
                "email_automation": 0.40,
                "calendar_management": 0.75,
                "lead_tracking": 0.70
            }

            # Communication patterns
            communication_patterns = {
                "email_response_time": 35,  # minutes average
                "call_to_email_ratio": 0.6,
                "follow_up_frequency": 3.2,  # days average
                "peak_activity_hour": 14  # 2 PM
            }

            # Calculate efficiency score
            efficiency_score = await self._calculate_workflow_efficiency_score(
                time_allocation, bottlenecks, technology_usage
            )

            # Generate suggestions
            suggestions = await self._generate_workflow_suggestions(
                bottlenecks, optimization_opportunities, technology_usage
            )

            workflow_analysis = WorkflowAnalysis(
                agent_id=agent_id,
                analysis_date=datetime.utcnow(),
                workflow_efficiency_score=efficiency_score,
                time_allocation=time_allocation,
                bottlenecks=bottlenecks,
                optimization_opportunities=optimization_opportunities,
                technology_usage=technology_usage,
                communication_patterns=communication_patterns,
                peak_performance_hours=[9, 10, 14, 15],  # Peak hours
                suggestions=suggestions
            )

            # Store analysis
            if agent_id not in self.workflow_analyses:
                self.workflow_analyses[agent_id] = []

            self.workflow_analyses[agent_id].append(workflow_analysis)

            # Keep only recent analyses
            self.workflow_analyses[agent_id] = self.workflow_analyses[agent_id][-10:]

            logger.info(f"Completed workflow analysis for agent {agent_id}")
            return workflow_analysis

        except Exception as e:
            logger.error(f"Error performing workflow analysis: {str(e)}")
            raise

    async def implement_recommendation(
        self,
        recommendation_id: str,
        implementation_notes: Optional[str] = None
    ) -> bool:
        """Mark a recommendation as implemented and track results."""
        try:
            recommendation = self.recommendations.get(recommendation_id)
            if not recommendation:
                raise ValueError(f"Recommendation {recommendation_id} not found")

            # Update recommendation status
            recommendation.status = "in_progress"
            recommendation.completion_date = datetime.utcnow()

            # In a real implementation, this would trigger:
            # 1. Integration with training systems
            # 2. Workflow automation setup
            # 3. Technology configuration
            # 4. Performance monitoring

            logger.info(f"Marked recommendation {recommendation_id} as implemented")
            return True

        except Exception as e:
            logger.error(f"Error implementing recommendation: {str(e)}")
            raise

    async def track_recommendation_results(
        self,
        recommendation_id: str,
        improvement_data: Dict[str, float]
    ):
        """Track the results of implemented recommendations."""
        try:
            recommendation = self.recommendations.get(recommendation_id)
            if not recommendation:
                raise ValueError(f"Recommendation {recommendation_id} not found")

            # Calculate actual improvement
            baseline_metrics = improvement_data.get("baseline", {})
            current_metrics = improvement_data.get("current", {})

            if baseline_metrics and current_metrics:
                improvements = {}
                for metric, current_value in current_metrics.items():
                    baseline_value = baseline_metrics.get(metric)
                    if baseline_value and baseline_value > 0:
                        improvement_pct = ((current_value - baseline_value) / baseline_value) * 100
                        improvements[metric] = improvement_pct

                if improvements:
                    avg_improvement = statistics.mean(improvements.values())
                    recommendation.actual_improvement = avg_improvement

            # Update status
            if recommendation.actual_improvement and recommendation.actual_improvement > 5:
                recommendation.status = "completed"
            else:
                recommendation.status = "in_progress"  # Needs more time

            logger.info(f"Tracked results for recommendation {recommendation_id}")

        except Exception as e:
            logger.error(f"Error tracking recommendation results: {str(e)}")
            raise

    async def get_team_productivity_comparison(
        self,
        agent_ids: List[str],
        metric: Optional[ProductivityMetric] = None
    ) -> Dict[str, Any]:
        """Compare productivity across multiple agents."""
        try:
            comparison_data = {
                "agents": [],
                "team_averages": {},
                "rankings": {},
                "insights": []
            }

            for agent_id in agent_ids:
                agent_data = self.performance_data.get(agent_id, [])
                if not agent_data:
                    continue

                # Calculate agent metrics
                agent_metrics = {}
                for productivity_metric in ProductivityMetric:
                    metric_data = [d.value for d in agent_data if d.metric == productivity_metric]
                    if metric_data:
                        agent_metrics[productivity_metric.value] = statistics.mean(metric_data)

                comparison_data["agents"].append({
                    "agent_id": agent_id,
                    "metrics": agent_metrics,
                    "overall_score": await self._calculate_overall_score(agent_metrics, {})
                })

            # Calculate team averages
            if comparison_data["agents"]:
                all_metrics = set()
                for agent in comparison_data["agents"]:
                    all_metrics.update(agent["metrics"].keys())

                for metric_name in all_metrics:
                    metric_values = [
                        agent["metrics"].get(metric_name, 0)
                        for agent in comparison_data["agents"]
                        if metric_name in agent["metrics"]
                    ]
                    if metric_values:
                        comparison_data["team_averages"][metric_name] = statistics.mean(metric_values)

                # Generate rankings
                comparison_data["agents"].sort(key=lambda x: x["overall_score"], reverse=True)
                for i, agent in enumerate(comparison_data["agents"]):
                    comparison_data["rankings"][agent["agent_id"]] = i + 1

            return comparison_data

        except Exception as e:
            logger.error(f"Error generating team comparison: {str(e)}")
            raise

    # Helper methods

    async def _trigger_analysis_if_needed(self, agent_id: str):
        """Trigger analysis if agent has sufficient data."""
        agent_data = self.performance_data.get(agent_id, [])
        unique_metrics = len(set(d.metric for d in agent_data))

        # Trigger analysis if agent has data for at least 3 metrics
        if unique_metrics >= 3:
            await self.analyze_agent_performance(agent_id)

    async def _calculate_overall_score(
        self,
        metric_values: Dict[str, float],
        benchmark_comparisons: Dict[str, float]
    ) -> float:
        """Calculate overall productivity score."""
        if not metric_values:
            return 0.0

        # Weight different metrics
        metric_weights = {
            ProductivityMetric.CONVERSION_RATE.value: 0.25,
            ProductivityMetric.LEAD_RESPONSE_TIME.value: 0.20,
            ProductivityMetric.CLIENT_SATISFACTION.value: 0.20,
            ProductivityMetric.FOLLOW_UP_CONSISTENCY.value: 0.15,
            ProductivityMetric.DEAL_CYCLE_TIME.value: 0.10,
            ProductivityMetric.ACTIVITY_VOLUME.value: 0.10
        }

        weighted_score = 0.0
        total_weight = 0.0

        for metric_name, value in metric_values.items():
            weight = metric_weights.get(metric_name, 0.05)

            # Normalize value based on benchmark
            benchmark_ratio = benchmark_comparisons.get(metric_name, 1.0)

            # For some metrics, lower is better (response time, cycle time)
            if metric_name in ["lead_response_time", "deal_cycle_time"]:
                normalized_score = min(2.0 / benchmark_ratio, 1.0) if benchmark_ratio > 0 else 0.5
            else:
                normalized_score = min(benchmark_ratio, 2.0)  # Cap at 2x benchmark

            weighted_score += normalized_score * weight * 100
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 50.0

    async def _identify_strengths_and_improvements(
        self,
        benchmark_comparisons: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """Identify strengths and improvement areas."""
        strengths = []
        improvements = []

        for metric_name, ratio in benchmark_comparisons.items():
            metric_display_name = metric_name.replace('_', ' ').title()

            if ratio >= 1.2:  # 20% above benchmark
                strengths.append(metric_display_name)
            elif ratio <= 0.8:  # 20% below benchmark
                improvements.append(metric_display_name)

        return strengths, improvements

    async def _calculate_performance_trends(
        self,
        agent_data: List[PerformanceData]
    ) -> Dict[str, List[float]]:
        """Calculate performance trends over time."""
        trends = {}

        # Group data by metric
        metric_data = {}
        for data in agent_data:
            metric_name = data.metric.value
            if metric_name not in metric_data:
                metric_data[metric_name] = []
            metric_data[metric_name].append((data.measurement_date, data.value))

        # Calculate trends
        for metric_name, data_points in metric_data.items():
            # Sort by date
            data_points.sort(key=lambda x: x[0])

            # Get last 7 data points for trend
            recent_values = [value for _, value in data_points[-7:]]
            trends[metric_name] = recent_values

        return trends

    async def _generate_recommendations_for_agent(
        self,
        agent_id: str,
        profile: AgentProductivityProfile
    ):
        """Generate recommendations based on agent profile."""
        try:
            # Check if agent already has recent recommendations
            existing_recs = [
                rec for rec in self.recommendations.values()
                if rec.agent_id == agent_id and
                rec.created_date > datetime.utcnow() - timedelta(days=7)
            ]

            if len(existing_recs) >= 3:  # Don't overwhelm with too many recommendations
                return

            # Generate new recommendations
            await self.generate_optimization_recommendations(agent_id)

        except Exception as e:
            logger.error(f"Error generating recommendations for agent: {str(e)}")

    async def _create_improvement_recommendation(
        self,
        agent_id: str,
        improvement_area: str,
        profile: AgentProductivityProfile
    ) -> Optional[OptimizationRecommendation]:
        """Create a recommendation for a specific improvement area."""
        try:
            area_lower = improvement_area.lower()

            if "response time" in area_lower:
                return OptimizationRecommendation(
                    id=f"rec_{uuid.uuid4().hex[:8]}",
                    agent_id=agent_id,
                    optimization_type=OptimizationType.WORKFLOW_IMPROVEMENT,
                    priority=Priority.HIGH,
                    impact_level=ImpactLevel.SIGNIFICANT,
                    title="Improve Lead Response Time",
                    description="Reduce average response time to new leads through automation and process optimization",
                    problem_analysis=f"Current response time is {profile.benchmark_comparisons.get('lead_response_time', 1.0):.1f}x the team average",
                    recommended_actions=[
                        "Set up instant lead notifications on mobile device",
                        "Create response templates for common inquiries",
                        "Use Claude AI for initial lead qualification",
                        "Implement automated acknowledgment emails"
                    ],
                    expected_improvement="50-70% reduction in response time",
                    implementation_effort="Medium - requires setup and habit formation",
                    time_to_impact="1-2 weeks",
                    success_metrics=["Average response time", "Lead engagement rate"],
                    related_metrics=[ProductivityMetric.LEAD_RESPONSE_TIME, ProductivityMetric.CONVERSION_RATE],
                    automation_potential=0.8,
                    roi_estimate="$2,000-5,000 additional monthly revenue",
                    due_date=datetime.utcnow() + timedelta(days=14)
                )

            elif "conversion" in area_lower:
                return OptimizationRecommendation(
                    id=f"rec_{uuid.uuid4().hex[:8]}",
                    agent_id=agent_id,
                    optimization_type=OptimizationType.SKILL_DEVELOPMENT,
                    priority=Priority.CRITICAL,
                    impact_level=ImpactLevel.TRANSFORMATIONAL,
                    title="Enhance Lead Conversion Skills",
                    description="Improve conversion rate through advanced sales techniques and client relationship building",
                    problem_analysis=f"Current conversion rate is {profile.benchmark_comparisons.get('conversion_rate', 1.0):.1f}x the team average",
                    recommended_actions=[
                        "Complete advanced objection handling training",
                        "Practice consultative selling techniques",
                        "Implement structured follow-up sequences",
                        "Use Claude AI for personalized client insights"
                    ],
                    expected_improvement="25-40% increase in conversion rate",
                    implementation_effort="High - requires training and practice",
                    time_to_impact="4-6 weeks",
                    success_metrics=["Conversion rate", "Average deal value", "Client satisfaction"],
                    related_metrics=[ProductivityMetric.CONVERSION_RATE, ProductivityMetric.CLIENT_SATISFACTION],
                    automation_potential=0.3,
                    roi_estimate="$10,000-20,000 additional monthly revenue",
                    due_date=datetime.utcnow() + timedelta(days=30)
                )

            elif "follow" in area_lower:
                return OptimizationRecommendation(
                    id=f"rec_{uuid.uuid4().hex[:8]}",
                    agent_id=agent_id,
                    optimization_type=OptimizationType.AUTOMATION_OPPORTUNITY,
                    priority=Priority.MEDIUM,
                    impact_level=ImpactLevel.MODERATE,
                    title="Automate Follow-up Processes",
                    description="Improve follow-up consistency through automation and systematic tracking",
                    problem_analysis=f"Current follow-up consistency is {profile.benchmark_comparisons.get('follow_up_consistency', 1.0):.1f}x the team average",
                    recommended_actions=[
                        "Set up automated follow-up email sequences",
                        "Use CRM task automation for follow-up reminders",
                        "Create follow-up templates for different scenarios",
                        "Implement lead scoring for prioritization"
                    ],
                    expected_improvement="40-60% improvement in follow-up consistency",
                    implementation_effort="Medium - requires system setup",
                    time_to_impact="2-3 weeks",
                    success_metrics=["Follow-up completion rate", "Lead engagement", "Time to close"],
                    related_metrics=[ProductivityMetric.FOLLOW_UP_CONSISTENCY, ProductivityMetric.DEAL_CYCLE_TIME],
                    automation_potential=0.9,
                    roi_estimate="$3,000-7,000 additional monthly revenue",
                    due_date=datetime.utcnow() + timedelta(days=21)
                )

            return None

        except Exception as e:
            logger.error(f"Error creating improvement recommendation: {str(e)}")
            return None

    async def _identify_automation_opportunities(
        self,
        agent_id: str,
        profile: AgentProductivityProfile
    ) -> Optional[OptimizationRecommendation]:
        """Identify automation opportunities for the agent."""
        try:
            # Check if agent has low technology adoption
            tech_adoption = profile.benchmark_comparisons.get('technology_adoption', 1.0)

            if tech_adoption < 0.8:  # Below 80% of benchmark
                return OptimizationRecommendation(
                    id=f"rec_{uuid.uuid4().hex[:8]}",
                    agent_id=agent_id,
                    optimization_type=OptimizationType.TECHNOLOGY_UTILIZATION,
                    priority=Priority.HIGH,
                    impact_level=ImpactLevel.SIGNIFICANT,
                    title="Increase Technology Utilization",
                    description="Leverage available technology tools to automate routine tasks and improve efficiency",
                    problem_analysis="Technology adoption is below team average, missing automation opportunities",
                    recommended_actions=[
                        "Complete technology training modules",
                        "Set up email automation workflows",
                        "Use Claude AI for lead insights and communication",
                        "Implement calendar automation and scheduling tools",
                        "Configure CRM automation rules"
                    ],
                    expected_improvement="30-50% time savings on routine tasks",
                    implementation_effort="Medium - requires learning and setup",
                    time_to_impact="2-4 weeks",
                    success_metrics=["Technology adoption score", "Time spent on admin tasks", "Activity volume"],
                    related_metrics=[ProductivityMetric.TECHNOLOGY_ADOPTION, ProductivityMetric.TIME_MANAGEMENT],
                    automation_potential=0.95,
                    roi_estimate="$5,000-10,000 value through time savings",
                    due_date=datetime.utcnow() + timedelta(days=28)
                )

            return None

        except Exception as e:
            logger.error(f"Error identifying automation opportunities: {str(e)}")
            return None

    async def _generate_technology_recommendations(
        self,
        agent_id: str,
        profile: AgentProductivityProfile
    ) -> Optional[OptimizationRecommendation]:
        """Generate technology-specific recommendations."""
        # This would analyze technology usage patterns and recommend improvements
        # For now, return None as this is handled by automation opportunities
        return None

    async def _analyze_performance_trends(
        self,
        agent_id: str,
        agent_data: List[PerformanceData]
    ) -> List[ProductivityInsight]:
        """Analyze performance trends for insights."""
        insights = []

        try:
            # Group data by metric
            metric_trends = {}
            for data in agent_data:
                metric_name = data.metric.value
                if metric_name not in metric_trends:
                    metric_trends[metric_name] = []
                metric_trends[metric_name].append((data.measurement_date, data.value))

            # Analyze trends
            for metric_name, data_points in metric_trends.items():
                if len(data_points) < 3:
                    continue

                # Sort by date
                data_points.sort(key=lambda x: x[0])
                values = [value for _, value in data_points]

                # Simple trend analysis
                if len(values) >= 3:
                    recent_avg = statistics.mean(values[-3:])
                    earlier_avg = statistics.mean(values[:-3]) if len(values) > 3 else values[0]

                    if recent_avg > earlier_avg * 1.1:  # 10% improvement
                        insights.append(ProductivityInsight(
                            id=f"trend_{uuid.uuid4().hex[:8]}",
                            agent_id=agent_id,
                            insight_type="trend",
                            title=f"Improving {metric_name.replace('_', ' ').title()}",
                            description=f"{metric_name.replace('_', ' ').title()} has improved by {((recent_avg - earlier_avg) / earlier_avg * 100):.1f}% recently",
                            supporting_data={"recent_average": recent_avg, "earlier_average": earlier_avg},
                            confidence_level=0.8,
                            actionable=True
                        ))
                    elif recent_avg < earlier_avg * 0.9:  # 10% decline
                        insights.append(ProductivityInsight(
                            id=f"trend_{uuid.uuid4().hex[:8]}",
                            agent_id=agent_id,
                            insight_type="risk",
                            title=f"Declining {metric_name.replace('_', ' ').title()}",
                            description=f"{metric_name.replace('_', ' ').title()} has declined by {((earlier_avg - recent_avg) / earlier_avg * 100):.1f}% recently",
                            supporting_data={"recent_average": recent_avg, "earlier_average": earlier_avg},
                            confidence_level=0.8,
                            actionable=True
                        ))

        except Exception as e:
            logger.error(f"Error analyzing performance trends: {str(e)}")

        return insights

    async def _identify_performance_patterns(
        self,
        agent_id: str,
        agent_data: List[PerformanceData]
    ) -> List[ProductivityInsight]:
        """Identify patterns in performance data."""
        insights = []

        try:
            # Look for day-of-week patterns
            weekday_performance = {}
            for data in agent_data:
                weekday = data.measurement_date.strftime('%A')
                if weekday not in weekday_performance:
                    weekday_performance[weekday] = []
                weekday_performance[weekday].append(data.value)

            # Find best and worst performance days
            if weekday_performance:
                daily_averages = {
                    day: statistics.mean(values)
                    for day, values in weekday_performance.items()
                }

                best_day = max(daily_averages, key=daily_averages.get)
                worst_day = min(daily_averages, key=daily_averages.get)

                insights.append(ProductivityInsight(
                    id=f"pattern_{uuid.uuid4().hex[:8]}",
                    agent_id=agent_id,
                    insight_type="pattern",
                    title="Weekly Performance Pattern",
                    description=f"Performance is typically highest on {best_day} and lowest on {worst_day}",
                    supporting_data=daily_averages,
                    confidence_level=0.7,
                    actionable=True
                ))

        except Exception as e:
            logger.error(f"Error identifying performance patterns: {str(e)}")

        return insights

    async def _identify_opportunities(
        self,
        agent_id: str,
        agent_data: List[PerformanceData]
    ) -> List[ProductivityInsight]:
        """Identify optimization opportunities."""
        insights = []

        try:
            # Look for metrics significantly below benchmark
            for data in agent_data:
                if data.benchmark_value and data.value < data.benchmark_value * 0.7:  # 30% below benchmark
                    insights.append(ProductivityInsight(
                        id=f"opportunity_{uuid.uuid4().hex[:8]}",
                        agent_id=agent_id,
                        insight_type="opportunity",
                        title=f"Improvement Opportunity: {data.metric.value.replace('_', ' ').title()}",
                        description=f"Current {data.metric.value.replace('_', ' ')} is 30% below team average, significant improvement potential",
                        supporting_data={"current_value": data.value, "benchmark": data.benchmark_value},
                        confidence_level=0.9,
                        actionable=True
                    ))

        except Exception as e:
            logger.error(f"Error identifying opportunities: {str(e)}")

        return insights

    async def _assess_performance_risks(
        self,
        agent_id: str,
        agent_data: List[PerformanceData]
    ) -> List[ProductivityInsight]:
        """Assess performance risks."""
        insights = []

        try:
            # Look for concerning trends or values
            recent_data = [d for d in agent_data if d.measurement_date > datetime.utcnow() - timedelta(days=7)]

            for data in recent_data:
                if data.benchmark_value and data.value < data.benchmark_value * 0.5:  # 50% below benchmark
                    insights.append(ProductivityInsight(
                        id=f"risk_{uuid.uuid4().hex[:8]}",
                        agent_id=agent_id,
                        insight_type="risk",
                        title=f"Performance Risk: {data.metric.value.replace('_', ' ').title()}",
                        description=f"Current {data.metric.value.replace('_', ' ')} is significantly below benchmark and requires immediate attention",
                        supporting_data={"current_value": data.value, "benchmark": data.benchmark_value},
                        confidence_level=0.95,
                        actionable=True
                    ))

        except Exception as e:
            logger.error(f"Error assessing performance risks: {str(e)}")

        return insights

    async def _calculate_workflow_efficiency_score(
        self,
        time_allocation: Dict[str, float],
        bottlenecks: List[Dict[str, Any]],
        technology_usage: Dict[str, float]
    ) -> float:
        """Calculate workflow efficiency score."""
        try:
            # Base score from time allocation (higher productive activities = better score)
            productive_time = time_allocation.get("prospecting", 0) + time_allocation.get("client_meetings", 0)
            allocation_score = min(productive_time * 2, 1.0) * 40  # Max 40 points

            # Technology usage score
            avg_tech_usage = statistics.mean(technology_usage.values())
            tech_score = avg_tech_usage * 30  # Max 30 points

            # Bottleneck penalty
            bottleneck_penalty = min(len(bottlenecks) * 5, 20)  # Max 20 point penalty

            # Calculate final score
            efficiency_score = max(allocation_score + tech_score - bottleneck_penalty, 0)
            return min(efficiency_score, 100)

        except Exception as e:
            logger.error(f"Error calculating workflow efficiency: {str(e)}")
            return 50.0

    async def _generate_workflow_suggestions(
        self,
        bottlenecks: List[Dict[str, Any]],
        optimization_opportunities: List[Dict[str, Any]],
        technology_usage: Dict[str, float]
    ) -> List[str]:
        """Generate workflow optimization suggestions."""
        suggestions = []

        try:
            # Address bottlenecks
            for bottleneck in bottlenecks:
                if bottleneck["activity"] == "lead_response":
                    suggestions.append("Set up mobile notifications for immediate lead alerts")
                    suggestions.append("Create quick response templates for common inquiries")
                elif bottleneck["activity"] == "client_communication":
                    suggestions.append("Batch similar communications to improve efficiency")
                    suggestions.append("Use video calls instead of lengthy email exchanges")

            # Technology improvement suggestions
            low_usage_tools = [tool for tool, usage in technology_usage.items() if usage < 0.7]
            if low_usage_tools:
                suggestions.append(f"Increase usage of {', '.join(low_usage_tools)} for better efficiency")

            # General optimization
            suggestions.extend([
                "Block calendar time for high-focus activities like prospecting",
                "Use AI assistance for routine communications and analysis",
                "Implement weekly workflow review sessions"
            ])

        except Exception as e:
            logger.error(f"Error generating workflow suggestions: {str(e)}")

        return suggestions


# Global service instance
productivity_optimizer = AgentProductivityOptimizer()


# Convenience functions for easy import
async def record_agent_performance(
    agent_id: str,
    metric: ProductivityMetric,
    value: float,
    period: str = "daily",
    context: Optional[Dict[str, Any]] = None
):
    """Record performance data for an agent."""
    await productivity_optimizer.record_performance_data(agent_id, metric, value, period, context)


async def analyze_agent_productivity(
    agent_id: str,
    analysis_period_days: int = 30
) -> AgentProductivityProfile:
    """Analyze agent productivity and get profile."""
    return await productivity_optimizer.analyze_agent_performance(agent_id, analysis_period_days)


async def get_optimization_recommendations(
    agent_id: str,
    max_recommendations: int = 5
) -> List[OptimizationRecommendation]:
    """Get optimization recommendations for an agent."""
    return await productivity_optimizer.generate_optimization_recommendations(agent_id, max_recommendations)


async def get_workflow_analysis(
    agent_id: str,
    analysis_period_days: int = 7
) -> WorkflowAnalysis:
    """Get workflow analysis for an agent."""
    return await productivity_optimizer.perform_workflow_analysis(agent_id, analysis_period_days)


async def get_productivity_insights(
    agent_id: str,
    insight_types: Optional[List[str]] = None
) -> List[ProductivityInsight]:
    """Get productivity insights for an agent."""
    return await productivity_optimizer.get_productivity_insights(agent_id, insight_types)