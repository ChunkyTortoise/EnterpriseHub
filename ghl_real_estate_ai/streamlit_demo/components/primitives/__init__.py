"""
Primitive Component Library for EnterpriseHub
Obsidian-themed reusable UI components.

Usage:
    from components.primitives import render_obsidian_card, CardConfig, icon, ICONS

    # Render a card
    render_obsidian_card(
        title="Hot Leads",
        content="<p>15 leads need attention</p>",
        config=CardConfig(variant='alert', glow_color='#EF4444'),
        icon='fire'
    )

    # Use icons
    st.markdown(f"{icon('fire', color='#EF4444')} Hot Lead", unsafe_allow_html=True)
    st.markdown(ICONS['hot_lead'](), unsafe_allow_html=True)
"""

from .card import render_obsidian_card, CardConfig
from .icon import icon, ICONS, get_lead_temp_icon, get_status_icon
from .metric import render_obsidian_metric, MetricConfig
from .badge import render_obsidian_badge, BadgeConfig, lead_temperature_badge, status_badge

__all__ = [
    # Card primitive
    'render_obsidian_card',
    'CardConfig',
    # Metric primitive
    'render_obsidian_metric',
    'MetricConfig',
    # Badge primitive
    'render_obsidian_badge',
    'BadgeConfig',
    'lead_temperature_badge',
    'status_badge',
    # Icon system
    'icon',
    'ICONS',
    'get_lead_temp_icon',
    'get_status_icon',
]
