"""
ROI Calculators Module
Interactive ROI modeling for multiple verticals: Real Estate, SaaS, E-commerce, and Healthcare.
"""
import streamlit as st
import utils.ui as ui

def render():
    """Main render function for ROI Calculators."""
    ui.section_header("ROI & Growth Calculators", "Quantify the impact of AI-driven optimization across your business verticals.")
    
    vertical = st.tabs(["🏠 Real Estate", "💻 SaaS", "🛒 E-commerce", "🏥 Healthcare"])
    
    with vertical[0]:
        _render_real_estate_roi()
    
    with vertical[1]:
        _render_saas_roi()
        
    with vertical[2]:
        _render_ecommerce_roi()
        
    with vertical[3]:
        _render_healthcare_roi()

def _render_real_estate_roi():
    st.markdown("### 🏠 Real Estate AI ROI Model")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Input Variables")
        leads_pm = st.number_input("Monthly Leads", value=100, step=10, key="re_leads")
        avg_comm = st.number_input("Avg. Commission ($)", value=12500, step=500, key="re_comm")
        current_conv = st.slider("Current Lead-to-Close (%)", 0.5, 10.0, 2.0, 0.1, key="re_conv")
        ai_lift = st.slider("Expected AI Efficiency Lift (%)", 10, 100, 30, 5, key="re_lift")

    # Calculations
    current_revenue = (leads_pm * (current_conv / 100)) * avg_comm
    new_conv = current_conv * (1 + (ai_lift / 100))
    projected_revenue = (leads_pm * (new_conv / 100)) * avg_comm
    monthly_gain = projected_revenue - current_revenue
    annual_gain = monthly_gain * 12
    
    with col2:
        st.markdown("#### Financial Impact")
        ui.card_metric("Current Monthly Revenue", f"${current_revenue:,.0f}", "Baseline")
        ui.card_metric("Projected Monthly Revenue", f"${projected_revenue:,.0f}", f"+{ai_lift}% AI Lift")
        ui.card_metric("Annual Revenue Lift", f"${annual_gain:,.0f}", "Incremental Profit", delta_color="normal")
        
    st.divider()
    st.markdown("#### 📈 Conversion Funnel Impact")
    st.write(f"Your conversion rate would improve from **{current_conv}%** to **{new_conv:.2f}%** through automated 24/7 lead nurturing and instant response times.")

def _render_saas_roi():
    st.markdown("### 💻 SaaS Efficiency Model")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Operational Metrics")
        mau = st.number_input("Monthly Active Users", value=5000, step=500, key="saas_mau")
        arpu = st.number_input("ARPU ($)", value=49, step=5, key="saas_arpu")
        churn_rate = st.slider("Current Monthly Churn (%)", 1.0, 15.0, 5.0, 0.5, key="saas_churn")
        ai_reduction = st.slider("AI Churn Reduction (%)", 5, 50, 15, 5, key="saas_red")

    # Calculations
    current_mrr = mau * arpu
    churned_revenue = current_mrr * (churn_rate / 100)
    saved_revenue = churned_revenue * (ai_reduction / 100)
    annual_savings = saved_revenue * 12
    
    with col2:
        st.markdown("#### Retention Impact")
        ui.card_metric("Current MRR", f"${current_mrr:,.0f}", "Total Portfolio")
        ui.card_metric("Monthly Revenue Saved", f"${saved_revenue:,.0f}", f"{ai_reduction}% Less Churn")
        ui.card_metric("Annual ARR Retention", f"${annual_savings:,.0f}", "Recovered Growth")

def _render_ecommerce_roi():
    st.markdown("### 🛒 E-commerce Conversion Model")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Store Performance")
        traffic = st.number_input("Monthly Traffic", value=50000, step=5000, key="eco_traffic")
        aov = st.number_input("Avg. Order Value ($)", value=85, step=5, key="eco_aov")
        cr = st.slider("Current Conversion Rate (%)", 0.1, 5.0, 1.5, 0.1, key="eco_cr")
        ai_boost = st.slider("AI Personalization Boost (%)", 5, 40, 12, 1, key="eco_boost")

    # Calculations
    current_sales = (traffic * (cr / 100)) * aov
    new_cr = cr * (1 + (ai_boost / 100))
    projected_sales = (traffic * (new_cr / 100)) * aov
    monthly_lift = projected_sales - current_sales
    
    with col2:
        st.markdown("#### Growth Impact")
        ui.card_metric("Current Monthly Sales", f"${current_sales:,.0f}", "Baseline")
        ui.card_metric("Projected Monthly Sales", f"${projected_sales:,.0f}", f"+{ai_boost}% Personalization")
        ui.card_metric("Annual Sales Lift", f"${monthly_lift*12:,.0f}", "Direct AI ROI")

def _render_healthcare_roi():
    st.markdown("### 🏥 Healthcare Patient Acquisition")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Practice Metrics")
        inquiries = st.number_input("Monthly Inquiries", value=250, step=25, key="hc_inq")
        ltv = st.number_input("Patient Lifetime Value ($)", value=3500, step=100, key="hc_ltv")
        booking_rate = st.slider("Current Booking Rate (%)", 10, 60, 25, 5, key="hc_book")
        ai_improvement = st.slider("AI Response Lift (%)", 10, 50, 20, 5, key="hc_lift")

    # Calculations
    current_patients = inquiries * (booking_rate / 100)
    projected_patients = inquiries * ((booking_rate * (1 + (ai_improvement / 100))) / 100)
    patient_gain = projected_patients - current_patients
    revenue_gain = patient_gain * ltv
    
    with col2:
        st.markdown("#### Patient Volume Impact")
        ui.card_metric("Monthly New Patients", f"{current_patients:.0f}", "Current")
        ui.card_metric("Projected New Patients", f"{projected_patients:.0f}", f"+{ai_improvement}% Efficiency")
        ui.card_metric("Monthly Revenue Gain", f"${revenue_gain:,.0f}", "Incremental LTV")
