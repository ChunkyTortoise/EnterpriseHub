"""
Lead Source Tracker

Tracks lead source attribution and conversion funnel metrics from GHL contact data.
Monitors the conversion journey: contact → qualified → appointment → close.

Usage:
    tracker = SourceTracker()
    await tracker.track_contact(ghl_contact)
    await tracker.track_conversion(contact_id, stage="qualified")
    metrics = await tracker.get_source_metrics(source_name="Facebook Ads")
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.service_types import LeadProfile

logger = get_logger(__name__)


class ConversionStage:
    """Conversion funnel stages."""

    CONTACT = "contact"
    QUALIFIED = "qualified"
    APPOINTMENT = "appointment"
    SHOWING = "showing"
    OFFER = "offer"
    CLOSE = "close"


class SourceTracker:
    """Tracks lead source performance and conversion funnel metrics.

    Integrates with GHL contact data to monitor source attribution,
    conversion rates at each stage, and revenue when available.
    """

    def __init__(self, db_service: Optional[Any] = None):
        """Initialize source tracker.

        Args:
            db_service: Optional database service for persistence
        """
        self._db_service = db_service
        self._initialized = True
        logger.info("SourceTracker initialized")

    async def track_contact(
        self,
        contact_id: str,
        source: Optional[str],
        tags: List[str] = None,
        custom_fields: Optional[LeadProfile] = None,
    ) -> None:
        """Track a new contact and their source attribution.

        Args:
            contact_id: GHL contact ID
            source: Lead source (e.g., "Facebook Ads", "Google", "Referral")
            tags: Contact tags from GHL
            custom_fields: Custom fields from GHL
        """
        if not self._db_service:
            logger.warning("No database service configured, skipping persistence")
            return

        source_normalized = self._normalize_source(source)

        try:
            await self._db_service.execute(
                """
                INSERT INTO lead_source_contacts
                (contact_id, source_name, tags, custom_fields, stage, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (contact_id) DO UPDATE
                SET source_name = EXCLUDED.source_name,
                    tags = EXCLUDED.tags,
                    custom_fields = EXCLUDED.custom_fields,
                    updated_at = NOW()
                """,
                contact_id,
                source_normalized,
                tags or [],
                custom_fields or {},
                ConversionStage.CONTACT,
            )
            logger.debug(f"Tracked contact {contact_id} from source {source_normalized}")
        except Exception as e:
            logger.error(f"Error tracking contact: {e}", exc_info=True)

    async def track_conversion(
        self,
        contact_id: str,
        stage: str,
        revenue: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track conversion to a new funnel stage.

        Args:
            contact_id: GHL contact ID
            stage: Conversion stage (qualified, appointment, showing, offer, close)
            revenue: Deal value for closed deals
            metadata: Additional metadata (deal_id, opportunity_id, etc.)
        """
        if not self._db_service:
            logger.warning("No database service configured, skipping persistence")
            return

        try:
            # Update contact stage
            await self._db_service.execute(
                """
                UPDATE lead_source_contacts
                SET stage = $2,
                    revenue = $3,
                    metadata = metadata || $4,
                    updated_at = NOW()
                WHERE contact_id = $1
                """,
                contact_id,
                stage,
                revenue,
                metadata or {},
            )

            # Record conversion event
            await self._db_service.execute(
                """
                INSERT INTO lead_source_conversions
                (contact_id, stage, revenue, metadata, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                """,
                contact_id,
                stage,
                revenue,
                metadata or {},
            )

            logger.debug(f"Tracked conversion for {contact_id} to stage {stage}")
        except Exception as e:
            logger.error(f"Error tracking conversion: {e}", exc_info=True)

    async def get_source_metrics(
        self,
        source_name: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get conversion metrics for a specific source.

        Args:
            source_name: Source to query (None for all sources)
            days: Time window in days

        Returns:
            Dict containing:
                - total_contacts: Number of contacts from source
                - qualified_leads: Number who reached qualified stage
                - appointments: Number who scheduled appointments
                - showings: Number who completed showings
                - offers: Number who made offers
                - closed_deals: Number of closed deals
                - conversion_rate: Overall conversion rate (close/contact)
                - total_revenue: Sum of revenue from closed deals
                - avg_deal_value: Average deal value
        """
        if not self._db_service:
            logger.warning("No database service configured")
            return self._mock_metrics()

        try:
            since_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT
                    source_name,
                    COUNT(*) as total_contacts,
                    COUNT(*) FILTER (WHERE stage IN ('qualified', 'appointment', 'showing', 'offer', 'close')) as qualified_leads,
                    COUNT(*) FILTER (WHERE stage IN ('appointment', 'showing', 'offer', 'close')) as appointments,
                    COUNT(*) FILTER (WHERE stage IN ('showing', 'offer', 'close')) as showings,
                    COUNT(*) FILTER (WHERE stage IN ('offer', 'close')) as offers,
                    COUNT(*) FILTER (WHERE stage = 'close') as closed_deals,
                    SUM(revenue) FILTER (WHERE stage = 'close') as total_revenue,
                    AVG(revenue) FILTER (WHERE stage = 'close') as avg_deal_value
                FROM lead_source_contacts
                WHERE created_at >= $1
            """

            params = [since_date]

            if source_name:
                query += " AND source_name = $2"
                params.append(source_name)

            query += " GROUP BY source_name"

            rows = await self._db_service.fetch(query, *params)

            results = []
            for row in rows:
                total_contacts = row["total_contacts"] or 0
                closed_deals = row["closed_deals"] or 0
                conversion_rate = (closed_deals / total_contacts * 100) if total_contacts > 0 else 0.0

                results.append({
                    "source_name": row["source_name"],
                    "total_contacts": total_contacts,
                    "qualified_leads": row["qualified_leads"] or 0,
                    "appointments": row["appointments"] or 0,
                    "showings": row["showings"] or 0,
                    "offers": row["offers"] or 0,
                    "closed_deals": closed_deals,
                    "conversion_rate": round(conversion_rate, 2),
                    "total_revenue": float(row["total_revenue"] or 0),
                    "avg_deal_value": float(row["avg_deal_value"] or 0),
                })

            if source_name and results:
                return results[0]

            return {"sources": results, "total_sources": len(results)}

        except Exception as e:
            logger.error(f"Error fetching source metrics: {e}", exc_info=True)
            return self._mock_metrics()

    async def get_top_sources(
        self,
        by: str = "conversion_rate",
        limit: int = 10,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get top performing sources.

        Args:
            by: Metric to sort by (conversion_rate, total_revenue, closed_deals)
            limit: Number of top sources to return
            days: Time window in days

        Returns:
            List of source metrics sorted by specified metric
        """
        metrics = await self.get_source_metrics(days=days)

        if not metrics or "sources" not in metrics:
            return []

        sources = metrics["sources"]

        # Sort by specified metric
        if by == "conversion_rate":
            sources.sort(key=lambda x: x["conversion_rate"], reverse=True)
        elif by == "total_revenue":
            sources.sort(key=lambda x: x["total_revenue"], reverse=True)
        elif by == "closed_deals":
            sources.sort(key=lambda x: x["closed_deals"], reverse=True)
        else:
            logger.warning(f"Unknown sort metric: {by}, defaulting to conversion_rate")
            sources.sort(key=lambda x: x["conversion_rate"], reverse=True)

        return sources[:limit]

    async def update_source_metrics_table(self) -> None:
        """Update the aggregated source metrics table.

        This method aggregates current data and updates the lead_source_metrics
        table used by the dashboard. Should be called periodically (e.g., daily).
        """
        if not self._db_service:
            logger.warning("No database service configured")
            return

        try:
            # Get all source metrics for last 30 days
            all_metrics = await self.get_source_metrics(days=30)

            if not all_metrics or "sources" not in all_metrics:
                logger.warning("No source metrics to update")
                return

            # Update metrics table for each source
            for source_data in all_metrics["sources"]:
                await self._db_service.execute(
                    """
                    INSERT INTO lead_source_metrics
                    (source_name, total_leads, qualified_leads, appointments,
                     closed_deals, total_revenue, avg_deal_value, conversion_rate, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    ON CONFLICT (source_name) DO UPDATE
                    SET total_leads = EXCLUDED.total_leads,
                        qualified_leads = EXCLUDED.qualified_leads,
                        appointments = EXCLUDED.appointments,
                        closed_deals = EXCLUDED.closed_deals,
                        total_revenue = EXCLUDED.total_revenue,
                        avg_deal_value = EXCLUDED.avg_deal_value,
                        conversion_rate = EXCLUDED.conversion_rate,
                        updated_at = NOW()
                    """,
                    source_data["source_name"],
                    source_data["total_contacts"],
                    source_data["qualified_leads"],
                    source_data["appointments"],
                    source_data["closed_deals"],
                    source_data["total_revenue"],
                    source_data["avg_deal_value"],
                    source_data["conversion_rate"],
                )

            logger.info(f"Updated metrics for {len(all_metrics['sources'])} sources")

        except Exception as e:
            logger.error(f"Error updating source metrics table: {e}", exc_info=True)

    def _normalize_source(self, source: Optional[str]) -> str:
        """Normalize source name for consistency.

        Args:
            source: Raw source string

        Returns:
            Normalized source name
        """
        if not source:
            return "Unknown"

        # Convert to title case and strip whitespace
        normalized = source.strip().title()

        # Map common variations
        source_map = {
            "Fb": "Facebook",
            "Facebook Ads": "Facebook",
            "Fb Ads": "Facebook",
            "Google Ads": "Google",
            "Paid Search": "Google",
            "Organic": "Google Organic",
            "Ref": "Referral",
            "Referrals": "Referral",
        }

        return source_map.get(normalized, normalized)

    def _mock_metrics(self) -> Dict[str, Any]:
        """Generate mock metrics for development."""
        return {
            "source_name": "Unknown",
            "total_contacts": 0,
            "qualified_leads": 0,
            "appointments": 0,
            "showings": 0,
            "offers": 0,
            "closed_deals": 0,
            "conversion_rate": 0.0,
            "total_revenue": 0.0,
            "avg_deal_value": 0.0,
        }


# Singleton instance
_instance: Optional[SourceTracker] = None


def get_source_tracker(db_service: Optional[Any] = None) -> SourceTracker:
    """Get or create singleton SourceTracker instance.

    Args:
        db_service: Optional database service for persistence

    Returns:
        SourceTracker instance
    """
    global _instance
    if _instance is None:
        _instance = SourceTracker(db_service=db_service)
    return _instance
