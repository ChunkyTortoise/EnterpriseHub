"""
Analytics API Schemas for Jorge's Real Estate AI Platform

Comprehensive Pydantic models for advanced analytics requests/responses.
Supports SHAP explainability, market intelligence, and real-time WebSocket events.

Performance: <5ms validation time
Cache TTL: 5-15 minutes depending on data volatility
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class AnalyticsMetric(str, Enum):
    """Market intelligence metric types for heatmap visualization."""

    LEAD_DENSITY = "lead_density"
    CONVERSION_RATE = "conversion_rate"
    AVG_DEAL_VALUE = "avg_deal_value"
    HOT_ZONE_SCORE = "hot_zone_score"


class Granularity(str, Enum):
    """Geographic granularity levels for market analysis."""

    NEIGHBORHOOD = "neighborhood"
    ZIPCODE = "zipcode"
    CITY = "city"
    CUSTOM_RADIUS = "custom_radius"


class EventPriority(str, Enum):
    """Priority levels for real-time analytics events."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventType(str, Enum):
    """Analytics WebSocket event types."""

    SHAP_UPDATE = "shap_update"
    MARKET_CHANGE = "market_change"
    LEAD_DENSITY_ALERT = "lead_density_alert"
    HOT_ZONE_DETECTION = "hot_zone_detection"
    FEATURE_TREND_UPDATE = "feature_trend_update"


# ============================================================================
# SHAP Analytics Request/Response Models
# ============================================================================


class SHAPAnalyticsRequest(BaseModel):
    """Request for interactive SHAP analysis with optional comparison leads."""

    lead_id: str = Field(..., description="Primary lead ID for SHAP analysis")
    include_waterfall: bool = Field(default=True, description="Generate waterfall chart data")
    include_feature_trends: bool = Field(default=True, description="Generate feature trend analysis")
    comparison_lead_ids: Optional[List[str]] = Field(
        default=None, description="Optional lead IDs for comparative SHAP analysis", max_length=5
    )
    time_range_days: int = Field(default=30, ge=1, le=365, description="Time range for feature trends (days)")

    @field_validator("lead_id")
    @classmethod
    def validate_lead_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("lead_id cannot be empty")
        return v.strip()


class SHAPWaterfallData(BaseModel):
    """Recharts-compatible waterfall chart data for SHAP visualization."""

    base_value: float = Field(..., description="SHAP base/expected value")
    final_prediction: float = Field(..., description="Final prediction value")
    features: List[str] = Field(..., description="Feature names in importance order")
    shap_values: List[float] = Field(..., description="SHAP values for each feature")
    cumulative_values: List[float] = Field(..., description="Cumulative prediction values")
    feature_labels: List[str] = Field(..., description="Human-readable feature descriptions")
    colors: List[str] = Field(..., description="Hex color codes for each feature bar")
    feature_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for each feature")

    @field_validator("shap_values", "cumulative_values", "feature_labels", "colors")
    @classmethod
    def validate_equal_lengths(cls, v, info: ValidationInfo):
        features = info.data.get("features", [])
        if len(v) != len(features):
            raise ValueError("All feature arrays must have equal length")
        return v


class FeatureTrendPoint(BaseModel):
    """Single data point for feature trend time-series visualization."""

    date: datetime = Field(..., description="Date of the data point")
    avg_value: float = Field(..., description="Average feature value")
    min_value: float = Field(..., description="Minimum feature value")
    max_value: float = Field(..., description="Maximum feature value")
    lead_count: int = Field(..., ge=0, description="Number of leads in this time period")
    percentile_25: Optional[float] = Field(None, description="25th percentile value")
    percentile_75: Optional[float] = Field(None, description="75th percentile value")


class SHAPWaterfallResponse(BaseModel):
    """Response model for SHAP waterfall chart data."""

    lead_id: str = Field(..., description="Lead ID that was analyzed")
    waterfall_data: SHAPWaterfallData = Field(..., description="Waterfall chart data")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class FeatureTrendResponse(BaseModel):
    """Response model for feature trend analysis."""

    feature_name: str = Field(..., description="Feature that was analyzed")
    time_range_days: int = Field(..., ge=1, description="Time range analyzed")
    trend_data: List[FeatureTrendPoint] = Field(..., description="Time-series trend data")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    summary_stats: Dict[str, float] = Field(
        default_factory=dict, description="Summary statistics (mean, std, trend_direction)"
    )


# ============================================================================
# Market Intelligence Request/Response Models
# ============================================================================


class MarketHeatmapRequest(BaseModel):
    """Request for geospatial market intelligence heatmap data."""

    region: str = Field(default="austin_tx", description="Geographic region identifier")
    metric_type: AnalyticsMetric = Field(default=AnalyticsMetric.LEAD_DENSITY, description="Market metric to visualize")
    time_range_days: int = Field(default=30, ge=1, le=365, description="Time range for data aggregation")
    granularity: Granularity = Field(default=Granularity.NEIGHBORHOOD, description="Geographic granularity level")
    custom_bounds: Optional[Dict[str, float]] = Field(
        None, description="Custom geographic bounds (north, south, east, west)"
    )
    min_threshold: Optional[float] = Field(None, description="Minimum threshold for metric filtering")

    @field_validator("custom_bounds")
    @classmethod
    def validate_bounds(cls, v):
        if v is not None:
            required_keys = {"north", "south", "east", "west"}
            if not required_keys.issubset(v.keys()):
                raise ValueError(f"custom_bounds must contain: {required_keys}")

            if v["north"] <= v["south"]:
                raise ValueError("north must be greater than south")
            if v["east"] <= v["west"]:
                raise ValueError("east must be greater than west")

        return v


