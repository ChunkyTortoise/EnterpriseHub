from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

class BuyerBotState(TypedDict):
    """
    State for Jorge's Buyer Qualification Bot.
    Follows proven JorgeSellerState pattern for consultative buyer qualification.
    Designed to identify 'Serious Buyers' and filter 'Window Shoppers'.
    """

    # Identity (match JorgeSellerState pattern)
    buyer_id: str
    buyer_name: str
    target_areas: Optional[List[str]]

    # Context
    conversation_history: List[Dict[str, str]]
    intent_profile: Optional[BuyerIntentProfile]
    user_message: Optional[str]
    intelligence_context: Optional[Any]
    intelligence_performance_ms: float

    # Buyer-Specific Context
    budget_range: Optional[Dict[str, int]]  # {"min": 300000, "max": 450000}
    financing_status: str  # "pre_approved", "needs_approval", "cash", "unknown"
    urgency_level: str     # "immediate", "3_months", "6_months", "browsing"
    property_preferences: Optional[Dict[str, Any]]

    # Contact info (optional, set at runtime)
    buyer_phone: Optional[str]
    buyer_email: Optional[str]
    metadata: Optional[Dict[str, Any]]

    # Bot Logic (match seller patterns)
    current_qualification_step: str  # "budget", "timeline", "preferences", "decision_makers"
    objection_detected: bool
    detected_objection_type: Optional[str]  # "budget_shock", "analysis_paralysis", "spouse_decision", "timing"

    # Decisions
    next_action: str
    response_content: str
    matched_properties: List[Dict[str, Any]]

    # Metrics
    financial_readiness_score: float  # 0-100
    buying_motivation_score: float    # 0-100
    buyer_temperature: Optional[str]
    is_qualified: bool

    # A/B testing
    tone_variant: Optional[str]  # A/B experiment variant: "formal", "casual", "empathetic"

    # Journey Tracking
    current_journey_stage: str  # "discovery", "qualification", "property_search", "offer_prep", "under_contract"
    properties_viewed_count: int
    last_action_timestamp: Optional[datetime]
