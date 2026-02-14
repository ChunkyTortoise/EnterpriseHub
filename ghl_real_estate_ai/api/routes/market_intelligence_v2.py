"""
Market Intelligence API V2 - Multi-Market Geographic Expansion Support.

ENHANCED: Market-agnostic API routes supporting multiple markets through configuration.

Features:
- Dynamic market selection via market_id parameter
- Unified API interface across all markets
- Market registry integration
- Backward compatibility with V1 routes
- Configuration-driven market data

Supported Markets:
- Rancho Cucamonga (tech_hub)
- Dallas (finance_hub)
- Houston (energy_hub)
- San Antonio (mixed_economy)
- Rancho Cucamonga (logistics_hub)

Usage:
    GET /api/v2/market-intelligence/metrics?market_id=rancho_cucamonga
    GET /api/v2/market-intelligence/properties?market_id=dallas&min_price=400000
    GET /api/v2/market-intelligence/neighborhoods?market_id=houston
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger

# ENHANCED: Import market registry and configuration schemas
from ghl_real_estate_ai.markets import (
    PropertyType,
    get_market_registry,
    get_market_service,
)

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v2/market-intelligence", tags=["Market Intelligence V2 (Multi-Market)"])

# ============================================================================
# ENHANCED: Market-Agnostic Pydantic Models
# ============================================================================


class MarketInfoResponse(BaseModel):
    """Market information response."""

    market_id: str
    market_name: str
    market_type: str
    state: str
    region: str
    active: bool
    neighborhoods_count: int
    employers_count: int
    primary_specialization: str
    coordinates: List[float]


class MarketMetricsResponse(BaseModel):
    """Market-agnostic metrics response model."""

    market_id: str
    market_name: str
    median_price: float
    average_days_on_market: int
    inventory_count: int
    months_supply: float
    price_trend_1m: float
    price_trend_3m: float
    price_trend_1y: float
    new_listings_7d: int
    closed_sales_30d: int
    pending_sales: int
    absorption_rate: float
    market_condition: str
    neighborhood: Optional[str] = None
    property_type: Optional[str] = None
    last_updated: datetime


class NeighborhoodResponse(BaseModel):
    """Market-agnostic neighborhood response."""

    market_id: str
    name: str
    zone: str
    median_price: float
    price_trend_3m: float
    school_rating: float
    walkability_score: int
    coordinates: List[float]
    appeal_scores: Dict[str, float]
    amenities: List[str]
    demographics: Dict[str, Any]
    corporate_proximity: Dict[str, float]


class EmployerResponse(BaseModel):
    """Market employer response."""

    employer_id: str
    name: str
    industry: str
    location: str
    coordinates: List[float]
    employee_count: int
    preferred_neighborhoods: List[str]
    average_salary_range: List[float]
    relocation_frequency: str
    hiring_seasons: List[str]


class PropertySearchRequest(BaseModel):
    """Market-agnostic property search request."""

    market_id: str = Field(..., description="Market identifier")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    min_beds: Optional[int] = Field(None, description="Minimum bedrooms")
    max_beds: Optional[int] = Field(None, description="Maximum bedrooms")
    min_baths: Optional[float] = Field(None, description="Minimum bathrooms")
    property_types: Optional[List[str]] = Field(None, description="Property types to include")
    neighborhoods: Optional[List[str]] = Field(None, description="Preferred neighborhoods")
    max_commute_minutes: Optional[int] = Field(None, description="Maximum commute time to work")
    work_location: Optional[str] = Field(None, description="Work location for commute calculation")
    appeal_preferences: Optional[List[str]] = Field(
        None, description="Appeal preferences (e.g., tech_appeal, family_appeal)"
    )
    limit: int = Field(50, description="Maximum results to return", le=100)


class PropertyRecommendationRequest(BaseModel):
    """Market-agnostic property recommendation request."""

    market_id: str = Field(..., description="Market identifier")
    lead_id: str = Field(..., description="Lead identifier")
    employer: Optional[str] = Field(None, description="Lead's employer")
    budget_range: Optional[List[float]] = Field(None, description="[min_price, max_price]")
    family_status: Optional[str] = Field(None, description="Family situation")
    appeal_preferences: Optional[List[str]] = Field(None, description="Appeal preferences")
    commute_requirements: Optional[str] = Field(None, description="Commute preferences")
    timeline: Optional[str] = Field(None, description="Purchase timeline")


# ============================================================================
# ENHANCED: Market Management Endpoints
# ============================================================================


@router.get("/markets", response_model=List[MarketInfoResponse])
async def list_available_markets():
    """Get list of all available markets with basic information."""
    try:
        registry = get_market_registry()
        active_markets = registry.list_active_markets()

        market_info = []
        for market_id in active_markets:
            config = registry.get_market_config(market_id)
            if config:
                market_info.append(
                    MarketInfoResponse(
                        market_id=config.market_id,
                        market_name=config.market_name,
                        market_type=config.market_type.value,
                        state=config.state,
                        region=config.region,
                        active=config.active,
                        neighborhoods_count=len(config.neighborhoods),
                        employers_count=len(config.employers),
                        primary_specialization=config.specializations.primary_specialization,
                        coordinates=list(config.coordinates),
                    )
                )

        logger.info(f"Listed {len(market_info)} active markets")
        return market_info

    except Exception as e:
        logger.error(f"Error listing markets: {e}")
        raise HTTPException(500, f"Failed to retrieve markets: {str(e)}")


@router.get("/markets/{market_id}/info", response_model=MarketInfoResponse)
async def get_market_info(market_id: str = Path(..., description="Market identifier")):
    """Get detailed information about a specific market."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        return MarketInfoResponse(
            market_id=config.market_id,
            market_name=config.market_name,
            market_type=config.market_type.value,
            state=config.state,
            region=config.region,
            active=config.active,
            neighborhoods_count=len(config.neighborhoods),
            employers_count=len(config.employers),
            primary_specialization=config.specializations.primary_specialization,
            coordinates=list(config.coordinates),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market info for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve market info: {str(e)}")


