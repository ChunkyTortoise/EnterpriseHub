"""
Cache Performance Dashboard Page.
Visualizes L1/L2/L3 cache hit rates, latency, and throughput.
"""

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.components.cache_performance_dashboard import (
    render_cache_performance_dashboard,
)
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css

st.set_page_config(
    page_title="Cache Performance | EnterpriseHub",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_elite_css()

st.title("CACHE PERFORMANCE")
st.markdown(
    "### L1 Memory | L2 Redis | L3 PostgreSQL -- 3-Tier Cache Intelligence"
)

render_cache_performance_dashboard()

st.markdown("---")
st.caption(
    "EnterpriseHub Cache Intelligence v2026.1 | "
    "Canonical metrics: L1 59.1% + L2 20.5% + L3 8.5% = 88.1% total hit rate"
)
