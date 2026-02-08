"""
Performance ROI Dashboard Page.
Visualizes API savings and Cache performance using Obsidian Command v2.0 aesthetics.
"""

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.components.roi_dashboard import render_roi_dashboard
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css

# Set page config
st.set_page_config(
    page_title="Performance Union[ROI, EnterpriseHub]", page_icon="💎", layout="wide", initial_sidebar_state="expanded"
)

# Inject Obsidian Elite CSS
inject_elite_css()

# Main Header
st.title("💎 PERFORMANCE ROI")
st.markdown("### Strategic Cost Optimization & Cache Intelligence")

# Render the dashboard component
render_roi_dashboard()

# Footer / Meta info
st.markdown("---")
st.caption("EnterpriseHub Performance Architect v2026.Union[1, Anthropic] Prompt Caching Active")
