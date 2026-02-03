"""
WebSocket Server for Real-time Compliance Alerts

Production-ready WebSocket implementation for streaming compliance alerts
to connected clients with subscription filtering, heartbeat mechanism,
and graceful connection management.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of compliance alerts"""
    VIOLATION_DETECTED = "violation_detected"
    SCORE_CHANGED = "score_changed"
    RISK_LEVEL_CHANGED = "risk_level_changed"
    REMEDIATION_DUE = "remediation_due"
    CERTIFICATION_EXPIRING = "certification_expiring"
    THRESHOLD_BREACH = "threshold_breach"
    ASSESSMENT_COMPLETED = "assessment_completed"
    POLICY_UPDATED = "policy_updated"
    AUDIT_EVENT = "audit_event"
    SYSTEM_STATUS = "system_status"


class AlertSeverity(str, Enum):
    """Severity levels for alerts"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceAlert(BaseModel):
    """Real-time compliance alert message"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    alert_type: AlertType
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str
    message: str
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    regulation: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = False
    source: str = "compliance_engine"

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat()
        })

    def to_json(self) -> str:
        """Serialize alert to JSON string"""
        return json.dumps({
            "id": self.id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "regulation": self.regulation,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "acknowledged": self.acknowledged,
            "source": self.source,
        })


class SubscriptionRequest(BaseModel):
    """Client subscription preferences"""
    action: str = "subscribe"  # subscribe, unsubscribe
    alert_types: List[AlertType] = Field(default_factory=list)
    model_ids: List[str] = Field(default_factory=list)
    severities: List[AlertSeverity] = Field(default_factory=list)
    regulations: List[str] = Field(default_factory=list)


