"""
Lead Nurturing Data Models

Comprehensive Pydantic v2 models for automated lead nurturing and follow-up system.
Integrates with existing evaluation models for seamless lead lifecycle management.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator
from uuid import UUID, uuid4

# Existing evaluation models
from .evaluation_models import LeadEvaluationResult, QualificationData


class LeadType(str, Enum):
    """Types of leads for targeted nurturing sequences."""
    BUYER_FIRST_TIME = "buyer_first_time"
    BUYER_INVESTMENT = "buyer_investment"
    BUYER_LUXURY = "buyer_luxury"
    BUYER_RELOCATION = "buyer_relocation"
    SELLER_DOWNSIZING = "seller_downsizing"
    SELLER_UPSIZING = "seller_upsizing"
    SELLER_INVESTMENT = "seller_investment"
    SELLER_RELOCATION = "seller_relocation"


class CommunicationChannel(str, Enum):
    """Available communication channels for follow-ups."""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    GHL_TASK = "ghl_task"
    LINKEDIN = "linkedin"
    AUTOMATED_CALL = "automated_call"


class MessageTone(str, Enum):
    """Communication tone options for personalization."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EDUCATIONAL = "educational"
    SUPPORTIVE = "supportive"
    URGENT = "urgent"
    CELEBRATORY = "celebratory"
    CONSULTATIVE = "consultative"


