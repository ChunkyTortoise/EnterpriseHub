"""
Buyer Bot Conversation Memory Service (Task #29)

Implements Redis-backed conversation state persistence for multi-session continuity.
Buyers can return days later and pick up where they left off.

Features:
- Redis-backed persistence with configurable TTL (7-30 days)
- State compression for large conversation histories (JSON + gzip)
- Graceful handling of expired/missing state
- Memory usage optimization (max history limits)
"""

import gzip
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.config.jorge_config_loader import get_config
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import ConversationMessage
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class BuyerConversationMemory:
    """
    Manages multi-session conversation state persistence for Buyer Bot.
    
    Persisted State Schema:
    - conversation_history: List of conversation messages
    - financial_readiness_score: Last calculated FRS
    - buying_motivation_score: Last calculated BMS
    - budget_range: Extracted budget info
    - property_preferences: Property preferences
    - urgency_level: Timeline/urgency classification
    - last_interaction_timestamp: ISO format timestamp
    - state_version: Schema version for migrations
    
    Usage:
        memory = BuyerConversationMemory()
        
        # Load state at conversation start
        state = await memory.load_state(contact_id)
        
        # Save state after interaction
        await memory.save_state(contact_id, {
            "conversation_history": [...],
            "financial_readiness_score": 85.0,
            ...
        })
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.config = get_config()
        
        # Load configuration
        memory_config = self.config.buyer_bot.conversation_memory
        self.enabled = memory_config.enabled
        self.ttl_days = memory_config.ttl_days
        self.ttl_seconds = memory_config.ttl_days * 86400  # Convert to seconds
        self.compress_threshold = memory_config.compress_threshold_bytes
        self.max_history_messages = memory_config.max_history_messages
        self.key_prefix = memory_config.cache_key_prefix
        
        # State schema version for future migrations
        self.STATE_VERSION = "1.0"
        
        logger.info(
            f"BuyerConversationMemory initialized: "
            f"enabled={self.enabled}, ttl={self.ttl_days}d, "
            f"compress_threshold={self.compress_threshold}B"
        )

    def _get_cache_key(self, contact_id: str) -> str:
        """Generate cache key for contact's conversation state."""
        return f"{self.key_prefix}:{contact_id}"

    async def save_state(
        self,
        contact_id: str,
        state: Dict[str, Any],
        ttl_override: Optional[int] = None
    ) -> bool:
        """
        Persist conversation state to Redis.
        
        Args:
            contact_id: Unique contact/buyer identifier
            state: State dictionary to persist
            ttl_override: Optional TTL override in seconds (default: use config)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Conversation memory disabled, skipping save")
            return False
            
        if not contact_id:
            logger.error("Cannot save state: contact_id is empty")
            return False
            
        try:
            # Prepare state for persistence
            persist_state = self._prepare_state_for_storage(state)
            
            # Add metadata
            persist_state["last_interaction_timestamp"] = datetime.now(timezone.utc).isoformat()
            persist_state["state_version"] = self.STATE_VERSION
            
            # Serialize to JSON
            json_data = json.dumps(persist_state, default=str)
            json_bytes = json_data.encode('utf-8')
            
            # Compress if needed
            should_compress = len(json_bytes) > self.compress_threshold
            if should_compress:
                compressed_data = gzip.compress(json_bytes)
                storage_data = {
                    "compressed": True,
                    "data": compressed_data.hex()  # Store as hex string
                }
                logger.debug(
                    f"Compressed state for {contact_id}: "
                    f"{len(json_bytes)}B → {len(compressed_data)}B "
                    f"({(1 - len(compressed_data)/len(json_bytes))*100:.1f}% reduction)"
                )
            else:
                storage_data = {
                    "compressed": False,
                    "data": json_data
                }
            
            # Save to Redis
            cache_key = self._get_cache_key(contact_id)
            ttl = ttl_override or self.ttl_seconds
            
            success = await self.cache.set(cache_key, storage_data, ttl=ttl)
            
            if success:
                logger.info(f"Saved conversation state for {contact_id} (TTL: {ttl}s)")
            else:
                logger.error(f"Failed to save conversation state for {contact_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error saving conversation state for {contact_id}: {e}", exc_info=True)
            return False

    async def load_state(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation state from Redis.
        
        Args:
            contact_id: Unique contact/buyer identifier
            
        Returns:
            State dictionary if found and valid, None if expired/missing
        """
        if not self.enabled:
            logger.debug("Conversation memory disabled, skipping load")
            return None
            
        if not contact_id:
            logger.error("Cannot load state: contact_id is empty")
            return None
            
        try:
            cache_key = self._get_cache_key(contact_id)
            storage_data = await self.cache.get(cache_key)
            
            if not storage_data:
                logger.debug(f"No saved conversation state found for {contact_id}")
                return None
            
            # Decompress if needed
            if storage_data.get("compressed"):
                compressed_bytes = bytes.fromhex(storage_data["data"])
                json_bytes = gzip.decompress(compressed_bytes)
                json_data = json_bytes.decode('utf-8')
            else:
                json_data = storage_data["data"]
            
            # Parse JSON
            state = json.loads(json_data)
            
            # Validate state version (for future migrations)
            state_version = state.get("state_version", "0.0")
            if state_version != self.STATE_VERSION:
                logger.warning(
                    f"State version mismatch for {contact_id}: "
                    f"{state_version} != {self.STATE_VERSION}"
                )
                # Could trigger migration logic here in the future
            
            logger.info(
                f"Loaded conversation state for {contact_id} "
                f"(last interaction: {state.get('last_interaction_timestamp', 'unknown')})"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error loading conversation state for {contact_id}: {e}", exc_info=True)
            return None

    async def clear_state(self, contact_id: str) -> bool:
        """
        Delete conversation state for a contact.
        
        Args:
            contact_id: Unique contact/buyer identifier
            
        Returns:
            True if deleted, False otherwise
        """
        if not contact_id:
            logger.error("Cannot clear state: contact_id is empty")
            return False
            
        try:
            cache_key = self._get_cache_key(contact_id)
            success = await self.cache.delete(cache_key)
            
            if success:
                logger.info(f"Cleared conversation state for {contact_id}")
            else:
                logger.debug(f"No state to clear for {contact_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error clearing conversation state for {contact_id}: {e}", exc_info=True)
            return False

    def _prepare_state_for_storage(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare state for storage by trimming conversation history and extracting key fields.
        
        Args:
            state: Full bot state dictionary
            
        Returns:
            Prepared state dictionary with only necessary fields
        """
        # Extract core fields to persist
        persist_state = {}
        
        # Conversation history (trimmed)
        conversation_history = state.get("conversation_history", [])
        if len(conversation_history) > self.max_history_messages:
            # Keep most recent messages
            conversation_history = conversation_history[-self.max_history_messages:]
            logger.debug(
                f"Trimmed conversation history to {self.max_history_messages} messages"
            )
        persist_state["conversation_history"] = conversation_history
        
        # Financial assessment
        persist_state["financial_readiness_score"] = state.get("financial_readiness_score", 0.0)
        persist_state["buying_motivation_score"] = state.get("buying_motivation_score", 0.0)
        
        # Budget and preferences
        persist_state["budget_range"] = state.get("budget_range")
        persist_state["property_preferences"] = state.get("property_preferences")
        
        # Qualification context
        persist_state["urgency_level"] = state.get("urgency_level", "unknown")
        persist_state["financing_status"] = state.get("financing_status", "unknown")
        persist_state["current_qualification_step"] = state.get("current_qualification_step", "budget")
        persist_state["current_journey_stage"] = state.get("current_journey_stage", "discovery")
        
        # Buyer persona
        persist_state["buyer_persona"] = state.get("buyer_persona")
        
        # Temperature/qualification
        persist_state["buyer_temperature"] = state.get("buyer_temperature")
        persist_state["is_qualified"] = state.get("is_qualified", False)
        
        # Objection history
        persist_state["objection_history"] = state.get("objection_history", [])
        
        # Contact info
        persist_state["buyer_name"] = state.get("buyer_name")
        persist_state["buyer_phone"] = state.get("buyer_phone")
        persist_state["buyer_email"] = state.get("buyer_email")
        
        return persist_state

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get conversation memory statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "enabled": self.enabled,
            "ttl_days": self.ttl_days,
            "ttl_seconds": self.ttl_seconds,
            "compress_threshold_bytes": self.compress_threshold,
            "max_history_messages": self.max_history_messages,
            "state_version": self.STATE_VERSION,
        }


# Global singleton instance
_buyer_conversation_memory_instance: Optional[BuyerConversationMemory] = None


def get_buyer_conversation_memory() -> BuyerConversationMemory:
    """Get or create the global BuyerConversationMemory singleton."""
    global _buyer_conversation_memory_instance
    if _buyer_conversation_memory_instance is None:
        _buyer_conversation_memory_instance = BuyerConversationMemory()
    return _buyer_conversation_memory_instance


def reset_buyer_conversation_memory() -> None:
    """Reset the singleton instance (for testing)."""
    global _buyer_conversation_memory_instance
    _buyer_conversation_memory_instance = None
