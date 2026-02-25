"""
Workflow service module for buyer bot.
Handles scheduling, follow-ups, and buyer persona classification.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig, JorgeSellerConfig
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.services.buyer_persona_service import BuyerPersonaService
from ghl_real_estate_ai.services.event_publisher import EventPublisher
from ghl_real_estate_ai.services.ghl_client import GHLClient

logger = get_logger(__name__)


class BuyerWorkflowService:
    """Handles workflow scheduling, follow-ups, and persona classification."""

    def __init__(
        self,
        event_publisher: Optional[EventPublisher] = None,
        buyer_persona_service: Optional[BuyerPersonaService] = None,
        ghl_client: Optional[GHLClient] = None,
        budget_config: Optional[BuyerBudgetConfig] = None,
    ):
        self.event_publisher = event_publisher
        self.buyer_persona_service = buyer_persona_service or BuyerPersonaService()
        self.ghl_client = ghl_client or GHLClient()
        self.budget_config = budget_config or BuyerBudgetConfig.from_environment()

    async def schedule_next_action(self, state: BuyerBotState) -> Dict:
        """
        Schedule next action based on buyer qualification level and engagement.
        Uses spec day-based schedule (days 2, 5, 8, 11, ..., 29, then every 14 days).
        """
        try:
            qualification_score = state.get("financial_readiness_score", 25)
            days_since_start = state.get("days_since_start", 0)

            # Use budget_config for action TYPE (what to do)
            next_action, follow_up_hours = self.budget_config.get_next_action(qualification_score)

            # Keep legacy day-based cadence for long-running low-intent nurture only.
            # Qualified leads should honor score-based follow-up urgency from budget config.
            if qualification_score < self.budget_config.QUALIFICATION_WARM_THRESHOLD:
                next_day = self._get_next_buyer_followup_day(days_since_start)
                if next_day is not None:
                    follow_up_hours = (next_day - days_since_start) * 24
                else:
                    follow_up_hours = JorgeSellerConfig.BUYER_LONGTERM_INTERVAL * 24

            await self._schedule_follow_up(state.get("buyer_id", "unknown"), next_action, follow_up_hours)

            result: Dict = {
                "next_action": next_action,
                "follow_up_scheduled": True,
                "follow_up_hours": follow_up_hours,
                "last_action_timestamp": datetime.now(timezone.utc),
            }

            # Hot-path: buyer routed directly to schedule_next_action (bypassing
            # generate_buyer_response).  Inject a proper appointment-booking message
            # so the delivery safety guard never needs to fire for hot leads.
            if next_action == "schedule_property_tour" and not str(
                state.get("response_content", "")
            ).strip():
                buyer_name = state.get("buyer_name", "")
                name_part = f"{buyer_name.split()[0]}, " if buyer_name and buyer_name.strip() else ""
                result["response_content"] = (
                    f"You're pre-approved and ready to move — let's get you into some homes! "
                    f"{name_part}What works better for tours, mornings or afternoons?"
                )
                result["current_qualification_step"] = "appointment"
                result["buyer_temperature"] = "hot"
                logger.info(
                    f"Hot-path appointment response injected for buyer "
                    f"{state.get('buyer_id', 'unknown')}"
                )

            return result

        except Exception as e:
            logger.error(f"Error scheduling next action for {state.get('buyer_id')}: {str(e)}")
            return {"next_action": "manual_review", "follow_up_scheduled": False}

    def _get_next_buyer_followup_day(self, days_since_start: int) -> Optional[int]:
        """Get the next scheduled follow-up day using spec day-based schedule."""
        schedule = JorgeSellerConfig.BUYER_FOLLOWUP_SCHEDULE
        max_active_day = max(schedule) if schedule else 29
        if days_since_start <= max_active_day:
            for day in schedule:
                if day > days_since_start:
                    return day
            return None
        else:
            return days_since_start + JorgeSellerConfig.BUYER_LONGTERM_INTERVAL

    async def _schedule_follow_up(self, buyer_id: str, action: str, hours: int):
        """Schedule follow-up action for buyer."""
        try:
            # Emit scheduling event
            if self.event_publisher:
                await self.event_publisher.publish_buyer_follow_up_scheduled(
                    contact_id=buyer_id, action_type=action, scheduled_hours=hours
                )

            logger.info(f"Scheduled {action} for buyer {buyer_id} in {hours} hours")

        except Exception as e:
            logger.error(f"Error scheduling follow-up for {buyer_id}: {str(e)}")

    async def classify_buyer_persona(self, state: BuyerBotState) -> Dict:
        """Classify buyer persona based on conversation analysis (Phase 1.4)."""
        try:
            conversation_history = state.get("conversation_history", [])
            buyer_id = state.get("buyer_id", "unknown")
            lead_data = state.get("lead_data", {})

            # Classify buyer persona
            persona_classification = await self.buyer_persona_service.classify_buyer_type(
                conversation_history=conversation_history,
                lead_data=lead_data,
            )

            # Get persona insights for response tailoring
            persona_insights = await self.buyer_persona_service.get_persona_insights(
                persona_classification.persona_type
            )

            # Sync persona to GHL as tags if confidence is high enough
            if persona_classification.confidence >= 0.6:
                await self._sync_buyer_persona_to_ghl(buyer_id, persona_classification)

            logger.info(
                f"Buyer persona classified for {buyer_id}: "
                f"{persona_classification.persona_type.value} "
                f"(confidence: {persona_classification.confidence:.2f})"
            )

            return {
                "buyer_persona": persona_classification.persona_type.value,
                "buyer_persona_confidence": persona_classification.confidence,
                "buyer_persona_signals": persona_classification.detected_signals,
                "buyer_persona_insights": persona_insights.model_dump(),
            }
        except Exception as e:
            logger.error(f"Error classifying buyer persona for {state.get('buyer_id')}: {str(e)}")
            return {
                "buyer_persona": "unknown",
                "buyer_persona_confidence": 0.0,
                "buyer_persona_signals": [],
                "buyer_persona_insights": {},
            }

    async def _sync_buyer_persona_to_ghl(self, buyer_id: str, persona_classification) -> None:
        """Sync buyer persona to GHL as tags (Phase 1.4)."""
        try:
            persona_tag = f"Buyer-{persona_classification.persona_type.value}"
            confidence_tag = f"Persona-Conf-{int(persona_classification.confidence * 100)}%"

            # Add tags to contact in GHL
            await self.ghl_client.add_tags(contact_id=buyer_id, tags=[persona_tag, confidence_tag])

            logger.info(f"Synced buyer persona tags to GHL for {buyer_id}: {persona_tag}")
        except Exception as e:
            logger.warning(f"Failed to sync buyer persona to GHL for {buyer_id}: {str(e)}")
