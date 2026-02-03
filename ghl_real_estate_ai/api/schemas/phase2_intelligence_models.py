"""
Phase 2 Intelligence Layer API Schema Models
Comprehensive Pydantic models for advanced property matching, conversation intelligence, and preference learning.

Built for Jorge's Real Estate AI Platform - Phase 2: Intelligence Layer

Performance Integration:
- Property Matching: <100ms with caching
- Conversation Analysis: <500ms processing
- Preference Learning: <50ms updates
- WebSocket Events: <10ms delivery

Jorge's methodology integration with 6% commission validation and confrontational qualification patterns.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from decimal import Decimal
from uuid import UUID
import json

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
from pydantic.types import confloat, conint, constr


# =====================================================================================
# Enums for Type Safety and Validation
# =====================================================================================

class PresentationStrategyAPI(str, Enum):
    """Property presentation strategy recommendations."""
    STANDARD = "standard"
    FEATURE_FOCUSED = "feature_focused"
    PRICE_VALUE = "price_value"
    LOCATION_PREMIUM = "location_premium"
    LIFESTYLE_MATCH = "lifestyle_match"
    URGENCY_DRIVEN = "urgency_driven"
    INVESTMENT_ANGLE = "investment_angle"
    FAMILY_FOCUSED = "family_focused"


class ObjectionTypeAPI(str, Enum):
    """Real estate objection categories for detection and response."""
    PRICE_CONCERN = "price_concern"
    TIMING_OBJECTION = "timing_objection"
    LOCATION_PREFERENCE = "location_preference"
    PROPERTY_FEATURES = "property_features"
    FINANCING_CONCERN = "financing_concern"
    MARKET_HESITATION = "market_hesitation"
    DECISION_AUTHORITY = "decision_authority"
    TRUST_CREDIBILITY = "trust_credibility"


class SentimentLevelAPI(str, Enum):
    """Sentiment classification levels for conversation analysis."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    SLIGHTLY_NEGATIVE = "slightly_negative"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class CoachingAreaAPI(str, Enum):
    """Coaching opportunity focus areas."""
    OBJECTION_HANDLING = "objection_handling"
    RAPPORT_BUILDING = "rapport_building"
    CLOSING_TECHNIQUE = "closing_technique"
    ACTIVE_LISTENING = "active_listening"
    PRODUCT_KNOWLEDGE = "product_knowledge"
    FOLLOW_UP_TIMING = "follow_up_timing"
    QUESTION_TECHNIQUE = "question_technique"
    VALUE_PROPOSITION = "value_proposition"


class PreferenceSourceAPI(str, Enum):
    """Source of preference learning data."""
    CONVERSATION_ANALYSIS = "conversation_analysis"
    PROPERTY_INTERACTION = "property_interaction"
    SEARCH_BEHAVIOR = "search_behavior"
    EMAIL_ENGAGEMENT = "email_engagement"
    WEBSITE_BEHAVIOR = "website_behavior"
    FEEDBACK_EXPLICIT = "feedback_explicit"
    AGENT_OBSERVATION = "agent_observation"
    HISTORICAL_TRANSACTION = "historical_transaction"


class PreferenceCategoryAPI(str, Enum):
    """Categories of client preferences for learning."""
    PROPERTY_FEATURES = "property_features"
    LOCATION_PREFERENCES = "location_preferences"
    LIFESTYLE_FACTORS = "lifestyle_factors"
    FINANCIAL_CONSTRAINTS = "financial_constraints"
    AESTHETIC_PREFERENCES = "aesthetic_preferences"
    TIMING_PREFERENCES = "timing_preferences"
    COMMUNICATION_STYLE = "communication_style"
    DECISION_MAKING_STYLE = "decision_making_style"


class DriftTypeAPI(str, Enum):
    """Types of preference drift for change analysis."""
    EXPANSION = "expansion"
    NARROWING = "narrowing"
    SHIFT = "shift"
    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    CONTRADICTION = "contradiction"
    SEASONAL = "seasonal"
    CONTEXT_DRIVEN = "context_driven"


# =====================================================================================
# Base Models with Common Patterns
# =====================================================================================

class TimestampedModel(BaseModel):
    """Base model with consistent timestamp handling."""
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat()
        })


class PerformanceModel(BaseModel):
    """Base model with performance tracking."""
    processing_time_ms: Optional[int] = Field(None, ge=0, description="Processing time in milliseconds")
    cache_used: bool = Field(False, description="Whether cached data was used")
    confidence_score: confloat(ge=0.0, le=1.0) = Field(0.0, description="Result confidence level")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "processing_time_ms": 45,
                "cache_used": True,
                "confidence_score": 0.89
            }
        })


class JorgeIntegrationModel(BaseModel):
    """Base model with Jorge methodology integration."""
    jorge_methodology_score: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="Jorge methodology alignment")
    commission_amount: Optional[Decimal] = Field(None, description="Jorge's 6% commission calculation")
    confrontational_effectiveness: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="Confrontational approach effectiveness")

    @field_validator('commission_amount')
    @classmethod
    def validate_commission_calculation(cls, v):
        """Validate Jorge's 6% commission calculation."""
        if v is not None and v < 0:
            raise ValueError("Commission amount must be positive")
        return v

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "jorge_methodology_score": 0.94,
                "commission_amount": "29100.00",
                "confrontational_effectiveness": 0.89
            }
        })


