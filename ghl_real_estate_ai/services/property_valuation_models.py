"""
Property Valuation Data Models

Pydantic models for property valuation system with comprehensive data validation.
Supports MLS integration, ML predictions, and multi-source validation.

Author: EnterpriseHub Development Team
Created: January 10, 2026
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import uuid


class PropertyType(str, Enum):
    """Property type enumeration."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"
    INVESTMENT = "investment"


class PropertyCondition(str, Enum):
    """Property condition enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NEEDS_REPAIR = "needs_repair"


class ValuationStatus(str, Enum):
    """Valuation status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class PropertyLocation(BaseModel):
    """Property location data with geocoding."""
    address: str = Field(..., description="Full property address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State abbreviation (e.g., CA)")
    zip_code: str = Field(..., description="ZIP/postal code")
    county: Optional[str] = Field(None, description="County name")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    neighborhood: Optional[str] = Field(None, description="Neighborhood/district")
    school_district: Optional[str] = Field(None, description="School district")

    @validator('state')
    def validate_state(cls, v):
        if v and len(v) != 2:
            raise ValueError('State must be 2-character abbreviation')
        return v.upper() if v else v

    @validator('zip_code')
    def validate_zip_code(cls, v):
        if v and not (5 <= len(v.replace('-', '')) <= 10):
            raise ValueError('ZIP code must be 5-10 digits')
        return v


class PropertyFeatures(BaseModel):
    """Detailed property features and amenities."""
    bedrooms: Optional[int] = Field(None, ge=0, le=20, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, ge=0, le=20, description="Number of bathrooms")
    square_footage: Optional[int] = Field(None, ge=100, le=50000, description="Living area square footage")
    lot_size: Optional[float] = Field(None, ge=0, description="Lot size in acres")
    year_built: Optional[int] = Field(None, ge=1800, le=2030, description="Year property was built")
    garage_spaces: Optional[int] = Field(None, ge=0, le=10, description="Number of garage spaces")
    stories: Optional[int] = Field(None, ge=1, le=5, description="Number of stories")

    # Additional features
    has_pool: Optional[bool] = Field(False, description="Has swimming pool")
    has_spa: Optional[bool] = Field(False, description="Has spa/hot tub")
    has_fireplace: Optional[bool] = Field(False, description="Has fireplace")
    has_ac: Optional[bool] = Field(False, description="Has air conditioning")
    has_basement: Optional[bool] = Field(False, description="Has basement")
    has_attic: Optional[bool] = Field(False, description="Has attic")

    # Condition and upgrades
    condition: Optional[PropertyCondition] = Field(None, description="Overall property condition")
    recent_renovations: Optional[List[str]] = Field([], description="List of recent renovations")
    amenities: Optional[List[str]] = Field([], description="Additional amenities")


