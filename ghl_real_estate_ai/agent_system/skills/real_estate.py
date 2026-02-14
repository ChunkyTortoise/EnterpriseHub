"""
Real Estate Ontario Mills Skills.
Wraps core real estate services into standardized Agent Skills.
"""

from typing import Any, Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

from .base import skill

logger = get_logger(__name__)

# Initialize singleton-like service wrappers
_property_matcher = None
_analytics_service = None


def get_matcher():
    global _property_matcher
    if _property_matcher is None:
        _property_matcher = PropertyMatcher()
    return _property_matcher


def get_analytics():
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


@skill(name="search_properties", tags=["real_estate", "search"])
def search_properties(
    budget: float, location: str, bedrooms: int = 0, min_score: float = 0.5, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for properties matching specific criteria.

    Args:
        budget: Maximum budget in USD.
        location: Neighborhood or city name.
        bedrooms: Minimum number of bedrooms.
        min_score: Minimum match score (0.0 to 1.0).
        limit: Maximum number of results to return.
    """
    matcher = get_matcher()
    preferences = {"budget": budget, "location": location, "bedrooms": bedrooms}
    # find_matches is synchronous in current implementation
    matches = matcher.find_matches(preferences, limit=limit, min_score=min_score)
    return matches


@skill(name="analyze_lead_behavior", tags=["real_estate", "analytics"])
async def analyze_lead_behavior(lead_id: str) -> Dict[str, Any]:
    """
    Analyzes a lead's behavioral patterns and returns insights.

    Args:
        lead_id: Unique identifier for the lead.
    """
    analytics = get_analytics()
    # Mocking behavioral analysis based on analytics service capabilities
    # In a full implementation, this would query the DB for lead activity
    return {
        "lead_id": lead_id,
        "engagement_score": 0.85,
        "preferred_neighborhoods": ["Rancho Cucamonga", "Round Rock"],
        "price_sensitivity": "medium",
        "last_active": "2026-01-19T14:30:00Z",
    }


@skill(name="generate_property_pitch", tags=["real_estate", "content"])
async def generate_property_pitch(property_id: str, lead_preferences: Dict[str, Any]) -> str:
    """
    Generates a personalized real estate pitch for a specific property and lead.

    Args:
        property_id: ID of the property to pitch.
        lead_preferences: Dictionary of lead's preferences (budget, beds, etc.)
    """
    matcher = get_matcher()
    # Find the property in the cached listings
    listings = matcher.listings
    target_property = next((p for p in listings if p.get("id") == property_id), None)

    if not target_property:
        # Fallback to a generic pitch if property not found
        return "This property represents a unique investment opportunity aligned with your stated goals."

    return await matcher.agentic_explain_match(target_property, lead_preferences)
