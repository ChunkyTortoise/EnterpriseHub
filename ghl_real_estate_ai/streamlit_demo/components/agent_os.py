import streamlit as st
import os
from pathlib import Path

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
    
    tab_hooks, tab_tools, tab_memory, tab_governance, tab_dojo = st.tabs([
        "🪝 Hooks", 
        "🛠️ Tools", 
        "🧠 Memory", 
        "🛡️ Governance",
        "🥋 Dojo"
    ])
    
    with tab_hooks:
        st.markdown("#### Agentic Hooks (The Brains)")
        st.info("Hooks are specialized cognitive units that perform specific domain analysis.")
        
        hooks_data = [
            {"category": "Architecture", "name": "Codebase Investigator", "status": "Ready", "last_run": "2m ago"},
            {"category": "Architecture", "name": "Pattern Architect", "status": "Ready", "last_run": "15m ago"},
            {"category": "Real Estate", "name": "Market Oracle", "status": "Active", "last_run": "Just now"},
            {"category": "Real Estate", "name": "Lead Persona Simulator", "status": "Idle", "last_run": "1h ago"},
            {"category": "Security", "name": "Security Sentry", "status": "Ready", "last_run": "5m ago"},
            {"category": "Security", "name": "Edge Case Generator", "status": "Ready", "last_run": "10m ago"}
        ]
        
        st.table(hooks_data)
        
        if st.button("🔄 Sync Hooks Registry"):
            st.toast("Syncing hooks from EXTENSIVE_CLAUDE_HOOKS_V2.md...")
            st.success("Hooks Registry Updated.")

    with tab_tools:
        st.markdown("#### Operational Power Tools (The Hands)")
        st.info("Tools allow agents to interact with the environment and codebase.")
        
        tools = [
            {"name": "Codebase Mapper", "desc": "AST scanning & dependency mapping", "status": "Installed"},
            {"name": "Security Auditor", "desc": "Wrapper for bandit/semgrep audits", "status": "Installed"},
            {"name": "Market Intel Scraper", "desc": "Real-time search & extraction", "status": "Operational"},
            {"name": "Graphiti Connector", "desc": "Long-term memory bridge", "status": "Active"},
            {"name": "GHL Webhook Sorter", "desc": "High-speed lead event routing", "status": "Operational"}
        ]
        
        for tool in tools:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{tool['name']}**")
                c1.markdown(f"<small>{tool['desc']}</small>", unsafe_allow_html=True)
                c2.success(tool['status'])

    with tab_memory:
        st.markdown("#### Graphiti Memory Strategy (The Hippocampus)")
        
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            st.markdown("##### Knowledge Graph Status")
            # Mock graph stats
            st.code("""
{
    "nodes": 1284,
    "edges": 4512,
    "top_entities": ["Lead", "Property", "Agent"],
    "coherence_score": 0.94
}
            """, language="json")
        
        with col_m2:
            st.markdown("##### Memory Controls")
            st.button("🧹 Clear Volatile Memory", use_container_width=True)
            st.button("🔍 Re-index Graph", use_container_width=True)
            st.button("💾 Backup Long-term Memory", use_container_width=True)

    with tab_governance:
        st.markdown("#### Safety & Compliance (The Conscience)")
        
        st.warning("⚠️ **Active Guardrails:** Maximum session cost set to $1.00 USD.")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("**Operational Limits**")
            st.slider("Max Session Cost ($)", 0.1, 5.0, 1.0)
            st.slider("Max Agent Turns", 5, 50, 15)
        
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
        
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            st.markdown("##### Recent Sparring Match")
            st.markdown("""
            **Match ID:** #SP-8821  
            **Agent:** 'The Closer'  
            **Opponent:** 'Skeptic Investor' (Simulated)  
            **Result:** Success - Lead moved to 'Agreement' stage.  
            **Score:** 88/100
            """)
        
        with col_d2:
            st.button("🥋 Start New Sparring Session", use_container_width=True, type="primary")
            st.button("📈 View Training Progress", use_container_width=True)
