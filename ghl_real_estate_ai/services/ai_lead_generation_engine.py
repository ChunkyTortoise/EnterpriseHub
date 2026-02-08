"""
AI Lead Generation Engine - Phase 1 Foundation Service

Advanced lead generation intelligence leveraging ML analytics pipeline:
- Lead source quality analysis and optimization
- Intelligent lead routing and prioritization
- Predictive lead generation recommendations
- Source performance tracking and attribution
- Real-time lead generation optimization

Integrates with:
- Enhanced Lead Scoring Service for comprehensive analysis
- ML Analytics Engine for predictive capabilities
- Event Publisher for real-time updates
- Cache Service for performance optimization
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ml.closing_probability_model import get_ml_analytics_engine
from ghl_real_estate_ai.services.cache_service import TenantScopedCache, get_cache_service
from ghl_real_estate_ai.services.enhanced_lead_scoring import LeadSourceType, get_enhanced_lead_scoring
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class LeadGenerationChannel(Enum):
    """Lead generation channel types for optimization."""

    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    SEO_ORGANIC = "seo_organic"
    EMAIL_MARKETING = "email_marketing"
    CONTENT_MARKETING = "content_marketing"
    REFERRAL_PROGRAM = "referral_program"
    WEBINARS = "webinars"
    COLD_OUTREACH = "cold_outreach"
    RETARGETING = "retargeting"
    INFLUENCER = "influencer"
    DIRECT_MAIL = "direct_mail"
    EVENTS = "events"


class OptimizationPriority(Enum):
    """Priority levels for lead generation optimization."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MONITOR = "monitor"


@dataclass
class ChannelPerformanceMetrics:
    """Comprehensive channel performance analysis."""

    channel: LeadGenerationChannel
    location_id: str

    # Volume Metrics
    total_leads: int = 0
    qualified_leads: int = 0
    converted_leads: int = 0

    # Quality Metrics
    average_lead_score: float = 0.0
    conversion_rate: float = 0.0
    qualification_rate: float = 0.0

    # Financial Metrics
    cost_per_lead: Optional[float] = None
    cost_per_conversion: Optional[float] = None
    roi: Optional[float] = None
    lifetime_value: Optional[float] = None

    # Timing Metrics
    average_time_to_convert: Optional[float] = None  # days
    lead_velocity: float = 0.0  # leads per day

    # Trend Analysis
    performance_trend: str = "stable"  # improving, declining, stable
    trend_confidence: float = 0.0

    # Optimization Insights
    optimization_opportunities: List[str] = None
    competitive_positioning: str = "unknown"

    # Metadata
    last_updated: datetime = None
    analysis_period_days: int = 30

    def __post_init__(self):
        if self.optimization_opportunities is None:
            self.optimization_opportunities = []
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)


