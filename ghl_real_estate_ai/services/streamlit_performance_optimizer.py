#!/usr/bin/env python3
"""
Streamlit Performance Optimizer
===============================

Enterprise-grade Streamlit component optimization system for the Customer Intelligence Platform.
Designed to handle 500+ concurrent users with optimized component rendering and memory management.

Features:
- Advanced component caching with intelligent invalidation
- Lazy loading for heavy components
- Memory-efficient data handling
- Optimized session state management
- Component-level performance monitoring
- Automatic resource cleanup
- Progressive data loading
- Smart component preloading

Performance Targets:
- Component Render Time: <50ms (95th percentile)
- Memory Usage: <500MB per session
- Cache Hit Rate: >95%
- Session Cleanup: <5s
- Component Load Time: <100ms

Author: Claude Code Frontend Optimization Specialist
Created: January 2026
"""

import streamlit as st
import asyncio
import time
import hashlib
import gc
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps, lru_cache
import threading
import weakref
import psutil
import pandas as pd
import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


@dataclass
class ComponentMetrics:
    """Performance metrics for Streamlit components."""
    component_name: str
    render_count: int = 0
    total_render_time_ms: float = 0.0
    avg_render_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_mb: float = 0.0
    last_rendered: datetime = field(default_factory=datetime.now)
    render_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0
    
    def record_render(self, duration_ms: float, cache_hit: bool = False, error: bool = False):
        """Record a component render."""
        if error:
            self.error_count += 1
            return
            
        self.render_count += 1
        self.total_render_time_ms += duration_ms
        self.avg_render_time_ms = self.total_render_time_ms / self.render_count
        self.last_rendered = datetime.now()
        self.render_times.append(duration_ms)
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0
    
    def get_p95_render_time(self) -> float:
        """Get 95th percentile render time."""
        if not self.render_times:
            return 0.0
        sorted_times = sorted(self.render_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]


class StreamlitPerformanceOptimizer:
    """
    Advanced Streamlit Performance Optimizer.
    
    Provides enterprise-grade component optimization with:
    - Intelligent caching strategies
    - Lazy loading capabilities
    - Memory management
    - Performance monitoring
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.session_data_cache = {}
        self.lazy_components = {}
        
        # Performance thresholds
        self.thresholds = {
            'max_render_time_ms': 50,
            'max_memory_per_session_mb': 500,
            'min_cache_hit_rate': 95,
            'max_component_load_time_ms': 100
        }
        
        # Memory management
        self.memory_monitor_thread = None
        self.memory_cleanup_enabled = True
        
        logger.info("Streamlit Performance Optimizer initialized")
    
    def optimized_component(
        self, 
        name: str, 
        ttl: int = 300, 
        key_func: Callable = None,
        lazy_load: bool = False,
        memory_limit_mb: float = 100
    ):
        """
        Decorator for optimizing Streamlit components.
        
        Args:
            name: Component identifier
            ttl: Cache TTL in seconds
            key_func: Function to generate cache key
            lazy_load: Enable lazy loading
            memory_limit_mb: Memory limit for component data
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._render_optimized_component(
                    name, func, args, kwargs, ttl, key_func, lazy_load, memory_limit_mb
                )
            return wrapper
        return decorator
    
    def _render_optimized_component(
        self, 
        name: str, 
        func: Callable, 
        args: tuple, 
        kwargs: dict,
        ttl: int,
        key_func: Optional[Callable],
        lazy_load: bool,
        memory_limit_mb: float
    ):
        """Render component with optimization strategies."""
        start_time = time.time()
        
        try:
            # Initialize component metrics
            if name not in self.component_metrics:
                self.component_metrics[name] = ComponentMetrics(component_name=name)
            
            metrics = self.component_metrics[name]
            
            # Generate cache key
            cache_key = self._generate_cache_key(name, args, kwargs, key_func)
            
            # Check cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_render(duration_ms, cache_hit=True)
                logger.debug(f"Component cache hit: {name} ({duration_ms:.2f}ms)")
                return cached_result
            
            # Lazy loading check
            if lazy_load and not self._should_load_component(name):
                return self._render_placeholder(name)
            
            # Memory check before rendering
            if not self._check_memory_limit(memory_limit_mb):
                logger.warning(f"Memory limit exceeded for component {name}")
                return self._render_memory_limit_message(name)
            
            # Render component
            with self._memory_monitor(name):
                result = func(*args, **kwargs)
            
            # Cache result
            self._set_in_cache(cache_key, result, ttl)
            
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_render(duration_ms, cache_hit=False)
            
            logger.debug(f"Component rendered: {name} ({duration_ms:.2f}ms)")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.component_metrics[name].record_render(duration_ms, error=True)
            logger.error(f"Component render failed: {name} - {e}")
            return self._render_error_message(name, str(e))
    
    def _generate_cache_key(self, name: str, args: tuple, kwargs: dict, key_func: Optional[Callable]) -> str:
        """Generate cache key for component."""
        if key_func:
            key_data = key_func(*args, **kwargs)
        else:
            # Create key from args and kwargs
            key_data = {
                'args': args,
                'kwargs': kwargs,
                'session_id': self._get_session_id()
            }
        
        # Convert to string and hash
        key_str = str(key_data)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"component:{name}:{key_hash}"
    
    def _get_from_cache(self, key: str) -> Any:
        """Get component result from cache."""
        try:
            if key in self.session_data_cache:
                return self.session_data_cache[key]
            
            # Try distributed cache
            return asyncio.create_task(self.cache_service.get(key))
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")
            return None
    
    def _set_in_cache(self, key: str, value: Any, ttl: int):
        """Set component result in cache."""
        try:
            # Store in session cache for immediate access
            self.session_data_cache[key] = value
            
            # Store in distributed cache for cross-session access
            asyncio.create_task(self.cache_service.set(key, value, ttl))
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")
    
    def _should_load_component(self, name: str) -> bool:
        """Determine if component should be loaded based on viewport/user interaction."""
        # Check if component is in viewport (simplified implementation)
        # In a real implementation, this would use JavaScript to detect viewport
        
        # Check user interaction history
        session_state = st.session_state
        interaction_key = f"component_interaction_{name}"
        
        # Load component if user has interacted with it recently
        if interaction_key in session_state:
            last_interaction = session_state[interaction_key]
            if isinstance(last_interaction, datetime) and \
               (datetime.now() - last_interaction).seconds < 60:
                return True
        
        # Load component if it's above the fold (first few components)
        component_order = session_state.get('component_order', [])
        if name in component_order and component_order.index(name) < 3:
            return True
        
        return False
    
    def _check_memory_limit(self, limit_mb: float) -> bool:
        """Check if memory usage is within limits."""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb < limit_mb
        except Exception:
            return True  # Allow rendering if we can't check memory
    
    def _memory_monitor(self, component_name: str):
        """Context manager to monitor memory usage during component rendering."""
        class MemoryMonitor:
            def __init__(self, name: str, optimizer: 'StreamlitPerformanceOptimizer'):
                self.name = name
                self.optimizer = optimizer
                self.start_memory = 0
            
            def __enter__(self):
                try:
                    process = psutil.Process()
                    self.start_memory = process.memory_info().rss / 1024 / 1024
                except Exception:
                    self.start_memory = 0
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    process = psutil.Process()
                    end_memory = process.memory_info().rss / 1024 / 1024
                    memory_used = end_memory - self.start_memory
                    
                    if self.name in self.optimizer.component_metrics:
                        self.optimizer.component_metrics[self.name].memory_usage_mb = memory_used
                        
                    if memory_used > 50:  # Log if component uses more than 50MB
                        logger.warning(f"High memory usage in component {self.name}: {memory_used:.2f}MB")
                except Exception as e:
                    logger.warning(f"Memory monitoring failed for {self.name}: {e}")
        
        return MemoryMonitor(component_name, self)
    
    def _render_placeholder(self, name: str):
        """Render placeholder for lazy-loaded component."""
        placeholder = st.empty()
        
        # Show loading indicator
        with placeholder:
            st.info(f"⏳ Loading {name}...")
            
        # Store placeholder reference for later loading
        if 'lazy_placeholders' not in st.session_state:
            st.session_state.lazy_placeholders = {}
        st.session_state.lazy_placeholders[name] = placeholder
        
        return placeholder
    
    def _render_memory_limit_message(self, name: str):
        """Render memory limit exceeded message."""
        st.warning(f"⚠️ Component {name} temporarily unavailable due to memory limits")
        if st.button(f"Force Load {name}", key=f"force_load_{name}"):
            st.rerun()
    
    def _render_error_message(self, name: str, error: str):
        """Render error message for failed component."""
        st.error(f"❌ Component {name} failed to load: {error}")
        
        # Provide retry option
        if st.button(f"Retry {name}", key=f"retry_{name}"):
            # Clear cache for this component
            self._clear_component_cache(name)
            st.rerun()
    
    def _clear_component_cache(self, name: str):
        """Clear cache for specific component."""
        # Clear session cache
        keys_to_remove = [k for k in self.session_data_cache.keys() if k.startswith(f"component:{name}:")]
        for key in keys_to_remove:
            del self.session_data_cache[key]
        
        logger.info(f"Cleared cache for component {name}")
    
    def _get_session_id(self) -> str:
        """Get current Streamlit session ID."""
        try:
            return st.session_state.get('session_id', 'default')
        except Exception:
            return 'default'
    
    # LAZY LOADING UTILITIES
    
    def register_lazy_component(self, name: str, loader_func: Callable, priority: int = 1):
        """Register a component for lazy loading."""
        self.lazy_components[name] = {
            'loader': loader_func,
            'priority': priority,
            'loaded': False,
            'load_time': None
        }
    
    def load_component_when_needed(self, name: str, *args, **kwargs):
        """Load component only when needed."""
        if name not in self.lazy_components:
            raise ValueError(f"Component {name} not registered for lazy loading")
        
        component = self.lazy_components[name]
        
        if not component['loaded']:
            start_time = time.time()
            
            try:
                result = component['loader'](*args, **kwargs)
                component['loaded'] = True
                component['load_time'] = (time.time() - start_time) * 1000
                
                logger.info(f"Lazy loaded component {name} in {component['load_time']:.2f}ms")
                return result
            except Exception as e:
                logger.error(f"Failed to lazy load component {name}: {e}")
                raise
        else:
            # Component already loaded, call loader again
            return component['loader'](*args, **kwargs)
    
    # ADVANCED CACHING STRATEGIES
    
    @lru_cache(maxsize=128)
    def _cached_data_processor(self, data_hash: str, processor_name: str):
        """LRU cache for data processing operations."""
        # This would be implemented with actual data processing logic
        pass
    
    def smart_dataframe_cache(self, df: pd.DataFrame, operation: str, **kwargs) -> pd.DataFrame:
        """Smart caching for DataFrame operations."""
        # Create hash of DataFrame and operation
        df_hash = hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()
        cache_key = f"df:{df_hash}:{operation}:{hashlib.md5(str(kwargs).encode()).hexdigest()}"
        
        # Check cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"DataFrame operation cache hit: {operation}")
            return cached_result
        
        # Perform operation (this would be expanded based on operation type)
        start_time = time.time()
        
        if operation == 'groupby':
            result = df.groupby(kwargs.get('by', [])).agg(kwargs.get('agg', {}))
        elif operation == 'filter':
            result = df.query(kwargs.get('query', 'True'))
        elif operation == 'sort':
            result = df.sort_values(kwargs.get('by', []))
        else:
            result = df
        
        duration_ms = (time.time() - start_time) * 1000
        logger.debug(f"DataFrame operation {operation} completed in {duration_ms:.2f}ms")
        
        # Cache result
        self._set_in_cache(cache_key, result, 600)  # 10 minutes
        
        return result
    
    # MEMORY MANAGEMENT
    
    def start_memory_monitoring(self):
        """Start background memory monitoring."""
        if self.memory_monitor_thread is None or not self.memory_monitor_thread.is_alive():
            self.memory_cleanup_enabled = True
            self.memory_monitor_thread = threading.Thread(target=self._memory_monitor_loop, daemon=True)
            self.memory_monitor_thread.start()
            logger.info("Memory monitoring started")
    
    def stop_memory_monitoring(self):
        """Stop background memory monitoring."""
        self.memory_cleanup_enabled = False
        if self.memory_monitor_thread:
            self.memory_monitor_thread.join(timeout=1)
        logger.info("Memory monitoring stopped")
    
    def _memory_monitor_loop(self):
        """Background memory monitoring loop."""
        while self.memory_cleanup_enabled:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                # Trigger cleanup if memory usage is high
                if memory_mb > 1000:  # 1GB threshold
                    self._perform_memory_cleanup()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(60)
    
    def _perform_memory_cleanup(self):
        """Perform memory cleanup operations."""
        logger.info("Performing memory cleanup")
        
        # Clear old session cache entries
        current_time = time.time()
        old_keys = []
        
        for key in list(self.session_data_cache.keys()):
            # Remove entries older than 1 hour
            if current_time - self.session_data_cache.get(f"{key}_timestamp", current_time) > 3600:
                old_keys.append(key)
        
        for key in old_keys:
            del self.session_data_cache[key]
        
        # Force garbage collection
        gc.collect()
        
        logger.info(f"Memory cleanup completed. Removed {len(old_keys)} cached entries")
    
    def cleanup_session_data(self, session_id: str = None):
        """Cleanup data for specific session."""
        session_id = session_id or self._get_session_id()
        
        # Remove session-specific cache entries
        keys_to_remove = [k for k in self.session_data_cache.keys() if session_id in k]
        
        for key in keys_to_remove:
            del self.session_data_cache[key]
        
        logger.info(f"Cleaned up session data for {session_id}")
    
    # PERFORMANCE ANALYTICS
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for all components."""
        metrics_summary = {}
        
        for name, metrics in self.component_metrics.items():
            metrics_summary[name] = {
                'render_count': metrics.render_count,
                'avg_render_time_ms': round(metrics.avg_render_time_ms, 2),
                'p95_render_time_ms': round(metrics.get_p95_render_time(), 2),
                'cache_hit_rate': round(metrics.get_cache_hit_rate(), 2),
                'cache_hits': metrics.cache_hits,
                'cache_misses': metrics.cache_misses,
                'memory_usage_mb': round(metrics.memory_usage_mb, 2),
                'error_count': metrics.error_count,
                'last_rendered': metrics.last_rendered.isoformat()
            }
        
        # Overall statistics
        all_metrics = list(self.component_metrics.values())
        overall_stats = {
            'total_components': len(all_metrics),
            'total_renders': sum(m.render_count for m in all_metrics),
            'avg_render_time_ms': round(
                sum(m.avg_render_time_ms for m in all_metrics) / len(all_metrics), 2
            ) if all_metrics else 0,
            'overall_cache_hit_rate': round(
                sum(m.cache_hits for m in all_metrics) / 
                max(sum(m.cache_hits + m.cache_misses for m in all_metrics), 1) * 100, 2
            ),
            'total_memory_mb': round(sum(m.memory_usage_mb for m in all_metrics), 2),
            'total_errors': sum(m.error_count for m in all_metrics)
        }
        
        # Memory usage
        try:
            process = psutil.Process()
            memory_info = {
                'current_memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'memory_percent': round(process.memory_percent(), 2)
            }
        except Exception:
            memory_info = {'current_memory_mb': 0, 'memory_percent': 0}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'components': metrics_summary,
            'overall': overall_stats,
            'memory': memory_info,
            'cache_stats': len(self.session_data_cache),
            'lazy_components': len(self.lazy_components)
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance metrics."""
        recommendations = []
        
        # Analyze component performance
        for name, metrics in self.component_metrics.items():
            # Slow rendering components
            if metrics.get_p95_render_time() > self.thresholds['max_render_time_ms']:
                recommendations.append({
                    'category': 'component_performance',
                    'severity': 'medium',
                    'component': name,
                    'issue': f'Slow rendering ({metrics.get_p95_render_time():.1f}ms p95)',
                    'suggestions': [
                        'Consider breaking into smaller components',
                        'Implement data pagination',
                        'Add more aggressive caching',
                        'Use lazy loading for heavy content'
                    ]
                })
            
            # Low cache hit rates
            if metrics.get_cache_hit_rate() < self.thresholds['min_cache_hit_rate']:
                recommendations.append({
                    'category': 'caching',
                    'severity': 'low',
                    'component': name,
                    'issue': f'Low cache hit rate ({metrics.get_cache_hit_rate():.1f}%)',
                    'suggestions': [
                        'Increase cache TTL',
                        'Review cache key generation logic',
                        'Consider component-specific caching strategies',
                        'Implement cache warming'
                    ]
                })
            
            # High memory usage
            if metrics.memory_usage_mb > 100:
                recommendations.append({
                    'category': 'memory_usage',
                    'severity': 'high',
                    'component': name,
                    'issue': f'High memory usage ({metrics.memory_usage_mb:.1f}MB)',
                    'suggestions': [
                        'Implement data streaming',
                        'Use data sampling for large datasets',
                        'Add memory cleanup after rendering',
                        'Consider data compression'
                    ]
                })
        
        return recommendations
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        self.component_metrics.clear()
        self.session_data_cache.clear()
        logger.info("Performance metrics reset")


