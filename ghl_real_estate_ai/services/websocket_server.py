"""
Real-Time WebSocket Server for Jorge's Real Estate AI Dashboard.

Provides real-time communication infrastructure with:
- JWT-based authentication for WebSocket connections
- Role-based event filtering and broadcasting
- Connection management with heartbeat monitoring
- Event publishing system for live dashboard updates
- Performance monitoring and metrics collection

Features enterprise-grade reliability with automatic reconnection,
connection pooling, and comprehensive error handling.
"""

import json
import asyncio
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from datetime import datetime, timezone
import logging

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auth_service import get_auth_service, UserRole
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)

class EventType(Enum):
    """Event types for real-time broadcasting."""
    LEAD_UPDATE = "lead_update"
    CONVERSATION_UPDATE = "conversation_update"
    COMMISSION_UPDATE = "commission_update"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_UPDATE = "performance_update"
    USER_ACTIVITY = "user_activity"
    DASHBOARD_REFRESH = "dashboard_refresh"
    PROPERTY_ALERT = "property_alert"  # Real-time property matching alerts
    LEAD_METRIC_UPDATE = "lead_metric_update"  # Updates to pcs_score or temperature

    # Jorge Bot Ecosystem Events
    BOT_STATUS_UPDATE = "bot_status_update"
    JORGE_QUALIFICATION_PROGRESS = "jorge_qualification_progress"
    LEAD_BOT_SEQUENCE_UPDATE = "lead_bot_sequence_update"
    INTENT_ANALYSIS_COMPLETE = "intent_analysis_complete"
    CONVERSATION_EVENT = "conversation_event"
    SYSTEM_HEALTH_UPDATE = "system_health_update"

    # Buyer Bot Events
    BUYER_INTENT_ANALYSIS = "buyer_intent_analysis"
    BUYER_QUALIFICATION_PROGRESS = "buyer_qualification_progress"
    BUYER_QUALIFICATION_COMPLETE = "buyer_qualification_complete"
    BUYER_FOLLOW_UP_SCHEDULED = "buyer_follow_up_scheduled"
    PROPERTY_MATCH_UPDATE = "property_match_update"

    # SMS Compliance Events
    SMS_COMPLIANCE = "sms_compliance"
    SMS_OPT_OUT_PROCESSED = "sms_opt_out_processed"
    SMS_FREQUENCY_LIMIT_HIT = "sms_frequency_limit_hit"

    # Bot Coordination Events
    BOT_HANDOFF_REQUEST = "bot_handoff_request"
    BOT_HANDOFF_ACCEPTED = "bot_handoff_accepted"
    BOT_HANDOFF_COMPLETED = "bot_handoff_completed"
    COACHING_OPPORTUNITY_DETECTED = "coaching_opportunity_detected"
    COACHING_ACCEPTED = "coaching_accepted"
    CONTEXT_SYNC_UPDATE = "context_sync_update"
    COORDINATION_STATUS_UPDATE = "coordination_status_update"
    OMNIPRESENT_INTELLIGENCE_UPDATE = "omnipresent_intelligence_update"
    COORDINATION_PERFORMANCE_METRICS = "coordination_performance_metrics"

