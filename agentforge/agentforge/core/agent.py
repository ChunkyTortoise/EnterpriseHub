"""Base agent definitions for AgentForge.

This module provides the abstract base class for all agents and the
input/output models that define the agent interface.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from agentforge.core.types import (
    AgentConfig,
    AgentStatus,
    ExecutionContext,
    Message,
    ToolCall,
    ToolResult,
)


class AgentInput(BaseModel):
    """Input model for agent execution.

    Defines the data structure passed to an agent when invoking its
    execute method. Contains conversation history, execution context,
    and available tools.

    Attributes:
        messages: List of conversation messages forming the input context.
        context: Execution context with session info, tracing, and metadata.
        tools: List of tool names available for this execution.
        tool_results: Results from previous tool calls in this session.
        stream: Whether to stream the response incrementally.
    """

    messages: list[Message] = Field(default_factory=list)
    context: ExecutionContext = Field(default_factory=ExecutionContext)
    tools: list[str] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    stream: bool = False


class AgentOutput(BaseModel):
    """Output model from agent execution.

    Defines the structure of data returned by an agent after processing.
    Can contain text content, tool calls to execute, or error information.

    Attributes:
        content: The text response from the agent.
        tool_calls: List of tool calls the agent wants to execute.
        error: Error message if execution failed.
        status: Current status of the agent after execution.
        metadata: Additional metadata about the execution.
        usage: Token usage statistics (prompt_tokens, completion_tokens).
        finish_reason: Reason for completion (stop, tool_calls, length, error).
    """

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    error: str | None = None
    status: AgentStatus = AgentStatus.COMPLETED
    metadata: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, int] = Field(default_factory=dict)
    finish_reason: str | None = None


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Defines the interface that all agent implementations must follow.
    Agents are the core execution units in AgentForge, responsible for
    processing inputs and producing outputs, potentially using tools.

    Subclasses must implement the execute() method to define their
    specific behavior.

    Attributes:
        agent_id: Unique identifier for this agent instance.
        config: Configuration for this agent.
        status: Current execution status.

    Example:
        ```python
        class MyAgent(BaseAgent):
            async def execute(self, input: AgentInput) -> AgentOutput:
                # Process input and return output
                return AgentOutput(content="Hello, world!")
        ```
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            config: Agent configuration. Uses defaults if not provided.
            agent_id: Unique identifier. Auto-generated if not provided.
        """
        self.agent_id = agent_id or str(uuid4())
        self.config = config or AgentConfig(name=self.__class__.__name__)
        self._status = AgentStatus.IDLE

    @property
    def status(self) -> AgentStatus:
        """Get the current agent status."""
        return self._status

    @status.setter
    def status(self, value: AgentStatus) -> None:
        """Set the agent status."""
        self._status = value

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the agent's primary logic.

        This method must be implemented by all subclasses. It receives
        an AgentInput, processes it according to the agent's logic,
        and returns an AgentOutput.

        Args:
            input: The input data for the agent to process.

        Returns:
            AgentOutput containing the results of execution.

        Raises:
            AgentExecutionError: If execution fails.
        """
        ...

    async def __call__(self, input: AgentInput) -> AgentOutput:
        """Allow agent to be called as a function.

        This provides a convenient way to invoke agents:
        output = await my_agent(input)

        Args:
            input: The input data for the agent to process.

        Returns:
            AgentOutput containing the results of execution.
        """
        return await self.execute(input)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id}, status={self.status.value})"


# Type alias for agent classes
Agent = BaseAgent


class AgentExecutionError(Exception):
    """Exception raised when agent execution fails.

    Attributes:
        agent_id: ID of the agent that failed.
        message: Error description.
        cause: Underlying exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.agent_id = agent_id
        self.cause = cause


__all__ = [
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    "Agent",
    "AgentExecutionError",
]
