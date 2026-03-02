"""
RAG Document Intelligence Page.
Demonstrates hybrid BM25+dense+reranking retrieval on real-estate documents.
"""

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.components.rag_demo_dashboard import (
    render_rag_demo_dashboard,
)
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css

st.set_page_config(
    page_title="RAG Document Intelligence | EnterpriseHub",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_elite_css()

st.title("RAG DOCUMENT INTELLIGENCE")
st.markdown(
    "### Hybrid BM25 + Dense Retrieval | Cross-Encoder Reranking | Source Attribution"
)

render_rag_demo_dashboard()

st.markdown("---")
st.caption(
    "EnterpriseHub RAG Intelligence v2026.1 | "
    "Phase 3 Complete: Hybrid Search + Reranking | "
    "Phase 4 In Progress: Agentic RAG with Query Planning"
)
