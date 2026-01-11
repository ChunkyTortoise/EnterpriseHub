"""
EnterpriseHub Professional Design System v2.0

A comprehensive design system for the GHL Real Estate AI platform,
providing enterprise-grade visual sophistication with WCAG 2.1 AA compliance.

Quick Start:
    from ghl_real_estate_ai.design_system import (
        inject_enterprise_theme,
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        ENTERPRISE_COLORS
    )

    # In your Streamlit app
    inject_enterprise_theme()

    # Use components
    enterprise_metric("Total Revenue", "$125,000", delta="+12.5%", delta_type="positive")
"""

from .enterprise_theme import (
    inject_enterprise_theme,
    enterprise_metric,
    enterprise_card,
    enterprise_badge,
    enterprise_progress_ring,
    enterprise_status_indicator,
    enterprise_kpi_grid,
    enterprise_section_header,
    enterprise_loading_spinner,
    enterprise_empty_state,
    enterprise_timestamp,
    apply_plotly_theme,
    ENTERPRISE_COLORS,
    ENTERPRISE_PLOTLY_THEME,
)

from .performance_monitor import (
    performance_monitor,
    track_render_performance,
    track_usage,
    EnterpriseDesignSystemMonitor,
    ComponentMetrics,
    UsageAnalytics,
    PerformanceAlert,
)

__version__ = "2.0.0"
__author__ = "EnterpriseHub Design Team"

__all__ = [
    "inject_enterprise_theme",
    "enterprise_metric",
    "enterprise_card",
    "enterprise_badge",
    "enterprise_progress_ring",
    "enterprise_status_indicator",
    "enterprise_kpi_grid",
    "enterprise_section_header",
    "enterprise_loading_spinner",
    "enterprise_empty_state",
    "enterprise_timestamp",
    "apply_plotly_theme",
    "ENTERPRISE_COLORS",
    "ENTERPRISE_PLOTLY_THEME",
    "performance_monitor",
    "track_render_performance",
    "track_usage",
    "EnterpriseDesignSystemMonitor",
    "ComponentMetrics",
    "UsageAnalytics",
    "PerformanceAlert",
]
