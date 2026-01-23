"""
Obsidian-themed badge primitive component.
Replaces 80+ inline badge implementations with reusable, type-safe component.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Literal, Optional
from .icon import icon


@dataclass
class BadgeConfig:
    """
    Type-safe badge configuration (AI-readable).

    Attributes:
        variant: Badge style variant for different contexts
        size: Badge size variant
        glow_effect: Whether to apply glow effect
        pulse_animation: Whether to add pulsing animation
        uppercase: Whether to transform text to uppercase
        show_icon: Whether to display an icon with the badge
    """
    variant: Literal[
        'hot', 'warm', 'cold',  # Lead temperature
        'success', 'warning', 'error', 'info',  # Status
        'premium', 'elite', 'standard',  # Tier
        'active', 'inactive', 'pending',  # Activity
        'priority', 'urgent', 'normal'  # Priority
    ] = 'info'
    size: Literal['xs', 'sm', 'md', 'lg'] = 'sm'
    glow_effect: bool = False
    pulse_animation: bool = False
    uppercase: bool = True
    show_icon: bool = False


@st.cache_resource
def get_badge_theme():
    """Singleton theme service for badges"""
    from ghl_real_estate_ai.streamlit_demo.theme_service import ObsidianThemeService
    return ObsidianThemeService()


def render_obsidian_badge(
    text: str,
    config: BadgeConfig = BadgeConfig(),
    custom_icon: Optional[str] = None
):
    """
    Render Obsidian-themed badge component with status variants.

    Args:
        text: Badge text content
        config: BadgeConfig with variant, size, effects, etc.
        custom_icon: Optional custom Font Awesome icon name

    Example:
        ```python
        from components.primitives import render_obsidian_badge, BadgeConfig

        # Hot lead with glow and pulse
        render_obsidian_badge(
            "HOT QUALIFIED",
            config=BadgeConfig(variant='hot', glow_effect=True, pulse_animation=True, show_icon=True)
        )

        # Premium tier badge
        render_obsidian_badge(
            "Elite Member",
            config=BadgeConfig(variant='premium', size='md', show_icon=True),
            custom_icon='crown'
        )

        # Status badge
        render_obsidian_badge(
            "Processing",
            config=BadgeConfig(variant='warning', size='sm', pulse_animation=True)
        )
        ```
    """
    theme = get_badge_theme()

    # Size configurations
    size_configs = {
        'xs': {
            'padding': '4px 8px',
            'font_size': '0.65rem',
            'border_radius': '4px',
            'icon_size': '0.7rem'
        },
        'sm': {
            'padding': '6px 12px',
            'font_size': '0.75rem',
            'border_radius': '6px',
            'icon_size': '0.8rem'
        },
        'md': {
            'padding': '8px 16px',
            'font_size': '0.85rem',
            'border_radius': '8px',
            'icon_size': '0.9rem'
        },
        'lg': {
            'padding': '10px 20px',
            'font_size': '0.9rem',
            'border_radius': '10px',
            'icon_size': '1rem'
        }
    }

    # Variant configurations with colors, icons, and semantics
    variant_configs = {
        # Lead Temperature
        'hot': {
            'background': 'rgba(239, 68, 68, 0.1)',
            'color': '#EF4444',
            'border': 'rgba(239, 68, 68, 0.3)',
            'glow': 'rgba(239, 68, 68, 0.4)',
            'icon': 'fire'
        },
        'warm': {
            'background': 'rgba(245, 158, 11, 0.1)',
            'color': '#F59E0B',
            'border': 'rgba(245, 158, 11, 0.3)',
            'glow': 'rgba(245, 158, 11, 0.4)',
            'icon': 'temperature-half'
        },
        'cold': {
            'background': 'rgba(59, 130, 246, 0.1)',
            'color': '#3B82F6',
            'border': 'rgba(59, 130, 246, 0.3)',
            'glow': 'rgba(59, 130, 246, 0.4)',
            'icon': 'snowflake'
        },
        
        # Status
        'success': {
            'background': 'rgba(16, 185, 129, 0.1)',
            'color': '#10B981',
            'border': 'rgba(16, 185, 129, 0.3)',
            'glow': 'rgba(16, 185, 129, 0.4)',
            'icon': 'check-circle'
        },
        'warning': {
            'background': 'rgba(245, 158, 11, 0.1)',
            'color': '#F59E0B',
            'border': 'rgba(245, 158, 11, 0.3)',
            'glow': 'rgba(245, 158, 11, 0.4)',
            'icon': 'exclamation-triangle'
        },
        'error': {
            'background': 'rgba(239, 68, 68, 0.1)',
            'color': '#EF4444',
            'border': 'rgba(239, 68, 68, 0.3)',
            'glow': 'rgba(239, 68, 68, 0.4)',
            'icon': 'exclamation-circle'
        },
        'info': {
            'background': 'rgba(59, 130, 246, 0.1)',
            'color': '#3B82F6',
            'border': 'rgba(59, 130, 246, 0.3)',
            'glow': 'rgba(59, 130, 246, 0.4)',
            'icon': 'info-circle'
        },
        
        # Tier
        'premium': {
            'background': 'rgba(99, 102, 241, 0.1)',
            'color': '#6366F1',
            'border': 'rgba(99, 102, 241, 0.3)',
            'glow': 'rgba(99, 102, 241, 0.4)',
            'icon': 'star'
        },
        'elite': {
            'background': 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%)',
            'color': '#A855F7',
            'border': 'rgba(168, 85, 247, 0.4)',
            'glow': 'rgba(168, 85, 247, 0.5)',
            'icon': 'crown'
        },
        'standard': {
            'background': theme.TOKENS['colors']['background']['card'],
            'color': theme.TOKENS['colors']['text']['secondary'],
            'border': 'rgba(255, 255, 255, 0.1)',
            'glow': None,
            'icon': 'tag'
        },
        
        # Activity
        'active': {
            'background': 'rgba(16, 185, 129, 0.1)',
            'color': '#10B981',
            'border': 'rgba(16, 185, 129, 0.3)',
            'glow': 'rgba(16, 185, 129, 0.4)',
            'icon': 'circle-dot'
        },
        'inactive': {
            'background': 'rgba(107, 114, 128, 0.1)',
            'color': '#6B7280',
            'border': 'rgba(107, 114, 128, 0.3)',
            'glow': None,
            'icon': 'circle'
        },
        'pending': {
            'background': 'rgba(245, 158, 11, 0.1)',
            'color': '#F59E0B',
            'border': 'rgba(245, 158, 11, 0.3)',
            'glow': 'rgba(245, 158, 11, 0.4)',
            'icon': 'clock'
        },
        
        # Priority
        'priority': {
            'background': 'rgba(239, 68, 68, 0.1)',
            'color': '#EF4444',
            'border': 'rgba(239, 68, 68, 0.3)',
            'glow': 'rgba(239, 68, 68, 0.4)',
            'icon': 'flag'
        },
        'urgent': {
            'background': 'rgba(220, 38, 127, 0.1)',
            'color': '#DC2626',
            'border': 'rgba(220, 38, 127, 0.4)',
            'glow': 'rgba(220, 38, 127, 0.5)',
            'icon': 'bolt'
        },
        'normal': {
            'background': theme.TOKENS['colors']['background']['card'],
            'color': theme.TOKENS['colors']['text']['secondary'],
            'border': 'rgba(255, 255, 255, 0.1)',
            'glow': None,
            'icon': 'minus'
        }
    }

    size_config = size_configs[config.size]
    variant_config = variant_configs[config.variant]

    # Build animations
    animation_styles = ""
    if config.pulse_animation:
        animation_styles += """
        animation: obsidianPulse 2s infinite;
        @keyframes obsidianPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        """

    # Build glow effect
    glow_style = ""
    if config.glow_effect and variant_config['glow']:
        glow_style = f"box-shadow: 0 0 15px {variant_config['glow']}, 0 0 5px {variant_config['glow']};"

    # Determine icon to use
    badge_icon = custom_icon or (variant_config['icon'] if config.show_icon else None)
    
    # Icon HTML
    icon_html = ""
    if badge_icon:
        icon_html = f"""
        <span style="margin-right: 0.4rem; display: inline-flex; align-items: center;">
            {icon(badge_icon, color=variant_config['color'], size=size_config['icon_size'])}
        </span>
        """

    # Text transformation
    display_text = text.upper() if config.uppercase else text

    # Render badge
    st.markdown(f"""
    <span class="obsidian-badge {config.variant}" style="
        background: {variant_config['background']};
        color: {variant_config['color']};
        border: 1px solid {variant_config['border']};
        padding: {size_config['padding']};
        border-radius: {size_config['border_radius']};
        font-size: {size_config['font_size']};
        font-weight: 700;
        font-family: {theme.TOKENS['typography']['family']['mono']};
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        {glow_style}
        {animation_styles}
        margin: 0 0.25rem 0.25rem 0;
    ">
        {icon_html}{display_text}
    </span>
    """, unsafe_allow_html=True)


# Convenience functions for common use cases
def lead_temperature_badge(temperature: Literal['hot', 'warm', 'cold'], text: str = None):
    """Convenience function for lead temperature badges."""
    display_text = text or f"{temperature.upper()} LEAD"
    config = BadgeConfig(
        variant=temperature,
        glow_effect=(temperature == 'hot'),
        pulse_animation=(temperature == 'hot'),
        show_icon=True
    )
    render_obsidian_badge(display_text, config)


def status_badge(status: Literal['success', 'warning', 'error', 'info'], text: str):
    """Convenience function for status badges."""
    config = BadgeConfig(
        variant=status,
        show_icon=True,
        glow_effect=(status in ['error', 'warning'])
    )
    render_obsidian_badge(text, config)


# Export for easy imports
__all__ = ['render_obsidian_badge', 'BadgeConfig', 'lead_temperature_badge', 'status_badge']
