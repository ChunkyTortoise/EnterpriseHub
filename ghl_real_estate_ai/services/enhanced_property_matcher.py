"""
Enhanced Property Matcher with 15-Factor Contextual Algorithm

Extends the basic PropertyMatcher with:
- Lifestyle intelligence (schools, commute, walkability, safety)
- Behavioral adaptive weighting
- Market timing analysis
- Explainable AI reasoning
- Self-improving feedback loops
"""

import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import (
    DEFAULT_SEGMENT_WEIGHTS,
    FACTOR_WEIGHTS_BASE,
    AdaptiveWeights,
    BehavioralProfile,
    ContextualScores,
    FactorScore,
    LeadSegment,
    LifestyleScores,
    MarketTimingScore,
    MatchingContext,
    MatchReasoning,
    MatchScoreBreakdown,
    PropertyMatch,
    TraditionalScores,
)
from ghl_real_estate_ai.services.behavioral_weighting_engine import BehavioralWeightingEngine
from ghl_real_estate_ai.services.lifestyle_intelligence_service import LifestyleIntelligenceService
from ghl_real_estate_ai.services.market_timing_service import MarketTimingService
from ghl_real_estate_ai.services.match_reasoning_engine import MatchReasoningEngine
from ghl_real_estate_ai.services.predictive_buyer_scoring import PredictiveBuyerScoring
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

logger = get_logger(__name__)


