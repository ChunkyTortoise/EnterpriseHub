"""Core module for AgentForge.

This module provides the fundamental building blocks for agent orchestration:
- BaseAgent: Abstract base class for all agents
- AgentInput/AgentOutput: Data models for agent I/O
- Type definitions: Enums and shared types
- DAG: Directed Acyclic Graph for workflow definition
- Exceptions: Custom exceptions for DAG operations
- Engine: Async execution engine
- Registry: Agent and tool registration
"""

from agentforge.core.agent import (
    Agent,
    AgentExecutionError,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from agentforge.core.dag import (
    DAG,
    DAGConfig,
)
from agentforge.core.engine import (
    Engine,
    ExecutionConfig,
    ExecutionEngine,
    ExecutionResult,
)
from agentforge.core.exceptions import (
    CycleDetectedError,
    DAGValidationError,
    ExecutionError,
    NodeNotFoundError,
)
from agentforge.core.types import (
    AgentConfig,
    AgentStatus,
    ExecutionContext,
    Message,
    MessageRole,
    Priority,
    ToolCall,
    ToolResult,
)

__all__ = [
    # Agent
    "Agent",
    "BaseAgent",
    "AgentInput",
    "AgentOutput",
    "AgentExecutionError",
    # DAG
    "DAG",
    "DAGConfig",
    # Engine
    "Engine",
    "ExecutionConfig",
    "ExecutionEngine",
    "ExecutionResult",
    # Exceptions
    "CycleDetectedError",
    "DAGValidationError",
    "ExecutionError",
    "NodeNotFoundError",
    # Types
    "AgentConfig",
    "AgentStatus",
    "ExecutionContext",
    "Message",
    "MessageRole",
    "Priority",
    "ToolCall",
    "ToolResult",
]
