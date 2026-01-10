"""
Redis Conversation Persistence Service

Provides persistent storage for Claude agent conversations with Redis backend,
enabling conversation continuity across sessions and improved agent context.
"""

import redis
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pickle

from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Structure for individual conversation messages"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    lead_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


@dataclass
class AgentConversationState:
    """Complete agent conversation state"""
    agent_id: str
    messages: List[ConversationMessage]
    active_leads: List[str]
    last_activity: datetime
    preferences: Dict[str, Any]
    total_conversations: int


class RedisConversationService:
    """
    Redis-based conversation persistence service for Claude agents.

    Features:
    - Persistent conversation history across sessions
    - Automatic expiration (30-day default)
    - Lead-specific conversation contexts
    - Agent preference learning
    - Performance optimized with pipeline operations
    """

    def __init__(self):
        self.redis_client = redis.from_url(
            settings.redis_url or "redis://localhost:6379/0",
            decode_responses=False  # We'll handle encoding manually for pickle
        )
        self.default_ttl = 30 * 24 * 60 * 60  # 30 days in seconds

        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError:
            logger.error("Failed to connect to Redis - falling back to in-memory storage")
            self.redis_client = None

    def _get_conversation_key(self, agent_id: str) -> str:
        """Generate Redis key for agent conversations"""
        return f"agent_conversations:{agent_id}"

    def _get_agent_state_key(self, agent_id: str) -> str:
        """Generate Redis key for agent state"""
        return f"agent_state:{agent_id}"

    def _get_lead_context_key(self, agent_id: str, lead_id: str) -> str:
        """Generate Redis key for lead-specific context"""
        return f"lead_context:{agent_id}:{lead_id}"

    async def store_conversation_message(
        self,
        agent_id: str,
        role: str,
        content: str,
        lead_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None
    ) -> bool:
        """
        Store a single conversation message with metadata.

        Args:
            agent_id: Unique agent identifier
            role: 'user' or 'assistant'
            content: Message content
            lead_id: Optional lead context
            context: Additional context metadata
            confidence: AI response confidence (for assistant messages)

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis not available - conversation not persisted")
            return False

        try:
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                lead_id=lead_id,
                context=context or {},
                confidence=confidence
            )

            # Store message in conversation history
            conversation_key = self._get_conversation_key(agent_id)
            message_data = pickle.dumps(asdict(message))

            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.rpush(conversation_key, message_data)
            pipe.expire(conversation_key, self.default_ttl)

            # Limit conversation history to last 100 messages
            pipe.ltrim(conversation_key, -100, -1)

            pipe.execute()

            # Update agent state
            await self._update_agent_state(agent_id, lead_id)

            logger.debug(f"Stored conversation message for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing conversation message: {str(e)}")
            return False

    async def get_conversation_history(
        self,
        agent_id: str,
        limit: int = 20,
        include_context: bool = False
    ) -> List[ConversationMessage]:
        """
        Retrieve conversation history for an agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of messages to return
            include_context: Whether to include full context metadata

        Returns:
            List of conversation messages, ordered chronologically
        """
        if not self.redis_client:
            return []

        try:
            conversation_key = self._get_conversation_key(agent_id)

            # Get last N messages
            message_data_list = self.redis_client.lrange(conversation_key, -limit, -1)

            messages = []
            for message_data in message_data_list:
                try:
                    message_dict = pickle.loads(message_data)

                    # Reconstruct datetime objects
                    message_dict['timestamp'] = datetime.fromisoformat(
                        message_dict['timestamp']
                    ) if isinstance(message_dict['timestamp'], str) else message_dict['timestamp']

                    # Filter context if not requested
                    if not include_context:
                        message_dict['context'] = {}

                    messages.append(ConversationMessage(**message_dict))

                except Exception as e:
                    logger.warning(f"Error parsing message: {str(e)}")
                    continue

            logger.debug(f"Retrieved {len(messages)} messages for agent {agent_id}")
            return messages

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []

    async def get_agent_state(self, agent_id: str) -> Optional[AgentConversationState]:
        """Get complete agent state including preferences and activity"""
        if not self.redis_client:
            return None

        try:
            state_key = self._get_agent_state_key(agent_id)
            state_data = self.redis_client.get(state_key)

            if not state_data:
                # Initialize new agent state
                return AgentConversationState(
                    agent_id=agent_id,
                    messages=[],
                    active_leads=[],
                    last_activity=datetime.now(),
                    preferences={},
                    total_conversations=0
                )

            state_dict = pickle.loads(state_data)

            # Reconstruct datetime objects
            state_dict['last_activity'] = datetime.fromisoformat(
                state_dict['last_activity']
            ) if isinstance(state_dict['last_activity'], str) else state_dict['last_activity']

            return AgentConversationState(**state_dict)

        except Exception as e:
            logger.error(f"Error retrieving agent state: {str(e)}")
            return None

    async def _update_agent_state(self, agent_id: str, lead_id: Optional[str] = None):
        """Update agent state with latest activity"""
        try:
            current_state = await self.get_agent_state(agent_id)
            if not current_state:
                current_state = AgentConversationState(
                    agent_id=agent_id,
                    messages=[],
                    active_leads=[],
                    last_activity=datetime.now(),
                    preferences={},
                    total_conversations=0
                )

            # Update activity
            current_state.last_activity = datetime.now()
            current_state.total_conversations += 1

            # Add lead to active leads if provided
            if lead_id and lead_id not in current_state.active_leads:
                current_state.active_leads.append(lead_id)
                # Keep only last 10 active leads
                current_state.active_leads = current_state.active_leads[-10:]

            # Store updated state
            state_key = self._get_agent_state_key(agent_id)
            state_data = pickle.dumps(asdict(current_state))

            self.redis_client.setex(state_key, self.default_ttl, state_data)

        except Exception as e:
            logger.error(f"Error updating agent state: {str(e)}")

    async def get_lead_conversation_context(
        self,
        agent_id: str,
        lead_id: str
    ) -> List[ConversationMessage]:
        """Get conversation messages specific to a lead"""
        try:
            all_messages = await self.get_conversation_history(agent_id, limit=100, include_context=True)

            # Filter messages for this specific lead
            lead_messages = [
                msg for msg in all_messages
                if msg.lead_id == lead_id
            ]

            return lead_messages[-20:]  # Return last 20 lead-specific messages

        except Exception as e:
            logger.error(f"Error retrieving lead conversation context: {str(e)}")
            return []

    async def store_agent_preferences(
        self,
        agent_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Store agent-specific preferences and learning"""
        try:
            current_state = await self.get_agent_state(agent_id)
            if current_state:
                current_state.preferences.update(preferences)

                state_key = self._get_agent_state_key(agent_id)
                state_data = pickle.dumps(asdict(current_state))

                self.redis_client.setex(state_key, self.default_ttl, state_data)
                return True

        except Exception as e:
            logger.error(f"Error storing agent preferences: {str(e)}")

        return False

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent statistics"""
        try:
            state = await self.get_agent_state(agent_id)
            if not state:
                return {"error": "Agent not found"}

            # Calculate additional stats
            recent_messages = await self.get_conversation_history(agent_id, limit=50)
            recent_activity = len([
                msg for msg in recent_messages
                if msg.timestamp > datetime.now() - timedelta(hours=24)
            ])

            avg_confidence = 0.0
            confidence_scores = [
                msg.confidence for msg in recent_messages
                if msg.role == 'assistant' and msg.confidence is not None
            ]
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)

            return {
                "agent_id": agent_id,
                "total_conversations": state.total_conversations,
                "active_leads": len(state.active_leads),
                "last_activity": state.last_activity.isoformat(),
                "recent_activity_24h": recent_activity,
                "average_confidence": round(avg_confidence, 3),
                "preferences": state.preferences,
                "status": "active" if state.last_activity > datetime.now() - timedelta(hours=24) else "inactive"
            }

        except Exception as e:
            logger.error(f"Error calculating agent stats: {str(e)}")
            return {"error": str(e)}

    async def cleanup_expired_conversations(self) -> int:
        """Clean up expired conversations (maintenance function)"""
        try:
            # This is handled automatically by Redis TTL, but we can add custom cleanup logic here
            # For now, just return 0 as Redis handles expiration
            return 0

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0

    def health_check(self) -> Dict[str, Any]:
        """Check Redis connection and service health"""
        try:
            if not self.redis_client:
                return {"status": "error", "message": "Redis client not initialized"}

            # Test Redis connection
            self.redis_client.ping()

            # Get Redis info
            info = self.redis_client.info()

            return {
                "status": "healthy",
                "redis_connected": True,
                "redis_version": info.get('redis_version', 'unknown'),
                "memory_usage": info.get('used_memory_human', 'unknown'),
                "connected_clients": info.get('connected_clients', 'unknown')
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "redis_connected": False
            }


# Global service instance
redis_conversation_service = RedisConversationService()