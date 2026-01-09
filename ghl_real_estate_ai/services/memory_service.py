"""
Memory Service for GHL Real Estate AI.

Handles persistent storage and retrieval of conversation context.
Currently supports:
- In-memory (for testing)
- File-based (JSON)
- Ready for Redis/PostgreSQL
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MemoryService:
    """
    Persistent memory service for storing conversation context.
    """

    def __init__(self, storage_type: str = "file"):
        """
        Initialize memory service.

        Args:
            storage_type: Type of storage ("memory" or "file").
                         Defaults to "file" as per settings.
        """
        self.storage_type = storage_type
        self.memory_dir = Path("data/memory")

        if self.storage_type == "file":
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"Memory service initialized with file storage at {self.memory_dir}"
            )
        else:
            self._memory_cache: Dict[str, Dict[str, Any]] = {}
            logger.info("Memory service initialized with in-memory storage")

    def _get_file_path(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> Path:
        """Get file path for a contact's memory, scoped by location."""
        import re

        # Sanitize contact_id and location_id (only allow alphanumeric, dash, underscore)
        def sanitize(id_str: str) -> str:
            """
            Execute sanitize operation.

            Args:
                id_str: Unique identifier

            Returns:
                Result of the operation
            """
            # Strip any path components and keep only the filename part
            filename = os.path.basename(id_str)
            # Remove any characters that aren't alphanumeric, dash, or underscore
            return re.sub(r"[^a-zA-Z0-9_-]", "", filename)

        safe_contact_id = sanitize(contact_id)
        if not safe_contact_id:
            safe_contact_id = "default_contact"

        if location_id:
            safe_location_id = sanitize(location_id)
            if not safe_location_id:
                safe_location_id = "default_location"

            tenant_dir = self.memory_dir / safe_location_id
            tenant_dir.mkdir(parents=True, exist_ok=True)
            return tenant_dir / f"{safe_contact_id}.json"

        return self.memory_dir / f"{safe_contact_id}.json"

    async def get_context(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve conversation context for a contact.

        Args:
            contact_id: GHL contact ID
            location_id: Optional GHL location ID for tenant isolation

        Returns:
            Conversation context dict
        """
        if self.storage_type == "memory":
            cache_key = f"{location_id}:{contact_id}" if location_id else contact_id
            return self._memory_cache.get(
                cache_key, self._get_default_context(contact_id, location_id)
            )

        file_path = self._get_file_path(contact_id, location_id)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read memory file for {contact_id}: {e}")

        return self._get_default_context(contact_id, location_id)

    async def save_context(
        self,
        contact_id: str,
        context: Dict[str, Any],
        location_id: Optional[str] = None,
    ) -> None:
        """
        Save conversation context for a contact.

        Args:
            contact_id: GHL contact ID
            context: Conversation context to save
            location_id: Optional GHL location ID for tenant isolation
        """
        context["updated_at"] = datetime.utcnow().isoformat()
        if location_id:
            context["location_id"] = location_id

        if self.storage_type == "memory":
            cache_key = f"{location_id}:{contact_id}" if location_id else contact_id
            self._memory_cache[cache_key] = context
            return

        file_path = self._get_file_path(contact_id, location_id)
        try:
            with open(file_path, "w") as f:
                json.dump(context, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory file for {contact_id}: {e}")

    def _get_default_context(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return default context for new conversations."""
        return {
            "contact_id": contact_id,
            "location_id": location_id,
            "conversation_history": [],
            "extracted_preferences": {},
            "lead_score": 0,
            "conversation_stage": "initial_contact",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_interaction_at": datetime.utcnow().isoformat(),
            "previous_sessions_summary": "",
            # Lead Intelligence Enhancement Features (2026-01-09)
            "lead_intelligence": {
                "behavioral_features": {},
                "engagement_metrics": {
                    "engagement_velocity": 0.0,
                    "sentiment_progression": 0.0,
                    "response_consistency": 0.0
                },
                "churn_risk": {
                    "risk_score": 0.0,
                    "risk_level": "low",
                    "prediction_horizon": "30_days",
                    "last_prediction": None
                },
                "property_matching": {
                    "lifestyle_scores": {},
                    "behavioral_weights": {},
                    "match_history": []
                },
                "workflow_automation": {
                    "active_workflows": [],
                    "completed_workflows": [],
                    "next_scheduled_action": None
                },
                "real_time_events": {
                    "last_score_update": None,
                    "recent_alerts": [],
                    "websocket_session_id": None
                }
            }
        }

    async def update_lead_intelligence(
        self,
        contact_id: str,
        intelligence_data: Dict[str, Any],
        location_id: Optional[str] = None,
    ) -> None:
        """
        Update lead intelligence data for a contact.

        Args:
            contact_id: GHL contact ID
            intelligence_data: Lead intelligence data to update
            location_id: Optional GHL location ID for tenant isolation
        """
        context = await self.get_context(contact_id, location_id)

        if "lead_intelligence" not in context:
            context["lead_intelligence"] = self._get_default_context(contact_id, location_id)["lead_intelligence"]

        # Deep merge intelligence data
        for category, data in intelligence_data.items():
            if category in context["lead_intelligence"]:
                if isinstance(data, dict) and isinstance(context["lead_intelligence"][category], dict):
                    context["lead_intelligence"][category].update(data)
                else:
                    context["lead_intelligence"][category] = data
            else:
                context["lead_intelligence"][category] = data

        await self.save_context(contact_id, context, location_id)
        logger.info(f"Updated lead intelligence for contact {contact_id}")

    async def get_lead_intelligence(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get lead intelligence data for a contact.

        Args:
            contact_id: GHL contact ID
            location_id: Optional GHL location ID for tenant isolation

        Returns:
            Lead intelligence data dict
        """
        context = await self.get_context(contact_id, location_id)
        return context.get("lead_intelligence", {})

    async def clear_context(self, contact_id: str) -> None:
        """Clear context for a contact."""
        if self.storage_type == "memory":
            if contact_id in self._memory_cache:
                del self._memory_cache[contact_id]
            return

        file_path = self._get_file_path(contact_id)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete memory file for {contact_id}: {e}")
