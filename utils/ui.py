"""
User Interface & Experience (UI/UX) Module.

This module serves as the centralized styling and component library for the Enterprise Hub.
It injects custom CSS to override Streamlit's default look with a professional,
enterprise-grade design system (Fintech/SaaS Aesthetic).
"""

import base64
import os
from typing import Optional

import streamlit as st

# --- DESIGN SYSTEM CONSTANTS ---
# Light theme (WCAG AAA compliant - all ratios >= 7:1)
# EDITORIAL FINTECH DESIGN SYSTEM (Steel & Slate)
# Based on Stripe/Linear/Institutional Finance aesthetics

LIGHT_THEME = {
    "primary": "#0F172A",  # Slate 900 (Institutional)
    "primary_dark": "#020617",  # Slate 950
    "primary_light": "#F1F5F9",  # Slate 100
    "accent": "#059669",  # Emerald 600 (Tactical Signal)
    "secondary": "#64748B",  # Slate 500
    "background": "#FFFFFF",  # Clean White
    "surface": "#F8FAFC",  # Slate 50
    "text_main": "#0F172A",  # Slate 900
    "text_light": "#475569",  # Slate 600
    "success": "#059669",  # Emerald 600
    "warning": "#D97706",  # Amber 600
    "danger": "#DC2626",  # Red 600
    "border": "#E2E8F0",  # Slate 200
    "font_family": ("'Inter Variable', 'Inter', -apple-system, system-ui, sans-serif"),
    "header_font": "'Space Grotesk', sans-serif",
}

DARK_THEME = {
    "primary": "#F8FAFC",  # Slate 50
    "primary_dark": "#F1F5F9",
    "primary_light": "#1E293B",  # Slate 800
    "accent": "#10B981",  # Emerald 500
    "secondary": "#94A3B8",
    "background": "#020617",  # Slate 950
    "surface": "#0F172A",  # Slate 900
    "text_main": "#F8FAFC",
    "text_light": "#94A3B8",
    "success": "#10B981",
    "warning": "#FBBF24",
    "danger": "#F87171",
    "border": "#1E293B",
    "font_family": "'Inter', -apple-system, system-ui, sans-serif",
    "header_font": "'Space Grotesk', sans-serif",
    "button_text": "#FFFFFF",
}

OCEAN_THEME = {
    "primary": "#083344",  # Cyan 950
    "primary_dark": "#164E63",
    "primary_light": "#ECFEFF",
    "accent": "#06B6D4",
    "secondary": "#0891B2",
    "background": "#F0F9FF",
    "surface": "#FFFFFF",
    "text_main": "#083344",
    "text_light": "#155E75",
    "success": "#0D9488",
    "warning": "#CA8A04",
    "danger": "#BE123C",
    "border": "#CFFAFE",
    "font_family": "'Inter', -apple-system, system-ui, sans-serif",
    "header_font": "'Space Grotesk', sans-serif",
    "button_text": "#FFFFFF",
}

SUNSET_THEME = {
    "primary": "#2E1065",  # Violet 950
    "primary_dark": "#4C1D95",
    "primary_light": "#F5F3FF",
    "accent": "#D946EF",
    "secondary": "#7E22CE",
    "background": "#FFF7ED",
    "surface": "#FFFFFF",
    "text_main": "#2E1065",
    "text_light": "#5B21B6",
    "success": "#166534",
    "warning": "#92400E",
    "danger": "#991B1B",
    "border": "#FED7AA",
    "font_family": "'Inter', -apple-system, system-ui, sans-serif",
    "header_font": "'Space Grotesk', sans-serif",
    "button_text": "#FFFFFF",
}

# Add button_text to light theme (white text for dark buttons)
LIGHT_THEME["button_text"] = "#FFFFFF"

# Default to light theme (will be overridden by setup_interface)
THEME = LIGHT_THEME


def get_base64_image(file_path: str) -> str:
    """Read a local file and return its base64 representation."""
    try:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        ext = file_path.split(".")[-1].lower()
        mime_type = f"image/{ext}"
        if ext == "svg":
            mime_type = "image/svg+xml"
        return f"data:{mime_type};base64,{encoded}"
    except Exception:
        # Silently fail and return empty string - will fallback to emoji
        return ""


