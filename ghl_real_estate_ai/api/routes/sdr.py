"""
SDR Agent API Routes.

Provides endpoints for:
- Inbound GHL webhook processing (reply, opt-out, stage change, booking)
- Prospect sourcing and enrollment
- Sequence inspection and disenrollment
- Cron batch processing of due touches
- SDR performance statistics
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ghl_real_estate_ai.agents.sdr.sdr_agent import SDRAgent
from ghl_real_estate_ai.database.session import get_db
from ghl_real_estate_ai.models.sdr_models import (
    SDRBatchProcessResult,
    SDREnrollRequest,
    SDRProspectResponse,
    SDRStatsResponse,
    SDRWebhookPayload,
)
from ghl_real_estate_ai.repositories.sdr_repository import SDRRepository
from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient
from ghl_real_estate_ai.services.sdr.cadence_scheduler import CadenceScheduler
from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import OutreachSequenceEngine
from ghl_real_estate_ai.services.sdr.performance_tracker import SDRPerformanceTracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sdr", tags=["sdr"])

# ---------------------------------------------------------------------------
# Module-level service instances (fire-and-forget pattern, matches jorge_followup)
# ---------------------------------------------------------------------------

_ghl_client = EnhancedGHLClient()
_sequence_engine = OutreachSequenceEngine(ghl_client=_ghl_client)
_scheduler = CadenceScheduler(sequence_engine=_sequence_engine)
_sdr_agent = SDRAgent(ghl_client=_ghl_client)


# ===========================================================================
# Webhook endpoints
# ===========================================================================


@router.post("/webhook/reply")
async def webhook_contact_reply(
    payload: SDRWebhookPayload,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    Handle a GHL ContactReply webhook.

    Processes the reply in the background so GHL does not time out.
    SDRAgent classifies objections, advances the sequence, and gates qualification.
    """
    if not payload.contact_id or not payload.location_id:
        raise HTTPException(status_code=400, detail="Missing contact_id or location_id")

    logger.info(
        f"[SDR] /webhook/reply contact={payload.contact_id} channel={payload.channel} location={payload.location_id}"
    )

    background_tasks.add_task(
        _sdr_agent.process_inbound_reply,
        contact_id=payload.contact_id,
        message=payload.message_body or "",
        channel=payload.channel or "sms",
        location_id=payload.location_id,
    )

    return {"status": "accepted", "message": "Reply processing initiated"}


