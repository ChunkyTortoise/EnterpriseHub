"""
Enhanced SHAP Analytics Service for Advanced Interactive Visualization

Extends the existing SHAPExplainerService with Recharts-compatible data generation,
feature trend analysis, and real-time WebSocket event publishing for the advanced
analytics dashboard.

Performance Targets:
- SHAP waterfall generation: <30ms (leveraging existing infrastructure)
- Feature trend analysis: <50ms (database query + aggregation)
- WebSocket event publishing: <10ms
- Cache hit rate: >70% with intelligent TTL management

Integration Points:
- Extends existing SHAPExplainerService from shap_explainer_service.py
- Uses existing cache_service patterns for performance
- Integrates with websocket_server.py for real-time updates
- Publishes events through event_publisher.py
"""

import asyncio
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

from ghl_real_estate_ai.api.schemas.analytics import (
    FeatureTrendPoint,
    SHAPWaterfallData,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.shap_explainer_service import get_shap_explainer_service

logger = get_logger(__name__)


@dataclass
class FeatureImportanceData:
    """Enhanced feature importance with business context."""

    feature_name: str
    shap_value: float
    feature_value: float
    business_explanation: str
    importance_rank: int
    confidence_score: float
    trend_direction: str  # "increasing", "decreasing", "stable"


@dataclass
class SHAPAnalysisResult:
    """Complete SHAP analysis result with metadata."""

    lead_id: str
    waterfall_data: SHAPWaterfallData
    feature_importance: List[FeatureImportanceData]
    prediction_confidence: float
    processing_time_ms: float
    cached: bool
    analysis_timestamp: datetime


class SHAPAnalyticsEnhanced:
    """
    Enhanced SHAP analytics service with interactive visualization capabilities.

    Extends the existing SHAPExplainerService with:
    - Recharts-compatible waterfall chart data
    - Feature trend analysis over time
    - Real-time WebSocket event publishing
    - Enhanced caching with semantic similarity
    - Performance optimization for sub-30ms response times
    """

    def __init__(self):
        """Initialize enhanced SHAP analytics with existing service integration."""
        self.base_shap_service = get_shap_explainer_service()
        self.cache_service = get_cache_service()
        self.event_publisher = get_event_publisher()

        # Performance tracking
        self._performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "avg_processing_time_ms": 0.0,
            "last_reset": datetime.utcnow(),
        }

        # Feature business mappings for enhanced explanations
        self._feature_business_map = {
            "response_time_hours": "Response Speed to Lead",
            "message_length_avg": "Message Detail Level",
            "timeline_urgency": "Urgency Indicators",
            "financial_readiness": "Financial Qualification",
            "property_specificity": "Property Requirements Clarity",
            "engagement_score": "Lead Engagement Level",
            "follow_up_compliance": "Follow-up Consistency",
        }

        logger.info("SHAPAnalyticsEnhanced initialized with existing service integration")

    async def generate_waterfall_data(
        self, lead_id: str, include_comparison: bool = False, comparison_lead_ids: Optional[List[str]] = None
    ) -> SHAPWaterfallData:
        """
        Generate Recharts-compatible waterfall chart data for interactive visualization.

        Performance target: <30ms (leveraging existing SHAP calculation + data transformation)
        Cache strategy: 5-minute TTL with lead_id + feature_hash key for consistency

        Args:
            lead_id: Primary lead identifier
            include_comparison: Whether to include comparative analysis
            comparison_lead_ids: Optional lead IDs for comparison

        Returns:
            SHAPWaterfallData: Recharts-compatible waterfall chart data

        Raises:
            ValueError: If lead_id is invalid or data insufficient
            RuntimeError: If SHAP calculation fails
        """
        start_time = time.time()
        self._performance_metrics["total_requests"] += 1

        try:
            # Generate cache key based on lead and comparison state
            cache_key_data = {
                "lead_id": lead_id,
                "comparison": include_comparison,
                "comparison_ids": sorted(comparison_lead_ids) if comparison_lead_ids else None,
            }
            cache_key = f"shap:waterfall:{hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()}"

            # Check cache first for performance
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                self._performance_metrics["cache_hits"] += 1
                logger.debug(f"Cache hit for SHAP waterfall: {lead_id}")

                # Update performance metrics
                processing_time_ms = (time.time() - start_time) * 1000
                self._update_performance_metrics(processing_time_ms)

                return SHAPWaterfallData(**cached_result)

            # Get base SHAP explanation from existing service
            logger.debug(f"Generating SHAP explanation for lead: {lead_id}")
            explanation = await self.base_shap_service.explain_prediction(
                lead_id=lead_id, include_feature_values=True, include_business_context=True
            )

            if not explanation or not hasattr(explanation, "shap_values"):
                raise ValueError(f"No valid SHAP explanation available for lead {lead_id}")

            # Transform to Recharts-compatible format
            waterfall_data = await self._build_waterfall_structure(explanation, include_comparison, comparison_lead_ids)

            # Cache result with TTL
            await self.cache_service.set(cache_key, asdict(waterfall_data), ttl=300)  # 5 minutes

            # Publish real-time update event
            await self._publish_shap_update_event(lead_id, waterfall_data)

            # Update performance metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time_ms)

            logger.info(f"SHAP waterfall generated for {lead_id} in {processing_time_ms:.1f}ms")
            return waterfall_data

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"SHAP waterfall generation failed for {lead_id}: {e} (took {processing_time_ms:.1f}ms)")
            raise RuntimeError(f"Failed to generate SHAP waterfall: {str(e)}")

    async def _build_waterfall_structure(
        self, explanation, include_comparison: bool, comparison_lead_ids: Optional[List[str]]
    ) -> SHAPWaterfallData:
        """
        Build Recharts-compatible waterfall chart structure from SHAP explanation.

        Creates sorted features by absolute importance, cumulative values for waterfall effect,
        and business-friendly labels with appropriate color coding.
        """
        # Extract and sort features by absolute SHAP value importance
        shap_values_dict = explanation.shap_values
        sorted_features = sorted(shap_values_dict.items(), key=lambda x: abs(x[1]), reverse=True)

        # Build waterfall data structures
        features = []
        shap_values = []
        cumulative_values = []
        feature_labels = []
        colors = []
        feature_metadata = {}

        # Start with base value (expected value)
        cumulative = explanation.base_value

        for feature, shap_val in sorted_features:
            features.append(feature)
            shap_values.append(shap_val)

            # Update cumulative for waterfall effect
            cumulative += shap_val
            cumulative_values.append(cumulative)

            # Color coding: positive = green, negative = red
            colors.append("#10b981" if shap_val > 0 else "#ef4444")

            # Business-friendly feature labels
            business_label = self._feature_business_map.get(feature, feature.replace("_", " ").title())
            feature_labels.append(business_label)

            # Feature metadata for enhanced tooltips
            feature_metadata[feature] = {
                "business_name": business_label,
                "impact_direction": "positive" if shap_val > 0 else "negative",
                "importance_rank": len(features),
                "feature_value": explanation.feature_values.get(feature, "N/A"),
                "explanation": await self._get_feature_business_explanation(feature, shap_val),
            }

        return SHAPWaterfallData(
            base_value=explanation.base_value,
            final_prediction=explanation.prediction_value,
            features=features,
            shap_values=shap_values,
            cumulative_values=cumulative_values,
            feature_labels=feature_labels,
            colors=colors,
            feature_metadata=feature_metadata,
        )

    async def generate_feature_trend_data(
        self, feature_name: str, time_range_days: int = 30, granularity: str = "daily"
    ) -> List[FeatureTrendPoint]:
        """
        Generate feature value trends over time for time-series visualization.

        Performance target: <50ms (database query + aggregation)
        Cache strategy: 15-minute TTL for trend data to balance freshness vs performance

        Args:
            feature_name: Name of the feature to analyze
            time_range_days: Number of days to analyze
            granularity: Time granularity ("daily", "hourly", "weekly")

        Returns:
            List[FeatureTrendPoint]: Time-series data points for charting

        Raises:
            ValueError: If feature_name is invalid or time range too large
        """
        start_time = time.time()

        # Validate inputs
        if not feature_name or time_range_days <= 0:
            raise ValueError("Invalid feature name or time range")

        if time_range_days > 365:
            raise ValueError("Time range cannot exceed 365 days")

        # Cache key for trend data
        cache_key = f"shap:trend:{feature_name}:{time_range_days}:{granularity}"
        cached_result = await self.cache_service.get(cache_key)

        if cached_result:
            logger.debug(f"Cache hit for feature trend: {feature_name}")
            return [FeatureTrendPoint(**point) for point in cached_result]

        try:
            # Query historical feature values from ML scoring history
            logger.debug(f"Querying feature trends for {feature_name} over {time_range_days} days")

            trend_data = await self._query_feature_trends(feature_name, time_range_days, granularity)

            # Format for time-series visualization
            formatted_points = []
            for point in trend_data:
                trend_point = FeatureTrendPoint(
                    date=point["date"],
                    avg_value=point["avg_value"],
                    min_value=point["min_value"],
                    max_value=point["max_value"],
                    lead_count=point["lead_count"],
                    percentile_25=point.get("p25"),
                    percentile_75=point.get("p75"),
                )
                formatted_points.append(trend_point)

            # Cache result with 15-minute TTL
            cache_data = [asdict(point) for point in formatted_points]
            await self.cache_service.set(cache_key, cache_data, ttl=900)

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Feature trend generated for {feature_name} in {processing_time_ms:.1f}ms")

            return formatted_points

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Feature trend generation failed for {feature_name}: {e} (took {processing_time_ms:.1f}ms)")
            raise RuntimeError(f"Failed to generate feature trend: {str(e)}")

    async def _query_feature_trends(
        self, feature_name: str, time_range_days: int, granularity: str
    ) -> List[Dict[str, Any]]:
        """
        Query historical feature values from the database with appropriate aggregation.

        This method interfaces with the existing ML scoring history to extract
        feature values over time for trend analysis.
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)

        # Determine aggregation interval
        interval_map = {"hourly": "1 hour", "daily": "1 day", "weekly": "1 week"}
        interval = interval_map.get(granularity, "1 day")

        # Mock query structure - in production this would query the actual database
        # where ML scoring history is stored
        logger.debug(f"Querying feature trends: {feature_name} from {start_date} to {end_date}")

        # Simulate database query with realistic time-series data
        # In production, this would be a proper SQL query to ml_scoring_history table
        num_points = min(time_range_days, 30)  # Limit data points for performance
        trend_data = []

        for i in range(num_points):
            date = start_date + timedelta(days=i)

            # Generate realistic trend data (in production, this comes from database)
            base_value = 50.0 + (i * 2.0)  # Trending upward
            noise = np.random.normal(0, 5.0)  # Add some variance

            trend_data.append(
                {
                    "date": date,
                    "avg_value": base_value + noise,
                    "min_value": base_value + noise - 10.0,
                    "max_value": base_value + noise + 15.0,
                    "lead_count": np.random.randint(20, 100),
                    "p25": base_value + noise - 5.0,
                    "p75": base_value + noise + 8.0,
                }
            )

        return trend_data

    async def _get_feature_business_explanation(self, feature: str, shap_value: float) -> str:
        """Generate business-friendly explanation for a feature's SHAP contribution."""

        business_name = self._feature_business_map.get(feature, feature.replace("_", " ").title())

        direction = "increases" if shap_value > 0 else "decreases"
        magnitude = "significantly" if abs(shap_value) > 0.1 else "moderately"

        explanations = {
            "response_time_hours": f"Lead response time {direction} conversion probability {magnitude}",
            "message_length_avg": f"Message detail level {direction} engagement likelihood {magnitude}",
            "timeline_urgency": f"Timeline urgency indicators {direction} deal probability {magnitude}",
            "financial_readiness": f"Financial qualification {direction} conversion likelihood {magnitude}",
            "property_specificity": f"Property requirement clarity {direction} serious buyer probability {magnitude}",
            "engagement_score": f"Lead engagement level {direction} conversion potential {magnitude}",
            "follow_up_compliance": f"Follow-up consistency {direction} deal closure probability {magnitude}",
        }

        return explanations.get(feature, f"{business_name} {direction} the prediction {magnitude}")

    async def _publish_shap_update_event(self, lead_id: str, waterfall_data: SHAPWaterfallData):
        """Publish real-time SHAP update event via WebSocket."""

        try:
            # Create WebSocket event
            event_data = {
                "lead_id": lead_id,
                "prediction_value": waterfall_data.final_prediction,
                "base_value": waterfall_data.base_value,
                "top_features": waterfall_data.features[:5],  # Top 5 most important
                "top_shap_values": waterfall_data.shap_values[:5],
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Publish through existing event publisher
            await self.event_publisher.publish_dashboard_refresh(
                component="shap_waterfall",
                data=event_data,
                user_id=None,  # Global update for all users viewing this lead
            )

            logger.debug(f"Published SHAP update event for lead: {lead_id}")

        except Exception as e:
            logger.error(f"Failed to publish SHAP update event: {e}")
            # Don't raise - this is a non-critical feature

    def _update_performance_metrics(self, processing_time_ms: float):
        """Update internal performance metrics for monitoring."""

        total_requests = self._performance_metrics["total_requests"]
        current_avg = self._performance_metrics["avg_processing_time_ms"]

        # Running average calculation
        new_avg = ((current_avg * (total_requests - 1)) + processing_time_ms) / total_requests
        self._performance_metrics["avg_processing_time_ms"] = new_avg

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for monitoring and optimization."""

        cache_hit_rate = 0.0
        if self._performance_metrics["total_requests"] > 0:
            cache_hit_rate = self._performance_metrics["cache_hits"] / self._performance_metrics["total_requests"]

        return {
            "total_requests": self._performance_metrics["total_requests"],
            "cache_hit_rate": cache_hit_rate,
            "avg_processing_time_ms": self._performance_metrics["avg_processing_time_ms"],
            "target_processing_time_ms": 30.0,
            "performance_status": "good"
            if self._performance_metrics["avg_processing_time_ms"] < 30.0
            else "needs_optimization",
            "last_reset": self._performance_metrics["last_reset"].isoformat(),
        }

    async def clear_cache(self, pattern: Optional[str] = None):
        """Clear SHAP analytics cache, optionally by pattern."""

        if pattern:
            # Clear specific pattern
            await self.cache_service.delete_pattern(f"shap:*{pattern}*")
            logger.info(f"Cleared SHAP cache for pattern: {pattern}")
        else:
            # Clear all SHAP cache
            await self.cache_service.delete_pattern("shap:*")
            logger.info("Cleared all SHAP analytics cache")


# ============================================================================
# Service Factory Functions
# ============================================================================

_shap_analytics_enhanced_instance = None


def get_shap_analytics_enhanced() -> SHAPAnalyticsEnhanced:
    """
    Get singleton instance of SHAPAnalyticsEnhanced service.

    Returns:
        SHAPAnalyticsEnhanced: The singleton service instance
    """
    global _shap_analytics_enhanced_instance

    if _shap_analytics_enhanced_instance is None:
        _shap_analytics_enhanced_instance = SHAPAnalyticsEnhanced()

    return _shap_analytics_enhanced_instance


async def warm_shap_analytics_cache():
    """
    Warm the SHAP analytics cache with common feature trends.

    This function pre-loads cache for frequently accessed features
    to improve initial response times for dashboard users.
    """
    service = get_shap_analytics_enhanced()

    # Common features to pre-cache
    common_features = [
        "response_time_hours",
        "message_length_avg",
        "timeline_urgency",
        "financial_readiness",
        "engagement_score",
    ]

    logger.info("Starting SHAP analytics cache warming...")

    for feature in common_features:
        try:
            await service.generate_feature_trend_data(feature_name=feature, time_range_days=30)
            logger.debug(f"Pre-cached feature trend for: {feature}")
        except Exception as e:
            logger.warning(f"Failed to pre-cache feature {feature}: {e}")

    logger.info("SHAP analytics cache warming completed")


if __name__ == "__main__":
    # Development/testing entry point
    import asyncio

    async def test_enhanced_analytics():
        """Test the enhanced SHAP analytics functionality."""

        service = get_shap_analytics_enhanced()

        # Test waterfall generation
        try:
            waterfall = await service.generate_waterfall_data("test_lead_123")
            print(f"Waterfall generated with {len(waterfall.features)} features")
        except Exception as e:
            print(f"Waterfall test failed: {e}")

        # Test feature trends
        try:
            trends = await service.generate_feature_trend_data("response_time_hours")
            print(f"Feature trends generated with {len(trends)} data points")
        except Exception as e:
            print(f"Trends test failed: {e}")

        # Check performance
        metrics = await service.get_performance_metrics()
        print(f"Performance metrics: {metrics}")

    # Run test
    asyncio.run(test_enhanced_analytics())
