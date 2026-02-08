"""
Adaptive UI Service - Vanguard 2
Manages stress-responsive dashboard states (Calm, Focused, Crisis).
"""

import logging
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DashboardMode(Enum):
    CALM = "Calm"
    FOCUSED = "Focused"
    CRISIS = "Crisis"


class AdaptiveUIService:
    def __init__(self):
        self.current_mode = DashboardMode.CALM
        self.stress_level = 0.0  # 0-10

    def analyze_stress(self, acoustic_features: Dict[str, Any], sentiment_score: float) -> DashboardMode:
        """
        Vanguard 2 logic:
        1. Extract acoustic features: speech rate, pitch variance, pause duration
        2. IF stress > 7 AND volatility > 6 -> "Crisis Mode"
        """
        # Simplified stress model
        speech_rate = acoustic_features.get("speech_rate", 1.0)
        pitch_variance = acoustic_features.get("pitch_variance", 0.1)

        # Stress level increases with speech rate and pitch variance, and negative sentiment
        stress_score = (speech_rate * 2) + (pitch_variance * 20) + (abs(sentiment_score) * 5)
        self.stress_level = min(10.0, stress_score)

        if self.stress_level > 7:
            self.current_mode = DashboardMode.CRISIS
        elif self.stress_level > 4:
            self.current_mode = DashboardMode.FOCUSED
        else:
            self.current_mode = DashboardMode.CALM

        logger.info(f"UI State: {self.current_mode.value} (Stress Level: {self.stress_level:.1f})")
        return self.current_mode

    def get_prescriptive_recommendation(self, mode: DashboardMode) -> str:
        """Surfaces decision recommendations based on UI mode."""
        if mode == DashboardMode.CRISIS:
            return "🛑 ESCALATE: Stalled lead needs immediate attention. Use 'Emergency Credit' template."
        elif mode == DashboardMode.FOCUSED:
            return "💡 ACTION: Contact Sarah Martinez (85% close rate). Use 'Warm Reframe' SMS."
        else:
            return "✅ STABLE: 12 KPIs active. Review weekly pipeline report."


_adaptive_ui_service = None


def get_adaptive_ui_service() -> AdaptiveUIService:
    global _adaptive_ui_service
    if _adaptive_ui_service is None:
        _adaptive_ui_service = AdaptiveUIService()
    return _adaptive_ui_service
