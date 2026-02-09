"""
Market Context Service - Market-aware intelligence for messaging and context.

Extracted from ClaudeAssistant god class.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.markets.registry import MarketRegistry, get_market_service

logger = get_logger(__name__)


class MarketContextService:
    """Provides market-aware context for intelligent messaging."""

    def __init__(self, market_id: Optional[str] = None):
        self.market_id = market_id
        self.market_registry = MarketRegistry()
        self._market_context_cache: Dict[str, Dict[str, Any]] = {}

    async def get_market_context(self, market_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive market context for intelligent messaging."""
        target_market_id = market_id or self.market_id or "austin"

        if target_market_id in self._market_context_cache:
            return self._market_context_cache[target_market_id]

        try:
            market_service = get_market_service(target_market_id)
            market_config = market_service.config

            context = {
                "market_id": target_market_id,
                "market_name": market_config.market_name,
                "market_type": market_config.market_type.value,
                "specializations": {
                    "primary": market_config.specializations.primary_specialization,
                    "secondary": market_config.specializations.secondary_specializations,
                    "unique_advantages": market_config.specializations.unique_advantages,
                    "target_clients": market_config.specializations.target_client_types,
                    "expertise_tags": market_config.specializations.expertise_tags,
                },
                "top_neighborhoods": [
                    {
                        "name": n.name,
                        "zone": n.zone,
                        "median_price": n.median_price,
                        "appeal_scores": n.appeal_scores,
                        "demographics": n.demographics,
                    }
                    for n in market_config.neighborhoods[:5]
                ],
                "major_employers": [
                    {
                        "name": e.name,
                        "industry": e.industry,
                        "employee_count": e.employee_count,
                        "avg_salary_range": e.average_salary_range,
                        "preferred_neighborhoods": e.preferred_neighborhoods,
                    }
                    for e in market_config.employers[:5]
                ],
                "market_indicators": {
                    "median_home_price": market_config.median_home_price,
                    "price_appreciation_1y": market_config.price_appreciation_1y,
                    "inventory_days": market_config.inventory_days,
                },
            }

            self._market_context_cache[target_market_id] = context
            return context

        except Exception as e:
            return {
                "market_id": target_market_id,
                "market_name": f"{target_market_id.title()} Metropolitan Area",
                "error": f"Could not load full market context: {str(e)}",
            }

    def format_market_context_for_messaging(self, market_context: Dict[str, Any]) -> str:
        """Format market context for Claude messaging."""
        market_name = market_context.get("market_name", "the local market")
        market_type = market_context.get("market_type", "mixed")

        specializations = market_context.get("specializations", {})
        primary_spec = specializations.get("primary", "professional relocation")

        neighborhoods = market_context.get("top_neighborhoods", [])
        if neighborhoods:
            top_areas = ", ".join([n["name"] for n in neighborhoods[:3]])
            neighborhood_context = f"Popular areas include {top_areas}"
        else:
            neighborhood_context = "several desirable neighborhoods"

        employers = market_context.get("major_employers", [])
        if employers:
            major_employers = ", ".join([e["name"] for e in employers[:3]])
            employer_context = f"Major employers like {major_employers}"
        else:
            employer_context = "major local employers"

        return f"{market_name} is a {market_type} market specializing in {primary_spec}. {neighborhood_context} are seeing strong activity. {employer_context} are driving relocation demand."
