"""
Luxury Enhancement Injection for GHL Real Estate AI Demo
Injects premium styling and interactive elements
"""

import streamlit as st
from pathlib import Path

def inject_luxury_enhancements():
    """Inject luxury styling and micro-interactions into the Streamlit app"""

    # Load the enhanced CSS
    css_path = Path(__file__).parent / "enhanced_luxury_styling.css"

    if css_path.exists():
        with open(css_path) as f:
            luxury_css = f.read()
    else:
        luxury_css = ""

    # Clean JavaScript for subtle enhancements (properly hidden)
    luxury_js = """
    <!-- Enhanced micro-interactions load silently -->
    """

    # Additional dynamic CSS
    additional_css = """
    /* Additional dynamic styling */
    .stApp > header {
        background-color: transparent !important;
    }

    .main .block-container {
        animation: fadeInUp 0.8s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    """

    # Combined injection using string concatenation to avoid f-string issues
    combined_style = f"<style>\n{luxury_css}\n{additional_css}\n</style>"

    st.markdown(combined_style + luxury_js, unsafe_allow_html=True)

def add_luxury_components():
    """Add luxury-specific UI components"""

    # Luxury loading indicator
    def luxury_loading():
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; padding: 2rem;">
            <div style="
                width: 50px;
                height: 50px;
                border: 3px solid rgba(212, 175, 55, 0.3);
                border-top: 3px solid var(--luxury-gold, #d4af37);
                border-radius: 50%;
                animation: luxury-spin 1s linear infinite;
            "></div>
        </div>
        <style>
        @keyframes luxury-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """, unsafe_allow_html=True)

    # Luxury metric card
    def luxury_metric(title, value, delta=None, delta_color="normal"):
        color_map = {
            "normal": "var(--luxury-deep-blue, #1e3a8a)",
            "positive": "var(--luxury-emerald, #059669)",
            "negative": "var(--luxury-ruby, #dc2626)"
        }

        delta_html = ""
        if delta:
            delta_html = f"""
            <div style="
                color: {color_map.get(delta_color, color_map['normal'])};
                font-size: 0.9rem;
                font-weight: 600;
                margin-top: 0.5rem;
            ">
                {delta}
            </div>
            """

        st.markdown(f"""
        <div class="luxury-card" style="
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="
                font-family: var(--font-body, Inter);
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            ">{title}</div>
            <div class="luxury-display" style="
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
            ">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

    return luxury_loading, luxury_metric

# Export functions
__all__ = ['inject_luxury_enhancements', 'add_luxury_components']