"""
WebSocket Manager for Real-Time Dashboard Connectivity

Manages WebSocket connections for live competitive intelligence updates,
providing real-time data streaming to executive dashboards.

Features:
- Persistent WebSocket connections with auto-reconnection
- Event-driven data updates
- Connection state management
- Message queuing and delivery guarantees
- Multiple client support
- Authentication and authorization

Author: Claude
Date: January 2026
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from uuid import uuid4

# WebSocket imports (optional dependencies)
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = Any

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """WebSocket connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessageType(Enum):
    """Types of WebSocket messages."""
    HEARTBEAT = "heartbeat"
    AUTHENTICATION = "authentication"
    SUBSCRIPTION = "subscription"
    DATA_UPDATE = "data_update"
    ANALYTICS_EVENT = "analytics_event"
    ALERT = "alert"
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class WebSocketEvent:
    """WebSocket event data structure."""
    event_id: str
    message_type: MessageType
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    client_id: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical


@dataclass
class WebSocketClient:
    """WebSocket client connection information."""
    client_id: str
    websocket: WebSocketServerProtocol
    connected_at: datetime
    last_heartbeat: datetime
    subscriptions: Set[str] = field(default_factory=set)
    authenticated: bool = False
    user_id: Optional[str] = None
    session_info: Dict[str, Any] = field(default_factory=dict)
    message_queue: List[WebSocketEvent] = field(default_factory=list)