class ClientConnection:
    """Represents a connected client with subscription preferences"""

    def __init__(self, client_id: str, websocket: WebSocket):
        self.client_id = client_id
        self.websocket = websocket
        self.connected_at = datetime.now(timezone.utc)
        self.last_heartbeat = self.connected_at
        self.subscribed_alert_types: Set[AlertType] = set()
        self.subscribed_model_ids: Set[str] = set()
        self.subscribed_severities: Set[AlertSeverity] = set()
        self.subscribed_regulations: Set[str] = set()
        self.alerts_received: int = 0
        self.is_active: bool = True

    def matches_alert(self, alert: ComplianceAlert) -> bool:
        """Check if this client should receive the given alert"""
        # If no subscriptions set, receive all alerts
        if not any([
            self.subscribed_alert_types,
            self.subscribed_model_ids,
            self.subscribed_severities,
            self.subscribed_regulations,
        ]):
            return True

        # Check alert type filter
        if self.subscribed_alert_types and alert.alert_type not in self.subscribed_alert_types:
            return False

        # Check model ID filter
        if self.subscribed_model_ids and alert.model_id:
            if alert.model_id not in self.subscribed_model_ids:
                return False

        # Check severity filter
        if self.subscribed_severities and alert.severity not in self.subscribed_severities:
            return False

        # Check regulation filter
        if self.subscribed_regulations and alert.regulation:
            if alert.regulation not in self.subscribed_regulations:
                return False

        return True

    def update_subscriptions(self, request: SubscriptionRequest) -> None:
        """Update client subscriptions based on request"""
        if request.action == "subscribe":
            self.subscribed_alert_types.update(request.alert_types)
            self.subscribed_model_ids.update(request.model_ids)
            self.subscribed_severities.update(request.severities)
            self.subscribed_regulations.update(request.regulations)
        elif request.action == "unsubscribe":
            self.subscribed_alert_types -= set(request.alert_types)
            self.subscribed_model_ids -= set(request.model_ids)
            self.subscribed_severities -= set(request.severities)
            self.subscribed_regulations -= set(request.regulations)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize connection info for status reporting"""
        return {
            "client_id": self.client_id,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "alerts_received": self.alerts_received,
            "subscriptions": {
                "alert_types": [t.value for t in self.subscribed_alert_types],
                "model_ids": list(self.subscribed_model_ids),
                "severities": [s.value for s in self.subscribed_severities],
                "regulations": list(self.subscribed_regulations),
            },
        }


class ConnectionManager:
    """
    Manages WebSocket connections for real-time compliance alerts.

    Thread-safe connection pooling with subscription filtering,
    heartbeat mechanism, and graceful disconnect handling.
    """

    def __init__(self, heartbeat_interval: int = 30):
        self._connections: Dict[str, ClientConnection] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
        self._alert_history: List[ComplianceAlert] = []
        self._max_history_size = 100

        logger.info("ConnectionManager initialized with heartbeat_interval=%d", heartbeat_interval)

    @property
    def active_connections_count(self) -> int:
        """Number of active connections"""
        return len(self._connections)

    @property
    def connection_stats(self) -> Dict[str, Any]:
        """Connection statistics for monitoring"""
        return {
            "active_connections": self.active_connections_count,
            "heartbeat_interval": self._heartbeat_interval,
            "is_running": self._running,
            "alert_history_size": len(self._alert_history),
        }

    async def start(self) -> None:
        """Start the connection manager and heartbeat task"""
        if self._running:
            logger.warning("ConnectionManager already running")
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("ConnectionManager started")

    async def stop(self) -> None:
        """Stop the connection manager and disconnect all clients"""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Close all connections
        async with self._lock:
            for client_id in list(self._connections.keys()):
                await self._close_connection(client_id, reason="Server shutting down")

        logger.info("ConnectionManager stopped")

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Accept new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
            client_id: Unique identifier for the client

        Returns:
            True if connection was accepted, False otherwise
        """
        try:
            await websocket.accept()

            async with self._lock:
                # Close existing connection for this client if any
                if client_id in self._connections:
                    logger.info("Closing existing connection for client_id=%s", client_id)
                    await self._close_connection(client_id, reason="Reconnection")

                connection = ClientConnection(client_id, websocket)
                self._connections[client_id] = connection

            logger.info(
                "Client connected: client_id=%s, total_connections=%d",
                client_id,
                self.active_connections_count
            )

            # Send welcome message
            await self._send_message(websocket, {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "heartbeat_interval": self._heartbeat_interval,
                "message": "Connected to compliance alert stream",
            })

            return True

        except Exception as e:
            logger.error("Failed to accept connection for client_id=%s: %s", client_id, e)
            return False

    def disconnect(self, client_id: str) -> None:
        """
        Handle client disconnect (synchronous cleanup).

        Args:
            client_id: The client to disconnect
        """
        if client_id in self._connections:
            self._connections[client_id].is_active = False
            del self._connections[client_id]
            logger.info(
                "Client disconnected: client_id=%s, remaining_connections=%d",
                client_id,
                self.active_connections_count
            )

    async def _close_connection(self, client_id: str, reason: str = "Unknown") -> None:
        """Close a specific connection gracefully"""
        if client_id not in self._connections:
            return

        connection = self._connections[client_id]
        connection.is_active = False

        try:
            await connection.websocket.close(code=status.WS_1000_NORMAL_CLOSURE, reason=reason)
        except Exception as e:
            logger.debug("Error closing websocket for client_id=%s: %s", client_id, e)

        del self._connections[client_id]

    async def subscribe(
        self,
        client_id: str,
        alert_types: Optional[List[AlertType]] = None,
        model_ids: Optional[List[str]] = None,
        severities: Optional[List[AlertSeverity]] = None,
        regulations: Optional[List[str]] = None,
    ) -> bool:
        """
        Subscribe client to specific alert types and/or filters.

        Args:
            client_id: The client to update
            alert_types: List of alert types to subscribe to
            model_ids: List of model IDs to filter by
            severities: List of severities to filter by
            regulations: List of regulations to filter by

        Returns:
            True if subscription was updated, False if client not found
        """
        async with self._lock:
            if client_id not in self._connections:
                logger.warning("Subscribe failed: client_id=%s not found", client_id)
                return False

            connection = self._connections[client_id]
            request = SubscriptionRequest(
                action="subscribe",
                alert_types=alert_types or [],
                model_ids=model_ids or [],
                severities=severities or [],
                regulations=regulations or [],
            )
            connection.update_subscriptions(request)

            logger.info(
                "Client subscribed: client_id=%s, alert_types=%s, models=%s",
                client_id,
                [t.value for t in (alert_types or [])],
                model_ids or []
            )

            # Confirm subscription
            await self._send_message(connection.websocket, {
                "type": "subscription_updated",
                "action": "subscribe",
                "subscriptions": connection.to_dict()["subscriptions"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            return True

    async def unsubscribe(
        self,
        client_id: str,
        alert_types: Optional[List[AlertType]] = None,
        model_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Unsubscribe client from specific alert types or models.

        Args:
            client_id: The client to update
            alert_types: List of alert types to unsubscribe from
            model_ids: List of model IDs to unsubscribe from

        Returns:
            True if subscription was updated, False if client not found
        """
        async with self._lock:
            if client_id not in self._connections:
                return False

            connection = self._connections[client_id]
            request = SubscriptionRequest(
                action="unsubscribe",
                alert_types=alert_types or [],
                model_ids=model_ids or [],
            )
            connection.update_subscriptions(request)

            return True

    async def broadcast_alert(self, alert: ComplianceAlert) -> int:
        """
        Send alert to all relevant subscribers.

        Args:
            alert: The compliance alert to broadcast

        Returns:
            Number of clients that received the alert
        """
        # Add to history
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history_size:
            self._alert_history = self._alert_history[-self._max_history_size:]

        recipients = 0
        failed_clients: List[str] = []

        async with self._lock:
            for client_id, connection in self._connections.items():
                if not connection.is_active:
                    continue

                if connection.matches_alert(alert):
                    try:
                        await self._send_message(connection.websocket, {
                            "type": "alert",
                            "alert": json.loads(alert.to_json()),
                        })
                        connection.alerts_received += 1
                        recipients += 1
                    except Exception as e:
                        logger.error(
                            "Failed to send alert to client_id=%s: %s",
                            client_id, e
                        )
                        failed_clients.append(client_id)

        # Clean up failed connections
        for client_id in failed_clients:
            self.disconnect(client_id)

        logger.info(
            "Alert broadcast: alert_id=%s, type=%s, recipients=%d",
            alert.id, alert.alert_type.value, recipients
        )

        return recipients

    async def send_to_client(self, client_id: str, alert: ComplianceAlert) -> bool:
        """
        Send alert to specific client.

        Args:
            client_id: The target client
            alert: The compliance alert to send

        Returns:
            True if sent successfully, False otherwise
        """
        async with self._lock:
            if client_id not in self._connections:
                logger.warning("Send failed: client_id=%s not found", client_id)
                return False

            connection = self._connections[client_id]
            if not connection.is_active:
                return False

            try:
                await self._send_message(connection.websocket, {
                    "type": "alert",
                    "alert": json.loads(alert.to_json()),
                })
                connection.alerts_received += 1
                return True
            except Exception as e:
                logger.error("Failed to send to client_id=%s: %s", client_id, e)
                self.disconnect(client_id)
                return False

    async def send_heartbeat(self) -> int:
        """
        Send periodic heartbeat to all connections.

        Returns:
            Number of clients that received the heartbeat
        """
        now = datetime.now(timezone.utc)
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": now.isoformat(),
            "active_connections": self.active_connections_count,
        }

        recipients = 0
        failed_clients: List[str] = []

        async with self._lock:
            for client_id, connection in self._connections.items():
                if not connection.is_active:
                    continue

                try:
                    await self._send_message(connection.websocket, heartbeat_message)
                    connection.last_heartbeat = now
                    recipients += 1
                except Exception as e:
                    logger.debug("Heartbeat failed for client_id=%s: %s", client_id, e)
                    failed_clients.append(client_id)

        # Clean up stale connections
        for client_id in failed_clients:
            self.disconnect(client_id)

        if recipients > 0:
            logger.debug("Heartbeat sent to %d clients", recipients)

        return recipients

    async def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        async with self._lock:
            if client_id not in self._connections:
                return None
            return self._connections[client_id].to_dict()

    async def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get information about all connections"""
        async with self._lock:
            return [conn.to_dict() for conn in self._connections.values()]

    async def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return [json.loads(a.to_json()) for a in self._alert_history[-limit:]]

    async def _heartbeat_loop(self) -> None:
        """Background task for periodic heartbeats"""
        logger.info("Heartbeat loop started with interval=%d seconds", self._heartbeat_interval)

        while self._running:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self._running and self.active_connections_count > 0:
                    await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat loop error: %s", e)

    async def _send_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Send JSON message to a websocket"""
        await websocket.send_json(message)


# Global connection manager instance
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


def create_websocket_router() -> tuple[APIRouter, ConnectionManager]:
    """
    Create FastAPI router for WebSocket endpoints.

    Returns:
        Tuple of (router, connection_manager)
    """
    router = APIRouter(prefix="/ws", tags=["websocket"])
    manager = get_connection_manager()

    @router.websocket("/alerts/{client_id}")
    async def websocket_alerts(websocket: WebSocket, client_id: str) -> None:
        """
        WebSocket endpoint for real-time compliance alerts.

        Clients connect and can send subscription preferences as JSON messages:
        {
            "action": "subscribe",
            "alert_types": ["violation_detected", "score_changed"],
            "model_ids": ["model-123"],
            "severities": ["critical", "high"],
            "regulations": ["eu_ai_act"]
        }

        Or unsubscribe:
        {
            "action": "unsubscribe",
            "alert_types": ["score_changed"]
        }

        Server sends:
        - Connection confirmation on connect
        - Alerts matching subscription filters
        - Heartbeat messages every 30 seconds
        - Subscription confirmations
        """
        connection_accepted = await manager.connect(websocket, client_id)
        if not connection_accepted:
            return

        try:
            while True:
                # Receive and process client messages
                data = await websocket.receive_json()

                action = data.get("action", "").lower()

                if action == "subscribe":
                    alert_types = [
                        AlertType(t) for t in data.get("alert_types", [])
                        if t in [at.value for at in AlertType]
                    ]
                    severities = [
                        AlertSeverity(s) for s in data.get("severities", [])
                        if s in [sev.value for sev in AlertSeverity]
                    ]
                    await manager.subscribe(
                        client_id,
                        alert_types=alert_types or None,
                        model_ids=data.get("model_ids"),
                        severities=severities or None,
                        regulations=data.get("regulations"),
                    )

                elif action == "unsubscribe":
                    alert_types = [
                        AlertType(t) for t in data.get("alert_types", [])
                        if t in [at.value for at in AlertType]
                    ]
                    await manager.unsubscribe(
                        client_id,
                        alert_types=alert_types or None,
                        model_ids=data.get("model_ids"),
                    )

                elif action == "ping":
                    # Client ping, respond with pong
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                elif action == "status":
                    # Client requesting connection status
                    info = await manager.get_connection_info(client_id)
                    await websocket.send_json({
                        "type": "status",
                        "connection": info,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                elif action == "history":
                    # Client requesting recent alerts
                    limit = min(data.get("limit", 10), 50)
                    history = await manager.get_recent_alerts(limit)
                    await websocket.send_json({
                        "type": "history",
                        "alerts": history,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                else:
                    # Unknown action
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}",
                        "valid_actions": ["subscribe", "unsubscribe", "ping", "status", "history"],
                    })

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected: client_id=%s", client_id)
        except Exception as e:
            logger.error("WebSocket error for client_id=%s: %s", client_id, e)
        finally:
            manager.disconnect(client_id)

    @router.get("/connections")
    async def list_connections() -> Dict[str, Any]:
        """List all active WebSocket connections (for monitoring)"""
        connections = await manager.get_all_connections()
        return {
            "total_connections": len(connections),
            "connections": connections,
            "stats": manager.connection_stats,
        }

    @router.get("/health")
    async def websocket_health() -> Dict[str, Any]:
        """WebSocket service health check"""
        return {
            "status": "healthy",
            "active_connections": manager.active_connections_count,
            "is_running": manager._running,
            "heartbeat_interval": manager._heartbeat_interval,
        }

    return router, manager


# Utility function for sending alerts from other parts of the application
async def send_compliance_alert(
    alert_type: AlertType,
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    model_id: Optional[str] = None,
    model_name: Optional[str] = None,
    regulation: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Convenience function to send a compliance alert to all subscribers.

    Args:
        alert_type: Type of the alert
        title: Alert title
        message: Alert message
        severity: Alert severity level
        model_id: Optional model ID for filtering
        model_name: Optional model name for display
        regulation: Optional regulation type for filtering
        data: Optional additional data

    Returns:
        Alert ID if sent successfully, None otherwise
    """
    manager = get_connection_manager()

    alert = ComplianceAlert(
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        model_id=model_id,
        model_name=model_name,
        regulation=regulation,
        data=data or {},
    )

    recipients = await manager.broadcast_alert(alert)

    if recipients > 0:
        logger.info("Alert sent: id=%s, recipients=%d", alert.id, recipients)
        return alert.id

    return None
