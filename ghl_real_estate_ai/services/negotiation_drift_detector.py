"""
Negotiation Drift Detector
Analyzes behavioral patterns (latency, hedging, sentiment shift) to detect flexibility.
"""
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NegotiationDriftDetector:
    def __init__(self):
        # Keywords indicating flexibility or hedging (Voss/Negotiation Science)
        self.hedging_terms = [
            r"maybe", r"possibly", r"potentially", r"might", r"could", 
            r"perhaps", r"think", r"if", r"flexible", r"open to",
            r"negotiable", r"depends", r"consider"
        ]
        
    def analyze_drift(self, 
                      message: str, 
                      response_latency_seconds: float = 0,
                      previous_sentiment: float = 0.0) -> Dict[str, Any]:
        """
        Calculates a 'Drift Score' (0.0 to 1.0) indicating how much a lead
        is drifting from their initial firm position.
        """
        # 1. Hedge Detection
        hedge_count = 0
        for term in self.hedging_terms:
            if re.search(term, message, re.IGNORECASE):
                hedge_count += 1
        
        # 2. Latency Factor
        # High latency on price questions often indicates internal debate/flexibility
        latency_factor = min(1.0, response_latency_seconds / 3600) # Capped at 1 hour
        
        # 3. Linguistic Complexity
        # Longer, more explanatory responses often indicate a desire to be understood (flexibility)
        complexity_factor = min(1.0, len(message.split()) / 100)
        
        # Calculate Drift Score
        # Weighting: Hedging (50%), Latency (30%), Complexity (20%)
        drift_score = (hedge_count * 0.1) + (latency_factor * 0.3) + (complexity_factor * 0.2)
        drift_score = min(1.0, drift_score)
        
        return {
            "drift_score": drift_score,
            "hedge_count": hedge_count,
            "latency_factor": latency_factor,
            "is_drifting": drift_score > 0.4,
            "recommendation": self._get_drift_recommendation(drift_score)
        }

    def _get_drift_recommendation(self, score: float) -> str:
        if score > 0.7:
            return "Lead is highly flexible. Push for commitment (Voss Direct Challenge)."
        elif score > 0.4:
            return "Lead is showing internal drift. Use Labeling to confirm flexibility."
        else:
            return "Lead is maintaining firm position. Use Mirroring to build rapport."

_drift_detector = None

def get_drift_detector() -> NegotiationDriftDetector:
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = NegotiationDriftDetector()
    return _drift_detector
