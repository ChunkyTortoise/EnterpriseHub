"""
AI-Powered Adaptive Dashboard Interface - Service 6 UX Enhancement
Comprehensive dashboard that learns and adapts to user behavior, providing personalized experiences
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant


@dataclass
class UserPreferences:
    """User preference model for dashboard personalization"""

    layout_type: str = "grid"  # grid, list, cards
    preferred_metrics: List[str] = None
    widget_positions: Dict[str, Tuple[int, int]] = None
    notification_settings: Dict[str, bool] = None
    theme_mode: str = "dark"  # dark, light, auto
    refresh_interval: int = 30  # seconds
    voice_enabled: bool = True
    mobile_layout: bool = False
    expertise_level: str = "intermediate"  # beginner, intermediate, expert

    def __post_init__(self):
        if self.preferred_metrics is None:
            self.preferred_metrics = ["hot_leads", "pipeline_value", "response_time", "conversion_rate"]
        if self.widget_positions is None:
            self.widget_positions = {}
        if self.notification_settings is None:
            self.notification_settings = {"hot_leads": True, "new_messages": True, "appointments": True}


@dataclass
class DashboardContext:
    """Context data for dashboard personalization"""

    user_id: str
    session_duration: int  # minutes
    actions_taken: List[str]
    focus_areas: List[str]
    time_of_day: str
    device_type: str
    current_page: str
    lead_interactions: Dict[str, int]


class AdaptiveDashboardInterface:
    """
    AI-powered dashboard interface that adapts to user behavior and preferences
    """

    def __init__(self):
        self.cache_service = get_cache_service()
        self.claude_assistant = ClaudeAssistant(context_type="dashboard_adaptive")
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables"""
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = UserPreferences()
        if "dashboard_context" not in st.session_state:
            st.session_state.dashboard_context = DashboardContext(
                user_id="jorge_executive",
                session_duration=0,
                actions_taken=[],
                focus_areas=[],
                time_of_day=self._get_time_of_day(),
                device_type=self._detect_device_type(),
                current_page="dashboard",
                lead_interactions={},
            )
        if "layout_state" not in st.session_state:
            st.session_state.layout_state = {}

    def _get_time_of_day(self) -> str:
        """Determine time of day for contextual adaptation"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _detect_device_type(self) -> str:
        """Detect device type for responsive design"""
        # In real implementation, this would check user agent
        return "desktop"  # Could be: mobile, tablet, desktop

    @st.cache_data(ttl=60)
    def _get_ai_insights(_self, context: DashboardContext, preferences: UserPreferences) -> Dict[str, Any]:
        """Generate AI-driven insights based on user context"""
        insights = {
            "priority_suggestion": "Focus on hot leads - you have 3 requiring immediate attention",
            "time_recommendation": f"Best time for outreach based on historical data: {context.time_of_day}",
            "efficiency_tip": "Consider batching similar activities to improve productivity",
            "market_alert": "Downtown Austin showing increased activity - consider prioritizing leads in this area",
            "personal_insight": f"You've been most successful with {context.focus_areas[0] if context.focus_areas else 'lead qualification'} today",
        }
        return insights

    def render_personalized_header(self):
        """Render adaptive header based on user context and preferences"""
        context = st.session_state.dashboard_context
        preferences = st.session_state.user_preferences

        # Time-based greeting
        greetings = {
            "morning": "🌅 Good Morning, Jorge",
            "afternoon": "☀️ Good Afternoon, Jorge",
            "evening": "🌇 Good Evening, Jorge",
            "night": "🌙 Working Late, Jorge?",
        }

        greeting = greetings.get(context.time_of_day, "👋 Hello, Jorge")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(
                f"""
            <div style='padding: 1rem 0;'>
                <h1 style='margin: 0; font-size: 2rem; font-weight: 700; color: #FFFFFF;'>{greeting}</h1>
                <p style='margin: 0.5rem 0 0 0; color: #8B949E; font-size: 1rem;'>
                    Here's your intelligent overview for today
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            # AI Insights Summary
            insights = self._get_ai_insights(context, preferences)
            st.info(f"💡 {insights['priority_suggestion']}")

        with col3:
            # Quick Settings
            with st.expander("⚙️ Dashboard Settings"):
                new_layout = st.selectbox(
                    "Layout Type",
                    ["grid", "list", "cards"],
                    index=["grid", "list", "cards"].index(preferences.layout_type),
                )

                new_refresh = st.slider("Auto-refresh (seconds)", 10, 300, preferences.refresh_interval)

                voice_enabled = st.checkbox("Voice Interface", value=preferences.voice_enabled)

                if st.button("Save Preferences"):
                    preferences.layout_type = new_layout
                    preferences.refresh_interval = new_refresh
                    preferences.voice_enabled = voice_enabled
                    st.session_state.user_preferences = preferences
                    st.rerun()

    def render_adaptive_metrics_grid(self):
        """Render metrics grid that adapts based on user preferences and behavior"""
        preferences = st.session_state.user_preferences
        context = st.session_state.dashboard_context

        st.markdown("### 📊 Smart Metrics Overview")

        # AI-curated metrics based on user behavior
        priority_metrics = self._get_priority_metrics(context, preferences)

        if preferences.layout_type == "grid":
            self._render_grid_layout(priority_metrics)
        elif preferences.layout_type == "list":
            self._render_list_layout(priority_metrics)
        else:
            self._render_cards_layout(priority_metrics)

    def _get_priority_metrics(self, context: DashboardContext, preferences: UserPreferences) -> Dict[str, Any]:
        """AI-driven metric prioritization based on user behavior"""
        base_metrics = {
            "hot_leads": {"value": 3, "change": "+2", "priority": 10, "color": "#10B981"},
            "pipeline_value": {"value": "$2.4M", "change": "+15%", "priority": 9, "color": "#6366F1"},
            "response_time": {"value": "2.3m", "change": "-30s", "priority": 8, "color": "#8B5CF6"},
            "conversion_rate": {"value": "27%", "change": "+5%", "priority": 8, "color": "#F59E0B"},
            "agent_efficiency": {"value": "94%", "change": "+2%", "priority": 7, "color": "#EF4444"},
            "market_velocity": {"value": "78", "change": "+12", "priority": 6, "color": "#06B6D4"},
        }

        # Boost priority based on user interactions
        for area in context.focus_areas:
            if area in base_metrics:
                base_metrics[area]["priority"] += 3

        # Sort by priority and return top metrics based on preferences
        sorted_metrics = sorted(base_metrics.items(), key=lambda x: x[1]["priority"], reverse=True)
        return dict(sorted_metrics[: len(preferences.preferred_metrics)])

    def _render_grid_layout(self, metrics: Dict[str, Any]):
        """Render metrics in grid layout"""
        cols = st.columns(len(metrics))

        for i, (key, data) in enumerate(metrics.items()):
            with cols[i]:
                self._render_metric_card(key.replace("_", " ").title(), data["value"], data["change"], data["color"])

    def _render_list_layout(self, metrics: Dict[str, Any]):
        """Render metrics in list layout"""
        for key, data in metrics.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{key.replace('_', ' ').title()}**")
            with col2:
                st.markdown(f"**{data['value']}**")
            with col3:
                change_color = "#10B981" if data["change"].startswith("+") else "#EF4444"
                st.markdown(f"<span style='color: {change_color}'>{data['change']}</span>", unsafe_allow_html=True)

    def _render_cards_layout(self, metrics: Dict[str, Any]):
        """Render metrics in card layout"""
        for key, data in metrics.items():
            with st.container():
                self._render_metric_card(key.replace("_", " ").title(), data["value"], data["change"], data["color"])

    def _render_metric_card(self, title: str, value: str, change: str, color: str):
        """Render individual metric card with AI-enhanced styling"""
        st.markdown(
            f"""
        <div style='
            background: rgba(22, 27, 34, 0.8);
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid {color};
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        '>
            <div style='
                font-size: 0.75rem;
                opacity: 0.8;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: {color};
                margin-bottom: 0.5rem;
            '>{title}</div>
            <div style='
                font-size: 2.5rem;
                font-weight: 700;
                color: #FFFFFF;
                margin-bottom: 0.5rem;
            '>{value}</div>
            <div style='
                font-size: 0.8rem;
                color: {"#10B981" if change.startswith("+") else "#EF4444"};
                font-weight: 600;
            '>{change}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_intelligent_recommendations(self):
        """Render AI-driven recommendations panel"""
        st.markdown("### 🧠 Intelligent Recommendations")

        context = st.session_state.dashboard_context
        preferences = st.session_state.user_preferences

        # Get AI insights
        insights = self._get_ai_insights(context, preferences)

        # Recommendation cards
        recommendations = [
            {
                "type": "action",
                "title": "Priority Action",
                "message": insights["priority_suggestion"],
                "action": "Review Hot Leads",
                "urgency": "high",
            },
            {
                "type": "optimization",
                "title": "Efficiency Tip",
                "message": insights["efficiency_tip"],
                "action": "Optimize Workflow",
                "urgency": "medium",
            },
            {
                "type": "market",
                "title": "Market Intelligence",
                "message": insights["market_alert"],
                "action": "View Market Data",
                "urgency": "medium",
            },
            {
                "type": "personal",
                "title": "Personal Insight",
                "message": insights["personal_insight"],
                "action": "Continue Focus",
                "urgency": "low",
            },
        ]

        for rec in recommendations:
            urgency_colors = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}

            urgency_color = urgency_colors.get(rec["urgency"], "#6366F1")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(
                    f"""
                <div style='
                    background: rgba(22, 27, 34, 0.6);
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 3px solid {urgency_color};
                    margin-bottom: 0.8rem;
                    border: 1px solid rgba(255,255,255,0.05);
                '>
                    <div style='
                        font-size: 0.9rem;
                        font-weight: 700;
                        color: {urgency_color};
                        margin-bottom: 0.5rem;
                    '>{rec["title"]}</div>
                    <div style='
                        color: #E6EDF3;
                        font-size: 0.85rem;
                        line-height: 1.4;
                    '>{rec["message"]}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                if st.button(rec["action"], key=f"rec_{rec['type']}", use_container_width=True):
                    st.session_state.dashboard_context.actions_taken.append(rec["action"])
                    st.toast(f"✅ {rec['action']} initiated")

    def render_contextual_widgets(self):
        """Render context-aware widgets based on user behavior"""
        st.markdown("### 🎯 Smart Widgets")

        context = st.session_state.dashboard_context

        col1, col2 = st.columns(2)

        with col1:
            # Time-based widget
            if context.time_of_day == "morning":
                self._render_morning_briefing()
            elif context.time_of_day == "afternoon":
                self._render_afternoon_summary()
            else:
                self._render_evening_wrap()

        with col2:
            # Behavior-based widget
            if "hot_leads" in context.focus_areas:
                self._render_hot_leads_focus()
            else:
                self._render_general_pipeline()

    def _render_morning_briefing(self):
        """Morning briefing widget"""
        st.markdown("#### 🌅 Morning Briefing")

        briefing_data = {
            "overnight_leads": 2,
            "scheduled_calls": 4,
            "priority_tasks": 3,
            "weather_note": "Perfect showing weather today - 75°F",
        }

        st.markdown(
            f"""
        <div style='background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2);'>
            <p>📋 <strong>{briefing_data["priority_tasks"]} priority tasks</strong> for today</p>
            <p>📞 <strong>{briefing_data["scheduled_calls"]} calls</strong> scheduled</p>
            <p>🌟 <strong>{briefing_data["overnight_leads"]} new leads</strong> overnight</p>
            <p>☀️ {briefing_data["weather_note"]}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_afternoon_summary(self):
        """Afternoon progress widget"""
        st.markdown("#### ☀️ Progress Update")

        progress_data = {"calls_completed": 6, "calls_planned": 8, "appointments_set": 2, "hot_leads_contacted": 2}

        completion_rate = (progress_data["calls_completed"] / progress_data["calls_planned"]) * 100

        st.markdown(
            f"""
        <div style='background: rgba(245, 158, 11, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(245, 158, 11, 0.2);'>
            <p>📈 <strong>{completion_rate:.0f}% daily progress</strong></p>
            <p>📞 {progress_data["calls_completed"]}/{progress_data["calls_planned"]} calls completed</p>
            <p>📅 <strong>{progress_data["appointments_set"]} appointments</strong> scheduled</p>
            <p>🔥 <strong>{progress_data["hot_leads_contacted"]} hot leads</strong> contacted</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_evening_wrap(self):
        """Evening wrap-up widget"""
        st.markdown("#### 🌇 Daily Wrap-up")

        wrap_data = {
            "total_interactions": 15,
            "leads_advanced": 4,
            "revenue_generated": "$125K",
            "tomorrow_prep": "3 hot leads to prioritize",
        }

        st.markdown(
            f"""
        <div style='background: rgba(139, 92, 246, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.2);'>
            <p>✅ <strong>{wrap_data["total_interactions"]} interactions</strong> today</p>
            <p>📈 <strong>{wrap_data["leads_advanced"]} leads</strong> advanced in pipeline</p>
            <p>💰 <strong>{wrap_data["revenue_generated"]} potential</strong> revenue identified</p>
            <p>🎯 Tomorrow: {wrap_data["tomorrow_prep"]}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_hot_leads_focus(self):
        """Hot leads focused widget"""
        st.markdown("#### 🔥 Hot Leads Focus")

        hot_leads = [
            {"name": "Sarah Martinez", "status": "Viewing scheduled", "urgency": "Today 3PM"},
            {"name": "Mike Johnson", "status": "Offer pending", "urgency": "Response due"},
            {"name": "Jennifer Wu", "status": "Ready to close", "urgency": "High priority"},
        ]

        for lead in hot_leads:
            st.markdown(
                f"""
            <div style='
                background: rgba(239, 68, 68, 0.1);
                padding: 0.8rem;
                border-radius: 6px;
                margin-bottom: 0.5rem;
                border-left: 3px solid #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.2);
            '>
                <div style='font-weight: 600; color: #FFFFFF;'>{lead["name"]}</div>
                <div style='font-size: 0.8rem; color: #E6EDF3; margin-top: 0.3rem;'>{lead["status"]}</div>
                <div style='font-size: 0.75rem; color: #EF4444; margin-top: 0.3rem;'>{lead["urgency"]}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def _render_general_pipeline(self):
        """General pipeline widget"""
        st.markdown("#### 📊 Pipeline Overview")

        pipeline_data = {"new": 12, "qualifying": 8, "hot": 3, "closing": 2}

        total = sum(pipeline_data.values())

        for stage, count in pipeline_data.items():
            percentage = (count / total) * 100
            color_map = {"new": "#6366F1", "qualifying": "#F59E0B", "hot": "#EF4444", "closing": "#10B981"}

            st.markdown(
                f"""
            <div style='
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            '>
                <span style='color: #E6EDF3; text-transform: capitalize;'>{stage}</span>
                <div style='display: flex; align-items: center; gap: 0.5rem;'>
                    <span style='color: #FFFFFF; font-weight: 600;'>{count}</span>
                    <div style='
                        width: 60px;
                        height: 6px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 3px;
                        overflow: hidden;
                    '>
                        <div style='
                            width: {percentage}%;
                            height: 100%;
                            background: {color_map[stage]};
                        '></div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def render_voice_interface_toggle(self):
        """Render voice interface controls"""
        if st.session_state.user_preferences.voice_enabled:
            st.markdown("### 🎤 Voice Assistant")

            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                voice_active = st.button("🎤 Activate Voice", use_container_width=True)

                if voice_active:
                    st.markdown(
                        """
                    <div style='
                        background: rgba(16, 185, 129, 0.1);
                        padding: 1rem;
                        border-radius: 8px;
                        border: 1px solid rgba(16, 185, 129, 0.3);
                        text-align: center;
                        animation: pulse 2s infinite;
                    '>
                        🎤 <strong>Listening...</strong><br>
                        <span style='font-size: 0.8rem; color: #8B949E;'>
                            Say "Hey Claude" to start
                        </span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

    async def save_user_preferences(self):
        """Save user preferences to cache for persistence"""
        try:
            preferences_data = asdict(st.session_state.user_preferences)
            await self.cache_service.set(
                f"user_preferences_{st.session_state.dashboard_context.user_id}",
                preferences_data,
                ttl=86400,  # 24 hours
            )
        except Exception as e:
            st.error(f"Failed to save preferences: {e}")

    def render_complete_adaptive_dashboard(self):
        """Render the complete adaptive dashboard interface"""
        st.set_page_config(
            page_title="Service 6 - Adaptive Intelligence Dashboard",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Apply AI-enhanced styling
        st.markdown(
            """
        <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .main > div {
            padding-top: 2rem;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Header
        self.render_personalized_header()

        st.markdown("---")

        # Main dashboard content
        self.render_adaptive_metrics_grid()

        st.markdown("---")

        # Two-column layout for recommendations and widgets
        col1, col2 = st.columns([2, 1])

        with col1:
            self.render_intelligent_recommendations()

        with col2:
            self.render_contextual_widgets()

        st.markdown("---")

        # Voice interface (if enabled)
        self.render_voice_interface_toggle()

        # Auto-refresh logic
        if st.session_state.user_preferences.refresh_interval > 0:
            # In a real implementation, you would use a proper auto-refresh mechanism
            # For demo purposes, we show a countdown
            st.markdown(
                f"""
            <div style='
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(22, 27, 34, 0.9);
                padding: 0.5rem 1rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.1);
                color: #8B949E;
                font-size: 0.75rem;
                backdrop-filter: blur(10px);
            '>
                Auto-refresh in {st.session_state.user_preferences.refresh_interval}s
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Update context with current session
        st.session_state.dashboard_context.session_duration += 1
        if "dashboard" not in st.session_state.dashboard_context.focus_areas:
            st.session_state.dashboard_context.focus_areas.append("dashboard")


def render_adaptive_dashboard_interface():
    """Main function to render the adaptive dashboard interface"""
    dashboard = AdaptiveDashboardInterface()
    dashboard.render_complete_adaptive_dashboard()


if __name__ == "__main__":
    render_adaptive_dashboard_interface()
