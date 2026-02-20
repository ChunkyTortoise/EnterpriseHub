from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile


class ConversationTurn(TypedDict, total=False):
    """TypedDict for a single conversation turn."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str]


class CMAReport(TypedDict, total=False):
    """TypedDict for Comparative Market Analysis report."""
    estimated_value: float
    value_range_low: float
    value_range_high: float
    confidence_score: float
    comparable_count: int
    market_days_estimate: int
    report_generated_at: str


class MarketData(TypedDict, total=False):
    """TypedDict for market data."""
    avg_days_on_market: float
    median_sale_price: float
    price_per_sqft: float
    inventory_level: str  # "low", "normal", "high"
    market_velocity: str  # "fast", "normal", "slow"
    last_updated: str


class ComparableProperty(TypedDict, total=False):
    """TypedDict for comparable property summary."""
    property_id: str
    address: str
    sale_price: float
    sale_date: str
    bedrooms: int
    bathrooms: float
    sqft: int
    distance_miles: float


class SellerPersona(TypedDict, total=False):
    """TypedDict for seller persona."""
    motivation_type: str  # "relocation", "upsizing", "downsizing", "financial", etc.
    urgency_level: str  # "high", "medium", "low"
    price_sensitivity: str  # "high", "medium", "low"
    communication_preference: str  # "phone", "text", "email"
    decision_style: str  # "analytical", "emotional", "collaborative"


class JorgeSellerState(TypedDict):
    """
    State for Jorge's Motivated Seller Bot.
    Focuses on consultative qualification and relationship-building.
    """

    lead_id: str
    lead_name: str
    property_address: Optional[str]

    # Context
    conversation_history: List[ConversationTurn]
    intent_profile: Optional[LeadIntentProfile]

    # Bot Logic
    current_tone: str  # "consultative", "educational", "understanding", "enthusiastic", "supportive"
    stall_detected: bool
    detected_stall_type: Optional[str]  # "thinking", "get_back", "zestimate", "agent"

    # Decisions
    next_action: str
    response_content: str

    # Metrics
    psychological_commitment: float
    is_qualified: bool

    # Journey Tracking
    current_journey_stage: (
        str  # "qualification", "valuation_defense", "listing_prep", "active_listing", "under_contract", "closed"
    )
    follow_up_count: int
    last_action_timestamp: Optional[datetime]

    # A/B testing
    tone_variant: Optional[str]  # A/B experiment variant: "formal", "casual", "empathetic"

    # Adaptive extension fields
    adaptive_mode: str
    adaptive_question_used: Optional[str]
    adaptation_applied: bool
    memory_updated: bool

    # CMA & Market Intelligence fields
    cma_report: Optional[CMAReport]
    estimated_value: Optional[float]
    listing_price_recommendation: Optional[float]
    zestimate: Optional[float]
    property_condition: Optional[str]  # "move_in_ready" | "needs_work" | "major_repairs"
    repair_estimates: Optional[Dict[str, float]]  # Keep as Dict[str, float] - dynamic repair types
    staging_recommendations: Optional[List[str]]
    market_data: Optional[MarketData]
    market_trend: Optional[str]  # "sellers_market" | "buyers_market" | "balanced"
    comparable_properties: Optional[List[ComparableProperty]]
    seller_intent_profile: Optional[Any]
    seller_persona: Optional[SellerPersona]

    # 10-point Qualification Flow fields
    seller_motivation: Optional[str]
    timeline_urgency: Optional[str]
    price_expectation: Optional[str]
    seller_liens: Optional[str]
    seller_repairs: Optional[str]
    seller_listing_history: Optional[str]
    seller_decision_maker: Optional[str]
    seller_contact_method: Optional[str]

    # QBQ (Question Behind the Question) loop fields
    deep_motivation: Optional[str]  # e.g., "Retiring to Florida", "Avoiding Foreclosure"
    qbq_attempted: bool  # Prevent repeated QBQ on same objection
