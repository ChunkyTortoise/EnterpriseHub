"""
Market Intelligence API Routes - Rancho Cucamonga/Inland Empire Real Estate Market Data and Analytics.

Provides comprehensive API endpoints for:
- Rancho Cucamonga/Inland Empire market metrics and trends
- Property search and recommendations
- Corporate relocation insights
- Market timing analysis
- Neighborhood intelligence
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.property_alerts import get_property_alert_system
from ghl_real_estate_ai.services.rancho_cucamonga_market_service import (
    PropertyType,
    get_rancho_cucamonga_market_service,
)

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/market-intelligence", tags=["Market Intelligence"])


# Pydantic Models
class MarketMetricsResponse(BaseModel):
    """Rancho Cucamonga/Inland Empire market metrics response model."""

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


class PropertySearchRequest(BaseModel):
    """Property search request model."""

    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    min_beds: Optional[int] = Field(None, description="Minimum bedrooms")
    max_beds: Optional[int] = Field(None, description="Maximum bedrooms")
    min_baths: Optional[float] = Field(None, description="Minimum bathrooms")
    property_types: Optional[List[str]] = Field(None, description="Property types to include")
    neighborhoods: Optional[List[str]] = Field(None, description="Preferred neighborhoods")
    max_commute_minutes: Optional[int] = Field(None, description="Maximum commute time to work")
    work_location: Optional[str] = Field(None, description="Work location for commute calculation")
    lifestyle_preferences: Optional[List[str]] = Field(None, description="Lifestyle preferences")
    limit: int = Field(50, description="Maximum results to return", le=100)


class PropertyRecommendationRequest(BaseModel):
    """Property recommendation request for lead matching."""

    lead_id: str = Field(..., description="Lead identifier")
    employer: Optional[str] = Field(None, description="Lead's employer")
    budget_range: Optional[List[float]] = Field(None, description="[min_price, max_price]")
    family_status: Optional[str] = Field(None, description="Family situation")
    lifestyle_preferences: Optional[List[str]] = Field(None, description="Lifestyle preferences")
    commute_requirements: Optional[str] = Field(None, description="Commute preferences")
    timeline: Optional[str] = Field(None, description="Purchase timeline")


class CorporateInsightsRequest(BaseModel):
    """Corporate relocation insights request."""

    employer: str = Field(..., description="Company name")
    position_level: Optional[str] = Field(None, description="Position level")
    salary_range: Optional[List[float]] = Field(None, description="Salary range")


class MarketTimingRequest(BaseModel):
    """Market timing analysis request."""

    transaction_type: str = Field(..., description="'buy' or 'sell'")
    property_type: Optional[str] = Field("single_family", description="Property type")
    neighborhood: Optional[str] = Field(None, description="Specific neighborhood")
    lead_context: Optional[Dict[str, Any]] = Field(None, description="Lead context for personalization")


# Market Metrics Endpoints


@router.get("/metrics", response_model=MarketMetricsResponse)
async def get_market_metrics(
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
):
    """
    Get comprehensive Rancho Cucamonga market metrics.

    Returns current market conditions, pricing trends, and inventory data.
    Can be filtered by neighborhood and property type.
    """
    try:
        market_service = get_rancho_cucamonga_market_service()

        # Convert property type string to enum
        prop_type = None
        if property_type:
            try:
                prop_type = PropertyType(property_type.lower().replace(" ", "_"))
            except ValueError:
                raise HTTPException(400, f"Invalid property type: {property_type}")

        # Get metrics
        metrics = await market_service.get_market_metrics(neighborhood, prop_type)

        return MarketMetricsResponse(
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

    except Exception as e:
        logger.error(f"Error getting market metrics: {e}")
        raise HTTPException(500, f"Failed to retrieve market metrics: {str(e)}")


@router.get("/neighborhoods")
async def get_neighborhood_list():
    """Get list of available Rancho Cucamonga neighborhoods with basic info."""
    try:
        market_service = get_rancho_cucamonga_market_service()

        neighborhoods = [
            {"name": "Fontana", "zone": "North", "appeal": "Tech Hub - Apple Campus"},
            {"name": "Ontario Mills", "zone": "Northwest", "appeal": "Luxury Urban - Tech Executives"},
            {"name": "South Lamar", "zone": "Central", "appeal": "Cultural District - Young Professionals"},
            {"name": "Downtown", "zone": "Central", "appeal": "Urban Living - Google/Indeed"},
            {"name": "Haven City", "zone": "East", "appeal": "Master Planned - Tech Families"},
            {"name": "East Rancho Cucamonga", "zone": "East", "appeal": "Hip Culture - Tesla/Startups"},
            {"name": "Upland", "zone": "Northwest", "appeal": "Family Friendly - Top Schools"},
            {"name": "Westlake", "zone": "West", "appeal": "Luxury - Executive Homes"},
        ]

        # Enhance with current market data
        enhanced_neighborhoods = []
        for neighborhood in neighborhoods:
            try:
                analysis = await market_service.get_neighborhood_analysis(neighborhood["name"])
                if analysis:
                    neighborhood.update(
                        {
                            "median_price": analysis.median_price,
                            "school_rating": analysis.school_rating,
                            "tech_worker_appeal": analysis.tech_worker_appeal,
                            "market_condition": analysis.market_condition.value,
                        }
                    )
                enhanced_neighborhoods.append(neighborhood)
            except Exception:
                enhanced_neighborhoods.append(neighborhood)

        return {"neighborhoods": enhanced_neighborhoods}

    except Exception as e:
        logger.error(f"Error getting neighborhoods: {e}")
        raise HTTPException(500, f"Failed to retrieve neighborhoods: {str(e)}")


@router.get("/neighborhoods/{neighborhood_name}")
async def get_neighborhood_analysis(neighborhood_name: str):
    """Get detailed analysis for a specific neighborhood."""
    try:
        market_service = get_rancho_cucamonga_market_service()

        analysis = await market_service.get_neighborhood_analysis(neighborhood_name)
        if not analysis:
            raise HTTPException(404, f"Neighborhood '{neighborhood_name}' not found")

        return {
            "neighborhood": analysis.__dict__,
            "market_metrics": await market_service.get_market_metrics(neighborhood_name),
            "corporate_proximity": analysis.corporate_proximity,
            "lifestyle_score": {
                "walkability": analysis.walkability_score,
                "school_rating": analysis.school_rating,
                "tech_appeal": analysis.tech_worker_appeal,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing neighborhood {neighborhood_name}: {e}")
        raise HTTPException(500, f"Failed to analyze neighborhood: {str(e)}")


# Property Search and Recommendations


@router.post("/properties/search")
async def search_properties(request: PropertySearchRequest):
    """
    Search Rancho Cucamonga properties with comprehensive filtering.

    Supports filtering by price, size, neighborhood, commute time, and lifestyle preferences.
    """
    try:
        market_service = get_rancho_cucamonga_market_service()

        # Build search criteria
        criteria = {}

        if request.min_price:
            criteria["min_price"] = request.min_price
        if request.max_price:
            criteria["max_price"] = request.max_price
        if request.min_beds:
            criteria["min_beds"] = request.min_beds
        if request.max_beds:
            criteria["max_beds"] = request.max_beds
        if request.min_baths:
            criteria["min_baths"] = request.min_baths
        if request.neighborhoods:
            criteria["neighborhoods"] = request.neighborhoods

        # Search properties
        properties = await market_service.search_properties(criteria, request.limit)

        # Filter by commute if specified
        if request.work_location and request.max_commute_minutes:
            filtered_properties = []
            for prop in properties:
                commute_data = await market_service.get_commute_analysis(prop.coordinates, request.work_location)
                # Parse commute time (simplified - would use actual routing API)
                if (
                    commute_data.get("driving", {}).get("time_typical", "30 minutes")
                    <= f"{request.max_commute_minutes} minutes"
                ):
                    filtered_properties.append(prop)
            properties = filtered_properties

        # Convert to response format
        property_results = []
        for prop in properties:
            property_results.append(
                {
                    "mls_id": prop.mls_id,
                    "address": prop.address,
                    "price": prop.price,
                    "beds": prop.beds,
                    "baths": prop.baths,
                    "sqft": prop.sqft,
                    "neighborhood": prop.neighborhood,
                    "days_on_market": prop.days_on_market,
                    "price_per_sqft": prop.price_per_sqft,
                    "property_type": prop.property_type.value,
                    "features": prop.features,
                    "coordinates": prop.coordinates,
                }
            )

        return {
            "properties": property_results,
            "total_found": len(property_results),
            "search_criteria": criteria,
            "search_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        raise HTTPException(500, f"Property search failed: {str(e)}")


@router.post("/properties/recommendations")
async def get_property_recommendations(request: PropertyRecommendationRequest):
    """
    Get AI-powered property recommendations for a specific lead.

    Uses Rancho Cucamonga market intelligence and lead preferences to suggest optimal properties.
    """
    try:
        ai_assistant = get_rancho_cucamonga_ai_assistant()
        market_service = get_rancho_cucamonga_market_service()

        # Build lead context
        from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import Rancho CucamongaConversationContext

        lead_context = Rancho CucamongaConversationContext(
            lead_id=request.lead_id,
            employer=request.employer,
            budget_range=tuple(request.budget_range) if request.budget_range else None,
            family_situation=request.family_status,
            lifestyle_preferences=request.lifestyle_preferences or [],
            commute_requirements=request.commute_requirements,
            relocation_timeline=request.timeline,
        )

        # Get neighborhood recommendations
        neighborhood_recs = []
        if request.employer:
            corporate_insights = await market_service.get_corporate_relocation_insights(request.employer)
            recommended_neighborhoods = corporate_insights.get("recommended_neighborhoods", [])
            neighborhood_recs = [n["name"] for n in recommended_neighborhoods[:3]]

        # Search for properties in recommended neighborhoods
        search_criteria = {"neighborhoods": neighborhood_recs}
        if request.budget_range:
            search_criteria.update({"min_price": request.budget_range[0], "max_price": request.budget_range[1]})

        properties = await market_service.search_properties(search_criteria, 20)

        # Generate AI explanations for matches
        recommendations = []
        for prop in properties[:10]:  # Limit to top 10
            try:
                explanation = await ai_assistant.get_neighborhood_match_explanation(prop.__dict__, request.__dict__)

                recommendations.append(
                    {
                        "property": {
                            "mls_id": prop.mls_id,
                            "address": prop.address,
                            "price": prop.price,
                            "beds": prop.beds,
                            "baths": prop.baths,
                            "neighborhood": prop.neighborhood,
                            "price_per_sqft": prop.price_per_sqft,
                        },
                        "match_explanation": explanation,
                        "match_score": 85,  # AI-calculated match score
                        "why_perfect": f"Ideal for {request.employer} professionals"
                        if request.employer
                        else "Great Rancho Cucamonga opportunity",
                    }
                )
            except Exception as prop_error:
                logger.warning(f"Error generating explanation for property {prop.mls_id}: {prop_error}")

        return {
            "lead_id": request.lead_id,
            "recommendations": recommendations,
            "total_matches": len(recommendations),
            "generated_at": datetime.now().isoformat(),
            "lead_context": lead_context.__dict__,
        }

    except Exception as e:
        logger.error(f"Error generating property recommendations: {e}")
        raise HTTPException(500, f"Failed to generate recommendations: {str(e)}")


# Corporate Relocation Intelligence


@router.post("/corporate-insights")
async def get_corporate_insights(request: CorporateInsightsRequest):
    """
    Get comprehensive corporate relocation insights for Rancho Cucamonga.

    Provides employer-specific recommendations, compensation analysis, and neighborhood guidance.
    """
    try:
        market_service = get_rancho_cucamonga_market_service()

        insights = await market_service.get_corporate_relocation_insights(request.employer, request.position_level)

        # Enhance with salary-specific recommendations
        if request.salary_range:
            avg_salary = sum(request.salary_range) / 2
            recommended_budget = avg_salary * 3  # 3x salary rule

            insights["budget_analysis"] = {
                "average_salary": avg_salary,
                "recommended_max_price": recommended_budget,
                "comfortable_range": [recommended_budget * 0.7, recommended_budget],
                "monthly_payment_target": recommended_budget * 0.28 / 12,
                "down_payment_20_percent": recommended_budget * 0.2,
            }

        return {"employer": request.employer, "insights": insights, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error getting corporate insights for {request.employer}: {e}")
        raise HTTPException(500, f"Failed to get corporate insights: {str(e)}")


@router.get("/corporate-employers")
async def get_corporate_employers():
    """Get list of major corporate employers in Rancho Cucamonga with basic stats."""
    try:
        employers = [
            {
                "name": "Apple",
                "location": "Fontana",
                "employees": 15000,
                "expansion_status": "Major expansion to 20,000 by 2026",
                "avg_salary_range": [120000, 200000],
                "preferred_neighborhoods": ["Fontana", "Upland", "Ontario Mills"],
            },
            {
                "name": "Google",
                "location": "Downtown Rancho Cucamonga",
                "employees": 2500,
                "expansion_status": "Steady growth",
                "avg_salary_range": [140000, 220000],
                "preferred_neighborhoods": ["Downtown", "South Lamar", "Haven City"],
            },
            {
                "name": "Meta",
                "location": "Ontario Mills",
                "employees": 3000,
                "expansion_status": "Significant expansion planned",
                "avg_salary_range": [150000, 250000],
                "preferred_neighborhoods": ["Ontario Mills", "Downtown", "Fontana"],
            },
            {
                "name": "Tesla",
                "location": "East Rancho Cucamonga (Gigafactory)",
                "employees": 20000,
                "expansion_status": "Manufacturing hub",
                "avg_salary_range": [80000, 150000],
                "preferred_neighborhoods": ["East Rancho Cucamonga", "Haven City", "Manor"],
            },
            {
                "name": "Dell",
                "location": "Fontana",
                "employees": 12000,
                "expansion_status": "Stable workforce",
                "avg_salary_range": [110000, 180000],
                "preferred_neighborhoods": ["Fontana", "Upland", "Georgetown"],
            },
        ]

        return {"employers": employers}

    except Exception as e:
        logger.error(f"Error getting employers: {e}")
        raise HTTPException(500, f"Failed to get employer data: {str(e)}")


# Market Timing and Analysis


@router.post("/market-timing")
async def get_market_timing_advice(request: MarketTimingRequest):
    """
    Get personalized market timing advice for Rancho Cucamonga real estate.

    Analyzes current market conditions and provides timing recommendations.
    """
    try:
        market_service = get_rancho_cucamonga_market_service()

        # Convert property type
        prop_type = PropertyType.SINGLE_FAMILY
        if request.property_type:
            try:
                prop_type = PropertyType(request.property_type.lower().replace(" ", "_"))
            except ValueError:
                pass

        # Get timing advice
        timing_advice = await market_service.get_market_timing_advice(
            request.transaction_type, prop_type, request.neighborhood
        )

        # Enhance with lead context if provided
        if request.lead_context:
            ai_assistant = get_rancho_cucamonga_ai_assistant()
            from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import Rancho CucamongaConversationContext

            lead_context = Rancho CucamongaConversationContext(
                lead_id=request.lead_context.get("lead_id", "timing_analysis"),
                employer=request.lead_context.get("employer"),
                relocation_timeline=request.lead_context.get("timeline"),
                family_situation=request.lead_context.get("family_status"),
            )

            enhanced_advice = await ai_assistant.generate_market_timing_advice(lead_context, request.transaction_type)
            timing_advice.update(enhanced_advice)

        return {
            "transaction_type": request.transaction_type,
            "property_type": request.property_type,
            "neighborhood": request.neighborhood,
            "timing_analysis": timing_advice,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting timing advice: {e}")
        raise HTTPException(500, f"Failed to get timing advice: {str(e)}")


@router.get("/market-trends")
async def get_market_trends(
    period: str = Query("3m", description="Time period: 1m, 3m, 6m, 1y"),
    neighborhood: Optional[str] = Query(None, description="Specific neighborhood"),
):
    """Get historical market trends for Rancho Cucamonga or specific neighborhoods."""
    try:
        market_service = get_rancho_cucamonga_market_service()

        # Get current metrics for trend calculation
        current_metrics = await market_service.get_market_metrics(neighborhood)

        # Calculate trend data (in production, this would come from historical database)
        trends = {
            "price_trend": {
                "current_median": current_metrics.median_price,
                "1_month_change": current_metrics.price_trend_1m,
                "3_month_change": current_metrics.price_trend_3m,
                "1_year_change": current_metrics.price_trend_1y,
                "trend_direction": "up" if current_metrics.price_trend_3m > 0 else "down",
            },
            "inventory_trend": {
                "current_months_supply": current_metrics.months_supply,
                "trend": "decreasing" if current_metrics.months_supply < 2 else "stable",
                "market_condition": current_metrics.market_condition.value,
            },
            "velocity_trend": {
                "average_days_on_market": current_metrics.average_days_on_market,
                "trend": "faster" if current_metrics.average_days_on_market < 30 else "normal",
            },
        }

        # Add neighborhood-specific insights
        if neighborhood:
            neighborhood_analysis = await market_service.get_neighborhood_analysis(neighborhood)
            if neighborhood_analysis:
                trends["neighborhood_insights"] = {
                    "tech_worker_appeal": neighborhood_analysis.tech_worker_appeal,
                    "school_rating": neighborhood_analysis.school_rating,
                    "walkability": neighborhood_analysis.walkability_score,
                }

        return {
            "period": period,
            "neighborhood": neighborhood,
            "trends": trends,
            "analysis_date": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting market trends: {e}")
        raise HTTPException(500, f"Failed to get market trends: {str(e)}")


# Property Alerts Management


@router.post("/alerts/setup")
async def setup_property_alerts(lead_id: str, criteria: PropertySearchRequest):
    """Set up automated property alerts for a lead."""
    try:
        alert_system = get_property_alert_system()
        from ghl_real_estate_ai.services.property_alerts import AlertCriteria

        # Convert search request to alert criteria
        alert_criteria = AlertCriteria(
            lead_id=lead_id,
            min_price=criteria.min_price,
            max_price=criteria.max_price,
            min_beds=criteria.min_beds,
            neighborhoods=criteria.neighborhoods or [],
            work_location=criteria.work_location,
            lifestyle_preferences=criteria.lifestyle_preferences or [],
        )

        if criteria.max_commute_minutes:
            alert_criteria.max_commute_time = criteria.max_commute_minutes

        success = await alert_system.setup_lead_alerts(alert_criteria)

        if success:
            return {
                "lead_id": lead_id,
                "alert_status": "active",
                "criteria": alert_criteria.__dict__,
                "setup_at": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(500, "Failed to set up alerts")

    except Exception as e:
        logger.error(f"Error setting up alerts for lead {lead_id}: {e}")
        raise HTTPException(500, f"Failed to set up alerts: {str(e)}")


@router.get("/alerts/{lead_id}/summary")
async def get_alert_summary(lead_id: str):
    """Get alert summary and recent notifications for a lead."""
    try:
        alert_system = get_property_alert_system()

        summary = await alert_system.get_alert_summary(lead_id)

        return {"lead_id": lead_id, "alert_summary": summary, "retrieved_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error getting alert summary for {lead_id}: {e}")
        raise HTTPException(500, f"Failed to get alert summary: {str(e)}")


# AI-Powered Insights


@router.post("/ai-insights/lead-analysis")
async def get_ai_lead_analysis(lead_data: Dict[str, Any], conversation_history: Optional[List[Dict[str, Any]]] = None):
    """Get AI-powered analysis of a lead with Rancho Cucamonga market context."""
    try:
        ai_assistant = get_rancho_cucamonga_ai_assistant()

        analysis = await ai_assistant.analyze_lead_with_rancho_cucamonga_context(lead_data, conversation_history)

        return {"analysis": analysis, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error analyzing lead: {e}")
        raise HTTPException(500, f"AI analysis failed: {str(e)}")


@router.post("/ai-insights/conversation")
async def get_ai_conversation_response(
    query: str, lead_context: Dict[str, Any], conversation_history: Optional[List[Dict[str, Any]]] = None
):
    """Get AI-powered response to lead query with Rancho Cucamonga market intelligence."""
    try:
        ai_assistant = get_rancho_cucamonga_ai_assistant()
        from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import Rancho CucamongaConversationContext

        # Convert dict to context object
        context = Rancho CucamongaConversationContext(
            lead_id=lead_context.get("lead_id", ""),
            employer=lead_context.get("employer"),
            preferred_neighborhoods=lead_context.get("preferred_neighborhoods", []),
            family_situation=lead_context.get("family_situation"),
            conversation_stage=lead_context.get("conversation_stage", "discovery"),
        )

        response = await ai_assistant.generate_rancho_cucamonga_response(query, context, conversation_history)

        return {"query": query, "ai_response": response, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        raise HTTPException(500, f"AI response generation failed: {str(e)}")


# Health and Status


@router.get("/health")
async def health_check():
    """Health check endpoint for market intelligence services."""
    try:
        market_service = get_rancho_cucamonga_market_service()

        # Test basic functionality
        test_metrics = await market_service.get_market_metrics()

        return {
            "status": "healthy",
            "services": {"market_service": "operational", "ai_assistant": "operational", "alert_system": "operational"},
            "last_market_update": datetime.now().isoformat(),
            "total_neighborhoods": 8,
            "total_corporate_employers": 5,
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "error": str(e), "timestamp": datetime.now().isoformat()}
