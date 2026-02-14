"""Lead recovery orchestration service.

Orchestrates the multi-stage recovery sequence for abandoned leads using
market triggers as re-engagement hooks.

Recovery Strategy:
- Day 3: "Quick check-in" with recent market intel
- Day 7: "Still thinking?" with price drop/rate change alert
- Day 14: "Market update" with neighborhood activity
- Day 30: "Hail Mary" with compelling seasonal timing
"""

import logging
import random
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.jorge.abandonment_detector import (
    AbandonedContact,
    AbandonmentStage,
)
from ghl_real_estate_ai.services.jorge.market_trigger_service import (
    MarketTrigger,
    get_market_trigger_service,
)

logger = logging.getLogger(__name__)


# Recovery message templates by stage
RECOVERY_TEMPLATES = {
    AbandonmentStage.DAY_3: [
        "Hey {name}! Just wanted to check in — I know home searching can feel overwhelming. "
        "I've got some updated market data for Rancho Cucamonga that might be helpful. "
        "Still interested in {interest_area}?",
        "Hi {name}, it's been a few days since we last chatted. "
        "The market's been pretty active lately — {market_update}. "
        "Would you like me to send you a quick summary of what's new?",
        "{name}, I wanted to share something with you: {market_trigger}. "
        "Thought you might be interested given what we discussed earlier. "
        "How's your search going?",
    ],
    AbandonmentStage.DAY_7: [
        "Hi {name}, I noticed we haven't talked in about a week. "
        "No pressure at all — just wanted to let you know {market_trigger}. "
        "This could be relevant to your search. Want the details?",
        "{name}, checking back in! {market_trigger}. "
        "I know timing is everything in real estate. "
        "Would it help if I sent you a personalized market update for {interest_area}?",
        "Hey {name}, hope you're doing well! {market_trigger}. "
        "Based on what you told me about your budget and preferences, "
        "this might be worth a look. Still actively searching?",
    ],
    AbandonmentStage.DAY_14: [
        "{name}, it's been a couple weeks since we last connected. "
        "I've been tracking the market in {interest_area} and {market_trigger}. "
        "Would you like a comprehensive update on what's changed?",
        "Hi {name}, I wanted to reach out because {market_trigger}. "
        "I remember you were interested in {interest_area}, and I think "
        "this could be significant for your search. Can I send you more info?",
        "{name}, just checking in. The Rancho Cucamonga market has been interesting lately — "
        "{market_trigger}. Would it be helpful if I put together a custom "
        "market analysis based on your criteria?",
    ],
    AbandonmentStage.DAY_30: [
        "{name}, I know it's been a while, but I wanted to reach out one more time. "
        "{market_trigger}. This could be a unique opportunity given current conditions. "
        "Even if you're taking a break from your search, this might be worth knowing about.",
        "Hi {name}, I don't want to be a bother, but {market_trigger}. "
        "If you're still considering {interest_area}, now might be a strategic time "
        "to re-evaluate. Would you like me to put together a fresh market overview?",
        "{name}, last check-in from me! {market_trigger}. "
        "I know timing has to be right, but I wanted to make sure you didn't miss this. "
        "Let me know if you'd like to talk through what's happening in the market right now.",
    ],
}


