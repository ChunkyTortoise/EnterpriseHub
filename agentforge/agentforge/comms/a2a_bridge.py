"""A2A (Agent-to-Agent) protocol bridge for AgentForge.

This module provides the bridge between AgentForge agents and the A2A protocol,
enabling seamless exposure of agents as A2A-compatible services and
communication with remote A2A agents.

Provides:
- A2ABridge for converting agents to A2A servers and clients
- Agent-to-Card conversion utilities
- Capability mapping from agent tools
"""

from typing import Any, Optional

from ..core.agent import AgentInput, AgentOutput, BaseAgent
from .a2a_client import A2AClient
from .a2a_server import A2AServer
from .a2a_types import AgentCapability, AgentCard


class A2ABridge:
    """Bridge between AgentForge agents and A2A protocol.

    Provides static methods for converting between AgentForge and A2A types,
    and creating A2A servers/clients for agent communication.

    Example:
        ```python
        # Expose an agent as A2A server
        server = A2ABridge.create_server(my_agent, "https://my-agent.example.com")

        # Create client to communicate with remote agent
        client = A2ABridge.create_client("https://other-agent.example.com")
        card = await client.discover_agent()
        task = await client.send_task("analyze", {"data": "..."})
        ```
    """

    @staticmethod
    def agent_to_card(agent: BaseAgent, base_url: str) -> AgentCard:
        """Convert an AgentForge agent to an A2A Agent Card.

        Extracts capabilities from the agent's tools and configuration.

        Args:
            agent: The AgentForge agent to convert.
            base_url: The base URL where this agent will be served.

        Returns:
            An AgentCard describing the agent.
        """
        capabilities = []

        # Convert tools to capabilities
        if hasattr(agent, "tools") and agent.tools:
            for tool in agent.tools:
                cap = A2ABridge._tool_to_capability(tool)
                capabilities.append(cap)

        # Add default capability if no tools
        if not capabilities:
            description = ""
            if hasattr(agent, "config") and agent.config:
                description = agent.config.description or ""
            elif hasattr(agent, "instructions"):
                description = str(agent.instructions)[:200] if agent.instructions else ""

            capabilities.append(
                AgentCapability(
                    name="execute",
                    description=description or "Execute the agent",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Input message"}
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "error": {"type": "string"},
                        },
                    },
                )
            )

        # Get agent name and description
        name = "UnknownAgent"
        description = ""
        if hasattr(agent, "config") and agent.config:
            name = agent.config.name
            description = agent.config.description
        elif hasattr(agent, "agent_id"):
            name = agent.agent_id

        return AgentCard(
            id=getattr(agent, "agent_id", name),
            name=name,
            description=description,
            version="1.0.0",
            capabilities=capabilities,
            endpoints={
                "tasks": "/a2a",
                "card": "/.well-known/agent.json",
            },
            metadata={
                "framework": "agentforge",
                "base_url": base_url,
            },
        )

    @staticmethod
    def _tool_to_capability(tool: Any) -> AgentCapability:
        """Convert a tool to an A2A capability.

        Args:
            tool: The tool to convert.

        Returns:
            An AgentCapability describing the tool.
        """
        # Handle different tool types
        name = "unknown"
        description = ""
        input_schema: dict[str, Any] = {}

        # Check for common tool attributes
        if hasattr(tool, "name"):
            name = tool.name
        elif hasattr(tool, "__name__"):
            name = tool.__name__
        else:
            name = str(tool)

        if hasattr(tool, "description"):
            description = tool.description
        elif hasattr(tool, "__doc__") and tool.__doc__:
            description = tool.__doc__

        if hasattr(tool, "parameters_schema"):
            input_schema = tool.parameters_schema
        elif hasattr(tool, "input_schema"):
            input_schema = tool.input_schema
        elif hasattr(tool, "args_schema"):
            # Pydantic model for args
            try:
                input_schema = tool.args_schema.model_json_schema()
            except Exception:
                input_schema = {}

        return AgentCapability(
            name=name,
            description=description[:500] if description else "",
            input_schema=input_schema,
            output_schema={},
        )

    @staticmethod
    def create_server(
        agent: BaseAgent,
        base_url: str,
        agent_card: Optional[AgentCard] = None,
    ) -> A2AServer:
        """Create an A2A server for an AgentForge agent.

        Creates a server that exposes the agent's capabilities via A2A protocol.

        Args:
            agent: The AgentForge agent to expose.
            base_url: The base URL where this agent will be served.
            agent_card: Optional pre-built agent card (generated if not provided).

        Returns:
            An A2AServer configured for the agent.
        """
        card = agent_card or A2ABridge.agent_to_card(agent, base_url)
        server = A2AServer(card)

        # Create handler that executes the agent
        async def execute_handler(input_data: dict[str, Any]) -> dict[str, Any]:
            # Build AgentInput from A2A input
            from ..core.types import Message, MessageRole

            message_content = input_data.get("message", "")
            if not message_content and input_data:
                # If no message field, serialize the whole input
                message_content = str(input_data)

            agent_input = AgentInput(
                messages=[Message(role=MessageRole.USER, content=message_content)],
                context=input_data.get("context", {}),
            )

            # Execute agent
            output: AgentOutput = await agent.execute(agent_input)

            # Build result
            result: dict[str, Any] = {
                "status": output.status.value if hasattr(output.status, "value") else str(output.status),
            }

            if output.content:
                result["content"] = output.content
            if output.error:
                result["error"] = output.error
            if output.metadata:
                result["metadata"] = output.metadata
            if output.tool_calls:
                result["tool_calls"] = [
                    {"name": tc.name, "arguments": tc.arguments}
                    for tc in output.tool_calls
                ]

            return result

        # Register handler for each capability
        for cap in card.capabilities:
            server.register_capability_handler(cap.name, execute_handler)

        return server

    @staticmethod
    def create_client(base_url: str) -> A2AClient:
        """Create an A2A client for communicating with remote agents.

        Args:
            base_url: The base URL of the remote agent.

        Returns:
            An A2AClient configured for the remote agent.
        """
        return A2AClient(base_url)

    @staticmethod
    async def call_remote_agent(
        base_url: str,
        capability: str,
        input_data: dict[str, Any],
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Convenience method to call a remote agent's capability.

        Creates a client, discovers the agent, and sends a task in one call.

        Args:
            base_url: The base URL of the remote agent.
            capability: The capability to invoke.
            input_data: Input data for the capability.
            timeout: Request timeout in seconds.

        Returns:
            The task output from the remote agent.

        Raises:
            A2AClientError: If the call fails.
        """
        client = A2AClient(base_url)
        task = await client.send_task(capability, input_data, timeout=timeout)

        if task.output:
            return task.output
        if task.error:
            return {"error": task.error}
        return {"status": task.status.value}


__all__ = ["A2ABridge"]
