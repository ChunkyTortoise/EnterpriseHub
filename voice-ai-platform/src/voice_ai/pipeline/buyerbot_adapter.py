"""Adapter wrapping EnterpriseHub BuyerBot for voice context."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

BUYERBOT_SYSTEM_PROMPT = """You are Jorge, a knowledgeable AI buyer's agent assistant.
Your role is to help potential home buyers find their ideal property.

Key behaviors:
- Understand their must-haves vs nice-to-haves (bedrooms, location, schools)
- Discuss budget range and financing options
- Explain the buying process and timeline
- Offer to schedule property showings or virtual tours
- Provide market insights for their target areas (Rancho Cucamonga speciality)
- When ready, help book an appointment with a human agent

Be enthusiastic but honest. Guide them through the process step by step.
"""


@dataclass
class BuyerBotAdapter:
    """Wraps EnterpriseHub BuyerBot logic for voice pipeline integration."""

    system_prompt: str = BUYERBOT_SYSTEM_PROMPT
    agency_name: str = "our real estate team"
    _context: dict[str, Any] = field(default_factory=dict, repr=False)

    def get_system_prompt(self, persona_override: str | None = None) -> str:
        if persona_override:
            return persona_override
        return self.system_prompt

    def get_greeting(self) -> str:
        return (
            "Great, I can help you find your perfect home! "
            "To get started, what area are you looking in, and what's your budget range?"
        )

    async def process_message(self, user_text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process a buyer message. In production, delegates to JorgeBuyerBot."""
        return {
            "response": "",
            "financial_readiness": None,
            "handoff_signals": [],
            "bot_type": "buyer",
        }
