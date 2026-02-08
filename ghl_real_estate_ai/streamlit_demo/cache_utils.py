"""
Streamlit Caching Utilities - Production-ready caching patterns.

Implements Streamlit best practices from 2026:
- max_entries parameter to prevent memory bloat
- Cache warming on app startup
- Smart TTL management
- Session state integration
"""

import asyncio
import hashlib
import logging
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


def st_cache_data_enhanced(
    ttl: int = 300,
    max_entries: int = 1000,
    show_spinner: str = "Loading...",
    key_prefix: str = "",
):
    """
    Enhanced @st.cache_data with production-ready parameters.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        max_entries: Maximum cache entries to prevent memory bloat (default: 1000)
        show_spinner: Spinner message while loading
        key_prefix: Prefix for cache key namespacing

    Usage:
        @st_cache_data_enhanced(ttl=3600, max_entries=500)
        def load_lead_data(lead_id: str):
            return fetch_from_database(lead_id)
    """

    def decorator(func: Callable) -> Callable:
        @st.cache_data(ttl=ttl, max_entries=max_entries, show_spinner=show_spinner)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def st_cache_resource_enhanced(show_spinner: str = "Initializing..."):
    """
    Enhanced @st.cache_resource for singletons (DB connections, API clients).

    Usage:
        @st_cache_resource_enhanced(show_spinner="Connecting to Redis...")
        def get_redis_client():
            return redis.Redis(...)
    """

    def decorator(func: Callable) -> Callable:
        @st.cache_resource(show_spinner=show_spinner)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class CacheWarmer:
    """
    Cache warming utility for Streamlit apps.

    Preloads frequently accessed data on app startup to eliminate
    "first load takes forever" issue.
    """

    def __init__(self):
        self.warm_functions: Dict[str, Callable] = {}
        self._warmed = False

    def register(self, name: str, func: Callable, *args, **kwargs):
        """
        Register a function to be warmed on startup.

        Args:
            name: Unique name for this warm function
            func: Cached function to warm
            *args, **kwargs: Arguments to pass to the function
        """
        self.warm_functions[name] = (func, args, kwargs)

    def warm_all(self, progress_callback: Optional[Callable] = None):
        """
        Warm all registered cache functions.

        Args:
            progress_callback: Optional callback(current, total, name)
        """
        if self._warmed:
            return

        total = len(self.warm_functions)
        for idx, (name, (func, args, kwargs)) in enumerate(self.warm_functions.items(), 1):
            try:
                if progress_callback:
                    progress_callback(idx, total, name)

                # Execute function to populate cache
                func(*args, **kwargs)
                logger.info(f"✅ Warmed cache: {name}")

            except Exception as e:
                logger.error(f"❌ Failed to warm cache {name}: {e}")

        self._warmed = True

    def reset(self):
        """Reset warmed state (useful for testing)."""
        self._warmed = False


# Global cache warmer instance
_cache_warmer = None


def get_cache_warmer() -> CacheWarmer:
    """Get global cache warmer singleton."""
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer()
    return _cache_warmer


def warm_cache_on_startup(warm_functions: Dict[str, tuple[Callable, tuple, dict]]):
    """
    Warm cache on Streamlit app startup.

    Args:
        warm_functions: Dict of {name: (function, args, kwargs)}

    Usage in app.py:
        warm_cache_on_startup({
            "top_leads": (load_lead_data, ("active",), {}),
            "properties": (load_properties, (), {"limit": 50}),
        })
    """
    warmer = get_cache_warmer()

    # Register all functions
    for name, (func, args, kwargs) in warm_functions.items():
        warmer.register(name, func, *args, **kwargs)

    # Warm with progress
    if not warmer._warmed:
        with st.spinner("Warming cache..."):
            progress_bar = st.progress(0)

            def update_progress(current, total, name):
                progress_bar.progress(current / total, text=f"Loading {name}...")

            warmer.warm_all(progress_callback=update_progress)
            progress_bar.empty()


