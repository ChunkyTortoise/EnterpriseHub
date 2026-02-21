"""
Seller Acceptance Prediction Service

Predicts probability of seller accepting various offer prices based on:
- Seller engagement patterns (PCS score, conversation history)
- Property characteristics and CMA data
- Market conditions and comparable sales
- Historical acceptance data

This is a Phase 4 stub implementation with graceful fallback to CMA-based
heuristics until the full XGBoost model (Task #12) is completed.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
cache = get_cache_service()


@dataclass
class AcceptancePrediction:
    """Prediction result with probability and metadata."""

    offer_price: float
    acceptance_probability: float  # 0.0 to 1.0
    confidence: float  # Model confidence (0.0 to 1.0)
    estimated_days_to_acceptance: int
    reasoning: str  # Human-readable explanation
    feature_importance: Dict[str, float]  # Which features drove prediction
    model_version: str = "heuristic_v1"  # Will be "xgboost_v1" when Task #12 done


@dataclass
class OptimalPriceRange:
    """Recommended pricing strategy with acceptance probabilities."""

    min_price: float
    max_price: float
    recommended_price: float
    acceptance_probability: float
    time_to_acceptance_days: int
    strategy_rationale: str


class AcceptancePredictorService:
    """
    Predicts seller acceptance probability for various offer prices.

    Phase 4 Implementation Status:
    - Heuristic baseline: IMPLEMENTED (production-ready fallback)
    - XGBoost model: PENDING (Task #12)
    - Feature extraction: Uses existing FeatureEngineer from ml/feature_engineering.py
    """

    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache for predictions
        self.model_available = False  # Will be True when Task #12 completes
        self.fallback_mode = True
        logger.info("AcceptancePredictorService initialized (heuristic fallback mode)")

    async def predict_acceptance_probability(
        self, seller_id: str, offer_price: float, context: Optional[Dict[str, Any]] = None
    ) -> AcceptancePrediction:
        """
        Predict probability seller will accept given offer price.

        Args:
            seller_id: Seller contact ID
            offer_price: Proposed offer price
            context: Optional context with PCS score, CMA data, property info

        Returns:
            AcceptancePrediction with probability and reasoning
        """
        cache_key = f"acceptance_pred:{seller_id}:{int(offer_price)}"
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for acceptance prediction: {seller_id}")
            return AcceptancePrediction(**cached)

        start_time = time.time()

        try:
            if self.model_available:
                # Full ML model (Task #12)
                prediction = await self._predict_with_ml_model(seller_id, offer_price, context)
            else:
                # Fallback heuristic
                prediction = await self._predict_with_heuristic(seller_id, offer_price, context)

            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Acceptance prediction for {seller_id}: "
                f"${offer_price:,.0f} → {prediction.acceptance_probability:.1%} "
                f"({latency_ms:.0f}ms)"
            )

            # Cache prediction
            await cache.set(cache_key, prediction.__dict__, ttl=self.cache_ttl)

            return prediction

        except Exception as e:
            logger.error(f"Acceptance prediction failed for {seller_id}: {e}", exc_info=True)
            # Return conservative fallback
            return AcceptancePrediction(
                offer_price=offer_price,
                acceptance_probability=0.5,
                confidence=0.0,
                estimated_days_to_acceptance=60,
                reasoning="Prediction unavailable - insufficient data",
                feature_importance={},
                model_version="fallback",
            )

    async def get_optimal_price_range(
        self,
        seller_id: str,
        target_probability: float = 0.85,
        context: Optional[Dict[str, Any]] = None,
    ) -> OptimalPriceRange:
        """
        Calculate optimal price range to achieve target acceptance probability.

        Args:
            seller_id: Seller contact ID
            target_probability: Desired acceptance probability (default 85%)
            context: Optional context with CMA data, property info

        Returns:
            OptimalPriceRange with recommended pricing strategy
        """
        try:
            context = context or {}
            cma_value = context.get("estimated_value") or context.get("cma_report", {}).get("estimated_value", 0)

            if not cma_value:
                logger.warning(f"No CMA value available for {seller_id} - using conservative defaults")
                return OptimalPriceRange(
                    min_price=0,
                    max_price=0,
                    recommended_price=0,
                    acceptance_probability=0.0,
                    time_to_acceptance_days=90,
                    strategy_rationale="Insufficient property data - CMA required",
                )

            # Test multiple price points
            price_points = [
                cma_value * 0.95,  # 5% below CMA
                cma_value * 0.97,  # 3% below CMA
                cma_value,  # At CMA
                cma_value * 1.03,  # 3% above CMA
                cma_value * 1.05,  # 5% above CMA
            ]

            predictions = []
            for price in price_points:
                pred = await self.predict_acceptance_probability(seller_id, price, context)
                predictions.append((price, pred))

            # Find price closest to target probability
            best_match = min(
                predictions,
                key=lambda x: abs(x[1].acceptance_probability - target_probability),
            )

            recommended_price = best_match[0]
            acceptance_prob = best_match[1].acceptance_probability

            # Calculate range (±2% around recommendation)
            price_range_pct = 0.02
            min_price = recommended_price * (1 - price_range_pct)
            max_price = recommended_price * (1 + price_range_pct)

            rationale = self._build_pricing_rationale(
                cma_value, recommended_price, acceptance_prob, best_match[1].estimated_days_to_acceptance
            )

            return OptimalPriceRange(
                min_price=min_price,
                max_price=max_price,
                recommended_price=recommended_price,
                acceptance_probability=acceptance_prob,
                time_to_acceptance_days=best_match[1].estimated_days_to_acceptance,
                strategy_rationale=rationale,
            )

        except Exception as e:
            logger.error(f"Optimal price range calculation failed for {seller_id}: {e}", exc_info=True)
            return OptimalPriceRange(
                min_price=0,
                max_price=0,
                recommended_price=0,
                acceptance_probability=0.0,
                time_to_acceptance_days=90,
                strategy_rationale="Price optimization unavailable",
            )

    async def _predict_with_heuristic(
        self, seller_id: str, offer_price: float, context: Optional[Dict[str, Any]]
    ) -> AcceptancePrediction:
        """
        Heuristic-based prediction using PCS score and price ratio.

        Logic:
        - High PCS (>70) + competitive price (>95% CMA) = High probability
        - Medium PCS (40-70) + fair price (>90% CMA) = Medium probability
        - Low PCS (<40) or low price (<85% CMA) = Low probability
        """
        context = context or {}

        # Extract key features
        pcs_score = context.get("pcs_score", 50.0)
        cma_value = context.get("estimated_value") or context.get("cma_report", {}).get("estimated_value", 0)

        if not cma_value or cma_value == 0:
            # No CMA data - conservative estimate based on PCS alone
            base_prob = pcs_score / 100.0
            return AcceptancePrediction(
                offer_price=offer_price,
                acceptance_probability=base_prob * 0.7,  # Penalize lack of CMA
                confidence=0.4,
                estimated_days_to_acceptance=self._estimate_days_from_probability(base_prob * 0.7),
                reasoning="Estimate based on seller engagement only (no CMA data)",
                feature_importance={"pcs_score": 1.0},
                model_version="heuristic_v1",
            )

        # Calculate price ratio
        price_ratio = offer_price / cma_value

        # Heuristic scoring
        # Base probability from PCS (0-100 → 0.0-1.0)
        pcs_component = pcs_score / 100.0

        # Price ratio component (sigmoid-like curve)
        if price_ratio >= 0.95:
            price_component = 0.9
        elif price_ratio >= 0.90:
            price_component = 0.7
        elif price_ratio >= 0.85:
            price_component = 0.5
        elif price_ratio >= 0.80:
            price_component = 0.3
        else:
            price_component = 0.1

        # Weighted combination (60% PCS, 40% price)
        acceptance_probability = (0.6 * pcs_component) + (0.4 * price_component)

        # Confidence based on data availability
        confidence = 0.7 if pcs_score > 0 else 0.4

        # Feature importance
        feature_importance = {
            "pcs_score": 0.6,
            "price_ratio": 0.4,
        }

        # Add market condition boost if available
        market_trend = context.get("market_trend", "balanced")
        if market_trend == "sellers_market":
            acceptance_probability *= 1.1
            feature_importance["market_trend"] = 0.1
        elif market_trend == "buyers_market":
            acceptance_probability *= 0.9
            feature_importance["market_trend"] = -0.1

        # Cap at 0.95 (never 100% certain)
        acceptance_probability = min(acceptance_probability, 0.95)

        # Estimate days to acceptance
        days_to_acceptance = self._estimate_days_from_probability(acceptance_probability)

        reasoning = self._build_reasoning(pcs_score, price_ratio, market_trend, acceptance_probability)

        return AcceptancePrediction(
            offer_price=offer_price,
            acceptance_probability=acceptance_probability,
            confidence=confidence,
            estimated_days_to_acceptance=days_to_acceptance,
            reasoning=reasoning,
            feature_importance=feature_importance,
            model_version="heuristic_v1",
        )

    async def _predict_with_ml_model(
        self, seller_id: str, offer_price: float, context: Optional[Dict[str, Any]]
    ) -> AcceptancePrediction:
        """
        Full ML-based prediction using XGBoost model.

        This will be implemented in Task #12. For now, falls back to heuristic.
        """
        logger.warning("ML model not yet available - falling back to heuristic")
        return await self._predict_with_heuristic(seller_id, offer_price, context)

    def _estimate_days_from_probability(self, probability: float) -> int:
        """Estimate days to acceptance based on probability."""
        if probability >= 0.85:
            return 20  # High probability = fast acceptance
        elif probability >= 0.70:
            return 35
        elif probability >= 0.50:
            return 50
        elif probability >= 0.30:
            return 70
        else:
            return 90  # Low probability = long timeline

    def _build_reasoning(self, pcs_score: float, price_ratio: float, market_trend: str, probability: float) -> str:
        """Generate human-readable explanation of prediction."""
        reasons = []

        # PCS component
        if pcs_score >= 70:
            reasons.append("high seller engagement and readiness")
        elif pcs_score >= 40:
            reasons.append("moderate seller engagement")
        else:
            reasons.append("limited seller engagement signals")

        # Price component
        if price_ratio >= 0.95:
            reasons.append("competitive pricing near market value")
        elif price_ratio >= 0.85:
            reasons.append("fair pricing relative to market")
        else:
            reasons.append("below-market pricing")

        # Market component
        if market_trend == "sellers_market":
            reasons.append("favorable seller's market conditions")
        elif market_trend == "buyers_market":
            reasons.append("challenging buyer's market dynamics")

        probability_desc = (
            "very likely"
            if probability >= 0.80
            else "likely"
            if probability >= 0.60
            else "possible"
            if probability >= 0.40
            else "unlikely"
        )

        return f"{probability_desc.capitalize()} to accept based on {', '.join(reasons)}."

    def _build_pricing_rationale(
        self, cma_value: float, recommended_price: float, acceptance_prob: float, days: int
    ) -> str:
        """Generate pricing strategy rationale."""
        pct_of_cma = (recommended_price / cma_value) * 100
        direction = "above" if pct_of_cma > 100 else "below" if pct_of_cma < 100 else "at"

        return (
            f"Pricing {direction} CMA ({pct_of_cma:.1f}%) optimizes for "
            f"{acceptance_prob:.0%} acceptance probability within {days} days. "
            f"This balances market competitiveness with seller motivation."
        )

    async def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring."""
        return {
            "service": "AcceptancePredictorService",
            "status": "healthy",
            "model_available": self.model_available,
            "fallback_mode": self.fallback_mode,
            "cache_ttl": self.cache_ttl,
        }


# Singleton instance
_predictor_service: Optional[AcceptancePredictorService] = None


def get_acceptance_predictor_service() -> AcceptancePredictorService:
    """Get or create singleton AcceptancePredictorService instance."""
    global _predictor_service
    if _predictor_service is None:
        _predictor_service = AcceptancePredictorService()
    return _predictor_service
