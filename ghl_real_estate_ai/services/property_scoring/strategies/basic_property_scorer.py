"""
Basic Property Scorer Strategy
Simple rule-based property scoring for baseline matching
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from ..interfaces.property_scorer import ConfidenceLevel, PropertyScorer, ScoringResult

logger = logging.getLogger(__name__)


class BasicPropertyScorer(PropertyScorer):
    """
    Basic property scoring using simple rule-based matching

    This scorer provides fast, deterministic scoring based on
    fundamental property attributes without complex algorithms.

    Features:
    - Budget compatibility scoring
    - Basic location matching
    - Simple feature matching
    - Straightforward reasoning
    """

    def __init__(self):
        super().__init__(name="Basic Property Scorer", version="1.0.0")

    def calculate_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> ScoringResult:
        """
        Calculate basic property score using simple rules

        Args:
            property_data: Property information
            lead_preferences: Lead preferences

        Returns:
            ScoringResult with basic scoring breakdown
        """
        self.validate_inputs(property_data, lead_preferences)

        # Calculate component scores
        budget_score = self._calculate_budget_score(property_data, lead_preferences)
        location_score = self._calculate_location_score(property_data, lead_preferences)
        feature_score = self._calculate_feature_score(property_data, lead_preferences)
        market_score = self._calculate_market_score(property_data)

        # Simple weighted average
        weights = {"budget": 0.4, "location": 0.3, "features": 0.2, "market": 0.1}
        overall_score = (
            budget_score * weights["budget"]
            + location_score * weights["location"]
            + feature_score * weights["features"]
            + market_score * weights["market"]
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            property_data, lead_preferences, budget_score, location_score, feature_score, market_score
        )

        # Determine confidence level
        confidence_level = self._determine_confidence_level(overall_score)

        return ScoringResult(
            overall_score=round(overall_score, 1),
            confidence_level=confidence_level,
            budget_score=round(budget_score, 1),
            location_score=round(location_score, 1),
            feature_score=round(feature_score, 1),
            market_score=round(market_score, 1),
            reasoning=reasoning,
            scorer_type=self.name,
            scoring_timestamp=datetime.now().isoformat(),
            model_version=self.version,
        )

    def validate_inputs(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> bool:
        """
        Validate inputs for basic scoring

        Args:
            property_data: Property data to validate
            lead_preferences: Preferences to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check required property fields
        required_prop_fields = ["price"]
        for field in required_prop_fields:
            if field not in property_data:
                raise ValueError(f"Property data missing required field: {field}")

        # Check required preference fields
        required_pref_fields = ["budget"]
        for field in required_pref_fields:
            if field not in lead_preferences:
                raise ValueError(f"Lead preferences missing required field: {field}")

        # Validate data types and ranges
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)

        if not isinstance(price, (int, float)) or price <= 0:
            raise ValueError("Property price must be a positive number")

        if not isinstance(budget, (int, float)) or budget <= 0:
            raise ValueError("Budget must be a positive number")

        return True

    def _calculate_budget_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """Calculate budget compatibility score"""
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)

        if budget == 0:
            return 50.0  # Neutral score if no budget

        price_ratio = price / budget

        if price_ratio <= 0.8:  # Significantly under budget
            return 100.0
        elif price_ratio <= 0.9:  # Comfortably under budget
            return 95.0
        elif price_ratio <= 1.0:  # Within budget
            return 90.0
        elif price_ratio <= 1.05:  # Slightly over budget
            return 70.0
        elif price_ratio <= 1.1:  # Moderately over budget
            return 50.0
        elif price_ratio <= 1.2:  # Significantly over budget
            return 25.0
        else:  # Way over budget
            return 10.0

    def _calculate_location_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """Calculate location match score"""
        pref_location = lead_preferences.get("location")
        if not pref_location:
            return 75.0  # Neutral score if no location preference

        address = property_data.get("address", {})
        if isinstance(address, str):
            # Handle legacy string format
            prop_location = address.lower()
        else:
            # Handle structured address
            neighborhood = address.get("neighborhood", "").lower()
            city = address.get("city", "").lower()
            prop_location = f"{neighborhood} {city}".lower()

        pref_location_lower = pref_location.lower()

        # Exact match
        if pref_location_lower in prop_location:
            return 100.0

        # Partial match (keywords)
        pref_keywords = pref_location_lower.split()
        matches = sum(1 for keyword in pref_keywords if keyword in prop_location)
        if matches > 0:
            return 70.0 + (matches / len(pref_keywords)) * 20.0

        return 40.0  # No match

    def _calculate_feature_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """Calculate feature match score"""
        score = 0.0
        total_weight = 0.0

        # Bedroom match
        pref_bedrooms = lead_preferences.get("bedrooms")
        if pref_bedrooms:
            prop_bedrooms = property_data.get("bedrooms", 0)
            if prop_bedrooms >= pref_bedrooms:
                score += 30.0
            elif prop_bedrooms >= pref_bedrooms - 1:
                score += 20.0
            else:
                score += 10.0
            total_weight += 30.0

        # Must-have features
        must_haves = lead_preferences.get("must_haves", [])
        if must_haves:
            prop_amenities = property_data.get("amenities", [])
            prop_amenities_lower = [a.lower() for a in prop_amenities]

            matches = 0
            for must_have in must_haves:
                if must_have.lower() in prop_amenities_lower:
                    matches += 1

            if matches == len(must_haves):
                score += 40.0
            else:
                score += 40.0 * (matches / len(must_haves)) * 0.5
            total_weight += 40.0

        # Nice-to-have features
        nice_to_haves = lead_preferences.get("nice_to_haves", [])
        if nice_to_haves:
            prop_amenities = property_data.get("amenities", [])
            prop_amenities_lower = [a.lower() for a in prop_amenities]

            matches = sum(1 for nth in nice_to_haves if nth.lower() in prop_amenities_lower)
            bonus = min(30.0, (matches / len(nice_to_haves)) * 30.0)
            score += bonus
            total_weight += 30.0

        # Property type match
        pref_type = lead_preferences.get("property_type")
        if pref_type:
            prop_type = property_data.get("property_type", "").lower()
            if pref_type.lower() in prop_type:
                score += 20.0
            total_weight += 20.0

        # Normalize score
        if total_weight > 0:
            return min(100.0, (score / total_weight) * 100.0)
        else:
            return 75.0  # Default score when no features specified

    def _calculate_market_score(self, property_data: Dict[str, Any]) -> float:
        """Calculate market context score"""
        score = 75.0  # Base market score

        # Days on market analysis
        days_on_market = property_data.get("days_on_market", 30)
        if days_on_market <= 10:  # Hot property
            score += 20.0
        elif days_on_market <= 30:  # Normal market pace
            score += 10.0
        elif days_on_market > 90:  # Stale listing
            score -= 20.0

        # Price per square foot analysis (basic check)
        price = property_data.get("price", 0)
        sqft = property_data.get("sqft", 1)
        if sqft > 0:
            price_per_sqft = price / sqft
            # Basic market comparison (would be enhanced with real market data)
            if 200 <= price_per_sqft <= 350:  # Reasonable range
                score += 10.0
            elif price_per_sqft < 200:  # Potentially undervalued
                score += 5.0
            elif price_per_sqft > 400:  # Potentially overpriced
                score -= 10.0

        return max(0.0, min(100.0, score))

    def _generate_reasoning(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any],
        budget_score: float,
        location_score: float,
        feature_score: float,
        market_score: float,
    ) -> List[str]:
        """Generate human-readable reasoning for the score"""
        reasoning = []

        # Budget reasoning
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)
        if budget > 0:
            if price <= budget * 0.9:
                savings = budget - price
                reasoning.append(f"Great value at ${savings / 1000:.0f}k under budget")
            elif price <= budget:
                reasoning.append("Priced within your budget")
            elif price <= budget * 1.1:
                overage = price - budget
                reasoning.append(f"${overage / 1000:.0f}k over budget but may be worth considering")

        # Location reasoning
        if location_score >= 90:
            reasoning.append("Excellent location match")
        elif location_score >= 70:
            reasoning.append("Good location fit")

        # Feature reasoning
        bedrooms = property_data.get("bedrooms", 0)
        pref_bedrooms = lead_preferences.get("bedrooms")
        if pref_bedrooms and bedrooms >= pref_bedrooms:
            reasoning.append(f"Has your preferred {bedrooms} bedrooms")

        must_haves = lead_preferences.get("must_haves", [])
        if must_haves:
            prop_amenities = [a.lower() for a in property_data.get("amenities", [])]
            matches = [mh for mh in must_haves if mh.lower() in prop_amenities]
            if matches:
                reasoning.append(f"Includes desired features: {', '.join(matches)}")

        # Market reasoning
        days_on_market = property_data.get("days_on_market", 30)
        if days_on_market <= 15:
            reasoning.append("Recently listed - likely to move quickly")

        # Fallback reasoning
        if not reasoning:
            reasoning.append("Meets basic criteria for your search")

        return reasoning[:5]  # Limit to top 5 reasons

    def _determine_confidence_level(self, overall_score: float) -> ConfidenceLevel:
        """Determine confidence level based on overall score"""
        if overall_score >= 90:
            return ConfidenceLevel.EXCELLENT
        elif overall_score >= 80:
            return ConfidenceLevel.HIGH
        elif overall_score >= 60:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def get_supported_features(self) -> List[str]:
        """Get list of features supported by basic scorer"""
        return [
            "budget_matching",
            "location_matching",
            "bedroom_matching",
            "amenity_matching",
            "property_type_matching",
            "basic_market_analysis",
            "basic_reasoning",
        ]
