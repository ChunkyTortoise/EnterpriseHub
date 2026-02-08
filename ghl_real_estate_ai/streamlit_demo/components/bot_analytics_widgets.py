"""
Bot Analytics Widgets - Reusable components for bot-specific analytics
=====================================================================

Author: Claude Code Assistant
Created: 2026-01-25
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_bot_performance_gauge(bot_name: str, score: float, target: float = 85.0):
    """Render a performance gauge for any bot."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"{bot_name} Performance"},
            delta={"reference": target},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 85], "color": "yellow"},
                    {"range": [85, 100], "color": "green"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": target},
            },
        )
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_conversation_flow_chart(conversations: List[Dict[str, Any]]):
    """Render conversation flow analysis."""
    # Process conversation data into flow metrics
    flow_stages = ["Initial Contact", "Qualification", "Objection Handling", "Close Attempt", "Resolution"]
    flow_counts = [
        len(conversations),
        len([c for c in conversations if c.get("qualified", False)]),
        len([c for c in conversations if c.get("objections", 0) > 0]),
        len([c for c in conversations if c.get("close_attempted", False)]),
        len([c for c in conversations if c.get("resolved", False)]),
    ]

    fig = go.Figure(
        go.Funnel(
            y=flow_stages,
            x=flow_counts,
            textinfo="value+percent initial",
            marker=dict(color=["deepskyblue", "lightsalmon", "tan", "teal", "silver"]),
        )
    )

    fig.update_layout(title="Conversation Flow Analysis", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_response_time_heatmap(response_times: Dict[str, List[float]]):
    """Render response time heatmap by hour/day."""
    # Create mock heatmap data if no real data provided
    if not response_times:
        hours = list(range(24))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Generate mock response times (in seconds)
        import random

        heatmap_data = []
        for day in days:
            day_times = []
            for hour in hours:
                # Business hours have faster response times
                if 9 <= hour <= 17:
                    avg_time = random.uniform(15, 45)  # 15-45 seconds
                else:
                    avg_time = random.uniform(60, 180)  # 1-3 minutes
                day_times.append(avg_time)
            heatmap_data.append(day_times)

        fig = go.Figure(
            data=go.Heatmap(z=heatmap_data, x=hours, y=days, colorscale="RdYlBu_r", colorbar=dict(title="Seconds"))
        )

        fig.update_layout(
            title="Average Response Time by Hour/Day", xaxis_title="Hour of Day", yaxis_title="Day of Week", height=300
        )

        st.plotly_chart(fig, use_container_width=True)


def render_sentiment_timeline(conversations: List[Dict[str, Any]]):
    """Render sentiment analysis timeline."""
    if not conversations:
        # Generate mock sentiment data
        dates = pd.date_range(start="2026-01-18", periods=7, freq="D")
        sentiment_data = {
            "Date": dates,
            "Positive": [23, 31, 28, 35, 42, 38, 45],
            "Neutral": [12, 15, 18, 14, 16, 19, 22],
            "Negative": [5, 8, 6, 9, 7, 8, 6],
        }
        df = pd.DataFrame(sentiment_data)

        fig = px.line(df, x="Date", y=["Positive", "Neutral", "Negative"], title="Conversation Sentiment Over Time")
        st.plotly_chart(fig, use_container_width=True)


def render_lead_scoring_distribution(scores: List[float], bot_type: str = "Bot"):
    """Render lead scoring distribution."""
    if not scores:
        # Generate mock scores
        import random

        scores = [random.uniform(40, 100) for _ in range(50)]

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=scores, nbinsx=10, name=f"{bot_type} Scores"))

    # Add average line
    avg_score = sum(scores) / len(scores)
    fig.add_vline(x=avg_score, line_dash="dash", line_color="red", annotation_text=f"Avg: {avg_score:.1f}")

    fig.update_layout(
        title=f"{bot_type} Lead Score Distribution", xaxis_title="Lead Score", yaxis_title="Frequency", height=300
    )

    st.plotly_chart(fig, use_container_width=True)


