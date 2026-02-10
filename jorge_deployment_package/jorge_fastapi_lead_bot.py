#!/usr/bin/env python3
"""
Jorge's FastAPI Lead Bot Microservice - High Performance Implementation

This FastAPI microservice provides high-performance webhook handling for Jorge's
lead qualification system with <500ms response times and 5-minute rule enforcement.

Key Features:
- <500ms lead analysis through optimized architecture
- 5-minute response rule monitoring and enforcement
- Jorge's business rules validation
- Real-time performance metrics
- Async processing for maximum throughput

Performance Targets:
- Lead Analysis: <500ms (target: <300ms)
- Webhook Response: <2s total
- 5-Minute Rule: >99% compliance
- API Uptime: 99.9% during business hours

Author: Claude Code Assistant
Created: January 23, 2026
"""

import asyncio
import hashlib
import hmac
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
import uvicorn

# Jorge's enhanced intelligence
from jorge_claude_intelligence import (
    CLAUDE_AVAILABLE,
    analyze_lead_for_jorge,
    claude_intelligence,
    get_five_minute_compliance_status,
)
from ghl_client import GHLClient
from config_settings import settings
from runtime_metrics import RuntimeMetricsRegistry
from webhook_idempotency import FileBackedIdempotencyStore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Jorge's Lead Bot API",
    description="High-performance lead qualification microservice for Jorge's real estate business",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ghl_client = GHLClient()
webhook_idempotency_store = FileBackedIdempotencyStore(
    storage_path=str(Path(__file__).resolve().parent / "data" / "webhook_idempotency.json"),
    ttl_seconds=settings.webhook_idempotency_ttl_seconds,
)
metrics_registry = RuntimeMetricsRegistry()
ADAPTIVE_FOLLOWUP_FEATURE = "adaptive_followup_timing"
LEAD_SOURCE_ATTRIBUTION_FEATURE = "lead_source_attribution"
AB_RESPONSE_STYLE_FEATURE = "ab_response_style_testing"
SLA_HANDOFF_THRESHOLDS_FEATURE = "sla_handoff_thresholds"
WORKSTREAM_G_VERSION = "workstream_g_v1"


# Pydantic models for request/response validation
class LeadMessage(BaseModel):
    """Lead message input model"""
    contact_id: str = Field(..., description="GHL contact ID")
    location_id: str = Field(..., description="GHL location ID")
    message: str = Field(..., description="Lead's message content")
    contact_data: Optional[Dict[str, Any]] = Field(None, description="Additional contact information")
    force_ai_analysis: bool = Field(False, description="Force Claude AI analysis even for low-priority leads")


class GHLWebhook(BaseModel):
    """GoHighLevel webhook payload model"""
    type: str = Field(..., description="Webhook event type")
    location_id: str = Field(..., description="GHL location ID")
    contact_id: str = Field(..., description="Contact ID")
    message: Optional[str] = Field(None, description="Message content")
    contact: Optional[Dict[str, Any]] = Field(None, description="Contact data")
    conversation: Optional[Dict[str, Any]] = Field(None, description="Conversation data")
    timestamp: Optional[str] = Field(None, description="Event timestamp")


class LeadAnalysisResponse(BaseModel):
    """Lead analysis response model"""
    success: bool = Field(..., description="Analysis success status")
    lead_score: float = Field(..., description="Lead score (0-100)")
    lead_temperature: str = Field(..., description="Lead temperature (Hot/Warm/Cold)")
    response_message: str = Field(..., description="Suggested response message")
    jorge_priority: str = Field(..., description="Priority for Jorge (high/normal/review)")
    estimated_commission: float = Field(..., description="Estimated commission ($)")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Recommended GHL actions")
    follow_up: Optional[Dict[str, Any]] = Field(None, description="Follow-up scheduling")


class PerformanceStatus(BaseModel):
    """Performance monitoring response model"""
    five_minute_compliance: Dict[str, Any] = Field(..., description="5-minute rule compliance data")
    current_performance: Dict[str, Any] = Field(..., description="Current performance metrics")
    system_health: Dict[str, Any] = Field(..., description="System health indicators")


