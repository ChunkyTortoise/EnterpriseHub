"""
Storage Layer for User Profiles

Provides abstract storage interface with Redis and in-memory implementations.
"""

from __future__ import annotations

import asyncio
import json
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.personalization.user_profile import UserProfile


class StorageError(Exception):
    """Base exception for storage operations."""

    pass


class ProfileNotFoundError(StorageError):
    """Raised when a profile is not found."""

    pass


class SerializationError(StorageError):
    """Raised when serialization/deserialization fails."""

    pass


class ConnectionError(StorageError):
    """Raised when connection to storage fails."""

    pass


T = TypeVar("T")


@dataclass
class StorageConfig:
    """Configuration for storage backends."""

    ttl_seconds: int = 3600  # 1 hour default
    max_retries: int = 3
    retry_delay: float = 0.1
    compression: bool = False
    prefix: str = "profile:"


class ProfileSerializer:
    """Serialize and deserialize user profiles."""

    @staticmethod
    def to_json(profile: UserProfile) -> str:
        """Serialize profile to JSON string."""
        try:
            return json.dumps(profile.to_dict())
        except (TypeError, ValueError) as e:
            raise SerializationError(f"Failed to serialize profile: {e}")

    @staticmethod
    def from_json(data: str) -> UserProfile:
        """Deserialize profile from JSON string."""
        try:
            return UserProfile.from_dict(json.loads(data))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise SerializationError(f"Failed to deserialize profile: {e}")

    @staticmethod
    def to_bytes(profile: UserProfile) -> bytes:
        """Serialize profile to bytes using pickle."""
        try:
            return pickle.dumps(profile)
        except pickle.PickleError as e:
            raise SerializationError(f"Failed to pickle profile: {e}")

    @staticmethod
    def from_bytes(data: bytes) -> UserProfile:
        """Deserialize profile from bytes using pickle."""
        try:
            return pickle.loads(data)
        except pickle.PickleError as e:
            raise SerializationError(f"Failed to unpickle profile: {e}")


