"""
Shared Blackboard for Agent Swarm.
A centralized context store for agents to share state and results.
"""
import json
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime

class SharedBlackboard:
    """
    Thread-safe blackboard for shared agent context.
    """
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def write(self, key: str, value: Any, agent_name: str):
        """Write data to the blackboard."""
        with self._lock:
            self._data[key] = value
            entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "key": key,
                "value": str(value)[:500]  # Truncate large values for history
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