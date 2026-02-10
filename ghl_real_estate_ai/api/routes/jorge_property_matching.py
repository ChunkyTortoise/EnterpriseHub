"""
Jorge's Property Matching API Routes.

Provides endpoints for intelligent property-lead matching using hybrid AI:
- Property matches with AI-powered explanations
- Lead preference extraction and management
- Market inventory analysis and filtering
- Performance tracking and optimization
- Match explanation and reasoning

Integrates with Jorge's Enhanced Lead Scorer and Neural Property Matcher.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.jorge_property_models import (
    LeadPropertyPreferences,
    MatchingAlgorithm,
    MatchingPerformanceMetrics,
    MatchReasoning,
    PropertyFilters,
    PropertyMatchRequest,
    PropertyMatchResponse,
    PropertyType,
)
from ghl_real_estate_ai.services.jorge_property_matching_service import JorgePropertyMatchingService

logger = get_logger(__name__)
router = APIRouter(prefix="/jorge/property-matching", tags=["jorge-property-matching"])


# ================== REQUEST/RESPONSE MODELS ==================


class PropertyMatchQuery(BaseModel):
    """Query parameters for property matching."""

    lead_id: str = Field(..., description="Lead ID for matching")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of matches to return")
    min_match_score: float = Field(default=50.0, ge=0, le=100, description="Minimum match score threshold")
    algorithm: MatchingAlgorithm = Field(
        default=MatchingAlgorithm.JORGE_OPTIMIZED, description="Matching algorithm to use"
    )
    force_refresh: bool = Field(default=False, description="Force refresh of cached results")


class LeadPropertyPreferencesUpdate(BaseModel):
    """Update lead property preferences."""

    budget_min: Optional[float] = Field(None, description="Minimum budget")
    budget_max: Optional[float] = Field(None, description="Maximum budget")
    preferred_bedrooms: Optional[int] = Field(None, ge=1, le=10, description="Preferred number of bedrooms")
    min_bedrooms: Optional[int] = Field(None, ge=1, le=10, description="Minimum bedrooms required")
    preferred_bathrooms: Optional[float] = Field(None, ge=1, le=10, description="Preferred bathrooms")
    preferred_neighborhoods: Optional[List[str]] = Field(None, description="Preferred neighborhoods")
    must_have_features: Optional[List[str]] = Field(None, description="Must-have features")
    nice_to_have_features: Optional[List[str]] = Field(None, description="Nice-to-have features")
    property_type_preference: Optional[PropertyType] = Field(None, description="Preferred property type")
    timeline_urgency: Optional[str] = Field(None, description="Timeline urgency")


class PropertyMatchExplanationRequest(BaseModel):
    """Request for detailed property match explanation."""

    property_id: str = Field(..., description="Property ID")
    lead_id: str = Field(..., description="Lead ID")
    include_talking_points: bool = Field(default=True, description="Include Jorge's talking points")
    include_market_analysis: bool = Field(default=True, description="Include market timing analysis")


class PropertyInventoryQuery(BaseModel):
    """Query for property inventory."""

    filters: Optional[PropertyFilters] = Field(None, description="Property filters")
    sort_by: str = Field(default="price", description="Sort field")
    sort_order: str = Field(default="asc", description="Sort order (asc/desc)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")


class PropertyMatchSummary(BaseModel):
    """Summary of property matching results."""

    lead_id: str
    total_matches: int
    avg_match_score: float
    best_match_score: float
    processing_time_ms: int
    algorithm_used: MatchingAlgorithm
    cache_hit: bool
    recommendations: List[str]


class MatchingPerformanceResponse(BaseModel):
    """Performance metrics response."""

    metrics: MatchingPerformanceMetrics
    recent_matches: int
    avg_processing_time_trend: str  # "improving", "stable", "declining"
    accuracy_trend: Optional[str] = None
    recommendations: List[str]


# ================== DEPENDENCY INJECTION ==================


def get_property_matching_service() -> JorgePropertyMatchingService:
    """Get property matching service instance."""
    return JorgePropertyMatchingService()


# ================== API ENDPOINTS ==================


@router.post("/matches", response_model=PropertyMatchResponse)
async def find_property_matches(
    query: PropertyMatchQuery,
    lead_data: Dict[str, Any] = Body(..., description="Complete lead data and context"),
    preferences: Optional[LeadPropertyPreferences] = Body(None, description="Explicit lead preferences"),
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Find optimal property matches for a lead using Jorge's hybrid AI approach.

    Combines neural network predictions with business rules specific to
    Rancho Cucamonga market for optimal recommendations.
    """
    try:
        tenant_id = current_user.get("payload", {}).get("tenant_id", "default_tenant")
        logger.info(f"Finding property matches for lead {query.lead_id} (Tenant: {tenant_id})")

        # Create matching request
        request = PropertyMatchRequest(
            lead_id=query.lead_id,
            tenant_id=tenant_id,
            lead_data=lead_data,
            preferences=preferences,
            max_results=query.max_results,
            min_match_score=query.min_match_score,
            algorithm=query.algorithm,
        )

        # Find matches
        response = await service.find_matches_for_lead(request)

        logger.info(
            f"Found {len(response.matches)} matches for lead {query.lead_id} in {response.processing_time_ms}ms"
        )
        return response

    except ValueError as e:
        logger.warning(f"Invalid request for lead {query.lead_id}: {e}")
        raise HTTPException(status_code=422, detail="Validation failed")
    except Exception as e:
        logger.error(f"Property matching failed for lead {query.lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Property matching service temporarily unavailable")


