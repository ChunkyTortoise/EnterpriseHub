"""
Analytics Service for GHL Real Estate AI.

Tracks and retrieves system performance metrics and lead conversion data.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

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
                cost = (input_tokens / 1_000_000 * settings.claude_input_cost_per_1m) + \
                       (output_tokens / 1_000_000 * settings.claude_output_cost_per_1m)
            elif provider == "gemini":
                cost = (input_tokens / 1_000_000 * settings.gemini_input_cost_per_1m) + \
                       (output_tokens / 1_000_000 * settings.gemini_output_cost_per_1m)
        
        # Calculate saved cost if cached
        saved_cost = 0.0
        if cached:
            if provider == "claude":
                saved_cost = (input_tokens / 1_000_000 * settings.claude_input_cost_per_1m) + \
                             (output_tokens / 1_000_000 * settings.claude_output_cost_per_1m)
            elif provider == "gemini":
                saved_cost = (input_tokens / 1_000_000 * settings.gemini_input_cost_per_1m) + \
                             (output_tokens / 1_000_000 * settings.gemini_output_cost_per_1m)

        usage_data = {
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "saved_cost": saved_cost,
            "cached": cached
        }

        await self.track_event(
            event_type="llm_usage",
            location_id=location_id,
            contact_id=contact_id,
            data=usage_data
        )

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

    async def get_daily_summary(
        self, location_id: str, date_str: Optional[str] = None
    ) -> Dict[str, Any]:
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
                "total_requests": 0
            }
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