class ProfileStore(ABC):
    """Abstract base class for profile storage backends."""

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self._serializer = ProfileSerializer()

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to storage backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to storage backend."""
        pass

    @abstractmethod
    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve a profile by user ID."""
        pass

    @abstractmethod
    async def set(self, user_id: str, profile: UserProfile) -> None:
        """Store a profile."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a profile. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    async def exists(self, user_id: str) -> bool:
        """Check if a profile exists."""
        pass

    @abstractmethod
    async def keys(self) -> List[str]:
        """Get all user IDs in storage."""
        pass

    async def get_or_create(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one."""
        profile = await self.get(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            await self.set(user_id, profile)
        return profile

    async def update(
        self,
        user_id: str,
        updater: Callable[[UserProfile], UserProfile],
    ) -> UserProfile:
        """Update a profile using an updater function."""
        profile = await self.get_or_create(user_id)
        updated = updater(profile)
        await self.set(user_id, updated)
        return updated

    async def batch_get(self, user_ids: List[str]) -> Dict[str, Optional[UserProfile]]:
        """Get multiple profiles in batch."""
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.get(user_id)
        return results

    async def batch_set(self, profiles: Dict[str, UserProfile]) -> None:
        """Store multiple profiles in batch."""
        for user_id, profile in profiles.items():
            await self.set(user_id, profile)

    def _make_key(self, user_id: str) -> str:
        """Create storage key for user ID."""
        return f"{self.config.prefix}{user_id}"


class InMemoryProfileStore(ProfileStore):
    """In-memory storage implementation for testing and development."""

    def __init__(self, config: Optional[StorageConfig] = None):
        super().__init__(config)
        self._storage: Dict[str, bytes] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> None:
        """No-op for in-memory store."""
        self._connected = True

    async def disconnect(self) -> None:
        """Clear storage and disconnect."""
        async with self._lock:
            self._storage.clear()
            self._expiry.clear()
        self._connected = False

    def _is_expired(self, user_id: str) -> bool:
        """Check if a profile has expired."""
        if user_id not in self._expiry:
            return False
        return time.time() > self._expiry[user_id]

    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve a profile from memory."""
        async with self._lock:
            if self._is_expired(user_id):
                del self._storage[user_id]
                del self._expiry[user_id]
                return None

            data = self._storage.get(user_id)
            if data is None:
                return None

            try:
                return self._serializer.from_bytes(data)
            except SerializationError:
                return None

    async def set(self, user_id: str, profile: UserProfile) -> None:
        """Store a profile in memory."""
        async with self._lock:
            data = self._serializer.to_bytes(profile)
            self._storage[user_id] = data

            if self.config.ttl_seconds > 0:
                self._expiry[user_id] = time.time() + self.config.ttl_seconds

    async def delete(self, user_id: str) -> bool:
        """Delete a profile from memory."""
        async with self._lock:
            if user_id in self._storage:
                del self._storage[user_id]
                if user_id in self._expiry:
                    del self._expiry[user_id]
                return True
            return False

    async def exists(self, user_id: str) -> bool:
        """Check if a profile exists in memory."""
        async with self._lock:
            if self._is_expired(user_id):
                del self._storage[user_id]
                del self._expiry[user_id]
                return False
            return user_id in self._storage

    async def keys(self) -> List[str]:
        """Get all user IDs in memory."""
        async with self._lock:
            # Clean up expired entries first
            expired = [user_id for user_id in list(self._storage.keys()) if self._is_expired(user_id)]
            for user_id in expired:
                del self._storage[user_id]
                if user_id in self._expiry:
                    del self._expiry[user_id]

            return list(self._storage.keys())

    async def clear(self) -> None:
        """Clear all profiles from memory."""
        async with self._lock:
            self._storage.clear()
            self._expiry.clear()

    async def size(self) -> int:
        """Get number of profiles in storage."""
        async with self._lock:
            return len(self._storage)


class RedisProfileStore(ProfileStore):
    """Redis-backed storage implementation for production use."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        config: Optional[StorageConfig] = None,
    ):
        super().__init__(config)
        self.redis_url = redis_url
        self._redis = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
        except ImportError:
            raise ConnectionError("redis package not installed. Install with: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    async def _execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute Redis operation with retry logic."""
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2**attempt))
        raise StorageError(f"Operation failed after {self.config.max_retries} attempts: {last_error}")

    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve a profile from Redis."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        key = self._make_key(user_id)

        try:
            data = await self._execute_with_retry(self._redis.get, key)
            if data is None:
                return None

            return self._serializer.from_bytes(data)
        except SerializationError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get profile: {e}")

    async def set(self, user_id: str, profile: UserProfile) -> None:
        """Store a profile in Redis."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        key = self._make_key(user_id)
        data = self._serializer.to_bytes(profile)

        try:
            await self._execute_with_retry(
                self._redis.setex,
                key,
                self.config.ttl_seconds,
                data,
            )
        except Exception as e:
            raise StorageError(f"Failed to set profile: {e}")

    async def delete(self, user_id: str) -> bool:
        """Delete a profile from Redis."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        key = self._make_key(user_id)

        try:
            result = await self._execute_with_retry(self._redis.delete, key)
            return result > 0
        except Exception as e:
            raise StorageError(f"Failed to delete profile: {e}")

    async def exists(self, user_id: str) -> bool:
        """Check if a profile exists in Redis."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        key = self._make_key(user_id)

        try:
            return await self._execute_with_retry(self._redis.exists, key) > 0
        except Exception as e:
            raise StorageError(f"Failed to check existence: {e}")

    async def keys(self) -> List[str]:
        """Get all user IDs in Redis."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        try:
            pattern = f"{self.config.prefix}*"
            keys = await self._execute_with_retry(self._redis.keys, pattern)
            # Strip prefix from keys
            prefix_len = len(self.config.prefix)
            return [k.decode("utf-8")[prefix_len:] if isinstance(k, bytes) else k[prefix_len:] for k in keys]
        except Exception as e:
            raise StorageError(f"Failed to get keys: {e}")

    async def batch_get(self, user_ids: List[str]) -> Dict[str, Optional[UserProfile]]:
        """Get multiple profiles from Redis using pipeline."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        if not user_ids:
            return {}

        keys = [self._make_key(uid) for uid in user_ids]

        try:
            pipe = self._redis.pipeline()
            for key in keys:
                pipe.get(key)

            results = await self._execute_with_retry(pipe.execute)

            profiles = {}
            for user_id, data in zip(user_ids, results):
                if data is None:
                    profiles[user_id] = None
                else:
                    try:
                        profiles[user_id] = self._serializer.from_bytes(data)
                    except SerializationError:
                        profiles[user_id] = None

            return profiles
        except Exception as e:
            raise StorageError(f"Failed to batch get profiles: {e}")

    async def batch_set(self, profiles: Dict[str, UserProfile]) -> None:
        """Store multiple profiles in Redis using pipeline."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        if not profiles:
            return

        try:
            pipe = self._redis.pipeline()
            for user_id, profile in profiles.items():
                key = self._make_key(user_id)
                data = self._serializer.to_bytes(profile)
                pipe.setex(key, self.config.ttl_seconds, data)

            await self._execute_with_retry(pipe.execute)
        except Exception as e:
            raise StorageError(f"Failed to batch set profiles: {e}")

    async def touch(self, user_id: str) -> bool:
        """Update TTL for a profile without fetching it."""
        if not self._connected:
            raise ConnectionError("Not connected to Redis")

        key = self._make_key(user_id)

        try:
            return await self._execute_with_retry(
                self._redis.expire,
                key,
                self.config.ttl_seconds,
            )
        except Exception as e:
            raise StorageError(f"Failed to touch profile: {e}")


