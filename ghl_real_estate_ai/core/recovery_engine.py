"""
Autonomous Recovery Engine (Agent R1)
Implements 'Safe Mode' fallbacks and circuit breaker recovery for bot failures.

Ensures that leads NEVER see an error message even if LLM/RAG services fail.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RecoveryEngine:
    """
    Handles graceful degradation when primary AI services fail.
    Provides rule-based fallbacks based on conversation state.
    """

    def __init__(self):
        self.failure_counts: Dict[str, int] = {}
        self.circuit_breaker_threshold = 3

    def get_safe_fallback(
        self,
        contact_name: str,
        conversation_history: List[Dict[str, str]],
        extracted_preferences: Dict[str, Any],
        is_seller: bool = False,
    ) -> str:
        """
        Generates a rule-based 'Safe Mode' response when AI fails.
        """
        name = contact_name if contact_name and contact_name != "there" else ""
        greeting = f"Hey {name}, " if name else "Hey! "

        # 1. Determine most likely next question based on missing data
        if is_seller:
            return self._get_seller_fallback(greeting, extracted_preferences)
        else:
            return self._get_buyer_fallback(greeting, extracted_preferences)

    def _get_buyer_fallback(self, greeting: str, prefs: Dict[str, Any]) -> str:
        """Rule-based buyer qualification flow fallback."""
        if not prefs.get("location"):
            return f"{greeting}What area are you looking to buy in?"
        if not prefs.get("budget"):
            return f"{greeting}What's your budget for the new home?"
        if not prefs.get("timeline"):
            return f"{greeting}When are you hoping to move?"
        if not prefs.get("bedrooms"):
            return f"{greeting}How many beds and baths do you need?"

        return f"{greeting}Got it. I'm checking some options for you. Would you like to hop on a quick call with Jorge's team later today?"

    def _get_seller_fallback(self, greeting: str, prefs: Dict[str, Any]) -> str:
        """Rule-based seller qualification flow fallback."""
        if not prefs.get("motivation"):
            return f"{greeting}What's got you considering wanting to sell, where would you move to?"
        if prefs.get("timeline_acceptable") is None:
            return f"{greeting}If our team sold your home within 30 to 45 days, would that pose a problem for you?"
        if not prefs.get("property_condition"):
            return f"{greeting}How would you describe your home, would you say it's move-in ready or would it need some work?"
        if not prefs.get("price_expectation"):
            return f"{greeting}What price would incentivize you to sell?"

        return f"{greeting}Thanks for those details. I'll have Jorge's team review this and get back to you. Are mornings or afternoons better for a call?"

    def log_failure(self, service_name: str):
        """Track service failures for circuit breaker logic."""
        self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
        logger.warning(
            f"RecoveryEngine: Service {service_name} failure logged. Total: {self.failure_counts[service_name]}"
        )

    def is_service_down(self, service_name: str) -> bool:
        """Check if a service should be bypassed."""
        return self.failure_counts.get(service_name, 0) >= self.circuit_breaker_threshold