@router.get("/markets/{market_id}/specializations")
async def get_market_specializations(market_id: str = Path(..., description="Market identifier")):
    """Get market specialization information and expertise areas."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        return {
            "market_id": market_id,
            "market_name": config.market_name,
            "specializations": {
                "primary_specialization": config.specializations.primary_specialization,
                "secondary_specializations": config.specializations.secondary_specializations,
                "unique_advantages": config.specializations.unique_advantages,
                "target_client_types": config.specializations.target_client_types,
                "expertise_tags": config.specializations.expertise_tags,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting specializations for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve specializations: {str(e)}")


# ============================================================================
# ENHANCED: Market Metrics Endpoints
# ============================================================================


@router.get("/markets/{market_id}/metrics", response_model=MarketMetricsResponse)
async def get_market_metrics(
    market_id: str = Path(..., description="Market identifier"),
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
):
    """
    Get comprehensive market metrics for any supported market.

    Returns current market conditions, pricing trends, and inventory data.
    Can be filtered by neighborhood and property type.
    """
    try:
        # Get market service via registry
        market_service = get_market_service(market_id)

        # Convert property type string to enum if provided
        prop_type = None
        if property_type:
            try:
                prop_type = PropertyType(property_type.lower().replace(" ", "_"))
            except ValueError:
                raise HTTPException(400, f"Invalid property type: {property_type}")

        # Get metrics from market service
        metrics = await market_service.get_market_metrics(neighborhood, prop_type)

        # Get market configuration for response
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        return MarketMetricsResponse(
            market_id=market_id,
            market_name=config.market_name if config else market_id,
            median_price=metrics.median_price,
            average_days_on_market=metrics.average_days_on_market,
            inventory_count=metrics.inventory_count,
            months_supply=metrics.months_supply,
            price_trend_1m=metrics.price_trend_1m,
            price_trend_3m=metrics.price_trend_3m,
            price_trend_1y=metrics.price_trend_1y,
            new_listings_7d=metrics.new_listings_7d,
            closed_sales_30d=metrics.closed_sales_30d,
            pending_sales=metrics.pending_sales,
            absorption_rate=metrics.absorption_rate,
            market_condition=metrics.market_condition.value,
            neighborhood=neighborhood,
            property_type=property_type,
            last_updated=datetime.now(),
        )

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(404, f"Market '{market_id}' not found")
        else:
            raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error getting market metrics for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve market metrics: {str(e)}")


# ============================================================================
# ENHANCED: Neighborhood Endpoints
# ============================================================================


@router.get("/markets/{market_id}/neighborhoods", response_model=List[NeighborhoodResponse])
async def get_market_neighborhoods(market_id: str = Path(..., description="Market identifier")):
    """Get list of neighborhoods for a specific market."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        neighborhoods = []
        for neighborhood in config.neighborhoods:
            neighborhoods.append(
                NeighborhoodResponse(
                    market_id=market_id,
                    name=neighborhood.name,
                    zone=neighborhood.zone,
                    median_price=neighborhood.median_price,
                    price_trend_3m=neighborhood.price_trend_3m,
                    school_rating=neighborhood.school_rating,
                    walkability_score=neighborhood.walkability_score,
                    coordinates=list(neighborhood.coordinates),
                    appeal_scores=neighborhood.appeal_scores,
                    amenities=neighborhood.amenities,
                    demographics=neighborhood.demographics,
                    corporate_proximity=neighborhood.corporate_proximity,
                )
            )

        return neighborhoods

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting neighborhoods for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve neighborhoods: {str(e)}")


