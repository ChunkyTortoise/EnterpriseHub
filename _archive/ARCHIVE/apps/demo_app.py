"""
Market Pulse Demo - Public Streamlit App

Live demo showcasing real-time stock market analysis capabilities.
Built with Python, Streamlit, and Plotly.

Portfolio: https://github.com/ChunkyTortoise/EnterpriseHub
Contact: Available for custom dashboard development
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="Market Pulse Demo - Real-Time Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Demo banner
st.info(
    "👋 **This is a live demo of the Market Pulse module** - "
    "Need a custom financial dashboard? "
    "[View Full Portfolio](https://chunkytortoise.github.io/EnterpriseHub/portfolio/) | "
    "[GitHub](https://github.com/ChunkyTortoise/EnterpriseHub) | "
    "Contact: LinkedIn DM"
)

# Import and render the Market Pulse module
try:
    from modules.market_pulse import render

    render()

except ImportError as e:
    st.error(
        f"Module import failed: {e}\n\n"
        "This demo requires the full EnterpriseHub repository structure."
    )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>Built with EnterpriseHub Framework</strong></p>
        <p>Python • Streamlit • Plotly • yfinance • Technical Analysis</p>
        <p>
            <a href='https://github.com/ChunkyTortoise/EnterpriseHub' target='_blank'>View Code</a> •
            <a href='https://chunkytortoise.github.io/EnterpriseHub/portfolio/' target='_blank'>Full Portfolio</a> •
            Available for custom projects
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