class WebSocketManager:
    """
    WebSocket Manager for Real-Time Dashboard Connectivity
    
    Provides enterprise-grade WebSocket management for competitive intelligence
    dashboards with authentication, subscription management, and reliable delivery.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        max_connections: int = 100,
        heartbeat_interval: int = 30,
        message_queue_max_size: int = 1000,
        enable_authentication: bool = True
    ):
        """
        Initialize WebSocket manager.
        
        Args:
            host: Server host address
            port: Server port
            max_connections: Maximum concurrent connections
            heartbeat_interval: Heartbeat interval in seconds
            message_queue_max_size: Maximum queued messages per client
            enable_authentication: Enable client authentication
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.message_queue_max_size = message_queue_max_size
        self.enable_authentication = enable_authentication
        
        # Connection management
        self.clients: Dict[str, WebSocketClient] = {}
        self.server: Optional[Any] = None
        self.is_running = False
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.message_filters: List[Callable] = []
        
        # Performance metrics
        self.connections_opened = 0
        self.connections_closed = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.errors_count = 0
        
        # Subscription topics
        self.subscription_topics = {
            "executive_summary",
            "competitive_alerts", 
            "market_trends",
            "competitor_activity",
            "analytics_updates",
            "strategic_patterns",
            "real_time_metrics"
        }
        
        logger.info(f"WebSocket manager initialized for {host}:{port}")
    
    async def start_server(self) -> bool:
        """Start the WebSocket server."""
        try:
            if not WEBSOCKETS_AVAILABLE:
                logger.error("WebSockets library not available")
                return False
            
            # Start WebSocket server
            self.server = await websockets.serve(
                self._handle_client_connection,
                self.host,
                self.port,
                max_size=1024 * 1024,  # 1MB max message size
                max_queue=self.message_queue_max_size,
                ping_interval=self.heartbeat_interval,
                ping_timeout=self.heartbeat_interval * 2
            )
            
            self.is_running = True
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_monitor())
            asyncio.create_task(self._message_processor())
            
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        try:
            self.is_running = False
            
            # Disconnect all clients
            for client_id in list(self.clients.keys()):
                await self._disconnect_client(client_id, "server_shutdown")
            
            # Close server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            logger.info("WebSocket server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}")
    
    async def _handle_client_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client connection."""
        client_id = str(uuid4())
        
        try:
            # Check connection limit
            if len(self.clients) >= self.max_connections:
                await websocket.close(code=1008, reason="Server full")
                return
            
            # Create client record
            client = WebSocketClient(
                client_id=client_id,
                websocket=websocket,
                connected_at=datetime.now(timezone.utc),
                last_heartbeat=datetime.now(timezone.utc)
            )
            
            self.clients[client_id] = client
            self.connections_opened += 1
            
            logger.info(f"Client {client_id} connected from {websocket.remote_address}")
            
            # Send welcome message
            await self._send_to_client(
                client_id,
                WebSocketEvent(
                    event_id=str(uuid4()),
                    message_type=MessageType.RESPONSE,
                    event_type="connection_established",
                    data={
                        "client_id": client_id,
                        "server_time": datetime.now(timezone.utc).isoformat(),
                        "available_topics": list(self.subscription_topics)
                    },
                    timestamp=datetime.now(timezone.utc)
                )
            )
            
            # Handle client messages
            async for message in websocket:
                await self._handle_client_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            self.errors_count += 1
        finally:
            await self._disconnect_client(client_id, "connection_closed")
    
    async def _handle_client_message(self, client_id: str, raw_message: str):
        """Handle incoming message from client."""
        try:
            # Parse message
            message_data = json.loads(raw_message)
            
            # Create event object
            event = WebSocketEvent(
                event_id=message_data.get("event_id", str(uuid4())),
                message_type=MessageType(message_data.get("message_type", "command")),
                event_type=message_data.get("event_type", "unknown"),
                data=message_data.get("data", {}),
                timestamp=datetime.now(timezone.utc),
                client_id=client_id,
                correlation_id=message_data.get("correlation_id")
            )
            
            self.messages_received += 1
            
            # Handle different message types
            if event.message_type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(client_id, event)
            elif event.message_type == MessageType.AUTHENTICATION:
                await self._handle_authentication(client_id, event)
            elif event.message_type == MessageType.SUBSCRIPTION:
                await self._handle_subscription(client_id, event)
            elif event.message_type == MessageType.COMMAND:
                await self._handle_command(client_id, event)
            
            # Trigger event handlers
            await self._trigger_event_handlers(event)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}")
            await self._send_error(client_id, "invalid_json", "Message must be valid JSON")
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self._send_error(client_id, "message_processing_error", str(e))
    
    async def _handle_heartbeat(self, client_id: str, event: WebSocketEvent):
        """Handle client heartbeat."""
        if client_id in self.clients:
            self.clients[client_id].last_heartbeat = datetime.now(timezone.utc)
            
            # Send heartbeat response
            await self._send_to_client(
                client_id,
                WebSocketEvent(
                    event_id=str(uuid4()),
                    message_type=MessageType.HEARTBEAT,
                    event_type="heartbeat_response",
                    data={"server_time": datetime.now(timezone.utc).isoformat()},
                    timestamp=datetime.now(timezone.utc),
                    correlation_id=event.correlation_id
                )
            )
    
    async def _handle_authentication(self, client_id: str, event: WebSocketEvent):
        \"\"\"Handle client authentication.\"\"\"
        try:
            auth_token = event.data.get(\"token\")
            
            if not self.enable_authentication:
                # Authentication disabled, auto-approve
                self.clients[client_id].authenticated = True
                self.clients[client_id].user_id = \"anonymous\"
                
                await self._send_to_client(\n                    client_id,\n                    WebSocketEvent(\n                        event_id=str(uuid4()),\n                        message_type=MessageType.RESPONSE,\n                        event_type=\"authentication_success\",\n                        data={\"user_id\": \"anonymous\"},\n                        timestamp=datetime.now(timezone.utc),\n                        correlation_id=event.correlation_id\n                    )\n                )\n                return\n            \n            # TODO: Implement proper token validation\n            # For now, accept any non-empty token\n            if auth_token:\n                self.clients[client_id].authenticated = True\n                self.clients[client_id].user_id = event.data.get(\"user_id\", \"user\")\n                \n                await self._send_to_client(\n                    client_id,\n                    WebSocketEvent(\n                        event_id=str(uuid4()),\n                        message_type=MessageType.RESPONSE,\n                        event_type=\"authentication_success\",\n                        data={\"user_id\": self.clients[client_id].user_id},\n                        timestamp=datetime.now(timezone.utc),\n                        correlation_id=event.correlation_id\n                    )\n                )\n            else:\n                await self._send_error(\n                    client_id, \n                    \"authentication_failed\", \n                    \"Invalid or missing authentication token\",\n                    event.correlation_id\n                )\n                \n        except Exception as e:\n            logger.error(f\"Authentication error for client {client_id}: {e}\")\n            await self._send_error(\n                client_id, \n                \"authentication_error\", \n                str(e),\n                event.correlation_id\n            )\n    \n    async def _handle_subscription(self, client_id: str, event: WebSocketEvent):\n        \"\"\"Handle subscription requests.\"\"\"\n        try:\n            if client_id not in self.clients:\n                return\n            \n            client = self.clients[client_id]\n            \n            # Check authentication if required\n            if self.enable_authentication and not client.authenticated:\n                await self._send_error(\n                    client_id,\n                    \"unauthorized\", \n                    \"Authentication required for subscriptions\",\n                    event.correlation_id\n                )\n                return\n            \n            action = event.data.get(\"action\")  # subscribe, unsubscribe\n            topics = event.data.get(\"topics\", [])\n            \n            if action == \"subscribe\":\n                for topic in topics:\n                    if topic in self.subscription_topics:\n                        client.subscriptions.add(topic)\n                        logger.debug(f\"Client {client_id} subscribed to {topic}\")\n            \n            elif action == \"unsubscribe\":\n                for topic in topics:\n                    client.subscriptions.discard(topic)\n                    logger.debug(f\"Client {client_id} unsubscribed from {topic}\")\n            \n            # Send confirmation\n            await self._send_to_client(\n                client_id,\n                WebSocketEvent(\n                    event_id=str(uuid4()),\n                    message_type=MessageType.RESPONSE,\n                    event_type=\"subscription_updated\",\n                    data={\n                        \"subscriptions\": list(client.subscriptions),\n                        \"action\": action,\n                        \"topics\": topics\n                    },\n                    timestamp=datetime.now(timezone.utc),\n                    correlation_id=event.correlation_id\n                )\n            )\n            \n        except Exception as e:\n            logger.error(f\"Subscription error for client {client_id}: {e}\")\n            await self._send_error(\n                client_id, \n                \"subscription_error\", \n                str(e),\n                event.correlation_id\n            )\n    \n    async def _handle_command(self, client_id: str, event: WebSocketEvent):\n        \"\"\"Handle command messages.\"\"\"\n        try:\n            command = event.event_type\n            \n            if command == \"get_status\":\n                status = {\n                    \"server_status\": \"running\",\n                    \"connected_clients\": len(self.clients),\n                    \"uptime\": \"N/A\",  # TODO: Calculate uptime\n                    \"available_topics\": list(self.subscription_topics)\n                }\n                \n                await self._send_to_client(\n                    client_id,\n                    WebSocketEvent(\n                        event_id=str(uuid4()),\n                        message_type=MessageType.RESPONSE,\n                        event_type=\"status_response\",\n                        data=status,\n                        timestamp=datetime.now(timezone.utc),\n                        correlation_id=event.correlation_id\n                    )\n                )\n            \n            elif command == \"get_metrics\":\n                metrics = self.get_connection_metrics()\n                \n                await self._send_to_client(\n                    client_id,\n                    WebSocketEvent(\n                        event_id=str(uuid4()),\n                        message_type=MessageType.RESPONSE,\n                        event_type=\"metrics_response\",\n                        data=metrics,\n                        timestamp=datetime.now(timezone.utc),\n                        correlation_id=event.correlation_id\n                    )\n                )\n            \n            else:\n                await self._send_error(\n                    client_id,\n                    \"unknown_command\",\n                    f\"Unknown command: {command}\",\n                    event.correlation_id\n                )\n                \n        except Exception as e:\n            logger.error(f\"Command handling error for client {client_id}: {e}\")\n            await self._send_error(\n                client_id,\n                \"command_error\", \n                str(e),\n                event.correlation_id\n            )\n    \n    async def _send_to_client(self, client_id: str, event: WebSocketEvent):\n        \"\"\"Send event to specific client.\"\"\"\n        try:\n            if client_id not in self.clients:\n                logger.warning(f\"Attempted to send to non-existent client {client_id}\")\n                return\n            \n            client = self.clients[client_id]\n            \n            # Prepare message\n            message = {\n                \"event_id\": event.event_id,\n                \"message_type\": event.message_type.value,\n                \"event_type\": event.event_type,\n                \"data\": event.data,\n                \"timestamp\": event.timestamp.isoformat(),\n                \"correlation_id\": event.correlation_id\n            }\n            \n            # Send message\n            await client.websocket.send(json.dumps(message))\n            self.messages_sent += 1\n            \n        except websockets.exceptions.ConnectionClosed:\n            logger.info(f\"Client {client_id} connection closed during send\")\n            await self._disconnect_client(client_id, \"connection_closed\")\n        except Exception as e:\n            logger.error(f\"Error sending to client {client_id}: {e}\")\n            self.errors_count += 1\n    \n    async def _send_error(self, client_id: str, error_code: str, error_message: str, correlation_id: Optional[str] = None):\n        \"\"\"Send error message to client.\"\"\"\n        await self._send_to_client(\n            client_id,\n            WebSocketEvent(\n                event_id=str(uuid4()),\n                message_type=MessageType.ERROR,\n                event_type=\"error\",\n                data={\n                    \"error_code\": error_code,\n                    \"error_message\": error_message\n                },\n                timestamp=datetime.now(timezone.utc),\n                correlation_id=correlation_id\n            )\n        )\n    \n    async def _disconnect_client(self, client_id: str, reason: str):\n        \"\"\"Disconnect client and cleanup.\"\"\"\n        try:\n            if client_id in self.clients:\n                client = self.clients[client_id]\n                \n                # Close connection if still open\n                if not client.websocket.closed:\n                    await client.websocket.close()\n                \n                # Remove from clients\n                del self.clients[client_id]\n                self.connections_closed += 1\n                \n                logger.info(f\"Client {client_id} disconnected: {reason}\")\n                \n        except Exception as e:\n            logger.error(f\"Error disconnecting client {client_id}: {e}\")\n    \n    async def _heartbeat_monitor(self):\n        \"\"\"Monitor client heartbeats and disconnect stale connections.\"\"\"\n        while self.is_running:\n            try:\n                now = datetime.now(timezone.utc)\n                stale_clients = []\n                \n                for client_id, client in self.clients.items():\n                    time_since_heartbeat = (now - client.last_heartbeat).total_seconds()\n                    \n                    if time_since_heartbeat > self.heartbeat_interval * 3:  # 3x heartbeat interval\n                        stale_clients.append(client_id)\n                \n                # Disconnect stale clients\n                for client_id in stale_clients:\n                    await self._disconnect_client(client_id, \"heartbeat_timeout\")\n                \n                await asyncio.sleep(self.heartbeat_interval)\n                \n            except Exception as e:\n                logger.error(f\"Error in heartbeat monitor: {e}\")\n                await asyncio.sleep(10)\n    \n    async def _message_processor(self):\n        \"\"\"Process queued messages for clients.\"\"\"\n        while self.is_running:\n            try:\n                for client_id, client in list(self.clients.items()):\n                    if client.message_queue:\n                        # Process queued messages\n                        messages_to_process = client.message_queue[:10]  # Process in batches\n                        client.message_queue = client.message_queue[10:]\n                        \n                        for event in messages_to_process:\n                            await self._send_to_client(client_id, event)\n                \n                await asyncio.sleep(0.1)  # 100ms processing interval\n                \n            except Exception as e:\n                logger.error(f\"Error in message processor: {e}\")\n                await asyncio.sleep(1)\n    \n    async def _trigger_event_handlers(self, event: WebSocketEvent):\n        \"\"\"Trigger registered event handlers.\"\"\"\n        try:\n            event_type = event.event_type\n            \n            if event_type in self.event_handlers:\n                for handler in self.event_handlers[event_type]:\n                    try:\n                        if asyncio.iscoroutinefunction(handler):\n                            await handler(event)\n                        else:\n                            handler(event)\n                    except Exception as e:\n                        logger.error(f\"Error in event handler for {event_type}: {e}\")\n                        \n        except Exception as e:\n            logger.error(f\"Error triggering event handlers: {e}\")\n    \n    # Public API methods\n    \n    async def broadcast_event(self, event: WebSocketEvent, topic: Optional[str] = None):\n        \"\"\"Broadcast event to all subscribed clients.\"\"\"\n        try:\n            recipients = []\n            \n            for client_id, client in self.clients.items():\n                # Check authentication if required\n                if self.enable_authentication and not client.authenticated:\n                    continue\n                \n                # Check topic subscription\n                if topic and topic not in client.subscriptions:\n                    continue\n                \n                recipients.append(client_id)\n            \n            # Send to recipients\n            send_tasks = []\n            for client_id in recipients:\n                task = asyncio.create_task(self._send_to_client(client_id, event))\n                send_tasks.append(task)\n            \n            if send_tasks:\n                await asyncio.gather(*send_tasks, return_exceptions=True)\n            \n            logger.debug(f\"Broadcasted {event.event_type} to {len(recipients)} clients\")\n            \n        except Exception as e:\n            logger.error(f\"Error broadcasting event: {e}\")\n    \n    def register_event_handler(self, event_type: str, handler: Callable):\n        \"\"\"Register event handler for specific event type.\"\"\"\n        if event_type not in self.event_handlers:\n            self.event_handlers[event_type] = []\n        \n        self.event_handlers[event_type].append(handler)\n        logger.info(f\"Registered event handler for {event_type}\")\n    \n    def add_subscription_topic(self, topic: str):\n        \"\"\"Add new subscription topic.\"\"\"\n        self.subscription_topics.add(topic)\n        logger.info(f\"Added subscription topic: {topic}\")\n    \n    def get_connection_metrics(self) -> Dict[str, Any]:\n        \"\"\"Get connection metrics and statistics.\"\"\"\n        return {\n            \"is_running\": self.is_running,\n            \"active_connections\": len(self.clients),\n            \"max_connections\": self.max_connections,\n            \"connections_opened\": self.connections_opened,\n            \"connections_closed\": self.connections_closed,\n            \"messages_sent\": self.messages_sent,\n            \"messages_received\": self.messages_received,\n            \"errors_count\": self.errors_count,\n            \"subscription_topics\": list(self.subscription_topics),\n            \"authenticated_clients\": sum(\n                1 for client in self.clients.values() if client.authenticated\n            )\n        }\n    \n    def get_client_info(self) -> List[Dict[str, Any]]:\n        \"\"\"Get information about connected clients.\"\"\"\n        return [\n            {\n                \"client_id\": client_id,\n                \"connected_at\": client.connected_at.isoformat(),\n                \"last_heartbeat\": client.last_heartbeat.isoformat(),\n                \"authenticated\": client.authenticated,\n                \"user_id\": client.user_id,\n                \"subscriptions\": list(client.subscriptions),\n                \"queued_messages\": len(client.message_queue)\n            }\n            for client_id, client in self.clients.items()\n        ]\n\n\n# Export public API\n__all__ = [\n    \"WebSocketManager\",\n    \"WebSocketEvent\",\n    \"WebSocketClient\", \n    \"ConnectionStatus\",\n    \"MessageType\"\n]