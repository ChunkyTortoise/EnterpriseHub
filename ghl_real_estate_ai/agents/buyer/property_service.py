"""
Property matching and needs qualification module for buyer bot.
"""

import inspect
from typing import Dict, Optional

from ghl_real_estate_ai.agents.buyer.utils import extract_property_preferences
from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.services.event_publisher import EventPublisher
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

logger = get_logger(__name__)


class PropertyService:
    """Handles property matching and buyer needs qualification."""

    def __init__(
        self,
        property_matcher: Optional[PropertyMatcher] = None,
        event_publisher: Optional[EventPublisher] = None,
        budget_config: Optional[BuyerBudgetConfig] = None,
    ):
        self.property_matcher = property_matcher or PropertyMatcher()
        self.event_publisher = event_publisher
        self.budget_config = budget_config or BuyerBudgetConfig.from_environment()

    async def qualify_property_needs(self, state: BuyerBotState) -> Dict:
        """Qualify property needs and preferences using budget_config urgency thresholds."""
        try:
            profile = state.get("intent_profile")
            if not profile:
                return {"property_preferences": None, "urgency_level": "browsing"}

            # Extract property preferences from conversation
            preferences = await extract_property_preferences(state.get("conversation_history", []))

            # Determine urgency level using budget_config
            urgency_score = float(state.get("urgency_score", 0))
            urgency_level = self.budget_config.get_urgency_level(urgency_score)

            return {
                "property_preferences": preferences,
                "urgency_level": urgency_level,
                "preference_clarity_score": state.get("preference_clarity", 0.5),
            }

        except Exception as e:
            logger.error(f"Error qualifying property needs for {state.get('buyer_id')}: {str(e)}")
            return {"property_preferences": None, "urgency_level": "browsing"}

    async def match_properties(self, state: BuyerBotState) -> Dict:
        """
        Match properties to buyer preferences using existing PropertyMatcher.
        Uses find_buyer_matches when budget is available for better filtering.
        """
        try:
            if not state.get("budget_range"):
                return {"matched_properties": [], "properties_viewed_count": 0, "next_action": "qualify_more"}

            budget_range = state["budget_range"]
            preferences = state.get("property_preferences") or {}

            # Use find_buyer_matches for budget-aware matching
            budget_max = budget_range.get("max", 0)
            beds = preferences.get("bedrooms")
            neighborhood = preferences.get("neighborhood")

            if budget_max > 0 and hasattr(self.property_matcher, "find_buyer_matches"):
                if inspect.iscoroutinefunction(self.property_matcher.find_buyer_matches):
                    matches = await self.property_matcher.find_buyer_matches(
                        budget=budget_max, beds=beds, neighborhood=neighborhood, limit=5
                    )
                else:
                    matches = self.property_matcher.find_buyer_matches(
                        budget=budget_max, beds=beds, neighborhood=neighborhood, limit=5
                    )
            elif inspect.iscoroutinefunction(self.property_matcher.find_matches):
                matches = await self.property_matcher.find_matches(preferences=preferences, limit=5)
            else:
                matches = self.property_matcher.find_matches(preferences=preferences, limit=5)

            # Emit property match event
            if self.event_publisher:
                await self.event_publisher.publish_property_match_update(
                    contact_id=state.get("buyer_id", "unknown"),
                    properties_matched=len(matches),
                    match_criteria=state.get("property_preferences"),
                )

            return {
                "matched_properties": matches[:5],  # Top 5 matches
                "property_matches": matches[:5],  # Add for consistency with script expectation
                "properties_viewed_count": len(matches),
                "next_action": "respond" if matches else "educate_market",
            }

        except Exception as e:
            logger.error(f"Error matching properties for {state.get('buyer_id')}: {str(e)}")
            return {"matched_properties": [], "properties_viewed_count": 0, "next_action": "qualify_more"}
