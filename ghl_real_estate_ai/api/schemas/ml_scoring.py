"""
ML Lead Scoring API Schemas
Production-ready Pydantic models for ML lead scoring API endpoints.

Integrates with:
- ML Analytics Engine for prediction requests/responses
- Feature Engineering pipeline for input validation
- Real-time API endpoints with <50ms target response times
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ConfidenceLevel(str, Enum):
    """ML prediction confidence levels"""

    HIGH = "high"  # >= 0.85, use ML prediction
    MEDIUM = "medium"  # 0.65-0.85, use with caution
    LOW = "low"  # < 0.65, escalate to Claude AI
    UNCERTAIN = "uncertain"  # Model unavailable/error


class LeadClassification(str, Enum):
    """Lead classification categories"""

    HOT = "hot"  # High conversion probability (80%+)
    WARM = "warm"  # Moderate conversion probability (50-80%)
    COLD = "cold"  # Low conversion probability (<50%)
    UNQUALIFIED = "unqualified"  # Not a viable lead


class ScoreSource(str, Enum):
    """Source of the lead score"""

    ML_ONLY = "ml_only"  # Pure ML prediction (high confidence)
    ML_CLAUDE_HYBRID = "ml_claude_hybrid"  # ML + Claude analysis
    CLAUDE_ONLY = "claude_only"  # Claude-only analysis (ML unavailable)
    CACHE = "cache"  # Cached previous result


class LeadScoringRequest(BaseModel):
    """Request schema for lead scoring API"""

    lead_id: str = Field(..., description="Unique identifier for the lead")
    lead_name: str = Field(..., description="Lead's name for personalization")

    # Lead context data
    email: Optional[str] = Field(None, description="Lead's email address")
    phone: Optional[str] = Field(None, description="Lead's phone number")
    message_content: Optional[str] = Field(None, description="Lead's message content")
    source: Optional[str] = Field("unknown", description="Lead source (GHL, website, etc.)")

    # Behavioral features
    response_time_hours: Optional[float] = Field(None, ge=0, description="Response time in hours")
    message_length: Optional[int] = Field(None, ge=0, description="Length of lead's message")
    questions_asked: Optional[int] = Field(None, ge=0, description="Number of questions asked")
    price_mentioned: Optional[bool] = Field(None, description="Whether price was mentioned")
    timeline_mentioned: Optional[bool] = Field(None, description="Whether timeline was mentioned")
    location_mentioned: Optional[bool] = Field(None, description="Whether location was mentioned")
    financing_mentioned: Optional[bool] = Field(None, description="Whether financing was mentioned")
    family_mentioned: Optional[bool] = Field(None, description="Whether family was mentioned")

    # Real estate specific features
    budget_range: Optional[str] = Field(None, description="Budget range if provided")
    property_type: Optional[str] = Field(None, description="Desired property type")
    bedrooms: Optional[int] = Field(None, ge=0, le=10, description="Number of bedrooms desired")
    location_preference: Optional[str] = Field(None, description="Preferred location/area")
    timeline_urgency: Optional[str] = Field(None, description="Buying timeline urgency")

    # Additional context
    previous_interactions: Optional[int] = Field(0, ge=0, description="Number of previous interactions")
    referral_source: Optional[str] = Field(None, description="Referral source if applicable")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Additional custom fields")

    # API options
    force_refresh: bool = Field(False, description="Force refresh, skip cache")
    include_explanations: bool = Field(True, description="Include ML feature explanations")
    timeout_ms: Optional[int] = Field(5000, ge=100, le=30000, description="Timeout in milliseconds")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace("+", "").replace("-", "").replace("(", "").replace(")", "").replace(" ", "")) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v


class BatchScoringRequest(BaseModel):
    """Request schema for batch lead scoring"""

    leads: List[LeadScoringRequest] = Field(..., max_length=100, description="List of leads to score")
    parallel_processing: bool = Field(True, description="Process leads in parallel")
    include_summary: bool = Field(True, description="Include batch processing summary")
    timeout_ms: Optional[int] = Field(15000, ge=1000, le=60000, description="Total batch timeout in ms")


class MLFeatureExplanation(BaseModel):
    """ML feature importance explanation"""

    feature_name: str = Field(..., description="Name of the ML feature")
    feature_value: Union[float, str, bool] = Field(..., description="Value of the feature")
    importance_score: float = Field(..., ge=0, le=1, description="SHAP importance score (0-1)")
    impact_direction: str = Field(..., description="positive, negative, or neutral")
    human_explanation: str = Field(..., description="Human-readable explanation")


class LeadScoringResponse(BaseModel):
    """Response schema for lead scoring API"""

    # Request identification
    lead_id: str = Field(..., description="Lead identifier from request")
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request identifier")

    # ML scoring results
    ml_score: float = Field(..., ge=0, le=100, description="ML lead score (0-100)")
    ml_confidence: float = Field(..., ge=0, le=1, description="ML confidence level (0-1)")
    confidence_level: ConfidenceLevel = Field(..., description="Categorical confidence level")
    classification: LeadClassification = Field(..., description="Lead classification category")

    # Conversion predictions
    conversion_probability: float = Field(..., ge=0, le=1, description="Probability of conversion (0-1)")
    estimated_commission: Optional[float] = Field(None, ge=0, description="Jorge's 6% commission estimate")
    expected_close_days: Optional[int] = Field(None, ge=1, description="Expected days to close")

    # Analysis details
    score_source: ScoreSource = Field(..., description="Source of the scoring")
    analysis_summary: str = Field(..., description="Human-readable analysis summary")
    key_insights: List[str] = Field(default_factory=list, description="Key insights about the lead")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")

    # ML explanations (optional based on request)
    feature_explanations: Optional[List[MLFeatureExplanation]] = Field(None, description="ML feature explanations")
    shap_values: Optional[Dict[str, float]] = Field(None, description="SHAP values for interpretability")

    # Performance metadata
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    ml_inference_time_ms: Optional[float] = Field(None, description="ML inference time in milliseconds")
    claude_analysis_time_ms: Optional[float] = Field(None, description="Claude analysis time if used")
    cache_hit: bool = Field(..., description="Whether result was from cache")

    # Timestamps
    scored_at: datetime = Field(default_factory=datetime.utcnow, description="When the scoring was performed")
    expires_at: Optional[datetime] = Field(None, description="When cached result expires")

    # Error handling
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings during processing")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information (dev mode only)")


class BatchScoringResponse(BaseModel):
    """Response schema for batch lead scoring"""

    batch_id: str = Field(default_factory=lambda: str(uuid4()), description="Batch processing identifier")
    total_leads: int = Field(..., description="Total number of leads processed")
    successful_scores: int = Field(..., description="Number of successful scores")
    failed_scores: int = Field(..., description="Number of failed scores")

    # Individual results
    results: List[LeadScoringResponse] = Field(..., description="Individual scoring results")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Error details for failed scores")

    # Batch summary
    average_score: float = Field(..., description="Average ML score across all leads")
    score_distribution: Dict[LeadClassification, int] = Field(..., description="Distribution by classification")
    total_processing_time_ms: float = Field(..., description="Total batch processing time")

    # Performance metrics
    throughput_scores_per_second: float = Field(..., description="Processing throughput")
    cache_hit_rate: float = Field(..., description="Percentage of cache hits")

    processed_at: datetime = Field(default_factory=datetime.utcnow, description="When batch was processed")


class LeadScoreHistoryResponse(BaseModel):
    """Response schema for lead scoring history"""

    lead_id: str = Field(..., description="Lead identifier")
    score_history: List[LeadScoringResponse] = Field(..., description="Historical scores")
    score_trend: str = Field(..., description="improving, declining, or stable")
    first_scored_at: datetime = Field(..., description="First scoring timestamp")
    last_scored_at: datetime = Field(..., description="Most recent scoring timestamp")
    total_scores: int = Field(..., description="Total number of scores recorded")


class MLModelStatus(BaseModel):
    """Response schema for ML model status"""

    model_name: str = Field(..., description="Name of the ML model")
    model_version: str = Field(..., description="Model version identifier")
    is_available: bool = Field(..., description="Whether model is available")
    last_trained: Optional[datetime] = Field(None, description="Last training timestamp")

    # Performance metrics
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="Model accuracy")
    precision: Optional[float] = Field(None, ge=0, le=1, description="Model precision")
    recall: Optional[float] = Field(None, ge=0, le=1, description="Model recall")
    f1_score: Optional[float] = Field(None, ge=0, le=1, description="Model F1 score")

    # Operational metrics
    average_inference_time_ms: float = Field(..., description="Average inference time")
    predictions_today: int = Field(..., description="Number of predictions today")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")

    status_checked_at: datetime = Field(default_factory=datetime.utcnow, description="Status check timestamp")


class ErrorResponse(BaseModel):
    """Standard error response schema"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response schema"""

    status: str = Field(..., description="overall, ml_model, cache, database")
    ml_model_status: str = Field(..., description="available, unavailable, degraded")
    cache_status: str = Field(..., description="available, unavailable, degraded")
    database_status: str = Field(..., description="available, unavailable, degraded")

    # Performance indicators
    average_response_time_ms: float = Field(..., description="Average API response time")
    requests_per_minute: int = Field(..., description="Current request rate")
    error_rate_percent: float = Field(..., description="Error rate percentage")

    checked_at: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")
    version: str = Field("1.0.0", description="API version")


