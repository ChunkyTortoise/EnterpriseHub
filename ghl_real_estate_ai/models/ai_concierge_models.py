"""
AI Concierge Models for Jorge's Real Estate AI Platform

Comprehensive Pydantic models for proactive intelligence, coaching opportunities,
strategy recommendations, and conversation quality assessment. These models enable
the AI Concierge to anticipate needs and provide intelligent guidance before being asked.

Key Features:
- Proactive insight generation with confidence scoring
- Real-time coaching opportunity detection
- Strategy recommendation with business impact assessment
- Conversation quality monitoring with actionable feedback
- Full validation and serialization for API and event systems

Performance Considerations:
- Optimized for <2s insight generation pipeline
- Efficient serialization for WebSocket event publishing
- Minimal memory footprint for real-time monitoring
- Cache-friendly data structures with TTL support
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, validator, root_validator


class InsightType(str, Enum):
    """Types of proactive insights the AI Concierge can generate."""

    COACHING = "coaching"                           # Real-time coaching opportunities
    STRATEGY_PIVOT = "strategy_pivot"               # Suggest conversation direction changes
    OBJECTION_PREDICTION = "objection_prediction"  # Anticipate and prepare for objections
    OPPORTUNITY_DETECTION = "opportunity_detection" # Identify closing or upselling opportunities
    CONVERSATION_QUALITY = "conversation_quality"   # Assess and improve conversation effectiveness
    RELATIONSHIP_BUILDING = "relationship_building" # Enhance rapport and connection
    VALUE_ARTICULATION = "value_articulation"      # Improve value proposition communication


class InsightPriority(str, Enum):
    """Priority levels for proactive insights to guide attention and response timing."""

    CRITICAL = "critical"    # Immediate attention required (conversation stalling, major objection)
    HIGH = "high"           # Important guidance (closing opportunity, strategic pivot needed)
    MEDIUM = "medium"       # Helpful suggestion (coaching improvement, relationship building)
    LOW = "low"             # Nice-to-have insight (general quality improvement)


class CoachingCategory(str, Enum):
    """Categories of coaching opportunities for targeted skill development."""

    OBJECTION_HANDLING = "objection_handling"      # How to address specific objections
    VALUE_PROPOSITION = "value_proposition"        # Articulating Jorge's unique value
    CLOSING_TECHNIQUES = "closing_techniques"      # Moving prospects toward decisions
    RAPPORT_BUILDING = "rapport_building"          # Enhancing personal connection
    NEEDS_DISCOVERY = "needs_discovery"           # Uncovering deeper motivations
    URGENCY_CREATION = "urgency_creation"         # Building appropriate time pressure
    FOLLOW_UP_STRATEGY = "follow_up_strategy"     # Optimizing next steps and timing


class StrategyType(str, Enum):
    """Types of strategic recommendations for conversation direction."""

    PIVOT_TO_BUYER = "pivot_to_buyer"             # Switch to buyer-focused conversation
    ESCALATE_URGENCY = "escalate_urgency"         # Increase timeline pressure appropriately
    DEMONSTRATE_VALUE = "demonstrate_value"        # Showcase Jorge's track record
    BUILD_RAPPORT = "build_rapport"               # Focus on relationship development
    QUALIFY_DEEPER = "qualify_deeper"             # Dig deeper into financial readiness
    SCHEDULE_MEETING = "schedule_meeting"         # Move to in-person or video meeting
    REQUEST_REFERRAL = "request_referral"        # Ask for additional leads


class ConversationTone(str, Enum):
    """Conversation tone classifications for appropriate response strategy."""

    CONFRONTATIONAL = "confrontational"    # Jorge's direct, no-BS approach
    CONSULTATIVE = "consultative"         # Educational and advisory tone
    RELATIONSHIP = "relationship"         # Rapport-building and personal
    TRANSACTIONAL = "transactional"      # Direct business-focused interaction


class ConversationStage(str, Enum):
    """Conversation progression stages for context-aware guidance."""

    INITIAL_CONTACT = "initial_contact"       # First interaction
    QUALIFICATION = "qualification"          # Assessing fit and readiness
    NEEDS_DISCOVERY = "needs_discovery"      # Understanding requirements
    VALUE_PRESENTATION = "value_presentation" # Showcasing Jorge's services
    OBJECTION_HANDLING = "objection_handling" # Addressing concerns
    CLOSING = "closing"                      # Moving toward commitment
    FOLLOW_UP = "follow_up"                  # Post-conversation nurturing


# ============================================================================
# Core Proactive Intelligence Models
# ============================================================================

class ProactiveInsight(BaseModel):
    """
    Core model for proactive AI insights that anticipate needs before being asked.

    Represents intelligent observations about conversation state with actionable
    recommendations for improving outcomes.
    """

    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique insight identifier")
    insight_type: InsightType = Field(..., description="Category of insight provided")
    priority: InsightPriority = Field(..., description="Urgency level for addressing this insight")

    # Core insight content
    title: str = Field(..., min_length=5, max_length=100, description="Concise insight headline")
    description: str = Field(..., min_length=20, max_length=500, description="Detailed insight explanation")
    reasoning: str = Field(..., min_length=10, max_length=300, description="Why this insight was generated")

    # Actionable recommendations
    recommended_actions: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Specific actions to take based on this insight"
    )
    suggested_responses: List[str] = Field(
        default_factory=list,
        max_items=3,
        description="Suggested conversation responses or talking points"
    )

    # Confidence and impact assessment
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in this insight (0.0-1.0)"
    )
    expected_impact: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Expected positive impact if action is taken (0.0-1.0)"
    )

    # Context and targeting
    conversation_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant conversation context that triggered this insight"
    )
    applicable_stage: ConversationStage = Field(
        ...,
        description="Conversation stage where this insight is most relevant"
    )

    # Lifecycle management
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Insight generation timestamp")
    expires_at: datetime = Field(..., description="When this insight becomes stale/irrelevant")
    dismissed: bool = Field(default=False, description="Whether user dismissed this insight")
    acted_upon: bool = Field(default=False, description="Whether user took action on this insight")
    effectiveness_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Measured effectiveness if action was taken (for learning)"
    )

    @validator('expires_at')
    def expires_at_must_be_future(cls, v, values):
        created_at = values.get('created_at', datetime.utcnow())
        if v <= created_at:
            raise ValueError('expires_at must be after created_at')
        return v

    @root_validator
    def validate_insight_content(cls, values):
        insight_type = values.get('insight_type')
        priority = values.get('priority')
        confidence = values.get('confidence_score', 0)

        # High-priority insights require higher confidence
        if priority == InsightPriority.CRITICAL and confidence < 0.8:
            raise ValueError('Critical priority insights require confidence >= 0.8')
        elif priority == InsightPriority.HIGH and confidence < 0.7:
            raise ValueError('High priority insights require confidence >= 0.7')

        return values

    def is_expired(self) -> bool:
        """Check if this insight has expired and should be removed."""
        return datetime.utcnow() > self.expires_at

    def is_actionable(self) -> bool:
        """Check if this insight is still actionable (not dismissed/expired)."""
        return not self.dismissed and not self.is_expired()

    class Config:
        schema_extra = {
            "example": {
                "insight_id": "insight_12345",
                "insight_type": "objection_prediction",
                "priority": "high",
                "title": "Price objection likely based on conversation tone",
                "description": "Lead has mentioned budget concerns 3 times and hesitation patterns suggest price objection coming",
                "reasoning": "Pattern recognition shows 85% probability of price objection in next 2-3 messages",
                "recommended_actions": [
                    "Proactively address value vs. cost",
                    "Share recent success story with similar client",
                    "Emphasize ROI and market timing"
                ],
                "suggested_responses": [
                    "I understand budget is important. Let me show you exactly how we maximize your return...",
                    "Similar clients initially had the same concern, but here's what happened..."
                ],
                "confidence_score": 0.85,
                "expected_impact": 0.75,
                "conversation_context": {
                    "recent_messages": 5,
                    "budget_mentions": 3,
                    "hesitation_markers": ["um", "well", "I need to think"],
                    "current_ml_score": 72.5
                },
                "applicable_stage": "value_presentation",
                "created_at": "2024-01-01T12:00:00Z",
                "expires_at": "2024-01-01T14:00:00Z"
            }
        }


class CoachingOpportunity(BaseModel):
    """
    Specific coaching opportunity detected in real-time conversation analysis.

    Provides targeted skill development suggestions based on conversation patterns,
    missed opportunities, or areas for improvement.
    """

    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique opportunity identifier")
    coaching_category: CoachingCategory = Field(..., description="Type of coaching needed")

    # Opportunity detection
    detected_pattern: str = Field(..., min_length=10, max_length=200, description="Pattern that triggered this opportunity")
    missed_opportunity: str = Field(..., min_length=10, max_length=200, description="What was missed or could be improved")

    # Coaching content
    coaching_insight: str = Field(..., min_length=20, max_length=400, description="Educational insight for skill development")
    recommended_technique: str = Field(..., min_length=10, max_length=200, description="Specific technique to apply")
    example_response: str = Field(..., min_length=20, max_length=300, description="Example of better response")

    # Success prediction
    success_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability of improved outcome with coaching (0.0-1.0)"
    )
    skill_level_required: str = Field(
        ...,
        regex="^(beginner|intermediate|advanced)$",
        description="Skill level needed to implement this coaching"
    )

    # Context and timing
    conversation_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant conversation context for this coaching"
    )
    immediate_application: bool = Field(
        ...,
        description="Whether this coaching can be applied in current conversation"
    )

    # Learning and improvement tracking
    learning_objective: str = Field(..., min_length=10, max_length=150, description="What skill will be developed")
    related_insights: List[str] = Field(
        default_factory=list,
        description="IDs of related insights or previous coaching"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    acknowledged: bool = Field(default=False, description="Whether coaching was acknowledged by user")

    def get_coaching_priority(self) -> InsightPriority:
        """Calculate priority based on success probability and immediacy."""
        if self.immediate_application and self.success_probability > 0.8:
            return InsightPriority.HIGH
        elif self.success_probability > 0.7:
            return InsightPriority.MEDIUM
        else:
            return InsightPriority.LOW

    class Config:
        schema_extra = {
            "example": {
                "opportunity_id": "coaching_67890",
                "coaching_category": "objection_handling",
                "detected_pattern": "Lead raised price concern but agent didn't acknowledge emotion first",
                "missed_opportunity": "Could have validated concern before presenting value",
                "coaching_insight": "Always acknowledge the emotional component of objections before addressing logical aspects",
                "recommended_technique": "Feel-Felt-Found method with empathy bridge",
                "example_response": "I understand price is a real concern - other successful sellers felt the same way initially. What they found was...",
                "success_probability": 0.82,
                "skill_level_required": "intermediate",
                "immediate_application": True,
                "learning_objective": "Master empathetic objection handling for price concerns"
            }
        }


class StrategyRecommendation(BaseModel):
    """
    Strategic recommendation for conversation direction and approach modification.

    Suggests high-level strategic pivots to improve conversation outcomes based on
    real-time analysis of conversation trajectory and lead characteristics.
    """

    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique recommendation identifier")
    strategy_type: StrategyType = Field(..., description="Type of strategic recommendation")

    # Strategy content
    strategy_title: str = Field(..., min_length=10, max_length=100, description="Clear strategy headline")
    strategy_description: str = Field(..., min_length=20, max_length=400, description="Detailed strategy explanation")
    rationale: str = Field(..., min_length=15, max_length=300, description="Why this strategy is recommended now")

    # Implementation guidance
    implementation_steps: List[str] = Field(
        ...,
        min_items=2,
        max_items=6,
        description="Step-by-step implementation guide"
    )
    conversation_pivot: str = Field(
        ...,
        min_length=20,
        max_length=200,
        description="How to transition conversation to this strategy"
    )

    # Impact and timing
    expected_outcome: str = Field(..., min_length=10, max_length=200, description="Expected positive outcome")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Expected impact on conversion (0.0-1.0)")
    urgency_level: str = Field(
        ...,
        regex="^(immediate|soon|when_appropriate)$",
        description="When to implement this strategy"
    )

    # Context and conditions
    trigger_conditions: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Conditions that triggered this recommendation"
    )
    success_indicators: List[str] = Field(
        ...,
        min_items=1,
        max_items=4,
        description="How to know if strategy is working"
    )

    # Risk and alternatives
    risk_level: str = Field(
        ...,
        regex="^(low|medium|high)$",
        description="Risk level of implementing this strategy"
    )
    fallback_strategy: Optional[str] = Field(
        None,
        max_length=200,
        description="Alternative approach if this strategy doesn't work"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Recommendation timestamp")
    implemented: bool = Field(default=False, description="Whether strategy was implemented")
    effectiveness_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Measured effectiveness after implementation"
    )

    def get_priority(self) -> InsightPriority:
        """Calculate priority based on urgency and impact."""
        if self.urgency_level == "immediate" and self.impact_score > 0.8:
            return InsightPriority.CRITICAL
        elif self.urgency_level in ["immediate", "soon"] and self.impact_score > 0.6:
            return InsightPriority.HIGH
        else:
            return InsightPriority.MEDIUM

    class Config:
        schema_extra = {
            "example": {
                "recommendation_id": "strategy_98765",
                "strategy_type": "pivot_to_buyer",
                "strategy_title": "Shift from seller to buyer conversation",
                "strategy_description": "Lead shows buyer signals - ready to transition from seller-focused to buyer consultation",
                "rationale": "Lead asked about available properties twice and mentioned moving timeline",
                "implementation_steps": [
                    "Acknowledge seller interest completion",
                    "Ask about their next home purchase plans",
                    "Transition to buyer consultation mode",
                    "Uncover buyer timeline and preferences"
                ],
                "conversation_pivot": "Since we've covered your selling timeline, I'm curious about your next move - have you started looking at what you'd like to purchase?",
                "expected_outcome": "Dual-side client with both listing and buyer representation",
                "impact_score": 0.85,
                "urgency_level": "soon",
                "trigger_conditions": [
                    "Buyer questions asked (2x)",
                    "Moving timeline mentioned",
                    "Property search behavior detected"
                ],
                "success_indicators": [
                    "Lead engages with buyer questions",
                    "Shares property preferences",
                    "Agrees to buyer consultation"
                ],
                "risk_level": "low"
            }
        }


# ============================================================================
# Conversation Quality and Assessment Models
# ============================================================================

class ConversationQualityScore(BaseModel):
    """
    Comprehensive conversation quality assessment with actionable improvement areas.

    Provides real-time quality scoring across multiple dimensions with specific
    guidance for enhancement.
    """

    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique assessment identifier")
    conversation_id: str = Field(..., description="Associated conversation identifier")

    # Overall quality metrics
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall conversation quality (0-100)")
    quality_grade: str = Field(
        ...,
        regex="^(A|B|C|D|F)$",
        description="Letter grade for conversation quality"
    )

    # Dimensional scores
    engagement_score: float = Field(..., ge=0.0, le=100.0, description="Lead engagement and participation")
    rapport_score: float = Field(..., ge=0.0, le=100.0, description="Relationship building and connection")
    needs_discovery_score: float = Field(..., ge=0.0, le=100.0, description="Effectiveness of needs assessment")
    value_articulation_score: float = Field(..., ge=0.0, le=100.0, description="Value proposition communication")
    objection_handling_score: float = Field(..., ge=0.0, le=100.0, description="Response to concerns and objections")
    closing_effectiveness_score: float = Field(..., ge=0.0, le=100.0, description="Moving toward next steps/commitment")

    # Conversation characteristics
    conversation_length: int = Field(..., ge=0, description="Total messages in conversation")
    response_time_avg: float = Field(..., ge=0.0, description="Average response time in minutes")
    lead_participation_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of conversation from lead")

    # Improvement areas
    strengths: List[str] = Field(..., max_items=5, description="Conversation strengths identified")
    improvement_areas: List[str] = Field(..., max_items=5, description="Areas needing improvement")
    specific_recommendations: List[str] = Field(..., max_items=6, description="Actionable improvement suggestions")

    # Trend and context
    quality_trend: str = Field(
        ...,
        regex="^(improving|declining|stable)$",
        description="Quality trend compared to recent conversations"
    )
    stage_appropriateness: float = Field(..., ge=0.0, le=1.0, description="How well approach matches conversation stage")

    assessed_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")
    next_assessment_due: datetime = Field(..., description="When next quality check should occur")

    @root_validator
    def calculate_overall_score(cls, values):
        """Calculate overall score from dimensional scores."""
        dimensional_scores = [
            values.get('engagement_score', 0),
            values.get('rapport_score', 0),
            values.get('needs_discovery_score', 0),
            values.get('value_articulation_score', 0),
            values.get('objection_handling_score', 0),
            values.get('closing_effectiveness_score', 0)
        ]

        # Weighted average (closing and value articulation weighted higher)
        weights = [1.0, 1.0, 1.0, 1.2, 1.1, 1.3]
        weighted_score = sum(score * weight for score, weight in zip(dimensional_scores, weights)) / sum(weights)

        # Update overall score if not provided
        if 'overall_score' not in values:
            values['overall_score'] = round(weighted_score, 1)

        # Determine grade
        overall_score = values.get('overall_score', 0)
        if overall_score >= 90:
            values['quality_grade'] = 'A'
        elif overall_score >= 80:
            values['quality_grade'] = 'B'
        elif overall_score >= 70:
            values['quality_grade'] = 'C'
        elif overall_score >= 60:
            values['quality_grade'] = 'D'
        else:
            values['quality_grade'] = 'F'

        return values

    def get_improvement_priority(self) -> InsightPriority:
        """Determine improvement priority based on overall score and trend."""
        if self.overall_score < 60 or self.quality_trend == "declining":
            return InsightPriority.HIGH
        elif self.overall_score < 75:
            return InsightPriority.MEDIUM
        else:
            return InsightPriority.LOW

    class Config:
        schema_extra = {
            "example": {
                "assessment_id": "quality_54321",
                "conversation_id": "conv_12345",
                "overall_score": 78.5,
                "quality_grade": "B",
                "engagement_score": 82.0,
                "rapport_score": 75.0,
                "needs_discovery_score": 80.0,
                "value_articulation_score": 85.0,
                "objection_handling_score": 70.0,
                "closing_effectiveness_score": 75.0,
                "conversation_length": 24,
                "response_time_avg": 1.2,
                "lead_participation_rate": 0.65,
                "strengths": [
                    "Excellent rapport building",
                    "Strong value articulation",
                    "Good response timing"
                ],
                "improvement_areas": [
                    "Objection handling technique",
                    "Stronger closing attempts",
                    "Deeper needs discovery"
                ],
                "specific_recommendations": [
                    "Use feel-felt-found method for objections",
                    "Ask for commitment more directly",
                    "Ask more 'why' questions about motivations"
                ],
                "quality_trend": "improving",
                "stage_appropriateness": 0.85
            }
        }


class ConversationTrajectory(BaseModel):
    """
    Predicted conversation trajectory and outcome analysis.

    Uses conversation patterns and ML analysis to predict likely outcomes
    and recommend trajectory adjustments.
    """

    trajectory_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique trajectory identifier")
    conversation_id: str = Field(..., description="Associated conversation identifier")

    # Prediction outcomes
    predicted_outcome: str = Field(
        ...,
        regex="^(conversion|nurture|disqualify|schedule_meeting|request_callback)$",
        description="Most likely conversation outcome"
    )
    outcome_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in predicted outcome")
    outcome_probabilities: Dict[str, float] = Field(
        ...,
        description="Probability distribution across all possible outcomes"
    )

    # Timing predictions
    estimated_time_to_decision: int = Field(..., ge=0, description="Hours until decision point")
    estimated_messages_remaining: int = Field(..., ge=0, description="Messages likely remaining in conversation")
    optimal_follow_up_timing: str = Field(
        ...,
        description="When to follow up if conversation pauses"
    )

    # Trajectory analysis
    current_stage: ConversationStage = Field(..., description="Current conversation stage")
    stage_progression: List[str] = Field(..., description="Expected stage progression")
    stall_probability: float = Field(..., ge=0.0, le=1.0, description="Probability conversation will stall")
    acceleration_opportunities: List[str] = Field(
        default_factory=list,
        description="Ways to accelerate toward positive outcome"
    )

    # Risk factors
    risk_factors: List[str] = Field(default_factory=list, description="Factors that could derail conversation")
    mitigation_strategies: List[str] = Field(default_factory=list, description="How to address risk factors")

    # Conversation momentum
    momentum_score: float = Field(..., ge=0.0, le=1.0, description="Current conversation momentum (0-1)")
    momentum_trend: str = Field(
        ...,
        regex="^(accelerating|stable|decelerating|stalled)$",
        description="Momentum trend"
    )

    # Recommendations
    recommended_next_steps: List[str] = Field(..., max_items=4, description="Specific next step recommendations")
    conversation_adjustments: List[str] = Field(
        default_factory=list,
        description="Suggested adjustments to improve trajectory"
    )

    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    next_analysis_due: datetime = Field(..., description="When to reassess trajectory")

    @validator('outcome_probabilities')
    def probabilities_sum_to_one(cls, v):
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):  # Allow small floating point error
            raise ValueError('Outcome probabilities must sum to approximately 1.0')
        return v

    def get_urgency_level(self) -> InsightPriority:
        """Determine urgency based on trajectory analysis."""
        if (self.stall_probability > 0.7 or
            self.momentum_trend in ["decelerating", "stalled"] or
            len(self.risk_factors) >= 3):
            return InsightPriority.CRITICAL
        elif (self.stall_probability > 0.4 or
              self.momentum_score < 0.6):
            return InsightPriority.HIGH
        else:
            return InsightPriority.MEDIUM

    class Config:
        schema_extra = {
            "example": {
                "trajectory_id": "traj_11111",
                "conversation_id": "conv_12345",
                "predicted_outcome": "schedule_meeting",
                "outcome_confidence": 0.78,
                "outcome_probabilities": {
                    "schedule_meeting": 0.45,
                    "nurture": 0.30,
                    "conversion": 0.15,
                    "disqualify": 0.10
                },
                "estimated_time_to_decision": 48,
                "estimated_messages_remaining": 8,
                "optimal_follow_up_timing": "24 hours if no response",
                "current_stage": "value_presentation",
                "stage_progression": ["value_presentation", "objection_handling", "closing"],
                "stall_probability": 0.25,
                "acceleration_opportunities": [
                    "Direct meeting request",
                    "Share success story",
                    "Create urgency with market conditions"
                ],
                "momentum_score": 0.75,
                "momentum_trend": "stable",
                "recommended_next_steps": [
                    "Request specific meeting time",
                    "Send calendar link",
                    "Prepare property analysis"
                ]
            }
        }


# ============================================================================
# Event and Communication Models
# ============================================================================

class ProactiveEvent(BaseModel):
    """Base model for proactive intelligence events published via WebSocket."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier")
    event_type: str = Field(..., description="Type of proactive event")
    conversation_id: str = Field(..., description="Associated conversation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    priority: InsightPriority = Field(..., description="Event priority level")

    # Event payload
    data: Dict[str, Any] = Field(..., description="Event-specific data payload")

    # Delivery tracking
    delivered: bool = Field(default=False, description="Whether event was delivered to client")
    acknowledged: bool = Field(default=False, description="Whether client acknowledged event")

    class Config:
        schema_extra = {
            "example": {
                "event_id": "evt_12345",
                "event_type": "proactive_insight",
                "conversation_id": "conv_67890",
                "priority": "high",
                "data": {
                    "insight_type": "coaching",
                    "title": "Opportunity for rapport building",
                    "description": "Lead mentioned personal interest in gardening - connection opportunity"
                }
            }
        }


class InsightAcceptance(BaseModel):
    """Model for tracking insight acceptance and effectiveness."""

    acceptance_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique acceptance identifier")
    insight_id: str = Field(..., description="ID of accepted insight")
    action_taken: str = Field(..., min_length=5, max_length=200, description="Action taken based on insight")
    outcome_observed: str = Field(..., min_length=5, max_length=200, description="Observed outcome after action")
    effectiveness_rating: float = Field(..., ge=0.0, le=1.0, description="User rating of insight effectiveness")

    accepted_at: datetime = Field(default_factory=datetime.utcnow, description="Acceptance timestamp")
    outcome_measured_at: Optional[datetime] = Field(None, description="When outcome was measured")

    class Config:
        schema_extra = {
            "example": {
                "acceptance_id": "accept_98765",
                "insight_id": "insight_12345",
                "action_taken": "Used suggested response about gardening connection",
                "outcome_observed": "Lead became more engaged, shared more personal details",
                "effectiveness_rating": 0.9,
                "accepted_at": "2024-01-01T12:00:00Z"
            }
        }


# ============================================================================
# Aggregation and Summary Models
# ============================================================================

class ConversationIntelligenceSummary(BaseModel):
    """Comprehensive summary of conversation intelligence and insights."""

    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique summary identifier")
    conversation_id: str = Field(..., description="Associated conversation")

    # Insight summary
    total_insights_generated: int = Field(..., ge=0, description="Total insights generated")
    insights_by_type: Dict[str, int] = Field(..., description="Count of insights by type")
    insights_by_priority: Dict[str, int] = Field(..., description="Count of insights by priority")

    # Action and effectiveness
    insights_acted_upon: int = Field(..., ge=0, description="Number of insights acted upon")
    average_effectiveness: float = Field(..., ge=0.0, le=1.0, description="Average effectiveness of acted-upon insights")
    most_valuable_insight_type: str = Field(..., description="Most valuable insight category")

    # Quality trends
    quality_score_trend: List[float] = Field(..., description="Quality scores over time")
    conversation_trajectory_trend: str = Field(..., description="Overall trajectory trend")

    # Key achievements
    breakthroughs: List[str] = Field(default_factory=list, description="Key conversation breakthroughs")
    missed_opportunities: List[str] = Field(default_factory=list, description="Identified missed opportunities")

    # Learning insights
    successful_strategies: List[str] = Field(default_factory=list, description="Strategies that worked well")
    areas_for_development: List[str] = Field(default_factory=list, description="Skills needing development")

    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Summary generation timestamp")
    covers_period: Dict[str, datetime] = Field(..., description="Time period covered by summary")

    class Config:
        schema_extra = {
            "example": {
                "summary_id": "summary_12345",
                "conversation_id": "conv_67890",
                "total_insights_generated": 12,
                "insights_by_type": {
                    "coaching": 4,
                    "strategy_pivot": 3,
                    "objection_prediction": 2,
                    "opportunity_detection": 3
                },
                "insights_by_priority": {
                    "critical": 1,
                    "high": 4,
                    "medium": 5,
                    "low": 2
                },
                "insights_acted_upon": 8,
                "average_effectiveness": 0.82,
                "most_valuable_insight_type": "objection_prediction",
                "breakthroughs": [
                    "Successfully pivoted to buyer conversation",
                    "Built strong rapport through shared interests"
                ],
                "successful_strategies": [
                    "Proactive objection handling",
                    "Personal connection building"
                ]
            }
        }


# Export all models for use throughout the application
__all__ = [
    # Enums
    "InsightType",
    "InsightPriority",
    "CoachingCategory",
    "StrategyType",
    "ConversationTone",
    "ConversationStage",

    # Core models
    "ProactiveInsight",
    "CoachingOpportunity",
    "StrategyRecommendation",
    "ConversationQualityScore",
    "ConversationTrajectory",

    # Event and tracking models
    "ProactiveEvent",
    "InsightAcceptance",
    "ConversationIntelligenceSummary"
]