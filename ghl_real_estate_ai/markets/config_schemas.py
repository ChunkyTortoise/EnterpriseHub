"""
Market Configuration Schemas for Multi-Market Support

This module defines Pydantic models for market configuration data,
enabling configuration-driven market expansion vs hardcoded implementations.

Key Models:
- MarketConfig: Core market metadata and settings
- NeighborhoodConfig: Neighborhood-specific data and metrics
- EmployerConfig: Corporate employer and relocation data
- MarketSpecializationConfig: Market-specific expertise and positioning

Author: EnterpriseHub AI
Created: 2026-01-19
"""

from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime


class PropertyType(Enum):
    """Property types - market agnostic"""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOME = "townhome"
    LAND = "land"
    MULTI_FAMILY = "multi_family"


class MarketCondition(Enum):
    """Market conditions - market agnostic"""
    STRONG_SELLERS = "strong_sellers"
    BALANCED = "balanced"
    STRONG_BUYERS = "strong_buyers"
    TRANSITIONING = "transitioning"


class MarketType(Enum):
    """Market type classification"""
    TECH_HUB = "tech_hub"  # Austin, Seattle, SF
    ENERGY_HUB = "energy_hub"  # Houston, Dallas
    LOGISTICS_HUB = "logistics_hub"  # Inland Empire
    MIXED_ECONOMY = "mixed_economy"  # San Antonio
    FINANCE_HUB = "finance_hub"  # Dallas, Charlotte


class NeighborhoodConfig(BaseModel):
    """Configuration for neighborhood data"""
    name: str = Field(..., description="Neighborhood name")
    zone: str = Field(..., description="Zone/region within market (e.g., Central, North)")
    median_price: float = Field(..., gt=0, description="Median home price")
    price_trend_3m: float = Field(default=0.0, description="3-month price trend percentage")
    school_rating: float = Field(..., ge=1.0, le=10.0, description="School district rating 1-10")
    walkability_score: int = Field(..., ge=0, le=100, description="Walk Score 0-100")

    # Market-specific appeal scores (configurable per market type)
    appeal_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Market-specific appeal metrics (e.g., tech_appeal, logistics_appeal)"
    )

    # Geographic and amenity data
    coordinates: Tuple[float, float] = Field(..., description="(lat, lng) coordinates")
    amenities: List[str] = Field(default_factory=list, description="Neighborhood amenities")
    demographics: Dict[str, Any] = Field(default_factory=dict, description="Demographic data")

    # Corporate proximity (employer_id -> commute_minutes)
    corporate_proximity: Dict[str, float] = Field(
        default_factory=dict,
        description="Commute times to major employers"
    )

    @field_validator('appeal_scores')
    @classmethod
    def validate_appeal_scores(cls, v):
        """Ensure all appeal scores are 0-100"""
        for key, score in v.items():
            if not 0 <= score <= 100:
                raise ValueError(f"Appeal score {key} must be 0-100, got {score}")
        return v


class EmployerConfig(BaseModel):
    """Configuration for major employers and corporate headquarters"""
    employer_id: str = Field(..., description="Unique employer identifier")
    name: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry category")
    location: str = Field(..., description="Primary location/campus")
    coordinates: Tuple[float, float] = Field(..., description="(lat, lng) coordinates")
    employee_count: int = Field(..., gt=0, description="Approximate employee count")

    # Relocation patterns
    preferred_neighborhoods: List[str] = Field(
        default_factory=list,
        description="Neighborhoods preferred by employees"
    )
    average_salary_range: Tuple[float, float] = Field(
        default=(50000, 150000),
        description="(min, max) salary range"
    )
    relocation_frequency: str = Field(
        default="medium",
        description="Relocation frequency: low, medium, high"
    )

    # Seasonal patterns
    hiring_seasons: List[str] = Field(
        default_factory=list,
        description="Peak hiring seasons (Q1, Q2, Q3, Q4)"
    )