def _generate_css(theme: dict) -> str:
    """Generate CSS with the specified theme colors."""
    return f"""
<style>
    /* IMPORT GOOGLE FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:slnt,wght@-10..0,100..900&family=Space+Grotesk:wght@300..700&display=swap');

    :root {{
        --glass-bg: {theme['surface']}CC;
        --glass-border: {theme['border']}40;
    }}

    /* GLOBAL RESET & TYPOGRAPHY */
    html, body, [class*="css"] {{
        font-family: {theme['font_family']};
        color: {theme['text_main']};
        background-color: {theme['background']};
    }}

    /* MAIN CONTAINER BACKGROUND - Visual 5.0 Animated Mesh */
    .stApp {{
        background-color: {theme['background']};
        background-image:
            radial-gradient(at 0% 0%, {theme['primary_light']}80 0,
                            transparent 50%),
            radial-gradient(at 100% 0%, {theme.get('accent', '#059669')}15 0,
                            transparent 50%),
            radial-gradient(at 100% 100%, {theme['primary_light']}80 0,
                            transparent 50%),
            radial-gradient(at 0% 100%,
                            {theme.get('secondary', '#64748B')}15 0,
                            transparent 50%);
        background-attachment: fixed;
        background-size: 200% 200%;
        animation: mesh 20s ease infinite;
    }}

    @keyframes mesh {{
        0% {{ background-position: 0% 0%; }}
        50% {{ background-position: 100% 100%; }}
        100% {{ background-position: 0% 0%; }}
    }}

    /* SIDEBAR STYLING - Saturated Glassmorphism */
    section[data-testid="stSidebar"] {{
        background-color: {theme['surface']}A6; /* High transparency */
        border-right: 1px solid {theme['border']}40;
        backdrop-filter: blur(25px) saturate(210%);
        -webkit-backdrop-filter: blur(25px) saturate(210%);
        box-shadow: 10px 0 15px -3px rgba(0, 0, 0, 0.05);
    }}

    section[data-testid="stSidebar"] h1 {{
        color: {theme['primary']};
        font-weight: 800;
        font-size: 1.25rem;
        letter-spacing: -0.04em;
        text-transform: uppercase;
        margin-bottom: 2rem;
    }}

    /* NAVIGATION RADIO BUTTONS */
    .stRadio > label {{
        color: {theme['text_main']};
        font-weight: 500;
    }}

    /* METRIC CARDS - Advanced Depth */
    .metric-card {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 0px;
        padding: 32px;
        transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        height: 100%;
        display: flex;
        flex-direction: column;
        border-top: 4px solid {theme['border']};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}

    .metric-card:hover {{
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        transform: translateY(-8px);
        border-top-color: {theme['accent']};
        background-color: {theme['background']};
    }}

    /* HEADERS - Fluid Typography */
    h1 {{
        font-size: clamp(2.5rem, 8vw, 4.5rem);
        font-weight: 900;
        letter-spacing: -0.06em;
        margin-bottom: 2rem;
        color: {theme['primary']};
        font-family: {theme['header_font']};
        line-height: 0.9;
        animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    h2 {{
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 4px solid {theme.get('accent', theme['primary'])};
        padding-left: 1rem;
        animation: fadeIn 1s ease-out;
    }}

    /* ANIMATIONS */
    @keyframes slideUp {{
        from {{ opacity: 0; transform: translateY(30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    .stMarkdown, .element-container {{
        animation: fadeIn 0.8s ease-out forwards;
    }}

    h3 {{
        font-size: 1.25rem;
        color: {theme['text_main']};
        margin-bottom: 0.5rem;
    }}

    /* ACTIVE NAVIGATION INDICATOR */
    div[data-testid="stSidebarNav"] li[data-selected="true"] {{
        background-color: {theme['primary_light']};
        border-left: 4px solid {theme['accent']};
    }}

    .stButton button {{
        background-color: {theme['primary']};
        color: {theme.get('button_text', 'white')};
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.25rem;
        border: 1px solid transparent;
        transition: all 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }}

    .stButton button:hover {{
        background-color: {theme['primary_dark']};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transform: translateY(-1px);
    }}

    .stButton button:active {{
        transform: translateY(0);
    }}

    .stButton button:focus {{
        outline: 2px solid {theme['primary']};
        outline-offset: 2px;
        box-shadow: 0 0 0 3px {theme['primary_light']};
    }}

    /* NATIVE METRIC STYLING */
    div[data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: {theme['primary']};
        font-feature-settings: "tnum";
        font-variant-numeric: tabular-nums;
    }}

    div[data-testid="stMetricLabel"] {{
        font-size: 0.875rem;
        color: {theme['text_light']};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ALERTS/MESSAGES */
    .stAlert {{
        border-radius: 8px;
        border: 1px solid transparent;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }}

    /* LINKS */
    a {{
        color: {theme['primary']};
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }}
    a:hover {{
        color: {theme['primary_dark']};
        text-decoration: underline;
    }}
    a:focus {{
        outline: 2px solid {theme['primary']};
        outline-offset: 2px;
        border-radius: 2px;
    }}

    /* DATAFRAMES */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {theme['border']};
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}

    /* HERO SECTION */
    .hero-container {{
        background: linear-gradient(135deg, {theme['primary_light']} 0%, {theme['primary_light']} 100%);
        border-radius: 16px;
        padding: 4rem 2rem;
        text-align: center;
        margin-bottom: 3rem;
        border: 1px solid {theme['border']};
    }}

    .hero-title {{
        font-size: 3.5rem;
        font-weight: 800;
        color: {theme['primary_dark']};
        margin-bottom: 1rem;
        line-height: 1.2;
    }}

    .hero-subtitle {{
        font-size: 1.25rem;
        color: {theme['secondary']};
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.6;
    }}

    /* FOOTER */
    .footer {{
        margin-top: 5rem;
        border-top: 1px solid {theme['border']};
        padding-top: 2rem;
        text-align: center;
        color: {theme['secondary']};
        font-size: 0.875rem;
    }}

    /* RESPONSIVE DESIGN - TABLET */
    @media (max-width: 1024px) {{
        .hero-title {{
            font-size: 2.5rem;
        }}

        .hero-subtitle {{
            font-size: 1.1rem;
        }}

        .hero-container {{
            padding: 3rem 1.5rem;
        }}

        h1 {{
            font-size: 2rem;
        }}

        h2 {{
            font-size: 1.5rem;
        }}
    }}

    /* RESPONSIVE DESIGN - MOBILE */
    @media (max-width: 768px) {{
        .hero-title {{
            font-size: 1.75rem;
            line-height: 1.3;
        }}

        .hero-subtitle {{
            font-size: 1rem;
            padding: 0 1rem;
        }}

        .hero-container {{
            padding: 2rem 1rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            padding: 16px;
            margin-bottom: 1rem;
        }}

        h1 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }}

        h2 {{
            font-size: 1.25rem;
            margin-top: 1.5rem;
        }}

        h3 {{
            font-size: 1.1rem;
        }}

        div[data-testid="stMetricValue"] {{
            font-size: 1.5rem;
        }}

        div[data-testid="stMetricLabel"] {{
            font-size: 0.75rem;
        }}

        .footer {{
            margin-top: 3rem;
            font-size: 0.75rem;
        }}

        /* Improve button sizing on mobile */
        .stButton button {{
            padding: 0.625rem 1rem;
            font-size: 0.9rem;
        }}
    }}

    /* RESPONSIVE DESIGN - SMALL MOBILE */
    @media (max-width: 480px) {{
        .hero-title {{
            font-size: 1.5rem;
        }}

        .hero-subtitle {{
            font-size: 0.9rem;
        }}

        .hero-container {{
            padding: 1.5rem 0.75rem;
        }}

        .metric-card {{
            padding: 12px;
        }}

        /* Stack columns on very small screens */
        section[data-testid="stSidebar"] {{
            width: 100% !important;
        }}
    }}

    /* LOADING SKELETON ANIMATIONS */
    @keyframes shimmer {{
        0% {{
            background-position: -468px 0;
        }}
        100% {{
            background-position: 468px 0;
        }}
    }}

    .skeleton {{
        background: linear-gradient(
            to right,
            {theme['border']} 0%,
            {theme['surface']} 20%,
            {theme['border']} 40%,
            {theme['border']} 100%
        );
        background-size: 468px 100%;
        animation: shimmer 1.2s ease-in-out infinite;
        border-radius: 8px;
    }}

    .skeleton-card {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}

    .skeleton-line {{
        height: 16px;
        margin-bottom: 12px;
        border-radius: 4px;
    }}

    .skeleton-title {{
        height: 24px;
        width: 60%;
        margin-bottom: 16px;
        border-radius: 4px;
    }}

    .skeleton-circle {{
        width: 60px;
        height: 60px;
        border-radius: 50%;
        margin-bottom: 12px;
    }}

    /* TOAST NOTIFICATIONS */
    .toast-container {{
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    }}

    @keyframes slideIn {{
        from {{
            transform: translateX(100%);
            opacity: 0;
        }}
        to {{
            transform: translateX(0);
            opacity: 1;
        }}
    }}

    @keyframes slideOut {{
        from {{
            transform: translateX(0);
            opacity: 1;
        }}
        to {{
            transform: translateX(100%);
            opacity: 0;
        }}
    }}

    .toast {{
        background-color: {theme['surface']};
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        display: flex;
        align-items: center;
        gap: 12px;
        border-left: 4px solid {theme['primary']};
        animation: slideIn 0.3s ease-out;
    }}

    .toast.toast-success {{
        border-left-color: {theme['success']};
    }}

    .toast.toast-error {{
        border-left-color: {theme['danger']};
    }}

    .toast.toast-warning {{
        border-left-color: {theme['warning']};
    }}

    .toast.toast-info {{
        border-left-color: {theme['primary']};
    }}

    .toast-icon {{
        font-size: 1.5rem;
        line-height: 1;
        flex-shrink: 0;
    }}

    .toast-message {{
        color: {theme['text_main']};
        font-size: 0.95rem;
        font-weight: 500;
        flex-grow: 1;
    }}

    /* MICRO-ANIMATIONS */
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes fadeInStagger {{
        0% {{
            opacity: 0;
            transform: translateY(20px);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes bounce {{
        0%, 100% {{
            transform: translateY(0);
        }}
        50% {{
            transform: translateY(-5px);
        }}
    }}

    @keyframes pulse {{
        0%, 100% {{
            opacity: 1;
        }}
        50% {{
            opacity: 0.8;
        }}
    }}

    /* Apply fade-in to cards */
    .metric-card {{
        animation: fadeIn 0.4s ease-out;
    }}

    /* Stagger animation for multiple cards */
    .metric-card:nth-child(1) {{
        animation-delay: 0.1s;
        animation-fill-mode: both;
    }}

    .metric-card:nth-child(2) {{
        animation-delay: 0.2s;
        animation-fill-mode: both;
    }}

    .metric-card:nth-child(3) {{
        animation-delay: 0.3s;
        animation-fill-mode: both;
    }}

    .metric-card:nth-child(4) {{
        animation-delay: 0.4s;
        animation-fill-mode: both;
    }}

    /* Bounce animation for CTA buttons */
    .cta-button {{
        display: inline-block;
        animation: bounce 2s ease-in-out infinite;
    }}

    .cta-button:hover {{
        animation: none;
    }}

    /* Smooth transitions for all interactive elements */
    button, a, input, select, textarea, .metric-card {{
        transition: all 0.2s ease-in-out;
    }}

    /* Hover lift effect */
    .hover-lift:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.15);
    }}

    /* Fade in content */
    .fade-in {{
        animation: fadeIn 0.6s ease-out;
    }}

    /* Reduced motion support for accessibility */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }}
    }}

</style>
"""


