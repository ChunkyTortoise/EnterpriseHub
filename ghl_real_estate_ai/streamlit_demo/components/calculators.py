import plotly.express as px
import streamlit as st


def render_roi_calculator(selected_lead):
    st.subheader("💰 Deal Closer AI: Financial Modeler")

    # Dynamic Context from Lead Hub
    budget = selected_lead.get("budget", 500000)

    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Property Price ($)", value=budget)
        down_payment = st.slider("Down Payment (%)", 0, 100, 20)
        rate = st.number_input("Interest Rate (%)", value=6.5, step=0.1)

    # Mortgage Math
    loan_amount = price * (1 - down_payment / 100)
    monthly_rate = (rate / 100) / 12
    months = 30 * 12
    payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

    with col2:
        st.metric("Est. Monthly Payment", f"${payment:,.2f}")
        st.write(
            "**AI Recommendation:** Based on Sarah's income profile, a 15% down payment at 6.2% is the 'sweet spot' for her debt-to-income ratio."
        )


def render_revenue_funnel():
    data = dict(number=[156, 47, 23, 12, 5], stage=["Conversations", "Active Leads", "Hot Leads", "Tours", "Contracts"])
    fig = px.funnel(data, x="number", y="stage", color_discrete_sequence=["#2563eb"])
    st.plotly_chart(fig, use_container_width=True)
