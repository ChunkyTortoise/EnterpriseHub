#!/usr/bin/env python3
"""
Seller Bot Data Models for Jorge's FastAPI Microservice

Type-safe Pydantic models for seller qualification API endpoints.
Based on architecture blueprint from Seller Bot Enhancement Agent.

Author: Claude Code Assistant
Created: January 23, 2026
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum


class SellerTemperature(str, Enum):
    """Seller temperature classification"""
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"


class SellerPriority(str, Enum):
    """Jorge's seller priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    REVIEW_REQUIRED = "review_required"


class WebhookType(str, Enum):
    """GHL webhook event types"""
    CONTACT_CREATED = "contact.created"
    CONTACT_UPDATED = "contact.updated"
    MESSAGE_RECEIVED = "message.received"
    CONVERSATION_NEW = "conversation.new"


# Request Models

class SellerMessage(BaseModel):
    """Seller message for analysis"""
    contact_id: str = Field(..., description="GHL contact ID")
    location_id: str = Field(..., description="GHL location ID")
    message: str = Field(..., description="Seller's message content")
    contact_data: Optional[Dict[str, Any]] = Field(None, description="Additional contact data from GHL")
    force_ai_analysis: bool = Field(False, description="Force Claude AI analysis over pattern matching")

    @validator('message')
    def message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

    @validator('contact_id', 'location_id')
    def ids_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Contact ID and Location ID are required')
        return v.strip()


class GHLSellerWebhook(BaseModel):
    """GHL webhook payload for seller events"""
    type: WebhookType = Field(..., description="Webhook event type")
    location_id: str = Field(..., description="GHL location ID")
    contact_id: str = Field(..., description="GHL contact ID")
    message: Optional[str] = Field(None, description="Message content if applicable")
    contact: Optional[Dict[str, Any]] = Field(None, description="Full contact object from GHL")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")


class SellerFollowupRequest(BaseModel):
    """Request for scheduled seller follow-up"""
    contact_id: str = Field(..., description="GHL contact ID")
    location_id: str = Field(..., description="GHL location ID")
    follow_up_type: str = Field(..., description="Type of follow-up (initial, reminder, escalation)")
    delay_hours: Optional[int] = Field(4, description="Hours to wait before follow-up")
    custom_message: Optional[str] = Field(None, description="Custom follow-up message")


# Response Models

class SellerQualificationStage(BaseModel):
    """Individual qualification stage data"""
    stage_number: int = Field(..., description="Question stage (1-4)")
    question_text: str = Field(..., description="The question asked")
    answer_received: bool = Field(..., description="Whether answer was provided")
    answer_quality: Optional[float] = Field(None, description="Answer quality score (0.0-1.0)")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Structured data extracted from answer")


class SellerBusinessRules(BaseModel):
    """Jorge's business rule validation results"""
    meets_budget_criteria: bool = Field(..., description="Meets $200K-$800K range")
    in_service_area: bool = Field(..., description="In Dallas/Plano/Frisco area")
    timeline_acceptable: bool = Field(..., description="Timeline within 60 days")
    overall_qualified: bool = Field(..., description="Passes all Jorge criteria")
    estimated_commission: float = Field(0.0, description="Estimated commission amount")
    disqualification_reasons: List[str] = Field(default_factory=list, description="Reasons for disqualification")


class SellerROIAnalysis(BaseModel):
    """ROI and pricing analysis results"""
    estimated_property_value: Optional[float] = Field(None, description="Estimated property value")
    commission_potential: float = Field(0.0, description="Potential commission at 6%")
    lead_value_tier: str = Field("standard", description="Lead value classification")
    pricing_confidence: float = Field(0.0, description="Confidence in pricing estimate")
    market_factors: Dict[str, Any] = Field(default_factory=dict, description="Market analysis factors")


class SellerPersonaData(BaseModel):
    """Psychographic persona analysis"""
    primary_persona: Optional[str] = Field(None, description="Detected primary persona")
    confidence_score: float = Field(0.0, description="Confidence in persona detection")
    behavioral_indicators: List[str] = Field(default_factory=list, description="Behavioral pattern indicators")
    communication_preference: str = Field("standard", description="Preferred communication style")


class SellerPerformanceMetrics(BaseModel):
    """Performance tracking for seller analysis"""
    response_time_ms: float = Field(..., description="Total analysis time in milliseconds")
    analysis_method: str = Field(..., description="Method used (pattern/ai/hybrid)")
    cache_hit: bool = Field(False, description="Whether result was cached")
    background_tasks_count: int = Field(0, description="Number of background tasks triggered")
    compliance_status: str = Field("unknown", description="Compliance with performance SLA")


