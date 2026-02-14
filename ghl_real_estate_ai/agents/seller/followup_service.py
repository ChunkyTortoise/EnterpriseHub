"""
Follow-up service for Jorge Seller Bot.

Handles automated follow-up execution for unresponsive or lukewarm sellers.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher

logger = get_logger(__name__)


class FollowUpService:
    """Service for executing automated follow-ups."""

    # Follow-up scripts based on previous stage
    FOLLOW_UP_SCRIPTS = {
        "qualification": "Checking back—did you ever decide on a timeline for {address}?",
        "valuation_defense": "I've updated the comps for your neighborhood. Zillow is still high. Ready for the truth?",
        "listing_prep": "The photographer is in your area Thursday. Should I book him for your place?",
    }

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher or get_event_publisher()

    async def execute_follow_up(self, state: JorgeSellerState) -> Dict[str, Any]:
        """Execute automated follow-up for unresponsive or lukewarm sellers."""
        follow_up_count = state.get("follow_up_count", 0) + 1

        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="execute_follow_up"
        )

        logger.info(f"Executing follow-up for {state['lead_name']} (Attempt {follow_up_count})")

        stage = state.get("current_journey_stage", "qualification")
        template = self.FOLLOW_UP_SCRIPTS.get(
            stage,
            "Still interested in selling {address} or should I close the file?"
        )
        follow_up_message = template.format(address=state.get("property_address", "your property"))

        # Emit conversation event for follow-up
        await self.event_publisher.publish_conversation_update(
            conversation_id=f"jorge_{state['lead_id']}",
            lead_id=state["lead_id"],
            stage="follow_up_sent",
            message=f"Follow-up #{follow_up_count}: {follow_up_message[:50]}...",
        )

        # Mark bot as completed for this cycle
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="completed",
            current_step="follow_up_sent"
        )

        # In prod, send via GHL
        return {"response_content": follow_up_message, "follow_up_count": follow_up_count}