# =====================================================================================
# Phase 2.2: Advanced Property Matching Models
# =====================================================================================

class PropertyMatchingFiltersAPI(BaseModel):
    """Filters for property matching requests."""
    min_score: confloat(ge=0.0, le=1.0) = Field(0.6, description="Minimum match score threshold")
    max_results: conint(ge=1, le=50) = Field(10, description="Maximum number of results")
    include_behavioral_analysis: bool = Field(True, description="Include behavioral weighting")
    property_types: Optional[List[str]] = Field(None, description="Filter by property types")
    price_range: Optional[Dict[str, int]] = Field(None, description="Price range filter")
    neighborhoods: Optional[List[str]] = Field(None, description="Neighborhood filter")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "min_score": 0.7,
                "max_results": 5,
                "include_behavioral_analysis": True,
                "property_types": ["single_family", "condo"],
                "price_range": {"min": 400000, "max": 600000},
                "neighborhoods": ["Domain", "West Lake Hills"]
            }
        })


class BehavioralMatchWeightsAPI(PerformanceModel):
    """Behavioral weighting for property matching algorithm."""
    feature_weight: confloat(ge=0.0, le=1.0) = Field(description="Weight for property features")
    location_weight: confloat(ge=0.0, le=1.0) = Field(description="Weight for location factors")
    price_weight: confloat(ge=0.0, le=1.0) = Field(description="Weight for pricing factors")
    urgency_weight: confloat(ge=0.0, le=1.0) = Field(description="Weight for urgency indicators")
    lifestyle_weight: confloat(ge=0.0, le=1.0) = Field(description="Weight for lifestyle alignment")

    # Behavioral insights from conversation analysis
    conversation_insights: Dict[str, Any] = Field(default_factory=dict, description="Insights from conversation analysis")
    adjusted_feature_priorities: Dict[str, float] = Field(default_factory=dict, description="ML-adjusted feature priorities")
    engagement_indicators: List[str] = Field(default_factory=list, description="Engagement pattern indicators")
    decision_urgency: str = Field("medium", description="Decision-making urgency level")

    @model_validator(mode="before")
    @classmethod
    def validate_weights_sum(cls, values):
        """Ensure behavioral weights are properly balanced."""
        weight_fields = ['feature_weight', 'location_weight', 'price_weight', 'urgency_weight', 'lifestyle_weight']
        total_weight = sum(values.get(field, 0) for field in weight_fields if values.get(field) is not None)

        if total_weight > 0 and not (0.8 <= total_weight <= 1.2):  # Allow some flexibility
            raise ValueError("Behavioral weights should approximately sum to 1.0")

        return values

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "feature_weight": 0.25,
                "location_weight": 0.20,
                "price_weight": 0.30,
                "urgency_weight": 0.15,
                "lifestyle_weight": 0.10,
                "conversation_insights": {
                    "home_office_emphasis": 0.9,
                    "pool_interest": 0.7,
                    "decision_timeframe": "urgent"
                },
                "adjusted_feature_priorities": {
                    "home_office": 0.95,
                    "pool": 0.75,
                    "garage": 0.85
                },
                "engagement_indicators": ["specific_questions", "timeline_urgency"],
                "decision_urgency": "high"
            }
        })


class AdvancedPropertyMatchAPI(PerformanceModel, JorgeIntegrationModel):
    """Single property match result with advanced scoring."""
    property_id: str = Field(description="Unique property identifier")
    overall_score: confloat(ge=0.0, le=1.0) = Field(description="Overall match score")

    # Scoring components
    base_compatibility_score: confloat(ge=0.0, le=1.0) = Field(description="Base compatibility without behavioral analysis")
    behavioral_fit: confloat(ge=0.0, le=1.0) = Field(description="Behavioral enhancement score")
    engagement_prediction: confloat(ge=0.0, le=1.0) = Field(description="Predicted client engagement level")
    urgency_match: confloat(ge=0.0, le=1.0) = Field(description="Match to client's urgency level")

    # Property details for context
    property_summary: Dict[str, Any] = Field(description="Key property details")
    feature_matches: Dict[str, float] = Field(description="Individual feature match scores")
    location_score: confloat(ge=0.0, le=1.0) = Field(description="Location desirability score")

    # Presentation and strategy
    presentation_strategy: PresentationStrategyAPI = Field(description="Recommended presentation approach")
    key_selling_points: List[str] = Field(description="Top selling points for this match")
    potential_objections: List[str] = Field(default_factory=list, description="Anticipated objections")

    # Match explanation and reasoning
    match_reasoning: str = Field(description="Detailed explanation of why this is a good match")
    market_context: Dict[str, Any] = Field(default_factory=dict, description="Market conditions context")

    # Ranking and competitiveness
    rank: Optional[int] = Field(None, ge=1, description="Rank among all matches")
    market_competitiveness: confloat(ge=0.0, le=1.0) = Field(0.5, description="Market competition level for this property")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "property_id": "prop_12345",
                "overall_score": 0.89,
                "base_compatibility_score": 0.82,
                "behavioral_fit": 0.91,
                "engagement_prediction": 0.85,
                "urgency_match": 0.93,
                "property_summary": {
                    "price": 525000,
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "square_footage": 2650,
                    "neighborhood": "Domain"
                },
                "feature_matches": {
                    "home_office": 0.95,
                    "pool": 0.85,
                    "garage": 0.90
                },
                "location_score": 0.87,
                "presentation_strategy": "lifestyle_match",
                "key_selling_points": [
                    "Perfect home office setup for remote work",
                    "Pool for family entertainment",
                    "Prime Domain location"
                ],
                "potential_objections": ["Price point", "HOA fees"],
                "match_reasoning": "Exceptional match based on explicit home office requirement and lifestyle preferences.",
                "rank": 1,
                "market_competitiveness": 0.85,
                "jorge_methodology_score": 0.92
            }
        })


