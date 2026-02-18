"""A2A (Agent-to-Agent) protocol types for AgentForge.

This module provides the core types for the A2A protocol v0.3 (July 2025),
standardized by Google under the Linux Foundation for agent-to-agent
discovery and task exchange.

Reference: https://github.com/google/A2A

Provides:
- AgentCard for agent discovery at /.well-known/agent.json
- Task lifecycle management (submitted, working, completed, failed, cancelled)
- JSON-RPC 2.0 message wrappers for protocol communication
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    """A capability offered by an agent.

    Describes a specific function or skill that an agent can perform,
    including the expected input and output schemas.

    Attributes:
        name: Unique identifier for this capability.
        description: Human-readable description of what this capability does.
        input_schema: JSON Schema describing expected input parameters.
        output_schema: JSON Schema describing the output structure.
    """

    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class AgentCard(BaseModel):
    """Agent Card for A2A protocol discovery.

    Served at /.well-known/agent.json for agent discovery. Describes
    an agent's identity, capabilities, and communication endpoints.

    Attributes:
        id: Unique identifier for this agent.
        name: Human-readable name for the agent.
        description: Brief description of the agent's purpose.
        version: Agent version string (semver recommended).
        capabilities: List of capabilities this agent offers.
        endpoints: API endpoints for interacting with the agent.
        metadata: Additional metadata (e.g., owner, documentation).
        created_at: ISO 8601 timestamp of agent creation.

    Example:
        ```python
        card = AgentCard(
            id="my-agent-001",
            name="WeatherAgent",
            description="Provides weather forecasts",
            capabilities=[
                AgentCapability(
                    name="get_forecast",
                    description="Get weather forecast for a location",
                    input_schema={"type": "object", "properties": {"location": {"type": "string"}}}
                )
            ],
            endpoints={"tasks": "/a2a", "card": "/.well-known/agent.json"}
        )
        ```
    """

    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    capabilities: list[AgentCapability] = Field(default_factory=list)
    endpoints: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> dict[str, Any]:
        """Export to JSON for /.well-known/agent.json.

        Returns:
            Dictionary representation of the agent card.
        """
        return self.model_dump()


class TaskStatus(str, Enum):
    """Enumeration of possible task states in A2A protocol.

    Attributes:
        SUBMITTED: Task has been submitted but not yet started.
        WORKING: Task is currently being processed.
        COMPLETED: Task has completed successfully.
        FAILED: Task execution encountered an error.
        CANCELLED: Task was cancelled before completion.
    """

    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """An A2A task representing a unit of work for an agent.

    Tasks are the primary mechanism for requesting work from agents.
    They track the full lifecycle from submission to completion.

    Attributes:
        id: Unique identifier for this task (auto-generated UUID).
        agent_id: ID of the agent processing this task.
        status: Current status of the task.
        input: Input data for the task (capability-specific).
        output: Output data from task execution (None until completed).
        error: Error message if task failed.
        created_at: ISO 8601 timestamp of task creation.
        updated_at: ISO 8601 timestamp of last update.
        metadata: Additional task metadata.

    Example:
        ```python
        task = Task(
            agent_id="weather-agent",
            input={"location": "San Francisco"},
            metadata={"capability": "get_forecast"}
        )
        ```
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    status: TaskStatus = TaskStatus.SUBMITTED
    input: dict[str, Any] = Field(default_factory=dict)
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow().isoformat()


class TaskUpdate(BaseModel):
    """Update to a task's state or output.

    Used for partial updates to task status, output, or metadata
    without replacing the entire task object.

    Attributes:
        task_id: ID of the task to update.
        status: New status (optional).
        output: Output data to set (optional).
        error: Error message to set (optional).
        metadata: Metadata to merge (optional).
    """

    task_id: str
    status: Optional[TaskStatus] = None
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class A2AMessage(BaseModel):
    """A2A protocol message using JSON-RPC 2.0 format.

    All A2A communication uses JSON-RPC 2.0 for consistency
    and interoperability with other JSON-RPC systems.

    Attributes:
        jsonrpc: Protocol version (always "2.0").
        method: The method to invoke (e.g., "tasks/send").
        params: Parameters for the method call.
        id: Optional request ID for correlation.

    Example:
        ```python
        message = A2AMessage(
            method="tasks/send",
            params={"capability": "get_forecast", "input": {"location": "NYC"}},
            id="req-123"
        )
        ```
    """

    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None


class A2AResponse(BaseModel):
    """A2A protocol response using JSON-RPC 2.0 format.

    Response to an A2AMessage, following JSON-RPC 2.0 conventions.
    Either 'result' or 'error' will be present, never both.

    Attributes:
        jsonrpc: Protocol version (always "2.0").
        result: The result of the method call (on success).
        error: Error object with 'code' and 'message' (on failure).
        id: Request ID from the corresponding message.

    Example:
        ```python
        # Success response
        response = A2AResponse(
            id="req-123",
            result={"forecast": "Sunny, 72°F"}
        )

        # Error response
        response = A2AResponse(
            id="req-123",
            error={"code": -32602, "message": "Invalid params"}
        )
        ```
    """

    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None
    id: Optional[str] = None


# JSON-RPC 2.0 error codes
class A2AErrorCode:
    """Standard JSON-RPC 2.0 error codes for A2A protocol."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # A2A-specific error codes (application defined, start at -32000)
    TASK_NOT_FOUND = -32001
    CAPABILITY_NOT_FOUND = -32002
    TASK_EXECUTION_FAILED = -32003
    AGENT_UNAVAILABLE = -32004


__all__ = [
    "AgentCapability",
    "AgentCard",
    "TaskStatus",
    "Task",
    "TaskUpdate",
    "A2AMessage",
    "A2AResponse",
    "A2AErrorCode",
]