class MarketSpecializationConfig(BaseModel):
    """Market-specific specializations and competitive advantages"""
    primary_specialization: str = Field(..., description="Primary market focus")
    secondary_specializations: List[str] = Field(
        default_factory=list,
        description="Secondary market focuses"
    )

    # Competitive positioning
    unique_advantages: List[str] = Field(
        default_factory=list,
        description="Unique competitive advantages"
    )
    target_client_types: List[str] = Field(
        default_factory=list,
        description="Target client demographics"
    )

    # Expertise areas
    expertise_tags: List[str] = Field(
        default_factory=list,
        description="Expertise tags for AI assistant"
    )
    knowledge_base_path: Optional[str] = Field(
        default=None,
        description="Path to market-specific knowledge base"
    )


class MarketConfig(BaseModel):
    """Core market configuration"""
    # Basic identification
    market_id: str = Field(..., description="Unique market identifier")
    market_name: str = Field(..., description="Human-readable market name")
    market_type: MarketType = Field(..., description="Market type classification")
    state: str = Field(..., description="State code or province")
    region: str = Field(..., description="Geographic region")
    currency: str = Field(default="usd", description="Market currency (usd, gbp, sgd, etc.)")

    # Geographic data
    coordinates: Tuple[float, float] = Field(..., description="Market center coordinates")
    timezone: str = Field(..., description="Timezone (e.g., America/Chicago)")
    mls_provider: str = Field(..., description="MLS data provider")

    # Market data
    neighborhoods: List[NeighborhoodConfig] = Field(
        default_factory=list,
        description="Neighborhood configurations"
    )
    employers: List[EmployerConfig] = Field(
        default_factory=list,
        description="Major employer configurations"
    )
    specializations: MarketSpecializationConfig = Field(
        ...,
        description="Market specialization configuration"
    )

    # Economic indicators
    median_home_price: float = Field(..., gt=0, description="Market median home price")
    price_appreciation_1y: float = Field(default=0.0, description="1-year price appreciation %")
    inventory_days: int = Field(default=30, description="Days of inventory")

    # Configuration metadata
    config_version: str = Field(default="1.0", description="Configuration version")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    active: bool = Field(default=True, description="Whether market is active")

    @field_validator('market_id')
    @classmethod
    def validate_market_id(cls, v):
        """Ensure market_id is lowercase and underscore-separated"""
        if not v.islower() or ' ' in v:
            raise ValueError("market_id must be lowercase with underscores")
        return v

    def get_neighborhood_by_name(self, name: str) -> Optional[NeighborhoodConfig]:
        """Get neighborhood by name"""
        for neighborhood in self.neighborhoods:
            if neighborhood.name.lower() == name.lower():
                return neighborhood
        return None

    def get_employer_by_id(self, employer_id: str) -> Optional[EmployerConfig]:
        """Get employer by ID"""
        for employer in self.employers:
            if employer.employer_id == employer_id:
                return employer
        return None

    def get_appeal_metrics_available(self) -> List[str]:
        """Get all available appeal metric types across neighborhoods"""
        appeal_types = set()
        for neighborhood in self.neighborhoods:
            appeal_types.update(neighborhood.appeal_scores.keys())
        return list(appeal_types)


class MarketValidationError(Exception):
    """Raised when market configuration validation fails"""
    pass


def validate_market_config(config: MarketConfig) -> List[str]:
    """
    Validate market configuration and return list of warnings/issues

    Args:
        config: MarketConfig to validate

    Returns:
        List of validation warnings/issues
    """
    warnings = []

    # Check required neighborhoods
    if len(config.neighborhoods) < 3:
        warnings.append(f"Market {config.market_id} has only {len(config.neighborhoods)} neighborhoods, recommend at least 3")

    # Check required employers
    if len(config.employers) < 2:
        warnings.append(f"Market {config.market_id} has only {len(config.employers)} employers, recommend at least 2")

    # Check neighborhood appeal scores consistency
    appeal_types = config.get_appeal_metrics_available()
    for neighborhood in config.neighborhoods:
        missing_appeals = set(appeal_types) - set(neighborhood.appeal_scores.keys())
        if missing_appeals:
            warnings.append(f"Neighborhood {neighborhood.name} missing appeal scores: {missing_appeals}")

    # Check employer-neighborhood relationships
    all_neighborhood_names = {n.name for n in config.neighborhoods}
    for employer in config.employers:
        invalid_neighborhoods = set(employer.preferred_neighborhoods) - all_neighborhood_names
        if invalid_neighborhoods:
            warnings.append(f"Employer {employer.name} references invalid neighborhoods: {invalid_neighborhoods}")

    return warnings