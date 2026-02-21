"""Message envelope and bus for agent communication.

This module provides the message envelope structure and message bus
for inter-agent communication in AgentForge.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MessageEnvelope(BaseModel):
    """Message envelope for agent communication.

    Wraps messages with routing and metadata information
    for the message bus.

    Attributes:
        id: Unique identifier for this envelope.
        sender: ID of the sending agent.
        receiver: ID of the recipient agent (None for broadcast).
        type: Message type (request, response, event, delegation).
        payload: The message payload data.
        trace_id: Optional trace ID for distributed tracing.
        timestamp: When the envelope was created.
        metadata: Additional routing metadata.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    receiver: str | None = None  # None = broadcast
    type: Literal["request", "response", "event", "delegation"] = "request"
    payload: dict[str, Any]
    trace_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] | None = None

    def reply(
        self,
        payload: dict[str, Any],
        type: Literal["response", "event", "delegation", "request"] = "response",
    ) -> "MessageEnvelope":
        """Create a reply message.

        Args:
            payload: The reply payload.
            type: Message type for the reply.

        Returns:
            A new MessageEnvelope addressed back to the sender.
        """
        if self.receiver is None:
            raise ValueError("Cannot create a direct reply for a broadcast message")

        return MessageEnvelope(
            sender=self.receiver,
            receiver=self.sender,
            type=type,
            payload=payload,
            trace_id=self.trace_id,
        )


class MessageBus:
    """In-process pub/sub for agent communication.

    Provides publish/subscribe and direct messaging capabilities
    for agents to communicate with each other.

    Example:
        ```python
        bus = MessageBus()

        # Subscribe to messages
        def handle_message(msg: MessageEnvelope):
            print(f"Got message from {msg.sender}")

        bus.subscribe("agent.agent-1", handle_message)

        # Send a message
        message = MessageEnvelope(
            sender="agent-2",
            receiver="agent-1",
            payload={"text": "Hello"},
        )
        await bus.send(message)
        ```
    """

    def __init__(self) -> None:
        """Initialize the message bus."""
        self._subscribers: dict[str, list[Callable]] = {}
        self._message_history: list[MessageEnvelope] = []
        self._max_history: int = 1000

    async def publish(self, topic: str, message: MessageEnvelope) -> None:
        """Publish a message to a topic.

        Args:
            topic: The topic to publish to.
            message: The message envelope to publish.
        """
        self._add_to_history(message)
        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Message handler failed for topic '%s'", topic)

    def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic.

        Args:
            topic: The topic to subscribe to.
            handler: Callback function for messages.
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Callable) -> bool:
        """Unsubscribe from a topic.

        Args:
            topic: The topic to unsubscribe from.
            handler: The handler to remove.

        Returns:
            True if handler was removed, False otherwise.
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(handler)
                return True
            except ValueError:
                pass
        return False

    async def send(self, message: MessageEnvelope) -> None:
        """Send a message to a specific receiver.

        Args:
            message: The message envelope to send.
        """
        if message.receiver:
            await self.publish(f"agent.{message.receiver}", message)
        else:
            await self.publish("broadcast", message)

    async def broadcast(self, sender: str, payload: dict[str, Any]) -> None:
        """Broadcast a message to all subscribers.

        Args:
            sender: ID of the sending agent.
            payload: The message payload.
        """
        message = MessageEnvelope(
            sender=sender,
            receiver=None,
            type="event",
            payload=payload,
        )
        await self.publish("broadcast", message)

    def _add_to_history(self, message: MessageEnvelope) -> None:
        """Add message to history with size limit.

        Args:
            message: The message to add.
        """
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history :]

    def get_history(self, agent: str | None = None, limit: int = 100) -> list[MessageEnvelope]:
        """Get message history, optionally filtered by agent.

        Args:
            agent: Optional agent ID to filter by.
            limit: Maximum number of messages to return.

        Returns:
            List of message envelopes.
        """
        if agent:
            messages = [
                m for m in self._message_history if m.sender == agent or m.receiver == agent
            ]
        else:
            messages = self._message_history
        return messages[-limit:]

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()


__all__ = ["MessageEnvelope", "MessageBus"]
