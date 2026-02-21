"""
Temperature Prediction Engine for predicting lead temperature changes.
"""

from typing import Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class TemperaturePredictionEngine:
    """Predicts lead temperature changes and provides early warnings"""

    def __init__(self):
        self.temperature_history: Dict[str, List[float]] = {}

    async def predict_temperature_trend(self, lead_id: str, current_scores: Dict[str, float]) -> Dict:
        """Predict lead temperature trend and provide early warnings"""

        # Store current temperature score
        current_temp = (current_scores.get("frs_score", 0) + current_scores.get("pcs_score", 0)) / 2

        if lead_id not in self.temperature_history:
            self.temperature_history[lead_id] = []

        self.temperature_history[lead_id].append(current_temp)

        # Keep only last 10 interactions for trend analysis
        if len(self.temperature_history[lead_id]) > 10:
            self.temperature_history[lead_id] = self.temperature_history[lead_id][-10:]

        history = self.temperature_history[lead_id]

        # Predict trend
        diff = 0
        if len(history) < 2:
            trend = "stable"
            confidence = 0.5
        else:
            # Simple linear trend analysis
            recent_avg = sum(history[-3:]) / min(3, len(history))
            older_avg = sum(history[:-3]) / max(1, len(history) - 3) if len(history) > 3 else recent_avg

            diff = recent_avg - older_avg

            if abs(diff) < 5:
                trend = "stable"
                confidence = 0.8
            elif diff > 0:
                trend = "heating_up"
                confidence = 0.7
            else:
                trend = "cooling_down"
                confidence = 0.7

        # Generate early warning if cooling
        early_warning = None
        if trend == "cooling_down" and current_temp > 40:
            early_warning = {
                "type": "temperature_declining",
                "urgency": "medium",
                "recommendation": "Immediate engagement recommended - lead showing signs of disengagement",
                "suggested_action": "Schedule call within 24 hours",
            }

        return {
            "current_temperature": current_temp,
            "trend": trend,
            "confidence": confidence,
            "early_warning": early_warning,
            "prediction_next_interaction": max(0, current_temp + (diff * 1.5)),
        }

    def get_temperature_history(self, lead_id: str) -> List[float]:
        """Get the temperature history for a lead."""
        return self.temperature_history.get(lead_id, []).copy()

    def clear_history(self, lead_id: str) -> bool:
        """Clear temperature history for a lead."""
        if lead_id in self.temperature_history:
            del self.temperature_history[lead_id]
            return True
        return False

    def get_all_tracked_leads(self) -> List[str]:
        """Get list of all lead IDs being tracked."""
        return list(self.temperature_history.keys())

    def calculate_temperature(self, frs_score: float, pcs_score: float) -> float:
        """Calculate temperature from FRS and PCS scores."""
        return (frs_score + pcs_score) / 2

    def classify_temperature(self, temperature: float) -> str:
        """Classify temperature into Hot/Warm/Cold categories."""
        if temperature >= 80:
            return "Hot"
        elif temperature >= 40:
            return "Warm"
        else:
            return "Cold"