class GHLAction(BaseModel):
    """Action to be performed in GHL"""
    action_type: str = Field(..., description="Type of action (add_tag, remove_tag, update_field, etc.)")
    target: str = Field(..., description="Target for action (tag name, field name, etc.)")
    value: Optional[Union[str, int, float, bool]] = Field(None, description="Value for action")
    priority: int = Field(1, description="Action priority (1=highest)")


class SellerAnalysisResponse(BaseModel):
    """Complete seller analysis response"""
    success: bool = Field(..., description="Whether analysis completed successfully")
    contact_id: str = Field(..., description="GHL contact ID")

    # Core qualification results
    seller_temperature: SellerTemperature = Field(..., description="Seller temperature (HOT/WARM/COLD)")
    jorge_priority: SellerPriority = Field(..., description="Jorge's priority classification")
    questions_answered: int = Field(0, description="Number of qualification questions answered")
    qualification_stages: List[SellerQualificationStage] = Field(default_factory=list, description="Detailed stage results")

    # Business analysis
    business_rules: SellerBusinessRules = Field(..., description="Jorge's business rule validation")
    roi_analysis: Optional[SellerROIAnalysis] = Field(None, description="ROI and pricing analysis")
    persona_data: Optional[SellerPersonaData] = Field(None, description="Psychographic analysis")

    # Response generation
    response_message: str = Field(..., description="Generated response message for seller")
    next_steps: str = Field(..., description="Recommended next steps")

    # Actions and automation
    ghl_actions: List[GHLAction] = Field(default_factory=list, description="Actions to perform in GHL")
    trigger_voice_ai: bool = Field(False, description="Whether to trigger Vapi voice AI")
    schedule_followup: bool = Field(False, description="Whether to schedule follow-up")

    # Performance and analytics
    performance: SellerPerformanceMetrics = Field(..., description="Performance tracking data")
    analytics_data: Dict[str, Any] = Field(default_factory=dict, description="Additional analytics data")

    # Error handling
    errors: List[str] = Field(default_factory=list, description="Any errors encountered during analysis")
    warnings: List[str] = Field(default_factory=list, description="Warnings or edge cases detected")


class WebhookResponse(BaseModel):
    """Response to GHL webhook"""
    success: bool = Field(..., description="Whether webhook processed successfully")
    contact_id: str = Field(..., description="Processed contact ID")
    processing_time_ms: float = Field(..., description="Total processing time")
    background_tasks_triggered: int = Field(0, description="Number of background tasks started")
    message: str = Field("Processed successfully", description="Status message")


# Analytics and Metrics Models

class SellerTemperatureDistribution(BaseModel):
    """Temperature distribution analytics"""
    hot_sellers: int = Field(0, description="Count of HOT sellers")
    warm_sellers: int = Field(0, description="Count of WARM sellers")
    cold_sellers: int = Field(0, description="Count of COLD sellers")
    hot_percentage: float = Field(0.0, description="Percentage of HOT sellers")
    warm_percentage: float = Field(0.0, description="Percentage of WARM sellers")
    cold_percentage: float = Field(0.0, description="Percentage of COLD sellers")


class SellerQualificationFunnel(BaseModel):
    """Qualification funnel analytics"""
    question_1_completion: float = Field(0.0, description="% completing question 1")
    question_2_completion: float = Field(0.0, description="% completing question 2")
    question_3_completion: float = Field(0.0, description="% completing question 3")
    question_4_completion: float = Field(0.0, description="% completing question 4 (HOT)")
    dropout_rate: float = Field(0.0, description="Overall dropout rate")
    avg_questions_per_seller: float = Field(0.0, description="Average questions answered")


class SellerROIAnalytics(BaseModel):
    """ROI and commission analytics"""
    avg_commission_potential: float = Field(0.0, description="Average commission potential")
    total_pipeline_value: float = Field(0.0, description="Total estimated pipeline value")
    high_value_leads_count: int = Field(0, description="Count of leads >$500K")
    commission_by_temperature: Dict[str, float] = Field(default_factory=dict, description="Commission by temperature")
    pricing_accuracy: float = Field(0.0, description="Pricing estimation accuracy")


