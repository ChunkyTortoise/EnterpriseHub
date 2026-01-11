"""
Real-Time WebSocket Routes for GHL Real Estate AI

Provides WebSocket endpoints for:
- Live lead scoring updates
- Real-time dashboard notifications
- Agent activity streams
"""

import json
import asyncio
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

from ghl_real_estate_ai.services.real_time_scoring import real_time_scoring
from ghl_real_estate_ai.api.middleware.jwt_auth import verify_websocket_token
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/scoring/{tenant_id}")
async def websocket_lead_scoring(
    websocket: WebSocket,
    tenant_id: str,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time lead scoring updates

    Authentication: Pass JWT token as query parameter

    Message Format:
    {
        "event_type": "score_update",
        "lead_id": "lead_123",
        "tenant_id": "tenant_456",
        "score": 87.5,
        "confidence": 0.92,
        "factors": {"budget": 0.9, "location": 0.85, "timeline": 0.8},
        "timestamp": "2026-01-09T20:15:30Z",
        "latency_ms": 45.2
    }
    """

    # Authenticate WebSocket connection
    user_data = await verify_websocket_token(token)
    if not user_data:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return

    # Verify tenant access
    if not _verify_tenant_access(user_data, tenant_id):
        await websocket.close(code=4003, reason="Insufficient permissions for tenant")
        return

    # Connect to real-time scoring service
    await real_time_scoring.connect_websocket(websocket, tenant_id)

    try:
        logger.info(f"🔌 WebSocket connected: user={user_data.get('user_id')}, tenant={tenant_id}")

        # Send connection confirmation
        await websocket.send_json({
            "event_type": "connection_established",
            "tenant_id": tenant_id,
            "user_id": user_data.get("user_id"),
            "timestamp": "2026-01-09T20:15:30Z",
            "features": ["real_time_scoring", "batch_updates", "performance_metrics"]
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (optional features)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30-second timeout for ping/pong
                )

                await _handle_client_message(websocket, tenant_id, data)

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "event_type": "ping",
                        "timestamp": "2026-01-09T20:15:30Z"
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"WebSocket message handling error: {e}")

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: tenant={tenant_id}")
    except Exception as e:
        logger.error(f"🔌 WebSocket error for tenant {tenant_id}: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="Internal server error")
    finally:
        # Clean up connection
        await real_time_scoring.disconnect_websocket(websocket, tenant_id)


@router.websocket("/dashboard/{tenant_id}")
async def websocket_dashboard_updates(
    websocket: WebSocket,
    tenant_id: str,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time dashboard updates

    Broadcasts:
    - New lead notifications
    - Score changes
    - Agent activity updates
    - System alerts
    """

    # Authenticate
    user_data = await verify_websocket_token(token)
    if not user_data or not _verify_tenant_access(user_data, tenant_id):
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await websocket.accept()

    try:
        logger.info(f"📊 Dashboard WebSocket connected: tenant={tenant_id}")

        # Send initial dashboard state
        dashboard_state = await _get_dashboard_state(tenant_id)
        await websocket.send_json({
            "event_type": "dashboard_init",
            "tenant_id": tenant_id,
            "data": dashboard_state
        })

        # Subscribe to dashboard events
        await _subscribe_dashboard_events(websocket, tenant_id)

    except WebSocketDisconnect:
        logger.info(f"📊 Dashboard WebSocket disconnected: tenant={tenant_id}")
    except Exception as e:
        logger.error(f"📊 Dashboard WebSocket error: {e}")


@router.get("/performance")
async def get_realtime_performance(tenant_id: str = Query(...)) -> Dict:
    """
    Get current real-time system performance metrics

    Returns:
    - Scoring latency statistics
    - WebSocket connection counts
    - Cache hit rates
    - System health indicators
    """

    metrics = await real_time_scoring.get_performance_metrics()

    return {
        "status": "healthy" if metrics["avg_latency_ms"] < 100 else "degraded",
        "scoring_performance": {
            "average_latency_ms": round(metrics["avg_latency_ms"], 1),
            "total_scores": metrics["total_scores"],
            "target_latency_ms": 100,
            "performance_ratio": min(100 / max(metrics["avg_latency_ms"], 1), 1.0)
        },
        "connections": {
            "active_websockets": metrics["active_connections"],
            "tenant_connections": metrics["tenant_connections"]
        },
        "cache": {
            "hit_rate": round(metrics["cache_hit_rate"], 3),
            "redis_connected": metrics["redis_connected"]
        },
        "timestamp": metrics["timestamp"]
    }


@router.post("/score-trigger")
async def trigger_lead_scoring(
    lead_id: str,
    tenant_id: str,
    lead_data: Dict,
    user_data: Dict = Depends(verify_websocket_token)
) -> Dict:
    """
    Manually trigger real-time lead scoring
    Useful for testing or forced re-scoring
    """

    if not _verify_tenant_access(user_data, tenant_id):
        return {"error": "Insufficient permissions"}

    try:
        scoring_event = await real_time_scoring.score_lead_realtime(
            lead_id=lead_id,
            tenant_id=tenant_id,
            lead_data=lead_data,
            broadcast=True
        )

        return {
            "success": True,
            "lead_id": lead_id,
            "score": scoring_event.score,
            "latency_ms": scoring_event.latency_ms,
            "broadcasted": True
        }

    except Exception as e:
        logger.error(f"Manual scoring trigger failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Helper functions
def _verify_tenant_access(user_data: Dict, tenant_id: str) -> bool:
    """Verify user has access to the specified tenant"""
    user_tenants = user_data.get("tenants", [])
    user_role = user_data.get("role", "user")

    # Admin can access any tenant
    if user_role == "admin":
        return True

    # Check if user belongs to this tenant
    return tenant_id in user_tenants


async def _handle_client_message(websocket: WebSocket, tenant_id: str, data: Dict) -> None:
    """Handle messages sent from client to WebSocket"""
    message_type = data.get("type", "unknown")

    if message_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": "2026-01-09T20:15:30Z"})

    elif message_type == "request_metrics":
        metrics = await real_time_scoring.get_performance_metrics()
        await websocket.send_json({
            "type": "metrics_response",
            "data": metrics
        })

    elif message_type == "subscribe_lead":
        lead_id = data.get("lead_id")
        if lead_id:
            # Add lead-specific subscription logic here
            await websocket.send_json({
                "type": "subscription_confirmed",
                "lead_id": lead_id
            })

    else:
        logger.warning(f"Unknown WebSocket message type: {message_type}")


async def _get_dashboard_state(tenant_id: str) -> Dict:
    """Get current dashboard state for initial load"""
    # This would fetch current metrics, active leads, etc.
    # For now, return placeholder data
    return {
        "active_leads": 42,
        "avg_score": 73.5,
        "hot_leads": 8,
        "recent_activity": [],
        "system_status": "healthy"
    }


async def _subscribe_dashboard_events(websocket: WebSocket, tenant_id: str) -> None:
    """Subscribe to dashboard-relevant events"""
    # This would set up subscriptions to various event streams
    # For now, just keep connection alive
    try:
        while True:
            await asyncio.sleep(30)  # Keep alive
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    "event_type": "heartbeat",
                    "timestamp": "2026-01-09T20:15:30Z"
                })
            else:
                break
    except WebSocketDisconnect:
        pass