def setup_interface(theme_mode: str = "light") -> None:
    """
    Initializes the UI interface with the Design System.

    Args:
        theme_mode: "light", "dark", "ocean", or "sunset" theme mode

    Call this at the start of the application.
    """
    global THEME

    # Select theme based on mode
    theme_map = {
        "light": LIGHT_THEME,
        "dark": DARK_THEME,
        "ocean": OCEAN_THEME,
        "sunset": SUNSET_THEME,
    }
    THEME = theme_map.get(theme_mode.lower(), LIGHT_THEME)

    # Generate and inject CSS with selected theme
    css = _generate_css(THEME)
    st.markdown(css, unsafe_allow_html=True)


def card_metric(
    label: str, value: str, delta: Optional[str] = None, help: Optional[str] = None
) -> None:
    """
    Displays a metric in a native Streamlit container but styled by global CSS.
    """
    st.metric(label=label, value=value, delta=delta, help=help)


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Displays a styled section header.
    """
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(
            f"<p style='color: {THEME['text_light']}; margin-top: -15px; margin-bottom: 30px; font-size: 1.1em;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )


def status_badge(status: str) -> str:
    """
    Returns a styled HTML badge for status indication.
    Statuses: 'active', 'pending', 'new', 'hero'
    """
    colors = {
        "active": ("#DCFCE7", "#166534"),  # Green-100 to Green-800
        "pending": ("#F1F5F9", "#475569"),  # Slate-100 to Slate-600
        "new": ("#DBEAFE", "#1E40AF"),  # Blue-100 to Blue-800
        "hero": ("#FEF3C7", "#92400E"),  # Amber-100 to Amber-800
    }

    bg, text = colors.get(status.lower(), colors["pending"])

    return f"""
    <span style='
        background-color: {bg};
        color: {text};
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 8px;
    '>
        {status}
    </span>
    """


def hero_section(title: str, subtitle: str, background_image: Optional[str] = None) -> None:
    """
    Renders a centered hero section with optional editorial background.
    """
    bg_style = f"background-color: {THEME['primary_light']};"
    overlay = ""

    if background_image:
        b64 = get_base64_image(background_image)
        if b64:
            bg_style = f"background-image: url('{b64}'); background-size: cover; background-position: center;"
            overlay = f"background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(8px); padding: 3rem; border-radius: 12px; border: 1px solid {THEME['border']};"

    html = (
        f'<section class="hero-container" role="banner" '
        f'aria-label="Hero section" style="{bg_style} border: none; '
        f'padding: 6rem 2rem;">'
        f'<div style="{overlay} max-width: 800px; margin: 0 auto;">'
        f'<h1 class="hero-title" style="color: {THEME["primary"]}; '
        f'margin-bottom: 0.5rem;">{title}</h1>'
        f'<p class="hero-subtitle" style="color: {THEME["text_light"]}; '
        f'font-weight: 500;">{subtitle}</p></div></section>'
    )
    st.markdown(html, unsafe_allow_html=True)


def feature_card(
    icon: str, title: str, description: str, status: str = "active", icon_path: Optional[str] = None
) -> None:
    """
    Renders a feature card using the Editorial style.
    """
    badge = status_badge(status)
    icon_display = icon

    if icon_path:
        b64 = get_base64_image(icon_path)
        if b64:
            icon_display = (
                f"<img src='{b64}' style='width: 48px; height: 48px; object-fit: contain;'>"
            )

    html = (
        f'<article class="metric-card" role="article" '
        f'aria-label="Feature: {title}" style="border-radius: 0; '
        f'border-top: 4px solid {THEME["border"]}; padding: 2rem;">'
        f'<div style="display: flex; justify-content: space-between; '
        f'align-items: start; margin-bottom: 1.5rem;">'
        f'<div style="font-size: 2.5rem; width: 48px; height: 48px; '
        f'display: flex; align-items: center; justify-content: center;" '
        f'role="img" aria-label="{title} icon">{icon_display}</div>'
        f'{badge}</div><h3 style="margin-top: 0; color: {THEME["text_main"]}; '
        f'font-size: 1.25rem; font-family: {THEME["header_font"]}; '
        f'letter-spacing: -0.02em;">{title}</h3>'
        f'<p style="color: {THEME["text_light"]}; font-size: 0.95rem; '
        f'line-height: 1.6; margin-bottom: 0; flex-grow: 1;">'
        f'{description}</p></article>'
    )
    st.markdown(html, unsafe_allow_html=True)


def use_case_card(icon: str, title: str, description: str) -> None:
    """
    Renders a use case card for the Overview page.
    """
    html = (
        f'<div class="use-case-card" role="article" '
        f'aria-label="Use case: {title}" style="background-color: '
        f'{THEME["surface"]}; border-left: 4px solid {THEME["accent"]}; '
        f'padding: 1.5rem; border-radius: 4px; border: 1px solid '
        f'{THEME["border"]}; border-left-width: 4px;">'
        f'<div style="display: flex; gap: 1rem; align-items: start;">'
        f'<div style="font-size: 1.5rem;" role="img" '
        f'aria-label="{title} icon">{icon}</div><div>'
        f'<strong style="display: block; margin-bottom: 0.5rem; '
        f'color: {THEME["primary"]}; font-family: {THEME["header_font"]};">'
        f'{title}</strong><div style="font-size: 0.9rem; '
        f'color: {THEME["text_light"]}; line-height: 1.6;">'
        f'{description}</div></div></div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def comparison_table() -> None:
    """
    Renders a comparison table showing EnterpriseHub vs alternatives.
    """
    html = f"""
    <section aria-label="Platform comparison table">
        <div style="overflow-x: auto; border-radius: 8px; border: 1px solid {THEME['border']};">
            <table role="table" aria-label="Comparison of EnterpriseHub with alternative solutions" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: {THEME['background']}; border-bottom: 2px solid {THEME['border']};">
                        <th scope="col" style="padding: 16px; text-align: left; font-weight: 600;">Capability</th>
                        <th scope="col" style="padding: 16px; text-align: center; font-weight: 600; color: {THEME['primary']};">EnterpriseHub</th>
                        <th scope="col" style="padding: 16px; text-align: center; font-weight: 600;">Excel Spreadsheets</th>
                        <th scope="col" style="padding: 16px; text-align: center; font-weight: 600;">Bloomberg Terminal</th>
                        <th scope="col" style="padding: 16px; text-align: center; font-weight: 600;">Agency Dashboards</th>
                    </tr>
                </thead>
                <tbody>
                <tr style="border-bottom: 1px solid {THEME['border']};">
                    <td style="padding: 14px;"><strong>Cost</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">$0 (Open Source)</td>
                    <td style="padding: 14px; text-align: center;">$0-200/year</td>
                    <td style="padding: 14px; text-align: center;">$24,000/year</td>
                    <td style="padding: 14px; text-align: center;">$200-500/month</td>
                </tr>
                <tr style="border-bottom: 1px solid {THEME['border']}; background-color: {THEME['background']};">
                    <td style="padding: 14px;"><strong>Setup Time</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">&lt; 5 minutes</td>
                    <td style="padding: 14px; text-align: center;">2-4 hours</td>
                    <td style="padding: 14px; text-align: center;">1-2 weeks</td>
                    <td style="padding: 14px; text-align: center;">2-6 weeks</td>
                </tr>
                <tr style="border-bottom: 1px solid {THEME['border']};">
                    <td style="padding: 14px;"><strong>Technical Analysis</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">✓ RSI, MACD, MA</td>
                    <td style="padding: 14px; text-align: center;">Manual formulas</td>
                    <td style="padding: 14px; text-align: center;">✓ Advanced</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                </tr>
                <tr style="border-bottom: 1px solid {THEME['border']}; background-color: {THEME['background']};">
                    <td style="padding: 14px;"><strong>AI-Powered Insights</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">✓ Claude 3.5 Sonnet</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                    <td style="padding: 14px; text-align: center;">Limited</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                </tr>
                <tr style="border-bottom: 1px solid {THEME['border']};">
                    <td style="padding: 14px;"><strong>Scenario Modeling</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">✓ 100 scenarios/heatmap</td>
                    <td style="padding: 14px; text-align: center;">Manual copy-paste</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                </tr>
                <tr style="border-bottom: 1px solid {THEME['border']}; background-color: {THEME['background']};">
                    <td style="padding: 14px;"><strong>Attribution Modeling</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">✓ 5 models</td>
                    <td style="padding: 14px; text-align: center;">Manual calculation</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                    <td style="padding: 14px; text-align: center;">Limited</td>
                </tr>
                <tr style="border-bottom: 1px solid {THEME['border']};">
                    <td style="padding: 14px;"><strong>Automated Testing</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">✓ 220+ tests</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                    <td style="padding: 14px; text-align: center;">Proprietary</td>
                    <td style="padding: 14px; text-align: center;">✗</td>
                </tr>
                <tr style="background-color: {THEME['background']};">
                    <td style="padding: 14px;"><strong>Ownership</strong></td>
                    <td style="padding: 14px; text-align: center; color: {THEME['success']}; font-weight: 600;">✓ Full source code</td>
                    <td style="padding: 14px; text-align: center;">You own files</td>
                    <td style="padding: 14px; text-align: center;">✗ Subscription only</td>
                    <td style="padding: 14px; text-align: center;">✗ Subscription only</td>
                </tr>
                </tbody>
            </table>
        </div>
    </section>
    """
    st.markdown(html, unsafe_allow_html=True)


def skeleton_loader(skeleton_type: str = "card", count: int = 1) -> None:
    """
    Renders animated loading placeholders with shimmer effect.

    This function creates skeleton screens that provide visual feedback during content loading,
    improving perceived performance and user experience. The shimmer animation creates a
    left-to-right wave effect that indicates the content is being loaded.

    Args:
        skeleton_type: Type of skeleton to render. Options:
            - "card": Full card skeleton with icon, title, and text lines
            - "text": Simple text lines skeleton
            - "metric": Metric card skeleton with icon and value placeholder
            - "table": Table row skeleton
        count: Number of skeleton instances to render (default: 1)

    Example:
        Basic usage in a module while data loads:
        ```python
        import streamlit as st
        from utils.ui import skeleton_loader

        if st.session_state.get("loading", False):
            skeleton_loader("card", count=3)
        else:
            # Render actual content
            for item in data:
                render_card(item)
        ```

        Different skeleton types:
        ```python
        # Show card skeletons while fetching data
        with st.spinner("Loading data..."):
            skeleton_loader("card", count=4)
            data = fetch_data()

        # Show text skeletons for loading text content
        skeleton_loader("text", count=5)

        # Show metric skeletons for dashboard metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            skeleton_loader("metric")
        with col2:
            skeleton_loader("metric")
        with col3:
            skeleton_loader("metric")
        ```

    Note:
        - Skeletons automatically adapt to the current theme (light/dark mode)
        - Animation respects user's motion preferences (prefers-reduced-motion)
        - Best used temporarily while actual content loads
        - Should be replaced with real content once data is available
    """
    skeletons = []

    for i in range(count):
        if skeleton_type == "card":
            skeleton_html = """
            <div class="skeleton-card" role="status" aria-label="Loading content" aria-live="polite">
                <div class="skeleton skeleton-circle" aria-hidden="true"></div>
                <div class="skeleton skeleton-title" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 100%;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 90%;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 75%;" aria-hidden="true"></div>
                <span class="sr-only">Loading...</span>
            </div>
            """
        elif skeleton_type == "text":
            skeleton_html = """
            <div role="status" aria-label="Loading text content" aria-live="polite">
                <div class="skeleton skeleton-line" style="width: 100%; margin-bottom: 8px;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 95%; margin-bottom: 8px;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 85%; margin-bottom: 8px;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 90%; margin-bottom: 8px;" aria-hidden="true"></div>
                <span class="sr-only">Loading...</span>
            </div>
            """
        elif skeleton_type == "metric":
            skeleton_html = """
            <div class="skeleton-card" role="status" aria-label="Loading metric" aria-live="polite">
                <div class="skeleton skeleton-line" style="width: 50%; height: 14px; margin-bottom: 12px;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 80%; height: 32px;" aria-hidden="true"></div>
                <span class="sr-only">Loading metric...</span>
            </div>
            """
        elif skeleton_type == "table":
            skeleton_html = """
            <div role="status" aria-label="Loading table row" aria-live="polite">
                <div style="display: flex; gap: 16px; margin-bottom: 12px;">
                    <div class="skeleton skeleton-line" style="width: 25%; height: 20px;" aria-hidden="true"></div>
                    <div class="skeleton skeleton-line" style="width: 25%; height: 20px;" aria-hidden="true"></div>
                    <div class="skeleton skeleton-line" style="width: 25%; height: 20px;" aria-hidden="true"></div>
                    <div class="skeleton skeleton-line" style="width: 25%; height: 20px;" aria-hidden="true"></div>
                </div>
                <span class="sr-only">Loading table row...</span>
            </div>
            """
        else:
            # Default to card type
            skeleton_html = """
            <div class="skeleton-card" role="status" aria-label="Loading content" aria-live="polite">
                <div class="skeleton skeleton-circle" aria-hidden="true"></div>
                <div class="skeleton skeleton-title" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 100%;" aria-hidden="true"></div>
                <div class="skeleton skeleton-line" style="width: 90%;" aria-hidden="true"></div>
                <span class="sr-only">Loading...</span>
            </div>
            """

        skeletons.append(skeleton_html)

    st.markdown("\n".join(skeletons), unsafe_allow_html=True)


def toast(message: str, toast_type: str = "success", duration: int = 3000) -> None:
    """
    Displays a toast notification with auto-dismiss functionality.

    Toast notifications provide non-intrusive feedback to users about the outcome of their
    actions. They appear in the top-right corner and automatically dismiss after a specified
    duration. This implementation uses Streamlit's native st.toast when available (Streamlit 1.27+),
    falling back to custom HTML/JavaScript for older versions.

    Args:
        message: The notification message to display
        toast_type: Type of notification. Options:
            - "success": Green notification for successful operations
            - "error": Red notification for errors or failures
            - "warning": Yellow/amber notification for warnings
            - "info": Blue notification for informational messages
        duration: Time in milliseconds before auto-dismiss (default: 3000ms = 3 seconds)

    Example:
        Basic usage in modules:
        ```python
        import streamlit as st
        from utils.ui import toast

        # Success notification
        if data_saved:
            toast("Data saved successfully!", "success")

        # Error notification
        try:
            process_data()
        except Exception as e:
            toast(f"Error processing data: {str(e)}", "error", duration=5000)

        # Warning notification
        if len(selected_items) > 100:
            toast("Processing more than 100 items may take longer", "warning")

        # Info notification
        toast("Tip: Use Ctrl+Enter to submit", "info")
        ```

        In financial analysis workflows:
        ```python
        # Market Pulse module
        if stock_data_loaded:
            toast(f"Loaded {len(df)} days of data for {ticker}", "success")

        # Margin Hunter module
        if optimization_complete:
            toast(f"Found optimal strategy: {best_strategy}", "success", duration=5000)

        # Data Detective module
        if missing_values_found:
            toast(f"Warning: {missing_count} missing values detected", "warning")
        ```

    Note:
        - Toast appears in top-right corner (configurable via CSS)
        - Multiple toasts stack vertically
        - Automatically dismisses after duration
        - Uses native Streamlit toast when available (Streamlit >= 1.27)
        - Falls back to custom implementation for compatibility
        - Respects theme colors for consistency
    """
    # Try to use native Streamlit toast (available in Streamlit 1.27+)
    if hasattr(st, "toast"):
        icon_map = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}
        icon = icon_map.get(toast_type, "ℹ")
        st.toast(f"{icon} {message}", icon=icon)
    else:
        # Fallback to custom HTML/JavaScript implementation
        icon_map = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}
        icon = icon_map.get(toast_type, "ℹ")

        toast_html = f"""
        <div class="toast-container" id="toast-{toast_type}-container">
            <div class="toast toast-{toast_type}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-icon" aria-hidden="true">{icon}</div>
                <div class="toast-message">{message}</div>
            </div>
        </div>
        <script>
            // Auto-dismiss toast after duration
            setTimeout(function() {{
                var toast = document.getElementById('toast-{toast_type}-container');
                if (toast) {{
                    toast.style.animation = 'slideOut 0.3s ease-out';
                    setTimeout(function() {{
                        toast.style.display = 'none';
                    }}, 300);
                }}
            }}, {duration});
        </script>
        """
        st.markdown(toast_html, unsafe_allow_html=True)


def animated_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    icon: Optional[str] = None,
    color: str = "primary",
) -> None:
    """
    Renders an animated metric card with count-up effect and gradient background.

    Args:
        label: Metric label (e.g., "Total Revenue")
        value: Metric value (e.g., "$1,234,567")
        delta: Optional change indicator (e.g., "+12.5%")
        icon: Optional emoji/icon to display
        color: Color scheme - "primary", "success", "warning", "danger"
    """
    # Use opacified versions of theme colors for backgrounds to ensure theme consistency
    color_map = {
        "primary": (THEME["primary"], THEME["primary_light"]),
        "success": (THEME["success"], f"{THEME['success']}15"),
        "warning": (THEME["warning"], f"{THEME['warning']}15"),
        "danger": (THEME["danger"], f"{THEME['danger']}15"),
    }

    main_color, bg_color = color_map.get(color, color_map["primary"])

    html = f"""
    <div class="metric-card hover-lift" style="background: linear-gradient(135deg, {bg_color} 0%, {THEME['surface']} 100%); border-left: 4px solid {main_color};">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <div style="font-size: 0.75rem; color: {THEME['text_light']}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                {label}
            </div>
            {f'<div style="font-size: 1.75rem;" role="img" aria-label="{label} icon">{icon}</div>' if icon else ''}
        </div>
        <div style="font-size: 2.25rem; font-weight: 700; color: {main_color}; margin-bottom: 4px; font-feature-settings: 'tnum'; font-variant-numeric: tabular-nums;">
            {value}
        </div>
        {f'<div style="font-size: 0.875rem; color: {THEME["success"] if "+" in delta else THEME["danger"]}; font-weight: 600;">{delta}</div>' if delta else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def glassmorphic_card(
    title: str,
    content: str,
    icon: Optional[str] = None,
    cta_text: Optional[str] = None,
    cta_url: Optional[str] = None,
) -> None:
    """
    Renders a glassmorphic card with backdrop blur effect (modern 2025 design trend).

    Args:
        title: Card title
        content: Card content (HTML allowed)
        icon: Optional emoji/icon
        cta_text: Optional call-to-action button text
        cta_url: Optional CTA link URL
    """
    html = f"""
    <div style="
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        height: 100%;
    " class="hover-lift">
        {f'<div style="font-size: 2.5rem; margin-bottom: 12px;" role="img" aria-label="{title} icon">{icon}</div>' if icon else ''}
        <h3 style="color: {THEME['text_main']}; margin-bottom: 12px; font-size: 1.5rem;">{title}</h3>
        <p style="color: {THEME['text_light']}; line-height: 1.6; margin-bottom: 16px;">
            {content}
        </p>
        {f'''<a href="{cta_url}" style="
            display: inline-block;
            background-color: {THEME['primary']};
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s;
        " onmouseover="this.style.backgroundColor='{THEME['primary_dark']}'; this.style.transform='translateY(-2px)';"
           onmouseout="this.style.backgroundColor='{THEME['primary']}'; this.style.transform='translateY(0)';">
            {cta_text} →
        </a>''' if cta_text and cta_url else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def progress_bar(
    label: str,
    value: int,
    max_value: int = 100,
    color: str = "primary",
    show_percentage: bool = True,
) -> None:
    """
    Renders an animated progress bar with smooth transitions.

    Args:
        label: Progress bar label
        value: Current value
        max_value: Maximum value (default: 100)
        color: Color scheme - "primary", "success", "warning", "danger"
        show_percentage: Whether to show percentage text
    """
    percentage = min(100, int((value / max_value) * 100))

    color_map = {
        "primary": THEME["primary"],
        "success": THEME["success"],
        "warning": THEME["warning"],
        "danger": THEME["danger"],
    }

    bar_color = color_map.get(color, THEME["primary"])

    html = f"""
    <div style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.875rem; font-weight: 600; color: {THEME['text_main']};">{label}</span>
            {f'<span style="font-size: 0.875rem; font-weight: 700; color: {bar_color};">{percentage}%</span>' if show_percentage else ''}
        </div>
        <div style="
            width: 100%;
            height: 12px;
            background-color: {THEME['background']};
            border-radius: 9999px;
            overflow: hidden;
            border: 1px solid {THEME['border']};
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {bar_color}, {THEME['primary_light']});
                border-radius: 9999px;
                transition: width 1s ease-out;
                animation: shimmer 2s ease-in-out infinite;
            "></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_plotly_template() -> dict:
    """
    Returns a Plotly template aligned with the current editorial theme.
    """
    return {
        "layout": {
            "font": {"family": THEME["font_family"], "color": THEME["text_main"]},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"t": 40, "b": 40, "l": 40, "r": 40},
            "xaxis": {
                "gridcolor": "rgba(0,0,0,0)",
                "linecolor": THEME["border"],
                "zerolinecolor": "rgba(0,0,0,0)",
                "showgrid": False,
                "showline": True,
                "mirror": False,
            },
            "yaxis": {
                "gridcolor": THEME["border"],
                "linecolor": THEME["border"],
                "zerolinecolor": "rgba(0,0,0,0)",
                "showgrid": True,
                "showline": True,
                "mirror": False,
                "gridwidth": 0.5,
                "griddash": "dot",
            },
            "colorway": [
                THEME["primary"],
                THEME.get("accent", "#059669"),
                "#3B82F6",
                "#8B5CF6",
                "#EC4899",
                "#F59E0B",
            ],
        }
    }


