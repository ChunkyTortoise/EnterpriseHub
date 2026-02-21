"""
Obsidian-themed card primitive component.
Reusable, type-safe card with variant styles.
"""

from dataclasses import dataclass
from typing import Literal, Optional

import streamlit as st

from ..theme.service import ObsidianThemeService


@dataclass
class CardConfig:
    """Type-safe card configuration."""

    variant: Literal["default", "glass", "premium", "alert"] = "default"
    glow_color: Optional[str] = None
    show_border: bool = True
    padding: str = "1.5rem"
    border_radius: str = "12px"


def _get_theme():
    return ObsidianThemeService()


def render_obsidian_card(title: str, content: str, config: CardConfig = CardConfig(), icon: Optional[str] = None):
    """
    Render Obsidian-themed card component.

    Args:
        title: Card header text
        content: Card body content (supports HTML)
        config: CardConfig with variant, glow, etc.
        icon: Font Awesome icon name (e.g., 'fire', 'chart-line')
    """
    theme = _get_theme()

    variant_styles = {
        "default": {
            "background": theme.TOKENS["colors"]["background"]["card"],
            "border": "1px solid rgba(255, 255, 255, 0.05)",
            "box-shadow": theme.TOKENS["shadow"]["obsidian"],
        },
        "glass": {
            "background": "rgba(13, 17, 23, 0.8)",
            "backdrop-filter": "blur(20px)",
            "border": "1px solid rgba(255, 255, 255, 0.1)",
            "box-shadow": f"{theme.TOKENS['shadow']['obsidian']}, inset 0 0 20px rgba(255, 255, 255, 0.05)",
        },
        "premium": {
            "background": f"linear-gradient(135deg, {theme.TOKENS['colors']['background']['card']} 0%, rgba(99, 102, 241, 0.1) 100%)",
            "border": "1px solid rgba(99, 102, 241, 0.3)",
            "box-shadow": theme.TOKENS["shadow"]["glow-indigo"],
        },
        "alert": {
            "background": theme.TOKENS["colors"]["background"]["card"],
            "border": f"2px solid {config.glow_color or '#EF4444'}",
            "box-shadow": f"0 0 25px {config.glow_color or 'rgba(239, 68, 68, 0.3)'}",
        },
    }

    styles = variant_styles[config.variant]
    icon_html = (
        f'<i class="fa-solid fa-{icon}" style="color: {theme.TOKENS["colors"]["primary"]["indigo"]}; margin-right: 0.5rem;"></i>'
        if icon
        else ""
    )
    backdrop_filter_style = (
        f"backdrop-filter: {styles.get('backdrop-filter', '')};" if "backdrop-filter" in styles else ""
    )

    st.markdown(
        f"""
    <div class="obsidian-card {config.variant}" style="
        background: {styles["background"]};
        border: {styles["border"]};
        box-shadow: {styles["box-shadow"]};
        padding: {config.padding};
        border-radius: {config.border_radius};
        {backdrop_filter_style}
        margin-bottom: 1rem;
    ">
        <h3 style="
            color: {theme.TOKENS["colors"]["text"]["primary"]};
            font-family: {theme.TOKENS["typography"]["family"]["heading"]};
            font-weight: {theme.TOKENS["typography"]["weight"]["heading"]};
            margin-bottom: 0.75rem;
            margin-top: 0;
        ">
            {icon_html}{title}
        </h3>
        <div style="
            color: {theme.TOKENS["colors"]["text"]["secondary"]};
            font-family: {theme.TOKENS["typography"]["family"]["body"]};
        ">
            {content}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


__all__ = ["render_obsidian_card", "CardConfig"]
