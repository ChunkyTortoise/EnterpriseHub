"""
Pydantic schemas for Jorge's Advanced Features API.

Defines request/response models for:
- Voice AI Phone Integration
- Automated Marketing Campaign Generator
- Client Retention & Referral Automation
- Advanced Market Prediction Analytics
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


# ================== ENUMS ==================

class CallTypeAPI(str, Enum):
    """API version of CallType enum."""
    NEW_LEAD = "new_lead"
    EXISTING_CLIENT = "existing_client"
    CALLBACK = "callback"
    EMERGENCY = "emergency"


class CallPriorityAPI(str, Enum):
    """API version of CallPriority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ConversationStageAPI(str, Enum):
    """API version of ConversationStage enum."""
    GREETING = "greeting"
    QUALIFICATION = "qualification"
    DISCOVERY = "discovery"
    SCHEDULING = "scheduling"
    CLOSING = "closing"
    TRANSFER = "transfer"


class CampaignTriggerAPI(str, Enum):
    """API version of CampaignTrigger enum."""
    NEW_LISTING = "new_listing"
    PRICE_CHANGE = "price_change"
    MARKET_UPDATE = "market_update"
    SEASONAL_CAMPAIGN = "seasonal_campaign"
    HIGH_QUALIFIED_CALL = "high_qualified_call"
    CLIENT_MILESTONE = "client_milestone"
    COMPETITOR_ACTIVITY = "competitor_activity"


class ContentFormatAPI(str, Enum):
    """API version of ContentFormat enum."""
    EMAIL = "email"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    DIRECT_MAIL = "direct_mail"
    VIDEO = "video"
    BLOG_POST = "blog_post"
    FLYER = "flyer"


class LifeEventTypeAPI(str, Enum):
    """API version of LifeEventType enum."""
    JOB_CHANGE = "job_change"
    FAMILY_EXPANSION = "family_expansion"
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    RETIREMENT = "retirement"
    PROMOTION = "promotion"
    RELOCATION = "relocation"
    INVESTMENT_INTEREST = "investment_interest"


class TimeHorizonAPI(str, Enum):
    """API version of TimeHorizon enum."""
    THREE_MONTHS = "3_months"
    SIX_MONTHS = "6_months"
    ONE_YEAR = "1_year"
    TWO_YEARS = "2_years"


class EventTypeAPI(str, Enum):
    """API version of EventType enum."""
    HIGH_QUALIFIED_CALL = "high_qualified_call"
    CAMPAIGN_LAUNCHED = "campaign_launched"
    CLIENT_MILESTONE = "client_milestone"
    MARKET_OPPORTUNITY = "market_opportunity"
    REFERRAL_RECEIVED = "referral_received"
    FOLLOW_UP_NEEDED = "follow_up_needed"


# ================== VOICE AI SCHEMAS ==================

class VoiceCallStartRequest(BaseModel):
    """Request to start a voice AI call."""
    phone_number: str = Field(..., description="Caller's phone number", min_length=10, max_length=15)
    caller_name: Optional[str] = Field(None, description="Caller's name if known", max_length=100)
    call_type: Optional[CallTypeAPI] = Field(CallTypeAPI.NEW_LEAD, description="Type of call")
    priority: Optional[CallPriorityAPI] = Field(CallPriorityAPI.NORMAL, description="Call priority")


class VoiceCallStartResponse(BaseModel):
    """Response for starting a voice call."""
    call_id: str = Field(..., description="Unique call identifier")
    status: str = Field(..., description="Call status")
    message: str = Field(..., description="Success message")
    jorge_greeting: Optional[str] = Field(None, description="Jorge's initial greeting")


class VoiceInputRequest(BaseModel):
    """Request to process voice input."""
    call_id: str = Field(..., description="Active call ID", min_length=1)
    speech_text: str = Field(..., description="Transcribed speech text", min_length=1, max_length=5000)
    audio_confidence: float = Field(..., ge=0.0, le=1.0, description="Speech recognition confidence")
    speaker: Optional[str] = Field("caller", description="Speaker identification: caller or agent")


