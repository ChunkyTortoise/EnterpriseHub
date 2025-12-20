"""
User Interface & Experience (UI/UX) Module.

This module serves as the centralized styling and component library for the Enterprise Hub.
It injects custom CSS to override Streamlit's default look with a professional,
enterprise-grade design system (inspired by Modern SaaS aesthetics).
"""
import streamlit as st

# --- DESIGN SYSTEM CONSTANTS ---
THEME = {
    "primary": "#2563EB",        # Enterprise Blue
    "secondary": "#475569",      # Slate 600
    "background": "#F8FAFC",     # Slate 50
    "surface": "#FFFFFF",        # White
    "text_main": "#0F172A",      # Slate 900
    "text_light": "#64748B",     # Slate 500
    "success": "#10B981",        # Emerald 500
    "warning": "#F59E0B",        # Amber 500
    "danger": "#EF4444",         # Red 500
    "font_family": "'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif"
}

CUSTOM_CSS = f"""
<style>
    /* IMPORT INTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* GLOBAL STYLES */
    html, body, [class*="css"] {{
        font-family: {THEME['font_family']};
        color: {THEME['text_main']};
    }}

    /* MAIN CONTAINER BACKGROUND */
    .stApp {{
        background-color: {THEME['background']};
    }}

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {{
        background-color: {THEME['surface']};
        border-right: 1px solid #E2E8F0;
    }}
    
    section[data-testid="stSidebar"] h1 {{
        color: {THEME['primary']};
        font-weight: 700;
        font-size: 1.5rem;
    }}

    /* CARD COMPONENT */
    .metric-card {{
        background-color: {THEME['surface']};
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: box-shadow 0.2s ease-in-out;
    }}
    
    .metric-card:hover {{
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}

    /* HEADERS */
    h1, h2, h3 {{
        color: {THEME['text_main']};
        font-weight: 700;
        letter-spacing: -0.025em;
    }}
    
    h1 {{
        font-size: 2.25rem;
        margin-bottom: 1rem;
    }}

    h2 {{
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }}
    
    h3 {{
        font-size: 1.125rem;
        color: {THEME['secondary']};
    }}

    /* BUTTONS */
    .stButton button {{
        background-color: {THEME['primary']};
        color: white;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border: none;
        transition: background-color 0.2s;
    }}
    
    .stButton button:hover {{
        background-color: #1D4ED8; /* Darker Blue */
        border-color: #1D4ED8;
    }}

    /* CUSTOM METRIC STYLING */
    div[data-testid="stMetricValue"] {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {THEME['primary']};
    }}
    
    div[data-testid="stMetricLabel"] {{
        font-size: 0.875rem;
        color: {THEME['text_light']};
        font-weight: 500;
    }}

    /* ALERTS/MESSAGES */
    .stAlert {{
        border-radius: 6px;
        border: 1px solid transparent;
    }}
    
    /* LINK STYLES */
    a {{
        color: {THEME['primary']};
        text-decoration: none;
    }}
    a:hover {{
        text-decoration: underline;
    }}

    /* DATAFRAME STYLING */
    div[data-testid="stDataFrame"] {{
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        overflow: hidden;
    }}

</style>
"""


def setup_interface():
    """
    Initializes the UI interface.
    Call this function at the very beginning of your Streamlit app.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def card_metric(label: str, value: str, delta: str = None, help: str = None):
    """
    Displays a metric in a styled card container.
    """
    st.metric(label=label, value=value, delta=delta, help=help)


def section_header(title: str, subtitle: str = None):
    """
    Displays a styled section header.
    """
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<p style='color: {THEME['text_light']}; margin-top: -10px; margin-bottom: 20px;'>{subtitle}</p>", unsafe_allow_html=True)


def status_badge(status: str):
    """
    Returns a styled HTML badge for status indication.
    Statuses: 'active', 'pending', 'new', 'hero'
    """
    colors = {
        "active": ("#DCFCE7", "#166534"),  # Green
        "pending": ("#F1F5F9", "#475569"), # Gray
        "new": ("#DBEAFE", "#1E40AF"),     # Blue
        "hero": ("#FEF3C7", "#92400E")     # Amber
    }
    
    bg, text = colors.get(status.lower(), colors["pending"])
    
    return f"""
    <span style='
        background-color: {bg};
        color: {text};
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 4px;
    '>
        {status}
    </span>
    """

def feature_card(icon: str, title: str, description: str, status: str = "active"):
    """
    Renders a feature card using HTML/CSS for better control.
    """
    badge = status_badge(status)
    
    html = f"""
    <div class="metric-card" style="height: 100%;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        {badge}
        <h3 style="margin-top: 0.5rem; color: {THEME['text_main']};">{title}</h3>
        <p style="color: {THEME['text_light']}; font-size: 0.9rem; line-height: 1.5;">
            {description}
        </p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
