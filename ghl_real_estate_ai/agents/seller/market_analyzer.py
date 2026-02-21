"""
Market analysis and pricing guidance service.

Analyzes market conditions and provides ML-powered pricing guidance.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService

try:
    from ghl_real_estate_ai.services.jorge.acceptance_predictor_service import get_acceptance_predictor_service

    ACCEPTANCE_PREDICTOR_AVAILABLE = True
except ImportError:
    ACCEPTANCE_PREDICTOR_AVAILABLE = False

logger = get_logger(__name__)


class MarketAnalyzer:
    """Service for market analysis and pricing guidance."""

    def __init__(self, ab_testing: Optional[ABTestingService] = None):
        self.ab_testing = ab_testing or ABTestingService()

    async def analyze_market_conditions(self, state: JorgeSellerState) -> Dict[str, Any]:
        """Determine market trend from available data."""
        market_data = state.get("market_data")
        if not market_data:
            return {"market_trend": "balanced"}

        try:
            inventory_level = market_data.get("inventory_level", 1450)
            # Use months of inventory approximation:
            # < 3 months supply = sellers market
            # > 6 months supply = buyers market
            # Rancho Cucamonga: ~480 sales/month avg, so months = inventory / 480
            months_of_inventory = inventory_level / 480

            if months_of_inventory < 3:
                trend = "sellers_market"
            elif months_of_inventory > 6:
                trend = "buyers_market"
            else:
                trend = "balanced"

            return {"market_trend": trend}

        except Exception as e:
            logger.warning(f"Market conditions analysis failed: {e}")
            return {"market_trend": "balanced"}

    async def provide_pricing_guidance(self, state: JorgeSellerState) -> Dict[str, Any]:
        """
        Generate ML-powered pricing guidance using acceptance predictions.

        Phase 4 Task #13: Integrates AcceptancePredictorService to provide
        data-driven pricing recommendations with acceptance probabilities.

        Includes A/B test: ML predictions vs static CMA-only guidance.
        """
        contact_id = state.get("contact_id", "unknown")
        property_address = state.get("property_address")
        cma_report = state.get("cma_report")

        # Skip if no property data available
        if not property_address or not cma_report:
            logger.debug(f"Skipping pricing guidance for {contact_id} - no CMA data")
            return {}

        if not ACCEPTANCE_PREDICTOR_AVAILABLE:
            return {"pricing_guidance_variant": "control"}

        try:
            # A/B Test: ML pricing vs static CMA
            variant = await self.ab_testing.assign_variant(
                experiment_id="seller_ml_pricing_v1",
                contact_id=contact_id,
                metadata={
                    "has_cma": True,
                    "pcs_score": state.get("intent_profile", {}).get("pcs", {}).get("total_score", 0),
                },
            )

            if variant == "control":
                # Control: Static CMA-only guidance (existing behavior)
                logger.info(f"Pricing guidance for {contact_id}: control (static CMA)")
                return {"pricing_guidance_variant": "control"}

            # Treatment: ML-powered acceptance predictions
            logger.info(f"Pricing guidance for {contact_id}: treatment (ML predictions)")

            predictor = get_acceptance_predictor_service()

            # Build prediction context
            context = {
                "pcs_score": state.get("intent_profile", {}).get("pcs", {}).get("total_score", 50),
                "estimated_value": cma_report.get("estimated_value", 0),
                "cma_report": cma_report,
                "market_trend": state.get("market_trend", "balanced"),
                "property_address": property_address,
            }

            # Get optimal pricing strategy
            optimal_pricing = await predictor.get_optimal_price_range(
                seller_id=contact_id,
                target_probability=0.85,  # Target 85% acceptance probability
                context=context,
            )

            # Get predictions for seller's asking price if available
            asking_price = state.get("asking_price") or cma_report.get("estimated_value", 0)
            asking_prediction = None

            if asking_price and asking_price > 0:
                asking_prediction = await predictor.predict_acceptance_probability(
                    seller_id=contact_id,
                    offer_price=asking_price,
                    context=context,
                )

            # Format conversational guidance
            guidance = self._format_pricing_guidance(
                optimal_pricing=optimal_pricing,
                asking_prediction=asking_prediction,
                asking_price=asking_price,
                cma_value=cma_report.get("estimated_value", 0),
            )

            # Track ML usage
            await self.ab_testing.track_event(
                experiment_id="seller_ml_pricing_v1",
                contact_id=contact_id,
                event_type="ml_pricing_shown",
                properties={
                    "recommended_price": optimal_pricing.recommended_price,
                    "acceptance_probability": optimal_pricing.acceptance_probability,
                    "days_to_acceptance": optimal_pricing.time_to_acceptance_days,
                },
            )

            logger.info(
                f"ML pricing guidance for {contact_id}: "
                f"${optimal_pricing.recommended_price:,.0f} "
                f"({optimal_pricing.acceptance_probability:.0%} acceptance)"
            )

            return {
                "pricing_guidance": guidance,
                "pricing_guidance_variant": "treatment",
                "optimal_pricing": {
                    "min_price": optimal_pricing.min_price,
                    "max_price": optimal_pricing.max_price,
                    "recommended_price": optimal_pricing.recommended_price,
                    "acceptance_probability": optimal_pricing.acceptance_probability,
                    "time_to_acceptance_days": optimal_pricing.time_to_acceptance_days,
                },
            }

        except Exception as e:
            logger.error(f"Pricing guidance failed for {contact_id}: {e}", exc_info=True)
            # Graceful fallback to control behavior
            return {"pricing_guidance_variant": "control"}

    def _format_pricing_guidance(
        self,
        optimal_pricing,
        asking_prediction,
        asking_price: float,
        cma_value: float,
    ) -> str:
        """Format pricing guidance in conversational style for Jorge."""
        lines = ["📊 Based on current market analysis and seller engagement patterns:"]

        # If seller has an asking price, show prediction
        if asking_prediction and asking_price:
            lines.append("")
            lines.append(f"Your asking price of ${asking_price:,.0f}:")
            lines.append(f"   • Acceptance probability: {asking_prediction.acceptance_probability:.0%}")
            lines.append(f"   • Typical time to acceptance: {asking_prediction.estimated_days_to_acceptance} days")

        # Show optimal pricing strategy
        lines.append("")
        lines.append("💡 Optimal pricing strategy:")

        # Show recommended price with acceptance probability
        lines.append(
            f"   • ${optimal_pricing.recommended_price:,.0f} → "
            f"{optimal_pricing.acceptance_probability:.0%} acceptance probability "
            f"({optimal_pricing.time_to_acceptance_days} days)"
        )

        # Show price range
        if optimal_pricing.min_price and optimal_pricing.max_price:
            lines.append(
                f"   • Competitive range: ${optimal_pricing.min_price:,.0f} - ${optimal_pricing.max_price:,.0f}"
            )

        # Add rationale
        if optimal_pricing.strategy_rationale:
            lines.append("")
            lines.append(f"📈 {optimal_pricing.strategy_rationale}")

        lines.append("")
        lines.append("Would you like to explore pricing strategies to maximize both speed and value?")

        return "\n".join(lines)
