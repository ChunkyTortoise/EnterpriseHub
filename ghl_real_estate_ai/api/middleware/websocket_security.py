"""
WebSocket Security Middleware

Features:
- WebSocket connection authentication
- Rate limiting for WebSocket connections
- Message validation and sanitization
- Connection monitoring and abuse detection
- Secure WebSocket session management
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from starlette.websockets import WebSocketState
import jwt
from jwt import DecodeError, ExpiredSignatureError

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.middleware.jwt_auth import JWTAuth, SECRET_KEY, ALGORITHM

logger = get_logger(__name__)


class WebSocketConnectionManager:
    """Enhanced WebSocket connection manager with security features."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.authenticated_connections: Dict[str, Dict[str, Any]] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.connection_limits = {
            'max_connections_per_ip': 10,
            'max_total_connections': 1000,
            'max_message_rate': 60,  # messages per minute
            'max_message_size': 64 * 1024,  # 64KB
        }
        self.ip_connections: Dict[str, Set[str]] = defaultdict(set)
        self.message_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> bool:
        """
        Establish WebSocket connection with security checks.

        Returns:
            bool: True if connection is allowed, False otherwise
        """
        try:
            # Check connection limits
            if not await self._check_connection_limits(client_ip, connection_id):
                logger.warning(
                    f"WebSocket connection denied due to limits: {client_ip}",
                    extra={
                        "security_event": "websocket_connection_denied",
                        "client_ip": client_ip,
                        "connection_id": connection_id,
                        "reason": "connection_limits"
                    }
                )
                return False

            # Accept the WebSocket connection
            await websocket.accept()

            # Store connection metadata
            self.connection_metadata[connection_id] = {
                'client_ip': client_ip,
                'user_agent': user_agent,
                'connected_at': datetime.utcnow(),
                'authenticated': False,
                'user_id': None,
                'message_count': 0,
                'last_activity': datetime.utcnow()
            }

            # Track IP connections
            self.ip_connections[client_ip].add(connection_id)
            self.active_connections[connection_id] = websocket

            # Authenticate if token provided
            if auth_token:
                await self._authenticate_connection(connection_id, auth_token)

            logger.info(
                f"WebSocket connection established: {connection_id}",
                extra={
                    "websocket_event": "connection_established",
                    "connection_id": connection_id,
                    "client_ip": client_ip,
                    "authenticated": self.connection_metadata[connection_id]['authenticated']
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"Error establishing WebSocket connection: {e}",
                extra={
                    "websocket_event": "connection_error",
                    "connection_id": connection_id,
                    "client_ip": client_ip,
                    "error": str(e)
                }
            )
            return False

    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket connection and cleanup."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            metadata = self.connection_metadata.get(connection_id, {})

            try:
                if websocket.application_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")

            # Cleanup tracking
            del self.active_connections[connection_id]

            if connection_id in self.authenticated_connections:
                del self.authenticated_connections[connection_id]

            if connection_id in self.connection_metadata:
                client_ip = metadata.get('client_ip')
                if client_ip and client_ip in self.ip_connections:
                    self.ip_connections[client_ip].discard(connection_id)
                    if not self.ip_connections[client_ip]:
                        del self.ip_connections[client_ip]

                del self.connection_metadata[connection_id]

            if connection_id in self.message_rates:
                del self.message_rates[connection_id]

            logger.info(
                f"WebSocket connection closed: {connection_id}",
                extra={
                    "websocket_event": "connection_closed",
                    "connection_id": connection_id,
                    "duration_seconds": (
                        datetime.utcnow() - metadata.get('connected_at', datetime.utcnow())
                    ).total_seconds() if metadata else 0
                }
            )

    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific WebSocket connection."""
        if connection_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)

            # Update activity tracking
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['last_activity'] = datetime.utcnow()

            return True

        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            return False

    async def broadcast_message(self, message: Dict[str, Any], authenticated_only: bool = True):
        """Broadcast message to all or authenticated connections."""
        target_connections = (
            self.authenticated_connections.keys() if authenticated_only
            else self.active_connections.keys()
        )

        disconnect_list = []
        for connection_id in list(target_connections):
            success = await self.send_message(connection_id, message)
            if not success:
                disconnect_list.append(connection_id)

        # Clean up failed connections
        for connection_id in disconnect_list:
            await self.disconnect(connection_id)

    async def validate_message(
        self,
        connection_id: str,
        message_data: str
    ) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate incoming WebSocket message.

        Returns:
            tuple: (is_valid, parsed_message, error_reason)
        """
        try:
            # Check message rate limiting
            if not await self._check_message_rate(connection_id):
                return False, None, "Message rate limit exceeded"

            # Check message size
            if len(message_data) > self.connection_limits['max_message_size']:
                logger.warning(
                    f"WebSocket message too large: {len(message_data)} bytes",
                    extra={
                        "security_event": "websocket_message_too_large",
                        "connection_id": connection_id,
                        "message_size": len(message_data)
                    }
                )
                return False, None, "Message too large"

            # Parse JSON
            try:
                message = json.loads(message_data)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Invalid JSON in WebSocket message: {e}",
                    extra={
                        "security_event": "websocket_invalid_json",
                        "connection_id": connection_id,
                        "error": str(e)
                    }
                )
                return False, None, "Invalid JSON format"

            # Validate message structure
            if not isinstance(message, dict):
                return False, None, "Message must be a JSON object"

            # Basic security validation
            if await self._contains_suspicious_content(message):
                logger.warning(
                    "Suspicious content in WebSocket message",
                    extra={
                        "security_event": "websocket_suspicious_content",
                        "connection_id": connection_id,
                        "message_type": message.get('type', 'unknown')
                    }
                )
                return False, None, "Message contains suspicious content"

            # Update message tracking
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['message_count'] += 1
                self.connection_metadata[connection_id]['last_activity'] = datetime.utcnow()

            return True, message, None

        except Exception as e:
            logger.error(f"Error validating WebSocket message: {e}")
            return False, None, "Message validation error"

    async def _check_connection_limits(self, client_ip: str, connection_id: str) -> bool:
        """Check if connection is within limits."""
        # Check per-IP connection limit
        ip_connection_count = len(self.ip_connections.get(client_ip, set()))
        if ip_connection_count >= self.connection_limits['max_connections_per_ip']:
            return False

        # Check total connection limit
        if len(self.active_connections) >= self.connection_limits['max_total_connections']:
            return False

        return True

    async def _check_message_rate(self, connection_id: str) -> bool:
        """Check if message rate is within limits."""
        now = time.time()
        message_times = self.message_rates[connection_id]

        # Add current message time
        message_times.append(now)

        # Count messages in the last minute
        minute_ago = now - 60
        recent_messages = [t for t in message_times if t > minute_ago]
        self.message_rates[connection_id] = deque(recent_messages, maxlen=100)

        return len(recent_messages) <= self.connection_limits['max_message_rate']

    async def _authenticate_connection(self, connection_id: str, auth_token: str) -> bool:
        """Authenticate WebSocket connection using JWT token."""
        try:
            # Verify JWT token
            payload = JWTAuth.verify_token(auth_token)
            user_id = payload.get('sub')

            if user_id:
                # Store authenticated connection
                self.authenticated_connections[connection_id] = {
                    'user_id': user_id,
                    'authenticated_at': datetime.utcnow(),
                    'token_payload': payload
                }

                # Update metadata
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]['authenticated'] = True
                    self.connection_metadata[connection_id]['user_id'] = user_id

                logger.info(
                    f"WebSocket connection authenticated: {connection_id}",
                    extra={
                        "websocket_event": "connection_authenticated",
                        "connection_id": connection_id,
                        "user_id": user_id
                    }
                )
                return True

        except (DecodeError, ExpiredSignatureError) as e:
            logger.warning(
                f"WebSocket authentication failed: {e}",
                extra={
                    "security_event": "websocket_auth_failed",
                    "connection_id": connection_id,
                    "error": str(e)
                }
            )

        return False

    async def _contains_suspicious_content(self, message: Dict[str, Any]) -> bool:
        """Check if message contains suspicious content."""
        suspicious_patterns = [
            'script', 'javascript', 'eval', 'function',
            'document.', 'window.', 'alert(', 'prompt(',
            'confirm(', 'location.', 'history.'
        ]

        def check_value(value):
            if isinstance(value, str):
                value_lower = value.lower()
                return any(pattern in value_lower for pattern in suspicious_patterns)
            elif isinstance(value, dict):
                return any(check_value(v) for v in value.values())
            elif isinstance(value, list):
                return any(check_value(item) for item in value)
            return False

        return check_value(message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        now = datetime.utcnow()
        authenticated_count = len(self.authenticated_connections)
        total_count = len(self.active_connections)

        # Calculate average connection duration
        total_duration = 0
        for metadata in self.connection_metadata.values():
            duration = (now - metadata.get('connected_at', now)).total_seconds()
            total_duration += duration

        avg_duration = total_duration / max(total_count, 1)

        return {
            'total_connections': total_count,
            'authenticated_connections': authenticated_count,
            'unauthenticated_connections': total_count - authenticated_count,
            'unique_ips': len(self.ip_connections),
            'average_duration_seconds': avg_duration,
            'connection_limits': self.connection_limits,
            'total_messages_processed': sum(
                metadata.get('message_count', 0)
                for metadata in self.connection_metadata.values()
            )
        }


# Global connection manager instance
connection_manager = WebSocketConnectionManager()


async def secure_websocket_endpoint(
    websocket: WebSocket,
    connection_id: str,
    auth_token: Optional[str] = None,
    require_auth: bool = False
):
    """
    Secure WebSocket endpoint decorator.

    Args:
        websocket: FastAPI WebSocket instance
        connection_id: Unique connection identifier
        auth_token: Optional JWT authentication token
        require_auth: Whether authentication is required
    """
    client_ip = websocket.client.host if websocket.client else "unknown"
    user_agent = websocket.headers.get("user-agent")

    # Establish secure connection
    connected = await connection_manager.connect(
        websocket=websocket,
        connection_id=connection_id,
        client_ip=client_ip,
        user_agent=user_agent,
        auth_token=auth_token
    )

    if not connected:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Check authentication requirement
    if require_auth and connection_id not in connection_manager.authenticated_connections:
        await websocket.send_json({
            "type": "error",
            "message": "Authentication required",
            "code": "auth_required"
        })
        await connection_manager.disconnect(connection_id)
        return

    try:
        while True:
            # Receive message
            try:
                message_data = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            # Validate message
            is_valid, parsed_message, error_reason = await connection_manager.validate_message(
                connection_id, message_data
            )

            if not is_valid:
                await websocket.send_json({
                    "type": "error",
                    "message": error_reason or "Invalid message",
                    "code": "validation_error"
                })
                continue

            # Process message (this would be handled by the specific endpoint)
            yield parsed_message

    except WebSocketException as e:
        logger.error(f"WebSocket error: {e}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(connection_id)


def get_websocket_manager() -> WebSocketConnectionManager:
    """Get the global WebSocket connection manager."""
    return connection_manager