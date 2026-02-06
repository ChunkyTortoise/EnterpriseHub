"""
Automated Reporting Module
Python pipelines that clean, transform, and email polished reports (Service 9).
"""
import streamlit as st
import pandas as pd
import numpy as np
import utils.ui as ui
from datetime import datetime

def render():
    """Main render function for Automated Reporting."""
    ui.section_header("Automated Reporting", "The Report Generator: No more manual Excel aggregation.")
    
    tabs = st.tabs(["📊 Report Gallery", "⚙️ Pipeline Config", "⏳ Efficiency Stats"])
    
    with tabs[0]:
        _render_gallery()
    
    with tabs[1]:
        _render_config()
        
    with tabs[2]:
        _render_efficiency()

def _render_gallery():
    st.markdown("### 📊 Enterprise Report Gallery")
    st.write("Live previews of automated Python-generated reports.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1. Sales Pipeline Velocity**")
        df = pd.DataFrame({
            "Stage": ["Discovery", "Qualified", "Proposal", "Negotiation"],
            "Count": [45, 28, 12, 8],
            "Value ($K)": [450, 280, 180, 120]
        })
        st.bar_chart(df.set_index("Stage")["Value ($K)"])
        
    with col2:
        st.markdown("**2. Marketing ROI Attribution**")
        df_m = pd.DataFrame({
            "Channel": ["Google", "Meta", "Email", "Direct"],
            "ROI": [3.2, 2.8, 8.5, 12.1]
        })
        st.bar_chart(df_m.set_index("Channel")["ROI"])

def _render_config():
    st.markdown("### ⚙️ Pipeline Configuration")
    
    with st.container(border=True):
        st.markdown("**Source Connections**")
        st.checkbox("HubSpot CRM API", value=True)
        st.checkbox("Stripe Billing API", value=True)
        st.checkbox("Google Sheets (Backup)", value=False)
        
        st.divider()
        st.markdown("**Execution Schedule**")
        st.radio("Frequency", ["Daily at 8:00 AM", "Weekly (Monday)", "Real-time (Webhooks)"], horizontal=True)
        
        st.divider()
        st.markdown("**Distribution**")
        st.multiselect("Notify via:", ["Email (PDF)", "Slack Channel", "Microsoft Teams"], default=["Email (PDF)", "Slack Channel"])

def _render_efficiency():
    st.markdown("### ⏳ Manual vs. Automated Reporting")
    
    col1, col2 = st.columns(2)
    with col1:
        staff_time = st.number_input("Hours spent manually compiling reports / week", value=8, step=1)
        staff_rate = st.number_input("Staff Hourly Rate ($)", value=85, step=5)
        
    # Calculations
    manual_annual_cost = staff_time * staff_rate * 52
    auto_annual_cost = 2200 # Service cost
    roi = (manual_annual_cost - auto_annual_cost) / auto_annual_cost * 100
    
    with col2:
        ui.animated_metric("Manual Annual Cost", f"${manual_annual_cost:,.0f}", icon="📉")
        ui.animated_metric("Reporting ROI", f"{roi:.0f}%", delta="After 1yr", icon="🚀")
        
    st.divider()
    st.info("💡 **Key Outcome:** Better data enables earlier pipeline interventions, improving close rates by 2-5% on average.")