def _compute_webhook_signature(secret: str, payload_bytes: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def _verify_webhook_signature(payload_bytes: bytes, signature: Optional[str], secret: str) -> bool:
    if not signature or not secret:
        return False

    normalized = signature.strip()
    if normalized.startswith("sha256="):
        normalized = normalized.split("=", 1)[1]

    expected = _compute_webhook_signature(secret, payload_bytes)
    return hmac.compare_digest(normalized, expected)


def _extract_webhook_id(payload: Dict[str, Any]) -> str:
    provider_event_id = (
        payload.get("id")
        or payload.get("eventId")
        or payload.get("event_id")
        or payload.get("webhookId")
        or payload.get("webhook_id")
    )
    if provider_event_id:
        return str(provider_event_id)

    contact_id = payload.get("contact_id") or payload.get("contactId") or "unknown_contact"
    event_type = payload.get("type") or "unknown_type"
    timestamp = payload.get("timestamp") or payload.get("createdAt") or "unknown_timestamp"
    fallback_key = f"{contact_id}:{timestamp}:{event_type}"
    return hashlib.sha256(fallback_key.encode("utf-8")).hexdigest()


def _is_storage_writable(directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    probe_file = directory / ".write_probe"
    try:
        with open(probe_file, "w", encoding="utf-8") as handle:
            handle.write(datetime.utcnow().isoformat())
        probe_file.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _claude_mode() -> str:
    if not CLAUDE_AVAILABLE:
        return "sdk_unavailable"
    if getattr(claude_intelligence, "claude_client", None):
        return "live"
    return "pattern_only"


def _record_analysis_cache_metrics(analysis_result: Dict[str, Any]) -> None:
    performance = analysis_result.get("performance", {})
    if performance.get("cache_hit") is True:
        metrics_registry.record_cache_hit()
    elif "cache_hit" in performance:
        metrics_registry.record_cache_miss()


def _extract_lead_source(webhook_data: GHLWebhook) -> str:
    candidates: List[Any] = []
    if isinstance(webhook_data.contact, dict):
        candidates.extend(
            [
                webhook_data.contact.get("source"),
                webhook_data.contact.get("lead_source"),
                webhook_data.contact.get("sourceName"),
                webhook_data.contact.get("utm_source"),
            ]
        )
    if isinstance(webhook_data.conversation, dict):
        candidates.extend(
            [
                webhook_data.conversation.get("source"),
                webhook_data.conversation.get("channel"),
            ]
        )

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return "unknown"


def _evaluate_growth_feature(feature_name: str, lead_source: str) -> tuple[bool, str]:
    enabled = False
    reason = "flag_disabled"

    if hasattr(settings, "evaluate_growth_feature"):
        enabled, reason = settings.evaluate_growth_feature(
            feature_name=feature_name,
            lead_source=lead_source,
        )

    metrics_registry.record_feature_flag_evaluation(
        feature_name=feature_name,
        enabled=enabled,
        reason=reason,
    )
    return enabled, reason


def _normalize_metric_key(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in (value or "").strip().lower())
    normalized = normalized.strip("_")
    return normalized or "unknown"


def _derive_conversion_feedback_signal(analysis_result: Dict[str, Any]) -> str:
    score = float(analysis_result.get("lead_score", 0) or 0)
    priority = str(analysis_result.get("jorge_priority", "normal")).strip().lower()
    temperature = str(analysis_result.get("lead_temperature", "cold")).strip().lower()

    if score >= 85 or priority == "high" or temperature == "hot":
        return "high_intent"
    if score >= 65 or priority == "review_required" or temperature == "warm":
        return "nurture"
    return "low_intent"


def _apply_lead_source_attribution_feedback(
    analysis_result: Dict[str, Any],
    lead_source: str,
    feature_enabled: bool,
    feature_reason: str,
) -> Dict[str, Any]:
    if not isinstance(analysis_result, dict):
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name="invalid_analysis_payload",
        )
        return {}

    normalized_source = (lead_source or "").strip().lower() or "unknown"
    source_metric_key = _normalize_metric_key(normalized_source)
    feedback_signal = _derive_conversion_feedback_signal(analysis_result)

    # Telemetry is captured regardless of rollout status to baseline the capability.
    metrics_registry.record_growth_feature_event(
        feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
        event_name=f"source_observed_{source_metric_key}",
    )
    metrics_registry.record_growth_feature_event(
        feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
        event_name=f"feedback_signal_observed_{feedback_signal}",
    )

    if not feature_enabled:
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name=f"bypassed_{feature_reason}",
        )
        return {}

    captured_at = datetime.now().isoformat()
    growth_context = {
        "attribution": {
            "source": normalized_source,
            "model": "last_touch",
            "captured_at": captured_at,
            "version": WORKSTREAM_G_VERSION,
        },
        "conversion_feedback": {
            "status": "pending",
            "signal": feedback_signal,
            "updated_at": captured_at,
            "version": WORKSTREAM_G_VERSION,
        },
    }

    analysis_result["lead_source_attribution"] = growth_context["attribution"]
    analysis_result["conversion_feedback"] = growth_context["conversion_feedback"]

    follow_up_data = analysis_result.get("follow_up")
    if isinstance(follow_up_data, dict):
        enriched_follow_up = dict(follow_up_data)
        metadata = dict(enriched_follow_up.get("metadata", {}))
        metadata.update(
            {
                "lead_source": normalized_source,
                "conversion_feedback_status": "pending",
                "conversion_feedback_signal": feedback_signal,
            }
        )
        enriched_follow_up["metadata"] = metadata
        analysis_result["follow_up"] = enriched_follow_up
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name="follow_up_enriched",
        )
    else:
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name="follow_up_missing",
        )

    if (
        getattr(settings, "ff_growth_lead_source_writeback", False)
        or getattr(settings, "ff_growth_conversion_feedback_writeback", False)
    ):
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name="writeback_ready",
        )
    else:
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name="telemetry_only_mode",
        )

    metrics_registry.record_growth_feature_event(
        feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
        event_name="applied",
    )
    return growth_context


