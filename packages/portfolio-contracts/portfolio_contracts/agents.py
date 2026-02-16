"""Agent contracts — shared across orchestration products."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Lifecycle status of an agent action."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentAction(BaseModel):
    """A recorded action taken by an agent."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    action_type: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] | None = None
    status: AgentStatus = AgentStatus.IDLE
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
