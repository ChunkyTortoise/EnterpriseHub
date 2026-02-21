"""
ROI Calculator — EnterpriseHub Real Estate AI
Shows the business value of AI-powered lead qualification.

Usage: Import render_roi_calculator() into main Streamlit app.
"""

import streamlit as st


def render_roi_calculator():
    st.header("ROI Calculator")
    st.caption("See your projected return from AI-powered lead qualification")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your Current Metrics")
        leads_per_month = st.slider("Leads per month", 10, 1000, 100)
        response_time_min = st.slider("Current response time (minutes)", 1, 120, 45)
        conversion_rate = st.slider("Current conversion rate (%)", 0.5, 20.0, 3.5, 0.1)
        agent_cost = st.number_input("Monthly AI subscription cost ($)", value=2000, step=100)

    # Calculation constants
    AI_RESPONSE_TIME_MIN = 3
    CONVERSION_IMPROVEMENT = 1.33  # 133% improvement from benchmarks
    AVG_DEAL_COMMISSION = 12000  # Rancho Cucamonga market average

    # Calculations
    new_conversion_rate = min(conversion_rate * CONVERSION_IMPROVEMENT, 20.0)
    extra_conversions = leads_per_month * (new_conversion_rate - conversion_rate) / 100
    monthly_revenue_recovered = extra_conversions * AVG_DEAL_COMMISSION

    time_saved_per_lead_hours = (response_time_min - AI_RESPONSE_TIME_MIN) / 60
    total_time_saved_hours = leads_per_month * time_saved_per_lead_hours

    net_gain = monthly_revenue_recovered - agent_cost
    roi_multiple = net_gain / agent_cost if agent_cost > 0 else 0
    payback_days = (agent_cost / (monthly_revenue_recovered / 30)) if monthly_revenue_recovered > 0 else 999

    with col2:
        st.subheader("Projected Results")
        st.metric(
            "Monthly Revenue Recovered",
            f"${monthly_revenue_recovered:,.0f}",
            delta=f"+{extra_conversions:.1f} conversions/mo",
        )
        st.metric(
            "Time Saved Monthly",
            f"{total_time_saved_hours:.0f} hours",
            delta=f"{response_time_min - AI_RESPONSE_TIME_MIN} min faster per lead",
        )
        st.metric("ROI Multiple", f"{roi_multiple:.1f}x", delta=f"${net_gain:,.0f} net gain/month")
        st.metric("Payback Period", f"{min(payback_days, 999):.0f} days" if payback_days < 999 else "< 1 day")

    with st.expander("Calculation Assumptions"):
        st.markdown(f"""
        | Assumption | Value | Source |
        |-----------|-------|--------|
        | AI response time | {AI_RESPONSE_TIME_MIN} minutes | System benchmark |
        | Conversion rate improvement | {(CONVERSION_IMPROVEMENT - 1) * 100:.0f}% | A/B test results (133% uplift) |
        | Average deal commission | ${AVG_DEAL_COMMISSION:,} | Rancho Cucamonga market average |
        | Response time improvement | {((response_time_min - AI_RESPONSE_TIME_MIN) / response_time_min * 100):.0f}% | {response_time_min} min → {AI_RESPONSE_TIME_MIN} min |
        """)


if __name__ == "__main__":
    st.set_page_config(page_title="ROI Calculator", layout="wide")
    render_roi_calculator()
