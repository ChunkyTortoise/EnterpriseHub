"""
User Interface & Experience (UI/UX) Module.

This module serves as the centralized styling and component library for the Enterprise Hub.
It injects custom CSS to override Streamlit's default look with a professional,
enterprise-grade design system (Fintech/SaaS Aesthetic).
"""
from typing import Optional
import streamlit as st

# --- DESIGN SYSTEM CONSTANTS ---
THEME = {
    "primary": "#4F46E5",        # Indigo 600
    "primary_dark": "#4338CA",   # Indigo 700
    "primary_light": "#E0E7FF",  # Indigo 100
    "secondary": "#64748B",      # Slate 500
    "background": "#F8FAFC",     # Slate 50
    "surface": "#FFFFFF",        # White
    "text_main": "#0F172A",      # Slate 900
    "text_light": "#475569",     # Slate 600
    "success": "#10B981",        # Emerald 500
    "warning": "#F59E0B",        # Amber 500
    "danger": "#EF4444",         # Red 500
    "border": "#E2E8F0",         # Slate 200
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
}

CUSTOM_CSS = f"""
<style>
    /* IMPORT INTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* GLOBAL RESET & TYPOGRAPHY */
    html, body, [class*="css"] {{
        font-family: {THEME['font_family']};
        color: {THEME['text_main']};
        background-color: {THEME['background']};
    }}

    /* MAIN CONTAINER BACKGROUND */
    .stApp {{
        background-color: {THEME['background']};
    }}

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {{
        background-color: {THEME['surface']};
        border-right: 1px solid {THEME['border']};
        box-shadow: 1px 0 0 0 {THEME['border']};
    }}
    
    section[data-testid="stSidebar"] h1 {{
        color: {THEME['primary']};
        font-weight: 700;
        font-size: 1.5rem;
        letter-spacing: -0.025em;
    }}
    
    /* NAVIGATION RADIO BUTTONS */
    .stRadio > label {{
        color: {THEME['text_main']};
        font-weight: 500;
    }}

    /* METRIC CARDS */
    .metric-card {{
        background-color: {THEME['surface']};
        border: 1px solid {THEME['border']};
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
        border-color: {THEME['primary_light']};
    }}

    /* HEADERS */
    h1, h2, h3 {{
        color: {THEME['text_main']};
        font-weight: 700;
        letter-spacing: -0.025em;
    }}
    
    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        color: {THEME['primary_dark']};  /* Fallback for non-webkit browsers */
        background: linear-gradient(45deg, {THEME['primary']}, {THEME['primary_dark']});
        background: -webkit-linear-gradient(45deg, {THEME['primary']}, {THEME['primary_dark']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    h2 {{
        font-size: 1.75rem;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid {THEME['border']};
        padding-bottom: 0.5rem;
    }}
    
    h3 {{
        font-size: 1.25rem;
        color: {THEME['text_main']};
        margin-bottom: 0.5rem;
    }}

    /* BUTTONS */
    .stButton button {{
        background-color: {THEME['primary']};
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.25rem;
        border: 1px solid transparent;
        transition: all 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }}
    
    .stButton button:hover {{
        background-color: {THEME['primary_dark']};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transform: translateY(-1px);
    }}
    
    .stButton button:active {{
        transform: translateY(0);
    }}

    .stButton button:focus {{
        outline: 2px solid {THEME['primary']};
        outline-offset: 2px;
        box-shadow: 0 0 0 3px {THEME['primary_light']};
    }}

    /* NATIVE METRIC STYLING */
    div[data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: {THEME['primary']};
        font-feature-settings: "tnum";
        font-variant-numeric: tabular-nums;
    }}
    
    div[data-testid="stMetricLabel"] {{
        font-size: 0.875rem;
        color: {THEME['text_light']};
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
        color: {THEME['primary']};
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }}
    a:hover {{
        color: {THEME['primary_dark']};
        text-decoration: underline;
    }}
    a:focus {{
        outline: 2px solid {THEME['primary']};
        outline-offset: 2px;
        border-radius: 2px;
    }}

    /* DATAFRAMES */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {THEME['border']};
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}

    /* HERO SECTION */
    .hero-container {{
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
        border-radius: 16px;
        padding: 4rem 2rem;
        text-align: center;
        margin-bottom: 3rem;
        border: 1px solid #C7D2FE;
    }}
    
    .hero-title {{
        font-size: 3.5rem;
        font-weight: 800;
        color: {THEME['primary_dark']};
        margin-bottom: 1rem;
        line-height: 1.2;
    }}
    
    .hero-subtitle {{
        font-size: 1.25rem;
        color: {THEME['secondary']};
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.6;
    }}

    /* FOOTER */
    .footer {{
        margin-top: 5rem;
        border-top: 1px solid {THEME['border']};
        padding-top: 2rem;
        text-align: center;
        color: {THEME['secondary']};
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

</style>
"""


def setup_interface() -> None:
    """
    Initializes the UI interface with the Design System.
    Call this at the start of the application.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def card_metric(label: str, value: str, delta: Optional[str] = None, help: Optional[str] = None) -> None:
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
            unsafe_allow_html=True
        )


def status_badge(status: str) -> str:
    """
    Returns a styled HTML badge for status indication.
    Statuses: 'active', 'pending', 'new', 'hero'
    """
    colors = {
        "active": ("#DCFCE7", "#166534"),  # Green-100 to Green-800
        "pending": ("#F1F5F9", "#475569"), # Slate-100 to Slate-600
        "new": ("#DBEAFE", "#1E40AF"),     # Blue-100 to Blue-800
        "hero": ("#FEF3C7", "#92400E")     # Amber-100 to Amber-800
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
        f"""
        <footer class="footer" role="contentinfo" aria-label="Site footer">
            <p>© 2025 Enterprise Hub. Built with Streamlit & Python.</p>
            <nav aria-label="Footer navigation" style="font-size: 0.8rem; margin-top: 0.5rem;">
                <a href="https://github.com/ChunkyTortoise/enterprise-hub" target="_blank" rel="noopener noreferrer" aria-label="View source code on GitHub">View Source</a> •
                <a href="https://linkedin.com/in/caymanroden" target="_blank" rel="noopener noreferrer" aria-label="Contact developer on LinkedIn">Contact Developer</a>
            </nav>
        </footer>
        """,
        unsafe_allow_html=True
    )
