"""
Segmentation Pulse Dashboard Component
Enhanced data visualization for Smart Segmentation with KPI ribbon and distribution chart
"""

from typing import Any, Dict

import plotly.graph_objects as go
import streamlit as st


def render_segmentation_pulse(segment_data: Dict[str, Any]):
    """
    Render the enhanced Segmentation Pulse dashboard with Obsidian Command styling.
    """

    # Extract metrics from segment data
    char = segment_data.get("characteristics", {})

    # KPI Ribbon - Obsidian Metric Cards
    st.markdown("### 📊 SEGMENTATION TELEMETRY")

    col1, col2, col3, col4 = st.columns(4)

    card_style = "background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); backdrop-filter: blur(12px);"

    with col1:
        st.markdown(
            f"""
        <div style='{card_style}'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: rgba(34, 197, 94, 0.1); border-radius: 10px; font-size: 1.5rem; line-height: 1;'>📈</div>
                <span style='color: #22c55e; font-size: 0.75rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>+12%</span>
            </div>
            <p style='font-size: 0.8rem; color: #8B949E; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif;'>Avg Engagement</p>
            <h3 style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0; font-family: "Space Grotesk", sans-serif;'>{char.get("avg_engagement", 0)}%</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style='{card_style}'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: rgba(99, 102, 241, 0.1); border-radius: 10px; font-size: 1.5rem; line-height: 1;'>🎯</div>
                <span style='color: #6366F1; font-size: 0.75rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>+5.2</span>
            </div>
            <p style='font-size: 0.8rem; color: #8B949E; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif;'>Avg Lead Score</p>
            <h3 style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0; font-family: "Space Grotesk", sans-serif;'>{char.get("avg_lead_score", 0):.1f}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        total_value = char.get("total_value", 0)
        st.markdown(
            f"""
        <div style='{card_style}'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: rgba(16, 185, 129, 0.1); border-radius: 10px; font-size: 1.5rem; line-height: 1;'>💰</div>
                <span style='color: #10b981; font-size: 0.75rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>+$2.4M</span>
            </div>
            <p style='font-size: 0.8rem; color: #8B949E; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif;'>Total Value</p>
            <h3 style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0; font-family: "Space Grotesk", sans-serif;'>${total_value:,.0f}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        segment_size = segment_data.get("size", 0)
        st.markdown(
            f"""
        <div style='{card_style}'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: rgba(255, 255, 255, 0.05); border-radius: 10px; font-size: 1.5rem; line-height: 1;'>👥</div>
                <span style='color: #8B949E; font-size: 0.75rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>+4 today</span>
            </div>
            <p style='font-size: 0.8rem; color: #8B949E; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif;'>Segment Size</p>
            <h3 style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0; font-family: "Space Grotesk", sans-serif;'>{segment_size} Leads</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Lead Score Distribution Chart
    render_lead_score_distribution()

    # Quick Actions
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("📧 Send Campaign to Segment", use_container_width=True):
            with st.spinner("Queueing campaign workflow..."):
                import time

                time.sleep(1.5)
                st.toast("Campaign 'Luxury Outreach' started!", icon="🚀")
                st.success("Campaign queued for this segment!")

    with col_b:
        if st.button("📊 View All Leads", use_container_width=True):
            st.info("Opening lead details...")

    with col_c:
        # Export functionality with segment-specific data
        import pandas as pd

        export_data = {
            "Metric": ["Avg Engagement", "Avg Lead Score", "Total Value", "Segment Size"],
            "Value": [
                f"{char.get('avg_engagement', 0)}%",
                f"{char.get('avg_lead_score', 0):.1f}",
                f"${char.get('total_value', 0):,.0f}",
                f"{segment_size}",
            ],
            "Trend": ["+12%", "+5.2", "+$2.4M", "+4 today"],
        }
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Export Segment CSV",
            data=csv,
            file_name=f"segment_{segment_data.get('name', 'data')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_lead_score_distribution():
    """Render interactive lead score distribution bar chart with Obsidian styling"""
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

    # Mock distribution data
    distribution_data = {"0-20": 3, "21-40": 8, "41-60": 15, "61-80": 22, "81-100": 14}

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=list(distribution_data.keys()),
            y=list(distribution_data.values()),
            marker=dict(color="#6366F1", line=dict(color="rgba(255,255,255,0.1)", width=1)),
            hovertemplate="<b>Score Range: %{x}</b><br>Leads: %{y}<extra></extra>",
            text=list(distribution_data.values()),
            textposition="outside",
            textfont=dict(color="#FFFFFF", family="Space Grotesk"),
        )
    )

    fig.update_layout(
        title={
            "text": "<b>LEAD SCORE DISTRIBUTION</b>",
            "font": {"size": 18, "color": "#FFFFFF", "family": "Space Grotesk"},
        },
        xaxis_title="SCORE RANGE",
        yaxis_title="LEADS",
        bargap=0.3,
    )

    st.plotly_chart(style_obsidian_chart(fig), use_container_width=True, key="lead_score_dist")

    # Insights below chart
    col_i1, col_i2, col_i3 = st.columns(3)

    insight_style = "background: rgba(22, 27, 34, 0.6); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid"

    with col_i1:
        st.markdown(
            f"""
        <div style='{insight_style} #6366F1;'>
            <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; margin-bottom: 0.25rem; text-transform: uppercase; font-family: "Space Grotesk", sans-serif;'>PEAK RANGE</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>61-80 Range</div>
            <div style='font-size: 0.75rem; color: #6366F1; margin-top: 0.25rem; font-weight: 600;'>22 nodes ready to sync</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_i2:
        st.markdown(
            f"""
        <div style='{insight_style} #f59e0b;'>
            <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; margin-bottom: 0.25rem; text-transform: uppercase; font-family: "Space Grotesk", sans-serif;'>NURTURE REQUIRED</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>21-60 Range</div>
            <div style='font-size: 0.75rem; color: #f59e0b; margin-top: 0.25rem; font-weight: 600;'>23 nodes pending signal</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_i3:
        st.markdown(
            f"""
        <div style='{insight_style} #10b981;'>
            <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; margin-bottom: 0.25rem; text-transform: uppercase; font-family: "Space Grotesk", sans-serif;'>OPTIMAL ZONE</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>81-100 Range</div>
            <div style='font-size: 0.75rem; color: #10b981; margin-top: 0.25rem; font-weight: 600;'>14 nodes at terminal velocity</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