def spacer(px: int = 20) -> None:
    """Adds vertical space between elements."""
    st.markdown(f"<div style='height: {px}px'></div>", unsafe_allow_html=True)


def login_modal() -> bool:
    """
    Renders a production-grade login modal.
    Returns True if authenticated, False otherwise.
    (Mocked for demonstration).
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Custom CSS for the login gateway
    login_css = f"""
    <style>
        .login-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: {THEME['background']};
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .login-card {{
            background: {THEME['surface']};
            padding: 48px;
            border-radius: 4px;
            width: 100%;
            max-width: 450px;
            border: 1px solid {THEME['border']};
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }}
    </style>
    """
    st.markdown(login_css, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        st.markdown(
            f"<h1 style='font-size: 2rem; margin-bottom: 8px;'>ENTERPRISE<span style='color: {THEME['accent']}'>HUB</span></h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color: #64748B; margin-bottom: 32px;'>Secure Production Gateway v5.0</p>",
            unsafe_allow_html=True,
        )

        username = st.text_input("Username or Email", placeholder="cayman@enterprise.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🚀 Access Console", use_container_width=True, type="primary"):
                if username and password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        with col2:
            st.button("Request Access", use_container_width=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    return False


def footer() -> None:
    """Renders the standard footer."""
    footer_html = """
    <hr>
    <footer role="contentinfo">
        <div class="footer">
            <p>© 2025 Enterprise Hub | Built with Streamlit & Python for
               Professional Excellence</p>
            <nav aria-label="Footer Navigation">
                <a href="https://github.com/ChunkyTortoise/enterprise-hub"
                   target="_blank" rel="noopener noreferrer">View Source</a> |
                <a href="https://linkedin.com/in/caymanroden"
                   target="_blank" rel="noopener noreferrer">
                   Contact Developer</a>
            </nav>
        </div>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
