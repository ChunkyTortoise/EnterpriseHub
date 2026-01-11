"""
Comprehensive data models for lead evaluation and agent assistance.

These models support the unified lead evaluation orchestrator system,
providing real-time analysis and guidance for real estate agents.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.config import ConfigDict


# Enums for standardized values
class ActionPriority(str, Enum):
    """Priority levels for recommended actions."""
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"


class QualificationStatus(str, Enum):
    """Status of qualification field completion."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"
    UNCLEAR = "unclear"
    CONFLICTING = "conflicting"


class ObjectionType(str, Enum):
    """Types of common objections in real estate."""
    PRICE = "price"
    TIMELINE = "timeline"
    LOCATION = "location"
    FINANCING = "financing"
    FEATURES = "features"
    MARKET_CONDITIONS = "market_conditions"
    TRUST = "trust"
    COMPETITION = "competition"
    FAMILY_DECISION = "family_decision"
    OTHER = "other"


class SentimentType(str, Enum):
    """Sentiment analysis categories."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


class EngagementLevel(str, Enum):
    """Lead engagement classification."""
    HIGHLY_ENGAGED = "highly_engaged"
    ENGAGED = "engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    PASSIVE = "passive"
    DISENGAGED = "disengaged"


# Core data models
class QualificationField(BaseModel):
    """Individual qualification field with status and confidence."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    field_name: str = Field(..., description="Name of the qualification field")
    status: QualificationStatus = Field(..., description="Current completion status")
    value: Optional[str] = Field(None, description="Extracted or provided value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the extracted value")
    source: str = Field(..., description="Source of the information (conversation, form, etc.)")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    attempts_count: int = Field(default=0, ge=0, description="Number of attempts to gather this field")
    notes: List[str] = Field(default_factory=list, description="Additional notes about this field")

    @validator('confidence')
    def validate_confidence(cls, v):
        return round(v, 3)


class UrgencySignals(BaseModel):
    """Signals indicating timeline urgency."""
    model_config = ConfigDict(validate_assignment=True)

    timeline_mentioned: bool = Field(default=False)
    specific_dates: List[str] = Field(default_factory=list)
    urgency_keywords: List[str] = Field(default_factory=list)
    life_event_triggers: List[str] = Field(default_factory=list)
    financial_pressure: bool = Field(default=False)
    market_timing_concerns: bool = Field(default=False)
    urgency_score: float = Field(default=0.0, ge=0.0, le=10.0)

    @validator('urgency_score')
    def validate_urgency_score(cls, v):
        return round(v, 2)


class ObjectionAnalysis(BaseModel):
    """Analysis of objections raised by the lead."""
    model_config = ConfigDict(validate_assignment=True)

    objection_type: ObjectionType
    raw_text: str = Field(..., description="Original text expressing the objection")
    severity: float = Field(..., ge=0.0, le=10.0, description="Severity of the objection")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in objection detection")
    suggested_responses: List[str] = Field(default_factory=list)
    talking_points: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('severity', 'confidence')
    def validate_scores(cls, v):
        return round(v, 2)


class ScoringBreakdown(BaseModel):
    """Detailed breakdown of lead scoring components."""
    model_config = ConfigDict(validate_assignment=True)

    # Individual scorer contributions
    basic_rules_score: float = Field(default=0.0, ge=0.0, le=100.0)
    advanced_intelligence_score: float = Field(default=0.0, ge=0.0, le=100.0)
    predictive_ml_score: float = Field(default=0.0, ge=0.0, le=100.0)
    urgency_detection_score: float = Field(default=0.0, ge=0.0, le=100.0)

    # Weighted components
    budget_alignment: float = Field(default=0.0, ge=0.0, le=100.0)
    location_preference: float = Field(default=0.0, ge=0.0, le=100.0)
    timeline_urgency: float = Field(default=0.0, ge=0.0, le=100.0)
    engagement_level: float = Field(default=0.0, ge=0.0, le=100.0)
    communication_quality: float = Field(default=0.0, ge=0.0, le=100.0)
    qualification_completeness: float = Field(default=0.0, ge=0.0, le=100.0)

    # Final composite score
    composite_score: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence_interval: tuple[float, float] = Field(default=(0.0, 0.0))

    # Metadata
    scoring_timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_versions: Dict[str, str] = Field(default_factory=dict)

    @validator('basic_rules_score', 'advanced_intelligence_score', 'predictive_ml_score',
             'urgency_detection_score', 'budget_alignment', 'location_preference',
             'timeline_urgency', 'engagement_level', 'communication_quality',
             'qualification_completeness', 'composite_score')
    def validate_scores(cls, v):
        return round(v, 2)


class QualificationProgress(BaseModel):
    """Overall qualification progress tracking."""
    model_config = ConfigDict(validate_assignment=True)

    total_fields: int = Field(..., gt=0)
    completed_fields: int = Field(default=0, ge=0)
    partial_fields: int = Field(default=0, ge=0)
    missing_fields: int = Field(default=0, ge=0)

    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    critical_fields_complete: bool = Field(default=False)
    qualification_tier: str = Field(default="unqualified")

    # Progress tracking
    last_field_completed: Optional[str] = Field(None)
    next_priority_fields: List[str] = Field(default_factory=list)
    estimated_completion_time: Optional[int] = Field(None, description="Minutes estimated to complete")

    @validator('completion_percentage')
    def validate_percentage(cls, v):
        return round(v, 2)

    @root_validator(skip_on_failure=True)
    def validate_field_counts(cls, values):
        total = values.get('total_fields', 0)
        completed = values.get('completed_fields', 0)
        partial = values.get('partial_fields', 0)
        missing = values.get('missing_fields', 0)

        if completed + partial + missing != total:
            values['missing_fields'] = total - completed - partial

        if total > 0:
            values['completion_percentage'] = round((completed / total) * 100, 2)

        return values


