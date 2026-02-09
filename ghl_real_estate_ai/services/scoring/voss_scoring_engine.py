"""
Voss Scoring Engine - Financial Readiness & Psychological Commitment
Implements the proprietary scoring formulas from the 2026 Strategic Roadmap.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class VossScoringEngine:
    """
    Elite scoring engine for high-stakes real estate qualification.

    Metrics:
    - FRS (Financial Readiness Score): Probability of transaction completion.
    - PCS (Psychological Commitment Score): Strength of emotional motivation.
    """

    def calculate_frs(
        self, motivation: float, timeline: float, condition_acceptance: float, price_realism: float
    ) -> float:
        """
        Formula: (Motivation × 0.35) + (Timeline × 0.30) + (Condition_Acceptance × 0.20) + (Price_Realism × 0.15)
        Scores 0-100.
        """
        frs = (motivation * 0.35) + (timeline * 0.30) + (condition_acceptance * 0.20) + (price_realism * 0.15)
        return round(min(100.0, max(0.0, frs)), 2)

    def calculate_pcs(
        self,
        response_velocity: float,  # 0-100 based on time
        message_length: float,  # 0-100 based on word count
        question_depth: float,  # 0-100 based on specificity
        objection_handling: float,  # 0-100 based on overcome speed
        call_acceptance: float,
    ) -> float:  # 0 or 100
        """
        Formula: ∑(Signal_Score × Weight)
        Weights: Velocity (20%), Length (15%), Depth (20%), Objections (25%), Call (20%)
        """
        pcs = (
            (response_velocity * 0.20)
            + (message_length * 0.15)
            + (question_depth * 0.20)
            + (objection_handling * 0.25)
            + (call_acceptance * 0.20)
        )
        return round(min(100.0, max(0.0, pcs)), 2)

    def get_jorge_qualification_pillars(self, nlp_insights: Dict[str, Any]) -> Dict[str, float]:
        """
        Extracts pillar scores (0-100) from NLP sentiment and linguistic markers.
        """
        # Simulated extraction based on linguistic markers from roadmap
        motivation = 50.0
        if any(
            word in nlp_insights.get("text", "").lower()
            for word in ["must", "need", "relocating", "divorce", "probate"]
        ):
            motivation = 90.0
        elif "curious" in nlp_insights.get("text", "").lower():
            motivation = 30.0

        timeline = 50.0
        if "30 days" in nlp_insights.get("text", "").lower() or "fast" in nlp_insights.get("text", "").lower():
            timeline = 95.0

        return {
            "motivation": motivation,
            "timeline": timeline,
            "condition_acceptance": nlp_insights.get("condition_score", 50.0),
            "price_realism": nlp_insights.get("price_realism_score", 50.0),
        }


_voss_scoring = None


def get_voss_scoring_engine() -> VossScoringEngine:
    global _voss_scoring
    if _voss_scoring is None:
        _voss_scoring = VossScoringEngine()
    return _voss_scoring
