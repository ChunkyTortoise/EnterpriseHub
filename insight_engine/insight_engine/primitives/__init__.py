"""
Primitive Component Library for Insight Engine.
Obsidian-themed reusable UI components for Streamlit dashboards.

Usage:
    from insight_engine.primitives import render_obsidian_card, CardConfig, icon, ICONS
"""

from .badge import BadgeConfig, lead_temperature_badge, render_obsidian_badge, status_badge
from .card import CardConfig, render_obsidian_card
from .icon import ICONS, get_lead_temp_icon, get_status_icon, icon
from .metric import MetricConfig, render_obsidian_metric

__all__ = [
    "render_obsidian_card",
    "CardConfig",
    "render_obsidian_metric",
    "MetricConfig",
    "render_obsidian_badge",
    "BadgeConfig",
    "lead_temperature_badge",
    "status_badge",
    "icon",
    "ICONS",
    "get_lead_temp_icon",
    "get_status_icon",
]
