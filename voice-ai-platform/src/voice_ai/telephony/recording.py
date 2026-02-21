"""Recording consent and handling for voice calls."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# US states requiring two-party consent for call recording
TWO_PARTY_CONSENT_STATES = {
    "CA",
    "CT",
    "FL",
    "IL",
    "MD",
    "MA",
    "MI",
    "MT",
    "NH",
    "PA",
    "WA",
}

CONSENT_PROMPT = (
    "This call may be recorded for quality assurance and training purposes. "
    "Do you consent to being recorded?"
)

AI_DISCLOSURE_TEMPLATE = (
    "Hi, this is Jorge, an AI assistant with {agency_name}. "
    "I'm here to help you with your real estate needs. "
)

CONSENT_POSITIVE_KEYWORDS = {"yes", "sure", "okay", "ok", "yeah", "yep", "absolutely", "go ahead"}
CONSENT_NEGATIVE_KEYWORDS = {"no", "nope", "don't", "do not", "refuse", "decline"}


@dataclass
class RecordingConsent:
    """Result of consent evaluation."""

    consent_given: bool
    needs_prompt: bool
    disclosure_text: str = ""


class RecordingManager:
    """Manages recording consent and compliance."""

    def __init__(self, agency_name: str = "our real estate team"):
        self.agency_name = agency_name

    def get_ai_disclosure(self) -> str:
        """Return the AI disclosure message (mandatory for outbound calls per TCPA)."""
        return AI_DISCLOSURE_TEMPLATE.format(agency_name=self.agency_name)

    def needs_consent_prompt(self, caller_state: str | None) -> bool:
        """Check if the caller's state requires two-party consent."""
        if caller_state is None:
            # Default to requiring consent if state is unknown
            return True
        return caller_state.upper() in TWO_PARTY_CONSENT_STATES

    def get_consent_prompt(self) -> str:
        """Return the consent prompt text."""
        return CONSENT_PROMPT

    def evaluate_consent_response(self, response_text: str) -> bool | None:
        """Evaluate whether the caller's response indicates consent.

        Returns True for consent, False for refusal, None for unclear.
        """
        text_lower = response_text.lower().strip()

        if any(kw in text_lower for kw in CONSENT_POSITIVE_KEYWORDS):
            return True
        if any(kw in text_lower for kw in CONSENT_NEGATIVE_KEYWORDS):
            return False
        return None

    def get_opening_sequence(self, direction: str, caller_state: str | None = None) -> list[str]:
        """Return the sequence of messages for the call opening.

        For outbound calls: AI disclosure + consent prompt (if needed)
        For inbound calls: consent prompt (if needed) + greeting
        """
        messages = []

        if direction == "outbound":
            messages.append(self.get_ai_disclosure())

        if self.needs_consent_prompt(caller_state):
            messages.append(self.get_consent_prompt())

        return messages