class VoiceResponseData(BaseModel):
    """Voice AI response data."""
    text: str = Field(..., description="Generated response text")
    emotion: str = Field(..., description="Response emotion/tone")
    pace: str = Field(default="normal", description="Speaking pace recommendation")
    confidence: float = Field(default=1.0, description="Response confidence level")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")
    conversation_stage: ConversationStageAPI = Field(..., description="Updated conversation stage")
    qualification_score: Optional[int] = Field(None, description="Current lead qualification score")
    transfer_recommended: bool = Field(False, description="Whether to transfer to Jorge")


class VoiceCallAnalytics(BaseModel):
    """Voice call analytics response."""
    call_id: str
    phone_number: str
    caller_name: Optional[str]
    duration_seconds: int
    conversation_stage_final: ConversationStageAPI
    qualification_score: int = Field(..., ge=0, le=100)
    transfer_to_jorge: bool
    lead_quality: str = Field(..., description="Overall lead quality assessment")
    key_information: Dict[str, Any] = Field(default_factory=dict)
    conversation_summary: str
    qualification_responses: Dict[str, str] = Field(default_factory=dict)
    next_steps: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class VoiceAnalyticsResponse(BaseModel):
    """Voice AI system analytics."""
    period_days: int
    total_calls: int
    total_duration_minutes: int
    avg_call_duration: float
    avg_qualification_score: float
    qualification_distribution: Dict[str, int]  # high/medium/low counts
    transfer_rate: float
    top_industries: List[str]
    top_call_sources: List[str]
    conversion_funnel: Dict[str, int]
    performance_trends: Dict[str, List[float]]
    generated_at: datetime = Field(default_factory=datetime.now)


# ================== MARKETING AUTOMATION SCHEMAS ==================

class CampaignCreationRequest(BaseModel):
    """Request to create automated marketing campaign."""
    trigger_type: CampaignTriggerAPI = Field(..., description="Campaign trigger type")
    target_audience: Dict[str, Any] = Field(..., description="Target audience criteria")
    campaign_objectives: List[str] = Field(..., min_length=1, description="Campaign objectives")
    content_formats: List[ContentFormatAPI] = Field(..., min_length=1, description="Desired content formats")
    budget_range: Optional[tuple[float, float]] = Field(None, description="Budget range (min, max)")
    timeline: Optional[str] = Field(None, description="Campaign timeline", max_length=500)
    brand_voice: Optional[str] = Field("jorge_professional", description="Brand voice to use")
    geographic_focus: Optional[List[str]] = Field(None, description="Geographic targeting areas")


class CampaignBriefResponse(BaseModel):
    """Campaign creation response."""
    campaign_id: str
    name: str
    trigger: CampaignTriggerAPI
    status: str
    target_audience: Dict[str, Any]
    objectives: List[str]
    content_formats: List[ContentFormatAPI]
    estimated_reach: Optional[int] = None
    estimated_budget: Optional[float] = None
    launch_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="jorge_ai")


class CampaignContentResponse(BaseModel):
    """Campaign content response."""
    campaign_id: str
    content: Dict[str, Any]  # Format -> content mapping
    content_variations: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ab_test_configs: Optional[List[Dict[str, Any]]] = None
    personalization_tokens: List[str] = Field(default_factory=list)
    compliance_notes: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


