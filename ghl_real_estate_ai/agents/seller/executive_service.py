"""
Executive briefing service for Jorge Seller Bot.

Generates structured executive briefs for human agents when a seller is highly qualified.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType, get_claude_orchestrator
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher

try:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

    GHL_CLIENT_AVAILABLE = True
except ImportError:
    GHL_CLIENT_AVAILABLE = False
    EnhancedGHLClient = None

logger = get_logger(__name__)


class ExecutiveService:
    """Service for generating executive briefs for high-quality leads."""

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher or get_event_publisher()

    async def generate_executive_brief(self, state: JorgeSellerState) -> Dict[str, Any]:
        """
        Generate a structured executive brief for human agents when a seller is highly qualified.
        Uses Claude Orchestrator with task type EXECUTIVE_BRIEFING.
        """
        lead_id = state.get("lead_id", "unknown")
        composite_score = state.get("composite_score", {}).get("total_score", 0.0)

        # Only generate brief for high-quality leads (Score > 80)
        if composite_score < 80:
            return {"executive_brief_generated": False}

        try:
            orchestrator = get_claude_orchestrator()

            # Prepare context for the brief
            context = {
                "lead_id": lead_id,
                "bot_type": "seller",
                "persona": state.get("seller_persona"),
                "scores": {
                    "composite": composite_score,
                    "frs": state.get("intent_profile").frs.total_score if state.get("intent_profile") else 0,
                    "pcs": state.get("psychological_commitment", 0),
                },
                "property_address": state.get("property_address"),
                "cma_summary": state.get("cma_report", {}).get("estimated_value"),
                "conversation_history": state.get("conversation_history", [])[-10:],  # Last 10 turns
            }

            # Generate brief via Orchestrator
            brief_response = await orchestrator.process_request(
                ClaudeRequest(
                    task_type=ClaudeTaskType.EXECUTIVE_BRIEFING,
                    context=context,
                    prompt=f"Generate a one-page executive brief for Jorge regarding seller {lead_id}. Highlight property value, motivation, and recommended next steps.",
                )
            )

            brief_content = brief_response.content

            # Sync brief to GHL as a note
            if GHL_CLIENT_AVAILABLE and EnhancedGHLClient:
                async with EnhancedGHLClient() as ghl:
                    await ghl.add_contact_note(contact_id=lead_id, body=f"--- EXECUTIVE BRIEF ---\n{brief_content}")

            logger.info(f"Executive brief generated and synced for seller {lead_id}")

            return {
                "executive_brief": brief_content,
                "executive_brief_generated": True,
                "current_journey_stage": "handoff_ready",
            }

        except Exception as e:
            logger.error(f"Error generating executive brief for seller {lead_id}: {e}")
            return {"executive_brief_generated": False}