@router.get("/markets/{market_id}/neighborhoods/{neighborhood_name}", response_model=NeighborhoodResponse)
async def get_neighborhood_details(
    market_id: str = Path(..., description="Market identifier"),
    neighborhood_name: str = Path(..., description="Neighborhood name"),
):
    """Get detailed analysis for a specific neighborhood in a market."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        # Find neighborhood in configuration
        neighborhood_config = config.get_neighborhood_by_name(neighborhood_name)
        if not neighborhood_config:
            raise HTTPException(404, f"Neighborhood '{neighborhood_name}' not found in {market_id}")

        return NeighborhoodResponse(
            market_id=market_id,
            name=neighborhood_config.name,
            zone=neighborhood_config.zone,
            median_price=neighborhood_config.median_price,
            price_trend_3m=neighborhood_config.price_trend_3m,
            school_rating=neighborhood_config.school_rating,
            walkability_score=neighborhood_config.walkability_score,
            coordinates=list(neighborhood_config.coordinates),
            appeal_scores=neighborhood_config.appeal_scores,
            amenities=neighborhood_config.amenities,
            demographics=neighborhood_config.demographics,
            corporate_proximity=neighborhood_config.corporate_proximity,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting neighborhood details for {market_id}/{neighborhood_name}: {e}")
        raise HTTPException(500, f"Failed to retrieve neighborhood details: {str(e)}")


# ============================================================================
# ENHANCED: Employer & Corporate Endpoints
# ============================================================================


@router.get("/markets/{market_id}/employers", response_model=List[EmployerResponse])
async def get_market_employers(market_id: str = Path(..., description="Market identifier")):
    """Get list of major employers for a specific market."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        employers = []
        for employer in config.employers:
            employers.append(
                EmployerResponse(
                    employer_id=employer.employer_id,
                    name=employer.name,
                    industry=employer.industry,
                    location=employer.location,
                    coordinates=list(employer.coordinates),
                    employee_count=employer.employee_count,
                    preferred_neighborhoods=employer.preferred_neighborhoods,
                    average_salary_range=list(employer.average_salary_range),
                    relocation_frequency=employer.relocation_frequency,
                    hiring_seasons=employer.hiring_seasons,
                )
            )

        return employers

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employers for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve employers: {str(e)}")


