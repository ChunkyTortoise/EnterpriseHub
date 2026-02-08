"""
Shared Sentiment Analysis Types
==============================

Common types used across sentiment analysis services to avoid circular imports.
Contains interfaces and data classes for sentiment analysis.

Author: EnterpriseHub - January 2026
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SentimentTriggerType(Enum):
    """Types of sentiment triggers that indicate selling motivation."""

    NEIGHBORHOOD_DECLINE = "neighborhood_decline"
    PERMIT_DISRUPTION = "permit_disruption"
    ECONOMIC_STRESS = "economic_stress"
    LIFESTYLE_CHANGE = "lifestyle_change"
    INVESTMENT_PRESSURE = "investment_pressure"
    INFRASTRUCTURE_CONCERN = "infrastructure_concern"


class AlertPriority(Enum):
    """Priority levels for sentiment alerts."""

    CRITICAL = "critical"  # Act within 24 hours
    HIGH = "high"  # Act within 3 days
    MEDIUM = "medium"  # Act within 1 week
    LOW = "low"  # Monitor for trends


@dataclass
class SentimentSignal:
    """Individual sentiment signal from a data source."""

    source: str  # "twitter", "nextdoor", "permits", "news"
    signal_type: SentimentTriggerType
    location: str  # ZIP code or neighborhood
    sentiment_score: float  # -100 to +100
    confidence: float  # 0.0 to 1.0
    raw_content: Optional[str]  # Original text/data
    detected_at: datetime
    urgency_multiplier: float  # 1.0-5.0 for timing urgency

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "signal_type": self.signal_type.value,
            "location": self.location,
            "sentiment_score": self.sentiment_score,
            "confidence": self.confidence,
            "raw_content": self.raw_content,
            "detected_at": self.detected_at.isoformat(),
            "urgency_multiplier": self.urgency_multiplier,
        }


class DataSourceInterface(ABC):
    """Abstract interface for sentiment data sources."""

    @abstractmethod
    async def fetch_sentiment_data(self, location: str, timeframe_days: int = 30) -> List[SentimentSignal]:
        """Fetch sentiment signals for a location and timeframe."""
        pass


@dataclass
class MarketSentiment:
    """Aggregated market sentiment for a location."""

    location: str
    overall_score: float  # 0.0 to 1.0 (0=negative, 1=positive)
    confidence_level: float  # 0.0 to 1.0
    signals: List[SentimentSignal]
    recommended_action: str  # "immediate", "1-week", "2-weeks", "monitor"
    analysis_timestamp: datetime

    @property
    def high_priority_signals(self) -> List[SentimentSignal]:
        """Get high priority signals only."""
        return [s for s in self.signals if s.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]]

    @property
    def motivation_indicators(self) -> Dict[str, int]:
        """Count signals by trigger type."""
        counts = {}
        for signal in self.signals:
            trigger_name = signal.signal_type.value
            counts[trigger_name] = counts.get(trigger_name, 0) + 1
        return counts