def create_session_cache_key(*args, prefix: str = "") -> str:
    """
    Create a consistent session-level cache key.

    Useful for caching data per user session without using @st.cache.

    Args:
        *args: Arguments to include in key
        prefix: Prefix for namespacing

    Returns:
        Hashed cache key

    Usage:
        key = create_session_cache_key("lead", lead_id, prefix="intelligence")
        if key not in st.session_state:
            st.session_state[key] = expensive_operation()
    """
    key_parts = [str(arg) for arg in args]
    key_string = ":".join(key_parts)

    if prefix:
        key_string = f"{prefix}:{key_string}"

    # Hash for consistent length
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
    return f"{prefix}_{key_hash}" if prefix else key_hash


def get_or_compute_session_cache(key: str, compute_func: Callable, *args, **kwargs) -> Any:
    """
    Get value from session state cache or compute if missing.

    Args:
        key: Session state key
        compute_func: Function to compute value if not cached
        *args, **kwargs: Arguments for compute_func

    Returns:
        Cached or computed value

    Usage:
        lead_score = get_or_compute_session_cache(
            "lead_score_12345",
            calculate_lead_score,
            lead_id="12345"
        )
    """
    if key not in st.session_state:
        st.session_state[key] = compute_func(*args, **kwargs)

    return st.session_state[key]


def invalidate_session_cache(pattern: Optional[str] = None):
    """
    Invalidate session cache entries.

    Args:
        pattern: Optional pattern to match keys (e.g., "lead_*")
                 If None, clears all session state

    Usage:
        # Clear all lead-related cache
        invalidate_session_cache("lead_*")

        # Clear everything
        invalidate_session_cache()
    """
    if pattern is None:
        st.session_state.clear()
        logger.info("Cleared all session cache")
        return

    import fnmatch

    keys_to_remove = [key for key in st.session_state.keys() if fnmatch.fnmatch(key, pattern)]

    for key in keys_to_remove:
        del st.session_state[key]

    logger.info(f"Invalidated {len(keys_to_remove)} session cache entries matching '{pattern}'")


class StreamlitCacheMetrics:
    """
    Track and display Streamlit cache performance metrics.

    Usage in sidebar:
        metrics = StreamlitCacheMetrics()
        metrics.display()
    """

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics from Streamlit."""
        # Note: Streamlit doesn't expose cache metrics directly,
        # so we track via session state

        if "_cache_metrics" not in st.session_state:
            st.session_state._cache_metrics = {
                "hits": 0,
                "misses": 0,
                "computes": 0,
                "last_reset": datetime.now(),
            }

        return st.session_state._cache_metrics

    @staticmethod
    def record_hit():
        """Record a cache hit."""
        metrics = StreamlitCacheMetrics.get_cache_stats()
        metrics["hits"] += 1

    @staticmethod
    def record_miss():
        """Record a cache miss."""
        metrics = StreamlitCacheMetrics.get_cache_stats()
        metrics["misses"] += 1

    @staticmethod
    def record_compute():
        """Record a cache computation."""
        metrics = StreamlitCacheMetrics.get_cache_stats()
        metrics["computes"] += 1

    @staticmethod
    def display():
        """Display cache metrics in Streamlit."""
        metrics = StreamlitCacheMetrics.get_cache_stats()

        total_requests = metrics["hits"] + metrics["misses"]
        hit_rate = metrics["hits"] / total_requests if total_requests > 0 else 0

        st.sidebar.markdown("### 📊 Cache Performance")

        col1, col2, col3 = st.sidebar.columns(3)
        col1.metric("Hit Rate", f"{hit_rate:.1%}")
        col2.metric("Hits", metrics["hits"])
        col3.metric("Misses", metrics["misses"])

        if st.sidebar.button("Reset Metrics"):
            st.session_state._cache_metrics = {
                "hits": 0,
                "misses": 0,
                "computes": 0,
                "last_reset": datetime.now(),
            }
            st.rerun()


# Example usage patterns
if __name__ == "__main__":
    # Example 1: Enhanced caching decorator
    @st_cache_data_enhanced(ttl=3600, max_entries=500)
    def load_leads_example(status: str):
        # Expensive database query
        return {"lead_id": "123", "status": status}

    # Example 2: Cache warming
    warm_cache_on_startup(
        {
            "active_leads": (load_leads_example, ("active",), {}),
            "qualified_leads": (load_leads_example, ("qualified",), {}),
        }
    )

    # Example 3: Session cache
    lead_data = get_or_compute_session_cache("lead_123", load_leads_example, status="active")

    # Example 4: Display metrics
    StreamlitCacheMetrics.display()
