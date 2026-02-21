from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile


class ConversationTurn(TypedDict, total=False):
    """TypedDict for a single conversation turn."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str]


class PropertyPreference(TypedDict, total=False):
    """TypedDict for property preferences."""

    property_type: str  # "single_family", "condo", "townhouse", etc.
    bedrooms_min: int
    bedrooms_max: int
    bathrooms_min: float
    sqft_min: int
    must_have_features: List[str]
    nice_to_have_features: List[str]
    preferred_locations: List[str]


class AffordabilityAnalysis(TypedDict, total=False):
    """TypedDict for affordability analysis."""

    monthly_payment: float
    down_payment: float
    total_cost: float
    estimated_closing_costs: float
    recommended_max_price: float
    affordability_ratio: float  # monthly_payment / income


class MortgageDetails(TypedDict, total=False):
    """TypedDict for mortgage details."""

    rate: float
    term: int  # years
    type: str  # "fixed", "arm", "fha", "va"
    pre_approval_amount: float
    lender_name: Optional[str]


class ObjectionEntry(TypedDict, total=False):
    """TypedDict for objection history entry."""

    objection_type: str
    timestamp: str
    resolved: bool
    resolution_notes: Optional[str]


class MatchedProperty(TypedDict, total=False):
    """TypedDict for matched property summary."""

    property_id: str
    address: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    match_score: float
    match_reasons: List[str]
    image_url: Optional[str]


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
    conversation_history: List[ConversationTurn]
    intent_profile: Optional[BuyerIntentProfile]
    user_message: Optional[str]
    intelligence_context: Optional[Any]
    intelligence_performance_ms: float

    # Buyer-Specific Context
    budget_range: Optional[Dict[str, int]]  # {"min": 300000, "max": 450000}
    financing_status: str  # "pre_approved", "needs_approval", "cash", "unknown"
    urgency_level: str  # "immediate", "3_months", "6_months", "browsing"
    property_preferences: Optional[PropertyPreference]

    # Contact info (optional, set at runtime)
    buyer_phone: Optional[str]
    buyer_email: Optional[str]
    metadata: Optional[Dict[str, Any]]  # Keep as Dict[str, Any] - truly dynamic metadata

    # Bot Logic (match seller patterns)
    current_qualification_step: str  # "budget", "timeline", "preferences", "decision_makers"
    objection_detected: bool
    detected_objection_type: Optional[str]  # "budget_shock", "analysis_paralysis", "spouse_decision", "timing"

    # Decisions
    next_action: str
    response_content: str
    matched_properties: List[MatchedProperty]

    # Metrics
    financial_readiness_score: float  # 0-100
    buying_motivation_score: float  # 0-100
    buyer_temperature: Optional[str]
    is_qualified: bool

    # A/B testing
    tone_variant: Optional[str]  # A/B experiment variant: "formal", "casual", "empathetic"

    # Journey Tracking
    current_journey_stage: str  # "discovery", "qualification", "property_search", "offer_prep", "under_contract"
    properties_viewed_count: int
    last_action_timestamp: Optional[datetime]

    # Affordability & Objection Handling fields
    affordability_analysis: Optional[AffordabilityAnalysis]
    mortgage_details: Optional[MortgageDetails]
    max_monthly_payment: Optional[float]
    objection_history: Optional[List[ObjectionEntry]]
