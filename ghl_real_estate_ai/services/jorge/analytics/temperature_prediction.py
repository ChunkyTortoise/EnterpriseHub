"""Lead temperature trend prediction and early warning system.

This module tracks lead temperature history and predicts future trends
to enable proactive engagement before leads cool down.

WARNING: Temperature history is stored in volatile memory and will be lost on restart.
For production deployments, configure Redis persistence to retain trend data across restarts.
See improvement roadmap item P0-3 for Redis migration guide.
"""

from typing import Dict, List


class TemperaturePredictionEngine:
    """Predicts lead temperature changes and provides early warnings

    WARNING: Temperature history is stored in volatile memory and will be lost on restart.
    For production deployments, configure Redis persistence to retain trend data across restarts.
    See improvement roadmap item P0-3 for Redis migration guide.
    """

    MAX_LEADS_IN_MEMORY = 10000  # Prevent unbounded memory growth

    def __init__(self):
        self.temperature_history: Dict[str, List[float]] = {}

    async def predict_temperature_trend(self, lead_id: str, current_scores: Dict[str, float]) -> Dict:
        """Predict lead temperature trend and provide early warnings"""

        # Store current temperature score
        current_temp = (current_scores.get("frs_score", 0) + current_scores.get("pcs_score", 0)) / 2

        if lead_id not in self.temperature_history:
            # Basic memory protection: if we're at capacity, evict oldest lead
            if len(self.temperature_history) >= self.MAX_LEADS_IN_MEMORY:
                # Remove the first (oldest) lead
                oldest_lead = next(iter(self.temperature_history))
                del self.temperature_history[oldest_lead]

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