@dataclass
class LeadGenerationRecommendation:
    """Intelligent lead generation recommendation."""

    recommendation_id: str
    location_id: str
    channel: LeadGenerationChannel
    priority: OptimizationPriority

    # Recommendation Details
    title: str
    description: str
    expected_impact: str
    implementation_difficulty: str  # easy, medium, hard
    estimated_timeframe: str  # immediate, days, weeks, months

    # Financial Projections
    projected_lead_increase: Optional[float] = None  # percentage
    projected_cost_reduction: Optional[float] = None  # percentage
    projected_roi_improvement: Optional[float] = None  # percentage
    investment_required: Optional[float] = None  # dollars

    # Implementation Details
    action_items: List[str] = None
    success_metrics: List[str] = None
    risk_factors: List[str] = None
    dependencies: List[str] = None

    # Confidence & Validation
    confidence_score: float = 0.0
    data_quality: str = "good"  # excellent, good, fair, poor
    validation_status: str = "pending"  # validated, pending, rejected

    # Metadata
    created_at: datetime = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.action_items is None:
            self.action_items = []
        if self.success_metrics is None:
            self.success_metrics = []
        if self.risk_factors is None:
            self.risk_factors = []
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class LeadGenerationInsights:
    """Comprehensive lead generation intelligence report."""

    location_id: str
    analysis_id: str

    # Performance Overview
    overall_performance_grade: str  # A+, A, B+, B, C+, C, D
    total_monthly_leads: int
    total_monthly_conversions: int
    overall_roi: float

    # Channel Analysis
    channel_performance: Dict[str, ChannelPerformanceMetrics] = None
    top_performing_channels: List[LeadGenerationChannel] = None
    underperforming_channels: List[LeadGenerationChannel] = None

    # Optimization Opportunities
    immediate_opportunities: List[LeadGenerationRecommendation] = None
    strategic_recommendations: List[LeadGenerationRecommendation] = None
    competitive_gaps: List[str] = None

    # Predictive Intelligence
    forecasted_leads: Dict[str, float] = None  # next_30_days, next_90_days
    seasonal_patterns: Dict[str, float] = None
    market_trend_impact: str = "neutral"  # positive, negative, neutral

    # Alerts & Warnings
    performance_alerts: List[str] = None
    budget_optimization_alerts: List[str] = None
    competitor_activity_alerts: List[str] = None

    # Metadata
    generated_at: datetime = None
    confidence_level: float = 0.0
    next_review_date: datetime = None

    def __post_init__(self):
        if self.channel_performance is None:
            self.channel_performance = {}
        if self.top_performing_channels is None:
            self.top_performing_channels = []
        if self.underperforming_channels is None:
            self.underperforming_channels = []
        if self.immediate_opportunities is None:
            self.immediate_opportunities = []
        if self.strategic_recommendations is None:
            self.strategic_recommendations = []
        if self.competitive_gaps is None:
            self.competitive_gaps = []
        if self.forecasted_leads is None:
            self.forecasted_leads = {}
        if self.seasonal_patterns is None:
            self.seasonal_patterns = {}
        if self.performance_alerts is None:
            self.performance_alerts = []
        if self.budget_optimization_alerts is None:
            self.budget_optimization_alerts = []
        if self.competitor_activity_alerts is None:
            self.competitor_activity_alerts = []
        if self.generated_at is None:
            self.generated_at = datetime.now(timezone.utc)


