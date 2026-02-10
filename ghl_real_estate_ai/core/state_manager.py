"""Session state manager for AgentForge with persistence."""
from __future__ import annotations

import os
import shelve
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentState:
    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": meta or {},
        })
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "memory": self.memory,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        return cls(
            session_id=data["session_id"],
            messages=data.get("messages", []),
            memory=data.get("memory", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else datetime.utcnow(),
        )


class StateManager:
    """Persistent storage for AgentState using shelve."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        default_path = Path(".agent_state") / "agent_state.db"
        path = Path(db_path or os.getenv("AGENT_STATE_DB", str(default_path)))
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = str(path)
        self._lock = threading.Lock()

    def load_state(self, session_id: str) -> AgentState:
        with self._lock:
            with shelve.open(self._db_path) as db:
                data = db.get(session_id)
                if data:
                    return AgentState.from_dict(data)
        return AgentState(session_id=session_id)

    def save_state(self, state: AgentState) -> None:
        state.updated_at = datetime.utcnow()
        with self._lock:
            with shelve.open(self._db_path, writeback=False) as db:
                db[state.session_id] = state.to_dict()

    def delete_state(self, session_id: str) -> None:
        with self._lock:
            with shelve.open(self._db_path, writeback=False) as db:
                if session_id in db:
                    del db[session_id]


_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
