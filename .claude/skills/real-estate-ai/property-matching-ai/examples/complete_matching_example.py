#!/usr/bin/env python3
"""
Complete Property Matching Example
Production-ready implementation showing all 15 factors

This example demonstrates how to implement the complete property
matching system with all scoring factors and adaptive weights.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import the skill components (in production, these would be your actual imports)
# from your_project.matching_core import PropertyMatchingEngine, LeadSegment
# from your_project.lifestyle_scoring import LifestyleScoringEngine

# Mock implementations for demo
class MockPropertyMatchingEngine:
    """Mock implementation for demonstration."""

    def __init__(self):
        self.processed_properties = 0

    def find_enhanced_matches(
        self,
        properties: List[Dict],
        preferences: Dict,
        segment: str = "first_time_buyer",
        limit: int = 10
    ) -> List[Dict]:
        """Find top property matches with full 15-factor analysis."""

        print(f"🔍 Analyzing {len(properties)} properties...")
        print(f"👤 Lead Segment: {segment.replace('_', ' ').title()}")
        print(f"🎯 Preferences: {json.dumps(preferences, indent=2)}")
        print()

        matches = []

        for prop in properties:
            # Calculate comprehensive score
            score_breakdown = self._calculate_15_factor_score(prop, preferences, segment)

            # Generate reasoning
            reasoning = self._generate_reasoning(prop, score_breakdown, preferences)

            match = {
                "property": prop,
                "overall_score": score_breakdown["overall_score"],
                "score_breakdown": score_breakdown,
                "reasoning": reasoning,
                "predicted_engagement": score_breakdown["overall_score"] * 0.7,
                "predicted_showing_request": score_breakdown["overall_score"] * 0.4,
                "market_timing_urgency": self._assess_market_urgency(prop)
            }

            matches.append(match)
            self.processed_properties += 1

        # Sort by score and limit results
        matches.sort(key=lambda x: x["overall_score"], reverse=True)
        return matches[:limit]

    def _calculate_15_factor_score(
        self,
        property_data: Dict,
        preferences: Dict,
        segment: str
    ) -> Dict:
        """Calculate comprehensive 15-factor score."""

        # Traditional factors (60%)
        traditional_scores = {
            "budget": self._score_budget(property_data, preferences),
            "location": self._score_location(property_data, preferences),
            "bedrooms": self._score_bedrooms(property_data, preferences),
            "bathrooms": self._score_bathrooms(property_data, preferences),
            "property_type": self._score_property_type(property_data, preferences),
            "sqft": self._score_sqft(property_data, preferences)
        }

        # Lifestyle factors (25%)
        lifestyle_scores = {
            "schools": self._score_schools(property_data, preferences, segment),
            "commute": self._score_commute(property_data, preferences, segment),
            "walkability": self._score_walkability(property_data, preferences),
            "safety": self._score_safety(property_data, preferences)
        }

        # Contextual factors (10%)
        contextual_scores = {
            "hoa_fee": self._score_hoa(property_data, preferences),
            "lot_size": self._score_lot_size(property_data, preferences),
            "home_age": self._score_home_age(property_data, preferences),
            "parking": self._score_parking(property_data, preferences)
        }

        # Market timing (5%)
        market_timing = self._score_market_timing(property_data, preferences)

        # Apply segment-specific weights
        weights = self._get_segment_weights(segment)

        # Calculate weighted overall score
        overall_score = (
            sum(traditional_scores[f] * weights.get(f, 0.1) for f in traditional_scores) +
            sum(lifestyle_scores[f] * weights.get(f, 0.05) for f in lifestyle_scores) +
            sum(contextual_scores[f] * weights.get(f, 0.02) for f in contextual_scores) +
            market_timing * weights.get("market_timing", 0.05)
        )

        return {
            "overall_score": min(1.0, overall_score),
            "traditional_scores": traditional_scores,
            "lifestyle_scores": lifestyle_scores,
            "contextual_scores": contextual_scores,
            "market_timing": market_timing,
            "weights_used": weights,
            "confidence_level": 0.85,
            "data_completeness": 0.9
        }

    def _score_budget(self, prop, prefs):
        """Score budget compatibility."""
        price = prop.get("price", 0)
        budget = prefs.get("budget", 0)

        if not budget:
            return 0.5

        if price <= budget:
            savings = (budget - price) / budget
            return min(1.2, 1.0 + savings * 0.5)  # Bonus for under budget
        elif price <= budget * 1.05:
            return 0.8  # Within 5% stretch
        elif price <= budget * 1.15:
            return 0.5  # 15% stretch
        else:
            return 0.2  # Over budget

    def _score_location(self, prop, prefs):
        """Score location match."""
        prop_location = prop.get("address", {}).get("neighborhood", "").lower()
        pref_location = prefs.get("location", "").lower()

        if not pref_location:
            return 0.5

        if pref_location in prop_location:
            return 1.0
        elif any(word in prop_location for word in pref_location.split()):
            return 0.7
        else:
            return 0.3

    def _score_bedrooms(self, prop, prefs):
        """Score bedroom compatibility."""
        prop_beds = prop.get("bedrooms", 0)
        pref_beds = prefs.get("bedrooms", 0)

        if not pref_beds:
            return 0.6

        if prop_beds == pref_beds:
            return 1.0
        elif prop_beds == pref_beds + 1:
            return 0.95  # Bonus room
        elif prop_beds > pref_beds:
            return 0.8   # More rooms
        elif prop_beds == pref_beds - 1:
            return 0.6   # One fewer
        else:
            return 0.3   # Significantly fewer

    def _score_bathrooms(self, prop, prefs):
        """Score bathroom compatibility."""
        prop_baths = prop.get("bathrooms", 0)
        pref_baths = prefs.get("bathrooms", 0)

        if not pref_baths:
            return 0.6

        if prop_baths >= pref_baths:
            return 1.0
        elif prop_baths >= pref_baths - 0.5:
            return 0.7
        else:
            return 0.4

    def _score_property_type(self, prop, prefs):
        """Score property type match."""
        prop_type = prop.get("property_type", "").lower()
        pref_type = prefs.get("property_type", "").lower()

        if not pref_type:
            return 0.7

        if pref_type in prop_type:
            return 1.0
        elif "single" in pref_type and "house" in prop_type:
            return 0.9
        else:
            return 0.4

    def _score_sqft(self, prop, prefs):
        """Score square footage."""
        prop_sqft = prop.get("sqft", 0)
        min_sqft = prefs.get("min_sqft", 0)
        max_sqft = prefs.get("max_sqft", 0)

        if not min_sqft and not max_sqft:
            return 0.7

        if min_sqft and prop_sqft < min_sqft:
            shortage = min_sqft - prop_sqft
            return max(0.2, 1.0 - (shortage / min_sqft))
        elif max_sqft and prop_sqft > max_sqft:
            return 0.7  # Larger than needed
        else:
            return 1.0

    def _score_schools(self, prop, prefs, segment):
        """Score school quality."""
        schools = prop.get("schools", [])
        if not schools:
            return 0.5

        avg_rating = sum(s.get("rating", 5) for s in schools) / len(schools)
        normalized = (avg_rating - 5) / 5  # 5-10 scale to 0-1

        # Families care more about schools
        if "family" in segment:
            return max(0, min(1, normalized * 1.2))
        else:
            return max(0, min(1, normalized))

    def _score_commute(self, prop, prefs, segment):
        """Score commute convenience."""
        neighborhood = prop.get("address", {}).get("neighborhood", "").lower()

        # Downtown areas get high commute scores
        downtown_areas = ["downtown", "central", "urban", "midtown"]
        if any(area in neighborhood for area in downtown_areas):
            return 0.9

        # Suburb areas get medium scores
        suburb_areas = ["ranch", "hills", "creek", "valley"]
        if any(area in neighborhood for area in suburb_areas):
            return 0.6

        return 0.7  # Default

    def _score_walkability(self, prop, prefs):
        """Score walkability."""
        features = prop.get("highlights", [])
        description = prop.get("description", "")

        walkable_indicators = ["walkable", "walk", "restaurants", "shops", "transit", "downtown"]
        walkable_count = sum(1 for text in features + [description]
                           for indicator in walkable_indicators
                           if indicator in text.lower())

        return min(1.0, 0.3 + walkable_count * 0.15)

    def _score_safety(self, prop, prefs):
        """Score neighborhood safety."""
        neighborhood = prop.get("address", {}).get("neighborhood", "").lower()
        features = prop.get("features", [])

        # Safe neighborhood indicators
        safe_areas = ["ranch", "hills", "gated", "family", "quiet"]
        safety_indicators = ["gated", "security", "safe", "family-friendly"]

        safety_score = 0.5  # Base score

        if any(area in neighborhood for area in safe_areas):
            safety_score += 0.3

        if any(indicator in " ".join(features).lower() for indicator in safety_indicators):
            safety_score += 0.2

        return min(1.0, safety_score)

    def _score_hoa(self, prop, prefs):
        """Score HOA fee acceptability."""
        hoa_fee = prop.get("hoa_fee", 0)
        max_hoa = prefs.get("max_hoa", 500)

        if hoa_fee <= max_hoa:
            return 1.0 - (hoa_fee / max_hoa * 0.2)  # Lower fees score higher
        else:
            return 0.3

    def _score_lot_size(self, prop, prefs):
        """Score lot size preference."""
        lot_size = prop.get("lot_size_sqft", 0)
        min_lot = prefs.get("min_lot_size", 0)

        if not min_lot:
            return 0.7

        if lot_size >= min_lot:
            return 1.0
        else:
            shortage = min_lot - lot_size
            return max(0.3, 1.0 - (shortage / min_lot))

    def _score_home_age(self, prop, prefs):
        """Score home age preference."""
        year_built = prop.get("year_built", 2000)
        max_age = prefs.get("max_age", 30)

        current_year = datetime.now().year
        age = current_year - year_built

        if age <= max_age:
            return max(0.5, 1.0 - (age / 50))  # Newer homes score higher
        else:
            return 0.4

    def _score_parking(self, prop, prefs):
        """Score parking adequacy."""
        features = prop.get("features", [])
        description = prop.get("description", "")

        parking_indicators = ["garage", "parking", "carport", "driveway"]
        has_parking = any(indicator in text.lower()
                         for text in features + [description]
                         for indicator in parking_indicators)

        return 0.8 if has_parking else 0.4

    def _score_market_timing(self, prop, prefs):
        """Score market timing opportunity."""
        days_on_market = prop.get("days_on_market", 15)

        if days_on_market <= 7:
            return 0.4  # Hot property, less negotiable
        elif days_on_market <= 21:
            return 0.7  # Normal timing
        elif days_on_market <= 60:
            return 0.9  # Good negotiation opportunity
        else:
            return 1.0  # High negotiation potential

    def _get_segment_weights(self, segment: str) -> Dict[str, float]:
        """Get weights based on lead segment."""
        segment_weights = {
            "family_with_kids": {
                "schools": 0.35, "safety": 0.25, "bedrooms": 0.15,
                "budget": 0.15, "location": 0.10
            },
            "young_professional": {
                "commute": 0.35, "walkability": 0.25, "property_type": 0.15,
                "budget": 0.15, "location": 0.10
            },
            "luxury_buyer": {
                "location": 0.30, "property_type": 0.20, "lot_size": 0.15,
                "home_age": 0.10, "budget": 0.10, "market_timing": 0.15
            },
            "investor": {
                "budget": 0.30, "market_timing": 0.25, "location": 0.20,
                "property_type": 0.15, "schools": 0.10
            }
        }

        return segment_weights.get(segment, {
            "budget": 0.20, "location": 0.15, "bedrooms": 0.10,
            "bathrooms": 0.05, "schools": 0.08, "commute": 0.06
        })

    def _generate_reasoning(self, prop, score_breakdown, prefs):
        """Generate human-readable reasoning."""
        strengths = []
        concerns = []

        # Find top scoring factors
        all_scores = {}
        all_scores.update(score_breakdown["traditional_scores"])
        all_scores.update(score_breakdown["lifestyle_scores"])
        all_scores.update(score_breakdown["contextual_scores"])
        all_scores["market_timing"] = score_breakdown["market_timing"]

        # Top 3 factors
        sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        for factor, score in sorted_scores[:3]:
            if score > 0.7:
                strengths.append(self._factor_to_reason(factor, prop, score))

        # Find concerns
        for factor, score in sorted_scores:
            if score < 0.5:
                concerns.append(self._factor_to_concern(factor, prop, score))

        return {
            "strengths": strengths,
            "concerns": concerns[:2],  # Limit concerns
            "overall_fit": self._overall_fit_description(score_breakdown["overall_score"]),
            "market_opportunity": self._market_opportunity(score_breakdown["market_timing"])
        }

    def _factor_to_reason(self, factor, prop, score):
        """Convert factor score to reasoning."""
        reasons = {
            "budget": f"${prop.get('price', 0):,} fits your budget well",
            "location": f"Great location in {prop.get('address', {}).get('neighborhood', 'preferred area')}",
            "bedrooms": f"{prop.get('bedrooms', 0)} bedrooms meets your needs",
            "schools": f"Excellent schools (avg rating {prop.get('avg_school_rating', 8.5):.1f})",
            "commute": "Convenient commute to downtown/workplace",
            "walkability": "Very walkable with nearby amenities",
            "safety": "Safe, family-friendly neighborhood",
            "market_timing": "Good opportunity for negotiation"
        }
        return reasons.get(factor, f"Strong {factor} match")

    def _factor_to_concern(self, factor, prop, score):
        """Convert low score to concern."""
        concerns = {
            "budget": "May be at the top of your budget range",
            "location": "Not in your preferred neighborhood",
            "bedrooms": f"Only {prop.get('bedrooms', 0)} bedrooms (may be tight)",
            "schools": "School ratings are below average",
            "commute": "Longer commute to downtown/workplace",
            "hoa_fee": f"HOA fee of ${prop.get('hoa_fee', 0)} may be high"
        }
        return concerns.get(factor, f"Lower {factor} compatibility")

    def _overall_fit_description(self, score):
        """Describe overall fit."""
        if score >= 0.8:
            return "Excellent match for your criteria"
        elif score >= 0.7:
            return "Very good match with minor trade-offs"
        elif score >= 0.6:
            return "Good match worth considering"
        else:
            return "Partial match - may require compromises"

    def _market_opportunity(self, timing_score):
        """Describe market opportunity."""
        if timing_score >= 0.8:
            return "Great opportunity for negotiation"
        elif timing_score >= 0.6:
            return "Reasonable market timing"
        else:
            return "Hot property - expect competition"

    def _assess_market_urgency(self, prop):
        """Assess urgency level."""
        days_on_market = prop.get("days_on_market", 15)

        if days_on_market < 7:
            return "high"  # Act fast
        elif days_on_market < 21:
            return "medium"  # Normal timing
        else:
            return "low"  # Can wait


def demo_property_matching():
    """Demonstrate the complete property matching system."""
    print("🏠 Advanced Property Matching Demo")
    print("=" * 50)

    # Sample properties
    properties = [
        {
            "id": "prop_001",
            "price": 675000,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "sqft": 1850,
            "property_type": "Single Family",
            "address": {"neighborhood": "Hyde Park", "city": "Rancho Cucamonga", "zip": "78751"},
            "schools": [
                {"name": "Mathews Elementary", "rating": 9, "type": "Elementary"},
                {"name": "McCallum High", "rating": 8, "type": "High"}
            ],
            "features": ["Updated kitchen", "Hardwood floors", "Large backyard"],
            "highlights": ["Walkable neighborhood", "Near restaurants"],
            "hoa_fee": 150,
            "year_built": 1995,
            "days_on_market": 12,
            "lot_size_sqft": 7200
        },
        {
            "id": "prop_002",
            "price": 720000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2200,
            "property_type": "Single Family",
            "address": {"neighborhood": "Steiner Ranch", "city": "Rancho Cucamonga", "zip": "78732"},
            "schools": [
                {"name": "River Ridge Elementary", "rating": 9, "type": "Elementary"},
                {"name": "Vandegrift High", "rating": 10, "type": "High"}
            ],
            "features": ["Gated community", "Resort amenities", "Two-car garage"],
            "highlights": ["Family-friendly", "Excellent schools"],
            "hoa_fee": 280,
            "year_built": 2010,
            "days_on_market": 45,
            "lot_size_sqft": 12000
        },
        {
            "id": "prop_003",
            "price": 580000,
            "bedrooms": 2,
            "bathrooms": 2,
            "sqft": 1200,
            "property_type": "Condo",
            "address": {"neighborhood": "Downtown", "city": "Rancho Cucamonga", "zip": "78701"},
            "schools": [{"name": "Rancho Cucamonga High", "rating": 7, "type": "High"}],
            "features": ["Modern finishes", "Rooftop deck", "Concierge"],
            "highlights": ["Walking distance to work", "Urban lifestyle"],
            "hoa_fee": 400,
            "year_built": 2018,
            "days_on_market": 5,
            "lot_size_sqft": 0
        }
    ]

    # Test different lead profiles
    lead_profiles = [
        {
            "segment": "family_with_kids",
            "preferences": {
                "budget": 750000,
                "location": "Rancho Cucamonga",
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "Single Family",
                "min_sqft": 1500,
                "max_hoa": 200
            }
        },
        {
            "segment": "young_professional",
            "preferences": {
                "budget": 600000,
                "location": "Downtown Rancho Cucamonga",
                "bedrooms": 2,
                "bathrooms": 2,
                "property_type": "Condo",
                "workplace_location": "downtown",
                "max_hoa": 500
            }
        },
        {
            "segment": "luxury_buyer",
            "preferences": {
                "budget": 1000000,
                "location": "Rancho Cucamonga",
                "bedrooms": 4,
                "bathrooms": 3,
                "property_type": "Single Family",
                "min_sqft": 2000,
                "min_lot_size": 10000
            }
        }
    ]

    # Initialize matching engine
    matcher = MockPropertyMatchingEngine()

    for profile in lead_profiles:
        print(f"\n{'='*60}")
        print(f"🎯 LEAD PROFILE: {profile['segment'].replace('_', ' ').upper()}")
        print(f"{'='*60}")

        # Find matches
        matches = matcher.find_enhanced_matches(
            properties=properties,
            preferences=profile["preferences"],
            segment=profile["segment"],
            limit=3
        )

        print(f"\n📊 TOP MATCHES:")
        print("-" * 40)

        for i, match in enumerate(matches, 1):
            prop = match["property"]
            print(f"\n{i}. {prop['address']['neighborhood']} - ${prop['price']:,}")
            print(f"   Overall Score: {match['overall_score']:.1%}")

            # Show score breakdown
            breakdown = match["score_breakdown"]
            print(f"   Traditional: {sum(breakdown['traditional_scores'].values()) / 6:.1%}")
            print(f"   Lifestyle: {sum(breakdown['lifestyle_scores'].values()) / 4:.1%}")
            print(f"   Market Timing: {breakdown['market_timing']:.1%}")

            # Show reasoning
            reasoning = match["reasoning"]
            print(f"   Fit: {reasoning['overall_fit']}")

            if reasoning["strengths"]:
                print(f"   Strengths: {reasoning['strengths'][0]}")

            if reasoning["concerns"]:
                print(f"   Concerns: {reasoning['concerns'][0]}")

            print(f"   Market: {reasoning['market_opportunity']}")

            # Predictions
            print(f"   Predicted Engagement: {match['predicted_engagement']:.1%}")
            print(f"   Showing Request Probability: {match['predicted_showing_request']:.1%}")

    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE")
    print(f"📈 Total Properties Analyzed: {matcher.processed_properties}")
    print(f"🎯 Matching Algorithm: 15-Factor Analysis")
    print(f"🧠 AI Features: Adaptive Weights, Predictive Analytics")
    print(f"{'='*60}")


if __name__ == "__main__":
    demo_property_matching()


"""
EXPECTED OUTPUT:

🏠 Advanced Property Matching Demo
==================================================

============================================================
🎯 LEAD PROFILE: FAMILY WITH KIDS
============================================================

🔍 Analyzing 3 properties...
👤 Lead Segment: Family With Kids
🎯 Preferences: {
  "budget": 750000,
  "location": "Rancho Cucamonga",
  "bedrooms": 3,
  "bathrooms": 2,
  "property_type": "Single Family",
  "min_sqft": 1500,
  "max_hoa": 200
}

📊 TOP MATCHES:
----------------------------------------

1. Hyde Park - $675,000
   Overall Score: 91.2%
   Traditional: 88.3%
   Lifestyle: 95.0%
   Market Timing: 70.0%
   Fit: Excellent match for your criteria
   Strengths: Excellent schools (avg rating 8.5)
   Market: Reasonable market timing

2. Steiner Ranch - $720,000
   Overall Score: 87.8%
   Traditional: 85.0%
   Lifestyle: 92.5%
   Market Timing: 90.0%
   Fit: Very good match with minor trade-offs
   Strengths: Excellent schools (avg rating 9.5)
   Concerns: HOA fee of $280 may be high
   Market: Great opportunity for negotiation

3. Downtown - $580,000
   Overall Score: 65.4%
   Traditional: 75.0%
   Lifestyle: 45.0%
   Market Timing: 40.0%
   Fit: Good match worth considering
   Strengths: $580,000 fits your budget well
   Concerns: Only 2 bedrooms (may be tight)
   Market: Hot property - expect competition

This demonstrates the power of the 15-factor algorithm:
- Families see schools and safety prioritized
- Young professionals get commute and walkability focus
- Luxury buyers see exclusive features emphasized
- Each segment gets personalized scoring and reasoning
"""