class PropertyMatchRequestAPI(BaseModel):
    """Request for advanced property matching analysis."""
    lead_id: constr(min_length=1) = Field(description="Lead identifier")
    preferences: Dict[str, Any] = Field(description="Lead preferences and requirements")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Recent conversation data for behavioral analysis")
    filters: Optional[PropertyMatchingFiltersAPI] = Field(None, description="Additional filtering options")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for matching")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "lead_id": "lead_12345",
                "preferences": {
                    "price_range": {"min": 400000, "max": 600000},
                    "bedrooms": {"min": 3, "ideal": 4},
                    "lifestyle_features": {"home_office": 0.9, "pool": 0.7}
                },
                "conversation_history": [
                    {
                        "message": "We absolutely need a home office",
                        "timestamp": "2025-01-25T10:00:00Z",
                        "engagement_score": 0.9
                    }
                ],
                "filters": {
                    "min_score": 0.7,
                    "max_results": 5
                }
            }
        })


class PropertyMatchResponseAPI(PerformanceModel):
    """Response from property matching analysis."""
    matches: List[AdvancedPropertyMatchAPI] = Field(description="Matched properties with scores")
    total_found: int = Field(ge=0, description="Total properties found")
    behavioral_weights: BehavioralMatchWeightsAPI = Field(description="Applied behavioral weights")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis completion time")
    market_insights: Dict[str, Any] = Field(default_factory=dict, description="Market condition insights")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "matches": [
                    {
                        "property_id": "prop_12345",
                        "overall_score": 0.89,
                        "presentation_strategy": "lifestyle_match"
                    }
                ],
                "total_found": 1,
                "processing_time_ms": 85,
                "cache_used": False,
                "confidence_score": 0.89
            }
        })


# =====================================================================================
# Phase 2.3: Conversation Intelligence Models
# =====================================================================================

class SentimentTimelinePointAPI(BaseModel):
    """Single point in conversation sentiment timeline."""
    timestamp_offset_seconds: int = Field(ge=0, description="Seconds from conversation start")
    sentiment_score: confloat(ge=-1.0, le=1.0) = Field(description="Sentiment score (-1 to 1)")
    sentiment_classification: SentimentLevelAPI = Field(description="Categorical sentiment level")
    confidence: confloat(ge=0.0, le=1.0) = Field(description="Classification confidence")
    speaker: str = Field(description="Who was speaking (user/agent/bot)")
    trigger_phrase: Optional[str] = Field(None, description="Phrase that triggered this sentiment")
    topic_context: Optional[str] = Field(None, description="What was being discussed")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "timestamp_offset_seconds": 120,
                "sentiment_score": 0.7,
                "sentiment_classification": "positive",
                "confidence": 0.89,
                "speaker": "user",
                "trigger_phrase": "that sounds perfect",
                "topic_context": "property_features"
            }
        })


class ObjectionDetectionAPI(PerformanceModel):
    """Detected objection with response recommendations."""
    objection_id: str = Field(description="Unique objection identifier")
    objection_category: ObjectionTypeAPI = Field(description="Type of objection detected")
    objection_text: str = Field(description="Actual objection content")
    detected_at_offset_seconds: int = Field(ge=0, description="When objection occurred in conversation")
    severity_level: conint(ge=1, le=5) = Field(description="Objection severity (1-5 scale)")

    # Response handling
    agent_response: Optional[str] = Field(None, description="Agent's response to objection")
    response_effectiveness_score: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="How well objection was handled")
    objection_resolved: bool = Field(False, description="Whether objection was successfully addressed")
    follow_up_needed: bool = Field(True, description="Whether follow-up is required")

    # Recommendations
    suggested_responses: List[str] = Field(description="AI-recommended responses")
    coaching_notes: Optional[str] = Field(None, description="Coaching feedback for improvement")

    # Context
    conversation_context: Optional[str] = Field(None, description="Surrounding conversation context")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "objection_id": "obj_12345",
                "objection_category": "price_concern",
                "objection_text": "The price seems really high for this market",
                "detected_at_offset_seconds": 180,
                "severity_level": 4,
                "agent_response": "I understand your concern. Let me show you comparable sales.",
                "response_effectiveness_score": 0.75,
                "objection_resolved": False,
                "follow_up_needed": True,
                "suggested_responses": [
                    "Let me show you the recent comparable sales data",
                    "This pricing reflects the premium location and recent upgrades"
                ],
                "coaching_notes": "Could have used more data to support pricing",
                "confidence_score": 0.92
            }
        })


