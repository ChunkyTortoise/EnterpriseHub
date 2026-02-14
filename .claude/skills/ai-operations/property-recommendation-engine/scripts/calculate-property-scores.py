#!/usr/bin/env python3
"""
Property Score Calculator for Property Recommendation Engine

Calculates match scores for properties against lead preferences
using multi-dimensional scoring algorithm.

Usage:
    python calculate-property-scores.py --lead-id <id> --limit 10
    python calculate-property-scores.py --preferences <prefs.json> --listings <listings.json>

Zero-Context Execution:
    This script runs independently without loading into Claude's context.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import math


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown by category."""
    budget_fit: float
    location_match: float
    features_match: float
    lifestyle_match: float
    behavioral_boost: float


@dataclass
class PropertyScore:
    """Complete property match score."""
    property_id: str
    address: str
    price: int
    match_score: float
    score_breakdown: ScoreBreakdown
    match_reasoning: str
    highlights: List[str]
    potential_concerns: List[str]
    rank: int


@dataclass
class RecommendationResult:
    """Complete recommendation result."""
    lead_id: str
    preferences_used: Dict[str, Any]
    properties_scored: int
    recommendations: List[PropertyScore]
    generated_at: str


def load_preferences(lead_id: str) -> Dict[str, Any]:
    """Load lead preferences from data sources."""
    try:
        from ghl_real_estate_ai.services.memory_service import MemoryService
        memory = MemoryService()
        return memory.get_lead_preferences(lead_id)
    except ImportError:
        # Sample preferences for testing
        return {
            "budget": 750000,
            "budget_flexibility": "flexible",  # firm, flexible, stretch
            "locations": ["Teravista", "Round Rock", "Pflugerville"],
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft_min": 2500,
            "garage": 2,
            "pool": False,
            "school_rating_min": 7,
            "commute_to": "Downtown Rancho Cucamonga",
            "commute_max_minutes": 45,
            "style_preference": "modern",
            "yard_size": "medium"
        }


def load_listings(file_path: str = None) -> List[Dict[str, Any]]:
    """Load property listings."""
    if file_path:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data.get("listings", data)

    try:
        from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
        matcher = PropertyMatcher()
        return matcher.listings
    except ImportError:
        # Sample listings for testing
        return [
            {
                "property_id": "prop_001",
                "address": {"street": "123 Teravista Pkwy", "neighborhood": "Teravista", "city": "Round Rock"},
                "price": 725000,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2800,
                "garage": 2,
                "pool": False,
                "year_built": 2018,
                "school_rating": 8,
                "style": "modern",
                "features": ["open floor plan", "updated kitchen", "large backyard"]
            },
            {
                "property_id": "prop_002",
                "address": {"street": "456 Round Rock Ave", "neighborhood": "Round Rock", "city": "Round Rock"},
                "price": 680000,
                "bedrooms": 4,
                "bathrooms": 2.5,
                "sqft": 2400,
                "garage": 2,
                "pool": False,
                "year_built": 2015,
                "school_rating": 7,
                "style": "traditional",
                "features": ["corner lot", "covered patio", "granite counters"]
            },
            {
                "property_id": "prop_003",
                "address": {"street": "789 Pflugerville Dr", "neighborhood": "Pflugerville", "city": "Pflugerville"},
                "price": 695000,
                "bedrooms": 5,
                "bathrooms": 3.5,
                "sqft": 3100,
                "garage": 3,
                "pool": True,
                "year_built": 2020,
                "school_rating": 8,
                "style": "modern",
                "features": ["pool", "game room", "chef's kitchen", "home office"]
            },
            {
                "property_id": "prop_004",
                "address": {"street": "321 Manor Rd", "neighborhood": "Manor", "city": "Manor"},
                "price": 550000,
                "bedrooms": 4,
                "bathrooms": 2,
                "sqft": 2200,
                "garage": 2,
                "pool": False,
                "year_built": 2012,
                "school_rating": 6,
                "style": "ranch",
                "features": ["single story", "large lot", "workshop"]
            },
            {
                "property_id": "prop_005",
                "address": {"street": "555 Rancho Cucamonga Blvd", "neighborhood": "Downtown", "city": "Rancho Cucamonga"},
                "price": 895000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 2000,
                "garage": 1,
                "pool": False,
                "year_built": 2022,
                "school_rating": 7,
                "style": "modern",
                "features": ["walkable", "rooftop deck", "smart home"]
            }
        ]


