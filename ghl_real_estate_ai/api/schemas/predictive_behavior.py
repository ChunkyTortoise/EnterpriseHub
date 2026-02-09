"""
Pydantic Schemas for Predictive Behavior API - Phase 2.1
========================================================

Request and response models for the Predictive Lead Behavior Service API.
Follows established schema patterns with comprehensive validation and documentation.

Features:
- Strong typing with Pydantic v2 validation
- Comprehensive field documentation
- Default values and constraints
- Nested models for complex data structures
- JSON serialization compatibility
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Enums
# ============================================================================


class BehaviorCategoryEnum(str, Enum):
    """Valid behavior categories for leads."""

    HIGHLY_ENGAGED = "highly_engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    LOW_ENGAGEMENT = "low_engagement"
    DORMANT = "dormant"
    CHURNING = "churning"
    CONVERTING = "converting"


class TrendTypeEnum(str, Enum):
    """Valid trend analysis types."""

    ENGAGEMENT = "engagement"
    CHURN = "churn"
    CONVERSION = "conversion"
    RESPONSE_RATE = "response_rate"


class FeedbackTypeEnum(str, Enum):
    """Valid feedback types for learning loop."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"


# ============================================================================
# Nested Models
# ============================================================================


class NextActionPredictionModel(BaseModel):
    """Model for individual next action predictions."""

    model_config = ConfigDict(str_strip_whitespace=True)

    action: str = Field(..., description="Predicted action (respond, ghost, schedule, etc.)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Action probability (0-1)")
    expected_timing_hours: Optional[float] = Field(None, ge=0.0, description="Expected time to action in hours")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    triggers: List[str] = Field(default_factory=list, description="Factors that would trigger this action")
    prevention_strategy: Optional[str] = Field(None, description="Strategy to prevent negative actions")


class BehavioralTrendModel(BaseModel):
    """Model for behavioral trend data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trend_type: str = Field(..., description="Type of trend (engagement, response_rate, etc.)")
    direction: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    velocity: float = Field(..., description="Rate of change")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Trend confidence")
    data_points: int = Field(..., ge=1, description="Number of observations")
    time_window_hours: int = Field(..., ge=1, description="Analysis window in hours")
    detected_at: str = Field(..., description="When trend was detected (ISO format)")


class ContactWindowModel(BaseModel):
    """Model for optimal contact time windows."""

    model_config = ConfigDict(str_strip_whitespace=True)

    start: str = Field(..., description="Window start time (HH:MM format)")
    end: str = Field(..., description="Window end time (HH:MM format)")
    timezone: str = Field(default="America/Chicago", description="Timezone for contact window")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this window")
    day_type: str = Field(default="weekday", description="Day type (weekday, weekend)")


class BehavioralPredictionModel(BaseModel):
    """Complete behavioral prediction model."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: str = Field(..., description="Lead identifier")
    location_id: str = Field(..., description="Location/tenant identifier")

    # Primary predictions
    behavior_category: BehaviorCategoryEnum = Field(..., description="Predicted behavior category")
    category_confidence: float = Field(..., ge=0.0, le=1.0, description="Category confidence")
    next_actions: List[NextActionPredictionModel] = Field(..., description="Top predicted actions")

    # Engagement metrics
    engagement_score_7d: float = Field(..., ge=0.0, le=100.0, description="7-day engagement score")
    engagement_trend: BehavioralTrendModel = Field(..., description="Engagement trend analysis")
    response_probability_24h: float = Field(..., ge=0.0, le=1.0, description="24h response probability")
    expected_response_time_hours: Optional[float] = Field(None, description="Expected response time")

    # Risk assessment
    churn_risk_score: float = Field(..., ge=0.0, le=100.0, description="Churn risk score")
    churn_risk_factors: List[str] = Field(..., description="Identified risk factors")
    conversion_readiness_score: float = Field(..., ge=0.0, le=100.0, description="Conversion readiness")
    estimated_conversion_days: Optional[int] = Field(None, description="Estimated conversion timeline")

    # Behavioral patterns
    communication_preferences: Dict[str, float] = Field(..., description="Channel preferences")
    optimal_contact_windows: List[ContactWindowModel] = Field(..., description="Best contact times")
    objection_patterns: List[str] = Field(..., description="Common objection patterns")
    decision_velocity: str = Field(..., description="Decision-making speed (fast/moderate/slow)")

    # Metadata
    predicted_at: str = Field(..., description="Prediction timestamp (ISO format)")
    prediction_latency_ms: float = Field(..., ge=0.0, description="Prediction computation time")
    model_version: str = Field(default="v1.0", description="Model version used")
    feature_count: int = Field(..., ge=0, description="Number of features used")