@router.post("/webhook/opt-out")
async def webhook_opt_out(
    payload: SDRWebhookPayload,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """Handle a GHL DND/stop webhook — marks contact opted-out."""
    if not payload.contact_id or not payload.location_id:
        raise HTTPException(status_code=400, detail="Missing contact_id or location_id")

    logger.info(f"[SDR] /webhook/opt-out contact={payload.contact_id}")

    # Treat as an inbound "stop" message so ObjectionHandler processes it
    background_tasks.add_task(
        _sdr_agent.process_inbound_reply,
        contact_id=payload.contact_id,
        message="stop texting",
        channel=payload.channel or "sms",
        location_id=payload.location_id,
    )

    return {"status": "accepted", "message": "Opt-out processing initiated"}


@router.post("/webhook/booking-confirmed")
async def webhook_booking_confirmed(
    payload: SDRWebhookPayload,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    Handle a GHL AppointmentScheduled webhook.

    Triggers gate evaluation and Jorge handoff if the contact qualifies.
    """
    if not payload.contact_id or not payload.location_id:
        raise HTTPException(status_code=400, detail="Missing contact_id or location_id")

    logger.info(f"[SDR] /webhook/booking-confirmed contact={payload.contact_id}")

    background_tasks.add_task(
        _sdr_agent.evaluate_and_handoff,
        contact_id=payload.contact_id,
        location_id=payload.location_id,
    )

    return {"status": "accepted", "message": "Booking evaluation initiated"}


@router.post("/webhook/stage-change")
async def webhook_stage_change(
    payload: SDRWebhookPayload,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    Handle a GHL pipeline stage-change webhook.

    Delegates to CadenceScheduler.process_webhook_trigger for scheduling logic.
    """
    if not payload.contact_id or not payload.location_id:
        raise HTTPException(status_code=400, detail="Missing contact_id or location_id")

    logger.info(f"[SDR] /webhook/stage-change contact={payload.contact_id} stage={payload.pipeline_stage_id}")

    background_tasks.add_task(
        _scheduler.process_webhook_trigger,
        contact_id=payload.contact_id,
        location_id=payload.location_id,
        trigger_type="stage_change",
        webhook_data=payload.model_dump(),
    )

    return {"status": "accepted", "message": "Stage change processing initiated"}


# ===========================================================================
# Prospect endpoints
# ===========================================================================


@router.post("/prospects/source")
async def trigger_prospecting_cycle(
    location_id: str,
    background_tasks: BackgroundTasks,
    max_per_source: int = Query(default=50, ge=1, le=200),
) -> Dict[str, str]:
    """
    Trigger a full prospecting cycle for a location.

    Pulls prospects from GHL_PIPELINE + STALE_LEAD sources and enrolls them.
    Runs in background to avoid timeouts on large pipelines.
    """
    logger.info(f"[SDR] /prospects/source location={location_id} max_per_source={max_per_source}")

    background_tasks.add_task(
        _sdr_agent.run_prospecting_cycle,
        location_id=location_id,
        max_per_source=max_per_source,
    )

    return {"status": "accepted", "message": "Prospecting cycle initiated"}


@router.post("/prospects/enroll")
async def enroll_prospects(
    request: SDREnrollRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Manually enroll one or more contacts in the SDR sequence.

    Dispatches SMS_1 immediately for each contact.
    """
    logger.info(f"[SDR] /prospects/enroll count={len(request.contact_ids)} location={request.location_id}")

    enrolled = []
    errors = []
    for contact_id in request.contact_ids:
        try:
            await _sequence_engine.enroll_prospect(
                contact_id=contact_id,
                location_id=request.location_id,
                lead_type=request.lead_type,
            )
            enrolled.append(contact_id)
        except Exception as exc:
            logger.error(f"[SDR] Enroll failed contact={contact_id}: {exc}")
            errors.append({"contact_id": contact_id, "error": str(exc)})

    return {
        "enrolled": enrolled,
        "errors": errors,
        "total_enrolled": len(enrolled),
    }


@router.get("/prospects/{contact_id}")
async def get_prospect(
    contact_id: str,
    location_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> SDRProspectResponse:
    """Return the SDR profile and current sequence state for a contact."""
    repo = SDRRepository(db)
    prospect = await repo.get_prospect_by_contact(contact_id, location_id)
    if prospect is None:
        raise HTTPException(status_code=404, detail="Prospect not found")

    seq = await repo.get_active_sequence(contact_id, location_id)
    return SDRProspectResponse(
        contact_id=prospect.contact_id,
        location_id=prospect.location_id,
        source=prospect.source,
        lead_type=prospect.lead_type,
        frs_score=prospect.frs_score,
        pcs_score=prospect.pcs_score,
        enrolled_at=prospect.enrolled_at,
        current_step=seq.current_step if seq else None,
        next_touch_at=seq.next_touch_at if seq else None,
        reply_count=seq.reply_count if seq else 0,
    )


# ===========================================================================
# Sequence endpoints
# ===========================================================================


@router.get("/sequences/{contact_id}")
async def get_sequence(
    contact_id: str,
    location_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Inspect the current sequence state and touch history for a contact."""
    repo = SDRRepository(db)
    seq = await repo.get_active_sequence(contact_id, location_id)
    if seq is None:
        raise HTTPException(status_code=404, detail="No active sequence found")

    touches = await repo.get_touches_for_sequence(seq.id)
    return {
        "sequence_id": seq.id,
        "contact_id": seq.contact_id,
        "location_id": seq.location_id,
        "current_step": seq.current_step,
        "next_touch_at": seq.next_touch_at.isoformat() if seq.next_touch_at else None,
        "reply_count": seq.reply_count,
        "ab_variant": seq.ab_variant,
        "enrolled_at": seq.enrolled_at.isoformat(),
        "touches": [
            {
                "id": t.id,
                "step": t.step,
                "channel": t.channel,
                "sent_at": t.sent_at.isoformat(),
                "replied_at": t.replied_at.isoformat() if t.replied_at else None,
            }
            for t in touches
        ],
    }


@router.delete("/sequences/{contact_id}")
async def disenroll_contact(contact_id: str, location_id: str) -> Dict[str, str]:
    """
    Manually disenroll a contact from their active SDR sequence.

    Sends an opt-out signal via process_inbound_reply to ensure
    GHL tags are applied and the sequence stops cleanly.
    """
    logger.info(f"[SDR] Manual disenroll contact={contact_id}")

    await _sdr_agent.process_inbound_reply(
        contact_id=contact_id,
        message="not interested",
        channel="sms",
        location_id=location_id,
    )

    return {"status": "disenrolled", "contact_id": contact_id}


# ===========================================================================
# Batch / cron endpoint
# ===========================================================================


@router.post("/sequences/process-batch")
async def process_batch(
    batch_size: int = Query(default=50, ge=1, le=200),
    location_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> SDRBatchProcessResult:
    """
    Process a batch of due outreach touches.

    Called by a 15-minute cron job. Queries DB for sequences where
    next_touch_at <= now and dispatches the next touch for each.
    """
    start = time.monotonic()
    logger.info(f"[SDR] /sequences/process-batch size={batch_size} location={location_id}")

    repo = SDRRepository(db)
    scheduler = CadenceScheduler(sequence_engine=_sequence_engine, repository=repo)
    stats = await scheduler.fetch_and_process_due_touches(batch_size=batch_size)

    duration_ms = (time.monotonic() - start) * 1000
    return SDRBatchProcessResult(
        processed=stats.get("processed", 0),
        dispatched=stats.get("dispatched", 0),
        skipped=stats.get("skipped", 0),
        errors=stats.get("errors", 0),
        duration_ms=round(duration_ms, 2),
    )


# ===========================================================================
# Stats endpoints
# ===========================================================================


@router.get("/stats", response_model=SDRStatsResponse)
async def get_stats(
    location_id: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> SDRStatsResponse:
    """Return SDR performance statistics via SDRPerformanceTracker rolling windows."""
    repo = SDRRepository(db)
    tracker = SDRPerformanceTracker(repo)
    return await tracker.get_stats(location_id=location_id, days=days)


@router.get("/stats/sequences")
async def get_sequence_stats(
    location_id: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Per-sequence step-by-step conversion funnel."""
    repo = SDRRepository(db)
    tracker = SDRPerformanceTracker(repo)
    funnel = await tracker.get_sequence_funnel(location_id=location_id, days=days)
    return {"location_id": location_id, "days": days, "funnel": funnel}


@router.get("/stats/objections")
async def get_objection_stats(
    location_id: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Objection type distribution and per-type rates."""
    repo = SDRRepository(db)
    tracker = SDRPerformanceTracker(repo)
    return await tracker.get_objection_analytics(location_id=location_id, days=days)
