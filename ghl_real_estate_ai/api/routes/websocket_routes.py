"""
WebSocket API Routes for Real-Time Dashboard Communication.

Provides FastAPI WebSocket endpoints for real-time communication with
the dashboard frontend. Includes authentication, connection management,
and administrative endpoints for monitoring WebSocket performance.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auth_service import UserRole, get_auth_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/websocket", tags=["Real-Time WebSocket"])

# Get service instances
websocket_manager = get_websocket_manager()
event_publisher = get_event_publisher()
auth_service = get_auth_service()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    Main WebSocket endpoint for real-time dashboard communication.

    Query Parameters:
        token: JWT authentication token (required)

    WebSocket Protocol:
        - Authentication required via JWT token
        - Supports heartbeat messages for connection health monitoring
        - Event subscription management
        - Role-based event filtering

    Message Types:
        Client -> Server:
        - heartbeat: Connection health check
        - subscribe: Subscribe to specific event types
        - unsubscribe: Unsubscribe from event types
        - get_status: Get connection status and metrics

        Server -> Client:
        - connection_established: Welcome message with connection info
        - real_time_event: Real-time event data
        - heartbeat_ack: Heartbeat acknowledgment
        - subscription_updated: Subscription change confirmation
        - status: Connection status response
    """
    connection_id = None

    try:
        # Validate token parameter
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
            return

        # Authenticate WebSocket connection
        client = await websocket_manager.authenticate_websocket(websocket, token)
        if not client:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            return

        # Establish connection
        connection_id = await websocket_manager.connect(websocket, client)
        logger.info(f"WebSocket connection established: {connection_id} for user {client.username}")

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client message
                await websocket_manager.handle_client_message(connection_id, message)

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from {connection_id}: {e}")
                await websocket_manager.send_personal_message(
                    connection_id, {"type": "error", "message": "Invalid JSON format", "error": str(e)}
                )

            except Exception as e:
                logger.error(f"Error handling WebSocket message from {connection_id}: {e}")
                await websocket_manager.send_personal_message(
                    connection_id, {"type": "error", "message": "Message processing error", "error": str(e)}
                )

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@router.get("/status")
async def get_websocket_status(current_user=Depends(get_current_user)):
    """
    Get WebSocket service status and metrics.

    Requires authentication. Returns comprehensive information about
    WebSocket connections, performance metrics, and system health.

    Returns:
        JSON object with status, metrics, and connection information
    """
    try:
        # Get metrics from WebSocket manager and event publisher
        ws_metrics = websocket_manager.get_metrics()
        event_metrics = event_publisher.get_metrics()

        # Combine metrics
        status_info = {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "websocket_metrics": ws_metrics,
            "event_metrics": event_metrics,
            "service_health": {
                "websocket_manager": "healthy",
                "event_publisher": "healthy",
                "background_services": "running",
            },
        }

        # Add user-specific information if not admin
        if current_user.role != UserRole.ADMIN:
            # Remove sensitive information for non-admin users
            status_info.pop("event_metrics", None)
            status_info["websocket_metrics"] = {
                "active_connections": ws_metrics.get("active_connections", 0),
                "your_connections": len(websocket_manager.connections_by_user.get(current_user.id, set())),
            }

        return JSONResponse(status_info)

    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/connections")
