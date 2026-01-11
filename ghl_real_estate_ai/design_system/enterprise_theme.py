"""
EnterpriseHub Professional Design System v2.0
Python integration module for Streamlit applications.

This module provides easy integration of the enterprise design system
into any Streamlit application within the GHL Real Estate AI platform.

Usage:
    from design_system.enterprise_theme import (
        inject_enterprise_theme,
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring
    )

    # In your Streamlit app
    inject_enterprise_theme()

    # Use components
    enterprise_metric("Revenue", "$125,000", delta="+12.5%", delta_type="positive")

Author: EnterpriseHub Design Team
Version: 2.0.0
Last Updated: January 10, 2026
"""

import streamlit as st
from pathlib import Path
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime


# Type definitions
DeltaType = Literal["positive", "negative", "neutral"]
BadgeVariant = Literal["default", "primary", "gold", "success", "warning", "danger", "info", "live"]
CardVariant = Literal["default", "gold", "success", "warning", "danger", "info", "glass", "premium"]


def get_css_path() -> Path:
    """Get the path to the enterprise theme CSS file."""
    return Path(__file__).parent / "enterprise_theme.css"


def inject_enterprise_theme(custom_css: Optional[str] = None) -> None:
    """
    Inject the enterprise design system CSS into the Streamlit app.

    Args:
        custom_css: Optional additional CSS to inject after the main theme
    """
    css_path = get_css_path()

    if css_path.exists():
        with open(css_path, "r") as f:
            enterprise_css = f.read()
    else:
        enterprise_css = get_fallback_css()

    # Combine with custom CSS if provided
    if custom_css:
        enterprise_css += f"\n\n/* Custom CSS */\n{custom_css}"

    st.markdown(f"<style>{enterprise_css}</style>", unsafe_allow_html=True)


def get_fallback_css() -> str:
    """Return minimal fallback CSS if the main file is not found."""
    return """
    :root {
        --enterprise-navy-600: #1e3a8a;
        --enterprise-gold-500: #d4af37;
        --neutral-800: #1e293b;
        --neutral-600: #475569;
        --neutral-100: #f1f5f9;
    }

    .enterprise-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    """


