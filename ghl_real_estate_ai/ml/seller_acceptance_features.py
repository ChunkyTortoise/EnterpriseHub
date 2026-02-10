"""
Seller Acceptance Feature Extraction Pipeline.

Extracts comprehensive features for predicting seller offer acceptance probability.
Covers seller psychology, pricing metrics, market context, property characteristics,
and comparable properties analysis.

Performance Target: <500ms extraction time
Feature Count: 20 normalized features [0, 1]
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SellerAcceptanceFeatures:
    """Normalized features for seller acceptance prediction.

    All features are normalized to [0, 1] range for ML model compatibility.
    """

    # Seller Psychology (5 features)
    psychological_commitment_score: float = 0.5  # PCS normalized
    urgency_score: float = 0.5  # Urgency level normalized
    motivation_intensity: float = 0.5  # Motivation strength normalized
    negotiation_flexibility: float = 0.5  # Flexibility score normalized
    communication_engagement: float = 0.5  # Engagement quality normalized

    # Pricing Metrics (5 features)
    list_price_ratio: float = 0.5  # List price / market value
    price_reduction_history: float = 0.0  # Total price drops normalized
    days_on_market_ratio: float = 0.5  # DOM vs market avg
    price_competitiveness: float = 0.5  # Price vs comps
    overpricing_penalty: float = 0.0  # Penalty for overpricing

    # Market Context (4 features)
    inventory_pressure: float = 0.5  # Market inventory level
    absorption_rate: float = 0.5  # Market absorption rate
    price_trend_momentum: float = 0.5  # Market price trend
    seasonal_factor: float = 0.5  # Seasonal demand factor

    # Property Characteristics (3 features)
    property_appeal_score: float = 0.5  # Bed/bath/sqft attractiveness
    condition_score: float = 0.5  # Property condition normalized
    location_desirability: float = 0.5  # Location quality

    # Comparables Analysis (3 features)
    comp_count_confidence: float = 0.5  # Number of comps normalized
    comp_price_variance: float = 0.5  # Price variance in comps
    comp_market_time: float = 0.5  # Avg DOM for comps normalized

    # Metadata
    extraction_time_ms: float = 0.0
    missing_fields: List[str] = field(default_factory=list)

    def to_feature_vector(self) -> List[float]:
        """Convert to flat feature vector for ML models."""
        return [
            # Seller Psychology
            self.psychological_commitment_score,
            self.urgency_score,
            self.motivation_intensity,
            self.negotiation_flexibility,
            self.communication_engagement,
            # Pricing Metrics
            self.list_price_ratio,
            self.price_reduction_history,
            self.days_on_market_ratio,
            self.price_competitiveness,
            self.overpricing_penalty,
            # Market Context
            self.inventory_pressure,
            self.absorption_rate,
            self.price_trend_momentum,
            self.seasonal_factor,
            # Property Characteristics
            self.property_appeal_score,
            self.condition_score,
            self.location_desirability,
            # Comparables Analysis
            self.comp_count_confidence,
            self.comp_price_variance,
            self.comp_market_time,
        ]

    @staticmethod
    def feature_names() -> List[str]:
        """Return ordered list of feature names."""
        return [
            # Seller Psychology
            "psychological_commitment_score",
            "urgency_score",
            "motivation_intensity",
            "negotiation_flexibility",
            "communication_engagement",
            # Pricing Metrics
            "list_price_ratio",
            "price_reduction_history",
            "days_on_market_ratio",
            "price_competitiveness",
            "overpricing_penalty",
            # Market Context
            "inventory_pressure",
            "absorption_rate",
            "price_trend_momentum",
            "seasonal_factor",
            # Property Characteristics
            "property_appeal_score",
            "condition_score",
            "location_desirability",
            # Comparables Analysis
            "comp_count_confidence",
            "comp_price_variance",
            "comp_market_time",
        ]


class SellerAcceptanceFeatureExtractor:
    """Extract and normalize features for seller acceptance prediction.

    Performance Target: <500ms per extraction
    Feature Normalization: All features scaled to [0, 1]
    Missing Value Handling: Sensible defaults based on market norms
    """

    # Market normalization constants (Rancho Cucamonga market)
    MAX_DOM = 120  # Maximum expected days on market
    MAX_PRICE = 2_000_000  # Maximum expected property price
    MAX_SQFT = 5000  # Maximum expected square footage
    MAX_COMPS = 20  # Maximum expected comparable count
    MAX_PRICE_DROP_PCT = 30.0  # Maximum expected price reduction %

    # Seasonal factors by month (0=Jan, 11=Dec)
    SEASONAL_FACTORS = [
        0.4, 0.5, 0.7, 0.85, 0.95, 1.0,  # Jan-Jun
        1.0, 0.95, 0.85, 0.7, 0.5, 0.4   # Jul-Dec
    ]

    def __init__(self):
        """Initialize the feature extractor."""
        self.extraction_count = 0
        self.total_extraction_time_ms = 0.0

    def extract_features(
        self,
        seller_id: str,
        property_data: Dict[str, Any],
        market_data: Dict[str, Any],
        psychology_profile: Optional[Dict[str, Any]] = None,
        conversation_data: Optional[Dict[str, Any]] = None,
    ) -> SellerAcceptanceFeatures:
        """Extract comprehensive features for seller acceptance prediction.

        Args:
            seller_id: Unique seller identifier
            property_data: Property details (price, sqft, beds, baths, condition, etc.)
            market_data: Market context (inventory, DOM, price trends, comps)
            psychology_profile: Optional seller psychology analysis (PCS, urgency, etc.)
            conversation_data: Optional conversation history and engagement metrics

        Returns:
            SellerAcceptanceFeatures with all 20 normalized features
        """
        start_time = time.perf_counter()
        features = SellerAcceptanceFeatures()

        try:
            # Extract seller psychology features
            self._extract_psychology_features(features, psychology_profile, conversation_data)

            # Extract pricing metrics
            self._extract_pricing_features(features, property_data, market_data)

            # Extract market context features
            self._extract_market_features(features, market_data)

            # Extract property characteristics
            self._extract_property_features(features, property_data)

            # Extract comparables analysis
            self._extract_comparable_features(features, market_data)

            # Calculate extraction time
            extraction_time = (time.perf_counter() - start_time) * 1000
            features.extraction_time_ms = extraction_time

            # Update statistics
            self.extraction_count += 1
            self.total_extraction_time_ms += extraction_time

            if extraction_time > 500:
                logger.warning(
                    f"Feature extraction exceeded target: {extraction_time:.2f}ms "
                    f"for seller {seller_id}"
                )

            logger.info(
                f"Extracted {len(features.feature_names())} features in {extraction_time:.2f}ms "
                f"for seller {seller_id}"
            )

            return features

        except Exception as e:
            logger.error(f"Error extracting features for seller {seller_id}: {e}")
            # Return features with defaults on error
            features.extraction_time_ms = (time.perf_counter() - start_time) * 1000
            features.missing_fields.append("extraction_error")
            return features

    def _extract_psychology_features(
        self,
        features: SellerAcceptanceFeatures,
        psychology_profile: Optional[Dict[str, Any]],
        conversation_data: Optional[Dict[str, Any]],
    ) -> None:
        """Extract seller psychology features (5 features)."""

        if psychology_profile:
            # Psychological Commitment Score (PCS)
            pcs = psychology_profile.get("psychological_commitment_score", 50.0)
            features.psychological_commitment_score = self._normalize_feature(
                pcs, min_val=0.0, max_val=100.0
            )

            # Urgency Score
            urgency_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
            urgency_level = psychology_profile.get("urgency_level", "medium")
            features.urgency_score = urgency_map.get(urgency_level, 0.5)

            # Motivation Intensity
            motivation_map = {
                "upsizing": 0.7,
                "downsizing": 0.6,
                "relocation": 0.8,
                "financial": 0.9,
                "divorce": 0.95,
                "estate": 0.85,
                "investment": 0.5,
            }
            motivation_type = psychology_profile.get("motivation_type", "unknown")
            features.motivation_intensity = motivation_map.get(motivation_type, 0.5)

            # Negotiation Flexibility
            flexibility = psychology_profile.get("negotiation_flexibility", 0.5)
            features.negotiation_flexibility = float(flexibility)
        else:
            features.missing_fields.append("psychology_profile")

        # Communication Engagement
        if conversation_data:
            msg_count = conversation_data.get("message_count", 0)
            avg_response_time = conversation_data.get("avg_response_time_seconds", 3600)

            # Higher message count = higher engagement (cap at 50 messages)
            msg_score = min(msg_count / 50.0, 1.0)

            # Lower response time = higher engagement (normalize to 1 hour)
            response_score = 1.0 - min(avg_response_time / 3600.0, 1.0)

            features.communication_engagement = (msg_score + response_score) / 2.0
        else:
            features.missing_fields.append("conversation_data")

    def _extract_pricing_features(
        self,
        features: SellerAcceptanceFeatures,
        property_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> None:
        """Extract pricing metrics features (5 features)."""

        # List Price Ratio (list price / estimated market value)
        list_price = property_data.get("list_price", 0.0)
        market_value = property_data.get("estimated_market_value") or market_data.get(
            "estimated_value", list_price
        )

        if market_value > 0:
            price_ratio = list_price / market_value
            # Normalize: 0.8 (20% under) to 1.2 (20% over) maps to [0, 1]
            features.list_price_ratio = self._normalize_feature(
                price_ratio, min_val=0.8, max_val=1.2, clip=True
            )

            # Overpricing penalty (0 if fairly priced, up to 1.0 if severely overpriced)
            if price_ratio > 1.0:
                features.overpricing_penalty = min((price_ratio - 1.0) * 5, 1.0)
        else:
            features.missing_fields.append("market_value")

        # Price Reduction History
        price_drops = property_data.get("price_drops", [])
        if price_drops:
            total_reduction_pct = sum(drop.get("percentage", 0) for drop in price_drops)
            features.price_reduction_history = self._normalize_feature(
                total_reduction_pct, min_val=0.0, max_val=self.MAX_PRICE_DROP_PCT
            )

        # Days on Market Ratio
        dom = property_data.get("days_on_market", 0)
        market_avg_dom = market_data.get("average_days_on_market", 30)

        if market_avg_dom > 0:
            dom_ratio = dom / market_avg_dom
            # Normalize: 0 to 3x market average
            features.days_on_market_ratio = self._normalize_feature(
                dom_ratio, min_val=0.0, max_val=3.0, clip=True
            )
        else:
            features.missing_fields.append("market_avg_dom")

        # Price Competitiveness (vs comparable properties)
        comps = market_data.get("comparables", [])
        if comps and list_price > 0:
            comp_prices = [c.get("sale_price", 0) for c in comps if c.get("sale_price")]
            if comp_prices:
                median_comp_price = float(np.median(comp_prices))
                comp_ratio = list_price / median_comp_price if median_comp_price > 0 else 1.0
                # Normalize: 0.8 to 1.2 (±20% vs comps)
                features.price_competitiveness = 1.0 - self._normalize_feature(
                    abs(comp_ratio - 1.0), min_val=0.0, max_val=0.2, clip=True
                )
            else:
                features.missing_fields.append("comp_prices")
        else:
            features.missing_fields.append("comparables_or_list_price")

    def _extract_market_features(
        self,
        features: SellerAcceptanceFeatures,
        market_data: Dict[str, Any],
    ) -> None:
        """Extract market context features (4 features)."""

        # Inventory Pressure (lower inventory = higher pressure = more likely to accept)
        inventory_level = market_data.get("inventory_level", 6.0)  # Months of inventory
        # Normalize: 12 months (buyer's market) to 2 months (seller's market)
        # Invert so low inventory = high score
        features.inventory_pressure = 1.0 - self._normalize_feature(
            inventory_level, min_val=2.0, max_val=12.0, clip=True
        )

        # Absorption Rate (higher rate = hotter market)
        absorption_rate = market_data.get("absorption_rate", 0.15)  # Properties sold per month
        # Normalize: 0.05 (cold) to 0.3 (hot)
        features.absorption_rate = self._normalize_feature(
            absorption_rate, min_val=0.05, max_val=0.3, clip=True
        )

        # Price Trend Momentum
        price_trend = market_data.get("price_trend_pct", 0.0)  # Year-over-year %
        # Normalize: -10% (declining) to +15% (rising)
        features.price_trend_momentum = self._normalize_feature(
            price_trend, min_val=-10.0, max_val=15.0, clip=True
        )

        # Seasonal Factor (based on current month)
        current_month = market_data.get("current_month", 5)  # 0=Jan, 11=Dec
        if 0 <= current_month <= 11:
            features.seasonal_factor = self.SEASONAL_FACTORS[current_month]
        else:
            features.seasonal_factor = 0.7  # Default to moderate
            features.missing_fields.append("current_month")

    def _extract_property_features(
        self,
        features: SellerAcceptanceFeatures,
        property_data: Dict[str, Any],
    ) -> None:
        """Extract property characteristics features (3 features)."""

        # Property Appeal Score (bed/bath/sqft attractiveness)
        beds = property_data.get("beds", 3)
        baths = property_data.get("baths", 2.0)
        sqft = property_data.get("sqft", 1500)

        # Calculate appeal based on market preferences
        # Ideal: 3-4 bed, 2-3 bath, 1500-2500 sqft
        bed_score = 1.0 - abs(beds - 3.5) / 3.5
        bath_score = 1.0 - abs(baths - 2.5) / 2.5
        sqft_score = 1.0 - abs(sqft - 2000) / 2000

        features.property_appeal_score = max(
            0.0, (bed_score + bath_score + sqft_score) / 3.0
        )

        # Condition Score
        condition_map = {
            "excellent": 1.0,
            "good": 0.8,
            "fair": 0.6,
            "needs_work": 0.4,
            "poor": 0.2,
            "move_in_ready": 0.9,
            "fixer_upper": 0.3,
        }
        condition = property_data.get("condition", "fair")
        features.condition_score = condition_map.get(condition, 0.6)

        # Location Desirability
        # Based on zip code, neighborhood, school ratings, etc.
        location_data = property_data.get("location", {})
        school_rating = location_data.get("school_rating", 5) / 10.0
        walkability = location_data.get("walkability_score", 50) / 100.0

        features.location_desirability = (school_rating + walkability) / 2.0

    def _extract_comparable_features(
        self,
        features: SellerAcceptanceFeatures,
        market_data: Dict[str, Any],
    ) -> None:
        """Extract comparables analysis features (3 features)."""

        comps = market_data.get("comparables", [])

        if comps:
            # Comp Count Confidence (more comps = higher confidence)
            comp_count = len(comps)
            features.comp_count_confidence = self._normalize_feature(
                comp_count, min_val=0.0, max_val=self.MAX_COMPS
            )

            # Comp Price Variance (lower variance = more predictable)
            comp_prices = [c.get("sale_price", 0) for c in comps if c.get("sale_price")]
            if len(comp_prices) >= 2:
                price_std = float(np.std(comp_prices))
                mean_price = float(np.mean(comp_prices))
                cv = price_std / mean_price if mean_price > 0 else 0.0  # Coefficient of variation
                # Normalize: 0 (no variance) to 0.3 (high variance)
                # Invert so low variance = high score
                features.comp_price_variance = 1.0 - self._normalize_feature(
                    cv, min_val=0.0, max_val=0.3, clip=True
                )

            # Comp Market Time (average DOM for comparable properties)
            comp_doms = [c.get("days_on_market", 30) for c in comps]
            if comp_doms:
                avg_comp_dom = sum(comp_doms) / len(comp_doms)
                # Normalize: 0 to MAX_DOM days
                # Invert so lower DOM = higher score (faster market)
                features.comp_market_time = 1.0 - self._normalize_feature(
                    avg_comp_dom, min_val=0.0, max_val=self.MAX_DOM
                )
        else:
            features.missing_fields.extend([
                "comp_count",
                "comp_price_variance",
                "comp_market_time",
            ])

    def _normalize_feature(
        self,
        value: float,
        min_val: float,
        max_val: float,
        clip: bool = False,
    ) -> float:
        """Normalize feature to [0, 1] range using min-max normalization.

        Args:
            value: Raw feature value
            min_val: Minimum expected value
            max_val: Maximum expected value
            clip: If True, clip result to [0, 1] range

        Returns:
            Normalized value in [0, 1] range
        """
        if max_val == min_val:
            return 0.5  # Default to midpoint if no range

        normalized = (value - min_val) / (max_val - min_val)

        if clip:
            return max(0.0, min(1.0, normalized))

        return normalized

    def get_statistics(self) -> Dict[str, float]:
        """Get extraction performance statistics."""
        avg_time = (
            self.total_extraction_time_ms / self.extraction_count
            if self.extraction_count > 0
            else 0.0
        )

        return {
            "total_extractions": self.extraction_count,
            "avg_extraction_time_ms": avg_time,
            "total_extraction_time_ms": self.total_extraction_time_ms,
            "target_time_ms": 500.0,
            "performance_ratio": avg_time / 500.0 if avg_time > 0 else 0.0,
        }