def _derive_conversion_feedback_outcome(contact_data: Optional[Dict[str, Any]]) -> str:
    if not isinstance(contact_data, dict):
        return "unknown"

    candidates = [
        contact_data.get("opportunity_status"),
        contact_data.get("opportunityStatus"),
        contact_data.get("status"),
        contact_data.get("stage"),
        contact_data.get("pipeline_stage"),
        contact_data.get("pipelineStage"),
    ]
    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        normalized = _normalize_metric_key(candidate)
        if any(token in normalized for token in ("won", "closed_won", "booked", "appointment", "contract")):
            return "converted"
        if any(token in normalized for token in ("lost", "dead", "unqualified", "do_not_contact", "opt_out")):
            return "lost"
        if any(token in normalized for token in ("new", "open", "contacted", "nurture", "qualified", "follow_up")):
            return "active"
    return "unknown"


def _derive_follow_up_engagement_score(
    analysis_result: Dict[str, Any],
    follow_up_data: Dict[str, Any],
) -> float:
    explicit_score = follow_up_data.get("engagement_score")
    if explicit_score is not None:
        try:
            return max(0.0, min(100.0, float(explicit_score)))
        except (TypeError, ValueError):
            pass

    score = float(analysis_result.get("lead_score", 0) or 0)
    priority = str(analysis_result.get("jorge_priority", "normal")).lower()
    temperature = str(analysis_result.get("lead_temperature", "cold")).lower()

    if priority == "high":
        score = max(score, 85.0)
    elif priority == "review_required":
        score = max(score, 65.0)

    if temperature == "hot":
        score = max(score, 80.0)
    elif temperature == "warm":
        score = max(score, 60.0)

    return max(0.0, min(100.0, score))


def _derive_ab_reporting_segment(analysis_result: Dict[str, Any]) -> str:
    priority = str(analysis_result.get("jorge_priority", "normal")).strip().lower()
    temperature = str(analysis_result.get("lead_temperature", "cold")).strip().lower()

    if priority == "high" or temperature == "hot":
        return "hot_priority"
    if priority == "review_required" or temperature == "warm":
        return "warm_review"
    return "standard"


def _assign_ab_response_style_variant(contact_id: str, lead_source: str) -> tuple[str, int]:
    assignment_key = f"{contact_id}:{(lead_source or '').strip().lower()}"
    bucket = int(hashlib.sha256(assignment_key.encode("utf-8")).hexdigest(), 16) % 100
    variant = "A" if bucket < 50 else "B"
    return variant, bucket


def _apply_ab_response_style_testing(
    analysis_result: Dict[str, Any],
    contact_id: str,
    lead_source: str,
    feature_enabled: bool,
    feature_reason: str,
) -> Dict[str, Any]:
    if not isinstance(analysis_result, dict):
        metrics_registry.record_growth_feature_event(
            feature_name=AB_RESPONSE_STYLE_FEATURE,
            event_name="invalid_analysis_payload",
        )
        return {}

    normalized_source = (lead_source or "").strip().lower() or "unknown"
    metrics_registry.record_growth_feature_event(
        feature_name=AB_RESPONSE_STYLE_FEATURE,
        event_name="assignment_observed",
    )

    if not feature_enabled:
        metrics_registry.record_growth_feature_event(
            feature_name=AB_RESPONSE_STYLE_FEATURE,
            event_name=f"bypassed_{feature_reason}",
        )
        return {}

    segment = _derive_ab_reporting_segment(analysis_result)
    variant, bucket = _assign_ab_response_style_variant(
        contact_id=contact_id,
        lead_source=normalized_source,
    )
    variant_metric = "variant_a" if variant == "A" else "variant_b"
    metrics_registry.record_growth_feature_event(
        feature_name=AB_RESPONSE_STYLE_FEATURE,
        event_name=variant_metric,
    )
    metrics_registry.record_growth_feature_event(
        feature_name=AB_RESPONSE_STYLE_FEATURE,
        event_name=f"segment_{segment}",
    )
    metrics_registry.record_growth_feature_event(
        feature_name=AB_RESPONSE_STYLE_FEATURE,
        event_name="applied",
    )

    response_style_context = {
        "variant": variant,
        "segment": segment,
        "bucket": bucket,
        "source": normalized_source,
        "version": WORKSTREAM_G_VERSION,
        "applied_at": datetime.now().isoformat(),
    }
    analysis_result["response_style_experiment"] = response_style_context
    return response_style_context


