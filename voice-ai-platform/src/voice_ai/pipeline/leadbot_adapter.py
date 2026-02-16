"""Adapter wrapping EnterpriseHub LeadBot for voice context."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Default system prompt for lead qualification voice calls
LEADBOT_SYSTEM_PROMPT = """You are Jorge, a friendly and professional AI real estate assistant.
Your role is to qualify inbound leads by understanding their needs, timeline, and budget.

Key behaviors:
- Ask about their property interests (buying, selling, or both)
- Understand their timeline (urgent, 3-6 months, just browsing)
- Gauge financial readiness (pre-approved, working with lender, etc.)
- Collect contact preferences for follow-up
- Be warm, conversational, and helpful — this is a phone call, not a form

When a lead shows strong buyer or seller intent, recommend transferring
to the appropriate specialist bot.
"""


@dataclass
class LeadBotAdapter:
    """Wraps EnterpriseHub LeadBot logic for voice pipeline integration.

    In production, this imports and delegates to LeadBotWorkflow.
    For the MVP, it provides the interface and system prompt management.
    """

    system_prompt: str = LEADBOT_SYSTEM_PROMPT
    agency_name: str = "our real estate team"
    _context: dict[str, Any] = field(default_factory=dict, repr=False)

    def get_system_prompt(self, persona_override: str | None = None) -> str:
        """Return the system prompt, optionally overridden by persona config."""
        if persona_override:
            return persona_override
        return self.system_prompt.format(agency_name=self.agency_name)

    def get_greeting(self) -> str:
        """Return the greeting message for call start."""
        return (
            f"Hi, this is Jorge, an AI assistant with {self.agency_name}. "
            "How can I help you with your real estate needs today?"
        )

    async def process_message(self, user_text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process a user message through the lead bot logic.

        Returns a dict with response text and metadata (lead_score, handoff_signals, etc.).

        In production, this delegates to LeadBotWorkflow.process_lead_conversation().
        """
        # MVP: return structured response for pipeline integration
        return {
            "response": "",  # LLM generates the actual response via system prompt
            "lead_score": None,
            "temperature": None,
            "handoff_signals": [],
            "bot_type": "lead",
        }

    def extract_handoff_signals(self, conversation_history: list[dict[str, str]]) -> dict[str, float]:
        """Analyze conversation for handoff signals to buyer/seller bots.

        Returns confidence scores for each potential handoff target.
        """
        buyer_keywords = {"buy", "purchase", "pre-approved", "budget", "mortgage", "home loan"}
        seller_keywords = {"sell", "listing", "home value", "cma", "market analysis"}

        all_text = " ".join(
            turn["content"].lower() for turn in conversation_history if turn["role"] == "user"
        )

        buyer_score = sum(1 for kw in buyer_keywords if kw in all_text) / len(buyer_keywords)
        seller_score = sum(1 for kw in seller_keywords if kw in all_text) / len(seller_keywords)

        return {
            "buyer": min(buyer_score, 1.0),
            "seller": min(seller_score, 1.0),
        }
