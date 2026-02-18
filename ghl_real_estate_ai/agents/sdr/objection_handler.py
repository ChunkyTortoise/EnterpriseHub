"""
SDR ObjectionHandler — pattern-matched objection classification and rebuttal generation.

Phase 1: pattern matching only (no Claude fallback yet).
Phase 2 will add: Claude-generated rebuttals via ClaudeOrchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Objection pattern library
# ---------------------------------------------------------------------------

OBJECTION_PATTERNS: Dict[str, List[str]] = {
    "not_interested": [
        "not interested",
        "don't contact",
        "do not contact",
        "remove me",
        "stop texting",
        "stop calling",
        "unsubscribe",
        "opt out",
        "leave me alone",
        "take me off",
    ],
    "already_agent": [
        "have an agent",
        "working with someone",
        "my realtor",
        "my agent",
        "already represented",
    ],
    "timing": [
        "not ready",
        "not yet",
        "maybe later",
        "few months",
        "next year",
        "not now",
        "waiting",
        "in a while",
    ],
    "price": [
        "too expensive",
        "can't afford",
        "market is crazy",
        "overpriced",
        "too high",
        "out of budget",
    ],
    "info_request": [
        "tell me more",
        "what's this about",
        "who are you",
        "how did you get my number",
        "what do you offer",
        "more information",
    ],
}

# Rebuttal strategies mapped to objection types
REBUTTAL_STRATEGY: Dict[str, str] = {
    "not_interested": "polite_exit",      # opt-out, tag DND, stop sequence
    "already_agent": "value_add",         # offer market report, keep warm
    "timing": "nurture_pause",            # move to NURTURE_PAUSE step
    "price": "education",                 # send market data email
    "info_request": "qualify",            # respond, advance sequence
}

# Types that require opting the contact out of all further outreach
_OPT_OUT_TYPES = {"not_interested"}


@dataclass
class ObjectionResult:
    """Result of objection handling."""

    objection_type: Optional[str]       # classified type, or None if no match
    strategy: str                       # "polite_exit" | "value_add" | "nurture_pause" | etc.
    rebuttal_message: Optional[str]     # message to send (None for opt-out)
    should_opt_out: bool
    should_pause: bool                  # True for timing objections → NURTURE_PAUSE


class ObjectionHandler:
    """
    Classifies inbound replies as objections and determines the appropriate response.

    Phase 1: pattern-match based (fast, no LLM dependency).
    Phase 2: adds Claude fallback for ambiguous messages via ClaudeOrchestrator.
    """

    def __init__(self, orchestrator: Any = None) -> None:
        # orchestrator reserved for Phase 2 Claude fallback
        self._orchestrator = orchestrator

    def classify_objection(self, message: str) -> Optional[str]:
        """
        Classify an inbound message as an objection type.

        Returns the objection type string or None if no objection detected.
        Uses case-insensitive substring matching.
        """
        message_lower = message.lower()
        for objection_type, patterns in OBJECTION_PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    logger.info(
                        f"[SDR] Objection classified: {objection_type} "
                        f"(matched '{pattern}')"
                    )
                    return objection_type
        return None

    def should_opt_out(self, objection_type: str) -> bool:
        """Return True if this objection type requires stopping all outreach."""
        return objection_type in _OPT_OUT_TYPES

    def handle(self, message: str, contact_id: str = "") -> ObjectionResult:
        """
        Classify and build an ObjectionResult for a given inbound message.

        Returns an ObjectionResult with strategy and rebuttal guidance.
        """
        objection_type = self.classify_objection(message)
        if objection_type is None:
            return ObjectionResult(
                objection_type=None,
                strategy="qualify",
                rebuttal_message=None,
                should_opt_out=False,
                should_pause=False,
            )

        strategy = REBUTTAL_STRATEGY.get(objection_type, "qualify")
        opt_out = self.should_opt_out(objection_type)
        pause = strategy == "nurture_pause"

        # Phase 1: static rebuttal messages
        rebuttal = _STATIC_REBUTTALS.get(objection_type) if not opt_out else None

        logger.info(
            f"[SDR] ObjectionHandler contact={contact_id} "
            f"type={objection_type} strategy={strategy} opt_out={opt_out}"
        )
        return ObjectionResult(
            objection_type=objection_type,
            strategy=strategy,
            rebuttal_message=rebuttal,
            should_opt_out=opt_out,
            should_pause=pause,
        )


# Phase 1 static rebuttals (Phase 2 replaces with Claude-generated personalized messages)
_STATIC_REBUTTALS: Dict[str, str] = {
    "already_agent": (
        "Totally understand — I just wanted to offer a free market analysis for your "
        "area regardless. No strings attached. Would that be helpful?"
    ),
    "timing": (
        "No worries at all! I'll check back in a few months. "
        "In the meantime, feel free to reach out anytime."
    ),
    "price": (
        "Completely fair. The market has been intense. "
        "I can send over a current market report so you have the data when you're ready — "
        "would that be useful?"
    ),
    "info_request": (
        "Great question! I help homeowners and buyers in the Rancho Cucamonga area "
        "navigate the market. I'd love to learn more about what you're looking for — "
        "what's your main goal right now?"
    ),
}
