"""
Example: Fixing WebSocket race conditions in tests
Shows proper synchronization patterns for WebSocket testing
"""

import asyncio
import pytest
import websockets
import json
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field


# ❌ BEFORE: Flaky WebSocket test
class FlakyWebSocketTest:
    @pytest.mark.asyncio
    async def test_websocket_communication_flaky(self):
        """This test fails intermittently due to WebSocket timing."""
        # Bad: Assumes immediate connection and readiness
        websocket = await websockets.connect("ws://localhost:8765")

        # Bad: Send immediately without waiting for readiness
        await websocket.send(json.dumps({"type": "auth", "token": "test"}))

        # Bad: Fixed delay
        await asyncio.sleep(1)

        # This might fail if auth hasn't processed yet
        await websocket.send(json.dumps({"type": "get_data"}))
        response = await websocket.recv()
        data = json.loads(response)

        assert data["status"] == "success"
        await websocket.close()


# ✅ AFTER: Robust WebSocket test with proper synchronization
@dataclass
class WebSocketTestClient:
    """Enhanced WebSocket client for testing with built-in synchronization."""
    uri: str
    websocket: websockets.WebSocketServerProtocol = None
    connected: bool = False
    authenticated: bool = False
    messages: List[Dict[str, Any]] = field(default_factory=list)
    _message_handlers: Dict[str, Callable] = field(default_factory=dict)

    async def wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float = 10.0,
        poll_interval: float = 0.1,
        error_message: str = "Condition not met"
    ) -> None:
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()

        while True:
            if condition():
                return

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(error_message)

            await asyncio.sleep(poll_interval)

    async def connect(self, timeout: float = 10.0):
        """Connect and wait for initial readiness."""
        self.websocket = await websockets.connect(self.uri)
        self.connected = True

        # Start message listening task
        asyncio.create_task(self._message_listener())

        # Wait for initial connection confirmation
        await self.wait_for_condition(
            condition=lambda: len(self.messages) > 0,
            timeout=timeout,
            error_message="No initial message received from WebSocket"
        )

    async def authenticate(self, token: str, timeout: float = 5.0):
        """Authenticate and wait for confirmation."""
        await self.send_message({
            "type": "auth",
            "token": token
        })

        # Wait for auth confirmation
        await self.wait_for_condition(
            condition=lambda: any(
                msg.get("type") == "auth_success" for msg in self.messages
            ),
            timeout=timeout,
            error_message="Authentication not confirmed"
        )

        self.authenticated = True

    async def send_message(self, message: Dict[str, Any]):
        """Send a message and ensure it's delivered."""
        if not self.connected:
            raise RuntimeError("Not connected")

        await self.websocket.send(json.dumps(message))

    async def wait_for_message_type(
        self,
        message_type: str,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Wait for a specific message type."""
        await self.wait_for_condition(
            condition=lambda: any(
                msg.get("type") == message_type for msg in self.messages
            ),
            timeout=timeout,
            error_message=f"Message of type '{message_type}' not received"
        )

        # Return the first message of the requested type
        for msg in self.messages:
            if msg.get("type") == message_type:
                return msg

    async def wait_for_message_count(self, count: int, timeout: float = 10.0):
        """Wait for a specific number of messages."""
        await self.wait_for_condition(
            condition=lambda: len(self.messages) >= count,
            timeout=timeout,
            error_message=f"Expected {count} messages, got {len(self.messages)}"
        )

    async def wait_for_message_containing(
        self,
        key: str,
        value: Any,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Wait for a message containing specific key-value pair."""
        await self.wait_for_condition(
            condition=lambda: any(
                msg.get(key) == value for msg in self.messages
            ),
            timeout=timeout,
            error_message=f"No message with {key}={value} received"
        )

        for msg in self.messages:
            if msg.get(key) == value:
                return msg

    async def _message_listener(self):
        """Background task to collect incoming messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.messages.append(data)

                    # Execute any registered handlers
                    message_type = data.get("type")
                    if message_type in self._message_handlers:
                        await self._message_handlers[message_type](data)

                except json.JSONDecodeError:
                    # Handle non-JSON messages
                    self.messages.append({"type": "raw", "data": message})

        except websockets.exceptions.ConnectionClosed:
            self.connected = False

    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message types."""
        self._message_handlers[message_type] = handler

    async def close(self):
        """Close the connection."""
        if self.websocket:
            await self.websocket.close()
        self.connected = False

    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get all messages of a specific type."""
        return [msg for msg in self.messages if msg.get("type") == message_type]


class RobustWebSocketTest:
    """Robust WebSocket tests with proper synchronization."""

    @pytest.fixture
    async def ws_client(self):
        """WebSocket client fixture with automatic connection and cleanup."""
        client = WebSocketTestClient("ws://localhost:8765")

        # Connect and wait for readiness
        await client.connect(timeout=10.0)

        yield client

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_websocket_authentication(self, ws_client):
        """Test WebSocket authentication with proper waiting."""
        # Authenticate and wait for confirmation
        await ws_client.authenticate("test_token", timeout=5.0)

        # Verify authentication was successful
        auth_messages = ws_client.get_messages_by_type("auth_success")
        assert len(auth_messages) == 1
        assert auth_messages[0]["user_id"] == "test_user"

    @pytest.mark.asyncio
    async def test_websocket_data_flow(self, ws_client):
        """Test complete data flow with synchronization."""
        # Authenticate first
        await ws_client.authenticate("test_token")

        # Request data
        await ws_client.send_message({
            "type": "get_data",
            "resource": "user_profile"
        })

        # Wait for specific response
        response = await ws_client.wait_for_message_type(
            "data_response",
            timeout=10.0
        )

        assert response["resource"] == "user_profile"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_websocket_subscription(self, ws_client):
        """Test WebSocket subscription with event waiting."""
        await ws_client.authenticate("test_token")

        # Subscribe to events
        await ws_client.send_message({
            "type": "subscribe",
            "channel": "user_notifications"
        })

        # Wait for subscription confirmation
        confirmation = await ws_client.wait_for_message_type(
            "subscription_confirmed",
            timeout=5.0
        )
        assert confirmation["channel"] == "user_notifications"

        # Trigger an event (this would be done by another part of the system)
        # For testing, we simulate it by sending a trigger message
        await ws_client.send_message({
            "type": "trigger_notification",
            "message": "test notification"
        })

        # Wait for the notification to arrive
        notification = await ws_client.wait_for_message_containing(
            "type", "notification",
            timeout=10.0
        )

        assert notification["channel"] == "user_notifications"
        assert notification["message"] == "test notification"

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, ws_client):
        """Test WebSocket error scenarios with proper waiting."""
        # Try to access protected resource without authentication
        await ws_client.send_message({
            "type": "get_protected_data"
        })

        # Wait for error response
        error = await ws_client.wait_for_message_type(
            "error",
            timeout=5.0
        )

        assert error["code"] == "UNAUTHORIZED"
        assert "authentication required" in error["message"].lower()


# ✅ Advanced pattern: Testing WebSocket reconnection
class WebSocketReconnectionTest:
    """Test WebSocket reconnection scenarios."""

    @pytest.mark.asyncio
    async def test_automatic_reconnection(self):
        """Test automatic reconnection with state preservation."""

        class ReconnectingWebSocketClient(WebSocketTestClient):
            def __init__(self, uri: str, max_reconnect_attempts: int = 3):
                super().__init__(uri)
                self.max_reconnect_attempts = max_reconnect_attempts
                self.reconnect_attempts = 0

            async def connect_with_retry(self, timeout: float = 30.0):
                """Connect with automatic retry on failure."""
                while self.reconnect_attempts < self.max_reconnect_attempts:
                    try:
                        await self.connect(timeout=timeout)
                        self.reconnect_attempts = 0  # Reset on successful connect
                        return
                    except Exception as e:
                        self.reconnect_attempts += 1
                        if self.reconnect_attempts >= self.max_reconnect_attempts:
                            raise
                        await asyncio.sleep(2 ** self.reconnect_attempts)  # Exponential backoff

            async def send_with_reconnect(self, message: Dict[str, Any]):
                """Send message with automatic reconnection on failure."""
                try:
                    await self.send_message(message)
                except (websockets.exceptions.ConnectionClosed, OSError):
                    # Reconnect and retry
                    await self.connect_with_retry()
                    if self.authenticated:
                        # Re-authenticate after reconnection
                        await self.authenticate("test_token")
                    await self.send_message(message)

        client = ReconnectingWebSocketClient("ws://localhost:8765")

        try:
            await client.connect_with_retry()
            await client.authenticate("test_token")

            # Simulate connection loss and recovery
            # (In real test, this would involve killing/restarting the server)

            # Verify messages can still be sent after reconnection
            await client.send_with_reconnect({
                "type": "test_after_reconnect"
            })

            # Wait for confirmation that reconnection worked
            response = await client.wait_for_message_type(
                "test_response",
                timeout=10.0
            )

            assert response["status"] == "success"

        finally:
            await client.close()


# ✅ Performance testing with WebSockets
class WebSocketPerformanceTest:
    """Test WebSocket performance with proper timing measurements."""

    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """Test WebSocket message throughput with timing analysis."""
        client = WebSocketTestClient("ws://localhost:8765")

        try:
            await client.connect()
            await client.authenticate("test_token")

            # Measure round-trip time for multiple messages
            message_count = 100
            start_time = asyncio.get_event_loop().time()

            # Send messages rapidly
            for i in range(message_count):
                await client.send_message({
                    "type": "echo",
                    "id": i,
                    "data": f"message_{i}"
                })

            # Wait for all echo responses
            await client.wait_for_condition(
                condition=lambda: len(client.get_messages_by_type("echo_response")) >= message_count,
                timeout=30.0,
                error_message=f"Not all {message_count} responses received"
            )

            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time

            # Performance assertions
            assert total_time < 10.0  # Should complete within 10 seconds
            avg_time_per_message = total_time / message_count
            assert avg_time_per_message < 0.1  # Average < 100ms per message

            print(f"Processed {message_count} messages in {total_time:.2f}s")
            print(f"Average time per message: {avg_time_per_message*1000:.2f}ms")

        finally:
            await client.close()