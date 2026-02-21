"""
Configuration classes for the Lead Bot module.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


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


@dataclass
class LeadBotConfig:
    """Configuration for Lead Bot enhanced features"""

    enable_predictive_analytics: bool = False
    enable_behavioral_optimization: bool = False
    enable_personality_adaptation: bool = False
    enable_track3_intelligence: bool = False
    enable_bot_intelligence: bool = False

    # Performance settings
    default_sequence_timing: bool = True
    personality_detection_enabled: bool = True
    jorge_handoff_enabled: bool = True


@dataclass
class LeadProcessingResult:
    """Result from processing a lead conversation"""

    conversation_id: str
    response_content: str
    current_step: str
    engagement_status: str
    lead_id: str
    temperature: Optional[float] = None
    handoff_signals: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    ab_test: Optional[Dict[str, Any]] = None
    sentiment_result: Optional[Any] = None
    churn_assessment: Optional[Dict[str, Any]] = None
    composite_score: Optional[Dict[str, Any]] = None