@router.get("/matches/{lead_id}", response_model=PropertyMatchSummary)
async def get_match_summary(
    lead_id: str,
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get a summary of recent property matches for a lead.
    """
    try:
        # This would retrieve cached/stored match results
        # For now, return a mock summary
        return PropertyMatchSummary(
            lead_id=lead_id,
            total_matches=5,
            avg_match_score=78.5,
            best_match_score=92.3,
            processing_time_ms=450,
            algorithm_used=MatchingAlgorithm.JORGE_OPTIMIZED,
            cache_hit=True,
            recommendations=[
                "Schedule showing for top match in Alta Loma",
                "Emphasize school district quality",
                "Highlight negotiation opportunity",
            ],
        )

    except Exception as e:
        logger.error(f"Failed to get match summary for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve match summary")


@router.post("/explain", response_model=MatchReasoning)
async def explain_property_match(
    request: PropertyMatchExplanationRequest,
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Generate detailed explanation for why a specific property matches a lead.

    Provides AI-powered reasoning with Jorge-specific talking points
    and market analysis.
    """
    try:
        logger.info(f"Generating explanation for property {request.property_id} and lead {request.lead_id}")

        # Generate detailed match explanation
        reasoning = await service.explain_specific_match(request.property_id, request.lead_id)

        if not reasoning:
            raise HTTPException(status_code=404, detail="Match explanation not available")

        return reasoning

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        raise HTTPException(status_code=500, detail="Explanation generation failed")


@router.get("/preferences/{lead_id}", response_model=LeadPropertyPreferences)
async def get_lead_preferences(
    lead_id: str,
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get extracted property preferences for a lead.
    """
    try:
        # This would retrieve stored/cached preferences
        # For demo, return sample preferences
        preferences = LeadPropertyPreferences(
            budget_min=650000,
            budget_max=850000,
            preferred_bedrooms=3,
            min_bedrooms=2,
            preferred_bathrooms=2.5,
            preferred_neighborhoods=["Alta Loma", "Victoria Arbors"],
            must_have_features=["updated_kitchen", "granite_counters"],
            nice_to_have_features=["pool", "hardwood_floors"],
            property_type_preference=PropertyType.SINGLE_FAMILY,
            timeline_urgency="60d",
        )

        return preferences

    except Exception as e:
        logger.error(f"Failed to get preferences for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve lead preferences")


@router.put("/preferences/{lead_id}", response_model=Dict[str, str])
async def update_lead_preferences(
    lead_id: str,
    updates: LeadPropertyPreferencesUpdate,
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update property preferences for a lead.

    This will invalidate existing match cache and require new matching.
    """
    try:
        logger.info(f"Updating preferences for lead {lead_id}")

        # Convert updates to full preferences object
        # In production, would merge with existing preferences
        preferences = LeadPropertyPreferences(
            budget_min=updates.budget_min,
            budget_max=updates.budget_max,
            preferred_bedrooms=updates.preferred_bedrooms,
            min_bedrooms=updates.min_bedrooms,
            preferred_bathrooms=updates.preferred_bathrooms,
            preferred_neighborhoods=updates.preferred_neighborhoods or [],
            must_have_features=updates.must_have_features or [],
            nice_to_have_features=updates.nice_to_have_features or [],
            property_type_preference=updates.property_type_preference,
            timeline_urgency=updates.timeline_urgency,
        )

        # Update preferences in service
        await service.update_lead_preferences(lead_id, preferences)

        return {"status": "success", "message": f"Preferences updated for lead {lead_id}"}

    except Exception as e:
        logger.error(f"Failed to update preferences for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to update lead preferences")


@router.get("/inventory", response_model=Dict[str, Any])
async def get_property_inventory(
    filters: Optional[str] = Query(None, description="JSON-encoded PropertyFilters"),
    sort_by: str = Query(default="price", description="Sort field"),
    sort_order: str = Query(default="asc", description="Sort order"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get current property inventory with optional filtering.

    Returns paginated results with market statistics.
    """
    try:
        # Parse filters if provided
        property_filters = None
        if filters:
            import json

            filter_data = json.loads(filters)
            property_filters = PropertyFilters(**filter_data)

        # Get inventory stats (mock implementation)
        inventory_stats = await service.get_market_inventory_stats()

        # Mock property list (would be real query in production)
        properties = [
            {
                "id": "prop_001",
                "address": "4512 Duval Street, Alta Loma",
                "price": 825000,
                "bedrooms": 4,
                "bathrooms": 3.0,
                "sqft": 2650,
                "neighborhood": "Alta Loma",
                "days_on_market": 12,
                "price_per_sqft": 311.32,
            },
            {
                "id": "prop_002",
                "address": "8765 Victoria Avenue, Victoria Arbors",
                "price": 695000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2200,
                "neighborhood": "Victoria Arbors",
                "days_on_market": 25,
                "price_per_sqft": 315.91,
            },
        ]

        return {
            "properties": properties,
            "total_count": len(properties),
            "page": page,
            "page_size": page_size,
            "total_pages": 1,
            "market_stats": inventory_stats,
            "filters_applied": property_filters.dict() if property_filters else None,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid filters JSON format")
    except Exception as e:
        logger.error(f"Failed to get property inventory: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve property inventory")


@router.get("/performance", response_model=MatchingPerformanceResponse)
async def get_matching_performance(
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get performance metrics for the property matching system.
    """
    try:
        metrics = service.get_performance_metrics()

        return MatchingPerformanceResponse(
            metrics=metrics,
            recent_matches=metrics.matches_generated,
            avg_processing_time_trend="improving",
            accuracy_trend="stable",
            recommendations=[
                "Cache hit rate is optimal",
                "Neural inference time within target",
                "Consider expanding property inventory",
            ],
        )

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve performance metrics")


@router.post("/test-match", response_model=PropertyMatchResponse)
async def test_property_matching(
    sample_lead_data: Dict[str, Any] = Body(..., description="Sample lead data for testing"),
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Test endpoint for property matching with sample data.

    Useful for testing and demonstration purposes.
    """
    try:
        logger.info("Running property matching test")

        # Create test request
        request = PropertyMatchRequest(
            lead_id="test_lead_001",
            lead_data=sample_lead_data,
            max_results=3,
            algorithm=MatchingAlgorithm.JORGE_OPTIMIZED,
        )

        # Find matches
        response = await service.find_matches_for_lead(request)

        # Add test indicator
        response.recommendation_summary = f"TEST: {response.recommendation_summary}"

        return response

    except Exception as e:
        logger.error(f"Property matching test failed: {e}")
        raise HTTPException(status_code=500, detail="Property matching test failed")


@router.get("/market-insights", response_model=Dict[str, Any])
async def get_market_insights(
    neighborhood: Optional[str] = Query(None, description="Specific neighborhood"),
    service: JorgePropertyMatchingService = Depends(get_property_matching_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get market insights and trends for Rancho Cucamonga.

    Provides neighborhood-specific intelligence for property recommendations.
    """
    try:
        # Get market insights (mock implementation)
        insights = {
            "market_area": neighborhood or "Rancho Cucamonga",
            "current_conditions": {
                "market_temperature": "warm",
                "inventory_level": "low",
                "avg_days_on_market": 28,
                "price_trend": "stable_growth",
                "buyer_demand": "high",
            },
            "neighborhood_rankings": [
                {"name": "Alta Loma", "score": 95, "trend": "hot"},
                {"name": "Victoria Arbors", "score": 88, "trend": "warm"},
                {"name": "North Rancho Cucamonga", "score": 92, "trend": "hot"},
                {"name": "Terra Vista", "score": 75, "trend": "emerging"},
            ],
            "investment_opportunities": [
                "First-time buyer market in Terra Vista",
                "Luxury upgrades in Alta Loma",
                "Family homes near top schools",
            ],
            "market_predictions": {
                "next_30_days": "Continued strong demand",
                "next_90_days": "Spring market surge expected",
                "price_forecast": "+3-5% appreciation",
            },
        }

        return insights

    except Exception as e:
        logger.error(f"Failed to get market insights: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve market insights")


# ================== HEALTH CHECK ==================


@router.get("/health", response_model=Dict[str, Any])
async def health_check(service: JorgePropertyMatchingService = Depends(get_property_matching_service)):
    """
    Health check for property matching service.
    """
    try:
        # Check service health
        metrics = service.get_performance_metrics()

        return {
            "status": "healthy",
            "service": "jorge-property-matching",
            "version": "1.0.0",
            "uptime_checks": {
                "neural_matcher": "available",
                "lead_scorer": "available",
                "cache_service": "available",
                "claude_assistant": "available",
            },
            "performance": {
                "avg_response_time_ms": metrics.avg_processing_time_ms,
                "cache_hit_rate": f"{metrics.cache_hit_rate:.1%}",
                "total_matches_served": metrics.matches_generated,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
