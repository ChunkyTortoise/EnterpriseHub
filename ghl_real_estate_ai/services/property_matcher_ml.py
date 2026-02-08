"""
ML-Enhanced Property Matcher Service
Advanced property matching with confidence scoring and ML features
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    # Fallback for environments without numpy
    HAS_NUMPY = False
    np = None

try:
    from ghl_utils.logger import get_logger
except ImportError:
    # Fallback logger
    import logging

    def get_logger(name):
        return logging.getLogger(name)


logger = get_logger(__name__)


@dataclass
class ConfidenceScore:
    """
    Comprehensive confidence score for property matches with component breakdown
    """

    overall: float = 0.0
    budget_match: float = 0.0
    location_match: float = 0.0
    feature_match: float = 0.0
    market_context: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    confidence_level: Optional[str] = None

    def get_confidence_level(self) -> str:
        """Classify confidence level based on overall score"""
        if self.confidence_level:
            return self.confidence_level

        if self.overall >= 80:
            return "high"
        elif self.overall >= 60:
            return "medium"
        else:
            return "low"


class MLFeaturePipeline:
    """
    Feature engineering pipeline for ML-based property matching
    """

    def __init__(self):
        self.numerical_features = [
            "price",
            "sqft",
            "bedrooms",
            "bathrooms",
            "year_built",
            "school_rating",
            "crime_score",
            "walkability_score",
            "days_on_market",
            "price_per_sqft",
        ]

        self.categorical_features = ["property_type", "neighborhood", "amenities"]

        self.derived_features = [
            "price_normalized",
            "location_score",
            "amenity_count",
            "price_per_sqft_percentile",
            "market_hotness",
        ]

    def normalize_price_features(self, price: float, market_data: Dict) -> float:
        """Normalize price based on local market data"""
        market_median = market_data.get("median_price", 500000)
        return min(price / market_median, 2.0)  # Cap at 2x median

    def encode_categorical_features(self, property_data: Dict) -> Dict[str, float]:
        """Encode categorical features for ML processing"""
        encoded = {}

        # Property type encoding
        type_scores = {"single family": 1.0, "townhome": 0.8, "condo": 0.6, "multi-family": 0.4}
        property_type = property_data.get("property_type", "").lower()
        encoded["property_type_score"] = type_scores.get(property_type, 0.5)

        # Neighborhood desirability (would be learned from data)
        neighborhood = property_data.get("address", {}).get("neighborhood", "").lower()
        neighborhood_scores = {
            "downtown": 0.9,
            "domain": 0.8,
            "south congress": 0.85,
            "westlake": 0.95,
            "mueller": 0.8,
            "circle c": 0.7,
        }
        encoded["neighborhood_score"] = neighborhood_scores.get(neighborhood, 0.5)

        return encoded

    def create_interaction_features(self, features: Dict) -> Dict[str, float]:
        """Create interaction features for better matching"""
        interactions = {}

        # Price per bedroom efficiency
        if features.get("bedrooms", 0) > 0:
            interactions["price_per_bedroom"] = features.get("price", 0) / features["bedrooms"]

        # Space efficiency
        if features.get("sqft", 0) > 0:
            interactions["sqft_per_bedroom"] = features.get("sqft", 0) / max(features.get("bedrooms", 1), 1)

        # Market timing score
        days_on_market = features.get("days_on_market", 30)
        interactions["market_timing_score"] = max(0, 1 - (days_on_market / 90))

        return interactions


class MLModelRegistry:
    """
    Registry for different ML models used in property matching
    """

    def __init__(self):
        self.models = {}
        self.model_metadata = {}

    def register_model(self, name: str, model: Any, metadata: Dict = None):
        """Register a trained model"""
        self.models[name] = model
        self.model_metadata[name] = metadata or {}

    def get_model(self, name: str) -> Optional[Any]:
        """Get a registered model"""
        return self.models.get(name)

    def list_models(self) -> List[str]:
        """List all registered models"""
        return list(self.models.keys())

    def supports_model_type(self, model_type: str) -> bool:
        """Check if a model type is supported"""
        supported_types = [
            "random_forest_confidence",
            "gradient_boost_match",
            "neural_preference_scorer",
            "market_trend_predictor",
        ]
        return model_type in supported_types


class PropertyMatcherML:
    """
    ML-Enhanced Property Matcher with confidence scoring and advanced features
    """

    def __init__(self, listings_path: Optional[str] = None):
        """
        Initialize the ML-enhanced Property Matcher

        Args:
            listings_path: Path to the property listings JSON file
        """
        self.listings_path = (
            Path(listings_path)
            if listings_path
            else Path(__file__).parent.parent / "data" / "knowledge_base" / "property_listings.json"
        )

        self.listings = self._load_listings()
        self.feature_pipeline = MLFeaturePipeline()
        self.model_registry = MLModelRegistry()

        # Placeholder for ML models (to be trained)
        self.ml_models = None

        # Market data cache (would be populated from real data)
        self.market_data = self._load_market_data()

    def _load_listings(self) -> List[Dict[str, Any]]:
        """Load listings from JSON file with enhanced error handling"""
        try:
            if self.listings_path.exists():
                with open(self.listings_path, "r") as f:
                    data = json.load(f)
                    listings = data.get("listings", [])
                    logger.info(f"Loaded {len(listings)} property listings")
                    return listings
            else:
                logger.warning(f"Property listings file not found at {self.listings_path}")
                return self._get_demo_listings()
        except Exception as e:
            logger.error(f"Failed to load property listings: {e}")
            return self._get_demo_listings()

    def _get_demo_listings(self) -> List[Dict[str, Any]]:
        """Get demo listings for testing when file is not available"""
        return [
            {
                "id": "demo_prop_1",
                "price": 750000,
                "address": {"street": "123 Oak Street", "neighborhood": "Downtown", "city": "Austin", "zip": "78701"},
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2100,
                "property_type": "Single Family",
                "year_built": 2015,
                "amenities": ["pool", "garage", "garden"],
                "school_rating": 8.5,
                "crime_score": 7.2,
                "walkability_score": 85,
                "days_on_market": 15,
                "price_per_sqft": 357.14,
            }
        ]

    def _load_market_data(self) -> Dict[str, Any]:
        """Load market context data (median prices, trends, etc.)"""
        # In production, this would load from a real market data source
        return {
            "median_price": 525000,
            "price_trend": 0.08,  # 8% annual growth
            "inventory_level": "low",
            "median_days_on_market": 25,
        }

    def extract_features(self, property_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract comprehensive features from property data for ML processing

        Args:
            property_data: Raw property data

        Returns:
            Dict of extracted features
        """
        features = {}

        # Basic numerical features
        for feature in self.feature_pipeline.numerical_features:
            features[feature] = float(property_data.get(feature, 0))

        # Normalized price features
        price = property_data.get("price", 0)
        features["price_normalized"] = self.feature_pipeline.normalize_price_features(price, self.market_data)

        # Categorical feature encoding
        encoded_cats = self.feature_pipeline.encode_categorical_features(property_data)
        features.update(encoded_cats)

        # Derived features
        features["amenity_count"] = len(property_data.get("amenities", []))

        # Market context features
        features["price_per_sqft_percentile"] = self._calculate_price_percentile(property_data.get("price_per_sqft", 0))
        features["market_hotness"] = self._calculate_market_hotness(property_data)

        # Location scoring
        features["location_score"] = encoded_cats.get("neighborhood_score", 0.5)

        # Interaction features
        interactions = self.feature_pipeline.create_interaction_features(features)
        features.update(interactions)

        return features

    def _calculate_price_percentile(self, price_per_sqft: float) -> float:
        """Calculate price per sqft percentile in local market"""
        # Simplified percentile calculation (would use real market data)
        market_median_psf = 280  # Example median
        return min(price_per_sqft / market_median_psf, 2.0)

    def _calculate_market_hotness(self, property_data: Dict[str, Any]) -> float:
        """Calculate market hotness score based on listing velocity"""
        days_on_market = property_data.get("days_on_market", 30)
        median_dom = self.market_data["median_days_on_market"]

        # Properties that sell faster than median are "hot"
        hotness = max(0, 1 - (days_on_market / median_dom))
        return hotness

    def calculate_budget_confidence(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """
        Calculate confidence score for budget match with nuanced scoring

        Args:
            property_data: Property information
            preferences: Lead preferences

        Returns:
            Confidence score between 0 and 1
        """
        budget = preferences.get("budget")
        if not budget:
            return 0.5  # Neutral confidence if budget not specified

        price = property_data.get("price", 0)
        if price == 0:
            return 0.0  # No confidence without price

        price_ratio = price / budget

        if price_ratio <= 0.9:  # Well under budget
            return 0.95
        elif price_ratio <= 1.0:  # Within budget
            return 0.9
        elif price_ratio <= 1.05:  # 5% over budget (acceptable stretch)
            return 0.7
        elif price_ratio <= 1.1:  # 10% over budget (significant stretch)
            return 0.4
        else:  # More than 10% over budget
            return max(0, 0.3 - (price_ratio - 1.1) * 0.5)

    def calculate_location_confidence(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """
        Calculate confidence score for location match

        Args:
            property_data: Property information
            preferences: Lead preferences

        Returns:
            Confidence score between 0 and 1
        """
        pref_location = preferences.get("location")
        if not pref_location:
            return 0.5  # Neutral if no location preference

        address = property_data.get("address", {})
        prop_neighborhood = address.get("neighborhood", "").lower()
        prop_city = address.get("city", "").lower()

        # Handle multiple preferred locations
        if isinstance(pref_location, str):
            pref_locations = [pref_location.lower()]
        else:
            pref_locations = [loc.lower() for loc in pref_location]

        # Exact neighborhood match
        for pref_loc in pref_locations:
            if pref_loc in prop_neighborhood:
                return 0.95

        # City match
        for pref_loc in pref_locations:
            if pref_loc in prop_city:
                return 0.8

        # Adjacent area heuristics (would be enhanced with real geographic data)
        neighborhood_clusters = {
            "downtown": ["east austin", "south congress"],
            "westlake": ["rollingwood", "bee cave"],
            "domain": ["round rock", "cedar park"],
        }

        for pref_loc in pref_locations:
            for cluster_key, cluster_areas in neighborhood_clusters.items():
                if pref_loc in cluster_key and prop_neighborhood in cluster_areas:
                    return 0.6
                elif pref_loc in cluster_areas and cluster_key in prop_neighborhood:
                    return 0.6

        return 0.3  # No location match

    def calculate_feature_confidence(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """
        Calculate confidence score for features and amenities match

        Args:
            property_data: Property information
            preferences: Lead preferences

        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0
        total_weight = 0.0

        # Bedroom match (high weight)
        pref_beds = preferences.get("bedrooms")
        if pref_beds:
            prop_beds = property_data.get("bedrooms", 0)
            if prop_beds >= pref_beds:
                score += 0.2
            elif prop_beds == pref_beds - 1:
                score += 0.1
            total_weight += 0.2

        # Must-have amenities (critical)
        must_haves = preferences.get("must_haves", [])
        if must_haves:
            prop_amenities = [a.lower() for a in property_data.get("amenities", [])]
            prop_features = str(property_data).lower()  # Search entire property data

            must_have_matches = 0
            for must_have in must_haves:
                must_have_lower = must_have.lower()
                # Check amenities and derived features
                if must_have_lower in prop_amenities or any(
                    keyword in prop_features for keyword in self._get_feature_keywords(must_have_lower)
                ):
                    must_have_matches += 1

            if must_have_matches == len(must_haves):
                score += 0.6  # All must-haves satisfied
            else:
                # Partial satisfaction reduces confidence significantly
                satisfaction_ratio = must_have_matches / len(must_haves)
                score += 0.6 * (satisfaction_ratio**2) * 0.5

            total_weight += 0.6

        # Nice-to-have amenities (bonus points)
        nice_to_haves = preferences.get("nice_to_haves", [])
        if nice_to_haves:
            prop_amenities = [a.lower() for a in property_data.get("amenities", [])]
            prop_features = str(property_data).lower()

            nice_to_have_matches = 0
            for nice_to_have in nice_to_haves:
                nice_to_have_lower = nice_to_have.lower()
                if nice_to_have_lower in prop_amenities or any(
                    keyword in prop_features for keyword in self._get_feature_keywords(nice_to_have_lower)
                ):
                    nice_to_have_matches += 1

            bonus = min(0.1, (nice_to_have_matches / len(nice_to_haves)) * 0.1)
            score += bonus
            total_weight += 0.1

        # Property type match
        pref_type = preferences.get("property_type")
        if pref_type:
            prop_type = property_data.get("property_type", "").lower()
            if pref_type.lower() in prop_type:
                score += 0.1
            total_weight += 0.1

        # Normalize score
        if total_weight > 0:
            return min(1.0, score / total_weight)
        else:
            return 0.6  # Default score when no specific features requested

    def _get_feature_keywords(self, feature: str) -> List[str]:
        """Get keywords to search for a given feature"""
        feature_keywords = {
            "garage": ["garage", "parking", "covered parking"],
            "pool": ["pool", "swimming"],
            "garden": ["garden", "landscap", "yard"],
            "good_schools": ["school", "rating", "education"],
            "walkable": ["walk", "walkability", "transit"],
            "modern": ["modern", "updated", "renovated", "contemporary"],
            "quiet": ["quiet", "peaceful", "cul-de-sac"],
            "view": ["view", "scenic", "overlook"],
        }
        return feature_keywords.get(feature, [feature])

    def calculate_market_confidence(self, property_data: Dict[str, Any]) -> float:
        """
        Calculate confidence based on market context and timing

        Args:
            property_data: Property information

        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0

        # Days on market analysis
        days_on_market = property_data.get("days_on_market", 30)
        median_dom = self.market_data["median_days_on_market"]

        if days_on_market <= median_dom * 0.5:  # Selling fast
            score += 0.4
        elif days_on_market <= median_dom:  # Normal pace
            score += 0.3
        elif days_on_market <= median_dom * 2:  # Slower than average
            score += 0.2
        else:  # Stale listing
            score += 0.1

        # Price positioning
        price_per_sqft = property_data.get("price_per_sqft", 0)
        market_median_psf = 280  # Would be dynamic

        price_ratio = price_per_sqft / market_median_psf if market_median_psf > 0 else 1
        if 0.9 <= price_ratio <= 1.1:  # Well-priced
            score += 0.3
        elif 0.8 <= price_ratio < 0.9:  # Great value
            score += 0.4
        elif price_ratio < 0.8:  # Suspiciously cheap
            score += 0.2
        else:  # Overpriced
            score += 0.1

        # Property condition indicators
        year_built = property_data.get("year_built", 2000)
        current_year = datetime.now().year
        property_age = current_year - year_built

        if property_age <= 5:  # New construction
            score += 0.2
        elif property_age <= 15:  # Relatively new
            score += 0.15
        elif property_age <= 30:  # Established
            score += 0.1
        else:  # Older property
            score += 0.05

        # School quality (if available)
        school_rating = property_data.get("school_rating", 0)
        if school_rating >= 9:
            score += 0.1
        elif school_rating >= 7:
            score += 0.05

        return min(1.0, score)

    def calculate_confidence_score(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> ConfidenceScore:
        """
        Calculate comprehensive confidence score with all components

        Args:
            property_data: Property information
            preferences: Lead preferences

        Returns:
            ConfidenceScore object with detailed breakdown
        """
        # Calculate component scores (0-1 scale)
        budget_conf = self.calculate_budget_confidence(property_data, preferences)
        location_conf = self.calculate_location_confidence(property_data, preferences)
        feature_conf = self.calculate_feature_confidence(property_data, preferences)
        market_conf = self.calculate_market_confidence(property_data)

        # Weighted overall score
        weights = {"budget": 0.35, "location": 0.30, "features": 0.25, "market": 0.10}

        overall_score = (
            budget_conf * weights["budget"]
            + location_conf * weights["location"]
            + feature_conf * weights["features"]
            + market_conf * weights["market"]
        )

        # Convert to 0-100 scale
        overall_percentage = overall_score * 100

        # Generate reasoning
        reasoning = self._generate_detailed_reasoning(
            property_data, preferences, budget_conf, location_conf, feature_conf, market_conf
        )

        score_obj = ConfidenceScore(
            overall=round(overall_percentage, 1),
            budget_match=round(budget_conf * 100, 1),
            location_match=round(location_conf * 100, 1),
            feature_match=round(feature_conf * 100, 1),
            market_context=round(market_conf * 100, 1),
            reasoning=reasoning,
        )
        score_obj.confidence_level = score_obj.get_confidence_level()
        return score_obj

    def _generate_detailed_reasoning(
        self,
        property_data: Dict[str, Any],
        preferences: Dict[str, Any],
        budget_conf: float,
        location_conf: float,
        feature_conf: float,
        market_conf: float,
    ) -> List[str]:
        """Generate human-readable reasoning for the confidence score"""
        reasoning = []

        # Budget reasoning
        budget = preferences.get("budget", 0)
        price = property_data.get("price", 0)
        if budget and price:
            if price <= budget * 0.9:
                savings = budget - price
                reasoning.append(f"Excellent value at ${savings / 1000:.0f}k under your ${budget / 1000:.0f}k budget")
            elif price <= budget:
                reasoning.append(f"Perfectly priced within your ${budget / 1000:.0f}k budget")
            elif price <= budget * 1.05:
                overage = price - budget
                reasoning.append(f"Slight stretch at ${overage / 1000:.0f}k over budget, but worth considering")

        # Location reasoning
        pref_location = preferences.get("location")
        if pref_location and location_conf > 0.8:
            neighborhood = property_data.get("address", {}).get("neighborhood", "")
            reasoning.append(f"Prime location in {neighborhood} as requested")
        elif location_conf > 0.6:
            reasoning.append("Good location match with nearby amenities")

        # Feature reasoning
        must_haves = preferences.get("must_haves", [])
        if must_haves and feature_conf > 0.8:
            reasoning.append(f"Has all your must-have features: {', '.join(must_haves)}")

        beds_requested = preferences.get("bedrooms")
        beds_actual = property_data.get("bedrooms", 0)
        if beds_requested and beds_actual >= beds_requested:
            reasoning.append(f"Perfect {beds_actual}-bedroom layout matches your needs")

        # Market context reasoning
        days_on_market = property_data.get("days_on_market", 30)
        if days_on_market <= 20:
            reasoning.append("Hot property - recently listed and likely to move quickly")

        price_per_sqft = property_data.get("price_per_sqft", 0)
        if price_per_sqft < 280:  # Below market median
            reasoning.append("Great price per square foot compared to local market")

        # School quality
        school_rating = property_data.get("school_rating", 0)
        if school_rating >= 8:
            reasoning.append(f"Excellent schools (rated {school_rating}/10)")

        # Fallback reasoning
        if not reasoning:
            reasoning.append("Strong overall match based on your preferences")

        return reasoning

    def analyze_feature_importance(
        self, property_data: Dict[str, Any], preferences: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Analyze which features contributed most to the confidence score

        Args:
            property_data: Property information
            preferences: Lead preferences

        Returns:
            Dict of feature importance scores
        """
        budget_conf = self.calculate_budget_confidence(property_data, preferences)
        location_conf = self.calculate_location_confidence(property_data, preferences)
        feature_conf = self.calculate_feature_confidence(property_data, preferences)
        market_conf = self.calculate_market_confidence(property_data)

        # Weights from confidence calculation
        weights = {"budget": 0.35, "location": 0.30, "features": 0.25, "market": 0.10}

        # Calculate contribution of each component
        importance = {
            "budget": budget_conf * weights["budget"],
            "location": location_conf * weights["location"],
            "features": feature_conf * weights["features"],
            "market": market_conf * weights["market"],
        }

        # Normalize to sum to 1.0
        total = sum(importance.values())
        if total > 0:
            importance = {k: v / total for k, v in importance.items()}

        return importance

    def find_enhanced_matches(
        self, preferences: Dict[str, Any], limit: int = 5, min_confidence: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Find property matches using ML-enhanced confidence scoring

        Args:
            preferences: Lead preferences
            limit: Maximum number of matches to return
            min_confidence: Minimum confidence score (0-100) to include

        Returns:
            List of properties with enhanced confidence scores
        """
        matches = []

        for property_data in self.listings:
            confidence_score = self.calculate_confidence_score(property_data, preferences)

            if confidence_score.overall >= min_confidence:
                enhanced_property = property_data.copy()
                enhanced_property["confidence_score"] = confidence_score
                enhanced_property["match_score"] = int(confidence_score.overall)  # For UI compatibility

                # Enhanced match reasons for UI
                enhanced_property["match_reasons"] = confidence_score.reasoning

                matches.append(enhanced_property)

        # Sort by confidence score
        matches.sort(key=lambda x: x["confidence_score"].overall, reverse=True)

        return matches[:limit]

    def train_confidence_model(self, features: List[List[float]], labels: List[float]) -> Dict[str, Any]:
        """
        Placeholder for training ML models on confidence scoring

        Args:
            features: Feature matrix for training (list of feature vectors)
            labels: Ground truth confidence scores

        Returns:
            Training results and model metadata
        """
        # This would implement actual ML model training
        # For now, return a placeholder structure
        feature_count = len(features[0]) if features and len(features) > 0 else 0
        return {
            "model_type": "confidence_scorer",
            "training_samples": len(features),
            "feature_count": feature_count,
            "status": "placeholder_implementation",
        }
