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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.agent_system.memory import memory_manager as graphiti_manager

logger = get_logger(__name__)


class MemoryService:
    """
    Persistent memory service for storing conversation context.
    """

    def __init__(self, storage_type: Optional[str] = None):
        """
        Initialize memory service.

        Args:
            storage_type: Optional storage type override ("memory", "file", or "redis").
                         If None, determined by settings.environment and location_id.
        """
        from ghl_real_estate_ai.services.cache_service import get_cache_service
        self.cache_service = get_cache_service()
        self.storage_type = storage_type or ("redis" if settings.environment == "production" else "file")
        self.memory_dir = Path("data/memory")

        if self.storage_type == "file":
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"Memory service initialized with file storage at {self.memory_dir}"
            )
        elif self.storage_type == "redis":
            logger.info("Memory service initialized with Redis-first storage")
        else:
            self._memory_cache: Dict[str, Dict[str, Any]] = {}
            logger.info("Memory service initialized with in-memory storage")

    def _should_use_redis(self, location_id: Optional[str]) -> bool:
        """Determine if Redis should be used for this request."""
        # In production, we always prefer Redis for multitenancy
        if settings.environment == "production" and settings.redis_url:
            return True
        # Explicit override
        return self.storage_type == "redis"

    def _get_file_path(self, contact_id: str, location_id: Optional[str] = None) -> Path:
        """
        Get the file path for storing a contact's context.
        
        Args:
            contact_id: GHL contact ID
            location_id: Optional GHL location ID for tenant isolation
            
        Returns:
            Path object
        """
        if location_id:
            # Create location-specific subdirectory
            location_dir = self.memory_dir / location_id
            location_dir.mkdir(parents=True, exist_ok=True)
            return location_dir / f"{contact_id}.json"
        
        return self.memory_dir / f"{contact_id}.json"

    async def get_context(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve conversation context for a contact with multitenant support.

        Args:
            contact_id: GHL contact ID
            location_id: Optional GHL location ID for tenant isolation

        Returns:
            Conversation context dict
        """
        # 1. Try Redis first for production/multitenant isolation
        if self._should_use_redis(location_id):
            cache_key = f"ctx:{location_id or 'global'}:{contact_id}"
            context = await self.cache_service.get(cache_key)
            if context:
                # Graphiti Integration: Inject Semantic Context
                if graphiti_manager.enabled:
                    try:
                        graphiti_context = await graphiti_manager.retrieve_context(contact_id)
                        context["relevant_knowledge"] = graphiti_context
                    except Exception as ge:
                        logger.warning(f"Failed to retrieve Graphiti context for {contact_id}: {ge}")
                return context

        # 2. Fallback to Memory cache
        if self.storage_type == "memory":
            cache_key = f"{location_id}:{contact_id}" if location_id else contact_id
            return self._memory_cache.get(
                cache_key, self._get_default_context(contact_id, location_id)
            )

        # 3. Fallback to File storage
        file_path = self._get_file_path(contact_id, location_id)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    context = json.load(f)
                    
                    # Graphiti Integration: Inject Semantic Context
                    if graphiti_manager.enabled:
                        try:
                            graphiti_context = await graphiti_manager.retrieve_context(contact_id)
                            context["relevant_knowledge"] = graphiti_context
                        except Exception as ge:
                            logger.warning(f"Failed to retrieve Graphiti context for {contact_id}: {ge}")
                            
                    return context
            except Exception as e:
                logger.error(f"Failed to read memory file for {contact_id}: {e}")

        return self._get_default_context(contact_id, location_id)

    async def add_interaction(
        self,
        contact_id: str,
        message: str,
        role: str,
        location_id: Optional[str] = None
    ) -> None:
        """
        Record a new interaction to preferred storage and Graphiti.
        """
        # 1. Update Context (handles Redis/File/Memory internally)
        context = await self.get_context(contact_id, location_id)
        
        interaction = {
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if "conversation_history" not in context:
            context["conversation_history"] = []
            
        context["conversation_history"].append(interaction)
        context["last_interaction_at"] = interaction["timestamp"]
        
        await self.save_context(contact_id, context, location_id)
        
        # 2. Update Graphiti (Episodic Memory)
        if graphiti_manager.enabled:
            try:
                await graphiti_manager.save_interaction(contact_id, message, role)
            except Exception as e:
                logger.warning(f"Failed to save interaction to Graphiti for {contact_id}: {e}")

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

        # 1. Save to Redis for production/multitenant isolation
        if self._should_use_redis(location_id):
            cache_key = f"ctx:{location_id or 'global'}:{contact_id}"
            # Context lasts 7 days in Redis
            await self.cache_service.set(cache_key, context, ttl=604800)
            
            # If we are in transition/backup mode, also save to file
            if settings.environment != "production":
                file_path = self._get_file_path(contact_id, location_id)
                try:
                    with open(file_path, "w") as f:
                        json.dump(context, f, indent=2)
                except Exception:
                    pass
            return

        # 2. Save to Memory
        if self.storage_type == "memory":
            cache_key = f"{location_id}:{contact_id}" if location_id else contact_id
            self._memory_cache[cache_key] = context
            return

        # 3. Save to File
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
            # Session Status Tracking (2026-01-09)
            "session_status": {
                "last_session_date": datetime.utcnow().isoformat(),
                "completed_systems": [
                    "real_time_lead_scoring_pipeline",
                    "unified_lead_intelligence_schema",
                    "ml_behavioral_features_engine",
                    "modular_statusline_plugin_system"
                ],
                "in_progress_agents": {
                    "a059964": "dynamic_scoring_weights",
                    "ad71ba7": "contextual_property_matching",
                    "ab5d2ca": "advanced_workflow_automation",
                    "a52bf61": "real_time_intelligence_dashboard",
                    "a39dab4": "churn_prediction_system"
                },
                "next_session_priority": "verify_agent_completion_status_then_continue_or_demo",
                "expected_business_impact": "25_to_30_percent_conversion_improvement"
            },
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

    async def store_conversation_memory(
        self,
        conversation_id: str,
        content: Dict[str, Any],
        ttl_hours: Optional[int] = None
    ) -> None:
        """
        Store a specialized conversation memory (e.g., for analytics).
        """
        # For now, we store it as a regular file in a sub-directory
        memory_path = self.memory_dir / "specialized"
        memory_path.mkdir(parents=True, exist_ok=True)
        
        file_path = memory_path / f"{conversation_id}.json"
        
        try:
            with open(file_path, "w") as f:
                json.dump({
                    "content": content,
                    "stored_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat() if ttl_hours else None
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to store conversation memory {conversation_id}: {e}")

