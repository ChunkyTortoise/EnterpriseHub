"""
Behavioral Event Tracking System

Collects, stores, and retrieves behavioral events for learning engine.
Integrates with Repository Pattern for persistence.
"""

import asyncio
import json
import logging
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.utils.async_utils import safe_create_task

from ..interfaces import BehavioralEvent, EventType, IBehaviorTracker

logger = logging.getLogger(__name__)


class InMemoryBehaviorTracker(IBehaviorTracker):
    """
    In-memory implementation for development/testing.

    Stores events in memory with periodic flush to repository.
    Provides fast access with automatic indexing by entity and event type.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # In-memory storage with thread-safe access
        self._events: List[BehavioralEvent] = []
        self._events_by_entity: Dict[str, List[BehavioralEvent]] = defaultdict(list)
        self._events_by_type: Dict[EventType, List[BehavioralEvent]] = defaultdict(list)
        self._lock = threading.RLock()

        # Configuration
        self.max_memory_events = self.config.get("max_memory_events", 10000)
        self.flush_interval_seconds = self.config.get("flush_interval_seconds", 60)
        self.auto_flush = self.config.get("auto_flush", True)

        # Repository for persistence (optional)
        self.repository = self.config.get("repository")

        # Performance tracking
        self.stats = {
            "events_tracked": 0,
            "events_flushed": 0,
            "flush_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_queries": 0,
        }

        # Background flush task
        self._flush_task = None
        if self.auto_flush:
            self._start_auto_flush()

    def _start_auto_flush(self):
        """Start background task for periodic flushing"""
        if self._flush_task is None:
            self._flush_task = safe_create_task(self._auto_flush_loop())

    async def _auto_flush_loop(self):
        """Background loop for automatic flushing"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval_seconds)
                if len(self._events) > 0:
                    await self._flush_to_repository()
            except Exception as e:
                logger.error(f"Auto-flush error: {e}")
                self.stats["flush_errors"] += 1

    async def track_event(self, event: BehavioralEvent) -> bool:
        """Track single event with automatic indexing"""
        try:
            with self._lock:
                # Store in main list
                self._events.append(event)

                # Index by entity for fast lookups
                if event.lead_id:
                    entity_key = f"lead_{event.lead_id}"
                    self._events_by_entity[entity_key].append(event)

                if event.agent_id:
                    entity_key = f"agent_{event.agent_id}"
                    self._events_by_entity[entity_key].append(event)

                if event.property_id:
                    entity_key = f"property_{event.property_id}"
                    self._events_by_entity[entity_key].append(event)

                # Index by event type
                self._events_by_type[event.event_type].append(event)

                self.stats["events_tracked"] += 1

                # Check if immediate flush needed
                if len(self._events) >= self.max_memory_events:
                    await self._flush_to_repository()

            return True

        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False

    async def track_events_batch(self, events: List[BehavioralEvent]) -> int:
        """Track multiple events efficiently"""
        successful = 0

        try:
            with self._lock:
                for event in events:
                    # Inline tracking for performance
                    self._events.append(event)

                    # Index by entities
                    if event.lead_id:
                        self._events_by_entity[f"lead_{event.lead_id}"].append(event)
                    if event.agent_id:
                        self._events_by_entity[f"agent_{event.agent_id}"].append(event)
                    if event.property_id:
                        self._events_by_entity[f"property_{event.property_id}"].append(event)

                    # Index by type
                    self._events_by_type[event.event_type].append(event)

                    successful += 1

                self.stats["events_tracked"] += successful

                # Check if flush needed
                if len(self._events) >= self.max_memory_events:
                    await self._flush_to_repository()

        except Exception as e:
            logger.error(f"Error in batch tracking: {e}")

        return successful

    async def get_events(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        event_types: Optional[List[EventType]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[BehavioralEvent]:
        """Retrieve events matching criteria with optimized filtering"""

        self.stats["total_queries"] += 1

        with self._lock:
            # Start with appropriate index
            if entity_id and entity_type:
                entity_key = f"{entity_type}_{entity_id}"
                if entity_key in self._events_by_entity:
                    events = self._events_by_entity[entity_key].copy()
                    self.stats["cache_hits"] += 1
                else:
                    events = []
                    self.stats["cache_misses"] += 1
            elif event_types and len(event_types) == 1:
                # Single event type optimization
                event_type = event_types[0]
                if event_type in self._events_by_type:
                    events = self._events_by_type[event_type].copy()
                    self.stats["cache_hits"] += 1
                else:
                    events = []
                    self.stats["cache_misses"] += 1
            else:
                # Full scan
                events = self._events.copy()
                self.stats["cache_misses"] += 1

            # Apply filters
            filtered_events = self._apply_filters(events, entity_id, entity_type, event_types, start_time, end_time)

            # Apply limit
            return filtered_events[:limit]

    def _apply_filters(
        self,
        events: List[BehavioralEvent],
        entity_id: Optional[str],
        entity_type: Optional[str],
        event_types: Optional[List[EventType]],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> List[BehavioralEvent]:
        """Apply filters to event list"""

        filtered = events

        # Filter by entity (if not already filtered)
        if entity_id and entity_type:
            if entity_type == "lead":
                filtered = [e for e in filtered if e.lead_id == entity_id]
            elif entity_type == "agent":
                filtered = [e for e in filtered if e.agent_id == entity_id]
            elif entity_type == "property":
                filtered = [e for e in filtered if e.property_id == entity_id]

        # Filter by event types
        if event_types:
            event_type_set = set(event_types)
            filtered = [e for e in filtered if e.event_type in event_type_set]

        # Filter by time range
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]

        # Sort by timestamp (most recent first)
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered

    async def get_event_count(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        event_types: Optional[List[EventType]] = None,
    ) -> int:
        """Count events matching criteria"""

        with self._lock:
            if entity_id and entity_type:
                entity_key = f"{entity_type}_{entity_id}"
                events = self._events_by_entity.get(entity_key, [])
            elif event_types and len(event_types) == 1:
                events = self._events_by_type.get(event_types[0], [])
            else:
                events = self._events

            if event_types and len(event_types) > 1:
                event_type_set = set(event_types)
                count = sum(1 for e in events if e.event_type in event_type_set)
            else:
                count = len(events)

            return count

    async def record_outcome(self, event_id: str, outcome: str, outcome_value: Optional[float] = None) -> bool:
        """Record outcome for event (for supervised learning)"""

        with self._lock:
            for event in self._events:
                if event.event_id == event_id:
                    event.outcome = outcome
                    event.outcome_value = outcome_value
                    event.outcome_timestamp = datetime.now()
                    return True

        # Event not found in memory, might be in repository
        logger.warning(f"Event {event_id} not found in memory for outcome recording")
        return False

    async def get_events_by_session(self, session_id: str, limit: int = 1000) -> List[BehavioralEvent]:
        """Get all events for a session"""

        with self._lock:
            events = [e for e in self._events if e.session_id == session_id]
            events.sort(key=lambda e: e.timestamp)
            return events[:limit]

    async def get_recent_events(
        self, minutes: int = 60, event_types: Optional[List[EventType]] = None, limit: int = 1000
    ) -> List[BehavioralEvent]:
        """Get recent events within time window"""

        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            events = [e for e in self._events if e.timestamp >= cutoff_time]

            if event_types:
                event_type_set = set(event_types)
                events = [e for e in events if e.event_type in event_type_set]

            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[:limit]

    async def _flush_to_repository(self):
        """Flush events to persistent storage"""

        if not self.repository or not self._events:
            return

        try:
            with self._lock:
                # Get events to flush
                events_to_flush = self._events.copy()

                # Convert events to dicts for storage
                event_dicts = [event.to_dict() for event in events_to_flush]

                # Save to repository (would use actual repository method)
                # await self.repository.save_events_batch(event_dicts)
                # For now, just simulate
                logger.info(f"Would flush {len(event_dicts)} events to repository")

                self.stats["events_flushed"] += len(events_to_flush)

                # Keep recent events in memory for fast access
                keep_recent = min(self.max_memory_events // 10, 1000)
                recent_events = self._events[-keep_recent:] if keep_recent > 0 else []

                # Clear and rebuild indices with recent events
                self._events = recent_events
                self._rebuild_indices()

        except Exception as e:
            logger.error(f"Error flushing events: {e}")
            self.stats["flush_errors"] += 1

    def _rebuild_indices(self):
        """Rebuild entity and type indices after flush"""

        # Clear existing indices
        self._events_by_entity.clear()
        self._events_by_type.clear()

        # Rebuild indices
        for event in self._events:
            # Index by entities
            if event.lead_id:
                self._events_by_entity[f"lead_{event.lead_id}"].append(event)
            if event.agent_id:
                self._events_by_entity[f"agent_{event.agent_id}"].append(event)
            if event.property_id:
                self._events_by_entity[f"property_{event.property_id}"].append(event)

            # Index by type
            self._events_by_type[event.event_type].append(event)

    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        with self._lock:
            return {
                **self.stats,
                "events_in_memory": len(self._events),
                "unique_entities": len(self._events_by_entity),
                "event_types_tracked": len(self._events_by_type),
                "memory_usage_estimate_mb": self._estimate_memory_usage(),
                "cache_hit_rate": self._calculate_cache_hit_rate(),
            }

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        # Rough estimate: ~1KB per event
        return (len(self._events) * 1024) / (1024 * 1024)

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total == 0:
            return 0.0
        return (self.stats["cache_hits"] / total) * 100.0

    async def clear_events(self, confirm: bool = False):
        """Clear all events (dangerous operation)"""
        if not confirm:
            raise ValueError("Must confirm clearing events with confirm=True")

        with self._lock:
            self._events.clear()
            self._events_by_entity.clear()
            self._events_by_type.clear()

            # Reset stats
            self.stats.update(
                {"events_tracked": 0, "events_flushed": 0, "cache_hits": 0, "cache_misses": 0, "total_queries": 0}
            )

    async def shutdown(self):
        """Shutdown tracker and cleanup resources"""
        try:
            # Stop auto-flush task
            if self._flush_task:
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass

            # Final flush
            if self._events:
                await self._flush_to_repository()

            # Clear memory
            await self.clear_events(confirm=True)

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


class TimedBehaviorTracker(InMemoryBehaviorTracker):
    """
    Extension of InMemoryBehaviorTracker with automatic event expiration.

    Useful for systems with limited memory that need automatic cleanup
    of old events.
    """

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        super().__init__(config)

        # Expiration settings
        self.event_ttl_hours = config.get("event_ttl_hours", 24)
        self.cleanup_interval_minutes = config.get("cleanup_interval_minutes", 60)

        # Start cleanup task
        self._cleanup_task = safe_create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Background loop for cleaning up expired events"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_minutes * 60)
                await self._cleanup_expired_events()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_expired_events(self):
        """Remove events older than TTL"""
        cutoff_time = datetime.now() - timedelta(hours=self.event_ttl_hours)

        with self._lock:
            initial_count = len(self._events)

            # Filter out expired events
            self._events = [e for e in self._events if e.timestamp >= cutoff_time]

            # Rebuild indices if events were removed
            if len(self._events) < initial_count:
                self._rebuild_indices()
                removed_count = initial_count - len(self._events)
                logger.info(f"Cleaned up {removed_count} expired events")

    async def shutdown(self):
        """Shutdown with cleanup task termination"""
        try:
            # Stop cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
        finally:
            await super().shutdown()
