"""Tests for the agentforge.comms module.

Tests for:
- MessageEnvelope creation and reply
- MessageBus publish/subscribe
- MessageBus history
- RequestResponsePattern
- DelegationPattern
- PubSubPattern
- AgentCard
"""

import asyncio
from typing import Any

import pytest

from agentforge.comms import (
    A2AProtocolSupport,
    AgentCapability,
    AgentCard,
    DelegationPattern,
    MessageBus,
    MessageEnvelope,
    PubSubPattern,
    RequestResponsePattern,
)


class TestMessageEnvelope:
    """Tests for MessageEnvelope."""

    def test_create_message_envelope(self) -> None:
        """Test creating a message envelope."""
        envelope = MessageEnvelope(
            sender="agent-1",
            receiver="agent-2",
            type="request",
            payload={"text": "Hello"},
        )

        assert envelope.sender == "agent-1"
        assert envelope.receiver == "agent-2"
        assert envelope.type == "request"
        assert envelope.payload == {"text": "Hello"}
        assert envelope.id is not None
        assert envelope.timestamp is not None

    def test_create_broadcast_envelope(self) -> None:
        """Test creating a broadcast envelope (no receiver)."""
        envelope = MessageEnvelope(
            sender="agent-1",
            receiver=None,
            type="event",
            payload={"status": "completed"},
        )

        assert envelope.sender == "agent-1"
        assert envelope.receiver is None
        assert envelope.type == "event"

    def test_message_envelope_reply(self) -> None:
        """Test creating a reply message."""
        original = MessageEnvelope(
            sender="agent-1",
            receiver="agent-2",
            type="request",
            payload={"query": "What is the weather?"},
            trace_id="trace-123",
        )

        reply = original.reply({"answer": "Sunny, 72°F"})

        assert reply.sender == "agent-2"
        assert reply.receiver == "agent-1"
        assert reply.type == "response"
        assert reply.payload == {"answer": "Sunny, 72°F"}
        assert reply.trace_id == "trace-123"

    def test_message_envelope_reply_broadcast_raises(self) -> None:
        """Test that replying to a broadcast envelope raises a clear error."""
        original = MessageEnvelope(
            sender="agent-1",
            receiver=None,
            type="event",
            payload={"status": "ok"},
        )

        with pytest.raises(ValueError, match="broadcast"):
            original.reply({"ack": True})

    def test_message_envelope_with_metadata(self) -> None:
        """Test creating envelope with metadata."""
        envelope = MessageEnvelope(
            sender="agent-1",
            receiver="agent-2",
            payload={"data": "test"},
            metadata={"priority": "high", "ttl": 60},
        )

        assert envelope.metadata == {"priority": "high", "ttl": 60}

    def test_message_envelope_default_values(self) -> None:
        """Test default values for optional fields."""
        envelope = MessageEnvelope(
            sender="agent-1",
            payload={"text": "test"},
        )

        assert envelope.receiver is None
        assert envelope.type == "request"
        assert envelope.trace_id is None
        assert envelope.metadata is None


