"""
GHL Real Estate AI - Unified Enterprise Module
Consolidates Interactive Playground, Analytics, Executive Insights, and Admin Controls.
"""
import streamlit as st
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

# Lazy import utils.ui to avoid circular dependencies
import utils.ui as ui

# Add ghl_real_estate_ai to path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# --- IMPORT GHL SERVICES ---
try:
    from ghl_real_estate_ai.services.campaign_analytics import CampaignTracker
    from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
    from ghl_real_estate_ai.services.bulk_operations import BulkOperationsManager
    from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService
    from ghl_real_estate_ai.services.predictive_scoring import PredictiveLeadScorer
    from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionService
    from ghl_real_estate_ai.services.competitive_benchmarking import CompetitiveBenchmarkingService
    from ghl_real_estate_ai.services.quality_assurance import QualityAssuranceService
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    IMPORT_ERROR = str(e)

# --- IMPORT DEMO COMPONENTS ---
try:
    from ghl_real_estate_ai.streamlit_demo.components.chat_interface import render_chat_interface
    from ghl_real_estate_ai.streamlit_demo.components.lead_dashboard import render_lead_dashboard
    from ghl_real_estate_ai.streamlit_demo.components.property_cards import render_property_matches
    from ghl_real_estate_ai.streamlit_demo.mock_services.mock_claude import MockClaudeService
    from ghl_real_estate_ai.streamlit_demo.mock_services.conversation_state import (
        init_conversation_state,
        add_message,
        update_extracted_data,
        calculate_lead_score
    )
    DEMO_COMPONENTS_AVAILABLE = True
except ImportError:
    DEMO_COMPONENTS_AVAILABLE = False

def render():
    """Main render function for the Real Estate AI module."""
    if not SERVICES_AVAILABLE:
        st.error(f"⚠️ GHL Services are not fully loaded. Some features may be disabled. Error: {IMPORT_ERROR}")
    
    ui.section_header("GHL Real Estate AI", "Institutional-grade real estate orchestration engine.")
    
    # Unified Tabs
    tabs = st.tabs([
        "🎮 Playground", 
        "📈 Dashboard", 
        "📊 Executive & ROI", 
        "🔮 Predictive",
        "🔄 Lifecycle",
        "🎯 Campaigns",
        "⚡ Bulk Ops",
        "⚙️ Admin"
    ])
    
    with tabs[0]:
        _render_playground()
        
    with tabs[1]:
        _render_analytics_dashboard()
        
    with tabs[2]:
        _render_executive_dashboard()
        
    with tabs[3]:
        _render_predictive_scoring()
        
    with tabs[4]:
        _render_lead_lifecycle()
        
    with tabs[5]:
        _render_campaign_analytics()
        
    with tabs[6]:
        _render_bulk_operations()
        
    with tabs[7]:
        _render_admin()

