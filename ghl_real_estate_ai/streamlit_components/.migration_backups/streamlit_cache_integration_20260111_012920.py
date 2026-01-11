"""
Streamlit Component Cache Integration
======================================

High-performance caching integration for Streamlit components leveraging:
- Redis multi-layer caching (L1/L2/L3)
- Predictive cache warming
- Component-level performance monitoring
- Automatic cache invalidation

Integrates with existing cache infrastructure:
- IntegrationCacheManager (L1: memory, L2: Redis, L3: database)
- PredictiveCacheManager (AI-driven cache warming, 99%+ hit rates)
- Enhanced Enterprise Base Components

Performance Targets:
- Component render time: <100ms (50ms target with caching)
- Cache hit rate: >90% (95% target)
- API call reduction: 80%+
- Memory efficiency: <50MB per component

Author: EnterpriseHub Performance Team
Date: 2026-01-10
Version: 1.0.0
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider using enterprise_metric for consistent styling
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import streamlit as st

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
import asyncio
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import logging

# Import existing cache infrastructure
try:
    from ..services.integration_cache_manager import IntegrationCacheManager, CacheMetrics
    from ..services.predictive_cache_manager import PredictiveCacheManager
    CACHE_MANAGERS_AVAILABLE = True
except ImportError:
    CACHE_MANAGERS_AVAILABLE = False
    logging.warning("Cache managers not available - using session state only")

logger = logging.getLogger(__name__)


@dataclass
class ComponentCacheConfig:
    """Configuration for component caching behavior."""
    component_id: str
    enable_l1_cache: bool = True          # In-memory session state cache
    enable_l2_cache: bool = True          # Redis cache
    enable_predictive: bool = True        # AI-driven cache warming

    default_ttl_seconds: int = 300        # 5 minutes default TTL
    max_memory_mb: int = 50               # Max memory per component

    # Performance monitoring
    track_metrics: bool = True
    log_cache_events: bool = False

    # Cache warming
    prewarm_on_load: bool = True
    predict_next_data: bool = True


@dataclass
class ComponentCacheMetrics:
    """Performance metrics for component caching."""
    component_id: str

    # Cache performance
    total_renders: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Layer-specific metrics
    session_state_hits: int = 0
    redis_hits: int = 0
    predictive_hits: int = 0

    # Timing metrics
    avg_render_time_ms: float = 0.0
    avg_cache_lookup_ms: float = 0.0
    total_time_saved_ms: float = 0.0

    # Data metrics
    data_requests_made: int = 0
    data_requests_cached: int = 0
    api_calls_saved: int = 0

    # Memory tracking
    current_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0

    last_updated: Optional[datetime] = None

    @property
    def cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0

    @property
    def api_reduction_rate(self) -> float:
        """Calculate API call reduction rate."""
        total = self.data_requests_made
        return (self.api_calls_saved / total * 100) if total > 0 else 0.0

    @property
    def avg_time_saved_per_render_ms(self) -> float:
        """Average time saved per render due to caching."""
        return (self.total_time_saved_ms / self.total_renders) if self.total_renders > 0 else 0.0


class StreamlitCacheIntegration(EnterpriseDashboardComponent):
    """
    Advanced caching integration for Streamlit components.

    Provides:
    - Multi-layer caching with automatic failover
    - Predictive cache warming
    - Performance monitoring and optimization
    - Intelligent cache invalidation
    - Component-level cache isolation
    """

    def __init__(
        self,
        component_id: str,
        config: Optional[ComponentCacheConfig] = None
    ):
        """
        Initialize cache integration for a component.

        Args:
            component_id: Unique identifier for the component
            config: Optional cache configuration
        """
        self.component_id = component_id
        self.config = config or ComponentCacheConfig(component_id=component_id)

        # Initialize cache managers if available
        self.cache_manager = None
        self.predictive_cache = None

        if CACHE_MANAGERS_AVAILABLE and self.config.enable_l2_cache:
            try:
                self.cache_manager = IntegrationCacheManager(
                    service_name=f"streamlit_{component_id}",
                    enable_redis=True,
                    enable_predictive=self.config.enable_predictive
                )

                if self.config.enable_predictive:
                    self.predictive_cache = PredictiveCacheManager(
                        cache_name=f"component_{component_id}",
                        enable_ai_prediction=True
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize cache managers: {e}")

        # Initialize metrics
        self.metrics = self._load_metrics()

        # Session state initialization
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize session state for component cache."""
        cache_key = f"cache_{self.component_id}"
        metrics_key = f"metrics_{self.component_id}"

        if cache_key not in st.session_state:
            st.session_state[cache_key] = {}

        if metrics_key not in st.session_state:
            st.session_state[metrics_key] = ComponentCacheMetrics(
                component_id=self.component_id
            )

    def _load_metrics(self) -> ComponentCacheMetrics:
        """Load metrics from session state."""
        metrics_key = f"metrics_{self.component_id}"

        if metrics_key in st.session_state:
            return st.session_state[metrics_key]

        return ComponentCacheMetrics(component_id=self.component_id)

    def _save_metrics(self) -> None:
        """Save metrics to session state."""
        metrics_key = f"metrics_{self.component_id}"
        self.metrics.last_updated = datetime.now()
        st.session_state[metrics_key] = self.metrics

    def _generate_cache_key(
        self,
        operation: str,
        *args,
        **kwargs
    ) -> str:
        """
        Generate consistent cache key for operation.

        Args:
            operation: Operation name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            SHA256 hash-based cache key
        """
        # Create deterministic string representation
        key_parts = [
            self.component_id,
            operation,
            str(sorted(args)),
            str(sorted(kwargs.items()))
        ]

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    async def get_cached_data(
        self,
        operation: str,
        fetch_func: Callable,
        ttl_seconds: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Get data with multi-layer caching.

        Cache hierarchy:
        1. Session state (L1) - fastest, limited scope
        2. Redis (L2) - fast, shared across sessions
        3. Predictive (warm) - AI-predicted data
        4. Fetch function (cold) - slowest, authoritative

        Args:
            operation: Operation name for cache key
            fetch_func: Function to fetch data on cache miss
            ttl_seconds: Cache TTL (default: from config)
            *args: Arguments for cache key and fetch function
            **kwargs: Keyword arguments for cache key and fetch function

        Returns:
            Cached or freshly fetched data
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(operation, *args, **kwargs)
        ttl = ttl_seconds or self.config.default_ttl_seconds

        self.metrics.total_renders += 1

        # Layer 1: Session state cache (fastest)
        if self.config.enable_l1_cache:
            session_cache = st.session_state.get(f"cache_{self.component_id}", {})

            if cache_key in session_cache:
                entry = session_cache[cache_key]

                # Check expiration
                if datetime.now() < entry['expires_at']:
                    self.metrics.cache_hits += 1
                    self.metrics.session_state_hits += 1

                    lookup_time = (time.time() - start_time) * 1000
                    self.metrics.avg_cache_lookup_ms = (
                        (self.metrics.avg_cache_lookup_ms * (self.metrics.cache_hits - 1) + lookup_time)
                        / self.metrics.cache_hits
                    )

                    self._save_metrics()

                    if self.config.log_cache_events:
                        logger.debug(f"L1 cache hit: {cache_key} ({lookup_time:.2f}ms)")

                    return entry['data']

        # Layer 2: Redis cache (fast, shared)
        if self.cache_manager and self.config.enable_l2_cache:
            try:
                redis_data = await self.cache_manager.get(cache_key)

                if redis_data is not None:
                    # Store in L1 for next access
                    if self.config.enable_l1_cache:
                        session_cache = st.session_state.get(f"cache_{self.component_id}", {})
                        session_cache[cache_key] = {
                            'data': redis_data,
                            'created_at': datetime.now(),
                            'expires_at': datetime.now() + timedelta(seconds=ttl)
                        }
                        st.session_state[f"cache_{self.component_id}"] = session_cache

                    self.metrics.cache_hits += 1
                    self.metrics.redis_hits += 1

                    lookup_time = (time.time() - start_time) * 1000
                    self.metrics.avg_cache_lookup_ms = (
                        (self.metrics.avg_cache_lookup_ms * (self.metrics.cache_hits - 1) + lookup_time)
                        / self.metrics.cache_hits
                    )

                    self._save_metrics()

                    if self.config.log_cache_events:
                        logger.debug(f"L2 cache hit: {cache_key} ({lookup_time:.2f}ms)")

                    return redis_data

            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")

        # Layer 3: Predictive cache (warm data)
        if self.predictive_cache and self.config.enable_predictive:
            try:
                predicted_data = await self.predictive_cache.get_predicted(cache_key)

                if predicted_data is not None:
                    self.metrics.cache_hits += 1
                    self.metrics.predictive_hits += 1

                    # Store in upper layers
                    await self._store_in_cache_layers(cache_key, predicted_data, ttl)

                    self._save_metrics()

                    if self.config.log_cache_events:
                        logger.info(f"Predictive cache hit: {cache_key}")

                    return predicted_data

            except Exception as e:
                logger.warning(f"Predictive cache lookup failed: {e}")

        # Cache miss - fetch data
        self.metrics.cache_misses += 1
        self.metrics.data_requests_made += 1

        fetch_start = time.time()

        # Call fetch function (may be async or sync)
        if asyncio.iscoroutinefunction(fetch_func):
            data = await fetch_func(*args, **kwargs)
        else:
            data = fetch_func(*args, **kwargs)

        fetch_time = (time.time() - fetch_start) * 1000

        # Store in all cache layers
        await self._store_in_cache_layers(cache_key, data, ttl)

        # Track time saved by future cache hits
        self.metrics.total_time_saved_ms += fetch_time * 0.9  # Assume 90% savings

        total_time = (time.time() - start_time) * 1000
        self.metrics.avg_render_time_ms = (
            (self.metrics.avg_render_time_ms * (self.metrics.total_renders - 1) + total_time)
            / self.metrics.total_renders
        )

        self._save_metrics()

        if self.config.log_cache_events:
            logger.debug(f"Cache miss: {cache_key} (fetch: {fetch_time:.2f}ms)")

        return data

    async def _store_in_cache_layers(
        self,
        cache_key: str,
        data: Any,
        ttl_seconds: int
    ) -> None:
        """Store data in all available cache layers."""

        # Layer 1: Session state
        if self.config.enable_l1_cache:
            session_cache = st.session_state.get(f"cache_{self.component_id}", {})
            session_cache[cache_key] = {
                'data': data,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl_seconds)
            }
            st.session_state[f"cache_{self.component_id}"] = session_cache

        # Layer 2: Redis
        if self.cache_manager and self.config.enable_l2_cache:
            try:
                await self.cache_manager.set(
                    cache_key,
                    data,
                    ttl_seconds=ttl_seconds
                )
                self.metrics.data_requests_cached += 1
            except Exception as e:
                logger.warning(f"Failed to store in Redis: {e}")

        # Layer 3: Predictive cache
        if self.predictive_cache and self.config.enable_predictive:
            try:
                await self.predictive_cache.record_access(
                    cache_key,
                    data,
                    ttl_seconds=ttl_seconds
                )
            except Exception as e:
                logger.warning(f"Failed to record in predictive cache: {e}")

    def invalidate_cache(
        self,
        operation: Optional[str] = None,
        *args,
        **kwargs
    ) -> None:
        """
        Invalidate cached data.

        Args:
            operation: Specific operation to invalidate (None = all)
            *args: Arguments for cache key
            **kwargs: Keyword arguments for cache key
        """
        if operation:
            cache_key = self._generate_cache_key(operation, *args, **kwargs)

            # Clear from session state
            session_cache = st.session_state.get(f"cache_{self.component_id}", {})
            if cache_key in session_cache:
                del session_cache[cache_key]
                st.session_state[f"cache_{self.component_id}"] = session_cache

            # Clear from Redis
            if self.cache_manager:
                try:
                    asyncio.create_task(self.cache_manager.delete(cache_key))
                except Exception as e:
                    logger.warning(f"Failed to delete from Redis: {e}")

        else:
            # Clear all cache for this component
            st.session_state[f"cache_{self.component_id}"] = {}

            if self.cache_manager:
                try:
                    asyncio.create_task(self.cache_manager.clear_namespace(f"streamlit_{self.component_id}"))
                except Exception as e:
                    logger.warning(f"Failed to clear Redis namespace: {e}")

    def get_metrics(self) -> ComponentCacheMetrics:
        """Get current cache metrics."""
        return self.metrics

    def render_performance_panel(self) -> None:
        """Render performance metrics panel in Streamlit."""
        st.markdown("### 📊 Cache Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Cache Hit Rate",
                f"{self.metrics.cache_hit_rate:.1f}%",
                delta=f"{self.metrics.cache_hits} hits"
            )

        with col2:
            st.metric(
                "API Reduction",
                f"{self.metrics.api_reduction_rate:.1f}%",
                delta=f"{self.metrics.api_calls_saved} saved"
            )

        with col3:
            st.metric(
                "Avg Lookup Time",
                f"{self.metrics.avg_cache_lookup_ms:.2f}ms",
                delta=f"{self.metrics.avg_time_saved_per_render_ms:.1f}ms saved/render"
            )

        with col4:
            st.metric(
                "Total Renders",
                f"{self.metrics.total_renders}",
                delta=f"{self.metrics.cache_hits}/{self.metrics.cache_misses} hit/miss"
            )

        # Detailed breakdown
        with st.expander("📈 Detailed Cache Statistics"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Cache Layer Performance**")
                st.write(f"- Session State (L1): {self.metrics.session_state_hits} hits")
                st.write(f"- Redis (L2): {self.metrics.redis_hits} hits")
                st.write(f"- Predictive (AI): {self.metrics.predictive_hits} hits")
                st.write(f"- Cache Misses: {self.metrics.cache_misses}")

            with col2:
                st.markdown("**Performance Metrics**")
                st.write(f"- Avg Render Time: {self.metrics.avg_render_time_ms:.2f}ms")
                st.write(f"- Total Time Saved: {self.metrics.total_time_saved_ms/1000:.2f}s")
                st.write(f"- Data Requests Made: {self.metrics.data_requests_made}")
                st.write(f"- Data Requests Cached: {self.metrics.data_requests_cached}")


# Decorator for caching component render functions
def cached_render(
    component_id: str,
    ttl_seconds: int = 300,
    enable_predictive: bool = True
):
    """
    Decorator for caching component render operations.

    Usage:
        @cached_render("my_component", ttl_seconds=300)
        def render_expensive_data():
            # Expensive data fetching
            return data

    Args:
        component_id: Unique component identifier
        ttl_seconds: Cache time-to-live
        enable_predictive: Enable AI-driven cache warming
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = StreamlitCacheIntegration(
                component_id=component_id,
                config=ComponentCacheConfig(
                    component_id=component_id,
                    default_ttl_seconds=ttl_seconds,
                    enable_predictive=enable_predictive
                )
            )

            return await cache.get_cached_data(
                operation=func.__name__,
                fetch_func=func,
                ttl_seconds=ttl_seconds,
                *args,
                **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use st.cache_data as fallback
            return st.cache_data(ttl=ttl_seconds)(func)(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Export public API
__all__ = [
    'StreamlitCacheIntegration',
    'ComponentCacheConfig',
    'ComponentCacheMetrics',
    'cached_render'
]
