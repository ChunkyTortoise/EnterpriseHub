"""Core type definitions for AgentForge.

This module defines the fundamental types, enums, and protocols used
throughout the framework. All types are designed to be Pydantic-compatible
for validation and serialization.
"""

from enum import Enum, StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    """Enumeration of possible agent execution states.

    Attributes:
        IDLE: Agent is not currently executing any task.
        RUNNING: Agent is actively processing a request.
        COMPLETED: Agent has successfully finished execution.
        FAILED: Agent execution encountered an error.
    """

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(StrEnum):
    """Enumeration of message roles in agent conversations.

    Attributes:
        SYSTEM: System-level instructions or context.
        USER: Input from a human user.
        ASSISTANT: Response from an AI assistant/agent.
        TOOL: Output from a tool execution.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Priority(int, Enum):
    """Task priority levels for agent scheduling.

    Attributes:
        LOW: Background or deferred tasks.
        NORMAL: Standard priority for most tasks.
        HIGH: Important tasks requiring prompt attention.
        CRITICAL: Urgent tasks that must be processed immediately.
    """

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class Message(BaseModel):
    """A single message in an agent conversation.

    Attributes:
        role: The role of the message sender.
        content: The text content of the message.
        name: Optional name identifier for the sender.
        tool_call_id: Optional ID linking to a tool call.
        metadata: Additional metadata attached to the message.
    """

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Represents a tool/function call request from an agent.

    Attributes:
        id: Unique identifier for this tool call.
        name: Name of the tool to invoke.
        arguments: Arguments to pass to the tool (as JSON-serializable dict).
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result from a tool execution.

    Attributes:
        tool_call_id: ID of the tool call this result corresponds to.
        content: The output content from the tool.
        is_error: Whether the tool execution resulted in an error.
        metadata: Additional metadata about the execution.
    """

    tool_call_id: str
    content: str
    is_error: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionContext(BaseModel):
    """Shared execution context passed through agent workflows.

    Attributes:
        session_id: Unique identifier for the conversation/session.
        parent_agent_id: ID of the parent agent if this is a sub-agent.
        trace_id: OpenTelemetry trace ID for observability.
        priority: Task priority level.
        timeout_seconds: Maximum execution time allowed.
        metadata: Arbitrary context data for custom use cases.
    """

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_agent_id: str | None = None
    trace_id: str | None = None
    priority: Priority = Priority.NORMAL
    timeout_seconds: float = 300.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for an agent instance.

    Attributes:
        name: Human-readable name for the agent.
        description: Brief description of the agent's purpose.
        model: LLM model identifier (e.g., "gpt-4", "claude-3-opus").
        temperature: Sampling temperature for LLM responses.
        max_tokens: Maximum tokens in LLM responses.
        system_prompt: System prompt for the agent.
        tools: List of tool names available to this agent.
        max_iterations: Maximum reasoning iterations allowed.
        timeout_seconds: Maximum execution time per request.
    """

    name: str
    description: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str | None = None
    tools: list[str] = Field(default_factory=list)
    max_iterations: int = 10
    timeout_seconds: float = 300.0


# Type aliases for clarity
MessageHistory = list[Message]
ToolRegistry = dict[str, Any]


__all__ = [
    "AgentStatus",
    "MessageRole",
    "Priority",
    "Message",
    "ToolCall",
    "ToolResult",
    "ExecutionContext",
    "AgentConfig",
    "MessageHistory",
    "ToolRegistry",
]
