"""Language detection result and contact language preference models."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LanguageDetection:
    """Result of language detection on a single message."""

    language: str  # ISO 639-1 code ("en", "es", etc.)
    confidence: float  # 0.0-1.0
    is_code_switching: bool = False  # True if mixed languages detected
    secondary_language: Optional[str] = None


@dataclass
class ContactLanguagePreference:
    """Accumulated language preference for a contact across messages."""

    contact_id: str
    primary_language: str = "en"
    language_counts: Dict[str, int] = field(default_factory=dict)
    total_messages: int = 0

    def update(self, detection: LanguageDetection) -> None:
        """Update preference from a new detection."""
        self.language_counts[detection.language] = self.language_counts.get(detection.language, 0) + 1
        self.total_messages += 1
        # Primary is most frequent
        self.primary_language = max(self.language_counts, key=self.language_counts.get)  # type: ignore[arg-type]
