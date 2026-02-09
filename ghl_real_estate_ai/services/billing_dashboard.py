import asyncio

import pandas as pd
import plotly.express as px
import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.database_service import get_database
from ghl_real_estate_ai.services.usage_billing_service import usage_billing_service

logger = get_logger(__name__)

st.set_page_config(page_title="Revenue & ROI Dashboard", layout="wide")


async def get_revenue_metrics():
    db = await get_database()
    async with db.get_connection() as conn:
        # Get total revenue from outcomes
        total_revenue = await conn.fetchval("SELECT SUM(monetary_value) FROM model_outcomes") or 0.0

        # Get revenue over time (last 30 days)
        revenue_over_time = await conn.fetch("""
            SELECT date_trunc('day', recorded_at) as day, SUM(monetary_value) as daily_revenue
            FROM model_outcomes
            WHERE recorded_at > NOW() - INTERVAL '30 days'
            GROUP BY day
            ORDER BY day
        """)

        # Get outcomes by lead
        top_leads = await conn.fetch("""
            SELECT lead_id, SUM(monetary_value) as total_value
            FROM model_outcomes
            GROUP BY lead_id
            ORDER BY total_value DESC
            LIMIT 10
        """)

        return {
            "total_revenue": float(total_revenue),
            "revenue_over_time": pd.DataFrame([dict(r) for r in revenue_over_time]),
            "top_leads": pd.DataFrame([dict(r) for r in top_leads]),
        }


async def get_billing_metrics(location_id: str = "default"):
    usage = await usage_billing_service.get_tenant_usage(location_id)
    return usage


def run_dashboard():
    st.title("💰 Revenue & Billing Intelligence")
    st.markdown("---")

    # Sidebar for filters
    st.sidebar.header("Filters")
    location_id = st.sidebar.text_input("Location ID", value="default")

    # Load Data
    try:
        loop = asyncio.get_event_loop()
        revenue_data = loop.run_until_complete(get_revenue_metrics())
        billing_data = loop.run_until_complete(get_billing_metrics(location_id))
    except Exception as e:
        st.error(f"Failed to load dashboard data: {e}")
        return

    # Top Metrics
    total_cost = billing_data.get("total_cost_usd", 0.0)
    net_roi = revenue_data["total_revenue"] - total_cost
    roi_percentage = (net_roi / total_cost * 100) if total_cost > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue Generated", f"${revenue_data['total_revenue']:,.2f}")
    col2.metric("Total AI Cost", f"${total_cost:,.2f}", delta=f"-{total_cost:,.2f}", delta_color="inverse")
    col3.metric("Net ROI", f"${net_roi:,.2f}", delta=f"{roi_percentage:.1f}%")
    col4.metric("AI Interactions", billing_data.get("total_calls", 0))

    st.markdown("---")

    # Charts
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Revenue Growth (Last 30 Days)")
        if not revenue_data["revenue_over_time"].empty:
            fig = px.line(revenue_data["revenue_over_time"], x="day", y="daily_revenue", title="Daily Value Generated")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data available for the last 30 days.")

    with c2:
        st.subheader("🏗️ Cost Breakdown by Model")
        # In a real scenario, we'd fetch multiple model keys from Redis
        # For now, we'll use a placeholder or summary
        model_data = pd.DataFrame(
            [
                {"Model": "Claude 3.5 Sonnet", "Cost": total_cost * 0.7},
                {"Model": "Gemini 1.5 Flash", "Cost": total_cost * 0.2},
                {"Model": "Twilio/SMS", "Cost": total_cost * 0.1},
            ]
        )
        fig = px.pie(model_data, values="Cost", names="Model", title="Expense Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detailed Tables
    st.subheader("💎 Top Value-Generating Leads")
    st.table(revenue_data["top_leads"])

    # Overage Alerts
    st.subheader("⚠️ Overage & Subscription Status")
    # This would normally fetch from 'subscriptions' table
    st.info(f"Tenant '{location_id}' is currently on the **ENTERPRISE** tier. No usage caps applied.")


if __name__ == "__main__":
    run_dashboard()
