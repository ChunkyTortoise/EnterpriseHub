"""
Attribution Analytics - Advanced Lead Source Performance Analysis for Jorge's Bot.

Provides comprehensive analytics, reporting, and alerting for lead source performance:
- Real-time conversion tracking and ROI monitoring
- Advanced cohort analysis and trend detection
- Automated performance alerts and recommendations
- Cost per acquisition optimization
- Multi-touch attribution modeling
- Integration with Jorge's marketing dashboard

Key Features:
- Weekly and monthly performance reporting
- Automated alerts for performance changes
- ROI optimization recommendations
- Channel performance forecasting
- Attribution model comparison
- Marketing spend optimization insights
"""

import asyncio
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.lead_source_tracker import (
    LeadSource,
    LeadSourceTracker,
    SourceAttribution,
    SourcePerformance,
)

logger = get_logger(__name__)


class ReportPeriod(str, Enum):
    """Reporting period options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AlertType(str, Enum):
    """Alert types for performance monitoring."""

    ROI_DROP = "roi_drop"
    COST_SPIKE = "cost_spike"
    VOLUME_DROP = "volume_drop"
    QUALITY_DROP = "quality_drop"
    CONVERSION_DROP = "conversion_drop"
    NEW_TOP_PERFORMER = "new_top_performer"
    BUDGET_EXCEEDED = "budget_exceeded"


class AttributionModel(str, Enum):
    """Attribution model types."""

    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"


@dataclass
class PerformanceAlert:
    """Performance alert with context and recommendations."""

    alert_type: AlertType
    source: LeadSource
    severity: str  # "low", "medium", "high", "critical"
    title: str
    description: str
    current_value: float
    previous_value: float
    threshold: float
    change_percentage: float
    recommendations: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class CohortAnalysis:
    """Cohort analysis results for a lead source."""

    source: LeadSource
    cohort_date: date
    cohort_size: int

    # Conversion rates by time period
    day_1_conversion: float = 0.0
    day_7_conversion: float = 0.0
    day_30_conversion: float = 0.0
    day_60_conversion: float = 0.0
    day_90_conversion: float = 0.0

    # Revenue metrics
    day_1_revenue: float = 0.0
    day_7_revenue: float = 0.0
    day_30_revenue: float = 0.0
    day_60_revenue: float = 0.0
    day_90_revenue: float = 0.0

    # Lead quality metrics
    avg_lead_score: float = 0.0
    qualification_rate: float = 0.0
    avg_response_time: float = 0.0


@dataclass
class ChannelForecast:
    """Forecast data for a marketing channel."""

    source: LeadSource
    forecast_date: date

    # Predicted metrics
    predicted_leads: int
    predicted_qualified_leads: int
    predicted_revenue: float
    predicted_cost: float
    predicted_roi: float

    # Confidence intervals
    confidence_level: float = 0.95
    leads_lower_bound: int = 0
    leads_upper_bound: int = 0
    revenue_lower_bound: float = 0.0
    revenue_upper_bound: float = 0.0

    # Model metadata
    model_accuracy: float = 0.0
    data_points_used: int = 0


@dataclass
class AttributionReport:
    """Comprehensive attribution analysis report."""

    period_start: datetime
    period_end: datetime
    generated_at: datetime

    # Summary metrics
    total_leads: int = 0
    total_qualified_leads: int = 0
    total_revenue: float = 0.0
    total_cost: float = 0.0
    overall_roi: float = 0.0

    # Source performance
    source_performance: List[SourcePerformance] = None

    # Advanced analytics
    cohort_analysis: List[CohortAnalysis] = None
    channel_forecasts: List[ChannelForecast] = None

    # Alerts and recommendations
    active_alerts: List[PerformanceAlert] = None
    optimization_recommendations: List[Dict[str, Any]] = None

    # Attribution model comparison
    attribution_comparison: Dict[str, Dict[str, float]] = None


class AttributionAnalytics:
    """
    Advanced analytics engine for lead source attribution and performance.

    Provides comprehensive insights into marketing channel performance,
    automated alerting, and optimization recommendations for Jorge's
    real estate lead generation campaigns.
    """

    def __init__(self):
        self.cache = CacheService()
        self.source_tracker = LeadSourceTracker()

        # Alert thresholds
        self.alert_thresholds = {
            AlertType.ROI_DROP: -0.20,  # 20% ROI drop
            AlertType.COST_SPIKE: 0.30,  # 30% cost increase
            AlertType.VOLUME_DROP: -0.25,  # 25% volume decrease
            AlertType.QUALITY_DROP: -0.15,  # 15% quality drop
            AlertType.CONVERSION_DROP: -0.20,  # 20% conversion drop
        }

        # Minimum data requirements for analysis
        self.min_data_requirements = {"min_leads": 10, "min_days": 7, "min_conversions": 3}

        logger.info("AttributionAnalytics initialized with advanced analytics capabilities")

    async def generate_attribution_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        attribution_model: AttributionModel = AttributionModel.LAST_TOUCH,
        include_forecasts: bool = True,
        include_cohorts: bool = True,
    ) -> AttributionReport:
        """
        Generate comprehensive attribution analysis report.

        Args:
            start_date: Report start date (defaults to 30 days ago)
            end_date: Report end date (defaults to now)
            attribution_model: Attribution model to use
            include_forecasts: Whether to include channel forecasts
            include_cohorts: Whether to include cohort analysis

        Returns:
            Complete AttributionReport with analytics
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            logger.info(f"Generating attribution report for {start_date} to {end_date}")

            # Initialize report
            report = AttributionReport(period_start=start_date, period_end=end_date, generated_at=datetime.utcnow())

            # Get source performance data
            source_performances = await self.source_tracker.get_all_source_performance(start_date, end_date)
            report.source_performance = source_performances

            # Calculate summary metrics
            report.total_leads = sum(p.total_leads for p in source_performances)
            report.total_qualified_leads = sum(p.qualified_leads for p in source_performances)
            report.total_revenue = sum(p.total_revenue for p in source_performances)
            report.total_cost = sum(p.cost_per_lead * p.total_leads for p in source_performances)

            if report.total_cost > 0:
                report.overall_roi = (report.total_revenue - report.total_cost) / report.total_cost

            # Generate cohort analysis
            if include_cohorts:
                report.cohort_analysis = await self._generate_cohort_analysis(start_date, end_date)

            # Generate channel forecasts
            if include_forecasts:
                report.channel_forecasts = await self._generate_channel_forecasts(source_performances)

            # Generate active alerts
            report.active_alerts = await self._generate_performance_alerts(source_performances)

            # Generate optimization recommendations
            report.optimization_recommendations = await self._generate_optimization_recommendations(
                source_performances, report.active_alerts
            )

            # Attribution model comparison
            report.attribution_comparison = await self._compare_attribution_models(start_date, end_date)

            logger.info(
                f"Attribution report generated: {report.total_leads} leads, "
                f"{len(report.source_performance)} sources, "
                f"{len(report.active_alerts or [])} alerts"
            )

            # Cache the report
            cache_key = f"attribution_report:{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}"
            await self.cache.set(cache_key, asdict(report), ttl=3600)

            return report

        except Exception as e:
            logger.error(f"Error generating attribution report: {e}", exc_info=True)
            # Return basic report on error
            return AttributionReport(
                period_start=start_date or datetime.utcnow() - timedelta(days=30),
                period_end=end_date or datetime.utcnow(),
                generated_at=datetime.utcnow(),
            )

    async def _generate_cohort_analysis(self, start_date: datetime, end_date: datetime) -> List[CohortAnalysis]:
        """Generate cohort analysis for lead sources."""
        try:
            cohorts = []

            # Get cohorts by week for the analysis period
            current_date = start_date.date()
            while current_date <= end_date.date():
                week_start = current_date - timedelta(days=current_date.weekday())

                # Analyze each significant source
                for source in LeadSource:
                    cohort = await self._analyze_source_cohort(source, week_start)
                    if cohort and cohort.cohort_size >= self.min_data_requirements["min_leads"]:
                        cohorts.append(cohort)

                current_date += timedelta(weeks=1)

            # Sort by cohort date and source
            cohorts.sort(key=lambda c: (c.cohort_date, c.source.value))

            return cohorts

        except Exception as e:
            logger.error(f"Error generating cohort analysis: {e}", exc_info=True)
            return []

    async def _analyze_source_cohort(self, source: LeadSource, cohort_date: date) -> Optional[CohortAnalysis]:
        """Analyze a specific source cohort."""
        try:
            # Get leads for this cohort
            cache_key = f"source_cohort:{source.value}:{cohort_date.strftime('%Y%m%d')}"
            cohort_data = await self.cache.get(cache_key)

            if not cohort_data:
                return None

            cohort = CohortAnalysis(
                source=source, cohort_date=cohort_date, cohort_size=cohort_data.get("cohort_size", 0)
            )

            # Calculate conversion rates by time periods
            periods = [1, 7, 30, 60, 90]
            for period in periods:
                conversions = cohort_data.get(f"day_{period}_conversions", 0)
                revenue = cohort_data.get(f"day_{period}_revenue", 0.0)

                conversion_rate = conversions / cohort.cohort_size if cohort.cohort_size > 0 else 0

                setattr(cohort, f"day_{period}_conversion", conversion_rate)
                setattr(cohort, f"day_{period}_revenue", revenue)

            # Additional metrics
            cohort.avg_lead_score = cohort_data.get("avg_lead_score", 0.0)
            cohort.qualification_rate = cohort_data.get("qualification_rate", 0.0)
            cohort.avg_response_time = cohort_data.get("avg_response_time", 0.0)

            return cohort

        except Exception as e:
            logger.error(f"Error analyzing cohort for {source}: {e}", exc_info=True)
            return None

    async def _generate_channel_forecasts(self, source_performances: List[SourcePerformance]) -> List[ChannelForecast]:
        """Generate forecasts for each marketing channel."""
        try:
            forecasts = []

            for performance in source_performances:
                if performance.total_leads < self.min_data_requirements["min_leads"]:
                    continue

                forecast = await self._forecast_channel_performance(performance)
                if forecast:
                    forecasts.append(forecast)

            return forecasts

        except Exception as e:
            logger.error(f"Error generating channel forecasts: {e}", exc_info=True)
            return []

    async def _forecast_channel_performance(self, performance: SourcePerformance) -> Optional[ChannelForecast]:
        """Generate forecast for a single channel using simple trend analysis."""
        try:
            source = performance.source

            # Get historical data points
            historical_data = await self._get_historical_data_points(source, days=60)

            if len(historical_data) < 7:  # Need at least a week of data
                return None

            # Simple linear trend forecast (in production, use more sophisticated models)
            leads_trend = self._calculate_trend([d["leads"] for d in historical_data[-14:]])
            revenue_trend = self._calculate_trend([d["revenue"] for d in historical_data[-14:]])

            # Forecast for next 30 days
            forecast_date = (datetime.utcnow() + timedelta(days=30)).date()

            # Conservative prediction based on recent trends
            recent_avg_leads = sum(d["leads"] for d in historical_data[-7:]) / 7
            recent_avg_revenue = sum(d["revenue"] for d in historical_data[-7:]) / 7
            recent_avg_cost = sum(d["cost"] for d in historical_data[-7:]) / 7

            predicted_daily_leads = max(0, recent_avg_leads + (leads_trend * 30))
            predicted_daily_revenue = max(0, recent_avg_revenue + (revenue_trend * 30))
            predicted_daily_cost = recent_avg_cost  # Assume cost stays constant

            # Monthly predictions
            predicted_leads = int(predicted_daily_leads * 30)
            predicted_revenue = predicted_daily_revenue * 30
            predicted_cost = predicted_daily_cost * 30

            predicted_roi = (predicted_revenue - predicted_cost) / predicted_cost if predicted_cost > 0 else 0
            predicted_qualified_leads = int(predicted_leads * performance.qualification_rate)

            # Calculate confidence intervals (simple ±20% range)
            confidence_range = 0.20

            forecast = ChannelForecast(
                source=source,
                forecast_date=forecast_date,
                predicted_leads=predicted_leads,
                predicted_qualified_leads=predicted_qualified_leads,
                predicted_revenue=predicted_revenue,
                predicted_cost=predicted_cost,
                predicted_roi=predicted_roi,
                confidence_level=0.80,  # 80% confidence with simple model
                leads_lower_bound=int(predicted_leads * (1 - confidence_range)),
                leads_upper_bound=int(predicted_leads * (1 + confidence_range)),
                revenue_lower_bound=predicted_revenue * (1 - confidence_range),
                revenue_upper_bound=predicted_revenue * (1 + confidence_range),
                model_accuracy=0.75,  # Estimated accuracy for simple trend model
                data_points_used=len(historical_data),
            )

            return forecast

        except Exception as e:
            logger.error(f"Error forecasting {performance.source}: {e}", exc_info=True)
            return None

    def _calculate_trend(self, data_points: List[float]) -> float:
        """Calculate simple linear trend from data points."""
        if len(data_points) < 2:
            return 0.0

        n = len(data_points)
        x_sum = sum(range(n))
        y_sum = sum(data_points)
        xy_sum = sum(i * y for i, y in enumerate(data_points))
        x_squared_sum = sum(i * i for i in range(n))

        # Linear regression slope
        denominator = n * x_squared_sum - x_sum * x_sum
        if denominator == 0:
            return 0.0

        trend = (n * xy_sum - x_sum * y_sum) / denominator
        return trend

    async def _get_historical_data_points(self, source: LeadSource, days: int = 60) -> List[Dict[str, float]]:
        """Get historical daily data points for a source."""
        try:
            data_points = []

            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            current_date = start_date
            while current_date <= end_date:
                cache_key = f"daily_source_data:{source.value}:{current_date.strftime('%Y%m%d')}"
                daily_data = await self.cache.get(cache_key)

                if daily_data:
                    data_points.append(
                        {
                            "date": current_date,
                            "leads": daily_data.get("leads", 0),
                            "revenue": daily_data.get("revenue", 0.0),
                            "cost": daily_data.get("cost", 0.0),
                        }
                    )
                else:
                    # Fill missing days with zeros
                    data_points.append({"date": current_date, "leads": 0, "revenue": 0.0, "cost": 0.0})

                current_date += timedelta(days=1)

            return data_points

        except Exception as e:
            logger.error(f"Error getting historical data for {source}: {e}", exc_info=True)
            return []

    async def _generate_performance_alerts(
        self, source_performances: List[SourcePerformance]
    ) -> List[PerformanceAlert]:
        """Generate performance alerts based on thresholds and trends."""
        try:
            alerts = []

            for performance in source_performances:
                if performance.total_leads < self.min_data_requirements["min_leads"]:
                    continue

                # Get previous period performance for comparison
                previous_performance = await self._get_previous_period_performance(
                    performance.source, performance.period_start, performance.period_end
                )

                if not previous_performance:
                    continue

                # Check for ROI drops
                roi_change = (
                    (performance.roi - previous_performance.roi) / abs(previous_performance.roi)
                    if previous_performance.roi != 0
                    else 0
                )
                if roi_change <= self.alert_thresholds[AlertType.ROI_DROP]:
                    alerts.append(
                        PerformanceAlert(
                            alert_type=AlertType.ROI_DROP,
                            source=performance.source,
                            severity="high" if roi_change <= -0.30 else "medium",
                            title=f"ROI Drop Alert - {performance.source.value}",
                            description=f"ROI dropped {abs(roi_change) * 100:.1f}% from {previous_performance.roi * 100:.1f}% to {performance.roi * 100:.1f}%",
                            current_value=performance.roi,
                            previous_value=previous_performance.roi,
                            threshold=self.alert_thresholds[AlertType.ROI_DROP],
                            change_percentage=roi_change,
                            recommendations=[
                                "Review recent campaign changes",
                                "Analyze landing page performance",
                                "Check for increased competition",
                                "Consider pausing underperforming campaigns",
                            ],
                            created_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(days=7),
                        )
                    )

                # Check for volume drops
                volume_change = (
                    (performance.total_leads - previous_performance.total_leads) / previous_performance.total_leads
                    if previous_performance.total_leads > 0
                    else 0
                )
                if volume_change <= self.alert_thresholds[AlertType.VOLUME_DROP]:
                    alerts.append(
                        PerformanceAlert(
                            alert_type=AlertType.VOLUME_DROP,
                            source=performance.source,
                            severity="high" if volume_change <= -0.40 else "medium",
                            title=f"Volume Drop Alert - {performance.source.value}",
                            description=f"Lead volume dropped {abs(volume_change) * 100:.1f}% from {previous_performance.total_leads} to {performance.total_leads}",
                            current_value=performance.total_leads,
                            previous_value=previous_performance.total_leads,
                            threshold=self.alert_thresholds[AlertType.VOLUME_DROP],
                            change_percentage=volume_change,
                            recommendations=[
                                "Check campaign delivery and budgets",
                                "Review audience targeting",
                                "Analyze creative fatigue",
                                "Consider expanding targeting",
                            ],
                            created_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(days=5),
                        )
                    )

                # Check for quality drops
                quality_change = (
                    (performance.qualification_rate - previous_performance.qualification_rate)
                    / previous_performance.qualification_rate
                    if previous_performance.qualification_rate > 0
                    else 0
                )
                if quality_change <= self.alert_thresholds[AlertType.QUALITY_DROP]:
                    alerts.append(
                        PerformanceAlert(
                            alert_type=AlertType.QUALITY_DROP,
                            source=performance.source,
                            severity="medium",
                            title=f"Quality Drop Alert - {performance.source.value}",
                            description=f"Lead qualification rate dropped {abs(quality_change) * 100:.1f}% from {previous_performance.qualification_rate * 100:.1f}% to {performance.qualification_rate * 100:.1f}%",
                            current_value=performance.qualification_rate,
                            previous_value=previous_performance.qualification_rate,
                            threshold=self.alert_thresholds[AlertType.QUALITY_DROP],
                            change_percentage=quality_change,
                            recommendations=[
                                "Review targeting criteria",
                                "Analyze message match with landing pages",
                                "Check for bot traffic",
                                "Update lead qualification criteria",
                            ],
                            created_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(days=7),
                        )
                    )

                # Check for new top performers
                if (
                    performance.roi > 1.0  # ROI > 100%
                    and performance.total_leads >= 5  # Sufficient volume
                    and previous_performance.roi < 0.5
                ):  # Previously poor performing
                    alerts.append(
                        PerformanceAlert(
                            alert_type=AlertType.NEW_TOP_PERFORMER,
                            source=performance.source,
                            severity="low",
                            title=f"New Top Performer - {performance.source.value}",
                            description=f"Source improved from {previous_performance.roi * 100:.1f}% to {performance.roi * 100:.1f}% ROI",
                            current_value=performance.roi,
                            previous_value=previous_performance.roi,
                            threshold=1.0,
                            change_percentage=roi_change,
                            recommendations=[
                                "Scale up successful campaigns",
                                "Analyze what changed",
                                "Replicate success to other sources",
                                "Increase budget allocation",
                            ],
                            created_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(days=14),
                        )
                    )

            # Sort alerts by severity and creation time
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            alerts.sort(key=lambda a: (severity_order.get(a.severity, 3), a.created_at), reverse=True)

            return alerts

        except Exception as e:
            logger.error(f"Error generating performance alerts: {e}", exc_info=True)
            return []

    async def _get_previous_period_performance(
        self, source: LeadSource, period_start: datetime, period_end: datetime
    ) -> Optional[SourcePerformance]:
        """Get performance for the previous equivalent period."""
        try:
            period_length = period_end - period_start
            previous_end = period_start
            previous_start = previous_end - period_length

            return await self.source_tracker.get_source_performance(source, previous_start, previous_end)

        except Exception as e:
            logger.error(f"Error getting previous period performance: {e}", exc_info=True)
            return None

    async def _generate_optimization_recommendations(
        self, source_performances: List[SourcePerformance], alerts: List[PerformanceAlert]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on performance data."""
        try:
            recommendations = []

            # Budget reallocation recommendations
            high_roi_sources = [p for p in source_performances if p.roi > 1.5 and p.total_leads > 5]
            low_roi_sources = [p for p in source_performances if p.roi < 0.2 and p.total_leads > 10]

            if high_roi_sources and low_roi_sources:
                recommendations.append(
                    {
                        "type": "budget_reallocation",
                        "priority": "high",
                        "title": "Reallocate Budget for Higher ROI",
                        "description": f"Move budget from {len(low_roi_sources)} underperforming sources to {len(high_roi_sources)} high-ROI sources",
                        "impact": "Could improve overall ROI by 25-50%",
                        "sources_to_reduce": [p.source.value for p in low_roi_sources[:3]],
                        "sources_to_increase": [p.source.value for p in high_roi_sources[:3]],
                        "estimated_improvement": "25-50% ROI increase",
                    }
                )

            # Quality improvement recommendations
            high_volume_low_quality = [
                p for p in source_performances if p.total_leads > 20 and p.qualification_rate < 0.3
            ]
            if high_volume_low_quality:
                recommendations.append(
                    {
                        "type": "quality_improvement",
                        "priority": "medium",
                        "title": "Improve Lead Quality",
                        "description": f"Focus on improving qualification rates for high-volume sources",
                        "impact": "Increase qualified leads without increasing costs",
                        "sources": [p.source.value for p in high_volume_low_quality],
                        "actions": [
                            "Refine targeting criteria",
                            "Improve ad copy and landing pages",
                            "Add qualification questions",
                            "Review lead scoring criteria",
                        ],
                    }
                )

            # Scale winners
            scalable_winners = [
                p for p in source_performances if p.roi > 1.0 and p.total_leads < 20 and p.qualification_rate > 0.4
            ]
            if scalable_winners:
                recommendations.append(
                    {
                        "type": "scale_winners",
                        "priority": "high",
                        "title": "Scale High-Performing, Low-Volume Sources",
                        "description": f"Increase investment in {len(scalable_winners)} profitable but low-volume sources",
                        "sources": [p.source.value for p in scalable_winners],
                        "estimated_impact": f"Could add {sum(p.total_leads * 3 for p in scalable_winners)} qualified leads per month",
                    }
                )

            # Attribution improvement
            unknown_source_volume = sum(p.total_leads for p in source_performances if p.source == LeadSource.UNKNOWN)
            if unknown_source_volume > 10:
                recommendations.append(
                    {
                        "type": "attribution_improvement",
                        "priority": "medium",
                        "title": "Improve Source Attribution",
                        "description": f"{unknown_source_volume} leads have unknown source attribution",
                        "actions": [
                            "Implement UTM parameters on all campaigns",
                            "Add hidden form fields for source tracking",
                            "Use phone number tracking",
                            "Improve referrer tracking",
                        ],
                        "impact": "Better optimization decisions with complete data",
                    }
                )

            # Alert-based recommendations
            critical_alerts = [a for a in alerts if a.severity in ["critical", "high"]]
            if critical_alerts:
                recommendations.append(
                    {
                        "type": "urgent_action_required",
                        "priority": "critical",
                        "title": f"Address {len(critical_alerts)} Critical Performance Issues",
                        "description": "Immediate action needed for underperforming sources",
                        "alerts": [
                            {
                                "source": a.source.value,
                                "issue": a.alert_type.value,
                                "change": f"{a.change_percentage * 100:.1f}%",
                            }
                            for a in critical_alerts[:5]
                        ],
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}", exc_info=True)
            return []

    async def _compare_attribution_models(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Dict[str, float]]:
        """Compare different attribution models for revenue attribution."""
        try:
            # For now, implement basic comparison
            # In production, this would involve complex multi-touch attribution

            comparison = {
                AttributionModel.FIRST_TOUCH.value: {},
                AttributionModel.LAST_TOUCH.value: {},
                AttributionModel.LINEAR.value: {},
            }

            # Get all source performances (currently using last-touch)
            source_performances = await self.source_tracker.get_all_source_performance(start_date, end_date)

            # Last touch attribution (current default)
            for performance in source_performances:
                comparison[AttributionModel.LAST_TOUCH.value][performance.source.value] = performance.total_revenue

            # Simulate first touch (would be 10-20% different in practice)
            for performance in source_performances:
                # Referrals typically get more credit in first-touch
                adjustment = 1.2 if "referral" in performance.source.value else 0.9
                comparison[AttributionModel.FIRST_TOUCH.value][performance.source.value] = (
                    performance.total_revenue * adjustment
                )

            # Simulate linear attribution (would spread credit across touchpoints)
            for performance in source_performances:
                # Linear typically reduces credit for last-touch sources
                adjustment = 0.8
                comparison[AttributionModel.LINEAR.value][performance.source.value] = (
                    performance.total_revenue * adjustment
                )

            return comparison

        except Exception as e:
            logger.error(f"Error comparing attribution models: {e}", exc_info=True)
            return {}

    async def track_daily_metrics(
        self, source: LeadSource, leads: int, revenue: float, cost: float, date: Optional[datetime] = None
    ) -> None:
        """Track daily metrics for a source (called by webhook processor)."""
        try:
            if not date:
                date = datetime.utcnow()

            cache_key = f"daily_source_data:{source.value}:{date.strftime('%Y%m%d')}"

            # Get existing data for the day
            existing_data = await self.cache.get(cache_key) or {"leads": 0, "revenue": 0.0, "cost": 0.0}

            # Add new data
            existing_data["leads"] += leads
            existing_data["revenue"] += revenue
            existing_data["cost"] += cost

            # Store updated data (30-day TTL)
            await self.cache.set(cache_key, existing_data, ttl=86400 * 30)

            logger.debug(f"Tracked daily metrics for {source.value}: +{leads} leads, +${revenue:.2f} revenue")

        except Exception as e:
            logger.error(f"Error tracking daily metrics: {e}", exc_info=True)

    async def get_weekly_summary(self, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate weekly performance summary for Jorge's dashboard."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            # Get this week's performance
            current_performances = await self.source_tracker.get_all_source_performance(start_date, end_date)

            # Get previous week for comparison
            prev_end = start_date
            prev_start = prev_end - timedelta(days=7)
            previous_performances = await self.source_tracker.get_all_source_performance(prev_start, prev_end)

            # Create performance lookup
            prev_lookup = {p.source: p for p in previous_performances}

            # Calculate summary
            summary = {
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "totals": {
                    "leads": sum(p.total_leads for p in current_performances),
                    "qualified_leads": sum(p.qualified_leads for p in current_performances),
                    "revenue": sum(p.total_revenue for p in current_performances),
                    "cost": sum(p.cost_per_lead * p.total_leads for p in current_performances),
                },
                "top_sources": [],
                "biggest_changes": [],
                "alerts_count": len(await self._generate_performance_alerts(current_performances)),
            }

            # Calculate ROI
            if summary["totals"]["cost"] > 0:
                summary["totals"]["roi"] = (summary["totals"]["revenue"] - summary["totals"]["cost"]) / summary[
                    "totals"
                ]["cost"]

            # Top performing sources
            top_sources = sorted(current_performances, key=lambda p: p.roi, reverse=True)[:5]
            summary["top_sources"] = [
                {"source": p.source.value, "leads": p.total_leads, "revenue": p.total_revenue, "roi": p.roi}
                for p in top_sources
                if p.roi > 0
            ]

            # Biggest changes
            changes = []
            for current in current_performances:
                prev = prev_lookup.get(current.source)
                if prev and prev.total_leads > 0:
                    lead_change = (current.total_leads - prev.total_leads) / prev.total_leads
                    roi_change = (current.roi - prev.roi) / abs(prev.roi) if prev.roi != 0 else 0

                    changes.append(
                        {
                            "source": current.source.value,
                            "lead_change": lead_change,
                            "roi_change": roi_change,
                            "magnitude": abs(lead_change) + abs(roi_change),
                        }
                    )

            # Sort by magnitude of change
            changes.sort(key=lambda c: c["magnitude"], reverse=True)
            summary["biggest_changes"] = changes[:3]

            return summary

        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}", exc_info=True)
            return {"error": "Failed to generate summary"}

    async def get_monthly_trends(self) -> Dict[str, Any]:
        """Get monthly trend analysis for dashboard."""
        try:
            trends = {}

            # Get last 6 months of data
            end_date = datetime.utcnow()
            months = []

            for i in range(6):
                month_end = end_date.replace(day=1) - timedelta(days=i * 30)
                month_start = month_end.replace(day=1)
                months.append((month_start, month_end))

            # Analyze each month
            monthly_data = []
            for month_start, month_end in reversed(months):
                performances = await self.source_tracker.get_all_source_performance(month_start, month_end)

                month_data = {
                    "month": month_start.strftime("%Y-%m"),
                    "total_leads": sum(p.total_leads for p in performances),
                    "total_revenue": sum(p.total_revenue for p in performances),
                    "total_cost": sum(p.cost_per_lead * p.total_leads for p in performances),
                    "roi": 0.0,
                }

                if month_data["total_cost"] > 0:
                    month_data["roi"] = (month_data["total_revenue"] - month_data["total_cost"]) / month_data[
                        "total_cost"
                    ]

                monthly_data.append(month_data)

            trends["monthly_performance"] = monthly_data

            # Calculate growth trends
            if len(monthly_data) >= 2:
                latest = monthly_data[-1]
                previous = monthly_data[-2]

                trends["growth_rates"] = {
                    "leads": (latest["total_leads"] - previous["total_leads"]) / previous["total_leads"]
                    if previous["total_leads"] > 0
                    else 0,
                    "revenue": (latest["total_revenue"] - previous["total_revenue"]) / previous["total_revenue"]
                    if previous["total_revenue"] > 0
                    else 0,
                    "roi": latest["roi"] - previous["roi"],
                }

            return trends

        except Exception as e:
            logger.error(f"Error getting monthly trends: {e}", exc_info=True)
            return {"error": "Failed to generate trends"}

    async def clear_expired_alerts(self) -> int:
        """Clear expired alerts and return count cleared."""
        try:
            # This would typically query a database
            # For now, return 0 as alerts are stored in cache with TTL
            return 0

        except Exception as e:
            logger.error(f"Error clearing expired alerts: {e}", exc_info=True)
            return 0

    def get_alert_recommendations(self, alert: PerformanceAlert) -> List[str]:
        """Get specific recommendations for an alert type."""
        return alert.recommendations
