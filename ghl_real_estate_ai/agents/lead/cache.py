"""
TTL-aware LRU Cache implementation for the Lead Bot module.
"""
import threading
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class TTLLRUCache:
    """
    Thread-safe LRU cache with TTL (Time-To-Live) support.

    Features:
    - Maximum entry limit to prevent unbounded memory growth
    - TTL-based expiration for stale data eviction
    - LRU eviction when max entries reached
    - Thread-safe operations
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize TTL-aware LRU cache.

        Args:
            max_entries: Maximum number of entries (default: 1000)
            ttl_seconds: Time-to-live in seconds (default: 3600 = 60 minutes)
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions_ttl": 0,
            "evictions_lru": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            value, timestamp = self._cache[key]
            current_time = datetime.now().timestamp()

            # Check if expired
            if current_time - timestamp > self._ttl_seconds:
                del self._cache[key]
                self._stats["evictions_ttl"] += 1
                self._stats["misses"] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.

        Evicts LRU entries if max_entries exceeded.
        """
        with self._lock:
            current_time = datetime.now().timestamp()

            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = (value, current_time)
                self._cache.move_to_end(key)
                return

            # Evict oldest entries if at capacity
            while len(self._cache) >= self._max_entries:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions_lru"] += 1
                logger.debug(f"LRU eviction: {oldest_key} (cache size: {len(self._cache)})")

            # Add new entry
            self._cache[key] = (value, current_time)

    def contains(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = datetime.now().timestamp()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items() if current_time - timestamp > self._ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats["evictions_ttl"] += 1

            if expired_keys:
                logger.debug(f"TTL cleanup: removed {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_entries": self._max_entries,
                "ttl_seconds": self._ttl_seconds,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions_ttl": self._stats["evictions_ttl"],
                "evictions_lru": self._stats["evictions_lru"],
            }

    def __len__(self) -> int:
        """Return number of entries in cache."""
        with self._lock:
            return len(self._cache)