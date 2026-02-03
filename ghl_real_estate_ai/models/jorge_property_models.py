"""
Jorge's Property Matching Models
Data structures for intelligent property-lead matching system
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from ghl_real_estate_ai.services.enhanced_smart_lead_scorer import (
    LeadPriority, BuyingStage, LeadScoreBreakdown
)


class ConfidenceLevel(Enum):
    """Confidence level for property matches."""
    VERY_HIGH = "very_high"    # 90-100%
    HIGH = "high"              # 75-90%
    MEDIUM = "medium"          # 50-75%
    LOW = "low"                # 25-50%
    VERY_LOW = "very_low"      # 0-25%


class PropertyType(Enum):
    """Property types in Rancho Cucamonga market."""
    SINGLE_FAMILY = "single_family"
    TOWNHOME = "townhome"
    CONDO = "condo"
    LUXURY_HOME = "luxury_home"
    NEW_CONSTRUCTION = "new_construction"


class MatchingAlgorithm(Enum):
    """Matching algorithms used."""
    NEURAL_ONLY = "neural_only"
    RULES_ONLY = "rules_only"
    HYBRID = "hybrid"
    JORGE_OPTIMIZED = "jorge_optimized"


class PropertyAddress(BaseModel):
    """Property address structure."""
    street: str
    city: str = "Rancho Cucamonga"
    state: str = "CA"
    zip_code: str
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SchoolInfo(BaseModel):
    """School information for property."""
    name: str
    type: str  # elementary, middle, high
    rating: int  # 1-10 scale
    distance_miles: float
    district: str


class PropertyFeatures(BaseModel):
    """Property features and amenities."""
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_size_sqft: Optional[int] = None
    garage_spaces: Optional[int] = None
    year_built: Optional[int] = None
    has_pool: bool = False
    has_spa: bool = False
    fireplace: bool = False
    hardwood_floors: bool = False
    granite_counters: bool = False
    stainless_appliances: bool = False
    updated_kitchen: bool = False
    updated_bathrooms: bool = False


class Property(BaseModel):
    """Complete property information."""
    id: str
    tenant_id: str = Field(..., description="Tenant ID owning or managing this property")
    mls_number: Optional[str] = None
    address: PropertyAddress
    price: float
    features: PropertyFeatures
    property_type: PropertyType

    # Market Data
    days_on_market: int = 0
    price_per_sqft: float = Field(..., description="Calculated price per sqft")
    estimated_value: Optional[float] = None
    price_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Location Intelligence
    schools: List[SchoolInfo] = Field(default_factory=list)
    commute_to_la: Optional[int] = None  # minutes
    walkability_score: Optional[int] = None  # 1-100

    # Media
    images: List[str] = Field(default_factory=list)
    virtual_tour_url: Optional[str] = None

    # Status
    status: str = "active"  # active, pending, sold
    listing_date: datetime
    last_updated: datetime = Field(default_factory=datetime.now)

    @field_validator('price_per_sqft', mode='before')
    @classmethod
    def calculate_price_per_sqft(cls, v, info: ValidationInfo):
        """Auto-calculate price per sqft."""
        if v is None and 'price' in info.data and 'features' in info.data:
            features = info.data['features']
            if hasattr(features, 'sqft') and features.sqft > 0:
                return round(info.data['price'] / features.sqft, 2)
        return v


class LeadPropertyPreferences(BaseModel):
    """Extracted property preferences from lead data."""
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_bedrooms: Optional[int] = None
    min_bedrooms: Optional[int] = None
    preferred_bathrooms: Optional[float] = None
    min_bathrooms: Optional[float] = None

    # Location Preferences
    preferred_neighborhoods: List[str] = Field(default_factory=list)
    max_commute_minutes: Optional[int] = None
    school_rating_min: Optional[int] = None

    # Features
    must_have_features: List[str] = Field(default_factory=list)
    nice_to_have_features: List[str] = Field(default_factory=list)
    dealbreaker_features: List[str] = Field(default_factory=list)

    # Property Type
    property_type_preference: Optional[PropertyType] = None
    max_year_built: Optional[int] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None

    # Timeline
    timeline_urgency: Optional[str] = None  # immediate, 30d, 60d, 90d, flexible


class MatchReasoning(BaseModel):
    """AI-generated reasoning for property match."""
    primary_reasons: List[str] = Field(..., description="Top 3 reasons for match")
    financial_fit: str = Field(..., description="Why price/budget works")
    lifestyle_fit: str = Field(..., description="How property matches lifestyle")
    market_timing: str = Field(..., description="Market timing considerations")
    potential_concerns: List[str] = Field(default_factory=list)
    jorge_talking_points: List[str] = Field(default_factory=list)
    client_script_suggestions: List[str] = Field(default_factory=list)


class PropertyMatch(BaseModel):
    """Property match result with scoring and explanation."""
    property: Property
    lead_id: str

    # Scoring
    match_score: float = Field(..., ge=0, le=100, description="Overall match score 0-100")
    neural_score: float = Field(..., ge=0, le=100, description="Neural network score")
    rule_score: float = Field(..., ge=0, le=100, description="Business rules score")
    confidence: ConfidenceLevel

    # Ranking
    recommendation_rank: int = Field(..., ge=1, description="Rank in recommendation list")

    # Explanation
    reasoning: MatchReasoning

    # Metadata
    algorithm_used: MatchingAlgorithm
    generated_at: datetime = Field(default_factory=datetime.now)

    # Performance tracking
    processing_time_ms: Optional[int] = None
    model_version: Optional[str] = None

    @field_validator('confidence', mode='before')
    @classmethod
    def determine_confidence(cls, v, info: ValidationInfo):
        """Auto-determine confidence based on match score."""
        if v is not None:
            return v

        score = info.data.get('match_score', 0)
        if score >= 90:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 75:
            return ConfidenceLevel.HIGH
        elif score >= 50:
            return ConfidenceLevel.MEDIUM
        elif score >= 25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class PropertyMatchRequest(BaseModel):
    """Request for property matching."""
    lead_id: str
    tenant_id: str = Field(..., description="Tenant ID for the lead and matching context")
    lead_data: Dict[str, Any]
    preferences: Optional[LeadPropertyPreferences] = None

    # Filters
    max_results: int = Field(default=5, ge=1, le=20)
    min_match_score: float = Field(default=50.0, ge=0, le=100)
    algorithm: MatchingAlgorithm = MatchingAlgorithm.JORGE_OPTIMIZED

    # Context
    urgency_override: Optional[LeadPriority] = None
    agent_notes: Optional[str] = None


class PropertyMatchResponse(BaseModel):
    """Response from property matching service."""
    matches: List[PropertyMatch]
    total_considered: int
    processing_time_ms: int
    algorithm_used: MatchingAlgorithm

    # Summary
    avg_match_score: float
    best_match_score: float
    recommendation_summary: str

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    model_version: str
    cache_hit: bool = False


class PropertyFilters(BaseModel):
    """Filters for property inventory queries."""
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[List[int]] = None
    bathrooms: Optional[List[float]] = None
    property_types: Optional[List[PropertyType]] = None
    neighborhoods: Optional[List[str]] = None
    max_days_on_market: Optional[int] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None

    # Special filters
    has_pool: Optional[bool] = None
    updated_kitchen: Optional[bool] = None
    min_school_rating: Optional[int] = None

    # Geospatial
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_miles: Optional[float] = None


@dataclass
class MatchingPerformanceMetrics:
    """Performance metrics for matching algorithms."""
    avg_processing_time_ms: float
    cache_hit_rate: float
    neural_inference_time_ms: float
    rules_processing_time_ms: float
    total_properties_evaluated: int
    matches_generated: int
    accuracy_score: Optional[float] = None  # If we have feedback data


class PropertyInventoryStats(BaseModel):
    """Statistics about current property inventory."""
    total_active_listings: int
    avg_price: float
    median_price: float
    price_range_min: float
    price_range_max: float

    # By property type
    inventory_by_type: Dict[str, int]
    avg_price_by_type: Dict[str, float]

    # Market metrics
    avg_days_on_market: float
    inventory_velocity: float  # Properties sold per day
    price_trend_30d: float  # Percentage change

    # Geographic
    inventory_by_neighborhood: Dict[str, int]
    hottest_neighborhoods: List[str]

    updated_at: datetime = Field(default_factory=datetime.now)


# Export all models for easy importing
__all__ = [
    'ConfidenceLevel', 'PropertyType', 'MatchingAlgorithm',
    'PropertyAddress', 'SchoolInfo', 'PropertyFeatures', 'Property',
    'LeadPropertyPreferences', 'MatchReasoning', 'PropertyMatch',
    'PropertyMatchRequest', 'PropertyMatchResponse', 'PropertyFilters',
    'MatchingPerformanceMetrics', 'PropertyInventoryStats'
]