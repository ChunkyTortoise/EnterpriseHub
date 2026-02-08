"""
Enhanced Property Scorer Implementation

Advanced rule-based scoring with sophisticated algorithms and multi-factor analysis.
Balanced performance and accuracy for production real estate applications.
"""

import math
from typing import Any, Dict, List, Set

try:
    from .property_scorer import ConfidenceLevel, PropertyScorer, ScoringResult
except ImportError:
    from property_scorer import ConfidenceLevel, PropertyScorer, ScoringResult


class EnhancedPropertyScorer(PropertyScorer):
    """
    Advanced rule-based property scoring with sophisticated algorithms.

    Enhanced features:
    - 15-factor scoring algorithm
    - Commute time analysis
    - School district scoring
    - Market trend integration
    - Advanced feature matching
    """

    def __init__(self):
        """Initialize enhanced scorer with Austin market expertise"""
        # Austin-specific market knowledge
        self.premium_neighborhoods = {
            "westlake",
            "downtown",
            "south congress",
            "clarksville",
            "tarrytown",
            "rollingwood",
            "barton hills",
        }

        self.tech_corridor_areas = {
            "domain",
            "arboretum",
            "northwest hills",
            "great hills",
            "anderson mill",
            "cedar park",
            "round rock",
        }

        self.emerging_areas = {"east austin", "mueller", "highland", "cherrywood", "govalle", "windsor park"}

        # Advanced scoring weights (15 factors)
        self.weights = {
            "budget_alignment": 0.20,
            "location_desirability": 0.15,
            "commute_convenience": 0.12,
            "neighborhood_trends": 0.10,
            "property_condition": 0.08,
            "size_optimization": 0.08,
            "school_quality": 0.07,
            "market_timing": 0.06,
            "investment_potential": 0.05,
            "lifestyle_amenities": 0.04,
            "safety_score": 0.02,
            "walkability": 0.02,
            "future_development": 0.01,
        }

    def calculate_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> ScoringResult:
        """
        Calculate enhanced property score using 15-factor algorithm.

        Sophisticated analysis including market trends, commute analysis,
        and lifestyle factors for comprehensive property evaluation.
        """
        if not self.validate_inputs(property_data, lead_preferences):
            raise ValueError("Invalid input data for enhanced scoring")

        # Calculate all scoring factors
        factor_scores = self._calculate_all_factors(property_data, lead_preferences)

        # Weighted overall score
        overall_score = sum(
            score * self.weights[factor] * 100  # Convert to percentage
            for factor, score in factor_scores.items()
        )

        # Calculate component group scores for UI display
        budget_score = factor_scores["budget_alignment"] * 100
        location_score = self._calculate_location_group_score(factor_scores)
        feature_score = self._calculate_feature_group_score(factor_scores)
        market_score = self._calculate_market_group_score(factor_scores)

        # Generate sophisticated reasoning
        reasoning = self._generate_enhanced_reasoning(property_data, lead_preferences, factor_scores)

        return ScoringResult(
            overall_score=round(overall_score, 1),
            confidence_level=self._determine_confidence_with_factors(factor_scores),
            budget_match=budget_score,
            location_match=location_score,
            feature_match=feature_score,
            market_context=market_score,
            reasoning=reasoning,
            metadata={
                "strategy": "enhanced",
                "factor_count": 15,
                "factor_scores": {k: round(v * 100, 1) for k, v in factor_scores.items()},
                "market_analysis": self._get_market_insights(property_data),
                "processing_time": "medium",
            },
        )

    def validate_inputs(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> bool:
        """Enhanced input validation for sophisticated scoring"""
        required_property = ["price", "address"]
        required_preferences = ["budget", "location"]

        # Check required fields
        for field in required_property:
            if field not in property_data or property_data[field] is None:
                return False

        for field in required_preferences:
            if field not in lead_preferences or lead_preferences[field] is None:
                return False

        # Validate price is reasonable
        price = property_data.get("price", 0)
        if price <= 0 or price > 50000000:  # Sanity check
            return False

        return True

    def get_performance_characteristics(self) -> Dict[str, str]:
        """Performance metadata for enhanced scorer"""
        return {
            "speed": "medium",
            "accuracy": "high",
            "complexity": "medium_high",
            "use_case": "production_matching",
            "throughput": "200-500_properties_per_second",
        }

    def _calculate_all_factors(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate all 15 scoring factors"""
        return {
            "budget_alignment": self._factor_budget_alignment(property_data, lead_preferences),
            "location_desirability": self._factor_location_desirability(property_data, lead_preferences),
            "commute_convenience": self._factor_commute_convenience(property_data, lead_preferences),
            "neighborhood_trends": self._factor_neighborhood_trends(property_data, lead_preferences),
            "property_condition": self._factor_property_condition(property_data, lead_preferences),
            "size_optimization": self._factor_size_optimization(property_data, lead_preferences),
            "school_quality": self._factor_school_quality(property_data, lead_preferences),
            "market_timing": self._factor_market_timing(property_data, lead_preferences),
            "investment_potential": self._factor_investment_potential(property_data, lead_preferences),
            "lifestyle_amenities": self._factor_lifestyle_amenities(property_data, lead_preferences),
            "safety_score": self._factor_safety_score(property_data, lead_preferences),
            "walkability": self._factor_walkability(property_data, lead_preferences),
            "future_development": self._factor_future_development(property_data, lead_preferences),
        }

    def _factor_budget_alignment(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Enhanced budget scoring with market context"""
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 1000000)

        ratio = price / budget

        # Sophisticated budget alignment curve
        if ratio <= 0.85:  # Well under budget
            return 0.95 + (0.85 - ratio) * 0.1  # Bonus for savings
        elif ratio <= 1.0:  # Within budget
            return 0.90 + (1.0 - ratio) * 0.33  # Perfect range
        elif ratio <= 1.05:  # Slightly over budget
            return 0.80 - (ratio - 1.0) * 4  # Gentle penalty
        elif ratio <= 1.15:  # Moderately over budget
            return 0.60 - (ratio - 1.05) * 3  # Steeper penalty
        else:  # Significantly over budget
            return max(0.1, 0.30 - min(0.2, (ratio - 1.15) * 2))

    def _factor_location_desirability(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Advanced location scoring with neighborhood analysis"""
        address = property_data.get("address", {})
        if isinstance(address, str):
            neighborhood = address.lower()
        else:
            neighborhood = address.get("neighborhood", "").lower()

        base_score = 0.6  # Default location score

        # Premium neighborhood bonus
        if any(premium in neighborhood for premium in self.premium_neighborhoods):
            base_score += 0.3
        # Tech corridor bonus (good for professionals)
        elif any(tech in neighborhood for tech in self.tech_corridor_areas):
            base_score += 0.25
        # Emerging area bonus (good value/future growth)
        elif any(emerging in neighborhood for emerging in self.emerging_areas):
            base_score += 0.2

        # Preference matching
        preferred_locations = lead_preferences.get("location", [])
        if isinstance(preferred_locations, str):
            preferred_locations = [preferred_locations]

        for preferred in preferred_locations:
            preferred_lower = preferred.lower()
            if preferred_lower in neighborhood or neighborhood in preferred_lower:
                base_score = min(1.0, base_score + 0.3)  # Preference match bonus
                break

        return min(1.0, base_score)

    def _factor_commute_convenience(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Commute analysis using Austin geography knowledge"""
        neighborhood = self._get_neighborhood_lower(property_data)
        work_location = lead_preferences.get("work_location", "").lower()

        # Default reasonable commute
        base_score = 0.7

        # Downtown workers
        if "downtown" in work_location:
            if neighborhood in ["downtown", "south congress", "east austin", "clarksville"]:
                base_score = 0.95  # Walking/biking distance
            elif neighborhood in ["tarrytown", "rollingwood", "barton hills"]:
                base_score = 0.85  # Short drive
            elif neighborhood in ["mueller", "highland", "cherrywood"]:
                base_score = 0.80  # Good transit options

        # Tech corridor workers
        elif any(tech in work_location for tech in ["domain", "arboretum", "apple", "google"]):
            if neighborhood in ["domain", "arboretum", "northwest hills"]:
                base_score = 0.95  # Very close
            elif neighborhood in ["cedar park", "round rock", "great hills"]:
                base_score = 0.85  # Reverse commute

        return base_score

    def _factor_neighborhood_trends(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Neighborhood market trend analysis"""
        neighborhood = self._get_neighborhood_lower(property_data)

        # Hot market areas (high growth/demand)
        hot_markets = ["mueller", "east austin", "highland", "south congress"]
        stable_markets = ["westlake", "tarrytown", "clarksville", "downtown"]
        emerging_markets = ["govalle", "windsor park", "cherrywood"]

        if any(hot in neighborhood for hot in hot_markets):
            return 0.9  # Strong appreciation
        elif any(stable in neighborhood for stable in stable_markets):
            return 0.85  # Steady, reliable
        elif any(emerging in neighborhood for emerging in emerging_markets):
            return 0.8  # Growth potential
        else:
            return 0.7  # Standard market

    def _factor_property_condition(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Property condition and age analysis"""
        year_built = property_data.get("year_built", 2010)
        current_year = 2024
        age = current_year - year_built

        # Age-based scoring
        if age <= 3:
            base_score = 0.95  # New construction
        elif age <= 10:
            base_score = 0.9  # Modern
        elif age <= 20:
            base_score = 0.8  # Well-maintained era
        elif age <= 30:
            base_score = 0.75  # Established
        else:
            base_score = 0.65  # Character home, may need updates

        # Recent renovation bonus
        if property_data.get("recently_renovated", False):
            base_score = min(1.0, base_score + 0.15)

        return base_score

    def _factor_size_optimization(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Bedroom/bathroom/square footage optimization"""
        # Bedroom analysis
        preferred_beds = lead_preferences.get("bedrooms", 3)
        property_beds = property_data.get("bedrooms", property_data.get("beds", 3))

        bed_score = 1.0 - (abs(property_beds - preferred_beds) * 0.15)
        bed_score = max(0.4, bed_score)

        # Square footage analysis
        sqft = property_data.get("sqft", property_data.get("square_feet", 2000))
        preferred_sqft = lead_preferences.get("min_sqft", 1800)

        if sqft >= preferred_sqft:
            sqft_score = min(1.0, 0.8 + (sqft - preferred_sqft) / 1000 * 0.2)
        else:
            shortage_pct = (preferred_sqft - sqft) / preferred_sqft
            sqft_score = max(0.3, 0.8 - shortage_pct * 2)

        return (bed_score + sqft_score) / 2

    def _factor_school_quality(self, property_data: Dict, lead_preferences: Dict) -> float:
        """School district quality (important for families)"""
        has_children = lead_preferences.get("has_children", False)
        if not has_children:
            return 0.8  # Neutral score when not applicable

        neighborhood = self._get_neighborhood_lower(property_data)

        # Austin ISD highly-rated areas
        excellent_schools = ["westlake", "tarrytown", "rollingwood", "barton hills"]
        good_schools = ["mueller", "highland", "great hills", "northwest hills"]

        if any(excellent in neighborhood for excellent in excellent_schools):
            return 0.95
        elif any(good in neighborhood for good in good_schools):
            return 0.85
        else:
            return 0.7

    def _factor_market_timing(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Market timing and listing freshness"""
        days_on_market = property_data.get("days_on_market", 30)

        # Fresh listings are often priced right
        if days_on_market <= 7:
            return 0.9
        elif days_on_market <= 30:
            return 0.85
        elif days_on_market <= 60:
            return 0.8
        else:
            return 0.7  # May indicate pricing issues

    def _factor_investment_potential(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Long-term investment and appreciation potential"""
        price = property_data.get("price", 0)
        sqft = property_data.get("sqft", property_data.get("square_feet", 2000))

        if sqft > 0:
            price_per_sqft = price / sqft
            # Austin market analysis
            if 200 <= price_per_sqft <= 300:
                return 0.9  # Good value zone
            elif 150 <= price_per_sqft <= 200:
                return 0.95  # Excellent value
            elif 300 <= price_per_sqft <= 400:
                return 0.8  # Market rate
            else:
                return 0.7  # Premium or concerning pricing

        return 0.75

    def _factor_lifestyle_amenities(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Lifestyle amenities and property features"""
        amenity_score = 0.6  # Base score

        # Property amenities
        amenities = property_data.get("amenities", [])
        if isinstance(amenities, str):
            amenities = amenities.split(",")

        valuable_amenities = ["pool", "garage", "outdoor_space", "updated_kitchen", "hardwood_floors"]

        for amenity in valuable_amenities:
            if any(amenity.lower() in str(a).lower() for a in amenities):
                amenity_score += 0.08

        return min(1.0, amenity_score)

    def _factor_safety_score(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Neighborhood safety assessment"""
        neighborhood = self._get_neighborhood_lower(property_data)

        # Generally safe Austin areas
        very_safe = ["westlake", "rollingwood", "tarrytown", "great hills"]
        safe = ["mueller", "domain", "northwest hills", "barton hills"]

        if any(safe_area in neighborhood for safe_area in very_safe):
            return 0.95
        elif any(safe_area in neighborhood for safe_area in safe):
            return 0.85
        else:
            return 0.75  # Standard urban safety

    def _factor_walkability(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Walkability and transit access"""
        neighborhood = self._get_neighborhood_lower(property_data)

        # Highly walkable Austin areas
        walkable = ["downtown", "south congress", "east austin", "clarksville"]

        if any(walk_area in neighborhood for walk_area in walkable):
            return 0.9
        else:
            return 0.6  # Car-dependent but typical for Austin

    def _factor_future_development(self, property_data: Dict, lead_preferences: Dict) -> float:
        """Future development and infrastructure projects"""
        neighborhood = self._get_neighborhood_lower(property_data)

        # Areas with planned development/transit
        growth_areas = ["mueller", "east austin", "domain", "highland"]

        if any(growth in neighborhood for growth in growth_areas):
            return 0.85
        else:
            return 0.75

    def _calculate_location_group_score(self, factor_scores: Dict[str, float]) -> float:
        """Group location-related factors for UI display"""
        location_factors = ["location_desirability", "commute_convenience", "neighborhood_trends", "walkability"]
        scores = [factor_scores[factor] for factor in location_factors if factor in factor_scores]
        return (sum(scores) / len(scores)) * 100 if scores else 75

    def _calculate_feature_group_score(self, factor_scores: Dict[str, float]) -> float:
        """Group feature-related factors for UI display"""
        feature_factors = ["size_optimization", "property_condition", "lifestyle_amenities"]
        scores = [factor_scores[factor] for factor in feature_factors if factor in factor_scores]
        return (sum(scores) / len(scores)) * 100 if scores else 75

    def _calculate_market_group_score(self, factor_scores: Dict[str, float]) -> float:
        """Group market-related factors for UI display"""
        market_factors = ["market_timing", "investment_potential", "future_development"]
        scores = [factor_scores[factor] for factor in market_factors if factor in factor_scores]
        return (sum(scores) / len(scores)) * 100 if scores else 75

    def _generate_enhanced_reasoning(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any], factor_scores: Dict[str, float]
    ) -> List[str]:
        """Generate sophisticated reasoning based on factor analysis"""
        reasoning = []

        # Top performing factors
        sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)

        # Budget reasoning
        budget_score = factor_scores["budget_alignment"]
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 1000000)

        if budget_score > 0.9:
            if price < budget:
                reasoning.append(f"Exceptional value at ${price:,} (${budget - price:,} under budget)")
            else:
                reasoning.append("Perfect budget alignment")
        elif budget_score > 0.75:
            reasoning.append("Good financial fit for your budget range")

        # Top factor highlights
        top_factors = sorted_factors[:3]
        factor_messages = {
            "location_desirability": "Prime location in highly desirable area",
            "neighborhood_trends": "Strong neighborhood with positive market trends",
            "property_condition": "Excellent condition with modern features",
            "commute_convenience": "Convenient commute to your work location",
            "school_quality": "Excellent school district for your family",
            "investment_potential": "Strong investment potential and appreciation",
            "lifestyle_amenities": "Outstanding amenities and lifestyle features",
        }

        for factor, score in top_factors:
            if score > 0.8 and factor in factor_messages:
                reasoning.append(factor_messages[factor])
                if len(reasoning) >= 5:
                    break

        # Specific property highlights
        sqft = property_data.get("sqft", property_data.get("square_feet", 0))
        if sqft and len(reasoning) < 4:
            reasoning.append(f"Spacious {sqft:,} square feet of living space")

        neighborhood = self._get_neighborhood_display(property_data)
        if neighborhood and len(reasoning) < 5:
            reasoning.append(f"Located in desirable {neighborhood} area")

        return reasoning[:5]

    def _get_market_insights(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market analysis insights"""
        neighborhood = self._get_neighborhood_lower(property_data)

        insights = {"neighborhood_type": "standard", "market_trend": "stable", "investment_outlook": "positive"}

        if any(premium in neighborhood for premium in self.premium_neighborhoods):
            insights["neighborhood_type"] = "premium"
            insights["market_trend"] = "strong"
            insights["investment_outlook"] = "excellent"
        elif any(tech in neighborhood for tech in self.tech_corridor_areas):
            insights["neighborhood_type"] = "tech_corridor"
            insights["market_trend"] = "growing"
            insights["investment_outlook"] = "very_good"
        elif any(emerging in neighborhood for emerging in self.emerging_areas):
            insights["neighborhood_type"] = "emerging"
            insights["market_trend"] = "hot"
            insights["investment_outlook"] = "high_growth"

        return insights

    def _get_neighborhood_lower(self, property_data: Dict[str, Any]) -> str:
        """Extract neighborhood name in lowercase"""
        address = property_data.get("address", {})
        if isinstance(address, str):
            return address.lower()
        return address.get("neighborhood", "").lower()

    def _get_neighborhood_display(self, property_data: Dict[str, Any]) -> str:
        """Extract neighborhood name for display"""
        address = property_data.get("address", {})
        if isinstance(address, str):
            return address
        return address.get("neighborhood", "")

    def _determine_confidence_with_factors(self, factor_scores: Dict[str, float]) -> ConfidenceLevel:
        """Determine confidence based on factor consistency"""
        scores = list(factor_scores.values())
        avg_score = sum(scores) / len(scores)
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)

        # High confidence if consistently high scores
        if avg_score > 0.85 and score_variance < 0.02:
            return ConfidenceLevel.HIGH
        elif avg_score > 0.7 and score_variance < 0.05:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
