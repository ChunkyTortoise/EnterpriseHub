"""Revenue-critical v2 API routes with strict contracts and source attribution."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from ghl_real_estate_ai.api.schemas.revenue_v2 import (
    ResponseSource,
    RevenueError,
    RevenueSSEEvent,
    RevenueV2Envelope,
    new_correlation_id,
    utc_now,
)
from ghl_real_estate_ai.services.database_service import get_database

router = APIRouter(prefix="/api/v2", tags=["revenue-v2"])


def _age_seconds(ts: datetime | None) -> int:
    if ts is None:
        return 0
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(int((now - ts).total_seconds()), 0)


def _set_headers(response: Response, source: ResponseSource, freshness: int) -> None:
    response.headers["X-Response-Source"] = source.value
    response.headers["X-Data-Freshness"] = str(freshness)


def _error_envelope(
    *,
    code: str,
    message: str,
    recoverable: bool,
    suggested_action: str,
    correlation_id: str,
    source: ResponseSource = ResponseSource.DATABASE,
) -> RevenueV2Envelope:
    return RevenueV2Envelope(
        source=source,
        data_freshness_seconds=0,
        generated_at=utc_now(),
        correlation_id=correlation_id,
        data={},
        error=RevenueError(
            error_code=code,
            error_message=message,
            recoverable=recoverable,
            suggested_action=suggested_action,
            correlation_id=correlation_id,
        ),
    )


@router.get("/billing/subscriptions/{location_id}", response_model=RevenueV2Envelope)
async def get_billing_subscription_v2(location_id: str, response: Response) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, location_id, tier, status, current_period_end, updated_at
                FROM subscriptions
                WHERE location_id = $1
                ORDER BY updated_at DESC NULLS LAST
                LIMIT 1
                """,
                location_id,
            )

        if not row:
            envelope = _error_envelope(
                code="subscription_not_found",
                message=f"No subscription found for location_id={location_id}",
                recoverable=True,
                suggested_action="Create a subscription or verify location_id",
                correlation_id=correlation_id,
            )
            _set_headers(response, envelope.source, envelope.data_freshness_seconds)
            return envelope

        record = dict(row)
        freshness = _age_seconds(record.get("updated_at"))
        envelope = RevenueV2Envelope(
            source=ResponseSource.DATABASE,
            data_freshness_seconds=freshness,
            generated_at=utc_now(),
            correlation_id=correlation_id,
            data={
                "subscription_id": record.get("id"),
                "location_id": record.get("location_id"),
                "tier": record.get("tier"),
                "status": record.get("status"),
                "current_period_end": str(record.get("current_period_end")),
            },
        )
        _set_headers(response, envelope.source, freshness)
        return envelope
    except Exception as exc:
        envelope = _error_envelope(
            code="billing_query_failed",
            message=str(exc),
            recoverable=True,
            suggested_action="Check database connectivity and subscriptions table",
            correlation_id=correlation_id,
        )
        _set_headers(response, envelope.source, envelope.data_freshness_seconds)
        return envelope


