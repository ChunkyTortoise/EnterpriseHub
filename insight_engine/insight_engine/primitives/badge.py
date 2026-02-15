"""
Obsidian-themed badge primitive component.
Reusable, type-safe badges with status variants.
"""

from dataclasses import dataclass
from typing import Literal, Optional

import streamlit as st

from ..theme.service import ObsidianThemeService
from .icon import icon


@dataclass
class BadgeConfig:
    """Type-safe badge configuration."""
    variant: Literal[
        "hot", "warm", "cold",
        "success", "warning", "error", "info",
        "premium", "elite", "standard",
        "active", "inactive", "pending",
        "priority", "urgent", "normal",
    ] = "info"
    size: Literal["xs", "sm", "md", "lg"] = "sm"
    glow_effect: bool = False
    pulse_animation: bool = False
    uppercase: bool = True
    show_icon: bool = False


def _get_theme():
    return ObsidianThemeService()


def render_obsidian_badge(text: str, config: BadgeConfig = BadgeConfig(), custom_icon: Optional[str] = None):
    """
    Render Obsidian-themed badge component.

    Args:
        text: Badge text content
        config: BadgeConfig with variant, size, effects
        custom_icon: Optional custom Font Awesome icon name
    """
    theme = _get_theme()

    size_configs = {
        "xs": {"padding": "4px 8px", "font_size": "0.65rem", "border_radius": "4px", "icon_size": "0.7rem"},
        "sm": {"padding": "6px 12px", "font_size": "0.75rem", "border_radius": "6px", "icon_size": "0.8rem"},
        "md": {"padding": "8px 16px", "font_size": "0.85rem", "border_radius": "8px", "icon_size": "0.9rem"},
        "lg": {"padding": "10px 20px", "font_size": "0.9rem", "border_radius": "10px", "icon_size": "1rem"},
    }

    variant_configs = {
        "hot": {"background": "rgba(239, 68, 68, 0.1)", "color": "#EF4444", "border": "rgba(239, 68, 68, 0.3)", "glow": "rgba(239, 68, 68, 0.4)", "icon": "fire"},
        "warm": {"background": "rgba(245, 158, 11, 0.1)", "color": "#F59E0B", "border": "rgba(245, 158, 11, 0.3)", "glow": "rgba(245, 158, 11, 0.4)", "icon": "temperature-half"},
        "cold": {"background": "rgba(59, 130, 246, 0.1)", "color": "#3B82F6", "border": "rgba(59, 130, 246, 0.3)", "glow": "rgba(59, 130, 246, 0.4)", "icon": "snowflake"},
        "success": {"background": "rgba(16, 185, 129, 0.1)", "color": "#10B981", "border": "rgba(16, 185, 129, 0.3)", "glow": "rgba(16, 185, 129, 0.4)", "icon": "check-circle"},
        "warning": {"background": "rgba(245, 158, 11, 0.1)", "color": "#F59E0B", "border": "rgba(245, 158, 11, 0.3)", "glow": "rgba(245, 158, 11, 0.4)", "icon": "exclamation-triangle"},
        "error": {"background": "rgba(239, 68, 68, 0.1)", "color": "#EF4444", "border": "rgba(239, 68, 68, 0.3)", "glow": "rgba(239, 68, 68, 0.4)", "icon": "exclamation-circle"},
        "info": {"background": "rgba(59, 130, 246, 0.1)", "color": "#3B82F6", "border": "rgba(59, 130, 246, 0.3)", "glow": "rgba(59, 130, 246, 0.4)", "icon": "info-circle"},
        "premium": {"background": "rgba(99, 102, 241, 0.1)", "color": "#6366F1", "border": "rgba(99, 102, 241, 0.3)", "glow": "rgba(99, 102, 241, 0.4)", "icon": "star"},
        "elite": {"background": "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%)", "color": "#A855F7", "border": "rgba(168, 85, 247, 0.4)", "glow": "rgba(168, 85, 247, 0.5)", "icon": "crown"},
        "standard": {"background": theme.TOKENS["colors"]["background"]["card"], "color": theme.TOKENS["colors"]["text"]["secondary"], "border": "rgba(255, 255, 255, 0.1)", "glow": None, "icon": "tag"},
        "active": {"background": "rgba(16, 185, 129, 0.1)", "color": "#10B981", "border": "rgba(16, 185, 129, 0.3)", "glow": "rgba(16, 185, 129, 0.4)", "icon": "circle-dot"},
        "inactive": {"background": "rgba(107, 114, 128, 0.1)", "color": "#6B7280", "border": "rgba(107, 114, 128, 0.3)", "glow": None, "icon": "circle"},
        "pending": {"background": "rgba(245, 158, 11, 0.1)", "color": "#F59E0B", "border": "rgba(245, 158, 11, 0.3)", "glow": "rgba(245, 158, 11, 0.4)", "icon": "clock"},
        "priority": {"background": "rgba(239, 68, 68, 0.1)", "color": "#EF4444", "border": "rgba(239, 68, 68, 0.3)", "glow": "rgba(239, 68, 68, 0.4)", "icon": "flag"},
        "urgent": {"background": "rgba(220, 38, 127, 0.1)", "color": "#DC2626", "border": "rgba(220, 38, 127, 0.4)", "glow": "rgba(220, 38, 127, 0.5)", "icon": "bolt"},
        "normal": {"background": theme.TOKENS["colors"]["background"]["card"], "color": theme.TOKENS["colors"]["text"]["secondary"], "border": "rgba(255, 255, 255, 0.1)", "glow": None, "icon": "minus"},
    }

    size_config = size_configs[config.size]
    variant_config = variant_configs[config.variant]

    glow_style = f"box-shadow: 0 0 15px {variant_config['glow']}, 0 0 5px {variant_config['glow']};" if config.glow_effect and variant_config["glow"] else ""

    badge_icon = custom_icon or (variant_config["icon"] if config.show_icon else None)
    icon_html = f'<span style="margin-right: 0.4rem; display: inline-flex; align-items: center;">{icon(badge_icon, color=variant_config["color"], size=size_config["icon_size"])}</span>' if badge_icon else ""

    display_text = text.upper() if config.uppercase else text

    st.markdown(f"""
    <span class="obsidian-badge {config.variant}" style="
        background: {variant_config["background"]};
        color: {variant_config["color"]};
        border: 1px solid {variant_config["border"]};
        padding: {size_config["padding"]};
        border-radius: {size_config["border_radius"]};
        font-size: {size_config["font_size"]};
        font-weight: 700;
        font-family: {theme.TOKENS["typography"]["family"]["mono"]};
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        {glow_style}
        margin: 0 0.25rem 0.25rem 0;
    ">
        {icon_html}{display_text}
    </span>
    """, unsafe_allow_html=True)


def lead_temperature_badge(temperature: Literal["hot", "warm", "cold"], text: str = None):
    """Convenience function for lead temperature badges."""
    display_text = text or f"{temperature.upper()} LEAD"
    config = BadgeConfig(variant=temperature, glow_effect=(temperature == "hot"), pulse_animation=(temperature == "hot"), show_icon=True)
    render_obsidian_badge(display_text, config)


def status_badge(status: Literal["success", "warning", "error", "info"], text: str):
    """Convenience function for status badges."""
    config = BadgeConfig(variant=status, show_icon=True, glow_effect=(status in ["error", "warning"]))
    render_obsidian_badge(text, config)


__all__ = ["render_obsidian_badge", "BadgeConfig", "lead_temperature_badge", "status_badge"]
