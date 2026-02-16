"""PII detector — scan documents and queries for personally identifiable information."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PIIEntity:
    """Detected PII entity."""
    entity_type: str  # EMAIL, PHONE, SSN, CREDIT_CARD, etc.
    text: str
    start: int
    end: int
    score: float = 1.0


@dataclass
class PIIScanResult:
    """Result of PII scanning."""
    has_pii: bool
    entities: list[PIIEntity] = field(default_factory=list)
    redacted_text: str = ""
    entity_counts: dict[str, int] = field(default_factory=dict)


class PIIDetector:
    """Detect and redact PII using Presidio if available, with regex fallback."""

    # Regex patterns for common PII types
    PATTERNS = {
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "PHONE": re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "SSN": re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-.\s]?){3}\d{4}\b"),
        "IP_ADDRESS": re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
    }

    REDACTION_CHAR = "*"

    def __init__(self, use_presidio: bool = False):
        self.use_presidio = use_presidio
        self.analyzer = None

        if use_presidio:
            try:
                from presidio_analyzer import AnalyzerEngine
                self.analyzer = AnalyzerEngine()
            except ImportError:
                logger.warning("Presidio not installed, falling back to regex PII detection")
                self.use_presidio = False

    def scan(self, text: str) -> PIIScanResult:
        """Scan text for PII entities."""
        if self.use_presidio and self.analyzer:
            return self._scan_presidio(text)
        return self._scan_regex(text)

    def redact(self, text: str) -> str:
        """Scan and redact PII from text."""
        result = self.scan(text)
        return result.redacted_text

    def _scan_presidio(self, text: str) -> PIIScanResult:
        """Scan using Presidio analyzer."""
        results = self.analyzer.analyze(text=text, language="en")

        entities = [
            PIIEntity(
                entity_type=r.entity_type,
                text=text[r.start : r.end],
                start=r.start,
                end=r.end,
                score=r.score,
            )
            for r in results
        ]

        redacted = self._apply_redaction(text, entities)
        counts: dict[str, int] = {}
        for e in entities:
            counts[e.entity_type] = counts.get(e.entity_type, 0) + 1

        return PIIScanResult(
            has_pii=len(entities) > 0,
            entities=entities,
            redacted_text=redacted,
            entity_counts=counts,
        )

    def _scan_regex(self, text: str) -> PIIScanResult:
        """Scan using regex patterns."""
        entities: list[PIIEntity] = []

        for entity_type, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                entities.append(
                    PIIEntity(
                        entity_type=entity_type,
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                    )
                )

        # Sort by position (reverse for redaction)
        entities.sort(key=lambda e: e.start)

        redacted = self._apply_redaction(text, entities)
        counts: dict[str, int] = {}
        for e in entities:
            counts[e.entity_type] = counts.get(e.entity_type, 0) + 1

        return PIIScanResult(
            has_pii=len(entities) > 0,
            entities=entities,
            redacted_text=redacted,
            entity_counts=counts,
        )

    def _apply_redaction(self, text: str, entities: list[PIIEntity]) -> str:
        """Replace PII entities with redaction markers."""
        if not entities:
            return text

        # Process from end to start to maintain positions
        result = list(text)
        for entity in sorted(entities, key=lambda e: e.start, reverse=True):
            replacement = f"[{entity.entity_type}]"
            result[entity.start : entity.end] = list(replacement)

        return "".join(result)
