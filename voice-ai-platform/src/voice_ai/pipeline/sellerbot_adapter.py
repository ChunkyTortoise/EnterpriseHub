"""Adapter wrapping EnterpriseHub SellerBot for voice context."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

SELLERBOT_SYSTEM_PROMPT = """You are Jorge, an expert AI seller's agent assistant.
Your role is to help homeowners understand the selling process and property valuation.

Key behaviors:
- Ask about their property (address, bedrooms, recent improvements)
- Discuss their selling timeline and motivation
- Explain the CMA (Comparative Market Analysis) process
- Provide general market trends for their area
- When appropriate, offer to book a listing consultation
- Address concerns about pricing, staging, and marketing

Be empathetic and knowledgeable. Selling a home is a big decision.
"""


@dataclass
class SellerBotAdapter:
    """Wraps EnterpriseHub SellerBot logic for voice pipeline integration."""

    system_prompt: str = SELLERBOT_SYSTEM_PROMPT
    agency_name: str = "our real estate team"
    _context: dict[str, Any] = field(default_factory=dict, repr=False)

    def get_system_prompt(self, persona_override: str | None = None) -> str:
        if persona_override:
            return persona_override
        return self.system_prompt

    def get_greeting(self) -> str:
        return (
            "I'd be happy to help you explore selling your home. "
            "Can you start by telling me a bit about your property and your timeline?"
        )

    async def process_message(self, user_text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process a seller message. In production, delegates to JorgeSellerBot."""
        return {
            "response": "",
            "frs_score": None,
            "pcs_score": None,
            "handoff_signals": [],
            "bot_type": "seller",
        }
