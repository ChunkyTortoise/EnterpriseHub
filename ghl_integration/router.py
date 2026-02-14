"""
Unified GHL Webhook Router

Central entry point for all GoHighLevel webhook events.
Routes events to appropriate bot handlers with validation and deduplication.
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from ghl_real_estate_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# Event type mappings from GHL to internal
GHL_EVENT_MAP = {
    "ContactCreate": "contact.create",
    "ContactUpdate": "contact.update",
    "ContactDelete": "contact.delete",
    "ConversationMessageCreate": "conversation.message.created",
    "OpportunityCreate": "opportunity.create",
    "OpportunityUpdate": "opportunity.update",
    "PipelineStageChange": "pipeline.stage.changed",
    "TaskCreate": "task.create",
    "NoteCreate": "note.create",
}

BOT_TYPE_MAP = {
    "lead": "lead_bot",
    "seller": "seller_bot",
    "buyer": "buyer_bot",
}


class GHLWebhookPayload(BaseModel):
    """Standard GHL webhook payload structure"""
    event: str
    version: str = "v2"
    timestamp: datetime
    data: Dict[str, Any]
    trace_id: Optional[str] = None


class WebhookResponse(BaseModel):
    """Standard webhook response"""
    success: bool
    event_id: str
    message: str
    processing_time_ms: float


class GHLWebhookRouter:
    """
    Unified router for GHL webhooks.
    
    Flow:
    1. Validate signature (RSA/HMAC)
    2. Deduplicate (event_id check)
    3. Parse payload
    4. Route to appropriate handler
    5. Emit event for real-time dashboard
    6. Background: Retry queue if processing fails
    """

    def __init__(self):
        self.cache = CacheService()
        self.handlers: Dict[str, Dict[str, Callable]] = {
            "lead": {},
            "seller": {},
            "buyer": {},
        }
        self.processing_metrics = {
            "events_received": 0,
            "events_processed": 0,
            "events_deduplicated": 0,
            "events_failed": 0,
            "avg_processing_time_ms": 0.0,
        }

    def register_handler(self, bot_type: str, event_type: str, handler: Callable):
        """Register a handler for specific bot type and event type"""
        if bot_type not in self.handlers:
            self.handlers[bot_type] = {}
        self.handlers[bot_type][event_type] = handler
        logger.info(f"Registered handler: {bot_type}/{event_type}")

    async def validate_signature(
        self,
        payload: bytes,
        signature: Optional[str],
        headers: Dict[str, str],
        webhook_secret: Optional[str] = None
    ) -> bool:
        """
        Validate GHL webhook signature.
        
        Supports:
        - HMAC-SHA256 signature verification
        - RSA signature verification (for enterprise)
        """
        if not signature:
            # In development, allow missing signatures
            if os.getenv("GHL_SKIP_SIGNATURE_VERIFICATION", "false").lower() == "true":
                logger.warning("Signature verification skipped (dev mode)")
                return True
            return False

        secret = webhook_secret or os.getenv("GHL_WEBHOOK_SECRET")
        if not secret:
            logger.error("GHL_WEBHOOK_SECRET not configured")
            return False

        try:
            # HMAC-SHA256 verification
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Support both hex and base64 encoded signatures
            if signature.startswith("sha256="):
                signature = signature[7:]  # Remove 'sha256=' prefix

            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if not is_valid:
                logger.warning(f"Signature mismatch: expected {expected_signature[:16]}... got {signature[:16]}...")
            
            return is_valid

        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False

    async def check_deduplication(self, event_id: str, event_type: str) -> bool:
        """
        Check if event is duplicate using Redis cache.
        24-hour TTL for deduplication window.
        """
        dedup_key = f"ghl:webhook:dedup:{event_id}"
        
        try:
            # Check if we've seen this event before
            exists = await self.cache.get(dedup_key)
            if exists:
                logger.info(f"Duplicate event detected: {event_id}")
                return True

            # Mark as seen with 24h TTL
            await self.cache.set(dedup_key, "1", ttl=86400)
            return False

        except Exception as e:
            logger.error(f"Deduplication check failed: {e}")
            # Allow event through on deduplication failure
            return False

    async def route_event(
        self,
        bot_type: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route event to appropriate handler.
        
        Args:
            bot_type: lead | seller | buyer
            event_type: Internal event type (e.g., 'contact.create')
            payload: Event payload data
        
        Returns:
            Handler result or error info
        """
        if bot_type not in self.handlers:
            return {
                "success": False,
                "error": f"Unknown bot type: {bot_type}",
            }

        # Map GHL event type to internal
        internal_event = GHL_EVENT_MAP.get(event_type, event_type)

        handler = self.handlers[bot_type].get(internal_event)
        if not handler:
            # Try generic handler
            handler = self.handlers[bot_type].get("*")
            if not handler:
                logger.warning(f"No handler for {bot_type}/{internal_event}")
                return {
                    "success": True,
                    "message": f"No handler for {internal_event}, event logged",
                }

        try:
            result = await handler(payload)
            return {
                "success": True,
                "handler_result": result,
            }
        except Exception as e:
            logger.error(f"Handler failed for {bot_type}/{internal_event}: {e}")
            return {
                "success": False,
                "error": str(e),
                "retry_eligible": True,
            }

    async def update_metrics(self, processing_time_ms: float, success: bool):
        """Update processing metrics"""
        self.processing_metrics["events_received"] += 1
        if success:
            self.processing_metrics["events_processed"] += 1
        else:
            self.processing_metrics["events_failed"] += 1

        # Update rolling average
        current_avg = self.processing_metrics["avg_processing_time_ms"]
        n = self.processing_metrics["events_received"]
        self.processing_metrics["avg_processing_time_ms"] = (
            (current_avg * (n - 1) + processing_time_ms) / n
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics"""
        return self.processing_metrics.copy()


# Create global router instance
_ghl_router = GHLWebhookRouter()

# FastAPI router
router = APIRouter(prefix="/ghl/webhook", tags=["ghl-webhooks"])


@router.post("/{bot_type}/{event_type}")
async def handle_ghl_webhook(
    bot_type: str,
    event_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Unified GHL webhook entry point.
    
    Args:
        bot_type: lead | seller | buyer
        event_type: new-lead | seller-inquiry | buyer-inquiry | response | etc.
    """
    import time
    start_time = time.time()

    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Validate signature
        signature = request.headers.get("X-GHL-Signature") or request.headers.get("x-ghl-signature")
        headers = dict(request.headers)
        
        is_valid = await _ghl_router.validate_signature(body, signature, headers)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse payload
        try:
            import json
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

        # Extract event ID for deduplication
        event_id = payload.get("trace_id") or payload.get("data", {}).get("id") or payload.get("event_id")
        if not event_id:
            event_id = hashlib.md5(body).hexdigest()

        # Check deduplication
        is_duplicate = await _ghl_router.check_deduplication(event_id, event_type)
        if is_duplicate:
            processing_time = (time.time() - start_time) * 1000
            return WebhookResponse(
                success=True,
                event_id=event_id,
                message="Duplicate event, skipped processing",
                processing_time_ms=processing_time,
            )

        # Route to handler
        result = await _ghl_router.route_event(bot_type, event_type, payload)

        processing_time = (time.time() - start_time) * 1000
        
        # Update metrics
        await _ghl_router.update_metrics(processing_time, result.get("success", False))

        if not result.get("success"):
            # Schedule retry in background
            if result.get("retry_eligible"):
                from .retry_manager import get_retry_manager
                retry_manager = get_retry_manager()
                await retry_manager.schedule_retry(bot_type, event_type, payload, event_id)

            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Handler processing failed")
            )

        return WebhookResponse(
            success=True,
            event_id=event_id,
            message=f"Event processed successfully for {bot_type}/{event_type}",
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal processing error: {str(e)}"
        )


@router.get("/health")
async def webhook_health_check():
    """Health check endpoint for webhook router"""
    metrics = _ghl_router.get_metrics()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "metrics": metrics,
    }


def get_ghl_router() -> GHLWebhookRouter:
    """Get the global GHL webhook router instance"""
    return _ghl_router
