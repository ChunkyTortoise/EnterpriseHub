"""Shared data models for Jorge analytics services."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ResponsePattern:
    """Tracks lead response patterns for optimization"""

    avg_response_hours: float
    response_count: int
    channel_preferences: Dict[str, float]  # SMS, Email, Voice, WhatsApp
    engagement_velocity: str  # "fast", "moderate", "slow"
    best_contact_times: List[int]  # Hours of day (0-23)
    message_length_preference: str  # "brief", "detailed"


@dataclass
class SequenceOptimization:
    """Optimized sequence timing based on behavioral patterns"""

    day_3: int
    day_7: int
    day_14: int
    day_30: int
    channel_sequence: List[str]  # Ordered list of channels to use