def _evaluate_sla_handoff_thresholds(
    analysis_result: Dict[str, Any],
    follow_up_data: Any,
    lead_source: str,
    elapsed_processing_ms: float,
    feature_enabled: bool,
    feature_reason: str,
) -> Dict[str, Any]:
    metrics_registry.record_growth_feature_event(
        feature_name=SLA_HANDOFF_THRESHOLDS_FEATURE,
        event_name="observed",
    )

    if not isinstance(analysis_result, dict):
        metrics_registry.record_growth_feature_event(
            feature_name=SLA_HANDOFF_THRESHOLDS_FEATURE,
            event_name="bypassed_invalid_analysis_payload",
        )
        return {}

    if not feature_enabled:
        metrics_registry.record_growth_feature_event(
            feature_name=SLA_HANDOFF_THRESHOLDS_FEATURE,
            event_name=f"bypassed_{feature_reason}",
        )
        return {}

    try:
        lead_score = float(analysis_result.get("lead_score", 0) or 0)
    except (TypeError, ValueError):
        lead_score = 0.0
    priority = str(analysis_result.get("jorge_priority", "normal")).strip().lower()
    timing_bucket = ""
    if isinstance(follow_up_data, dict):
        timing_bucket = str(follow_up_data.get("timing_bucket", "")).strip().lower()
    elapsed_ms = max(0.0, float(elapsed_processing_ms or 0.0))
    normalized_source = (lead_source or "").strip().lower() or "unknown"

    risk_level = "low"
    reason_code = "sla_low_risk"
    needs_handoff = False

    if (
        (priority == "high" and lead_score >= 85)
        or timing_bucket in {"immediate", "accelerated"}
        or (elapsed_ms >= 120000 and priority in {"high", "review_required"})
    ):
        risk_level = "high"
        reason_code = "sla_high_risk_contact_now"
        needs_handoff = True
    elif (
        priority == "review_required"
        or lead_score >= 70
        or timing_bucket == "standard"
        or elapsed_ms >= 60000
    ):
        risk_level = "medium"
        reason_code = "sla_medium_risk_monitor"

    metrics_registry.record_growth_feature_event(
        feature_name=SLA_HANDOFF_THRESHOLDS_FEATURE,
        event_name=f"risk_{risk_level}",
    )
    metrics_registry.record_growth_feature_event(
        feature_name=SLA_HANDOFF_THRESHOLDS_FEATURE,
        event_name="handoff_recommended" if needs_handoff else "handoff_not_required",
    )

    return {
        "needs_handoff": needs_handoff,
        "risk_level": risk_level,
        "reason_code": reason_code,
        "lead_score": round(lead_score, 2),
        "priority": priority,
        "timing_bucket": timing_bucket or "unspecified",
        "elapsed_processing_ms": round(elapsed_ms, 2),
        "lead_source": normalized_source,
        "version": WORKSTREAM_G_VERSION,
        "evaluated_at": datetime.now().isoformat(),
    }


def _apply_adaptive_follow_up_timing(
    follow_up_data: Any,
    analysis_result: Dict[str, Any],
    lead_source: str,
    feature_enabled: bool,
    feature_reason: str,
) -> Any:
    if not isinstance(follow_up_data, dict):
        metrics_registry.record_growth_feature_event(
            feature_name=ADAPTIVE_FOLLOWUP_FEATURE,
            event_name="invalid_payload",
        )
        return follow_up_data

    if not feature_enabled:
        metrics_registry.record_growth_feature_event(
            feature_name=ADAPTIVE_FOLLOWUP_FEATURE,
            event_name=f"bypassed_{feature_reason}",
        )
        return follow_up_data

    engagement_score = _derive_follow_up_engagement_score(analysis_result, follow_up_data)
    if engagement_score >= 85:
        timing_bucket = "immediate"
        delay_minutes = 5
    elif engagement_score >= 70:
        timing_bucket = "accelerated"
        delay_minutes = 30
    elif engagement_score >= 55:
        timing_bucket = "standard"
        delay_minutes = 120
    else:
        timing_bucket = "nurture"
        delay_minutes = 720

    updated_follow_up = dict(follow_up_data)
    updated_follow_up.update(
        {
            "adaptive_timing_applied": True,
            "adaptive_timing_version": WORKSTREAM_G_VERSION,
            "engagement_score": round(engagement_score, 2),
            "timing_bucket": timing_bucket,
            "recommended_delay_minutes": delay_minutes,
            "lead_source": lead_source,
        }
    )

    metrics_registry.record_growth_feature_event(
        feature_name=ADAPTIVE_FOLLOWUP_FEATURE,
        event_name=f"applied_{timing_bucket}",
    )
    return updated_follow_up


# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """Monitor all request performance and 5-minute rule compliance"""

    start_time = time.time()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        process_time = time.time() - start_time
        latency_ms = process_time * 1000.0
        metrics_registry.record_request(
            path=request.url.path,
            latency_ms=latency_ms,
            status_code=status_code,
        )

        if "response" in locals():
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Timestamp"] = datetime.now().isoformat()

        if "/webhook" in str(request.url) or "/analyze-lead" in str(request.url):
            if process_time > 300:
                logger.error(
                    "five_minute_rule_violation endpoint=%s process_time_s=%.3f",
                    request.url,
                    process_time,
                )
            elif process_time > 240:
                logger.warning(
                    "approaching_five_minute_limit endpoint=%s process_time_s=%.3f",
                    request.url,
                    process_time,
                )

        if process_time > 2.0:
            logger.warning(
                "slow_request method=%s path=%s process_time_s=%.3f",
                request.method,
                request.url.path,
                process_time,
            )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancer monitoring"""

    try:
        metrics_snapshot = metrics_registry.snapshot()
        data_dir = Path(__file__).resolve().parent / "data"
        storage_ok = _is_storage_writable(data_dir / "conversations")
        ghl_health_response = ghl_client.check_health()
        ghl_status_code = getattr(ghl_health_response, "status_code", 500)
        ghl_ok = 200 <= int(ghl_status_code) < 400

        status = "healthy"
        if not storage_ok or not ghl_ok:
            status = "degraded"

        health_status = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "services": {
                "fastapi": "running",
                "claude_mode": _claude_mode(),
                "ghl_integration": "connected" if ghl_ok else "degraded",
                "ghl_status_code": ghl_status_code,
                "file_storage_writable": storage_ok,
            },
            "performance": {
                "avg_response_time_ms": metrics_snapshot["rates"]["avg_response_ms"],
                "p95_response_time_ms": metrics_snapshot["counters"]["latency_ms_p95"],
                "five_minute_violations": metrics_snapshot["counters"]["five_minute_violations"],
            },
        }

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# Performance monitoring endpoint
@app.get("/performance", response_model=PerformanceStatus, tags=["Monitoring"])
async def get_performance_metrics():
    """Get current performance metrics and 5-minute rule compliance"""

    try:
        compliance_data = get_five_minute_compliance_status()
        metrics_snapshot = metrics_registry.snapshot()
        window_5m = metrics_snapshot["windows"]["5m"]

        performance_data = PerformanceStatus(
            five_minute_compliance=compliance_data,
            current_performance={
                "avg_response_time_ms": metrics_snapshot["rates"]["avg_response_ms"],
                "p95_response_time_ms": window_5m["latency_ms_p95"],
                "total_requests": metrics_snapshot["counters"]["requests_total"],
                "total_errors": metrics_snapshot["counters"]["errors_total"],
                "compliance_rate": compliance_data.get("compliance_rate", 1.0),
                "violations_24h": len(compliance_data.get("last_24h_violations", [])),
                "cache_hit_rate": metrics_snapshot["rates"]["cache_hit_rate"],
                "ghl_success_rate": metrics_snapshot["rates"]["ghl_success_rate"],
                "webhook_duplicate_count": metrics_snapshot["counters"]["duplicate_webhooks"],
                "signature_failures": metrics_snapshot["counters"]["signature_failures"],
                "five_minute_violations_5m": window_5m["five_minute_violations"],
            },
            system_health={
                "status": (
                    "healthy"
                    if (
                        compliance_data.get("compliance_rate", 0) >= 0.99
                        and window_5m["errors_total"] == 0
                        and window_5m["five_minute_violations"] == 0
                    )
                    else "degraded"
                ),
                "claude_mode": _claude_mode(),
                "ghl_connected": bool(settings.ghl_access_token),
                "cache_hit_rate": metrics_snapshot["rates"]["cache_hit_rate"],
            },
        )

        return performance_data

    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Machine-readable runtime metrics export."""

    return {
        "runtime_metrics": metrics_registry.snapshot(),
        "five_minute_compliance": get_five_minute_compliance_status(),
        "growth_rollout": (
            settings.growth_rollout_config()
            if hasattr(settings, "growth_rollout_config")
            else {}
        ),
    }


# Main lead analysis endpoint
@app.post("/analyze-lead", response_model=LeadAnalysisResponse, tags=["Lead Processing"])
async def analyze_lead(lead_data: LeadMessage, background_tasks: BackgroundTasks):
    """
    Analyze lead message with Jorge's enhanced AI system

    This endpoint provides high-performance lead analysis with <500ms target response time
    """

    start_time = time.time()

    try:
        logger.info(f"Analyzing lead for contact {lead_data.contact_id}")

        # Perform enhanced lead analysis
        analysis_result = await analyze_lead_for_jorge(
            message=lead_data.message,
            contact_id=lead_data.contact_id,
            location_id=lead_data.location_id,
            context=lead_data.contact_data,
            force_ai=lead_data.force_ai_analysis
        )
        _record_analysis_cache_metrics(analysis_result)

        # Generate response message based on analysis
        response_message = await generate_response_message(analysis_result)

        # Schedule background tasks (GHL updates, follow-ups)
        background_tasks.add_task(
            update_ghl_contact,
            lead_data.contact_id,
            lead_data.location_id,
            analysis_result
        )

        # Create structured response
        response = LeadAnalysisResponse(
            success=True,
            lead_score=analysis_result.get("lead_score", 0),
            lead_temperature=analysis_result.get("lead_temperature", "COLD"),
            response_message=response_message,
            jorge_priority=analysis_result.get("jorge_priority", "normal"),
            estimated_commission=analysis_result.get("estimated_commission", 0),
            performance=analysis_result.get("performance", {}),
            actions=analysis_result.get("actions", []),
            follow_up=analysis_result.get("follow_up")
        )

        # Log performance
        process_time = time.time() - start_time
        logger.info(f"Lead analysis completed in {process_time*1000:.0f}ms for contact {lead_data.contact_id}")

        return response

    except Exception as e:
        logger.error(f"Lead analysis failed for contact {lead_data.contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lead analysis failed: {str(e)}")