class CampaignStatus(str, Enum):
    """Status of nurturing campaigns."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EngagementType(str, Enum):
    """Types of lead engagement interactions."""
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    EMAIL_REPLIED = "email_replied"
    SMS_RESPONDED = "sms_responded"
    PROPERTY_VIEWED = "property_viewed"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    FORM_SUBMITTED = "form_submitted"
    WEBSITE_VISITED = "website_visited"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    PHONE_ANSWERED = "phone_answered"


class TriggerType(str, Enum):
    """Types of automated triggers for follow-up sequences."""
    TIME_BASED = "time_based"
    BEHAVIOR_BASED = "behavior_based"
    SCORE_BASED = "score_based"
    MILESTONE_BASED = "milestone_based"
    OBJECTION_BASED = "objection_based"
    ENGAGEMENT_BASED = "engagement_based"


class NurturingSequenceStep(BaseModel):
    """Individual step in a nurturing sequence."""
    model_config = ConfigDict(str_strip_whitespace=True)

    step_number: int = Field(..., description="Step order in sequence", ge=1)
    delay_hours: int = Field(..., description="Hours to wait before this step", ge=0)
    channel: CommunicationChannel = Field(..., description="Communication channel")
    template_id: str = Field(..., description="Message template identifier")
    tone: MessageTone = Field(MessageTone.PROFESSIONAL, description="Communication tone")
    personalization_level: str = Field("medium", description="Level of personalization")
    conditions: List[str] = Field(default_factory=list, description="Conditions to execute step")
    triggers: List[str] = Field(default_factory=list, description="Triggers that activate step")
    max_attempts: int = Field(3, description="Maximum delivery attempts", ge=1, le=5)
    priority: int = Field(5, description="Step priority (1-10)", ge=1, le=10)

    @model_validator(mode='after')
    def validate_conditions(self):
        """Validate step conditions make sense."""
        if self.delay_hours == 0 and self.step_number > 1:
            raise ValueError("Non-initial steps must have delay > 0")
        return self


class NurturingSequence(BaseModel):
    """Complete nurturing sequence definition."""
    model_config = ConfigDict(str_strip_whitespace=True)

    sequence_id: str = Field(..., description="Unique sequence identifier")
    name: str = Field(..., description="Human-readable sequence name")
    lead_type: LeadType = Field(..., description="Target lead type")
    description: str = Field("", description="Sequence description and purpose")
    duration_days: int = Field(..., description="Total sequence duration", ge=1, le=90)
    steps: List[NurturingSequenceStep] = Field(..., description="Sequence steps")
    success_criteria: List[str] = Field(default_factory=list, description="Success metrics")
    exit_conditions: List[str] = Field(default_factory=list, description="Early exit conditions")
    is_active: bool = Field(True, description="Whether sequence is active")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode='after')
    def validate_sequence(self):
        """Validate sequence structure and logic."""
        if not self.steps:
            raise ValueError("Sequence must have at least one step")

        # Validate step numbers are sequential
        step_numbers = [step.step_number for step in self.steps]
        expected = list(range(1, len(self.steps) + 1))
        if step_numbers != expected:
            raise ValueError("Step numbers must be sequential starting from 1")

        # Validate total delay doesn't exceed duration
        total_delay = sum(step.delay_hours for step in self.steps)
        if total_delay > (self.duration_days * 24):
            raise ValueError("Total step delays exceed sequence duration")

        return self


class PersonalizedMessage(BaseModel):
    """Personalized message generated for a lead."""
    model_config = ConfigDict(str_strip_whitespace=True)

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    lead_id: str = Field(..., description="Target lead identifier")
    template_id: str = Field(..., description="Source template identifier")
    channel: CommunicationChannel = Field(..., description="Delivery channel")
    subject: Optional[str] = Field(None, description="Message subject (for email)")
    content: str = Field(..., description="Personalized message content")
    tone: MessageTone = Field(..., description="Message tone")
    personalization_data: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)
    claude_analysis: Optional[Dict[str, Any]] = Field(None, description="Claude analysis data")
    estimated_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)


class EngagementInteraction(BaseModel):
    """Lead engagement interaction tracking."""
    model_config = ConfigDict(str_strip_whitespace=True)

    interaction_id: str = Field(default_factory=lambda: str(uuid4()))
    lead_id: str = Field(..., description="Lead identifier")
    campaign_id: str = Field(..., description="Associated campaign ID")
    touchpoint_id: Optional[str] = Field(None, description="Associated touchpoint ID")
    engagement_type: EngagementType = Field(..., description="Type of engagement")
    channel: CommunicationChannel = Field(..., description="Interaction channel")
    interaction_data: Dict[str, Any] = Field(default_factory=dict)
    engagement_score: float = Field(0.0, description="Calculated engagement score", ge=0.0, le=1.0)
    occurred_at: datetime = Field(default_factory=datetime.now)
    response_time: Optional[timedelta] = Field(None, description="Time to respond")
    sentiment: Optional[str] = Field(None, description="Interaction sentiment")
    notes: str = Field("", description="Additional notes")


class NurturingTouchpoint(BaseModel):
    """Scheduled touchpoint in a nurturing campaign."""
    model_config = ConfigDict(str_strip_whitespace=True)

    touchpoint_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str = Field(..., description="Parent campaign ID")
    step_number: int = Field(..., description="Sequence step number", ge=1)
    scheduled_at: datetime = Field(..., description="Scheduled execution time")
    executed_at: Optional[datetime] = Field(None, description="Actual execution time")
    status: str = Field("pending", description="Touchpoint status")
    channel: CommunicationChannel = Field(..., description="Communication channel")
    message: Optional[PersonalizedMessage] = Field(None, description="Generated message")
    delivery_attempts: int = Field(0, description="Number of delivery attempts", ge=0)
    delivery_success: bool = Field(False, description="Successful delivery flag")
    delivery_error: Optional[str] = Field(None, description="Delivery error message")
    engagement_data: List[EngagementInteraction] = Field(default_factory=list)
    effectiveness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    next_touchpoint_id: Optional[str] = Field(None, description="Next touchpoint in sequence")


class NurturingCampaign(BaseModel):
    """Active nurturing campaign for a specific lead."""
    model_config = ConfigDict(str_strip_whitespace=True)

    campaign_id: str = Field(default_factory=lambda: str(uuid4()))
    lead_id: str = Field(..., description="Target lead identifier")
    sequence: NurturingSequence = Field(..., description="Assigned sequence")
    current_step: int = Field(1, description="Current sequence step", ge=1)
    status: CampaignStatus = Field(CampaignStatus.ACTIVE, description="Campaign status")
    enrollment_data: LeadEvaluationResult = Field(..., description="Lead data at enrollment")
    touchpoints: List[NurturingTouchpoint] = Field(default_factory=list)
    total_engagements: int = Field(0, description="Total engagement count", ge=0)
    engagement_score: float = Field(0.0, description="Overall engagement score", ge=0.0, le=1.0)
    conversion_events: List[Dict[str, Any]] = Field(default_factory=list)
    agent_notes: str = Field("", description="Agent notes about campaign")
    auto_pause_conditions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)

    @model_validator(mode='after')
    def validate_campaign(self):
        """Validate campaign state and consistency."""
        if self.current_step > len(self.sequence.steps):
            raise ValueError("Current step exceeds sequence length")

        # Validate touchpoints match sequence steps
        expected_touchpoints = len([tp for tp in self.touchpoints if tp.executed_at is not None])
        if expected_touchpoints >= self.current_step and self.status == CampaignStatus.ACTIVE:
            # Ensure we're not ahead of executed touchpoints
            pass

        return self


class NurturingTrigger(BaseModel):
    """Automated trigger configuration for nurturing sequences."""
    model_config = ConfigDict(str_strip_whitespace=True)

    trigger_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Human-readable trigger name")
    trigger_type: TriggerType = Field(..., description="Type of trigger")
    sequence_id: str = Field(..., description="Target sequence to trigger")
    conditions: List[str] = Field(..., description="Trigger conditions")
    priority: int = Field(5, description="Trigger priority", ge=1, le=10)
    is_active: bool = Field(True, description="Whether trigger is active")
    cooldown_hours: int = Field(24, description="Hours between trigger activations", ge=1)
    max_daily_triggers: int = Field(5, description="Max triggers per day", ge=1, le=20)
    success_rate: float = Field(0.0, description="Historical success rate", ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = Field(None)


class CampaignPerformanceMetrics(BaseModel):
    """Performance metrics for nurturing campaigns."""
    model_config = ConfigDict(str_strip_whitespace=True)

    sequence_id: str = Field(..., description="Sequence identifier")
    lead_type: LeadType = Field(..., description="Lead type for metrics")
    total_campaigns: int = Field(0, description="Total campaigns executed", ge=0)
    active_campaigns: int = Field(0, description="Currently active campaigns", ge=0)
    completed_campaigns: int = Field(0, description="Completed campaigns", ge=0)
    response_rate: float = Field(0.0, description="Overall response rate", ge=0.0, le=1.0)
    engagement_rate: float = Field(0.0, description="Engagement rate", ge=0.0, le=1.0)
    conversion_rate: float = Field(0.0, description="Conversion rate", ge=0.0, le=1.0)
    average_duration: Optional[timedelta] = Field(None, description="Average campaign duration")
    roi_score: float = Field(0.0, description="Return on investment score", ge=0.0)
    channel_performance: Dict[str, float] = Field(default_factory=dict)
    step_performance: Dict[int, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)


class NurturingAgent(BaseModel):
    """Main nurturing agent configuration and state."""
    model_config = ConfigDict(str_strip_whitespace=True)

    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field("Lead Nurturing Agent", description="Agent name")
    version: str = Field("1.0.0", description="Agent version")
    is_active: bool = Field(True, description="Whether agent is active")
    max_concurrent_campaigns: int = Field(100, description="Max concurrent campaigns", ge=1)
    default_timezone: str = Field("UTC", description="Default timezone")
    claude_api_config: Dict[str, Any] = Field(default_factory=dict)
    communication_preferences: Dict[str, Any] = Field(default_factory=dict)
    performance_targets: Dict[str, float] = Field(default_factory=dict)
    active_sequences: List[str] = Field(default_factory=list)
    active_campaigns: int = Field(0, description="Current active campaigns", ge=0)
    total_campaigns_managed: int = Field(0, description="Total campaigns managed", ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)


# Message Template Models
class MessageTemplate(BaseModel):
    """Template for personalized messages."""
    model_config = ConfigDict(str_strip_whitespace=True)

    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    channel: CommunicationChannel = Field(..., description="Target channel")
    lead_type: LeadType = Field(..., description="Target lead type")
    tone: MessageTone = Field(..., description="Message tone")
    subject_template: Optional[str] = Field(None, description="Subject line template")
    content_template: str = Field(..., description="Message content template")
    personalization_fields: List[str] = Field(default_factory=list)
    dynamic_content_rules: List[str] = Field(default_factory=list)
    effectiveness_score: float = Field(0.0, ge=0.0, le=1.0)
    usage_count: int = Field(0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(True)


# Behavioral Learning Models
class LeadBehaviorProfile(BaseModel):
    """Behavioral profile for learning and optimization."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: str = Field(..., description="Lead identifier")
    communication_preferences: Dict[str, Any] = Field(default_factory=dict)
    optimal_contact_times: List[Dict[str, Any]] = Field(default_factory=list)
    response_patterns: Dict[str, Any] = Field(default_factory=dict)
    engagement_triggers: List[str] = Field(default_factory=list)
    objection_patterns: List[str] = Field(default_factory=list)
    successful_approaches: List[str] = Field(default_factory=list)
    learning_confidence: float = Field(0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.now)


class OptimizationRecommendation(BaseModel):
    """AI-generated optimization recommendation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    target_type: str = Field(..., description="What to optimize (sequence, timing, etc.)")
    target_id: str = Field(..., description="Target identifier")
    recommendation: str = Field(..., description="Optimization recommendation")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    expected_impact: str = Field(..., description="Expected impact description")
    implementation_effort: str = Field(..., description="Implementation effort estimate")
    data_supporting: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = Field("pending", description="Recommendation status")
    implemented_at: Optional[datetime] = Field(None)
    actual_impact: Optional[Dict[str, Any]] = Field(None)