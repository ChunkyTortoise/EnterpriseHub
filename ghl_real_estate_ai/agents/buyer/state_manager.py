"""
State management and routing module for buyer bot.
Handles initial state building and workflow routing logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from ghl_real_estate_ai.agents.buyer.constants import MAX_CONVERSATION_HISTORY
from ghl_real_estate_ai.agents.buyer.handoff_manager import HandoffManager
from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import BotMetadata, ConversationMessage
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState

logger = get_logger(__name__)


class StateManager:
    """Manages buyer bot state building and routing logic."""

    def __init__(
        self, budget_config: Optional[BuyerBudgetConfig] = None, handoff_manager: Optional[HandoffManager] = None
    ):
        self.budget_config = budget_config or BuyerBudgetConfig.from_environment()
        self.handoff_manager = handoff_manager or HandoffManager()

    def build_initial_state(
        self,
        conversation_id: str,
        user_message: str,
        conversation_history: Optional[List[ConversationMessage]],
        buyer_name: Optional[str] = None,
        buyer_phone: Optional[str] = None,
        buyer_email: Optional[str] = None,
        metadata: Optional[BotMetadata] = None,
        tone_variant: str = "empathetic",
        handoff_context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Build the initial state for the buyer workflow."""
        if conversation_history is None:
            conversation_history = []

        # Only append current message if not already the last entry (webhook may have pre-appended)
        if not conversation_history or conversation_history[-1].get("content") != user_message:
            conversation_history.append(
                {"role": "user", "content": user_message, "timestamp": datetime.now(timezone.utc).isoformat()}
            )

        # Prune to prevent unbounded memory growth
        if len(conversation_history) > MAX_CONVERSATION_HISTORY:
            conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]

        initial_state = {
            "buyer_id": conversation_id,
            "buyer_name": buyer_name or f"Buyer {conversation_id}",
            "target_areas": None,
            "conversation_history": conversation_history,
            "intent_profile": None,
            "budget_range": None,
            "financing_status": "unknown",
            "urgency_level": "browsing",
            "property_preferences": None,
            "current_qualification_step": "budget",
            "objection_detected": False,
            "detected_objection_type": None,
            "next_action": "qualify",
            "response_content": "",
            "matched_properties": [],
            "financial_readiness_score": 0.0,
            "buying_motivation_score": 0.0,
            "is_qualified": False,
            "current_journey_stage": "discovery",
            "properties_viewed_count": 0,
            "last_action_timestamp": None,
            "user_message": user_message,
            "tone_variant": tone_variant,
            "intelligence_context": None,
            "intelligence_performance_ms": 0.0,
            "skip_qualification": False,
            "handoff_context_used": False,
        }

        # Apply handoff context if valid
        if handoff_context and self.handoff_manager.has_valid_handoff_context(handoff_context):
            initial_state = self.handoff_manager.populate_state_from_context(handoff_context, initial_state)
            logger.info(f"Buyer bot using handoff context for {conversation_id} - skipping re-qualification")

        if buyer_phone:
            initial_state["buyer_phone"] = buyer_phone
        if buyer_email:
            initial_state["buyer_email"] = buyer_email
        if metadata:
            initial_state["metadata"] = metadata

        return initial_state

    def route_buyer_action(self, state: BuyerBotState) -> Literal["respond", "schedule", "end"]:
        """Route to next action based on buyer qualification using budget_config."""
        try:
            next_action = state.get("next_action", "respond")
            qualification_score = state.get("financial_readiness_score", 0)

            # Use budget_config for routing thresholds
            return self.budget_config.get_routing_action(qualification_score, next_action)
        except Exception as e:
            logger.error(f"Error routing buyer action: {str(e)}")
            return "respond"

    def route_after_matching(self, state: BuyerBotState) -> Literal["handle_objections", "respond", "schedule", "end"]:
        """Route after property matching — check for objections first."""
        if state.get("objection_detected"):
            return "handle_objections"
        return self.route_buyer_action(state)

    def determine_qualification_status(self, state: BuyerBotState) -> Dict[str, Any]:
        """Determine the final qualification status from workflow state."""
        is_qualified = state.get("financial_readiness_score", 0) >= 50 and state.get("buying_motivation_score", 0) >= 50

        return {
            "is_qualified": is_qualified,
            "current_step": state.get("current_qualification_step", "unknown"),
            "engagement_status": "qualified" if is_qualified else "nurturing",
            "financial_readiness": state.get("financial_readiness_score", 0.0),
        }

    def truncate_response_if_needed(self, response_text: str, max_length: int = 160) -> Dict[str, str]:
        """Truncate response if it exceeds SMS length limit."""
        if response_text and len(response_text) > max_length:
            return {
                "response_content_full": response_text,
                "response_content": response_text[:max_length],
            }
        return {"response_content": response_text}
