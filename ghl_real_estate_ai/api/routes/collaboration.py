"""
Real-Time Collaboration API Routes

REST and WebSocket endpoints for live agent coordination and team collaboration.

Features:
- Room management (create, join, leave)
- Real-time messaging with delivery confirmation
- Presence tracking and status updates
- Message history with pagination
- Performance monitoring and health checks

Performance Targets:
- Message latency: <50ms (p95)
- Connection establishment: <100ms
- API response time: <100ms
"""

import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, status
from fastapi.websockets import WebSocketState

from ghl_real_estate_ai.services.realtime_collaboration_engine import (
    get_collaboration_engine,
    RealtimeCollaborationEngine
)
from ghl_real_estate_ai.models.collaboration_models import (
    Room,
    CollaborationMessage,
    PresenceUpdate,
    MessageDeliveryConfirmation,
    CreateRoomRequest,
    JoinRoomRequest,
    SendMessageRequest,
    UpdatePresenceRequest,
    GetRoomHistoryRequest,
)
from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# REST API Endpoints

@router.post("/rooms", response_model=Room, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: CreateRoomRequest,
    current_user: dict = Depends(get_current_user),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    Create a new collaboration room.

    Performance: <10ms

    **Room Types:**
    - `agent_team`: Team coordination room
    - `client_session`: Client portal communication
    - `lead_collaboration`: Lead handoff coordination
    - `property_tour`: Virtual property tour
    - `training_session`: Agent training and coaching
    - `emergency_response`: Urgent issue coordination

    **Example Request:**
    ```json
    {
        "tenant_id": "tenant_123",
        "room_type": "agent_team",
        "name": "Q1 Sales Team",
        "description": "Real-time coordination for Q1 sales team",
        "created_by": "user_456",
        "initial_members": ["user_456", "user_789"],
        "max_members": 50,
        "settings": {
            "allow_file_sharing": true,
            "message_retention_days": 30
        },
        "context": {
            "team_id": "team_123",
            "region": "west_coast"
        }
    }
    ```
    """
    try:
        # Verify user has permission to create room for tenant
        if request.tenant_id != current_user.get("tenant_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create room for this tenant"
            )

        room = await engine.create_room(request)

        if not room:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create room"
            )

        return room

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/messages", response_model=MessageDeliveryConfirmation)
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    Send a message to a collaboration room.

    Performance: <50ms (p95)

    **Message Types:**
    - `text`: Standard text message
    - `system`: System notification
    - `file_share`: File attachment
    - `document_share`: Document attachment
    - `lead_handoff`: Lead handoff notification
    - `property_share`: Property information
    - `coaching_tip`: Real-time coaching tip
    - `alert`: Important alert
    - `command`: Bot command

    **Example Request:**
    ```json
    {
        "room_id": "room_abc123",
        "sender_id": "user_456",
        "sender_name": "John Agent",
        "message_type": "text",
        "content": "New high-priority lead just came in!",
        "priority": "high",
        "metadata": {
            "lead_id": "lead_789",
            "lead_score": 95
        }
    }
    ```

    **Response includes:**
    - Message ID
    - Delivery status
    - List of users who received the message
    - Latency metrics
    """
    try:
        # Verify sender is current user
        if request.sender_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot send messages as another user"
            )

        confirmation = await engine.send_message(request)

        if not confirmation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message"
            )

        return confirmation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rooms/{room_id}/history", response_model=List[CollaborationMessage])
async def get_room_history(
    room_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    before_message_id: Optional[str] = None,
    after_message_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    Get message history for a room.

    Performance: <100ms

    **Pagination:**
    - Use `limit` to control number of messages returned (1-500)
    - Use `before_message_id` to get older messages
    - Use `after_message_id` to get newer messages

    **Example:**
    ```
    GET /collaboration/rooms/room_abc123/history?limit=50
    ```
    """
    try:
        request = GetRoomHistoryRequest(
            room_id=room_id,
            limit=limit,
            before_message_id=before_message_id,
            after_message_id=after_message_id
        )

        messages = await engine.get_room_history(request)

        return messages

    except Exception as e:
        logger.error(f"Error getting room history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/presence", status_code=status.HTTP_204_NO_CONTENT)
async def update_presence(
    request: UpdatePresenceRequest,
    current_user: dict = Depends(get_current_user),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    Update user presence status.

    **Status Options:**
    - `online`: User is active
    - `away`: User is away from keyboard
    - `busy`: User is busy (do not disturb for non-urgent)
    - `offline`: User is offline
    - `in_call`: User is in a call
    - `do_not_disturb`: User should not be disturbed

    **Example Request:**
    ```json
    {
        "user_id": "user_456",
        "tenant_id": "tenant_123",
        "status": "busy",
        "status_message": "In client meeting",
        "current_room_id": "room_abc123"
    }
    ```
    """
    try:
        # Verify user is updating their own presence
        if request.user_id != current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update presence for another user"
            )

        success = await engine.update_presence(request)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update presence"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating presence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rooms/{room_id}/presence", response_model=List[PresenceUpdate])
