import asyncio
import os
import random
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import ghl_real_estate_ai.agent_system.skills.monitoring
from ghl_real_estate_ai.agent_system.dojo.runner import DojoRunner
from ghl_real_estate_ai.agent_system.skills.base import registry
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


def render_sparkline(data, color="#6366F1"):
    """Renders a small sparkline chart."""
    fig = go.Figure(data=go.Scatter(y=data, mode="lines", line=dict(color=color, width=2), hoverinfo="none"))
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=30,
        width=100,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def render_agent_os_tab():
    """
    Renders the Agentic OS management tab within the Ops Hub.
    Provides visibility into hooks, tools, memory, and governance.
    """
    st.subheader("🧬 Agentic Operating System")
    st.markdown("Monitoring and orchestration for the autonomous agent framework.")

    # System Status
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Hooks Active", "35/35", "✅")
    col2.metric("Operational Tools", "5/5", "✅")
    col3.metric("Memory Nodes", "1,284", "+42")
    col4.metric("Dojo Regimens", "12", "Active")

    st.markdown("---")

    # Agent Performance Sparklines
    st.markdown("#### ⚡ Real-Time Agent Performance")
    agents = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    perf_cols = st.columns(len(agents))

    for i, agent in enumerate(agents):
        with perf_cols[i]:
            # Use the monitoring skill
            perf_data = registry.get_skill("check_agent_performance").execute(agent_name=agent)

            st.markdown(f"**{agent}**")
            # Generate random sparkline data for demo
            spark_data = [random.uniform(0.8, 1.0) for _ in range(10)]
            st.plotly_chart(render_sparkline(spark_data), use_container_width=False, config={"displayModeBar": False})
            st.caption(f"Success: {perf_data['success_rate'] * 100:.0f}%")

    st.markdown("---")

    tab_hooks, tab_tools, tab_memory, tab_governance, tab_dojo = st.tabs(
        ["🪝 Hooks", "🛠️ Tools", "🧠 Memory", "🛡️ Governance", "🥋 Dojo"]
    )

    with tab_hooks:
        st.markdown("#### Agentic Hooks (The Brains)")
        st.info("Hooks are specialized cognitive units that perform specific domain analysis.")

        hooks_data = [
            {"category": "Architecture", "name": "Codebase Investigator", "status": "Ready", "last_run": "2m ago"},
            {"category": "Architecture", "name": "Pattern Architect", "status": "Ready", "last_run": "15m ago"},
            {"category": "Real Estate", "name": "Market Oracle", "status": "Active", "last_run": "Just now"},
            {"category": "Real Estate", "name": "Lead Persona Simulator", "status": "Active", "last_run": "Just now"},
            {"category": "Real Estate", "name": "Sentiment Decoder", "status": "Active", "last_run": "Just now"},
            {"category": "Security", "name": "Security Sentry", "status": "Ready", "last_run": "5m ago"},
            {"category": "Security", "name": "Edge Case Generator", "status": "Ready", "last_run": "10m ago"},
        ]

        st.table(hooks_data)

        if st.button("🔄 Sync Hooks Registry"):
            st.toast("Syncing hooks from registry...")
            st.success("Hooks Registry Updated.")

    with tab_tools:
        st.markdown("#### Operational Power Tools (The Hands)")
        st.info("Tools allow agents to interact with the environment and codebase.")

        tools = [
            {"name": "Codebase Mapper", "desc": "AST scanning & dependency mapping", "status": "Installed"},
            {"name": "Security Auditor", "desc": "Wrapper for bandit/semgrep audits", "status": "Installed"},
            {"name": "Market Intel Scraper", "desc": "Real-time search & extraction", "status": "Operational"},
            {"name": "Graphiti Connector", "desc": "Long-term memory bridge", "status": "Active"},
            {"name": "GHL Webhook Sorter", "desc": "High-speed lead event routing", "status": "Operational"},
        ]

        for tool in tools:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{tool['name']}**")
                c1.markdown(f"<small>{tool['desc']}</small>", unsafe_allow_html=True)
                c2.success(tool["status"])

    with tab_memory:
        st.markdown("#### Graphiti Memory Strategy (The Hippocampus)")

        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            st.markdown("##### Knowledge Graph Status")
            st.code(
                """
{
    "nodes": 1284,
    "edges": 4512,
    "top_entities": ["Lead", "Property", "Agent"],
    "coherence_score": 0.94
}
            """,
                language="json",
            )

        with col_m2:
            st.markdown("##### Memory Controls")
            st.button("🧹 Clear Volatile Memory", use_container_width=True)
            st.button("🔍 Re-index Graph", use_container_width=True)
            st.button("💾 Backup Long-term Memory", use_container_width=True)

    with tab_governance:
        st.markdown("#### Safety & Compliance (The Conscience)")

        from ghl_real_estate_ai.agent_system.config import MAX_COST_PER_SESSION, MAX_TURNS

        st.warning(f"⚠️ **Active Guardrails:** Maximum session cost set to ${MAX_COST_PER_SESSION:.2f} USD.")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("**Operational Limits**")
            st.slider("Max Session Cost ($)", 0.1, 5.0, float(MAX_COST_PER_SESSION))
            st.slider("Max Agent Turns", 5, 50, int(MAX_TURNS))

        with col_g2:
            st.write("**Kill Switches**")
            st.toggle("Emergency System Halt", value=False)
            st.toggle("Strict Pattern Enforcement", value=True)
            st.toggle("Human-in-the-loop for Commits", value=True)

    with tab_dojo:
        st.markdown("#### Continuous Improvement Gym (The Dojo)")

        st.markdown("""
        The Dojo is where agents 'spar' with simulated leads to improve their negotiation and conversion skills.
        """)

        col_d1, col_d2 = st.columns([1, 1])
        with col_d1:
            st.markdown("##### 🥋 Start New Sparring Session")
            regimen = st.selectbox(
                "Select Training Regimen", ["Objection Handling", "Compliance Drills", "Lead Qualification"]
            )

            persona = st.selectbox(
                "Select Opponent Persona",
                ["The Confused First-Timer", "The Aggressive Investor", "The Fair Housing Trap", "The Vague Browser"],
            )

            if st.button("🚀 Begin Sparring Match", use_container_width=True, type="primary"):
                with st.status("🥋 Sparring in progress...", expanded=True) as status:
                    runner = DojoRunner()
                    # Use a new event loop or the existing one

                    st.write("Initializing Trainee Agent...")
                    st.write(f"Simulating Lead Persona: {persona}...")

                    st.session_state.last_regimen = regimen
                    st.session_state.last_persona = persona

                    result = run_async(runner.run_sparring_match(regimen, persona))

                    status.update(label="✅ Sparring Match Complete!", state="complete", expanded=False)
                    st.session_state.last_dojo_result = result
                    st.rerun()

        with col_d2:
            if "last_dojo_result" in st.session_state:
                res = st.session_state.last_dojo_result
                st.markdown("##### 📊 Latest Match Results")

                # Display scores using the new Sensei format
                scores = res.get("scores", {})
                overall = res.get("overall", 0)

                st.metric("Overall Score", f"{overall * 20:.0f}%")

                cols = st.columns(2)
                cols[0].write(f"**Empathy:** {scores.get('empathy', 0)}/5")
                cols[0].write(f"**Goal Pursuit:** {scores.get('goal_pursuit', 0)}/5")
                cols[1].write(f"**Compliance:** {scores.get('compliance', 0)}/5")
                cols[1].write(f"**Tone:** {scores.get('tone_match', 0)}/5")

                st.info(f"**Session Cost:** ${res.get('session_cost', 0):.4f}")

                # Sensei Feedback (Phase 4)
                if "feedback" in res:
                    st.markdown("##### 🧠 Sensei Feedback")
                    st.write(res["feedback"])

                    if res.get("coaching_tips"):
                        st.markdown("**Coaching Tips:**")
                        for tip in res["coaching_tips"]:
                            st.markdown(f"- {tip}")

                # RLHF Bridge (Phase 4)
                if overall >= 4.0:
                    if st.button("🌟 Export to RLHF Pool", use_container_width=True):
                        if "rlhf_pool" not in st.session_state:
                            st.session_state.rlhf_pool = []

                        st.session_state.rlhf_pool.append(
                            {
                                "type": "dojo_match",
                                "regimen": st.session_state.last_regimen,
                                "persona": st.session_state.last_persona,
                                "history": res["history"],
                                "score": overall,
                                "feedback": res.get("feedback", ""),
                            }
                        )
                        st.success("Match exported to RLHF Pool as a few-shot example!")

                with st.expander("View Transcript"):
                    for msg in res["history"]:
                        role = "👤 Lead" if msg["role"] == "user" else "🤖 Agent"
                        st.markdown(f"**{role}:** {msg['content']}")
            else:
                st.info("No sparring sessions run in this session yet.")