def _render_executive_dashboard():
    """Render executive-level strategic insights and ROI Calculator."""
    ui.section_header("Executive Strategic Insights", "Institutional-grade portfolio analysis.")
    
    # ROI Calculator Section
    with st.expander("💰 ROI & Savings Calculator", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            leads_mo = st.number_input("Monthly Leads", value=200, step=50)
        with c2:
            time_per_lead = st.number_input("Minutes per Lead (Manual)", value=15, step=5)
        with c3:
            hourly_rate = st.number_input("Support Staff Hourly Rate ($)", value=25, step=5)
            
        # Calculation
        hours_saved = (leads_mo * time_per_lead * 0.60) / 60 # Assuming 60% automation
        money_saved = hours_saved * hourly_rate
        annual_savings = money_saved * 12
        
        st.markdown(f"### 💸 Projected Savings: **${money_saved:,.0f}/mo** | **${annual_savings:,.0f}/yr**")
        st.caption(f"Based on 60% automation of {leads_mo} leads/mo")

    if not SERVICES_AVAILABLE: return

    exec_service = ExecutiveDashboardService()
    report = exec_service.get_executive_summary()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ui.card_metric("Attributed Revenue", f"${report['revenue_metrics']['total_attributed_revenue']:,.2f}", "Total Value")
    with col2:
        ui.card_metric("Portfolio Health", "94.2%", "Market Performance")
    with col3:
        ui.card_metric("AI Efficiency Gain", "32.4%", "Workflow Optimization")

    st.divider()
    st.markdown("#### 💡 Strategic Recommendations")
    for rec in report['strategic_recommendations'][:3]:
        ui.use_case_card(
            icon="🎯" if rec['priority'] == 'high' else "💡",
            title=rec['category'].upper(),
            description=f"<strong>{rec['recommendation']}</strong><br><br>Expected Impact: {rec['expected_impact']}"
        )
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

def _render_predictive_scoring():
    """Render predictive lead scoring and model analysis."""
    ui.section_header("Predictive Lead Intelligence", "Ensemble-based conversion forecasting.")
    if not SERVICES_AVAILABLE: return
    
    predictive = PredictiveLeadScorer()
    analysis = predictive.get_model_performance()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Model Performance Metrics")
        ui.card_metric("AUC-ROC Score", f"{analysis['metrics']['auc_roc']:.3f}", "Model Accuracy")
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        ui.card_metric("F1 Score", f"{analysis['metrics']['f1_score']:.3f}", "Prediction Reliability")
    
    with col2:
        st.markdown("#### Key Predictive Features")
        for feat, weight in list(analysis['feature_importance'].items())[:4]:
            st.markdown(f"""
                <div style='padding: 10px; border-radius: 8px; background-color: #f1f5f9; margin-bottom: 8px; border-left: 4px solid #10b981;'>
                    <strong>{feat}</strong>: <code>{weight:.2f}</code>
                </div>
            """, unsafe_allow_html=True)

def _render_lead_lifecycle():
    """Render lead journey and funnel analytics."""
    ui.section_header("Lead Lifecycle & Funnel", "Visualizing the path to conversion.")
    
    data = _load_mock_data()
    all_conversations = data.get("conversations", [])
    
    if all_conversations:
        df = pd.DataFrame(all_conversations)
        
        # Simulated Funnel Stages
        total = len(df)
        hot = len(df[df['classification'] == 'hot'])
        warm = len(df[df['classification'] == 'warm'])
        converted = int(hot * 0.4) # Simulated conversion from hot leads
        
        fig = go.Figure(go.Funnel(
            y = ["Total Inquiries", "Warm Leads", "Hot Leads", "Converted"],
            x = [total, warm + hot, hot, converted],
            marker = {"color": ["#94A3B8", "#3B82F6", "#10B981", "#059669"]}
        ))
        fig.update_layout(ui.get_plotly_template())
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No lifecycle data available.")

def _render_campaign_analytics():
    """Render ROI and campaign performance analytics."""
    ui.section_header("Campaign Performance & ROI", "Multi-channel marketing attribution.")
    
    col1, col2, col3 = st.columns(3)
    with col1: ui.card_metric("Campaign ROI", "342%", "+12% MoM")
    with col2: ui.card_metric("Cost Per Lead", "$14.20", "-$2.10 MoM")
    with col3: ui.card_metric("Total Spend", "$4,250", "Budget: $5k")
    
    st.divider()
    
    # Simulated Channel ROI
    channels = ['Facebook Ads', 'Google Search', 'SMS Re-engage', 'Direct Mail']
    roi_values = [280, 410, 520, 150]
    
    fig = px.bar(
        x=channels, y=roi_values,
        labels={'x': 'Channel', 'y': 'ROI %'},
        color=roi_values,
        color_continuous_scale='Emrld'
    )
    fig.update_layout(ui.get_plotly_template())
    st.plotly_chart(fig, use_container_width=True)

def _render_bulk_operations():
    """Render mass lead management and batch processing."""
    ui.section_header("Bulk Operations & Batching", "Enterprise-scale data management.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("#### ⚡ Quick Actions")
        st.button("🚀 Batch Score All Leads", use_container_width=True)
        st.button("✉️ Send Bulk Re-engagement", use_container_width=True)
        st.button("🏷️ Tag 'Cold' for Archival", use_container_width=True)
        st.divider()
        st.file_uploader("Upload CSV for Bulk Import", type=['csv'])
        
    with col2:
        st.markdown("#### 📈 Recent Bulk Jobs")
        jobs = pd.DataFrame([
            {"Job": "Batch Scoring", "Date": "2026-01-04", "Status": "Complete", "Target": "1,240 Leads"},
            {"Job": "SMS Campaign", "Date": "2026-01-03", "Status": "In Progress", "Target": "450 Contacts"},
            {"Job": "Data Export", "Date": "2026-01-02", "Status": "Complete", "Target": "Archive_Q4"}
        ])
        st.table(jobs)

def _render_admin():
    """Render system administration and multitenant management."""
    ui.section_header("System Administration", "Platform-wide configuration.")
    
    data = _load_mock_data()
    health = data.get("system_health", {})
    
    if health:
        col1, col2, col3, col4 = st.columns(4)
        with col1: ui.card_metric("System Uptime", f"{health['uptime_percentage']}%", "Stable")
        with col2: ui.card_metric("API Calls (24h)", f"{health['total_api_calls_24h']:,}", "Normal")
        with col3: ui.card_metric("Error Rate", f"{health['error_rate_percentage']}%", "Healthy")
        with col4: ui.card_metric("Token Usage", f"{health['anthropic_tokens_used_24h']:,}", "Claude 3.5")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🖥️ Server Resources")
            ui.card_metric("CPU Usage", f"{health['cpu_usage_percentage']}%", "Target < 70%")
            ui.card_metric("Memory", f"{health['memory_usage_mb']} MB", "Limit: 1GB")
        with c2:
            st.markdown("#### 📡 Integration Status")
            ui.card_metric("Active Webhooks", str(health['active_webhooks']), "GHL Connected")
            ui.card_metric("SMS Sent (24h)", str(health['sms_sent_24h']), "98% Compliant")
    else:
        st.warning("System health data unavailable.")


@st.cache_data(ttl=60)
def _load_mock_data() -> Dict[str, Any]:
    """Load mock analytics data."""
    mock_file = project_root / "ghl_real_estate_ai" / "data" / "mock_analytics.json"
    if mock_file.exists():
        with open(mock_file, "r") as f:
            return json.load(f)
    return {"tenants": [], "conversations": []}

if __name__ == "__main__":
    render()