class EnhancedPropertyMatcher(PropertyMatcher):
    """
    Advanced property matching with 15-factor algorithm and behavioral adaptation.

    Scoring Factors:
    Traditional (60%): budget, location, bedrooms, bathrooms, property_type, sqft
    Lifestyle (25%): schools, commute, walkability, safety
    Contextual (10%): HOA, lot_size, home_age, parking
    Market Timing (5%): days_on_market, price_trends, inventory
    """

    def __init__(self, listings_path: Optional[str] = None, enable_ml: bool = True):
        super().__init__(listings_path)
        self.enable_ml = enable_ml
        self.buyer_scoring = PredictiveBuyerScoring()

        # Load behavioral data and interaction history
        self._load_interaction_data()

        # Initialize specialized component services
        self.lifestyle_service = LifestyleIntelligenceService()
        self.behavioral_engine = BehavioralWeightingEngine()
        self.market_timing_service = MarketTimingService()
        self.reasoning_engine = MatchReasoningEngine()

    def find_enhanced_matches(
        self,
        preferences: Dict[str, Any],
        behavioral_profile: Optional[BehavioralProfile] = None,
        segment: Optional[LeadSegment] = None,
        limit: int = 10,
        min_score: float = 0.6,
    ) -> List[PropertyMatch]:
        """
        Find property matches using enhanced 15-factor algorithm.

        Args:
            preferences: Lead's stated preferences
            behavioral_profile: Past interaction patterns
            segment: Detected lead segment for weight adaptation
            limit: Maximum matches to return
            min_score: Minimum overall score threshold

        Returns:
            List of PropertyMatch objects with detailed scoring and reasoning
        """
        logger.info(f"Finding enhanced matches for {len(self.listings)} properties")

        # Create matching context
        context = self._create_matching_context(preferences, behavioral_profile, segment)

        # 1. Analyze behavioral profile if not provided
        if not context.behavioral_profile:
            context.behavioral_profile = self.behavioral_engine.analyze_behavioral_profile(
                context.lead_id, context.preferences
            )

        # 2. Calculate adaptive weights using behavioral engine
        adaptive_weights = self.behavioral_engine.calculate_adaptive_weights(
            context.behavioral_profile, context.preferences
        )

        matches = []

        for property_data in self.listings:
            try:
                # Apply strict budget filter if budget is specified
                budget = context.preferences.get("budget")
                if budget and property_data.get("price", 0) > budget * 1.15:  # allow 15% stretch for matches
                    continue

                # Calculate comprehensive score using specialized services
                score_breakdown = self._calculate_comprehensive_score(property_data, context, adaptive_weights)

                # Skip if below minimum threshold
                if score_breakdown.overall_score < min_score:
                    continue

                # Generate comprehensive reasoning using reasoning engine
                reasoning = self.reasoning_engine.generate_comprehensive_reasoning(
                    property_data, score_breakdown, preferences, behavioral_profile
                )

                # Create property match result
                match = PropertyMatch(
                    property=property_data,
                    overall_score=score_breakdown.overall_score,
                    score_breakdown=score_breakdown,
                    reasoning=reasoning,
                    match_rank=None,
                    generated_at=datetime.utcnow(),
                    lead_id=context.lead_id,
                    preferences_used=preferences,
                    predicted_engagement=self._predict_engagement(score_breakdown),
                    predicted_showing_request=self._predict_showing_probability(score_breakdown),
                    confidence_interval=self._calculate_confidence_interval(score_breakdown),
                )

                matches.append(match)

            except Exception as e:
                logger.error(f"Error scoring property {property_data.get('id', 'unknown')}: {e}")
                continue

        # Sort by overall score and assign ranks
        matches.sort(key=lambda x: x.overall_score, reverse=True)
        for i, match in enumerate(matches[:limit]):
            match.match_rank = i + 1

        logger.info(f"Generated {len(matches[:limit])} enhanced matches")
        return matches[:limit]

    def _calculate_comprehensive_score(
        self, property_data: Dict[str, Any], context: MatchingContext, adaptive_weights: AdaptiveWeights
    ) -> MatchScoreBreakdown:
        """Calculate comprehensive 15-factor score breakdown using specialized services."""

        # 1. Traditional Factors (budget, location, bedrooms, etc.)
        traditional_scores = self._score_traditional_factors(
            property_data, context.preferences, adaptive_weights.traditional_weights
        )

        # 2. Lifestyle Factors (schools, commute, walkability, safety)
        # Use specialized lifestyle intelligence service
        lifestyle_scores = self.lifestyle_service.calculate_lifestyle_score(
            property_data, context.preferences, context.behavioral_profile
        )

        # 3. Contextual Factors (HOA, lot size, age, parking)
        contextual_scores = self._score_contextual_factors(
            property_data, context.preferences, adaptive_weights.contextual_weights
        )

        # 4. Market Timing (days on market, pricing trends)
        # Use specialized market timing service
        market_timing_score = self.market_timing_service.calculate_market_timing_score(property_data)

        # Calculate weighted overall score
        # Using weights from adaptive_weights
        overall_score = (
            traditional_scores.budget.weighted_score
            + traditional_scores.location.weighted_score
            + traditional_scores.bedrooms.weighted_score
            + traditional_scores.bathrooms.weighted_score
            + traditional_scores.property_type.weighted_score
            + traditional_scores.sqft.weighted_score
            + lifestyle_scores.overall_score * 0.25  # Lifestyle weight 25%
            + contextual_scores.overall_score * 0.10  # Contextual weight 10%
            + market_timing_score.optimal_timing_score * adaptive_weights.market_timing_weight
        )

        # Calculate confidence and data completeness
        confidence_level = self._calculate_confidence_level(
            traditional_scores, lifestyle_scores, contextual_scores, market_timing_score
        )

        data_completeness = self._calculate_data_completeness(property_data, context.preferences)

        return MatchScoreBreakdown(
            traditional_scores=traditional_scores,
            lifestyle_scores=lifestyle_scores,
            contextual_scores=contextual_scores,
            market_timing_score=market_timing_score,
            adaptive_weights=adaptive_weights,
            overall_score=min(overall_score, 1.0),
            confidence_level=confidence_level,
            data_completeness=data_completeness,
        )

    def _score_traditional_factors(
        self, property_data: Dict[str, Any], preferences: Dict[str, Any], weights: Dict[str, float]
    ) -> TraditionalScores:
        """Score traditional real estate factors."""

        # Budget scoring with stretch tolerance
        budget_score = self._score_budget_match(
            property_data.get("price", 0), preferences.get("budget", 0), weights.get("budget", 0.20)
        )

        # Location scoring with fuzzy matching
        location_score = self._score_location_match(
            property_data.get("address", {}), preferences.get("location", ""), weights.get("location", 0.15)
        )

        # Bedroom scoring with tolerance
        bedrooms_score = self._score_bedrooms_match(
            property_data.get("bedrooms", 0), preferences.get("bedrooms", 0), weights.get("bedrooms", 0.10)
        )

        # Bathroom scoring
        bathrooms_score = self._score_bathrooms_match(
            property_data.get("bathrooms", 0), preferences.get("bathrooms", 0), weights.get("bathrooms", 0.05)
        )

        # Property type matching
        property_type_score = self._score_property_type_match(
            property_data.get("property_type", ""),
            preferences.get("property_type", ""),
            weights.get("property_type", 0.05),
        )

        # Square footage scoring
        sqft_score = self._score_sqft_match(
            property_data.get("sqft", 0),
            preferences.get("min_sqft", 0),
            preferences.get("max_sqft", 0),
            weights.get("sqft", 0.05),
        )

        return TraditionalScores(
            budget=budget_score,
            location=location_score,
            bedrooms=bedrooms_score,
            bathrooms=bathrooms_score,
            property_type=property_type_score,
            sqft=sqft_score,
        )

    def _score_lifestyle_factors(
        self, property_data: Dict[str, Any], context: MatchingContext, weights: Dict[str, float]
    ) -> LifestyleScores:
        """Score lifestyle compatibility factors."""

        # For now, implement basic scoring - will enhance with dedicated services

        # Schools scoring
        schools_score = self._score_schools_basic(property_data, weights.get("schools", 0.08))

        # Commute scoring (basic implementation)
        commute_score = self._score_commute_basic(property_data, weights.get("commute", 0.06))

        # Walkability scoring
        walkability_score = self._score_walkability_basic(property_data, weights.get("walkability", 0.06))

        # Safety scoring
        safety_score = self._score_safety_basic(property_data, weights.get("safety", 0.05))

        # Overall lifestyle score
        overall_score = (
            schools_score
            + commute_score
            + walkability_score
            + safety_score
            + weights.get("amenities_proximity", 0.02) * 0.5
        )

        # Placeholder objects - will implement full versions with dedicated services
        return LifestyleScores(
            schools=self._create_placeholder_school_score(property_data, schools_score),
            commute=self._create_placeholder_commute_score(property_data, commute_score),
            walkability=self._create_placeholder_walkability_score(property_data, walkability_score),
            safety=self._create_placeholder_safety_score(property_data, safety_score),
            amenities_proximity=0.5,  # Placeholder
            overall_score=overall_score,
        )

    def _score_contextual_factors(
        self, property_data: Dict[str, Any], preferences: Dict[str, Any], weights: Dict[str, float]
    ) -> ContextualScores:
        """Score contextual property factors."""

        # HOA fee scoring
        hoa_score = self._score_hoa_fee(
            property_data.get("hoa_fee", 0), preferences.get("max_hoa", 9999), weights.get("hoa_fee", 0.03)
        )

        # Lot size scoring
        lot_score = self._score_lot_size(
            property_data.get("lot_size_sqft", 0), preferences.get("min_lot_size", 0), weights.get("lot_size", 0.03)
        )

        # Home age scoring
        age_score = self._score_home_age(
            property_data.get("year_built", 2000), preferences.get("max_age", 999), weights.get("home_age", 0.02)
        )

        # Parking scoring (basic implementation)
        parking_score = self._score_parking_basic(property_data, weights.get("parking", 0.02))

        # Property condition (inferred from age and features)
        condition_score = self._score_property_condition(property_data, weights.get("property_condition", 0.02))

        overall_score = (
            hoa_score.weighted_score
            + lot_score.weighted_score
            + age_score.weighted_score
            + parking_score.weighted_score
            + condition_score.weighted_score
        )

        return ContextualScores(
            hoa_fee_score=hoa_score,
            lot_size_score=lot_score,
            home_age_score=age_score,
            parking_score=parking_score,
            property_condition_score=condition_score,
            overall_score=overall_score,
        )

    def _score_market_timing(self, property_data: Dict[str, Any], weight: float) -> MarketTimingScore:
        """Score market timing and opportunity factors."""

        days_on_market = property_data.get("days_on_market", 0)

        # Days on market scoring (longer = more negotiable)
        dom_score = self._calculate_dom_score(days_on_market)

        # Price trend scoring (placeholder - would integrate with price history)
        price_trend_score = 0.5  # Neutral for now

        # Inventory scarcity (placeholder - would integrate with market data)
        inventory_score = 0.5  # Neutral for now

        # Competition level assessment
        competition_level = "medium"
        if days_on_market > 30:
            competition_level = "low"
        elif days_on_market < 7:
            competition_level = "high"

        # Overall timing score
        optimal_timing_score = dom_score * 0.6 + price_trend_score * 0.3 + inventory_score * 0.1

        # Urgency indicator
        urgency_indicator = "can_wait"
        if days_on_market < 7:
            urgency_indicator = "act_fast"
        elif days_on_market < 21:
            urgency_indicator = "good_time"

        reasoning = self._generate_timing_reasoning(days_on_market, competition_level, urgency_indicator)

        return MarketTimingScore(
            days_on_market_score=dom_score,
            price_trend_score=price_trend_score,
            inventory_scarcity_score=inventory_score,
            competition_level=competition_level,
            optimal_timing_score=optimal_timing_score,
            urgency_indicator=urgency_indicator,
            reasoning=reasoning,
        )

    # Helper methods for scoring individual factors

    def _score_budget_match(self, price: float, budget: float, weight: float) -> FactorScore:
        """Score budget compatibility with stretch tolerance."""
        if not budget or budget <= 0:
            return FactorScore("budget", 0.5, 0.5 * weight, weight, 0.3, "Budget not specified", "missing")

        if price <= budget:
            # Under budget - calculate savings bonus
            savings_ratio = (budget - price) / budget
            raw_score = 1.0 if savings_ratio <= 0.1 else min(1.0, 1.0 + savings_ratio * 0.5)
            reasoning = f"${price:,} is ${budget - price:,} under your ${budget:,} budget"
            confidence = 0.95
        elif price <= budget * 1.05:  # 5% stretch acceptable
            raw_score = 0.8
            reasoning = f"${price:,} is slightly over budget but within 5% stretch"
            confidence = 0.8
        elif price <= budget * 1.10:  # 10% stretch with penalty
            raw_score = 0.5
            reasoning = f"${price:,} is 10% over budget - may require negotiation"
            confidence = 0.6
        else:
            raw_score = 0.1
            reasoning = f"${price:,} exceeds budget by {((price / budget - 1) * 100):.0f}%"
            confidence = 0.9

        return FactorScore(
            factor_name="budget",
            raw_score=min(raw_score, 1.0),
            weighted_score=min(raw_score, 1.0) * weight,
            weight=weight,
            confidence=confidence,
            reasoning=reasoning,
            data_quality="high",
        )

    def _score_location_match(self, address: Dict[str, Any], preferred_location: str, weight: float) -> FactorScore:
        """Score location match with fuzzy string matching."""
        if not preferred_location:
            return FactorScore("location", 0.5, 0.5 * weight, weight, 0.3, "Location not specified", "missing")

        city = address.get("city", "").lower()
        neighborhood = address.get("neighborhood", "").lower()
        state = address.get("state", "").lower()
        zip_code = address.get("zip", "")

        pref_lower = preferred_location.lower()

        # Exact match scoring
        if pref_lower in city or pref_lower in neighborhood:
            raw_score = 1.0
            reasoning = f"Located in preferred {preferred_location}"
            confidence = 0.95
        elif any(word in city + neighborhood for word in pref_lower.split()):
            raw_score = 0.8
            reasoning = f"Close to preferred location in {city.title()}"
            confidence = 0.8
        elif zip_code and pref_lower in zip_code:
            raw_score = 0.9
            reasoning = f"In preferred zip code {zip_code}"
            confidence = 0.9
        else:
            raw_score = 0.2
            reasoning = f"Not in preferred {preferred_location} area"
            confidence = 0.7

        return FactorScore(
            factor_name="location",
            raw_score=raw_score,
            weighted_score=raw_score * weight,
            weight=weight,
            confidence=confidence,
            reasoning=reasoning,
            data_quality="high",
        )

    def _score_bedrooms_match(self, property_beds: int, preferred_beds: int, weight: float) -> FactorScore:
        """Score bedroom count compatibility."""
        if not preferred_beds:
            return FactorScore("bedrooms", 0.5, 0.5 * weight, weight, 0.3, "Bedroom count not specified", "missing")

        if property_beds >= preferred_beds:
            if property_beds == preferred_beds:
                raw_score = 1.0
                reasoning = f"Exact match: {property_beds} bedrooms"
                confidence = 0.95
            elif property_beds == preferred_beds + 1:
                raw_score = 0.9
                reasoning = f"{property_beds} bedrooms (1 extra bonus room)"
                confidence = 0.9
            else:
                raw_score = 0.8
                reasoning = f"{property_beds} bedrooms (more than needed)"
                confidence = 0.8
        elif property_beds == preferred_beds - 1:
            raw_score = 0.5
            reasoning = f"{property_beds} bedrooms (1 short of {preferred_beds} needed)"
            confidence = 0.8
        else:
            raw_score = 0.2
            reasoning = f"Only {property_beds} bedrooms (need {preferred_beds})"
            confidence = 0.9

        return FactorScore(
            factor_name="bedrooms",
            raw_score=raw_score,
            weighted_score=raw_score * weight,
            weight=weight,
            confidence=confidence,
            reasoning=reasoning,
            data_quality="high",
        )

    # Additional scoring methods (implementing basic versions)

    def _score_bathrooms_match(self, property_baths: float, preferred_baths: float, weight: float) -> FactorScore:
        """Score bathroom count compatibility."""
        if not preferred_baths:
            raw_score = 0.5
            reasoning = "Bathroom count not specified"
            confidence = 0.3
        elif property_baths >= preferred_baths:
            raw_score = 1.0
            reasoning = f"{property_baths} bathrooms meets requirement"
            confidence = 0.9
        elif property_baths >= preferred_baths - 0.5:
            raw_score = 0.7
            reasoning = f"{property_baths} bathrooms (slightly under preference)"
            confidence = 0.8
        else:
            raw_score = 0.3
            reasoning = f"Only {property_baths} bathrooms (need {preferred_baths})"
            confidence = 0.9

        return FactorScore("bathrooms", raw_score, raw_score * weight, weight, confidence, reasoning, "high")

    def _score_property_type_match(self, property_type: str, preferred_type: str, weight: float) -> FactorScore:
        """Score property type compatibility."""
        if not preferred_type:
            return FactorScore(
                "property_type", 0.5, 0.5 * weight, weight, 0.3, "Property type not specified", "missing"
            )

        prop_lower = property_type.lower()
        pref_lower = preferred_type.lower()

        if pref_lower in prop_lower:
            raw_score = 1.0
            reasoning = f"Matches preferred {preferred_type}"
            confidence = 0.95
        elif "single" in pref_lower and "house" in prop_lower:
            raw_score = 0.9
            reasoning = f"{property_type} matches single-family preference"
            confidence = 0.9
        else:
            raw_score = 0.3
            reasoning = f"{property_type} doesn't match {preferred_type} preference"
            confidence = 0.8

        return FactorScore("property_type", raw_score, raw_score * weight, weight, confidence, reasoning, "high")

    def _score_sqft_match(self, property_sqft: int, min_sqft: int, max_sqft: int, weight: float) -> FactorScore:
        """Score square footage compatibility."""
        if not min_sqft and not max_sqft:
            return FactorScore("sqft", 0.5, 0.5 * weight, weight, 0.3, "Square footage not specified", "missing")

        if min_sqft and property_sqft < min_sqft:
            shortage = min_sqft - property_sqft
            raw_score = max(0.1, 1.0 - (shortage / min_sqft))
            reasoning = f"{property_sqft:,} sq ft ({shortage:,} below minimum)"
            confidence = 0.8
        elif max_sqft and property_sqft > max_sqft:
            overage = property_sqft - max_sqft
            raw_score = max(0.6, 1.0 - (overage / (max_sqft * 0.5)))
            reasoning = f"{property_sqft:,} sq ft (larger than preferred)"
            confidence = 0.7
        else:
            raw_score = 1.0
            reasoning = f"{property_sqft:,} sq ft fits size preference"
            confidence = 0.9

        return FactorScore("sqft", raw_score, raw_score * weight, weight, confidence, reasoning, "high")

    # Basic implementations for lifestyle factors (will be enhanced with dedicated services)

    def _score_schools_basic(self, property_data: Dict[str, Any], weight: float) -> float:
        """Basic school scoring from property data."""
        schools = property_data.get("schools", [])
        if not schools:
            return 0.0

        total_rating = sum(school.get("rating", 5) for school in schools)
        avg_rating = total_rating / len(schools)
        normalized_score = (avg_rating - 5) / 5  # Normalize 5-10 scale to 0-1

        return max(0, min(1, normalized_score)) * weight

    def _score_commute_basic(self, property_data: Dict[str, Any], weight: float) -> float:
        """Basic commute scoring."""
        # Placeholder: would integrate with commute analysis
        neighborhood = property_data.get("address", {}).get("neighborhood", "")
        if any(area in neighborhood.lower() for area in ["downtown", "central", "campus"]):
            return 0.8 * weight
        return 0.5 * weight

    def _score_walkability_basic(self, property_data: Dict[str, Any], weight: float) -> float:
        """Basic walkability scoring from highlights."""
        highlights = property_data.get("highlights", [])
        description = property_data.get("description", "")

        walkable_terms = ["walkable", "walk score", "restaurants", "shops", "transit"]

        score = 0.5  # Base score
        for term in walkable_terms:
            if any(term in text.lower() for text in highlights + [description]):
                score += 0.1

        return min(1.0, score) * weight

    def _score_safety_basic(self, property_data: Dict[str, Any], weight: float) -> float:
        """Basic safety scoring."""
        # Placeholder: would integrate with crime data
        neighborhood = property_data.get("address", {}).get("neighborhood", "")
        safe_neighborhoods = ["steiner ranch", "westlake", "avery ranch", "circle c"]

        if any(safe_area in neighborhood.lower() for safe_area in safe_neighborhoods):
            return 0.8 * weight
        return 0.5 * weight

    # Contextual factor scoring methods

    def _score_hoa_fee(self, hoa_fee: float, max_hoa: float, weight: float) -> FactorScore:
        """Score HOA fee acceptability."""
        if hoa_fee <= max_hoa:
            raw_score = 1.0 - (hoa_fee / max_hoa * 0.3)  # Lower fees score higher
            reasoning = f"${hoa_fee}/month HOA within ${max_hoa} budget"
            confidence = 0.9
        else:
            raw_score = 0.3
            reasoning = f"${hoa_fee}/month HOA exceeds ${max_hoa} budget"
            confidence = 0.9

        return FactorScore("hoa_fee", raw_score, raw_score * weight, weight, confidence, reasoning, "high")

    def _score_lot_size(self, lot_sqft: int, min_lot: int, weight: float) -> FactorScore:
        """Score lot size acceptability."""
        if not min_lot:
            raw_score = 0.5
            reasoning = "Lot size preference not specified"
            confidence = 0.3
        elif lot_sqft >= min_lot:
            raw_score = 1.0
            reasoning = f"{lot_sqft:,} sq ft lot meets {min_lot:,} minimum"
            confidence = 0.9
        else:
            shortage = min_lot - lot_sqft
            raw_score = max(0.2, 1.0 - (shortage / min_lot))
            reasoning = f"{lot_sqft:,} sq ft lot below {min_lot:,} preference"
            confidence = 0.8

        return FactorScore("lot_size", raw_score, raw_score * weight, weight, confidence, reasoning, "high")

    def _score_home_age(self, year_built: int, max_age: int, weight: float) -> FactorScore:
        """Score home age acceptability."""
        current_year = datetime.now().year
        age = current_year - year_built

        if age <= max_age:
            # Newer homes score higher
            raw_score = max(0.5, 1.0 - (age / 50))  # 50-year scale
            reasoning = f"Built in {year_built} ({age} years old)"
            confidence = 0.9
        else:
            raw_score = 0.3
            reasoning = f"Built in {year_built} (older than {max_age} year preference)"
            confidence = 0.9

        return FactorScore("home_age", raw_score, raw_score * weight, weight, confidence, reasoning, "high")

    def _score_parking_basic(self, property_data: Dict[str, Any], weight: float) -> FactorScore:
        """Basic parking scoring from features."""
        features = property_data.get("features", [])
        description = property_data.get("description", "")

        parking_indicators = ["garage", "parking", "carport", "driveway"]
        has_parking = any(
            indicator in text.lower() for text in features + [description] for indicator in parking_indicators
        )

        raw_score = 0.8 if has_parking else 0.3
        reasoning = "Parking mentioned" if has_parking else "Parking not clearly indicated"

        return FactorScore("parking", raw_score, raw_score * weight, weight, 0.6, reasoning, "medium")

    def _score_property_condition(self, property_data: Dict[str, Any], weight: float) -> FactorScore:
        """Score property condition from age and features."""
        year_built = property_data.get("year_built", 2000)
        features = property_data.get("features", [])

        age = datetime.now().year - year_built

        # Base score from age
        if age < 5:
            base_score = 1.0
        elif age < 15:
            base_score = 0.8
        elif age < 30:
            base_score = 0.6
        else:
            base_score = 0.4

        # Bonus for updates/renovations
        update_indicators = ["updated", "new", "renovated", "remodeled", "upgraded"]
        updates = sum(1 for feature in features for indicator in update_indicators if indicator in feature.lower())

        update_bonus = min(0.3, updates * 0.1)
        raw_score = min(1.0, base_score + update_bonus)

        reasoning = f"Built {year_built}, {updates} updated features mentioned"

        return FactorScore("property_condition", raw_score, raw_score * weight, weight, 0.7, reasoning, "medium")

    # Helper methods for weights and context

    def _calculate_adaptive_weights(self, context: MatchingContext) -> AdaptiveWeights:
        """Calculate adaptive weights based on lead profile and segment."""

        # Start with base weights
        traditional_weights = FACTOR_WEIGHTS_BASE.copy()
        lifestyle_weights = {
            "schools": FACTOR_WEIGHTS_BASE["schools"],
            "commute": FACTOR_WEIGHTS_BASE["commute"],
            "walkability": FACTOR_WEIGHTS_BASE["walkability"],
            "safety": FACTOR_WEIGHTS_BASE["safety"],
        }
        contextual_weights = {
            "hoa_fee": FACTOR_WEIGHTS_BASE["hoa_fee"],
            "lot_size": FACTOR_WEIGHTS_BASE["lot_size"],
            "home_age": FACTOR_WEIGHTS_BASE["home_age"],
            "parking": FACTOR_WEIGHTS_BASE["parking"],
        }
        market_timing_weight = FACTOR_WEIGHTS_BASE["market_timing"]

        # Apply segment-specific adjustments if available
        if context.behavioral_profile and context.behavioral_profile.segment:
            segment = context.behavioral_profile.segment
            segment_weights = DEFAULT_SEGMENT_WEIGHTS.get(segment, {})

            # Blend segment weights with base weights
            for factor, segment_weight in segment_weights.items():
                if factor in traditional_weights:
                    traditional_weights[factor] = (traditional_weights[factor] + segment_weight) / 2
                elif factor in lifestyle_weights:
                    lifestyle_weights[factor] = (lifestyle_weights[factor] + segment_weight) / 2
                elif factor in contextual_weights:
                    contextual_weights[factor] = (contextual_weights[factor] + segment_weight) / 2
                elif factor == "market_timing":
                    market_timing_weight = (market_timing_weight + segment_weight) / 2

        return AdaptiveWeights(
            traditional_weights=traditional_weights,
            lifestyle_weights=lifestyle_weights,
            contextual_weights=contextual_weights,
            market_timing_weight=market_timing_weight,
            confidence_level=0.8,  # Will improve with ML
            learning_iterations=0,
            last_updated=datetime.utcnow(),
        )

    def _create_matching_context(
        self,
        preferences: Dict[str, Any],
        behavioral_profile: Optional[BehavioralProfile],
        segment: Optional[LeadSegment],
    ) -> MatchingContext:
        """Create matching context for the session."""

        # Auto-detect segment if not provided
        if not segment and behavioral_profile:
            segment = self._detect_lead_segment(preferences, behavioral_profile)

        return MatchingContext(
            lead_id=preferences.get("lead_id", "unknown"),
            preferences=preferences,
            behavioral_profile=behavioral_profile,
            session_id=f"match_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            search_history=[],
            market_conditions={},
            available_data_sources=["property_listings", "interaction_history"],
            min_score_threshold=0.6,
            max_results=10,
            require_explanation=True,
            fallback_to_basic=True,
        )

    def _detect_lead_segment(self, preferences: Dict[str, Any], behavioral_profile: BehavioralProfile) -> LeadSegment:
        """Auto-detect lead segment from preferences and behavior."""

        # Family indicators
        bedrooms = preferences.get("bedrooms", 0)
        if bedrooms >= 3:
            # Check for school-focused behavior or family-related preferences
            return LeadSegment.FAMILY_WITH_KIDS

        # Young professional indicators
        if preferences.get("property_type", "").lower() in ["condo", "townhome"]:
            if bedrooms <= 2:
                return LeadSegment.YOUNG_PROFESSIONAL

        # Investor indicators
        if preferences.get("investment_property", False):
            return LeadSegment.INVESTOR

        # Luxury indicators
        budget = preferences.get("budget", 0)
        if budget > 800000:
            return LeadSegment.LUXURY_BUYER

        # Default
        return LeadSegment.FIRST_TIME_BUYER

    # Market timing and prediction methods

    def _calculate_dom_score(self, days_on_market: int) -> float:
        """Calculate days on market opportunity score."""
        if days_on_market <= 7:
            return 0.3  # Hot property, less negotiable
        elif days_on_market <= 21:
            return 0.6  # Normal market time
        elif days_on_market <= 60:
            return 0.9  # Good negotiation opportunity
        else:
            return 1.0  # High negotiation potential

    def _generate_timing_reasoning(self, days_on_market: int, competition_level: str, urgency_indicator: str) -> str:
        """Generate market timing reasoning."""
        if days_on_market < 7:
            return f"Hot property ({days_on_market} days on market) - expect multiple offers"
        elif days_on_market < 21:
            return f"Normal market time ({days_on_market} days) - good opportunity"
        elif days_on_market < 60:
            return f"Extended time on market ({days_on_market} days) - negotiation opportunity"
        else:
            return f"Long time on market ({days_on_market} days) - high negotiation potential"

    # Placeholder helper methods

    def _create_placeholder_school_score(self, property_data: Dict[str, Any], score: float):
        """Create placeholder school score object."""
        from ghl_real_estate_ai.models.matching_models import SchoolScore

        schools = property_data.get("schools", [])
        avg_rating = sum(s.get("rating", 5) for s in schools) / max(len(schools), 1)

        return SchoolScore(
            elementary_rating=next((s["rating"] for s in schools if s.get("type") == "Elementary"), None),
            middle_rating=next((s["rating"] for s in schools if s.get("type") == "Middle"), None),
            high_rating=next((s["rating"] for s in schools if s.get("type") == "High"), None),
            average_rating=avg_rating,
            distance_penalty=0.1,
            overall_score=score,
            top_school_name=schools[0].get("name") if schools else None,
            reasoning=f"Average school rating: {avg_rating:.1f}/10",
        )

    def _create_placeholder_commute_score(self, property_data: Dict[str, Any], score: float):
        """Create placeholder commute score object."""
        from ghl_real_estate_ai.models.matching_models import CommuteScore

        return CommuteScore(
            to_downtown_minutes=None,
            to_workplace_minutes=None,
            public_transit_access=0.5,
            highway_access=0.5,
            overall_score=score,
            reasoning="Commute analysis pending integration with mapping API",
        )

    def _create_placeholder_walkability_score(self, property_data: Dict[str, Any], score: float):
        """Create placeholder walkability score object."""
        from ghl_real_estate_ai.models.matching_models import WalkabilityScore

        return WalkabilityScore(
            walk_score=None,
            nearby_amenities_count=0,
            grocery_distance_miles=None,
            restaurant_density=0.5,
            park_access=0.5,
            overall_score=score,
            reasoning="Walkability analysis pending amenities data integration",
        )

    def _create_placeholder_safety_score(self, property_data: Dict[str, Any], score: float):
        """Create placeholder safety score object."""
        from ghl_real_estate_ai.models.matching_models import SafetyScore

        return SafetyScore(
            crime_rate_per_1000=None,
            neighborhood_safety_rating=None,
            police_response_time=None,
            overall_score=score,
            reasoning="Safety analysis pending crime data integration",
        )

    # Confidence and quality methods

    def _calculate_confidence_level(self, traditional, lifestyle, contextual, market_timing) -> float:
        """Calculate overall confidence in the scoring."""
        # Average confidence across all factors
        confidences = [
            traditional.budget.confidence,
            traditional.location.confidence,
            traditional.bedrooms.confidence,
            0.5,  # lifestyle factors - medium confidence with basic implementation
            0.7,  # contextual and timing factors
        ]
        return sum(confidences) / len(confidences)

    def _calculate_data_completeness(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Calculate what percentage of factors have good data quality."""
        required_property_fields = ["price", "bedrooms", "bathrooms", "address", "property_type", "sqft"]
        property_completeness = sum(1 for field in required_property_fields if property_data.get(field)) / len(
            required_property_fields
        )

        required_preference_fields = ["budget", "location", "bedrooms"]
        preference_completeness = sum(1 for field in required_preference_fields if preferences.get(field)) / len(
            required_preference_fields
        )

        return (property_completeness + preference_completeness) / 2

    # Prediction methods

    def _predict_engagement(self, score_breakdown: MatchScoreBreakdown) -> float:
        """Predict click-through rate for this match."""
        # Simple model based on overall score and confidence
        base_ctr = score_breakdown.overall_score * 0.4  # Base CTR from score
        confidence_bonus = score_breakdown.confidence_level * 0.1
        return min(0.95, base_ctr + confidence_bonus)

    def _predict_showing_probability(self, score_breakdown: MatchScoreBreakdown) -> float:
        """Predict probability of showing request."""
        # Higher bar for showing requests
        if score_breakdown.overall_score > 0.8:
            return score_breakdown.overall_score * 0.3
        else:
            return score_breakdown.overall_score * 0.15

    def _calculate_confidence_interval(self, score_breakdown: MatchScoreBreakdown) -> Tuple[float, float]:
        """Calculate confidence interval for the score."""
        score = score_breakdown.overall_score
        confidence = score_breakdown.confidence_level

        # Simple confidence interval based on data quality
        margin = (1 - confidence) * 0.2  # Lower confidence = wider interval
        return (max(0, score - margin), min(1, score + margin))

    # Reasoning generation

    def _generate_match_reasoning(
        self, property_data: Dict[str, Any], score_breakdown: MatchScoreBreakdown, context: MatchingContext
    ) -> MatchReasoning:
        """Generate comprehensive match reasoning."""

        primary_strengths = []
        secondary_benefits = []
        potential_concerns = []
        agent_talking_points = []

        # Analyze top scoring factors
        all_factors = [
            ("budget", score_breakdown.traditional_scores.budget),
            ("location", score_breakdown.traditional_scores.location),
            ("bedrooms", score_breakdown.traditional_scores.bedrooms),
            ("schools", score_breakdown.lifestyle_scores.overall_score, "lifestyle"),
            ("market_timing", score_breakdown.market_timing_score.optimal_timing_score, "timing"),
        ]

        # Sort by weighted score to find strengths
        scored_factors = [
            (name, factor.weighted_score if hasattr(factor, "weighted_score") else factor, category)
            for name, factor, *category in all_factors
        ]
        scored_factors.sort(key=lambda x: x[1], reverse=True)

        # Build primary strengths from top factors
        for factor_name, score, *category in scored_factors[:3]:
            if score > 0.15:  # Significant contribution
                if factor_name == "budget":
                    primary_strengths.append(score_breakdown.traditional_scores.budget.reasoning)
                elif factor_name == "location":
                    primary_strengths.append(score_breakdown.traditional_scores.location.reasoning)
                elif factor_name == "bedrooms":
                    primary_strengths.append(score_breakdown.traditional_scores.bedrooms.reasoning)
                elif factor_name == "schools":
                    primary_strengths.append("Excellent schools in the area")
                elif factor_name == "market_timing":
                    primary_strengths.append(score_breakdown.market_timing_score.reasoning)

        # Identify potential concerns
        if score_breakdown.traditional_scores.budget.raw_score < 0.5:
            potential_concerns.append("Price may be above comfortable budget")

        if score_breakdown.traditional_scores.bedrooms.raw_score < 0.7:
            potential_concerns.append("Bedroom count may not fully meet needs")

        # Generate agent talking points
        agent_talking_points.extend(
            [
                f"Overall match score: {score_breakdown.overall_score:.1%}",
                f"Key strength: {primary_strengths[0] if primary_strengths else 'Good overall fit'}",
                f"Market timing: {score_breakdown.market_timing_score.urgency_indicator.replace('_', ' ')}",
            ]
        )

        return MatchReasoning(
            primary_strengths=primary_strengths,
            secondary_benefits=secondary_benefits,
            potential_concerns=potential_concerns,
            agent_talking_points=agent_talking_points,
            comparison_to_past_likes=None,  # Will implement with behavioral analysis
            lifestyle_fit_summary=f"Lifestyle compatibility: {score_breakdown.lifestyle_scores.overall_score:.1%}",
            market_opportunity_summary=score_breakdown.market_timing_score.reasoning,
        )

    # Data loading methods

    def _load_interaction_data(self):
        """Load interaction history for behavioral analysis."""
        try:
            interaction_path = Path(__file__).parent.parent / "data" / "portal_interactions" / "lead_interactions.json"
            if interaction_path.exists():
                with open(interaction_path, "r") as f:
                    self.interaction_data = json.load(f)
            else:
                self.interaction_data = {"interactions": []}
        except Exception as e:
            logger.error(f"Failed to load interaction data: {e}")
            self.interaction_data = {"interactions": []}

    # Backward compatibility method

    def find_matches(self, preferences: Dict[str, Any], limit: int = 3, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Backward compatibility method that falls back to basic matching.

        For enhanced matching, use find_enhanced_matches() instead.
        """
        logger.info("Using backward compatibility mode - consider upgrading to find_enhanced_matches()")

        try:
            # Try enhanced matching first
            enhanced_matches = self.find_enhanced_matches(preferences=preferences, limit=limit, min_score=min_score)

            # Convert to legacy format
            legacy_matches = []
            for match in enhanced_matches:
                legacy_match = match.property.copy()
                legacy_match["match_score"] = round(match.overall_score, 2)
                legacy_matches.append(legacy_match)

            return legacy_matches

        except Exception as e:
            logger.error(f"Enhanced matching failed, falling back to basic: {e}")
            # Fall back to parent class implementation
            return super().find_matches(preferences, limit, min_score)


# Demo function for testing
def demo_enhanced_matching():
    """Demo the enhanced property matching system."""
    print("🎯 Enhanced Property Matching Demo\n")

    matcher = EnhancedPropertyMatcher()

    # Test preferences
    test_preferences = {
        "lead_id": "demo_lead_001",
        "budget": 600000,
        "location": "Austin",
        "bedrooms": 3,
        "bathrooms": 2,
        "property_type": "Single Family",
        "min_sqft": 1500,
        "max_hoa": 200,
    }

    # Test enhanced matching
    matches = matcher.find_enhanced_matches(preferences=test_preferences, limit=5, min_score=0.4)

    print(f"Found {len(matches)} enhanced matches:")
    print("=" * 80)

    for i, match in enumerate(matches, 1):
        print(f"\n{i}. {match.property.get('address', {}).get('street', 'Unknown Address')}")
        print(f"   Overall Score: {match.overall_score:.1%}")
        print(f"   Price: ${match.property.get('price', 0):,}")
        print(f"   Primary Strengths:")
        for strength in match.reasoning.primary_strengths[:2]:
            print(f"     • {strength}")
        if match.reasoning.potential_concerns:
            print(f"   Potential Concerns:")
            for concern in match.reasoning.potential_concerns[:1]:
                print(f"     ⚠ {concern}")
        print(f"   Market Timing: {match.score_breakdown.market_timing_score.urgency_indicator.replace('_', ' ')}")


if __name__ == "__main__":
    demo_enhanced_matching()
