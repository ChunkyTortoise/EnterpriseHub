"""
Obsidian-themed metric primitive component.
Replaces 50+ inline metric implementations with reusable, type-safe component.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Union

import streamlit as st

from .icon import icon


@dataclass
class MetricConfig:
    """
    Type-safe metric configuration (AI-readable).

    Attributes:
        variant: Metric style variant
        trend: Trend direction for indicator
        trend_color: Custom color for trend indicator
        show_comparison: Whether to show comparison value
        size: Size variant for the metric display
        glow_effect: Whether to apply glow effect to the metric
    """

    variant: Literal["default", "success", "warning", "error", "premium"] = "default"
    trend: Literal["up", "down", "neutral", "none"] = "none"
    trend_color: Optional[str] = None
    show_comparison: bool = False
    size: Literal["small", "medium", "large"] = "medium"
    glow_effect: bool = False


@st.cache_resource
def get_metric_theme():
    """Singleton theme service for metrics"""
    from ghl_real_estate_ai.streamlit_demo.theme_service import ObsidianThemeService

    return ObsidianThemeService()


def render_obsidian_metric(
    value: Union[str, int, float],
    label: str,
    config: MetricConfig = MetricConfig(),
    comparison_value: Optional[str] = None,
    metric_icon: Optional[str] = None,
):
    """
    Render Obsidian-themed metric component with trend indicators.

    Args:
        value: Primary metric value to display
        label: Descriptive label for the metric
        config: MetricConfig with variant, trend, etc.
        comparison_value: Optional comparison text (e.g., "+12% vs last week")
        metric_icon: Font Awesome icon name (e.g., 'chart-line', 'dollar-sign')

    Example:
        ```python
        from components.primitives import render_obsidian_metric, MetricConfig

        # Success metric with upward trend
        render_obsidian_metric(
            value="$2.4M",
            label="Revenue This Quarter",
            config=MetricConfig(variant='success', trend='up', show_comparison=True),
            comparison_value="+18% vs Q3",
            metric_icon='dollar-sign'
        )

        # Premium metric with glow effect
        render_obsidian_metric(
            value=847,
            label="Hot Leads",
            config=MetricConfig(variant='premium', size='large', glow_effect=True),
            metric_icon='fire'
        )
        ```
    """
    theme = get_metric_theme()

    # Size configurations
    size_configs = {
        "small": {"value_size": "1.8rem", "label_size": "0.75rem", "padding": "1rem", "icon_size": "1rem"},
        "medium": {"value_size": "2.5rem", "label_size": "0.85rem", "padding": "1.5rem", "icon_size": "1.2rem"},
        "large": {"value_size": "3.2rem", "label_size": "0.9rem", "padding": "2rem", "icon_size": "1.5rem"},
    }

    # Variant-specific colors
    variant_colors = {
        "default": {
            "value": theme.TOKENS["colors"]["text"]["primary"],
            "background": theme.TOKENS["colors"]["background"]["card"],
            "border": "rgba(255, 255, 255, 0.05)",
            "glow": None,
        },
        "success": {
            "value": "#10B981",
            "background": "rgba(16, 185, 129, 0.05)",
            "border": "rgba(16, 185, 129, 0.2)",
            "glow": "rgba(16, 185, 129, 0.3)",
        },
        "warning": {
            "value": "#F59E0B",
            "background": "rgba(245, 158, 11, 0.05)",
            "border": "rgba(245, 158, 11, 0.2)",
            "glow": "rgba(245, 158, 11, 0.3)",
        },
        "error": {
            "value": "#EF4444",
            "background": "rgba(239, 68, 68, 0.05)",
            "border": "rgba(239, 68, 68, 0.2)",
            "glow": "rgba(239, 68, 68, 0.3)",
        },
        "premium": {
            "value": "#6366F1",
            "background": "rgba(99, 102, 241, 0.08)",
            "border": "rgba(99, 102, 241, 0.25)",
            "glow": "rgba(99, 102, 241, 0.4)",
        },
    }

    # Trend indicators
    trend_indicators = {
        "up": {"icon": "arrow-trend-up", "color": "#10B981"},
        "down": {"icon": "arrow-trend-down", "color": "#EF4444"},
        "neutral": {"icon": "minus", "color": "#8B949E"},
        "none": {"icon": None, "color": None},
    }

    size_config = size_configs[config.size]
    colors = variant_colors[config.variant]
    trend_config = trend_indicators[config.trend]

    # Build glow effect
    glow_style = ""
    if config.glow_effect and colors["glow"]:
        glow_style = f"box-shadow: 0 0 25px {colors['glow']}, {theme.TOKENS['shadow']['obsidian']};"
    else:
        glow_style = f"box-shadow: {theme.TOKENS['shadow']['obsidian']};"

    # Icon HTML
    metric_icon_html = ""
    if metric_icon:
        metric_icon_html = f"""
        <div style="margin-bottom: 0.5rem;">
            {icon(metric_icon, color=colors["value"], size=size_config["icon_size"])}
        </div>
        """

    # Trend indicator HTML
    trend_html = ""
    if config.trend != "none" and trend_config["icon"]:
        trend_color = config.trend_color or trend_config["color"]
        trend_html = f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
            {icon(trend_config["icon"], color=trend_color, size="0.9rem")}
            <span style="color: {trend_color}; font-size: 0.8rem; font-weight: 600;">
                {config.trend.upper()}
            </span>
        </div>
        """

    # Comparison value HTML
    comparison_html = ""
    if config.show_comparison and comparison_value:
        comparison_html = f"""
        <div style="
            color: {theme.TOKENS["colors"]["text"]["tertiary"]};
            font-size: 0.75rem;
            font-weight: 500;
            margin-top: 0.5rem;
            font-family: {theme.TOKENS["typography"]["family"]["mono"]};
        ">
            {comparison_value}
        </div>
        """

    # Render metric
    st.markdown(
        f"""
    <div class="obsidian-metric {config.variant}" style="
        background: {colors["background"]};
        border: 1px solid {colors["border"]};
        {glow_style}
        padding: {size_config["padding"]};
        border-radius: 12px;
        margin-bottom: 1rem;
        text-align: center;
    ">
        {metric_icon_html}
        <div style="
            color: {colors["value"]};
            font-size: {size_config["value_size"]};
            font-weight: 700;
            font-family: {theme.TOKENS["typography"]["family"]["heading"]};
            line-height: 1.2;
            margin-bottom: 0.5rem;
        ">
            {value}
        </div>
        <div style="
            color: {theme.TOKENS["colors"]["text"]["secondary"]};
            font-size: {size_config["label_size"]};
            font-weight: 600;
            font-family: {theme.TOKENS["typography"]["family"]["body"]};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        ">
            {label}
        </div>
        {trend_html}
        {comparison_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


# Export for easy imports
__all__ = ["render_obsidian_metric", "MetricConfig"]