@router.get("/markets/{market_id}/employers/{employer_id}", response_model=EmployerResponse)
async def get_employer_details(
    market_id: str = Path(..., description="Market identifier"),
    employer_id: str = Path(..., description="Employer identifier"),
):
    """Get detailed information about a specific employer."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        # Find employer in configuration
        employer_config = config.get_employer_by_id(employer_id)
        if not employer_config:
            raise HTTPException(404, f"Employer '{employer_id}' not found in {market_id}")

        return EmployerResponse(
            employer_id=employer_config.employer_id,
            name=employer_config.name,
            industry=employer_config.industry,
            location=employer_config.location,
            coordinates=list(employer_config.coordinates),
            employee_count=employer_config.employee_count,
            preferred_neighborhoods=employer_config.preferred_neighborhoods,
            average_salary_range=list(employer_config.average_salary_range),
            relocation_frequency=employer_config.relocation_frequency,
            hiring_seasons=employer_config.hiring_seasons,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employer details for {market_id}/{employer_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve employer details: {str(e)}")


# ============================================================================
# ENHANCED: Property Search Endpoints
# ============================================================================


@router.post("/markets/{market_id}/properties/search")
async def search_properties(
    market_id: str = Path(..., description="Market identifier"), search_request: PropertySearchRequest = None
):
    """
    Search for properties in a specific market with comprehensive filtering.

    Supports filtering by price, bedrooms, bathrooms, neighborhoods,
    appeal preferences, and commute requirements.
    """
    try:
        if search_request:
            # Override market_id in request with path parameter
            search_request.market_id = market_id
        else:
            search_request = PropertySearchRequest(market_id=market_id)

        # Get market service via registry
        market_service = get_market_service(market_id)

        # Build search criteria from request
        criteria = {}
        if search_request.min_price is not None:
            criteria["min_price"] = search_request.min_price
        if search_request.max_price is not None:
            criteria["max_price"] = search_request.max_price
        if search_request.min_beds is not None:
            criteria["min_beds"] = search_request.min_beds
        if search_request.max_beds is not None:
            criteria["max_beds"] = search_request.max_beds
        if search_request.min_baths is not None:
            criteria["min_baths"] = search_request.min_baths
        if search_request.property_types:
            criteria["property_types"] = search_request.property_types
        if search_request.neighborhoods:
            criteria["neighborhoods"] = search_request.neighborhoods
        if search_request.appeal_preferences:
            criteria["appeal_preferences"] = search_request.appeal_preferences
        if search_request.work_location and search_request.max_commute_minutes:
            criteria["work_location"] = search_request.work_location
            criteria["max_commute_minutes"] = search_request.max_commute_minutes

        # Search properties
        properties = await market_service.search_properties(criteria, search_request.limit)

        return {
            "market_id": market_id,
            "search_criteria": criteria,
            "total_results": len(properties),
            "properties": [property.__dict__ for property in properties],
        }

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(404, f"Market '{market_id}' not found")
        else:
            raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error searching properties in {market_id}: {e}")
        raise HTTPException(500, f"Failed to search properties: {str(e)}")


@router.post("/properties/recommendations")
async def get_property_recommendations(request: PropertyRecommendationRequest):
    """
    Get AI-powered property recommendations for a lead in a specific market.

    Uses market specialization and employer data to provide personalized recommendations.
    """
    try:
        # Get market service via registry
        market_service = get_market_service(request.market_id)

        # Build criteria from lead preferences
        criteria = {}
        if request.budget_range:
            criteria["min_price"] = request.budget_range[0]
            criteria["max_price"] = request.budget_range[1]

        # Add employer-based criteria if provided
        if request.employer:
            registry = get_market_registry()
            config = registry.get_market_config(request.market_id)
            if config:
                for employer in config.employers:
                    if employer.name.lower() in request.employer.lower():
                        criteria["preferred_neighborhoods"] = employer.preferred_neighborhoods
                        break

        # Add appeal preferences
        if request.appeal_preferences:
            criteria["appeal_preferences"] = request.appeal_preferences

        # Get property recommendations
        properties = await market_service.search_properties(criteria, 20)

        # ROADMAP-047: AI-Powered Property Recommendations
        # Current: Returning basic search results
        # Required:
        #   1. Initialize market AI assistant for request.market_id
        #   2. Generate personalized recommendations using Claude
        #   3. Rank properties by lead preference match score
        #   4. Add explanation for why each property is recommended
        #   5. Cache recommendations for 1 hour
        # Dependencies: None

        return {
            "market_id": request.market_id,
            "lead_id": request.lead_id,
            "criteria": criteria,
            "recommendations": [property.__dict__ for property in properties[:10]],
            "total_found": len(properties),
        }

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(404, f"Market '{request.market_id}' not found")
        else:
            raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error getting recommendations for {request.market_id}/{request.lead_id}: {e}")
        raise HTTPException(500, f"Failed to get recommendations: {str(e)}")


# ============================================================================
# ENHANCED: Market Analytics Endpoints
# ============================================================================


@router.get("/markets/{market_id}/analytics/appeal-metrics")
async def get_appeal_metrics(market_id: str = Path(..., description="Market identifier")):
    """Get available appeal metrics for a market (e.g., tech_appeal, family_appeal)."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        # Get all appeal metrics available in this market
        appeal_metrics = config.get_appeal_metrics_available()

        return {
            "market_id": market_id,
            "market_name": config.market_name,
            "available_appeal_metrics": appeal_metrics,
            "market_specialization": config.specializations.primary_specialization,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appeal metrics for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve appeal metrics: {str(e)}")


@router.get("/markets/{market_id}/analytics/commute")
async def get_commute_analysis(
    market_id: str = Path(..., description="Market identifier"),
    employer_id: Optional[str] = Query(None, description="Filter by specific employer"),
):
    """Get commute analysis for neighborhoods relative to major employers."""
    try:
        registry = get_market_registry()
        config = registry.get_market_config(market_id)

        if not config:
            raise HTTPException(404, f"Market '{market_id}' not found")

        commute_data = []

        # Filter employers if specific employer requested
        employers = config.employers
        if employer_id:
            employers = [emp for emp in employers if emp.employer_id == employer_id]
            if not employers:
                raise HTTPException(404, f"Employer '{employer_id}' not found")

        for employer in employers:
            employer_commute = {
                "employer_id": employer.employer_id,
                "employer_name": employer.name,
                "industry": employer.industry,
                "neighborhood_commutes": [],
            }

            for neighborhood in config.neighborhoods:
                commute_time = neighborhood.corporate_proximity.get(employer.employer_id, None)
                if commute_time is not None:
                    employer_commute["neighborhood_commutes"].append(
                        {
                            "neighborhood": neighborhood.name,
                            "zone": neighborhood.zone,
                            "commute_minutes": commute_time,
                            "median_price": neighborhood.median_price,
                        }
                    )

            # Sort by commute time
            employer_commute["neighborhood_commutes"].sort(key=lambda x: x["commute_minutes"])
            commute_data.append(employer_commute)

        return {"market_id": market_id, "commute_analysis": commute_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commute analysis for {market_id}: {e}")
        raise HTTPException(500, f"Failed to retrieve commute analysis: {str(e)}")


# ============================================================================
# ENHANCED: Backward Compatibility Aliases
# ============================================================================


@router.get("/metrics")
async def get_metrics_legacy(
    market_id: str = Query("rancho_cucamonga", description="Market identifier for backward compatibility"),
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
):
    """
    LEGACY ENDPOINT: Backward compatibility with V1 API.

    Defaults to Rancho Cucamonga market for existing integrations.
    """
    logger.info(f"Legacy metrics endpoint called, routing to market: {market_id}")
    return await get_market_metrics(market_id, neighborhood, property_type)
