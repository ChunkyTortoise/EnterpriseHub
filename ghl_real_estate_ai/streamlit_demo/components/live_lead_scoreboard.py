"""
Live Lead Scoreboard Component for GHL Real Estate AI

Real-time animated lead scoring dashboard with:
- Live score updates and animations
- Priority-based visual indicators
- Mobile-responsive design
- Interactive drill-down capabilities
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_live_scoreboard_css():
    """Inject custom CSS for live scoreboard animations"""
    st.markdown(
        "\n    <style>\n    /* Live Scoreboard Animations */\n    @keyframes pulse-hot {\n        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }\n        70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }\n        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }\n    }\n\n    @keyframes pulse-warm {\n        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 149, 0, 0.7); }\n        70% { transform: scale(1.01); box-shadow: 0 0 0 5px rgba(255, 149, 0, 0); }\n        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 149, 0, 0); }\n    }\n\n    @keyframes score-increase {\n        0% { transform: scale(1) translateY(0); color: #28a745; }\n        50% { transform: scale(1.1) translateY(-2px); color: #20c997; }\n        100% { transform: scale(1) translateY(0); color: #28a745; }\n    }\n\n    @keyframes score-decrease {\n        0% { transform: scale(1) translateY(0); color: #dc3545; }\n        50% { transform: scale(0.95) translateY(2px); color: #e74c3c; }\n        100% { transform: scale(1) translateY(0); color: #dc3545; }\n    }\n\n    .scoreboard-card {\n        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n        border-radius: 15px;\n        padding: 1.5rem;\n        margin: 0.5rem 0;\n        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);\n        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n        border: 1px solid rgba(255, 255, 255, 0.1);\n        position: relative;\n        overflow: hidden;\n    }\n\n    .scoreboard-card::before {\n        content: '';\n        position: absolute;\n        top: 0;\n        left: 0;\n        right: 0;\n        height: 3px;\n        background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);\n        background-size: 200% 100%;\n        animation: gradient-shift 3s ease infinite;\n    }\n\n    @keyframes gradient-shift {\n        0% { background-position: 0% 0; }\n        50% { background-position: 100% 0; }\n        100% { background-position: 0% 0; }\n    }\n\n    .scoreboard-card:hover {\n        transform: translateY(-4px);\n        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25);\n    }\n\n    .score-circle {\n        width: 80px;\n        height: 80px;\n        border-radius: 50%;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n        font-size: 1.5rem;\n        font-weight: bold;\n        color: white;\n        margin: 0 auto 1rem;\n        position: relative;\n        overflow: hidden;\n    }\n\n    .score-hot {\n        background: radial-gradient(circle, #ff4757, #ff3742);\n        animation: pulse-hot 2s infinite;\n    }\n\n    .score-warm {\n        background: radial-gradient(circle, #ffa502, #ff6348);\n        animation: pulse-warm 3s infinite;\n    }\n\n    .score-cold {\n        background: linear-gradient(135deg, #a4b0be, #747d8c);\n    }\n\n    .lead-name {\n        font-size: 1.2rem;\n        font-weight: 600;\n        color: white;\n        margin-bottom: 0.5rem;\n        text-align: center;\n    }\n\n    .lead-details {\n        color: rgba(255, 255, 255, 0.8);\n        font-size: 0.9rem;\n        text-align: center;\n        line-height: 1.4;\n    }\n\n    .score-trend {\n        display: flex;\n        align-items: center;\n        justify-content: center;\n        margin-top: 0.5rem;\n        font-size: 0.8rem;\n        font-weight: 500;\n    }\n\n    .trend-up {\n        color: #2ecc71;\n        animation: score-increase 1s ease-in-out;\n    }\n\n    .trend-down {\n        color: #e74c3c;\n        animation: score-decrease 1s ease-in-out;\n    }\n\n    .trend-stable {\n        color: #95a5a6;\n    }\n\n    .factors-list {\n        background: rgba(255, 255, 255, 0.1);\n        border-radius: 8px;\n        padding: 0.75rem;\n        margin-top: 1rem;\n    }\n\n    .factor-badge {\n        display: inline-block;\n        background: rgba(255, 255, 255, 0.2);\n        color: white;\n        padding: 0.2rem 0.6rem;\n        border-radius: 12px;\n        font-size: 0.7rem;\n        margin: 0.2rem;\n        border: 1px solid rgba(255, 255, 255, 0.1);\n    }\n\n    .scoreboard-header {\n        text-align: center;\n        margin-bottom: 2rem;\n    }\n\n    .live-indicator {\n        display: inline-flex;\n        align-items: center;\n        background: linear-gradient(45deg, #00b4db, #0083b0);\n        color: white;\n        padding: 0.5rem 1rem;\n        border-radius: 20px;\n        font-size: 0.9rem;\n        font-weight: 500;\n        margin-bottom: 1rem;\n    }\n\n    .live-dot {\n        width: 8px;\n        height: 8px;\n        background: #2ecc71;\n        border-radius: 50%;\n        margin-right: 0.5rem;\n        animation: pulse 2s infinite;\n    }\n\n    @keyframes pulse {\n        0% { opacity: 1; transform: scale(1); }\n        50% { opacity: 0.7; transform: scale(1.2); }\n        100% { opacity: 1; transform: scale(1); }\n    }\n\n    /* Mobile Responsive */\n    @media (max-width: 768px) {\n        .scoreboard-card {\n            padding: 1rem;\n            margin: 0.25rem 0;\n        }\n\n        .score-circle {\n            width: 60px;\n            height: 60px;\n            font-size: 1.2rem;\n        }\n\n        .lead-name {\n            font-size: 1rem;\n        }\n\n        .lead-details {\n            font-size: 0.8rem;\n        }\n    }\n\n    /* Dark mode support */\n    @media (prefers-color-scheme: dark) {\n        .scoreboard-card {\n            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);\n            border: 1px solid rgba(255, 255, 255, 0.05);\n        }\n    }\n    </style>\n    ",
        unsafe_allow_html=True,
    )


class LiveLeadScoreboard:
    """Live lead scoreboard with real-time updates and animations"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager
        self.last_update = datetime.now()

    def render(self, container_key: str = "live_scoreboard"):
        """Render the live lead scoreboard"""
        render_live_scoreboard_css()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f'\n            <div class="scoreboard-header">\n                <div class="live-indicator">\n                    <div class="live-dot"></div>\n                    Live Lead Scoring\n                </div>\n                <h2 style="color: #2c3e50; margin: 0;">🎯 Active Lead Pipeline</h2>\n            </div>\n            ',
                unsafe_allow_html=True,
            )
        leads_data = self._get_live_leads_data()
        self._render_scoreboard_grid(leads_data)
        self._render_performance_summary(leads_data)
        if self.state_manager.user_preferences.auto_refresh:
            time.sleep(0.1)
            st.rerun()

    def _get_live_leads_data(self) -> List[Dict[str, Any]]:
        """Get real-time lead scoring data"""
        try:
            recent_events = self.realtime_service.get_recent_events(
                event_type="lead_score_update", limit=20, since=datetime.now() - timedelta(hours=1)
            )
            if not recent_events:
                from ghl_real_estate_ai.services.realtime_data_service import DemoDataGenerator

                return DemoDataGenerator.generate_lead_scores(12)
            leads = []
            for event in recent_events:
                data = event.data
                leads.append(
                    {
                        "id": data.get("lead_id", "unknown"),
                        "name": self._generate_lead_name(data.get("lead_id", "")),
                        "score": data.get("score", 0),
                        "previous_score": data.get("previous_score", 0),
                        "status": self._get_score_status(data.get("score", 0)),
                        "factors": data.get("factors", []),
                        "last_activity": event.timestamp,
                        "trend": self._calculate_trend(data.get("score", 0), data.get("previous_score", 0)),
                    }
                )
            return sorted(leads, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            st.error(f"Error loading live leads data: {e}")
            from ghl_real_estate_ai.services.realtime_data_service import DemoDataGenerator

            return DemoDataGenerator.generate_lead_scores(8)

    def _generate_lead_name(self, lead_id: str) -> str:
        """Generate realistic lead names from ID"""
        names = [
            "Sarah Johnson",
            "Michael Chen",
            "Emily Rodriguez",
            "David Kim",
            "Lisa Anderson",
            "James Wilson",
            "Maria Garcia",
            "Robert Taylor",
            "Jennifer Brown",
            "Christopher Lee",
            "Amanda Martinez",
            "Daniel White",
        ]
        import hashlib

        hash_val = int(hashlib.md5(lead_id.encode()).hexdigest(), 16)
        return names[hash_val % len(names)]

    def _get_score_status(self, score: int) -> str:
        """Determine lead status from score"""
        if score >= 80:
            return "hot"
        elif score >= 60:
            return "warm"
        else:
            return "cold"

    def _calculate_trend(self, current: int, previous: int) -> str:
        """Calculate score trend"""
        if current > previous:
            return "up"
        elif current < previous:
            return "down"
        else:
            return "stable"

    def _render_scoreboard_grid(self, leads_data: List[Dict[str, Any]]):
        """Render the main scoreboard grid"""
        is_mobile = st.session_state.get("is_mobile", False)
        cols_per_row = 1 if is_mobile else 2 if self.state_manager.user_preferences.compact_view else 3
        for i in range(0, len(leads_data), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(leads_data):
                    lead = leads_data[i + j]
                    with cols[j]:
                        self._render_lead_card(lead)

    def _render_lead_card(self, lead: Dict[str, Any]):
        """Render individual lead scoring card"""
        score = lead["score"]
        status = lead["status"]
        trend = lead.get("trend", "stable")
        trend_icons = {"up": "📈 ↗️", "down": "📉 ↘️", "stable": "➡️"}
        trend_classes = {"up": "trend-up", "down": "trend-down", "stable": "trend-stable"}
        factors_html = "".join(
            [
                f"""<span class="factor-badge">{factor.replace("_", " ").title()}</span>"""
                for factor in lead["factors"][:4]
            ]
        )
        time_diff = datetime.now() - lead["last_activity"]
        time_str = self._format_time_diff(time_diff)
        st.markdown(
            f"""\n        <div class="scoreboard-card">\n            <div class="score-circle score-{status}">\n                {score}\n            </div>\n            <div class="lead-name">{lead["name"]}</div>\n            <div class="lead-details">\n                <div>ID: {lead["id"]}</div>\n                <div>Last Activity: {time_str}</div>\n            </div>\n            <div class="score-trend {trend_classes[trend]}">\n                {trend_icons[trend]} {abs(score - lead["previous_score"])} pts\n            </div>\n            <div class="factors-list">\n                {factors_html}\n            </div>\n        </div>\n        """,
            unsafe_allow_html=True,
        )
        if st.button(f"View Details", key=f"lead_details_{lead['id']}", use_container_width=True):
            self._show_lead_details(lead)

    def _format_time_diff(self, time_diff: timedelta) -> str:
        """Format time difference for display"""
        total_seconds = int(time_diff.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        else:
            hours = total_seconds // 3600
            return f"{hours}h ago"

    def _show_lead_details(self, lead: Dict[str, Any]):
        """Show detailed lead information in modal/expander"""
        with st.expander(f"🔍 {lead['name']} - Detailed Analysis", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Current Score", value=f"{lead['score']}", delta=f"{lead['score'] - lead['previous_score']}"
                )
                st.metric(label="Status", value=lead["status"].title())
            with col2:
                score_history = self._generate_score_history(lead)
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(score_history))),
                        y=score_history,
                        mode="lines+markers",
                        name="Score Trend",
                        line=dict(color="#3498db", width=3),
                        marker=dict(size=6),
                    )
                )
                fig.update_layout(
                    title="Score Trend (Last 7 Days)",
                    xaxis_title="Days Ago",
                    yaxis_title="Score",
                    height=200,
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("**🎯 Scoring Factors:**")
            factors_df = pd.DataFrame(
                [
                    {"Factor": factor.replace("_", " ").title(), "Impact": "High" if i < 2 else "Medium"}
                    for i, factor in enumerate(lead["factors"])
                ]
            )
            if not factors_df.empty:
                st.dataframe(factors_df, hide_index=True, use_container_width=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📞 Call Lead", key=f"call_{lead['id']}"):
                    st.success("📞 Call initiated!")
            with col2:
                if st.button("📧 Send Email", key=f"email_{lead['id']}"):
                    st.success("📧 Email template opened!")
            with col3:
                if st.button("📅 Schedule Meeting", key=f"schedule_{lead['id']}"):
                    st.success("📅 Calendar opened!")

    def _generate_score_history(self, lead: Dict[str, Any]) -> List[int]:
        """Generate realistic score history for visualization"""
        import random

        current_score = lead["score"]
        history = []
        for i in range(7, 0, -1):
            if lead["trend"] == "up":
                score = current_score - random.randint(0, i * 3)
            elif lead["trend"] == "down":
                score = current_score + random.randint(0, i * 3)
            else:
                score = current_score + random.randint(-i * 2, i * 2)
            score = max(0, min(100, score))
            history.append(score)
        history.append(current_score)
        return history

    def _render_performance_summary(self, leads_data: List[Dict[str, Any]]):
        """Render performance summary metrics"""
        if not leads_data:
            return
        total_leads = len(leads_data)
        hot_leads = len([l for l in leads_data if l["status"] == "hot"])
        warm_leads = len([l for l in leads_data if l["status"] == "warm"])
        cold_leads = len([l for l in leads_data if l["status"] == "cold"])
        avg_score = sum((l["score"] for l in leads_data)) / total_leads if total_leads > 0 else 0
        trending_up = len([l for l in leads_data if l["trend"] == "up"])
        st.markdown("### 📊 Pipeline Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Leads", total_leads)
        with col2:
            st.metric(
                "🔥 Hot Leads", hot_leads, delta=f"{hot_leads / total_leads * 100:.1f}%" if total_leads > 0 else "0%"
            )
        with col3:
            st.metric("🌡️ Warm Leads", warm_leads)
        with col4:
            st.metric("❄️ Cold Leads", cold_leads)
        with col5:
            st.metric(
                "📈 Trending Up",
                trending_up,
                delta=f"{trending_up / total_leads * 100:.1f}%" if total_leads > 0 else "0%",
            )
        st.markdown("### 🎯 Average Pipeline Score")
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=avg_score,
                ontario_mills={"x": [0, 1], "y": [0, 1]},
                title={"text": "Pipeline Health"},
                delta={"reference": 70, "increasing": {"color": "green"}},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "yellow"},
                        {"range": [80, 100], "color": "green"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
                },
            )
        )
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)


def render_live_lead_scoreboard(realtime_service, state_manager):
    """Main function to render the live lead scoreboard"""
    scoreboard = LiveLeadScoreboard(realtime_service, state_manager)
    scoreboard.render()


if __name__ == "__main__":
    st.set_page_config(page_title="Live Lead Scoreboard Demo", page_icon="🎯", layout="wide")

    class MockRealtimeService:
        @st.cache_data(ttl=300)
        def get_recent_events(self, event_type=None, limit=50, since=None):

            return []

    class MockStateManager:
        class UserPreferences:
            auto_refresh = True
            compact_view = False

        user_preferences = UserPreferences()

    st.title("🎯 Live Lead Scoreboard Demo")
    render_live_lead_scoreboard(MockRealtimeService(), MockStateManager())
