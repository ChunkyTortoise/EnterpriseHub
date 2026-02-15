"""
Font Awesome icon wrapper for consistent usage across dashboards.
Provides type-safe icon rendering with common icons.
"""

from typing import Literal


def icon(
    name: str, style: Literal["solid", "regular", "brands"] = "solid", color: str = "#6366F1", size: str = "1em"
) -> str:
    """
    Render Font Awesome icon as HTML.

    Args:
        name: Icon name (e.g., 'house', 'fire', 'chart-line')
        style: Icon style ('solid', 'regular', 'brands')
        color: Hex color code
        size: CSS size (e.g., '1em', '1.5rem', '20px')

    Returns:
        HTML string for icon
    """
    style_class = {"solid": "fa-solid", "regular": "fa-regular", "brands": "fa-brands"}.get(style, "fa-solid")
    return f'<i class="{style_class} fa-{name}" style="color: {color}; font-size: {size};"></i>'


ICONS = {
    "hot_lead": lambda: icon("fire", color="#EF4444"),
    "warm_lead": lambda: icon("temperature-half", color="#F59E0B"),
    "cold_lead": lambda: icon("snowflake", color="#3B82F6"),
    "property": lambda: icon("house", color="#6366F1"),
    "building": lambda: icon("building", color="#6366F1"),
    "analytics": lambda: icon("chart-line", color="#6366F1"),
    "chart": lambda: icon("chart-bar", color="#6366F1"),
    "conversation": lambda: icon("comments", color="#6366F1"),
    "phone": lambda: icon("phone", color="#10B981"),
    "email": lambda: icon("envelope", color="#6366F1"),
    "calendar": lambda: icon("calendar", color="#6366F1"),
    "clock": lambda: icon("clock", color="#8B949E"),
    "location": lambda: icon("location-dot", color="#EF4444"),
    "dollar": lambda: icon("dollar-sign", color="#10B981"),
    "money": lambda: icon("money-bill", color="#10B981"),
    "star": lambda: icon("star", color="#F59E0B"),
    "check": lambda: icon("check", color="#10B981"),
    "warning": lambda: icon("exclamation-triangle", color="#F59E0B"),
    "error": lambda: icon("circle-xmark", color="#EF4444"),
    "info": lambda: icon("circle-info", color="#3B82F6"),
    "user": lambda: icon("user", color="#6366F1"),
    "users": lambda: icon("users", color="#6366F1"),
    "settings": lambda: icon("gear", color="#8B949E"),
    "dashboard": lambda: icon("gauge-high", color="#6366F1"),
    "ai": lambda: icon("brain", color="#8B5CF6"),
    "robot": lambda: icon("robot", color="#8B5CF6"),
    "sparkles": lambda: icon("sparkles", color="#F59E0B"),
}


def get_lead_temp_icon(temperature: str) -> str:
    """Get icon for lead temperature ('hot', 'warm', 'cold')."""
    icon_map = {
        "hot": ICONS["hot_lead"](),
        "warm": ICONS["warm_lead"](),
        "cold": ICONS["cold_lead"](),
    }
    return icon_map.get(temperature.lower(), ICONS["info"]())


def get_status_icon(status: str) -> str:
    """Get icon for status ('success', 'warning', 'error', 'info')."""
    icon_map = {
        "success": ICONS["check"](),
        "warning": ICONS["warning"](),
        "error": ICONS["error"](),
        "info": ICONS["info"](),
    }
    return icon_map.get(status.lower(), ICONS["info"]())


__all__ = ["icon", "ICONS", "get_lead_temp_icon", "get_status_icon"]
