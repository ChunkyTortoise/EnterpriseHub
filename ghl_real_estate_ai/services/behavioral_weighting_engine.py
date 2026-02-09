"""
Behavioral Weighting Engine for Adaptive Property Matching

Analyzes lead behavioral patterns to dynamically adjust matching weights:
- Past property likes/passes analysis
- Preference vs. behavior deviation detection
- Lead segment classification
- Adaptive weight calculation
- Negative feedback loops
- Learning from interaction outcomes
"""

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import (
    DEFAULT_SEGMENT_WEIGHTS,
    FACTOR_WEIGHTS_BASE,
    AdaptiveWeights,
    BehavioralProfile,
    LeadSegment,
)

logger = get_logger(__name__)


class BehavioralWeightingEngine:
    """
    Engine for analyzing lead behavior and adapting property matching weights.

    Key Features:
    - Analyzes past likes/passes to detect preference patterns
    - Identifies deviations between stated preferences and actual behavior
    - Applies segment-specific weight adjustments
    - Implements negative feedback loops for rejected properties
    - Continuously learns from interaction outcomes
    """

    def __init__(self, interaction_data_path: Optional[str] = None):
        """
        Initialize the behavioral weighting engine.

        Args:
            interaction_data_path: Path to lead interaction history data
        """
        self.interaction_data_path = interaction_data_path or str(
            Path(__file__).parent.parent / "data" / "portal_interactions" / "lead_interactions.json"
        )
        self._load_interaction_data()
        self._load_property_listings()

    def analyze_behavioral_profile(self, lead_id: str, stated_preferences: Dict[str, Any]) -> BehavioralProfile:
        """
        Analyze lead's behavioral patterns to create comprehensive profile.

        Args:
            lead_id: Unique lead identifier
            stated_preferences: Lead's explicitly stated preferences

        Returns:
            BehavioralProfile with segment, patterns, and deviations
        """
        logger.info(f"Analyzing behavioral profile for lead {lead_id}")

        # Get lead's interaction history
        lead_interactions = self._get_lead_interactions(lead_id)

        if not lead_interactions:
            logger.warning(f"No interaction history found for lead {lead_id}")
            return self._create_default_profile(lead_id, stated_preferences)

        # Analyze liked and passed properties
        liked_properties, passed_properties = self._categorize_interactions(lead_interactions)

        # Detect behavioral patterns
        engagement_patterns = self._analyze_engagement_patterns(lead_interactions)

        # Calculate preference deviations
        preference_deviations = self._calculate_preference_deviations(
            liked_properties, passed_properties, stated_preferences
        )

        # Detect lead segment
        segment = self._detect_lead_segment(stated_preferences, liked_properties, passed_properties)

        # Calculate response metrics
        response_rate, avg_time_on_card = self._calculate_response_metrics(lead_interactions)

        # Assess search consistency
        search_consistency = self._assess_search_consistency(liked_properties, passed_properties)

        return BehavioralProfile(
            segment=segment,
            past_likes=[prop["id"] for prop in liked_properties],
            past_passes=[prop["id"] for prop in passed_properties],
            engagement_patterns=engagement_patterns,
            preference_deviations=preference_deviations,
            response_rate=response_rate,
            avg_time_on_card=avg_time_on_card,
            search_consistency=search_consistency,
        )

    def calculate_adaptive_weights(
        self,
        behavioral_profile: BehavioralProfile,
        stated_preferences: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdaptiveWeights:
        """
        Calculate dynamically adjusted matching weights.

        Args:
            behavioral_profile: Lead's behavioral analysis
            stated_preferences: Explicitly stated preferences
            context: Additional context (market conditions, etc.)

        Returns:
            AdaptiveWeights with personalized factor weights
        """
        logger.info(f"Calculating adaptive weights for segment: {behavioral_profile.segment}")

        # Start with segment-specific base weights
        segment_weights = DEFAULT_SEGMENT_WEIGHTS.get(
            behavioral_profile.segment, DEFAULT_SEGMENT_WEIGHTS[LeadSegment.FIRST_TIME_BUYER]
        ).copy()

        # Apply behavioral deviations
        adjusted_weights = self._apply_behavioral_deviations(segment_weights, behavioral_profile.preference_deviations)

        # Apply engagement-based adjustments
        engagement_adjustments = self._calculate_engagement_adjustments(behavioral_profile.engagement_patterns)

        # Combine adjustments
        final_weights = self._combine_weight_adjustments(adjusted_weights, engagement_adjustments)

        # Normalize weights to ensure they sum appropriately
        normalized_weights = self._normalize_weights(final_weights)

        # Split into categories
        traditional_weights, lifestyle_weights, contextual_weights, market_timing_weight = self._categorize_weights(
            normalized_weights
        )

        # Calculate confidence level based on data quality
        confidence_level = self._calculate_weight_confidence(behavioral_profile)

        return AdaptiveWeights(
            traditional_weights=traditional_weights,
            lifestyle_weights=lifestyle_weights,
            contextual_weights=contextual_weights,
            market_timing_weight=market_timing_weight,
            confidence_level=confidence_level,
            learning_iterations=len(behavioral_profile.past_likes) + len(behavioral_profile.past_passes),
            last_updated=datetime.utcnow(),
        )

    def apply_negative_feedback(
        self, property_id: str, feedback_category: str, feedback_text: str, current_weights: AdaptiveWeights
    ) -> AdaptiveWeights:
        """
        Apply negative feedback loop to adjust weights.

        When a property is rejected, analyze why and adjust weights to avoid
        similar properties in the future.

        Args:
            property_id: ID of rejected property
            feedback_category: Category of rejection (price_too_high, wrong_location, etc.)
            feedback_text: Free-text feedback
            current_weights: Current weight configuration

        Returns:
            Updated AdaptiveWeights with negative feedback applied
        """
        logger.info(f"Applying negative feedback for property {property_id}: {feedback_category}")

        # Get property details to understand what was rejected
        rejected_property = self._get_property_by_id(property_id)
        if not rejected_property:
            logger.warning(f"Property {property_id} not found for feedback analysis")
            return current_weights

        # Analyze rejection reason and adjust weights accordingly
        weight_adjustments = self._calculate_negative_feedback_adjustments(
            rejected_property, feedback_category, feedback_text
        )

        # Apply adjustments to current weights
        updated_weights = self._apply_weight_adjustments(current_weights, weight_adjustments)

        return updated_weights

    # Helper methods for behavioral analysis

    def _get_lead_interactions(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get all interactions for a specific lead."""
        return [
            interaction
            for interaction in self.interaction_data.get("interactions", [])
            if interaction.get("lead_id") == lead_id
        ]

    def _categorize_interactions(
        self, interactions: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Categorize interactions into likes and passes with property details."""
        liked_properties = []
        passed_properties = []

        for interaction in interactions:
            property_id = interaction.get("property_id")
            property_data = self._get_property_by_id(property_id)

            if not property_data:
                continue

            # Add interaction metadata to property data
            enriched_property = property_data.copy()
            enriched_property.update(
                {
                    "interaction_timestamp": interaction.get("timestamp"),
                    "time_on_card": interaction.get("meta_data", {}).get("time_on_card"),
                    "feedback_category": interaction.get("meta_data", {}).get("feedback_category"),
                    "feedback_text": interaction.get("meta_data", {}).get("feedback_text"),
                }
            )

            if interaction.get("action") == "like":
                liked_properties.append(enriched_property)
            elif interaction.get("action") == "pass":
                passed_properties.append(enriched_property)

        return liked_properties, passed_properties

    def _analyze_engagement_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement patterns from interactions."""
        if not interactions:
            return {"total_interactions": 0, "like_ratio": 0.5, "avg_time_on_card": 0}

        total_interactions = len(interactions)
        likes = sum(1 for i in interactions if i.get("action") == "like")
        like_ratio = likes / total_interactions if total_interactions > 0 else 0

        # Analyze time on card patterns
        times_on_card = [
            i.get("meta_data", {}).get("time_on_card", 0)
            for i in interactions
            if i.get("meta_data", {}).get("time_on_card")
        ]

        avg_time_on_card = statistics.mean(times_on_card) if times_on_card else 0

        # Analyze interaction timing patterns
        interaction_times = []
        for interaction in interactions:
            try:
                timestamp = datetime.fromisoformat(interaction["timestamp"].replace("Z", "+00:00"))
                interaction_times.append(timestamp)
            except:
                continue

        # Session analysis
        sessions = self._identify_browsing_sessions(interaction_times)

        return {
            "total_interactions": total_interactions,
            "like_ratio": like_ratio,
            "avg_time_on_card": avg_time_on_card,
            "total_sessions": len(sessions),
            "avg_session_length": statistics.mean([len(s) for s in sessions]) if sessions else 0,
            "most_active_hour": self._find_most_active_hour(interaction_times),
        }

    def _calculate_preference_deviations(
        self,
        liked_properties: List[Dict[str, Any]],
        passed_properties: List[Dict[str, Any]],
        stated_preferences: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Calculate deviations between stated preferences and actual behavior.

        Returns dict mapping factor names to deviation scores (-1 to 1):
        - Positive values: they like MORE of this factor than stated
        - Negative values: they like LESS of this factor than stated
        """
        deviations = {}

        if not liked_properties:
            return deviations

        # Analyze budget deviations
        if stated_preferences.get("budget"):
            stated_budget = stated_preferences["budget"]
            liked_prices = [prop.get("price", 0) for prop in liked_properties if prop.get("price")]

            if liked_prices:
                avg_liked_price = statistics.mean(liked_prices)
                # Positive deviation = they like more expensive than stated
                budget_deviation = (avg_liked_price - stated_budget) / stated_budget
                deviations["budget"] = max(-1, min(1, budget_deviation))

        # Analyze location deviations
        stated_location = stated_preferences.get("location", "").lower()
        if stated_location:
            liked_locations = [prop.get("address", {}).get("neighborhood", "").lower() for prop in liked_properties]
            # If they consistently like different locations than stated
            location_matches = sum(1 for loc in liked_locations if stated_location in loc)
            location_deviation = (location_matches / len(liked_locations)) if liked_locations else 0.5
            # Convert to -1 to 1 scale where 1 = perfect match, -1 = complete mismatch
            deviations["location"] = (location_deviation - 0.5) * 2

        # Analyze bedroom deviations
        if stated_preferences.get("bedrooms"):
            stated_bedrooms = stated_preferences["bedrooms"]
            liked_bedrooms = [prop.get("bedrooms", 0) for prop in liked_properties if prop.get("bedrooms")]

            if liked_bedrooms:
                avg_liked_bedrooms = statistics.mean(liked_bedrooms)
                # Positive deviation = they like more bedrooms than stated
                bedroom_deviation = (avg_liked_bedrooms - stated_bedrooms) / max(stated_bedrooms, 1)
                deviations["bedrooms"] = max(-1, min(1, bedroom_deviation))

        # Analyze property type deviations
        stated_type = stated_preferences.get("property_type", "").lower()
        if stated_type:
            liked_types = [prop.get("property_type", "").lower() for prop in liked_properties]
            type_matches = sum(1 for prop_type in liked_types if stated_type in prop_type)
            type_match_rate = type_matches / len(liked_types) if liked_types else 0.5
            deviations["property_type"] = (type_match_rate - 0.5) * 2

        # Analyze feature preferences from likes
        self._analyze_feature_preferences(liked_properties, passed_properties, deviations)

        return deviations

    def _analyze_feature_preferences(
        self,
        liked_properties: List[Dict[str, Any]],
        passed_properties: List[Dict[str, Any]],
        deviations: Dict[str, float],
    ):
        """Analyze implicit feature preferences from behavioral data."""

        # Analyze liked features
        liked_features = []
        for prop in liked_properties:
            features = prop.get("features", [])
            liked_features.extend([feature.lower() for feature in features])

        # Analyze passed features
        passed_features = []
        for prop in passed_properties:
            features = prop.get("features", [])
            passed_features.extend([feature.lower() for feature in features])

        # Count feature frequencies
        liked_counter = Counter(liked_features)
        passed_counter = Counter(passed_features)

        # Identify strongly preferred features
        feature_preferences = {}
        all_features = set(liked_features + passed_features)

        for feature in all_features:
            liked_count = liked_counter.get(feature, 0)
            passed_count = passed_counter.get(feature, 0)
            total_count = liked_count + passed_count

            if total_count >= 2:  # Only consider features seen multiple times
                preference_ratio = liked_count / total_count
                feature_preferences[feature] = preference_ratio

        # Map features to factors
        feature_factor_mapping = {
            "garage": "parking",
            "parking": "parking",
            "updated": "property_condition",
            "new": "property_condition",
            "renovated": "property_condition",
            "pool": "amenities",
            "backyard": "lot_size",
            "large": "sqft",
            "spacious": "sqft",
            "walkable": "walkability",
            "schools": "schools",
            "safe": "safety",
            "quiet": "safety",
        }

        # Apply feature preferences to deviations
        for feature, preference in feature_preferences.items():
            for keyword, factor in feature_factor_mapping.items():
                if keyword in feature:
                    # Strong preference (>0.7) indicates positive deviation
                    if preference > 0.7:
                        deviations[factor] = deviations.get(factor, 0) + 0.3
                    elif preference < 0.3:
                        deviations[factor] = deviations.get(factor, 0) - 0.3

    def _detect_lead_segment(
        self,
        stated_preferences: Dict[str, Any],
        liked_properties: List[Dict[str, Any]],
        passed_properties: List[Dict[str, Any]],
    ) -> LeadSegment:
        """Detect lead segment from preferences and behavior."""

        # Scoring system for different segments
        segment_scores = defaultdict(float)

        # Family indicators
        bedrooms = stated_preferences.get("bedrooms", 0)
        if bedrooms >= 3:
            segment_scores[LeadSegment.FAMILY_WITH_KIDS] += 2

        # Check liked properties for family indicators
        family_features = ["school", "safe", "family", "playground", "park", "quiet"]
        liked_family_features = sum(
            1
            for prop in liked_properties
            for feature in prop.get("features", [])
            for family_feat in family_features
            if family_feat in feature.lower()
        )
        segment_scores[LeadSegment.FAMILY_WITH_KIDS] += liked_family_features * 0.5

        # Young professional indicators
        urban_features = ["walkable", "downtown", "restaurant", "nightlife", "transit"]
        urban_count = sum(
            1
            for prop in liked_properties
            for feature in prop.get("features", [])
            for urban_feat in urban_features
            if urban_feat in feature.lower()
        )
        if bedrooms <= 2 and urban_count > 0:
            segment_scores[LeadSegment.YOUNG_PROFESSIONAL] += 2 + urban_count * 0.3

        # Investor indicators
        if stated_preferences.get("investment_property", False):
            segment_scores[LeadSegment.INVESTOR] += 3

        # Look for investor-focused behavior
        investor_features = ["rental", "investment", "cash flow", "appreciation"]
        investor_count = sum(
            1
            for prop in liked_properties
            for feature in prop.get("features", [])
            for inv_feat in investor_features
            if inv_feat in feature.lower()
        )
        segment_scores[LeadSegment.INVESTOR] += investor_count * 0.8

        # Luxury buyer indicators
        budget = stated_preferences.get("budget", 0)
        if budget > 800000:
            segment_scores[LeadSegment.LUXURY_BUYER] += 2

        luxury_features = ["luxury", "premium", "high-end", "custom", "gourmet", "spa"]
        luxury_count = sum(
            1
            for prop in liked_properties
            for feature in prop.get("features", [])
            for lux_feat in luxury_features
            if lux_feat in feature.lower()
        )
        segment_scores[LeadSegment.LUXURY_BUYER] += luxury_count * 0.4

        # Retiree indicators
        retiree_features = ["single-story", "low maintenance", "golf", "55+", "senior"]
        retiree_count = sum(
            1
            for prop in liked_properties
            for feature in prop.get("features", [])
            for retiree_feat in retiree_features
            if retiree_feat in feature.lower()
        )
        segment_scores[LeadSegment.RETIREE] += retiree_count * 0.6

        # First-time buyer indicators (default if no strong indicators)
        if budget and budget < 400000:
            segment_scores[LeadSegment.FIRST_TIME_BUYER] += 1

        # Return segment with highest score
        if segment_scores:
            return max(segment_scores.items(), key=lambda x: x[1])[0]
        else:
            return LeadSegment.FIRST_TIME_BUYER

    def _calculate_response_metrics(self, interactions: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate response rate and average time on card."""
        if not interactions:
            return 0.0, 0.0

        # For demo purposes, calculate from available data
        # In real implementation, this would include email opens, call responses, etc.
        total_interactions = len(interactions)
        engaged_interactions = sum(
            1
            for i in interactions
            if i.get("meta_data", {}).get("time_on_card", 0) > 10  # > 10 seconds = engaged
        )

        response_rate = engaged_interactions / total_interactions if total_interactions > 0 else 0

        # Calculate average time on card
        times_on_card = [
            i.get("meta_data", {}).get("time_on_card", 0)
            for i in interactions
            if i.get("meta_data", {}).get("time_on_card")
        ]
        avg_time = statistics.mean(times_on_card) if times_on_card else 0

        return response_rate, avg_time

    def _assess_search_consistency(
        self, liked_properties: List[Dict[str, Any]], passed_properties: List[Dict[str, Any]]
    ) -> str:
        """Assess how consistent the lead's search patterns are."""
        all_properties = liked_properties + passed_properties

        if len(all_properties) < 3:
            return "insufficient_data"

        # Analyze consistency in key attributes
        price_consistency = self._calculate_price_consistency(all_properties)
        location_consistency = self._calculate_location_consistency(all_properties)
        size_consistency = self._calculate_size_consistency(all_properties)

        # Overall consistency score
        overall_consistency = (price_consistency + location_consistency + size_consistency) / 3

        if overall_consistency > 0.8:
            return "very_consistent"
        elif overall_consistency > 0.6:
            return "consistent"
        elif overall_consistency > 0.4:
            return "somewhat_consistent"
        else:
            return "inconsistent"

    # Weight adjustment helper methods

    def _apply_behavioral_deviations(
        self, base_weights: Dict[str, float], deviations: Dict[str, float]
    ) -> Dict[str, float]:
        """Apply behavioral deviations to base weights."""
        adjusted_weights = base_weights.copy()

        for factor, deviation in deviations.items():
            if factor in adjusted_weights:
                # Apply deviation as a multiplier
                # Positive deviation = increase weight, negative = decrease weight
                multiplier = 1.0 + (deviation * 0.3)  # Max 30% adjustment
                adjusted_weights[factor] = max(0.01, adjusted_weights[factor] * multiplier)

        return adjusted_weights

    def _calculate_engagement_adjustments(self, engagement_patterns: Dict[str, Any]) -> Dict[str, float]:
        """Calculate weight adjustments based on engagement patterns."""
        adjustments = {}

        like_ratio = engagement_patterns.get("like_ratio", 0.5)
        avg_time_on_card = engagement_patterns.get("avg_time_on_card", 0)

        # If they're very selective (low like ratio), increase precision factors
        if like_ratio < 0.3:
            adjustments["budget"] = 1.2  # Be more precise on budget
            adjustments["location"] = 1.1  # Be more precise on location

        # If they spend a lot of time on cards, they care about details
        if avg_time_on_card > 20:
            adjustments["property_condition"] = 1.3
            adjustments["amenities"] = 1.2

        return adjustments

    def _combine_weight_adjustments(
        self, base_weights: Dict[str, float], adjustments: Dict[str, float]
    ) -> Dict[str, float]:
        """Combine base weights with adjustment multipliers."""
        combined = base_weights.copy()

        for factor, multiplier in adjustments.items():
            if factor in combined:
                combined[factor] *= multiplier

        return combined

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0."""
        total_weight = sum(weights.values())
        if total_weight == 0:
            return weights

        return {factor: weight / total_weight for factor, weight in weights.items()}

    def _categorize_weights(
        self, all_weights: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], float]:
        """Split weights into traditional, lifestyle, contextual, and market timing."""

        traditional_factors = ["budget", "location", "bedrooms", "bathrooms", "property_type", "sqft"]
        lifestyle_factors = ["schools", "commute", "walkability", "safety"]
        contextual_factors = ["hoa_fee", "lot_size", "home_age", "parking", "property_condition"]
        market_timing_factors = ["market_timing"]

        traditional_weights = {f: all_weights.get(f, FACTOR_WEIGHTS_BASE.get(f, 0)) for f in traditional_factors}
        lifestyle_weights = {f: all_weights.get(f, FACTOR_WEIGHTS_BASE.get(f, 0)) for f in lifestyle_factors}
        contextual_weights = {f: all_weights.get(f, FACTOR_WEIGHTS_BASE.get(f, 0)) for f in contextual_factors}
        market_timing_weight = all_weights.get("market_timing", FACTOR_WEIGHTS_BASE.get("market_timing", 0.05))

        return traditional_weights, lifestyle_weights, contextual_weights, market_timing_weight

    def _calculate_weight_confidence(self, behavioral_profile: BehavioralProfile) -> float:
        """Calculate confidence level in the adaptive weights."""
        total_interactions = len(behavioral_profile.past_likes) + len(behavioral_profile.past_passes)

        if total_interactions >= 20:
            return 0.95
        elif total_interactions >= 10:
            return 0.85
        elif total_interactions >= 5:
            return 0.70
        else:
            return 0.50

    # Data loading and utility methods

    def _load_interaction_data(self):
        """Load lead interaction history data."""
        try:
            with open(self.interaction_data_path, "r") as f:
                self.interaction_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load interaction data: {e}")
            self.interaction_data = {"interactions": []}

    def _load_property_listings(self):
        """Load property listings for cross-referencing."""
        try:
            listings_path = Path(__file__).parent.parent / "data" / "knowledge_base" / "property_listings.json"
            with open(listings_path, "r") as f:
                listings_data = json.load(f)
                # Create lookup dict for faster access
                self.property_lookup = {prop["id"]: prop for prop in listings_data.get("listings", [])}
        except Exception as e:
            logger.error(f"Failed to load property listings: {e}")
            self.property_lookup = {}

    def _get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get property details by ID."""
        return self.property_lookup.get(property_id)

    def _create_default_profile(self, lead_id: str, stated_preferences: Dict[str, Any]) -> BehavioralProfile:
        """Create default behavioral profile for leads with no history."""
        # Detect segment from preferences only
        segment = LeadSegment.FIRST_TIME_BUYER
        bedrooms = stated_preferences.get("bedrooms", 0)
        budget = stated_preferences.get("budget", 0)

        if bedrooms >= 3:
            segment = LeadSegment.FAMILY_WITH_KIDS
        elif budget > 800000:
            segment = LeadSegment.LUXURY_BUYER
        elif stated_preferences.get("property_type", "").lower() in ["condo", "townhome"]:
            segment = LeadSegment.YOUNG_PROFESSIONAL

        return BehavioralProfile(
            segment=segment,
            past_likes=[],
            past_passes=[],
            engagement_patterns={"total_interactions": 0},
            preference_deviations={},
            response_rate=0.5,
            avg_time_on_card=0.0,
            search_consistency="unknown",
        )

    # Negative feedback methods

    def _calculate_negative_feedback_adjustments(
        self, rejected_property: Dict[str, Any], feedback_category: str, feedback_text: str
    ) -> Dict[str, float]:
        """Calculate weight adjustments based on negative feedback."""
        adjustments = {}

        # Map feedback categories to weight adjustments
        feedback_mappings = {
            "price_too_high": {"budget": 1.2},  # Increase budget importance
            "wrong_location": {"location": 1.3},  # Increase location importance
            "too_small": {"sqft": 1.2, "bedrooms": 1.1},
            "no_parking": {"parking": 1.5},
            "bad_schools": {"schools": 1.4},
            "not_walkable": {"walkability": 1.3},
            "unsafe_area": {"safety": 1.4},
            "too_old": {"home_age": 1.2, "property_condition": 1.2},
        }

        if feedback_category in feedback_mappings:
            adjustments = feedback_mappings[feedback_category]

        # Analyze feedback text for additional insights
        feedback_lower = feedback_text.lower()
        if "budget" in feedback_lower or "expensive" in feedback_lower:
            adjustments["budget"] = adjustments.get("budget", 1.0) * 1.1
        if "location" in feedback_lower or "area" in feedback_lower:
            adjustments["location"] = adjustments.get("location", 1.0) * 1.1

        return adjustments

    def _apply_weight_adjustments(
        self, current_weights: AdaptiveWeights, adjustments: Dict[str, float]
    ) -> AdaptiveWeights:
        """Apply negative feedback adjustments to current weights."""
        # Create new weights with adjustments applied
        new_traditional = current_weights.traditional_weights.copy()
        new_lifestyle = current_weights.lifestyle_weights.copy()
        new_contextual = current_weights.contextual_weights.copy()

        for factor, multiplier in adjustments.items():
            if factor in new_traditional:
                new_traditional[factor] *= multiplier
            elif factor in new_lifestyle:
                new_lifestyle[factor] *= multiplier
            elif factor in new_contextual:
                new_contextual[factor] *= multiplier

        # Renormalize weights
        all_weights = {**new_traditional, **new_lifestyle, **new_contextual}
        normalized = self._normalize_weights(all_weights)

        # Split back into categories
        trad, life, cont, timing = self._categorize_weights(normalized)

        return AdaptiveWeights(
            traditional_weights=trad,
            lifestyle_weights=life,
            contextual_weights=cont,
            market_timing_weight=current_weights.market_timing_weight,
            confidence_level=current_weights.confidence_level * 1.05,  # Slightly increase confidence
            learning_iterations=current_weights.learning_iterations + 1,
            last_updated=datetime.utcnow(),
        )

    # Helper methods for consistency analysis

    def _calculate_price_consistency(self, properties: List[Dict[str, Any]]) -> float:
        """Calculate price range consistency."""
        prices = [prop.get("price", 0) for prop in properties if prop.get("price")]
        if len(prices) < 2:
            return 0.5

        price_range = max(prices) - min(prices)
        avg_price = statistics.mean(prices)
        cv = (statistics.stdev(prices) / avg_price) if avg_price > 0 else 1.0

        # Lower coefficient of variation = higher consistency
        return max(0, 1.0 - cv)

    def _calculate_location_consistency(self, properties: List[Dict[str, Any]]) -> float:
        """Calculate location consistency."""
        neighborhoods = [prop.get("address", {}).get("neighborhood", "").lower() for prop in properties]
        unique_neighborhoods = set(neighborhoods)

        if len(unique_neighborhoods) <= 1:
            return 1.0
        elif len(unique_neighborhoods) <= 3:
            return 0.7
        else:
            return 0.3

    def _calculate_size_consistency(self, properties: List[Dict[str, Any]]) -> float:
        """Calculate size consistency."""
        sqfts = [prop.get("sqft", 0) for prop in properties if prop.get("sqft")]
        if len(sqfts) < 2:
            return 0.5

        size_range = max(sqfts) - min(sqfts)
        avg_size = statistics.mean(sqfts)
        cv = (statistics.stdev(sqfts) / avg_size) if avg_size > 0 else 1.0

        return max(0, 1.0 - cv)

    def _identify_browsing_sessions(self, interaction_times: List[datetime]) -> List[List[datetime]]:
        """Identify browsing sessions from interaction timestamps."""
        if not interaction_times:
            return []

        sessions = []
        current_session = [interaction_times[0]]

        for i in range(1, len(interaction_times)):
            time_gap = interaction_times[i] - interaction_times[i - 1]
            if time_gap.total_seconds() <= 1800:  # 30 minutes = same session
                current_session.append(interaction_times[i])
            else:
                sessions.append(current_session)
                current_session = [interaction_times[i]]

        if current_session:
            sessions.append(current_session)

        return sessions

    def _find_most_active_hour(self, interaction_times: List[datetime]) -> Optional[int]:
        """Find the hour of day when lead is most active."""
        if not interaction_times:
            return None

        hours = [dt.hour for dt in interaction_times]
        hour_counts = Counter(hours)
        return hour_counts.most_common(1)[0][0] if hour_counts else None


# Demo function
def demo_behavioral_weighting():
    """Demo the behavioral weighting engine."""
    print("🧠 Behavioral Weighting Engine Demo\n")

    engine = BehavioralWeightingEngine()

    # Test with different lead scenarios
    test_scenarios = [
        {
            "lead_id": "test_contact_api",
            "preferences": {"budget": 600000, "location": "Austin", "bedrooms": 3, "property_type": "Single Family"},
        },
        {
            "lead_id": "test_interactions_api",
            "preferences": {"budget": 450000, "location": "East Austin", "bedrooms": 2, "property_type": "Condo"},
        },
    ]

    for scenario in test_scenarios:
        print(f"\n{'=' * 60}")
        print(f"Lead: {scenario['lead_id']}")
        print(f"Preferences: {scenario['preferences']}")
        print(f"{'=' * 60}")

        # Analyze behavioral profile
        profile = engine.analyze_behavioral_profile(scenario["lead_id"], scenario["preferences"])

        print(f"\n🎯 Detected Segment: {profile.segment.value}")
        print(f"📊 Past Interactions: {len(profile.past_likes)} likes, {len(profile.past_passes)} passes")
        print(f"⏱️  Avg Time on Card: {profile.avg_time_on_card:.1f}s")
        print(f"📈 Search Consistency: {profile.search_consistency}")

        if profile.preference_deviations:
            print(f"\n🔍 Preference Deviations:")
            for factor, deviation in profile.preference_deviations.items():
                direction = "higher" if deviation > 0 else "lower"
                print(f"   {factor}: {abs(deviation):.2f} ({direction} than stated)")

        # Calculate adaptive weights
        adaptive_weights = engine.calculate_adaptive_weights(profile, scenario["preferences"])

        print(f"\n⚖️  Adaptive Weights (Top 5):")
        all_weights = {**adaptive_weights.traditional_weights, **adaptive_weights.lifestyle_weights}
        top_weights = sorted(all_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        for factor, weight in top_weights:
            print(f"   {factor}: {weight:.3f}")

        print(f"\n✅ Weight Confidence: {adaptive_weights.confidence_level:.1%}")


if __name__ == "__main__":
    demo_behavioral_weighting()
