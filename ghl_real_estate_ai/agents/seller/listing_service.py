"""
Listing preparation service for Jorge Seller Bot.

Generates staging recommendations and repair estimates based on property condition.
"""

from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState

logger = get_logger(__name__)


class ListingService:
    """Service for listing preparation recommendations."""

    def __init__(self):
        pass

    async def prepare_listing(self, state: JorgeSellerState) -> Dict[str, Any]:
        """Generate listing preparation recommendations."""
        if not state.get("is_qualified") or not state.get("property_address"):
            return {}

        property_condition = state.get("property_condition")
        staging_recs = self._generate_staging_recommendations(property_condition)
        repair_estimates = self._estimate_repairs(property_condition)

        return {
            "staging_recommendations": staging_recs,
            "repair_estimates": repair_estimates,
            "current_journey_stage": "listing_prep",
        }

    def _generate_staging_recommendations(
        self, condition: Optional[str]
    ) -> List[str]:
        """Generate staging recommendations based on property condition."""
        base_recs = [
            "Declutter all rooms and remove personal photos",
            "Deep clean entire property including windows",
            "Maximize natural lighting — open all blinds and curtains",
            "Add fresh flowers or plants to key rooms",
        ]

        if condition == "move_in_ready":
            base_recs.extend([
                "Professional photography to showcase turnkey condition",
                "Highlight recent upgrades in listing description",
            ])
        elif condition == "needs_work":
            base_recs.extend([
                "Fresh neutral paint in main living areas",
                "Replace dated light fixtures and hardware",
                "Consider professional staging for primary living spaces",
            ])
        elif condition == "major_repairs":
            base_recs.extend([
                "Get pre-listing inspection to identify all issues",
                "Obtain contractor estimates for major repairs",
                "Consider selling as-is with repair credit",
                "Price accordingly to reflect condition",
            ])

        return base_recs

    def _estimate_repairs(
        self, condition: Optional[str]
    ) -> Dict[str, float]:
        """Estimate repair costs based on condition (Rancho Cucamonga rates)."""
        if condition == "move_in_ready":
            return {
                "deep_cleaning": 500.0,
                "touch_up_paint": 300.0,
                "landscaping_refresh": 400.0,
                "total": 1200.0,
            }
        elif condition == "needs_work":
            return {
                "interior_paint": 3500.0,
                "flooring_update": 5000.0,
                "fixture_replacement": 1500.0,
                "deep_cleaning": 500.0,
                "landscaping": 800.0,
                "total": 11300.0,
            }
        elif condition == "major_repairs":
            return {
                "roof_repair": 8000.0,
                "hvac_update": 6000.0,
                "plumbing_repair": 4000.0,
                "electrical_update": 3500.0,
                "foundation_assessment": 2000.0,
                "total": 23500.0,
            }
        return {"minimal_prep": 800.0, "total": 800.0}
