"""
Font Awesome icon wrapper for consistent usage across EnterpriseHub.
Provides type-safe icon rendering with common real estate icons.
"""

from typing import Literal


def icon(
    name: str,
    style: Literal['solid', 'regular', 'brands'] = 'solid',
    color: str = '#6366F1',
    size: str = '1em'
) -> str:
    """
    Render Font Awesome icon.

    Args:
        name: Icon name (e.g., 'house', 'fire', 'chart-line')
        style: Icon style ('solid', 'regular', 'brands')
        color: Hex color code
        size: CSS size (e.g., '1em', '1.5rem', '20px')

    Returns:
        HTML string for icon

    Example:
        ```python
        import streamlit as st
        from components.primitives import icon

        # Inline icon
        st.markdown(f"{icon('fire', color='#EF4444')} Hot Leads", unsafe_allow_html=True)

        # Large icon
        st.markdown(icon('house', size='2rem'), unsafe_allow_html=True)

        # Regular style
        st.markdown(icon('star', style='regular'), unsafe_allow_html=True)

        # Brand icon
        st.markdown(icon('github', style='brands'), unsafe_allow_html=True)
        ```

    Icon Reference:
        Find icons at: https://fontawesome.com/icons
        Common real estate icons:
        - house, building, home
        - fire (hot leads), temperature-half (warm), snowflake (cold)
        - chart-line, chart-bar, analytics
        - comments, phone, envelope
        - calendar, clock, location-dot
        - dollar-sign, money-bill, coins
        - star, check, exclamation-triangle
    """
    style_class = {
        'solid': 'fa-solid',
        'regular': 'fa-regular',
        'brands': 'fa-brands'
    }.get(style, 'fa-solid')

    return f'<i class="{style_class} fa-{name}" style="color: {color}; font-size: {size};"></i>'


# Common icons for real estate platform
# Each returns a pre-configured icon HTML string
ICONS = {
    'hot_lead': lambda: icon('fire', color='#EF4444'),
    'warm_lead': lambda: icon('temperature-half', color='#F59E0B'),
    'cold_lead': lambda: icon('snowflake', color='#3B82F6'),
    'property': lambda: icon('house', color='#6366F1'),
    'building': lambda: icon('building', color='#6366F1'),
    'analytics': lambda: icon('chart-line', color='#6366F1'),
    'chart': lambda: icon('chart-bar', color='#6366F1'),
    'conversation': lambda: icon('comments', color='#6366F1'),
    'phone': lambda: icon('phone', color='#10B981'),
    'email': lambda: icon('envelope', color='#6366F1'),
    'calendar': lambda: icon('calendar', color='#6366F1'),
    'clock': lambda: icon('clock', color='#8B949E'),
    'location': lambda: icon('location-dot', color='#EF4444'),
    'dollar': lambda: icon('dollar-sign', color='#10B981'),
    'money': lambda: icon('money-bill', color='#10B981'),
    'star': lambda: icon('star', color='#F59E0B'),
    'star_outline': lambda: icon('star', style='regular', color='#F59E0B'),
    'check': lambda: icon('check', color='#10B981'),
    'circle_check': lambda: icon('circle-check', color='#10B981'),
    'warning': lambda: icon('exclamation-triangle', color='#F59E0B'),
    'error': lambda: icon('circle-xmark', color='#EF4444'),
    'info': lambda: icon('circle-info', color='#3B82F6'),
    'user': lambda: icon('user', color='#6366F1'),
    'users': lambda: icon('users', color='#6366F1'),
    'settings': lambda: icon('gear', color='#8B949E'),
    'dashboard': lambda: icon('gauge-high', color='#6366F1'),
    'search': lambda: icon('magnifying-glass', color='#6366F1'),
    'filter': lambda: icon('filter', color='#6366F1'),
    'download': lambda: icon('download', color='#6366F1'),
    'upload': lambda: icon('upload', color='#6366F1'),
    'ai': lambda: icon('brain', color='#8B5CF6'),
    'robot': lambda: icon('robot', color='#8B5CF6'),
    'sparkles': lambda: icon('sparkles', color='#F59E0B'),
}


def get_lead_temp_icon(temperature: str) -> str:
    """
    Get icon for lead temperature.

    Args:
        temperature: Lead temperature ('hot', 'warm', 'cold')

    Returns:
        HTML icon string

    Example:
        ```python
        temp_icon = get_lead_temp_icon('hot')
        st.markdown(f"{temp_icon} Priority Lead", unsafe_allow_html=True)
        ```
    """
    icon_map = {
        'hot': ICONS['hot_lead'](),
        'warm': ICONS['warm_lead'](),
        'cold': ICONS['cold_lead'](),
    }
    return icon_map.get(temperature.lower(), ICONS['info']())


def get_status_icon(status: str) -> str:
    """
    Get icon for status.

    Args:
        status: Status type ('success', 'warning', 'error', 'info')

    Returns:
        HTML icon string

    Example:
        ```python
        status_icon = get_status_icon('success')
        st.markdown(f"{status_icon} Operation completed", unsafe_allow_html=True)
        ```
    """
    icon_map = {
        'success': ICONS['check'](),
        'warning': ICONS['warning'](),
        'error': ICONS['error'](),
        'info': ICONS['info'](),
    }
    return icon_map.get(status.lower(), ICONS['info']())


__all__ = ['icon', 'ICONS', 'get_lead_temp_icon', 'get_status_icon']
