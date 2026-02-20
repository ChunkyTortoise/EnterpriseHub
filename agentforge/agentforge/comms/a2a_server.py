"""A2A (Agent-to-Agent) protocol server for AgentForge.

This module provides the server-side implementation of the A2A protocol,
enabling agents to expose their capabilities for discovery and task execution.

Provides:
- A2AServer for handling A2A protocol messages
- Task management and lifecycle tracking
- Capability handler registration
"""

from collections.abc import Callable
from typing import Any

from .a2a_types import (
    A2AErrorCode,
    A2AMessage,
    A2AResponse,
    AgentCard,
    Task,
    TaskStatus,
)

# Type alias for capability handlers
CapabilityHandler = Callable[[dict[str, Any]], Any]


class A2AServer:
    """A2A protocol server for exposing agents.

    Handles incoming A2A protocol messages and manages task lifecycle.
    Supports registration of custom capability handlers.

    Attributes:
        agent_card: The agent card describing this agent.

    Example:
        ```python
        # Create agent card
        card = AgentCard(
            id="weather-agent",
            name="WeatherAgent",
            description="Provides weather forecasts",
            capabilities=[
                AgentCapability(name="get_forecast", description="Get weather forecast")
            ]
        )

        # Create server
        server = A2AServer(card)

        # Register capability handler
        async def handle_forecast(input_data: dict) -> dict:
            return {"forecast": "Sunny, 72°F"}

        server.register_capability_handler("get_forecast", handle_forecast)

        # Handle incoming message
        message = A2AMessage(
            method="tasks/send",
            params={"capability": "get_forecast", "input": {"location": "NYC"}}
        )
        response = await server.handle_message(message)
        ```
    """

    def __init__(self, agent_card: AgentCard) -> None:
        """Initialize the A2A server.

        Args:
            agent_card: The agent card describing this agent.
        """
        self.agent_card = agent_card
        self._tasks: dict[str, Task] = {}
        self._handlers: dict[str, Callable] = {}
        self._task_handlers: dict[str, CapabilityHandler] = {}

        # Register default A2A method handlers
        self._handlers["tasks/send"] = self._handle_task_send
        self._handlers["tasks/get"] = self._handle_task_get
        self._handlers["tasks/cancel"] = self._handle_task_cancel
        self._handlers["tasks/list"] = self._handle_task_list
        self._handlers["agent/card"] = self._handle_agent_card

    def register_capability_handler(
        self, capability: str, handler: CapabilityHandler
    ) -> None:
        """Register a handler for a specific capability.

        Args:
            capability: The capability name to handle.
            handler: Async or sync function that takes input dict and returns output.
        """
        self._task_handlers[capability] = handler

    def unregister_capability_handler(self, capability: str) -> bool:
        """Unregister a capability handler.

        Args:
            capability: The capability name to unregister.

        Returns:
            True if handler was removed, False if not found.
        """
        if capability in self._task_handlers:
            del self._task_handlers[capability]
            return True
        return False

    async def handle_message(self, message: A2AMessage) -> A2AResponse:
        """Handle an incoming A2A message.

        Routes the message to the appropriate handler based on method.

        Args:
            message: The A2A message to handle.

        Returns:
            A2AResponse with result or error.
        """
        handler = self._handlers.get(message.method)
        if not handler:
            return A2AResponse(
                id=message.id,
                error={
                    "code": A2AErrorCode.METHOD_NOT_FOUND,
                    "message": f"Method not found: {message.method}",
                },
            )

        try:
            result = await handler(message.params)
            return A2AResponse(id=message.id, result=result)
        except ValueError as e:
            return A2AResponse(
                id=message.id,
                error={"code": A2AErrorCode.INVALID_PARAMS, "message": str(e)},
            )
        except Exception as e:
            return A2AResponse(
                id=message.id,
                error={"code": A2AErrorCode.INTERNAL_ERROR, "message": str(e)},
            )

    async def _handle_task_send(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/send method.

        Creates a new task and executes the capability handler.

        Args:
            params: Must contain 'capability' and optionally 'input'.

        Returns:
            The created/updated task as dict.

        Raises:
            ValueError: If capability is missing or unknown.
        """
        capability = params.get("capability")
        if not capability:
            raise ValueError("Missing required parameter: capability")

        input_data = params.get("input", {})

        if capability not in self._task_handlers:
            raise ValueError(f"Unknown capability: {capability}")

        # Create task
        task = Task(
            agent_id=self.agent_card.id,
            status=TaskStatus.WORKING,
            input=input_data,
            metadata={"capability": capability},
        )
        self._tasks[task.id] = task

        # Execute handler
        handler = self._task_handlers[capability]
        try:
            # Support both async and sync handlers
            import asyncio
            import inspect

            if inspect.iscoroutinefunction(handler):
                output = await handler(input_data)
            else:
                output = await asyncio.to_thread(handler, input_data)

            task.status = TaskStatus.COMPLETED
            task.output = output if isinstance(output, dict) else {"result": output}
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

        task.touch()
        return task.model_dump()

    async def _handle_task_get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/get method.

        Retrieves a task by ID.

        Args:
            params: Must contain 'task_id'.

        Returns:
            The task as dict.

        Raises:
            ValueError: If task_id is missing or task not found.
        """
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("Missing required parameter: task_id")

        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        return self._tasks[task_id].model_dump()

    async def _handle_task_cancel(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/cancel method.

        Cancels a task if it's still working.

        Args:
            params: Must contain 'task_id'.

        Returns:
            The updated task as dict.

        Raises:
            ValueError: If task_id is missing or task not found.
        """
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("Missing required parameter: task_id")

        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        if task.status == TaskStatus.WORKING:
            task.status = TaskStatus.CANCELLED
            task.touch()

        return task.model_dump()

    async def _handle_task_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/list method.

        Lists tasks with optional filtering.

        Args:
            params: Optional 'status' filter and 'limit'.

        Returns:
            Dict with 'tasks' list and 'total' count.
        """
        status_filter = params.get("status")
        limit = params.get("limit", 100)

        tasks = list(self._tasks.values())

        if status_filter:
            tasks = [t for t in tasks if t.status.value == status_filter]

        tasks = tasks[:limit]

        return {
            "tasks": [t.model_dump() for t in tasks],
            "total": len(self._tasks),
        }

    async def _handle_agent_card(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle agent/card method.

        Returns the agent card for discovery.

        Args:
            params: Ignored (empty).

        Returns:
            The agent card as dict.
        """
        return self.agent_card.model_dump()

    def get_well_known_response(self) -> str:
        """Get the /.well-known/agent.json response.

        Returns:
            JSON string of the agent card.
        """
        return self.agent_card.model_dump_json()

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: The task ID to look up.

        Returns:
            The task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def list_tasks(
        self, status: TaskStatus | None = None, limit: int = 100
    ) -> list[Task]:
        """List tasks with optional filtering.

        Args:
            status: Optional status to filter by.
            limit: Maximum number of tasks to return.

        Returns:
            List of tasks.
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        return tasks[:limit]

    def clear_completed_tasks(self, max_age_hours: int = 24) -> int:
        """Clear completed, failed, or cancelled tasks older than max_age.

        Args:
            max_age_hours: Maximum age in hours for completed tasks.

        Returns:
            Number of tasks cleared.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = []

        for task_id, task in self._tasks.items():
            if task.status in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ):
                try:
                    updated = datetime.fromisoformat(task.updated_at)
                    if updated < cutoff:
                        to_remove.append(task_id)
                except (ValueError, TypeError):
                    # If we can't parse the date, remove it anyway
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        return len(to_remove)


__all__ = ["A2AServer", "CapabilityHandler"]