@router.get("/prediction/deal-outcome/{deal_id}", response_model=RevenueV2Envelope)
async def get_prediction_deal_outcome_v2(deal_id: str, response: Response) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT deal_id, current_stage, offer_amount, property_value, commission_rate, updated_at
                FROM deals
                WHERE deal_id = $1
                LIMIT 1
                """,
                deal_id,
            )

        if not row:
            envelope = _error_envelope(
                code="deal_not_found",
                message=f"No deal found for deal_id={deal_id}",
                recoverable=True,
                suggested_action="Verify deal_id or create deal data before scoring",
                correlation_id=correlation_id,
            )
            _set_headers(response, envelope.source, envelope.data_freshness_seconds)
            return envelope

        record = dict(row)
        offer = float(record.get("offer_amount") or 0.0)
        value = float(record.get("property_value") or 0.0)
        ratio = (offer / value) if value > 0 else 0.0
        closing_probability = min(max(round(ratio * 100, 2), 5.0), 95.0)
        freshness = _age_seconds(record.get("updated_at"))

        envelope = RevenueV2Envelope(
            source=ResponseSource.DATABASE,
            data_freshness_seconds=freshness,
            generated_at=utc_now(),
            correlation_id=correlation_id,
            data={
                "deal_id": record.get("deal_id"),
                "current_stage": record.get("current_stage"),
                "closing_probability": closing_probability,
                "scoring_inputs": {
                    "offer_amount": offer,
                    "property_value": value,
                    "commission_rate": float(record.get("commission_rate") or 0.0),
                },
            },
        )
        _set_headers(response, envelope.source, freshness)
        return envelope
    except Exception as exc:
        envelope = _error_envelope(
            code="prediction_query_failed",
            message=str(exc),
            recoverable=True,
            suggested_action="Check deals table availability and data shape",
            correlation_id=correlation_id,
        )
        _set_headers(response, envelope.source, envelope.data_freshness_seconds)
        return envelope


@router.get("/customer-journeys/{lead_id}", response_model=RevenueV2Envelope)
async def get_customer_journey_v2(lead_id: str, response: Response) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT lead_id, current_stage, updated_at
                FROM lead_journey_state
                WHERE lead_id = $1
                LIMIT 1
                """,
                lead_id,
            )
        if not row:
            envelope = _error_envelope(
                code="journey_not_found",
                message=f"No journey found for lead_id={lead_id}",
                recoverable=True,
                suggested_action="Initialize lead journey state before requesting analytics",
                correlation_id=correlation_id,
            )
            _set_headers(response, envelope.source, envelope.data_freshness_seconds)
            return envelope

        record = dict(row)
        freshness = _age_seconds(record.get("updated_at"))
        envelope = RevenueV2Envelope(
            source=ResponseSource.DATABASE,
            data_freshness_seconds=freshness,
            generated_at=utc_now(),
            correlation_id=correlation_id,
            data={
                "lead_id": record.get("lead_id"),
                "current_stage": record.get("current_stage"),
            },
        )
        _set_headers(response, envelope.source, freshness)
        return envelope
    except Exception as exc:
        envelope = _error_envelope(
            code="journey_query_failed",
            message=str(exc),
            recoverable=True,
            suggested_action="Check lead_journey_state table and lead lifecycle initialization",
            correlation_id=correlation_id,
        )
        _set_headers(response, envelope.source, envelope.data_freshness_seconds)
        return envelope