class PropertyData(BaseModel):
    """Complete property data model for valuation."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique property ID")
    property_type: PropertyType = Field(..., description="Type of property")
    location: PropertyLocation = Field(..., description="Property location details")
    features: PropertyFeatures = Field(..., description="Property features and amenities")

    # Market data
    list_price: Optional[Decimal] = Field(None, ge=0, description="Current list price")
    tax_assessed_value: Optional[Decimal] = Field(None, ge=0, description="Tax assessed value")
    property_taxes: Optional[Decimal] = Field(None, ge=0, description="Annual property taxes")
    hoa_fees: Optional[Decimal] = Field(None, ge=0, description="Monthly HOA fees")

    # Additional context
    mls_number: Optional[str] = Field(None, description="MLS listing number")
    parcel_number: Optional[str] = Field(None, description="Tax parcel/APN number")
    description: Optional[str] = Field(None, description="Property description")
    photos: Optional[List[str]] = Field([], description="List of photo URLs")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class ComparableSale(BaseModel):
    """Comparable sale property data from MLS."""
    mls_number: str = Field(..., description="MLS listing number")
    address: str = Field(..., description="Property address")
    sale_price: Decimal = Field(..., ge=0, description="Sale price")
    sale_date: datetime = Field(..., description="Date of sale")

    # Property details
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms")
    square_footage: Optional[int] = Field(None, description="Living area square footage")
    lot_size: Optional[float] = Field(None, description="Lot size in acres")
    year_built: Optional[int] = Field(None, description="Year built")

    # Location and similarity
    distance_miles: Optional[float] = Field(None, ge=0, description="Distance from subject property")
    similarity_score: Optional[float] = Field(None, ge=0, le=1, description="AI similarity score")
    adjustment_factors: Optional[Dict[str, float]] = Field({}, description="Price adjustment factors")

    # Market context
    days_on_market: Optional[int] = Field(None, description="Days on market before sale")
    price_per_sqft: Optional[Decimal] = Field(None, description="Price per square foot")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None,
            datetime: lambda v: v.isoformat()
        }


class MLPrediction(BaseModel):
    """Machine learning price prediction results."""
    predicted_value: Decimal = Field(..., ge=0, description="ML predicted value")
    value_range_low: Decimal = Field(..., ge=0, description="Lower bound of prediction range")
    value_range_high: Decimal = Field(..., ge=0, description="Upper bound of prediction range")
    confidence_score: float = Field(..., ge=0, le=1, description="Prediction confidence (0-1)")

    # Model metadata
    model_version: str = Field(..., description="ML model version")
    model_accuracy: Optional[float] = Field(None, description="Model's historical accuracy")
    feature_importance: Optional[Dict[str, float]] = Field({}, description="Feature importance scores")

    # Prediction details
    prediction_date: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(None, description="Prediction processing time")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class ThirdPartyEstimate(BaseModel):
    """Third-party valuation estimate (Zillow, Redfin, etc.)."""
    source: str = Field(..., description="Estimation source (zillow, redfin, etc.)")
    estimated_value: Decimal = Field(..., ge=0, description="Estimated value")
    value_range_low: Optional[Decimal] = Field(None, description="Lower range estimate")
    value_range_high: Optional[Decimal] = Field(None, description="Higher range estimate")
    confidence_level: Optional[str] = Field(None, description="Confidence level description")
    estimate_date: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: Optional[str] = Field(None, description="Data freshness indicator")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class ClaudeInsights(BaseModel):
    """Claude AI generated market insights and commentary."""
    market_commentary: str = Field(..., description="AI-generated market analysis")
    pricing_recommendations: List[str] = Field(..., description="Pricing strategy recommendations")
    market_trends: List[str] = Field(..., description="Current market trends")
    competitive_analysis: Optional[str] = Field(None, description="Competitive positioning analysis")
    risk_factors: Optional[List[str]] = Field([], description="Identified risk factors")
    opportunities: Optional[List[str]] = Field([], description="Market opportunities")

    # AI metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(None, description="AI processing time")
    confidence_score: Optional[float] = Field(None, description="AI confidence in insights")


class ComprehensiveValuation(BaseModel):
    """Complete property valuation results."""
    property_id: str = Field(..., description="Property identifier")
    valuation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Core valuation
    estimated_value: Decimal = Field(..., ge=0, description="Final estimated value")
    value_range_low: Decimal = Field(..., ge=0, description="Lower bound")
    value_range_high: Decimal = Field(..., ge=0, description="Upper bound")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence")

    # Supporting data
    comparable_sales: List[ComparableSale] = Field(..., description="MLS comparable sales")
    ml_prediction: Optional[MLPrediction] = Field(None, description="ML model prediction")
    third_party_estimates: List[ThirdPartyEstimate] = Field([], description="Third-party estimates")
    claude_insights: Optional[ClaudeInsights] = Field(None, description="AI market insights")

    # CMA report
    cma_report_url: Optional[str] = Field(None, description="Generated CMA report URL")

    # Valuation metadata
    valuation_method: str = Field("comprehensive", description="Valuation methodology used")
    data_sources: List[str] = Field(..., description="Data sources utilized")
    status: ValuationStatus = Field(ValuationStatus.COMPLETED, description="Valuation status")

    # Performance tracking
    total_processing_time_ms: Optional[float] = Field(None, description="Total processing time")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Valuation expiration")

    @root_validator
    def validate_value_ranges(cls, values):
        """Ensure value ranges are logical."""
        low = values.get('value_range_low')
        high = values.get('value_range_high')
        estimated = values.get('estimated_value')

        if low and high and low > high:
            raise ValueError('Value range low cannot be higher than high')

        if estimated and low and high:
            if not (low <= estimated <= high):
                raise ValueError('Estimated value must be within the specified range')

        return values

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None,
            datetime: lambda v: v.isoformat()
        }


class ValuationRequest(BaseModel):
    """Request model for property valuation."""
    property_data: PropertyData = Field(..., description="Property to be valued")
    seller_id: Optional[str] = Field(None, description="Associated seller ID")
    valuation_type: str = Field("comprehensive", description="Type of valuation requested")

    # Options
    include_mls_data: bool = Field(True, description="Include MLS comparable sales")
    include_ml_prediction: bool = Field(True, description="Include ML price prediction")
    include_third_party: bool = Field(True, description="Include third-party estimates")
    include_claude_insights: bool = Field(True, description="Include AI market insights")
    generate_cma_report: bool = Field(True, description="Generate CMA report")

    # Performance options
    max_processing_time_seconds: int = Field(30, ge=5, le=120, description="Maximum processing time")
    cache_results: bool = Field(True, description="Cache results for performance")

    # Metadata
    requested_by: Optional[str] = Field(None, description="User requesting valuation")
    request_context: Optional[Dict[str, Any]] = Field({}, description="Additional request context")


class QuickEstimateRequest(BaseModel):
    """Request model for quick property estimate."""
    address: str = Field(..., description="Property address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="ZIP code")

    # Optional quick details
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms")
    square_footage: Optional[int] = Field(None, description="Square footage")

    class Config:
        schema_extra = {
            "example": {
                "address": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94105",
                "bedrooms": 3,
                "bathrooms": 2.5,
                "square_footage": 2000
            }
        }


class QuickEstimateResponse(BaseModel):
    """Response model for quick property estimate."""
    estimated_value: Decimal = Field(..., description="Quick estimated value")
    value_range_low: Decimal = Field(..., description="Lower estimate")
    value_range_high: Decimal = Field(..., description="Higher estimate")
    confidence_score: float = Field(..., description="Confidence in estimate")
    data_sources: List[str] = Field(..., description="Sources used")
    processing_time_ms: float = Field(..., description="Processing time")

    # Recommendations
    recommendation: str = Field(..., description="Next steps recommendation")
    full_valuation_available: bool = Field(True, description="Full valuation available")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }