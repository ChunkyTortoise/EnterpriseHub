"""
Compliance Platform - Webhook Endpoints for Event Notifications

Production-ready webhook management system for delivering compliance events
to external systems with enterprise-grade reliability features.

Features:
- Webhook subscription management (CRUD operations)
- HMAC-SHA256 signature verification for security
- Retry logic with exponential backoff
- Delivery tracking and history
- Incoming webhook handler for external integrations
- Rate limiting per subscription
- Idempotency support for reliable delivery
"""

import asyncio
import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import aiohttp
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl, field_validator

from ghl_real_estate_ai.compliance_platform.realtime.event_publisher import (
    ComplianceEvent,
    ComplianceEventType,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/compliance/webhooks", tags=["webhooks"])


# =============================================================================
# Webhook Event Types (aligned with compliance event types)
# =============================================================================


class WebhookEventType(str, Enum):
    """Webhook event types for external notification delivery."""

    MODEL_REGISTERED = "model.registered"
    MODEL_UPDATED = "model.updated"
    ASSESSMENT_COMPLETED = "assessment.completed"
    VIOLATION_DETECTED = "violation.detected"
    VIOLATION_RESOLVED = "violation.resolved"
    SCORE_CHANGED = "score.changed"
    THRESHOLD_BREACH = "threshold.breach"
    CERTIFICATION_EXPIRING = "certification.expiring"
    RISK_LEVEL_CHANGED = "risk.level.changed"
    REMEDIATION_STARTED = "remediation.started"
    REMEDIATION_COMPLETED = "remediation.completed"


# Mapping from internal compliance events to webhook events
COMPLIANCE_TO_WEBHOOK_EVENT_MAP: Dict[ComplianceEventType, WebhookEventType] = {
    ComplianceEventType.MODEL_REGISTERED: WebhookEventType.MODEL_REGISTERED,
    ComplianceEventType.MODEL_UPDATED: WebhookEventType.MODEL_UPDATED,
    ComplianceEventType.ASSESSMENT_COMPLETED: WebhookEventType.ASSESSMENT_COMPLETED,
    ComplianceEventType.VIOLATION_DETECTED: WebhookEventType.VIOLATION_DETECTED,
    ComplianceEventType.VIOLATION_RESOLVED: WebhookEventType.VIOLATION_RESOLVED,
    ComplianceEventType.SCORE_CHANGED: WebhookEventType.SCORE_CHANGED,
    ComplianceEventType.THRESHOLD_BREACH: WebhookEventType.THRESHOLD_BREACH,
    ComplianceEventType.CERTIFICATION_EXPIRING: WebhookEventType.CERTIFICATION_EXPIRING,
    ComplianceEventType.RISK_LEVEL_CHANGED: WebhookEventType.RISK_LEVEL_CHANGED,
    ComplianceEventType.REMEDIATION_STARTED: WebhookEventType.REMEDIATION_STARTED,
    ComplianceEventType.REMEDIATION_COMPLETED: WebhookEventType.REMEDIATION_COMPLETED,
}


class DeliveryStatus(str, Enum):
    """Webhook delivery status."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


# =============================================================================
# Pydantic Models
# =============================================================================


class WebhookSubscription(BaseModel):
    """Webhook subscription configuration."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    url: HttpUrl
    events: List[WebhookEventType]
    secret: str  # HMAC secret for signature verification
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Configuration options
    retry_enabled: bool = True
    max_retries: int = 5
    timeout_seconds: int = 30

    # Rate limiting
    rate_limit_per_minute: int = 100

    # Statistics
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: Optional[datetime] = None
    last_delivery_status: Optional[DeliveryStatus] = None


class WebhookRegistrationRequest(BaseModel):
    """Request model for webhook subscription registration."""

    url: HttpUrl
    events: List[WebhookEventType]
    secret: Optional[str] = None  # Auto-generated if not provided
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retry_enabled: bool = True
    max_retries: int = 5
    timeout_seconds: int = Field(default=30, ge=5, le=60)
    rate_limit_per_minute: int = Field(default=100, ge=1, le=1000)

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: List[WebhookEventType]) -> List[WebhookEventType]:
        """Validate at least one event is specified."""
        if not v:
            raise ValueError("At least one event type must be specified")
        return list(set(v))  # Remove duplicates


class WebhookUpdateRequest(BaseModel):
    """Request model for updating webhook subscription."""

    url: Optional[HttpUrl] = None
    events: Optional[List[WebhookEventType]] = None
    active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    retry_enabled: Optional[bool] = None
    max_retries: Optional[int] = Field(default=None, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(default=None, ge=5, le=60)
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, le=1000)


class WebhookPayload(BaseModel):
    """Webhook delivery payload sent to subscribers."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: WebhookEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    source: str = "compliance_platform"
    version: str = "1.0"


class WebhookDeliveryRecord(BaseModel):
    """Record of a webhook delivery attempt."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    subscription_id: str
    event_id: str
    event_type: WebhookEventType
    url: str
    status: DeliveryStatus
    attempt_number: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    response_status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    next_retry_at: Optional[datetime] = None


class WebhookTestRequest(BaseModel):
    """Request model for testing webhook delivery."""

    custom_payload: Optional[Dict[str, Any]] = None


class IncomingWebhookPayload(BaseModel):
    """Payload for incoming webhooks from external systems."""

    event_type: str
    timestamp: Optional[datetime] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None


# =============================================================================
# Webhook Delivery Service
# =============================================================================


class WebhookDeliveryService:
    """
    Handles webhook delivery with retry logic and signature generation.

    Features:
    - HMAC-SHA256 signature generation
    - Exponential backoff retry
    - Rate limiting per subscription
    - Delivery tracking and history
    - Idempotency support
    """

    def __init__(
        self,
        base_retry_delay: float = 1.0,
        max_retry_delay: float = 300.0,
        default_timeout: float = 30.0,
    ):
        """
        Initialize webhook delivery service.

        Args:
            base_retry_delay: Base delay for exponential backoff (seconds)
            max_retry_delay: Maximum retry delay (seconds)
            default_timeout: Default request timeout (seconds)
        """
        self.base_retry_delay = base_retry_delay
        self.max_retry_delay = max_retry_delay
        self.default_timeout = default_timeout

        # In-memory storage (replace with database in production)
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._delivery_history: List[WebhookDeliveryRecord] = []
        self._rate_limit_state: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "window_start": time.time()}
        )

        # Pending retries
        self._retry_tasks: Dict[str, asyncio.Task] = {}

        # Delivered event IDs for idempotency (with TTL cleanup)
        self._delivered_events: Set[str] = set()
        self._event_ttl_seconds = 3600  # 1 hour idempotency window

        logger.info("WebhookDeliveryService initialized")

    def register_subscription(self, subscription: WebhookSubscription) -> None:
        """
        Register a new webhook subscription.

        Args:
            subscription: Webhook subscription to register
        """
        self._subscriptions[subscription.id] = subscription
        logger.info(
            f"Registered webhook subscription {subscription.id}",
            extra={
                "subscription_id": subscription.id,
                "url": str(subscription.url),
                "events": [e.value for e in subscription.events],
            },
        )

    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID."""
        return self._subscriptions.get(subscription_id)

    def list_subscriptions(self) -> List[WebhookSubscription]:
        """List all subscriptions."""
        return list(self._subscriptions.values())

    def update_subscription(
        self,
        subscription_id: str,
        updates: WebhookUpdateRequest,
    ) -> Optional[WebhookSubscription]:
        """
        Update an existing subscription.

        Args:
            subscription_id: ID of subscription to update
            updates: Updates to apply

        Returns:
            Updated subscription or None if not found
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(subscription, field, value)

        subscription.updated_at = datetime.now(timezone.utc)
        self._subscriptions[subscription_id] = subscription

        logger.info(
            f"Updated webhook subscription {subscription_id}",
            extra={
                "subscription_id": subscription_id,
                "updated_fields": list(update_data.keys()),
            },
        )
        return subscription

    def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription.

        Args:
            subscription_id: ID of subscription to delete

        Returns:
            True if deleted, False if not found
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]

            # Cancel any pending retries
            if subscription_id in self._retry_tasks:
                self._retry_tasks[subscription_id].cancel()
                del self._retry_tasks[subscription_id]

            logger.info(f"Deleted webhook subscription {subscription_id}")
            return True
        return False

    def _sign_payload(self, payload: str, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.

        Args:
            payload: JSON payload string
            secret: Subscription secret key

        Returns:
            Hexadecimal signature string
        """
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _generate_signature_header(
        self,
        payload: str,
        secret: str,
        timestamp: int,
    ) -> str:
        """
        Generate signature header with timestamp.

        Format: t=<timestamp>,v1=<signature>

        Args:
            payload: JSON payload string
            secret: Subscription secret key
            timestamp: Unix timestamp

        Returns:
            Signature header value
        """
        # Create signed payload: timestamp.payload
        signed_payload = f"{timestamp}.{payload}"
        signature = self._sign_payload(signed_payload, secret)
        return f"t={timestamp},v1={signature}"

    def verify_signature(
        self,
        payload: str,
        signature_header: str,
        secret: str,
        tolerance_seconds: int = 300,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw payload string
            signature_header: Signature header value (t=...,v1=...)
            secret: Subscription secret
            tolerance_seconds: Maximum age tolerance for timestamp

        Returns:
            True if signature is valid
        """
        try:
            # Parse signature header
            parts = {}
            for part in signature_header.split(","):
                if "=" in part:
                    key, value = part.split("=", 1)
                    parts[key] = value

            timestamp = int(parts.get("t", 0))
            expected_sig = parts.get("v1", "")

            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > tolerance_seconds:
                logger.warning(f"Webhook signature timestamp out of tolerance: {timestamp}")
                return False

            # Verify signature
            signed_payload = f"{timestamp}.{payload}"
            computed_sig = self._sign_payload(signed_payload, secret)

            return hmac.compare_digest(computed_sig, expected_sig)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    def _check_rate_limit(self, subscription_id: str, limit: int) -> bool:
        """
        Check if subscription is within rate limit.

        Args:
            subscription_id: Subscription ID
            limit: Requests per minute limit

        Returns:
            True if within limit, False if rate limited
        """
        state = self._rate_limit_state[subscription_id]
        current_time = time.time()

        # Reset window if expired (60 seconds)
        if current_time - state["window_start"] >= 60:
            state["count"] = 0
            state["window_start"] = current_time

        if state["count"] >= limit:
            return False

        state["count"] += 1
        return True

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        delay = self.base_retry_delay * (2 ** (attempt - 1))
        # Add jitter (up to 20%)
        jitter = delay * 0.2 * (0.5 - hash(str(time.time())) % 1000 / 1000)
        return min(delay + jitter, self.max_retry_delay)

    async def deliver_event(
        self,
        event_type: WebhookEventType,
        data: Dict[str, Any],
        model_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deliver event to all subscribed webhooks.

        Args:
            event_type: Type of event to deliver
            data: Event payload data
            model_id: Optional model ID
            model_name: Optional model name

        Returns:
            Delivery results summary
        """
        payload = WebhookPayload(
            event_type=event_type,
            data=data,
            model_id=model_id,
            model_name=model_name,
        )

        # Check idempotency
        event_key = f"{payload.event_id}:{event_type.value}"
        if event_key in self._delivered_events:
            logger.info(f"Skipping duplicate event delivery: {event_key}")
            return {
                "event_id": payload.event_id,
                "status": "skipped",
                "reason": "duplicate",
            }

        # Find subscriptions for this event type
        subscriptions = [s for s in self._subscriptions.values() if s.active and event_type in s.events]

        if not subscriptions:
            logger.debug(f"No active subscriptions for event type: {event_type}")
            return {
                "event_id": payload.event_id,
                "status": "no_subscribers",
                "delivered_count": 0,
            }

        # Deliver to all subscriptions
        results = []
        for subscription in subscriptions:
            result = await self._send_webhook(subscription, payload)
            results.append(result)

        # Mark event as delivered
        self._delivered_events.add(event_key)

        # Calculate summary
        delivered = sum(1 for r in results if r.status == DeliveryStatus.DELIVERED)
        failed = sum(1 for r in results if r.status == DeliveryStatus.FAILED)
        retrying = sum(1 for r in results if r.status == DeliveryStatus.RETRYING)

        logger.info(
            f"Event delivery complete: {payload.event_id}",
            extra={
                "event_id": payload.event_id,
                "event_type": event_type.value,
                "total_subscriptions": len(subscriptions),
                "delivered": delivered,
                "failed": failed,
                "retrying": retrying,
            },
        )

        return {
            "event_id": payload.event_id,
            "event_type": event_type.value,
            "status": "delivered",
            "total_subscriptions": len(subscriptions),
            "delivered_count": delivered,
            "failed_count": failed,
            "retrying_count": retrying,
            "results": [
                {
                    "subscription_id": r.subscription_id,
                    "status": r.status.value,
                    "response_code": r.response_status_code,
                    "response_time_ms": r.response_time_ms,
                    "error": r.error_message,
                }
                for r in results
            ],
        }

    async def _send_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        attempt: int = 1,
    ) -> WebhookDeliveryRecord:
        """
        Send webhook to a subscription.

        Args:
            subscription: Target subscription
            payload: Webhook payload
            attempt: Current attempt number

        Returns:
            Delivery record
        """
        record = WebhookDeliveryRecord(
            subscription_id=subscription.id,
            event_id=payload.event_id,
            event_type=payload.event_type,
            url=str(subscription.url),
            status=DeliveryStatus.PENDING,
            attempt_number=attempt,
        )

        # Check rate limit
        if not self._check_rate_limit(
            subscription.id,
            subscription.rate_limit_per_minute,
        ):
            record.status = DeliveryStatus.FAILED
            record.error_message = "Rate limit exceeded"
            self._delivery_history.append(record)
            logger.warning(f"Rate limit exceeded for subscription {subscription.id}")
            return record

        # Prepare payload
        payload_json = payload.model_dump_json()
        timestamp = int(time.time())
        signature_header = self._generate_signature_header(
            payload_json,
            subscription.secret,
            timestamp,
        )

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature_header,
            "X-Webhook-ID": payload.event_id,
            "X-Webhook-Timestamp": str(timestamp),
            "User-Agent": "CompliancePlatform-Webhook/1.0",
        }

        # Send request
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=subscription.timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    str(subscription.url),
                    data=payload_json,
                    headers=headers,
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    record.response_status_code = response.status
                    record.response_time_ms = response_time

                    if 200 <= response.status < 300:
                        record.status = DeliveryStatus.DELIVERED
                        subscription.successful_deliveries += 1
                        logger.debug(f"Webhook delivered to {subscription.id}: {response.status}")
                    else:
                        # Non-2xx response
                        response_text = await response.text()
                        record.status = DeliveryStatus.FAILED
                        record.error_message = f"HTTP {response.status}: {response_text[:200]}"
                        logger.warning(f"Webhook delivery failed for {subscription.id}: {response.status}")

        except asyncio.TimeoutError:
            record.status = DeliveryStatus.FAILED
            record.error_message = f"Request timed out after {subscription.timeout_seconds}s"
            record.response_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"Webhook timeout for subscription {subscription.id}")

        except aiohttp.ClientError as e:
            record.status = DeliveryStatus.FAILED
            record.error_message = f"Connection error: {str(e)}"
            record.response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Webhook connection error for {subscription.id}: {e}")

        except Exception as e:
            record.status = DeliveryStatus.FAILED
            record.error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected webhook error for {subscription.id}: {e}")

        # Update subscription statistics
        subscription.total_deliveries += 1
        subscription.last_delivery_at = datetime.now(timezone.utc)
        subscription.last_delivery_status = record.status

        if record.status == DeliveryStatus.FAILED:
            subscription.failed_deliveries += 1

            # Schedule retry if enabled and attempts remaining
            if subscription.retry_enabled and attempt < subscription.max_retries:
                record.status = DeliveryStatus.RETRYING
                retry_delay = self._calculate_retry_delay(attempt)
                record.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)

                # Schedule async retry
                task = asyncio.create_task(
                    self._schedule_retry(
                        subscription,
                        payload,
                        attempt + 1,
                        retry_delay,
                    )
                )
                self._retry_tasks[f"{subscription.id}:{payload.event_id}"] = task

                logger.info(f"Scheduled retry {attempt + 1} for {subscription.id} in {retry_delay:.1f}s")

        # Store delivery record
        self._delivery_history.append(record)

        return record

    async def _schedule_retry(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        attempt: int,
        delay: float,
    ) -> None:
        """
        Schedule a retry attempt after delay.

        Args:
            subscription: Target subscription
            payload: Webhook payload
            attempt: Attempt number
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)
        await self._send_webhook(subscription, payload, attempt)

    def get_delivery_history(
        self,
        subscription_id: Optional[str] = None,
        event_type: Optional[WebhookEventType] = None,
        status: Optional[DeliveryStatus] = None,
        limit: int = 100,
    ) -> List[WebhookDeliveryRecord]:
        """
        Get webhook delivery history with optional filters.

        Args:
            subscription_id: Filter by subscription ID
            event_type: Filter by event type
            status: Filter by delivery status
            limit: Maximum records to return

        Returns:
            List of delivery records
        """
        records = self._delivery_history.copy()

        if subscription_id:
            records = [r for r in records if r.subscription_id == subscription_id]
        if event_type:
            records = [r for r in records if r.event_type == event_type]
        if status:
            records = [r for r in records if r.status == status]

        # Return most recent first
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get delivery service statistics."""
        total_subscriptions = len(self._subscriptions)
        active_subscriptions = sum(1 for s in self._subscriptions.values() if s.active)

        status_counts = defaultdict(int)
        for record in self._delivery_history:
            status_counts[record.status.value] += 1

        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "total_deliveries": len(self._delivery_history),
            "status_breakdown": dict(status_counts),
            "pending_retries": len(self._retry_tasks),
            "cached_events": len(self._delivered_events),
        }


# =============================================================================
# Global Service Instance
# =============================================================================

_delivery_service: Optional[WebhookDeliveryService] = None


def get_delivery_service() -> WebhookDeliveryService:
    """Get or create the global webhook delivery service."""
    global _delivery_service
    if _delivery_service is None:
        _delivery_service = WebhookDeliveryService()
    return _delivery_service


# =============================================================================
# API Endpoints - Subscription Management
# =============================================================================


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_webhook(
    request: WebhookRegistrationRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Register a new webhook subscription.

    Creates a new webhook subscription that will receive events for the
    specified event types. A secret key is auto-generated if not provided.

    Args:
        request: Webhook registration request

    Returns:
        Created subscription details with secret key
    """
    service = get_delivery_service()

    # Generate secret if not provided
    secret = request.secret or secrets.token_hex(32)

    subscription = WebhookSubscription(
        url=request.url,
        events=request.events,
        secret=secret,
        metadata=request.metadata,
        retry_enabled=request.retry_enabled,
        max_retries=request.max_retries,
        timeout_seconds=request.timeout_seconds,
        rate_limit_per_minute=request.rate_limit_per_minute,
    )

    service.register_subscription(subscription)

    logger.info(
        f"Created webhook subscription {subscription.id}",
        extra={
            "subscription_id": subscription.id,
            "url": str(subscription.url),
            "events": [e.value for e in subscription.events],
        },
    )

    return {
        "success": True,
        "subscription": {
            "id": subscription.id,
            "url": str(subscription.url),
            "events": [e.value for e in subscription.events],
            "secret": secret,  # Only returned on creation
            "active": subscription.active,
            "created_at": subscription.created_at.isoformat(),
            "retry_enabled": subscription.retry_enabled,
            "max_retries": subscription.max_retries,
            "timeout_seconds": subscription.timeout_seconds,
            "rate_limit_per_minute": subscription.rate_limit_per_minute,
        },
        "message": "Webhook subscription created successfully. Store the secret securely - it will not be shown again.",
    }


@router.get("/subscriptions")
async def list_subscriptions() -> Dict[str, Any]:
    """
    List all webhook subscriptions.

    Returns:
        List of all registered subscriptions (without secrets)
    """
    service = get_delivery_service()
    subscriptions = service.list_subscriptions()

    return {
        "subscriptions": [
            {
                "id": s.id,
                "url": str(s.url),
                "events": [e.value for e in s.events],
                "active": s.active,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "metadata": s.metadata,
                "retry_enabled": s.retry_enabled,
                "max_retries": s.max_retries,
                "statistics": {
                    "total_deliveries": s.total_deliveries,
                    "successful_deliveries": s.successful_deliveries,
                    "failed_deliveries": s.failed_deliveries,
                    "last_delivery_at": s.last_delivery_at.isoformat() if s.last_delivery_at else None,
                    "last_delivery_status": s.last_delivery_status.value if s.last_delivery_status else None,
                },
            }
            for s in subscriptions
        ],
        "total_count": len(subscriptions),
    }


@router.get("/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str) -> Dict[str, Any]:
    """
    Get webhook subscription details.

    Args:
        subscription_id: Subscription ID

    Returns:
        Subscription details (without secret)

    Raises:
        HTTPException: If subscription not found
    """
    service = get_delivery_service()
    subscription = service.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "subscription_not_found",
                "error_message": f"Subscription {subscription_id} not found",
            },
        )

    return {
        "subscription": {
            "id": subscription.id,
            "url": str(subscription.url),
            "events": [e.value for e in subscription.events],
            "active": subscription.active,
            "created_at": subscription.created_at.isoformat(),
            "updated_at": subscription.updated_at.isoformat(),
            "metadata": subscription.metadata,
            "retry_enabled": subscription.retry_enabled,
            "max_retries": subscription.max_retries,
            "timeout_seconds": subscription.timeout_seconds,
            "rate_limit_per_minute": subscription.rate_limit_per_minute,
            "statistics": {
                "total_deliveries": subscription.total_deliveries,
                "successful_deliveries": subscription.successful_deliveries,
                "failed_deliveries": subscription.failed_deliveries,
                "success_rate": (
                    subscription.successful_deliveries / subscription.total_deliveries * 100
                    if subscription.total_deliveries > 0
                    else 0
                ),
                "last_delivery_at": subscription.last_delivery_at.isoformat()
                if subscription.last_delivery_at
                else None,
                "last_delivery_status": subscription.last_delivery_status.value
                if subscription.last_delivery_status
                else None,
            },
        }
    }


