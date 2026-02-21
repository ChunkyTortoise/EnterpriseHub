from datetime import datetime
from typing import Any, List, Optional, TypedDict

from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile


class ConversationTurn(TypedDict, total=False):
    """TypedDict for a single conversation turn."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str]


class CrossBotPreference(TypedDict, total=False):
    """TypedDict for cross-bot shared preferences."""

    preferred_contact_method: str
    best_contact_time: str
    decision_maker_present: bool
    spouse_name: Optional[str]
    special_considerations: List[str]


class SellerData(TypedDict, total=False):
    """TypedDict for seller workflow data."""

    motivation: str
    timeline: str
    price_expectation: float
    property_condition: str
    repairs_needed: List[str]
    previous_listing: bool


class ClosingMilestone(TypedDict, total=False):
    """TypedDict for closing milestone."""

    milestone_type: str  # "inspection", "appraisal", "financing", "title", "closing"
    scheduled_date: Optional[str]
    completed: bool
    completed_date: Optional[str]
    notes: Optional[str]


class LeadFollowUpState(TypedDict):
    """
    State definition for the LangGraph 3-7-30 Day Follow-Up Workflow.
    Tracks the lead's journey through the re-engagement funnel.
    """

    lead_id: str
    lead_name: str
    contact_phone: str
    contact_email: Optional[str]
    property_address: Optional[str]

    # Conversation Context
    conversation_history: List[ConversationTurn]
    intent_profile: Optional[LeadIntentProfile]

    # Workflow Status
    current_step: str  # "initial", "day_3_sms", "day_7_call", "day_14_email", "day_30_nudge", "showing_scheduled", "offer_stage", "closing_nurture", "handed_off", "nurture"
    engagement_status: (
        str  # "new", "ghosted", "re_engaged", "qualified", "showing_booked", "offer_sent", "under_contract", "closed"
    )
    response_content: Optional[str]

    # Logic Tracking
    last_interaction_time: Optional[datetime]
    stall_breaker_attempted: bool
    cma_generated: bool

    # Full Lifecycle Fields
    showing_date: Optional[datetime]
    showing_feedback: Optional[str]
    offer_amount: Optional[float]
    closing_date: Optional[datetime]

    # Phase 3.3 Intelligence Enhancement Fields
    intelligence_context: Optional[Any]  # BotIntelligenceContext
    intelligence_performance_ms: Optional[float]

    # A/B testing
    tone_variant: Optional[str]  # A/B experiment variant: "formal", "casual", "empathetic"

    # Enhanced nurture fields for intelligence-driven optimization
    preferred_engagement_timing: Optional[List[int]]  # Hours of day when lead is most responsive
    churn_risk_score: Optional[float]  # 0-1 risk of lead disengagement
    cross_bot_preferences: Optional[CrossBotPreference]  # Shared preferences from Jorge bots
    sequence_optimization_applied: Optional[bool]  # Whether timing was optimized based on intelligence


class SellerWorkflowState(TypedDict):
    """
    State definition for the Jorge Seller Workflow.
    Tracks the seller's journey from qualification to closing.
    """

    lead_id: str
    lead_name: str
    contact_phone: str
    contact_email: Optional[str]
    property_address: Optional[str]

    # Conversation Context
    conversation_history: List[ConversationTurn]
    seller_data: SellerData
    temperature: str  # "hot", "warm", "cold"

    # Workflow Status
    current_step: str  # "qualification", "pre_listing", "active_listing", "under_contract", "closing_nurture", "closed"
    engagement_status: str  # "new", "qualifying", "qualified", "listing_prep", "active", "under_contract", "closed"

    # Logic Tracking
    questions_answered: int
    last_interaction_time: Optional[datetime]
    valuation_provided: bool

    # Full Lifecycle Fields
    listing_date: Optional[datetime]
    contract_date: Optional[datetime]
    closing_date: Optional[datetime]
    final_sale_price: Optional[float]
    net_proceeds: Optional[float]
    closing_milestones: List[ClosingMilestone]  # Inspection, Appraisal, etc.
