"""A2A (Agent-to-Agent) protocol support for AgentForge.

This module provides support for the A2A protocol, enabling
interoperability with other agent frameworks.

Provides:
- AgentCard for agent discovery
- A2AProtocolSupport for optional A2A integration
"""

from typing import Any

from pydantic import BaseModel


class AgentCard(BaseModel):
    """Agent Card for A2A protocol discovery.

    Describes an agent's capabilities for discovery and
    capability negotiation in the A2A protocol.

    Attributes:
        name: Human-readable name for the agent.
        description: Brief description of the agent's purpose.
        version: Agent version string.
        capabilities: List of capability names offered.
        endpoints: API endpoints for the agent.
        metadata: Additional metadata.
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    capabilities: list[str] = []
    endpoints: dict[str, str] = {}
    metadata: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        """Export to JSON for /.well-known/agent.json.

        Returns:
            Dictionary representation of the agent card.
        """
        return self.model_dump()


class A2AProtocolSupport:
    """A2A protocol support (optional dependency).

    Provides basic A2A protocol functionality for agent
    discovery and task handling.

    Example:
        ```python
        card = AgentCard(
            name="MyAgent",
            description="A helpful assistant",
            capabilities=["search", "analyze"],
        )
        a2a = A2AProtocolSupport(agent_card=card)

        # Get agent card for discovery
        agent_json = a2a.get_agent_card()

        # Handle an A2A task
        result = await a2a.handle_task({"action": "search", "query": "hello"})
        ```
    """

    def __init__(self, agent_card: AgentCard) -> None:
        """Initialize A2A protocol support.

        Args:
            agent_card: The agent card describing this agent.
        """
        self.agent_card = agent_card

    def get_agent_card(self) -> dict[str, Any]:
        """Get the agent card for discovery.

        Returns:
            The agent card as a dictionary.
        """
        return self.agent_card.to_json()

    async def handle_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Handle an A2A task.

        Args:
            task: The task to handle.

        Returns:
            Task result dictionary.
        """
        # Stub - would integrate with a2a-python if available
        return {"status": "not_implemented"}


__all__ = ["AgentCard", "A2AProtocolSupport"]
