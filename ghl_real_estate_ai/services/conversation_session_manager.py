"""
Conversation Session Manager
Manages persistent conversation state across chat interactions
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class ConversationSessionManager:
    """
    Manages conversation sessions for bot interactions.

    Session Structure (Redis):
    {
        "conversation_id": "uuid",
        "bot_type": "jorge-seller-bot",
        "lead_id": "lead_123",
        "lead_name": "John Doe",
        "created_at": "ISO timestamp",
        "last_activity": "ISO timestamp",
        "history": [{"role": "user", "content": "...", "timestamp": "..."}],
        "bot_state": {} # Latest bot workflow state
    }
    """

    SESSION_TTL = 86400  # 24 hours

    def __init__(self):
        self.cache = get_cache_service()

    async def create_session(self, bot_type: str, lead_id: str, lead_name: str) -> str:
        """Create new conversation session"""
        conversation_id = str(uuid.uuid4())

        session_data = {
            "conversation_id": conversation_id,
            "bot_type": bot_type,
            "lead_id": lead_id,
            "lead_name": lead_name,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "history": [],
            "bot_state": {},
        }

        await self.cache.set(f"conversation:{conversation_id}", session_data, ttl=self.SESSION_TTL)

        # Index by lead_id for lookup
        await self.cache.sadd(f"conversations:lead:{lead_id}", conversation_id)

        logger.info(f"Created conversation session {conversation_id} for lead {lead_id} with bot {bot_type}")
        return conversation_id

    async def get_session(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation session"""
        session = await self.cache.get(f"conversation:{conversation_id}")
        if session:
            # Refresh TTL on access
            await self.cache.expire(f"conversation:{conversation_id}", self.SESSION_TTL)
        return session

    async def add_message(
        self, conversation_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add message to conversation history"""
        session = await self.get_session(conversation_id)
        if not session:
            raise ValueError(f"Conversation {conversation_id} not found")

        message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}

        if metadata:
            message["metadata"] = metadata

        session["history"].append(message)
        session["last_activity"] = datetime.now().isoformat()

        await self.cache.set(f"conversation:{conversation_id}", session, ttl=self.SESSION_TTL)

        logger.debug(f"Added {role} message to conversation {conversation_id}")

    async def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history formatted for bots"""
        session = await self.get_session(conversation_id)
        if not session:
            return []

        # Return in bot-compatible format (role + content only)
        return [{"role": msg["role"], "content": msg["content"]} for msg in session.get("history", [])]

    async def get_full_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get full conversation history with metadata"""
        session = await self.get_session(conversation_id)
        if not session:
            return []

        return session.get("history", [])

    async def update_session_state(self, conversation_id: str, state: Dict[str, Any]) -> None:
        """Update bot workflow state for session"""
        session = await self.get_session(conversation_id)
        if not session:
            raise ValueError(f"Conversation {conversation_id} not found")

        session["bot_state"] = state
        session["last_activity"] = datetime.now().isoformat()

        await self.cache.set(f"conversation:{conversation_id}", session, ttl=self.SESSION_TTL)

    async def get_session_state(self, conversation_id: str) -> Dict[str, Any]:
        """Get bot workflow state for session"""
        session = await self.get_session(conversation_id)
        if not session:
            return {}

        return session.get("bot_state", {})

    async def get_lead_conversations(self, lead_id: str) -> List[str]:
        """Get all conversation IDs for a lead"""
        conversation_ids = await self.cache.smembers(f"conversations:lead:{lead_id}")
        return list(conversation_ids) if conversation_ids else []

    async def get_active_conversations(self, bot_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of active conversations, optionally filtered by bot type"""
        # ROADMAP-090: For large scale, implement better indexing (Redis search, DB index)
        # For now, scan for conversations active in last 24 hours
        active_conversations = []

        # Get conversation keys (would implement better indexing for production scale)
        # This is a simplified implementation for demo purposes

        return active_conversations

    async def extend_session_ttl(self, conversation_id: str, additional_hours: int = 24) -> bool:
        """Extend session TTL by specified hours"""
        session = await self.get_session(conversation_id)
        if not session:
            return False

        new_ttl = self.SESSION_TTL + (additional_hours * 3600)
        await self.cache.expire(f"conversation:{conversation_id}", new_ttl)

        logger.info(f"Extended session {conversation_id} TTL by {additional_hours} hours")
        return True

    async def delete_session(self, conversation_id: str) -> bool:
        """Delete conversation session and cleanup indices"""
        session = await self.get_session(conversation_id)
        if not session:
            return False

        lead_id = session.get("lead_id")

        # Remove from Redis
        await self.cache.delete(f"conversation:{conversation_id}")

        # Remove from lead index
        if lead_id:
            await self.cache.srem(f"conversations:lead:{lead_id}", conversation_id)

        logger.info(f"Deleted conversation session {conversation_id}")
        return True

    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a conversation"""
        session = await self.get_session(conversation_id)
        if not session:
            return None

        history = session.get("history", [])

        return {
            "conversation_id": conversation_id,
            "bot_type": session.get("bot_type"),
            "lead_id": session.get("lead_id"),
            "lead_name": session.get("lead_name"),
            "created_at": session.get("created_at"),
            "last_activity": session.get("last_activity"),
            "message_count": len(history),
            "user_messages": len([msg for msg in history if msg["role"] == "user"]),
            "bot_messages": len([msg for msg in history if msg["role"] == "bot"]),
            "duration_minutes": self._calculate_duration_minutes(
                session.get("created_at"), session.get("last_activity")
            ),
            "bot_state": session.get("bot_state", {}),
        }

    def _calculate_duration_minutes(self, created_at: str, last_activity: str) -> Optional[float]:
        """Calculate conversation duration in minutes"""
        try:
            if not created_at or not last_activity:
                return None

            created = datetime.fromisoformat(created_at)
            last = datetime.fromisoformat(last_activity)

            duration = last - created
            return round(duration.total_seconds() / 60, 2)

        except Exception:
            return None

    async def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions (would be called by background task)"""
        # Redis TTL handles automatic expiration, but this could clean up indices
        cleaned_count = 0

        # Implementation would scan for expired indices and clean them up
        # For now, rely on Redis TTL for automatic cleanup

        logger.debug(f"Cleaned up {cleaned_count} expired conversation sessions")
        return cleaned_count


# Singleton instance
_session_manager: Optional[ConversationSessionManager] = None


def get_session_manager() -> ConversationSessionManager:
    """Get singleton instance of conversation session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = ConversationSessionManager()
        logger.info("Initialized ConversationSessionManager singleton")
    return _session_manager