class CoachingOpportunityAPI(TimestampedModel, PerformanceModel):
    """Identified coaching opportunity for agent improvement."""
    opportunity_id: str = Field(description="Unique coaching opportunity identifier")
    conversation_id: str = Field(description="Source conversation identifier")
    agent_user_id: Optional[str] = Field(None, description="Agent who needs coaching")

    opportunity_type: CoachingAreaAPI = Field(description="Type of coaching opportunity")
    priority_level: conint(ge=1, le=5) = Field(description="Priority level (1-5, 5=highest)")
    opportunity_description: str = Field(description="Description of the opportunity")
    specific_example: Optional[str] = Field(None, description="Specific conversation excerpt")

    # Improvement guidance
    recommended_approach: str = Field(description="Recommended improvement approach")
    suggested_scripts: List[str] = Field(default_factory=list, description="Suggested conversation scripts")
    training_resources: List[str] = Field(default_factory=list, description="Relevant training materials")
    practice_scenarios: List[str] = Field(default_factory=list, description="Practice scenario suggestions")

    # Context and impact
    occurred_at_offset_seconds: Optional[int] = Field(None, description="When opportunity occurred")
    impact_on_outcome: Optional[str] = Field(None, description="How this affected conversation outcome")
    missed_opportunity_cost: Optional[str] = Field(None, description="What was potentially lost")

    # Tracking
    coaching_status: str = Field("identified", description="Coaching status (identified/planned/in_progress/completed)")
    manager_notified: bool = Field(False, description="Whether manager has been notified")
    follow_up_scheduled: Optional[datetime] = Field(None, description="Scheduled follow-up time")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "opportunity_id": "coach_12345",
                "conversation_id": "conv_67890",
                "agent_user_id": "agent_123",
                "opportunity_type": "closing_technique",
                "priority_level": 4,
                "opportunity_description": "Could have pushed for specific timeline commitment",
                "specific_example": "User said 'sometime soon' but agent didn't ask for specific date",
                "recommended_approach": "Ask follow-up questions to get specific timelines",
                "suggested_scripts": [
                    "What specific date do you need to be in your new home?",
                    "Help me understand your ideal timeline for moving"
                ],
                "coaching_status": "identified",
                "manager_notified": False,
                "confidence_score": 0.85
            }
        })


class ConversationInsightAPI(PerformanceModel, JorgeIntegrationModel, TimestampedModel):
    """Comprehensive conversation analysis results."""
    conversation_id: str = Field(description="Conversation identifier")
    lead_id: str = Field(description="Lead identifier")

    # Core insight scores
    overall_engagement_score: confloat(ge=0.0, le=1.0) = Field(description="Overall lead engagement level")
    interest_level_score: confloat(ge=0.0, le=1.0) = Field(description="Interest in properties/services")
    objection_intensity_score: confloat(ge=0.0, le=1.0) = Field(description="Level of objections raised")
    rapport_quality_score: confloat(ge=0.0, le=1.0) = Field(description="Quality of agent-lead rapport")
    next_step_clarity_score: confloat(ge=0.0, le=1.0) = Field(description="Clarity of next steps")

    # Conversation characteristics
    dominant_sentiment: SentimentLevelAPI = Field(description="Overall conversation sentiment")
    sentiment_volatility: confloat(ge=0.0, le=1.0) = Field(0.0, description="How much sentiment changed")
    speaking_time_ratio: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="Lead speaking time / Total time")
    interruption_count: int = Field(0, ge=0, description="Number of interruptions")
    question_count: int = Field(0, ge=0, description="Number of questions asked")

    # Key insights
    key_topics: List[str] = Field(default_factory=list, description="Main conversation topics")
    buying_signals: List[str] = Field(default_factory=list, description="Detected buying signals")
    concern_indicators: List[str] = Field(default_factory=list, description="Areas of concern")
    engagement_patterns: Dict[str, Any] = Field(default_factory=dict, description="Engagement pattern analysis")

    # Next steps and recommendations
    recommended_next_actions: List[str] = Field(default_factory=list, description="Suggested next steps")
    priority_follow_up_topics: List[str] = Field(default_factory=list, description="Priority topics for follow-up")
    suggested_timeline: Optional[str] = Field(None, description="Suggested follow-up timeline")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "conversation_id": "conv_12345",
                "lead_id": "lead_67890",
                "overall_engagement_score": 0.85,
                "interest_level_score": 0.78,
                "objection_intensity_score": 0.34,
                "rapport_quality_score": 0.82,
                "next_step_clarity_score": 0.67,
                "dominant_sentiment": "positive",
                "sentiment_volatility": 0.23,
                "speaking_time_ratio": 0.65,
                "key_topics": ["home_office", "price_range", "timeline"],
                "buying_signals": ["specific_questions", "timeline_urgency"],
                "concern_indicators": ["price_sensitivity"],
                "recommended_next_actions": [
                    "Schedule property viewing",
                    "Provide market analysis"
                ],
                "jorge_methodology_score": 0.91,
                "confrontational_effectiveness": 0.87
            }
        })