@router.get("/property-intelligence/{property_id}", response_model=RevenueV2Envelope)
async def get_property_intelligence_v2(property_id: str, response: Response) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT property_id, market_score, roi_projection, updated_at
                FROM property_analyses
                WHERE property_id = $1
                ORDER BY updated_at DESC NULLS LAST
                LIMIT 1
                """,
                property_id,
            )

        if not row:
            envelope = _error_envelope(
                code="property_analysis_not_found",
                message=f"No property analysis found for property_id={property_id}",
                recoverable=True,
                suggested_action="Run property analysis pipeline before requesting insight",
                correlation_id=correlation_id,
            )
            _set_headers(response, envelope.source, envelope.data_freshness_seconds)
            return envelope

        record = dict(row)
        freshness = _age_seconds(record.get("updated_at"))
        envelope = RevenueV2Envelope(
            source=ResponseSource.DATABASE,
            data_freshness_seconds=freshness,
            generated_at=utc_now(),
            correlation_id=correlation_id,
            data={
                "property_id": record.get("property_id"),
                "market_score": float(record.get("market_score") or 0.0),
                "roi_projection": float(record.get("roi_projection") or 0.0),
            },
        )
        _set_headers(response, envelope.source, freshness)
        return envelope
    except Exception as exc:
        envelope = _error_envelope(
            code="property_query_failed",
            message=str(exc),
            recoverable=True,
            suggested_action="Check property_analyses table and ingestion jobs",
            correlation_id=correlation_id,
        )
        _set_headers(response, envelope.source, envelope.data_freshness_seconds)
        return envelope


@router.get("/sms-compliance/{location_id}", response_model=RevenueV2Envelope)
async def get_sms_compliance_v2(
    location_id: str,
    response: Response,
    lookback_days: int = Query(default=30, ge=1, le=180),
) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            opt_out_row = await conn.fetchrow(
                """
                SELECT COUNT(*) AS cnt
                FROM sms_opt_outs
                WHERE location_id = $1 AND opted_out_at >= NOW() - ($2::text || ' days')::interval
                """,
                location_id,
                lookback_days,
            )
            sent_row = await conn.fetchrow(
                """
                SELECT COUNT(*) AS cnt, MAX(sent_at) AS last_sent_at
                FROM communication_logs
                WHERE channel = 'sms'
                AND metadata->>'location_id' = $1
                AND sent_at >= NOW() - ($2::text || ' days')::interval
                """,
                location_id,
                lookback_days,
            )

        opt_outs = int((opt_out_row or {}).get("cnt", 0))
        sent = int((sent_row or {}).get("cnt", 0))
        rate = (opt_outs / sent) if sent else 0.0
        score = max(0.0, 100.0 - (rate * 100 * 20.0))
        freshness = _age_seconds((sent_row or {}).get("last_sent_at")) if sent_row else 0

        envelope = RevenueV2Envelope(
            source=ResponseSource.DATABASE,
            data_freshness_seconds=freshness,
            generated_at=utc_now(),
            correlation_id=correlation_id,
            data={
                "location_id": location_id,
                "lookback_days": lookback_days,
                "messages_sent": sent,
                "opt_outs": opt_outs,
                "opt_out_rate": round(rate, 4),
                "compliance_score": round(score, 2),
            },
        )
        _set_headers(response, envelope.source, freshness)
        return envelope
    except Exception as exc:
        envelope = _error_envelope(
            code="sms_compliance_query_failed",
            message=str(exc),
            recoverable=True,
            suggested_action="Check sms_opt_outs/communication_logs tables and location metadata",
            correlation_id=correlation_id,
        )
        _set_headers(response, envelope.source, envelope.data_freshness_seconds)
        return envelope


@router.get("/market-intelligence/recommendations/stream")
async def stream_market_recommendations_v2(
    market_id: str,
    lead_id: str,
    limit: int = Query(default=5, ge=1, le=20),
):
    correlation_id = new_correlation_id()

    async def event_stream():
        start_event = RevenueSSEEvent(
            event="start",
            correlation_id=correlation_id,
            payload={"market_id": market_id, "lead_id": lead_id},
        )
        yield f"event: start\ndata: {start_event.model_dump_json()}\n\n"

        try:
            db = await get_database()
            async with db.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT property_id, market_score, roi_projection
                    FROM property_analyses
                    ORDER BY updated_at DESC NULLS LAST
                    LIMIT $1
                    """,
                    limit,
                )

            for row in rows:
                token_event = RevenueSSEEvent(
                    event="token",
                    correlation_id=correlation_id,
                    payload={
                        "property_id": row.get("property_id"),
                        "market_score": float(row.get("market_score") or 0.0),
                        "roi_projection": float(row.get("roi_projection") or 0.0),
                    },
                )
                yield f"event: token\ndata: {token_event.model_dump_json()}\n\n"

            complete_event = RevenueSSEEvent(
                event="complete",
                correlation_id=correlation_id,
                payload={"count": len(rows), "source": ResponseSource.DATABASE.value},
            )
            yield f"event: complete\ndata: {complete_event.model_dump_json()}\n\n"
        except Exception as exc:
            error_event = RevenueSSEEvent(
                event="error",
                correlation_id=correlation_id,
                payload={
                    "error_code": "market_stream_failed",
                    "error_message": str(exc),
                    "recoverable": True,
                    "suggested_action": "Check market intelligence data pipeline and retry",
                },
            )
            yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