def calculate_budget_score(price: int, preferences: Dict) -> Tuple[float, str]:
    """
    Calculate budget fit score.

    Returns score (0-1) and reasoning.
    """
    budget = preferences.get("budget", float("inf"))
    flexibility = preferences.get("budget_flexibility", "firm")

    if price <= budget:
        # Under budget
        under_percent = (budget - price) / budget * 100
        if under_percent > 10:
            score = 1.0
            reason = f"${under_percent:.0f}% under budget - excellent value"
        else:
            score = 0.95
            reason = "Within budget"
    else:
        # Over budget
        over_percent = (price - budget) / budget * 100

        if flexibility == "stretch" and over_percent <= 15:
            score = 0.7 - (over_percent / 100)
            reason = f"${over_percent:.0f}% over budget but within stretch range"
        elif flexibility == "flexible" and over_percent <= 10:
            score = 0.75 - (over_percent / 100)
            reason = f"Slightly over budget (${price - budget:,})"
        elif over_percent <= 5:
            score = 0.6
            reason = f"Just over budget by ${price - budget:,}"
        else:
            score = max(0, 0.5 - (over_percent / 100))
            reason = f"Over budget by ${price - budget:,}"

    return round(score, 2), reason


def calculate_location_score(property_loc: Dict, preferences: Dict) -> Tuple[float, str]:
    """
    Calculate location match score.

    Returns score (0-1) and reasoning.
    """
    preferred_locations = [loc.lower() for loc in preferences.get("locations", [])]
    property_neighborhood = property_loc.get("neighborhood", "").lower()
    property_city = property_loc.get("city", "").lower()

    if property_neighborhood in preferred_locations:
        score = 1.0
        reason = f"In preferred area: {property_loc.get('neighborhood')}"
    elif property_city in preferred_locations:
        score = 0.85
        reason = f"In preferred city: {property_loc.get('city')}"
    elif any(loc in property_neighborhood for loc in preferred_locations):
        score = 0.75
        reason = "Near preferred location"
    else:
        score = 0.4
        reason = f"Outside preferred areas ({property_loc.get('neighborhood')})"

    return round(score, 2), reason


def calculate_features_score(property_data: Dict, preferences: Dict) -> Tuple[float, str, List[str], List[str]]:
    """
    Calculate features match score.

    Returns score (0-1), reasoning, highlights, and concerns.
    """
    scores = []
    highlights = []
    concerns = []

    # Bedrooms
    req_beds = preferences.get("bedrooms", 0)
    prop_beds = property_data.get("bedrooms", 0)
    if prop_beds >= req_beds:
        scores.append(1.0)
        if prop_beds > req_beds:
            highlights.append(f"Extra bedroom ({prop_beds} vs {req_beds} needed)")
    else:
        scores.append(prop_beds / req_beds if req_beds > 0 else 0)
        concerns.append(f"Only {prop_beds} bedrooms (need {req_beds})")

    # Bathrooms
    req_baths = preferences.get("bathrooms", 0)
    prop_baths = property_data.get("bathrooms", 0)
    if prop_baths >= req_baths:
        scores.append(1.0)
        if prop_baths > req_baths:
            highlights.append(f"Extra bathroom(s)")
    else:
        scores.append(prop_baths / req_baths if req_baths > 0 else 0)
        concerns.append(f"Only {prop_baths} bathrooms (need {req_baths})")

    # Square footage
    req_sqft = preferences.get("sqft_min", 0)
    prop_sqft = property_data.get("sqft", 0)
    if req_sqft > 0:
        if prop_sqft >= req_sqft:
            scores.append(1.0)
            if prop_sqft > req_sqft * 1.1:
                highlights.append(f"Spacious {prop_sqft:,} sqft")
        else:
            scores.append(prop_sqft / req_sqft)
            concerns.append(f"Only {prop_sqft:,} sqft (want {req_sqft:,})")

    # Garage
    req_garage = preferences.get("garage", 0)
    prop_garage = property_data.get("garage", 0)
    if req_garage > 0:
        if prop_garage >= req_garage:
            scores.append(1.0)
        else:
            scores.append(prop_garage / req_garage if req_garage > 0 else 0)
            concerns.append(f"Only {prop_garage}-car garage")

    # Pool preference
    want_pool = preferences.get("pool", False)
    has_pool = property_data.get("pool", False)
    if want_pool and has_pool:
        scores.append(1.0)
        highlights.append("Has pool as requested")
    elif not want_pool and not has_pool:
        scores.append(1.0)
    elif want_pool and not has_pool:
        scores.append(0.7)  # Missing preferred feature
    # If they don't want pool but has one - neutral

    # Calculate average
    avg_score = sum(scores) / len(scores) if scores else 0.5

    # Generate reasoning
    if avg_score >= 0.9:
        reason = "Excellent feature match"
    elif avg_score >= 0.7:
        reason = "Good feature alignment with minor gaps"
    elif avg_score >= 0.5:
        reason = "Partial feature match - some compromises needed"
    else:
        reason = "Significant feature gaps"

    return round(avg_score, 2), reason, highlights, concerns