class RecommendedAction(BaseModel):
    """Specific action recommendation for the agent."""
    model_config = ConfigDict(validate_assignment=True)

    action_type: str = Field(..., description="Type of action to take")
    priority: ActionPriority
    description: str = Field(..., description="Detailed action description")
    reasoning: str = Field(..., description="Why this action is recommended")

    # Execution details
    suggested_script: Optional[str] = Field(None, description="Suggested conversation script")
    follow_up_questions: List[str] = Field(default_factory=list)
    required_information: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)

    # Metadata
    confidence: float = Field(..., ge=0.0, le=1.0)
    estimated_duration: Optional[int] = Field(None, description="Estimated minutes to complete")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None)

    @validator('confidence')
    def validate_confidence(cls, v):
        return round(v, 3)


class AgentAssistanceData(BaseModel):
    """Real-time assistance data for agents during conversations."""
    model_config = ConfigDict(validate_assignment=True)

    # Current conversation context
    current_sentiment: SentimentType = Field(default=SentimentType.NEUTRAL)
    engagement_level: EngagementLevel = Field(default=EngagementLevel.PASSIVE)
    conversation_flow_stage: str = Field(default="introduction")

    # Real-time insights
    detected_objections: List[ObjectionAnalysis] = Field(default_factory=list)
    urgency_signals: UrgencySignals = Field(default_factory=UrgencySignals)
    qualification_gaps: List[str] = Field(default_factory=list)

    # Recommendations
    immediate_actions: List[RecommendedAction] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    conversation_pivots: List[str] = Field(default_factory=list)

    # Contextual information
    property_matches_available: bool = Field(default=False)
    market_insights: List[str] = Field(default_factory=list)
    competitor_intelligence: List[str] = Field(default_factory=list)

    # Performance indicators
    conversation_effectiveness: float = Field(default=0.0, ge=0.0, le=10.0)
    rapport_building_score: float = Field(default=0.0, ge=0.0, le=10.0)
    information_gathering_rate: float = Field(default=0.0, ge=0.0, le=10.0)

    @validator('conversation_effectiveness', 'rapport_building_score', 'information_gathering_rate')
    def validate_scores(cls, v):
        return round(v, 2)


class LeadEvaluationResult(BaseModel):
    """Comprehensive lead evaluation result from the orchestrator."""
    model_config = ConfigDict(validate_assignment=True)

    # Basic identification
    lead_id: str = Field(..., description="Unique lead identifier")
    evaluation_id: str = Field(..., description="Unique evaluation instance ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Core scoring
    scoring_breakdown: ScoringBreakdown
    qualification_progress: QualificationProgress
    qualification_fields: Dict[str, QualificationField] = Field(default_factory=dict)

    # Real-time assistance
    agent_assistance: AgentAssistanceData
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)

    # Performance metadata
    evaluation_duration_ms: Optional[int] = Field(None)
    cache_hit_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    api_calls_made: int = Field(default=0, ge=0)

    # Version tracking
    orchestrator_version: str = Field(default="1.0.0")
    model_versions: Dict[str, str] = Field(default_factory=dict)

    # Quality indicators
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    data_freshness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evaluation_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @validator('confidence_score', 'data_freshness_score', 'evaluation_quality_score')
    def validate_quality_scores(cls, v):
        return round(v, 3)

    @validator('cache_hit_rate')
    def validate_cache_hit_rate(cls, v):
        return round(v, 3) if v is not None else v


# Specialized models for different evaluation contexts
class ConversationEvaluationContext(BaseModel):
    """Context for real-time conversation evaluation."""
    model_config = ConfigDict(validate_assignment=True)

    conversation_id: str
    messages_count: int = Field(default=0, ge=0)
    conversation_duration_seconds: int = Field(default=0, ge=0)
    last_message_timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_topic: Optional[str] = Field(None)
    agent_id: Optional[str] = Field(None)

    # Message analysis
    recent_messages: List[Dict[str, Any]] = Field(default_factory=list, max_items=10)
    conversation_summary: Optional[str] = Field(None)
    key_points_extracted: List[str] = Field(default_factory=list)

    # Real-time indicators
    response_time_pressure: bool = Field(default=False)
    live_assistance_enabled: bool = Field(default=True)
    escalation_required: bool = Field(default=False)


class BatchEvaluationContext(BaseModel):
    """Context for batch evaluation processing."""
    model_config = ConfigDict(validate_assignment=True)

    batch_id: str
    lead_ids: List[str] = Field(..., min_items=1)
    evaluation_type: str = Field(default="comprehensive")
    priority: str = Field(default="normal")

    # Processing options
    enable_ml_scoring: bool = Field(default=True)
    enable_advanced_intelligence: bool = Field(default=True)
    include_property_matching: bool = Field(default=False)
    generate_agent_assistance: bool = Field(default=False)

    # Performance tuning
    max_concurrent_evaluations: int = Field(default=5, gt=0, le=20)
    timeout_seconds: int = Field(default=30, gt=0, le=300)
    cache_results: bool = Field(default=True)


# Export all models
__all__ = [
    # Enums
    "ActionPriority",
    "QualificationStatus",
    "ObjectionType",
    "SentimentType",
    "EngagementLevel",

    # Core models
    "QualificationField",
    "UrgencySignals",
    "ObjectionAnalysis",
    "ScoringBreakdown",
    "QualificationProgress",
    "RecommendedAction",
    "AgentAssistanceData",
    "LeadEvaluationResult",

    # Context models
    "ConversationEvaluationContext",
    "BatchEvaluationContext",
]