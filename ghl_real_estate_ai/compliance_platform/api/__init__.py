"""
Enterprise AI Compliance Platform - API Module

Provides FastAPI routes for the compliance platform including:
- AI model registration and management
- Compliance assessment and scoring
- Violation tracking and acknowledgment
- Report generation
- Dashboard and metrics endpoints
- Webhook management for external event notifications
"""

from .router import router
from .webhooks import (
    DeliveryStatus,
    WebhookDeliveryService,
    WebhookEventType,
    WebhookPayload,
    WebhookSubscription,
    broadcast_compliance_event,
    get_delivery_service,
)
from .webhooks import (
    router as webhooks_router,
)

__all__ = [
    "router",
    "webhooks_router",
    "WebhookDeliveryService",
    "WebhookEventType",
    "WebhookSubscription",
    "WebhookPayload",
    "DeliveryStatus",
    "get_delivery_service",
    "broadcast_compliance_event",
]