async def get_room_presence(
    room_id: str,
    current_user: dict = Depends(get_current_user),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    Get presence status for all room members.

    Returns real-time presence information for all users in the room.

    **Example Response:**
    ```json
    [
        {
            "user_id": "user_456",
            "tenant_id": "tenant_123",
            "status": "online",
            "status_message": null,
            "last_seen": "2026-01-10T15:30:00Z",
            "current_room_id": "room_abc123"
        },
        {
            "user_id": "user_789",
            "tenant_id": "tenant_123",
            "status": "busy",
            "status_message": "In client meeting",
            "last_seen": "2026-01-10T15:25:00Z",
            "current_room_id": "room_abc123"
        }
    ]
    ```
    """
    try:
        presence_list = await engine.get_room_presence(room_id)

        return presence_list

    except Exception as e:
        logger.error(f"Error getting room presence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics")
async def get_collaboration_metrics(
    current_user: dict = Depends(get_current_user),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    Get comprehensive collaboration performance metrics.

    **Metrics include:**
    - Message latency (average, p95, p99)
    - Message throughput (messages/sec)
    - Connection health
    - Redis pub/sub health
    - WebSocket server health
    - Performance target compliance

    **Example Response:**
    ```json
    {
        "timestamp": "2026-01-10T15:30:00Z",
        "collaboration_engine": {
            "total_connections": 250,
            "active_rooms": 45,
            "total_messages_sent": 12500,
            "average_message_latency_ms": 32.5,
            "p95_message_latency_ms": 45.2,
            "p99_message_latency_ms": 62.1,
            "messages_per_second": 125.3
        },
        "performance_status": {
            "latency_target_met": true,
            "throughput_target_met": true,
            "overall_healthy": true
        }
    }
    ```
    """
    try:
        metrics = await engine.get_collaboration_metrics()

        return metrics

    except Exception as e:
        logger.error(f"Error getting collaboration metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# WebSocket Endpoints

@router.websocket("/ws/{room_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(..., description="JWT authentication token"),
    user_id: str = Query(..., description="User identifier"),
    display_name: str = Query(..., description="User display name"),
    engine: RealtimeCollaborationEngine = Depends(get_collaboration_engine)
):
    """
    WebSocket endpoint for real-time collaboration in a room.

    **Connection:**
    ```javascript
    const ws = new WebSocket(
        'ws://localhost:8000/collaboration/ws/room_abc123?token=JWT_TOKEN&user_id=user_456&display_name=John%20Agent'
    );
    ```

    **Events Received:**
    - `connection_established`: Connection confirmation
    - `collaboration_message`: New message in room
    - `typing_indicator`: User typing notification
    - `presence_update`: User status change
    - `room_history`: Historical messages

    **Events You Can Send:**
    - `send_message`: Send a message
    - `typing_indicator`: Notify typing status
    - `update_presence`: Update your status
    - `ping`: Keep connection alive

    **Example Message:**
    ```json
    {
        "event_type": "send_message",
        "message_type": "text",
        "content": "Hello team!",
        "priority": "normal"
    }
    ```

    Performance: <100ms connection establishment, <50ms message delivery
    """
    await websocket.accept()

    try:
        # TODO: Verify JWT token
        # For now, accept connection

        # Join room
        request = JoinRoomRequest(
            room_id=room_id,
            user_id=user_id,
            display_name=display_name,
            role="member"
        )

        success = await engine.join_room(websocket, request)

        if not success:
            await websocket.close(code=4000, reason="Failed to join room")
            return

        logger.info(f"WebSocket connected: user={user_id}, room={room_id}")

        # Send connection confirmation
        await websocket.send_json({
            "event_type": "connection_established",
            "room_id": room_id,
            "user_id": user_id,
            "timestamp": "2026-01-10T15:30:00Z",
            "features": [
                "real_time_messaging",
                "presence_tracking",
                "typing_indicators",
                "file_sharing",
                "message_history"
            ]
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30-second timeout for ping/pong
                )

                await _handle_websocket_message(
                    websocket=websocket,
                    room_id=room_id,
                    user_id=user_id,
                    display_name=display_name,
                    data=data,
                    engine=engine
                )

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "event_type": "ping",
                        "timestamp": "2026-01-10T15:30:00Z"
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"WebSocket message handling error: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id}, room={room_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4001, reason=str(e))
    finally:
        # Leave room
        # TODO: Implement connection tracking to get connection_id
        # await engine.leave_room(connection_id, room_id)
        pass


# Helper functions

async def _handle_websocket_message(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
    display_name: str,
    data: Dict,
    engine: RealtimeCollaborationEngine
):
    """Handle incoming WebSocket message."""
    try:
        event_type = data.get("event_type")

        if event_type == "send_message":
            # Send message
            request = SendMessageRequest(
                room_id=room_id,
                sender_id=user_id,
                sender_name=display_name,
                message_type=data.get("message_type", "text"),
                content=data.get("content", ""),
                priority=data.get("priority", "normal"),
                metadata=data.get("metadata", {}),
                attachments=data.get("attachments", []),
                reply_to=data.get("reply_to")
            )

            confirmation = await engine.send_message(request)

            # Send confirmation back to sender
            await websocket.send_json({
                "event_type": "message_confirmation",
                "confirmation": confirmation.dict() if confirmation else None
            })

        elif event_type == "typing_indicator":
            # Send typing indicator
            is_typing = data.get("is_typing", False)

            await engine.send_typing_indicator(
                room_id=room_id,
                user_id=user_id,
                user_name=display_name,
                is_typing=is_typing
            )

        elif event_type == "update_presence":
            # Update presence
            request = UpdatePresenceRequest(
                user_id=user_id,
                tenant_id=data.get("tenant_id", ""),
                status=data.get("status", "online"),
                status_message=data.get("status_message"),
                current_room_id=room_id
            )

            await engine.update_presence(request)

        elif event_type == "ping":
            # Respond to ping
            await websocket.send_json({
                "event_type": "pong",
                "timestamp": "2026-01-10T15:30:00Z"
            })

        else:
            logger.warning(f"Unknown event type: {event_type}")

    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket.send_json({
            "event_type": "error",
            "error": str(e)
        })


__all__ = ["router"]
