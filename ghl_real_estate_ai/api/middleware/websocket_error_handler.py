"""
WebSocket Error Management for Jorge's Real Estate AI Platform.

Provides comprehensive error handling for WebSocket connections including:
- Connection management and recovery
- Automatic reconnection with exponential backoff
- Message validation and error handling
- Connection state tracking
- Graceful error responses and cleanup

Features:
- Intelligent connection recovery
- Message parsing error handling
- Connection state management
- Error correlation tracking
- Automatic cleanup of failed connections
"""

import asyncio
import json
import logging
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.utils.async_utils import safe_create_task

logger = get_logger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states for Jorge's platform."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TERMINATED = "terminated"


class ErrorSeverity(Enum):
    """Error severity levels for WebSocket errors."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WebSocketError:
    """Structured WebSocket error information."""

    error_id: str
    connection_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: float
    recoverable: bool
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None


@dataclass
class ConnectionMetrics:
    """Track connection health metrics."""

    connection_id: str
    established_at: float
    messages_sent: int = 0
    messages_received: int = 0
    errors_count: int = 0
    last_activity: float = field(default_factory=time.time)
    reconnection_attempts: int = 0


class WebSocketErrorManager:
    """Comprehensive WebSocket error management for Jorge's platform."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.connection_states: Dict[str, ConnectionState] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.error_handlers: Dict[str, Callable] = {}
        self.max_reconnection_attempts = 5
        self.reconnection_base_delay = 1.0
        self.connection_timeout = 30.0
        self.heartbeat_interval = 30.0

    async def register_connection(
        self, websocket: WebSocket, connection_type: str = "general", client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new WebSocket connection with error handling."""

        connection_id = self._generate_connection_id(connection_type)

        try:
            await websocket.accept()

            self.connections[connection_id] = websocket
            self.connection_states[connection_id] = ConnectionState.CONNECTED
            self.connection_metrics[connection_id] = ConnectionMetrics(
                connection_id=connection_id, established_at=time.time()
            )

            logger.info(
                f"WebSocket connection established: {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "connection_type": connection_type,
                    "client_info": client_info or {},
                    "jorge_platform": True,
                },
            )

            # Start connection monitoring
            safe_create_task(self._monitor_connection(connection_id))

            return connection_id

        except Exception as e:
            await self._handle_connection_error(connection_id=connection_id, error=e, context="connection_registration")
            raise

    async def send_message(self, connection_id: str, message: Dict[str, Any], message_type: str = "data") -> bool:
        """Send message with comprehensive error handling."""

        if connection_id not in self.connections:
            await self._handle_connection_error(
                connection_id=connection_id,
                error=Exception(f"Connection {connection_id} not found"),
                context="message_send",
            )
            return False

        websocket = self.connections[connection_id]

        try:
            # Validate message format
            validated_message = await self._validate_message(message, message_type)

            # Check connection state
            if self.connection_states.get(connection_id) != ConnectionState.CONNECTED:
                raise Exception(f"Connection {connection_id} not in connected state")

            # Send message
            await websocket.send_json(validated_message)

            # Update metrics
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].messages_sent += 1
                self.connection_metrics[connection_id].last_activity = time.time()

            return True

        except WebSocketDisconnect:
            await self._handle_disconnection(connection_id, "client_disconnect")
            return False

        except Exception as e:
            await self._handle_message_error(
                connection_id=connection_id, message=message, error=e, direction="outbound"
            )
            return False

    async def receive_message(self, connection_id: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Receive message with error handling and validation."""

        if connection_id not in self.connections:
            await self._handle_connection_error(
                connection_id=connection_id,
                error=Exception(f"Connection {connection_id} not found"),
                context="message_receive",
            )
            return None

        websocket = self.connections[connection_id]

        try:
            # Receive with timeout
            if timeout:
                raw_message = await asyncio.wait_for(websocket.receive_json(), timeout=timeout)
            else:
                raw_message = await websocket.receive_json()

            # Validate received message
            validated_message = await self._validate_received_message(raw_message)

            # Update metrics
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].messages_received += 1
                self.connection_metrics[connection_id].last_activity = time.time()

            return validated_message

        except WebSocketDisconnect:
            await self._handle_disconnection(connection_id, "client_disconnect")
            return None

        except asyncio.TimeoutError:
            await self._handle_timeout(connection_id)
            return None

        except json.JSONDecodeError as e:
            await self._handle_message_error(
                connection_id=connection_id, message=None, error=e, direction="inbound", error_type="json_decode"
            )
            return None

        except Exception as e:
            await self._handle_message_error(connection_id=connection_id, message=None, error=e, direction="inbound")
            return None

    async def disconnect_connection(
        self, connection_id: str, reason: str = "server_disconnect", close_code: int = status.WS_1000_NORMAL_CLOSURE
    ):
        """Gracefully disconnect a WebSocket connection."""

        if connection_id not in self.connections:
            return

        websocket = self.connections[connection_id]

        try:
            # Send disconnect notification
            await self._send_disconnect_notification(connection_id, reason)

            # Close the connection
            await websocket.close(code=close_code)

        except Exception as e:
            logger.warning(
                f"Error during graceful disconnect: {e}", extra={"connection_id": connection_id, "reason": reason}
            )

        finally:
            await self._cleanup_connection(connection_id, reason)

    async def _validate_message(self, message: Dict[str, Any], message_type: str) -> Dict[str, Any]:
        """Validate outbound message format."""

        # Base message structure
        validated = {
            "type": message_type,
            "timestamp": time.time(),
            "data": message.get("data", {}),
            "correlation_id": message.get("correlation_id", self._generate_correlation_id()),
        }

        # Jorge-specific validation
        if message_type in ["lead_update", "property_alert", "bot_response"]:
            if "lead_id" not in validated["data"]:
                raise ValueError(f"Missing lead_id for {message_type} message")

        if message_type == "error":
            validated["error"] = {
                "type": message.get("error_type", "unknown"),
                "message": message.get("error_message", "An error occurred"),
                "recoverable": message.get("recoverable", True),
            }

        # Size validation
        message_size = len(json.dumps(validated))
        if message_size > 64 * 1024:  # 64KB limit
            raise ValueError(f"Message too large: {message_size} bytes (max 64KB)")

        return validated

    async def _validate_received_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inbound message format."""

        # Required fields
        if "type" not in message:
            raise ValueError("Message missing required 'type' field")

        message_type = message["type"]

        # Jorge-specific message validation
        if message_type in ["subscribe", "unsubscribe"]:
            if "channel" not in message:
                raise ValueError(f"Missing 'channel' for {message_type} message")

        if message_type == "bot_command":
            if "command" not in message or "bot_type" not in message:
                raise ValueError("Bot command missing required fields")

        if message_type == "analytics_query":
            if "timeframe" not in message:
                raise ValueError("Analytics query missing timeframe")

        return message

    async def _handle_connection_error(self, connection_id: str, error: Exception, context: str):
        """Handle connection-level errors."""

        error_info = WebSocketError(
            error_id=self._generate_error_id(),
            connection_id=connection_id,
            error_type=type(error).__name__,
            message=str(error),
            severity=self._determine_error_severity(error, context),
            timestamp=time.time(),
            recoverable=self._is_recoverable_error(error, context),
            details={"context": context},
            stack_trace=traceback.format_exc() if settings.environment == "development" else None,
        )

        await self._log_error(error_info)

        # Update connection state
        if connection_id in self.connection_states:
            self.connection_states[connection_id] = ConnectionState.ERROR

        # Update error metrics
        if connection_id in self.connection_metrics:
            self.connection_metrics[connection_id].errors_count += 1

        # Attempt recovery if possible
        if error_info.recoverable and context == "message_send":
            safe_create_task(self._attempt_reconnection(connection_id))

    async def _handle_message_error(
        self,
        connection_id: str,
        message: Optional[Dict[str, Any]],
        error: Exception,
        direction: str,
        error_type: str = "message_error",
    ):
        """Handle message-level errors."""

        error_info = WebSocketError(
            error_id=self._generate_error_id(),
            connection_id=connection_id,
            error_type=error_type,
            message=str(error),
            severity=ErrorSeverity.MEDIUM,
            timestamp=time.time(),
            recoverable=True,
            details={"direction": direction, "message_preview": str(message)[:200] if message else "N/A"},
        )

        await self._log_error(error_info)

        # Send error response to client
        if direction == "inbound" and connection_id in self.connections:
            try:
                await self.send_message(
                    connection_id=connection_id,
                    message={
                        "error_type": error_type,
                        "error_message": "Invalid message format",
                        "error_id": error_info.error_id,
                        "guidance": self._get_message_error_guidance(error_type),
                    },
                    message_type="error",
                )
            except Exception:
                # If we can't send error response, the connection is likely broken
                await self._cleanup_connection(connection_id, "send_error_failed")

    async def _handle_disconnection(self, connection_id: str, reason: str):
        """Handle client disconnection."""

        logger.info(
            f"WebSocket client disconnected: {connection_id}",
            extra={"connection_id": connection_id, "reason": reason, "jorge_platform": True},
        )

        await self._cleanup_connection(connection_id, reason)

    async def _handle_timeout(self, connection_id: str):
        """Handle connection timeout."""

        error_info = WebSocketError(
            error_id=self._generate_error_id(),
            connection_id=connection_id,
            error_type="timeout",
            message="Connection timeout",
            severity=ErrorSeverity.MEDIUM,
            timestamp=time.time(),
            recoverable=True,
            details={"timeout_duration": self.connection_timeout},
        )

        await self._log_error(error_info)

        # Attempt to send timeout notification
        try:
            await self.send_message(
                connection_id=connection_id,
                message={
                    "error_type": "timeout",
                    "error_message": "Connection timeout - please check your network",
                    "error_id": error_info.error_id,
                    "guidance": "Refresh the page to reconnect",
                },
                message_type="error",
            )
        except Exception:
            # Connection is likely broken
            await self._cleanup_connection(connection_id, "timeout")

    async def _attempt_reconnection(self, connection_id: str):
        """Attempt to reconnect a failed connection."""

        if connection_id not in self.connection_metrics:
            return

        metrics = self.connection_metrics[connection_id]

        if metrics.reconnection_attempts >= self.max_reconnection_attempts:
            logger.warning(
                f"Max reconnection attempts reached for {connection_id}",
                extra={"connection_id": connection_id, "attempts": metrics.reconnection_attempts},
            )
            await self._cleanup_connection(connection_id, "max_reconnections")
            return

        # Exponential backoff
        delay = self.reconnection_base_delay * (2**metrics.reconnection_attempts)
        await asyncio.sleep(delay)

        metrics.reconnection_attempts += 1
        self.connection_states[connection_id] = ConnectionState.RECONNECTING

        logger.info(
            f"Attempting reconnection {metrics.reconnection_attempts} for {connection_id}",
            extra={"connection_id": connection_id, "delay": delay},
        )

    async def _monitor_connection(self, connection_id: str):
        """Monitor connection health with heartbeat."""

        while connection_id in self.connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if connection_id not in self.connections:
                    break

                # Send heartbeat
                await self.send_message(
                    connection_id=connection_id, message={"heartbeat": True}, message_type="heartbeat"
                )

                # Check for inactive connections
                if connection_id in self.connection_metrics:
                    metrics = self.connection_metrics[connection_id]
                    inactive_time = time.time() - metrics.last_activity

                    if inactive_time > self.connection_timeout:
                        logger.warning(
                            f"Connection {connection_id} inactive for {inactive_time:.1f}s",
                            extra={"connection_id": connection_id, "inactive_time": inactive_time},
                        )
                        break

            except Exception as e:
                logger.error(f"Connection monitoring error: {e}", extra={"connection_id": connection_id})
                break

        # Cleanup if loop ended
        if connection_id in self.connections:
            await self._cleanup_connection(connection_id, "monitor_failure")

    async def _cleanup_connection(self, connection_id: str, reason: str):
        """Clean up connection resources."""

        # Remove from active connections
        if connection_id in self.connections:
            del self.connections[connection_id]

        # Update state
        if connection_id in self.connection_states:
            self.connection_states[connection_id] = ConnectionState.DISCONNECTED

        logger.info(
            f"WebSocket connection cleaned up: {connection_id}",
            extra={"connection_id": connection_id, "reason": reason, "jorge_platform": True},
        )

    async def _send_disconnect_notification(self, connection_id: str, reason: str):
        """Send disconnect notification to client."""

        try:
            await self.send_message(
                connection_id=connection_id,
                message={
                    "disconnect_reason": reason,
                    "message": "Connection will be closed",
                    "guidance": "Please refresh the page to reconnect",
                },
                message_type="disconnect",
            )
        except Exception:
            # Ignore errors during disconnect notification
            pass

    async def _log_error(self, error_info: WebSocketError):
        """Log WebSocket error with appropriate level."""

        log_method = {
            ErrorSeverity.LOW: logger.info,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
        }.get(error_info.severity, logger.error)

        log_method(
            f"WebSocket Error [{error_info.error_type}]: {error_info.message}",
            extra={
                "error_id": error_info.error_id,
                "connection_id": error_info.connection_id,
                "error_type": error_info.error_type,
                "severity": error_info.severity.value,
                "recoverable": error_info.recoverable,
                "details": error_info.details,
                "stack_trace": error_info.stack_trace,
                "jorge_platform": True,
            },
        )

    def _determine_error_severity(self, error: Exception, context: str) -> ErrorSeverity:
        """Determine error severity level."""

        if isinstance(error, WebSocketDisconnect):
            return ErrorSeverity.LOW

        if isinstance(error, (json.JSONDecodeError, ValueError)):
            return ErrorSeverity.MEDIUM

        if context in ["connection_registration", "connection_failure"]:
            return ErrorSeverity.HIGH

        return ErrorSeverity.MEDIUM

    def _is_recoverable_error(self, error: Exception, context: str) -> bool:
        """Determine if error is recoverable."""

        if isinstance(error, WebSocketDisconnect):
            return False  # Client disconnects are final

        if isinstance(error, (json.JSONDecodeError, ValueError)):
            return True  # Message errors can be retried

        return True  # Most other errors are recoverable

    def _get_message_error_guidance(self, error_type: str) -> str:
        """Get user guidance for message errors."""

        guidance_map = {
            "json_decode": "Message format is invalid. Please send valid JSON.",
            "validation": "Message is missing required fields. Check the message structure.",
            "size_limit": "Message is too large. Maximum size is 64KB.",
            "rate_limit": "Too many messages sent. Please slow down.",
            "unknown": "An error occurred processing your message. Please try again.",
        }

        return guidance_map.get(error_type, guidance_map["unknown"])

    def _generate_connection_id(self, connection_type: str) -> str:
        """Generate unique connection ID."""
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        return f"jorge_{connection_type}_{timestamp}_{unique_id}"

    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        return f"ws_err_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID for message tracking."""
        return f"ws_msg_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"

    # Public API methods

    def get_connection_status(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection status and metrics."""

        if connection_id not in self.connection_states:
            return None

        return {
            "connection_id": connection_id,
            "state": self.connection_states[connection_id].value,
            "metrics": self.connection_metrics.get(connection_id).__dict__
            if connection_id in self.connection_metrics
            else None,
            "is_connected": connection_id in self.connections,
        }

    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get status of all connections."""

        return [self.get_connection_status(conn_id) for conn_id in self.connection_states.keys()]

    async def broadcast_message(
        self, message: Dict[str, Any], message_type: str = "broadcast", exclude_connections: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Broadcast message to all connections."""

        exclude_connections = exclude_connections or []
        results = {}

        for connection_id in list(self.connections.keys()):
            if connection_id not in exclude_connections:
                success = await self.send_message(connection_id, message, message_type)
                results[connection_id] = success

        return results


# Global instance
_websocket_error_manager = WebSocketErrorManager()


def get_websocket_error_manager() -> WebSocketErrorManager:
    """Get the global WebSocket error manager instance."""
    return _websocket_error_manager


# Convenience decorators for WebSocket endpoints


def websocket_error_handler(connection_type: str = "general", auto_reconnect: bool = True):
    """Decorator to add error handling to WebSocket endpoints."""

    def decorator(func):
        async def wrapper(websocket: WebSocket, *args, **kwargs):
            manager = get_websocket_error_manager()
            connection_id = None

            try:
                connection_id = await manager.register_connection(websocket=websocket, connection_type=connection_type)

                # Call the original endpoint function
                return await func(websocket, connection_id, *args, **kwargs)

            except WebSocketDisconnect:
                if connection_id:
                    await manager._handle_disconnection(connection_id, "client_disconnect")
            except Exception as e:
                if connection_id:
                    await manager._handle_connection_error(
                        connection_id=connection_id, error=e, context="endpoint_execution"
                    )
                raise
            finally:
                if connection_id:
                    await manager._cleanup_connection(connection_id, "endpoint_complete")

        return wrapper

    return decorator