# ============================================================================
# Request Models
# ============================================================================


class BehavioralPredictionRequest(BaseModel):
    """Request for single lead behavioral prediction."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: str = Field(..., min_length=1, description="Lead identifier")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None, description="Recent conversation data for analysis"
    )
    force_refresh: bool = Field(default=False, description="Skip cache and force fresh prediction")


class BatchPredictionRequest(BaseModel):
    """Request for batch behavioral predictions."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lead_ids: List[str] = Field(..., min_length=1, max_length=100, description="List of lead identifiers (max 100)")
    batch_size: int = Field(default=10, ge=1, le=20, description="Processing batch size")
    force_refresh: bool = Field(default=False, description="Skip cache for all predictions")


class BehavioralTrendRequest(BaseModel):
    """Request for behavioral trend analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    trend_type: TrendTypeEnum = Field(..., description="Type of trend to analyze")
    time_window_hours: int = Field(
        default=168,  # 7 days
        ge=1,
        le=720,  # 30 days
        description="Analysis time window in hours",
    )
    cohort_segment: Optional[str] = Field(None, description="Optional cohort segment filter")


class FeedbackRequest(BaseModel):
    """Request for submitting prediction feedback."""

    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: str = Field(..., min_length=1, description="Lead identifier")
    prediction_id: str = Field(..., min_length=1, description="Prediction identifier")
    predicted_action: str = Field(..., description="What was predicted")
    actual_action: str = Field(..., description="What actually happened")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the feedback")


# ============================================================================
# Response Models
# ============================================================================


class BehavioralPredictionResponse(BaseModel):
    """Response for behavioral prediction requests."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Request success status")
    prediction: Optional[BehavioralPredictionModel] = Field(None, description="Prediction result")
    latency_ms: float = Field(..., description="Processing time in milliseconds")
    cached: bool = Field(..., description="Whether result was cached")
    location_id: str = Field(..., description="Location identifier")
    timestamp: str = Field(..., description="Response timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchPredictionResponse(BaseModel):
    """Response for batch prediction requests."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Request success status")
    job_id: str = Field(..., description="Background job identifier")
    lead_count: int = Field(..., description="Number of leads to process")
    batch_size: int = Field(..., description="Processing batch size")
    status: str = Field(..., description="Job status (processing, completed, failed)")
    estimated_completion_seconds: float = Field(..., description="Estimated completion time")
    location_id: str = Field(..., description="Location identifier")
    created_at: str = Field(..., description="Job creation timestamp")


class BehavioralTrendResponse(BaseModel):
    """Response for trend analysis requests."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Request success status")
    trend_type: str = Field(..., description="Analyzed trend type")
    time_window_hours: int = Field(..., description="Analysis window")
    trends: List[BehavioralTrendModel] = Field(..., description="Trend analysis results")
    location_id: str = Field(..., description="Location identifier")
    analyzed_at: str = Field(..., description="Analysis timestamp")


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Submission success status")
    message: str = Field(..., description="Response message")
    feedback_id: Optional[str] = Field(None, description="Generated feedback identifier")
    prediction_accuracy: Optional[float] = Field(None, description="Calculated prediction accuracy")
    location_id: str = Field(..., description="Location identifier")
    recorded_at: str = Field(..., description="Recording timestamp")


class AnalyticsSummaryResponse(BaseModel):
    """Response for analytics summary requests."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Request success status")
    analytics_type: str = Field(..., description="Type of analytics")
    time_window_hours: int = Field(..., description="Analysis window")
    location_id: str = Field(..., description="Location identifier")
    data: Dict[str, Any] = Field(..., description="Analytics data")
    generated_at: str = Field(..., description="Generation timestamp")


class HealthCheckResponse(BaseModel):
    """Response for health check requests."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Health check success")
    status: str = Field(..., description="Service status (healthy, unhealthy, degraded)")
    data: Dict[str, Any] = Field(..., description="Health metrics and status data")
    timestamp: str = Field(..., description="Check timestamp")