async def get_active_connections(current_user=Depends(get_current_user)):
    """
    Get information about active WebSocket connections.

    Admin only endpoint that returns details about all active connections
    including user information, connection times, and subscription status.

    Returns:
        List of active connection information
    """
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required to view connection information")

    try:
        connections = websocket_manager.get_connection_info()

        return JSONResponse(
            {"total_connections": len(connections), "connections": connections, "timestamp": datetime.now().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error getting active connections: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/broadcast")
async def broadcast_event(event_data: Dict[str, Any], current_user=Depends(get_current_user)):
    """
    Broadcast a custom event to connected clients.

    Admin only endpoint for manually broadcasting events to WebSocket clients.
    Useful for testing, maintenance announcements, and administrative messages.

    Request Body:
        - event_type: Type of event to broadcast
        - data: Event data payload
        - target_roles: Optional list of roles to target (default: all)
        - priority: Event priority (low, normal, high, critical)

    Returns:
        Confirmation of broadcast execution
    """
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required to broadcast events")

    try:
        from ghl_real_estate_ai.services.websocket_server import EventType, RealTimeEvent

        # Validate event data
        event_type_str = event_data.get("event_type")
        if not event_type_str:
            raise HTTPException(status_code=400, detail="event_type is required")

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            valid_types = [e.value for e in EventType]
            raise HTTPException(status_code=400, detail=f"Invalid event_type. Valid types: {valid_types}")

        # Create event
        event = RealTimeEvent(
            event_type=event_type,
            data=event_data.get("data", {}),
            timestamp=datetime.now(),
            user_id=current_user.id,
            priority=event_data.get("priority", "normal"),
        )

        # Determine target roles
        target_roles_str = event_data.get("target_roles", [])
        target_roles = None
        if target_roles_str:
            try:
                target_roles = {UserRole(role) for role in target_roles_str}
            except ValueError:
                valid_roles = [role.value for role in UserRole]
                raise HTTPException(status_code=400, detail=f"Invalid role in target_roles. Valid roles: {valid_roles}")

        # Broadcast event
        if target_roles:
            await websocket_manager.broadcast_event(event, target_roles=target_roles)
        else:
            await websocket_manager.broadcast_event(event)

        logger.info(
            f"Admin {current_user.username} broadcasted {event_type.value} event to {len(target_roles) if target_roles else 'all'} roles"
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "Event broadcasted successfully",
                "event_type": event_type.value,
                "target_roles": target_roles_str if target_roles_str else "all",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test-connection")
async def test_websocket_connection(current_user=Depends(get_current_user)):
    """
    Test WebSocket connectivity and authentication.

    Endpoint for testing WebSocket service health and user authentication.
    Returns connection test results and recommendations.

    Returns:
        Connection test results and service status
    """
    try:
        # Check if user has any active connections
        user_connections = websocket_manager.connections_by_user.get(current_user.id, set())

        # Get current metrics
        metrics = websocket_manager.get_metrics()

        test_results = {
            "status": "healthy",
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role.value,
            "active_connections": len(user_connections),
            "connection_ids": list(user_connections),
            "service_metrics": {
                "total_active_connections": metrics.get("active_connections", 0),
                "total_requests": metrics.get("total_connections", 0),
                "service_uptime": metrics.get("uptime_seconds", 0),
            },
            "authentication": {
                "status": "valid",
                "token_valid": True,
                "permissions": {
                    "can_connect": True,
                    "can_receive_events": True,
                    "default_subscriptions": [
                        event.value for event in websocket_manager._get_default_subscriptions(current_user.role)
                    ],
                },
            },
            "recommendations": [],
        }

        # Add recommendations based on current state
        if len(user_connections) == 0:
            test_results["recommendations"].append(
                "No active WebSocket connections. Consider connecting to enable real-time updates."
            )
        elif len(user_connections) > 3:
            test_results["recommendations"].append(
                f"Multiple connections detected ({len(user_connections)}). Consider closing unused connections for better performance."
            )

        if metrics.get("active_connections", 0) > 100:
            test_results["recommendations"].append("High connection load detected. Performance may be impacted.")

        return JSONResponse(test_results)

    except Exception as e:
        logger.error(f"Error testing WebSocket connection: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/start-services")
async def start_websocket_services(current_user=Depends(get_current_user)):
    """
    Start WebSocket background services.

    Admin only endpoint for starting WebSocket manager and event publisher
    background services. Used for service management and recovery.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required for service management")

    try:
        await websocket_manager.start_services()
        await event_publisher.start()

        logger.info(f"Admin {current_user.username} started WebSocket services")

        return JSONResponse(
            {
                "status": "success",
                "message": "WebSocket services started successfully",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error starting WebSocket services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stop-services")
async def stop_websocket_services(current_user=Depends(get_current_user)):
    """
    Stop WebSocket background services.

    Admin only endpoint for stopping WebSocket manager and event publisher
    background services. Used for maintenance and service management.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required for service management")

    try:
        await event_publisher.stop()
        await websocket_manager.stop_services()

        logger.info(f"Admin {current_user.username} stopped WebSocket services")

        return JSONResponse(
            {
                "status": "success",
                "message": "WebSocket services stopped successfully",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error stopping WebSocket services: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def websocket_health_check():
    """
    WebSocket service health check.

    Public endpoint for checking WebSocket service health.
    Does not require authentication.

    Returns:
        Service health status and basic metrics
    """
    try:
        # Get basic health information
        metrics = websocket_manager.get_metrics()

        health_status = {
            "status": "healthy",
            "service": "WebSocket Real-Time Service",
            "active_connections": metrics.get("active_connections", 0),
            "total_requests": metrics.get("total_connections", 0),
            "last_check": datetime.now().isoformat(),
            "version": "1.0.0",
        }

        return JSONResponse(health_status)

    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return JSONResponse(
            {"status": "unhealthy", "error": str(e), "last_check": datetime.now().isoformat()}, status_code=503
        )