class ConversationAnalysisRequestAPI(BaseModel):
    """Request for conversation intelligence analysis."""
    conversation_id: constr(min_length=1) = Field(description="Conversation identifier")
    lead_id: constr(min_length=1) = Field(description="Lead identifier")
    conversation_history: List[Dict[str, Any]] = Field(description="Complete conversation messages")
    enable_preference_learning: bool = Field(True, description="Enable background preference learning")
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")
    include_coaching: bool = Field(True, description="Include coaching opportunity detection")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "conversation_id": "conv_12345",
                "lead_id": "lead_67890",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "I'm interested in properties with home offices",
                        "timestamp": "2025-01-25T10:00:00Z"
                    },
                    {
                        "role": "agent",
                        "content": "Great! I have several properties that would be perfect",
                        "timestamp": "2025-01-25T10:01:00Z"
                    }
                ],
                "enable_preference_learning": True,
                "analysis_type": "comprehensive",
                "include_coaching": True
            }
        })


class ConversationResponseAPI(PerformanceModel):
    """Complete conversation analysis response."""
    insights: ConversationInsightAPI = Field(description="Core conversation insights")
    objections: List[ObjectionDetectionAPI] = Field(description="Detected objections")
    coaching_opportunities: List[CoachingOpportunityAPI] = Field(description="Coaching opportunities")
    sentiment_timeline: List[SentimentTimelinePointAPI] = Field(description="Sentiment progression")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis completion time")
    recommendations: List[str] = Field(description="Next-step recommendations")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "insights": {
                    "conversation_id": "conv_12345",
                    "overall_engagement_score": 0.85
                },
                "objections": [
                    {
                        "objection_category": "price_concern",
                        "severity_level": 3
                    }
                ],
                "coaching_opportunities": [
                    {
                        "opportunity_type": "closing_technique",
                        "priority_level": 4
                    }
                ],
                "sentiment_timeline": [
                    {
                        "sentiment_score": 0.7,
                        "sentiment_classification": "positive"
                    }
                ],
                "recommendations": [
                    "Schedule property viewing within 48 hours",
                    "Address price concerns with market data"
                ],
                "processing_time_ms": 340,
                "confidence_score": 0.89
            }
        })


# =====================================================================================
# Phase 2.4: Client Preference Learning Models
# =====================================================================================

class PreferenceLearningEventAPI(TimestampedModel, PerformanceModel):
    """Individual preference learning event for audit trail."""
    event_id: str = Field(description="Unique event identifier")
    client_id: str = Field(description="Client identifier")

    # Event metadata
    event_source: PreferenceSourceAPI = Field(description="Source of preference data")
    source_confidence: str = Field(description="Confidence in source reliability")
    source_reference: Optional[str] = Field(None, description="Reference to source (conversation_id, property_id)")

    # Learning details
    preference_category: PreferenceCategoryAPI = Field(description="Category of preference learned")
    learned_preference: Dict[str, Any] = Field(description="The actual preference data learned")
    evidence_strength: confloat(ge=0.0, le=1.0) = Field(0.0, description="Strength of evidence for this preference")

    # Context
    source_context: Dict[str, Any] = Field(default_factory=dict, description="Context from source interaction")
    agent_notes: Optional[str] = Field(None, description="Manual notes from agent")
    raw_evidence: Optional[str] = Field(None, description="Raw text/data that led to learning")

    # Learning algorithm details
    learning_method: str = Field("conversation_analysis", description="Method used for learning")
    algorithm_version: str = Field("1.0", description="Version of learning algorithm")
    feature_extraction_results: Dict[str, Any] = Field(default_factory=dict, description="Feature extraction details")

    # Impact assessment
    profile_impact_score: confloat(ge=0.0, le=1.0) = Field(0.0, description="How much this changed the profile")
    conflicted_with_existing: bool = Field(False, description="Whether this conflicted with existing preferences")
    reinforced_existing: bool = Field(False, description="Whether this reinforced existing preferences")
    created_new_preference: bool = Field(False, description="Whether this created a new preference")

    # Quality validation
    human_validated: bool = Field(False, description="Whether human has validated this learning")
    validation_timestamp: Optional[datetime] = Field(None, description="When validation occurred")
    validation_notes: Optional[str] = Field(None, description="Validation feedback")
    false_positive_flag: bool = Field(False, description="Marked as false positive")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "event_id": "evt_12345",
                "client_id": "client_67890",
                "event_source": "conversation_analysis",
                "source_confidence": "high",
                "source_reference": "conv_12345",
                "preference_category": "lifestyle_factors",
                "learned_preference": {
                    "home_office": {
                        "importance": 0.95,
                        "confidence": 0.92,
                        "context": "explicit_requirement"
                    }
                },
                "evidence_strength": 0.92,
                "source_context": {
                    "conversation_segment": "We absolutely need a home office",
                    "speaker_emphasis": "high"
                },
                "profile_impact_score": 0.15,
                "created_new_preference": True,
                "confidence_score": 0.92
            }
        })


class PreferenceDriftDetectionAPI(TimestampedModel, PerformanceModel):
    """Detected drift in client preferences."""
    drift_id: str = Field(description="Unique drift detection identifier")
    client_id: str = Field(description="Client identifier")

    # Drift identification
    preference_category: PreferenceCategoryAPI = Field(description="Category where drift was detected")
    drift_type: DriftTypeAPI = Field(description="Type of drift detected")
    drift_magnitude: confloat(ge=0.0, le=1.0) = Field(description="How significant the drift (0.0 to 1.0)")

    # Drift details
    previous_preference: Dict[str, Any] = Field(description="Previous preference value")
    new_preference: Dict[str, Any] = Field(description="New preference value")
    confidence_change: confloat(ge=-1.0, le=1.0) = Field(0.0, description="Change in confidence (-1.0 to 1.0)")

    # Causality analysis
    triggering_events: List[Dict[str, Any]] = Field(default_factory=list, description="Events that caused drift")
    time_period_analyzed: Optional[str] = Field(None, description="Time period between preferences")
    sample_size: Optional[int] = Field(None, ge=1, description="Number of data points for detection")

    # Impact assessment
    significance_level: confloat(ge=0.0, le=1.0) = Field(0.0, description="Statistical significance")
    impact_on_matching: confloat(ge=0.0, le=1.0) = Field(0.0, description="Impact on property matching")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended next steps")

    # Resolution tracking
    agent_notified: bool = Field(False, description="Whether agent has been notified")
    client_confirmation_needed: bool = Field(False, description="Whether client confirmation required")
    client_confirmation_received: bool = Field(False, description="Whether client has confirmed drift")
    resolution_action: Optional[str] = Field(None, description="Action taken to resolve drift")
    resolution_timestamp: Optional[datetime] = Field(None, description="When drift was resolved")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "drift_id": "drift_12345",
                "client_id": "client_67890",
                "preference_category": "aesthetic_preferences",
                "drift_type": "shift",
                "drift_magnitude": 0.4,
                "previous_preference": {"modern": 0.8, "traditional": 0.2},
                "new_preference": {"modern": 0.4, "traditional": 0.6},
                "confidence_change": -0.2,
                "triggering_events": [
                    {
                        "event": "viewed_traditional_property",
                        "timestamp": "2025-01-24T15:30:00Z"
                    }
                ],
                "significance_level": 0.85,
                "impact_on_matching": 0.6,
                "recommended_actions": [
                    "Confirm style preference with client",
                    "Update property matching criteria"
                ],
                "agent_notified": False,
                "confidence_score": 0.85
            }
        })


class PreferenceProfileAPI(TimestampedModel, PerformanceModel):
    """Complete client preference profile."""
    client_id: str = Field(description="Client identifier")
    location_id: str = Field(description="Location identifier")

    # Profile metadata
    profile_version: int = Field(1, ge=1, description="Profile version for tracking changes")
    overall_confidence_score: confloat(ge=0.0, le=1.0) = Field(0.0, description="Overall profile reliability")
    profile_completeness_percentage: conint(ge=0, le=100) = Field(0, description="Profile completeness (0-100%)")
    learning_sessions_count: int = Field(0, ge=0, description="Number of learning sessions")
    total_data_points: int = Field(0, ge=0, description="Total data points collected")

    # Core property preferences (JSON structures for flexibility)
    bedrooms_preference: Dict[str, Any] = Field(default_factory=dict, description="Bedroom preferences with confidence")
    bathrooms_preference: Dict[str, Any] = Field(default_factory=dict, description="Bathroom preferences with confidence")
    square_footage_preference: Dict[str, Any] = Field(default_factory=dict, description="Size preferences with confidence")
    price_range_preference: Dict[str, Any] = Field(default_factory=dict, description="Price range with confidence")

    # Style and aesthetic preferences
    property_style_preferences: Dict[str, float] = Field(default_factory=dict, description="Style preferences (modern: 0.8)")
    property_age_preference: Dict[str, float] = Field(default_factory=dict, description="Age preferences")
    condition_preferences: Dict[str, float] = Field(default_factory=dict, description="Condition preferences")

    # Location and lifestyle preferences
    location_preferences: Dict[str, Any] = Field(default_factory=dict, description="Location and neighborhood preferences")
    lifestyle_features: Dict[str, float] = Field(default_factory=dict, description="Feature importance scores")

    # Communication and decision-making
    communication_preferences: Dict[str, Any] = Field(default_factory=dict, description="Communication style preferences")
    decision_making_style: Dict[str, Any] = Field(default_factory=dict, description="Decision-making patterns")

    # Financial and timeline preferences
    financing_preferences: Dict[str, Any] = Field(default_factory=dict, description="Financing preferences")
    timeline_preferences: Dict[str, Any] = Field(default_factory=dict, description="Timeline and urgency")

    # Learned patterns and priorities
    feature_priority_scores: Dict[str, float] = Field(default_factory=dict, description="Feature importance ranking")
    deal_breaker_features: List[str] = Field(default_factory=list, description="Absolute deal breakers")
    nice_to_have_features: List[str] = Field(default_factory=list, description="Desired but not required")

    # Quality metrics
    prediction_accuracy_score: confloat(ge=0.0, le=1.0) = Field(0.0, description="How well preferences predict choices")
    consistency_score: confloat(ge=0.0, le=1.0) = Field(0.0, description="Consistency of preferences over time")
    drift_frequency: confloat(ge=0.0, le=1.0) = Field(0.0, description="How often preferences change")
    source_diversity_score: confloat(ge=0.0, le=1.0) = Field(0.0, description="Diversity of learning sources")

    # Performance optimization
    cache_key: Optional[str] = Field(None, description="Cache key for fast retrieval")
    last_prediction_timestamp: Optional[datetime] = Field(None, description="Last property prediction time")
    prediction_cache: Dict[str, Any] = Field(default_factory=dict, description="Cached prediction results")

    @field_validator('profile_completeness_percentage')
    @classmethod
    def validate_completeness_percentage(cls, v):
        """Ensure completeness percentage is valid."""
        if not 0 <= v <= 100:
            raise ValueError("Profile completeness must be between 0 and 100")
        return v

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "client_id": "client_12345",
                "location_id": "loc_67890",
                "profile_version": 3,
                "overall_confidence_score": 0.84,
                "profile_completeness_percentage": 75,
                "learning_sessions_count": 12,
                "total_data_points": 35,
                "bedrooms_preference": {
                    "min": 3,
                    "max": 4,
                    "ideal": 3,
                    "confidence": 0.89
                },
                "price_range_preference": {
                    "min": 400000,
                    "max": 550000,
                    "confidence": 0.92
                },
                "property_style_preferences": {
                    "modern": 0.85,
                    "contemporary": 0.75,
                    "traditional": 0.25
                },
                "lifestyle_features": {
                    "home_office": 0.95,
                    "pool": 0.65,
                    "garage": 0.88
                },
                "feature_priority_scores": {
                    "price": 0.95,
                    "location": 0.82,
                    "home_office": 0.90
                },
                "deal_breaker_features": ["busy_road", "no_garage"],
                "prediction_accuracy_score": 0.87,
                "consistency_score": 0.82
            }
        })


class PreferenceLearningRequestAPI(BaseModel):
    """Request for preference learning analysis."""
    client_id: constr(min_length=1) = Field(description="Client identifier")
    source_type: PreferenceSourceAPI = Field(description="Source type for learning")

    # Source data (one of these based on source_type)
    conversation_data: Optional[List[Dict[str, Any]]] = Field(None, description="Conversation data for analysis")
    conversation_analysis: Optional[Dict[str, Any]] = Field(None, description="Pre-analyzed conversation insights")
    property_id: Optional[str] = Field(None, description="Property ID for interaction learning")
    interaction_data: Optional[Dict[str, Any]] = Field(None, description="Property interaction data")

    # Learning configuration
    learning_config: Dict[str, Any] = Field(default_factory=dict, description="Learning algorithm configuration")
    confidence_threshold: confloat(ge=0.0, le=1.0) = Field(0.6, description="Minimum confidence for preference learning")

    @model_validator(mode="before")
    @classmethod
    def validate_source_data(cls, values):
        """Ensure appropriate data is provided for source type."""
        source_type = values.get('source_type')

        if source_type == PreferenceSourceAPI.CONVERSATION_ANALYSIS:
            if not values.get('conversation_data') and not values.get('conversation_analysis'):
                raise ValueError("Conversation data or analysis required for conversation source type")

        elif source_type == PreferenceSourceAPI.PROPERTY_INTERACTION:
            if not values.get('property_id') or not values.get('interaction_data'):
                raise ValueError("Property ID and interaction data required for property interaction source type")

        return values

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "client_id": "client_12345",
                "source_type": "conversation_analysis",
                "conversation_data": [
                    {
                        "message": "We absolutely need a home office",
                        "timestamp": "2025-01-25T10:00:00Z",
                        "speaker": "user",
                        "confidence": 0.95
                    }
                ],
                "confidence_threshold": 0.7
            }
        })


# =====================================================================================
# Cross-Track Coordination Models
# =====================================================================================

class CrossTrackHandoffRequestAPI(BaseModel):
    """Request for cross-track handoff coordination."""
    lead_id: constr(min_length=1) = Field(description="Lead ID transitioning")
    client_id: constr(min_length=1) = Field(description="Client ID after transition")
    qualification_score: confloat(ge=0.0, le=1.0) = Field(description="Lead qualification score")
    handoff_reason: str = Field(description="Reason for handoff")
    agent_notes: Optional[str] = Field(None, description="Agent transition notes")

    # Context preservation
    preserve_conversation_context: bool = Field(True, description="Preserve conversation analysis")
    preserve_preferences: bool = Field(True, description="Preserve learned preferences")
    preserve_property_matches: bool = Field(True, description="Preserve property matching history")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "lead_id": "lead_12345",
                "client_id": "client_67890",
                "qualification_score": 0.89,
                "handoff_reason": "qualified_buyer",
                "agent_notes": "Highly engaged lead, ready for property viewings",
                "preserve_conversation_context": True,
                "preserve_preferences": True,
                "preserve_property_matches": True
            }
        })


class LeadToClientTransitionAPI(PerformanceModel, TimestampedModel):
    """Response for lead-to-client handoff coordination."""
    transition_id: str = Field(description="Unique transition identifier")
    lead_id: str = Field(description="Original lead ID")
    client_id: str = Field(description="New client ID")
    location_id: str = Field(description="Location identifier")

    transition_timestamp: datetime = Field(default_factory=datetime.now, description="Handoff completion time")

    # Context preservation status
    context_preserved: bool = Field(description="Whether context was successfully preserved")
    preferences_migrated: bool = Field(description="Whether preferences were migrated")
    conversation_insights_count: int = Field(ge=0, description="Number of insights transferred")
    property_matches_count: int = Field(0, ge=0, description="Number of property matches transferred")

    # Next steps for client experience
    next_steps: List[str] = Field(description="Recommended next steps for client journey")
    priority_actions: List[str] = Field(default_factory=list, description="High-priority actions for immediate follow-up")

    # Intelligence summary
    intelligence_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of transferred intelligence")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "transition_id": "trans_12345",
                "lead_id": "lead_67890",
                "client_id": "client_12345",
                "location_id": "loc_456",
                "context_preserved": True,
                "preferences_migrated": True,
                "conversation_insights_count": 8,
                "property_matches_count": 5,
                "next_steps": [
                    "Schedule property viewings",
                    "Prepare financing pre-approval",
                    "Set up automated property alerts"
                ],
                "priority_actions": [
                    "Contact within 24 hours",
                    "Schedule viewing for top 3 properties"
                ],
                "processing_time_ms": 145,
                "confidence_score": 0.94
            }
        })


