"""
CMA (Comparative Market Analysis) and property valuation service.

Handles CMA generation, valuation defense, and pricing guidance for seller leads.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

logger = get_logger(__name__)


class CMAService:
    """Service for CMA generation and property valuation."""

    def __init__(
        self,
        cma_generator: Optional[CMAGenerator] = None,
        claude: Optional[ClaudeAssistant] = None
    ):
        self.cma_generator = cma_generator or CMAGenerator()
        self.claude = claude or ClaudeAssistant()

    async def generate_cma(self, state: JorgeSellerState) -> Dict[str, Any]:
        """Generate CMA report if property address is available."""
        property_address = state.get("property_address")
        if not property_address:
            return {}

        try:
            zestimate = state.get("zestimate", 0.0)
            report = await self.cma_generator.generate_report(
                property_address, zestimate or 0.0
            )

            comparable_properties = []
            for comp in report.comparables:
                comparable_properties.append({
                    "address": comp.address,
                    "sale_price": comp.sale_price,
                    "sqft": comp.sqft,
                    "beds": comp.beds,
                    "baths": comp.baths,
                    "price_per_sqft": comp.price_per_sqft,
                })

            market_data = {
                "market_name": report.market_context.market_name,
                "price_trend": report.market_context.price_trend,
                "dom_average": report.market_context.dom_average,
                "inventory_level": report.market_context.inventory_level,
                "narrative": report.market_narrative,
            }

            logger.info(
                f"CMA generated for {property_address}: "
                f"estimated value ${report.estimated_value:,.0f}"
            )

            return {
                "cma_report": {
                    "estimated_value": report.estimated_value,
                    "value_range_low": report.value_range_low,
                    "value_range_high": report.value_range_high,
                    "confidence_score": report.confidence_score,
                    "zillow_variance_percent": report.zillow_variance_percent,
                    "zillow_explanation": report.zillow_explanation,
                    "market_narrative": report.market_narrative,
                },
                "estimated_value": report.estimated_value,
                "comparable_properties": comparable_properties,
                "market_data": market_data,
            }

        except Exception as e:
            logger.warning(f"CMA generation failed for {property_address}: {e}")
            return {}

    async def defend_valuation(self, state: JorgeSellerState) -> Dict[str, Any]:
        """Build Zillow-defense response using CMA data when Zestimate stall detected."""
        cma_report = state.get("cma_report")
        if not cma_report:
            return {}

        try:
            estimated_value = cma_report.get("estimated_value", 0)
            variance = cma_report.get("zillow_variance_percent", 0)
            explanation = cma_report.get("zillow_explanation", "")
            comp_count = len(state.get("comparable_properties", []))
            market_narrative = cma_report.get("market_narrative", "")

            defense_context = (
                f"Our CMA analysis of {comp_count} recent comparable sales shows "
                f"an estimated value of ${estimated_value:,.0f}. "
                f"The Zillow Zestimate differs by {abs(variance):.1f}%. "
                f"{explanation} {market_narrative}"
            )

            prompt = f"""
            As Jorge, the seller mentioned Zillow/Zestimate. Use this CMA data to
            gently educate them about why real comparable sales are more accurate:

            {defense_context}

            Be helpful and educational, not dismissive. Keep under 160 chars for SMS.
            """

            response = await self.claude.analyze_with_context(prompt)
            content = (
                response.get("content")
                or response.get("analysis")
                or f"Real comps show ${estimated_value:,.0f} — Zillow can't walk through your house!"
            )

            return {"response_content": content}

        except Exception as e:
            logger.warning(f"Valuation defense failed: {e}")
            return {}