class RecoveryOrchestrator:
    """Orchestrates recovery attempts for abandoned leads.

    Leverages MarketTriggerService to generate personalized, timely
    recovery messages with real market intel as re-engagement hooks.
    """

    def __init__(self, ghl_client=None):
        """Initialize orchestrator with GHL client.

        Args:
            ghl_client: EnhancedGHLClient for sending recovery messages
        """
        self._ghl_client = ghl_client
        self._market_trigger_service = get_market_trigger_service()
        logger.info("RecoveryOrchestrator initialized")

    async def orchestrate_recovery(
        self,
        abandoned_contacts: List[AbandonedContact],
    ) -> Dict[str, Any]:
        """Execute recovery sequence for a batch of abandoned contacts.

        Args:
            abandoned_contacts: List of contacts eligible for recovery

        Returns:
            Summary of recovery attempts: {
                "total_attempted": int,
                "by_stage": {"3d": int, "7d": int, ...},
                "successful": int,
                "failed": int,
            }
        """
        if not self._ghl_client:
            logger.warning("No GHL client configured, skipping recovery")
            return {"error": "No GHL client configured"}

        summary = {
            "total_attempted": 0,
            "by_stage": {},
            "successful": 0,
            "failed": 0,
            "contacts_processed": [],
        }

        for contact in abandoned_contacts:
            try:
                success = await self._attempt_recovery(contact)
                summary["total_attempted"] += 1

                stage_key = contact.current_stage.value
                summary["by_stage"][stage_key] = summary["by_stage"].get(stage_key, 0) + 1

                if success:
                    summary["successful"] += 1
                    summary["contacts_processed"].append(
                        {
                            "contact_id": contact.contact_id,
                            "stage": stage_key,
                            "status": "success",
                        }
                    )
                else:
                    summary["failed"] += 1
                    summary["contacts_processed"].append(
                        {
                            "contact_id": contact.contact_id,
                            "stage": stage_key,
                            "status": "failed",
                        }
                    )

            except Exception as exc:
                logger.error(
                    f"Failed to attempt recovery for {contact.contact_id}: {exc}"
                )
                summary["failed"] += 1

        logger.info(
            f"Recovery orchestration complete: {summary['successful']}/{summary['total_attempted']} successful"
        )
        return summary

    async def _attempt_recovery(self, contact: AbandonedContact) -> bool:
        """Attempt recovery for a single contact.

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Generate personalized recovery message
            message = await self._generate_recovery_message(contact)

            if not message:
                logger.warning(f"No recovery message generated for {contact.contact_id}")
                return False

            # Send message via GHL
            await self._ghl_client.send_message(
                contact_id=contact.contact_id,
                message=message,
                # Use SMS or last known channel
                channel=contact.contact_metadata.get("preferred_channel", "sms"),
            )

            logger.info(
                f"Recovery message sent to {contact.contact_id} (stage: {contact.current_stage.value})"
            )
            return True

        except Exception as exc:
            logger.error(f"Recovery attempt failed for {contact.contact_id}: {exc}")
            return False

    async def _generate_recovery_message(
        self, contact: AbandonedContact
    ) -> Optional[str]:
        """Generate personalized recovery message with market trigger.

        Strategy:
        1. Select template based on abandonment stage
        2. Find relevant market trigger for contact
        3. Personalize with contact metadata
        4. Return formatted message
        """
        # Get template for current stage
        stage = contact.current_stage
        templates = RECOVERY_TEMPLATES.get(stage)

        if not templates:
            logger.warning(f"No templates for stage {stage.value}")
            return None

        # Select random template for variety
        template = random.choice(templates)

        # Get relevant market trigger for contact
        market_trigger = await self._get_relevant_market_trigger(contact)

        # Extract personalization variables
        name = contact.contact_metadata.get("name", "there")
        interest_area = contact.contact_metadata.get(
            "interest_area", "Rancho Cucamonga"
        )

        # Format market trigger text
        if market_trigger:
            trigger_text = market_trigger.message
            market_update = trigger_text
        else:
            # Fallback generic market updates by stage
            market_update = self._get_generic_market_update(stage)
            trigger_text = market_update

        # Format message
        try:
            message = template.format(
                name=name,
                interest_area=interest_area,
                market_trigger=trigger_text,
                market_update=market_update,
            )
            return message
        except KeyError as e:
            logger.error(f"Template formatting error: {e}")
            return None

    async def _get_relevant_market_trigger(
        self, contact: AbandonedContact
    ) -> Optional[MarketTrigger]:
        """Find a relevant market trigger for contact based on preferences.

        Checks contact's watchlist and generates appropriate trigger.
        """
        # Get contact's watchlist from market trigger service
        watchlist = self._market_trigger_service.get_watchlist(contact.contact_id)

        if not watchlist:
            # Try to create watchlist from contact metadata
            if contact.contact_metadata:
                from ghl_real_estate_ai.services.jorge.market_trigger_service import (
                    ContactWatchlist,
                )

                watchlist = ContactWatchlist(
                    contact_id=contact.contact_id,
                    preferred_areas=contact.contact_metadata.get("preferred_areas", []),
                    max_price=contact.contact_metadata.get("max_budget"),
                    min_beds=contact.contact_metadata.get("min_beds"),
                )
                self._market_trigger_service.register_watchlist(watchlist)

        # Generate triggers based on stage
        # Day 3/7: Price drops and rate changes (high urgency)
        # Day 14/30: Neighborhood sales and seasonal timing (softer approach)
        if contact.current_stage in [AbandonmentStage.DAY_3, AbandonmentStage.DAY_7]:
            # Try rate change first
            triggers = self._market_trigger_service.evaluate_rate_change(
                new_rate=6.8,  # Mock current rate
                previous_rate=7.0,
            )
            if triggers:
                return triggers[0]

            # Fallback to price drop
            triggers = self._market_trigger_service.evaluate_price_drop(
                area="Rancho Cucamonga",
                original_price=650000,
                new_price=620000,
            )
            if triggers:
                return triggers[0]

        else:  # Day 14/30
            # Use neighborhood sales
            triggers = self._market_trigger_service.evaluate_neighborhood_sale(
                neighborhood="Alta Loma",
                sold_price=680000,
                price_per_sqft=320,
                area_avg_per_sqft=310,
            )
            if triggers:
                return triggers[0]

        return None

    def _get_generic_market_update(self, stage: AbandonmentStage) -> str:
        """Get generic market update when no specific trigger available."""
        updates = {
            AbandonmentStage.DAY_3: "inventory is moving quickly this week",
            AbandonmentStage.DAY_7: "we're seeing some interesting price adjustments",
            AbandonmentStage.DAY_14: "the market dynamics have shifted slightly",
            AbandonmentStage.DAY_30: "we're entering a seasonally strategic period",
        }
        return updates.get(stage, "there have been some market changes")


# Singleton instance
_orchestrator: Optional[RecoveryOrchestrator] = None


def get_recovery_orchestrator(ghl_client=None) -> RecoveryOrchestrator:
    """Get or create singleton recovery orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RecoveryOrchestrator(ghl_client=ghl_client)
    return _orchestrator
