"""
Shared Blackboard for Agent Swarm.
Enables agents to share context, insights, and state.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

class SharedBlackboard:
    """
    A centralized data store for agent collaboration.
    Agents can post insights, retrieve shared data, and track progress.
    """
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        
    def post(self, key: str, value: Any, agent_id: str):
        """Post a piece of information to the blackboard."""
        self.data[key] = value
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "key": key,
            "value": value
        })
        
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve information from the blackboard."""
        return self.data.get(key, default)
        
    def get_full_context(self) -> str:
        """Summarize the current blackboard state for agent consumption."""
        summary = f"Trace ID: {self.trace_id}\n"
        summary += f"Started at: {self.created_at.isoformat()}\n\n"
        summary += "Current Insights:\n"
        for key, value in self.data.items():
            summary += f"- {key}: {value}\n"
        return summary
