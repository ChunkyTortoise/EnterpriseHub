"""
Cache Service - Unified Caching Layer for Customer Intelligence Platform.

Provides a standardized interface for caching with support for multiple backends:
- Memory: Fast, in-process caching (default)
- Redis: Distributed, persistent caching (production)
- File: Persistent local caching (development)
"""
import os
import json
import pickle
import time
import asyncio
from typing import Any, Optional, Union, Dict
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AbstractCache(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        pass
        
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds."""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
        
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass


class MemoryCache(AbstractCache):
    """In-memory cache using a dictionary."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        logger.info("Initialized MemoryCache")
        
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
            
        if time.time() > self._expiry.get(key, 0):
            await self.delete(key)
            return None
            
        return self._cache[key]
        
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl
        return True
        
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            del self._expiry[key]
            return True
        return False
        
    async def clear(self) -> bool:
        self._cache.clear()
        self._expiry.clear()
        return True


class FileCache(AbstractCache):
    """File-based cache using pickle for persistence."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Initialized FileCache at {cache_dir}")
        
    def _get_path(self, key: str) -> str:
        # Sanitize key to be safe for filenames
        safe_key = "".join(c for c in key if c.isalnum() or c in ('-', '_')).strip()
        if not safe_key:
            safe_key = "default"
        return os.path.join(self.cache_dir, f"{safe_key}.pickle")
        
    async def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
            
        try:
            async with asyncio.Lock():
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                    
            if time.time() > data['expiry']:
                os.remove(path)
                return None
                
            return data['value']
        except Exception as e:
            logger.warning(f"FileCache read error for {key}: {e}")
            return None
            
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        path = self._get_path(key)
        data = {
            'value': value,
            'expiry': time.time() + ttl
        }
        try:
            async with asyncio.Lock():
                with open(path, 'wb') as f:
                    pickle.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"FileCache write error for {key}: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        path = self._get_path(key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False
        
    async def clear(self) -> bool:
        try:
            for f in os.listdir(self.cache_dir):
                if f.endswith(".pickle"):
                    os.remove(os.path.join(self.cache_dir, f))
            return True
        except Exception as e:
            logger.error(f"FileCache clear error: {e}")
            return False


class RedisCache(AbstractCache):
    """Redis-based cache for production with connection pooling."""

    def __init__(self, redis_url: str, max_connections: int = 50):
        try:
            import redis.asyncio as redis
            from redis.asyncio.connection import ConnectionPool

            # Create connection pool for better performance
            self.connection_pool = ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=False,  # We handle encoding with pickle
            )

            self.redis = redis.Redis(connection_pool=self.connection_pool)
            self.enabled = True
            logger.info(f"Initialized RedisCache with connection pool (max={max_connections}) connected to {redis_url}")
        except ImportError:
            logger.error("Redis package not installed. Install with 'pip install redis'")
            self.enabled = False
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.enabled = False
            
    async def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            data = await self.redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
            
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self.enabled:
            return False
        try:
            data = pickle.dumps(value)
            await self.redis.set(key, data, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        if not self.enabled:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
            
    async def clear(self) -> bool:
        if not self.enabled:
            return False
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    async def close(self):
        """Close Redis connection pool."""
        if self.enabled and hasattr(self, 'connection_pool'):
            await self.connection_pool.disconnect()
            logger.info("Redis connection pool closed")

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Batch get multiple keys using pipeline."""
        if not self.enabled:
            return {}
        try:
            pipeline = self.redis.pipeline()
            for key in keys:
                pipeline.get(key)
            results = await pipeline.execute()

            output = {}
            for key, data in zip(keys, results):
                if data:
                    try:
                        output[key] = pickle.loads(data)
                    except Exception:
                        pass
            return output
        except Exception as e:
            logger.error(f"Redis get_many error: {e}")
            return {}

    async def set_many(self, items: dict[str, Any], ttl: int = 300) -> bool:
        """Batch set multiple items using pipeline."""
        if not self.enabled:
            return False
        try:
            pipeline = self.redis.pipeline()
            for key, value in items.items():
                data = pickle.dumps(value)
                pipeline.set(key, data, ex=ttl)
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Redis set_many error: {e}")
            return False


class CacheService:
    """
    Unified Cache Service Factory.
    Selects the best backend based on configuration.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        self.backend: AbstractCache = None
        
        # Try Redis first if configured
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                self.backend = RedisCache(redis_url)
                # Verify connection
                if not getattr(self.backend, 'enabled', False):
                    logger.warning("Redis configured but unavailable, falling back...")
                    self.backend = None
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                self.backend = None
                
        # Fallback to FileCache for persistence in development
        if not self.backend:
            # Use FileCache if we want persistence, or Memory for speed
            # For this app, persistence is good for demos
            cache_dir = os.getenv("CACHE_DIR", ".cache")
            self.backend = FileCache(cache_dir)
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self.backend.get(key)
        
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache (default TTL: 5 minutes)."""
        return await self.backend.set(key, value, ttl)
        
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self.backend.delete(key)
        
    async def clear(self) -> bool:
        """Clear all cache."""
        return await self.backend.clear()

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Batch get multiple keys."""
        if hasattr(self.backend, 'get_many'):
            return await self.backend.get_many(keys)
        else:
            # Fallback for backends without batch support
            result = {}
            for key in keys:
                value = await self.get(key)
                if value is not None:
                    result[key] = value
            return result

    async def set_many(self, items: dict[str, Any], ttl: int = 300) -> bool:
        """Batch set multiple items."""
        if hasattr(self.backend, 'set_many'):
            return await self.backend.set_many(items, ttl)
        else:
            # Fallback for backends without batch support
            for key, value in items.items():
                await self.set(key, value, ttl)
            return True


# Decorator for caching function results
def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.append(str(hash(str(args))))
            if kwargs:
                key_parts.append(str(hash(str(sorted(kwargs.items())))))
            
            cache_key = ":".join(filter(None, key_parts))
            
            # Try to get from cache
            cache = get_cache_service()
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Global accessor
def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    return CacheService()


# Export main classes and functions
__all__ = [
    'CacheService', 'AbstractCache', 'MemoryCache', 'FileCache', 'RedisCache',
    'get_cache_service', 'cached'
]