import pandas as pd
import plotly.express as px
import streamlit as st


def render_financing_calculator():
    """Comprehensive financing calculator with multiple scenarios"""
    st.subheader("💰 Financing Calculator & Pre-Qualification")

    # Calculator inputs
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏠 Loan Details")
        home_price = st.number_input("Home Price", value=400000, step=5000)
        down_payment_percent = st.slider("Down Payment %", 0, 50, 20)
        loan_term = st.selectbox("Loan Term", [15, 20, 30])
        interest_rate = st.number_input("Interest Rate %", value=7.25, step=0.125)

    with col2:
        st.markdown("#### 💳 Additional Costs")
        property_tax_rate = st.number_input("Property Tax Rate %", value=2.1, step=0.1)
        insurance_annual = st.number_input("Home Insurance (Annual)", value=1200, step=100)
        hoa_monthly = st.number_input("HOA Fees (Monthly)", value=0, step=25)
        pmi_rate = st.number_input("PMI Rate % (if < 20% down)", value=0.5, step=0.1)

    # Calculate payments
    down_payment = home_price * (down_payment_percent / 100)
    loan_amount = home_price - down_payment

    # Monthly payment calculation
    monthly_rate = (interest_rate / 100) / 12
    num_payments = loan_term * 12

    if monthly_rate > 0:
        monthly_principal_interest = (
            loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        )
    else:
        monthly_principal_interest = loan_amount / num_payments

    monthly_tax = (home_price * (property_tax_rate / 100)) / 12
    monthly_insurance = insurance_annual / 12
    monthly_pmi = (loan_amount * (pmi_rate / 100)) / 12 if down_payment_percent < 20 else 0

    total_monthly = monthly_principal_interest + monthly_tax + monthly_insurance + hoa_monthly + monthly_pmi

    # Display results
    st.markdown("#### 📊 Payment Breakdown")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Monthly Payment", f"${total_monthly:,.0f}")
    with col2:
        st.metric("🏠 Principal & Interest", f"${monthly_principal_interest:,.0f}")
    with col3:
        st.metric("🏛️ Taxes & Insurance", f"${monthly_tax + monthly_insurance:,.0f}")
    with col4:
        st.metric("💵 Down Payment", f"${down_payment:,.0f}")

    # Payment breakdown chart
    payment_data = {
        "Component": ["Principal & Interest", "Property Tax", "Insurance", "HOA", "PMI"],
        "Amount": [monthly_principal_interest, monthly_tax, monthly_insurance, hoa_monthly, monthly_pmi],
    }

    df = pd.DataFrame(payment_data)
    df = df[df["Amount"] > 0]  # Only show components with values

    fig = px.pie(df, values="Amount", names="Component", title="Monthly Payment Breakdown")
    st.plotly_chart(fig, use_container_width=True)

    # Affordability analysis
    st.markdown("#### 🎯 Affordability Analysis")

    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.number_input("Gross Monthly Income", value=8000, step=500)
        monthly_debts = st.number_input("Monthly Debt Payments", value=800, step=100)

    debt_to_income = ((total_monthly + monthly_debts) / monthly_income) * 100

    with col2:
        st.metric("📈 Total DTI Ratio", f"{debt_to_income:.1f}%")

        if debt_to_income <= 28:
            st.success("✅ Excellent DTI - Strong approval likelihood")
        elif debt_to_income <= 36:
            st.warning("⚠️ Good DTI - Should qualify with good credit")
        elif debt_to_income <= 43:
            st.warning("⚠️ High DTI - May need stronger compensating factors")
        else:
            st.error("❌ Very High DTI - May have difficulty qualifying")

    # Scenario comparison
    st.markdown("#### 🔍 Scenario Comparison")

    scenarios = []
    for dp in [10, 15, 20, 25]:
        scenario_down = home_price * (dp / 100)
        scenario_loan = home_price - scenario_down
        scenario_pmi = (scenario_loan * 0.005) / 12 if dp < 20 else 0
        scenario_payment = (
            scenario_loan
            * (monthly_rate * (1 + monthly_rate) ** num_payments)
            / ((1 + monthly_rate) ** num_payments - 1)
            + monthly_tax
            + monthly_insurance
            + hoa_monthly
            + scenario_pmi
        )

        scenarios.append(
            {
                "Down Payment %": f"{dp}%",
                "Down Payment $": f"${scenario_down:,.0f}",
                "Monthly Payment": f"${scenario_payment:,.0f}",
                "PMI": f"${scenario_pmi:,.0f}" if scenario_pmi > 0 else "None",
            }
        )

    scenario_df = pd.DataFrame(scenarios)
    st.dataframe(scenario_df, use_container_width=True)
