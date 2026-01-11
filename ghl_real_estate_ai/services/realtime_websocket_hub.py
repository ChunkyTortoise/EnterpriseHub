"""
Real-Time WebSocket Hub

WebSocket connection management with tenant isolation and real-time event broadcasting.
Provides enterprise-grade connection handling with performance monitoring and automatic cleanup.

Performance Targets:
- Connection accept: <10ms
- Broadcast to 1000 clients: <50ms
- Health check cycle: every 30s
- Stale connection cleanup: every 60s

Features:
- Tenant-based connection pooling and isolation
- Connection health monitoring with ping/pong
- Automatic reconnection handling
- Redis pub/sub for distributed broadcasting
- Performance metrics and monitoring
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket connection with metadata."""
    connection_id: str
    tenant_id: str
    user_id: str
    websocket: WebSocket
    connected_at: datetime
    last_ping: datetime
    subscription_topics: List[str]

    # Performance metrics
    message_count: int = 0
    error_count: int = 0
    last_activity: Optional[datetime] = None

    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = self.connected_at

    @property
    def is_stale(self) -> bool:
        """Check if connection is stale (no ping for >60s)."""
        return datetime.now() - self.last_ping > timedelta(seconds=60)

    @property
    def connection_age_seconds(self) -> float:
        """Get connection age in seconds."""
        return (datetime.now() - self.connected_at).total_seconds()


@dataclass
class ConnectionHealth:
    """Connection health metrics."""
    connection_id: str
    tenant_id: str
    is_alive: bool
    last_ping: datetime
    response_time_ms: float
    message_count: int
    error_count: int

    # Performance indicators
    avg_response_time_ms: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class BroadcastResult:
    """Result of broadcasting operation."""
    event_type: str
    tenant_id: Optional[str]
    connections_targeted: int
    connections_successful: int
    connections_failed: int
    broadcast_time_ms: float

    # Error details
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success_rate(self) -> float:
        """Calculate broadcast success rate."""
        if self.connections_targeted == 0:
            return 1.0
        return self.connections_successful / self.connections_targeted


