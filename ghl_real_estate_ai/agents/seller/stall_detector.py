"""
Stall detection service for seller conversations.

Detects when leads are using standard stalling language and categorizes the stall type.
"""

from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher

logger = get_logger(__name__)


class StallDetector:
    """Service for detecting and categorizing seller stalls."""

    # Stall type keywords for detection
    STALL_KEYWORDS = {
        "thinking": ["think", "pondering", "consider", "decide"],
        "get_back": ["get back", "later", "next week", "busy"],
        "zestimate": ["zestimate", "zillow", "online value", "estimate says"],
        "agent": ["agent", "realtor", "broker", "with someone"],
        "just_looking": [
            "just looking", "just browsing", "exploring options",
            "kicking tires", "not ready yet", "window shopping", "just curious",
        ],
    }

    # Friendly response templates for detected stalls
    FRIENDLY_RESPONSES = {
        "thinking": "Totally get it—big decision. What's the main thing holding you back? Happy to pull numbers if that helps.",
        "get_back": "No rush! Has anything changed with your timeline? I can send fresh comps if useful.",
        "zestimate": "Zillow can't walk through your house! Want to see what neighbors actually sold for recently? Real numbers might surprise you.",
        "agent": "Great you have someone! Happy to share comps from your area—could be useful for your agent too.",
        "price": "Pricing is tricky. Want me to pull recent sales nearby? Real data beats guessing every time.",
        "timeline": "Makes sense. What's driving your timeline—market, a move, or something else?",
    }

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher or get_event_publisher()

    async def detect_stall(self, state: JorgeSellerState) -> Dict[str, Any]:
        """Detect if the lead is using standard stalling language."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="detect_stall"
        )

        last_msg = ""
        if state.get("conversation_history"):
            last_msg = state["conversation_history"][-1].get("content", "").lower()

        detected_type = None
        for stall_type, keywords in self.STALL_KEYWORDS.items():
            if any(k in last_msg for k in keywords):
                detected_type = stall_type
                break

        # Emit conversation event for stall detection
        if detected_type:
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="stall_detected",
                message=f"Stall type detected: {detected_type}",
            )

        return {
            "stall_detected": detected_type is not None,
            "detected_stall_type": detected_type
        }

    def get_friendly_response(self, stall_type: str) -> Optional[str]:
        """Get a friendly response template for a detected stall type."""
        return self.FRIENDLY_RESPONSES.get(stall_type)

    def classify_temperature(self, profile) -> str:
        """Classify seller temperature based on intent scores."""
        total_score = profile.pcs.total_score + profile.frs.total_score

        if total_score >= 75:
            return "hot"
        elif total_score >= 50:
            return "warm"
        else:
            return "cold"

    def extract_property_condition(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract property condition from conversation keywords."""
        if not conversation_history:
            return None

        text = " ".join(
            msg.get("content", "").lower()
            for msg in conversation_history
            if msg.get("role") == "user"
        )

        move_in_ready_markers = [
            "move-in ready", "move in ready", "turnkey", "just remodeled",
            "recently renovated", "updated", "great condition", "perfect condition",
        ]
        needs_work_markers = [
            "needs work", "needs some work", "needs updating", "dated",
            "cosmetic", "needs paint", "some updates", "a little work",
        ]
        major_repairs_markers = [
            "major repairs", "fixer", "fixer-upper", "foundation",
            "roof issues", "structural", "condemned", "tear down",
        ]

        if any(m in text for m in major_repairs_markers):
            return "major_repairs"
        elif any(m in text for m in needs_work_markers):
            return "needs_work"
        elif any(m in text for m in move_in_ready_markers):
            return "move_in_ready"

        return None