def enterprise_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: DeltaType = "neutral",
    icon: Optional[str] = None
) -> None:
    """
    Render an enterprise-styled metric card.

    Args:
        label: Metric label text
        value: Metric value to display
        delta: Optional delta/change indicator
        delta_type: Type of delta - "positive", "negative", or "neutral"
        icon: Optional emoji icon to display
    """
    delta_html = ""
    if delta:
        delta_classes = {
            "positive": "enterprise-metric__delta--positive",
            "negative": "enterprise-metric__delta--negative",
            "neutral": ""
        }
        delta_class = delta_classes.get(delta_type, "")

        arrow = ""
        if delta_type == "positive":
            arrow = "+"
        elif delta_type == "negative":
            arrow = ""  # Negative sign is usually included in the delta value

        delta_html = f'''
        <span class="enterprise-metric__delta {delta_class}">
            {arrow}{delta}
        </span>
        '''

    icon_html = f'<span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>' if icon else ""

    st.markdown(f"""
    <div class="enterprise-metric">
        <div class="enterprise-metric__label">{icon_html}{label}</div>
        <div class="enterprise-metric__value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def enterprise_card(
    content: str,
    title: Optional[str] = None,
    variant: CardVariant = "default",
    footer: Optional[str] = None
) -> None:
    """
    Render an enterprise-styled card.

    Args:
        content: HTML content for the card body
        title: Optional card title
        variant: Card style variant
        footer: Optional footer content
    """
    variant_class = f"enterprise-card--{variant}" if variant != "default" else ""

    title_html = ""
    if title:
        title_html = f'''
        <div style="
            font-family: var(--font-heading, Inter);
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--neutral-800, #1e293b);
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-light, #e2e8f0);
        ">{title}</div>
        '''

    footer_html = ""
    if footer:
        footer_html = f'''
        <div style="
            margin-top: 1rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border-light, #e2e8f0);
            font-size: 0.875rem;
            color: var(--neutral-500, #64748b);
        ">{footer}</div>
        '''

    st.markdown(f"""
    <div class="enterprise-card {variant_class}">
        {title_html}
        <div class="enterprise-card__content">{content}</div>
        {footer_html}
    </div>
    """, unsafe_allow_html=True)


def enterprise_badge(
    text: str,
    variant: BadgeVariant = "default",
    icon: Optional[str] = None
) -> str:
    """
    Generate HTML for an enterprise-styled badge.

    Args:
        text: Badge text
        variant: Badge style variant
        icon: Optional emoji icon

    Returns:
        HTML string for the badge
    """
    icon_html = f'<span style="margin-right: 4px;">{icon}</span>' if icon else ""

    return f'''
    <span class="enterprise-badge enterprise-badge--{variant}">
        {icon_html}{text}
    </span>
    '''


def enterprise_progress_ring(
    value: float,
    label: str,
    size: int = 80,
    stroke_width: int = 8,
    color: Optional[str] = None
) -> None:
    """
    Render a circular progress ring.

    Args:
        value: Progress value (0-100)
        label: Label text below the ring
        size: Ring size in pixels
        stroke_width: Stroke width in pixels
        color: Optional custom color (uses gradient if not provided)
    """
    # Calculate circle properties
    radius = (size - stroke_width) / 2
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - value / 100)

    # Determine color based on value if not provided
    if color is None:
        if value >= 80:
            color = "#059669"  # Success
        elif value >= 60:
            color = "#f59e0b"  # Warning
        else:
            color = "#ef4444"  # Danger

    st.markdown(f"""
    <div style="text-align: center;">
        <div style="position: relative; display: inline-block;">
            <svg width="{size}" height="{size}" style="transform: rotate(-90deg);">
                <circle
                    cx="{size/2}"
                    cy="{size/2}"
                    r="{radius}"
                    fill="none"
                    stroke="#e2e8f0"
                    stroke-width="{stroke_width}"
                />
                <circle
                    cx="{size/2}"
                    cy="{size/2}"
                    r="{radius}"
                    fill="none"
                    stroke="{color}"
                    stroke-width="{stroke_width}"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{offset}"
                    stroke-linecap="round"
                    style="transition: stroke-dashoffset 1s ease-in-out;"
                />
            </svg>
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(0deg);
                font-family: var(--font-display, 'Playfair Display');
                font-size: 1.25rem;
                font-weight: 700;
                color: {color};
            ">{value:.0f}%</div>
        </div>
        <div style="
            margin-top: 0.5rem;
            font-size: 0.875rem;
            color: var(--neutral-500, #64748b);
        ">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def enterprise_status_indicator(
    status: Literal["active", "warning", "danger", "inactive"],
    label: str,
    description: Optional[str] = None
) -> None:
    """
    Render a status indicator with label.

    Args:
        status: Status type
        label: Status label
        description: Optional description text
    """
    status_config = {
        "active": {"color": "#059669", "bg": "#d1fae5", "icon": ""},
        "warning": {"color": "#f59e0b", "bg": "#fef3c7", "icon": ""},
        "danger": {"color": "#ef4444", "bg": "#fee2e2", "icon": ""},
        "inactive": {"color": "#64748b", "bg": "#f1f5f9", "icon": ""}
    }

    config = status_config.get(status, status_config["inactive"])

    description_html = ""
    if description:
        description_html = f'''
        <div style="
            font-size: 0.75rem;
            color: var(--neutral-500, #64748b);
            margin-top: 0.25rem;
        ">{description}</div>
        '''

    st.markdown(f"""
    <div class="status-indicator {status}" style="
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 0.75rem;
        background: {config['bg']};
        border: 1px solid {config['color']}20;
    ">
        <span style="font-size: 1rem;">{config['icon']}</span>
        <div>
            <span style="
                font-weight: 600;
                font-size: 0.875rem;
                color: {config['color']};
            ">{label}</span>
            {description_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def enterprise_kpi_grid(metrics: List[Dict[str, Any]], columns: int = 4) -> None:
    """
    Render a grid of KPI metrics.

    Args:
        metrics: List of metric dictionaries with keys: label, value, delta, delta_type, icon
        columns: Number of columns in the grid
    """
    cols = st.columns(columns)

    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            enterprise_metric(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                delta_type=metric.get("delta_type", "neutral"),
                icon=metric.get("icon")
            )


def enterprise_section_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    action_button: Optional[str] = None
) -> None:
    """
    Render a section header with optional subtitle and action button.

    Args:
        title: Section title
        subtitle: Optional subtitle text
        icon: Optional emoji icon
        action_button: Optional action button HTML
    """
    icon_html = f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ""

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'''
        <p style="
            margin: 0.5rem 0 0 0;
            font-size: 1rem;
            color: var(--neutral-500, #64748b);
            line-height: 1.5;
        ">{subtitle}</p>
        '''

    action_html = f'<div style="margin-left: auto;">{action_button}</div>' if action_button else ""

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: flex-start;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--border-light, #e2e8f0);
    ">
        <div>
            <h2 class="enterprise-gradient-text" style="
                font-family: var(--font-display, 'Playfair Display');
                font-size: 1.875rem;
                font-weight: 700;
                margin: 0;
                background: linear-gradient(135deg, #1e3a8a, #d4af37);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            ">{icon_html}{title}</h2>
            {subtitle_html}
        </div>
        {action_html}
    </div>
    """, unsafe_allow_html=True)


def enterprise_loading_spinner(message: str = "Loading...") -> None:
    """
    Render an enterprise-styled loading spinner.

    Args:
        message: Loading message text
    """
    st.markdown(f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    ">
        <div style="
            width: 50px;
            height: 50px;
            border: 3px solid rgba(212, 175, 55, 0.2);
            border-top-color: #d4af37;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <p style="
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--neutral-500, #64748b);
        ">{message}</p>
    </div>
    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """, unsafe_allow_html=True)


def enterprise_empty_state(
    title: str,
    description: str,
    icon: str = "",
    action_label: Optional[str] = None
) -> None:
    """
    Render an empty state placeholder.

    Args:
        title: Empty state title
        description: Description text
        icon: Emoji icon
        action_label: Optional action button label
    """
    action_html = ""
    if action_label:
        action_html = f'''
        <button class="enterprise-btn enterprise-btn--primary" style="
            display: inline-flex;
            align-items: center;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #1e3a8a, #0f1d32);
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 1rem;
        ">{action_label}</button>
        '''

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        background: var(--neutral-50, #f8fafc);
        border: 2px dashed var(--border-light, #e2e8f0);
        border-radius: 1rem;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="
            font-family: var(--font-heading, Inter);
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--neutral-800, #1e293b);
            margin: 0 0 0.5rem 0;
        ">{title}</h3>
        <p style="
            font-size: 0.875rem;
            color: var(--neutral-500, #64748b);
            max-width: 300px;
            margin: 0 auto;
        ">{description}</p>
        {action_html}
    </div>
    """, unsafe_allow_html=True)


def enterprise_timestamp(
    timestamp: datetime,
    prefix: str = "Last updated"
) -> None:
    """
    Render a formatted timestamp.

    Args:
        timestamp: Datetime object
        prefix: Text prefix before the timestamp
    """
    formatted_time = timestamp.strftime("%B %d, %Y at %I:%M %p")

    st.markdown(f"""
    <div style="
        font-size: 0.75rem;
        color: var(--neutral-400, #94a3b8);
        font-style: italic;
        text-align: right;
    ">
        {prefix}: {formatted_time}
    </div>
    """, unsafe_allow_html=True)


# Color palette constants for external use
ENTERPRISE_COLORS = {
    "navy": {
        "950": "#020617",
        "900": "#0a1628",
        "800": "#0f1d32",
        "700": "#1e3a5f",
        "600": "#1e3a8a",
        "500": "#2563eb",
        "400": "#3b82f6",
        "300": "#60a5fa",
    },
    "gold": {
        "600": "#b8860b",
        "500": "#d4af37",
        "400": "#e5c158",
        "300": "#f0d77a",
        "200": "#faf0c8",
    },
    "bronze": {
        "600": "#8b5a2b",
        "500": "#cd7f32",
        "400": "#d4946a",
    },
    "success": {
        "600": "#047857",
        "500": "#059669",
        "400": "#10b981",
        "100": "#d1fae5",
    },
    "warning": {
        "600": "#d97706",
        "500": "#f59e0b",
        "400": "#fbbf24",
        "100": "#fef3c7",
    },
    "danger": {
        "600": "#dc2626",
        "500": "#ef4444",
        "400": "#f87171",
        "100": "#fee2e2",
    },
    "info": {
        "600": "#0284c7",
        "500": "#0ea5e9",
        "400": "#38bdf8",
        "100": "#e0f2fe",
    },
}

# Plotly theme configuration
ENTERPRISE_PLOTLY_THEME = {
    "layout": {
        "font": {
            "family": "Inter, -apple-system, sans-serif",
            "size": 12,
            "color": "#334155"
        },
        "title": {
            "font": {
                "family": "Inter, sans-serif",
                "size": 18,
                "color": "#1e293b"
            }
        },
        "paper_bgcolor": "rgba(255, 255, 255, 0)",
        "plot_bgcolor": "rgba(255, 255, 255, 0)",
        "colorway": [
            "#1e3a8a",  # Navy primary
            "#d4af37",  # Gold
            "#059669",  # Success green
            "#3b82f6",  # Blue accent
            "#f59e0b",  # Amber
            "#8b5cf6",  # Purple
            "#ef4444",  # Red
            "#06b6d4",  # Cyan
            "#84cc16",  # Lime
            "#ec4899"   # Pink
        ],
        "xaxis": {
            "gridcolor": "#e2e8f0",
            "linecolor": "#e2e8f0",
            "tickfont": {"size": 11, "color": "#64748b"}
        },
        "yaxis": {
            "gridcolor": "#e2e8f0",
            "linecolor": "#e2e8f0",
            "tickfont": {"size": 11, "color": "#64748b"}
        },
        "legend": {
            "font": {"size": 11, "color": "#475569"},
            "bgcolor": "rgba(255, 255, 255, 0.8)"
        },
        "margin": {"l": 60, "r": 30, "t": 50, "b": 50}
    }
}


def apply_plotly_theme(fig) -> None:
    """
    Apply the enterprise theme to a Plotly figure.

    Args:
        fig: Plotly figure object
    """
    fig.update_layout(**ENTERPRISE_PLOTLY_THEME["layout"])


# Export all public functions and constants
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
]
