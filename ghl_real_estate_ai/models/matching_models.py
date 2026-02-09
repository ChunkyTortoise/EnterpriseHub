"""
Data models for enhanced property matching system.
Defines all data structures for the 15-factor contextual matching algorithm.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class LeadSegment(Enum):
    """Lead segments for behavioral weighting"""

    FAMILY_WITH_KIDS = "family_with_kids"
    YOUNG_PROFESSIONAL = "young_professional"
    INVESTOR = "investor"
    RETIREE = "retiree"
    FIRST_TIME_BUYER = "first_time_buyer"
    LUXURY_BUYER = "luxury_buyer"
    DOWNSIZER = "downsizer"


class MatchFactorType(Enum):
    """Types of matching factors"""

    TRADITIONAL = "traditional"  # budget, location, bedrooms, type
    LIFESTYLE = "lifestyle"  # schools, commute, walkability, safety
    CONTEXTUAL = "contextual"  # HOA, lot size, age, parking
    MARKET_TIMING = "market_timing"  # days on market, price trends


@dataclass
class FactorScore:
    """Individual factor score with reasoning"""

    factor_name: str
    raw_score: float  # 0.0 to 1.0
    weighted_score: float  # raw_score * weight
    weight: float
    confidence: float
    reasoning: str
    data_quality: str  # "high", "medium", "low", "missing"


@dataclass
class TraditionalScores:
    """Traditional real estate matching factors"""

    budget: FactorScore
    location: FactorScore
    bedrooms: FactorScore
    bathrooms: FactorScore
    property_type: FactorScore
    sqft: FactorScore


@dataclass
class SchoolScore:
    """School quality scoring"""

    elementary_rating: Optional[float]
    middle_rating: Optional[float]
    high_rating: Optional[float]
    average_rating: float
    distance_penalty: float  # 0.0 to 1.0 (closer is better)
    overall_score: float
    top_school_name: Optional[str]
    reasoning: str


@dataclass
class CommuteScore:
    """Commute analysis"""

    to_downtown_minutes: Optional[int]
    to_workplace_minutes: Optional[int]
    public_transit_access: float  # 0.0 to 1.0
    highway_access: float  # 0.0 to 1.0
    overall_score: float
    reasoning: str


@dataclass
class WalkabilityScore:
    """Walkability assessment"""

    walk_score: Optional[int]  # 0-100 Walk Score API
    nearby_amenities_count: int
    grocery_distance_miles: Optional[float]
    restaurant_density: float
    park_access: float
    overall_score: float
    reasoning: str


@dataclass
class SafetyScore:
    """Safety and crime assessment"""

    crime_rate_per_1000: Optional[float]
    neighborhood_safety_rating: Optional[float]  # 1-10 scale
    police_response_time: Optional[int]  # minutes
    overall_score: float
    reasoning: str


@dataclass
class LifestyleScores:
    """Lifestyle compatibility factors"""

    schools: SchoolScore
    commute: CommuteScore
    walkability: WalkabilityScore
    safety: SafetyScore
    amenities_proximity: float
    overall_score: float


@dataclass
class ContextualScores:
    """Property contextual factors"""

    hoa_fee_score: FactorScore
    lot_size_score: FactorScore
    home_age_score: FactorScore
    parking_score: FactorScore
    property_condition_score: FactorScore
    overall_score: float


@dataclass
class MarketTimingScore:
    """Market timing and opportunity scoring"""

    days_on_market_score: float  # longer DOM = more negotiable
    price_trend_score: float  # recent reductions = opportunity
    inventory_scarcity_score: float  # low inventory = act fast
    competition_level: str  # "low", "medium", "high"
    optimal_timing_score: float  # overall timing opportunity
    urgency_indicator: str  # "act_fast", "good_time", "can_wait"
    reasoning: str


@dataclass
class BehavioralProfile:
    """Lead behavioral analysis for adaptive weighting"""

    segment: LeadSegment
    past_likes: List[str]  # property IDs
    past_passes: List[str]  # property IDs
    engagement_patterns: Dict[str, Any]
    preference_deviations: Dict[str, float]  # what they do vs. what they say
    response_rate: float
    avg_time_on_card: float
    search_consistency: str  # "very_consistent", "consistent", "inconsistent"


@dataclass
class AdaptiveWeights:
    """Dynamically calculated weights per lead"""

    traditional_weights: Dict[str, float]
    lifestyle_weights: Dict[str, float]
    contextual_weights: Dict[str, float]
    market_timing_weight: float
    confidence_level: float
    learning_iterations: int
    last_updated: datetime


@dataclass
class MatchScoreBreakdown:
    """Detailed scoring breakdown"""

    traditional_scores: TraditionalScores
    lifestyle_scores: LifestyleScores
    contextual_scores: ContextualScores
    market_timing_score: MarketTimingScore
    adaptive_weights: AdaptiveWeights
    overall_score: float
    confidence_level: float
    data_completeness: float  # percentage of factors with good data


@dataclass
class MatchReasoning:
    """Human-readable match explanation"""

    primary_strengths: List[str]  # Top 3-5 reasons why it matches
    secondary_benefits: List[str]  # Additional positives
    potential_concerns: List[str]  # Honest drawbacks
    agent_talking_points: List[str]  # For follow-up conversations
    comparison_to_past_likes: Optional[str]  # vs previously liked properties
    lifestyle_fit_summary: str  # Lifestyle compatibility narrative
    market_opportunity_summary: str  # Timing and market insights


@dataclass
class PropertyMatch:
    """Complete property match result"""

    property: Dict[str, Any]  # Original property data
    overall_score: float  # Final weighted score 0.0-1.0
    score_breakdown: MatchScoreBreakdown
    reasoning: MatchReasoning
    match_rank: Optional[int]  # Position in results list
    generated_at: datetime
    lead_id: str
    preferences_used: Dict[str, Any]

    # Performance tracking
    predicted_engagement: float  # Predicted CTR
    predicted_showing_request: float  # Probability of showing
    confidence_interval: tuple[float, float]  # Min/max expected score


@dataclass
class MatchingContext:
    """Context for matching session"""

    lead_id: str
    preferences: Dict[str, Any]
    behavioral_profile: BehavioralProfile
    session_id: str
    search_history: List[Dict[str, Any]]
    market_conditions: Dict[str, Any]
    available_data_sources: List[str]  # APIs available

    # Quality controls
    min_score_threshold: float
    max_results: int
    require_explanation: bool
    fallback_to_basic: bool  # If enhanced fails, use basic matching


# Configuration constants
DEFAULT_SEGMENT_WEIGHTS = {
    LeadSegment.FAMILY_WITH_KIDS: {
        "schools": 0.25,
        "safety": 0.15,
        "budget": 0.20,
        "bedrooms": 0.15,
        "location": 0.10,
        "lot_size": 0.08,
        "walkability": 0.07,
    },
    LeadSegment.YOUNG_PROFESSIONAL: {
        "commute": 0.25,
        "walkability": 0.20,
        "budget": 0.20,
        "location": 0.15,
        "property_type": 0.10,
        "market_timing": 0.10,
    },
    LeadSegment.INVESTOR: {
        "market_timing": 0.30,
        "budget": 0.25,
        "property_condition": 0.15,
        "location": 0.15,
        "days_on_market": 0.10,
        "hoa_fee": 0.05,
    },
    LeadSegment.LUXURY_BUYER: {
        "location": 0.30,
        "property_condition": 0.25,
        "lot_size": 0.15,
        "amenities": 0.15,
        "sqft": 0.10,
        "budget": 0.05,  # Less sensitive to price
    },
    LeadSegment.FIRST_TIME_BUYER: {
        "budget": 0.30,
        "market_timing": 0.15,
        "location": 0.15,
        "property_condition": 0.15,
        "sqft": 0.15,
        "safety": 0.10,
    },
    LeadSegment.RETIREE: {
        "safety": 0.25,
        "property_condition": 0.20,
        "amenities": 0.15,
        "location": 0.15,
        "hoa_fee": 0.15,
        "budget": 0.10,
    },
    LeadSegment.DOWNSIZER: {
        "location": 0.25,
        "property_condition": 0.20,
        "budget": 0.20,
        "walkability": 0.15,
        "sqft": 0.10,
        "lot_size": 0.10,
    },
}

FACTOR_WEIGHTS_BASE = {
    # Traditional factors (60% total)
    "budget": 0.20,
    "location": 0.15,
    "bedrooms": 0.10,
    "bathrooms": 0.05,
    "property_type": 0.05,
    "sqft": 0.05,
    # Lifestyle factors (25% total)
    "schools": 0.08,
    "commute": 0.06,
    "walkability": 0.06,
    "safety": 0.05,
    # Contextual factors (10% total)
    "hoa_fee": 0.03,
    "lot_size": 0.03,
    "home_age": 0.02,
    "parking": 0.02,
    # Market timing (5% total)
    "market_timing": 0.05,
}
