"""
WebSocket Intelligence API Routes

FastAPI endpoints for real-time lead intelligence streaming via WebSocket.
Integrates with WebSocket Manager for enterprise-grade performance.

Performance Targets:
- Connection latency: <100ms
- ML intelligence updates: <50ms broadcast
- Support: 100+ concurrent connections per tenant
- Cache hit rate: >90%
"""

import asyncio
import json
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from fastapi.websockets import WebSocketState

from ghl_real_estate_ai.services.websocket_manager import (
    get_websocket_manager,
    WebSocketManager,
    SubscriptionTopic,
    IntelligenceEventType,
    process_lead_event_realtime,
    ProcessingPriority
)
from ghl_real_estate_ai.api.middleware.jwt_auth import verify_websocket_token
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket-intelligence"])


# WebSocket Endpoints

@router.websocket("/intelligence/{tenant_id}")
async def websocket_lead_intelligence(
    websocket: WebSocket,
    tenant_id: str,
    token: str = Query(..., description="JWT authentication token"),
    topics: Optional[str] = Query(
        None,
        description="Comma-separated list of topics (lead_scoring,churn_prediction,property_matching)"
    ),
    lead_ids: Optional[str] = Query(
        None,
        description="Comma-separated list of lead IDs to filter (optional)"
    )
):
    """
    WebSocket endpoint for real-time lead intelligence streaming.

    Authentication: Pass JWT token as query parameter.

    **Subscription Topics:**
    - `lead_scoring`: Real-time lead score updates
    - `churn_prediction`: Churn risk alerts
    - `property_matching`: Property match notifications
    - `lead_intelligence`: All intelligence updates
    - `system_metrics`: Performance and health metrics
    - `all`: Subscribe to all events (default)

    **Message Format (Received):**
    ```json
    {
        "event_type": "lead_score_update",
        "event_id": "evt_abc123",
        "tenant_id": "tenant_123",
        "lead_id": "lead_456",
        "timestamp": "2026-01-10T12:34:56Z",
        "lead_score": {
            "score": 0.87,
            "confidence": "high",
            "tier": "hot",
            "inference_time_ms": 28.3
        },
        "processing_time_ms": 34.8,
        "cache_hit": true,
        "broadcast_latency_ms": 12.5
    }
    ```

    **Client Messages (Optional):**
    - Ping: `{"type": "ping"}` → Response: `{"type": "pong"}`
    - Request Metrics: `{"type": "request_metrics"}` → Performance data
    - Subscribe Lead: `{"type": "subscribe_lead", "lead_id": "lead_123"}`
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

    # Parse subscription topics
    subscription_topics = _parse_topics(topics)

    # Parse lead filters
    lead_filters = _parse_lead_ids(lead_ids)

    # Get WebSocket manager
    ws_manager = await get_websocket_manager()

    # Subscribe to intelligence updates
    subscription_id = await ws_manager.subscribe_to_lead_intelligence(
        websocket=websocket,
        tenant_id=tenant_id,
        user_id=user_data.get("user_id", "unknown"),
        topics=subscription_topics,
        lead_filters=lead_filters
    )

    if not subscription_id:
        await websocket.close(code=1011, reason="Failed to establish subscription")
        return

    try:
        logger.info(
            f"WebSocket intelligence connected: "
            f"subscription={subscription_id}, tenant={tenant_id}, "
            f"topics={[t.value for t in subscription_topics]}"
        )

        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "user_id": user_data.get("user_id"),
            "timestamp": datetime.now().isoformat(),
            "topics": [t.value for t in subscription_topics],
            "lead_filters": lead_filters,
            "features": [
                "real_time_ml_intelligence",
                "lead_scoring_updates",
                "churn_risk_alerts",
                "property_match_notifications",
                "performance_metrics"
            ]
        })

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages with timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30-second timeout
                )

                # Handle client message
                await _handle_client_message(
                    websocket,
                    ws_manager,
                    subscription_id,
                    tenant_id,
                    data
                )

            except asyncio.TimeoutError:
                # Send heartbeat ping
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })

            except WebSocketDisconnect:
                break

            except Exception as e:
                logger.warning(f"WebSocket message handling error: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket intelligence disconnected: {subscription_id}")

    except Exception as e:
        logger.error(f"WebSocket intelligence error: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="Internal server error")

    finally:
        # Clean up subscription
        await ws_manager.unsubscribe(subscription_id)


@router.websocket("/dashboard/{tenant_id}")
async def websocket_dashboard_intelligence(
    websocket: WebSocket,
    tenant_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for dashboard real-time intelligence updates.

    Provides aggregated intelligence updates optimized for dashboard displays:
    - Lead score changes and trends
    - Churn risk alerts for intervention
    - Hot lead notifications
    - System performance metrics

    **Message Format:**
    ```json
    {
        "type": "dashboard_update",
        "timestamp": "2026-01-10T12:34:56Z",
        "data": {
            "active_hot_leads": 12,
            "avg_lead_score": 0.73,
            "churn_alerts": 3,
            "recent_updates": [...],
            "performance": {
                "avg_processing_ms": 34.8,
                "cache_hit_rate": 0.92
            }
        }
    }
    ```
    """
    # Authenticate
    user_data = await verify_websocket_token(token)
    if not user_data or not _verify_tenant_access(user_data, tenant_id):
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Get WebSocket manager
    ws_manager = await get_websocket_manager()

    # Subscribe to all intelligence topics for dashboard
    subscription_id = await ws_manager.subscribe_to_lead_intelligence(
        websocket=websocket,
        tenant_id=tenant_id,
        user_id=user_data.get("user_id", "unknown"),
        topics=[SubscriptionTopic.ALL]
    )

    if not subscription_id:
        await websocket.close(code=1011, reason="Failed to establish subscription")
        return

    try:
        logger.info(f"Dashboard WebSocket connected: tenant={tenant_id}")

        # Send initial dashboard state
        await websocket.send_json({
            "type": "dashboard_init",
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "subscription_id": subscription_id
        })

        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )

                # Handle dashboard-specific messages
                if data.get("type") == "request_summary":
                    health = await ws_manager.get_connection_health()
                    await websocket.send_json({
                        "type": "dashboard_summary",
                        "data": health["websocket_manager"],
                        "timestamp": datetime.now().isoformat()
                    })

            except asyncio.TimeoutError:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info(f"Dashboard WebSocket disconnected: tenant={tenant_id}")

    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")

    finally:
        await ws_manager.unsubscribe(subscription_id)


