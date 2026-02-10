"""Agent capability registry for dynamic agent routing and lifecycle management."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class AgentStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


@dataclass
class AgentCapability:
    name: str
    description: str
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    role: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.ACTIVE
    owner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = field(default_factory=dict)


class AgentRegistry:
    """In-memory agent registry with lifecycle management."""

    def __init__(self) -> None:
        self._agents: Dict[str, AgentRecord] = {}

    def register(self, record: AgentRecord) -> None:
        record.updated_at = datetime.utcnow()
        self._agents[record.agent_id] = record

    def list_agents(self, status: Optional[AgentStatus] = None) -> List[AgentRecord]:
        if status is None:
            return list(self._agents.values())
        return [agent for agent in self._agents.values() if agent.status == status]

    def find_by_capability(self, capability_name: str) -> List[AgentRecord]:
        return [
            agent for agent in self._agents.values()
            if any(cap.name == capability_name for cap in agent.capabilities)
        ]

    def list_capabilities(self) -> List[str]:
        capabilities = set()
        for agent in self._agents.values():
            for cap in agent.capabilities:
                capabilities.add(cap.name)
        return sorted(capabilities)

    def update_metadata(self, agent_id: str, metadata: Dict[str, str]) -> None:
        agent = self._agents.get(agent_id)
        if not agent:
            return
        agent.metadata.update(metadata)
        agent.updated_at = datetime.utcnow()

    def deprecate(self, agent_id: str, reason: Optional[str] = None) -> None:
        agent = self._agents.get(agent_id)
        if not agent:
            return
        agent.status = AgentStatus.DEPRECATED
        agent.updated_at = datetime.utcnow()
        if reason:
            agent.metadata["deprecation_reason"] = reason

    def disable(self, agent_id: str, reason: Optional[str] = None) -> None:
        agent = self._agents.get(agent_id)
        if not agent:
            return
        agent.status = AgentStatus.DISABLED
        agent.updated_at = datetime.utcnow()
        if reason:
            agent.metadata["disabled_reason"] = reason

    def get(self, agent_id: str) -> Optional[AgentRecord]:
        return self._agents.get(agent_id)


_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    return _registry
