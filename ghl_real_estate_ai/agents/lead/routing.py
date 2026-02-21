"""
Lead Router for classifying and routing leads based on intent signals.
"""

from typing import TYPE_CHECKING, List, Literal

from ghl_real_estate_ai.agents.lead.constants import BUYING_SIGNALS, MILESTONE_KEYWORDS
from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.models.workflows import LeadFollowUpState

logger = get_logger(__name__)


class LeadRouter:
    """Routes leads based on intent signals, engagement, and temperature"""

    @staticmethod
    def classify_lead_for_routing(state: "LeadFollowUpState") -> Literal["qualified", "nurture"]:
        """
        Classify lead for routing based on intent signals, engagement, and temperature.

        Returns:
            'qualified' if lead shows strong buying/selling signals
            'nurture' if lead needs more engagement
        """
        # Check intent profile for classification
        intent_profile = state.get("intent_profile")
        if intent_profile:
            frs = getattr(intent_profile, "frs", None)
            if frs:
                classification = getattr(frs, "classification", "")
                if classification in ["Hot Lead", "Warm Lead"]:
                    return "qualified"

        # Check lead score from state
        lead_score = state.get("lead_score", 0)
        if lead_score >= 70:
            return "qualified"

        # Analyze conversation for buying signals
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            message_text = " ".join(
                msg.get("content", "").lower() for msg in recent_messages if msg.get("role") == "user"
            )

            if any(signal in message_text for signal in BUYING_SIGNALS):
                return "qualified"

        # Check engagement status
        engagement = state.get("engagement_status", "")
        if engagement in ["showing_booked", "offer_sent", "under_contract"]:
            return "qualified"

        # Default to nurture for leads needing more engagement
        return "nurture"

    @staticmethod
    def determine_escrow_milestone(state: "LeadFollowUpState") -> str:
        """
        Determine current escrow milestone based on lead state and timeline.

        Milestones in order:
        1. contract_signed - Initial contract execution
        2. inspection - Home inspection period
        3. appraisal - Property appraisal
        4. loan_approval - Final loan approval
        5. final_walkthrough - Pre-closing walkthrough
        6. closing - Closing day
        """
        # Check for milestone indicators in conversation history
        conversation_text = " ".join(msg.get("content", "").lower() for msg in state.get("conversation_history", []))

        # Check custom fields or state for milestone tracking
        custom_fields = state.get("custom_fields", {})
        current_milestone = custom_fields.get("escrow_milestone", "")

        if current_milestone:
            return current_milestone

        # Check in reverse order (most advanced milestone first)
        for milestone, keywords in MILESTONE_KEYWORDS.items():
            if any(kw in conversation_text for kw in keywords):
                return milestone

        # Default to inspection as first major milestone after contract
        return "inspection"

    @staticmethod
    def select_stall_breaker(last_message: str, ghost_engine) -> str:
        """Select the appropriate stall-breaking script based on intent profile via GhostEngine."""
        objection_type = "market_shift"  # Default

        last_msg_lower = last_message.lower()

        if "thinking" in last_msg_lower:
            objection_type = "thinking_about_it"
        elif "get back" in last_msg_lower:
            objection_type = "get_back_to_you"
        elif "zestimate" in last_msg_lower or "zillow" in last_msg_lower:
            objection_type = "zestimate_reference"
        elif "agent" in last_msg_lower or "realtor" in last_msg_lower:
            objection_type = "has_realtor"

        return ghost_engine.get_stall_breaker(objection_type)

    @staticmethod
    def has_price_keywords(message: str) -> bool:
        """Check if message contains price-related keywords."""
        from ghl_real_estate_ai.agents.lead.constants import PRICE_KEYWORDS

        msg_lower = message.lower()
        return any(kw in msg_lower for kw in PRICE_KEYWORDS)

    @staticmethod
    def extract_buying_signals(conversation_history: List[dict]) -> List[str]:
        """Extract buying/selling signals from conversation history."""
        signals_found = []
        for msg in conversation_history:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                for signal in BUYING_SIGNALS:
                    if signal in content and signal not in signals_found:
                        signals_found.append(signal)
        return signals_found