def render_bot_comparison_radar(bot_metrics: Dict[str, Dict[str, float]]):
    """Render radar chart comparing multiple bots."""
    if not bot_metrics:
        # Mock comparison data
        bot_metrics = {
            "Lead Bot": {"Response Speed": 85, "Accuracy": 78, "Engagement": 82, "Conversion": 45, "Satisfaction": 88},
            "Buyer Bot": {"Response Speed": 90, "Accuracy": 85, "Engagement": 79, "Conversion": 52, "Satisfaction": 91},
            "Seller Bot": {
                "Response Speed": 88,
                "Accuracy": 92,
                "Engagement": 95,
                "Conversion": 67,
                "Satisfaction": 86,
            },
        }

    fig = go.Figure()

    categories = list(next(iter(bot_metrics.values())).keys())

    for bot_name, metrics in bot_metrics.items():
        values = list(metrics.values())
        values += values[:1]  # Close the polygon
        categories_closed = categories + [categories[0]]

        fig.add_trace(go.Scatterpolar(r=values, theta=categories_closed, fill="toself", name=bot_name))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Bot Performance Comparison",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_activity_calendar(activities: List[Dict[str, Any]]):
    """Render calendar heatmap of bot activities."""
    # Generate mock activity data
    dates = pd.date_range(start="2026-01-01", end="2026-01-31", freq="D")
    import random

    activity_data = []
    for date in dates:
        activity_count = random.randint(5, 50)
        activity_data.append(
            {
                "Date": date.strftime("%Y-%m-%d"),
                "Activity Count": activity_count,
                "Week": date.isocalendar()[1],
                "Day": date.strftime("%a"),
                "Day_num": date.weekday(),
            }
        )

    df = pd.DataFrame(activity_data)

    # Create calendar-like layout
    weeks = df["Week"].unique()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    calendar_matrix = []
    for week in weeks:
        week_data = df[df["Week"] == week]
        week_activities = []
        for day_num in range(7):
            day_activity = week_data[week_data["Day_num"] == day_num]
            if not day_activity.empty:
                week_activities.append(day_activity.iloc[0]["Activity Count"])
            else:
                week_activities.append(0)
        calendar_matrix.append(week_activities)

    fig = go.Figure(
        data=go.Heatmap(
            z=calendar_matrix,
            x=days,
            y=[f"Week {w}" for w in weeks],
            colorscale="Blues",
            showscale=True,
            colorbar=dict(title="Activities"),
        )
    )

    fig.update_layout(title="Bot Activity Calendar (January 2026)", height=300)

    st.plotly_chart(fig, use_container_width=True)


def render_kpi_cards(metrics: Dict[str, Any], title: str = "Bot KPIs"):
    """Render beautiful KPI cards."""
    st.markdown(f"### {title}")

    # Calculate columns needed
    num_metrics = len(metrics)
    cols = st.columns(min(num_metrics, 4))

    for i, (key, value) in enumerate(metrics.items()):
        with cols[i % 4]:
            # Format value based on type
            if isinstance(value, float):
                if value < 1:
                    display_value = f"{value:.1%}"
                elif value < 100:
                    display_value = f"{value:.1f}"
                else:
                    display_value = f"{value:,.0f}"
            else:
                display_value = str(value)

            # Generate mock delta for demo
            import random

            delta_value = random.choice(["+1.2%", "+5.7%", "-0.3%", "+2.1%", "+8.4%"])

            st.metric(label=key.replace("_", " ").title(), value=display_value, delta=delta_value)


def render_conversation_insights(insights: List[str]):
    """Render conversation insights with styling."""
    if not insights:
        insights = [
            "🎯 67% of conversations include price objections",
            "⏰ Response time <30 sec increases engagement by 40%",
            "📞 Voice handoffs show 73% higher conversion rates",
            "🧠 Stall detection accuracy improved to 89%",
            "💬 Average conversation length: 4.2 exchanges",
        ]

    st.markdown("### 💡 Conversation Insights")

    for insight in insights:
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(30,136,229,0.1) 100%);
            border-left: 3px solid #6366f1;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
        ">
            {insight}
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_performance_dashboard(bot_name: str, metrics: Dict[str, float]):
    """Render comprehensive performance dashboard for a bot."""
    st.markdown(f"### ⚡ {bot_name} Performance Dashboard")

    # Performance Score Calculation
    overall_score = sum(metrics.values()) / len(metrics) if metrics else 0

    # Main Performance Score
    col_score, col_trend = st.columns([1, 2])

    with col_score:
        # Performance gauge
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=overall_score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Overall Performance"},
                delta={"reference": 85},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "#1f77b4"},
                    "steps": [
                        {"range": [0, 60], "color": "#ff6b6b"},
                        {"range": [60, 80], "color": "#ffd93d"},
                        {"range": [80, 100], "color": "#6bcf7f"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
                },
            )
        )
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

    with col_trend:
        # Performance trend chart
        if metrics:
            metric_names = list(metrics.keys())
            metric_values = list(metrics.values())

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=metric_values, theta=metric_names, fill="toself", name=bot_name))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                title="Performance Breakdown",
                height=250,
            )

            st.plotly_chart(fig_radar, use_container_width=True)


