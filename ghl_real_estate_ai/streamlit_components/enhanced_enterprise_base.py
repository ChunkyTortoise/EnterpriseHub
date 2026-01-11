"""
Enhanced Enterprise Base Component for GHL Real Estate AI
========================================================

Advanced base class for all Streamlit components providing:
- Consistent enterprise styling and theming
- Standardized component patterns and behaviors
- Performance optimization and caching
- Accessibility compliance (WCAG AAA)
- Professional real estate industry UI patterns

This enhanced base component replaces the original base component with
enterprise-grade functionality and sophisticated visual design.

Author: EnterpriseHub Design System
Date: January 2026
Version: 2.0.0
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
import uuid
from datetime import datetime

from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


@dataclass
class ComponentMetrics:
    """Component performance and usage metrics."""
    component_id: str
    render_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    user_interactions: int = 0
    accessibility_score: float = 100.0
    last_rendered: Optional[datetime] = None


@dataclass
class ComponentState:
    """Component state management."""
    component_id: str
    is_loading: bool = False
    has_error: bool = False
    error_message: Optional[str] = None
    data_cache: Dict[str, Any] = None
    user_preferences: Dict[str, Any] = None


class EnhancedEnterpriseComponent(ABC):
    """
    Enhanced base class for all enterprise Streamlit components.

    Provides:
    - Consistent enterprise theming and styling
    - Performance monitoring and optimization
    - Accessibility compliance
    - Error handling and loading states
    - Caching and state management
    - Professional real estate UI patterns
    """

    def __init__(
        self,
        component_id: Optional[str] = None,
        theme_variant: ThemeVariant = ThemeVariant.ENTERPRISE_LIGHT,
        enable_metrics: bool = True,
        enable_caching: bool = True
    ):
        """
        Initialize enhanced enterprise component.

        Args:
            component_id: Unique identifier for the component
            theme_variant: Enterprise theme variant to use
            enable_metrics: Enable performance and usage metrics
            enable_caching: Enable component-level caching
        """
        self.component_id = component_id or f"enterprise_component_{uuid.uuid4().hex[:8]}"
        self.theme_variant = theme_variant
        self.enable_metrics = enable_metrics
        self.enable_caching = enable_caching

        # Initialize theme manager
        self.theme_manager = EnterpriseThemeManager(theme_variant)

        # Initialize component state
        self.state = ComponentState(component_id=self.component_id)
        self.metrics = ComponentMetrics(component_id=self.component_id)

        # Inject theme CSS on first initialization
        self._ensure_theme_injected()

    def _ensure_theme_injected(self) -> None:
        """Ensure enterprise theme is injected into the app."""
        theme_key = f"enterprise_theme_injected_{self.theme_variant.value}"

        if theme_key not in st.session_state:
            self.theme_manager.inject_enterprise_css()
            st.session_state[theme_key] = True

    def _start_performance_tracking(self) -> float:
        """Start performance tracking for render operations."""
        if not self.enable_metrics:
            return 0.0

        return time.time()

    def _end_performance_tracking(self, start_time: float) -> None:
        """End performance tracking and record metrics."""
        if not self.enable_metrics or start_time == 0.0:
            return

        render_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        self.metrics.render_time_ms = render_time
        self.metrics.last_rendered = datetime.now()

        # Store metrics in session state for aggregation
        metrics_key = f"component_metrics_{self.component_id}"
        if metrics_key not in st.session_state:
            st.session_state[metrics_key] = []

        st.session_state[metrics_key].append({
            'timestamp': datetime.now().isoformat(),
            'render_time_ms': render_time,
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses
        })

        # Keep only last 100 measurements
        if len(st.session_state[metrics_key]) > 100:
            st.session_state[metrics_key] = st.session_state[metrics_key][-100:]

    def _cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key for component operations."""
        import hashlib
        key_string = f"{self.component_id}_{operation}_{str(args)}_{str(kwargs)}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Retrieve cached data if available."""
        if not self.enable_caching:
            return None

        cache_store = st.session_state.get('enterprise_component_cache', {})

        if cache_key in cache_store:
            self.metrics.cache_hits += 1
            return cache_store[cache_key]['data']

        self.metrics.cache_misses += 1
        return None

    def _set_cached_data(
        self,
        cache_key: str,
        data: Any,
        ttl_seconds: int = 300
    ) -> None:
        """Store data in component cache."""
        if not self.enable_caching:
            return

        if 'enterprise_component_cache' not in st.session_state:
            st.session_state['enterprise_component_cache'] = {}

        cache_store = st.session_state['enterprise_component_cache']

        # Clean expired entries
        current_time = time.time()
        expired_keys = [
            key for key, value in cache_store.items()
            if current_time - value.get('timestamp', 0) > value.get('ttl', 300)
        ]

        for key in expired_keys:
            del cache_store[key]

        # Store new data
        cache_store[cache_key] = {
            'data': data,
            'timestamp': current_time,
            'ttl': ttl_seconds
        }

    def render_with_enterprise_wrapper(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        show_metrics: bool = False,
        container_type: str = "default",
        **render_kwargs
    ) -> None:
        """
        Render component with enterprise wrapper and performance tracking.

        Args:
            title: Component title
            subtitle: Component subtitle
            show_metrics: Show performance metrics
            container_type: Container styling type
            **render_kwargs: Arguments passed to the render method
        """
        start_time = self._start_performance_tracking()

        try:
            # Set loading state
            self.state.is_loading = True
            self.state.has_error = False
            self.state.error_message = None

            # Create component container
            self._create_component_container(
                title=title,
                subtitle=subtitle,
                container_type=container_type
            )

            # Render the actual component
            self.render(**render_kwargs)

            # Show performance metrics if enabled
            if show_metrics and self.enable_metrics:
                self._render_performance_metrics()

        except Exception as e:
            self._handle_component_error(e)

        finally:
            self.state.is_loading = False
            self._end_performance_tracking(start_time)

    def _create_component_container(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        container_type: str = "default"
    ) -> None:
        """Create styled container for the component."""
        if not title and not subtitle:
            return

        container_styles = {
            "default": "enterprise-card",
            "elevated": "enterprise-card card-elevated",
            "interactive": "enterprise-card card-interactive"
        }

        container_class = container_styles.get(container_type, "enterprise-card")

        header_html = ""
        if title:
            header_html += f"""
                <h2 style="
                    margin: 0 0 {subtitle and '8px' or '16px'} 0;
                    color: var(--enterprise-charcoal-primary);
                    font-size: var(--enterprise-text-xl);
                    font-weight: 600;
                ">{title}</h2>
            """

        if subtitle:
            header_html += f"""
                <p style="
                    margin: 0 0 16px 0;
                    color: var(--enterprise-slate-secondary);
                    font-size: var(--enterprise-text-sm);
                ">{subtitle}</p>
            """

        if header_html:
            st.markdown(f"""
                <div class="{container_class}" style="margin-bottom: 24px;">
                    {header_html}
                </div>
            """, unsafe_allow_html=True)

    def _handle_component_error(self, error: Exception) -> None:
        """Handle component errors with enterprise styling."""
        self.state.has_error = True
        self.state.error_message = str(error)

        error_html = create_enterprise_alert(
            message=f"Component Error: {str(error)}",
            alert_type="danger",
            title="🚨 Component Error"
        )

        st.markdown(error_html, unsafe_allow_html=True)

        # Log error for debugging
        if self.enable_metrics:
            error_key = f"component_errors_{self.component_id}"
            if error_key not in st.session_state:
                st.session_state[error_key] = []

            st.session_state[error_key].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(error),
                'component_id': self.component_id
            })

    def _render_performance_metrics(self) -> None:
        """Render performance metrics for the component."""
        if not self.enable_metrics:
            return

        metrics_html = f"""
            <div style="
                background: var(--enterprise-bg-secondary);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: var(--enterprise-radius-md);
                padding: var(--enterprise-space-8);
                margin-top: var(--enterprise-space-4);
                font-size: var(--enterprise-text-xs);
                color: var(--enterprise-slate-secondary);
            ">
                <strong>Performance Metrics:</strong>
                Render Time: {self.metrics.render_time_ms:.2f}ms |
                Cache Hits: {self.metrics.cache_hits} |
                Cache Misses: {self.metrics.cache_misses} |
                Component ID: {self.component_id}
            </div>
        """

        st.markdown(metrics_html, unsafe_allow_html=True)

    @abstractmethod
    def render(self, **kwargs) -> None:
        """
        Abstract method that must be implemented by concrete components.

        This method contains the actual component rendering logic.
        """
        pass

    # Enterprise UI Helper Methods

    def create_metric_grid(
        self,
        metrics: List[Dict[str, Any]],
        columns: int = 4
    ) -> None:
        """
        Create a grid of enterprise metrics.

        Args:
            metrics: List of metric dictionaries with title, value, delta, etc.
            columns: Number of columns in the grid
        """
        cols = st.columns(columns)

        for i, metric in enumerate(metrics):
            col_idx = i % columns
            with cols[col_idx]:
                metric_html = create_enterprise_metric(
                    title=metric.get('title', ''),
                    value=metric.get('value', ''),
                    delta=metric.get('delta'),
                    delta_type=metric.get('delta_type', 'neutral'),
                    icon=metric.get('icon', '')
                )
                st.markdown(metric_html, unsafe_allow_html=True)

    def create_info_card(
        self,
        content: str,
        title: Optional[str] = None,
        variant: str = "default",
        icon: str = ""
    ) -> None:
        """
        Create an enterprise-styled information card.

        Args:
            content: Card content (HTML supported)
            title: Optional card title
            variant: Card style variant
            icon: Optional icon
        """
        card_content = ""
        if title:
            card_content += f"""
                <h3 style="
                    margin: 0 0 12px 0;
                    color: var(--enterprise-charcoal-primary);
                    font-size: var(--enterprise-text-lg);
                    font-weight: 600;
                ">{icon} {title}</h3>
            """
        card_content += content

        card_html = create_enterprise_card(
            content=card_content,
            variant=variant
        )

        st.markdown(card_html, unsafe_allow_html=True)

    def create_status_indicator(
        self,
        status: str,
        message: str,
        show_icon: bool = True
    ) -> None:
        """
        Create a status indicator with enterprise styling.

        Args:
            status: Status type (success, warning, error, info)
            message: Status message
            show_icon: Whether to show status icon
        """
        icons = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️'
        }

        icon = icons.get(status, '') if show_icon else ''
        full_message = f"{icon} {message}" if icon else message

        alert_html = create_enterprise_alert(
            message=full_message,
            alert_type=status if status != 'error' else 'danger'
        )

        st.markdown(alert_html, unsafe_allow_html=True)

    def create_loading_placeholder(
        self,
        message: str = "Loading...",
        height: str = "200px"
    ) -> None:
        """
        Create an enterprise-styled loading placeholder.

        Args:
            message: Loading message
            height: Placeholder height
        """
        loading_html = f"""
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: {height};
                background: var(--enterprise-bg-secondary);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: var(--enterprise-radius-lg);
                color: var(--enterprise-slate-secondary);
            ">
                <div style="
                    width: 32px;
                    height: 32px;
                    border: 3px solid rgba(183, 121, 31, 0.2);
                    border-top: 3px solid var(--enterprise-primary-gold);
                    border-radius: 50%;
                    margin-bottom: 16px;
                " class="animate-spin"></div>
                <div style="font-weight: 500;">{message}</div>
            </div>
        """

        st.markdown(loading_html, unsafe_allow_html=True)

    def add_component_header(
        self,
        title: str,
        subtitle: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add a professional component header with optional actions.

        Args:
            title: Header title
            subtitle: Optional subtitle
            actions: List of action button configurations
        """
        header_content = f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 1px solid rgba(148, 163, 184, 0.2);
            ">
                <div>
                    <h1 style="
                        margin: 0;
                        color: var(--enterprise-charcoal-primary);
                        font-size: var(--enterprise-text-3xl);
                        font-weight: 600;
                    ">{title}</h1>
        """

        if subtitle:
            header_content += f"""
                    <p style="
                        margin: 4px 0 0 0;
                        color: var(--enterprise-slate-secondary);
                        font-size: var(--enterprise-text-base);
                    ">{subtitle}</p>
            """

        header_content += "</div>"

        # Add action buttons if provided
        if actions:
            header_content += '<div style="display: flex; gap: 8px;">'
            for action in actions:
                btn_class = f"enterprise-btn enterprise-btn-{action.get('variant', 'secondary')}"
                header_content += f"""
                    <button class="{btn_class}" onclick="{action.get('onclick', '')}">
                        {action.get('icon', '')} {action.get('label', 'Action')}
                    </button>
                """
            header_content += "</div>"

        header_content += "</div>"

        st.markdown(header_content, unsafe_allow_html=True)

    # Accessibility helpers

    def add_screen_reader_text(self, text: str) -> None:
        """Add screen reader only text for accessibility."""
        sr_text = f"""
            <span style="
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            ">{text}</span>
        """
        st.markdown(sr_text, unsafe_allow_html=True)

    def add_aria_live_region(self, content: str, politeness: str = "polite") -> None:
        """Add ARIA live region for dynamic content updates."""
        live_region = f"""
            <div aria-live="{politeness}" aria-atomic="true" style="
                position: absolute;
                left: -10000px;
                top: auto;
                width: 1px;
                height: 1px;
                overflow: hidden;
            ">{content}</div>
        """
        st.markdown(live_region, unsafe_allow_html=True)

    # Performance optimization helpers

    def cached_data_operation(
        self,
        operation_func: Callable,
        cache_key_params: List[Any],
        ttl_seconds: int = 300
    ) -> Any:
        """
        Perform cached data operation with automatic cache management.

        Args:
            operation_func: Function to execute if cache miss
            cache_key_params: Parameters to include in cache key
            ttl_seconds: Cache time-to-live in seconds

        Returns:
            Result of the operation (cached or fresh)
        """
        cache_key = self._cache_key("data_operation", *cache_key_params)
        cached_result = self._get_cached_data(cache_key)

        if cached_result is not None:
            return cached_result

        # Execute operation and cache result
        result = operation_func()
        self._set_cached_data(cache_key, result, ttl_seconds)

        return result

    # Component lifecycle hooks

    def on_component_mount(self) -> None:
        """Called when component is first mounted."""
        pass

    def on_component_update(self, **kwargs) -> None:
        """Called when component props/state change."""
        pass

    def on_component_unmount(self) -> None:
        """Called when component is unmounted."""
        pass


# Convenience base classes for common component types

class EnterpriseDataComponent(EnhancedEnterpriseComponent):
    """Enhanced base class for data visualization components."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.component_type = ComponentType.CHART

    def create_chart_container(
        self,
        title: str,
        height: int = 400,
        show_export: bool = True
    ) -> None:
        """Create a standardized chart container."""
        container_html = f"""
            <div class="enterprise-card" style="margin-bottom: 24px;">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                ">
                    <h3 style="
                        margin: 0;
                        color: var(--enterprise-charcoal-primary);
                        font-size: var(--enterprise-text-lg);
                        font-weight: 600;
                    ">{title}</h3>
        """

        if show_export:
            container_html += """
                    <button class="enterprise-btn enterprise-btn-secondary">
                        📊 Export
                    </button>
            """

        container_html += """
                </div>
                <div style="height: """ + str(height) + """px;"></div>
            </div>
        """

        st.markdown(container_html, unsafe_allow_html=True)


class EnterpriseDashboardComponent(EnhancedEnterpriseComponent):
    """Enhanced base class for dashboard components."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.component_type = ComponentType.DASHBOARD

    def create_dashboard_header(
        self,
        title: str,
        subtitle: Optional[str] = None,
        auto_refresh: bool = False
    ) -> None:
        """Create standardized dashboard header."""
        self.add_component_header(
            title=title,
            subtitle=subtitle,
            actions=[
                {
                    'label': 'Refresh',
                    'variant': 'secondary',
                    'icon': '🔄',
                    'onclick': 'location.reload()'
                }
            ] if not auto_refresh else []
        )


# Export key components
__all__ = [
    'EnhancedEnterpriseComponent',
    'EnterpriseDataComponent',
    'EnterpriseDashboardComponent',
    'ComponentMetrics',
    'ComponentState'
]