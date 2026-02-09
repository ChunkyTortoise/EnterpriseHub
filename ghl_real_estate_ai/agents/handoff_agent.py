"""
🤖 Handoff Agent - Service 6 Phase 2
===================================

Coordinates seamless transitions between Lead, Seller, and Buyer bots.
Features:
- Listens to EventStreamingService for LEAD_SCORED events
- Intelligent intent classification (Seller vs Buyer)
- Automatic handoff to specialized qualification workflows
- Maintains coordination context across the agent ecosystem

Author: Claude AI Enhancement System
Date: 2026-01-25
"""

from typing import Dict

from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import get_enhanced_bot_orchestrator
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_intent_detector import get_intent_detector
from ghl_real_estate_ai.services.event_streaming_service import (
    EventType,
    Priority,
    StreamEvent,
    get_event_streaming_service,
)
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)


class HandoffAgent:
    """
    Agent responsible for coordinating handoffs between different specialized bots.
    """

    def __init__(self):
        self.memory_service = MemoryService()
        self.intent_detector = get_intent_detector()
        self.orchestrator = get_enhanced_bot_orchestrator()
        self.streaming_service = None
        self.is_running = False

    async def initialize(self):
        """Initialize and register event handlers"""
        self.streaming_service = await get_event_streaming_service()
        self.streaming_service.register_handler(EventType.LEAD_SCORED, self.handle_lead_scored)
        logger.info("Handoff Agent initialized and registered for LEAD_SCORED events")

    async def handle_lead_scored(self, event: StreamEvent):
        """
        Handle a lead scoring event by evaluating handoff requirements.
        """
        data = event.data
        lead_id = data.get("lead_id") or data.get("contact_id")
        location_id = data.get("location_id") or "default"

        if not lead_id:
            logger.warning(f"Received LEAD_SCORED event without lead_id: {event.id}")
            return

        logger.info(f"Handoff Agent evaluating lead {lead_id} (Score: {data.get('score')})")

        try:
            # 1. Retrieve full context
            context = await self.memory_service.get_context(lead_id, location_id)
            history = context.get("conversation_history", [])

            if not history:
                logger.info(f"No history for lead {lead_id}, skipping handoff evaluation")
                return

            # 2. Determine lead type (Buyer vs Seller)
            lead_type = context.get("customer_type")
            if not lead_type:
                lead_type = await self._classify_lead_type(history, context)
                # Save detected type
                context["customer_type"] = lead_type
                await self.memory_service.save_context(lead_id, context, location_id)

            # 3. Evaluate if handoff is needed
            # We hand off to Jorge bots if the score is high enough (e.g., > 60)
            score = data.get("score", 0)
            if score < 60:
                logger.info(f"Lead {lead_id} score {score} too low for specialized handoff")
                return

            # 4. Trigger Handoff
            if lead_type == "seller":
                await self._handoff_to_seller_bot(lead_id, location_id, context)
            elif lead_type == "buyer":
                await self._handoff_to_buyer_bot(lead_id, location_id, context)
            else:
                logger.info(f"Unknown lead type for {lead_id}, remaining in lead sequence")

        except Exception as e:
            logger.error(f"Error in Handoff Agent for lead {lead_id}: {e}")

    async def _classify_lead_type(self, history: list, context: Dict) -> str:
        """Use intent detector to distinguish between Buyer and Seller"""
        # Simple heuristic first
        text = " ".join([m.get("content", "").lower() for m in history])

        seller_keywords = ["sell", "worth", "listing", "value of my home", "market analysis", "commission"]
        buyer_keywords = ["buy", "looking for", "bedrooms", "neighborhood", "house for sale", "showing"]

        seller_score = sum(1 for k in seller_keywords if k in text)
        buyer_score = sum(1 for k in buyer_keywords if k in text)

        if seller_score > buyer_score:
            return "seller"
        elif buyer_score > seller_score:
            return "buyer"

        # Fallback to Claude for deeper analysis
        try:
            analysis = await self.intent_detector.analyze_property_intent(history, context)
            # Check if analysis suggests selling
            summary = analysis.get("intent_summary", "").lower()
            if "sell" in summary or "seller" in summary:
                return "seller"
            return "buyer"  # Default to buyer
        except:
            return "buyer"

    async def _handoff_to_seller_bot(self, lead_id: str, location_id: str, context: Dict):
        """Trigger Jorge Seller Bot workflow"""
        logger.info(f"🚀 HANDOFF: Lead {lead_id} -> Jorge Seller Bot")

        # Publish handoff event
        await self.streaming_service.publish_event(
            event_type=EventType.ACTION_TRIGGERED,
            data={
                "action": "bot_handoff",
                "from": "lead_bot",
                "to": "jorge_seller_bot",
                "lead_id": lead_id,
                "location_id": location_id,
                "reason": "High-intent seller detected",
            },
            priority=Priority.HIGH,
        )

        # In a real system, the next message received will now be routed to JorgeSellerBot
        # For immediate action, we can trigger an initial "confrontational" qualification message
        try:
            # Update context to reflect specialized bot is now active
            context["active_bot"] = "jorge_seller"
            await self.memory_service.save_context(lead_id, context, location_id)

            # Optionally trigger the first interaction
            # await self.orchestrator.orchestrate_conversation(...)
        except Exception as e:
            logger.error(f"Failed to complete handoff to seller bot: {e}")

    async def _handoff_to_buyer_bot(self, lead_id: str, location_id: str, context: Dict):
        """Trigger Jorge Buyer Bot workflow"""
        logger.info(f"🚀 HANDOFF: Lead {lead_id} -> Jorge Buyer Bot")

        # Publish handoff event
        await self.streaming_service.publish_event(
            event_type=EventType.ACTION_TRIGGERED,
            data={
                "action": "bot_handoff",
                "from": "lead_bot",
                "to": "jorge_buyer_bot",
                "lead_id": lead_id,
                "location_id": location_id,
                "reason": "High-intent buyer detected",
            },
            priority=Priority.HIGH,
        )

        try:
            context["active_bot"] = "jorge_buyer"
            await self.memory_service.save_context(lead_id, context, location_id)
        except Exception as e:
            logger.error(f"Failed to complete handoff to buyer bot: {e}")


# Singleton instance
_handoff_agent = None


async def get_handoff_agent() -> HandoffAgent:
    """Get or create the handoff agent singleton"""
    global _handoff_agent
    if _handoff_agent is None:
        _handoff_agent = HandoffAgent()
        await _handoff_agent.initialize()
    return _handoff_agent
