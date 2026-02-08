"""
AI Performance Metrics Dashboard - Shows real-time AI performance statistics
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st


def render_ai_metrics_dashboard():
    """
    Render comprehensive AI performance metrics dashboard - Obsidian Command Edition
    """
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

    st.markdown("### 📊 AI PERFORMANCE TELEMETRY")
    st.markdown("*Real-time conversational AI statistics (Last 7 Days)*")
    metrics = get_ai_performance_metrics()
    col1, col2, col3, col4 = st.columns(4)
    card_style = "padding: 1.5rem; border-radius: 12px; color: #FFFFFF; border: 1px solid rgba(255,255,255,0.05); text-align: center; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); backdrop-filter: blur(12px);"
    label_style = "font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;"
    value_style = "font-size: 2.25rem; font-weight: 700; margin: 8px 0; font-family: 'Space Grotesk', sans-serif;"
    with col1:
        st.markdown(
            f"\n        <div style='background: rgba(99, 102, 241, 0.1); {card_style} border-top: 4px solid #6366F1;'>\n            <div style='{value_style}'>{metrics['avg_response_time']}</div>\n            <div style='{label_style}'>Avg Latency</div>\n            <div style='font-size: 0.7rem; color: #6366F1; font-weight: 700; text-transform: uppercase; margin-top: 8px;'>⚡ ULTRA FAST</div>\n        </div>\n        ",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"\n        <div style='background: rgba(16, 185, 129, 0.1); {card_style} border-top: 4px solid #10b981;'>\n            <div style='{value_style}'>{metrics['messages_handled']:,}</div>\n            <div style='{label_style}'>Signals Handled</div>\n            <div style='font-size: 0.7rem; color: #10b981; font-weight: 700; text-transform: uppercase; margin-top: 8px;'>📈 +23% MOMENTUM</div>\n        </div>\n        ",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"\n        <div style='background: rgba(245, 158, 11, 0.1); {card_style} border-top: 4px solid #f59e0b;'>\n            <div style='{value_style}'>{metrics['automation_rate']}%</div>\n            <div style='{label_style}'>Autonomy Rate</div>\n            <div style='font-size: 0.7rem; color: #f59e0b; font-weight: 700; text-transform: uppercase; margin-top: 8px;'>🤖 AI ORCHESTRATED</div>\n        </div>\n        ",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"\n        <div style='background: rgba(139, 92, 246, 0.1); {card_style} border-top: 4px solid #8b5cf6;'>\n            <div style='{value_style}'>{metrics['showings_scheduled']}</div>\n            <div style='{label_style}'>Syncs Executed</div>\n            <div style='font-size: 0.7rem; color: #8b5cf6; font-weight: 700; text-transform: uppercase; margin-top: 8px;'>📅 AUTO-SYNCHRONIZED</div>\n        </div>\n        ",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### 🎯 AI ACTIVITY LOG")
        activities = [
            {"type": "Signals Answered", "count": metrics["questions_answered"], "icon": "❓"},
            {"type": "Nodes Qualified", "count": metrics["leads_qualified"], "icon": "✅"},
            {"type": "Property Alignments", "count": metrics["property_matches"], "icon": "🏠"},
            {"type": "Meetings Scheduled", "count": metrics["showings_scheduled"], "icon": "📅"},
            {"type": "Follow-ups Dispatched", "count": metrics["followups_sent"], "icon": "💬"},
            {"type": "Human Escalations", "count": metrics["human_handoffs"], "icon": "👤"},
        ]
        for activity in activities:
            st.markdown(
                f"""\n            <div style='display: flex; justify-content: space-between; align-items: center; \n                        padding: 1rem 1.25rem; background: rgba(255,255,255,0.02); border-radius: 10px; \n                        border: 1px solid rgba(255,255,255,0.05); margin-bottom: 0.75rem; transition: all 0.2s ease;'>\n                <div style='display: flex; align-items: center; gap: 1rem;'>\n                    <span style='font-size: 1.5rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>{activity["icon"]}</span>\n                    <span style='font-size: 0.9rem; color: #E6EDF3; font-family: "Inter", sans-serif; font-weight: 500;'>{activity["type"].upper()}</span>\n                </div>\n                <span style='font-size: 1.15rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>{activity["count"]}</span>\n            </div>\n            """,
                unsafe_allow_html=True,
            )
        success_rate = (1 - metrics["human_handoffs"] / metrics["messages_handled"]) * 100
        st.markdown(
            f"""\n        <div style='background: rgba(16, 185, 129, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #10b981; margin-top: 1.5rem; border: 1px solid rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981;'>\n            <div style='font-size: 0.75rem; color: #10b981; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Success Probability</div>\n            <div style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0.5rem 0; font-family: "Space Grotesk", sans-serif;'>{success_rate:.1f}%</div>\n            <div style='font-size: 0.85rem; color: #8B949E; font-family: "Inter", sans-serif; line-height: 1.5;'>\n                AI successfully handled {success_rate:.1f}% of conversation streams without manual escalation.\n            </div>\n        </div>\n        """,
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown("#### 📈 LATENCY TRAJECTORY")
        fig = create_response_time_chart(metrics["daily_response_times"])
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        st.markdown("#### ⏱️ RESOURCE OPTIMIZATION")
        time_saved_minutes = metrics["messages_handled"] * 2.5
        time_saved_hours = time_saved_minutes / 60
        st.markdown(
            f"""\n        <div style='background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #6366F1; border: 1px solid rgba(99, 102, 241, 0.1); border-left: 4px solid #6366F1;'>\n            <div style='font-size: 0.75rem; color: #6366F1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Temporal Efficiency</div>\n            <div style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0.5rem 0; font-family: "Space Grotesk", sans-serif;'>{time_saved_hours:.1f} HOURS</div>\n            <div style='font-size: 0.85rem; color: #8B949E; font-family: "Inter", sans-serif;'>\n                Operational recovery: {time_saved_hours:.1f} hours returned to enterprise workflows.\n            </div>\n        </div>\n        """,
            unsafe_allow_html=True,
        )
        hourly_rate = 50
        cost_saved = time_saved_hours * hourly_rate
        st.markdown(
            f"""\n        <div style='background: rgba(16, 185, 129, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #10b981; margin-top: 1.5rem; border: 1px solid rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981;'>\n            <div style='font-size: 0.75rem; color: #10b981; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Capital Efficiency</div>\n            <div style='font-size: 2.25rem; font-weight: 700; color: #FFFFFF; margin: 0.5rem 0; font-family: "Space Grotesk", sans-serif;'>${cost_saved:,.0f}</div>\n            <div style='font-size: 0.85rem; color: #8B949E; font-family: "Inter", sans-serif;'>\n                Estimated fiscal recovery at institution-grade rates (${hourly_rate}/hr).\n            </div>\n        </div>\n        """,
            unsafe_allow_html=True,
        )


def render_ai_metrics_compact():
    """Render compact metrics for sidebar or small spaces"""
    metrics = get_ai_performance_metrics()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Response Time", metrics["avg_response_time"], delta="-0.3s", delta_color="inverse")
    with col2:
        st.metric("Messages", f"{metrics['messages_handled']:,}", delta="+23%")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Automation", f"{metrics['automation_rate']}%", delta="+2%")
    with col4:
        st.metric("Showings", metrics["showings_scheduled"], delta="+4")


@st.cache_data(ttl=300)
def get_ai_performance_metrics() -> Dict[str, Any]:
    """
    Get AI performance metrics
    In production, this would query actual monitoring data
    """
    return {
        "avg_response_time": "1.2s",
        "messages_handled": 247,
        "questions_answered": 189,
        "leads_qualified": 34,
        "showings_scheduled": 12,
        "property_matches": 56,
        "followups_sent": 78,
        "human_handoffs": 8,
        "automation_rate": 96.8,
        "daily_response_times": [
            {"day": "Mon", "avg_time": 1.4},
            {"day": "Tue", "avg_time": 1.3},
            {"day": "Wed", "avg_time": 1.2},
            {"day": "Thu", "avg_time": 1.1},
            {"day": "Fri", "avg_time": 1.2},
            {"day": "Sat", "avg_time": 1.3},
            {"day": "Sun", "avg_time": 1.2},
        ],
    }


def create_response_time_chart(daily_data: List[Dict[str, Any]]) -> go.Figure:
    """Create response time trend chart"""
    days = [d["day"] for d in daily_data]
    times = [d["avg_time"] for d in daily_data]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=days,
            y=times,
            mode="lines+markers",
            line=dict(color="#3b82f6", width=3),
            marker=dict(size=10, color="#2563eb", line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
            hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}s<extra></extra>",
        )
    )
    fig.update_layout(
        title=None,
        xaxis_title="Day of Week",
        yaxis_title="Response Time (seconds)",
        template="plotly_white",
        height=250,
        margin=dict(l=40, r=20, t=20, b=40),
        font=dict(size=11),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f1f5f9", range=[0, max(times) * 1.2])
    return fig