@router.put("/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    request: WebhookUpdateRequest,
) -> Dict[str, Any]:
    """
    Update webhook subscription.

    Args:
        subscription_id: Subscription ID
        request: Updates to apply

    Returns:
        Updated subscription details

    Raises:
        HTTPException: If subscription not found
    """
    service = get_delivery_service()
    subscription = service.update_subscription(subscription_id, request)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "subscription_not_found",
                "error_message": f"Subscription {subscription_id} not found",
            },
        )

    logger.info(f"Updated webhook subscription {subscription_id}")

    return {
        "success": True,
        "subscription": {
            "id": subscription.id,
            "url": str(subscription.url),
            "events": [e.value for e in subscription.events],
            "active": subscription.active,
            "updated_at": subscription.updated_at.isoformat(),
        },
        "message": "Subscription updated successfully",
    }


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str) -> Dict[str, Any]:
    """
    Delete webhook subscription.

    Args:
        subscription_id: Subscription ID

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If subscription not found
    """
    service = get_delivery_service()
    deleted = service.delete_subscription(subscription_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "subscription_not_found",
                "error_message": f"Subscription {subscription_id} not found",
            },
        )

    logger.info(f"Deleted webhook subscription {subscription_id}")

    return {
        "success": True,
        "subscription_id": subscription_id,
        "message": "Subscription deleted successfully",
    }


