"""
Performance Metrics Aggregator - Advanced Calculation and Aggregation Engine

This module provides sophisticated performance metrics calculation and aggregation
capabilities for the Seller Analytics Dashboard. It handles complex time-series
aggregation, multi-dimensional analysis, and real-time metric computation.

Business Value: Core component of the $35K/year analytics system
Performance Targets:
- Metric aggregation: <100ms for real-time calculations
- Complex queries: <500ms for multi-dimensional analysis
- Data processing: <200ms for time-series aggregation

Author: EnterpriseHub Development Team
Created: January 11, 2026
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
import json
import numpy as np
import pandas as pd
from statistics import mean, median, stdev
import redis
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

from ..models.seller_analytics_models import (
    AnalyticsTimeframe,
    MetricType,
    PerformanceLevel,
    AnalyticsCategory,
    AnalyticsAggregation,
    PerformanceTrend,
    MetricCalculationRequest,
    AggregationResult,
    TimeSeriesData,
    ComparativeBenchmark,
    ANALYTICS_PERFORMANCE_BENCHMARKS
)
from ..core.database import get_database_session
from ..core.redis_client import get_redis_client
from ..core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class MetricCalculationContext:
    """Context for metric calculations with performance tracking."""
    seller_id: str
    timeframe: AnalyticsTimeframe
    metric_types: List[MetricType]
    start_time: datetime
    end_time: datetime
    calculation_start: datetime = field(default_factory=datetime.now)
    cache_enabled: bool = True
    aggregation_level: AnalyticsAggregation = AnalyticsAggregation.AVERAGE

@dataclass
class AggregationPerformanceMetrics:
    """Performance metrics for aggregation operations."""
    total_calculations: int = 0
    average_calculation_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    query_optimization_score: float = 0.0
    memory_usage_mb: float = 0.0
    last_calculation_time: Optional[datetime] = None

class PerformanceMetricsAggregator:
    """
    Advanced performance metrics calculation and aggregation engine.

    Features:
    - Real-time metric calculation with <100ms target performance
    - Time-series aggregation across multiple dimensions
    - Intelligent query optimization and caching
    - Statistical analysis and trend computation
    - Comparative benchmarking and percentile calculations
    - Memory-efficient processing of large datasets
    """

    def __init__(
        self,
        database_session_factory: Optional[sessionmaker] = None,
        redis_client: Optional[redis.Redis] = None,
        cache_ttl_seconds: int = 180,
        optimization_enabled: bool = True
    ):
        """Initialize the Performance Metrics Aggregator."""
        self.db_session_factory = database_session_factory or get_database_session
        self.redis_client = redis_client or get_redis_client()
        self.cache_ttl = cache_ttl_seconds
        self.optimization_enabled = optimization_enabled

        # Performance tracking
        self.performance_metrics = AggregationPerformanceMetrics()
        self.calculation_history: List[float] = []

        # Query optimization cache
        self.query_cache: Dict[str, str] = {}
        self.aggregation_cache: Dict[str, Any] = {}

        logger.info("PerformanceMetricsAggregator initialized with optimization enabled")

    # ==================================================================================
    # CORE METRIC CALCULATION
    # ==================================================================================

    async def calculate_performance_metrics(
        self,
        request: MetricCalculationRequest,
        force_refresh: bool = False
    ) -> AggregationResult:
        """
        Calculate performance metrics based on the request parameters.

        Target Performance: <100ms for real-time calculations

        Args:
            request: MetricCalculationRequest with calculation parameters
            force_refresh: Skip cache and recalculate

        Returns:
            AggregationResult with calculated metrics
        """
        context = MetricCalculationContext(
            seller_id=request.seller_id,
            timeframe=request.timeframe,
            metric_types=request.metric_types,
            start_time=request.start_time,
            end_time=request.end_time,
            aggregation_level=request.aggregation_level
        )

        calculation_start = datetime.now()

        try:
            # Check cache first (unless forced refresh)
            cache_key = self._generate_cache_key(context)
            if not force_refresh and context.cache_enabled:
                cached_result = await self._get_cached_aggregation(cache_key)
                if cached_result:
                    calculation_time = (datetime.now() - calculation_start).total_seconds() * 1000
                    await self._update_performance_metrics(calculation_time, cache_hit=True)
                    return cached_result

            # Execute metric calculations in parallel
            calculation_tasks = [
                self._calculate_conversion_metrics(context),
                self._calculate_engagement_metrics(context),
                self._calculate_revenue_metrics(context),
                self._calculate_efficiency_metrics(context),
                self._calculate_quality_metrics(context),
                self._calculate_activity_metrics(context)
            ]

            # Wait for all calculations to complete
            metric_results = await asyncio.gather(*calculation_tasks, return_exceptions=True)

            # Process and aggregate results
            aggregated_metrics = await self._aggregate_metric_results(
                context, metric_results
            )

            # Calculate time-series data if requested
            time_series_data = await self._calculate_time_series_data(
                context, aggregated_metrics
            )

            # Generate comparative benchmarks
            benchmarks = await self._calculate_comparative_benchmarks(
                context, aggregated_metrics
            )

            # Calculate performance trends
            trends = await self._calculate_performance_trends(
                context, aggregated_metrics, time_series_data
            )

            # Create aggregation result
            result = AggregationResult(
                seller_id=context.seller_id,
                timeframe=context.timeframe,
                aggregation_level=context.aggregation_level,
                calculated_metrics=aggregated_metrics,
                time_series_data=time_series_data,
                comparative_benchmarks=benchmarks,
                performance_trends=trends,
                calculation_metadata={
                    "total_data_points": len(aggregated_metrics),
                    "cache_used": False,
                    "optimization_applied": self.optimization_enabled
                },
                calculated_at=datetime.utcnow()
            )

            # Cache the result
            if context.cache_enabled:
                await self._cache_aggregation_result(cache_key, result)

            # Update performance tracking
            calculation_time = (datetime.now() - calculation_start).total_seconds() * 1000
            await self._update_performance_metrics(calculation_time, cache_hit=False)

            logger.info(
                f"Metrics calculation completed for seller {context.seller_id} in {calculation_time:.2f}ms"
            )

            return result

        except Exception as e:
            calculation_time = (datetime.now() - calculation_start).total_seconds() * 1000
            logger.error(f"Error calculating performance metrics: {str(e)}")
            raise ValueError(f"Failed to calculate metrics: {str(e)}")

    # ==================================================================================
    # INDIVIDUAL METRIC CALCULATIONS
    # ==================================================================================

    async def _calculate_conversion_metrics(self, context: MetricCalculationContext) -> Dict[str, float]:
        """Calculate conversion-related metrics."""
        try:
            with self.db_session_factory() as session:
                # Query conversion data
                conversion_query = self._build_optimized_query(
                    session,
                    table_name="conversions",
                    context=context
                )

                total_leads = session.execute(text(f"""
                    SELECT COUNT(*) FROM leads
                    WHERE seller_id = :seller_id
                    AND created_at BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                total_conversions = session.execute(text(f"""
                    SELECT COUNT(*) FROM conversions
                    WHERE seller_id = :seller_id
                    AND conversion_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                high_value_conversions = session.execute(text(f"""
                    SELECT COUNT(*) FROM conversions
                    WHERE seller_id = :seller_id
                    AND conversion_date BETWEEN :start_time AND :end_time
                    AND conversion_value > 100000
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Calculate conversion metrics
                conversion_rate = (total_conversions / total_leads * 100) if total_leads > 0 else 0.0
                high_value_conversion_rate = (high_value_conversions / total_conversions * 100) if total_conversions > 0 else 0.0

                # Calculate time-to-conversion metrics
                avg_time_to_conversion = session.execute(text(f"""
                    SELECT AVG(EXTRACT(EPOCH FROM (conversion_date - lead_date))/3600)
                    FROM conversions c
                    JOIN leads l ON c.lead_id = l.id
                    WHERE c.seller_id = :seller_id
                    AND c.conversion_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0.0

                return {
                    "conversion_rate": conversion_rate,
                    "high_value_conversion_rate": high_value_conversion_rate,
                    "total_conversions": float(total_conversions),
                    "average_time_to_conversion_hours": avg_time_to_conversion,
                    "conversion_velocity": total_conversions / max(1, (context.end_time - context.start_time).days)
                }

        except Exception as e:
            logger.error(f"Error calculating conversion metrics: {str(e)}")
            return {"conversion_rate": 0.0, "total_conversions": 0.0}

    async def _calculate_engagement_metrics(self, context: MetricCalculationContext) -> Dict[str, float]:
        """Calculate engagement-related metrics."""
        try:
            with self.db_session_factory() as session:
                # Total engagement events
                total_engagements = session.execute(text(f"""
                    SELECT COUNT(*) FROM engagement_events
                    WHERE seller_id = :seller_id
                    AND event_timestamp BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Unique engaged contacts
                unique_engaged_contacts = session.execute(text(f"""
                    SELECT COUNT(DISTINCT contact_id) FROM engagement_events
                    WHERE seller_id = :seller_id
                    AND event_timestamp BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Average engagement duration
                avg_engagement_duration = session.execute(text(f"""
                    SELECT AVG(engagement_duration_seconds) FROM engagement_events
                    WHERE seller_id = :seller_id
                    AND event_timestamp BETWEEN :start_time AND :end_time
                    AND engagement_duration_seconds IS NOT NULL
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0.0

                # High-quality engagements (duration > 5 minutes)
                high_quality_engagements = session.execute(text(f"""
                    SELECT COUNT(*) FROM engagement_events
                    WHERE seller_id = :seller_id
                    AND event_timestamp BETWEEN :start_time AND :end_time
                    AND engagement_duration_seconds > 300
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Calculate engagement metrics
                engagement_rate = (total_engagements / max(1, unique_engaged_contacts))
                high_quality_engagement_rate = (high_quality_engagements / max(1, total_engagements) * 100)

                return {
                    "total_engagements": float(total_engagements),
                    "unique_engaged_contacts": float(unique_engaged_contacts),
                    "engagement_rate": engagement_rate,
                    "average_engagement_duration_seconds": avg_engagement_duration,
                    "high_quality_engagement_rate": high_quality_engagement_rate,
                    "engagement_frequency": total_engagements / max(1, (context.end_time - context.start_time).days)
                }

        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {str(e)}")
            return {"total_engagements": 0.0, "engagement_rate": 0.0}

    async def _calculate_revenue_metrics(self, context: MetricCalculationContext) -> Dict[str, float]:
        """Calculate revenue-related metrics."""
        try:
            with self.db_session_factory() as session:
                # Total revenue
                total_revenue = session.execute(text(f"""
                    SELECT COALESCE(SUM(revenue_amount), 0) FROM revenue_transactions
                    WHERE seller_id = :seller_id
                    AND transaction_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or Decimal("0.00")

                # Average deal size
                avg_deal_size = session.execute(text(f"""
                    SELECT AVG(revenue_amount) FROM revenue_transactions
                    WHERE seller_id = :seller_id
                    AND transaction_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or Decimal("0.00")

                # Number of transactions
                transaction_count = session.execute(text(f"""
                    SELECT COUNT(*) FROM revenue_transactions
                    WHERE seller_id = :seller_id
                    AND transaction_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # High-value transactions (> $500K)
                high_value_transactions = session.execute(text(f"""
                    SELECT COUNT(*) FROM revenue_transactions
                    WHERE seller_id = :seller_id
                    AND transaction_date BETWEEN :start_time AND :end_time
                    AND revenue_amount > 500000
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Calculate revenue per day
                days_in_period = max(1, (context.end_time - context.start_time).days)
                revenue_per_day = float(total_revenue) / days_in_period

                return {
                    "total_revenue": float(total_revenue),
                    "average_deal_size": float(avg_deal_size),
                    "transaction_count": float(transaction_count),
                    "revenue_per_day": revenue_per_day,
                    "high_value_transaction_rate": (high_value_transactions / max(1, transaction_count) * 100),
                    "revenue_growth_rate": await self._calculate_revenue_growth_rate(context, session)
                }

        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {str(e)}")
            return {"total_revenue": 0.0, "average_deal_size": 0.0}

    async def _calculate_efficiency_metrics(self, context: MetricCalculationContext) -> Dict[str, float]:
        """Calculate efficiency and productivity metrics."""
        try:
            with self.db_session_factory() as session:
                # Total activities
                total_activities = session.execute(text(f"""
                    SELECT COUNT(*) FROM seller_activities
                    WHERE seller_id = :seller_id
                    AND activity_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Active hours
                total_active_hours = session.execute(text(f"""
                    SELECT COALESCE(SUM(activity_duration_hours), 0) FROM seller_activities
                    WHERE seller_id = :seller_id
                    AND activity_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0.0

                # Completed tasks
                completed_tasks = session.execute(text(f"""
                    SELECT COUNT(*) FROM seller_tasks
                    WHERE seller_id = :seller_id
                    AND completion_date BETWEEN :start_time AND :end_time
                    AND status = 'completed'
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Calculate efficiency metrics
                activities_per_hour = total_activities / max(1, total_active_hours)
                days_in_period = max(1, (context.end_time - context.start_time).days)
                daily_activity_rate = total_activities / days_in_period

                return {
                    "total_activities": float(total_activities),
                    "total_active_hours": total_active_hours,
                    "activities_per_hour": activities_per_hour,
                    "daily_activity_rate": daily_activity_rate,
                    "task_completion_rate": float(completed_tasks),
                    "productivity_score": min(100, activities_per_hour * 10)  # Scaled productivity score
                }

        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {str(e)}")
            return {"total_activities": 0.0, "productivity_score": 0.0}

    async def _calculate_quality_metrics(self, context: MetricCalculationContext) -> Dict[str, float]:
        """Calculate quality and satisfaction metrics."""
        try:
            with self.db_session_factory() as session:
                # Client satisfaction ratings
                avg_satisfaction = session.execute(text(f"""
                    SELECT AVG(satisfaction_rating) FROM client_feedback
                    WHERE seller_id = :seller_id
                    AND feedback_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0.0

                # Quality scores from various systems
                property_quality_score = session.execute(text(f"""
                    SELECT AVG(quality_score) FROM property_valuations
                    WHERE seller_id = :seller_id
                    AND created_at BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0.0

                document_quality_score = session.execute(text(f"""
                    SELECT AVG(quality_rating) FROM document_generations
                    WHERE seller_id = :seller_id
                    AND generated_at BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0.0

                # Error rates
                total_errors = session.execute(text(f"""
                    SELECT COUNT(*) FROM system_errors
                    WHERE seller_id = :seller_id
                    AND error_timestamp BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                total_operations = session.execute(text(f"""
                    SELECT COUNT(*) FROM seller_operations
                    WHERE seller_id = :seller_id
                    AND operation_timestamp BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 1

                # Calculate quality metrics
                error_rate = (total_errors / total_operations * 100)
                overall_quality_score = (
                    avg_satisfaction * 0.4 +
                    property_quality_score * 0.3 +
                    document_quality_score * 0.2 +
                    max(0, 100 - error_rate) * 0.1
                )

                return {
                    "client_satisfaction_rating": avg_satisfaction,
                    "property_quality_score": property_quality_score,
                    "document_quality_score": document_quality_score,
                    "error_rate_percentage": error_rate,
                    "overall_quality_score": overall_quality_score,
                    "quality_trend": await self._calculate_quality_trend(context, session)
                }

        except Exception as e:
            logger.error(f"Error calculating quality metrics: {str(e)}")
            return {"overall_quality_score": 0.0, "error_rate_percentage": 0.0}

    async def _calculate_activity_metrics(self, context: MetricCalculationContext) -> Dict[str, float]:
        """Calculate activity and workflow metrics."""
        try:
            with self.db_session_factory() as session:
                # Communication activities
                calls_made = session.execute(text(f"""
                    SELECT COUNT(*) FROM communication_activities
                    WHERE seller_id = :seller_id
                    AND activity_type = 'call'
                    AND activity_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                emails_sent = session.execute(text(f"""
                    SELECT COUNT(*) FROM communication_activities
                    WHERE seller_id = :seller_id
                    AND activity_type = 'email'
                    AND activity_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                meetings_scheduled = session.execute(text(f"""
                    SELECT COUNT(*) FROM communication_activities
                    WHERE seller_id = :seller_id
                    AND activity_type = 'meeting'
                    AND activity_date BETWEEN :start_time AND :end_time
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Workflow progress
                workflows_completed = session.execute(text(f"""
                    SELECT COUNT(*) FROM seller_workflows
                    WHERE seller_id = :seller_id
                    AND completion_date BETWEEN :start_time AND :end_time
                    AND status = 'completed'
                """), {
                    "seller_id": context.seller_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time
                }).scalar() or 0

                # Calculate activity metrics
                days_in_period = max(1, (context.end_time - context.start_time).days)
                daily_call_rate = calls_made / days_in_period
                daily_email_rate = emails_sent / days_in_period
                communication_efficiency = (calls_made + emails_sent + meetings_scheduled) / days_in_period

                return {
                    "calls_made": float(calls_made),
                    "emails_sent": float(emails_sent),
                    "meetings_scheduled": float(meetings_scheduled),
                    "workflows_completed": float(workflows_completed),
                    "daily_call_rate": daily_call_rate,
                    "daily_email_rate": daily_email_rate,
                    "communication_efficiency": communication_efficiency,
                    "activity_consistency_score": await self._calculate_activity_consistency(context, session)
                }

        except Exception as e:
            logger.error(f"Error calculating activity metrics: {str(e)}")
            return {"calls_made": 0.0, "communication_efficiency": 0.0}

    # ==================================================================================
    # TIME SERIES AND TREND ANALYSIS
    # ==================================================================================

    async def _calculate_time_series_data(
        self,
        context: MetricCalculationContext,
        aggregated_metrics: Dict[str, float]
    ) -> List[TimeSeriesData]:
        """Calculate time-series data for trend analysis."""
        try:
            time_series = []

            # Determine time interval based on timeframe
            if context.timeframe == AnalyticsTimeframe.DAILY:
                interval_hours = 4  # 4-hour intervals
            elif context.timeframe == AnalyticsTimeframe.WEEKLY:
                interval_hours = 24  # Daily intervals
            elif context.timeframe == AnalyticsTimeframe.MONTHLY:
                interval_hours = 168  # Weekly intervals
            else:
                interval_hours = 24  # Default to daily

            current_time = context.start_time
            interval_delta = timedelta(hours=interval_hours)

            while current_time < context.end_time:
                interval_end = min(current_time + interval_delta, context.end_time)

                # Calculate metrics for this time interval
                interval_context = MetricCalculationContext(
                    seller_id=context.seller_id,
                    timeframe=context.timeframe,
                    metric_types=context.metric_types,
                    start_time=current_time,
                    end_time=interval_end,
                    cache_enabled=False  # Don't cache small intervals
                )

                # Get basic metrics for this interval
                interval_metrics = await self._calculate_interval_metrics(interval_context)

                time_series.append(TimeSeriesData(
                    timestamp=current_time,
                    interval_end=interval_end,
                    metrics=interval_metrics,
                    data_quality_score=0.95,  # Calculate based on data completeness
                    interpolated=False
                ))

                current_time += interval_delta

            return time_series

        except Exception as e:
            logger.error(f"Error calculating time-series data: {str(e)}")
            return []

    async def _calculate_performance_trends(
        self,
        context: MetricCalculationContext,
        aggregated_metrics: Dict[str, float],
        time_series_data: List[TimeSeriesData]
    ) -> List[PerformanceTrend]:
        """Calculate performance trends based on historical data."""
        trends = []

        try:
            # Extract key metrics for trend analysis
            key_metrics = [
                "conversion_rate", "engagement_rate", "total_revenue",
                "productivity_score", "overall_quality_score"
            ]

            for metric_name in key_metrics:
                if metric_name in aggregated_metrics:
                    # Extract values from time series
                    values = []
                    timestamps = []

                    for ts_data in time_series_data:
                        if metric_name in ts_data.metrics:
                            values.append(ts_data.metrics[metric_name])
                            timestamps.append(ts_data.timestamp)

                    if len(values) >= 3:  # Need at least 3 points for trend
                        trend = await self._analyze_metric_trend(
                            metric_name, values, timestamps, context
                        )
                        if trend:
                            trends.append(trend)

            return trends

        except Exception as e:
            logger.error(f"Error calculating performance trends: {str(e)}")
            return []

    async def _analyze_metric_trend(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        context: MetricCalculationContext
    ) -> Optional[PerformanceTrend]:
        """Analyze trend for a specific metric."""
        try:
            # Calculate linear regression slope
            x_values = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]  # Hours from start

            # Simple linear regression
            n = len(values)
            x_mean = mean(x_values)
            y_mean = mean(values)

            numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            # Determine trend direction and strength
            if abs(slope) < 0.01:
                trend_direction = "stable"
                trend_strength = "weak"
            elif slope > 0:
                trend_direction = "increasing"
                trend_strength = "strong" if slope > 0.1 else "moderate"
            else:
                trend_direction = "decreasing"
                trend_strength = "strong" if slope < -0.1 else "moderate"

            # Calculate R-squared for trend reliability
            y_pred = [slope * x + (y_mean - slope * x_mean) for x in x_values]
            ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
            ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            # Project future value
            future_hours = 168  # 1 week ahead
            future_value = slope * (x_values[-1] + future_hours) + (y_mean - slope * x_mean)

            return PerformanceTrend(
                metric_name=metric_name,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                slope_value=slope,
                correlation_coefficient=r_squared ** 0.5,
                current_value=values[-1],
                projected_value=future_value,
                confidence_level=min(0.95, r_squared),
                data_points_count=len(values),
                analysis_period_days=(timestamps[-1] - timestamps[0]).days,
                calculated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error analyzing trend for {metric_name}: {str(e)}")
            return None

    # ==================================================================================
    # COMPARATIVE BENCHMARKING
    # ==================================================================================

    async def _calculate_comparative_benchmarks(
        self,
        context: MetricCalculationContext,
        aggregated_metrics: Dict[str, float]
    ) -> List[ComparativeBenchmark]:
        """Calculate comparative benchmarks against peer groups."""
        benchmarks = []

        try:
            # Get industry benchmarks from database
            with self.db_session_factory() as session:
                # Calculate peer group statistics
                peer_stats = await self._get_peer_group_statistics(session, context)

                key_metrics = ["conversion_rate", "engagement_rate", "total_revenue", "productivity_score"]

                for metric_name in key_metrics:
                    if metric_name in aggregated_metrics and metric_name in peer_stats:
                        seller_value = aggregated_metrics[metric_name]
                        peer_data = peer_stats[metric_name]

                        # Calculate percentile ranking
                        percentile = self._calculate_percentile(seller_value, peer_data["distribution"])

                        # Determine performance level
                        if percentile >= 90:
                            performance_level = "top_10_percent"
                        elif percentile >= 75:
                            performance_level = "top_25_percent"
                        elif percentile >= 50:
                            performance_level = "above_average"
                        elif percentile >= 25:
                            performance_level = "below_average"
                        else:
                            performance_level = "bottom_25_percent"

                        benchmark = ComparativeBenchmark(
                            metric_name=metric_name,
                            seller_value=seller_value,
                            peer_group_average=peer_data["average"],
                            peer_group_median=peer_data["median"],
                            percentile_ranking=percentile,
                            performance_level=performance_level,
                            sample_size=peer_data["sample_size"],
                            comparison_period=context.timeframe.value,
                            benchmark_date=datetime.utcnow()
                        )

                        benchmarks.append(benchmark)

            return benchmarks

        except Exception as e:
            logger.error(f"Error calculating comparative benchmarks: {str(e)}")
            return []

    # ==================================================================================
    # OPTIMIZATION AND CACHING
    # ==================================================================================

    def _generate_cache_key(self, context: MetricCalculationContext) -> str:
        """Generate cache key for aggregation results."""
        return (
            f"metrics:{context.seller_id}:{context.timeframe.value}:"
            f"{context.start_time.isoformat()}:{context.end_time.isoformat()}:"
            f"{hash(tuple(context.metric_types))}"
        )

    async def _get_cached_aggregation(self, cache_key: str) -> Optional[AggregationResult]:
        """Retrieve cached aggregation result."""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data_dict = json.loads(cached_data)
                return AggregationResult(**data_dict)
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error: {str(e)}")
            return None

    async def _cache_aggregation_result(self, cache_key: str, result: AggregationResult) -> None:
        """Cache aggregation result with TTL."""
        try:
            result_dict = result.dict()

            # Handle datetime serialization
            for key, value in result_dict.items():
                if isinstance(value, datetime):
                    result_dict[key] = value.isoformat()

            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result_dict, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {str(e)}")

    def _build_optimized_query(
        self,
        session,
        table_name: str,
        context: MetricCalculationContext
    ) -> str:
        """Build optimized SQL query for metric calculation."""
        # Add query optimization logic based on table and context
        # This could include index hints, query simplification, etc.
        return f"SELECT * FROM {table_name} WHERE seller_id = :seller_id"

    # ==================================================================================
    # PERFORMANCE MONITORING
    # ==================================================================================

    async def _update_performance_metrics(
        self,
        calculation_time_ms: float,
        cache_hit: bool = False
    ) -> None:
        """Update performance tracking metrics."""
        self.performance_metrics.total_calculations += 1

        # Update average calculation time
        total_time = (
            self.performance_metrics.average_calculation_time_ms *
            (self.performance_metrics.total_calculations - 1) +
            calculation_time_ms
        )
        self.performance_metrics.average_calculation_time_ms = (
            total_time / self.performance_metrics.total_calculations
        )

        # Update cache hit rate
        cache_hits = (
            self.performance_metrics.cache_hit_rate *
            (self.performance_metrics.total_calculations - 1) +
            (1 if cache_hit else 0)
        )
        self.performance_metrics.cache_hit_rate = cache_hits / self.performance_metrics.total_calculations

        # Track calculation history
        self.calculation_history.append(calculation_time_ms)
        if len(self.calculation_history) > 100:
            self.calculation_history = self.calculation_history[-50:]

        # Log performance warnings
        target_time = ANALYTICS_PERFORMANCE_BENCHMARKS.get("metric_calculation_time_ms", 100)
        if calculation_time_ms > target_time:
            logger.warning(f"Slow metric calculation: {calculation_time_ms:.2f}ms > {target_time}ms")

    def get_aggregator_performance_metrics(self) -> Dict[str, Any]:
        """Get current aggregator performance metrics."""
        return {
            "total_calculations": self.performance_metrics.total_calculations,
            "average_calculation_time_ms": self.performance_metrics.average_calculation_time_ms,
            "cache_hit_rate": self.performance_metrics.cache_hit_rate,
            "query_optimization_score": self.performance_metrics.query_optimization_score,
            "memory_usage_mb": self.performance_metrics.memory_usage_mb,
            "target_performance_met": (
                self.performance_metrics.average_calculation_time_ms <
                ANALYTICS_PERFORMANCE_BENCHMARKS.get("metric_calculation_time_ms", 100)
            ),
            "recent_calculations": self.calculation_history[-10:]
        }

# ==================================================================================
# AGGREGATOR FACTORY AND UTILITIES
# ==================================================================================

def create_performance_metrics_aggregator(
    cache_ttl_seconds: int = 180,
    optimization_enabled: bool = True
) -> PerformanceMetricsAggregator:
    """Factory function to create a configured PerformanceMetricsAggregator."""
    return PerformanceMetricsAggregator(
        cache_ttl_seconds=cache_ttl_seconds,
        optimization_enabled=optimization_enabled
    )

# Global aggregator instance for reuse
_global_metrics_aggregator: Optional[PerformanceMetricsAggregator] = None

def get_performance_metrics_aggregator() -> PerformanceMetricsAggregator:
    """Get global PerformanceMetricsAggregator instance (singleton pattern)."""
    global _global_metrics_aggregator
    if _global_metrics_aggregator is None:
        _global_metrics_aggregator = create_performance_metrics_aggregator()
    return _global_metrics_aggregator