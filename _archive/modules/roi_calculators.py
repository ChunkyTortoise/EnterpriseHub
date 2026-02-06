"""
ROI Calculators Module
Interactive ROI modeling based on the Professional Services Catalog 2026.
"""
import streamlit as st
import utils.ui as ui
from utils.roi_logic import (
    calculate_automation_roi,
    calculate_data_roi,
    calculate_marketing_roi,
    calculate_strategic_roi
)

def render():
    """Main render function for ROI Calculators."""
    # ui.section_header("ROI & Growth Calculators", "Quantify the impact of AI-driven optimization.")
    
    tab = st.tabs(["🤖 Automation ROI", "📊 BI & Data ROI", "📈 Marketing ROI", "🏢 Strategic ROI"])
    
    with tab[0]:
        _render_automation_roi()
    
    with tab[1]:
        _render_data_roi()
        
    with tab[2]:
        _render_marketing_roi()
        
    with tab[3]:
        _render_strategic_roi()

def _render_automation_roi():
    st.markdown("### 🤖 Intelligent Automation ROI (Services 3, 4, 6)")
    col1, col2 = st.columns([1, 1])
    
        with col1:
    
            st.markdown("#### Scenario: Agency Lead Research")
    
            leads_day = st.number_input("Leads per Day", value=200, step=50)
    
            hours_per_lead = st.number_input("Manual Hours per Lead", value=2.0, step=0.5)
    
            hourly_rate = st.number_input("Staff Hourly Rate ($)", value=50, step=10)
    
            automation_pct = st.slider("Automation Percentage (%)", 50, 95, 85)
    
    
    
        # Calculations from Service 4 model
    
        results = calculate_automation_roi(leads_day, hours_per_lead, hourly_rate, automation_pct)
    
        hours_saved = results["hours_saved"]
    
        weekly_savings = results["weekly_savings"]
    
        annual_savings = results["annual_savings"]
    
        
    
        with col2:
    
            st.markdown("#### Financial Impact")
    
            ui.card_metric("Weekly Hours Saved", f"{hours_saved:,.0f} hrs", f"{automation_pct}% Efficiency")
    
            ui.card_metric("Weekly Savings", f"${weekly_savings:,.0f}", "Labor Recovery")
    
            ui.card_metric("Annual Revenue Lift", f"${annual_savings:,.0f}", "Projected 12mo ROI", delta_color="normal")
    
            
    
        st.info("💡 **Catalog Ref:** Service 4 (Multi-Agent Swarms) typical ROI: 10,450%. Based on 340 hours saved per week.")
    
    
    
    def _render_data_roi():
    
        st.markdown("### 📊 Business Intelligence & Data ROI (Services 8, 9, 11)")
    
        col1, col2 = st.columns([1, 1])
    
        
    
        with col1:
    
            st.markdown("#### Scenario: SaaS Churn Reduction")
    
            arr = st.number_input("Annual Recurring Revenue ($M)", value=5.0, step=1.0)
    
            churn_rate = st.slider("Current Annual Churn (%)", 5, 25, 12)
    
            ai_reduction = st.slider("AI-Driven Churn Reduction (%)", 5, 50, 20)
    
    
    
        # Calculations from Service 8 model
    
        results = calculate_data_roi(arr, churn_rate, ai_reduction)
    
        churn_loss = results["churn_loss"]
    
        recovered_revenue = results["recovered_revenue"]
    
        
    
        with col2:
    
            st.markdown("#### Retention Impact")
    
            ui.card_metric("Annual Churn Loss", f"${churn_loss/1000:,.0f}K", "Revenue Leakage")
    
            ui.card_metric("Recovered Revenue", f"${recovered_revenue/1000:,.0f}K", f"{ai_reduction}% Reduction")
    
            ui.card_metric("Payback Period", "1.2 Weeks", "Service S8")
    
    
    
        st.divider()
    
        st.markdown("#### Scenario: Automated Reporting (Service 9)")
    
        c1, c2 = st.columns(2)
    
        with c1:
    
            staff_time = st.number_input("Hours per week on manual Excel", value=4.0, step=1.0)
    
        with c2:
    
            ui.card_metric("Annual Time Saved", f"{staff_time * 52:,.0f} hrs", "Zero-Touch Pipelines")
    
    
    
    def _render_marketing_roi():
    
        st.markdown("### 📈 Growth & Marketing ROI (Services 12, 16)")
    
        col1, col2 = st.columns([1, 1])
    
        
    
        with col1:
    
            st.markdown("#### Scenario: Programmatic SEO (S12)")
    
            posts_count = st.number_input("AI Articles Published", value=200, step=50)
    
            traffic_per_post = st.number_input("Monthly Traffic per Post", value=100, step=20)
    
            conv_rate = st.slider("Conversion Rate (%)", 0.1, 5.0, 0.5, 0.1)
    
            ltv = st.number_input("Customer LTV ($)", value=2000, step=500)
    
    
    
        # Calculations from Service 12 model
    
        results = calculate_marketing_roi(posts_count, traffic_per_post, conv_rate, ltv)
    
        total_traffic = results["total_traffic"]
    
        conversions = results["conversions"]
    
        monthly_value = results["monthly_value"]
    
        
    
        with col2:
    
            st.markdown("#### SEO Value Engine")
    
            ui.card_metric("Monthly Traffic", f"{total_traffic:,.0f}", "Organic Reach")
    
            ui.card_metric("Monthly Conversions", f"{conversions:,.0f}", f"{conv_rate}% Conv")
    
            ui.card_metric("Annualized Value", f"${monthly_value * 12 / 1000000:.1f}M", "Projected Growth")
    
    
    
    def _render_strategic_roi():
    
        st.markdown("### 🏢 Strategic AI Leadership (Service 25)")
    
        
    
        col1, col2 = st.columns(2)
    
        with col1:
    
            budget = st.number_input("Annual AI Budget ($)", value=300000, step=50000)
    
            waste_pct = st.slider("Estimated Strategy Mismatch (%)", 10, 50, 30)
    
            
    
        results = calculate_strategic_roi(budget, waste_pct)
    
        prevented_waste = results["prevented_waste"]
    
        
    
        with col2:
    
            ui.animated_metric("Prevented Waste", f"${prevented_waste:,.0f}", "Fractional Oversight")
    
            st.info("Fractional AI Leadership (S25) typically pays for itself by consolidating redundant projects and accelerating time-to-value by 30-40%.")
    
    