class CampaignPerformanceMetrics(BaseModel):
    """Campaign performance metrics."""
    campaign_id: str
    campaign_name: str
    status: str
    launch_date: datetime
    end_date: Optional[datetime] = None
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    ctr: float = Field(ge=0.0, description="Click-through rate")
    conversion_rate: float = Field(ge=0.0, description="Conversion rate")
    roi: float = Field(description="Return on investment")
    cost_per_lead: float = Field(ge=0.0)
    cost_per_conversion: float = Field(ge=0.0)
    lead_quality_score: float = Field(ge=0.0, le=1.0)
    engagement_metrics: Dict[str, float] = Field(default_factory=dict)
    geographic_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class ABTestRequest(BaseModel):
    """A/B test configuration request."""
    test_name: str = Field(..., description="Test name", min_length=1, max_length=200)
    test_description: Optional[str] = Field(None, description="Test description", max_length=1000)
    variants: Dict[str, Dict[str, Any]] = Field(..., description="Test variants (A, B, etc.)")
    metric: str = Field(..., description="Primary metric to optimize")
    duration_days: int = Field(default=14, ge=1, le=90, description="Test duration in days")
    traffic_split: Dict[str, float] = Field(default={"A": 0.5, "B": 0.5}, description="Traffic allocation")
    significance_threshold: float = Field(default=0.95, ge=0.8, le=0.99, description="Statistical significance threshold")


class ABTestResponse(BaseModel):
    """A/B test creation response."""
    test_id: str
    campaign_id: str
    test_name: str
    status: str
    variants: Dict[str, Dict[str, Any]]
    start_date: datetime
    end_date: datetime
    traffic_split: Dict[str, float]
    created_at: datetime = Field(default_factory=datetime.now)


# ================== CLIENT RETENTION SCHEMAS ==================

class ClientLifecycleUpdate(BaseModel):
    """Update client lifecycle information."""
    client_id: str = Field(..., description="Client identifier", min_length=1)
    life_event: LifeEventTypeAPI = Field(..., description="Type of life event")
    event_context: Dict[str, Any] = Field(..., description="Event context and details")
    detected_date: Optional[datetime] = Field(None, description="When event was detected")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence")
    source: str = Field(default="manual", description="How event was detected")


class ClientLifecycleResponse(BaseModel):
    """Client lifecycle update response."""
    client_id: str
    life_event: LifeEventTypeAPI
    status: str
    triggered_actions: List[str] = Field(default_factory=list)
    engagement_plan_updated: bool
    next_touchpoints: List[Dict[str, Any]] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=datetime.now)


class ReferralTrackingRequest(BaseModel):
    """Track new referral opportunity."""
    referrer_client_id: str = Field(..., description="Referring client ID", min_length=1)
    referred_contact_info: Dict[str, str] = Field(..., description="Referred contact information")
    referral_source: str = Field(..., description="How referral came about", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    referral_type: str = Field(default="buyer", description="Type of referral")
    urgency_level: str = Field(default="normal", description="Urgency level")


class ReferralTrackingResponse(BaseModel):
    """Referral tracking response."""
    referral_id: str
    referrer_id: str
    referred_contact: Dict[str, str]
    status: str
    tracking_number: str
    initial_outreach_scheduled: bool
    referrer_acknowledgment_sent: bool
    estimated_value: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ClientEngagementSummary(BaseModel):
    """Client engagement summary."""
    client_id: str
    client_name: str
    client_type: str = Field(description="past_client, current_client, prospect")
    total_interactions: int = Field(ge=0)
    interactions_this_period: int = Field(ge=0)
    last_interaction_date: datetime
    engagement_score: float = Field(ge=0.0, le=1.0)
    engagement_trend: str = Field(description="increasing, stable, decreasing")
    referrals_made: int = Field(ge=0)
    referrals_successful: int = Field(ge=0)
    lifetime_value: float = Field(ge=0.0)
    predicted_lifetime_value: float = Field(ge=0.0)
    retention_probability: float = Field(ge=0.0, le=1.0)
    next_milestone_date: Optional[datetime] = None
    recommended_actions: List[str] = Field(default_factory=list)


class RetentionAnalyticsResponse(BaseModel):
    """Retention system analytics."""
    period_days: int
    total_clients: int
    active_clients: int
    retention_rate: float = Field(ge=0.0, le=1.0)
    churn_rate: float = Field(ge=0.0, le=1.0)
    avg_engagement_score: float = Field(ge=0.0, le=1.0)
    total_referrals: int = Field(ge=0)
    referral_conversion_rate: float = Field(ge=0.0, le=1.0)
    avg_referrals_per_client: float = Field(ge=0.0)
    lifetime_value_avg: float = Field(ge=0.0)
    client_segmentation: Dict[str, int] = Field(default_factory=dict)
    engagement_distribution: Dict[str, int] = Field(default_factory=dict)
    milestone_tracking: Dict[str, int] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)


