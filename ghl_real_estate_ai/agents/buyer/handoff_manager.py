"""
Handoff context management module for buyer bot.
Handles validation and population of handoff context from other bots.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Try to import handoff context - may not be available in all environments
try:
    from ghl_real_estate_ai.services.jorge.jorge_handoff_service import EnrichedHandoffContext
    HANDOFF_CONTEXT_AVAILABLE = True
except ImportError:
    HANDOFF_CONTEXT_AVAILABLE = False
    EnrichedHandoffContext = None


class HandoffManager:
    """Manages handoff context validation and state population."""

    def __init__(self):
        self.handoff_context_available = HANDOFF_CONTEXT_AVAILABLE

    def has_valid_handoff_context(
        self,
        handoff_context: Optional[Any]
    ) -> bool:
        """
        Check if handoff context is valid and recent (<24h).

        Args:
            handoff_context: The handoff context to validate

        Returns:
            True if context is valid and recent, False otherwise
        """
        if not handoff_context or not self.handoff_context_available:
            return False

        # Check if context has timestamp and is recent
        if hasattr(handoff_context, 'timestamp'):
            try:
                if isinstance(handoff_context.timestamp, str):
                    context_time = datetime.fromisoformat(handoff_context.timestamp.replace('Z', '+00:00'))
                else:
                    context_time = handoff_context.timestamp

                age = datetime.now(timezone.utc) - context_time
                if age > timedelta(hours=24):
                    logger.info(f"Handoff context is stale (age: {age.total_seconds() / 3600:.1f}h)")
                    return False
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse handoff context timestamp: {e}")
                return False

        # Check if context has meaningful data
        has_data = (
            getattr(handoff_context, 'budget_range', None) or
            getattr(handoff_context, 'conversation_summary', None) or
            getattr(handoff_context, 'key_insights', None)
        )

        if not has_data:
            logger.info("Handoff context present but lacks meaningful data")
            return False

        logger.info("Valid handoff context detected - will skip re-qualification")
        return True

    def populate_state_from_context(
        self,
        handoff_context: Any,
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Populate buyer state from handoff context to skip re-qualification.

        Args:
            handoff_context: The validated handoff context
            initial_state: The initial buyer state dict

        Returns:
            Updated state dict with context data
        """
        try:
            # Populate budget information
            if getattr(handoff_context, 'budget_range', None):
                initial_state["budget_range"] = handoff_context.budget_range
                initial_state["financial_readiness_score"] = 70.0  # High since came from lead bot
                logger.info(f"Populated budget from handoff: {handoff_context.budget_range}")

            # Populate urgency level
            if getattr(handoff_context, 'urgency_level', None):
                initial_state["urgency_level"] = handoff_context.urgency_level
                # Map urgency to score
                urgency_map = {
                    "immediate": 90,
                    "urgent": 80,
                    "ready": 70,
                    "considering": 50,
                    "browsing": 30
                }
                initial_state["urgency_score"] = urgency_map.get(handoff_context.urgency_level, 50)
                logger.info(f"Populated urgency from handoff: {handoff_context.urgency_level}")

            # Add key insights to metadata for context
            if getattr(handoff_context, 'key_insights', None):
                if "metadata" not in initial_state:
                    initial_state["metadata"] = {}
                initial_state["metadata"]["handoff_insights"] = handoff_context.key_insights
                logger.info(f"Added {len(handoff_context.key_insights)} key insights from handoff")

            # Add conversation summary for continuity
            if getattr(handoff_context, 'conversation_summary', None):
                # Prepend summary to conversation history as system message
                summary_msg = {
                    "role": "system",
                    "content": f"[HANDOFF CONTEXT] {handoff_context.conversation_summary}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                if "conversation_history" not in initial_state:
                    initial_state["conversation_history"] = []
                initial_state["conversation_history"].insert(0, summary_msg)
                logger.info("Added conversation summary from handoff")

            # Mark that we should skip qualification
            initial_state["skip_qualification"] = True
            initial_state["handoff_context_used"] = True
            initial_state["current_qualification_step"] = "property_matching"  # Skip to matching

            logger.info("Successfully populated state from handoff context")
            return initial_state

        except Exception as e:
            logger.error(f"Error populating state from handoff context: {e}")
            # Return original state on error - fall back to normal qualification
            initial_state["skip_qualification"] = False
            return initial_state