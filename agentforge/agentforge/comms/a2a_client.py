"""A2A (Agent-to-Agent) protocol client for AgentForge.

This module provides the client-side implementation of the A2A protocol,
enabling communication with A2A-compatible agents.

Uses zero-dependency HTTP client (urllib.request with asyncio.to_thread)
for maximum compatibility.

Provides:
- A2AClient for discovering and communicating with remote agents
- Task submission, monitoring, and cancellation
- Agent card discovery via /.well-known/agent.json
"""

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any, Optional

from .a2a_types import A2AMessage, A2AResponse, AgentCard, Task


class A2AClientError(Exception):
    """Exception raised when A2A client encounters an error.

    Attributes:
        message: Error description.
        code: Optional error code from A2A response.
    """

    def __init__(self, message: str, code: Optional[int] = None) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            code: Optional error code from A2A response.
        """
        super().__init__(message)
        self.code = code


class A2AClient:
    """Client for communicating with A2A-compatible agents.

    Provides methods for discovering agents, sending tasks, and
    monitoring task status.

    Attributes:
        base_url: The base URL of the remote agent.
        agent_card: The discovered agent card (after discover_agent()).

    Example:
        ```python
        # Create client
        client = A2AClient("https://agent.example.com")

        # Discover agent capabilities
        card = await client.discover_agent()
        print(f"Agent: {card.name}")
        print(f"Capabilities: {[c.name for c in card.capabilities]}")

        # Send a task
        task = await client.send_task(
            capability="get_forecast",
            input_data={"location": "San Francisco"}
        )
        print(f"Result: {task.output}")

        # Or poll for long-running tasks
        task = await client.send_task(...)
        while task.status == TaskStatus.WORKING:
            await asyncio.sleep(1)
            task = await client.get_task(task.id)
        ```
    """

    def __init__(
        self, base_url: str, agent_card: Optional[AgentCard] = None
    ) -> None:
        """Initialize the A2A client.

        Args:
            base_url: The base URL of the remote agent.
            agent_card: Optional pre-fetched agent card.
        """
        self.base_url = base_url.rstrip("/")
        self._agent_card = agent_card

    @property
    def agent_card(self) -> Optional[AgentCard]:
        """Get the discovered agent card.

        Returns:
            The agent card if discovered, None otherwise.
        """
        return self._agent_card

    async def discover_agent(self, timeout: float = 10.0) -> AgentCard:
        """Discover an agent by fetching its Agent Card.

        Fetches the agent card from /.well-known/agent.json.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            The discovered AgentCard.

        Raises:
            A2AClientError: If discovery fails.
        """
        url = f"{self.base_url}/.well-known/agent.json"

        def fetch() -> AgentCard:
            try:
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    data = json.loads(response.read().decode())
                    return AgentCard(**data)
            except urllib.error.HTTPError as e:
                raise A2AClientError(
                    f"Discovery failed: HTTP {e.code}", code=e.code
                )
            except urllib.error.URLError as e:
                raise A2AClientError(f"Discovery failed: {e.reason}")
            except json.JSONDecodeError as e:
                raise A2AClientError(f"Invalid agent card JSON: {e}")

        self._agent_card = await asyncio.to_thread(fetch)
        return self._agent_card

    async def send_task(
        self,
        capability: str,
        input_data: dict[str, Any],
        timeout: float = 30.0,
    ) -> Task:
        """Send a task to the agent.

        Creates and executes a task for the specified capability.

        Args:
            capability: The capability to invoke.
            input_data: Input data for the capability.
            timeout: Request timeout in seconds.

        Returns:
            The created Task with status and output.

        Raises:
            A2AClientError: If the request fails or agent returns an error.
        """
        message = A2AMessage(
            method="tasks/send",
            params={"capability": capability, "input": input_data},
        )

        response = await self._send_message(message, timeout)

        if response.error:
            raise A2AClientError(
                response.error.get("message", "Unknown error"),
                code=response.error.get("code"),
            )

        return Task(**response.result)

    async def get_task(self, task_id: str, timeout: float = 10.0) -> Task:
        """Get the status of a task.

        Retrieves the current state of a previously submitted task.

        Args:
            task_id: The ID of the task to retrieve.
            timeout: Request timeout in seconds.

        Returns:
            The current Task state.

        Raises:
            A2AClientError: If the request fails or task not found.
        """
        message = A2AMessage(
            method="tasks/get",
            params={"task_id": task_id},
        )

        response = await self._send_message(message, timeout)

        if response.error:
            raise A2AClientError(
                response.error.get("message", "Unknown error"),
                code=response.error.get("code"),
            )

        return Task(**response.result)

    async def cancel_task(self, task_id: str, timeout: float = 10.0) -> Task:
        """Cancel a task.

        Attempts to cancel a task that is still working.

        Args:
            task_id: The ID of the task to cancel.
            timeout: Request timeout in seconds.

        Returns:
            The updated Task state.

        Raises:
            A2AClientError: If the request fails or task not found.
        """
        message = A2AMessage(
            method="tasks/cancel",
            params={"task_id": task_id},
        )

        response = await self._send_message(message, timeout)

        if response.error:
            raise A2AClientError(
                response.error.get("message", "Unknown error"),
                code=response.error.get("code"),
            )

        return Task(**response.result)

    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        timeout: float = 10.0,
    ) -> tuple[list[Task], int]:
        """List tasks on the agent.

        Retrieves a list of tasks with optional filtering.

        Args:
            status: Optional status filter (submitted, working, completed, etc.).
            limit: Maximum number of tasks to return.
            timeout: Request timeout in seconds.

        Returns:
            Tuple of (list of tasks, total count).

        Raises:
            A2AClientError: If the request fails.
        """
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status

        message = A2AMessage(method="tasks/list", params=params)

        response = await self._send_message(message, timeout)

        if response.error:
            raise A2AClientError(
                response.error.get("message", "Unknown error"),
                code=response.error.get("code"),
            )

        result = response.result
        tasks = [Task(**t) for t in result.get("tasks", [])]
        total = result.get("total", 0)
        return tasks, total

    async def get_agent_card(self, timeout: float = 10.0) -> AgentCard:
        """Get the agent card via A2A protocol method.

        Alternative to discover_agent() that uses the A2A JSON-RPC method
        instead of the well-known endpoint.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            The AgentCard.

        Raises:
            A2AClientError: If the request fails.
        """
        message = A2AMessage(method="agent/card", params={})

        response = await self._send_message(message, timeout)

        if response.error:
            raise A2AClientError(
                response.error.get("message", "Unknown error"),
                code=response.error.get("code"),
            )

        return AgentCard(**response.result)

    async def poll_task_until_complete(
        self,
        task_id: str,
        poll_interval: float = 1.0,
        max_wait: float = 300.0,
    ) -> Task:
        """Poll a task until it completes, fails, or is cancelled.

        Convenience method for waiting on long-running tasks.

        Args:
            task_id: The ID of the task to poll.
            poll_interval: Time between polls in seconds.
            max_wait: Maximum time to wait in seconds.

        Returns:
            The final Task state.

        Raises:
            A2AClientError: If polling fails or timeout exceeded.
            asyncio.TimeoutError: If max_wait is exceeded.
        """
        elapsed = 0.0
        while elapsed < max_wait:
            task = await self.get_task(task_id)

            if task.status in (
                "completed",
                "failed",
                "cancelled",
            ):
                return task

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise asyncio.TimeoutError(
            f"Task {task_id} did not complete within {max_wait} seconds"
        )

    async def _send_message(
        self, message: A2AMessage, timeout: float = 30.0
    ) -> A2AResponse:
        """Send a JSON-RPC message to the agent.

        Internal method for sending A2A messages via HTTP POST.

        Args:
            message: The A2A message to send.
            timeout: Request timeout in seconds.

        Returns:
            The A2AResponse from the agent.
        """
        url = f"{self.base_url}/a2a"
        data = message.model_dump_json().encode()

        def send() -> A2AResponse:
            try:
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    result = json.loads(response.read().decode())
                    return A2AResponse(**result)
            except urllib.error.HTTPError as e:
                # Try to parse error response
                try:
                    error_body = json.loads(e.read().decode())
                    return A2AResponse(
                        id=message.id,
                        error=error_body.get("error", {"message": str(e)}),
                    )
                except (json.JSONDecodeError, Exception):
                    return A2AResponse(
                        id=message.id,
                        error={"code": e.code, "message": str(e)},
                    )
            except urllib.error.URLError as e:
                return A2AResponse(
                    id=message.id,
                    error={"code": -1, "message": f"Connection failed: {e.reason}"},
                )
            except json.JSONDecodeError as e:
                return A2AResponse(
                    id=message.id,
                    error={"code": -1, "message": f"Invalid JSON response: {e}"},
                )

        return await asyncio.to_thread(send)


__all__ = ["A2AClient", "A2AClientError"]