# HTTP Endpoints for WebSocket Support

@router.get("/health")
async def get_websocket_health():
    """
    Get WebSocket manager health and performance metrics.

    **Returns:**
    - Connection statistics
    - Performance metrics
    - Cache performance
    - ML inference performance
    - Health status
    """
    try:
        ws_manager = await get_websocket_manager()
        health = await ws_manager.get_connection_health()

        return {
            "status": "healthy" if health["performance_status"]["overall_healthy"] else "degraded",
            "timestamp": health["timestamp"],
            "metrics": health["websocket_manager"],
            "performance_targets": health["performance_targets"],
            "performance_status": health["performance_status"]
        }

    except Exception as e:
        logger.error(f"Failed to get WebSocket health: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WebSocket health check failed: {str(e)}"
        )


@router.post("/trigger-intelligence")
async def trigger_lead_intelligence(
    lead_id: str = Query(..., description="Lead ID to process"),
    tenant_id: str = Query(..., description="Tenant ID"),
    priority: str = Query("medium", description="Processing priority (low, medium, high, critical)"),
    user_data: dict = Depends(verify_websocket_token)
):
    """
    Manually trigger lead intelligence processing and broadcasting.

    Useful for:
    - Forced lead re-scoring
    - Testing real-time updates
    - Manual intelligence refresh

    **Parameters:**
    - `lead_id`: Lead identifier to process
    - `tenant_id`: Tenant identifier
    - `priority`: Processing priority level

    **Returns:**
    - Intelligence results
    - Processing time
    - Broadcast statistics
    """
    if not _verify_tenant_access(user_data, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for tenant"
        )

    try:
        # Parse priority
        priority_map = {
            "low": ProcessingPriority.LOW,
            "medium": ProcessingPriority.MEDIUM,
            "high": ProcessingPriority.HIGH,
            "critical": ProcessingPriority.CRITICAL
        }
        processing_priority = priority_map.get(priority.lower(), ProcessingPriority.MEDIUM)

        # Process lead event
        intelligence = await process_lead_event_realtime(
            lead_id=lead_id,
            tenant_id=tenant_id,
            event_data={
                "type": "manual_trigger",
                "triggered_by": user_data.get("user_id"),
                "timestamp": datetime.now().isoformat()
            },
            priority=processing_priority
        )

        if not intelligence:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process lead intelligence"
            )

        # Build response
        return {
            "success": True,
            "lead_id": lead_id,
            "tenant_id": tenant_id,
            "intelligence": {
                "lead_score": intelligence.lead_score.score if intelligence.lead_score else None,
                "score_tier": intelligence.lead_score.score_tier if intelligence.lead_score else None,
                "churn_risk": intelligence.churn_prediction.churn_probability if intelligence.churn_prediction else None,
                "property_matches": len(intelligence.property_matches),
                "overall_health": intelligence.overall_health_score,
                "confidence": intelligence.confidence_score
            },
            "performance": {
                "processing_time_ms": intelligence.processing_time_ms,
                "cache_hit": intelligence.cache_hit_rate > 0.5,
                "ml_operations": intelligence.parallel_operations
            },
            "broadcasted": True
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to trigger lead intelligence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligence processing failed: {str(e)}"
        )