class ConnectionStatus(Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class WebSocketClient:
    """WebSocket client connection information."""
    websocket: WebSocket
    user_id: int
    username: str
    role: UserRole
    connected_at: datetime
    last_heartbeat: datetime
    location_id: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    subscribed_events: Set[EventType] = None

    def __post_init__(self):
        if self.subscribed_events is None:
            self.subscribed_events = set()

@dataclass 
class RealTimeEvent:
    """Real-time event data structure."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[int] = None
    location_id: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "location_id": self.location_id,
            "priority": self.priority
        }

class WebSocketManager:
    """
    Enterprise WebSocket Connection Manager.
    
    Features:
    - JWT authentication for secure connections
    - Role-based access control and event filtering  
    - Connection pooling with automatic cleanup
    - Heartbeat monitoring for connection health
    - Event broadcasting with subscriber filtering
    - Performance metrics and monitoring
    """
    
    def __init__(self):
        # Connection management
        self.active_connections: Dict[str, WebSocketClient] = {}
        self.connections_by_user: Dict[int, Set[str]] = {}
        self.connections_by_role: Dict[UserRole, Set[str]] = {}
        
        # Services
        self.auth_service = get_auth_service()
        self.cache_service = get_cache_service()
        
        # Performance metrics
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "events_published": 0,
            "authentication_failures": 0,
            "connection_errors": 0,
            "heartbeat_failures": 0
        }
        
        # Heartbeat configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60   # seconds
        self._heartbeat_task = None
        
        # Event publishing
        self.event_queue = asyncio.Queue()
        self._event_processor_task = None
        
        logger.info("WebSocket Manager initialized")

    async def start_services(self):
        """Start background services for heartbeat and event processing."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
        if self._event_processor_task is None:
            self._event_processor_task = asyncio.create_task(self._event_processor())
            
        logger.info("WebSocket background services started")

    async def stop_services(self):
        """Stop background services."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            
        if self._event_processor_task:
            self._event_processor_task.cancel()
            self._event_processor_task = None
            
        logger.info("WebSocket background services stopped")

    async def authenticate_websocket(self, websocket: WebSocket, token: str) -> Optional[WebSocketClient]:
        """
        Authenticate WebSocket connection using JWT token.
        
        Args:
            websocket: WebSocket connection
            token: JWT authentication token
            
        Returns:
            WebSocketClient if authentication successful, None otherwise
        """
        try:
            # Verify JWT token
            payload = self.auth_service.verify_token(token)
            if not payload:
                logger.warning("WebSocket authentication failed: Invalid token")
                self.metrics["authentication_failures"] += 1
                return None
                
            # Get user information
            user = await self.auth_service.get_user_by_id(payload["user_id"])
            if not user or not user.is_active:
                logger.warning(f"WebSocket authentication failed: User {payload.get('user_id')} not found or inactive")
                self.metrics["authentication_failures"] += 1
                return None
                
            # Create client connection
            client = WebSocketClient(
                websocket=websocket,
                user_id=user.id,
                username=user.username,
                role=user.role,
                connected_at=datetime.now(timezone.utc),
                last_heartbeat=datetime.now(timezone.utc),
                status=ConnectionStatus.AUTHENTICATED
            )
            
            # Set default subscriptions based on role
            client.subscribed_events = self._get_default_subscriptions(user.role)
            
            logger.info(f"WebSocket authenticated successfully for user {user.username} (role: {user.role.value})")
            return client
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            self.metrics["authentication_failures"] += 1
            return None

    def _get_default_subscriptions(self, role: UserRole) -> Set[EventType]:
        """Get default event subscriptions based on user role."""
        if role == UserRole.ADMIN:
            # Admin sees all events
            return set(EventType)
        elif role == UserRole.AGENT:
            # Agent sees business-relevant events including Jorge bot ecosystem
            return {
                EventType.LEAD_UPDATE,
                EventType.CONVERSATION_UPDATE,
                EventType.COMMISSION_UPDATE,
                EventType.DASHBOARD_REFRESH,
                EventType.PERFORMANCE_UPDATE,
                EventType.PROPERTY_ALERT,
                # Key Jorge bot events for agents
                EventType.BOT_STATUS_UPDATE,
                EventType.JORGE_QUALIFICATION_PROGRESS,
                EventType.LEAD_BOT_SEQUENCE_UPDATE,
                EventType.CONVERSATION_EVENT,
                EventType.BOT_HANDOFF_REQUEST,
                EventType.COACHING_OPPORTUNITY_DETECTED
            }
        else:  # VIEWER
            # Viewer sees limited read-only events
            return {
                EventType.DASHBOARD_REFRESH,
                EventType.SYSTEM_ALERT,
                EventType.SYSTEM_HEALTH_UPDATE,
                EventType.BOT_STATUS_UPDATE
            }

    async def connect(self, websocket: WebSocket, client: WebSocketClient) -> str:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client: Authenticated client information
            
        Returns:
            Connection ID for tracking
        """
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = f"{client.user_id}_{int(time.time())}_{id(websocket)}"
        
        # Store connection
        self.active_connections[connection_id] = client
        
        # Index by user
        if client.user_id not in self.connections_by_user:
            self.connections_by_user[client.user_id] = set()
        self.connections_by_user[client.user_id].add(connection_id)
        
        # Index by role  
        if client.role not in self.connections_by_role:
            self.connections_by_role[client.role] = set()
        self.connections_by_role[client.role].add(connection_id)
        
        # Update metrics
        self.metrics["total_connections"] += 1
        self.metrics["active_connections"] = len(self.active_connections)
        
        # Cache connection info for monitoring
        await self.cache_service.set(
            f"websocket:connection:{connection_id}",
            {
                "user_id": client.user_id,
                "username": client.username,
                "role": client.role.value,
                "connected_at": client.connected_at.isoformat(),
                "status": client.status.value
            },
            ttl=3600  # 1 hour
        )
        
        # Send welcome message
        await self.send_personal_message(connection_id, {
            "type": "connection_established",
            "message": f"Welcome, {client.username}! Real-time updates are now active.",
            "connection_id": connection_id,
            "subscriptions": [event.value for event in client.subscribed_events],
            "server_time": datetime.now(timezone.utc).isoformat()
        })
        
        # Broadcast user connection event
        await self.broadcast_event(RealTimeEvent(
            event_type=EventType.USER_ACTIVITY,
            data={
                "action": "user_connected",
                "username": client.username,
                "role": client.role.value,
                "timestamp": client.connected_at.isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            priority="low"
        ), target_roles={UserRole.ADMIN})
        
        logger.info(f"WebSocket connected: {client.username} (ID: {connection_id}, Role: {client.role.value})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
        """
        if connection_id not in self.active_connections:
            return
            
        client = self.active_connections[connection_id]
        
        # Remove from indexes
        del self.active_connections[connection_id]
        
        if client.user_id in self.connections_by_user:
            self.connections_by_user[client.user_id].discard(connection_id)
            if not self.connections_by_user[client.user_id]:
                del self.connections_by_user[client.user_id]
                
        if client.role in self.connections_by_role:
            self.connections_by_role[client.role].discard(connection_id)
            if not self.connections_by_role[client.role]:
                del self.connections_by_role[client.role]
        
        # Update metrics
        self.metrics["active_connections"] = len(self.active_connections)
        
        # Clean up cache
        await self.cache_service.delete(f"websocket:connection:{connection_id}")
        
        # Broadcast user disconnection
        await self.broadcast_event(RealTimeEvent(
            event_type=EventType.USER_ACTIVITY,
            data={
                "action": "user_disconnected", 
                "username": client.username,
                "role": client.role.value,
                "session_duration": (datetime.now(timezone.utc) - client.connected_at).total_seconds()
            },
            timestamp=datetime.now(timezone.utc),
            priority="low"
        ), target_roles={UserRole.ADMIN})
        
        logger.info(f"WebSocket disconnected: {client.username} (ID: {connection_id})")

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """
        Send message to specific connection.
        
        Args:
            connection_id: Target connection ID
            message: Message data to send
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Attempt to send message to non-existent connection: {connection_id}")
            return
            
        client = self.active_connections[connection_id]
        
        try:
            await client.websocket.send_text(json.dumps(message))
            self.metrics["messages_sent"] += 1
            
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            self.metrics["connection_errors"] += 1
            await self.disconnect(connection_id)

    async def broadcast_event(
        self,
        event: RealTimeEvent,
        target_users: Optional[Set[int]] = None,
        target_roles: Optional[Set[UserRole]] = None,
        exclude_user: Optional[int] = None
    ):
        """
        Broadcast event to all or filtered connections.
        
        Args:
            event: Event to broadcast
            target_users: Specific user IDs to target (optional)
            target_roles: Specific roles to target (optional) 
            exclude_user: User ID to exclude from broadcast (optional)
        """
        self.metrics["events_published"] += 1
        
        # Determine target connections
        target_connections = set()
        
        if target_users:
            # Target specific users
            for user_id in target_users:
                if user_id in self.connections_by_user:
                    target_connections.update(self.connections_by_user[user_id])
                    
        elif target_roles:
            # Target specific roles
            for role in target_roles:
                if role in self.connections_by_role:
                    target_connections.update(self.connections_by_role[role])
        else:
            # Target all connections
            target_connections = set(self.active_connections.keys())
        
        # Apply filters
        filtered_connections = []
        for connection_id in target_connections:
            client = self.active_connections.get(connection_id)
            if not client:
                continue
                
            # Exclude specific user
            if exclude_user and client.user_id == exclude_user:
                continue
                
            # Check event subscription
            if event.event_type not in client.subscribed_events:
                continue
                
            # Check role permissions
            if not self._can_user_receive_event(client.role, event.event_type):
                continue
                
            filtered_connections.append(connection_id)
        
        # Send to all target connections
        message = {
            "type": "real_time_event",
            "event": event.to_dict()
        }
        
        # Use asyncio.gather for concurrent sending
        send_tasks = [
            self.send_personal_message(connection_id, message)
            for connection_id in filtered_connections
        ]
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
            
        logger.debug(f"Broadcasted {event.event_type.value} to {len(filtered_connections)} connections")

    def _can_user_receive_event(self, role: UserRole, event_type: EventType) -> bool:
        """Check if user role can receive specific event type."""
        if role == UserRole.ADMIN:
            return True
            
        # Define role permissions for events
        role_permissions = {
            UserRole.AGENT: {
                EventType.LEAD_UPDATE,
                EventType.CONVERSATION_UPDATE,
                EventType.COMMISSION_UPDATE,
                EventType.PERFORMANCE_UPDATE,
                EventType.DASHBOARD_REFRESH,
                EventType.SYSTEM_ALERT,
                EventType.PROPERTY_ALERT,
                EventType.LEAD_METRIC_UPDATE,
                # Jorge Bot Ecosystem Events
                EventType.BOT_STATUS_UPDATE,
                EventType.JORGE_QUALIFICATION_PROGRESS,
                EventType.LEAD_BOT_SEQUENCE_UPDATE,
                EventType.INTENT_ANALYSIS_COMPLETE,
                EventType.CONVERSATION_EVENT,
                EventType.SYSTEM_HEALTH_UPDATE,
                # Bot Coordination Events (limited access)
                EventType.BOT_HANDOFF_REQUEST,
                EventType.BOT_HANDOFF_COMPLETED,
                EventType.COACHING_OPPORTUNITY_DETECTED,
                EventType.COORDINATION_STATUS_UPDATE
            },
            UserRole.VIEWER: {
                EventType.DASHBOARD_REFRESH,
                EventType.SYSTEM_ALERT,
                EventType.PERFORMANCE_UPDATE,
                EventType.SYSTEM_HEALTH_UPDATE,
                EventType.BOT_STATUS_UPDATE
            }
        }
        
        return event_type in role_permissions.get(role, set())

    async def handle_client_message(self, connection_id: str, message_data: Dict[str, Any]):
        """
        Handle incoming message from WebSocket client.
        
        Args:
            connection_id: Client connection ID
            message_data: Parsed message data
        """
        if connection_id not in self.active_connections:
            return
            
        client = self.active_connections[connection_id]
        message_type = message_data.get("type")
        
        try:
            if message_type == "heartbeat":
                # Update heartbeat timestamp
                client.last_heartbeat = datetime.now(timezone.utc)
                await self.send_personal_message(connection_id, {
                    "type": "heartbeat_ack",
                    "timestamp": client.last_heartbeat.isoformat()
                })
                
            elif message_type == "subscribe":
                # Update event subscriptions
                events = message_data.get("events", [])
                for event_name in events:
                    try:
                        event_type = EventType(event_name)
                        if self._can_user_receive_event(client.role, event_type):
                            client.subscribed_events.add(event_type)
                    except ValueError:
                        logger.warning(f"Invalid event type in subscription: {event_name}")
                        
                await self.send_personal_message(connection_id, {
                    "type": "subscription_updated",
                    "subscriptions": [event.value for event in client.subscribed_events]
                })
                
            elif message_type == "unsubscribe":
                # Remove event subscriptions
                events = message_data.get("events", [])
                for event_name in events:
                    try:
                        event_type = EventType(event_name)
                        client.subscribed_events.discard(event_type)
                    except ValueError:
                        pass
                        
                await self.send_personal_message(connection_id, {
                    "type": "subscription_updated", 
                    "subscriptions": [event.value for event in client.subscribed_events]
                })
                
            elif message_type == "get_status":
                # Send connection status
                await self.send_personal_message(connection_id, {
                    "type": "status",
                    "connection_id": connection_id,
                    "user": {
                        "id": client.user_id,
                        "username": client.username,
                        "role": client.role.value
                    },
                    "connected_at": client.connected_at.isoformat(),
                    "last_heartbeat": client.last_heartbeat.isoformat(),
                    "subscriptions": [event.value for event in client.subscribed_events],
                    "metrics": self.get_metrics()
                })
                
            else:
                logger.warning(f"Unknown message type from {connection_id}: {message_type}")
                
            self.metrics["messages_received"] += 1
            
        except Exception as e:
            logger.error(f"Error handling client message from {connection_id}: {e}")

    async def _heartbeat_monitor(self):
        """Background task to monitor connection health via heartbeats."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                current_time = datetime.now(timezone.utc)
                stale_connections = []
                
                for connection_id, client in self.active_connections.items():
                    time_since_heartbeat = (current_time - client.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        stale_connections.append(connection_id)
                        logger.warning(f"Stale connection detected: {connection_id} (last heartbeat: {time_since_heartbeat}s ago)")
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    self.metrics["heartbeat_failures"] += 1
                    await self.disconnect(connection_id)
                    
            except asyncio.CancelledError:
                logger.info("Heartbeat monitor task cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")

    async def _event_processor(self):
        """Background task to process queued events."""
        while True:
            try:
                # Get event from queue (blocks until available)
                event = await self.event_queue.get()
                
                # Broadcast event
                await self.broadcast_event(event)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Event processor task cancelled")
                break
            except Exception as e:
                logger.error(f"Event processor error: {e}")

    async def publish_event(self, event: RealTimeEvent):
        """
        Queue event for broadcasting.
        
        Args:
            event: Event to publish
        """
        await self.event_queue.put(event)

    def get_metrics(self) -> Dict[str, Any]:
        """Get WebSocket performance metrics."""
        return {
            **self.metrics,
            "active_connections_by_role": {
                role.value: len(connections) 
                for role, connections in self.connections_by_role.items()
            },
            "queue_size": self.event_queue.qsize(),
            "uptime_seconds": time.time() - (self.metrics.get("start_time", time.time()))
        }

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        return [
            {
                "connection_id": connection_id,
                "user_id": client.user_id,
                "username": client.username,
                "role": client.role.value,
                "connected_at": client.connected_at.isoformat(),
                "last_heartbeat": client.last_heartbeat.isoformat(),
                "subscriptions": [event.value for event in client.subscribed_events],
                "status": client.status.value
            }
            for connection_id, client in self.active_connections.items()
        ]

# Global WebSocket manager instance
_websocket_manager = None

def get_websocket_manager() -> WebSocketManager:
    """Get singleton WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager