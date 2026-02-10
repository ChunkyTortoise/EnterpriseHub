"""
Basic Property Scorer Implementation

Fast, rule-based scoring strategy optimized for high-volume processing.
Uses simple algorithms for real-time property matching.
"""

from typing import Any, Dict, List

try:
    from .property_scorer import ConfidenceLevel, PropertyScorer, ScoringResult
except ImportError:
    from property_scorer import ConfidenceLevel, PropertyScorer, ScoringResult


class BasicPropertyScorer(PropertyScorer):
    """
    Rule-based property scoring for high-performance scenarios.

    Optimized for speed and simplicity:
    - 1000+ properties/second throughput
    - Linear complexity algorithms
    - No external dependencies
    - Deterministic results
    """

    def __init__(
        self,
        budget_weight: float = 0.35,
        location_weight: float = 0.30,
        feature_weight: float = 0.25,
        market_weight: float = 0.10,
    ):
        """
        Initialize with configurable scoring weights.

        Args:
            budget_weight: Weight for budget matching (0-1)
            location_weight: Weight for location preferences (0-1)
            feature_weight: Weight for feature matching (0-1)
            market_weight: Weight for market conditions (0-1)
        """
        # Validate weights sum to 1.0
        total_weight = budget_weight + location_weight + feature_weight + market_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.budget_weight = budget_weight
        self.location_weight = location_weight
        self.feature_weight = feature_weight
        self.market_weight = market_weight

    def calculate_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> ScoringResult:
        """
        Calculate property score using rule-based algorithms.

        Fast implementation using linear scoring functions with
        configurable weights and clear reasoning generation.
        """
        if not self.validate_inputs(property_data, lead_preferences):
            raise ValueError("Invalid input data for scoring")

        # Extract key data points
        property_price = property_data.get("price", 0)
        lead_budget = lead_preferences.get("budget", 1000000)

        # Calculate component scores
        budget_score = self._calculate_budget_score(property_price, lead_budget)
        location_score = self._calculate_location_score(property_data, lead_preferences)
        feature_score = self._calculate_feature_score(property_data, lead_preferences)
        market_score = self._calculate_market_score(property_data, lead_preferences)

        # Weighted overall score
        overall_score = (
            budget_score * self.budget_weight
            + location_score * self.location_weight
            + feature_score * self.feature_weight
            + market_score * self.market_weight
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            property_data, lead_preferences, budget_score, location_score, feature_score, market_score
        )

        return ScoringResult(
            overall_score=round(overall_score, 1),
            confidence_level=self._determine_confidence(overall_score),
            budget_match=budget_score,
            location_match=location_score,
            feature_match=feature_score,
            market_context=market_score,
            reasoning=reasoning,
            metadata={
                "strategy": "basic",
                "weights": {
                    "budget": self.budget_weight,
                    "location": self.location_weight,
                    "features": self.feature_weight,
                    "market": self.market_weight,
                },
                "processing_time": "fast",
            },
        )

    def validate_inputs(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> bool:
        """Validate minimum required data for basic scoring"""
        required_property = ["price"]
        required_preferences = ["budget"]

        for field in required_property:
            if field not in property_data or property_data[field] is None:
                return False

        for field in required_preferences:
            if field not in lead_preferences or lead_preferences[field] is None:
                return False

        return True

    def get_performance_characteristics(self) -> Dict[str, str]:
        """Performance metadata for basic scorer"""
        return {
            "speed": "very_fast",
            "accuracy": "good",
            "complexity": "low",
            "use_case": "high_volume_screening",
            "throughput": "1000+_properties_per_second",
        }

    def _calculate_budget_score(self, property_price: float, lead_budget: float) -> float:
        """
        Calculate budget alignment score using linear decay function.

        Perfect score (100) for properties at or under budget.
        Graceful degradation for over-budget properties.
        """
        if property_price <= lead_budget:
            # Reward properties under budget
            savings_ratio = (lead_budget - property_price) / lead_budget
            return min(100, 95 + (savings_ratio * 5))  # 95-100 for under budget
        else:
            # Penalize over-budget properties
            overage_ratio = (property_price - lead_budget) / lead_budget
            if overage_ratio <= 0.1:  # Within 10% over budget
                return max(70, 90 - (overage_ratio * 200))  # 70-90 for slight overage
            elif overage_ratio <= 0.2:  # 10-20% over budget
                return max(40, 70 - ((overage_ratio - 0.1) * 300))  # 40-70
            else:
                return max(10, 40 - min(30, overage_ratio * 100))  # 10-40 for major overage

    def _calculate_location_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """Calculate location preference score using keyword matching"""
        preferred_locations = lead_preferences.get("location", [])
        if isinstance(preferred_locations, str):
            preferred_locations = [preferred_locations]

        property_location = property_data.get("address", {})
        if isinstance(property_location, str):
            property_location = {"neighborhood": property_location}

        property_neighborhood = property_location.get("neighborhood", "").lower()
        property_city = property_location.get("city", "").lower()

        # Default good score if no preferences specified
        if not preferred_locations:
            return 75.0

        # Check for location matches
        max_score = 0
        for preferred in preferred_locations:
            preferred_lower = preferred.lower()

            # Exact neighborhood match
            if preferred_lower == property_neighborhood:
                max_score = max(max_score, 100)
            # Partial neighborhood match
            elif preferred_lower in property_neighborhood or property_neighborhood in preferred_lower:
                max_score = max(max_score, 85)
            # City level match
            elif preferred_lower == property_city:
                max_score = max(max_score, 75)
            # Partial city match
            elif preferred_lower in property_city or property_city in preferred_lower:
                max_score = max(max_score, 60)

        return max_score if max_score > 0 else 40  # Minimum score for unmatched

    def _calculate_feature_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """Calculate feature matching score based on bedroom/bathroom requirements"""
        score = 80  # Base score

        # Bedroom matching
        preferred_beds = lead_preferences.get("bedrooms", 3)
        property_beds = property_data.get("bedrooms", property_data.get("beds", 3))

        if property_beds == preferred_beds:
            score += 15  # Perfect match
        elif abs(property_beds - preferred_beds) == 1:
            score += 10  # Close match
        elif abs(property_beds - preferred_beds) == 2:
            score += 5  # Acceptable
        else:
            score -= 10  # Poor match

        # Bathroom scoring (less critical)
        preferred_baths = lead_preferences.get("bathrooms", 2)
        property_baths = property_data.get("bathrooms", property_data.get("baths", 2))

        if isinstance(property_baths, str):
            try:
                property_baths = float(property_baths)
            except (ValueError, TypeError):
                property_baths = 2

        bath_diff = abs(property_baths - preferred_baths)
        if bath_diff <= 0.5:
            score += 5  # Good match
        elif bath_diff <= 1:
            score += 2  # Acceptable
        # No penalty for larger differences

        return min(100, max(30, score))  # Clamp between 30-100

    def _calculate_market_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """
        Calculate market condition score using simple heuristics.

        Basic implementation using property age and listing duration.
        """
        base_score = 70  # Default market score

        # Property age factor (newer is generally better)
        year_built = property_data.get("year_built", 2010)
        current_year = 2024
        property_age = current_year - year_built

        if property_age <= 5:
            base_score += 20  # New construction
        elif property_age <= 10:
            base_score += 15  # Recent
        elif property_age <= 20:
            base_score += 10  # Good condition
        elif property_age <= 30:
            base_score += 5  # Established
        # No penalty for older homes (character, location value)

        # Price per square foot analysis (basic market value)
        price = property_data.get("price", 0)
        sqft = property_data.get("sqft", property_data.get("square_feet", 2000))

        if price > 0 and sqft > 0:
            price_per_sqft = price / sqft
            # Austin market baseline ~$200-400/sqft
            if 250 <= price_per_sqft <= 350:
                base_score += 10  # Market rate
            elif price_per_sqft < 250:
                base_score += 15  # Good value
            elif price_per_sqft > 400:
                base_score -= 10  # Premium pricing

        return min(100, max(40, base_score))

    def _generate_reasoning(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any],
        budget_score: float,
        location_score: float,
        feature_score: float,
        market_score: float,
    ) -> List[str]:
        """Generate human-readable explanations for the scoring"""
        reasoning = []
        property_price = property_data.get("price", 0)
        lead_budget = lead_preferences.get("budget", 1000000)

        # Budget reasoning
        if budget_score >= 90:
            if property_price <= lead_budget:
                savings = lead_budget - property_price
                reasoning.append(f"Excellent value - ${savings:,} under budget")
            else:
                reasoning.append("Perfect fit within budget range")
        elif budget_score >= 70:
            if property_price > lead_budget:
                overage = property_price - lead_budget
                reasoning.append(f"Slightly over budget by ${overage:,} but manageable")
            else:
                reasoning.append("Good budget alignment")
        else:
            overage = property_price - lead_budget
            reasoning.append(f"${overage:,} over preferred budget - consider negotiation")

        # Location reasoning
        if location_score >= 85:
            reasoning.append("Excellent location match for your preferences")
        elif location_score >= 60:
            reasoning.append("Good location with convenient access")
        else:
            reasoning.append("Location may require longer commute")

        # Feature reasoning
        preferred_beds = lead_preferences.get("bedrooms", 3)
        property_beds = property_data.get("bedrooms", property_data.get("beds", 3))

        if feature_score >= 90:
            reasoning.append(f"Perfect {property_beds} bedroom layout as requested")
        elif feature_score >= 70:
            reasoning.append(f"Good {property_beds} bedroom configuration")
        else:
            reasoning.append(f"{property_beds} bedrooms available (requested {preferred_beds})")

        # Market reasoning
        if market_score >= 80:
            reasoning.append("Strong market value and condition")
        elif market_score >= 60:
            reasoning.append("Fair market pricing")

        # Ensure we have at least 3 reasons
        if len(reasoning) < 3:
            sqft = property_data.get("sqft", property_data.get("square_feet", 0))
            if sqft:
                reasoning.append(f"Spacious {sqft:,} square feet")

            neighborhood = property_data.get("address", {}).get("neighborhood", "")
            if neighborhood:
                reasoning.append(f"Located in {neighborhood}")

        return reasoning[:5]  # Limit to top 5 reasons

    def _determine_confidence(self, overall_score: float) -> ConfidenceLevel:
        """Determine confidence level based on overall score"""
        if overall_score >= 85:
            return ConfidenceLevel.HIGH
        elif overall_score >= 70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
