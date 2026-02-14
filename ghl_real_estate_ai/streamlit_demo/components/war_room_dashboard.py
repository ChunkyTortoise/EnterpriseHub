"""
Jorge War Room Dashboard - Section 4 of 2026 Strategic Roadmap
Interactive Heat Map and Relationship Graph for market dominance.
"""

import asyncio

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.services.war_room_service import get_war_room_service
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart


def render_war_room_dashboard():
    st.markdown("### 🏢 JORGE WAR ROOM: Rancho Cucamonga Market Heat")
    st.markdown("*Real-time visualization of lead clustering and conversion probability*")

    service = get_war_room_service()

    loop = asyncio.new_event_loop()
    data = run_async(service.get_market_heat_data())

    # 1. Heat Map (Geographic)
    st.markdown("#### 🗺️ Market Heat Map")
    df_nodes = pd.DataFrame([n.model_dump() for n in data.nodes])

    fig_map = px.scatter_mapbox(
        df_nodes,
        lat="lat",
        lon="lng",
        color="heat_value",
        size="leads_count",
        hover_name="address",
        hover_data=["highest_frs"],
        color_continuous_scale="Viridis",
        zoom=11,
        height=500,
    )
    fig_map.update_layout(mapbox_style="carto-darkmatter")
    st.plotly_chart(style_obsidian_chart(fig_map), use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔗 Lead-Property Relationships")
        # Simple graph visualization using Plotly
        edge_x = []
        edge_y = []
        for link in data.links:
            # Find coordinates for target prop
            target = next(n for n in data.nodes if n.id == link.target)
            # Generate random start point for lead
            edge_x.extend([random_offset(target.lng), target.lng, None])
            edge_y.extend([random_offset(target.lat), target.lat, None])

        edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color="#888"), hoverinfo="none", mode="lines")

        fig_graph = go.Figure(
            data=[edge_trace],
            layout=go.Layout(
                showlegend=False,
                hovermode="closest",
                margin=dict(b=0, l=0, r=0, t=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ),
        )
        st.plotly_chart(style_obsidian_chart(fig_graph), use_container_width=True)

    with col2:
        st.markdown("#### 🔥 Top 10 Hot Leads")
        hot_leads = [
            {"name": "Sarah Chen", "frs": 89, "timeline": "30d", "area": "Victoria Gardens"},
            {"name": "David Kim", "frs": 95, "timeline": "Immediate", "area": "Manor"},
            {"name": "Robert Williams", "frs": 76, "timeline": "45d", "area": "South Lake"},
        ]
        df_hot = pd.DataFrame(hot_leads)
        st.table(df_hot)

        st.info(
            "💡 **Strategy:** 3 leads clustered in Victoria Gardens Area. Recommend hosting a private neighborhood brief this Friday."
        )


def random_offset(val):
    import random

    return val + random.uniform(-0.02, 0.02)
