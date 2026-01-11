"""
Persistent Chat Memory Service - Enhanced Context & Session Management
=====================================================================

Extends Redis-based storage to support persistent chat sessions with:
- Cross-screen context synchronization
- Process-aware memory management
- Real estate workflow state tracking
- Performance-optimized session storage
- Automatic context expiration and cleanup

Integrates with existing RedisConversationService while adding enhanced
features for persistent chat functionality.

Business Impact:
- Seamless chat continuity across platform screens
- Process-aware guidance throughout sales workflow
- Improved agent productivity through context retention
- Reduced cognitive load with intelligent memory management

Author: EnterpriseHub AI Platform
Date: January 10, 2026
Version: 1.0.0
"""

import asyncio
import json
import logging
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis

from ..services.redis_conversation_service import redis_conversation_service, ConversationMessage
from ..streamlit_components.persistent_claude_chat import (
    ProcessContext, ChatSession, RealtorProcessStage
)
from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


class MemoryPriority(str, Enum):
    """Priority levels for memory storage and retention."""
    CRITICAL = "critical"      # Never expires - key insights, preferences
    HIGH = "high"             # 30 days - important workflow context
    MEDIUM = "medium"         # 7 days - standard conversation context
    LOW = "low"               # 24 hours - temporary session data


class ContextSyncStatus(str, Enum):
    """Status of context synchronization across screens."""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class PersistentMemoryEntry:
    """Enhanced memory entry with priority and metadata."""
    key: str
    data: Any
    priority: MemoryPriority
    created_at: datetime
    last_accessed: datetime
    access_count: int
    tags: List[str]
    expires_at: Optional[datetime] = None

    def update_access(self):
        """Update access tracking."""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class ProcessMemory:
    """Memory specific to real estate process stages."""
    stage: RealtorProcessStage
    lead_context: Dict[str, Any]
    discoveries: List[str]
    objections_handled: List[str]
    successful_strategies: List[str]
    timestamp: datetime
    completion_score: float = 0.0


@dataclass
class CrossScreenContext:
    """Context synchronization across different screens."""
    agent_id: str
    session_id: str
    screen_contexts: Dict[str, Dict[str, Any]]  # screen_name -> context
    active_screen: str
    last_sync: datetime
    sync_status: ContextSyncStatus