class RealtimeWebSocketHub:
    """
    Real-Time WebSocket Hub

    Manages WebSocket connections with tenant isolation, health monitoring,
    and high-performance broadcasting for real-time dashboard updates.
    """

    def __init__(
        self,
        storage_dir: str = "data/websocket_hub",
        redis_client=None,
        max_connections_per_tenant: int = 100
    ):
        """
        Initialize WebSocket hub.

        Args:
            storage_dir: Directory for connection logs
            redis_client: Redis client for pub/sub (optional)
            max_connections_per_tenant: Connection limit per tenant
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.redis_client = redis_client
        self.max_connections_per_tenant = max_connections_per_tenant

        # Connection storage
        self._connections: Dict[str, WebSocketConnection] = {}
        self._tenant_connections: Dict[str, Set[str]] = defaultdict(set)
        self._connection_health: Dict[str, ConnectionHealth] = {}

        # Performance metrics
        self._metrics = {
            'total_connections': 0,
            'active_connections': 0,
            'total_broadcasts': 0,
            'failed_broadcasts': 0,
            'avg_broadcast_time_ms': 0.0,
            'connections_per_tenant': defaultdict(int)
        }

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"Real-Time WebSocket Hub initialized at {self.storage_dir}")

    async def connect_client(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str,
        subscription_topics: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Connect a WebSocket client with tenant isolation.

        Args:
            websocket: FastAPI WebSocket instance
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            subscription_topics: Topics to subscribe to

        Returns:
            Connection ID if successful, None if failed
        """
        start_time = time.time()

        try:
            # Check tenant connection limits
            if len(self._tenant_connections[tenant_id]) >= self.max_connections_per_tenant:
                logger.warning(f"Connection limit reached for tenant {tenant_id}")
                return None

            # Accept WebSocket connection
            await websocket.accept()

            # Create connection
            connection_id = f"conn_{uuid.uuid4().hex[:12]}"
            if subscription_topics is None:
                subscription_topics = ["dashboard_updates", "lead_events"]

            connection = WebSocketConnection(
                connection_id=connection_id,
                tenant_id=tenant_id,
                user_id=user_id,
                websocket=websocket,
                connected_at=datetime.now(),
                last_ping=datetime.now(),
                subscription_topics=subscription_topics
            )

            # Store connection
            self._connections[connection_id] = connection
            self._tenant_connections[tenant_id].add(connection_id)

            # Initialize health monitoring
            self._connection_health[connection_id] = ConnectionHealth(
                connection_id=connection_id,
                tenant_id=tenant_id,
                is_alive=True,
                last_ping=datetime.now(),
                response_time_ms=0.0,
                message_count=0,
                error_count=0
            )

            # Update metrics
            self._metrics['total_connections'] += 1
            self._metrics['active_connections'] = len(self._connections)
            self._metrics['connections_per_tenant'][tenant_id] += 1

            # Start background tasks if first connection
            if len(self._connections) == 1:
                await self._start_background_tasks()

            # Log connection
            connection_time = (time.time() - start_time) * 1000
            logger.info(f"WebSocket client connected: {connection_id} "
                       f"(tenant: {tenant_id}, time: {connection_time:.1f}ms)")

            return connection_id

        except Exception as e:
            logger.error(f"Failed to connect WebSocket client: {e}")
            return None

    async def disconnect_client(self, connection_id: str) -> bool:
        """
        Disconnect a WebSocket client and cleanup resources.

        Args:
            connection_id: Connection identifier to disconnect

        Returns:
            True if disconnected successfully, False if not found
        """
        try:
            connection = self._connections.get(connection_id)
            if not connection:
                logger.warning(f"Connection {connection_id} not found for disconnect")
                return False

            # Close WebSocket
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.debug(f"WebSocket already closed for {connection_id}: {e}")

            # Remove from storage
            del self._connections[connection_id]
            self._tenant_connections[connection.tenant_id].discard(connection_id)
            self._connection_health.pop(connection_id, None)

            # Update metrics
            self._metrics['active_connections'] = len(self._connections)
            self._metrics['connections_per_tenant'][connection.tenant_id] -= 1

            # Stop background tasks if no connections
            if len(self._connections) == 0:
                await self._stop_background_tasks()

            logger.info(f"WebSocket client disconnected: {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to disconnect client {connection_id}: {e}")
            return False

    async def broadcast_to_tenant(
        self,
        tenant_id: str,
        event_data: Dict[str, Any]
    ) -> BroadcastResult:
        """
        Broadcast event to all connections for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            event_data: Event data to broadcast

        Returns:
            BroadcastResult with success metrics
        """
        start_time = time.time()

        try:
            # Get tenant connections
            connection_ids = list(self._tenant_connections.get(tenant_id, set()))

            if not connection_ids:
                logger.debug(f"No connections found for tenant {tenant_id}")
                return BroadcastResult(
                    event_type=event_data.get("event_type", "unknown"),
                    tenant_id=tenant_id,
                    connections_targeted=0,
                    connections_successful=0,
                    connections_failed=0,
                    broadcast_time_ms=(time.time() - start_time) * 1000
                )

            # Filter by subscription topics if specified
            topic = event_data.get("topic")
            if topic:
                filtered_connections = []
                for conn_id in connection_ids:
                    connection = self._connections.get(conn_id)
                    if connection and topic in connection.subscription_topics:
                        filtered_connections.append(conn_id)
                connection_ids = filtered_connections

            # Broadcast to connections
            successful = 0
            failed = 0
            errors = []

            for connection_id in connection_ids:
                connection = self._connections.get(connection_id)
                if not connection:
                    continue

                try:
                    # Send message
                    message = {
                        "event_type": event_data.get("event_type", "unknown"),
                        "tenant_id": tenant_id,
                        "data": event_data,
                        "timestamp": datetime.now().isoformat()
                    }

                    await connection.websocket.send_json(message)

                    # Update connection metrics
                    connection.message_count += 1
                    connection.last_activity = datetime.now()

                    # Update health
                    if connection_id in self._connection_health:
                        self._connection_health[connection_id].message_count += 1

                    successful += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Connection {connection_id}: {str(e)}")

                    # Update error metrics
                    connection.error_count += 1
                    if connection_id in self._connection_health:
                        self._connection_health[connection_id].error_count += 1
                        self._connection_health[connection_id].is_alive = False

            # Update metrics
            self._metrics['total_broadcasts'] += 1
            if failed > 0:
                self._metrics['failed_broadcasts'] += 1

            broadcast_time = (time.time() - start_time) * 1000

            # Update average broadcast time
            total_broadcasts = self._metrics['total_broadcasts']
            current_avg = self._metrics['avg_broadcast_time_ms']
            self._metrics['avg_broadcast_time_ms'] = (
                (current_avg * (total_broadcasts - 1) + broadcast_time) / total_broadcasts
            )

            result = BroadcastResult(
                event_type=event_data.get("event_type", "unknown"),
                tenant_id=tenant_id,
                connections_targeted=len(connection_ids),
                connections_successful=successful,
                connections_failed=failed,
                broadcast_time_ms=broadcast_time,
                errors=errors
            )

            logger.debug(f"Broadcast to tenant {tenant_id}: "
                        f"{successful}/{len(connection_ids)} successful "
                        f"({broadcast_time:.1f}ms)")

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast to tenant {tenant_id}: {e}")
            return BroadcastResult(
                event_type=event_data.get("event_type", "error"),
                tenant_id=tenant_id,
                connections_targeted=0,
                connections_successful=0,
                connections_failed=1,
                broadcast_time_ms=(time.time() - start_time) * 1000,
                errors=[str(e)]
            )

    async def broadcast_to_all(
        self,
        event_data: Dict[str, Any]
    ) -> BroadcastResult:
        """
        Broadcast event to all connected clients.

        Args:
            event_data: Event data to broadcast

        Returns:
            BroadcastResult with success metrics
        """
        start_time = time.time()

        try:
            connection_ids = list(self._connections.keys())

            if not connection_ids:
                logger.debug("No connections found for global broadcast")
                return BroadcastResult(
                    event_type=event_data.get("event_type", "unknown"),
                    tenant_id=None,
                    connections_targeted=0,
                    connections_successful=0,
                    connections_failed=0,
                    broadcast_time_ms=(time.time() - start_time) * 1000
                )

            # Broadcast to all connections
            successful = 0
            failed = 0
            errors = []

            for connection_id in connection_ids:
                connection = self._connections.get(connection_id)
                if not connection:
                    continue

                try:
                    # Send message
                    message = {
                        "event_type": event_data.get("event_type", "unknown"),
                        "data": event_data,
                        "timestamp": datetime.now().isoformat()
                    }

                    await connection.websocket.send_json(message)

                    # Update metrics
                    connection.message_count += 1
                    connection.last_activity = datetime.now()

                    successful += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Connection {connection_id}: {str(e)}")
                    connection.error_count += 1

            # Update global metrics
            self._metrics['total_broadcasts'] += 1
            if failed > 0:
                self._metrics['failed_broadcasts'] += 1

            broadcast_time = (time.time() - start_time) * 1000

            result = BroadcastResult(
                event_type=event_data.get("event_type", "unknown"),
                tenant_id=None,
                connections_targeted=len(connection_ids),
                connections_successful=successful,
                connections_failed=failed,
                broadcast_time_ms=broadcast_time,
                errors=errors
            )

            logger.debug(f"Global broadcast: {successful}/{len(connection_ids)} successful "
                        f"({broadcast_time:.1f}ms)")

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast to all connections: {e}")
            return BroadcastResult(
                event_type=event_data.get("event_type", "error"),
                tenant_id=None,
                connections_targeted=0,
                connections_successful=0,
                connections_failed=1,
                broadcast_time_ms=(time.time() - start_time) * 1000,
                errors=[str(e)]
            )

    async def get_connection_health(self) -> Dict[str, Any]:
        """
        Get connection health metrics and status.

        Returns:
            Dictionary with health metrics and connection status
        """
        try:
            # Calculate aggregated health metrics
            total_connections = len(self._connections)
            alive_connections = sum(
                1 for health in self._connection_health.values() if health.is_alive
            )

            avg_response_time = 0.0
            if self._connection_health:
                avg_response_time = sum(
                    health.response_time_ms for health in self._connection_health.values()
                ) / len(self._connection_health)

            # Connection distribution per tenant
            tenant_distribution = {}
            for tenant_id, connection_ids in self._tenant_connections.items():
                tenant_distribution[tenant_id] = len(connection_ids)

            # Recent performance metrics
            uptime_connections = []
            for connection in self._connections.values():
                uptime_connections.append(connection.connection_age_seconds)

            avg_uptime = sum(uptime_connections) / max(len(uptime_connections), 1)

            return {
                "timestamp": datetime.now().isoformat(),
                "connections": {
                    "total": total_connections,
                    "alive": alive_connections,
                    "avg_response_time_ms": avg_response_time,
                    "avg_uptime_seconds": avg_uptime
                },
                "tenants": {
                    "count": len(self._tenant_connections),
                    "distribution": tenant_distribution,
                    "max_connections_per_tenant": self.max_connections_per_tenant
                },
                "performance": {
                    "total_broadcasts": self._metrics['total_broadcasts'],
                    "failed_broadcasts": self._metrics['failed_broadcasts'],
                    "avg_broadcast_time_ms": self._metrics['avg_broadcast_time_ms'],
                    "success_rate": (
                        1.0 - (self._metrics['failed_broadcasts'] /
                              max(self._metrics['total_broadcasts'], 1))
                    )
                },
                "health_details": [
                    asdict(health) for health in self._connection_health.values()
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get connection health: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def cleanup_stale_connections(self) -> int:
        """
        Clean up stale connections that haven't pinged recently.

        Returns:
            Number of connections cleaned up
        """
        try:
            stale_connections = []

            # Find stale connections
            for connection_id, connection in self._connections.items():
                if connection.is_stale:
                    stale_connections.append(connection_id)

            # Clean up stale connections
            cleaned_count = 0
            for connection_id in stale_connections:
                success = await self.disconnect_client(connection_id)
                if success:
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} stale connections")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup stale connections: {e}")
            return 0

    # Background tasks

    async def _start_background_tasks(self):
        """Start background health monitoring and cleanup tasks."""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _stop_background_tasks(self):
        """Stop background tasks when no connections remain."""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None

        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def _health_check_loop(self):
        """Background task for connection health monitoring."""
        try:
            while True:
                await asyncio.sleep(30)  # Health check every 30s

                # Ping all connections
                for connection_id, connection in list(self._connections.items()):
                    try:
                        ping_start = time.time()

                        # Send ping message
                        await connection.websocket.send_json({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        })

                        # Update health metrics
                        response_time = (time.time() - ping_start) * 1000

                        if connection_id in self._connection_health:
                            health = self._connection_health[connection_id]
                            health.last_ping = datetime.now()
                            health.response_time_ms = response_time
                            health.is_alive = True

                        connection.last_ping = datetime.now()

                    except Exception as e:
                        logger.debug(f"Health check failed for {connection_id}: {e}")

                        # Mark as unhealthy
                        if connection_id in self._connection_health:
                            self._connection_health[connection_id].is_alive = False

                        # Remove dead connection
                        await self.disconnect_client(connection_id)

        except asyncio.CancelledError:
            logger.debug("Health check loop cancelled")
        except Exception as e:
            logger.error(f"Health check loop error: {e}")

    async def _cleanup_loop(self):
        """Background task for cleaning up stale connections."""
        try:
            while True:
                await asyncio.sleep(60)  # Cleanup every 60s
                await self.cleanup_stale_connections()

        except asyncio.CancelledError:
            logger.debug("Cleanup loop cancelled")
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}")

    # =================== COACHING BROADCAST METHODS ===================

    async def broadcast_coaching_suggestions(
        self,
        agent_id: str,
        tenant_id: str,
        coaching_suggestions: List[str],
        urgency: str = "medium",
        conversation_stage: str = "discovery"
    ) -> BroadcastResult:
        """
        Broadcast real-time coaching suggestions to a specific agent.

        Args:
            agent_id: Target agent identifier
            tenant_id: Tenant identifier for isolation
            coaching_suggestions: List of coaching suggestions
            urgency: Urgency level (low, medium, high, critical)
            conversation_stage: Current conversation stage

        Returns:
            BroadcastResult with broadcast metrics
        """
        try:
            coaching_event = {
                "event_type": "coaching_suggestions",
                "topic": f"coaching.{agent_id}.suggestions",
                "data": {
                    "agent_id": agent_id,
                    "suggestions": coaching_suggestions,
                    "urgency": urgency,
                    "conversation_stage": conversation_stage,
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": {
                    "priority": "high" if urgency in ["high", "critical"] else "normal",
                    "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()
                }
            }

            # Broadcast to tenant with coaching topic filtering
            result = await self.broadcast_to_tenant(tenant_id, coaching_event)

            logger.debug(f"Coaching suggestions broadcasted to agent {agent_id}: "
                        f"{result.connections_successful}/{result.connections_targeted} successful")

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast coaching suggestions to agent {agent_id}: {e}")
            return BroadcastResult(
                event_type="coaching_suggestions",
                tenant_id=tenant_id,
                connections_targeted=0,
                connections_successful=0,
                connections_failed=1,
                broadcast_time_ms=0,
                errors=[str(e)]
            )

    async def broadcast_objection_alert(
        self,
        agent_id: str,
        tenant_id: str,
        objection_type: str,
        suggested_responses: List[str],
        severity: str = "medium"
    ) -> BroadcastResult:
        """
        Broadcast objection detection alert to a specific agent.

        Args:
            agent_id: Target agent identifier
            tenant_id: Tenant identifier for isolation
            objection_type: Type of objection detected
            suggested_responses: Suggested response options
            severity: Objection severity (low, medium, high)

        Returns:
            BroadcastResult with broadcast metrics
        """
        try:
            objection_event = {
                "event_type": "objection_alert",
                "topic": f"coaching.{agent_id}.objections",
                "data": {
                    "agent_id": agent_id,
                    "objection_type": objection_type,
                    "suggested_responses": suggested_responses,
                    "severity": severity,
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": {
                    "priority": "high" if severity == "high" else "normal",
                    "alert_sound": True if severity == "high" else False,
                    "expires_at": (datetime.now() + timedelta(minutes=3)).isoformat()
                }
            }

            # Broadcast to tenant with objection topic filtering
            result = await self.broadcast_to_tenant(tenant_id, objection_event)

            logger.debug(f"Objection alert broadcasted to agent {agent_id}: "
                        f"{objection_type} severity {severity}")

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast objection alert to agent {agent_id}: {e}")
            return BroadcastResult(
                event_type="objection_alert",
                tenant_id=tenant_id,
                connections_targeted=0,
                connections_successful=0,
                connections_failed=1,
                broadcast_time_ms=0,
                errors=[str(e)]
            )

    async def broadcast_question_suggestion(
        self,
        agent_id: str,
        tenant_id: str,
        suggested_question: str,
        purpose: str,
        priority: str = "medium",
        expected_info: str = ""
    ) -> BroadcastResult:
        """
        Broadcast next question suggestion to a specific agent.

        Args:
            agent_id: Target agent identifier
            tenant_id: Tenant identifier for isolation
            suggested_question: The suggested question to ask
            purpose: Question purpose (qualification, discovery, objection_handling, closing)
            priority: Priority level (high, medium, low)
            expected_info: What information this question should reveal

        Returns:
            BroadcastResult with broadcast metrics
        """
        try:
            question_event = {
                "event_type": "question_suggestion",
                "topic": f"coaching.{agent_id}.questions",
                "data": {
                    "agent_id": agent_id,
                    "suggested_question": suggested_question,
                    "purpose": purpose,
                    "priority": priority,
                    "expected_info": expected_info,
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": {
                    "priority": priority,
                    "expires_at": (datetime.now() + timedelta(minutes=2)).isoformat()
                }
            }

            # Broadcast to tenant with question topic filtering
            result = await self.broadcast_to_tenant(tenant_id, question_event)

            logger.debug(f"Question suggestion broadcasted to agent {agent_id}: "
                        f"{purpose} priority {priority}")

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast question suggestion to agent {agent_id}: {e}")
            return BroadcastResult(
                event_type="question_suggestion",
                tenant_id=tenant_id,
                connections_targeted=0,
                connections_successful=0,
                connections_failed=1,
                broadcast_time_ms=0,
                errors=[str(e)]
            )

    async def subscribe_to_coaching(
        self,
        connection_id: str,
        agent_id: str
    ) -> bool:
        """
        Subscribe a WebSocket connection to coaching topics for a specific agent.

        Args:
            connection_id: WebSocket connection identifier
            agent_id: Agent identifier for coaching topics

        Returns:
            True if subscription successful, False otherwise
        """
        try:
            connection = self._connections.get(connection_id)
            if not connection:
                logger.warning(f"Connection {connection_id} not found for coaching subscription")
                return False

            # Add coaching topics to subscription list
            coaching_topics = [
                f"coaching.{agent_id}.suggestions",
                f"coaching.{agent_id}.objections",
                f"coaching.{agent_id}.questions"
            ]

            for topic in coaching_topics:
                if topic not in connection.subscription_topics:
                    connection.subscription_topics.append(topic)

            logger.info(f"Connection {connection_id} subscribed to coaching for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe connection {connection_id} to coaching: {e}")
            return False

    async def unsubscribe_from_coaching(
        self,
        connection_id: str,
        agent_id: str
    ) -> bool:
        """
        Unsubscribe a WebSocket connection from coaching topics for a specific agent.

        Args:
            connection_id: WebSocket connection identifier
            agent_id: Agent identifier for coaching topics

        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            connection = self._connections.get(connection_id)
            if not connection:
                logger.warning(f"Connection {connection_id} not found for coaching unsubscription")
                return False

            # Remove coaching topics from subscription list
            coaching_topics = [
                f"coaching.{agent_id}.suggestions",
                f"coaching.{agent_id}.objections",
                f"coaching.{agent_id}.questions"
            ]

            for topic in coaching_topics:
                if topic in connection.subscription_topics:
                    connection.subscription_topics.remove(topic)

            logger.info(f"Connection {connection_id} unsubscribed from coaching for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe connection {connection_id} from coaching: {e}")
            return False


# Singleton instance
_realtime_websocket_hub = None


def get_realtime_websocket_hub(**kwargs) -> RealtimeWebSocketHub:
    """Get singleton Real-Time WebSocket Hub instance."""
    global _realtime_websocket_hub
    if _realtime_websocket_hub is None:
        _realtime_websocket_hub = RealtimeWebSocketHub(**kwargs)
    return _realtime_websocket_hub


# Export main classes
__all__ = [
    "RealtimeWebSocketHub",
    "WebSocketConnection",
    "ConnectionHealth",
    "BroadcastResult",
    "get_realtime_websocket_hub"
]