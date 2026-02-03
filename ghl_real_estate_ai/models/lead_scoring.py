from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, conint, confloat
from datetime import datetime, timezone

class MotivationSignals(BaseModel):
    """Pillar 1: Motivation Signals (Linguistic Markers)"""
    score: conint(ge=0, le=100) = Field(..., description="0-100 score for motivation")
    detected_markers: List[str] = Field(default_factory=list, description="List of detected linguistic markers (e.g. 'relocating', 'divorce')")
    category: str = Field(..., description="'High Intent', 'Mixed Intent', or 'Low Intent'")

class TimelineCommitment(BaseModel):
    """Pillar 2: Timeline Commitment"""
    score: conint(ge=0, le=100) = Field(..., description="0-100 score for timeline")
    target_date: Optional[datetime] = Field(None, description="Specific target date if mentioned")
    category: str = Field(..., description="'High Commitment', 'Flexible', or 'Vague'")

class ConditionRealism(BaseModel):
    """Pillar 3: Condition Realism"""
    score: conint(ge=0, le=100) = Field(..., description="0-100 score for condition realism")
    acknowledged_defects: List[str] = Field(default_factory=list, description="List of acknowledged defects")
    category: str = Field(..., description="'Realistic', 'Negotiable', or 'Unrealistic'")

class PriceResponsiveness(BaseModel):
    """Pillar 4: Price Responsiveness"""
    score: conint(ge=0, le=100) = Field(..., description="0-100 score for price responsiveness")
    zestimate_mentioned: bool = Field(False, description="Whether Zestimate was mentioned")
    category: str = Field(..., description="'Price-Aware', 'Price-Flexible', or 'Unrealistic'")

class FinancialReadinessScore(BaseModel):
    """
    FRS Formula: (Motivation × 0.35) + (Timeline × 0.30) + (Condition × 0.20) + (Price × 0.15)
    """
    total_score: float = Field(..., description="0-100 calculated FRS")
    motivation: MotivationSignals
    timeline: TimelineCommitment
    condition: ConditionRealism
    price: PriceResponsiveness
    classification: str = Field(..., description="'Hot', 'Warm', 'Lukewarm', or 'Cold'")

class PsychologicalCommitmentScore(BaseModel):
    """
    PCS: Emotional commitment tracking
    """
    total_score: float = Field(..., description="0-100 calculated PCS")
    response_velocity_score: int = Field(..., description="Score based on response time")
    message_length_score: int = Field(..., description="Score based on word count")
    question_depth_score: int = Field(..., description="Score based on question specificity")
    objection_handling_score: int = Field(..., description="Score based on overcoming objections")
    call_acceptance_score: int = Field(..., description="Score based on agreeing to calls/tours")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeadIntentProfile(BaseModel):
    """Complete Lead Profile for Jorge's Dashboard"""
    lead_id: str
    frs: FinancialReadinessScore
    pcs: PsychologicalCommitmentScore
    lead_type: str = Field("unknown", description="'buyer', 'seller', or 'unknown'")
    market_context: Optional[str] = None
    next_best_action: str = Field(..., description="Recommended next step for Jorge or Bot")
    stall_breaker_suggested: Optional[str] = None


class BuyerIntentProfile(BaseModel):
    """Buyer intent analysis results. Mirrors LeadIntentProfile structure for buyers."""

    # Financial Readiness Score (FRS) - 0-100
    financial_readiness: float = Field(..., description="Overall financial readiness score")
    budget_clarity: float = Field(..., description="Clarity of budget understanding")
    financing_status_score: float = Field(..., description="Pre-approval/financing status score")

    # Motivation Score (MS) - 0-100
    urgency_score: float = Field(..., description="Urgency to purchase")
    timeline_pressure: float = Field(..., description="Timeline commitment level")
    consequence_awareness: float = Field(..., description="Understanding of market consequences")

    # Property Fit Score (PFS) - 0-100
    preference_clarity: float = Field(..., description="Clarity of property preferences")
    market_realism: float = Field(..., description="Realistic expectations vs market")
    decision_authority: float = Field(..., description="Authority to make decisions")

    # Overall Classification
    buyer_temperature: str = Field(..., description="hot/warm/lukewarm/cold/ice_cold")
    confidence_level: float = Field(..., description="Confidence in the analysis")

    # Analysis Context
    conversation_turns: int = Field(..., description="Number of conversation turns analyzed")
    key_insights: Dict[str, Any] = Field(default_factory=dict, description="Key buyer insights")
    next_qualification_step: str = Field(..., description="Next step in qualification process")