# ============================================================================
# Validation Models
# ============================================================================


class PredictionValidationRequest(BaseModel):
    """Request for prediction validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    prediction_id: str = Field(..., description="Prediction to validate")
    validation_criteria: Dict[str, Any] = Field(..., description="Validation criteria")


class ModelPerformanceRequest(BaseModel):
    """Request for model performance metrics."""

    model_config = ConfigDict(str_strip_whitespace=True)

    metric_type: str = Field(..., description="Performance metric type")
    time_window_hours: int = Field(default=168, description="Analysis window")
    include_breakdown: bool = Field(default=False, description="Include detailed breakdown")


# ============================================================================
# Error Models
# ============================================================================


class PredictionError(BaseModel):
    """Model for prediction error details."""

    model_config = ConfigDict(str_strip_whitespace=True)

    error_code: str = Field(..., description="Error classification code")
    error_message: str = Field(..., description="Human-readable error message")
    lead_id: Optional[str] = Field(None, description="Lead that caused error")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    timestamp: str = Field(..., description="Error timestamp")


class ValidationError(BaseModel):
    """Model for validation error details."""

    model_config = ConfigDict(str_strip_whitespace=True)

    field_name: str = Field(..., description="Field that failed validation")
    error_message: str = Field(..., description="Validation error message")
    provided_value: Optional[Any] = Field(None, description="Value that failed validation")
    expected_format: Optional[str] = Field(None, description="Expected value format")


# ============================================================================
# Utility Models
# ============================================================================


class PaginationRequest(BaseModel):
    """Request model for paginated endpoints."""

    model_config = ConfigDict(str_strip_whitespace=True)

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=50, ge=1, le=200, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class PaginatedResponse(BaseModel):
    """Response model for paginated data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    items: List[Any] = Field(..., description="Page items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total items available")
    total_pages: int = Field(..., description="Total pages available")
    has_next: bool = Field(..., description="Whether next page exists")
    has_previous: bool = Field(..., description="Whether previous page exists")


class FilterRequest(BaseModel):
    """Request model for filtering data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter criteria")
    date_from: Optional[str] = Field(None, description="Start date filter (ISO format)")
    date_to: Optional[str] = Field(None, description="End date filter (ISO format)")
    search_query: Optional[str] = Field(None, description="Text search query")


# ============================================================================
# Configuration Models
# ============================================================================


class PredictionConfigRequest(BaseModel):
    """Request for updating prediction configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cache_ttl_seconds: Optional[int] = Field(None, ge=60, le=3600, description="Cache TTL")
    batch_size: Optional[int] = Field(None, ge=1, le=50, description="Default batch size")
    accuracy_threshold: Optional[float] = Field(None, ge=0.5, le=1.0, description="Accuracy threshold")
    enable_real_time_events: Optional[bool] = Field(None, description="Enable WebSocket events")


class ModelConfigResponse(BaseModel):
    """Response for model configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    model_version: str = Field(..., description="Current model version")
    feature_count: int = Field(..., description="Number of features used")
    accuracy_target: float = Field(..., description="Target accuracy percentage")
    latency_target_ms: float = Field(..., description="Target latency in milliseconds")
    cache_configuration: Dict[str, Any] = Field(..., description="Cache settings")
    performance_thresholds: Dict[str, float] = Field(..., description="Performance thresholds")


# ============================================================================
# Example Usage Documentation
# ============================================================================


class ExamplePredictionRequest(BehavioralPredictionRequest):
    """Example prediction request with sample data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lead_id": "lead_12345",
                "conversation_history": [
                    {
                        "id": "msg_1",
                        "content": "I'm interested in properties in Austin",
                        "direction": "inbound",
                        "timestamp": "2026-01-25T10:00:00Z",
                    },
                    {
                        "id": "msg_2",
                        "content": "Great! I can help you find the perfect property...",
                        "direction": "outbound",
                        "timestamp": "2026-01-25T10:02:00Z",
                    },
                ],
                "force_refresh": False,
            }
        }
    )