def render_real_time_metrics(active_count: int, messages_per_min: float, load_status: str):
    """Render real-time performance metrics."""
    st.markdown("### 🔴 Real-Time Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Active Conversations", active_count, delta="+2 vs last hour")

    with col2:
        st.metric("Messages/Min", f"{messages_per_min:.1f}", delta="+0.3")

    with col3:
        load_color = {"Normal": "🟢", "Light": "🔵", "High": "🟡", "Critical": "🔴"}.get(load_status, "⚪")
        st.metric("System Load", f"{load_color} {load_status}")


def render_performance_alerts(alerts: List[Dict[str, str]]):
    """Render performance alerts and notifications."""
    if not alerts:
        alerts = [
            {"level": "success", "message": "All systems operating within normal parameters"},
            {"level": "warning", "message": "Response time spike detected at 2:30 PM"},
            {"level": "info", "message": "New performance optimization deployed"},
        ]

    st.markdown("### 🚨 Performance Alerts")

    for alert in alerts:
        level_colors = {"success": "🟢", "warning": "🟡", "error": "🔴", "info": "🔵"}

        icon = level_colors.get(alert["level"], "⚪")

        if alert["level"] == "error":
            st.error(f"{icon} {alert['message']}")
        elif alert["level"] == "warning":
            st.warning(f"{icon} {alert['message']}")
        elif alert["level"] == "success":
            st.success(f"{icon} {alert['message']}")
        else:
            st.info(f"{icon} {alert['message']}")


def render_optimization_recommendations(recommendations: List[str]):
    """Render AI-powered optimization recommendations."""
    if not recommendations:
        recommendations = [
            "💡 Increase response buffer during peak hours (10 AM - 2 PM)",
            "🔧 Optimize Day 14 email templates - showing 15% lower engagement",
            "📈 Consider A/B testing new conversation starters",
            "⚡ Weekend performance could benefit from lighter messaging tone",
            "🎯 Focus on mid-tier price range optimization ($500-700K)",
        ]

    st.markdown("### 🎯 AI Optimization Recommendations")

    for i, rec in enumerate(recommendations, 1):
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(5,150,105,0.1) 100%);
            border-left: 3px solid #10b981;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
        ">
            <strong>#{i}</strong> {rec}
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_performance_comparison_table(bot_data: Dict[str, Dict[str, float]]):
    """Render a comparison table of bot performances."""
    if not bot_data:
        # Mock data for demonstration
        bot_data = {
            "Lead Bot": {"response_time": 2.3, "success_rate": 94.2, "efficiency": 87.5},
            "Buyer Bot": {"response_time": 1.8, "match_accuracy": 89.7, "satisfaction": 4.7},
            "Seller Bot": {"response_time": 1.2, "close_rate": 67.8, "effectiveness": 84.7},
        }

    st.markdown("### 📊 Bot Performance Comparison")

    # Convert to DataFrame for easier display
    df = pd.DataFrame(bot_data).T

    # Style the dataframe
    styled_df = df.style.highlight_max(axis=0, color="lightgreen").highlight_min(axis=0, color="lightcoral")

    st.dataframe(styled_df, use_container_width=True)

    # Create comparison chart
    fig = go.Figure()

    for bot_name, metrics in bot_data.items():
        fig.add_trace(
            go.Scatterpolar(r=list(metrics.values()), theta=list(metrics.keys()), fill="toself", name=bot_name)
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Multi-Bot Performance Radar",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)
