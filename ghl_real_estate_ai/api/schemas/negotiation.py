"""
AI Negotiation Partner Data Models and Schemas

Comprehensive data models for seller psychology analysis, market leverage calculation,
negotiation strategy generation, and win probability prediction.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Enums for type safety
class SellerMotivationType(str, Enum):
    EMOTIONAL = "emotional"  # Emotional attachment, lifestyle change
    FINANCIAL = "financial"  # Financial pressure, investment optimization
    STRATEGIC = "strategic"  # Market timing, relocation
    DISTRESSED = "distressed"  # Foreclosure, divorce, death


class UrgencyLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MarketCondition(str, Enum):
    BUYERS_MARKET = "buyers_market"
    BALANCED = "balanced"
    SELLERS_MARKET = "sellers_market"


class NegotiationTactic(str, Enum):
    PRICE_FOCUSED = "price_focused"
    TIMELINE_FOCUSED = "timeline_focused"
    TERMS_FOCUSED = "terms_focused"
    RELATIONSHIP_BUILDING = "relationship_building"
    COMPETITIVE_PRESSURE = "competitive_pressure"


class ListingBehaviorPattern(str, Enum):
    OVERPRICED_STUBBORN = "overpriced_stubborn"
    PRICE_DROPPER = "price_dropper"
    REALISTIC_PRICING = "realistic_pricing"
    TESTING_MARKET = "testing_market"
    MOTIVATED_SELLER = "motivated_seller"


# Core Data Models
class ListingHistory(BaseModel):
    """Historical data points for a property listing"""

    model_config = ConfigDict(use_enum_values=True)

    original_list_price: Decimal
    current_price: Decimal
    price_drops: List[Dict[str, Any]]  # [{date, old_price, new_price, percentage}]
    days_on_market: int
    listing_views: Optional[int] = None
    showing_requests: Optional[int] = None
    offers_received: Optional[int] = None
    previous_listing_attempts: Optional[int] = None


class SellerPsychologyProfile(BaseModel):
    """Comprehensive psychological profile of the seller"""

    model_config = ConfigDict(use_enum_values=True)

    motivation_type: SellerMotivationType
    urgency_level: UrgencyLevel
    urgency_score: float = Field(..., ge=0, le=100)

    # Behavioral indicators
    behavioral_pattern: ListingBehaviorPattern
    emotional_attachment_score: float = Field(..., ge=0, le=100)
    financial_pressure_score: float = Field(..., ge=0, le=100)
    flexibility_score: float = Field(..., ge=0, le=100)

    # Communication patterns
    response_time_hours: Optional[float] = None
    communication_style: Optional[str] = None  # professional, emotional, urgent

    # Key insights
    primary_concerns: List[str] = []
    negotiation_hot_buttons: List[str] = []
    relationship_importance: float = Field(..., ge=0, le=100)


class MarketLeverage(BaseModel):
    """Buyer's negotiating position and market leverage"""

    model_config = ConfigDict(use_enum_values=True)

    overall_leverage_score: float = Field(..., ge=0, le=100)
    market_condition: MarketCondition

    # Market dynamics
    inventory_levels: Dict[str, float]  # {price_range: months_inventory}
    competitive_pressure: float = Field(..., ge=0, le=100)
    seasonal_advantage: float = Field(..., ge=-50, le=50)

    # Property-specific factors
    property_uniqueness_score: float = Field(..., ge=0, le=100)
    comparable_sales_strength: float = Field(..., ge=0, le=100)
    price_positioning: str  # overpriced, fairly_priced, underpriced

    # Buyer advantages
    financing_strength: float = Field(..., ge=0, le=100)
    cash_offer_boost: float = Field(..., ge=0, le=25)
    quick_close_advantage: float = Field(..., ge=0, le=15)


class NegotiationStrategy(BaseModel):
    """Strategic recommendations for negotiation approach"""

    model_config = ConfigDict(use_enum_values=True)

    primary_tactic: NegotiationTactic
    confidence_score: float = Field(..., ge=0, le=100)

    # Offer recommendations
    recommended_offer_price: Decimal
    offer_range: Dict[str, Decimal]  # {min, target, max}

    # Strategic elements
    key_terms_to_emphasize: List[str] = []
    concessions_to_request: List[str] = []
    relationship_building_approach: str

    # Tactical guidance
    opening_strategy: str
    response_to_counter: str
    negotiation_timeline: str

    # Talking points
    primary_talking_points: List[str] = []
    objection_responses: Dict[str, str] = {}

    # Vanguard 3: Agentic Negotiation (Phase 11)
    optimal_bid_sequence: List[float] = []
    strategy_blend: Optional[str] = None


