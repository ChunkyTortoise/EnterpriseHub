"""PII detection on call transcripts using pattern matching.

Production deployment would use Microsoft Presidio; this module provides
a lightweight pattern-based detector for the MVP that follows the same interface.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# PII patterns with regex
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "US_SSN": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "PHONE_NUMBER": re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "US_BANK_NUMBER": re.compile(r"\b\d{8,17}\b"),  # Simplified; real impl would be more specific
}

HIGH_RISK_TYPES = {"US_SSN", "CREDIT_CARD", "US_BANK_NUMBER"}


@dataclass
class PIIResult:
    """A single PII detection result."""

    entity_type: str
    start: int
    end: int
    score: float = 0.85


class PIIDetector:
    """Real-time PII detection on call transcripts.

    Scans text for PII entities and can redact them for safe storage.
    """

    ENTITIES = list(PII_PATTERNS.keys())

    def detect(self, text: str) -> list[PIIResult]:
        """Detect PII entities in transcript text."""
        results: list[PIIResult] = []
        for entity_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                results.append(
                    PIIResult(
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        score=0.85,
                    )
                )
        return results

    def redact(self, text: str) -> str:
        """Redact PII from text for safe storage/logging."""
        results = self.detect(text)
        if not results:
            return text

        # Sort by position (reverse) to replace from end to start
        results.sort(key=lambda r: r.start, reverse=True)
        redacted = text
        for r in results:
            replacement = f"<{r.entity_type}>"
            redacted = redacted[: r.start] + replacement + redacted[r.end :]
        return redacted

    def has_sensitive_pii(self, text: str) -> tuple[bool, list[str]]:
        """Check if text contains high-risk PII (SSN, credit card, bank number)."""
        results = self.detect(text)
        found = [r.entity_type for r in results if r.entity_type in HIGH_RISK_TYPES]
        return bool(found), found

    def get_pii_types(self, text: str) -> list[str]:
        """Return unique PII types found in text."""
        results = self.detect(text)
        return list({r.entity_type for r in results})
