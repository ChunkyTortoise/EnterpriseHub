"""EnterpriseHub ROI Calculator — Streamlit Application.

Helps real estate teams quantify the financial impact of deploying
EnterpriseHub vs. manual lead management.
"""

import streamlit as st

st.set_page_config(
    page_title="EnterpriseHub ROI Calculator",
    page_icon="📊",
    layout="wide",
)

# --- Header ---
st.title("EnterpriseHub ROI Calculator")
st.markdown(
    "Calculate your return on AI-powered lead management. "
    "Adjust the inputs below to see projected savings for your agency."
)
st.divider()

# --- Input Sections ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Lead Volume")
    leads_per_month = st.number_input(
        "Monthly inbound leads",
        min_value=10,
        max_value=10_000,
        value=100,
        step=10,
    )
    current_response_time_min = st.number_input(
        "Current avg response time (minutes)",
        min_value=5,
        max_value=480,
        value=45,
        step=5,
    )
    agents_count = st.number_input(
        "Number of human agents",
        min_value=1,
        max_value=100,
        value=5,
    )

    st.subheader("Current Costs")
    agent_hourly_rate = st.number_input(
        "Agent hourly cost ($)",
        min_value=10,
        max_value=100,
        value=25,
        step=5,
    )
    current_monthly_api_cost = st.number_input(
        "Current LLM / API costs ($/month)",
        min_value=0,
        max_value=50_000,
        value=3_600,
        step=100,
    )
    time_per_lead_min = st.number_input(
        "Minutes spent per lead (current)",
        min_value=5,
        max_value=120,
        value=45,
        step=5,
    )

with col_right:
    st.subheader("Financial Metrics")
    avg_deal_value = st.number_input(
        "Average deal close value ($)",
        min_value=1_000,
        max_value=10_000_000,
        value=50_000,
        step=5_000,
    )
    current_conversion_rate = st.slider(
        "Current lead-to-close rate (%)",
        min_value=1,
        max_value=50,
        value=12,
    )
    commission_rate = st.slider(
        "Commission rate (%)",
        min_value=1.0,
        max_value=6.0,
        value=3.0,
        step=0.5,
    )

    st.subheader("Deployment Package")
    PACKAGES = {
        "Lead Audit ($1,500)": 1_500,
        "Jorge Bot Lite ($5,000)": 5_000,
        "Jorge Bot Pro ($10,000)": 10_000,
        "Revenue Engine ($15,000)": 15_000,
    }
    package = st.selectbox(
        "Select package",
        options=list(PACKAGES.keys()),
        index=2,
    )
    investment = PACKAGES[package]

# --- Calculations ---

# 1. Time savings
current_hours_per_month = leads_per_month * time_per_lead_min / 60
automated_hours_per_month = leads_per_month * 2 / 60  # 2 min with EnterpriseHub
hours_saved_per_month = current_hours_per_month - automated_hours_per_month
labor_savings_per_month = hours_saved_per_month * agent_hourly_rate

# 2. Conversion improvement (proven 133% increase, i.e. 2.33x multiplier)
new_conversion_rate = min(current_conversion_rate * 2.33, 50.0)
current_deals_per_month = leads_per_month * (current_conversion_rate / 100)
new_deals_per_month = leads_per_month * (new_conversion_rate / 100)
additional_deals = new_deals_per_month - current_deals_per_month
additional_revenue = additional_deals * avg_deal_value
additional_commission = additional_revenue * (commission_rate / 100)

# 3. API cost savings (89% reduction via 3-tier caching)
api_savings_per_month = current_monthly_api_cost * 0.89

# 4. Totals
total_monthly_savings = labor_savings_per_month + additional_commission + api_savings_per_month
annual_savings = total_monthly_savings * 12
roi_percentage = ((annual_savings - investment) / investment) * 100 if investment > 0 else 0
payback_months = investment / total_monthly_savings if total_monthly_savings > 0 else float("inf")

# --- Results ---
st.divider()
st.header("Your Projected Results")

# Key metrics row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Savings", f"${total_monthly_savings:,.0f}")
m2.metric("Annual ROI", f"{roi_percentage:,.0f}%")
payback_label = "< 1 month" if payback_months < 1 else f"{payback_months:.1f} months"
m3.metric("Payback Period", payback_label)
m4.metric("Additional Deals / Month", f"+{additional_deals:.1f}")