# ================== MARKET PREDICTION SCHEMAS ==================

class MarketAnalysisRequest(BaseModel):
    """Request for market prediction analysis."""
    neighborhood: str = Field(..., description="Neighborhood to analyze", min_length=1, max_length=100)
    time_horizon: TimeHorizonAPI = Field(..., description="Prediction time horizon")
    property_type: Optional[str] = Field(None, description="Property type filter", max_length=50)
    price_range: Optional[tuple[float, float]] = Field(None, description="Price range filter")
    analysis_focus: List[str] = Field(default=["appreciation", "market_trends"], description="Analysis focus areas")
    include_comparables: bool = Field(default=True, description="Include comparable properties analysis")


class MarketPredictionResult(BaseModel):
    """Market prediction analysis result."""
    neighborhood: str
    time_horizon: TimeHorizonAPI
    predicted_appreciation: float = Field(description="Predicted price appreciation percentage")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Prediction confidence")
    current_median_price: float = Field(ge=0.0)
    predicted_median_price: float = Field(ge=0.0)
    supporting_factors: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    market_indicators: Dict[str, float] = Field(default_factory=dict)
    comparable_neighborhoods: List[Dict[str, Any]] = Field(default_factory=list)
    investment_rating: str = Field(description="Investment attractiveness rating")
    generated_at: datetime = Field(default_factory=datetime.now)


class InvestmentOpportunityRequest(BaseModel):
    """Request for investment opportunity analysis."""
    client_budget: float = Field(..., gt=0, description="Client's investment budget")
    risk_tolerance: str = Field(..., description="Risk tolerance: low, medium, high")
    investment_goals: List[str] = Field(..., min_length=1, description="Investment objectives")
    time_horizon: TimeHorizonAPI = Field(..., description="Investment time horizon")
    preferred_property_types: Optional[List[str]] = Field(None, description="Preferred property types")
    geographic_preferences: Optional[List[str]] = Field(None, description="Preferred areas")
    minimum_cash_flow: Optional[float] = Field(None, description="Minimum monthly cash flow requirement")
    maximum_renovation_budget: Optional[float] = Field(None, description="Max renovation budget")


class InvestmentOpportunity(BaseModel):
    """Individual investment opportunity."""
    property_id: str
    address: str
    property_type: str
    current_price: float = Field(ge=0.0)
    predicted_value_1year: float = Field(ge=0.0)
    predicted_roi: float = Field(description="Predicted return on investment")
    cash_flow_potential: float = Field(description="Monthly cash flow potential")
    appreciation_forecast: float = Field(description="Annual appreciation forecast")
    risk_score: float = Field(ge=0.0, le=1.0, description="Investment risk score")
    market_rent: float = Field(ge=0.0)
    cap_rate: float = Field(description="Capitalization rate")
    renovation_needed: bool
    estimated_renovation_cost: float = Field(ge=0.0)
    neighborhood_score: float = Field(ge=0.0, le=1.0)
    investment_highlights: List[str] = Field(default_factory=list)
    potential_concerns: List[str] = Field(default_factory=list)


class InvestmentOpportunitiesResponse(BaseModel):
    """Investment opportunities analysis response."""
    opportunities: List[InvestmentOpportunity]
    search_criteria: Dict[str, Any]
    market_overview: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    total_opportunities_found: int
    analysis_date: datetime = Field(default_factory=datetime.now)