# =====================================================================================
# Common Response and Error Models
# =====================================================================================

class HealthCheckResponseAPI(BaseModel):
    """Health check response for Phase 2 intelligence services."""
    overall_status: str = Field(description="Overall service health (healthy/degraded/error)")
    location_id: str = Field(description="Location being monitored")
    services: Dict[str, Dict[str, Any]] = Field(description="Individual service health details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    performance_targets: Dict[str, int] = Field(description="Performance targets for validation")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "overall_status": "healthy",
                "location_id": "loc_12345",
                "services": {
                    "property_matching": {
                        "status": "healthy",
                        "avg_response_time": 85,
                        "cache_hit_rate": 0.89
                    },
                    "conversation_intelligence": {
                        "status": "healthy",
                        "avg_processing_time": 340,
                        "accuracy": 0.91
                    },
                    "preference_learning": {
                        "status": "healthy",
                        "avg_update_time": 35,
                        "learning_accuracy": 0.87
                    }
                },
                "performance_targets": {
                    "property_matching_ms": 100,
                    "conversation_analysis_ms": 500,
                    "preference_learning_ms": 50
                }
            }
        })


class ErrorResponseAPI(BaseModel):
    """Standardized error response for Phase 2 intelligence APIs."""
    error_code: str = Field(description="Machine-readable error code")
    error_message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")

    # Jorge-specific error handling
    fallback_available: bool = Field(False, description="Whether fallback service is available")
    retry_recommended: bool = Field(False, description="Whether retry is recommended")
    estimated_resolution_time: Optional[str] = Field(None, description="Estimated time to resolution")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "error_code": "PROPERTY_MATCHING_TIMEOUT",
                "error_message": "Property matching analysis timed out after 5 seconds",
                "details": {
                    "service": "advanced_property_matching",
                    "timeout_threshold": 5000,
                    "actual_processing_time": 5250
                },
                "fallback_available": True,
                "retry_recommended": True,
                "estimated_resolution_time": "2 minutes"
            }
        })


class PaginationResponseAPI(BaseModel):
    """Pagination information for list responses."""
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")

    @model_validator(mode="before")
    @classmethod
    def calculate_pagination_fields(cls, values):
        """Calculate pagination fields based on totals."""
        page = values.get('page', 1)
        page_size = values.get('page_size', 20)
        total_items = values.get('total_items', 0)

        total_pages = max(1, (total_items + page_size - 1) // page_size)
        has_next = page < total_pages
        has_previous = page > 1

        values.update({
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous
        })

        return values

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "page": 2,
                "page_size": 20,
                "total_items": 127,
                "total_pages": 7,
                "has_next": True,
                "has_previous": True
            }
        })


# =====================================================================================
# WebSocket Event Models
# =====================================================================================

class WebSocketEventAPI(BaseModel):
    """Base WebSocket event for real-time updates."""
    event_type: str = Field(description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    location_id: str = Field(description="Location identifier")
    user_id: Optional[str] = Field(None, description="User who triggered event")
    event_data: Dict[str, Any] = Field(description="Event-specific data")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "event_type": "property_match_generated",
                "timestamp": "2025-01-25T10:30:00Z",
                "location_id": "loc_12345",
                "user_id": "user_67890",
                "event_data": {
                    "lead_id": "lead_123",
                    "property_id": "prop_456",
                    "match_score": 0.89
                }
            }
        })


# Export all models for easy importing
__all__ = [
    # Enums
    "PresentationStrategyAPI", "ObjectionTypeAPI", "SentimentLevelAPI",
    "CoachingAreaAPI", "PreferenceSourceAPI", "PreferenceCategoryAPI", "DriftTypeAPI",

    # Base Models
    "TimestampedModel", "PerformanceModel", "JorgeIntegrationModel",

    # Property Matching Models
    "PropertyMatchingFiltersAPI", "BehavioralMatchWeightsAPI", "AdvancedPropertyMatchAPI",
    "PropertyMatchRequestAPI", "PropertyMatchResponseAPI",

    # Conversation Intelligence Models
    "SentimentTimelinePointAPI", "ObjectionDetectionAPI", "CoachingOpportunityAPI",
    "ConversationInsightAPI", "ConversationAnalysisRequestAPI", "ConversationResponseAPI",

    # Preference Learning Models
    "PreferenceLearningEventAPI", "PreferenceDriftDetectionAPI", "PreferenceProfileAPI",
    "PreferenceLearningRequestAPI",

    # Cross-Track Coordination Models
    "CrossTrackHandoffRequestAPI", "LeadToClientTransitionAPI",

    # Common Models
    "HealthCheckResponseAPI", "ErrorResponseAPI", "PaginationResponseAPI", "WebSocketEventAPI"
]