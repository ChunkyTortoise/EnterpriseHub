"""
Enhanced Services - AI Lead Intelligence Component

Provides comprehensive behavioral insights and analytics for leads including:
- Health score visualization
- Engagement timeline tracking
- Sentiment analysis
- Property interest heatmap
- Urgency indicators
"""


import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_ai_lead_insights(lead_data):
    """
    Renders comprehensive AI-powered lead intelligence visualizations

    Args:
        lead_data (dict): Lead information including:
            - name, health_score, engagement_level
            - last_contact, communication_preference
            - urgency_indicators, extracted_preferences
            - conversation_history
    """

    st.markdown("### 🧠 AI Lead Intelligence")
    st.markdown("*Deep behavioral analysis powered by Claude AI*")

    # Section 1: Health Score Overview
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown("#### 💓 LEAD HEALTH SCORE")

        health_score = lead_data.get("health_score", 75)
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        # Health Score Gauge - Obsidian Edition
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=health_score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={
                    "text": "ENGAGEMENT HEALTH",
                    "font": {"size": 12, "color": "#8B949E", "family": "Space Grotesk"},
                },
                number={"font": {"size": 40, "color": "#FFFFFF", "family": "Space Grotesk"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#8B949E"},
                    "bar": {"color": "#6366F1"},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [0, 40], "color": "rgba(239, 68, 68, 0.1)"},
                        {"range": [40, 70], "color": "rgba(245, 158, 11, 0.1)"},
                        {"range": [70, 100], "color": "rgba(16, 185, 129, 0.1)"},
                    ],
                    "threshold": {"line": {"color": "#10b981", "width": 4}, "thickness": 0.75, "value": 80},
                },
            )
        )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        # Key Metrics - Obsidian Edition
        engagement_level = lead_data.get("engagement_level", "medium")
        comm_pref = lead_data.get("communication_preference", "text")

        st.markdown(
            f"""
        <div style='background: rgba(22, 27, 34, 0.7); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-top: 1rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);'>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.85rem;'>
                <div>
                    <div style='color: #8B949E; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Engagement</div>
                    <div style='color: #FFFFFF; font-weight: 600; margin-top: 4px; font-family: "Inter", sans-serif;'>{engagement_level.upper()}</div>
                </div>
                <div>
                    <div style='color: #8B949E; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Channel</div>
                    <div style='color: #6366F1; font-weight: 600; margin-top: 4px; font-family: "Inter", sans-serif;'>{comm_pref.upper()}</div>
                </div>
                <div>
                    <div style='color: #8B949E; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Last Sync</div>
                    <div style='color: #FFFFFF; font-weight: 600; margin-top: 4px; font-family: "Inter", sans-serif;'>{lead_data.get("last_contact", "N/A")}</div>
                </div>
                <div>
                    <div style='color: #8B949E; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Trajectory</div>
                    <div style='color: #FFFFFF; font-weight: 600; margin-top: 4px; font-family: "Inter", sans-serif;'>{lead_data.get("stage", "N/A").upper()}</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        # Section 2: Engagement Timeline - Obsidian Style
        st.markdown("#### 📈 ENGAGEMENT TELEMETRY (30D)")

        # ... [Data Generation Remains Same] ...

        # Create timeline chart - Obsidian Style
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=timeline_df["date"],
                y=timeline_df["activity"],
                mode="lines+markers",
                name="Activity Score",
                line={"color": "#6366F1", "width": 3, "shape": "spline"},
                fill="tozeroy",
                fillcolor="rgba(99, 102, 241, 0.1)",
                marker={"size": 8, "color": "#6366F1", "line": {"color": "#FFFFFF", "width": 1}},
            )
        )

        # Add event markers - Obsidian Style
        key_events = [
            {"date": dates[5], "y": activity_scores[5], "text": "📧 OPEN"},
            {"date": dates[15], "y": activity_scores[15], "text": "🏠 VIEW"},
            {"date": dates[25], "y": activity_scores[25], "text": "📝 SYNC"},
        ]

        for event in key_events:
            fig.add_annotation(
                x=event["date"],
                y=event["y"],
                text=event["text"],
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#6366F1",
                font={"size": 10, "color": "#FFFFFF", "family": "Space Grotesk"},
                bgcolor="rgba(22, 27, 34, 0.9)",
                bordercolor="rgba(255,255,255,0.1)",
                borderwidth=1,
            )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

    # Section 3: Sentiment Analysis & Property Interest
    st.markdown("---")
    col3, col4 = st.columns([1, 1])

    with col3:
        st.markdown("#### 😊 SENTIMENT SYNTHESIS")

        # ... [Data Generation Remains Same] ...

        # Sentiment donut chart - Obsidian Style
        colors = {"Positive": "#10b981", "Neutral": "#8B949E", "Negative": "#ef4444"}

        fig = px.pie(
            sentiment_df, values="percentage", names="sentiment", hole=0.6, color="sentiment", color_discrete_map=colors
        )

        fig.update_traces(
            textposition="outside", textinfo="label+percent", textfont=dict(color="#FFFFFF", family="Space Grotesk")
        )

        # Add center annotation - Obsidian Style
        fig.add_annotation(
            text=f"<b>{sentiments['Positive']}%</b>",
            showarrow=False,
            font={"size": 28, "color": "#10b981", "family": "Space Grotesk"},
            y=0.55,
        )
        fig.add_annotation(
            text="POSITIVE",
            showarrow=False,
            font={"size": 10, "color": "#8B949E", "family": "Space Grotesk", "letter_spacing": "0.1em"},
            y=0.42,
        )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        # Recent conversation excerpt - Obsidian Style
        st.markdown(
            """
        <div style='background: rgba(16, 185, 129, 0.05); padding: 1.25rem; border-radius: 12px; border-left: 4px solid #10b981; font-size: 0.9rem; font-style: italic; color: #E6EDF3; margin-top: 1rem; border: 1px solid rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; font-family: "Inter", sans-serif; line-height: 1.6;'>
            "We're really excited about the downtown area. The walkability is exactly what we're looking for!"
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown("#### 🏠 PROPERTY INTEREST HEATMAP")

        # ... [Data Generation Remains Same] ...

        for prop in properties:
            interest_score = (prop["views"] * 2) + prop["dwell"]
            bar_width = min((interest_score / 35) * 100, 100)

            color = "#10b981" if interest_score >= 20 else "#f59e0b" if interest_score >= 10 else "#6366F1"

            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.6); padding: 1rem 1.25rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 0.75rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                    <div style='font-weight: 700; font-size: 0.85rem; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>{prop["name"].upper()}</div>
                    <div style='font-size: 0.7rem; color: #8B949E; font-family: "Inter", sans-serif; font-weight: 600;'>{prop["views"]} SIGNAL · {prop["dwell"]}M DWELL</div>
                </div>
                <div style='background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; overflow: hidden;'>
                    <div style='background: {color}; width: {bar_width}%; height: 100%; box-shadow: 0 0 10px {color}40;'></div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Section 4: Urgency Indicators - Obsidian Style
    if urgency_indicators:
        st.markdown("---")
        st.markdown("#### ⚡ CRITICAL SIGNALS")

        for indicator in urgency_indicators[:3]:
            st.markdown(
                f"""
            <div style='background: rgba(245, 158, 11, 0.1); 
                        padding: 1rem 1.25rem; border-radius: 12px; border-left: 4px solid #f59e0b; 
                        margin-bottom: 0.75rem; display: flex; align-items: center; gap: 15px; border: 1px solid rgba(245, 158, 11, 0.2); border-left: 4px solid #f59e0b;'>
                <span style='font-size: 1.5rem; filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.4));'>⚠️</span>
                <div>
                    <div style='font-weight: 700; color: #FFFFFF; font-size: 0.95rem; font-family: "Space Grotesk", sans-serif; letter-spacing: 0.02em;'>{indicator.upper()}</div>
                    <div style='color: #f59e0b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif; margin-top: 2px;'>Immediate action directive</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
