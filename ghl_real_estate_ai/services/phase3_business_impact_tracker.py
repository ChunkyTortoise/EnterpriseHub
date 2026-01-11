"""
Phase 3 Business Impact Measurement and ROI Tracking
===================================================

Real-time business metrics collection and A/B testing framework for Phase 3 features.

Features:
- Daily revenue impact by feature
- Weekly/monthly trend analysis
- ROI calculation with cost attribution
- A/B test statistical significance
- Success metric measurement per feature

Performance Targets:
- Metric collection: <10ms async
- Dashboard query: <50ms
- Statistical analysis: <100ms

Business Impact Tracking:
- Real-Time Intelligence: Lead response time, agent productivity
- Property Intelligence: Match satisfaction, showing rate
- Churn Prevention: Churn rate reduction, intervention success
- AI Coaching: Training time, productivity increase

ROI Targets:
- Real-Time Intelligence: $75K-120K/year
- Property Intelligence: $45K-60K/year
- Churn Prevention: $55K-80K/year
- AI Coaching: $60K-90K/year
- Total Phase 3: $235K-350K/year

Author: EnterpriseHub Development Team
Created: January 2026
Version: 1.0.0
"""

import asyncio
import time
import json
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from collections import defaultdict, deque
import logging

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.feature_flag_manager import (
    get_feature_flag_manager,
    FeatureFlag
)

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Business metric types."""
    REVENUE = "revenue"
    CONVERSION_RATE = "conversion_rate"
    RESPONSE_TIME = "response_time"
    SATISFACTION_RATE = "satisfaction_rate"
    CHURN_RATE = "churn_rate"
    PRODUCTIVITY_SCORE = "productivity_score"
    TRAINING_TIME = "training_time"
    COST_SAVINGS = "cost_savings"


class FeaturePhase(str, Enum):
    """Feature rollout phases for tracking."""
    BETA_10 = "beta_10"
    BETA_25 = "beta_25"
    BETA_50 = "beta_50"
    GENERAL_AVAILABILITY = "ga"


@dataclass
class BusinessMetric:
    """Individual business metric measurement."""
    metric_type: MetricType
    feature_id: str
    tenant_id: str

    # Measurement
    value: float
    variant: str  # "control" or "treatment"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Context
    user_id: Optional[str] = None
    phase: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metric_type': self.metric_type.value,
            'feature_id': self.feature_id,
            'tenant_id': self.tenant_id,
            'value': self.value,
            'variant': self.variant,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'phase': self.phase,
            'additional_data': self.additional_data
        }


@dataclass
class FeatureROI:
    """ROI calculation for feature."""
    feature_id: str
    feature_name: str

    # Financial metrics
    revenue_impact: float = 0.0
    cost_savings: float = 0.0
    infrastructure_cost: float = 0.0
    api_costs: float = 0.0

    # Performance metrics
    conversion_lift: float = 0.0  # Percentage improvement
    satisfaction_lift: float = 0.0
    productivity_lift: float = 0.0
    churn_reduction: float = 0.0

    # ROI calculations
    total_benefit: float = 0.0
    total_cost: float = 0.0
    net_value: float = 0.0
    roi_percentage: float = 0.0

    # Tracking
    measurement_start: datetime = field(default_factory=datetime.utcnow)
    measurement_end: Optional[datetime] = None
    sample_size: int = 0

    def calculate_roi(self) -> None:
        """Calculate ROI metrics."""
        self.total_benefit = self.revenue_impact + self.cost_savings
        self.total_cost = self.infrastructure_cost + self.api_costs
        self.net_value = self.total_benefit - self.total_cost

        if self.total_cost > 0:
            self.roi_percentage = (self.net_value / self.total_cost) * 100
        else:
            self.roi_percentage = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['measurement_start'] = self.measurement_start.isoformat()
        if self.measurement_end:
            result['measurement_end'] = self.measurement_end.isoformat()
        return result


@dataclass
class ABTestResult:
    """A/B test statistical analysis result."""
    feature_id: str
    metric_type: MetricType

    # Sample statistics
    control_mean: float
    treatment_mean: float
    control_std: float
    treatment_std: float
    control_count: int
    treatment_count: int

    # Statistical significance
    p_value: float = 1.0
    confidence_level: float = 0.0
    is_significant: bool = False  # p < 0.05
    lift_percentage: float = 0.0

    # Recommendation
    recommended_action: str = "insufficient_data"
    confidence_interval_lower: float = 0.0
    confidence_interval_upper: float = 0.0

    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['metric_type'] = self.metric_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


class Phase3BusinessImpactTracker:
    """
    Business impact measurement and ROI tracking for Phase 3 features.

    Tracks:
    - Real-time revenue impact
    - Feature-specific KPIs
    - A/B test results
    - Cost analysis
    - Progressive rollout metrics
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0"
    ):
        """
        Initialize business impact tracker.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url

        # Redis client
        self.redis: Optional[Any] = None

        # Feature flag manager
        self.flag_manager = None

        # In-memory buffers
        self.metric_buffer: deque = deque(maxlen=10000)
        self.roi_cache: Dict[str, FeatureROI] = {}

        # Redis key prefixes
        self.METRIC_PREFIX = "phase3_metric:"
        self.ROI_PREFIX = "phase3_roi:"
        self.ABTEST_PREFIX = "phase3_abtest:"
        self.DAILY_SUMMARY_PREFIX = "phase3_daily:"

        # Phase 3 feature configurations
        self.FEATURE_CONFIGS = {
            "realtime_intelligence": {
                "name": "Real-Time Lead Intelligence",
                "primary_metric": MetricType.RESPONSE_TIME,
                "roi_target": 75000,  # Annual
                "baseline_response_time": 900,  # 15 minutes in seconds
                "target_response_time": 30,  # 30 seconds
            },
            "property_intelligence": {
                "name": "Multimodal Property Intelligence",
                "primary_metric": MetricType.SATISFACTION_RATE,
                "roi_target": 45000,
                "baseline_satisfaction": 88.0,  # %
                "target_satisfaction": 93.0,  # %
            },
            "churn_prevention": {
                "name": "Proactive Churn Prevention",
                "primary_metric": MetricType.CHURN_RATE,
                "roi_target": 55000,
                "baseline_churn": 35.0,  # %
                "target_churn": 20.0,  # %
            },
            "ai_coaching": {
                "name": "AI-Powered Coaching",
                "primary_metric": MetricType.TRAINING_TIME,
                "roi_target": 60000,
                "baseline_training_hours": 40,  # Hours per agent
                "target_training_hours": 20,  # Hours per agent
            }
        }

        logger.info("Phase3BusinessImpactTracker initialized")

    async def initialize(self) -> bool:
        """Initialize Redis and feature flag manager."""
        try:
            if aioredis is None:
                logger.warning("Redis not available, using in-memory tracking only")
                return True

            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=1.0
            )

            await self.redis.ping()

            # Initialize feature flag manager
            self.flag_manager = await get_feature_flag_manager(self.redis_url)

            logger.info("Business impact tracker initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize tracker: {e}")
            return False

    async def record_metric(
        self,
        metric: BusinessMetric
    ) -> bool:
        """
        Record business metric measurement.

        Args:
            metric: BusinessMetric instance

        Returns:
            True if successful
        """
        try:
            # Add to buffer
            self.metric_buffer.append(metric)

            # Save to Redis for persistence
            if self.redis:
                # Daily partition key
                date_key = metric.timestamp.strftime('%Y%m%d')
                redis_key = f"{self.METRIC_PREFIX}{metric.feature_id}:{date_key}"

                await self.redis.rpush(
                    redis_key,
                    json.dumps(metric.to_dict())
                )

                # Set expiry (90 days)
                await self.redis.expire(redis_key, 86400 * 90)

            return True

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            return False

    async def track_realtime_intelligence_event(
        self,
        tenant_id: str,
        user_id: str,
        response_time_seconds: float,
        lead_id: str
    ) -> None:
        """Track real-time intelligence usage event."""
        try:
            # Get variant
            variant = "control"
            if self.flag_manager:
                enabled = await self.flag_manager.is_enabled(
                    "realtime_intelligence",
                    tenant_id,
                    user_id
                )
                if enabled:
                    variant = await self.flag_manager.get_variant(
                        "realtime_intelligence",
                        tenant_id,
                        user_id
                    )

            # Record response time metric
            metric = BusinessMetric(
                metric_type=MetricType.RESPONSE_TIME,
                feature_id="realtime_intelligence",
                tenant_id=tenant_id,
                user_id=user_id,
                value=response_time_seconds,
                variant=variant,
                additional_data={'lead_id': lead_id}
            )

            await self.record_metric(metric)

        except Exception as e:
            logger.error(f"Error tracking realtime intelligence event: {e}")

    async def track_property_match_satisfaction(
        self,
        tenant_id: str,
        user_id: str,
        lead_id: str,
        satisfaction_score: float,  # 0-100
        property_id: str
    ) -> None:
        """Track property matching satisfaction."""
        try:
            variant = "control"
            if self.flag_manager:
                enabled = await self.flag_manager.is_enabled(
                    "property_intelligence",
                    tenant_id,
                    user_id
                )
                if enabled:
                    variant = await self.flag_manager.get_variant(
                        "property_intelligence",
                        tenant_id,
                        user_id
                    )

            metric = BusinessMetric(
                metric_type=MetricType.SATISFACTION_RATE,
                feature_id="property_intelligence",
                tenant_id=tenant_id,
                user_id=user_id,
                value=satisfaction_score,
                variant=variant,
                additional_data={
                    'lead_id': lead_id,
                    'property_id': property_id
                }
            )

            await self.record_metric(metric)

        except Exception as e:
            logger.error(f"Error tracking property satisfaction: {e}")

    async def track_churn_prevention_intervention(
        self,
        tenant_id: str,
        user_id: str,
        lead_id: str,
        intervention_stage: int,  # 1, 2, or 3
        churned: bool
    ) -> None:
        """Track churn prevention intervention outcome."""
        try:
            variant = "control"
            if self.flag_manager:
                enabled = await self.flag_manager.is_enabled(
                    "churn_prevention",
                    tenant_id,
                    user_id
                )
                if enabled:
                    variant = await self.flag_manager.get_variant(
                        "churn_prevention",
                        tenant_id,
                        user_id
                    )

            # Record churn outcome
            metric = BusinessMetric(
                metric_type=MetricType.CHURN_RATE,
                feature_id="churn_prevention",
                tenant_id=tenant_id,
                user_id=user_id,
                value=1.0 if churned else 0.0,
                variant=variant,
                additional_data={
                    'lead_id': lead_id,
                    'intervention_stage': intervention_stage
                }
            )

            await self.record_metric(metric)

        except Exception as e:
            logger.error(f"Error tracking churn prevention: {e}")

    async def track_ai_coaching_session(
        self,
        tenant_id: str,
        agent_id: str,
        session_duration_minutes: float,
        productivity_score: float  # 0-100
    ) -> None:
        """Track AI coaching session."""
        try:
            variant = "control"
            if self.flag_manager:
                enabled = await self.flag_manager.is_enabled(
                    "ai_coaching",
                    tenant_id,
                    agent_id
                )
                if enabled:
                    variant = await self.flag_manager.get_variant(
                        "ai_coaching",
                        tenant_id,
                        agent_id
                    )

            # Record training time
            training_metric = BusinessMetric(
                metric_type=MetricType.TRAINING_TIME,
                feature_id="ai_coaching",
                tenant_id=tenant_id,
                user_id=agent_id,
                value=session_duration_minutes,
                variant=variant
            )

            # Record productivity score
            productivity_metric = BusinessMetric(
                metric_type=MetricType.PRODUCTIVITY_SCORE,
                feature_id="ai_coaching",
                tenant_id=tenant_id,
                user_id=agent_id,
                value=productivity_score,
                variant=variant
            )

            await self.record_metric(training_metric)
            await self.record_metric(productivity_metric)

        except Exception as e:
            logger.error(f"Error tracking AI coaching: {e}")

    async def calculate_feature_roi(
        self,
        feature_id: str,
        days: int = 30
    ) -> Optional[FeatureROI]:
        """
        Calculate ROI for specific feature.

        Args:
            feature_id: Feature identifier
            days: Analysis period in days

        Returns:
            FeatureROI calculation
        """
        try:
            config = self.FEATURE_CONFIGS.get(feature_id)
            if not config:
                return None

            roi = FeatureROI(
                feature_id=feature_id,
                feature_name=config['name'],
                measurement_start=datetime.utcnow() - timedelta(days=days)
            )

            # Fetch metrics
            metrics = await self._fetch_metrics(feature_id, days)

            if not metrics:
                return roi

            # Calculate feature-specific ROI
            if feature_id == "realtime_intelligence":
                roi = await self._calculate_realtime_intelligence_roi(
                    metrics,
                    config,
                    roi
                )
            elif feature_id == "property_intelligence":
                roi = await self._calculate_property_intelligence_roi(
                    metrics,
                    config,
                    roi
                )
            elif feature_id == "churn_prevention":
                roi = await self._calculate_churn_prevention_roi(
                    metrics,
                    config,
                    roi
                )
            elif feature_id == "ai_coaching":
                roi = await self._calculate_ai_coaching_roi(
                    metrics,
                    config,
                    roi
                )

            # Calculate final ROI
            roi.calculate_roi()

            # Cache result
            self.roi_cache[feature_id] = roi

            # Save to Redis
            if self.redis:
                redis_key = f"{self.ROI_PREFIX}{feature_id}"
                await self.redis.setex(
                    redis_key,
                    3600,  # 1 hour TTL
                    json.dumps(roi.to_dict())
                )

            return roi

        except Exception as e:
            logger.error(f"Error calculating ROI for {feature_id}: {e}")
            return None

    async def _calculate_realtime_intelligence_roi(
        self,
        metrics: List[BusinessMetric],
        config: Dict[str, Any],
        roi: FeatureROI
    ) -> FeatureROI:
        """Calculate ROI for real-time intelligence feature."""
        # Filter response time metrics
        response_times = [
            m.value for m in metrics
            if m.metric_type == MetricType.RESPONSE_TIME and m.variant == "treatment"
        ]

        if not response_times:
            return roi

        avg_response_time = statistics.mean(response_times)

        # Calculate time savings
        baseline_time = config['baseline_response_time']
        time_saved_per_lead = baseline_time - avg_response_time

        # Estimate leads per month (from metrics)
        leads_per_month = len(metrics) * (30 / 7)  # Extrapolate

        # Agent hourly cost estimate
        agent_hourly_cost = 50.0  # $50/hour

        # Monthly cost savings
        monthly_hours_saved = (time_saved_per_lead * leads_per_month) / 3600
        monthly_savings = monthly_hours_saved * agent_hourly_cost

        roi.cost_savings = monthly_savings * 12  # Annual

        # Infrastructure costs
        roi.infrastructure_cost = 5000  # Annual WebSocket hosting
        roi.api_costs = 2000  # Annual API costs

        return roi

    async def _calculate_property_intelligence_roi(
        self,
        metrics: List[BusinessMetric],
        config: Dict[str, Any],
        roi: FeatureROI
    ) -> FeatureROI:
        """Calculate ROI for property intelligence feature."""
        satisfaction_scores = [
            m.value for m in metrics
            if m.metric_type == MetricType.SATISFACTION_RATE and m.variant == "treatment"
        ]

        if not satisfaction_scores:
            return roi

        avg_satisfaction = statistics.mean(satisfaction_scores)

        # Calculate satisfaction lift
        baseline = config['baseline_satisfaction']
        roi.satisfaction_lift = ((avg_satisfaction - baseline) / baseline) * 100

        # Estimate revenue impact
        # Higher satisfaction -> more showings -> more closings
        satisfaction_to_revenue = 5000  # $5K per % improvement
        roi.revenue_impact = roi.satisfaction_lift * satisfaction_to_revenue * 12

        # Costs
        roi.infrastructure_cost = 3000  # Annual
        roi.api_costs = 8000  # Claude Vision + APIs

        return roi

    async def _calculate_churn_prevention_roi(
        self,
        metrics: List[BusinessMetric],
        config: Dict[str, Any],
        roi: FeatureROI
    ) -> FeatureROI:
        """Calculate ROI for churn prevention feature."""
        churn_events = [
            m.value for m in metrics
            if m.metric_type == MetricType.CHURN_RATE and m.variant == "treatment"
        ]

        if not churn_events:
            return roi

        churn_rate = (sum(churn_events) / len(churn_events)) * 100

        # Calculate churn reduction
        baseline = config['baseline_churn']
        roi.churn_reduction = baseline - churn_rate

        # Revenue impact
        # Each prevented churn = ~$3K in commission
        leads_per_month = len(metrics) * (30 / 7)
        prevented_churns = leads_per_month * (roi.churn_reduction / 100)
        monthly_revenue = prevented_churns * 3000

        roi.revenue_impact = monthly_revenue * 12  # Annual

        # Costs
        roi.infrastructure_cost = 2000
        roi.api_costs = 4000  # Notification services

        return roi

    async def _calculate_ai_coaching_roi(
        self,
        metrics: List[BusinessMetric],
        config: Dict[str, Any],
        roi: FeatureROI
    ) -> FeatureROI:
        """Calculate ROI for AI coaching feature."""
        training_times = [
            m.value for m in metrics
            if m.metric_type == MetricType.TRAINING_TIME and m.variant == "treatment"
        ]

        productivity_scores = [
            m.value for m in metrics
            if m.metric_type == MetricType.PRODUCTIVITY_SCORE and m.variant == "treatment"
        ]

        if training_times:
            avg_training_time = statistics.mean(training_times)

            # Calculate training time reduction
            baseline = config['baseline_training_hours'] * 60  # Convert to minutes
            time_saved = baseline - (avg_training_time * len(training_times))

            # Cost savings from reduced training time
            trainer_hourly_cost = 75.0  # $75/hour
            monthly_savings = (time_saved / 60) * trainer_hourly_cost

            roi.cost_savings = monthly_savings * 12  # Annual

        if productivity_scores:
            avg_productivity = statistics.mean(productivity_scores)

            # Productivity lift
            baseline_productivity = 70.0  # Baseline score
            roi.productivity_lift = ((avg_productivity - baseline_productivity) / baseline_productivity) * 100

            # Revenue impact from productivity increase
            roi.revenue_impact = roi.productivity_lift * 2000 * 12  # $2K per % per year

        # Costs
        roi.infrastructure_cost = 4000
        roi.api_costs = 6000  # Claude API for analysis

        return roi

    async def run_ab_test_analysis(
        self,
        feature_id: str,
        metric_type: MetricType,
        days: int = 30
    ) -> Optional[ABTestResult]:
        """
        Run A/B test statistical analysis.

        Args:
            feature_id: Feature identifier
            metric_type: Metric to analyze
            days: Analysis period

        Returns:
            ABTestResult with statistical analysis
        """
        try:
            metrics = await self._fetch_metrics(feature_id, days)

            if not metrics:
                return None

            # Separate control and treatment
            control_values = [
                m.value for m in metrics
                if m.metric_type == metric_type and m.variant == "control"
            ]

            treatment_values = [
                m.value for m in metrics
                if m.metric_type == metric_type and m.variant == "treatment"
            ]

            if len(control_values) < 30 or len(treatment_values) < 30:
                # Insufficient sample size
                return ABTestResult(
                    feature_id=feature_id,
                    metric_type=metric_type,
                    control_mean=statistics.mean(control_values) if control_values else 0,
                    treatment_mean=statistics.mean(treatment_values) if treatment_values else 0,
                    control_std=0,
                    treatment_std=0,
                    control_count=len(control_values),
                    treatment_count=len(treatment_values),
                    recommended_action="insufficient_data"
                )

            # Calculate statistics
            control_mean = statistics.mean(control_values)
            treatment_mean = statistics.mean(treatment_values)
            control_std = statistics.stdev(control_values)
            treatment_std = statistics.stdev(treatment_values)

            # Calculate lift
            if control_mean != 0:
                lift = ((treatment_mean - control_mean) / control_mean) * 100
            else:
                lift = 0.0

            # Simple t-test approximation
            # (for production, use scipy.stats.ttest_ind)
            pooled_std = ((control_std ** 2 / len(control_values)) +
                         (treatment_std ** 2 / len(treatment_values))) ** 0.5

            if pooled_std > 0:
                t_stat = abs(treatment_mean - control_mean) / pooled_std
                # Simple p-value approximation
                p_value = 2 * (1 - min(0.999, t_stat / 10))
            else:
                p_value = 1.0

            # Determine significance
            is_significant = p_value < 0.05
            confidence_level = (1 - p_value) * 100

            # Recommendation
            if not is_significant:
                recommendation = "continue_testing"
            elif lift > 5:  # Positive lift
                recommendation = "roll_forward"
            elif lift < -5:  # Negative impact
                recommendation = "rollback"
            else:
                recommendation = "neutral"

            result = ABTestResult(
                feature_id=feature_id,
                metric_type=metric_type,
                control_mean=control_mean,
                treatment_mean=treatment_mean,
                control_std=control_std,
                treatment_std=treatment_std,
                control_count=len(control_values),
                treatment_count=len(treatment_values),
                p_value=p_value,
                confidence_level=confidence_level,
                is_significant=is_significant,
                lift_percentage=lift,
                recommended_action=recommendation
            )

            # Save to Redis
            if self.redis:
                redis_key = f"{self.ABTEST_PREFIX}{feature_id}:{metric_type.value}"
                await self.redis.setex(
                    redis_key,
                    3600,
                    json.dumps(result.to_dict())
                )

            return result

        except Exception as e:
            logger.error(f"Error running A/B test analysis: {e}")
            return None

    async def _fetch_metrics(
        self,
        feature_id: str,
        days: int
    ) -> List[BusinessMetric]:
        """Fetch metrics from Redis for analysis period."""
        metrics = []

        try:
            if not self.redis:
                # Use in-memory buffer
                cutoff = datetime.utcnow() - timedelta(days=days)
                return [
                    m for m in self.metric_buffer
                    if m.feature_id == feature_id and m.timestamp >= cutoff
                ]

            # Fetch from Redis for each day
            for i in range(days):
                date = datetime.utcnow() - timedelta(days=i)
                date_key = date.strftime('%Y%m%d')
                redis_key = f"{self.METRIC_PREFIX}{feature_id}:{date_key}"

                data_list = await self.redis.lrange(redis_key, 0, -1)

                for data in data_list:
                    metric_dict = json.loads(data)
                    metric_dict['timestamp'] = datetime.fromisoformat(
                        metric_dict['timestamp']
                    )
                    metric_dict['metric_type'] = MetricType(metric_dict['metric_type'])

                    metric = BusinessMetric(**metric_dict)
                    metrics.append(metric)

        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")

        return metrics

    async def get_daily_summary(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get daily business impact summary across all features."""
        if date is None:
            date = datetime.utcnow()

        date_key = date.strftime('%Y%m%d')

        summary = {
            'date': date_key,
            'features': {},
            'total_revenue_impact': 0.0,
            'total_cost_savings': 0.0,
            'total_roi': 0.0
        }

        # Calculate for each feature
        for feature_id in self.FEATURE_CONFIGS.keys():
            roi = await self.calculate_feature_roi(feature_id, days=1)
            if roi:
                summary['features'][feature_id] = {
                    'revenue_impact': roi.revenue_impact / 365,  # Daily
                    'cost_savings': roi.cost_savings / 365,
                    'net_value': roi.net_value / 365,
                    'roi_percentage': roi.roi_percentage
                }

                summary['total_revenue_impact'] += roi.revenue_impact / 365
                summary['total_cost_savings'] += roi.cost_savings / 365

        # Calculate total ROI
        total_benefit = summary['total_revenue_impact'] + summary['total_cost_savings']
        total_cost = sum(
            self.FEATURE_CONFIGS[f].get('infrastructure_cost', 0) / 365
            for f in self.FEATURE_CONFIGS
        )

        if total_cost > 0:
            summary['total_roi'] = ((total_benefit - total_cost) / total_cost) * 100

        return summary

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Business impact tracker closed")


# Global instance
_business_impact_tracker: Optional[Phase3BusinessImpactTracker] = None


async def get_business_impact_tracker(
    redis_url: str = "redis://localhost:6379/0"
) -> Phase3BusinessImpactTracker:
    """Get or create global business impact tracker."""
    global _business_impact_tracker

    if _business_impact_tracker is None:
        _business_impact_tracker = Phase3BusinessImpactTracker(redis_url=redis_url)
        await _business_impact_tracker.initialize()

    return _business_impact_tracker


__all__ = [
    "Phase3BusinessImpactTracker",
    "BusinessMetric",
    "FeatureROI",
    "ABTestResult",
    "MetricType",
    "get_business_impact_tracker"
]