# Global instance
_streamlit_optimizer: Optional[StreamlitPerformanceOptimizer] = None


def get_streamlit_optimizer() -> StreamlitPerformanceOptimizer:
    """Get global Streamlit optimizer instance."""
    global _streamlit_optimizer
    if _streamlit_optimizer is None:
        _streamlit_optimizer = StreamlitPerformanceOptimizer()
        _streamlit_optimizer.start_memory_monitoring()
    return _streamlit_optimizer


# Convenience decorators

def optimized_component(name: str, ttl: int = 300, lazy: bool = False):
    """Decorator for optimizing Streamlit components."""
    optimizer = get_streamlit_optimizer()
    return optimizer.optimized_component(name, ttl=ttl, lazy_load=lazy)


def cached_data_loader(ttl: int = 600, key_prefix: str = "data"):
    """Decorator for caching data loading operations."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = {'func': func.__name__, 'args': args, 'kwargs': kwargs}
            key_hash = hashlib.md5(str(key_data).encode()).hexdigest()
            cache_key = f"{key_prefix}:{key_hash}"
            
            # Use Streamlit's built-in caching
            @st.cache_data(ttl=ttl)
            def cached_func(*args, **kwargs):
                return func(*args, **kwargs)
            
            return cached_func(*args, **kwargs)
        
        return wrapper
    return decorator