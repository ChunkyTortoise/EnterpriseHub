"""
Stripe Metered Billing Interface.

This module provides utilities for recording usage events to Stripe's
Metered Billing API, supporting both single events and high-throughput
meter event streams.

Stripe API Version: 2025-04-30.basil (or later with Meters API support)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import stripe


@dataclass
class MeterEvent:
    """
    Represents a single meter event for Stripe billing.

    Attributes:
        event_name: The name of the meter event (defined in Stripe Dashboard).
        customer_id: Stripe customer ID (cus_xxx).
        value: The numeric value for this event (e.g., 1 for single API call).
        timestamp: When the event occurred (defaults to now).
        idempotency_key: Unique key to prevent duplicate recording.
        metadata: Additional context for the event.
    """

    event_name: str
    customer_id: str
    value: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_stripe_payload(self) -> dict[str, Any]:
        """Convert to Stripe API payload format."""
        return {
            "event_name": self.event_name,
            "data": {
                "value": self.value,
            },
            "customer_id": self.customer_id,
            "timestamp": int(self.timestamp.timestamp()),
            "identifier": self.idempotency_key,
        }


class StripeUsageMeter:
    """
    Interface for recording metered usage to Stripe.

    Supports both single event recording and high-throughput
    meter event streams for >1K events/second scenarios.

    Attributes:
        api_key: Stripe secret key (sk_live_xxx or sk_test_xxx).
        meter_id: The Stripe meter ID for billing events.

    Example:
        meter = StripeUsageMeter(
            api_key="sk_test_xxx",
            meter_id="meter_xxx"
        )

        # Single event
        await meter.record_usage(
            event_name="api_calls",
            customer_id="cus_xxx",
            value=1
        )

        # High throughput
        session_token = await meter.create_session()
        await meter.record_usage_high_throughput(
            session_token=session_token,
            events=[...]
        )
    """

    def __init__(
        self,
        api_key: str,
        meter_id: str,
        api_version: str = "2025-04-30.basil",
    ):
        """
        Initialize the Stripe usage meter.

        Args:
            api_key: Stripe secret key.
            meter_id: Stripe meter ID for this product.
            api_version: Stripe API version (must support Meters API).
        """
        self.api_key = api_key
        self.meter_id = meter_id
        self.api_version = api_version

        # Configure Stripe client
        stripe.api_key = api_key
        stripe.api_version = api_version

    async def record_usage(
        self,
        event_name: str,
        customer_id: str,
        value: float = 1.0,
        idempotency_key: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Record a single meter event to Stripe.

        Use this for normal throughput scenarios (<100 events/second).
        For higher throughput, use record_usage_high_throughput().

        Args:
            event_name: The meter event name configured in Stripe Dashboard.
            customer_id: Stripe customer ID (cus_xxx).
            value: Numeric value for this event (default: 1.0).
            idempotency_key: Unique key to prevent duplicates (auto-generated if None).
            timestamp: When the event occurred (defaults to now).
            metadata: Additional context (not sent to Stripe, for logging).

        Returns:
            Stripe API response with event details.

        Raises:
            stripe.error.StripeError: If the API call fails.

        Example:
            response = await meter.record_usage(
                event_name="api_calls",
                customer_id="cus_abc123",
                value=1,
                idempotency_key="req_xyz789"
            )
        """
        event = MeterEvent(
            event_name=event_name,
            customer_id=customer_id,
            value=value,
            timestamp=timestamp or datetime.utcnow(),
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            metadata=metadata or {},
        )

        # Run in thread pool since stripe is synchronous
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: stripe.billing.MeterEvent.create(
                **event.to_stripe_payload(),
                idempotency_key=event.idempotency_key,
            ),
        )

        return {
            "event_id": response.id,
            "event_name": response.event_name,
            "customer_id": response.customer_id,
            "timestamp": response.timestamp,
            "status": "recorded",
        }

    async def record_usage_high_throughput(
        self,
        session_token: str,
        events: list[MeterEvent],
    ) -> dict[str, Any]:
        """
        Record multiple meter events using meter event streams.

        Use this for high-throughput scenarios (>1K events/second).
        This uses Stripe's meter event stream API for efficient batching.

        Args:
            session_token: Session token from create_session().
            events: List of MeterEvent objects to record.

        Returns:
            Summary of recorded events with counts and any errors.

        Raises:
            stripe.error.StripeError: If the API call fails.

        Example:
            session_token = await meter.create_session()
            events = [
                MeterEvent("api_calls", "cus_abc", 1),
                MeterEvent("api_calls", "cus_def", 1),
                MeterEvent("api_calls", "cus_ghi", 1),
            ]
            result = await meter.record_usage_high_throughput(session_token, events)
        """
        if not events:
            return {"recorded": 0, "errors": []}

        # Build event stream payload
        stream_events = [event.to_stripe_payload() for event in events]

        loop = asyncio.get_event_loop()

        try:
            # Create meter event stream
            response = await loop.run_in_executor(
                None,
                lambda: stripe.billing.MeterEventStream.create(
                    events=stream_events,
                    session_token=session_token,
                ),
            )

            return {
                "stream_id": response.id,
                "recorded": len(events),
                "session_token": session_token,
                "status": "recorded",
                "errors": [],
            }
        except stripe.error.StripeError as e:
            # Return partial success info if available
            return {
                "recorded": 0,
                "errors": [{"error": str(e), "events_count": len(events)}],
                "status": "failed",
            }

    async def create_session(self) -> str:
        """
        Create a new session token for meter event streams.

        Session tokens are required for high-throughput meter event
        streams to ensure proper ordering and deduplication.

        Returns:
            Session token string for use with record_usage_high_throughput().

        Example:
            session_token = await meter.create_session()
        """
        loop = asyncio.get_event_loop()

        # Create a session for meter event streaming
        response = await loop.run_in_executor(None, lambda: stripe.billing.MeterEventSession.create())

        return response.session_token

    async def get_meter(self) -> dict[str, Any]:
        """
        Retrieve meter configuration from Stripe.

        Returns:
            Meter configuration including name, status, and aggregation settings.
        """
        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(None, lambda: stripe.billing.Meter.retrieve(self.meter_id))

        return {
            "meter_id": response.id,
            "display_name": response.display_name,
            "event_name": response.event_name,
            "event_time_window": response.event_time_window,
            "status": response.status,
            "aggregation": response.aggregation,
        }

    async def list_meter_events(
        self,
        customer_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List meter events for auditing and debugging.

        Args:
            customer_id: Filter by Stripe customer ID.
            start_time: Filter events after this time.
            end_time: Filter events before this time.
            limit: Maximum number of events to return.

        Returns:
            List of meter event records.
        """
        loop = asyncio.get_event_loop()

        params = {
            "meter": self.meter_id,
            "limit": limit,
        }

        if customer_id:
            params["customer"] = customer_id
        if start_time:
            params["start_time"] = int(start_time.timestamp())
        if end_time:
            params["end_time"] = int(end_time.timestamp())

        response = await loop.run_in_executor(None, lambda: stripe.billing.MeterEvent.list(**params))

        return [
            {
                "event_id": event.id,
                "event_name": event.event_name,
                "customer_id": event.customer_id,
                "timestamp": datetime.fromtimestamp(event.timestamp),
                "value": event.data.get("value"),
            }
            for event in response.data
        ]