def calculate_lifestyle_score(property_data: Dict, preferences: Dict) -> Tuple[float, str]:
    """
    Calculate lifestyle match score (schools, commute, style).

    Returns score (0-1) and reasoning.
    """
    scores = []
    reasons = []

    # School rating
    min_school = preferences.get("school_rating_min", 0)
    prop_school = property_data.get("school_rating", 5)
    if min_school > 0:
        if prop_school >= min_school:
            scores.append(1.0)
            if prop_school >= 8:
                reasons.append(f"Top-rated schools ({prop_school}/10)")
        else:
            scores.append(prop_school / min_school)
            reasons.append(f"School rating {prop_school}/10 (wanted {min_school}+)")

    # Style preference
    pref_style = preferences.get("style_preference", "").lower()
    prop_style = property_data.get("style", "").lower()
    if pref_style:
        if pref_style == prop_style:
            scores.append(1.0)
            reasons.append(f"Matches {pref_style} style preference")
        elif pref_style in prop_style or prop_style in pref_style:
            scores.append(0.8)
        else:
            scores.append(0.6)

    # Year built (newer generally better for modern preference)
    if pref_style == "modern":
        year_built = property_data.get("year_built", 2000)
        if year_built >= 2020:
            scores.append(1.0)
            reasons.append("Newer construction (2020+)")
        elif year_built >= 2015:
            scores.append(0.9)
        elif year_built >= 2010:
            scores.append(0.7)
        else:
            scores.append(0.5)

    avg_score = sum(scores) / len(scores) if scores else 0.7

    reason = "; ".join(reasons) if reasons else "Lifestyle factors within acceptable range"

    return round(avg_score, 2), reason


def calculate_behavioral_boost(property_data: Dict, feedback_history: List[Dict] = None) -> float:
    """
    Calculate behavioral boost based on past preferences.

    Returns boost factor (0-0.2).
    """
    if not feedback_history:
        return 0

    boost = 0
    property_features = set(f.lower() for f in property_data.get("features", []))

    for feedback in feedback_history:
        if feedback.get("liked"):
            liked_features = set(f.lower() for f in feedback.get("interests", []))
            overlap = len(property_features & liked_features)
            boost += overlap * 0.05

    return min(boost, 0.2)  # Cap at 0.2


def generate_match_reasoning(
    budget_score: float, budget_reason: str,
    location_score: float, location_reason: str,
    features_score: float, features_reason: str,
    lifestyle_score: float, lifestyle_reason: str
) -> str:
    """Generate human-readable match reasoning."""
    reasons = []

    # Lead with strongest match
    if budget_score >= 0.9:
        reasons.append(budget_reason)
    if location_score >= 0.9:
        reasons.append(location_reason)
    if features_score >= 0.9:
        reasons.append(features_reason)

    # Add lifestyle highlights
    if lifestyle_score >= 0.8 and lifestyle_reason:
        reasons.append(lifestyle_reason)

    # Note any concerns
    concerns = []
    if budget_score < 0.7:
        concerns.append(budget_reason)
    if location_score < 0.7:
        concerns.append(location_reason)
    if features_score < 0.7:
        concerns.append(features_reason)

    if reasons:
        reasoning = "Strong match: " + "; ".join(reasons[:2])
    else:
        reasoning = "Moderate match"

    if concerns:
        reasoning += ". Note: " + concerns[0]

    return reasoning


def score_property(property_data: Dict, preferences: Dict, feedback_history: List = None) -> PropertyScore:
    """
    Calculate complete match score for a property.

    Args:
        property_data: Property listing data
        preferences: Lead preferences
        feedback_history: Optional past feedback

    Returns:
        PropertyScore with complete breakdown
    """
    # Calculate component scores
    budget_score, budget_reason = calculate_budget_score(
        property_data.get("price", 0), preferences
    )

    location_score, location_reason = calculate_location_score(
        property_data.get("address", {}), preferences
    )

    features_score, features_reason, highlights, concerns = calculate_features_score(
        property_data, preferences
    )

    lifestyle_score, lifestyle_reason = calculate_lifestyle_score(
        property_data, preferences
    )

    behavioral_boost = calculate_behavioral_boost(property_data, feedback_history)

    # Add lifestyle-based highlights
    if property_data.get("school_rating", 0) >= 8:
        highlights.append(f"School rating: {property_data['school_rating']}/10")

    for feature in property_data.get("features", [])[:3]:
        if feature not in [h.lower() for h in highlights]:
            highlights.append(feature.title())

    # Calculate weighted final score
    final_score = (
        budget_score * 0.25 +
        location_score * 0.25 +
        features_score * 0.30 +
        lifestyle_score * 0.20 +
        behavioral_boost
    )

    # Generate reasoning
    reasoning = generate_match_reasoning(
        budget_score, budget_reason,
        location_score, location_reason,
        features_score, features_reason,
        lifestyle_score, lifestyle_reason
    )

    # Format address
    addr = property_data.get("address", {})
    address_str = f"{addr.get('street', 'Unknown')}, {addr.get('city', '')}"

    return PropertyScore(
        property_id=property_data.get("property_id", "unknown"),
        address=address_str,
        price=property_data.get("price", 0),
        match_score=round(min(final_score, 1.0), 3),
        score_breakdown=ScoreBreakdown(
            budget_fit=budget_score,
            location_match=location_score,
            features_match=features_score,
            lifestyle_match=lifestyle_score,
            behavioral_boost=behavioral_boost
        ),
        match_reasoning=reasoning,
        highlights=highlights[:5],
        potential_concerns=concerns[:3],
        rank=0  # Set after sorting
    )


