"""
Executive Command Center - Real-time dashboard for Jorge
Beautiful, actionable, single-pane-of-glass view
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import streamlit as st


def render_executive_dashboard(mock_data: bool = True):
    """
    Render the Executive Command Center dashboard - Obsidian Command Edition.
    """
    from ghl_real_estate_ai.streamlit_demo.components.primitives import ICONS, CardConfig, icon, render_obsidian_card
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

    st.markdown("# 🎯 EXECUTIVE COMMAND")
    st.markdown("**Real-time tactical intelligence across the enterprise**")
    st.markdown("---")

    # Top-level metrics row - Obsidian Edition
    col1, col2, col3, col4, col5 = st.columns(5)

    metric_card_style = "padding: 20px; border-radius: 12px; color: #FFFFFF; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); backdrop-filter: blur(12px);"

    with col1:
        render_obsidian_card(
            title="HOT LEADS",
            content="""
            <div style='font-size: 2.75rem; font-weight: 700; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>3</div>
            <div style='font-size: 0.8rem; opacity: 0.7; font-weight: 600;'>+2 SINCE BASELINE</div>
            """,
            config=CardConfig(variant="alert", glow_color="#10b981", padding="20px"),
            icon="fire",
        )

    with col2:
        render_obsidian_card(
            title="WARM LEADS",
            content="""
            <div style='font-size: 2.75rem; font-weight: 700; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>8</div>
            <div style='font-size: 0.8rem; opacity: 0.7; font-weight: 600;'>READY FOR SYNC</div>
            """,
            config=CardConfig(variant="alert", glow_color="#f59e0b", padding="20px"),
            icon="bolt",
        )

    with col3:
        render_obsidian_card(
            title="PIPELINE",
            content="""
            <div style='font-size: 2.75rem; font-weight: 700; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>$2.4M</div>
            <div style='font-size: 0.8rem; opacity: 0.7; font-weight: 600;'>PROJECTED YIELD</div>
            """,
            config=CardConfig(variant="premium", padding="20px"),
            icon="dollar-sign",
        )

    with col4:
        render_obsidian_card(
            title="LATENCY",
            content="""
            <div style='font-size: 2.75rem; font-weight: 700; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>2.3m</div>
            <div style='font-size: 0.8rem; opacity: 0.7; font-weight: 600;'>AI RESPONSE TIME</div>
            """,
            config=CardConfig(variant="alert", glow_color="#8b5cf6", padding="20px"),
            icon="clock",
        )

    with col5:
        # Market Velocity Gauge - Obsidian Style
        velocity_score = 78
        import plotly.graph_objects as go

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=velocity_score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "MARKET VELOCITY", "font": {"size": 12, "color": "#8B949E", "family": "Space Grotesk"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#8B949E"},
                    "bar": {"color": "#6366F1"},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [0, 50], "color": "rgba(239, 68, 68, 0.1)"},
                        {"range": [50, 100], "color": "rgba(16, 185, 129, 0.1)"},
                    ],
                },
            )
        )
        st.plotly_chart(style_obsidian_chart(fig_gauge), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Hot Leads Feed
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### 🔥 PRIORITY HOT LEADS")

        # Hot lead cards - Obsidian Edition
        hot_leads = [
            {
                "name": "Sarah Martinez",
                "score": 5,
                "budget": "$425K",
                "location": "Round Rock",
                "timeline": "ASAP - Pre-approved",
                "last_message": "Can we see it this weekend?",
                "minutes_ago": 12,
            },
            {
                "name": "Mike Johnson",
                "score": 4,
                "budget": "$380K",
                "location": "Pflugerville",
                "timeline": "End of month",
                "last_message": "What's your cash offer?",
                "minutes_ago": 45,
            },
            {
                "name": "Jennifer Wu",
                "score": 4,
                "budget": "$500K",
                "location": "Hyde Park",
                "timeline": "Flexible",
                "last_message": "Love that area. Let's talk.",
                "minutes_ago": 120,
            },
        ]

        for lead in hot_leads:
            render_obsidian_card(
                title="",
                content=f"""
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>
                            {lead["name"]}
                            <span style='background: rgba(16, 185, 129, 0.15); color: #10b981; 
                                        padding: 4px 12px; border-radius: 6px; 
                                        font-size: 0.7rem; margin-left: 12px; font-weight: 800; text-transform: uppercase; border: 1px solid rgba(16, 185, 129, 0.3);'>
                                {lead["score"]} SIGNALS DETECTED
                            </span>
                        </div>
                        <div style='color: #8B949E; font-size: 0.9rem; margin-top: 8px; font-family: "Inter", sans-serif;'>
                            💰 {lead["budget"]} | 📍 {lead["location"]} | ⏰ {lead["timeline"]}
                        </div>
                        <div style='color: #E6EDF3; font-size: 1rem; margin-top: 12px; 
                                    font-style: italic; opacity: 0.9;'>
                            "{lead["last_message"]}"
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: #6366F1; font-size: 0.8rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>
                            {lead["minutes_ago"]}M AGO
                        </div>
                    </div>
                </div>
                """,
                config=CardConfig(variant="glass", padding="1.5rem"),
                icon="fire",
            )

            # Action Row - Buttons are automatically styled by inject_elite_css
            act_c1, act_c2, act_c3 = st.columns(3)
            with act_c1:
                st.button("📞 CALL NODE", key=f"call_ex_{lead['name']}", use_container_width=True)
            with act_c2:
                st.button("📅 SYNC CALENDAR", key=f"sch_ex_{lead['name']}", use_container_width=True)
            with act_c3:
                st.button("💬 SEND SIGNAL", key=f"sms_ex_{lead['name']}", use_container_width=True)
            st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    with col_right:
        # AI Performance Scorecard - Obsidian Edition
        st.markdown("### 📊 AI PERFORMANCE")
        st.markdown(
            f"""
        <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(10px);'>
            <div style='margin-bottom: 20px;'>
                <div style='color: #8B949E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Response Rate</div>
                <div style='font-size: 2rem; font-weight: 700; color: #10b981; font-family: "Space Grotesk", sans-serif;'>94%</div>
                <div style='background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; margin-top: 10px; overflow: hidden;'>
                    <div style='background: #10b981; width: 94%; height: 100%; box-shadow: 0 0 10px #10b981;'></div>
                </div>
            </div>
            <div style='margin-bottom: 20px;'>
                <div style='color: #8B949E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Qualification Accuracy</div>
                <div style='font-size: 2rem; font-weight: 700; color: #6366F1; font-family: "Space Grotesk", sans-serif;'>88%</div>
                <div style='background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; margin-top: 10px; overflow: hidden;'>
                    <div style='background: #6366F1; width: 88%; height: 100%; box-shadow: 0 0 10px #6366F1;'></div>
                </div>
            </div>
            <div>
                <div style='color: #8B949E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Conversion to Hot</div>
                <div style='font-size: 2rem; font-weight: 700; color: #f59e0b; font-family: "Space Grotesk", sans-serif;'>27%</div>
                <div style='background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; margin-top: 10px; overflow: hidden;'>
                    <div style='background: #f59e0b; width: 27%; height: 100%; box-shadow: 0 0 10px #f59e0b;'></div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick Actions - Obsidian Edition
        st.markdown("### ⚡ COMMAND ACTIONS")
        st.markdown(
            f"""
        <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(10px);'>
            <div style='display: flex; flex-direction: column; gap: 12px;'>
                <button style='width: 100%; background: #6366F1; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: 700; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.1em; box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);'>📨 BLAST HOT LEADS</button>
                <button style='width: 100%; background: transparent; color: #FFFFFF; border: 1px solid rgba(255,255,255,0.2); padding: 14px; border-radius: 8px; cursor: pointer; font-weight: 600; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.1em;'>📊 EXPORT INTEL REPORT</button>
                <button style='width: 100%; background: transparent; color: #FFFFFF; border: 1px solid rgba(255,255,255,0.2); padding: 14px; border-radius: 8px; cursor: pointer; font-weight: 600; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.1em;'>⚙️ NEURAL SETTINGS</button>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Activity Feed and Market Intelligence
    st.markdown("<br>", unsafe_allow_html=True)
    col_bottom_left, col_bottom_right = st.columns([1, 1])

    with col_bottom_left:
        st.markdown("### 🗺️ MARKET INTELLIGENCE HEATMAP")
        st.markdown(
            """
        <div style="background: rgba(22, 27, 34, 0.7); padding: 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);">
            <div style="font-family: 'Space Grotesk', sans-serif; color: #8B949E; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem;">Lead Density by Neighborhood (Last 24h)</div>
            <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px;">
                <!-- Row 1 -->
                <div style="aspect-ratio: 1; background: #ef4444; border-radius: 4px; box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);" title="Downtown: 42 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.8;" title="Domain: 28 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.5;" title="Zilker: 15 leads"></div>
                <div style="aspect-ratio: 1; background: rgba(255,255,255,0.05); border-radius: 4px;" title="Mueller: 5 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.9;" title="East Austin: 31 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.4;" title="Rainey: 12 leads"></div>
                <div style="aspect-ratio: 1; background: #ef4444; border-radius: 4px; box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);" title="Round Rock: 38 leads"></div>
                <!-- Row 2 -->
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.6;" title="Pflugerville: 19 leads"></div>
                <div style="aspect-ratio: 1; background: rgba(255,255,255,0.05); border-radius: 4px;" title="Cedar Park: 8 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.7;" title="Lakeway: 24 leads"></div>
                <div style="aspect-ratio: 1; background: #ef4444; border-radius: 4px; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);" title="South Lamar: 45 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.4;" title="Barton Hills: 14 leads"></div>
                <div style="aspect-ratio: 1; background: rgba(255,255,255,0.05); border-radius: 4px;" title="Circle C: 6 leads"></div>
                <div style="aspect-ratio: 1; background: #6366F1; border-radius: 4px; opacity: 0.3;" title="Avery Ranch: 11 leads"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 15px; font-size: 0.7rem; color: #8B949E; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                <span>Low Intensity</span>
                <span>Max Intensity</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Lead Velocity Sparklines - Obsidian Style
        st.markdown("### 📈 TELEMETRY VELOCITY (7D)")

        velocity_cols = st.columns(3)
        with velocity_cols[0]:
            st.markdown(
                "<div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase;'>New Nodes</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(sparkline([10, 15, 8, 22, 18, 25, 30], color="#6366F1"), use_container_width=True)
        with velocity_cols[1]:
            st.markdown(
                "<div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase;'>Hot Signals</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(sparkline([2, 5, 3, 8, 6, 10, 12], color="#10B981"), use_container_width=True)
        with velocity_cols[2]:
            st.markdown(
                "<div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase;'>Closings</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(sparkline([0, 1, 0, 2, 1, 0, 3], color="#8b5cf6"), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔮 PREDICTIVE REVENUE ROADMAP (Q1 2026)")
    # Forecast data - Obsidian Style
    months = ["Jan", "Feb", "Mar", "Apr"]
    forecast = [2.4, 3.1, 4.2, 5.5]
    confidence_upper = [2.5, 3.5, 4.8, 6.2]
    confidence_lower = [2.3, 2.7, 3.6, 4.8]

    fig_forecast = go.Figure()
    fig_forecast.add_trace(
        go.Scatter(
            x=months, y=forecast, mode="lines+markers", name="AI Projection", line=dict(color="#6366F1", width=4)
        )
    )
    fig_forecast.add_trace(go.Scatter(x=months, y=confidence_upper, mode="lines", line=dict(width=0), showlegend=False))
    fig_forecast.add_trace(
        go.Scatter(
            x=months,
            y=confidence_lower,
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(99, 102, 241, 0.1)",
            line=dict(width=0),
            name="Confidence Band",
        )
    )

    st.plotly_chart(style_obsidian_chart(fig_forecast), use_container_width=True)
    st.caption("Revenue projections based on current lead velocity and AI-driven conversion optimization.")

    with col_bottom_right:
        # Activity Feed - Obsidian Style
        st.markdown("### 📱 REAL-TIME SIGNAL LOG")

        activities = [
            {"type": "hot", "icon": "🔥", "message": "Sarah Martinez scaled to HOT status", "time": "12m ago"},
            {"type": "message", "icon": "💬", "message": "AI dispatched follow-up to Mike Johnson", "time": "45m ago"},
            {
                "type": "appointment",
                "icon": "📅",
                "message": "Sync scheduled for Jennifer Wu - Tomorrow 2pm",
                "time": "2h ago",
            },
            {
                "type": "message",
                "icon": "💬",
                "message": "Inbound signal: David Chen querying Hyde Park",
                "time": "3h ago",
            },
            {"type": "warm", "icon": "⚡", "message": "Emma Davis synchronized - status WARM", "time": "4h ago"},
        ]

        for activity in activities:
            border_color = "#10b981" if activity["type"] == "hot" else "rgba(255,255,255,0.1)"
            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.6); padding: 12px 16px; border-radius: 8px; 
                        margin-bottom: 8px; border-left: 3px solid {border_color};
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                        display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.05); border-left: 3px solid {border_color};'>
                <div>
                    <span style='font-size: 1.2rem; margin-right: 12px;'>{activity["icon"]}</span>
                    <span style='color: #E6EDF3; font-weight: 500; font-family: "Inter", sans-serif; font-size: 0.9rem;'>{activity["message"]}</span>
                </div>
                <div style='color: #6366F1; font-size: 0.75rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>{activity["time"].upper()}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def sparkline(data: list, color: str = "#2563eb", height: int = 60):
    """Generates a minimal sparkline chart using Plotly."""
    import plotly.graph_objects as go

    # Convert hex to rgba for fill
    if color.startswith("#"):
        hex_color = color.lstrip("#")
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        fill_color = f"rgba({r}, {g}, {b}, 0.2)"
    else:
        fill_color = color

    fig = go.Figure(
        go.Scatter(y=data, mode="lines", fill="tozeroy", line=dict(color=color, width=2), fillcolor=fill_color)
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
    )
    return fig