@router.get("/subscriptions/{tenant_id}")
async def get_tenant_subscriptions(
    tenant_id: str,
    user_data: dict = Depends(verify_websocket_token)
):
    """
    Get active WebSocket subscriptions for a tenant.

    **Returns:**
    - List of active subscriptions
    - Connection details
    - Subscription topics
    - Performance metrics
    """
    if not _verify_tenant_access(user_data, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for tenant"
        )

    try:
        ws_manager = await get_websocket_manager()

        # Get tenant subscriptions
        tenant_subs = ws_manager._tenant_subscriptions.get(tenant_id, set())

        subscriptions = []
        for sub_id in tenant_subs:
            subscription = ws_manager._subscriptions.get(sub_id)
            if subscription:
                subscriptions.append({
                    "subscription_id": subscription.subscription_id,
                    "connection_id": subscription.connection_id,
                    "topics": [t.value for t in subscription.topics],
                    "lead_filters": subscription.lead_filters,
                    "created_at": subscription.created_at.isoformat(),
                    "last_update": subscription.last_update.isoformat(),
                    "update_count": subscription.update_count
                })

        return {
            "tenant_id": tenant_id,
            "active_subscriptions": len(subscriptions),
            "subscriptions": subscriptions,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get tenant subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subscriptions: {str(e)}"
        )


# Helper Functions

def _verify_tenant_access(user_data: dict, tenant_id: str) -> bool:
    """Verify user has access to tenant"""
    user_tenants = user_data.get("tenants", [])
    user_role = user_data.get("role", "user")

    # Admin can access any tenant
    if user_role == "admin":
        return True

    # Check if user belongs to this tenant
    return tenant_id in user_tenants


def _parse_topics(topics_str: Optional[str]) -> List[SubscriptionTopic]:
    """Parse comma-separated topics string"""
    if not topics_str:
        return [SubscriptionTopic.ALL]

    topic_map = {
        "lead_intelligence": SubscriptionTopic.LEAD_INTELLIGENCE,
        "lead_scoring": SubscriptionTopic.LEAD_SCORING,
        "churn_prediction": SubscriptionTopic.CHURN_PREDICTION,
        "property_matching": SubscriptionTopic.PROPERTY_MATCHING,
        "system_metrics": SubscriptionTopic.SYSTEM_METRICS,
        "all": SubscriptionTopic.ALL
    }

    topics = []
    for topic_str in topics_str.split(","):
        topic_str = topic_str.strip().lower()
        if topic_str in topic_map:
            topics.append(topic_map[topic_str])

    return topics if topics else [SubscriptionTopic.ALL]


def _parse_lead_ids(lead_ids_str: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated lead IDs string"""
    if not lead_ids_str:
        return None

    return [lid.strip() for lid in lead_ids_str.split(",") if lid.strip()]


async def _handle_client_message(
    websocket: WebSocket,
    ws_manager: WebSocketManager,
    subscription_id: str,
    tenant_id: str,
    data: dict
):
    """Handle messages from WebSocket client"""
    message_type = data.get("type", "unknown")

    try:
        if message_type == "ping":
            # Respond to ping
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })

        elif message_type == "request_metrics":
            # Send performance metrics
            health = await ws_manager.get_connection_health()
            await websocket.send_json({
                "type": "metrics_response",
                "data": health["websocket_manager"],
                "timestamp": datetime.now().isoformat()
            })

        elif message_type == "subscribe_lead":
            # Add lead-specific subscription (dynamic)
            lead_id = data.get("lead_id")
            if lead_id:
                subscription = ws_manager._subscriptions.get(subscription_id)
                if subscription:
                    if subscription.lead_filters is None:
                        subscription.lead_filters = []
                    if lead_id not in subscription.lead_filters:
                        subscription.lead_filters.append(lead_id)
                        ws_manager._lead_subscriptions[lead_id].add(subscription_id)

                await websocket.send_json({
                    "type": "subscription_updated",
                    "lead_id": lead_id,
                    "timestamp": datetime.now().isoformat()
                })

        elif message_type == "unsubscribe_lead":
            # Remove lead-specific subscription
            lead_id = data.get("lead_id")
            if lead_id:
                subscription = ws_manager._subscriptions.get(subscription_id)
                if subscription and subscription.lead_filters:
                    if lead_id in subscription.lead_filters:
                        subscription.lead_filters.remove(lead_id)
                        ws_manager._lead_subscriptions[lead_id].discard(subscription_id)

                await websocket.send_json({
                    "type": "subscription_updated",
                    "lead_id": lead_id,
                    "removed": True,
                    "timestamp": datetime.now().isoformat()
                })

        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"Failed to handle client message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Failed to process message",
            "timestamp": datetime.now().isoformat()
        })


# Export router
__all__ = ["router"]
