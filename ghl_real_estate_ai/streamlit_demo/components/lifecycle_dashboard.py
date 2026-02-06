"""
🧬 Full Lifecycle Conversion Engine Dashboard
===========================================

Unified view of the lead journey from initial contact to post-closing.
Integrates event logs from GHL, AI thought streams, and milestone tracking.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time
import asyncio
from ghl_real_estate_ai.services.agent_state_sync import sync_service
try:
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
except ImportError:
    import asyncio
    def run_async(coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

def render_full_lifecycle_dashboard():
    """Renders the Full Lifecycle tab for Jorge's Command Center."""
    
    # Ensure state is initialized (run_async handles the loop)
    state = run_async(sync_service._ensure_initialized())
    current_state = sync_service.get_state()
    
    st.markdown("""
        <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">🧬 FULL LIFECYCLE ENGINE</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Autonomous Lead Journey & Event Reconciliation</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(99, 102, 241, 0.1); color: #6366F1; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(99, 102, 241, 0.3); letter-spacing: 0.1em;">
                    STATUS: ACTIVE
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Lead Selection for Lifecycle View
    leads = current_state.get("leads", [])
    lead_options = {f"{l['name']} ({l.get('status', 'New')})": l['id'] for l in leads}
    
    if not lead_options:
        st.warning("No leads found in sync service. Please trigger activity.")
        return

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_label = st.selectbox("Select Lead to View Lifecycle:", 
                                list(lead_options.keys()),
                                index=0)
        selected_lead_id = lead_options[selected_label]
        selected_lead = next((l for l in leads if l['id'] == selected_lead_id), None)

    with col_sel2:
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Sync GHL Activity", use_container_width=True):
            with st.spinner("Reconciling events with GoHighLevel..."):
                # Trigger a real sync in production
                time.sleep(1)
                st.toast("Sync complete!", icon="✅")
                st.rerun()

    # Lifecycle Progress Bar
    st.markdown("### 🗺️ Journey Progression")
    
    stages = ["Inbound", "Qualified", "Showing", "Offer", "Escrow", "Closed"]
    
    # Map engagement_status to stage index
    status_map = {
        "new": 0,
        "qualifying": 0,
        "qualified": 1,
        "showing_booked": 2,
        "post_showing": 2,
        "offer_sent": 3,
        "under_contract": 4,
        "closed": 5
    }
    
    current_status = selected_lead.get("engagement_status", "new").lower() if selected_lead else "new"
    current_stage_idx = status_map.get(current_status, 0)
    
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            is_past = i < current_stage_idx
            is_current = i == current_stage_idx
            color = "#10B981" if is_past else "#6366F1" if is_current else "#334155"
            bg_color = "rgba(16, 185, 129, 0.1)" if is_past else "rgba(99, 102, 241, 0.1)" if is_current else "transparent"
            
            st.markdown(f"""
                <div style="background: {bg_color}; border: 1px solid {color}; border-radius: 8px; padding: 10px; text-align: center;">
                    <div style="color: {color}; font-weight: bold; font-size: 0.8rem;">{stage.upper()}</div>
                    <div style="font-size: 1.2rem;">{'✅' if is_past else '🔵' if is_current else '⚪'}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Split View: Unified Event Log & AI Controls
    col_log, col_ctrl = st.columns([2, 1])

    with col_log:
        st.markdown("### 📡 Unified Event Log")
        st.markdown("*Real-time reconciliation of CRM actions and AI thought streams*")
        
        # Pull real events from sync service
        events = sync_service.get_lead_events(selected_lead_id)
        
        if not events:
            st.info(f"No events logged for {selected_label} yet.")
            # Fallback mock for visual demo if empty
            events = [
                {"time": "Now", "source": "System", "event": "Lifecycle monitoring activated.", "type": "action"}
            ]

        for e in events:
            icon = "🧠" if e["type"] == "thought" else "🏷️" if e["type"] == "action" else "🚀" if e["type"] == "node" else "💬"
            color = "#8B5CF6" if e["source"] == "AI" else "#1E88E5"
            
            st.markdown(f"""
                <div style="display: flex; gap: 10px; margin-bottom: 12px; border-left: 3px solid {color}; padding-left: 15px;">
                    <div style="color: #8B949E; font-size: 0.75rem; min-width: 80px;">{e['time']}</div>
                    <div style="background: {color}20; color: {color}; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; height: fit-content;">{e['source']}</div>
                    <div style="color: #E6EDF3; font-size: 0.9rem;">{icon} {e['event']}</div>
                </div>
            """, unsafe_allow_html=True)

    with col_ctrl:
        st.markdown("### ⚙️ Lifecycle Control")
        st.markdown("*Manual overrides for autonomous nodes*")
        
        current_node = selected_lead.get("current_step", "analyze_intent")
        
        with st.container(border=True):
            st.markdown(f"**Current Node: `{current_node}`**")
            
            if st.button("🚀 Push Next Node", use_container_width=True):
                st.toast("Triggering next lifecycle node...")
                # In prod, this would call an API
                
            if st.button("🔄 Restart Node", use_container_width=True):
                st.toast(f"Restarting node: {current_node}")
                
            st.divider()
            st.markdown("**Quick Actions**")
            if st.button("📞 Trigger Retell Call", use_container_width=True):
                st.toast("Initiating AI Call...")
            if st.button("📄 Generate Updated CMA", use_container_width=True):
                st.toast("Generating CMA report...")
            if st.button("🏷️ Apply 'Post-Closing' Tag", use_container_width=True):
                st.toast("Applying GHL tag...")

    # Lifecycle Conversion Metrics
    st.markdown("---")
    st.markdown("### 📊 Conversion Path Analytics")
    
    m1, m2, m3, m4 = st.columns(4)
    
    # Calculate some dynamic values based on lead
    score = selected_lead.get("score", 50)
    frs = selected_lead.get("frs_score", score)
    
    with m1:
        st.metric("Time in Stage", "1.2 Days", "-0.2 Days")
    with m2:
        st.metric("Engagement Velocity", "High" if score > 70 else "Medium", "+5%")
    with m3:
        st.metric("FRS Commitment", f"{frs}/100", "+2")
    with m4:
        st.metric("Predicted Closing", "Feb 15", "On Track")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_full_lifecycle_dashboard()

    # Lifecycle Conversion Metrics
    st.markdown("---")
    st.markdown("### 📊 Conversion Path Analytics")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Time in Stage", "2.4 Days", "-0.5 Days")
    with m2:
        st.metric("Engagement Velocity", "High", "+12%")
    with m3:
        st.metric("FRS Commitment", "88/100", "+5")
    with m4:
        st.metric("Predicted Closing", "Feb 12", "On Track")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_full_lifecycle_dashboard()