# WebSocket message schemas for real-time updates
class WebSocketMessage(BaseModel):
    """Base WebSocket message schema"""

    type: str = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    message_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique message identifier")


class LeadScoredEvent(WebSocketMessage):
    """WebSocket event for when a lead is scored"""

    type: str = Field("lead_scored", description="Message type")
    lead_id: str = Field(..., description="Lead identifier")
    lead_name: str = Field(..., description="Lead name")
    ml_score: float = Field(..., description="ML score")
    classification: LeadClassification = Field(..., description="Lead classification")
    score_source: ScoreSource = Field(..., description="Source of scoring")
    processing_time_ms: float = Field(..., description="Processing time")


class BatchProcessingEvent(WebSocketMessage):
    """WebSocket event for batch processing updates"""

    type: str = Field("batch_processing", description="Message type")
    batch_id: str = Field(..., description="Batch identifier")
    total_leads: int = Field(..., description="Total leads in batch")
    processed_leads: int = Field(..., description="Number of leads processed")
    current_lead: Optional[str] = Field(None, description="Currently processing lead")
    estimated_completion_ms: Optional[int] = Field(None, description="Estimated completion time")


class ModelStatusEvent(WebSocketMessage):
    """WebSocket event for ML model status changes"""

    type: str = Field("model_status", description="Message type")
    model_name: str = Field(..., description="Model name")
    status: str = Field(..., description="available, unavailable, degraded")
    message: str = Field(..., description="Status change message")
