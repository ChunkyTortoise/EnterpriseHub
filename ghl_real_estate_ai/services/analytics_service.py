"""
Analytics Service for GHL Real Estate AI.

Tracks and retrieves system performance metrics and lead conversion data.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """
    Service for tracking and analyzing conversation events.
    """

    def __init__(self, analytics_dir: str = "data/analytics"):
        """
        Initialize analytics service.

        Args:
            analytics_dir: Directory to store analytics data.
        """
        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Analytics service initialized at {self.analytics_dir}")

    def _get_location_file(self, location_id: str) -> Path:
        """Get the daily analytics file for a location."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        tenant_dir = self.analytics_dir / location_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / f"events_{date_str}.jsonl"

    async def track_event(
        self,
        event_type: str,
        location_id: str,
        contact_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a specific event.

        Args:
            event_type: Type of event (e.g., 'message_received', 'lead_qualified')
            location_id: GHL Location ID
            contact_id: Optional GHL Contact ID
            data: Optional event metadata
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "contact_id": contact_id,
            "location_id": location_id,
            "data": data or {},
        }

        file_path = self._get_location_file(location_id)

        try:
            # We use JSONL (JSON Lines) for efficient appending
            with open(file_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to track event {event_type} for {location_id}: {e}")

    async def track_llm_usage(
        self,
        location_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cached: bool = False,
        contact_id: Optional[str] = None,
    ) -> None:
        """
        Track LLM token usage and calculate costs.
        """
        cost = 0.0
        if not cached:
            if provider == "claude":
                cost = (input_tokens / 1_000_000 * settings.claude_input_cost_per_1m) + (
                    output_tokens / 1_000_000 * settings.claude_output_cost_per_1m
                )
            elif provider == "gemini":
                cost = (input_tokens / 1_000_000 * settings.gemini_input_cost_per_1m) + (
                    output_tokens / 1_000_000 * settings.gemini_output_cost_per_1m
                )

        # Calculate saved cost if cached
        saved_cost = 0.0
        if cached:
            if provider == "claude":
                saved_cost = (input_tokens / 1_000_000 * settings.claude_input_cost_per_1m) + (
                    output_tokens / 1_000_000 * settings.claude_output_cost_per_1m
                )
            elif provider == "gemini":
                saved_cost = (input_tokens / 1_000_000 * settings.gemini_input_cost_per_1m) + (
                    output_tokens / 1_000_000 * settings.gemini_output_cost_per_1m
                )

        usage_data = {
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "saved_cost": saved_cost,
            "cached": cached,
        }

        await self.track_event(event_type="llm_usage", location_id=location_id, contact_id=contact_id, data=usage_data)

    async def get_events(
        self,
        location_id: str,
        date_str: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events for a specific location and date.

        Args:
            location_id: GHL Location ID
            date_str: Date string (YYYY-MM-DD), defaults to today
            event_type: Optional filter by event type

        Returns:
            List of event dictionaries
        """
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

        file_path = self.analytics_dir / location_id / f"events_{date_str}.jsonl"

        events = []
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    for line in f:
                        if line.strip():
                            event = json.loads(line)
                            if not event_type or event.get("event_type") == event_type:
                                events.append(event)
            except Exception as e:
                logger.error(f"Failed to read events from {file_path}: {e}")

        return events

    async def get_daily_summary(self, location_id: str, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a summary of metrics for a specific day.
        """
        events = await self.get_events(location_id, date_str)

        summary = {
            "total_messages": 0,
            "incoming_messages": 0,
            "outgoing_messages": 0,
            "leads_scored": 0,
            "hot_leads": 0,
            "avg_lead_score": 0,
            "active_contacts": set(),
            "llm_usage": {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "saved_cost": 0.0,
                "cache_hits": 0,
                "total_requests": 0,
            },
        }

        total_score = 0
        scored_count = 0

        for event in events:
            etype = event.get("event_type")
            data = event.get("data", {})

            if event.get("contact_id"):
                summary["active_contacts"].add(event.get("contact_id"))

            if etype == "message_received":
                summary["incoming_messages"] += 1
                summary["total_messages"] += 1
            elif etype == "message_sent":
                summary["outgoing_messages"] += 1
                summary["total_messages"] += 1
            elif etype == "lead_scored":
                summary["leads_scored"] += 1
                score = data.get("score", 0)
                total_score += score
                scored_count += 1
                if score >= 70:  # Standard hot lead threshold
                    summary["hot_leads"] += 1
            elif etype == "llm_usage":
                usage = summary["llm_usage"]
                usage["total_requests"] += 1
                usage["input_tokens"] += data.get("input_tokens", 0)
                usage["output_tokens"] += data.get("output_tokens", 0)
                usage["total_tokens"] += data.get("total_tokens", 0)
                usage["total_cost"] += data.get("cost", 0.0)
                usage["saved_cost"] += data.get("saved_cost", 0.0)
                if data.get("cached"):
                    usage["cache_hits"] += 1

        summary["active_contacts_count"] = len(summary["active_contacts"])
        del summary["active_contacts"]  # Don't return the set

        if scored_count > 0:
            summary["avg_lead_score"] = total_score / scored_count

        return summary

    async def get_jorge_bot_metrics(self, location_id: str = "all", days: int = 7) -> Dict[str, Any]:
        """
        Specialized retrieval for Jorge's Lead and Seller bot metrics.
        Aggregates across multiple locations if location_id is 'all'.
        """
        from datetime import timedelta

        locations = []
        if location_id == "all":
            if self.analytics_dir.exists():
                locations = [d.name for d in self.analytics_dir.iterdir() if d.is_dir()]
        else:
            locations = [location_id]

        aggregated = {
            "seller": {
                "total_interactions": 0,
                "vague_streaks": 0,
                "take_away_closes": 0,
                "handoffs": 0,
                "avg_quality": 0.0,
                "temp_breakdown": {"hot": 0, "warm": 0, "cold": 0},
            },
            "lead": {"total_scored": 0, "avg_score": 0.0, "immediate_priority": 0, "high_priority": 0},
            "locations_active": len(locations),
        }

        quality_sum = 0.0
        quality_count = 0
        score_sum = 0.0
        score_count = 0

        # Look back over specified days
        for i in range(days):
            date_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")

            for loc in locations:
                events = await self.get_events(loc, date_str)

                for event in events:
                    etype = event.get("event_type")
                    data = event.get("data", {})

                    if etype == "jorge_seller_interaction":
                        aggregated["seller"]["total_interactions"] += 1
                        if data.get("vague_streak", 0) > 0:
                            aggregated["seller"]["vague_streaks"] += 1
                        if data.get("response_type") == "take_away_close":
                            aggregated["seller"]["take_away_closes"] += 1
                        if data.get("response_type") == "handoff":
                            aggregated["seller"]["handoffs"] += 1

                        temp = data.get("temperature", "cold")
                        aggregated["seller"]["temp_breakdown"][temp] = (
                            aggregated["seller"]["temp_breakdown"].get(temp, 0) + 1
                        )

                        quality_sum += data.get("response_quality", 0.0)
                        quality_count += 1

                    elif etype == "lead_scored":
                        aggregated["lead"]["total_scored"] += 1
                        score = data.get("score", 0)
                        score_sum += score
                        score_count += 1

                        # Priority logic (use predictive_score if available)
                        priority = data.get("predictive_score", {}).get("priority_level", "").lower()
                        if priority == "critical" or priority == "immediate":
                            aggregated["lead"]["immediate_priority"] += 1
                        elif priority == "high":
                            aggregated["lead"]["high_priority"] += 1
                        elif score >= 90:
                            aggregated["lead"]["immediate_priority"] += 1
                        elif score >= 75:
                            aggregated["lead"]["high_priority"] += 1

        if quality_count > 0:
            aggregated["seller"]["avg_quality"] = quality_sum / quality_count
        if score_count > 0:
            aggregated["lead"]["avg_score"] = score_sum / score_count

        return aggregated

    async def get_seller_friction_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyzes which of Jorge's 4 questions cause the most drop-offs.
        """
        from datetime import timedelta

        # question numbers 1-4
        friction = {
            1: {"answered": 0, "vague": 0, "dropoff": 0, "name": "Motivation"},
            2: {"answered": 0, "vague": 0, "dropoff": 0, "name": "Timeline"},
            3: {"answered": 0, "vague": 0, "dropoff": 0, "name": "Condition"},
            4: {"answered": 0, "vague": 0, "dropoff": 0, "name": "Price"},
        }

        locations = []
        if self.analytics_dir.exists():
            locations = [d.name for d in self.analytics_dir.iterdir() if d.is_dir()]

        for i in range(days):
            date_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            for loc in locations:
                events = await self.get_events(loc, date_str, event_type="jorge_seller_interaction")

                # Group by contact to find max question reached
                contact_progress = {}
                for event in events:
                    cid = event.get("contact_id")
                    q_num = event.get("data", {}).get("questions_answered", 0)
                    is_vague = event.get("data", {}).get("vague_streak", 0) > 0

                    if cid not in contact_progress or q_num > contact_progress[cid]["max_q"]:
                        contact_progress[cid] = {"max_q": q_num, "vague_at": set()}
                    if is_vague:
                        contact_progress[cid]["vague_at"].add(q_num)

                for cid, info in contact_progress.items():
                    max_q = info["max_q"]
                    for q in range(1, max_q + 1):
                        if q in friction:
                            friction[q]["answered"] += 1
                            if q in info["vague_at"]:
                                friction[q]["vague"] += 1

                    # If they didn't reach question 4, they dropped off after max_q
                    if max_q < 4 and (max_q + 1) in friction:
                        friction[max_q + 1]["dropoff"] += 1

        return friction

    async def get_cached_daily_summary(
        self, location_id: str, date_str: Optional[str] = None, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get daily summary, using cache if available to avoid expensive file reads.
        """
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

        from ghl_real_estate_ai.services.cache_service import get_tenant_cache

        cache = get_tenant_cache(location_id)
        cache_key = f"analytics_summary:{date_str}"

        if not force_refresh:
            cached_summary = await cache.get(cache_key)
            if cached_summary:
                return cached_summary

        # Compute summary
        summary = await self.get_daily_summary(location_id, date_str)

        # Cache for 5 minutes (300 seconds)
        await cache.set(cache_key, summary, ttl=300)

        return summary

    async def get_llm_roi_analysis(self, location_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate the ROI of AI operations, including cost savings from caching and automation.
        """
        from datetime import timedelta

        total_cost = 0.0
        total_saved_cost = 0.0
        total_tokens = 0
        cache_hits = 0
        total_requests = 0

        for i in range(days):
            date_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            events = await self.get_events(location_id, date_str, event_type="llm_usage")

            for event in events:
                data = event.get("data", {})
                total_requests += 1
                total_cost += data.get("cost", 0.0)
                total_saved_cost += data.get("saved_cost", 0.0)
                total_tokens += data.get("total_tokens", 0)
                if data.get("cached"):
                    cache_hits += 1

        # Estimated human hours saved (conservative estimate: 1 request saves 2 minutes of manual work)
        hours_saved = (total_requests * 2) / 60
        human_labor_cost_per_hour = 25.0  # Average real estate assistant rate
        labor_savings = hours_saved * human_labor_cost_per_hour

        total_value_generated = labor_savings + total_saved_cost
        net_roi = total_value_generated - total_cost
        roi_percentage = (net_roi / total_cost * 100) if total_cost > 0 else 0

        return {
            "location_id": location_id,
            "period_days": days,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "actual_cost": round(total_cost, 4),
            "saved_via_caching": round(total_saved_cost, 4),
            "cache_hit_rate": round(cache_hits / total_requests, 2) if total_requests > 0 else 0,
            "estimated_hours_saved": round(hours_saved, 1),
            "labor_cost_savings": round(labor_savings, 2),
            "total_value_generated": round(total_value_generated, 2),
            "net_roi": round(net_roi, 2),
            "roi_percentage": round(roi_percentage, 1),
        }
