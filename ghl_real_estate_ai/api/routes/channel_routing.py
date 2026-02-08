"""
Unified Channel Router API Routes

Exposes compliance-aware message routing, channel preference learning,
cross-channel analytics, and delivery tracking.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.unified_channel_router import (
    get_channel_router,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/channels",
    tags=["Channel Routing"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class SendMessageRequest(BaseModel):
    contact_id: str = Field(..., description="Contact identifier")
    message: str = Field(..., description="Message content")
    preferred_channel: str = Field("sms", description="Preferred channel: sms, email, voice, video, chat")
    priority: str = Field("normal", description="Priority: low, normal, high, urgent")
    metadata: Optional[Dict[str, Any]] = None
    subject: Optional[str] = Field(None, description="Email subject (if email channel)")


class DeliveryResponse(BaseModel):
    contact_id: str
    message_id: str
    channel_used: str
    delivery_status: str
    compliance_status: str
    sentiment_polarity: float
    fallback_channel: Optional[str] = None
    error: Optional[str] = None


class ChannelAnalyticsResponse(BaseModel):
    total_messages: int
    messages_by_channel: Dict[str, int]
    delivery_rate: float
    compliance_block_rate: float
    channel_effectiveness: Dict[str, float]
    preferred_channels: Dict[str, str]


class BatchSendRequest(BaseModel):
    messages: List[SendMessageRequest] = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/send", response_model=DeliveryResponse)
async def send_message(request: SendMessageRequest):
    """Route and deliver a message with compliance and sentiment checks."""
    try:
        router_service = get_channel_router()
        result = await router_service.send_message(
            contact_id=request.contact_id,
            message=request.message,
            preferred_channel=request.preferred_channel,
            priority=request.priority,
            metadata=request.metadata,
            subject=request.subject,
        )
        return DeliveryResponse(
            contact_id=result.contact_id,
            message_id=result.message_id,
            channel_used=result.channel_used.value,
            delivery_status=result.delivery_status.value,
            compliance_status=result.compliance_status,
            sentiment_polarity=result.sentiment_polarity,
            fallback_channel=result.fallback_channel.value if result.fallback_channel else None,
            error=result.error,
        )
    except Exception as e:
        logger.error("Message delivery failed for %s: %s", request.contact_id, e)
        raise HTTPException(500, f"Channel routing error: {e}")


@router.post("/send/batch")
async def send_messages_batch(request: BatchSendRequest):
    """Send messages to multiple contacts."""
    try:
        router_service = get_channel_router()
        results = []
        for msg in request.messages:
            result = await router_service.send_message(
                contact_id=msg.contact_id,
                message=msg.message,
                preferred_channel=msg.preferred_channel,
                priority=msg.priority,
                metadata=msg.metadata,
                subject=msg.subject,
            )
            results.append(
                {
                    "contact_id": result.contact_id,
                    "message_id": result.message_id,
                    "channel_used": result.channel_used.value,
                    "delivery_status": result.delivery_status.value,
                    "compliance_status": result.compliance_status,
                }
            )
        delivered = sum(1 for r in results if r["delivery_status"] in ("sent", "delivered", "fallback"))
        return {"results": results, "total": len(results), "delivered": delivered}
    except Exception as e:
        logger.error("Batch message delivery failed: %s", e)
        raise HTTPException(500, f"Batch delivery error: {e}")


@router.get("/preference/{contact_id}")
async def get_channel_preference(contact_id: str):
    """Get the learned optimal channel for a contact."""
    router_service = get_channel_router()
    pref = await router_service.get_channel_preference(contact_id)
    return {
        "contact_id": contact_id,
        "preferred_channel": pref.value if pref else None,
    }


@router.get("/analytics", response_model=ChannelAnalyticsResponse)
async def get_channel_analytics():
    """Get cross-channel delivery analytics."""
    try:
        router_service = get_channel_router()
        analytics = await router_service.get_analytics()
        return ChannelAnalyticsResponse(
            total_messages=analytics.total_messages,
            messages_by_channel=analytics.messages_by_channel,
            delivery_rate=analytics.delivery_rate,
            compliance_block_rate=analytics.compliance_block_rate,
            channel_effectiveness=analytics.channel_effectiveness,
            preferred_channels=analytics.preferred_channels,
        )
    except Exception as e:
        logger.error("Channel analytics failed: %s", e)
        raise HTTPException(500, f"Analytics error: {e}")


@router.delete("/analytics")
async def clear_channel_analytics():
    """Clear channel routing analytics."""
    router_service = get_channel_router()
    router_service.clear_analytics()
    return {"status": "cleared"}


@router.get("/health")
async def channel_routing_health():
    """Health check for the unified channel router."""
    try:
        router_service = get_channel_router()
        return {
            "status": "healthy",
            "service": "unified_channel_router",
            "registered_handlers": len(router_service._channel_handlers),
            "contacts_with_preferences": len(router_service._preferences),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
