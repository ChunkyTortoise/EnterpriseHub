"""
SDR ProspectSourcer — pulls prospects from GHL pipeline and stale lead sources.

Phase 1: GHL_PIPELINE + STALE_LEAD sources only.
Phase 2 will add: EXPIRED_MLS, FSBO via SimulatedMLSFeed.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

logger = get_logger(__name__)


class ProspectSource(Enum):
    """Sources from which the SDR can pull prospects."""

    GHL_PIPELINE = "ghl_pipeline"
    EXPIRED_MLS = "expired_mls"    # Phase 2
    FSBO = "fsbo"                  # Phase 2
    STALE_LEAD = "stale_lead"


@dataclass
class ProspectProfile:
    """Lightweight prospect record built from GHL + optional MLS data."""

    contact_id: str
    location_id: str
    source: ProspectSource
    lead_type: str              # "buyer" | "seller" | "unknown"
    property_address: Optional[str]
    days_in_stage: int
    last_activity: Optional[datetime]
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    mls_data: Optional[Dict[str, Any]] = field(default=None)


class ProspectSourcer:
    """
    Aggregates prospects from configured sources and deduplicates by contact_id.

    Phase 1 sources:
    - GHL_PIPELINE: contacts in specific pipeline stage IDs
    - STALE_LEAD: contacts with no activity in N days
    """

    def __init__(
        self,
        ghl_client: "EnhancedGHLClient",
    ) -> None:
        self._ghl = ghl_client
        self._pipeline_stage_ids: List[str] = [
            s.strip()
            for s in os.getenv("SDR_PIPELINE_STAGE_IDS", "").split(",")
            if s.strip()
        ]

    async def fetch_prospects(
        self,
        location_id: str,
        sources: Optional[List[ProspectSource]] = None,
        max_per_source: int = 50,
    ) -> List[ProspectProfile]:
        """
        Pull prospects from all requested sources, deduplicate by contact_id.

        Args:
            location_id: GHL location to scope the search
            sources: which sources to pull from (defaults to [GHL_PIPELINE, STALE_LEAD])
            max_per_source: max contacts per source to avoid runaway GHL calls

        Returns:
            Deduplicated list of ProspectProfile
        """
        if sources is None:
            sources = [ProspectSource.GHL_PIPELINE, ProspectSource.STALE_LEAD]

        tasks = []
        for source in sources:
            if source == ProspectSource.GHL_PIPELINE:
                tasks.append(self._fetch_ghl_pipeline_leads(location_id, max_per_source))
            elif source == ProspectSource.STALE_LEAD:
                tasks.append(self._fetch_stale_leads(location_id, max_per_source))
            else:
                logger.warning(f"[SDR] Source {source.value} not yet implemented (Phase 2)")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        seen_ids: set = set()
        prospects: List[ProspectProfile] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[SDR] ProspectSourcer task failed: {result}")
                continue
            for p in result:
                if p.contact_id not in seen_ids:
                    seen_ids.add(p.contact_id)
                    prospects.append(p)

        logger.info(
            f"[SDR] ProspectSourcer fetched {len(prospects)} unique prospects "
            f"from {len(sources)} source(s) for location={location_id}"
        )
        return prospects

    async def _fetch_ghl_pipeline_leads(
        self, location_id: str, limit: int
    ) -> List[ProspectProfile]:
        """Pull contacts from configured GHL pipeline stage IDs."""
        if not self._pipeline_stage_ids:
            logger.info("[SDR] No SDR_PIPELINE_STAGE_IDS configured, skipping pipeline source")
            return []

        prospects: List[ProspectProfile] = []
        for stage_id in self._pipeline_stage_ids:
            try:
                contacts = await self._ghl.get_contacts_by_pipeline_stage(
                    location_id=location_id,
                    stage_id=stage_id,
                    limit=limit,
                )
                for c in contacts:
                    prospects.append(
                        ProspectProfile(
                            contact_id=c.id,
                            location_id=location_id,
                            source=ProspectSource.GHL_PIPELINE,
                            lead_type=_infer_lead_type(c.tags),
                            property_address=c.custom_fields.get("property_address"),
                            days_in_stage=_days_since(c.updated_at),
                            last_activity=c.last_activity_at,
                            custom_fields=c.custom_fields,
                        )
                    )
            except Exception as exc:
                logger.error(f"[SDR] Pipeline stage {stage_id} fetch failed: {exc}")

        return prospects

    async def _fetch_stale_leads(
        self, location_id: str, limit: int, inactive_days: int = 14
    ) -> List[ProspectProfile]:
        """Pull contacts with no activity in the last N days."""
        since = datetime.now(timezone.utc) - timedelta(days=inactive_days)
        try:
            contacts = await self._ghl.get_contacts_inactive_since(
                location_id=location_id, since=since, limit=limit
            )
        except Exception as exc:
            logger.error(f"[SDR] Stale lead fetch failed: {exc}")
            return []

        return [
            ProspectProfile(
                contact_id=c.id,
                location_id=location_id,
                source=ProspectSource.STALE_LEAD,
                lead_type=_infer_lead_type(c.tags),
                property_address=c.custom_fields.get("property_address"),
                days_in_stage=0,
                last_activity=c.last_activity_at,
                custom_fields=c.custom_fields,
            )
            for c in contacts
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _infer_lead_type(tags: List[str]) -> str:
    """Guess buyer/seller from GHL tags. Returns 'unknown' if ambiguous."""
    tags_lower = {t.lower() for t in tags}
    if "buyer" in tags_lower or "pre-approved-buyer" in tags_lower:
        return "buyer"
    if "seller" in tags_lower or "urgent-seller" in tags_lower:
        return "seller"
    return "unknown"


def _days_since(dt: Optional[datetime]) -> int:
    if dt is None:
        return 0
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)