class MarketTrendsResponse(BaseModel):
    """Market trends data response."""
    neighborhood: str
    period_months: int
    historical_data: Dict[str, List[float]] = Field(default_factory=dict)
    predicted_data: Dict[str, List[float]] = Field(default_factory=dict)
    trend_analysis: Dict[str, Any] = Field(default_factory=dict)
    seasonal_patterns: Dict[str, List[float]] = Field(default_factory=dict)
    market_velocity: float = Field(description="Market velocity indicator")
    inventory_levels: Dict[str, float] = Field(default_factory=dict)
    price_segments: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)


# ================== INTEGRATION & DASHBOARD SCHEMAS ==================

class DashboardMetrics(BaseModel):
    """Unified dashboard metrics from all modules."""
    voice_ai: Dict[str, Any] = Field(default_factory=dict)
    marketing: Dict[str, Any] = Field(default_factory=dict)
    client_retention: Dict[str, Any] = Field(default_factory=dict)
    market_predictions: Dict[str, Any] = Field(default_factory=dict)
    integration_health: Dict[str, Any] = Field(default_factory=dict)
    summary_insights: List[str] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    refresh_interval_seconds: int = Field(default=300)


class ModuleHealthStatus(BaseModel):
    """Health status of individual modules."""
    module_name: str
    status: str = Field(description="healthy, degraded, down, maintenance")
    last_check: datetime
    uptime_percentage: float = Field(ge=0.0, le=100.0)
    response_time_ms: float = Field(ge=0.0)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list)
    resource_usage: Dict[str, float] = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    """Overall system health response."""
    overall_status: str = Field(description="Overall system health status")
    modules: List[ModuleHealthStatus]
    system_metrics: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    last_check: datetime = Field(default_factory=datetime.now)


class IntegrationEventRequest(BaseModel):
    """Request to trigger integration event."""
    event_type: EventTypeAPI
    event_data: Dict[str, Any] = Field(..., description="Event-specific data")
    priority: str = Field(default="normal", description="Event priority")
    source_module: str = Field(default="manual", description="Module that triggered event")
    correlation_id: Optional[str] = Field(None, description="Event correlation ID")


class IntegrationEventResponse(BaseModel):
    """Integration event response."""
    event_id: str
    event_type: EventTypeAPI
    status: str
    actions_triggered: List[str] = Field(default_factory=list)
    modules_notified: List[str] = Field(default_factory=list)
    processing_time_ms: float
    correlation_id: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.now)


# ================== CONFIGURATION SCHEMAS ==================

class ModuleConfiguration(BaseModel):
    """Configuration for individual modules."""
    module_name: str
    enabled: bool = Field(default=True)
    settings: Dict[str, Any] = Field(default_factory=dict)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    rate_limits: Dict[str, int] = Field(default_factory=dict)
    integration_endpoints: Dict[str, str] = Field(default_factory=dict)


class SystemConfiguration(BaseModel):
    """Overall system configuration."""
    voice_ai: ModuleConfiguration
    marketing: ModuleConfiguration
    retention: ModuleConfiguration
    market_prediction: ModuleConfiguration
    integration: Dict[str, Any] = Field(default_factory=dict)
    global_settings: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)


# ================== ERROR SCHEMAS ==================

class APIError(BaseModel):
    """Standard API error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error response."""
    error: str = "validation_error"
    message: str
    field_errors: List[Dict[str, str]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


# ================== UTILITY SCHEMAS ==================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total_count: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_prev: bool


class FilterParams(BaseModel):
    """Common filtering parameters."""
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    status: Optional[str] = Field(None, description="Status filter")
    tags: Optional[List[str]] = Field(None, description="Tag filters")
    search: Optional[str] = Field(None, description="Search query", max_length=200)


# Common model configuration for all schemas (Pydantic V2)
COMMON_MODEL_CONFIG = ConfigDict(
    use_enum_values=True,
    validate_assignment=True,
    extra="forbid",
)