class TieredProfileStore(ProfileStore):
    """Multi-tier storage with hot cache and cold storage."""

    def __init__(
        self,
        hot_store: ProfileStore,
        cold_store: ProfileStore,
        hot_threshold: int = 10,  # Access count to promote to hot
    ):
        super().__init__(hot_store.config)
        self.hot_store = hot_store
        self.cold_store = cold_store
        self.hot_threshold = hot_threshold
        self._access_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect both stores."""
        await self.hot_store.connect()
        await self.cold_store.connect()

    async def disconnect(self) -> None:
        """Disconnect both stores."""
        await self.hot_store.disconnect()
        await self.cold_store.disconnect()

    async def _record_access(self, user_id: str) -> None:
        """Record an access to track hot profiles."""
        async with self._lock:
            self._access_counts[user_id] = self._access_counts.get(user_id, 0) + 1

    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Get profile from hot store or fall back to cold store."""
        # Try hot store first
        profile = await self.hot_store.get(user_id)
        if profile is not None:
            await self._record_access(user_id)
            return profile

        # Try cold store
        profile = await self.cold_store.get(user_id)
        if profile is not None:
            # Promote to hot store if accessed frequently
            await self._record_access(user_id)
            count = self._access_counts.get(user_id, 0)
            if count >= self.hot_threshold:
                await self.hot_store.set(user_id, profile)
            return profile

        return None

    async def set(self, user_id: str, profile: UserProfile) -> None:
        """Store profile in both stores."""
        # Always store in cold store
        await self.cold_store.set(user_id, profile)
        # Store in hot store if frequently accessed
        count = self._access_counts.get(user_id, 0)
        if count >= self.hot_threshold:
            await self.hot_store.set(user_id, profile)

    async def delete(self, user_id: str) -> bool:
        """Delete from both stores."""
        hot_deleted = await self.hot_store.delete(user_id)
        cold_deleted = await self.cold_store.delete(user_id)

        async with self._lock:
            if user_id in self._access_counts:
                del self._access_counts[user_id]

        return hot_deleted or cold_deleted

    async def exists(self, user_id: str) -> bool:
        """Check existence in either store."""
        return await self.hot_store.exists(user_id) or await self.cold_store.exists(user_id)

    async def keys(self) -> List[str]:
        """Get all keys from cold store."""
        return await self.cold_store.keys()