class SellerMetricsResponse(BaseModel):
    """Comprehensive seller metrics response"""
    timeframe: str = Field(..., description="Metrics timeframe (24h, 7d, 30d)")
    total_sellers: int = Field(0, description="Total sellers processed")

    # Performance metrics
    avg_response_time_ms: float = Field(0.0, description="Average analysis response time")
    performance_sla_compliance: float = Field(0.0, description="% meeting <500ms SLA")
    five_minute_rule_compliance: float = Field(0.0, description="% meeting 5-minute rule")

    # Business metrics
    temperature_distribution: SellerTemperatureDistribution = Field(..., description="Temperature breakdown")
    qualification_funnel: SellerQualificationFunnel = Field(..., description="Funnel analytics")
    roi_analytics: SellerROIAnalytics = Field(..., description="ROI and commission data")

    # Jorge-specific KPIs
    jorge_qualified_sellers: int = Field(0, description="Sellers meeting Jorge's criteria")
    hot_seller_conversion_rate: float = Field(0.0, description="% of sellers reaching HOT")
    voice_ai_triggers: int = Field(0, description="Vapi voice AI triggers")
    estimated_monthly_commission: float = Field(0.0, description="Projected monthly commission")

    # System health
    error_rate: float = Field(0.0, description="Analysis error rate")
    cache_hit_rate: float = Field(0.0, description="Cache effectiveness")
    background_task_success_rate: float = Field(0.0, description="Background task success rate")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status (healthy/unhealthy/degraded)")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field("1.0.0", description="Service version")

    # Component health
    seller_engine_status: str = Field("unknown", description="JorgeSellerEngine status")
    ghl_client_status: str = Field("unknown", description="GHL client connectivity")
    conversation_manager_status: str = Field("unknown", description="ConversationManager status")
    claude_api_status: str = Field("unknown", description="Claude API connectivity")

    # Performance indicators
    avg_response_time_ms: float = Field(0.0, description="Recent average response time")
    active_conversations: int = Field(0, description="Currently active conversations")
    pending_background_tasks: int = Field(0, description="Pending background tasks")

    # Warnings and alerts
    warnings: List[str] = Field(default_factory=list, description="System warnings")
    alerts: List[str] = Field(default_factory=list, description="Active alerts")


# Configuration Models

class SellerBotConfig(BaseModel):
    """Seller bot configuration"""
    performance_timeout_ms: int = Field(500, description="Analysis timeout in milliseconds")
    webhook_timeout_ms: int = Field(2000, description="Webhook processing timeout")
    hot_questions_required: int = Field(4, description="Questions required for HOT temperature")
    hot_quality_threshold: float = Field(0.7, description="Answer quality threshold for HOT")
    warm_questions_required: int = Field(3, description="Questions required for WARM temperature")

    # Jorge business rules
    min_budget: int = Field(200000, description="Minimum budget requirement")
    max_budget: int = Field(800000, description="Maximum budget for focus")
    service_areas: List[str] = Field(
        default=["Dallas", "Plano", "Frisco", "McKinney", "Allen", "Richardson"],
        description="Jorge's service areas"
    )
    commission_rate: float = Field(0.06, description="Commission rate (6%)")
    confrontational_level: str = Field("high", description="Jorge's confrontational level")

    # Feature flags
    enable_claude_ai: bool = Field(True, description="Enable Claude AI analysis")
    enable_voice_ai_handoff: bool = Field(True, description="Enable Vapi voice AI")
    enable_background_tasks: bool = Field(True, description="Enable background GHL tasks")
    enable_caching: bool = Field(True, description="Enable response caching")


# Error Models

class SellerBotError(BaseModel):
    """Standard error response"""
    error: bool = Field(True, description="Indicates this is an error response")
    error_code: str = Field(..., description="Error code for debugging")
    message: str = Field(..., description="Human-readable error message")
    contact_id: Optional[str] = Field(None, description="Contact ID if applicable")
    timestamp: datetime = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    @classmethod
    def internal_error(cls, message: str, contact_id: Optional[str] = None) -> "SellerBotError":
        return cls(
            error_code="INTERNAL_ERROR",
            message=message,
            contact_id=contact_id,
            timestamp=datetime.now()
        )

    @classmethod
    def validation_error(cls, message: str, contact_id: Optional[str] = None) -> "SellerBotError":
        return cls(
            error_code="VALIDATION_ERROR",
            message=message,
            contact_id=contact_id,
            timestamp=datetime.now()
        )

    @classmethod
    def timeout_error(cls, message: str, contact_id: Optional[str] = None) -> "SellerBotError":
        return cls(
            error_code="TIMEOUT_ERROR",
            message=message,
            contact_id=contact_id,
            timestamp=datetime.now()
        )