class PersistentChatMemoryService:
    """
    Enhanced memory service for persistent chat with process awareness.

    Provides sophisticated memory management for real estate workflows,
    including cross-screen synchronization and intelligent context retention.
    """

    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, PersistentMemoryEntry] = {}
        self.process_memory_cache: Dict[str, ProcessMemory] = {}
        self.cross_screen_cache: Dict[str, CrossScreenContext] = {}

        # Initialize Redis connection
        self._initialize_redis()

        # Memory retention policies
        self.retention_policies = {
            MemoryPriority.CRITICAL: timedelta(days=365),  # 1 year
            MemoryPriority.HIGH: timedelta(days=30),       # 30 days
            MemoryPriority.MEDIUM: timedelta(days=7),      # 7 days
            MemoryPriority.LOW: timedelta(hours=24)        # 24 hours
        }

        logger.info("PersistentChatMemoryService initialized")

    def _initialize_redis(self):
        """Initialize Redis connection with fallback."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url or "redis://localhost:6379/0",
                decode_responses=False
            )
            self.redis_client.ping()
            logger.info("Redis connection established for persistent chat memory")
        except (redis.ConnectionError, AttributeError):
            logger.warning("Redis unavailable - using in-memory storage for chat memory")
            self.redis_client = None

    def _generate_memory_key(self, agent_id: str, context_type: str, identifier: str = "") -> str:
        """Generate Redis key for memory storage."""
        base = f"chat_memory:{agent_id}:{context_type}"
        if identifier:
            base += f":{identifier}"
        return base

    def _generate_process_key(self, agent_id: str, stage: RealtorProcessStage) -> str:
        """Generate key for process-specific memory."""
        return f"process_memory:{agent_id}:{stage.value}"

    def _generate_cross_screen_key(self, agent_id: str, session_id: str) -> str:
        """Generate key for cross-screen context."""
        return f"cross_screen:{agent_id}:{session_id}"

    async def store_chat_session(
        self,
        chat_session: ChatSession,
        priority: MemoryPriority = MemoryPriority.MEDIUM
    ) -> bool:
        """
        Store complete chat session with priority-based retention.

        Args:
            chat_session: Complete chat session object
            priority: Storage priority level

        Returns:
            Success status
        """
        try:
            key = self._generate_memory_key(
                chat_session.agent_id, "session", chat_session.session_id
            )

            # Prepare data for storage
            session_data = {
                "session_id": chat_session.session_id,
                "agent_id": chat_session.agent_id,
                "conversation_history": [
                    {
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                        "timestamp": msg.get("timestamp").isoformat() if isinstance(msg.get("timestamp"), datetime) else str(msg.get("timestamp")),
                        "confidence": msg.get("confidence", 0.0)
                    }
                    for msg in chat_session.conversation_history
                ],
                "process_context": asdict(chat_session.process_context),
                "performance_metrics": chat_session.performance_metrics,
                "persistent_insights": chat_session.persistent_insights,
                "created_at": chat_session.created_at.isoformat(),
                "last_activity": chat_session.last_activity.isoformat(),
                "total_interactions": chat_session.total_interactions
            }

            # Calculate expiration
            expires_at = datetime.now() + self.retention_policies[priority]

            # Create memory entry
            memory_entry = PersistentMemoryEntry(
                key=key,
                data=session_data,
                priority=priority,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                tags=["chat_session", chat_session.agent_id],
                expires_at=expires_at
            )

            # Store in Redis if available
            if self.redis_client:
                serialized_data = pickle.dumps(memory_entry)
                ttl = int(self.retention_policies[priority].total_seconds())

                pipeline = self.redis_client.pipeline()
                pipeline.setex(key, ttl, serialized_data)
                # Index by agent for easy retrieval
                pipeline.sadd(f"agent_sessions:{chat_session.agent_id}", key)
                pipeline.execute()

                logger.debug(f"Chat session stored in Redis: {key}")

            # Store in local cache
            self.memory_cache[key] = memory_entry

            return True

        except Exception as e:
            logger.error(f"Error storing chat session: {e}")
            return False

    async def retrieve_chat_session(
        self,
        agent_id: str,
        session_id: str
    ) -> Optional[ChatSession]:
        """
        Retrieve chat session by agent and session ID.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier

        Returns:
            ChatSession object if found, None otherwise
        """
        try:
            key = self._generate_memory_key(agent_id, "session", session_id)

            # Try Redis first
            if self.redis_client:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        memory_entry = pickle.loads(data)
                        memory_entry.update_access()

                        # Update access count in Redis
                        self.redis_client.setex(
                            key,
                            int(self.retention_policies[memory_entry.priority].total_seconds()),
                            pickle.dumps(memory_entry)
                        )

                        return self._deserialize_chat_session(memory_entry.data)
                except Exception as e:
                    logger.warning(f"Redis retrieval failed: {e}")

            # Try local cache
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired():
                    entry.update_access()
                    return self._deserialize_chat_session(entry.data)
                else:
                    del self.memory_cache[key]

            return None

        except Exception as e:
            logger.error(f"Error retrieving chat session: {e}")
            return None

    def _deserialize_chat_session(self, data: Dict[str, Any]) -> ChatSession:
        """Deserialize chat session data."""
        # Parse process context
        process_data = data.get("process_context", {})
        process_context = ProcessContext(
            stage=RealtorProcessStage(process_data.get("stage", "lead_capture")),
            lead_id=process_data.get("lead_id"),
            property_ids=process_data.get("property_ids", []),
            client_type=process_data.get("client_type", "buyer"),
            urgency=process_data.get("urgency", "medium"),
            current_screen=process_data.get("current_screen", "dashboard"),
            active_tasks=process_data.get("active_tasks", []),
            recent_actions=process_data.get("recent_actions", []),
            workflow_progress=process_data.get("workflow_progress", {}),
            last_updated=datetime.fromisoformat(process_data.get("last_updated")) if process_data.get("last_updated") else datetime.now()
        )

        # Parse conversation history
        conversation_history = []
        for msg in data.get("conversation_history", []):
            parsed_msg = {
                "role": msg.get("role"),
                "content": msg.get("content"),
                "timestamp": datetime.fromisoformat(msg.get("timestamp")) if isinstance(msg.get("timestamp"), str) else msg.get("timestamp"),
                "confidence": msg.get("confidence", 0.0)
            }
            conversation_history.append(parsed_msg)

        # Create chat session
        return ChatSession(
            session_id=data.get("session_id"),
            agent_id=data.get("agent_id"),
            process_context=process_context,
            conversation_history=conversation_history,
            persistent_insights=data.get("persistent_insights", []),
            performance_metrics=data.get("performance_metrics", {}),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now(),
            last_activity=datetime.fromisoformat(data.get("last_activity")) if data.get("last_activity") else datetime.now(),
            total_interactions=data.get("total_interactions", 0)
        )

    async def store_process_memory(
        self,
        agent_id: str,
        process_memory: ProcessMemory,
        priority: MemoryPriority = MemoryPriority.HIGH
    ) -> bool:
        """
        Store process-specific memory for workflow guidance.

        Args:
            agent_id: Agent identifier
            process_memory: Process memory object
            priority: Storage priority

        Returns:
            Success status
        """
        try:
            key = self._generate_process_key(agent_id, process_memory.stage)

            # Serialize process memory
            memory_data = {
                "stage": process_memory.stage.value,
                "lead_context": process_memory.lead_context,
                "discoveries": process_memory.discoveries,
                "objections_handled": process_memory.objections_handled,
                "successful_strategies": process_memory.successful_strategies,
                "timestamp": process_memory.timestamp.isoformat(),
                "completion_score": process_memory.completion_score
            }

            expires_at = datetime.now() + self.retention_policies[priority]

            memory_entry = PersistentMemoryEntry(
                key=key,
                data=memory_data,
                priority=priority,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                tags=["process_memory", agent_id, process_memory.stage.value],
                expires_at=expires_at
            )

            # Store in Redis
            if self.redis_client:
                ttl = int(self.retention_policies[priority].total_seconds())
                self.redis_client.setex(key, ttl, pickle.dumps(memory_entry))

                # Index by agent and stage
                self.redis_client.sadd(f"agent_process:{agent_id}", key)
                self.redis_client.sadd(f"stage_memory:{process_memory.stage.value}", key)

            # Store in local cache
            self.process_memory_cache[key] = process_memory

            logger.debug(f"Process memory stored: {agent_id}, {process_memory.stage}")
            return True

        except Exception as e:
            logger.error(f"Error storing process memory: {e}")
            return False

    async def retrieve_process_memory(
        self,
        agent_id: str,
        stage: RealtorProcessStage
    ) -> Optional[ProcessMemory]:
        """
        Retrieve process-specific memory.

        Args:
            agent_id: Agent identifier
            stage: Process stage

        Returns:
            ProcessMemory object if found
        """
        try:
            key = self._generate_process_key(agent_id, stage)

            # Try Redis first
            if self.redis_client:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        memory_entry = pickle.loads(data)
                        memory_entry.update_access()
                        return self._deserialize_process_memory(memory_entry.data)
                except Exception as e:
                    logger.warning(f"Redis process memory retrieval failed: {e}")

            # Try local cache
            if key in self.process_memory_cache:
                return self.process_memory_cache[key]

            return None

        except Exception as e:
            logger.error(f"Error retrieving process memory: {e}")
            return None

    def _deserialize_process_memory(self, data: Dict[str, Any]) -> ProcessMemory:
        """Deserialize process memory data."""
        return ProcessMemory(
            stage=RealtorProcessStage(data.get("stage")),
            lead_context=data.get("lead_context", {}),
            discoveries=data.get("discoveries", []),
            objections_handled=data.get("objections_handled", []),
            successful_strategies=data.get("successful_strategies", []),
            timestamp=datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else datetime.now(),
            completion_score=data.get("completion_score", 0.0)
        )

    async def sync_cross_screen_context(
        self,
        agent_id: str,
        session_id: str,
        screen_name: str,
        context: Dict[str, Any]
    ) -> CrossScreenContext:
        """
        Synchronize context across different screens.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            screen_name: Current screen name
            context: Screen-specific context

        Returns:
            Updated cross-screen context
        """
        try:
            key = self._generate_cross_screen_key(agent_id, session_id)

            # Get existing context or create new
            cross_context = await self.get_cross_screen_context(agent_id, session_id)

            if not cross_context:
                cross_context = CrossScreenContext(
                    agent_id=agent_id,
                    session_id=session_id,
                    screen_contexts={},
                    active_screen=screen_name,
                    last_sync=datetime.now(),
                    sync_status=ContextSyncStatus.SYNCED
                )

            # Update screen context
            cross_context.screen_contexts[screen_name] = {
                **context,
                "last_updated": datetime.now().isoformat()
            }
            cross_context.active_screen = screen_name
            cross_context.last_sync = datetime.now()
            cross_context.sync_status = ContextSyncStatus.SYNCED

            # Store updated context
            if self.redis_client:
                ttl = int(timedelta(hours=24).total_seconds())  # 24 hours
                self.redis_client.setex(key, ttl, pickle.dumps(cross_context))

            self.cross_screen_cache[key] = cross_context

            logger.debug(f"Cross-screen context synced: {agent_id}, {screen_name}")
            return cross_context

        except Exception as e:
            logger.error(f"Error syncing cross-screen context: {e}")
            return CrossScreenContext(
                agent_id=agent_id,
                session_id=session_id,
                screen_contexts={screen_name: context},
                active_screen=screen_name,
                last_sync=datetime.now(),
                sync_status=ContextSyncStatus.ERROR
            )

    async def get_cross_screen_context(
        self,
        agent_id: str,
        session_id: str
    ) -> Optional[CrossScreenContext]:
        """Get cross-screen context for session."""
        try:
            key = self._generate_cross_screen_key(agent_id, session_id)

            # Try Redis first
            if self.redis_client:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        return pickle.loads(data)
                except Exception as e:
                    logger.warning(f"Redis cross-screen retrieval failed: {e}")

            # Try local cache
            return self.cross_screen_cache.get(key)

        except Exception as e:
            logger.error(f"Error getting cross-screen context: {e}")
            return None

    async def get_recent_sessions(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent chat sessions for agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of sessions

        Returns:
            List of session metadata
        """
        try:
            sessions = []

            if self.redis_client:
                # Get session keys for agent
                session_keys = self.redis_client.smembers(f"agent_sessions:{agent_id}")

                for key in list(session_keys)[:limit]:
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            memory_entry = pickle.loads(data)
                            session_data = memory_entry.data

                            sessions.append({
                                "session_id": session_data.get("session_id"),
                                "last_activity": session_data.get("last_activity"),
                                "total_interactions": session_data.get("total_interactions", 0),
                                "created_at": session_data.get("created_at"),
                                "access_count": memory_entry.access_count
                            })
                    except:
                        # Remove invalid key
                        self.redis_client.srem(f"agent_sessions:{agent_id}", key)

            # Sort by last activity
            sessions.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
            return sessions[:limit]

        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            return []

    async def cleanup_expired_memory(self) -> Dict[str, int]:
        """
        Clean up expired memory entries.

        Returns:
            Cleanup statistics
        """
        cleanup_stats = {
            "sessions_cleaned": 0,
            "process_memory_cleaned": 0,
            "cross_screen_cleaned": 0,
            "total_cleaned": 0
        }

        try:
            current_time = datetime.now()

            # Clean local caches
            expired_keys = []

            # Check memory cache
            for key, entry in self.memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self.memory_cache[key]
                cleanup_stats["sessions_cleaned"] += 1

            # Redis cleanup happens automatically with TTL
            # But we can clean up our indexes
            if self.redis_client:
                # Clean up agent session indexes
                for agent_sessions_key in self.redis_client.scan_iter(match="agent_sessions:*"):
                    session_keys = self.redis_client.smembers(agent_sessions_key)
                    for session_key in session_keys:
                        if not self.redis_client.exists(session_key):
                            self.redis_client.srem(agent_sessions_key, session_key)
                            cleanup_stats["sessions_cleaned"] += 1

            cleanup_stats["total_cleaned"] = sum(cleanup_stats.values())

            logger.info(f"Memory cleanup completed: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            return cleanup_stats

    async def get_memory_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get memory usage statistics.

        Args:
            agent_id: Optional agent filter

        Returns:
            Memory statistics
        """
        stats = {
            "total_sessions": 0,
            "total_process_memories": 0,
            "total_cross_screen_contexts": 0,
            "memory_usage_mb": 0,
            "cache_hit_rate": 0.0,
            "avg_session_size": 0,
            "retention_breakdown": {priority.value: 0 for priority in MemoryPriority}
        }

        try:
            # Calculate local cache statistics
            total_size = 0
            session_sizes = []

            for entry in self.memory_cache.values():
                if agent_id is None or agent_id in entry.tags:
                    stats["total_sessions"] += 1
                    entry_size = len(pickle.dumps(entry.data))
                    total_size += entry_size
                    session_sizes.append(entry_size)
                    stats["retention_breakdown"][entry.priority.value] += 1

            stats["memory_usage_mb"] = total_size / (1024 * 1024)
            stats["avg_session_size"] = sum(session_sizes) / len(session_sizes) if session_sizes else 0

            # Redis statistics (if available)
            if self.redis_client:
                redis_info = self.redis_client.info("memory")
                stats["redis_memory_mb"] = redis_info.get("used_memory", 0) / (1024 * 1024)

            return stats

        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}")
            return stats


# Global instance for easy access
persistent_chat_memory_service = PersistentChatMemoryService()


# Export key classes and functions
__all__ = [
    'PersistentChatMemoryService',
    'PersistentMemoryEntry',
    'ProcessMemory',
    'CrossScreenContext',
    'MemoryPriority',
    'ContextSyncStatus',
    'persistent_chat_memory_service'
]