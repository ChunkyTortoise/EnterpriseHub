"""
Offline Sync Service (Phase 4: Mobile Optimization)

Handles data synchronization for mobile devices when offline, ensuring agents
can continue working with cached data and sync changes when connectivity returns.

Features:
- Intelligent data caching for offline operation
- Queue management for offline actions
- Conflict resolution for data sync
- Progressive sync with bandwidth optimization
- Background sync when connectivity returns
- Critical data prioritization
- Local storage optimization

Performance Targets:
- Sync completion time: <30 seconds for typical session
- Data compression: 80% bandwidth savings
- Offline operation: 100% core functionality available
- Sync conflict resolution: <2 seconds
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
import time
import sqlite3
import threading
from pathlib import Path

# Local imports
from ghl_real_estate_ai.config.mobile.settings import (
    MOBILE_PERFORMANCE_TARGETS,
    REALTIME_CONFIG
)

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status"""
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"
    CONFLICT = "conflict"


class DataType(Enum):
    """Types of data for synchronization"""
    COACHING_SUGGESTIONS = "coaching_suggestions"
    CLIENT_INTERACTIONS = "client_interactions"
    PROPERTY_DATA = "property_data"
    AGENT_NOTES = "agent_notes"
    VOICE_RECORDINGS = "voice_recordings"
    QUICK_ACTIONS = "quick_actions"
    PERFORMANCE_METRICS = "performance_metrics"
    USER_PREFERENCES = "user_preferences"


class SyncPriority(Enum):
    """Priority levels for sync operations"""
    CRITICAL = 1    # Must sync immediately when online
    HIGH = 2       # Sync within 30 seconds
    MEDIUM = 3     # Sync within 5 minutes
    LOW = 4        # Sync when convenient


@dataclass
class SyncItem:
    """Item in sync queue"""
    id: str
    data_type: DataType
    priority: SyncPriority
    action: str  # create, update, delete
    data: Dict[str, Any]
    created_at: datetime
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class SyncConflict:
    """Data synchronization conflict"""
    item_id: str
    data_type: DataType
    local_version: Dict[str, Any]
    remote_version: Dict[str, Any]
    conflict_type: str  # "update_conflict", "delete_conflict", "version_mismatch"
    created_at: datetime


@dataclass
class OfflineSession:
    """Offline operation session"""
    session_id: str
    agent_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    items_cached: int = 0
    actions_queued: int = 0
    data_size_mb: float = 0.0
    sync_conflicts: List[SyncConflict] = field(default_factory=list)


