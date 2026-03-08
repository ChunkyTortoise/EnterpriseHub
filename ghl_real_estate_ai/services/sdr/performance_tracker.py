"""
SDR Performance Tracker — rolling-window analytics from DB aggregation.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.models.sdr_models import SDRStatsResponse
from ghl_real_estate_ai.repositories.sdr_repository import SDRRepository


class SDRPerformanceTracker:
    """Computes rolling-window SDR metrics from the repository aggregation methods."""

    def __init__(self, repository: SDRRepository) -> None:
        self._repo = repository

    async def get_stats(
        self,
        location_id: Optional[str] = None,
        days: int = 30,
    ) -> SDRStatsResponse:
        """Return aggregate SDR performance metrics for the given window."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        enrolled = await self._repo.count_enrolled(location_id, since)
        touches_sent = await self._repo.count_touches_sent(location_id, since)
        replies_received = await self._repo.count_replies(location_id, since)
        reply_rate = (replies_received / touches_sent) if touches_sent > 0 else 0.0
        by_step = await self._repo.count_by_step(location_id, since)
        objections = await self._repo.objection_distribution(location_id, since)
        return SDRStatsResponse(
            window=f"{days}d",
            enrolled=enrolled,
            touches_sent=touches_sent,
            replies_received=replies_received,
            reply_rate=round(reply_rate, 4),
            objections_handled=sum(objections.values()),
            qualified_leads=by_step.get("qualified", 0),
            appointments_booked=by_step.get("booked", 0),
            cost_per_qualified=None,
            conversion_by_step=by_step,
        )

    async def get_sequence_funnel(
        self,
        location_id: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Return step-by-step conversion counts in canonical sequence order."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        by_step = await self._repo.count_by_step(location_id, since)
        step_order = [
            "enrolled", "sms_1", "email_1", "sms_2", "voicemail_1",
            "email_2", "sms_3", "voicemail_2", "nurture_pause",
            "qualified", "booked", "disqualified", "opted_out",
        ]
        return [{"step": s, "count": by_step.get(s, 0)} for s in step_order]

    async def get_objection_analytics(
        self,
        location_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Return objection type distribution and per-type rates."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        distribution = await self._repo.objection_distribution(location_id, since)
        total = sum(distribution.values())
        return {
            "total": total,
            "distribution": distribution,
            "rates": {
                k: round(v / total, 4) if total > 0 else 0.0
                for k, v in distribution.items()
            },
        }