class AILeadGenerationEngine:
    """
    AI-Powered Lead Generation Intelligence Engine.

    Provides advanced analytics and optimization for lead generation:
    - Channel performance analysis
    - Predictive lead generation recommendations
    - Real-time optimization insights
    - ROI optimization and budget allocation
    - Competitive intelligence and market trend analysis
    """

    def __init__(self):
        """Initialize the AI lead generation engine."""
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()
        self.lead_scoring = get_enhanced_lead_scoring()

        # Channel scoring weights based on typical real estate performance
        self.channel_baseline_scores = {
            LeadGenerationChannel.REFERRAL_PROGRAM: 90,
            LeadGenerationChannel.SEO_ORGANIC: 85,
            LeadGenerationChannel.WEBINARS: 80,
            LeadGenerationChannel.CONTENT_MARKETING: 75,
            LeadGenerationChannel.GOOGLE_ADS: 70,
            LeadGenerationChannel.EMAIL_MARKETING: 65,
            LeadGenerationChannel.FACEBOOK_ADS: 60,
            LeadGenerationChannel.EVENTS: 65,
            LeadGenerationChannel.RETARGETING: 55,
            LeadGenerationChannel.INFLUENCER: 50,
            LeadGenerationChannel.COLD_OUTREACH: 40,
            LeadGenerationChannel.DIRECT_MAIL: 35,
        }

        # Performance thresholds for optimization recommendations
        self.performance_thresholds = {
            "conversion_rate": {"excellent": 0.15, "good": 0.10, "fair": 0.05, "poor": 0.02},
            "cost_per_lead": {"excellent": 25, "good": 50, "fair": 100, "poor": 200},
            "roi": {"excellent": 5.0, "good": 3.0, "fair": 1.5, "poor": 0.5},
        }

    async def analyze_lead_generation_performance(
        self, location_id: str, analysis_period_days: int = 30
    ) -> LeadGenerationInsights:
        """
        Comprehensive lead generation performance analysis.

        Args:
            location_id: Tenant identifier for isolation
            analysis_period_days: Period for analysis (default 30 days)

        Returns:
            LeadGenerationInsights with comprehensive intelligence
        """
        start_time = time.perf_counter()
        analysis_id = str(uuid.uuid4())

        tenant_cache = TenantScopedCache(location_id, self.cache)

        # Check cache for recent analysis
        cache_key = f"lead_gen_analysis:{analysis_period_days}"
        cached_insights = await tenant_cache.get(cache_key)
        if cached_insights:
            logger.debug(f"Lead generation analysis cache hit for {location_id}")
            return cached_insights

        try:
            # 1. Analyze Channel Performance
            channel_performance = await self._analyze_all_channels(location_id, analysis_period_days)

            # 2. Calculate Overall Performance Metrics
            overall_metrics = self._calculate_overall_performance(channel_performance)

            # 3. Identify Optimization Opportunities
            immediate_opportunities, strategic_recommendations = await self._identify_optimization_opportunities(
                location_id, channel_performance
            )

            # 4. Generate Predictive Insights
            forecasted_leads = await self._generate_lead_forecasts(location_id, channel_performance)

            # 5. Detect Performance Alerts
            alerts = self._detect_performance_alerts(channel_performance, overall_metrics)

            # 6. Competitive & Market Intelligence
            competitive_gaps = await self._analyze_competitive_gaps(location_id, channel_performance)

            processing_time = (time.perf_counter() - start_time) * 1000

            # 7. Generate Comprehensive Insights
            insights = LeadGenerationInsights(
                location_id=location_id,
                analysis_id=analysis_id,
                overall_performance_grade=overall_metrics["performance_grade"],
                total_monthly_leads=overall_metrics["total_leads"],
                total_monthly_conversions=overall_metrics["total_conversions"],
                overall_roi=overall_metrics["overall_roi"],
                channel_performance={channel.value: metrics for channel, metrics in channel_performance.items()},
                top_performing_channels=overall_metrics["top_channels"],
                underperforming_channels=overall_metrics["underperforming_channels"],
                immediate_opportunities=immediate_opportunities,
                strategic_recommendations=strategic_recommendations,
                competitive_gaps=competitive_gaps,
                forecasted_leads=forecasted_leads,
                performance_alerts=alerts["performance_alerts"],
                budget_optimization_alerts=alerts["budget_alerts"],
                competitor_activity_alerts=alerts["competitor_alerts"],
                confidence_level=self._calculate_analysis_confidence(channel_performance),
                next_review_date=datetime.now(timezone.utc) + timedelta(days=7),
            )

            # 8. Cache Results (4 hour TTL for strategic insights)
            await tenant_cache.set(cache_key, insights, ttl=14400)

            # 9. Publish Real-time Event
            await self._publish_lead_generation_insights_event(insights, processing_time)

            logger.info(
                f"Lead generation analysis complete for {location_id}: "
                f"Grade {insights.overall_performance_grade}, {len(immediate_opportunities)} opportunities "
                f"[{processing_time:.2f}ms]"
            )

            return insights

        except Exception as e:
            logger.error(f"Lead generation analysis failed for {location_id}: {e}")
            return self._create_fallback_insights(location_id, analysis_id)

    async def _analyze_all_channels(
        self, location_id: str, analysis_period_days: int
    ) -> Dict[LeadGenerationChannel, ChannelPerformanceMetrics]:
        """Analyze performance across all lead generation channels."""

        channel_performance = {}

        for channel in LeadGenerationChannel:
            metrics = await self._analyze_channel_performance(location_id, channel, analysis_period_days)
            channel_performance[channel] = metrics

        return channel_performance

    async def _analyze_channel_performance(
        self, location_id: str, channel: LeadGenerationChannel, analysis_period_days: int
    ) -> ChannelPerformanceMetrics:
        """Analyze performance for a specific channel."""

        tenant_cache = TenantScopedCache(location_id, self.cache)

        # Get historical data for this channel (in production, would query database)
        historical_data = await self._get_channel_historical_data(tenant_cache, channel, analysis_period_days)

        # Calculate core metrics
        total_leads = historical_data.get("total_leads", 0)
        qualified_leads = historical_data.get("qualified_leads", 0)
        converted_leads = historical_data.get("converted_leads", 0)

        conversion_rate = converted_leads / max(1, total_leads)
        qualification_rate = qualified_leads / max(1, total_leads)

        # Calculate financial metrics
        total_cost = historical_data.get("total_cost", 0)
        cost_per_lead = total_cost / max(1, total_leads) if total_cost else None
        cost_per_conversion = total_cost / max(1, converted_leads) if total_cost and converted_leads else None

        # Estimate average deal value and ROI
        avg_deal_value = historical_data.get("avg_deal_value", 250000)  # Real estate average
        total_revenue = converted_leads * avg_deal_value
        roi = (total_revenue - total_cost) / max(1, total_cost) if total_cost else None

        # Analyze trends
        trend_analysis = self._analyze_channel_trends(historical_data)

        # Generate optimization opportunities
        opportunities = self._generate_channel_optimization_opportunities(channel, conversion_rate, cost_per_lead, roi)

        return ChannelPerformanceMetrics(
            channel=channel,
            location_id=location_id,
            total_leads=total_leads,
            qualified_leads=qualified_leads,
            converted_leads=converted_leads,
            average_lead_score=historical_data.get("avg_lead_score", 50),
            conversion_rate=conversion_rate,
            qualification_rate=qualification_rate,
            cost_per_lead=cost_per_lead,
            cost_per_conversion=cost_per_conversion,
            roi=roi,
            average_time_to_convert=historical_data.get("avg_time_to_convert"),
            lead_velocity=total_leads / analysis_period_days,
            performance_trend=trend_analysis["trend"],
            trend_confidence=trend_analysis["confidence"],
            optimization_opportunities=opportunities,
            analysis_period_days=analysis_period_days,
        )

    def _calculate_overall_performance(
        self, channel_performance: Dict[LeadGenerationChannel, ChannelPerformanceMetrics]
    ) -> Dict[str, Any]:
        """Calculate overall performance metrics across all channels."""

        # Aggregate metrics
        total_leads = sum(metrics.total_leads for metrics in channel_performance.values())
        total_conversions = sum(metrics.converted_leads for metrics in channel_performance.values())
        total_costs = sum(
            metrics.cost_per_lead * metrics.total_leads
            for metrics in channel_performance.values()
            if metrics.cost_per_lead
        )

        # Calculate weighted average ROI
        roi_values = [(metrics.roi or 0, metrics.converted_leads) for metrics in channel_performance.values()]
        overall_roi = sum(roi * weight for roi, weight in roi_values) / max(1, sum(weight for _, weight in roi_values))

        # Identify top and underperforming channels
        channels_by_roi = sorted(
            [(channel, metrics.roi or 0) for channel, metrics in channel_performance.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        top_channels = [channel for channel, roi in channels_by_roi[:3] if roi > 1.0]
        underperforming_channels = [channel for channel, roi in channels_by_roi if roi < 0.5]

        # Calculate performance grade
        performance_grade = self._calculate_performance_grade(overall_roi, total_conversions, total_leads)

        return {
            "total_leads": total_leads,
            "total_conversions": total_conversions,
            "overall_roi": overall_roi,
            "performance_grade": performance_grade,
            "top_channels": top_channels,
            "underperforming_channels": underperforming_channels,
        }

    async def _identify_optimization_opportunities(
        self, location_id: str, channel_performance: Dict[LeadGenerationChannel, ChannelPerformanceMetrics]
    ) -> Tuple[List[LeadGenerationRecommendation], List[LeadGenerationRecommendation]]:
        """Identify immediate and strategic optimization opportunities."""

        immediate_opportunities = []
        strategic_recommendations = []

        for channel, metrics in channel_performance.items():
            # Immediate opportunities (quick wins)
            if metrics.conversion_rate < 0.05 and metrics.total_leads > 20:
                immediate_opportunities.append(
                    self._create_conversion_optimization_recommendation(location_id, channel, metrics)
                )

            if metrics.cost_per_lead and metrics.cost_per_lead > 100:
                immediate_opportunities.append(
                    self._create_cost_reduction_recommendation(location_id, channel, metrics)
                )

            # Strategic recommendations (long-term)
            if metrics.roi and metrics.roi > 3.0 and metrics.total_leads < 50:
                strategic_recommendations.append(self._create_scaling_recommendation(location_id, channel, metrics))

            if metrics.performance_trend == "declining" and metrics.trend_confidence > 0.7:
                strategic_recommendations.append(
                    self._create_performance_recovery_recommendation(location_id, channel, metrics)
                )

        # Sort by priority and impact
        immediate_opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
        strategic_recommendations.sort(key=lambda x: x.projected_roi_improvement or 0, reverse=True)

        return immediate_opportunities[:5], strategic_recommendations[:5]

    async def _generate_lead_forecasts(
        self, location_id: str, channel_performance: Dict[LeadGenerationChannel, ChannelPerformanceMetrics]
    ) -> Dict[str, float]:
        """Generate predictive lead forecasts."""

        # Calculate total current lead velocity
        total_daily_velocity = sum(metrics.lead_velocity for metrics in channel_performance.values())

        # Apply seasonal and trend adjustments
        seasonal_multiplier = self._get_seasonal_multiplier(datetime.now().month)
        trend_multiplier = 1.0  # Would analyze trends in full implementation

        # Forecast periods
        forecasts = {
            "next_7_days": total_daily_velocity * 7 * seasonal_multiplier * trend_multiplier,
            "next_30_days": total_daily_velocity * 30 * seasonal_multiplier * trend_multiplier,
            "next_90_days": total_daily_velocity * 90 * seasonal_multiplier * trend_multiplier,
        }

        return {period: round(count, 1) for period, count in forecasts.items()}

    def _detect_performance_alerts(
        self,
        channel_performance: Dict[LeadGenerationChannel, ChannelPerformanceMetrics],
        overall_metrics: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        """Detect performance alerts and warnings."""

        performance_alerts = []
        budget_alerts = []
        competitor_alerts = []

        # Performance alerts
        for channel, metrics in channel_performance.items():
            if metrics.conversion_rate < 0.02:
                performance_alerts.append(
                    f"⚠️ {channel.value}: Very low conversion rate ({metrics.conversion_rate:.1%})"
                )

            if metrics.performance_trend == "declining" and metrics.trend_confidence > 0.8:
                performance_alerts.append(f"📉 {channel.value}: Declining performance trend detected")

            if metrics.cost_per_lead and metrics.cost_per_lead > 150:
                budget_alerts.append(f"💰 {channel.value}: High cost per lead (${metrics.cost_per_lead:.0f})")

        # Overall performance alerts
        if overall_metrics["overall_roi"] < 1.0:
            performance_alerts.append("🚨 Overall ROI below breakeven threshold")

        if len(overall_metrics["underperforming_channels"]) > 3:
            budget_alerts.append("🎯 Multiple underperforming channels - budget reallocation needed")

        return {
            "performance_alerts": performance_alerts,
            "budget_alerts": budget_alerts,
            "competitor_alerts": competitor_alerts,  # Would be populated by competitive intelligence
        }

    async def _analyze_competitive_gaps(
        self, location_id: str, channel_performance: Dict[LeadGenerationChannel, ChannelPerformanceMetrics]
    ) -> List[str]:
        """Analyze competitive gaps and market opportunities."""

        gaps = []

        # Identify unused high-performing channels
        active_channels = {channel for channel, metrics in channel_performance.items() if metrics.total_leads > 0}
        high_value_channels = {
            LeadGenerationChannel.REFERRAL_PROGRAM,
            LeadGenerationChannel.WEBINARS,
            LeadGenerationChannel.SEO_ORGANIC,
        }

        missing_channels = high_value_channels - active_channels
        for channel in missing_channels:
            gaps.append(f"Opportunity: Not utilizing {channel.value} (typically high-ROI channel)")

        # Identify underinvestment in top-performing channels
        for channel, metrics in channel_performance.items():
            if metrics.roi and metrics.roi > 4.0 and metrics.total_leads < 30:
                gaps.append(f"Underinvestment: {channel.value} showing high ROI but low volume")

        return gaps[:5]  # Limit to top 5 gaps

    async def _publish_lead_generation_insights_event(self, insights: LeadGenerationInsights, processing_time: float):
        """Publish real-time lead generation insights event."""

        try:
            # Use existing event publisher for analytics completion
            await self.event_publisher.publish_intent_analysis_complete(
                contact_id=f"lead_gen_analysis_{insights.analysis_id[:8]}",
                processing_time_ms=processing_time,
                confidence_score=insights.confidence_level,
                intent_category=insights.overall_performance_grade,
                location_id=insights.location_id,
            )

        except Exception as e:
            logger.warning(f"Failed to publish lead generation insights event: {e}")

    # Helper methods for analysis and calculations

    async def _get_channel_historical_data(
        self, tenant_cache: TenantScopedCache, channel: LeadGenerationChannel, days: int
    ) -> Dict[str, Any]:
        """Get historical performance data for channel (simulated for MVP)."""

        # In production, this would query a time-series database
        # For MVP, return simulated data based on channel type
        baseline_score = self.channel_baseline_scores.get(channel, 50)

        return {
            "total_leads": max(0, int(baseline_score * days * 0.1)),  # Proportional to channel quality
            "qualified_leads": max(0, int(baseline_score * days * 0.07)),
            "converted_leads": max(0, int(baseline_score * days * 0.02)),
            "total_cost": max(0, baseline_score * days * 2),  # $2 per point per day
            "avg_deal_value": 250000,
            "avg_lead_score": baseline_score,
            "avg_time_to_convert": 45,  # days
        }

    def _analyze_channel_trends(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends for channel."""

        # Simplified trend analysis (would use statistical methods in production)
        current_performance = historical_data.get("total_leads", 0)

        if current_performance > 50:
            trend = "improving"
            confidence = 0.8
        elif current_performance < 10:
            trend = "declining"
            confidence = 0.9
        else:
            trend = "stable"
            confidence = 0.6

        return {"trend": trend, "confidence": confidence}

    def _generate_channel_optimization_opportunities(
        self,
        channel: LeadGenerationChannel,
        conversion_rate: float,
        cost_per_lead: Optional[float],
        roi: Optional[float],
    ) -> List[str]:
        """Generate channel-specific optimization opportunities."""

        opportunities = []

        if conversion_rate < 0.05:
            opportunities.append("Improve lead qualification process")
            opportunities.append("Optimize landing page conversion")

        if cost_per_lead and cost_per_lead > 75:
            opportunities.append("Reduce acquisition costs")
            opportunities.append("Improve audience targeting")

        if roi and roi > 3.0:
            opportunities.append("Scale successful campaigns")
            opportunities.append("Increase budget allocation")

        # Channel-specific opportunities
        if channel == LeadGenerationChannel.GOOGLE_ADS:
            opportunities.append("Optimize keyword bidding strategy")
        elif channel == LeadGenerationChannel.SEO_ORGANIC:
            opportunities.append("Expand content marketing")
        elif channel == LeadGenerationChannel.REFERRAL_PROGRAM:
            opportunities.append("Enhance referral incentives")

        return opportunities

    def _calculate_performance_grade(self, roi: float, conversions: int, leads: int) -> str:
        """Calculate overall performance grade."""

        score = 0

        # ROI contribution (40%)
        if roi > 5.0:
            score += 40
        elif roi > 3.0:
            score += 32
        elif roi > 1.5:
            score += 24
        elif roi > 0.5:
            score += 16
        else:
            score += 8

        # Volume contribution (30%)
        if conversions > 20:
            score += 30
        elif conversions > 10:
            score += 24
        elif conversions > 5:
            score += 18
        else:
            score += 12

        # Conversion rate contribution (30%)
        conversion_rate = conversions / max(1, leads)
        if conversion_rate > 0.15:
            score += 30
        elif conversion_rate > 0.10:
            score += 24
        elif conversion_rate > 0.05:
            score += 18
        else:
            score += 12

        # Map score to grade
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "C+"
        elif score >= 60:
            return "C"
        else:
            return "D"

    def _get_seasonal_multiplier(self, month: int) -> float:
        """Get seasonal adjustment multiplier for lead forecasting."""

        # Real estate seasonal patterns
        seasonal_multipliers = {
            1: 0.8,  # January (slow)
            2: 0.85,  # February
            3: 1.1,  # March (spring buying)
            4: 1.2,  # April (peak)
            5: 1.25,  # May (peak)
            6: 1.2,  # June
            7: 1.1,  # July
            8: 1.0,  # August
            9: 1.05,  # September
            10: 1.0,  # October
            11: 0.9,  # November (slower)
            12: 0.8,  # December (holidays)
        }

        return seasonal_multipliers.get(month, 1.0)

    def _create_conversion_optimization_recommendation(
        self, location_id: str, channel: LeadGenerationChannel, metrics: ChannelPerformanceMetrics
    ) -> LeadGenerationRecommendation:
        """Create conversion optimization recommendation."""

        return LeadGenerationRecommendation(
            recommendation_id=str(uuid.uuid4()),
            location_id=location_id,
            channel=channel,
            priority=OptimizationPriority.HIGH,
            title=f"Improve {channel.value} Conversion Rate",
            description=f"Current conversion rate of {metrics.conversion_rate:.1%} is below optimal. Implement lead nurturing and qualification improvements.",
            expected_impact="15-30% increase in conversions",
            implementation_difficulty="medium",
            estimated_timeframe="2-3 weeks",
            projected_lead_increase=20,
            action_items=[
                "Review and optimize lead qualification process",
                "Implement lead scoring for better prioritization",
                "Create targeted nurture sequences",
                "A/B test landing pages",
            ],
            success_metrics=[
                "Conversion rate improvement to >8%",
                "Increased lead quality scores",
                "Reduced time to conversion",
            ],
            confidence_score=0.85,
        )

    def _create_cost_reduction_recommendation(
        self, location_id: str, channel: LeadGenerationChannel, metrics: ChannelPerformanceMetrics
    ) -> LeadGenerationRecommendation:
        """Create cost reduction recommendation."""

        return LeadGenerationRecommendation(
            recommendation_id=str(uuid.uuid4()),
            location_id=location_id,
            channel=channel,
            priority=OptimizationPriority.HIGH,
            title=f"Reduce {channel.value} Cost Per Lead",
            description=f"Current cost of ${metrics.cost_per_lead:.0f} per lead is above optimal range. Implement targeting and efficiency improvements.",
            expected_impact="20-40% cost reduction",
            implementation_difficulty="easy",
            estimated_timeframe="1-2 weeks",
            projected_cost_reduction=30,
            action_items=[
                "Audit and refine audience targeting",
                "Pause underperforming ad sets",
                "Optimize bidding strategies",
                "Improve ad creative performance",
            ],
            success_metrics=["Cost per lead reduced to <$75", "Maintained or improved lead volume", "Improved ROI"],
            confidence_score=0.9,
        )

    def _create_scaling_recommendation(
        self, location_id: str, channel: LeadGenerationChannel, metrics: ChannelPerformanceMetrics
    ) -> LeadGenerationRecommendation:
        """Create scaling recommendation for high-performing channels."""

        return LeadGenerationRecommendation(
            recommendation_id=str(uuid.uuid4()),
            location_id=location_id,
            channel=channel,
            priority=OptimizationPriority.MEDIUM,
            title=f"Scale High-Performing {channel.value} Channel",
            description=f"Channel showing strong ROI of {metrics.roi:.1f}x. Opportunity to increase budget and volume.",
            expected_impact="50-100% increase in qualified leads",
            implementation_difficulty="easy",
            estimated_timeframe="immediate",
            projected_lead_increase=75,
            projected_roi_improvement=20,
            action_items=[
                "Increase budget allocation by 50%",
                "Expand to similar audiences",
                "Test additional creative variations",
                "Monitor performance closely",
            ],
            success_metrics=["Maintained or improved ROI", "Increased lead volume", "Stable conversion rates"],
            confidence_score=0.95,
        )

    def _create_performance_recovery_recommendation(
        self, location_id: str, channel: LeadGenerationChannel, metrics: ChannelPerformanceMetrics
    ) -> LeadGenerationRecommendation:
        """Create performance recovery recommendation."""

        return LeadGenerationRecommendation(
            recommendation_id=str(uuid.uuid4()),
            location_id=location_id,
            channel=channel,
            priority=OptimizationPriority.CRITICAL,
            title=f"Recover Declining {channel.value} Performance",
            description=f"Channel showing declining trend with {metrics.trend_confidence:.0%} confidence. Immediate action required.",
            expected_impact="Stabilize and improve performance",
            implementation_difficulty="hard",
            estimated_timeframe="3-4 weeks",
            action_items=[
                "Conduct full channel audit",
                "Analyze competitive changes",
                "Test new approaches",
                "Consider temporary budget reduction",
            ],
            success_metrics=["Performance trend reversal", "ROI improvement", "Cost efficiency gains"],
            confidence_score=0.75,
            risk_factors=["May require significant changes", "Performance recovery not guaranteed"],
        )

    def _calculate_analysis_confidence(
        self, channel_performance: Dict[LeadGenerationChannel, ChannelPerformanceMetrics]
    ) -> float:
        """Calculate overall confidence level in the analysis."""

        # Base confidence on data volume and quality
        total_leads = sum(metrics.total_leads for metrics in channel_performance.values())
        active_channels = sum(1 for metrics in channel_performance.values() if metrics.total_leads > 5)

        volume_score = min(1.0, total_leads / 100)  # 100 leads = full confidence
        diversity_score = min(1.0, active_channels / 5)  # 5 active channels = full confidence

        return round((volume_score * 0.6 + diversity_score * 0.4), 3)

    def _create_fallback_insights(self, location_id: str, analysis_id: str) -> LeadGenerationInsights:
        """Create fallback insights when analysis fails."""

        return LeadGenerationInsights(
            location_id=location_id,
            analysis_id=analysis_id,
            overall_performance_grade="C",
            total_monthly_leads=0,
            total_monthly_conversions=0,
            overall_roi=0.0,
            performance_alerts=["⚠️ Analysis failed - manual review required"],
            confidence_level=0.1,
        )


# Singleton accessor following established pattern
_ai_lead_generation_engine = None


def get_ai_lead_generation_engine() -> AILeadGenerationEngine:
    """Get singleton AI lead generation engine instance."""
    global _ai_lead_generation_engine
    if _ai_lead_generation_engine is None:
        _ai_lead_generation_engine = AILeadGenerationEngine()
    return _ai_lead_generation_engine


# Convenience functions for common operations
async def analyze_lead_generation_performance(
    location_id: str, analysis_period_days: int = 30
) -> LeadGenerationInsights:
    """Convenience function for lead generation performance analysis."""
    engine = get_ai_lead_generation_engine()
    return await engine.analyze_lead_generation_performance(location_id, analysis_period_days)


async def get_channel_recommendations(
    location_id: str, channel: LeadGenerationChannel
) -> List[LeadGenerationRecommendation]:
    """Convenience function for channel-specific recommendations."""
    engine = get_ai_lead_generation_engine()
    insights = await engine.analyze_lead_generation_performance(location_id)
    return [
        rec for rec in insights.immediate_opportunities + insights.strategic_recommendations if rec.channel == channel
    ]