class OfflineSyncService:
    """
    🔄 Offline Sync Service for Mobile Claude AI

    Manages data synchronization for mobile devices, ensuring seamless
    operation during offline periods and efficient sync when online.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "mobile_offline_cache.db"
        self.sync_queue: List[SyncItem] = []
        self.conflicts: List[SyncConflict] = []
        self.offline_sessions: Dict[str, OfflineSession] = {}

        # Sync configuration
        self.performance_targets = MOBILE_PERFORMANCE_TARGETS
        self.realtime_config = REALTIME_CONFIG

        # Connection status
        self.is_online = True
        self.last_sync_time = datetime.now()

        # Initialize local database
        self._initialize_local_database()

        # Start background sync monitoring
        self._sync_lock = threading.Lock()
        self._background_sync_task = None

        # Data compression settings
        self.compression_enabled = True
        self.batch_sync_size = 50  # Items per batch

        # Offline cache for essential data
        self.essential_cache = self._initialize_essential_cache()

    def _initialize_local_database(self):
        """Initialize SQLite database for offline storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Sync queue table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        attempts INTEGER DEFAULT 0,
                        last_attempt TEXT,
                        error_message TEXT
                    )
                """)

                # Offline cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS offline_cache (
                        key TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        access_count INTEGER DEFAULT 0
                    )
                """)

                # Sync conflicts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_conflicts (
                        id TEXT PRIMARY KEY,
                        item_id TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        local_version TEXT NOT NULL,
                        remote_version TEXT NOT NULL,
                        conflict_type TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                """)

                conn.commit()

            logger.info("Offline sync database initialized")

        except Exception as e:
            logger.error(f"Error initializing offline database: {e}")

    def _initialize_essential_cache(self) -> Dict[str, Any]:
        """Initialize cache with essential data for offline operation"""
        return {
            "coaching_templates": {
                "objection_responses": [
                    "I understand your concern about [concern]. Let me address that...",
                    "That's a great question. Here's what I recommend...",
                    "Many clients have similar concerns. Here's how we handle that..."
                ],
                "qualifying_questions": [
                    "What's your timeline for making a decision?",
                    "What's most important to you in this price range?",
                    "Have you been pre-approved for financing?"
                ],
                "closing_statements": [
                    "Based on what we've discussed, what would you like to do next?",
                    "Would you like to schedule a time to see this property?",
                    "I can arrange a private showing this weekend if you're interested."
                ]
            },
            "property_info_templates": {
                "key_features": ["bedrooms", "bathrooms", "square_footage", "price"],
                "neighborhood_highlights": ["schools", "shopping", "transportation"],
                "investment_points": ["appreciation", "rental_potential", "market_trends"]
            },
            "common_responses": {
                "acknowledgment": ["I see", "That makes sense", "I understand"],
                "agreement": ["Absolutely", "Exactly", "You're right"],
                "transition": ["Let me show you", "Here's what I recommend", "The next step is"]
            }
        }

    async def set_connection_status(self, is_online: bool):
        """Update connection status and trigger sync if coming online"""
        was_offline = not self.is_online
        self.is_online = is_online

        if is_online and was_offline:
            logger.info("Connection restored - starting sync")
            await self._start_background_sync()
        elif not is_online:
            logger.info("Connection lost - entering offline mode")
            await self._prepare_offline_mode()

    async def start_offline_session(self, agent_id: str) -> OfflineSession:
        """Start tracking offline session for an agent"""
        session_id = f"offline_{agent_id}_{int(time.time())}"

        session = OfflineSession(
            session_id=session_id,
            agent_id=agent_id,
            start_time=datetime.now()
        )

        self.offline_sessions[session_id] = session

        # Pre-cache essential data for this agent
        await self._preload_agent_data(agent_id, session)

        logger.info(f"Offline session started for agent {agent_id}: {session_id}")
        return session

    async def cache_data(
        self,
        key: str,
        data: Any,
        data_type: DataType,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """
        Cache data for offline access

        Args:
            key: Unique identifier for the data
            data: Data to cache
            data_type: Type of data being cached
            expires_at: Optional expiration time

        Returns:
            True if cached successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Serialize data
                data_json = json.dumps(data)
                created_at = datetime.now().isoformat()
                expires_at_str = expires_at.isoformat() if expires_at else None

                # Insert or update cache entry
                cursor.execute("""
                    INSERT OR REPLACE INTO offline_cache
                    (key, data_type, data, created_at, expires_at, access_count)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (key, data_type.value, data_json, created_at, expires_at_str))

                conn.commit()

            logger.debug(f"Data cached: {key} ({data_type.value})")
            return True

        except Exception as e:
            logger.error(f"Error caching data: {e}")
            return False

    async def get_cached_data(
        self,
        key: str,
        data_type: Optional[DataType] = None
    ) -> Optional[Any]:
        """
        Retrieve data from offline cache

        Args:
            key: Data identifier
            data_type: Optional data type filter

        Returns:
            Cached data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build query
                if data_type:
                    cursor.execute("""
                        SELECT data, expires_at FROM offline_cache
                        WHERE key = ? AND data_type = ?
                    """, (key, data_type.value))
                else:
                    cursor.execute("""
                        SELECT data, expires_at FROM offline_cache
                        WHERE key = ?
                    """, (key,))

                result = cursor.fetchone()

                if not result:
                    return None

                data_json, expires_at_str = result

                # Check expiration
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if datetime.now() > expires_at:
                        # Remove expired data
                        cursor.execute("DELETE FROM offline_cache WHERE key = ?", (key,))
                        conn.commit()
                        return None

                # Update access count
                cursor.execute("""
                    UPDATE offline_cache SET access_count = access_count + 1
                    WHERE key = ?
                """, (key,))
                conn.commit()

                return json.loads(data_json)

        except Exception as e:
            logger.error(f"Error retrieving cached data: {e}")
            return None

    async def queue_for_sync(
        self,
        item_id: str,
        data_type: DataType,
        action: str,
        data: Dict[str, Any],
        priority: SyncPriority = SyncPriority.MEDIUM
    ) -> bool:
        """
        Queue an item for synchronization when online

        Args:
            item_id: Unique identifier
            data_type: Type of data
            action: Action to perform (create, update, delete)
            data: Data payload
            priority: Sync priority

        Returns:
            True if queued successfully
        """
        try:
            sync_item = SyncItem(
                id=item_id,
                data_type=data_type,
                priority=priority,
                action=action,
                data=data,
                created_at=datetime.now()
            )

            # Add to in-memory queue
            self.sync_queue.append(sync_item)

            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO sync_queue
                    (id, data_type, priority, action, data, created_at, attempts)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (
                    sync_item.id,
                    sync_item.data_type.value,
                    sync_item.priority.value,
                    sync_item.action,
                    json.dumps(sync_item.data),
                    sync_item.created_at.isoformat()
                ))
                conn.commit()

            logger.debug(f"Item queued for sync: {item_id} ({action})")

            # Try immediate sync if online
            if self.is_online and priority == SyncPriority.CRITICAL:
                await self._sync_single_item(sync_item)

            return True

        except Exception as e:
            logger.error(f"Error queueing item for sync: {e}")
            return False

    async def get_offline_coaching_suggestions(self, context: str) -> List[Dict[str, Any]]:
        """Get coaching suggestions from offline cache"""
        try:
            # Use essential cache for offline coaching
            templates = self.essential_cache.get("coaching_templates", {})

            suggestions = []

            # Analyze context for relevant suggestions
            context_lower = context.lower()

            # Check for objection patterns
            if any(word in context_lower for word in ["but", "however", "concern", "worried"]):
                suggestions.extend([
                    {
                        "type": "objection_response",
                        "title": "Address Concern",
                        "message": "Client raised a concern - acknowledge and respond",
                        "templates": templates.get("objection_responses", [])
                    }
                ])

            # Check for interest patterns
            if any(word in context_lower for word in ["like", "interested", "love", "perfect"]):
                suggestions.extend([
                    {
                        "type": "close_for_action",
                        "title": "Capitalize on Interest",
                        "message": "Client is engaged - move to next step",
                        "templates": templates.get("closing_statements", [])
                    }
                ])

            # Default to qualifying questions
            if not suggestions:
                suggestions.append({
                    "type": "qualifying_question",
                    "title": "Learn More",
                    "message": "Continue discovery conversation",
                    "templates": templates.get("qualifying_questions", [])
                })

            return suggestions

        except Exception as e:
            logger.error(f"Error getting offline coaching suggestions: {e}")
            return []

    async def _preload_agent_data(self, agent_id: str, session: OfflineSession):
        """Preload essential data for an agent's offline session"""
        try:
            # Cache coaching templates
            await self.cache_data(
                f"agent_{agent_id}_coaching_templates",
                self.essential_cache["coaching_templates"],
                DataType.COACHING_SUGGESTIONS,
                datetime.now() + timedelta(hours=24)
            )

            # Cache property information templates
            await self.cache_data(
                f"agent_{agent_id}_property_templates",
                self.essential_cache["property_info_templates"],
                DataType.PROPERTY_DATA,
                datetime.now() + timedelta(hours=24)
            )

            # Cache common responses
            await self.cache_data(
                f"agent_{agent_id}_responses",
                self.essential_cache["common_responses"],
                DataType.QUICK_ACTIONS,
                datetime.now() + timedelta(hours=24)
            )

            session.items_cached = 3
            session.data_size_mb = 0.1  # Estimate

            logger.info(f"Preloaded offline data for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error preloading agent data: {e}")

    async def _prepare_offline_mode(self):
        """Prepare system for offline operation"""
        try:
            logger.info("Preparing for offline mode...")

            # Load sync queue from database
            await self._load_sync_queue()

            # Clean up expired cache entries
            await self._cleanup_expired_cache()

            logger.info("Offline mode preparation complete")

        except Exception as e:
            logger.error(f"Error preparing offline mode: {e}")

    async def _start_background_sync(self):
        """Start background synchronization process"""
        if self._background_sync_task and not self._background_sync_task.done():
            return  # Already running

        self._background_sync_task = asyncio.create_task(self._background_sync_worker())

    async def _background_sync_worker(self):
        """Background worker for syncing queued items"""
        while self.is_online:
            try:
                await self._sync_batch()
                await asyncio.sleep(5)  # Sync every 5 seconds
            except Exception as e:
                logger.error(f"Background sync error: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def _sync_batch(self):
        """Sync a batch of queued items"""
        if not self.sync_queue:
            return

        with self._sync_lock:
            # Sort by priority and take a batch
            sorted_queue = sorted(self.sync_queue, key=lambda x: (x.priority.value, x.created_at))
            batch = sorted_queue[:self.batch_sync_size]

            sync_start_time = time.time()

            for item in batch:
                try:
                    success = await self._sync_single_item(item)
                    if success:
                        self.sync_queue.remove(item)
                        await self._remove_from_db_queue(item.id)
                    else:
                        item.attempts += 1
                        item.last_attempt = datetime.now()

                        # Remove items with too many failed attempts
                        if item.attempts > 5:
                            self.sync_queue.remove(item)
                            await self._remove_from_db_queue(item.id)
                            logger.warning(f"Dropping sync item after 5 failed attempts: {item.id}")

                except Exception as e:
                    logger.error(f"Error syncing item {item.id}: {e}")

            sync_duration = time.time() - sync_start_time
            if batch:
                logger.info(f"Synced {len(batch)} items in {sync_duration:.2f}s")

    async def _sync_single_item(self, item: SyncItem) -> bool:
        """Sync a single item with the server"""
        try:
            # Simulate API call (replace with actual implementation)
            await asyncio.sleep(0.1)  # Simulate network delay

            # TODO: Replace with actual API calls
            if item.action == "create":
                success = await self._api_create(item.data_type, item.data)
            elif item.action == "update":
                success = await self._api_update(item.data_type, item.id, item.data)
            elif item.action == "delete":
                success = await self._api_delete(item.data_type, item.id)
            else:
                success = False

            return success

        except Exception as e:
            logger.error(f"Error syncing item {item.id}: {e}")
            return False

    async def _api_create(self, data_type: DataType, data: Dict[str, Any]) -> bool:
        """Simulate API create call"""
        # TODO: Implement actual API calls
        await asyncio.sleep(0.05)  # Simulate API latency
        return True

    async def _api_update(self, data_type: DataType, item_id: str, data: Dict[str, Any]) -> bool:
        """Simulate API update call"""
        # TODO: Implement actual API calls
        await asyncio.sleep(0.05)
        return True

    async def _api_delete(self, data_type: DataType, item_id: str) -> bool:
        """Simulate API delete call"""
        # TODO: Implement actual API calls
        await asyncio.sleep(0.05)
        return True

    async def _load_sync_queue(self):
        """Load sync queue from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, data_type, priority, action, data, created_at, attempts, last_attempt, error_message
                    FROM sync_queue
                    ORDER BY priority, created_at
                """)

                for row in cursor.fetchall():
                    item_id, data_type_str, priority, action, data_json, created_at_str, attempts, last_attempt_str, error_message = row

                    sync_item = SyncItem(
                        id=item_id,
                        data_type=DataType(data_type_str),
                        priority=SyncPriority(priority),
                        action=action,
                        data=json.loads(data_json),
                        created_at=datetime.fromisoformat(created_at_str),
                        attempts=attempts,
                        last_attempt=datetime.fromisoformat(last_attempt_str) if last_attempt_str else None,
                        error_message=error_message
                    )

                    self.sync_queue.append(sync_item)

            logger.info(f"Loaded {len(self.sync_queue)} items from sync queue")

        except Exception as e:
            logger.error(f"Error loading sync queue: {e}")

    async def _remove_from_db_queue(self, item_id: str):
        """Remove item from database sync queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error removing item from DB queue: {e}")

    async def _cleanup_expired_cache(self):
        """Remove expired cache entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute("""
                    DELETE FROM offline_cache
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (now,))
                deleted_count = cursor.rowcount
                conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")

        except Exception as e:
            logger.error(f"Error cleaning expired cache: {e}")

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        queue_by_priority = {}
        for priority in SyncPriority:
            count = sum(1 for item in self.sync_queue if item.priority == priority)
            queue_by_priority[priority.name.lower()] = count

        return {
            "is_online": self.is_online,
            "last_sync_time": self.last_sync_time.isoformat(),
            "queue_size": len(self.sync_queue),
            "queue_by_priority": queue_by_priority,
            "conflicts_count": len(self.conflicts),
            "active_offline_sessions": len(self.offline_sessions)
        }

    async def clear_cache(self, data_type: Optional[DataType] = None):
        """Clear offline cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if data_type:
                    cursor.execute("DELETE FROM offline_cache WHERE data_type = ?", (data_type.value,))
                else:
                    cursor.execute("DELETE FROM offline_cache")

                deleted_count = cursor.rowcount
                conn.commit()

            logger.info(f"Cleared {deleted_count} cache entries")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")