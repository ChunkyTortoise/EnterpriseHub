"""Standardized Streamlit UI components for AgentForge."""
from __future__ import annotations

from typing import Optional

import streamlit as st


def chat_message(role: str, text: str, avatar: Optional[str] = None) -> None:
    """Render a standardized chat message."""
    try:
        with st.chat_message(role, avatar=avatar):
            st.markdown(text)
    except Exception:
        st.markdown(f"**{role.title()}:** {text}")


def citation_card(source: str, page: Optional[int] = None, confidence: Optional[float] = None) -> None:
    """Render a citation card with source metadata."""
    with st.container(border=True):
        st.markdown(f"**Source:** {source}")
        if page is not None:
            st.markdown(f"**Page:** {page}")
        if confidence is not None:
            st.progress(min(max(confidence, 0.0), 1.0))
            st.caption(f"Confidence: {confidence:.2f}")


def agent_status(step: str, log: str) -> None:
    """Render a collapsible agent status block."""
    with st.expander(step, expanded=False):
        st.markdown(log)
