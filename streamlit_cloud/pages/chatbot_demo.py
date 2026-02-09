"""Interactive Chatbot Demo -- Live Lead Qualification

Streamlit multipage app page that demonstrates the chatbot widget
with real-time qualification scoring. Runs entirely on mock data --
no external dependencies required.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add parent directory so imports work on Streamlit Cloud
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.chatbot_widget import ChatbotWidget, QualificationScores  # noqa: E402

st.set_page_config(
    page_title="Chatbot Demo",
    page_icon="\U0001f4ac",
    layout="wide",
)

st.title("\U0001f4ac Interactive Chatbot Demo")
st.caption("Watch lead qualification scores update in real-time as you chat")

# ── Sidebar configuration ────────────────────────────────────────────────────

st.sidebar.markdown("### \u2699\ufe0f Configuration")
industry = st.sidebar.selectbox(
    "Industry",
    ["real_estate", "dental", "hvac"],
    format_func=lambda x: {
        "real_estate": "\U0001f3e0 Real Estate",
        "dental": "\U0001f9b7 Dental",
        "hvac": "\u2744\ufe0f HVAC",
    }[x],
)

# Reset state on industry change
if st.session_state.get("industry") != industry:
    st.session_state["industry"] = industry
    st.session_state["messages"] = []
    st.session_state["bot_type"] = "lead"
    st.session_state["scores"] = QualificationScores()
    st.session_state["message_count"] = 0

# Reset button
if st.sidebar.button("\U0001f504 Reset Chat"):
    widget = ChatbotWidget(industry=industry)
    widget.reset()
    st.rerun()

# ── Render widget ─────────────────────────────────────────────────────────────

widget = ChatbotWidget(industry=industry)
widget.render()
