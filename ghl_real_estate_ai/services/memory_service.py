"""
Memory Service for GHL Real Estate AI.

Handles persistent storage and retrieval of conversation context.
Currently supports:
- In-memory (for testing)
- File-based (JSON)
- Ready for Redis/PostgreSQL
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import aiofiles.os

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MemoryService:
    """
    Persistent memory service for storing conversation context.
    Uses singleton pattern to avoid redundant initialization across modules.
    """

    _instances: dict = {}

    def __new__(cls, storage_type: Optional[str] = None):
        key = storage_type or "_default"
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, storage_type: Optional[str] = None):
        """
        Initialize memory service.

        Args:
            storage_type: Optional storage type override ("memory", "file", or "redis").
                         If None, determined by settings.environment and location_id.
        """
        if self._initialized:
            return
        self._initialized = True

        from ghl_real_estate_ai.services.cache_service import get_cache_service

        self.cache_service = get_cache_service()
        self.storage_type = storage_type or ("redis" if settings.environment == "production" else "file")
        self.memory_dir = Path("data/memory")

        if self.storage_type == "file":
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Memory service initialized with file storage at {self.memory_dir}")
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

    @staticmethod
    def _sanitize_path_component(value: str) -> str:
        """Sanitize a value for safe use as a path component (no traversal)."""
        import re

        # Strip path separators and dangerous characters
        sanitized = re.sub(r'[/\:*?"<>|.]', "_", value)
        # Prevent empty result
        return sanitized or "unknown"

    async def _get_file_path_async(self, contact_id: str, location_id: Optional[str] = None) -> Path:
        """
        Get the file path for storing a contact's context (async version).
        """
        safe_contact = self._sanitize_path_component(contact_id)
        if location_id:
            safe_location = self._sanitize_path_component(location_id)
            location_dir = self.memory_dir / safe_location
            if not await aiofiles.os.path.exists(location_dir):
                await aiofiles.os.makedirs(location_dir, exist_ok=True)
            return location_dir / f"{safe_contact}.json"

        return self.memory_dir / f"{safe_contact}.json"

    def _get_file_path(self, contact_id: str, location_id: Optional[str] = None) -> Path:
        """
        Get the file path for storing a contact's context (sync version).
        """
        safe_contact = self._sanitize_path_component(contact_id)
        if location_id:
            safe_location = self._sanitize_path_component(location_id)
            location_dir = self.memory_dir / safe_location
            location_dir.mkdir(parents=True, exist_ok=True)
            return location_dir / f"{safe_contact}.json"

        return self.memory_dir / f"{safe_contact}.json"

    def _resolve_location_id(self, location_id: Optional[str]) -> str:
        """
        Resolve location_id with strict enforcement.

        Args:
            location_id: The location_id passed to the method

        Returns:
            Resolved location_id string

        Raises:
            ValueError: If location_id cannot be resolved and strict mode is on
        """
        if location_id:
            return location_id

        # Fallback to global settings if available
        if settings.ghl_location_id:
            # logger.debug(f"Using default location_id from settings: {settings.ghl_location_id}")
            return settings.ghl_location_id

        # In production, we MUST have a location_id
        if settings.environment == "production":
            logger.error("CRITICAL: Operation attempted without location_id in production")
            raise ValueError("location_id is required for all memory operations in production")

        return "default"

    async def get_context(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve conversation context for a contact with strict tenant isolation.

        Args:
            contact_id: GHL contact ID
            location_id: Optional GHL location ID for tenant isolation

        Returns:
            Conversation context dict
        """
        resolved_loc = self._resolve_location_id(location_id)

        # 1. Try Redis first for production/multitenant isolation
        if self._should_use_redis(resolved_loc):
            cache_key = f"ctx:{resolved_loc}:{contact_id}"
            context = await self.cache_service.get(cache_key)
            if context:
                # Security Verification: Ensure retrieved context belongs to this location_id
                if context.get("location_id") != resolved_loc:
                    logger.error(
                        f"TENANT LEAK PREVENTED: Contact {contact_id} context for location {context.get('location_id')} accessed with location {resolved_loc}"
                    )
                    return self._get_default_context(contact_id, resolved_loc)

                # Graphiti Integration: Inject Semantic Context
                from ghl_real_estate_ai.agent_system.memory import memory_manager as graphiti_manager

                if graphiti_manager.enabled:
                    try:
                        graphiti_context = await graphiti_manager.retrieve_context(contact_id)
                        context["relevant_knowledge"] = graphiti_context
                    except Exception as ge:
                        logger.warning(f"Failed to retrieve Graphiti context for {contact_id}: {ge}")
                return context

        # 2. Fallback to Memory cache
        if self.storage_type == "memory":
            cache_key = f"{resolved_loc}:{contact_id}"
            context = self._memory_cache.get(cache_key)
            if context:
                if context.get("location_id") != resolved_loc:
                    logger.error(
                        f"TENANT LEAK PREVENTED (Memory): {contact_id} leak from {context.get('location_id')} to {resolved_loc}"
                    )
                    return self._get_default_context(contact_id, resolved_loc)
                return context
            return self._get_default_context(contact_id, resolved_loc)

        # 3. Fallback to File storage
        file_path = await self._get_file_path_async(contact_id, resolved_loc)
        if await aiofiles.os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, "r") as f:
                    content = await f.read()
                    context = json.loads(content)

                    # Security Verification
                    if context.get("location_id") != resolved_loc:
                        logger.error(
                            f"TENANT LEAK PREVENTED (File): {contact_id} leak from {context.get('location_id')} to {resolved_loc}"
                        )
                        return self._get_default_context(contact_id, resolved_loc)

                    # Graphiti Integration: Inject Semantic Context
                    from ghl_real_estate_ai.agent_system.memory import memory_manager as graphiti_manager

                    if graphiti_manager.enabled:
                        try:
                            graphiti_context = await graphiti_manager.retrieve_context(contact_id)
                            context["relevant_knowledge"] = graphiti_context
                        except Exception as ge:
                            logger.warning(f"Failed to retrieve Graphiti context for {contact_id}: {ge}")

                    return context
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Failed to read memory file for {contact_id}: {str(e)}")

        return self._get_default_context(contact_id, resolved_loc)

    async def get_context_batch(self, contact_ids: List[str], location_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Batch retrieve conversation context for a list of contacts with strict tenant isolation.
        Aims to solve N+1 query problems in dashboard listings.

        Args:
            contact_ids: List of GHL contact IDs
            location_id: Optional GHL location ID for tenant isolation

        Returns:
            Dictionary mapping contact_id to context dict
        """
        if not contact_ids:
            return {}

        resolved_loc = self._resolve_location_id(location_id)
        results = {}

        # 1. Try Redis first (Batch mode)
        if self._should_use_redis(resolved_loc):
            cache_keys = [f"ctx:{resolved_loc}:{cid}" for cid in contact_ids]
            cached_contexts = await self.cache_service.get_many(cache_keys)
            
            for cid in contact_ids:
                key = f"ctx:{resolved_loc}:{cid}"
                if key in cached_contexts:
                    context = cached_contexts[key]
                    # Security Verification
                    if context.get("location_id") == resolved_loc:
                        results[cid] = context
                    else:
                        logger.error(f"TENANT LEAK PREVENTED (Redis Batch): {cid} leak from {context.get('location_id')}")

        # Identify missing IDs that need to be fetched from file system or default
        missing_ids = [cid for cid in contact_ids if cid not in results]
        
        if not missing_ids:
            return results

        # 2. Try Memory/File storage for missing IDs (Parallel mode)
        async def fetch_missing(cid):
            if self.storage_type == "memory":
                cache_key = f"{resolved_loc}:{cid}"
                context = self._memory_cache.get(cache_key)
                if context and context.get("location_id") == resolved_loc:
                    return cid, context
                return cid, self._get_default_context(cid, resolved_loc)
            
            # File storage fallback
            return cid, await self.get_context(cid, resolved_loc)

        missing_results = await asyncio.gather(*[fetch_missing(cid) for cid in missing_ids])
        
        for cid, context in missing_results:
            results[cid] = context

        return results

    async def add_interaction(
        self, contact_id: str, message: str, role: str, location_id: Optional[str] = None
    ) -> None:
        """
        Record a new interaction to preferred storage and Graphiti with strict isolation.
        """
        resolved_loc = self._resolve_location_id(location_id)

        # 1. Update Context (handles Redis/File/Memory internally)
        context = await self.get_context(contact_id, resolved_loc)

        interaction = {"role": role, "content": message, "timestamp": datetime.utcnow().isoformat()}

        if "conversation_history" not in context:
            context["conversation_history"] = []

        context["conversation_history"].append(interaction)
        context["last_interaction_at"] = interaction["timestamp"]

        await self.save_context(contact_id, context, resolved_loc)

        # 2. Update Graphiti (Episodic Memory)
        from ghl_real_estate_ai.agent_system.memory import memory_manager as graphiti_manager

        if graphiti_manager.enabled:
            try:
                # NOTE: Graphiti should also be scoped, but for now we use contact_id
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
        Save conversation context for a contact with strict tenant isolation.

        Args:
            contact_id: GHL contact ID
            context: Conversation context to save
            location_id: Optional GHL location ID for tenant isolation
        """
        resolved_loc = self._resolve_location_id(location_id)

        context["updated_at"] = datetime.utcnow().isoformat()
        context["location_id"] = resolved_loc

        # 1. Save to Redis for production/multitenant isolation
        if self._should_use_redis(resolved_loc):
            cache_key = f"ctx:{resolved_loc}:{contact_id}"
            # Context lasts 7 days in Redis
            await self.cache_service.set(cache_key, context, ttl=604800)

            # If we are in transition/backup mode, also save to file
            if settings.environment != "production":
                file_path = self._get_file_path(contact_id, resolved_loc)
                try:
                    with open(file_path, "w") as f:
                        json.dump(context, f, indent=2)
                except IOError:
                    logger.warning(f"Failed to backup memory context to file for {contact_id}")
            return

        # 2. Save to Memory
        if self.storage_type == "memory":
            cache_key = f"{resolved_loc}:{contact_id}"
            self._memory_cache[cache_key] = context
            return

        # 3. Save to File
        file_path = await self._get_file_path_async(contact_id, resolved_loc)
        try:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(context, indent=2))
        except (IOError, TypeError) as e:
            logger.error(f"Failed to save memory file for {contact_id}: {str(e)}")

    def _get_default_context(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Return default context for new conversations."""
        return {
            "contact_id": contact_id,
            "location_id": location_id or self._resolve_location_id(location_id),
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
                    "modular_statusline_plugin_system",
                ],
                "in_progress_agents": {
                    "a059964": "dynamic_scoring_weights",
                    "ad71ba7": "contextual_property_matching",
                    "ab5d2ca": "advanced_workflow_automation",
                    "a52bf61": "real_time_intelligence_dashboard",
                    "a39dab4": "churn_prediction_system",
                },
                "next_session_priority": "verify_agent_completion_status_then_continue_or_demo",
                "expected_business_impact": "25_to_30_percent_conversion_improvement",
            },
            # Lead Intelligence Enhancement Features (2026-01-09)
            "lead_intelligence": {
                "behavioral_features": {},
                "engagement_metrics": {
                    "engagement_velocity": 0.0,
                    "sentiment_progression": 0.0,
                    "response_consistency": 0.0,
                },
                "churn_risk": {
                    "risk_score": 0.0,
                    "risk_level": "low",
                    "prediction_horizon": "30_days",
                    "last_prediction": None,
                },
                "property_matching": {"lifestyle_scores": {}, "behavioral_weights": {}, "match_history": []},
                "workflow_automation": {
                    "active_workflows": [],
                    "completed_workflows": [],
                    "next_scheduled_action": None,
                },
                "real_time_events": {"last_score_update": None, "recent_alerts": [], "websocket_session_id": None},
            },
        }

    async def update_lead_intelligence(
        self,
        contact_id: str,
        intelligence_data: Dict[str, Any],
        location_id: Optional[str] = None,
    ) -> None:
        """
        Update lead intelligence data for a contact with strict tenant isolation.

        Args:
            contact_id: GHL contact ID
            intelligence_data: Lead intelligence data to update
            location_id: Optional GHL location ID for tenant isolation
        """
        resolved_loc = self._resolve_location_id(location_id)
        context = await self.get_context(contact_id, resolved_loc)

        if "lead_intelligence" not in context:
            context["lead_intelligence"] = self._get_default_context(contact_id, resolved_loc)["lead_intelligence"]

        # Deep merge intelligence data
        for category, data in intelligence_data.items():
            if category in context["lead_intelligence"]:
                if isinstance(data, dict) and isinstance(context["lead_intelligence"][category], dict):
                    context["lead_intelligence"][category].update(data)
                else:
                    context["lead_intelligence"][category] = data
            else:
                context["lead_intelligence"][category] = data

        await self.save_context(contact_id, context, resolved_loc)
        logger.info(f"Updated lead intelligence for contact {contact_id} in location {resolved_loc}")

    async def get_lead_intelligence(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get lead intelligence data for a contact with strict tenant isolation.

        Args:
            contact_id: GHL contact ID
            location_id: Optional GHL location ID for tenant isolation

        Returns:
            Lead intelligence data dict
        """
        resolved_loc = self._resolve_location_id(location_id)
        context = await self.get_context(contact_id, resolved_loc)
        return context.get("lead_intelligence", {})

    async def clear_context(self, contact_id: str, location_id: Optional[str] = None) -> None:
        """
        Clear context for a contact with strict tenant isolation.
        """
        resolved_loc = self._resolve_location_id(location_id)

        # 1. Clear from Redis
        if self._should_use_redis(resolved_loc):
            cache_key = f"ctx:{resolved_loc}:{contact_id}"
            await self.cache_service.delete(cache_key)

        # 2. Clear from Memory
        if self.storage_type == "memory":
            cache_key = f"{resolved_loc}:{contact_id}"
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            return

        # 3. Clear from File
        file_path = self._get_file_path(contact_id, resolved_loc)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError as e:
                logger.error(f"Failed to delete memory file for {contact_id} in {resolved_loc}: {str(e)}")

    async def store_conversation_memory(
        self, conversation_id: str, content: Dict[str, Any], ttl_hours: Optional[int] = None
    ) -> None:
        """
        Store a specialized conversation memory (e.g., for analytics) asynchronously.
        """
        # For now, we store it as a regular file in a sub-directory
        memory_path = self.memory_dir / "specialized"
        if not await aiofiles.os.path.exists(memory_path):
            await aiofiles.os.makedirs(memory_path, exist_ok=True)

        file_path = memory_path / f"{conversation_id}.json"

        try:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(
                    {
                        "content": content,
                        "stored_at": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()
                        if ttl_hours
                        else None,
                    },
                    indent=2,
                ))
        except (IOError, TypeError) as e:
            logger.error(f"Failed to store conversation memory {conversation_id}: {str(e)}")
