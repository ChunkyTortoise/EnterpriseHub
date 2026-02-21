"""Communication patterns for agent communication.

This module provides common communication patterns for agents:
- Request/Response
- Pub/Sub
- Delegation
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from agentforge.comms.message import MessageBus, MessageEnvelope


class CommunicationPattern(ABC):
    """Abstract base for communication patterns."""

    @abstractmethod
    async def execute(self, bus: MessageBus, *args, **kwargs) -> Any:
        """Execute the communication pattern.

        Args:
            bus: The message bus to use.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Pattern-specific result.
        """
        ...


class RequestResponsePattern(CommunicationPattern):
    """Request/response pattern for synchronous calls.

    Implements a request-response pattern where one agent
    can send a request and wait for a response.

    Example:
        ```python
        bus = MessageBus()
        pattern = RequestResponsePattern(timeout=30.0)

        # Send request and wait for response
        response = await pattern.request(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            payload={"query": "hello"},
        )
        ```
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize the pattern.

        Args:
            timeout: Default timeout for requests in seconds.
        """
        self.timeout = timeout
        self._pending_requests: dict[str, asyncio.Future] = {}

    async def request(
        self, bus: MessageBus, sender: str, receiver: str, payload: dict[str, Any]
    ) -> MessageEnvelope:
        """Send a request and wait for response.

        Args:
            bus: The message bus to use.
            sender: ID of the requesting agent.
            receiver: ID of the agent to request from.
            payload: Request payload.

        Returns:
            The response message envelope.

        Raises:
            asyncio.TimeoutError: If timeout expires.
        """
        request = MessageEnvelope(
            sender=sender,
            receiver=receiver,
            type="request",
            payload=payload,
        )
        request.trace_id = request.id

        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending_requests[request.id] = future

        # Subscribe to response
        def handle_response(msg: MessageEnvelope) -> None:
            if msg.type == "response" and msg.trace_id == request.id and not future.done():
                future.set_result(msg)

        bus.subscribe(f"agent.{sender}", handle_response)

        try:
            await bus.send(request)
            return await asyncio.wait_for(future, timeout=self.timeout)
        finally:
            self._pending_requests.pop(request.id, None)
            bus.unsubscribe(f"agent.{sender}", handle_response)

    async def execute(self, bus: MessageBus, *args, **kwargs) -> MessageEnvelope:
        """Execute the request/response pattern.

        Args:
            bus: The message bus to use.
            *args: Positional arguments (sender, receiver, payload).
            **kwargs: Keyword arguments.

        Returns:
            The response message envelope.
        """
        return await self.request(bus, *args, **kwargs)


class DelegationPattern(CommunicationPattern):
    """Delegation pattern for handing off subtasks.

    Allows an agent to delegate a subtask to another agent.

    Example:
        ```python
        delegation = DelegationPattern()

        # Delegate a task
        await delegation.delegate(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            task={"action": "analyze", "data": "..."},
            context={"priority": "high"},
        )
        ```
    """

    async def delegate(
        self,
        bus: MessageBus,
        sender: str,
        receiver: str,
        task: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> None:
        """Delegate a task to another agent.

        Args:
            bus: The message bus to use.
            sender: ID of the delegating agent.
            receiver: ID of the agent to delegate to.
            task: The task to delegate.
            context: Optional context for the task.
        """
        message = MessageEnvelope(
            sender=sender,
            receiver=receiver,
            type="delegation",
            payload={"task": task, "context": context or {}},
        )
        await bus.send(message)

    async def execute(self, bus: MessageBus, *args, **kwargs) -> None:
        """Execute the delegation pattern.

        Args:
            bus: The message bus to use.
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        return await self.delegate(bus, *args, **kwargs)


class PubSubPattern(CommunicationPattern):
    """Publish/subscribe pattern for event-driven communication.

    Implements an event-driven pattern where agents can
    publish events and subscribe to event types.

    Example:
        ```python
        pubsub = PubSubPattern()

        # Subscribe to events
        def handle_event(msg: MessageEnvelope):
            print(f"Got event: {msg.payload}")

        pubsub.subscribe_to_event(bus, "status_update", handle_event)

        # Publish an event
        await pubsub.publish_event(
            bus=bus,
            sender="agent-1",
            event_type="status_update",
            data={"status": "completed"},
        )
        ```
    """

    async def publish_event(
        self, bus: MessageBus, sender: str, event_type: str, data: dict[str, Any]
    ) -> None:
        """Publish an event.

        Args:
            bus: The message bus to use.
            sender: ID of the publishing agent.
            event_type: Type of event.
            data: Event data.
        """
        message = MessageEnvelope(
            sender=sender,
            receiver=None,
            type="event",
            payload={"event_type": event_type, "data": data},
        )
        await bus.publish(f"events.{event_type}", message)

    def subscribe_to_event(self, bus: MessageBus, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type.

        Args:
            bus: The message bus to use.
            event_type: Type of event to subscribe to.
            handler: Callback function for events.
        """
        bus.subscribe(f"events.{event_type}", handler)

    async def execute(self, bus: MessageBus, *args, **kwargs) -> None:
        """Execute the pub/sub pattern.

        Args:
            bus: The message bus to use.
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        return await self.publish_event(bus, *args, **kwargs)


__all__ = [
    "CommunicationPattern",
    "RequestResponsePattern",
    "DelegationPattern",
    "PubSubPattern",
]
