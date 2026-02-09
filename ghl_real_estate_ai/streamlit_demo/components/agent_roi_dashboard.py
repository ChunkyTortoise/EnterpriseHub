"""
Agent ROI Dashboard - Lead-to-Close Attribution + Profitability
Helps GHL agencies see the clear ROI on their AI bot investment.
"""


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_agent_roi_dashboard():
    """
    Renders the Agent ROI Dashboard.
    Pillar 3: SaaS Monetization
    Feature #4: Automated ROI Dashboard for Agents
    """
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import render_dossier_block, style_obsidian_chart

    st.markdown(
        """
        <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">💰 AGENT ROI COMMAND</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Real-time lead-to-close attribution and profitability engine</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(16, 185, 129, 0.1); color: #10B981; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(16, 185, 129, 0.3); letter-spacing: 0.1em;">
                    ROI MULTIPLIER: 12.4x
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total AI Investment", "$1,200", "-$300 (Optimized)")
    with k2:
        st.metric("Qualified Leads", "142", "+24%")
    with k3:
        st.metric("Closed Commissions", "$14,800", "+12%")
    with k4:
        st.metric("Cost Per Qual. Lead", "$8.45", "-15%")

    st.markdown("---")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("#### 📈 ATTRIBUTION FUNNEL")

        # Funnel data
        funnel_data = dict(
            number=[1200, 450, 142, 38, 12],
            stage=["Conversations", "Engaged Leads", "Qualified Nodes", "Tours Scheduled", "Closed Deals"],
        )
        fig_funnel = px.funnel(funnel_data, x="number", y="stage", color_discrete_sequence=["#6366F1"])
        st.plotly_chart(style_obsidian_chart(fig_funnel), use_container_width=True)

        st.markdown("#### 📊 COMMISSION VS. AI COST (6 MONTHS)")
        # Time series data
        months = ["Aug", "Sept", "Oct", "Nov", "Dec", "Jan"]
        commissions = [8500, 11200, 9800, 13500, 12100, 14800]
        ai_costs = [1500, 1450, 1400, 1300, 1250, 1200]

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(x=months, y=commissions, name="Commissions ($)", line=dict(color="#10B981", width=4))
        )
        fig_trend.add_trace(
            go.Scatter(x=months, y=ai_costs, name="AI Spend ($)", line=dict(color="#EF4444", width=2, dash="dot"))
        )
        st.plotly_chart(style_obsidian_chart(fig_trend), use_container_width=True)

    with col_side:
        st.markdown("#### 🤖 BOT PERFORMANCE BREAKDOWN")

        # Bot type comparison
        bot_types = ["Buyer Bot", "Seller Bot", "Re-engagement"]
        yields = [45, 62, 35]  # Leads per $100 spent

        fig_bots = px.pie(
            values=yields, names=bot_types, hole=0.4, color_discrete_sequence=["#6366F1", "#8B5CF6", "#10B981"]
        )
        st.plotly_chart(style_obsidian_chart(fig_bots), use_container_width=True)

        st.markdown("#### 🎯 TOP CLOSING PERSONAS")
        persona_data = pd.DataFrame(
            {"Persona": ["Tech Prof.", "Investor", "First-Time", "Downsizer"], "Conversion": [92, 85, 64, 78]}
        )
        st.dataframe(persona_data, hide_index=True, use_container_width=True)

        render_dossier_block(
            """
        **Strategic Insight:** Your 'Seller Bot' has 40% higher ROI than the industry average. 
        Re-engagement engine recovered 12 deals this month ($3,400 in found commission).
        """,
            title="CLAUDE'S PROFITABILITY ANALYSIS",
        )

    st.markdown("---")
    st.markdown("#### 📑 RECENTLY CLOSED ATTRIBUTION")
    # Sample deals
    deals = [
        {"Lead": "Sarah Chen", "Bot": "Buyer", "Investment": "$12", "Revenue": "$1,450", "ROI": "120x"},
        {"Lead": "David Kim", "Bot": "Seller", "Investment": "$18", "Revenue": "$2,800", "ROI": "155x"},
        {"Lead": "Mike Rodriguez", "Bot": "Re-engage", "Investment": "$5", "Revenue": "$1,100", "ROI": "220x"},
    ]
    st.table(deals)
