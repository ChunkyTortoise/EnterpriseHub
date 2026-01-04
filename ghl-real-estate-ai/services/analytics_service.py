"""
Analytics Service for GHL Real Estate AI.

Tracks and retrieves system performance metrics and lead conversion data.
"""
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import asyncio

from ghl_utils.logger import get_logger

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
        data: Optional[Dict[str, Any]] = None
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
            "data": data or {}
        }

        file_path = self._get_location_file(location_id)
        
        try:
            # We use JSONL (JSON Lines) for efficient appending
            with open(file_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to track event {event_type} for {location_id}: {e}")

    async def get_events(
        self, 
        location_id: str, 
        date_str: Optional[str] = None,
        event_type: Optional[str] = None
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
            "active_contacts": set()
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
                if score >= 70: # Standard hot lead threshold
                    summary["hot_leads"] += 1
        
        summary["active_contacts_count"] = len(summary["active_contacts"])
        del summary["active_contacts"] # Don't return the set
        
        if scored_count > 0:
            summary["avg_lead_score"] = total_score / scored_count
            
        return summary
