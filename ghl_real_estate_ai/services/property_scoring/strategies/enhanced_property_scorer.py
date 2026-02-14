"""
Enhanced Property Scorer Strategy
Advanced rule-based scoring with sophisticated algorithms and market context
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..interfaces.property_scorer import ConfidenceLevel, PropertyScorer, ScoringResult

logger = logging.getLogger(__name__)


class EnhancedPropertyScorer(PropertyScorer):
    """
    Enhanced property scoring with sophisticated algorithms

    This scorer provides advanced matching capabilities including:
    - Nuanced budget analysis with flexibility zones
    - Geographic proximity scoring
    - Weighted feature matching with priorities
    - Market timing analysis
    - Risk assessment
    - Opportunity identification

    Features:
    - Multi-tier budget analysis
    - Geographic distance calculations
    - Feature priority weighting
    - Market trend consideration
    - Price trend analysis
    - Comprehensive reasoning
    """

    def __init__(self, market_data: Optional[Dict[str, Any]] = None):
        super().__init__(name="Enhanced Property Scorer", version="1.1.0")
        self.market_data = market_data or self._get_default_market_data()

    def calculate_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> ScoringResult:
        """
        Calculate enhanced property score with sophisticated analysis

        Args:
            property_data: Property information
            lead_preferences: Lead preferences

        Returns:
            ScoringResult with detailed scoring breakdown
        """
        self.validate_inputs(property_data, lead_preferences)

        # Calculate component scores with enhanced algorithms
        budget_score = self._calculate_enhanced_budget_score(property_data, lead_preferences)
        location_score = self._calculate_enhanced_location_score(property_data, lead_preferences)
        feature_score = self._calculate_enhanced_feature_score(property_data, lead_preferences)
        market_score = self._calculate_enhanced_market_score(property_data)

        # Dynamic weighting based on preferences
        weights = self._calculate_dynamic_weights(lead_preferences)
        overall_score = (
            budget_score * weights["budget"]
            + location_score * weights["location"]
            + feature_score * weights["features"]
            + market_score * weights["market"]
        )

        # Risk and opportunity analysis
        risk_factors = self._identify_risk_factors(property_data, lead_preferences)
        opportunities = self._identify_opportunities(property_data, lead_preferences)

        # Generate enhanced reasoning
        reasoning = self._generate_enhanced_reasoning(
            property_data, lead_preferences, budget_score, location_score, feature_score, market_score
        )

        # Determine confidence level with enhanced criteria
        confidence_level = self._determine_enhanced_confidence_level(
            overall_score, budget_score, feature_score, risk_factors
        )

        return ScoringResult(
            overall_score=round(overall_score, 1),
            confidence_level=confidence_level,
            budget_score=round(budget_score, 1),
            location_score=round(location_score, 1),
            feature_score=round(feature_score, 1),
            market_score=round(market_score, 1),
            reasoning=reasoning,
            risk_factors=risk_factors,
            opportunities=opportunities,
            match_insights=self._generate_match_insights(property_data, lead_preferences, overall_score),
            scorer_type=self.name,
            scoring_timestamp=datetime.now().isoformat(),
            model_version=self.version,
        )

    def validate_inputs(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> bool:
        """Enhanced validation with detailed checks"""
        # Basic validation from parent
        super().validate_inputs(property_data, lead_preferences)

        # Enhanced validation
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)

        # Price reasonableness check
        if price > 10_000_000:  # $10M seems excessive for most residential
            logger.warning(f"Unusually high property price: ${price:,}")

        if budget > 5_000_000:  # $5M seems high for typical leads
            logger.warning(f"Unusually high budget: ${budget:,}")

        return True

    def _calculate_enhanced_budget_score(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> float:
        """Enhanced budget scoring with flexibility zones"""
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)

        if budget == 0:
            return 60.0  # Neutral score if no budget

        price_ratio = price / budget

        # Enhanced scoring with more granular bands
        if price_ratio <= 0.75:  # Significantly under budget
            return 100.0
        elif price_ratio <= 0.85:  # Comfortably under budget
            return 98.0
        elif price_ratio <= 0.95:  # Just under budget
            return 95.0
        elif price_ratio <= 1.0:  # At budget
            return 92.0
        elif price_ratio <= 1.02:  # Tiny stretch (2%)
            return 88.0
        elif price_ratio <= 1.05:  # Small stretch (5%)
            return 80.0
        elif price_ratio <= 1.08:  # Moderate stretch (8%)
            return 70.0
        elif price_ratio <= 1.1:  # Significant stretch (10%)
            return 55.0
        elif price_ratio <= 1.15:  # Major stretch (15%)
            return 35.0
        elif price_ratio <= 1.2:  # Very high stretch (20%)
            return 20.0
        else:  # Unrealistic stretch
            return max(5.0, 50.0 - (price_ratio - 1.2) * 100.0)

    def _calculate_enhanced_location_score(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> float:
        """Enhanced location scoring with geographic analysis"""
        pref_location = lead_preferences.get("location")
        if not pref_location:
            return 75.0  # Neutral score

        address = property_data.get("address", {})
        if isinstance(address, str):
            # Handle legacy string format
            prop_location = address.lower()
            neighborhood = ""
            city = ""
        else:
            # Handle structured address
            neighborhood = address.get("neighborhood", "").lower()
            city = address.get("city", "").lower()
            prop_location = f"{neighborhood} {city}".lower()

        pref_location_lower = pref_location.lower()

        # Exact neighborhood match
        if pref_location_lower == neighborhood:
            return 100.0

        # Neighborhood partial match
        if pref_location_lower in neighborhood or neighborhood in pref_location_lower:
            return 95.0

        # City match
        if pref_location_lower == city:
            return 85.0

        # Adjacent area analysis (enhanced with real estate knowledge)
        adjacent_score = self._calculate_adjacent_area_score(pref_location_lower, neighborhood)
        if adjacent_score > 0:
            return adjacent_score

        # Keyword matching with weights
        pref_keywords = pref_location_lower.split()
        neighborhood_keywords = neighborhood.split()
        city_keywords = city.split()

        matches = 0
        total_keywords = len(pref_keywords)

        for keyword in pref_keywords:
            if keyword in neighborhood_keywords:
                matches += 1  # Neighborhood match is strongest
            elif keyword in city_keywords:
                matches += 0.7  # City match is good
            elif keyword in prop_location:
                matches += 0.5  # General location match

        if matches > 0:
            base_score = 50.0 + (matches / total_keywords) * 35.0
            return min(85.0, base_score)

        return 30.0  # No meaningful match

    def _calculate_adjacent_area_score(self, pref_location: str, neighborhood: str) -> float:
        """Calculate score for adjacent/similar areas"""
        # Enhanced neighborhood clusters with real estate knowledge
        area_clusters = {
            "downtown": {
                "core": ["downtown", "central", "urban core"],
                "adjacent": ["east rancho_cucamonga", "day creek", "rainey district"],
                "similar": ["deep ellum", "uptown"],
            },
            "westlake": {
                "core": ["westlake", "west lake"],
                "adjacent": ["deer creek", "bee cave", "lakeway"],
                "similar": ["north rancho", "alta loma estates"],
            },
            "ontario_mills": {
                "core": ["ontario_mills", "north rancho_cucamonga"],
                "adjacent": ["round rock", "cedar park", "pflugerville"],
                "similar": ["arboretum", "north rancho"],
            },
        }

        for cluster_name, cluster_data in area_clusters.items():
            # Check if preferred location is in this cluster
            if any(area in pref_location for area in cluster_data["core"]):
                # Check neighborhood against cluster areas
                if any(area in neighborhood for area in cluster_data["core"]):
                    return 100.0
                elif any(area in neighborhood for area in cluster_data["adjacent"]):
                    return 75.0
                elif any(area in neighborhood for area in cluster_data["similar"]):
                    return 65.0

        return 0.0

    def _calculate_enhanced_feature_score(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> float:
        """Enhanced feature scoring with weighted priorities"""
        score = 0.0
        max_possible_score = 0.0

        # Bedroom matching with flexibility
        pref_bedrooms = lead_preferences.get("bedrooms")
        if pref_bedrooms:
            prop_bedrooms = property_data.get("bedrooms", 0)
            bedroom_weight = 25.0
            max_possible_score += bedroom_weight

            if prop_bedrooms == pref_bedrooms:
                score += bedroom_weight  # Perfect match
            elif prop_bedrooms == pref_bedrooms + 1:
                score += bedroom_weight * 0.95  # Bonus room is good
            elif prop_bedrooms == pref_bedrooms - 1:
                score += bedroom_weight * 0.7  # One less is acceptable
            elif prop_bedrooms > pref_bedrooms:
                score += bedroom_weight * 0.8  # More space is generally good
            else:
                score += bedroom_weight * 0.3  # Significantly fewer bedrooms

        # Must-have features (critical)
        must_haves = lead_preferences.get("must_haves", [])
        if must_haves:
            must_have_weight = 40.0
            max_possible_score += must_have_weight

            prop_features = self._extract_all_features(property_data)
            satisfied_must_haves = 0

            for must_have in must_haves:
                if self._feature_exists(must_have, prop_features):
                    satisfied_must_haves += 1

            satisfaction_ratio = satisfied_must_haves / len(must_haves)
            if satisfaction_ratio == 1.0:
                score += must_have_weight  # All must-haves satisfied
            else:
                # Partial satisfaction with penalty for missing critical features
                score += must_have_weight * satisfaction_ratio * 0.6

        # Nice-to-have features (bonus)
        nice_to_haves = lead_preferences.get("nice_to_haves", [])
        if nice_to_haves:
            nice_to_have_weight = 20.0
            max_possible_score += nice_to_have_weight

            prop_features = self._extract_all_features(property_data)
            satisfied_nice_to_haves = 0

            for nice_to_have in nice_to_haves:
                if self._feature_exists(nice_to_have, prop_features):
                    satisfied_nice_to_haves += 1

            bonus_ratio = satisfied_nice_to_haves / len(nice_to_haves)
            score += nice_to_have_weight * bonus_ratio

        # Property type matching
        pref_type = lead_preferences.get("property_type")
        if pref_type:
            type_weight = 15.0
            max_possible_score += type_weight
            prop_type = property_data.get("property_type", "").lower()

            if pref_type.lower() == prop_type:
                score += type_weight  # Exact match
            elif pref_type.lower() in prop_type or prop_type in pref_type.lower():
                score += type_weight * 0.8  # Close match

        # Normalize score
        if max_possible_score > 0:
            return min(100.0, (score / max_possible_score) * 100.0)
        else:
            return 80.0  # Default score when no features specified

    def _extract_all_features(self, property_data: Dict[str, Any]) -> List[str]:
        """Extract all features from property data for matching"""
        features = []

        # Explicit amenities
        amenities = property_data.get("amenities", [])
        features.extend([a.lower() for a in amenities])

        # Derived features from other fields
        if property_data.get("garage", False) or "garage" in str(property_data).lower():
            features.append("garage")

        if property_data.get("pool", False) or "pool" in str(property_data).lower():
            features.append("pool")

        # School rating as feature
        school_rating = property_data.get("school_rating", 0)
        if school_rating >= 8:
            features.append("good_schools")

        # Walkability score as feature
        walkability = property_data.get("walkability_score", 0)
        if walkability >= 70:
            features.append("walkable")

        return features

    def _feature_exists(self, feature: str, prop_features: List[str]) -> bool:
        """Check if a feature exists using enhanced matching"""
        feature_lower = feature.lower()

        # Direct match
        if feature_lower in prop_features:
            return True

        # Keyword matching for complex features
        feature_keywords = {
            "garage": ["garage", "covered parking", "carport"],
            "pool": ["pool", "swimming", "spa"],
            "garden": ["garden", "landscaped", "yard"],
            "good_schools": ["school", "rating", "education", "excellent schools"],
            "walkable": ["walkable", "walk score", "transit"],
            "modern": ["modern", "updated", "renovated", "contemporary"],
            "quiet": ["quiet", "peaceful", "cul-de-sac"],
            "view": ["view", "scenic", "overlook", "vista"],
        }

        keywords = feature_keywords.get(feature_lower, [feature_lower])
        return any(keyword in " ".join(prop_features) for keyword in keywords)

    def _calculate_enhanced_market_score(self, property_data: Dict[str, Any]) -> float:
        """Enhanced market scoring with comprehensive analysis"""
        base_score = 70.0

        # Days on market analysis
        days_on_market = property_data.get("days_on_market", 30)
        market_median_dom = self.market_data.get("median_days_on_market", 25)

        if days_on_market <= market_median_dom * 0.3:  # Hot property
            base_score += 25.0
        elif days_on_market <= market_median_dom * 0.7:  # Moving well
            base_score += 15.0
        elif days_on_market <= market_median_dom:  # Normal pace
            base_score += 10.0
        elif days_on_market <= market_median_dom * 1.5:  # Slower
            base_score -= 5.0
        elif days_on_market <= market_median_dom * 2:  # Stale
            base_score -= 15.0
        else:  # Very stale
            base_score -= 25.0

        # Price positioning analysis
        price_per_sqft = property_data.get("price_per_sqft")
        if price_per_sqft:
            market_median_psf = self.market_data.get("median_price_per_sqft", 280)
            psf_ratio = price_per_sqft / market_median_psf

            if 0.9 <= psf_ratio <= 1.1:  # Well-priced
                base_score += 15.0
            elif 0.8 <= psf_ratio < 0.9:  # Great value
                base_score += 20.0
            elif psf_ratio < 0.8:  # Potentially undervalued or issues
                base_score += 5.0
            elif 1.1 < psf_ratio <= 1.3:  # Premium pricing
                base_score -= 5.0
            else:  # Overpriced
                base_score -= 15.0

        # Property age and condition
        year_built = property_data.get("year_built")
        if year_built:
            current_year = datetime.now().year
            property_age = current_year - year_built

            if property_age <= 3:  # New construction
                base_score += 10.0
            elif property_age <= 10:  # Modern
                base_score += 5.0
            elif property_age <= 20:  # Established
                base_score += 0.0
            elif property_age <= 40:  # Mature
                base_score -= 3.0
            else:  # Older property
                base_score -= 8.0

        # Market trend consideration
        market_trend = self.market_data.get("price_trend", 0)
        if market_trend > 0.05:  # Strong appreciation
            base_score += 8.0
        elif market_trend > 0.02:  # Moderate appreciation
            base_score += 4.0
        elif market_trend < -0.02:  # Declining market
            base_score -= 5.0

        return max(10.0, min(100.0, base_score))

    def _calculate_dynamic_weights(self, lead_preferences: Dict[str, Any]) -> Dict[str, float]:
        """Calculate dynamic weights based on lead preferences"""
        # Default weights
        weights = {"budget": 0.35, "location": 0.30, "features": 0.25, "market": 0.10}

        # Adjust based on must-haves
        must_haves = lead_preferences.get("must_haves", [])
        if len(must_haves) >= 3:  # Feature-focused lead
            weights["features"] += 0.05
            weights["budget"] -= 0.03
            weights["market"] -= 0.02

        # Adjust based on budget constraints
        budget = lead_preferences.get("budget", 0)
        if budget > 1_000_000:  # High-budget lead may be less price-sensitive
            weights["budget"] -= 0.05
            weights["features"] += 0.03
            weights["location"] += 0.02

        # Adjust based on location specificity
        location = lead_preferences.get("location", "")
        if len(location.split()) > 2:  # Very specific location
            weights["location"] += 0.05
            weights["budget"] -= 0.03
            weights["market"] -= 0.02

        return weights

    def _identify_risk_factors(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors"""
        risks = []

        # Budget risks
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)
        if budget > 0 and price > budget * 1.1:
            overage = price - budget
            risks.append(f"${overage / 1000:.0f}k over budget - financing may be challenging")

        # Market risks
        days_on_market = property_data.get("days_on_market", 30)
        if days_on_market > 90:
            risks.append("Property has been on market for extended period")

        # Price risks
        price_per_sqft = property_data.get("price_per_sqft")
        if price_per_sqft:
            market_median_psf = self.market_data.get("median_price_per_sqft", 280)
            if price_per_sqft > market_median_psf * 1.3:
                risks.append("Price per sq ft significantly above market median")

        # Feature risks
        must_haves = lead_preferences.get("must_haves", [])
        prop_features = self._extract_all_features(property_data)
        missing_must_haves = [mh for mh in must_haves if not self._feature_exists(mh, prop_features)]
        if missing_must_haves:
            risks.append(f"Missing required features: {', '.join(missing_must_haves)}")

        return risks

    def _identify_opportunities(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> List[str]:
        """Identify potential opportunities"""
        opportunities = []

        # Budget opportunities
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)
        if budget > 0 and price <= budget * 0.85:
            savings = budget - price
            opportunities.append(f"${savings / 1000:.0f}k under budget for upgrades or savings")

        # Market opportunities
        days_on_market = property_data.get("days_on_market", 30)
        if days_on_market > 60:
            opportunities.append("Potential for price negotiation due to extended listing time")

        # Feature opportunities
        bedrooms = property_data.get("bedrooms", 0)
        pref_bedrooms = lead_preferences.get("bedrooms", 0)
        if pref_bedrooms > 0 and bedrooms > pref_bedrooms:
            extra_rooms = bedrooms - pref_bedrooms
            opportunities.append(f"{extra_rooms} extra bedroom(s) for office, guest room, or storage")

        # Market timing
        market_trend = self.market_data.get("price_trend", 0)
        if market_trend > 0.05:
            opportunities.append("Strong market appreciation expected")

        return opportunities

    def _generate_enhanced_reasoning(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any],
        budget_score: float,
        location_score: float,
        feature_score: float,
        market_score: float,
    ) -> List[str]:
        """Generate comprehensive reasoning"""
        reasoning = []

        # Budget reasoning with specifics
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)
        if budget > 0:
            price_ratio = price / budget
            if price_ratio <= 0.85:
                savings = budget - price
                reasoning.append(f"Excellent value at ${savings / 1000:.0f}k under budget - room for improvements")
            elif price_ratio <= 0.95:
                savings = budget - price
                reasoning.append(f"Well-priced at ${savings / 1000:.0f}k under budget")
            elif price_ratio <= 1.0:
                reasoning.append("Priced perfectly within your budget")
            elif price_ratio <= 1.05:
                overage = price - budget
                reasoning.append(f"Slight stretch at ${overage / 1000:.0f}k over budget but strong value")

        # Location reasoning with context
        if location_score >= 95:
            reasoning.append("Perfect location match in your preferred area")
        elif location_score >= 85:
            reasoning.append("Excellent location in desirable nearby area")
        elif location_score >= 70:
            reasoning.append("Good location with convenient access to preferred areas")

        # Feature reasoning with details
        must_haves = lead_preferences.get("must_haves", [])
        if must_haves:
            prop_features = self._extract_all_features(property_data)
            satisfied = [mh for mh in must_haves if self._feature_exists(mh, prop_features)]
            if len(satisfied) == len(must_haves):
                reasoning.append(f"Has all your must-have features: {', '.join(satisfied)}")
            elif satisfied:
                reasoning.append(f"Includes {len(satisfied)} of {len(must_haves)} must-have features")

        # Bedroom-specific reasoning
        bedrooms = property_data.get("bedrooms", 0)
        pref_bedrooms = lead_preferences.get("bedrooms")
        if pref_bedrooms and bedrooms >= pref_bedrooms:
            if bedrooms == pref_bedrooms:
                reasoning.append(f"Perfect {bedrooms}-bedroom layout as requested")
            else:
                extra = bedrooms - pref_bedrooms
                reasoning.append(f"{bedrooms} bedrooms with {extra} bonus room(s) for flexibility")

        # Market timing reasoning
        days_on_market = property_data.get("days_on_market", 30)
        if days_on_market <= 15:
            reasoning.append("Recently listed - act quickly in this competitive market")
        elif days_on_market > 60:
            reasoning.append("Extended listing time may provide negotiation opportunities")

        # Value proposition
        price_per_sqft = property_data.get("price_per_sqft")
        if price_per_sqft:
            market_median_psf = self.market_data.get("median_price_per_sqft", 280)
            if price_per_sqft <= market_median_psf * 0.9:
                reasoning.append(
                    f"Excellent price per sq ft at ${price_per_sqft:.0f} vs ${market_median_psf:.0f} market median"
                )

        return reasoning[:7]  # Limit to top 7 reasons

    def _determine_enhanced_confidence_level(
        self, overall_score: float, budget_score: float, feature_score: float, risk_factors: List[str]
    ) -> ConfidenceLevel:
        """Enhanced confidence level determination"""
        # Base confidence from score
        if overall_score >= 92:
            base_confidence = ConfidenceLevel.EXCELLENT
        elif overall_score >= 82:
            base_confidence = ConfidenceLevel.HIGH
        elif overall_score >= 65:
            base_confidence = ConfidenceLevel.MEDIUM
        else:
            base_confidence = ConfidenceLevel.LOW

        # Adjust for risk factors
        if len(risk_factors) >= 3:
            # Downgrade confidence due to multiple risks
            if base_confidence == ConfidenceLevel.EXCELLENT:
                return ConfidenceLevel.HIGH
            elif base_confidence == ConfidenceLevel.HIGH:
                return ConfidenceLevel.MEDIUM
            elif base_confidence == ConfidenceLevel.MEDIUM:
                return ConfidenceLevel.LOW

        # Adjust for critical component failures
        if budget_score < 50 or feature_score < 40:
            # Critical mismatch
            return ConfidenceLevel.LOW

        return base_confidence

    def _generate_match_insights(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any], overall_score: float
    ) -> Dict[str, Any]:
        """Generate detailed match insights"""
        return {
            "property_id": property_data.get("id", "unknown"),
            "score_band": self._get_score_band(overall_score),
            "key_strengths": self._identify_key_strengths(property_data, lead_preferences),
            "improvement_areas": self._identify_improvement_areas(property_data, lead_preferences),
            "recommendation": self._generate_recommendation(overall_score),
        }

    def _get_score_band(self, score: float) -> str:
        """Categorize score into bands"""
        if score >= 90:
            return "excellent_match"
        elif score >= 80:
            return "strong_match"
        elif score >= 70:
            return "good_match"
        elif score >= 60:
            return "fair_match"
        else:
            return "poor_match"

    def _identify_key_strengths(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> List[str]:
        """Identify the property's key strengths for this lead"""
        strengths = []

        # Check budget advantage
        price = property_data.get("price", 0)
        budget = lead_preferences.get("budget", 0)
        if budget > 0 and price <= budget * 0.9:
            strengths.append("excellent_value")

        # Check feature completeness
        must_haves = lead_preferences.get("must_haves", [])
        if must_haves:
            prop_features = self._extract_all_features(property_data)
            if all(self._feature_exists(mh, prop_features) for mh in must_haves):
                strengths.append("complete_feature_match")

        return strengths

    def _identify_improvement_areas(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> List[str]:
        """Identify areas where the property could be improved"""
        improvements = []

        # Check for missing features
        must_haves = lead_preferences.get("must_haves", [])
        prop_features = self._extract_all_features(property_data)
        missing = [mh for mh in must_haves if not self._feature_exists(mh, prop_features)]
        if missing:
            improvements.extend(missing)

        return improvements

    def _generate_recommendation(self, overall_score: float) -> str:
        """Generate action recommendation"""
        if overall_score >= 85:
            return "strongly_recommend"
        elif overall_score >= 75:
            return "recommend"
        elif overall_score >= 65:
            return "consider"
        else:
            return "pass"

    def _get_default_market_data(self) -> Dict[str, Any]:
        """Get default market data when not provided"""
        return {
            "median_price": 525000,
            "median_price_per_sqft": 280,
            "median_days_on_market": 25,
            "price_trend": 0.06,  # 6% annual appreciation
            "inventory_level": "low",
        }

    def get_supported_features(self) -> List[str]:
        """Get list of features supported by enhanced scorer"""
        return [
            "advanced_budget_analysis",
            "geographic_scoring",
            "weighted_feature_matching",
            "market_timing_analysis",
            "risk_assessment",
            "opportunity_identification",
            "dynamic_weighting",
            "comprehensive_reasoning",
            "confidence_adjustment",
            "match_insights",
        ]
