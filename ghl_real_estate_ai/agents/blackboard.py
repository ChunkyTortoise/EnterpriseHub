"""
Shared Blackboard for Agent Swarm.
A centralized context store for agents to share state and results.
"""

import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


class SharedBlackboard:
    """
    Thread-safe blackboard for shared agent context.
    Implemented as a singleton to sync state between API and Swarm.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SharedBlackboard, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._data: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._initialized = True

    def write(self, key: str, value: Any, agent_name: str):
        """Write data to the blackboard."""
        with self._lock:
            self._data[key] = value
            entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "key": key,
                "value": str(value)[:500],  # Truncate large values for history
            }
            self._history.append(entry)

    def read(self, key: str) -> Optional[Any]:
        """Read data from the blackboard."""
        with self._lock:
            return self._data.get(key)

    def get_full_context(self) -> str:
        """Returns a string representation of all current data for LLM context."""
        with self._lock:
            return json.dumps(self._data, indent=2)

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the change history of the blackboard."""
        with self._lock:
            return self._history.copy()

    def log_debate(self, lead_id: str, agent_name: str, thought: str, action_proposed: str, confidence: float):
        """Phase 7: Log granular agent reasoning for the explainability dashboard."""
        with self._lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "lead_id": lead_id,
                "agent": agent_name,
                "thought": thought,
                "action_proposed": action_proposed,
                "confidence": confidence,
            }
            # We can store this in a special 'debates' list or write to a dedicated DB table
            debates = self._data.get("agent_debates", [])
            debates.append(entry)
            self._data["agent_debates"] = debates[-50:]  # Keep last 50 for live view