class TestMessageBus:
    """Tests for MessageBus."""

    @pytest.mark.asyncio
    async def test_publish_subscribe(self) -> None:
        """Test publish/subscribe functionality."""
        bus = MessageBus()
        received: list[MessageEnvelope] = []

        def handler(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("test.topic", handler)

        message = MessageEnvelope(
            sender="agent-1",
            payload={"text": "Hello"},
        )
        await bus.publish("test.topic", message)

        assert len(received) == 1
        assert received[0].payload == {"text": "Hello"}

    @pytest.mark.asyncio
    async def test_async_handler(self) -> None:
        """Test async handler support."""
        bus = MessageBus()
        received: list[MessageEnvelope] = []

        async def async_handler(msg: MessageEnvelope) -> None:
            await asyncio.sleep(0.01)
            received.append(msg)

        bus.subscribe("test.async", async_handler)

        message = MessageEnvelope(
            sender="agent-1",
            payload={"text": "Async test"},
        )
        await bus.publish("test.async", message)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        """Test unsubscribing from a topic."""
        bus = MessageBus()
        received: list[MessageEnvelope] = []

        def handler(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("test.topic", handler)
        bus.unsubscribe("test.topic", handler)

        message = MessageEnvelope(
            sender="agent-1",
            payload={"text": "Hello"},
        )
        await bus.publish("test.topic", message)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_send_to_receiver(self) -> None:
        """Test sending to a specific receiver."""
        bus = MessageBus()
        received: list[MessageEnvelope] = []

        def handler(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("agent.agent-2", handler)

        message = MessageEnvelope(
            sender="agent-1",
            receiver="agent-2",
            payload={"text": "Direct message"},
        )
        await bus.send(message)

        assert len(received) == 1
        assert received[0].receiver == "agent-2"

    @pytest.mark.asyncio
    async def test_broadcast(self) -> None:
        """Test broadcasting to all subscribers."""
        bus = MessageBus()
        received: list[MessageEnvelope] = []

        def handler(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("broadcast", handler)

        await bus.broadcast("agent-1", {"status": "completed"})

        assert len(received) == 1
        assert received[0].type == "event"
        assert received[0].receiver is None

    def test_message_history(self) -> None:
        """Test message history."""
        bus = MessageBus()

        # Add messages via _add_to_history (simulating publish)
        for i in range(5):
            msg = MessageEnvelope(
                sender=f"agent-{i}",
                payload={"index": i},
            )
            bus._add_to_history(msg)

        history = bus.get_history()
        assert len(history) == 5

    def test_message_history_filtered_by_agent(self) -> None:
        """Test message history filtered by agent."""
        bus = MessageBus()

        # Add messages
        for i in range(5):
            msg = MessageEnvelope(
                sender="agent-1" if i % 2 == 0 else "agent-2",
                receiver="agent-2" if i % 2 == 0 else "agent-1",
                payload={"index": i},
            )
            bus._add_to_history(msg)

        history = bus.get_history(agent="agent-1")
        assert len(history) == 5  # All messages involve agent-1

    def test_message_history_limit(self) -> None:
        """Test message history limit."""
        bus = MessageBus()

        # Add 10 messages
        for i in range(10):
            msg = MessageEnvelope(
                sender="agent-1",
                payload={"index": i},
            )
            bus._add_to_history(msg)

        history = bus.get_history(limit=3)
        assert len(history) == 3

    def test_clear_history(self) -> None:
        """Test clearing message history."""
        bus = MessageBus()

        msg = MessageEnvelope(
            sender="agent-1",
            payload={"text": "test"},
        )
        bus._add_to_history(msg)

        assert len(bus.get_history()) == 1
        bus.clear_history()
        assert len(bus.get_history()) == 0

    def test_history_size_limit(self) -> None:
        """Test history size limit."""
        bus = MessageBus()
        bus._max_history = 5

        # Add more messages than the limit
        for i in range(10):
            msg = MessageEnvelope(
                sender="agent-1",
                payload={"index": i},
            )
            bus._add_to_history(msg)

        # Should only keep the last 5
        assert len(bus._message_history) == 5
        assert bus._message_history[0].payload["index"] == 5


class TestRequestResponsePattern:
    """Tests for RequestResponsePattern."""

    @pytest.mark.asyncio
    async def test_request_response(self) -> None:
        """Test request/response pattern."""
        bus = MessageBus()
        pattern = RequestResponsePattern(timeout=5.0)

        # Set up responder
        async def handle_request(msg: MessageEnvelope) -> None:
            if msg.type == "request":
                response = msg.reply({"result": "success"})
                await bus.send(response)

        bus.subscribe("agent.agent-2", handle_request)

        # Make request
        response = await pattern.request(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            payload={"query": "test"},
        )

        assert response.payload == {"result": "success"}

    @pytest.mark.asyncio
    async def test_request_timeout(self) -> None:
        """Test request timeout."""
        bus = MessageBus()
        pattern = RequestResponsePattern(timeout=0.1)

        # No responder set up

        with pytest.raises(asyncio.TimeoutError):
            await pattern.request(
                bus=bus,
                sender="agent-1",
                receiver="agent-2",
                payload={"query": "test"},
            )

    @pytest.mark.asyncio
    async def test_execute_method(self) -> None:
        """Test execute method."""
        bus = MessageBus()
        pattern = RequestResponsePattern(timeout=5.0)

        # Set up responder
        async def handle_request(msg: MessageEnvelope) -> None:
            if msg.type == "request":
                response = msg.reply({"status": "ok"})
                await bus.send(response)

        bus.subscribe("agent.agent-2", handle_request)

        # Use execute method
        response = await pattern.execute(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            payload={"action": "test"},
        )

        assert response.payload == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_request_response_concurrent_correlation(self) -> None:
        """Test concurrent requests are correlated to the correct response."""
        bus = MessageBus()
        pattern = RequestResponsePattern(timeout=2.0)

        async def handle_request(msg: MessageEnvelope) -> None:
            if msg.type != "request":
                return
            query = msg.payload["query"]
            # Respond out-of-order to ensure correlation is trace-id based.
            await asyncio.sleep(0.01 if query == 2 else 0.05)
            response = msg.reply({"query": query})
            await bus.send(response)

        bus.subscribe("agent.agent-2", handle_request)

        async def make_request(query: int) -> tuple[int, int]:
            response = await pattern.request(
                bus=bus,
                sender="agent-1",
                receiver="agent-2",
                payload={"query": query},
            )
            return query, response.payload["query"]

        results = await asyncio.gather(make_request(1), make_request(2))
        assert sorted(results) == [(1, 1), (2, 2)]


class TestDelegationPattern:
    """Tests for DelegationPattern."""

    @pytest.mark.asyncio
    async def test_delegate(self) -> None:
        """Test delegation pattern."""
        bus = MessageBus()
        pattern = DelegationPattern()

        received: list[MessageEnvelope] = []

        async def handle_delegation(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("agent.agent-2", handle_delegation)

        await pattern.delegate(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            task={"action": "analyze", "data": "test data"},
            context={"priority": "high"},
        )

        # Wait for async processing
        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0].type == "delegation"
        assert received[0].payload["task"]["action"] == "analyze"
        assert received[0].payload["context"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_delegate_without_context(self) -> None:
        """Test delegation without context."""
        bus = MessageBus()
        pattern = DelegationPattern()

        received: list[MessageEnvelope] = []

        def handle_delegation(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("agent.agent-2", handle_delegation)

        await pattern.delegate(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            task={"action": "process"},
        )

        assert len(received) == 1
        assert received[0].payload["context"] == {}

    @pytest.mark.asyncio
    async def test_execute_method(self) -> None:
        """Test execute method."""
        bus = MessageBus()
        pattern = DelegationPattern()

        received: list[MessageEnvelope] = []

        def handle_delegation(msg: MessageEnvelope) -> None:
            received.append(msg)

        bus.subscribe("agent.agent-2", handle_delegation)

        await pattern.execute(
            bus=bus,
            sender="agent-1",
            receiver="agent-2",
            task={"action": "test"},
        )

        assert len(received) == 1


class TestPubSubPattern:
    """Tests for PubSubPattern."""

    @pytest.mark.asyncio
    async def test_publish_event(self) -> None:
        """Test publishing an event."""
        bus = MessageBus()
        pattern = PubSubPattern()

        received: list[MessageEnvelope] = []

        def handle_event(msg: MessageEnvelope) -> None:
            received.append(msg)

        pattern.subscribe_to_event(bus, "status_update", handle_event)

        await pattern.publish_event(
            bus=bus,
            sender="agent-1",
            event_type="status_update",
            data={"status": "completed"},
        )

        assert len(received) == 1
        assert received[0].type == "event"
        assert received[0].payload["event_type"] == "status_update"
        assert received[0].payload["data"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_subscribe_to_multiple_events(self) -> None:
        """Test subscribing to multiple event types."""
        bus = MessageBus()
        pattern = PubSubPattern()

        status_received: list[MessageEnvelope] = []
        error_received: list[MessageEnvelope] = []

        def handle_status(msg: MessageEnvelope) -> None:
            status_received.append(msg)

        def handle_error(msg: MessageEnvelope) -> None:
            error_received.append(msg)

        pattern.subscribe_to_event(bus, "status_update", handle_status)
        pattern.subscribe_to_event(bus, "error", handle_error)

        await pattern.publish_event(
            bus=bus,
            sender="agent-1",
            event_type="status_update",
            data={"status": "running"},
        )

        await pattern.publish_event(
            bus=bus,
            sender="agent-1",
            event_type="error",
            data={"error": "Something went wrong"},
        )

        assert len(status_received) == 1
        assert len(error_received) == 1

    @pytest.mark.asyncio
    async def test_execute_method(self) -> None:
        """Test execute method."""
        bus = MessageBus()
        pattern = PubSubPattern()

        received: list[MessageEnvelope] = []

        def handle_event(msg: MessageEnvelope) -> None:
            received.append(msg)

        pattern.subscribe_to_event(bus, "test_event", handle_event)

        await pattern.execute(
            bus=bus,
            sender="agent-1",
            event_type="test_event",
            data={"test": "data"},
        )

        assert len(received) == 1


class TestAgentCard:
    """Tests for AgentCard."""

    def test_create_agent_card(self) -> None:
        """Test creating an agent card."""
        caps = [
            AgentCapability(name="search", description="Search capability"),
            AgentCapability(name="analyze", description="Analyze capability"),
        ]
        card = AgentCard(
            id="test-agent-001",
            name="TestAgent",
            description="A test agent",
            version="2.0.0",
            capabilities=caps,
            endpoints={"api": "https://api.example.com"},
        )

        assert card.id == "test-agent-001"
        assert card.name == "TestAgent"
        assert card.description == "A test agent"
        assert card.version == "2.0.0"
        assert len(card.capabilities) == 2
        assert card.capabilities[0].name == "search"
        assert card.endpoints == {"api": "https://api.example.com"}

    def test_agent_card_defaults(self) -> None:
        """Test agent card default values."""
        card = AgentCard(id="test-agent-defaults", name="TestAgent")

        assert card.description == ""
        assert card.version == "1.0.0"
        assert card.capabilities == []
        assert card.endpoints == {}
        assert card.metadata == {}

    def test_agent_card_to_json(self) -> None:
        """Test exporting agent card to JSON."""
        card = AgentCard(
            id="test-json-001",
            name="TestAgent",
            description="A test agent",
            capabilities=[AgentCapability(name="search", description="Search")],
            metadata={"author": "test"},
        )

        json_data = card.to_json()

        assert json_data["name"] == "TestAgent"
        assert json_data["description"] == "A test agent"
        assert len(json_data["capabilities"]) == 1
        assert json_data["metadata"] == {"author": "test"}


class TestA2AProtocolSupport:
    """Tests for A2AProtocolSupport."""

    def test_create_a2a_protocol_support(self) -> None:
        """Test creating A2A protocol support."""
        card = AgentCard(
            id="a2a-test-001",
            name="TestAgent",
            capabilities=[AgentCapability(name="search", description="Search")],
        )
        a2a = A2AProtocolSupport(agent_card=card)

        assert a2a.agent_card == card

    def test_get_agent_card(self) -> None:
        """Test getting agent card."""
        card = AgentCard(
            id="a2a-test-002",
            name="TestAgent",
            description="Test description",
        )
        a2a = A2AProtocolSupport(agent_card=card)

        card_json = a2a.get_agent_card()

        assert card_json["name"] == "TestAgent"
        assert card_json["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_handle_task(self) -> None:
        """Test handling an A2A task."""
        card = AgentCard(id="a2a-test-003", name="TestAgent")
        a2a = A2AProtocolSupport(agent_card=card)

        result = await a2a.handle_task({"action": "test"})

        # Stub implementation returns not_implemented
        assert result["status"] == "not_implemented"


class TestIntegration:
    """Integration tests for comms module."""

    @pytest.mark.asyncio
    async def test_full_communication_flow(self) -> None:
        """Test a full communication flow between agents."""
        bus = MessageBus()

        # Agent 1: Request/Response handler
        async def agent1_handler(msg: MessageEnvelope) -> None:
            if msg.type == "request":
                response = msg.reply({"processed": True})
                await bus.send(response)

        bus.subscribe("agent.agent-1", agent1_handler)

        # Agent 2: Make request
        pattern = RequestResponsePattern(timeout=5.0)
        response = await pattern.request(
            bus=bus,
            sender="agent-2",
            receiver="agent-1",
            payload={"task": "process"},
        )

        assert response.payload == {"processed": True}

        # Check history
        history = bus.get_history()
        assert len(history) >= 2  # Request and response

    @pytest.mark.asyncio
    async def test_event_broadcast_flow(self) -> None:
        """Test event broadcast flow."""
        bus = MessageBus()
        pubsub = PubSubPattern()

        events_received: list[dict[str, Any]] = []

        def event_handler(msg: MessageEnvelope) -> None:
            events_received.append(msg.payload)

        pubsub.subscribe_to_event(bus, "progress", event_handler)

        # Publish multiple events
        for i in range(3):
            await pubsub.publish_event(
                bus=bus,
                sender="worker-agent",
                event_type="progress",
                data={"percent": (i + 1) * 33},
            )

        assert len(events_received) == 3
        assert events_received[-1]["data"]["percent"] == 99
