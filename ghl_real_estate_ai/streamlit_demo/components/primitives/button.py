"""
Obsidian-themed button primitive component.
ROADMAP-071: Button variants with hover effects.

Variants:
- primary: Main action button with indigo gradient
- secondary: Secondary action button (muted)
- danger: Destructive action button with red accent
- ghost: Transparent button with border
- link: Text-only link-style button
"""

from dataclasses import dataclass, field
from typing import Optional

import streamlit as st


@dataclass
class ButtonConfig:
    """Configuration for an Obsidian-themed button."""

    variant: str = "primary"  # primary | secondary | danger | ghost | link
    size: str = "medium"  # small | medium | large
    full_width: bool = False
    disabled: bool = False
    icon: Optional[str] = None  # Prefix icon text (emoji or unicode)


# Variant-specific style definitions
_VARIANT_STYLES = {
    "primary": {
        "bg": "linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)",
        "color": "#FFFFFF",
        "border": "none",
        "hover_bg": "linear-gradient(135deg, #4338CA 0%, #6D28D9 100%)",
        "shadow": "0 4px 14px rgba(79, 70, 229, 0.4)",
    },
    "secondary": {
        "bg": "#F3F4F6",
        "color": "#374151",
        "border": "1px solid #D1D5DB",
        "hover_bg": "#E5E7EB",
        "shadow": "0 2px 6px rgba(0, 0, 0, 0.06)",
    },
    "danger": {
        "bg": "linear-gradient(135deg, #DC2626 0%, #EF4444 100%)",
        "color": "#FFFFFF",
        "border": "none",
        "hover_bg": "linear-gradient(135deg, #B91C1C 0%, #DC2626 100%)",
        "shadow": "0 4px 14px rgba(220, 38, 38, 0.4)",
    },
    "ghost": {
        "bg": "transparent",
        "color": "#4F46E5",
        "border": "1px solid #4F46E5",
        "hover_bg": "rgba(79, 70, 229, 0.08)",
        "shadow": "none",
    },
    "link": {
        "bg": "transparent",
        "color": "#4F46E5",
        "border": "none",
        "hover_bg": "transparent",
        "shadow": "none",
    },
}

_SIZE_STYLES = {
    "small": {"padding": "0.375rem 0.75rem", "font_size": "0.8rem", "radius": "6px"},
    "medium": {"padding": "0.625rem 1.25rem", "font_size": "0.9rem", "radius": "8px"},
    "large": {"padding": "0.875rem 1.75rem", "font_size": "1rem", "radius": "10px"},
}


def render_obsidian_button(
    label: str,
    key: str,
    config: Optional[ButtonConfig] = None,
    on_click=None,
) -> bool:
    """Render an Obsidian-themed button and return True if clicked.

    Uses Streamlit's native ``st.button`` under the hood so click state is
    handled by the framework. Custom styling is injected via a preceding
    ``st.markdown`` block that targets the button's key-based CSS class.

    Args:
        label: Button text.
        key: Unique Streamlit widget key.
        config: Optional ``ButtonConfig`` for variant, size, etc.
        on_click: Optional callback passed to ``st.button``.

    Returns:
        True when the button is clicked during the current run.
    """
    if config is None:
        config = ButtonConfig()

    variant = _VARIANT_STYLES.get(config.variant, _VARIANT_STYLES["primary"])
    size = _SIZE_STYLES.get(config.size, _SIZE_STYLES["medium"])

    display_label = f"{config.icon} {label}" if config.icon else label

    # Inject scoped CSS for this button's container
    width_css = "width: 100%;" if config.full_width else ""
    opacity_css = "opacity: 0.5; pointer-events: none;" if config.disabled else ""
    underline = "text-decoration: underline;" if config.variant == "link" else ""

    st.markdown(
        f"""<style>
        div[data-testid="stButton"][key="{key}"] button {{
            background: {variant["bg"]};
            color: {variant["color"]};
            border: {variant["border"]};
            padding: {size["padding"]};
            font-size: {size["font_size"]};
            border-radius: {size["radius"]};
            box-shadow: {variant["shadow"]};
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            {width_css}
            {opacity_css}
            {underline}
        }}
        div[data-testid="stButton"][key="{key}"] button:hover {{
            background: {variant["hover_bg"]};
            transform: translateY(-1px);
        }}
        </style>""",
        unsafe_allow_html=True,
    )

    clicked = st.button(
        display_label,
        key=key,
        disabled=config.disabled,
        on_click=on_click,
        use_container_width=config.full_width,
    )
    return clicked
