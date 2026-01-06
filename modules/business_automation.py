"""
Business Automation Module
Custom GPTs, Zapier workflows, and n8n automations (Service 6).
"""
import streamlit as st
import pandas as pd
import utils.ui as ui

def render():
    """Main render function for Business Automation."""
    ui.section_header("Business Automation", "The Workflow Liberator: Eliminate repetitive tasks automatically.")
    
    tabs = st.tabs(["🔄 Workflow Library", "⚡ Automation Builder", "💰 Time Savings"])
    
    with tabs[0]:
        _render_library()
    
    with tabs[1]:
        _render_builder()
        
    with tabs[2]:
        _render_savings()

def _render_library():
    st.markdown("### 🔄 Proven Automation Templates")
    
    col1, col2 = st.columns(2)
    with col1:
        ui.use_case_card(
            icon="📧",
            title="Lead Capture to Outreach",
            description="New lead → Auto-research company → Generate personalized email → Add to CRM → Slack notification."
        )
        ui.use_case_card(
            icon="📄",
            title="Form Submission Processing",
            description="Form submitted → Extract & categorize data → Update spreadsheet → Send confirmation → Create task."
        )
    with col2:
        ui.use_case_card(
            icon="📱",
            title="Content Distribution",
            description="Blog published → Generate social posts → Schedule to Meta/LinkedIn → Update calendar."
        )
        ui.use_case_card(
            icon="🔍",
            title="Competitor Price Tracking",
            description="Scrape competitor site → Detect change → Update internal dashboard → SMS alert to Sales."
        )

def _render_builder():
    st.markdown("### ⚡ Visual Workflow Architect")
    st.write("Drag and drop connections to design your autonomous workflow.")
    
    st.image("https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png", width=100) # Placeholder
    st.info("Interactive n8n-style canvas coming in v6.1. Currently in beta for Founding Clients.")
    
    with st.container(border=True):
        st.markdown("**Example: Lead Enrichment Workflow**")
        st.code("""
        Trigger: New Lead in HubSpot
        Step 1: Get LinkedIn profile via Clearbit
        Step 2: Generate icebreaker with Claude 3.5
        Step 3: Update HubSpot custom field 'AI Icebreaker'
        Step 4: Notify assigned rep in Slack
        """, language="python")

def _render_savings():
    st.markdown("### 💰 Time & Cost Savings Analysis")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        tasks_week = st.number_input("Repetitive Tasks per Week", value=50, step=10)
        mins_per_task = st.number_input("Minutes per Task (Manual)", value=15, step=5)
        hourly_rate = st.number_input("Blended Hourly Rate ($)", value=75, step=5)
        
    # Calculations
    hours_week = (tasks_week * mins_per_task) / 60
    weekly_cost = hours_week * hourly_rate
    annual_cost = weekly_cost * 52
    
    with col2:
        ui.animated_metric("Manual Hours / Week", f"{hours_week:.1f} hrs", icon="⏳")
        ui.animated_metric("Annual Labor Cost", f"${annual_cost:,.0f}", delta="Automatable", delta_color="inverse")
        
    st.divider()
    st.success(f"Typical implementations achieve **85-90%** automation, recovering **${annual_cost * 0.85:,.0f}** in annual productivity.")