class MarketHeatmapDataPoint(BaseModel):
    """Single heatmap data point for Deck.gl HexagonLayer visualization."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lng: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    value: float = Field(..., ge=0, description="Metric value for visualization")
    label: str = Field(..., description="Human-readable location label")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data for the location")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lat": 30.2672,
                "lng": -97.7431,
                "value": 85.5,
                "label": "Downtown Austin",
                "metadata": {"avg_score": 78.5, "hot_leads": 12, "conversion_rate": 0.15, "total_leads": 80},
            }
        }
    )


class MarketHeatmapResponse(BaseModel):
    """Response model for market intelligence heatmap data."""

    region: str = Field(..., description="Geographic region analyzed")
    metric_type: AnalyticsMetric = Field(..., description="Market metric visualized")
    heatmap_data: List[MarketHeatmapDataPoint] = Field(..., description="Heatmap visualization data")
    bounds: Dict[str, float] = Field(..., description="Geographic bounds of the data")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    data_points_count: int = Field(..., ge=0, description="Number of data points returned")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class MarketMetricsResponse(BaseModel):
    """Response model for comprehensive market intelligence metrics."""

    region: str = Field(..., description="Geographic region analyzed")
    metrics: Dict[str, Any] = Field(..., description="Comprehensive market metrics")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "region": "austin_tx",
                "metrics": {
                    "lead_density": {"avg": 45.2, "max": 120.5, "hot_zones": 8},
                    "conversion_rates": {"avg": 0.12, "best_zone": 0.28},
                    "avg_deal_values": {"median": 485000, "top_zone": 750000},
                    "hot_zones": [{"name": "Downtown", "score": 95.2, "reason": "high_density_high_conversion"}],
                },
                "processing_time_ms": 45.2,
                "cached": False,
                "generated_at": "2024-01-01T12:00:00Z",
            }
        }
    )


# ============================================================================
# WebSocket Event Models
# ============================================================================


class AnalyticsWebSocketEvent(BaseModel):
    """Base model for real-time analytics WebSocket events."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of analytics event")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    priority: EventPriority = Field(default=EventPriority.MEDIUM, description="Event priority level")
    session_id: Optional[str] = Field(None, description="User session identifier")
    user_id: Optional[int] = Field(None, description="User identifier")

    model_config = ConfigDict(use_enum_values=True)


class SHAPUpdateEvent(AnalyticsWebSocketEvent):
    """WebSocket event for SHAP analysis updates."""

    event_type: Literal[EventType.SHAP_UPDATE] = EventType.SHAP_UPDATE

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "shap_update_123456",
                "event_type": "shap_update",
                "data": {
                    "lead_id": "lead_789",
                    "updated_features": ["response_time_hours", "message_sentiment"],
                    "new_prediction": 0.78,
                    "previous_prediction": 0.65,
                    "change_reason": "faster_response_improved_score",
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "priority": "high",
            }
        }
    )


class MarketChangeEvent(AnalyticsWebSocketEvent):
    """WebSocket event for market condition changes."""

    event_type: Literal[EventType.MARKET_CHANGE] = EventType.MARKET_CHANGE

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "market_change_123456",
                "event_type": "market_change",
                "data": {
                    "region": "austin_tx",
                    "metric": "lead_density",
                    "zone": "Downtown",
                    "old_value": 45.2,
                    "new_value": 62.8,
                    "change_percent": 38.9,
                    "trend": "increasing",
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "priority": "medium",
            }
        }
    )


class HotZoneDetectionEvent(AnalyticsWebSocketEvent):
    """WebSocket event for hot zone detection alerts."""

    event_type: Literal[EventType.HOT_ZONE_DETECTION] = EventType.HOT_ZONE_DETECTION

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "hot_zone_123456",
                "event_type": "hot_zone_detection",
                "data": {
                    "zone_name": "South Congress",
                    "zone_lat": 30.2515,
                    "zone_lng": -97.7481,
                    "hot_zone_score": 88.5,
                    "contributing_factors": ["high_lead_density", "above_avg_conversion", "premium_property_values"],
                    "recommended_actions": ["increase_ad_spend", "deploy_premium_agent", "schedule_market_visit"],
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "priority": "critical",
            }
        }
    )


# ============================================================================
# Error Response Models
# ============================================================================


class AnalyticsError(BaseModel):
    """Standardized error response for analytics API endpoints."""

    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error context and debugging information"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "SHAP_ANALYSIS_FAILED",
                "error_message": "Failed to generate SHAP analysis for lead",
                "error_details": {
                    "lead_id": "lead_789",
                    "reason": "insufficient_historical_data",
                    "minimum_required": 10,
                    "actual_data_points": 3,
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "req_123456",
            }
        }
    )


# ============================================================================
# Performance Metrics Models
# ============================================================================


class PerformanceMetrics(BaseModel):
    """Performance metrics for analytics API monitoring."""

    endpoint: str = Field(..., description="API endpoint path")
    avg_response_time_ms: float = Field(..., ge=0, description="Average response time")
    p95_response_time_ms: float = Field(..., ge=0, description="95th percentile response time")
    cache_hit_rate: float = Field(..., ge=0, le=1, description="Cache hit rate (0-1)")
    total_requests: int = Field(..., ge=0, description="Total requests in time period")
    error_rate: float = Field(..., ge=0, le=1, description="Error rate (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/analytics/shap/waterfall",
                "avg_response_time_ms": 28.5,
                "p95_response_time_ms": 45.2,
                "cache_hit_rate": 0.72,
                "total_requests": 1247,
                "error_rate": 0.003,
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
    )
