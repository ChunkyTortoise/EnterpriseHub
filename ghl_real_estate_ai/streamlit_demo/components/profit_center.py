"""
Profit Center Component - ROI & Value Generation Analytics
Visualizes the financial impact of AI swarm operations.
"""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from ghl_real_estate_ai.services.roi_engine import roi_engine


def render_profit_center():
    """
    Renders the Profit Center view showing cumulative ROI from AI operations.
    """
    st.markdown(
        """
    <div style="background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
                padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            💎 AI Profit Center
        </h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; opacity: 0.9;">
            Predictive ROI & Value Generation Analytics
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get cumulative ROI data (Mocked for now based on roi_engine constants)
    # In production, this would query the database/blackboard history
    stats = {
        "tasks_completed": 1240,
        "matches_found": 86,
    }
    metrics = roi_engine.calculate_swarm_roi(stats, agent_name="ProfitCenterUI")

    # Top-level metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Value Generated", f"${metrics['total_value_generated']:,.2f}", delta="+14.2% vs last month")
    with col2:
        st.metric(
            "Time Saved (Human Hours)",
            f"{metrics['time_saved_hours']:.1f} hrs",
            delta=f"${metrics['time_saved_value']:,.2f} value",
        )
    with col3:
        st.metric(
            "Revenue Lift (Est.)",
            f"${metrics['conversion_lift_value']:,.2f}",
            delta=f"{metrics['matches_found']} matches",
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cumulative Value Growth")
        # Generate some growth data
        dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
        values = [5000 + (x * 200) + (x**1.5 * 10) for x in range(30)]

        df = pd.DataFrame({"Date": dates, "Value": values})
        fig = px.area(df, x="Date", y="Value", title="Value Generated Over Time")
        fig.update_traces(line_color="#38ef7d")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Value Attribution by Agent")
        agent_data = {
            "Agent": ["Property Matcher", "Lead Scorer", "Follow-up Engine", "Negotiation Partner"],
            "Value": [15000, 8000, 12000, 5000],
        }
        fig_agents = px.pie(
            agent_data,
            values="Value",
            names="Agent",
            title="Value Distribution",
            color_discrete_sequence=px.colors.sequential.Greens_r,
        )
        fig_agents.update_layout(height=400)
        st.plotly_chart(fig_agents, use_container_width=True)

    # Detailed Breakdown
    st.markdown("#### ROI Breakdown by Task Category")
    category_data = {
        "Category": ["Lead Qualification", "Property Matching", "Automated Outreach", "Data Enrichment"],
        "Hours Saved": [450, 320, 280, 190],
        "Value Generated": [22500, 35000, 14000, 9500],
    }
    cat_df = pd.DataFrame(category_data)
    st.table(cat_df)

    # Future Projections
    st.info(
        "💡 **AI Insight**: Based on current lead velocity, the system is projected to generate an additional **$12,400** in value over the next 30 days."
    )


if __name__ == "__main__":
    render_profit_center()
