"""Revenue-critical v2 API routes with strict contracts and tenant scoping."""

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from ghl_real_estate_ai.api.schemas.revenue_v2 import (
    ErrorEnvelope,
    ResponseMeta,
    ResponseSource,
    RevenueSSEEvent,
    RevenueV2Envelope,
    new_correlation_id,
    utc_now,
)
from ghl_real_estate_ai.services.database_service import get_database

router = APIRouter(prefix="/api/v2", tags=["revenue-v2"])

_CACHE: dict[str, tuple[RevenueV2Envelope, datetime]] = {}
_TABLE_COLUMNS_CACHE: dict[str, set[str]] = {}


def _age_seconds(ts: datetime | None) -> int:
    if ts is None:
        return 0
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(int((now - ts).total_seconds()), 0)


def _cache_key(*, tenant_id: str, route_name: str, resource_id: str) -> str:
    return f"tenant:{tenant_id}:{route_name}:{resource_id}"


def _cache_get(key: str) -> Optional[RevenueV2Envelope]:
    hit = _CACHE.get(key)
    if not hit:
        return None
    payload, expires_at = hit
    if expires_at <= datetime.now(timezone.utc):
        _CACHE.pop(key, None)
        return None
    return payload


def _cache_set(key: str, payload: RevenueV2Envelope, ttl_seconds: int = 300) -> None:
    expires_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=ttl_seconds)
    _CACHE[key] = (payload, expires_at)


async def _table_columns(conn: Any, table_name: str) -> set[str]:
    cached = _TABLE_COLUMNS_CACHE.get(table_name)
    if cached is not None:
        return cached

    try:
        rows = await conn.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            """,
            table_name,
        )
    except Exception:
        rows = []

    columns = {row.get("column_name") for row in rows if row.get("column_name")}
    _TABLE_COLUMNS_CACHE[table_name] = columns
    return columns


def _tenant_column(columns: set[str]) -> str | None:
    for candidate in ("tenant_id", "location_id", "account_id"):
        if candidate in columns:
            return candidate
    return None


def _tenant_scope_unenforceable(correlation_id: str, resource: str) -> RevenueV2Envelope:
    return _error(
        correlation_id=correlation_id,
        source=ResponseSource.DATABASE,
        code="tenant_scope_unenforceable",
        message=f"Tenant scope cannot be safely enforced for resource '{resource}'.",
        retryable=False,
        details={"resource": resource},
    )


def _set_headers(response: Response, meta: ResponseMeta) -> None:
    response.headers["X-Response-Source"] = meta.source.value
    response.headers["X-Data-Freshness"] = str(meta.freshness_seconds)
    response.headers["X-Correlation-Id"] = meta.correlation_id


def _meta(source: ResponseSource, correlation_id: str, freshness_seconds: int = 0) -> ResponseMeta:
    return ResponseMeta(
        source=source,
        correlation_id=correlation_id,
        generated_at=utc_now(),
        freshness_seconds=freshness_seconds,
    )


def _success(
    *,
    source: ResponseSource,
    correlation_id: str,
    freshness_seconds: int,
    data: Dict[str, Any],
) -> RevenueV2Envelope:
    return RevenueV2Envelope(
        data=data,
        meta=_meta(source=source, correlation_id=correlation_id, freshness_seconds=freshness_seconds),
        error=None,
    )


def _error(
    *,
    correlation_id: str,
    source: ResponseSource,
    code: str,
    message: str,
    retryable: bool,
    details: Dict[str, Any] | None = None,
) -> RevenueV2Envelope:
    return RevenueV2Envelope(
        data={},
        meta=_meta(source=source, correlation_id=correlation_id, freshness_seconds=0),
        error=ErrorEnvelope(
            code=code,
            message=message,
            correlation_id=correlation_id,
            retryable=retryable,
            details=details or {},
        ),
    )


def _missing_tenant_scope(correlation_id: str) -> RevenueV2Envelope:
    return _error(
        correlation_id=correlation_id,
        source=ResponseSource.DATABASE,
        code="tenant_scope_required",
        message="Missing required tenant scope. Provide tenant_id.",
        retryable=False,
        details={"required": ["tenant_id"]},
    )


def _row_tenant_mismatch(record: Dict[str, Any], tenant_id: str) -> bool:
    owner = record.get("tenant_id") or record.get("location_id") or record.get("account_id")
    return owner is not None and str(owner) != str(tenant_id)


def _tenant_access_denied(correlation_id: str, tenant_id: str, resource_id: str) -> RevenueV2Envelope:
    return _error(
        correlation_id=correlation_id,
        source=ResponseSource.DATABASE,
        code="tenant_scope_violation",
        message="Requested resource does not belong to provided tenant scope.",
        retryable=False,
        details={"tenant_id": tenant_id, "resource_id": resource_id},
    )


def _load_weekly_kpi_row(tenant_id: str, week_start: str | None) -> Dict[str, Any]:
    csv_path = Path("reports/weekly_pilot_kpis.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing KPI CSV: {csv_path}")

    tenant_rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("tenant_id") == tenant_id:
                tenant_rows.append(row)

    if not tenant_rows:
        raise ValueError(f"No KPI rows found for tenant_id={tenant_id}")

    if week_start:
        for row in tenant_rows:
            if row.get("week_start") == week_start:
                return row
        raise ValueError(f"No KPI row for tenant_id={tenant_id}, week_start={week_start}")

    tenant_rows.sort(key=lambda r: r.get("week_start", ""), reverse=True)
    return tenant_rows[0]


def _render_proof_pack_markdown(tenant_id: str, row: Dict[str, Any]) -> str:
    return f"""# Weekly Executive Proof-Pack

