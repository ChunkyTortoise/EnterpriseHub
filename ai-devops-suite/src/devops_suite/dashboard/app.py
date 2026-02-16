"""Unified Streamlit dashboard with 4 tabs: Monitoring, Prompts, Pipeline, Alerts."""

from __future__ import annotations


def render_dashboard():
    """Entry point for Streamlit dashboard. Run with: streamlit run -m devops_suite.dashboard.app"""
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit not installed. Run: pip install streamlit")
        return

    st.set_page_config(page_title="AI DevOps Suite", page_icon="🔧", layout="wide")
    st.title("AI DevOps Suite")

    tab_monitor, tab_prompts, tab_pipeline, tab_alerts = st.tabs(
        ["Monitoring", "Prompts", "Pipeline", "Alerts"]
    )

    with tab_monitor:
        st.header("Agent Monitoring")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Agents", "0")
        with col2:
            st.metric("P95 Latency", "0ms")
        with col3:
            st.metric("Success Rate", "0%")
        st.subheader("Latency Over Time")
        st.info("Connect to the API to see live metrics.")

    with tab_prompts:
        st.header("Prompt Registry")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Prompts", "0")
        with col2:
            st.metric("Active Experiments", "0")
        st.subheader("Prompt Performance")
        st.info("Create prompts via the API to see them here.")

    with tab_pipeline:
        st.header("Data Pipeline")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Jobs", "0")
        with col2:
            st.metric("Runs Today", "0")
        with col3:
            st.metric("Quality Score", "N/A")
        st.subheader("Recent Job Runs")
        st.info("Create pipeline jobs via the API.")

    with tab_alerts:
        st.header("Alert History")
        st.metric("Active Rules", "0")
        st.subheader("Recent Alerts")
        st.info("Configure alert rules via the API.")


if __name__ == "__main__":
    render_dashboard()