class WinProbabilityAnalysis(BaseModel):
    """ML-powered prediction of offer acceptance probability"""

    win_probability: float = Field(..., ge=0, le=100)
    confidence_interval: Dict[str, float]  # {lower, upper}

    # Contributing factors
    factor_weights: Dict[str, float] = {}
    risk_factors: List[str] = []
    success_drivers: List[str] = []

    # Scenario analysis
    scenarios: Dict[str, float] = {}  # {offer_type: win_probability}
    optimal_offer_analysis: Dict[str, Any] = {}


class NegotiationIntelligence(BaseModel):
    """Complete negotiation intelligence package"""

    property_id: str
    lead_id: str
    tenant_id: str = Field(..., description="Tenant ID owning or managing this negotiation")
    analysis_timestamp: datetime

    # Core analyses
    seller_psychology: SellerPsychologyProfile
    market_leverage: MarketLeverage
    negotiation_strategy: NegotiationStrategy
    win_probability: WinProbabilityAnalysis

    # Executive summary
    executive_summary: str
    key_insights: List[str] = []
    action_items: List[str] = []

    # Metadata
    analysis_version: str = "1.0"
    processing_time_ms: Optional[int] = None


# API Request/Response Models
class NegotiationAnalysisRequest(BaseModel):
    """Request for negotiation intelligence analysis"""

    property_id: str
    lead_id: str
    tenant_id: str = Field(..., description="Tenant ID for the negotiation context")

    # Optional context
    buyer_preferences: Optional[Dict[str, Any]] = None
    existing_offers: Optional[List[Dict[str, Any]]] = None
    timeline_constraints: Optional[Dict[str, Any]] = None
    financing_details: Optional[Dict[str, Any]] = None


class RealTimeCoachingRequest(BaseModel):
    """Request for real-time negotiation coaching"""

    negotiation_id: str
    conversation_context: str
    current_situation: str
    buyer_feedback: Optional[str] = None
    seller_response: Optional[str] = None


class RealTimeCoachingResponse(BaseModel):
    """Real-time coaching recommendations"""

    immediate_guidance: str
    tactical_adjustments: List[str] = []
    next_steps: List[str] = []
    conversation_suggestions: Dict[str, str] = {}
    risk_alerts: List[str] = []


class StrategyUpdateRequest(BaseModel):
    """Request to update strategy based on new information"""

    negotiation_id: str
    new_information: Dict[str, Any]
    strategy_adjustments: Optional[Dict[str, Any]] = None


# Historical Analysis Models
class NegotiationOutcome(BaseModel):
    """Historical negotiation outcome for learning"""

    negotiation_id: str
    property_id: str

    # Outcome details
    final_sale_price: Decimal
    negotiation_duration_days: int
    offer_acceptance_ratio: float

    # Strategy effectiveness
    strategy_used: NegotiationTactic
    tactics_effectiveness: Dict[str, float] = {}
    actual_vs_predicted: Dict[str, float] = {}

    # Learning insights
    what_worked: List[str] = []
    what_failed: List[str] = []
    lessons_learned: str


class MarketIntelligenceUpdate(BaseModel):
    """Real-time market intelligence update"""

    timestamp: datetime
    market_condition_change: Optional[MarketCondition] = None
    inventory_update: Optional[Dict[str, float]] = None
    competitive_activity: Optional[List[Dict[str, Any]]] = None
    price_trend_alerts: Optional[List[str]] = None


# Integration Models
class GHLNegotiationEvent(BaseModel):
    """GHL webhook event for negotiation milestones"""

    event_type: str  # offer_submitted, offer_countered, offer_accepted
    negotiation_id: str
    contact_id: str
    property_id: str
    event_data: Dict[str, Any]
    timestamp: datetime


class NegotiationMetrics(BaseModel):
    """Performance metrics for the negotiation system"""

    total_negotiations: int
    average_win_rate: float
    average_price_improvement: float
    strategy_effectiveness: Dict[str, float] = {}
    prediction_accuracy: float
    user_satisfaction_score: float
