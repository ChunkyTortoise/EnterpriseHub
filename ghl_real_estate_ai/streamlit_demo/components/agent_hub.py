"""Streamlit UI for the Agent Hub LangGraph workflow."""
from __future__ import annotations

import streamlit as st

from ghl_real_estate_ai.agents.agent_hub import AgentHub


def render_agent_hub() -> None:
    st.header("🧭 Agent Hub")
    st.caption("Planner → Researcher → Reviewer → Publisher with human approval.")

    query = st.text_area("Task or question", placeholder="e.g., Summarize the current market outlook.")
    if st.button("Generate Draft", key="agent_hub_generate"):
        if not query.strip():
            st.warning("Enter a task first.")
        else:
            hub = AgentHub()
            st.session_state.agent_hub_state = hub.run_for_review(query)

    state = st.session_state.get("agent_hub_state")
    if not state:
        return

    st.markdown("#### Workflow")
    st.markdown(
        \"\"\"\n```mermaid\ngraph LR\n    Planner --> Researcher --> Reviewer --> Publisher\n    Reviewer --> Researcher\n```\n\"\"\",\n        unsafe_allow_html=True,\n    )

    st.markdown("#### Draft")
    st.text_area("Plan", value=state.get("plan", ""), height=120, key="agent_hub_plan", disabled=True)
    st.text_area("Research", value=state.get("research", ""), height=160, key="agent_hub_research", disabled=True)
    st.text_area("Review Notes", value=state.get("review_notes", ""), height=100, key="agent_hub_review", disabled=True)

    st.markdown("#### Human Approval")
    draft_edit = st.text_area("Edit Draft (optional)", value=state.get("draft", ""), height=180)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve & Publish", key="agent_hub_publish"):
            hub = AgentHub()
            updated = hub.publish(state, edits=draft_edit)
            st.session_state.agent_hub_final = updated.get("final", "")
    with col2:
        if st.button("Reject", key="agent_hub_reject"):
            st.session_state.agent_hub_final = "Draft rejected. Please refine the task or inputs."

    final = st.session_state.get("agent_hub_final")
    if final:
        st.markdown("#### Final Output")
        st.success(final)