st.divider()

# Savings breakdown
st.subheader("Savings Breakdown (Monthly)")

breakdown_col, chart_col = st.columns([1, 2])

with breakdown_col:
    st.markdown(f"**Labor savings**: ${labor_savings_per_month:,.0f}")
    st.markdown(f"**Additional commission**: ${additional_commission:,.0f}")
    st.markdown(f"**API cost savings**: ${api_savings_per_month:,.0f}")
    st.markdown(f"---")
    st.markdown(f"**Total**: ${total_monthly_savings:,.0f} / month")

with chart_col:
    chart_data = {
        "Category": ["Labor Savings", "Additional Commission", "API Cost Savings"],
        "Amount": [labor_savings_per_month, additional_commission, api_savings_per_month],
    }
    st.bar_chart(chart_data, x="Category", y="Amount", color="#4CAF50")

st.divider()

# Before / After comparison
st.subheader("Before vs. After Comparison")

response_reduction = ((current_response_time_min - 2) / current_response_time_min * 100) if current_response_time_min > 0 else 0
conversion_improvement = ((new_conversion_rate - current_conversion_rate) / current_conversion_rate * 100) if current_conversion_rate > 0 else 0
current_monthly_revenue = current_deals_per_month * avg_deal_value
new_monthly_revenue = new_deals_per_month * avg_deal_value
reduced_api_cost = current_monthly_api_cost * 0.11
time_reduction = ((time_per_lead_min - 2) / time_per_lead_min * 100) if time_per_lead_min > 0 else 0

comparison_data = {
    "Metric": [
        "Response time",
        "Conversion rate",
        "Deals per month",
        "Monthly revenue",
        "API costs",
        "Time per lead",
    ],
    "Before": [
        f"{current_response_time_min} min",
        f"{current_conversion_rate}%",
        f"{current_deals_per_month:.1f}",
        f"${current_monthly_revenue:,.0f}",
        f"${current_monthly_api_cost:,.0f}",
        f"{time_per_lead_min} min",
    ],
    "After (EnterpriseHub)": [
        "2 min",
        f"{new_conversion_rate:.1f}%",
        f"{new_deals_per_month:.1f}",
        f"${new_monthly_revenue:,.0f}",
        f"${reduced_api_cost:,.0f}",
        "2 min",
    ],
    "Change": [
        f"-{response_reduction:.0f}%",
        f"+{conversion_improvement:.0f}%",
        f"+{additional_deals:.1f}",
        f"+${new_monthly_revenue - current_monthly_revenue:,.0f}",
        "-89%",
        f"-{time_reduction:.0f}%",
    ],
}

st.table(comparison_data)

st.divider()

# Investment summary
st.subheader("Investment Summary")

s1, s2 = st.columns(2)

with s1:
    st.markdown(f"**Package**: {package}")
    st.markdown(f"**Investment**: ${investment:,.0f}")
    st.markdown(f"**Monthly savings**: ${total_monthly_savings:,.0f}")

with s2:
    st.markdown(f"**Payback period**: {payback_label}")
    st.markdown(f"**12-month ROI**: {roi_percentage:,.0f}%")
    net_savings = annual_savings - investment
    st.markdown(f"**12-month net savings**: ${net_savings:,.0f}")

st.divider()

# CTA
st.subheader("Ready to see these results for your business?")

cta1, cta2, cta3 = st.columns(3)
with cta1:
    st.link_button(
        "Book a Discovery Call (Free)",
        "https://calendly.com/caymanroden/discovery-call",
        use_container_width=True,
    )
with cta2:
    st.link_button(
        "Email Us",
        "mailto:caymanroden@gmail.com?subject=EnterpriseHub%20ROI%20Inquiry",
        use_container_width=True,
    )
with cta3:
    st.link_button(
        "View GitHub Repository",
        "https://github.com/ChunkyTortoise/EnterpriseHub",
        use_container_width=True,
    )

# Footer
st.divider()
st.caption(
    "Calculations based on validated EnterpriseHub benchmarks (Feb 2026): "
    "89% token cost reduction, 133% conversion improvement, 2-minute response time. "
    "Actual results may vary based on implementation and market conditions."
)
