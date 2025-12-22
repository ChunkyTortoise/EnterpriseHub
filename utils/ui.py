"""
User Interface & Experience (UI/UX) Module.

This module serves as the centralized styling and component library for the Enterprise Hub.
It injects custom CSS to override Streamlit's default look with a professional,
enterprise-grade design system (Fintech/SaaS Aesthetic).
"""

from typing import Optional

import streamlit as st

# --- DESIGN SYSTEM CONSTANTS ---
# Light theme (WCAG AAA compliant - all ratios >= 7:1)
LIGHT_THEME = {
    "primary": "#4338CA",  # Indigo 700 (darker for AAA compliance)
    "primary_dark": "#3730A3",  # Indigo 800
    "primary_light": "#E0E7FF",  # Indigo 100
    "secondary": "#64748B",  # Slate 500
    "background": "#F8FAFC",  # Slate 50
    "surface": "#FFFFFF",  # White
    "text_main": "#0F172A",  # Slate 900
    "text_light": "#475569",  # Slate 600
    "success": "#065F46",  # Emerald 800 (darker for AAA: 7.1:1)
    "warning": "#B45309",  # Amber 700 (darker for AAA compliance)
    "danger": "#991B1B",  # Red 800 (darker for AAA: 8.1:1)
    "border": "#E2E8F0",  # Slate 200
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
}

# Dark theme (WCAG AAA compliant)
DARK_THEME = {
    "primary": "#A5B4FC",  # Indigo 300 (lighter for AAA: 8.5:1)
    "primary_dark": "#818CF8",  # Indigo 400
    "primary_light": "#312E81",  # Indigo 900
    "secondary": "#94A3B8",  # Slate 400
    "background": "#0F172A",  # Slate 900
    "surface": "#1E293B",  # Slate 800
    "text_main": "#F8FAFC",  # Slate 50
    "text_light": "#CBD5E1",  # Slate 300
    "success": "#6EE7B7",  # Emerald 300 (AAA compliant)
    "warning": "#FCD34D",  # Amber 300 (AAA compliant)
    "danger": "#FCA5A5",  # Red 300 (lighter for AAA: 8.9:1)
    "border": "#334155",  # Slate 700
    "button_text": "#0F172A",  # Dark text for light buttons in dark mode
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
}

# Add button_text to light theme (white text for dark buttons)
LIGHT_THEME["button_text"] = "#FFFFFF"

# Default to light theme (will be overridden by setup_interface)
THEME = LIGHT_THEME


def _generate_css(theme: dict) -> str:
    """Generate CSS with the specified theme colors."""
    return f"""
<style>
    /* IMPORT INTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* GLOBAL RESET & TYPOGRAPHY */
    html, body, [class*="css"] {{
        font-family: {theme['font_family']};
        color: {theme['text_main']};
        background-color: {theme['background']};
    }}

    /* MAIN CONTAINER BACKGROUND */
    .stApp {{
        background-color: {theme['background']};
    }}

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {{
        background-color: {theme['surface']};
        border-right: 1px solid {theme['border']};
        box-shadow: 1px 0 0 0 {theme['border']};
    }}

    section[data-testid="stSidebar"] h1 {{
        color: {theme['primary']};
        font-weight: 700;
        font-size: 1.5rem;
        letter-spacing: -0.025em;
    }}

    /* NAVIGATION RADIO BUTTONS */
    .stRadio > label {{
        color: {theme['text_main']};
        font-weight: 500;
    }}

    /* METRIC CARDS */
    .metric-card {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
        height: 100%;
        display: flex;
        flex-direction: column;
    }}

    .metric-card:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
        border-color: {theme['primary_light']};
    }}

    /* HEADERS */
    h1, h2, h3 {{
        color: {theme['text_main']};
        font-weight: 700;
        letter-spacing: -0.025em;
    }}

    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        color: {theme['primary_dark']};  /* Fallback for non-webkit browsers */
        background: linear-gradient(45deg, {theme['primary']}, {theme['primary_dark']});
        background: -webkit-linear-gradient(45deg, {theme['primary']}, {theme['primary_dark']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    h2 {{
        font-size: 1.75rem;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid {theme['border']};
        padding-bottom: 0.5rem;
    }}

    h3 {{
        font-size: 1.25rem;
        color: {theme['text_main']};
        margin-bottom: 0.5rem;
    }}

    /* BUTTONS */
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
        theme_mode: "light" or "dark" theme mode

    Call this at the start of the application.
    """
    global THEME

    # Select theme based on mode
    THEME = DARK_THEME if theme_mode.lower() == "dark" else LIGHT_THEME

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


def feature_card(icon: str, title: str, description: str, status: str = "active") -> None:
    """
    Renders a feature card using HTML/CSS for better control.
    """
    badge = status_badge(status)

    html = f"""
    <article class="metric-card" role="article" aria-label="Feature: {title}">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
            <div style="font-size: 2.5rem; background: {THEME['background']}; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 12px;" role="img" aria-label="{title} icon">{icon}</div>
            {badge}
        </div>
        <h3 style="margin-top: 0.5rem; color: {THEME['text_main']}; font-size: 1.25rem;">{title}</h3>
        <p style="color: {THEME['text_light']}; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0; flex-grow: 1;">
            {description}
        </p>
    </article>
    """
    st.markdown(html, unsafe_allow_html=True)


def hero_section(title: str, subtitle: str) -> None:
    """
    Renders a centered hero section with gradient background.
    """
    html = f"""
    <section class="hero-container" role="banner" aria-label="Hero section">
        <h1 class="hero-title">{title}</h1>
        <p class="hero-subtitle">{subtitle}</p>
    </section>
    """
    st.markdown(html, unsafe_allow_html=True)


def use_case_card(icon: str, title: str, description: str) -> None:
    """
    Renders a use case card for the social proof section.
    """
    html = f"""
    <article class="metric-card" role="article" aria-label="Use case: {title}">
        <h3 style="margin-top: 0;"><span role="img" aria-label="{title} icon">{icon}</span> {title}</h3>
        <p style="color: {THEME['text_light']}; line-height: 1.6;">
            {description}
        </p>
    </article>
    """
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


def footer() -> None:
    """
    Renders the application footer.
    """
    st.markdown(
        """
        <footer class="footer" role="contentinfo" aria-label="Site footer">
            <p>© 2025 Enterprise Hub. Built with Streamlit & Python.</p>
            <nav aria-label="Footer navigation" style="font-size: 0.8rem; margin-top: 0.5rem;">
                <a href="https://github.com/ChunkyTortoise/enterprise-hub" target="_blank" rel="noopener noreferrer" aria-label="View source code on GitHub">View Source</a> •
                <a href="https://linkedin.com/in/caymanroden" target="_blank" rel="noopener noreferrer" aria-label="Contact developer on LinkedIn">Contact Developer</a>
            </nav>
        </footer>
        """,
        unsafe_allow_html=True,
    )


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