## Tenant
- Tenant ID: {tenant_id}
- Week Start: {row.get("week_start")}

## KPI Summary
- 5-minute response SLA attainment: {row.get("response_sla_pct")}%
- Lead qualification throughput: {row.get("qualified_leads")} qualified / {row.get("leads_received")} received
- Appointments booked: {row.get("appointments_booked")}
- Cost per qualified lead: ${row.get("cost_per_qualified_lead")}

## Operational Highlights
- Wins: N/A
- Risks: TBD
- Notable incidents and remediation status: None reported
"""


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
            envelope = _error(
                correlation_id=correlation_id,
                source=ResponseSource.DATABASE,
                code="subscription_not_found",
                message=f"No subscription found for location_id={location_id}",
                retryable=False,
                details={"location_id": location_id},
            )
            _set_headers(response, envelope.meta)
            return envelope

        record = dict(row)
        if _row_tenant_mismatch(record, location_id):
            envelope = _tenant_access_denied(correlation_id, location_id, location_id)
            _set_headers(response, envelope.meta)
            return envelope

        freshness = _age_seconds(record.get("updated_at"))
        envelope = _success(
            source=ResponseSource.DATABASE,
            correlation_id=correlation_id,
            freshness_seconds=freshness,
            data={
                "subscription_id": record.get("id"),
                "tenant_id": record.get("location_id"),
                "location_id": record.get("location_id"),
                "tier": record.get("tier"),
                "status": record.get("status"),
                "current_period_end": str(record.get("current_period_end")),
            },
        )
        _set_headers(response, envelope.meta)
        return envelope
    except Exception as exc:
        envelope = _error(
            correlation_id=correlation_id,
            source=ResponseSource.DATABASE,
            code="billing_query_failed",
            message=str(exc),
            retryable=True,
            details={"hint": "Check database connectivity and subscriptions table"},
        )
        _set_headers(response, envelope.meta)
        return envelope


@router.get("/prediction/deal-outcome/{deal_id}", response_model=RevenueV2Envelope)
async def get_prediction_deal_outcome_v2(
    deal_id: str,
    response: Response,
    tenant_id: str | None = Query(default=None, min_length=1),
) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    if not tenant_id:
        envelope = _missing_tenant_scope(correlation_id)
        _set_headers(response, envelope.meta)
        return envelope

    try:
        db = await get_database()
        async with db.get_connection() as conn:
            columns = await _table_columns(conn, "deals")
            tenant_col = _tenant_column(columns)
            if not tenant_col:
                envelope = _tenant_scope_unenforceable(correlation_id, "deals")
                _set_headers(response, envelope.meta)
                return envelope
            tenant_clause = f" AND {tenant_col} = $2" if tenant_col else ""
            args = (deal_id, tenant_id) if tenant_col else (deal_id,)
            row = await conn.fetchrow(
                f"""
                SELECT deal_id, current_stage, offer_amount, property_value, commission_rate, updated_at
                FROM deals
                WHERE deal_id = $1
                {tenant_clause}
                LIMIT 1
                """,
                *args,
            )

        if not row:
            envelope = _error(
                correlation_id=correlation_id,
                source=ResponseSource.DATABASE,
                code="deal_not_found",
                message=f"No deal found for deal_id={deal_id}",
                retryable=False,
                details={"tenant_id": tenant_id, "deal_id": deal_id},
            )
            _set_headers(response, envelope.meta)
            return envelope

        record = dict(row)
        if _row_tenant_mismatch(record, tenant_id):
            envelope = _tenant_access_denied(correlation_id, tenant_id, deal_id)
            _set_headers(response, envelope.meta)
            return envelope

        offer = float(record.get("offer_amount") or 0.0)
        value = float(record.get("property_value") or 0.0)
        ratio = (offer / value) if value > 0 else 0.0
        closing_probability = min(max(round(ratio * 100, 2), 5.0), 95.0)
        freshness = _age_seconds(record.get("updated_at"))

        envelope = _success(
            source=ResponseSource.DATABASE,
            correlation_id=correlation_id,
            freshness_seconds=freshness,
            data={
                "tenant_id": tenant_id,
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
        _set_headers(response, envelope.meta)
        return envelope
    except Exception as exc:
        envelope = _error(
            correlation_id=correlation_id,
            source=ResponseSource.DATABASE,
            code="prediction_query_failed",
            message=str(exc),
            retryable=True,
            details={"tenant_id": tenant_id, "hint": "Check deals table availability and data shape"},
        )
        _set_headers(response, envelope.meta)
        return envelope


@router.get("/customer-journeys/{lead_id}", response_model=RevenueV2Envelope)
async def get_customer_journey_v2(
    lead_id: str,
    response: Response,
    tenant_id: str | None = Query(default=None, min_length=1),
) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    if not tenant_id:
        envelope = _missing_tenant_scope(correlation_id)
        _set_headers(response, envelope.meta)
        return envelope

    try:
        db = await get_database()
        async with db.get_connection() as conn:
            columns = await _table_columns(conn, "lead_journey_state")
            tenant_col = _tenant_column(columns)
            if not tenant_col:
                envelope = _tenant_scope_unenforceable(correlation_id, "lead_journey_state")
                _set_headers(response, envelope.meta)
                return envelope
            tenant_clause = f" AND {tenant_col} = $2" if tenant_col else ""
            args = (lead_id, tenant_id) if tenant_col else (lead_id,)
            row = await conn.fetchrow(
                f"""
                SELECT lead_id, current_stage, updated_at
                FROM lead_journey_state
                WHERE lead_id = $1
                {tenant_clause}
                LIMIT 1
                """,
                *args,
            )

        if not row:
            envelope = _error(
                correlation_id=correlation_id,
                source=ResponseSource.DATABASE,
                code="journey_not_found",
                message=f"No journey found for lead_id={lead_id}",
                retryable=False,
                details={"tenant_id": tenant_id, "lead_id": lead_id},
            )
            _set_headers(response, envelope.meta)
            return envelope

        record = dict(row)
        if _row_tenant_mismatch(record, tenant_id):
            envelope = _tenant_access_denied(correlation_id, tenant_id, lead_id)
            _set_headers(response, envelope.meta)
            return envelope

        freshness = _age_seconds(record.get("updated_at"))
        envelope = _success(
            source=ResponseSource.DATABASE,
            correlation_id=correlation_id,
            freshness_seconds=freshness,
            data={
                "tenant_id": tenant_id,
                "lead_id": record.get("lead_id"),
                "current_stage": record.get("current_stage"),
            },
        )
        _set_headers(response, envelope.meta)
        return envelope
    except Exception as exc:
        envelope = _error(
            correlation_id=correlation_id,
            source=ResponseSource.DATABASE,
            code="journey_query_failed",
            message=str(exc),
            retryable=True,
            details={"tenant_id": tenant_id, "hint": "Check lead_journey_state table"},
        )
        _set_headers(response, envelope.meta)
        return envelope


@router.get("/property-intelligence/{property_id}", response_model=RevenueV2Envelope)
async def get_property_intelligence_v2(
    property_id: str,
    response: Response,
    tenant_id: str | None = Query(default=None, min_length=1),
) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    if not tenant_id:
        envelope = _missing_tenant_scope(correlation_id)
        _set_headers(response, envelope.meta)
        return envelope

    cache_key = _cache_key(tenant_id=tenant_id, route_name="property-intelligence", resource_id=property_id)
    cached = _cache_get(cache_key)
    if cached:
        envelope = cached.model_copy(deep=True)
        envelope.meta.source = ResponseSource.CACHE
        envelope.meta.correlation_id = correlation_id
        _set_headers(response, envelope.meta)
        return envelope

    try:
        db = await get_database()
        async with db.get_connection() as conn:
            columns = await _table_columns(conn, "property_analyses")
            tenant_col = _tenant_column(columns)
            if not tenant_col:
                envelope = _tenant_scope_unenforceable(correlation_id, "property_analyses")
                _set_headers(response, envelope.meta)
                return envelope
            tenant_clause = f" AND {tenant_col} = $2" if tenant_col else ""
            args = (property_id, tenant_id) if tenant_col else (property_id,)
            row = await conn.fetchrow(
                f"""
                SELECT property_id, market_score, roi_projection, updated_at
                FROM property_analyses
                WHERE property_id = $1
                {tenant_clause}
                ORDER BY updated_at DESC NULLS LAST
                LIMIT 1
                """,
                *args,
            )

        if not row:
            envelope = _error(
                correlation_id=correlation_id,
                source=ResponseSource.DATABASE,
                code="property_analysis_not_found",
                message=f"No property analysis found for property_id={property_id}",
                retryable=False,
                details={"tenant_id": tenant_id, "property_id": property_id},
            )
            _set_headers(response, envelope.meta)
            return envelope

        record = dict(row)
        if _row_tenant_mismatch(record, tenant_id):
            envelope = _tenant_access_denied(correlation_id, tenant_id, property_id)
            _set_headers(response, envelope.meta)
            return envelope

        freshness = _age_seconds(record.get("updated_at"))
        envelope = _success(
            source=ResponseSource.DATABASE,
            correlation_id=correlation_id,
            freshness_seconds=freshness,
            data={
                "tenant_id": tenant_id,
                "property_id": record.get("property_id"),
                "market_score": float(record.get("market_score") or 0.0),
                "roi_projection": float(record.get("roi_projection") or 0.0),
            },
        )
        _cache_set(cache_key, envelope)
        _set_headers(response, envelope.meta)
        return envelope
    except Exception as exc:
        envelope = _error(
            correlation_id=correlation_id,
            source=ResponseSource.DATABASE,
            code="property_query_failed",
            message=str(exc),
            retryable=True,
            details={"tenant_id": tenant_id, "hint": "Check property_analyses table"},
        )
        _set_headers(response, envelope.meta)
        return envelope


@router.get("/sms-compliance/{location_id}", response_model=RevenueV2Envelope)
async def get_sms_compliance_v2(
    location_id: str,
    response: Response,
    lookback_days: int = Query(default=30, ge=1, le=180),
) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    cache_key = _cache_key(tenant_id=location_id, route_name="sms-compliance", resource_id=str(lookback_days))
    cached = _cache_get(cache_key)
    if cached:
        envelope = cached.model_copy(deep=True)
        envelope.meta.source = ResponseSource.CACHE
        envelope.meta.correlation_id = correlation_id
        _set_headers(response, envelope.meta)
        return envelope

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

        envelope = _success(
            source=ResponseSource.DATABASE,
            correlation_id=correlation_id,
            freshness_seconds=freshness,
            data={
                "tenant_id": location_id,
                "location_id": location_id,
                "lookback_days": lookback_days,
                "messages_sent": sent,
                "opt_outs": opt_outs,
                "opt_out_rate": round(rate, 4),
                "compliance_score": round(score, 2),
            },
        )
        _cache_set(cache_key, envelope)
        _set_headers(response, envelope.meta)
        return envelope
    except Exception as exc:
        envelope = _error(
            correlation_id=correlation_id,
            source=ResponseSource.DATABASE,
            code="sms_compliance_query_failed",
            message=str(exc),
            retryable=True,
            details={"location_id": location_id, "hint": "Check sms_opt_outs and communication_logs tables"},
        )
        _set_headers(response, envelope.meta)
        return envelope


@router.get("/market-intelligence/recommendations/stream")
async def stream_market_recommendations_v2(
    market_id: str,
    lead_id: str,
    tenant_id: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
):
    correlation_id = new_correlation_id()

    async def event_stream():
        start_event = RevenueSSEEvent(
            event="start",
            correlation_id=correlation_id,
            payload={"market_id": market_id, "lead_id": lead_id, "tenant_id": tenant_id},
        )
        yield f"event: start\ndata: {start_event.model_dump_json()}\n\n"

        if not tenant_id:
            error_event = RevenueSSEEvent(
                event="error",
                correlation_id=correlation_id,
                payload={
                    "code": "tenant_scope_required",
                    "message": "Missing required tenant scope. Provide tenant_id.",
                    "retryable": False,
                    "retry_hint": "Add tenant_id query parameter and retry.",
                },
            )
            yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
            return

        try:
            db = await get_database()
            async with db.get_connection() as conn:
                columns = await _table_columns(conn, "property_analyses")
                tenant_col = _tenant_column(columns)
                if not tenant_col:
                    error_event = RevenueSSEEvent(
                        event="error",
                        correlation_id=correlation_id,
                        payload={
                            "code": "tenant_scope_unenforceable",
                            "message": "Tenant scope cannot be safely enforced for property_analyses.",
                            "retryable": False,
                            "retry_hint": "Ensure property_analyses has tenant/location ownership column.",
                        },
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                tenant_clause = f" WHERE {tenant_col} = $2" if tenant_col else ""
                args = (limit, tenant_id) if tenant_col else (limit,)
                rows = await conn.fetch(
                    f"""
                    SELECT property_id, market_score, roi_projection
                    FROM property_analyses
                    {tenant_clause}
                    ORDER BY updated_at DESC NULLS LAST
                    LIMIT $1
                    """,
                    *args,
                )

            for row in rows:
                token_event = RevenueSSEEvent(
                    event="token",
                    correlation_id=correlation_id,
                    payload={
                        "tenant_id": tenant_id,
                        "property_id": row.get("property_id"),
                        "market_score": float(row.get("market_score") or 0.0),
                        "roi_projection": float(row.get("roi_projection") or 0.0),
                    },
                )
                yield f"event: token\ndata: {token_event.model_dump_json()}\n\n"

            complete_event = RevenueSSEEvent(
                event="complete",
                correlation_id=correlation_id,
                payload={"count": len(rows), "source": ResponseSource.DATABASE.value, "tenant_id": tenant_id},
            )
            yield f"event: complete\ndata: {complete_event.model_dump_json()}\n\n"
        except Exception as exc:
            error_event = RevenueSSEEvent(
                event="error",
                correlation_id=correlation_id,
                payload={
                    "code": "market_stream_failed",
                    "message": str(exc),
                    "retryable": True,
                    "retry_hint": "Retry the stream in 30 seconds.",
                },
            )
            yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/reports/weekly-proof-pack", response_model=RevenueV2Envelope)
async def get_weekly_proof_pack_v2(
    response: Response,
    tenant_id: str | None = Query(default=None, min_length=1),
    week_start: str | None = Query(default=None),
    allow_latest_fallback: bool = Query(default=False),
) -> RevenueV2Envelope:
    correlation_id = new_correlation_id()
    if not tenant_id:
        envelope = _missing_tenant_scope(correlation_id)
        _set_headers(response, envelope.meta)
        return envelope

    try:
        db = await get_database()
        async with db.get_connection() as conn:
            db_row = (
                await conn.fetchrow(
                    """
                SELECT tenant_id, week_start, leads_received, qualified_leads, response_sla_pct,
                       appointments_booked, cost_per_qualified_lead, updated_at
                FROM pilot_kpi_records
                WHERE tenant_id = $1
                ORDER BY week_start DESC
                LIMIT 1
                """,
                    tenant_id,
                )
                if week_start is None
                else await conn.fetchrow(
                    """
                SELECT tenant_id, week_start, leads_received, qualified_leads, response_sla_pct,
                       appointments_booked, cost_per_qualified_lead, updated_at
                FROM pilot_kpi_records
                WHERE tenant_id = $1 AND week_start = $2::date
                LIMIT 1
                """,
                    tenant_id,
                    week_start,
                )
            )

            if not db_row and week_start and allow_latest_fallback:
                db_row = await conn.fetchrow(
                    """
                    SELECT tenant_id, week_start, leads_received, qualified_leads, response_sla_pct,
                           appointments_booked, cost_per_qualified_lead, updated_at
                    FROM pilot_kpi_records
                    WHERE tenant_id = $1
                    ORDER BY week_start DESC
                    LIMIT 1
                    """,
                    tenant_id,
                )

        if not db_row:
            envelope = _error(
                correlation_id=correlation_id,
                source=ResponseSource.DATABASE,
                code="weekly_proof_pack_unavailable",
                message="No KPI rows available for requested tenant/week.",
                retryable=False,
                details={"tenant_id": tenant_id, "week_start": week_start},
            )
            _set_headers(response, envelope.meta)
            return envelope

        kpi_row = dict(db_row)
        freshness = _age_seconds(kpi_row.get("updated_at"))
        rendered_markdown = _render_proof_pack_markdown(tenant_id, kpi_row)
        envelope = _success(
            source=ResponseSource.DATABASE,
            correlation_id=correlation_id,
            freshness_seconds=freshness,
            data={
                "tenant_id": tenant_id,
                "week_start": kpi_row.get("week_start"),
                "kpi": {
                    "leads_received": int(kpi_row.get("leads_received", 0)),
                    "qualified_leads": int(kpi_row.get("qualified_leads", 0)),
                    "response_sla_pct": float(kpi_row.get("response_sla_pct", 0.0)),
                    "appointments_booked": int(kpi_row.get("appointments_booked", 0)),
                    "cost_per_qualified_lead": float(kpi_row.get("cost_per_qualified_lead", 0.0)),
                },
                "proof_pack_markdown": rendered_markdown,
            },
        )
        _set_headers(response, envelope.meta)
        return envelope
    except Exception as exc:
        # Explicit fallback branch for DB connection/table issues.
        try:
            kpi_row = _load_weekly_kpi_row(
                tenant_id=tenant_id, week_start=week_start if not allow_latest_fallback else None
            )
            proof_pack_path = Path("reports/weekly_executive_proof_pack.md")
            markdown = (
                proof_pack_path.read_text(encoding="utf-8")
                if proof_pack_path.exists()
                else _render_proof_pack_markdown(tenant_id, kpi_row)
            )
            freshness = (
                _age_seconds(datetime.fromtimestamp(proof_pack_path.stat().st_mtime, tz=timezone.utc))
                if proof_pack_path.exists()
                else 0
            )

            envelope = _success(
                source=ResponseSource.LIVE_PROVIDER,
                correlation_id=correlation_id,
                freshness_seconds=freshness,
                data={
                    "tenant_id": tenant_id,
                    "week_start": kpi_row.get("week_start"),
                    "kpi": {
                        "leads_received": int(kpi_row.get("leads_received", 0)),
                        "qualified_leads": int(kpi_row.get("qualified_leads", 0)),
                        "response_sla_pct": float(kpi_row.get("response_sla_pct", 0.0)),
                        "appointments_booked": int(kpi_row.get("appointments_booked", 0)),
                        "cost_per_qualified_lead": float(kpi_row.get("cost_per_qualified_lead", 0.0)),
                    },
                    "proof_pack_markdown": markdown,
                    "fallback_reason": str(exc),
                },
            )
            _set_headers(response, envelope.meta)
            return envelope
        except Exception as fallback_exc:
            envelope = _error(
                correlation_id=correlation_id,
                source=ResponseSource.LIVE_PROVIDER,
                code="weekly_proof_pack_unavailable",
                message=str(fallback_exc),
                retryable=True,
                details={"tenant_id": tenant_id, "db_error": str(exc)},
            )
            _set_headers(response, envelope.meta)
            return envelope
