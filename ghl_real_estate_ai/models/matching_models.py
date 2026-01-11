"""
Data models for enhanced property matching system.
Defines all data structures for the 15-factor contextual matching algorithm.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


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
    LIFESTYLE = "lifestyle"      # schools, commute, walkability, safety
    CONTEXTUAL = "contextual"    # HOA, lot size, age, parking
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


# ============================================================================
# Multimodal Property Intelligence Models
# ============================================================================


@dataclass
class VisionIntelligenceScore:
    """Claude Vision analysis scoring for property matching"""
    luxury_score: float  # 0-10 from Claude Vision
    condition_score: float  # 0-10 from Claude Vision
    style_match_score: float  # 0-1 calculated from style compatibility

    # Detailed insights
    luxury_level: str  # ultra_luxury, high_end_luxury, etc.
    property_condition: str  # excellent, very_good, good, fair, poor
    architectural_style: str  # modern, contemporary, traditional, etc.

    # Feature matches
    premium_features: List[str]  # High-end finishes detected
    visual_appeal_score: float  # 0-10 overall appeal

    # Confidence and metadata
    confidence: float  # 0-1
    images_analyzed: int
    processing_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "luxury_score": self.luxury_score,
            "condition_score": self.condition_score,
            "style_match_score": self.style_match_score,
            "luxury_level": self.luxury_level,
            "property_condition": self.property_condition,
            "architectural_style": self.architectural_style,
            "premium_features": self.premium_features,
            "visual_appeal_score": self.visual_appeal_score,
            "confidence": self.confidence,
            "images_analyzed": self.images_analyzed,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class NeighborhoodIntelligenceScore:
    """Neighborhood intelligence scoring for property matching"""
    walkability_score: Optional[int]  # 0-100 Walk Score
    transit_score: Optional[int]  # 0-100 Transit Score
    bike_score: Optional[int]  # 0-100 Bike Score

    # School ratings
    school_average_rating: Optional[float]  # 1-10 average
    elementary_rating: Optional[float]
    middle_rating: Optional[float]
    high_rating: Optional[float]

    # Commute analysis
    commute_score: Optional[int]  # 0-100 calculated score
    average_commute_minutes: Optional[int]
    employment_centers_nearby: int
    public_transit_accessible: bool

    # Overall neighborhood composite
    overall_neighborhood_score: Optional[int]  # 0-100 composite

    # Confidence and metadata
    data_completeness: float  # 0-1 (what % of data available)
    processing_time_ms: float
    cache_hit: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "walkability_score": self.walkability_score,
            "transit_score": self.transit_score,
            "bike_score": self.bike_score,
            "school_average_rating": self.school_average_rating,
            "elementary_rating": self.elementary_rating,
            "middle_rating": self.middle_rating,
            "high_rating": self.high_rating,
            "commute_score": self.commute_score,
            "average_commute_minutes": self.average_commute_minutes,
            "employment_centers_nearby": self.employment_centers_nearby,
            "public_transit_accessible": self.public_transit_accessible,
            "overall_neighborhood_score": self.overall_neighborhood_score,
            "data_completeness": self.data_completeness,
            "processing_time_ms": self.processing_time_ms,
            "cache_hit": self.cache_hit
        }


@dataclass
class MultimodalScoreBreakdown:
    """Enhanced scoring breakdown with multimodal intelligence"""
    # Traditional scoring (from base PropertyMatch)
    traditional_score: float  # 0-1
    traditional_weight: float

    # Vision intelligence scoring
    vision_score: float  # 0-1 weighted vision contribution
    vision_weight: float

    # Neighborhood intelligence scoring
    neighborhood_score: float  # 0-1 weighted neighborhood contribution
    neighborhood_weight: float

    # Lifestyle + contextual (from base matching)
    lifestyle_contextual_score: float  # 0-1
    lifestyle_contextual_weight: float

    # Market timing
    market_timing_score: float  # 0-1
    market_timing_weight: float

    # Combined multimodal score
    multimodal_overall_score: float  # 0-1 final score
    multimodal_confidence: float  # 0-1 confidence in multimodal scoring

    # Performance metadata
    total_processing_time_ms: float
    vision_processing_time_ms: float
    neighborhood_processing_time_ms: float
    cache_hit_rate: float  # 0-1

    # Optional detailed intelligence (with defaults at end)
    vision_intelligence: Optional[VisionIntelligenceScore] = None
    neighborhood_intelligence: Optional[NeighborhoodIntelligenceScore] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "traditional_score": self.traditional_score,
            "traditional_weight": self.traditional_weight,
            "vision_score": self.vision_score,
            "vision_weight": self.vision_weight,
            "vision_intelligence": self.vision_intelligence.to_dict() if self.vision_intelligence else None,
            "neighborhood_score": self.neighborhood_score,
            "neighborhood_weight": self.neighborhood_weight,
            "neighborhood_intelligence": self.neighborhood_intelligence.to_dict() if self.neighborhood_intelligence else None,
            "lifestyle_contextual_score": self.lifestyle_contextual_score,
            "lifestyle_contextual_weight": self.lifestyle_contextual_weight,
            "market_timing_score": self.market_timing_score,
            "market_timing_weight": self.market_timing_weight,
            "multimodal_overall_score": self.multimodal_overall_score,
            "multimodal_confidence": self.multimodal_confidence,
            "total_processing_time_ms": self.total_processing_time_ms,
            "vision_processing_time_ms": self.vision_processing_time_ms,
            "neighborhood_processing_time_ms": self.neighborhood_processing_time_ms,
            "cache_hit_rate": self.cache_hit_rate
        }


@dataclass
class MultimodalPropertyMatch(PropertyMatch):
    """
    Enhanced property match with multimodal intelligence.

    Extends PropertyMatch with vision and neighborhood intelligence while
    maintaining backward compatibility for A/B testing.
    """
    # Multimodal enhancements
    multimodal_score_breakdown: Optional[MultimodalScoreBreakdown] = None
    multimodal_overall_score: Optional[float] = None  # Enhanced score for A/B comparison

    # Multimodal reasoning enhancements
    vision_highlights: List[str] = field(default_factory=list)
    neighborhood_highlights: List[str] = field(default_factory=list)
    multimodal_insights: List[str] = field(default_factory=list)

    # A/B testing metadata
    matching_version: str = "traditional"  # "traditional" or "multimodal"
    ab_test_group: Optional[str] = None  # For A/B testing tracking
    satisfaction_predicted: Optional[float] = None  # Predicted user satisfaction (88% baseline → 93% target)

    # Performance comparison
    traditional_vs_multimodal_delta: Optional[float] = None  # Score difference
    multimodal_enabled: bool = False

    def get_active_score(self) -> float:
        """Get the active score based on matching version"""
        if self.matching_version == "multimodal" and self.multimodal_overall_score is not None:
            return self.multimodal_overall_score
        return self.overall_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching/serialization"""
        base_dict = {
            "property": self.property,
            "overall_score": self.overall_score,
            "match_rank": self.match_rank,
            "generated_at": self.generated_at.isoformat(),
            "lead_id": self.lead_id,
            "preferences_used": self.preferences_used,
            "predicted_engagement": self.predicted_engagement,
            "predicted_showing_request": self.predicted_showing_request,
            "confidence_interval": self.confidence_interval,

            # Multimodal fields
            "multimodal_overall_score": self.multimodal_overall_score,
            "multimodal_score_breakdown": self.multimodal_score_breakdown.to_dict() if self.multimodal_score_breakdown else None,
            "vision_highlights": self.vision_highlights,
            "neighborhood_highlights": self.neighborhood_highlights,
            "multimodal_insights": self.multimodal_insights,
            "matching_version": self.matching_version,
            "ab_test_group": self.ab_test_group,
            "satisfaction_predicted": self.satisfaction_predicted,
            "traditional_vs_multimodal_delta": self.traditional_vs_multimodal_delta,
            "multimodal_enabled": self.multimodal_enabled
        }

        return base_dict


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
        "walkability": 0.07
    },
    LeadSegment.YOUNG_PROFESSIONAL: {
        "commute": 0.25,
        "walkability": 0.20,
        "budget": 0.20,
        "location": 0.15,
        "property_type": 0.10,
        "market_timing": 0.10
    },
    LeadSegment.INVESTOR: {
        "market_timing": 0.30,
        "budget": 0.25,
        "property_condition": 0.15,
        "location": 0.15,
        "days_on_market": 0.10,
        "hoa_fee": 0.05
    },
    LeadSegment.LUXURY_BUYER: {
        "location": 0.30,
        "property_condition": 0.25,
        "lot_size": 0.15,
        "amenities": 0.15,
        "sqft": 0.10,
        "budget": 0.05  # Less sensitive to price
    }
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
    "market_timing": 0.05
}

# Multimodal enhancement weights (for A/B testing)
MULTIMODAL_WEIGHTS = {
    # Traditional factors (reduced from 60% to 45%)
    "traditional_base": 0.45,

    # Vision intelligence (15%)
    "vision_luxury_score": 0.08,
    "vision_condition_score": 0.05,
    "vision_style_match": 0.02,

    # Neighborhood intelligence (15%)
    "neighborhood_walkability": 0.05,
    "neighborhood_schools": 0.05,
    "neighborhood_commute": 0.05,

    # Lifestyle + Contextual (15%)
    "lifestyle_contextual": 0.15,

    # Market timing (10%)
    "market_timing": 0.10
}