# GHL webhook endpoint
@app.post("/webhook/ghl", tags=["Webhooks"])
async def handle_ghl_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle GoHighLevel webhook events for immediate lead processing

    This endpoint must respond within 5 minutes to maintain Jorge's conversion rates
    """

    start_time = time.time()
    webhook_id = "unknown_webhook"
    signature_valid = False
    duplicate = False

    try:
        raw_payload = await request.body()
        signature_header = request.headers.get("X-GHL-Signature")
        signature_valid = _verify_webhook_signature(
            payload_bytes=raw_payload,
            signature=signature_header,
            secret=settings.webhook_secret,
        )
        if not signature_valid:
            metrics_registry.record_signature_failure()

        if settings.is_production() and not signature_valid:
            logger.warning(
                "webhook_rejected signature_valid=%s duplicate=%s reason=invalid_signature",
                signature_valid,
                duplicate,
            )
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

        payload_dict = json.loads(raw_payload.decode("utf-8"))
        webhook_data = GHLWebhook.model_validate(payload_dict)
        webhook_id = _extract_webhook_id(payload_dict)
        duplicate = webhook_idempotency_store.check_and_mark(webhook_id)

        logger.info(
            "webhook_received webhook_id=%s signature_valid=%s duplicate=%s type=%s contact_id=%s",
            webhook_id,
            signature_valid,
            duplicate,
            webhook_data.type,
            webhook_data.contact_id,
        )

        if duplicate:
            metrics_registry.record_duplicate_webhook()
            return {
                "status": "duplicate_ignored",
                "webhook_id": webhook_id,
                "duplicate": True,
            }

        # Route different webhook types
        if webhook_data.type in ["contact.created", "message.received", "conversation.new"]:
            result = await handle_lead_webhook(webhook_data, background_tasks)
            result["webhook_id"] = webhook_id
            return result
        elif webhook_data.type in ["contact.updated"]:
            result = await handle_contact_update(webhook_data, background_tasks)
            result["webhook_id"] = webhook_id
            return result
        else:
            logger.info(f"Webhook type {webhook_data.type} not processed")
            return {"status": "acknowledged", "webhook_id": webhook_id, "duplicate": False}

    except ValidationError as e:
        logger.error("Webhook payload validation failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")
    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Webhook processing failed webhook_id=%s signature_valid=%s duplicate=%s error=%s",
            webhook_id,
            signature_valid,
            duplicate,
            e,
        )

        # Return success to GHL to prevent retries, but log error
        return {
            "status": "error_logged",
            "webhook_id": webhook_id,
            "error": str(e),
            "process_time_ms": int((time.time() - start_time) * 1000)
        }


async def handle_lead_webhook(webhook_data: GHLWebhook, background_tasks: BackgroundTasks):
    """Handle new lead or message webhooks"""

    start_time = time.time()

    try:
        # Extract message content
        message = webhook_data.message or "New lead inquiry"

        # Analyze the lead
        analysis_result = await analyze_lead_for_jorge(
            message=message,
            contact_id=webhook_data.contact_id,
            location_id=webhook_data.location_id,
            context=webhook_data.contact
        )
        _record_analysis_cache_metrics(analysis_result)
        lead_source = _extract_lead_source(webhook_data)
        lead_source_attribution_enabled, lead_source_attribution_reason = _evaluate_growth_feature(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            lead_source=lead_source,
        )
        growth_context = _apply_lead_source_attribution_feedback(
            analysis_result=analysis_result,
            lead_source=lead_source,
            feature_enabled=lead_source_attribution_enabled,
            feature_reason=lead_source_attribution_reason,
        )
        ab_style_enabled, ab_style_reason = _evaluate_growth_feature(
            feature_name=AB_RESPONSE_STYLE_FEATURE,
            lead_source=lead_source,
        )
        _apply_ab_response_style_testing(
            analysis_result=analysis_result,
            contact_id=webhook_data.contact_id,
            lead_source=lead_source,
            feature_enabled=ab_style_enabled,
            feature_reason=ab_style_reason,
        )
        adaptive_followup_enabled, adaptive_followup_reason = _evaluate_growth_feature(
            feature_name=ADAPTIVE_FOLLOWUP_FEATURE,
            lead_source=lead_source,
        )
        sla_handoff_enabled, sla_handoff_reason = _evaluate_growth_feature(
            feature_name=SLA_HANDOFF_THRESHOLDS_FEATURE,
            lead_source=lead_source,
        )

        # Generate immediate response if needed
        if analysis_result.get("jorge_priority") == "high":
            background_tasks.add_task(
                send_immediate_response,
                webhook_data.contact_id,
                webhook_data.location_id,
                analysis_result
            )

        # Schedule follow-up if needed
        follow_up_data = analysis_result.get("follow_up")
        has_follow_up_payload = bool(follow_up_data)
        if has_follow_up_payload:
            follow_up_data = _apply_adaptive_follow_up_timing(
                follow_up_data=follow_up_data,
                analysis_result=analysis_result,
                lead_source=lead_source,
                feature_enabled=adaptive_followup_enabled,
                feature_reason=adaptive_followup_reason,
            )
        else:
            metrics_registry.record_growth_feature_event(
                feature_name=ADAPTIVE_FOLLOWUP_FEATURE,
                event_name="no_follow_up_payload",
            )

        sla_handoff_recommendation = _evaluate_sla_handoff_thresholds(
            analysis_result=analysis_result,
            follow_up_data=follow_up_data,
            lead_source=lead_source,
            elapsed_processing_ms=(time.time() - start_time) * 1000.0,
            feature_enabled=sla_handoff_enabled,
            feature_reason=sla_handoff_reason,
        )
        if sla_handoff_recommendation.get("needs_handoff"):
            analysis_result["sla_handoff"] = sla_handoff_recommendation
            actions = analysis_result.get("actions")
            if not isinstance(actions, list):
                actions = []
            actions.append(
                {
                    "type": "human_handoff",
                    "reason_code": sla_handoff_recommendation.get("reason_code", "sla_high_risk_contact_now"),
                    "risk_level": sla_handoff_recommendation.get("risk_level", "high"),
                    "version": WORKSTREAM_G_VERSION,
                }
            )
            analysis_result["actions"] = actions

            if isinstance(follow_up_data, dict):
                follow_up_enriched = dict(follow_up_data)
                metadata = dict(follow_up_enriched.get("metadata", {}))
                metadata.update(
                    {
                        "needs_handoff": True,
                        "handoff_reason_code": sla_handoff_recommendation.get("reason_code"),
                        "handoff_risk_level": sla_handoff_recommendation.get("risk_level"),
                    }
                )
                follow_up_enriched["metadata"] = metadata
                follow_up_data = follow_up_enriched

        # Update GHL contact with final analysis payload
        background_tasks.add_task(
            update_ghl_contact,
            webhook_data.contact_id,
            webhook_data.location_id,
            analysis_result,
            growth_context,
        )

        if has_follow_up_payload:
            background_tasks.add_task(
                schedule_follow_up,
                webhook_data.contact_id,
                follow_up_data,
            )

        process_time = time.time() - start_time

        return {
            "status": "processed",
            "lead_score": analysis_result.get("lead_score"),
            "jorge_priority": analysis_result.get("jorge_priority"),
            "estimated_commission": analysis_result.get("estimated_commission"),
            "process_time_ms": int(process_time * 1000),
            "five_minute_compliant": process_time < 300
        }

    except Exception as e:
        logger.error(f"Lead webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_contact_update(webhook_data: GHLWebhook, background_tasks: BackgroundTasks):
    """Handle contact update webhooks"""

    lead_source = _extract_lead_source(webhook_data)
    attribution_enabled, attribution_reason = _evaluate_growth_feature(
        feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
        lead_source=lead_source,
    )
    conversion_outcome = _derive_conversion_feedback_outcome(webhook_data.contact)
    metrics_registry.record_growth_feature_event(
        feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
        event_name=f"conversion_feedback_observed_{conversion_outcome}",
    )
    if not attribution_enabled:
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name=f"conversion_feedback_bypassed_{attribution_reason}",
        )
    elif getattr(settings, "ff_growth_conversion_feedback_writeback", False):
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name=f"conversion_feedback_loop_{conversion_outcome}",
        )
    else:
        metrics_registry.record_growth_feature_event(
            feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
            event_name="conversion_feedback_telemetry_only",
        )

    return {
        "status": "acknowledged",
        "note": "Contact update processed"
    }


# Background task functions
async def generate_response_message(analysis_result: Dict) -> str:
    """Generate appropriate response message based on analysis"""

    try:
        # Use AI insights if available
        ai_insights = analysis_result.get("ai_insights", {})
        tone = ai_insights.get("recommended_response_tone", "professional")

        # Jorge's business context responses
        if analysis_result.get("jorge_priority") == "high":
            base_message = (
                "Thanks for reaching out! Your inquiry looks like a great fit for our current market. "
                "I'd love to discuss your goals in detail - when would be a good time for a quick call today or tomorrow?"
            )
        elif analysis_result.get("jorge_priority") == "review_required":
            base_message = (
                "Thank you for your inquiry! Based on your requirements, I'll review some specific options "
                "and get back to you within 24 hours with tailored recommendations."
            )
        else:
            base_message = (
                "Thanks for your interest! I'd be happy to help you with your real estate needs. "
                "Let me know if you have any questions about the current market."
            )

        style_context = analysis_result.get("response_style_experiment", {})
        if isinstance(style_context, dict) and style_context.get("variant") == "B":
            return f"{base_message} If it's easier, I can text over two quick options to compare first."
        return base_message

    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return "Thanks for your message! I'll get back to you shortly."


async def update_ghl_contact(
    contact_id: str,
    location_id: str,
    analysis_result: Dict,
    growth_context: Optional[Dict[str, Any]] = None,
):
    """Update GHL contact with analysis results"""

    try:
        # Prepare custom field updates
        updates = {
            "ai_lead_score": analysis_result.get("lead_score", 0),
            "lead_temperature": analysis_result.get("lead_temperature", "COLD"),
            "jorge_priority": analysis_result.get("jorge_priority", "normal"),
            "estimated_commission": analysis_result.get("estimated_commission", 0),
            "last_ai_analysis": datetime.now().isoformat()
        }

        if isinstance(growth_context, dict) and growth_context:
            attribution = growth_context.get("attribution", {})
            conversion_feedback = growth_context.get("conversion_feedback", {})

            if getattr(settings, "ff_growth_lead_source_writeback", False):
                updates.update(
                    {
                        "lead_source_attribution": attribution.get("source", "unknown"),
                        "lead_source_model": attribution.get("model", "last_touch"),
                    }
                )
                metrics_registry.record_growth_feature_event(
                    feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
                    event_name="writeback_attribution_enabled",
                )
            else:
                metrics_registry.record_growth_feature_event(
                    feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
                    event_name="writeback_attribution_disabled",
                )

            if getattr(settings, "ff_growth_conversion_feedback_writeback", False):
                updates.update(
                    {
                        "conversion_feedback_state": conversion_feedback.get("status", "pending"),
                        "conversion_feedback_signal": conversion_feedback.get("signal", "unknown"),
                        "conversion_feedback_updated_at": datetime.now().isoformat(),
                    }
                )
                metrics_registry.record_growth_feature_event(
                    feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
                    event_name="writeback_feedback_enabled",
                )
            else:
                metrics_registry.record_growth_feature_event(
                    feature_name=LEAD_SOURCE_ATTRIBUTION_FEATURE,
                    event_name="writeback_feedback_disabled",
                )

        # Add Jorge-specific validation results
        meets_jorge_criteria = analysis_result.get("meets_jorge_criteria", False)
        if analysis_result.get("jorge_validation"):
            validation = analysis_result["jorge_validation"]
            meets_jorge_criteria = validation.get("passes_jorge_criteria", False)
            updates.update({
                "meets_jorge_criteria": meets_jorge_criteria,
                "service_area_match": validation.get("service_area_match", False)
            })

        # Update contact in GHL
        updates_applied = await ghl_client.update_contact_custom_fields(contact_id, updates)
        metrics_registry.record_ghl_call(success=updates_applied)
        if not updates_applied:
            logger.error("GHL custom field update failed for contact %s", contact_id)

        # Add appropriate tags
        tags_to_add = []
        if analysis_result.get("jorge_priority") == "high":
            tags_to_add.append("Priority-High")
        if analysis_result.get("lead_temperature") == "HOT":
            tags_to_add.append("Hot-Lead")
        if meets_jorge_criteria:
            tags_to_add.append("Jorge-Qualified")
        if analysis_result.get("sla_handoff", {}).get("needs_handoff") is True:
            tags_to_add.append("Needs-Handoff-SLA")
        if (
            isinstance(growth_context, dict)
            and growth_context
            and getattr(settings, "ff_growth_conversion_feedback_writeback", False)
        ):
            feedback_signal = str(
                growth_context.get("conversion_feedback", {}).get("signal", "")
            ).strip().lower()
            if feedback_signal == "high_intent":
                tags_to_add.append("Conversion-Signal-High-Intent")

        if tags_to_add:
            tags_applied = await ghl_client.add_contact_tags(contact_id, tags_to_add)
            metrics_registry.record_ghl_call(success=tags_applied)
            if not tags_applied:
                logger.error("GHL tag update failed for contact %s tags=%s", contact_id, tags_to_add)

        logger.info(f"Updated GHL contact {contact_id} with analysis results")

    except Exception as e:
        metrics_registry.record_ghl_call(success=False)
        logger.error(f"Failed to update GHL contact {contact_id}: {e}")


async def send_immediate_response(contact_id: str, location_id: str, analysis_result: Dict):
    """Send immediate response for high-priority leads"""

    try:
        response_message = await generate_response_message(analysis_result)

        # Send message via GHL
        send_result = await ghl_client.send_message(contact_id, response_message)
        metrics_registry.record_ghl_call(success=bool(send_result))

        logger.info(f"Sent immediate response to high-priority lead {contact_id}")

    except Exception as e:
        metrics_registry.record_ghl_call(success=False)
        logger.error(f"Failed to send immediate response to {contact_id}: {e}")


async def schedule_follow_up(contact_id: str, follow_up_data: Dict):
    """Schedule follow-up tasks"""

    try:
        # This would integrate with Jorge's scheduling system
        logger.info(f"Follow-up scheduled for contact {contact_id}: {follow_up_data}")

    except Exception as e:
        logger.error(f"Failed to schedule follow-up for {contact_id}: {e}")


# Development/testing endpoints
@app.post("/test/analyze", tags=["Testing"])
async def test_lead_analysis(message: str = "I want to buy a house for $700k in Plano"):
    """Test endpoint for lead analysis (development only)"""

    return await analyze_lead_for_jorge(
        message=message,
        contact_id="test_contact_123",
        location_id="test_location_456",
        force_ai=True
    )


if __name__ == "__main__":
    # Run the FastAPI server
    logger.info("🚀 Starting Jorge's Lead Bot FastAPI Microservice...")
    logger.info("📊 Performance Targets: <500ms lead analysis, 5-minute rule compliance")

    uvicorn.run(
        "jorge_fastapi_lead_bot:app",
        host="0.0.0.0",
        port=8001,
        reload=True,  # Development mode
        log_level="info",
        access_log=True
    )
