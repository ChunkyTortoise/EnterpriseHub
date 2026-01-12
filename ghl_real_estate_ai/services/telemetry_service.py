"""
Telemetry Service for Behavioral Intelligence.
Tracks lead interactions with the portal to identify intent.
"""
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, List

class TelemetryService:
    def __init__(self, data_dir: str = "data/telemetry"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def record_interaction(self, lead_id: str, action: str, metadata: Dict[str, Any]):
        """Record a lead's interaction (view, save, chat)."""
        file_path = self.data_dir / f"{lead_id}.json"
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "metadata": metadata
        }
        
        history = self.get_lead_history(lead_id)
        history.append(interaction)
        
        with open(file_path, "w") as f:
            json.dump(history, f, indent=2)

    def get_lead_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """Retrieve interaction history for a lead."""
        file_path = self.data_dir / f"{lead_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return []

    def get_intent_score(self, lead_id: str) -> int:
        """Calculate intent score based on telemetry."""
        history = self.get_lead_history(lead_id)
        if not history:
            return 0
            
        score = 0
        for interaction in history:
            if interaction["action"] == "save":
                score += 20
            elif interaction["action"] == "chat":
                score += 15
            elif interaction["action"] == "view":
                score += 5
        return min(100, score)