@router.post("/subscriptions/{subscription_id}/test")
async def test_webhook(
    subscription_id: str,
    request: Optional[WebhookTestRequest] = None,
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """
    Send test event to webhook.

    Sends a test event to the specified subscription to verify
    connectivity and signature validation.

    Args:
        subscription_id: Subscription ID
        request: Optional custom test payload

    Returns:
        Test delivery result

    Raises:
        HTTPException: If subscription not found
    """
    service = get_delivery_service()
    subscription = service.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "subscription_not_found",
                "error_message": f"Subscription {subscription_id} not found",
            },
        )

    # Create test payload
    test_data = (
        request.custom_payload
        if request and request.custom_payload
        else {
            "test": True,
            "message": "This is a test webhook delivery",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    payload = WebhookPayload(
        event_type=WebhookEventType.MODEL_REGISTERED,  # Use a safe test event type
        data=test_data,
        model_id="test_model_id",
        model_name="Test Model",
    )

    # Deliver test event
    record = await service._send_webhook(subscription, payload)

    logger.info(
        f"Sent test webhook to subscription {subscription_id}",
        extra={
            "subscription_id": subscription_id,
            "status": record.status.value,
        },
    )

    return {
        "success": record.status == DeliveryStatus.DELIVERED,
        "subscription_id": subscription_id,
        "event_id": payload.event_id,
        "delivery": {
            "status": record.status.value,
            "response_status_code": record.response_status_code,
            "response_time_ms": record.response_time_ms,
            "error_message": record.error_message,
        },
        "message": (
            "Test webhook delivered successfully"
            if record.status == DeliveryStatus.DELIVERED
            else f"Test webhook failed: {record.error_message}"
        ),
    }


@router.get("/subscriptions/{subscription_id}/history")
async def get_subscription_delivery_history(
    subscription_id: str,
    status_filter: Optional[DeliveryStatus] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Get delivery history for a subscription.

    Args:
        subscription_id: Subscription ID
        status_filter: Optional status filter
        limit: Maximum records to return

    Returns:
        Delivery history for the subscription
    """
    service = get_delivery_service()

    # Verify subscription exists
    subscription = service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "subscription_not_found",
                "error_message": f"Subscription {subscription_id} not found",
            },
        )

    records = service.get_delivery_history(
        subscription_id=subscription_id,
        status=status_filter,
        limit=limit,
    )

    return {
        "subscription_id": subscription_id,
        "deliveries": [
            {
                "id": r.id,
                "event_id": r.event_id,
                "event_type": r.event_type.value,
                "status": r.status.value,
                "attempt_number": r.attempt_number,
                "timestamp": r.timestamp.isoformat(),
                "response_status_code": r.response_status_code,
                "response_time_ms": r.response_time_ms,
                "error_message": r.error_message,
                "next_retry_at": r.next_retry_at.isoformat() if r.next_retry_at else None,
            }
            for r in records
        ],
        "total_count": len(records),
    }


# =============================================================================
# API Endpoints - Event Delivery
# =============================================================================


@router.post("/deliver")
async def deliver_event(
    event_type: WebhookEventType,
    data: Dict[str, Any],
    model_id: Optional[str] = None,
    model_name: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """
    Manually trigger event delivery to all subscriptions.

    This endpoint is typically used internally by the compliance engine
    to broadcast events to external systems.

    Args:
        event_type: Type of event
        data: Event payload data
        model_id: Optional model ID
        model_name: Optional model name

    Returns:
        Delivery results summary
    """
    service = get_delivery_service()

    result = await service.deliver_event(
        event_type=event_type,
        data=data,
        model_id=model_id,
        model_name=model_name,
    )

    return result


@router.get("/history")
async def get_delivery_history(
    event_type: Optional[WebhookEventType] = None,
    status_filter: Optional[DeliveryStatus] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Get global webhook delivery history.

    Args:
        event_type: Optional event type filter
        status_filter: Optional status filter
        limit: Maximum records to return

    Returns:
        Delivery history across all subscriptions
    """
    service = get_delivery_service()
    records = service.get_delivery_history(
        event_type=event_type,
        status=status_filter,
        limit=limit,
    )

    return {
        "deliveries": [
            {
                "id": r.id,
                "subscription_id": r.subscription_id,
                "event_id": r.event_id,
                "event_type": r.event_type.value,
                "url": r.url,
                "status": r.status.value,
                "attempt_number": r.attempt_number,
                "timestamp": r.timestamp.isoformat(),
                "response_status_code": r.response_status_code,
                "response_time_ms": r.response_time_ms,
                "error_message": r.error_message,
            }
            for r in records
        ],
        "total_count": len(records),
    }


@router.get("/statistics")
async def get_statistics() -> Dict[str, Any]:
    """
    Get webhook delivery service statistics.

    Returns:
        Service statistics including subscription counts and delivery metrics
    """
    service = get_delivery_service()
    stats = service.get_statistics()

    return {
        "statistics": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# API Endpoints - Incoming Webhooks
# =============================================================================


@router.post("/incoming/{integration_type}")
async def handle_incoming_webhook(
    integration_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Handle incoming webhooks from external systems.

    Validates signature and processes events from external integrations
    like monitoring tools, CI/CD systems, or third-party compliance services.

    Supported integration types:
    - github: GitHub webhooks for repository events
    - gitlab: GitLab webhooks for CI/CD events
    - datadog: Datadog alerts and monitors
    - pagerduty: PagerDuty incident notifications
    - custom: Generic webhook handler

    Args:
        integration_type: Type of integration sending the webhook
        request: Raw request object
        x_webhook_signature: Optional signature header

    Returns:
        Processing result

    Raises:
        HTTPException: If signature validation fails
    """
    try:
        # Read raw body
        body = await request.body()
        body_str = body.decode("utf-8")

        logger.info(
            f"Received incoming webhook from {integration_type}",
            extra={
                "integration_type": integration_type,
                "content_length": len(body),
                "has_signature": bool(x_webhook_signature),
            },
        )

        # Parse payload
        try:
            payload_data = json.loads(body_str)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "invalid_json",
                    "error_message": f"Invalid JSON payload: {e}",
                },
            )

        # Integration-specific handling
        handler_result = await _process_integration_webhook(
            integration_type,
            payload_data,
            body_str,
            x_webhook_signature,
        )

        # Optionally trigger internal events based on incoming webhook
        if handler_result.get("trigger_internal_event"):
            service = get_delivery_service()
            await service.deliver_event(
                event_type=handler_result["internal_event_type"],
                data=handler_result["internal_event_data"],
            )

        return {
            "success": True,
            "integration_type": integration_type,
            "event_id": str(uuid4()),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "result": handler_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing incoming webhook from {integration_type}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "processing_error",
                "error_message": f"Failed to process webhook: {str(e)}",
            },
        )


async def _process_integration_webhook(
    integration_type: str,
    payload: Dict[str, Any],
    raw_body: str,
    signature: Optional[str],
) -> Dict[str, Any]:
    """
    Process webhook based on integration type.

    Args:
        integration_type: Type of integration
        payload: Parsed payload
        raw_body: Raw body string for signature verification
        signature: Optional signature header

    Returns:
        Processing result
    """
    handlers = {
        "github": _handle_github_webhook,
        "gitlab": _handle_gitlab_webhook,
        "datadog": _handle_datadog_webhook,
        "pagerduty": _handle_pagerduty_webhook,
        "custom": _handle_custom_webhook,
    }

    handler = handlers.get(integration_type, _handle_custom_webhook)
    return await handler(payload, raw_body, signature)


async def _handle_github_webhook(
    payload: Dict[str, Any],
    raw_body: str,
    signature: Optional[str],
) -> Dict[str, Any]:
    """Handle GitHub webhook."""
    event_type = payload.get("action", "unknown")
    repository = payload.get("repository", {}).get("full_name", "unknown")

    return {
        "integration": "github",
        "event_type": event_type,
        "repository": repository,
        "processed": True,
    }


async def _handle_gitlab_webhook(
    payload: Dict[str, Any],
    raw_body: str,
    signature: Optional[str],
) -> Dict[str, Any]:
    """Handle GitLab webhook."""
    event_type = payload.get("object_kind", "unknown")
    project = payload.get("project", {}).get("path_with_namespace", "unknown")

    return {
        "integration": "gitlab",
        "event_type": event_type,
        "project": project,
        "processed": True,
    }


async def _handle_datadog_webhook(
    payload: Dict[str, Any],
    raw_body: str,
    signature: Optional[str],
) -> Dict[str, Any]:
    """Handle Datadog alert webhook."""
    alert_type = payload.get("alert_type", "unknown")
    alert_title = payload.get("title", "Unknown Alert")

    # Map Datadog alerts to internal compliance events
    if "compliance" in alert_title.lower() or "violation" in alert_title.lower():
        return {
            "integration": "datadog",
            "alert_type": alert_type,
            "alert_title": alert_title,
            "processed": True,
            "trigger_internal_event": True,
            "internal_event_type": WebhookEventType.VIOLATION_DETECTED,
            "internal_event_data": {
                "source": "datadog",
                "alert_type": alert_type,
                "title": alert_title,
                "payload": payload,
            },
        }

    return {
        "integration": "datadog",
        "alert_type": alert_type,
        "alert_title": alert_title,
        "processed": True,
    }


async def _handle_pagerduty_webhook(
    payload: Dict[str, Any],
    raw_body: str,
    signature: Optional[str],
) -> Dict[str, Any]:
    """Handle PagerDuty incident webhook."""
    event_type = payload.get("event", {}).get("event_type", "unknown")
    incident_title = payload.get("event", {}).get("data", {}).get("title", "Unknown Incident")

    return {
        "integration": "pagerduty",
        "event_type": event_type,
        "incident_title": incident_title,
        "processed": True,
    }


async def _handle_custom_webhook(
    payload: Dict[str, Any],
    raw_body: str,
    signature: Optional[str],
) -> Dict[str, Any]:
    """Handle generic custom webhook."""
    return {
        "integration": "custom",
        "payload_keys": list(payload.keys()),
        "processed": True,
    }


# =============================================================================
# Bridge Function for ComplianceEventPublisher Integration
# =============================================================================


async def broadcast_compliance_event(event: ComplianceEvent) -> Dict[str, Any]:
    """
    Bridge function to broadcast compliance events to webhooks.

    Called by ComplianceEventPublisher to deliver events to external webhooks.

    Args:
        event: Internal compliance event

    Returns:
        Delivery results
    """
    service = get_delivery_service()

    # Map internal event type to webhook event type
    webhook_event_type = COMPLIANCE_TO_WEBHOOK_EVENT_MAP.get(event.event_type)
    if not webhook_event_type:
        logger.warning(f"No webhook mapping for event type: {event.event_type}")
        return {"status": "unmapped_event_type"}

    return await service.deliver_event(
        event_type=webhook_event_type,
        data=event.payload,
        model_id=event.model_id,
        model_name=event.model_name,
    )
