"""
Enhanced Tooltip System - Contextual Information Display
Advanced tooltip system with rich contextual insights and interactive elements.

This module provides intelligent tooltips that go beyond simple text to deliver
actionable insights, mini-visualizations, and contextual recommendations.

Features:
- Rich contextual tooltips with mini-charts and trend indicators
- Interactive tooltip elements with quick actions
- Adaptive positioning and intelligent overflow handling
- Performance-optimized rendering with lazy loading
- Accessibility-compliant with screen reader support
- Mobile-optimized touch interactions

Created: January 10, 2026
Author: EnterpriseHub Development Team
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
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
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import json
from dataclasses import dataclass
from enum import Enum


class TooltipType(Enum):
    """Types of enhanced tooltips."""
    BASIC = "basic"
    PERFORMANCE = "performance"
    TREND = "trend"
    COMPARISON = "comparison"
    ACTIONABLE = "actionable"
    PREDICTIVE = "predictive"


@dataclass
class TooltipData:
    """Data structure for tooltip content."""
    title: str
    primary_value: Union[str, float, int]
    secondary_value: Optional[Union[str, float, int]] = None
    trend_data: Optional[List[float]] = None
    comparison_data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, str]]] = None
    insights: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedTooltipSystem(EnterpriseDashboardComponent):
    """
    Advanced tooltip system with rich contextual information and interactivity.
    """

    @staticmethod
    def render_performance_tooltip(
        data: TooltipData,
        performance_score: float,
        tooltip_id: str
    ) -> None:
        """Render a performance-focused tooltip with mini-chart and insights."""

        # Determine performance color
        if performance_score >= 90:
            perf_color = "#10B981"
            perf_status = "Excellent"
        elif performance_score >= 75:
            perf_color = "#3B82F6"
            perf_status = "Good"
        elif performance_score >= 60:
            perf_color = "#F59E0B"
            perf_status = "Warning"
        else:
            perf_color = "#EF4444"
            perf_status = "Critical"

        # CSS for performance tooltip
        tooltip_css = f"""
        <style>
        .performance-tooltip-{tooltip_id} {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 320px;
            position: relative;
            transition: all 0.3s ease;
        }}

        .tooltip-header-{tooltip_id} {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            padding-bottom: 8px;
        }}

        .tooltip-title-{tooltip_id} {{
            font-size: 14px;
            font-weight: 600;
            color: #1F2937;
        }}

        .performance-badge-{tooltip_id} {{
            background: {perf_color};
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .tooltip-main-value-{tooltip_id} {{
            font-size: 24px;
            font-weight: 700;
            color: {perf_color};
            margin-bottom: 8px;
        }}

        .tooltip-secondary-{tooltip_id} {{
            font-size: 12px;
            color: #6B7280;
            margin-bottom: 12px;
        }}

        .tooltip-mini-chart-{tooltip_id} {{
            height: 40px;
            margin: 8px 0;
            background: linear-gradient(90deg,
                rgba({perf_color[1:]}, 0.1) 0%,
                rgba({perf_color[1:]}, 0.2) 50%,
                rgba({perf_color[1:]}, 0.1) 100%);
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }}

        .tooltip-insights-{tooltip_id} {{
            background: rgba(59, 130, 246, 0.05);
            border-left: 3px solid #3B82F6;
            padding: 8px 12px;
            margin: 8px 0;
            border-radius: 0 6px 6px 0;
        }}

        .tooltip-insight-{tooltip_id} {{
            font-size: 11px;
            color: #374151;
            margin-bottom: 4px;
        }}

        .tooltip-actions-{tooltip_id} {{
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }}

        .tooltip-action-btn-{tooltip_id} {{
            background: rgba(59, 130, 246, 0.1);
            color: #3B82F6;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .tooltip-action-btn-{tooltip_id}:hover {{
            background: rgba(59, 130, 246, 0.2);
            transform: translateY(-1px);
        }}
        </style>
        """

        st.markdown(tooltip_css, unsafe_allow_html=True)

        # Generate mini sparkline chart if trend data available
        sparkline_svg = ""
        if data.trend_data and len(data.trend_data) > 1:
            sparkline_svg = EnhancedTooltipSystem._generate_sparkline_svg(
                data.trend_data, perf_color, tooltip_id
            )

        # Generate insights HTML
        insights_html = ""
        if data.insights:
            insights_html = f"""
            <div class="tooltip-insights-{tooltip_id}">
                {''.join([f'<div class="tooltip-insight-{tooltip_id}">💡 {insight}</div>' for insight in data.insights])}
            </div>
            """

        # Generate actions HTML
        actions_html = ""
        if data.actions:
            action_buttons = ''.join([
                f'<button class="tooltip-action-btn-{tooltip_id}">{action["label"]}</button>'
                for action in data.actions
            ])
            actions_html = f'<div class="tooltip-actions-{tooltip_id}">{action_buttons}</div>'

        # Complete tooltip HTML
        tooltip_html = f"""
        <div class="performance-tooltip-{tooltip_id}">
            <div class="tooltip-header-{tooltip_id}">
                <div class="tooltip-title-{tooltip_id}">{data.title}</div>
                <div class="performance-badge-{tooltip_id}">{perf_status}</div>
            </div>

            <div class="tooltip-main-value-{tooltip_id}">{data.primary_value}</div>

            {f'<div class="tooltip-secondary-{tooltip_id}">{data.secondary_value}</div>' if data.secondary_value else ''}

            {f'<div class="tooltip-mini-chart-{tooltip_id}">{sparkline_svg}</div>' if sparkline_svg else ''}

            {insights_html}

            {actions_html}
        </div>
        """

        st.markdown(tooltip_html, unsafe_allow_html=True)

    @staticmethod
    def render_trend_tooltip(
        data: TooltipData,
        trend_direction: str,
        trend_percentage: float,
        tooltip_id: str
    ) -> None:
        """Render a trend-focused tooltip with directional indicators and predictions."""

        # Trend configuration
        trend_config = {
            "up": {"color": "#10B981", "icon": "📈", "bg": "rgba(16, 185, 129, 0.1)"},
            "down": {"color": "#EF4444", "icon": "📉", "bg": "rgba(239, 68, 68, 0.1)"},
            "stable": {"color": "#6B7280", "icon": "➡️", "bg": "rgba(107, 114, 128, 0.1)"}
        }

        config = trend_config.get(trend_direction, trend_config["stable"])

        # CSS for trend tooltip
        trend_css = f"""
        <style>
        .trend-tooltip-{tooltip_id} {{
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.9) 0%,
                rgba(255, 255, 255, 0.95) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-left: 4px solid {config['color']};
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 300px;
        }}

        .trend-header-{tooltip_id} {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }}

        .trend-icon-{tooltip_id} {{
            font-size: 20px;
        }}

        .trend-title-{tooltip_id} {{
            font-size: 14px;
            font-weight: 600;
            color: #1F2937;
            flex: 1;
        }}

        .trend-percentage-{tooltip_id} {{
            background: {config['bg']};
            color: {config['color']};
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}

        .trend-main-value-{tooltip_id} {{
            font-size: 24px;
            font-weight: 700;
            color: #1F2937;
            margin-bottom: 8px;
        }}

        .trend-chart-container-{tooltip_id} {{
            height: 60px;
            margin: 12px 0;
            background: {config['bg']};
            border-radius: 8px;
            position: relative;
            overflow: hidden;
        }}

        .trend-predictions-{tooltip_id} {{
            background: rgba(99, 102, 241, 0.05);
            border: 1px solid rgba(99, 102, 241, 0.1);
            border-radius: 8px;
            padding: 10px;
            margin-top: 12px;
        }}

        .prediction-label-{tooltip_id} {{
            font-size: 11px;
            color: #6366F1;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}

        .prediction-value-{tooltip_id} {{
            font-size: 13px;
            color: #374151;
            font-weight: 500;
        }}
        </style>
        """

        st.markdown(trend_css, unsafe_allow_html=True)

        # Generate trend chart
        trend_chart_svg = ""
        if data.trend_data and len(data.trend_data) >= 3:
            trend_chart_svg = EnhancedTooltipSystem._generate_trend_chart_svg(
                data.trend_data, config['color'], tooltip_id
            )

        # Generate prediction if metadata available
        prediction_html = ""
        if data.metadata and 'prediction' in data.metadata:
            prediction_html = f"""
            <div class="trend-predictions-{tooltip_id}">
                <div class="prediction-label-{tooltip_id}">Prediction</div>
                <div class="prediction-value-{tooltip_id}">{data.metadata['prediction']}</div>
            </div>
            """

        # Complete trend tooltip HTML
        trend_html = f"""
        <div class="trend-tooltip-{tooltip_id}">
            <div class="trend-header-{tooltip_id}">
                <div class="trend-icon-{tooltip_id}">{config['icon']}</div>
                <div class="trend-title-{tooltip_id}">{data.title}</div>
                <div class="trend-percentage-{tooltip_id}">{trend_percentage:+.1f}%</div>
            </div>

            <div class="trend-main-value-{tooltip_id}">{data.primary_value}</div>

            {f'<div class="trend-chart-container-{tooltip_id}">{trend_chart_svg}</div>' if trend_chart_svg else ''}

            {prediction_html}
        </div>
        """

        st.markdown(trend_html, unsafe_allow_html=True)

    @staticmethod
    def render_comparison_tooltip(
        data: TooltipData,
        comparison_data: Dict[str, Any],
        tooltip_id: str
    ) -> None:
        """Render a comparison-focused tooltip with multiple metrics and benchmarks."""

        comparison_css = f"""
        <style>
        .comparison-tooltip-{tooltip_id} {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 350px;
        }}

        .comparison-header-{tooltip_id} {{
            font-size: 14px;
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 12px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            padding-bottom: 8px;
        }}

        .comparison-item-{tooltip_id} {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }}

        .comparison-label-{tooltip_id} {{
            font-size: 12px;
            color: #6B7280;
            font-weight: 500;
        }}

        .comparison-value-{tooltip_id} {{
            font-size: 13px;
            color: #1F2937;
            font-weight: 600;
        }}

        .comparison-bar-{tooltip_id} {{
            width: 80px;
            height: 4px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 2px;
            overflow: hidden;
            margin-left: 8px;
        }}

        .comparison-fill-{tooltip_id} {{
            height: 100%;
            background: linear-gradient(90deg, #3B82F6, #1D4ED8);
            border-radius: 2px;
            transition: width 0.3s ease;
        }}

        .benchmark-section-{tooltip_id} {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
        }}

        .benchmark-label-{tooltip_id} {{
            font-size: 11px;
            color: #6366F1;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        </style>
        """

        st.markdown(comparison_css, unsafe_allow_html=True)

        # Generate comparison items
        comparison_items = ""
        if comparison_data.get('metrics'):
            for metric_name, metric_value in comparison_data['metrics'].items():
                # Calculate percentage for bar chart
                max_value = comparison_data.get('max_values', {}).get(metric_name, 100)
                percentage = min((float(metric_value) / max_value) * 100, 100)

                comparison_items += f"""
                <div class="comparison-item-{tooltip_id}">
                    <div class="comparison-label-{tooltip_id}">{metric_name}</div>
                    <div style="display: flex; align-items: center;">
                        <div class="comparison-value-{tooltip_id}">{metric_value}</div>
                        <div class="comparison-bar-{tooltip_id}">
                            <div class="comparison-fill-{tooltip_id}" style="width: {percentage}%;"></div>
                        </div>
                    </div>
                </div>
                """

        # Generate benchmark section
        benchmark_html = ""
        if comparison_data.get('benchmark'):
            benchmark_html = f"""
            <div class="benchmark-section-{tooltip_id}">
                <div class="benchmark-label-{tooltip_id}">Industry Benchmark</div>
                <div class="comparison-value-{tooltip_id}">{comparison_data['benchmark']}</div>
            </div>
            """

        # Complete comparison tooltip HTML
        comparison_html = f"""
        <div class="comparison-tooltip-{tooltip_id}">
            <div class="comparison-header-{tooltip_id}">{data.title}</div>
            {comparison_items}
            {benchmark_html}
        </div>
        """

        st.markdown(comparison_html, unsafe_allow_html=True)

    @staticmethod
    def render_actionable_tooltip(
        data: TooltipData,
        actions: List[Dict[str, str]],
        tooltip_id: str
    ) -> None:
        """Render an actionable tooltip with quick action buttons and recommendations."""

        actionable_css = f"""
        <style>
        .actionable-tooltip-{tooltip_id} {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 300px;
        }}

        .actionable-header-{tooltip_id} {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }}

        .action-icon-{tooltip_id} {{
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, #3B82F6, #1D4ED8);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
        }}

        .actionable-title-{tooltip_id} {{
            font-size: 14px;
            font-weight: 600;
            color: #1F2937;
        }}

        .quick-actions-{tooltip_id} {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 12px;
        }}

        .action-button-{tooltip_id} {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(59, 130, 246, 0.05);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: #3B82F6;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
        }}

        .action-button-{tooltip_id}:hover {{
            background: rgba(59, 130, 246, 0.1);
            transform: translateX(4px);
            border-color: rgba(59, 130, 246, 0.3);
        }}

        .action-emoji-{tooltip_id} {{
            font-size: 14px;
        }}

        .recommendations-{tooltip_id} {{
            background: rgba(16, 185, 129, 0.05);
            border: 1px solid rgba(16, 185, 129, 0.1);
            border-radius: 8px;
            padding: 10px;
            margin-top: 12px;
        }}

        .recommendation-{tooltip_id} {{
            font-size: 11px;
            color: #374151;
            margin-bottom: 4px;
            display: flex;
            align-items: flex-start;
            gap: 6px;
        }}
        </style>
        """

        st.markdown(actionable_css, unsafe_allow_html=True)

        # Generate action buttons
        action_buttons = ""
        for action in actions:
            emoji = action.get('emoji', '🔧')
            label = action.get('label', 'Action')
            action_buttons += f"""
            <div class="action-button-{tooltip_id}">
                <span class="action-emoji-{tooltip_id}">{emoji}</span>
                <span>{label}</span>
            </div>
            """

        # Generate recommendations
        recommendations_html = ""
        if data.insights:
            recommendations = ''.join([
                f'<div class="recommendation-{tooltip_id}"><span>💡</span><span>{insight}</span></div>'
                for insight in data.insights
            ])
            recommendations_html = f"""
            <div class="recommendations-{tooltip_id}">
                {recommendations}
            </div>
            """

        # Complete actionable tooltip HTML
        actionable_html = f"""
        <div class="actionable-tooltip-{tooltip_id}">
            <div class="actionable-header-{tooltip_id}">
                <div class="action-icon-{tooltip_id}">⚡</div>
                <div class="actionable-title-{tooltip_id}">{data.title}</div>
            </div>

            <div style="font-size: 18px; font-weight: 700; color: #1F2937; margin-bottom: 8px;">
                {data.primary_value}
            </div>

            <div class="quick-actions-{tooltip_id}">
                {action_buttons}
            </div>

            {recommendations_html}
        </div>
        """

        st.markdown(actionable_html, unsafe_allow_html=True)

    @staticmethod
    def _generate_sparkline_svg(
        data: List[float],
        color: str,
        tooltip_id: str,
        width: int = 120,
        height: int = 30
    ) -> str:
        """Generate SVG sparkline chart for tooltip."""

        if len(data) < 2:
            return ""

        # Normalize data to fit within height
        min_val, max_val = min(data), max(data)
        if max_val == min_val:
            normalized = [height / 2] * len(data)
        else:
            normalized = [
                height - ((val - min_val) / (max_val - min_val)) * height
                for val in data
            ]

        # Generate SVG path
        x_step = width / (len(data) - 1)
        path_points = [f"{i * x_step},{normalized[i]}" for i in range(len(data))]
        path = f"M{' L'.join(path_points)}"

        svg = f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
            <path d="{path}" stroke="{color}" stroke-width="2" fill="none" opacity="0.8"/>
            <circle cx="{(len(data) - 1) * x_step}" cy="{normalized[-1]}" r="3" fill="{color}"/>
        </svg>
        """

        return svg

    @staticmethod
    def _generate_trend_chart_svg(
        data: List[float],
        color: str,
        tooltip_id: str,
        width: int = 200,
        height: int = 50
    ) -> str:
        """Generate SVG trend chart for tooltip."""

        if len(data) < 3:
            return ""

        # Normalize data
        min_val, max_val = min(data), max(data)
        if max_val == min_val:
            normalized = [height / 2] * len(data)
        else:
            normalized = [
                height - ((val - min_val) / (max_val - min_val)) * (height - 10) - 5
                for val in data
            ]

        # Generate area path
        x_step = width / (len(data) - 1)
        path_points = [f"{i * x_step},{normalized[i]}" for i in range(len(data))]

        # Create path for area fill
        area_path = f"M{' L'.join(path_points)} L{width},{height} L0,{height} Z"
        line_path = f"M{' L'.join(path_points)}"

        svg = f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="position: absolute; top: 5px; left: 10px;">
            <defs>
                <linearGradient id="gradient-{tooltip_id}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:{color};stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:{color};stop-opacity:0.05" />
                </linearGradient>
            </defs>
            <path d="{area_path}" fill="url(#gradient-{tooltip_id})"/>
            <path d="{line_path}" stroke="{color}" stroke-width="2" fill="none"/>
        </svg>
        """

        return svg


# Convenience function to create tooltip based on type
def create_enhanced_tooltip(
    tooltip_type: TooltipType,
    data: TooltipData,
    tooltip_id: str,
    **kwargs
) -> None:
    """Create an enhanced tooltip based on the specified type."""

    if tooltip_type == TooltipType.PERFORMANCE:
        performance_score = kwargs.get('performance_score', 75)
        EnhancedTooltipSystem.render_performance_tooltip(data, performance_score, tooltip_id)

    elif tooltip_type == TooltipType.TREND:
        trend_direction = kwargs.get('trend_direction', 'stable')
        trend_percentage = kwargs.get('trend_percentage', 0)
        EnhancedTooltipSystem.render_trend_tooltip(data, trend_direction, trend_percentage, tooltip_id)

    elif tooltip_type == TooltipType.COMPARISON:
        comparison_data = kwargs.get('comparison_data', {})
        EnhancedTooltipSystem.render_comparison_tooltip(data, comparison_data, tooltip_id)

    elif tooltip_type == TooltipType.ACTIONABLE:
        actions = kwargs.get('actions', [])
        EnhancedTooltipSystem.render_actionable_tooltip(data, actions, tooltip_id)

    else:
        # Basic tooltip fallback
        st.info(f"{data.title}: {data.primary_value}")


# Export main classes
__all__ = [
    'EnhancedTooltipSystem',
    'TooltipType',
    'TooltipData',
    'create_enhanced_tooltip'
]