def calculate_property_scores(
    lead_id: str = None,
    preferences: Dict = None,
    listings: List[Dict] = None,
    limit: int = 10,
    min_score: float = 0.0
) -> RecommendationResult:
    """
    Calculate scores for all properties and return recommendations.

    Args:
        lead_id: Lead ID to load preferences
        preferences: Pre-loaded preferences (optional)
        listings: Pre-loaded listings (optional)
        limit: Max number of recommendations
        min_score: Minimum match score threshold

    Returns:
        RecommendationResult with ranked recommendations
    """
    # Load preferences if not provided
    if preferences is None and lead_id:
        preferences = load_preferences(lead_id)
    elif preferences is None:
        preferences = {}

    # Load listings if not provided
    if listings is None:
        listings = load_listings()

    # Score all properties
    scored_properties = []
    for listing in listings:
        score = score_property(listing, preferences)
        if score.match_score >= min_score:
            scored_properties.append(score)

    # Sort by match score
    scored_properties.sort(key=lambda x: x.match_score, reverse=True)

    # Assign ranks and limit
    recommendations = []
    for i, prop in enumerate(scored_properties[:limit]):
        prop.rank = i + 1
        recommendations.append(prop)

    return RecommendationResult(
        lead_id=lead_id or "manual",
        preferences_used=preferences,
        properties_scored=len(listings),
        recommendations=recommendations,
        generated_at=datetime.now().isoformat()
    )


def main():
    parser = argparse.ArgumentParser(description="Calculate property match scores")
    parser.add_argument("--lead-id", type=str, help="Lead ID to load preferences")
    parser.add_argument("--preferences", type=str, help="Path to preferences JSON")
    parser.add_argument("--listings", type=str, help="Path to listings JSON")
    parser.add_argument("--limit", type=int, default=10, help="Max recommendations")
    parser.add_argument("--min-score", type=float, default=0.5, help="Minimum match score")
    parser.add_argument("--output", type=str, default="json", choices=["json", "table"])

    args = parser.parse_args()

    # Load preferences from file if provided
    preferences = None
    if args.preferences:
        with open(args.preferences, "r") as f:
            preferences = json.load(f)

    # Load listings from file if provided
    listings = None
    if args.listings:
        with open(args.listings, "r") as f:
            data = json.load(f)
            listings = data.get("listings", data)

    # Calculate scores
    result = calculate_property_scores(
        lead_id=args.lead_id,
        preferences=preferences,
        listings=listings,
        limit=args.limit,
        min_score=args.min_score
    )

    if args.output == "table":
        print(f"Property Recommendations for {result.lead_id}")
        print(f"{'=' * 70}")
        print(f"Scored {result.properties_scored} properties")
        print()
        print(f"{'Rank':<6}{'Address':<35}{'Price':<12}{'Score':<10}")
        print(f"{'-' * 70}")
        for rec in result.recommendations:
            print(f"{rec.rank:<6}{rec.address[:33]:<35}${rec.price:,}{'<12'}{rec.match_score:.0%}")
            print(f"       {rec.match_reasoning[:60]}")
            print()
    else:
        # Convert dataclasses for JSON
        output = {
            "lead_id": result.lead_id,
            "properties_scored": result.properties_scored,
            "generated_at": result.generated_at,
            "recommendations": [
                {
                    "rank": r.rank,
                    "property_id": r.property_id,
                    "address": r.address,
                    "price": r.price,
                    "match_score": r.match_score,
                    "score_breakdown": asdict(r.score_breakdown),
                    "match_reasoning": r.match_reasoning,
                    "highlights": r.highlights,
                    "potential_concerns": r.potential_concerns
                }
                for r in result.recommendations
            ]
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
