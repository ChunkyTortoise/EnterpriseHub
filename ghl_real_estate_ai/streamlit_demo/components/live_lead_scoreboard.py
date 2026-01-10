"""
Live Lead Scoreboard Component for GHL Real Estate AI

Real-time animated lead scoring dashboard with:
- Live score updates and animations
- Priority-based visual indicators
- Mobile-responsive design
- Interactive drill-down capabilities
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import math
from typing import Dict, List, Any, Optional

def render_live_scoreboard_css():
    """Inject custom CSS for live scoreboard animations"""
    st.markdown("""
    <style>
    /* Live Scoreboard Animations */
    @keyframes pulse-hot {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
    }

    @keyframes pulse-warm {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 149, 0, 0.7); }
        70% { transform: scale(1.01); box-shadow: 0 0 0 5px rgba(255, 149, 0, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 149, 0, 0); }
    }

    @keyframes score-increase {
        0% { transform: scale(1) translateY(0); color: #28a745; }
        50% { transform: scale(1.1) translateY(-2px); color: #20c997; }
        100% { transform: scale(1) translateY(0); color: #28a745; }
    }

    @keyframes score-decrease {
        0% { transform: scale(1) translateY(0); color: #dc3545; }
        50% { transform: scale(0.95) translateY(2px); color: #e74c3c; }
        100% { transform: scale(1) translateY(0); color: #dc3545; }
    }

    .scoreboard-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }

    .scoreboard-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
        background-size: 200% 100%;
        animation: gradient-shift 3s ease infinite;
    }

    @keyframes gradient-shift {
        0% { background-position: 0% 0; }
        50% { background-position: 100% 0; }
        100% { background-position: 0% 0; }
    }

    .scoreboard-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25);
    }

    .score-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        margin: 0 auto 1rem;
        position: relative;
        overflow: hidden;
    }

    .score-hot {
        background: radial-gradient(circle, #ff4757, #ff3742);
        animation: pulse-hot 2s infinite;
    }

    .score-warm {
        background: radial-gradient(circle, #ffa502, #ff6348);
        animation: pulse-warm 3s infinite;
    }

    .score-cold {
        background: linear-gradient(135deg, #a4b0be, #747d8c);
    }

    .lead-name {
        font-size: 1.2rem;
        font-weight: 600;
        color: white;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .lead-details {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
        text-align: center;
        line-height: 1.4;
    }

    .score-trend {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 0.5rem;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .trend-up {
        color: #2ecc71;
        animation: score-increase 1s ease-in-out;
    }

    .trend-down {
        color: #e74c3c;
        animation: score-decrease 1s ease-in-out;
    }

    .trend-stable {
        color: #95a5a6;
    }

    .factors-list {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 1rem;
    }

    .factor-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.7rem;
        margin: 0.2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .scoreboard-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .live-indicator {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(45deg, #00b4db, #0083b0);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background: #2ecc71;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.2); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .scoreboard-card {
            padding: 1rem;
            margin: 0.25rem 0;
        }

        .score-circle {
            width: 60px;
            height: 60px;
            font-size: 1.2rem;
        }

        .lead-name {
            font-size: 1rem;
        }

        .lead-details {
            font-size: 0.8rem;
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .scoreboard-card {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
    }
    </style>
    """, unsafe_allow_html=True)

class LiveLeadScoreboard:
    """Live lead scoreboard with real-time updates and animations"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager
        self.last_update = datetime.now()

    def render(self, container_key: str = "live_scoreboard"):
        """Render the live lead scoreboard"""
        # Inject CSS
        render_live_scoreboard_css()

        # Header with live indicator
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div class="scoreboard-header">
                <div class="live-indicator">
                    <div class="live-dot"></div>
                    Live Lead Scoring
                </div>
                <h2 style="color: #2c3e50; margin: 0;">🎯 Active Lead Pipeline</h2>
            </div>
            """, unsafe_allow_html=True)

        # Get real-time lead data
        leads_data = self._get_live_leads_data()

        # Render scoreboard grid
        self._render_scoreboard_grid(leads_data)

        # Performance metrics
        self._render_performance_summary(leads_data)

        # Auto-refresh if enabled
        if self.state_manager.user_preferences.auto_refresh:
            time.sleep(0.1)  # Small delay for smooth animation
            st.rerun()

    def _get_live_leads_data(self) -> List[Dict[str, Any]]:
        """Get real-time lead scoring data"""
        try:
            # Get recent lead score events
            recent_events = self.realtime_service.get_recent_events(
                event_type="lead_score_update",
                limit=20,
                since=datetime.now() - timedelta(hours=1)
            )

            # If no real-time data, use demo data
            if not recent_events:
                from services.realtime_data_service import DemoDataGenerator
                return DemoDataGenerator.generate_lead_scores(12)

            # Process real-time events into lead data
            leads = []
            for event in recent_events:
                data = event.data
                leads.append({
                    'id': data.get('lead_id', 'unknown'),
                    'name': self._generate_lead_name(data.get('lead_id', '')),
                    'score': data.get('score', 0),
                    'previous_score': data.get('previous_score', 0),
                    'status': self._get_score_status(data.get('score', 0)),
                    'factors': data.get('factors', []),
                    'last_activity': event.timestamp,
                    'trend': self._calculate_trend(data.get('score', 0), data.get('previous_score', 0))
                })

            return sorted(leads, key=lambda x: x['score'], reverse=True)

        except Exception as e:
            st.error(f"Error loading live leads data: {e}")
            # Fallback to demo data
            from services.realtime_data_service import DemoDataGenerator
            return DemoDataGenerator.generate_lead_scores(8)

    def _generate_lead_name(self, lead_id: str) -> str:
        """Generate realistic lead names from ID"""
        names = [
            "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "David Kim",
            "Lisa Anderson", "James Wilson", "Maria Garcia", "Robert Taylor",
            "Jennifer Brown", "Christopher Lee", "Amanda Martinez", "Daniel White"
        ]
        import hashlib
        hash_val = int(hashlib.md5(lead_id.encode()).hexdigest(), 16)
        return names[hash_val % len(names)]

    def _get_score_status(self, score: int) -> str:
        """Determine lead status from score"""
        if score >= 80:
            return 'hot'
        elif score >= 60:
            return 'warm'
        else:
            return 'cold'

    def _calculate_trend(self, current: int, previous: int) -> str:
        """Calculate score trend"""
        if current > previous:
            return 'up'
        elif current < previous:
            return 'down'
        else:
            return 'stable'

    def _render_scoreboard_grid(self, leads_data: List[Dict[str, Any]]):
        """Render the main scoreboard grid"""
        # Determine grid layout based on preferences
        is_mobile = st.session_state.get('is_mobile', False)
        cols_per_row = 1 if is_mobile else (2 if self.state_manager.user_preferences.compact_view else 3)

        # Create grid
        for i in range(0, len(leads_data), cols_per_row):
            cols = st.columns(cols_per_row)

            for j in range(cols_per_row):
                if i + j < len(leads_data):
                    lead = leads_data[i + j]
                    with cols[j]:
                        self._render_lead_card(lead)

    def _render_lead_card(self, lead: Dict[str, Any]):
        """Render individual lead scoring card"""
        score = lead['score']
        status = lead['status']
        trend = lead['trend']

        # Trend indicators
        trend_icons = {
            'up': '📈 ↗️',
            'down': '📉 ↘️',
            'stable': '➡️'
        }

        trend_classes = {
            'up': 'trend-up',
            'down': 'trend-down',
            'stable': 'trend-stable'
        }

        # Format factors
        factors_html = ''.join([
            f'<span class="factor-badge">{factor.replace("_", " ").title()}</span>'
            for factor in lead['factors'][:4]  # Limit to 4 factors
        ])

        # Time since last activity
        time_diff = datetime.now() - lead['last_activity']
        time_str = self._format_time_diff(time_diff)

        # Render card
        st.markdown(f"""
        <div class="scoreboard-card">
            <div class="score-circle score-{status}">
                {score}
            </div>
            <div class="lead-name">{lead['name']}</div>
            <div class="lead-details">
                <div>ID: {lead['id']}</div>
                <div>Last Activity: {time_str}</div>
            </div>
            <div class="score-trend {trend_classes[trend]}">
                {trend_icons[trend]} {abs(score - lead['previous_score'])} pts
            </div>
            <div class="factors-list">
                {factors_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Add click interaction
        if st.button(f"View Details", key=f"lead_details_{lead['id']}", width='stretch'):
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

            # Score breakdown chart
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Current Score",
                    value=f"{lead['score']}",
                    delta=f"{lead['score'] - lead['previous_score']}"
                )

                st.metric(
                    label="Status",
                    value=lead['status'].title(),
                )

            with col2:
                # Score history simulation
                score_history = self._generate_score_history(lead)
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=list(range(len(score_history))),
                    y=score_history,
                    mode='lines+markers',
                    name='Score Trend',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=6)
                ))

                fig.update_layout(
                    title="Score Trend (Last 7 Days)",
                    xaxis_title="Days Ago",
                    yaxis_title="Score",
                    height=200,
                    margin=dict(l=0, r=0, t=30, b=0)
                )

                st.plotly_chart(fig, width='stretch')

            # Scoring factors analysis
            st.markdown("**🎯 Scoring Factors:**")
            factors_df = pd.DataFrame([
                {"Factor": factor.replace("_", " ").title(), "Impact": "High" if i < 2 else "Medium"}
                for i, factor in enumerate(lead['factors'])
            ])

            if not factors_df.empty:
                st.dataframe(factors_df, hide_index=True, width='stretch')

            # Action buttons
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

        current_score = lead['score']
        history = []

        # Generate 7 days of history
        for i in range(7, 0, -1):
            # Add some variance based on trend
            if lead['trend'] == 'up':
                score = current_score - random.randint(0, i * 3)
            elif lead['trend'] == 'down':
                score = current_score + random.randint(0, i * 3)
            else:
                score = current_score + random.randint(-i * 2, i * 2)

            # Clamp to valid range
            score = max(0, min(100, score))
            history.append(score)

        history.append(current_score)
        return history

    def _render_performance_summary(self, leads_data: List[Dict[str, Any]]):
        """Render performance summary metrics"""
        if not leads_data:
            return

        # Calculate metrics
        total_leads = len(leads_data)
        hot_leads = len([l for l in leads_data if l['status'] == 'hot'])
        warm_leads = len([l for l in leads_data if l['status'] == 'warm'])
        cold_leads = len([l for l in leads_data if l['status'] == 'cold'])

        avg_score = sum(l['score'] for l in leads_data) / total_leads if total_leads > 0 else 0
        trending_up = len([l for l in leads_data if l['trend'] == 'up'])

        # Render metrics
        st.markdown("### 📊 Pipeline Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Leads", total_leads)

        with col2:
            st.metric(
                "🔥 Hot Leads",
                hot_leads,
                delta=f"{(hot_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%"
            )

        with col3:
            st.metric("🌡️ Warm Leads", warm_leads)

        with col4:
            st.metric("❄️ Cold Leads", cold_leads)

        with col5:
            st.metric(
                "📈 Trending Up",
                trending_up,
                delta=f"{(trending_up/total_leads*100):.1f}%" if total_leads > 0 else "0%"
            )

        # Average score gauge
        st.markdown("### 🎯 Average Pipeline Score")

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Pipeline Health"},
            delta={'reference': 70, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(fig, width='stretch')


def render_live_lead_scoreboard(realtime_service, state_manager):
    """Main function to render the live lead scoreboard"""
    scoreboard = LiveLeadScoreboard(realtime_service, state_manager)
    scoreboard.render()


# Streamlit component integration
if __name__ == "__main__":
    # Demo mode for testing
    st.set_page_config(
        page_title="Live Lead Scoreboard Demo",
        page_icon="🎯",
        layout="wide"
    )

    # Mock services for demo
    class MockRealtimeService:
        def get_recent_events(self, event_type=None, limit=50, since=None):
            from services.realtime_data_service import DemoDataGenerator
            # Return empty to trigger demo data
            return []

    class MockStateManager:
        class UserPreferences:
            auto_refresh = True
            compact_view = False

        user_preferences = UserPreferences()

    # Render demo
    st.title("🎯 Live Lead Scoreboard Demo")
    render_live_lead_scoreboard(MockRealtimeService(), MockStateManager())