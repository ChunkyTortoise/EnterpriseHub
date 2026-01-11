"""
Unified Intelligence Dashboard - Complete Lead Intelligence Command Center

Integrates all dashboard components into a single, powerful interface:
- Existing agent assistance functionality
- New advanced intelligence visualizations
- Real-time Claude AI data streams
- Performance monitoring and analytics
- Unified user experience

This serves as the main entry point for agents to access all lead intelligence capabilities.
"""

import streamlit as st
import asyncio
import json
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Import existing dashboard components
from .agent_assistance_dashboard import AgentAssistanceDashboard, create_agent_dashboard
from .enhanced_lead_intelligence_dashboard import EnhancedLeadIntelligenceDashboard
from .advanced_intelligence_visualizations import (
    AdvancedIntelligenceVisualizations,
    create_advanced_visualizations,
    LeadJourneyStage,
    SentimentAnalysis,
    CompetitiveIntelligence,
    ContentRecommendation,
    generate_sample_journey_stages,
    generate_sample_sentiment_data,
    generate_sample_competitive_data,
    generate_sample_content_recommendations
)

# Import Claude AI services for real-time data
try:
    from ..services.claude_agent_service import get_claude_agent_service
    from ..services.claude_semantic_analyzer import get_claude_semantic_analyzer
    from ..services.qualification_orchestrator import get_qualification_orchestrator
    from ..services.claude_action_planner import get_claude_action_planner
    CLAUDE_SERVICES_AVAILABLE = True
except ImportError:
    CLAUDE_SERVICES_AVAILABLE = False

# === UNIFIED ENTERPRISE THEME INTEGRATION ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_ENTERPRISE_THEME_AVAILABLE = True
except ImportError:
    UNIFIED_ENTERPRISE_THEME_AVAILABLE = False


class UnifiedIntelligenceDashboard:
    """
    Unified dashboard combining all lead intelligence capabilities.

    Provides a single interface for agents to access:
    - Real-time coaching and assistance
    - Advanced lead journey mapping
    - Sentiment analysis and emotional intelligence
    - Competitive intelligence insights
    - Intelligent content recommendations
    - Performance analytics and monitoring
    """

    def __init__(self, location_id: Optional[str] = None, agent_id: Optional[str] = None):
        """
        Initialize unified dashboard with optional context.

        Args:
            location_id: GHL location identifier for scoped data
            agent_id: Agent identifier for personalized experience
        """
        self.location_id = location_id
        self.agent_id = agent_id

        # Initialize dashboard components
        self.agent_dashboard = create_agent_dashboard()
        self.enhanced_dashboard = EnhancedLeadIntelligenceDashboard()
        self.advanced_viz = create_advanced_visualizations()

        # Initialize Claude services if available
        self.claude_services = {}
        if CLAUDE_SERVICES_AVAILABLE:
            self._init_claude_services()

        # Dashboard state management
        if 'unified_dashboard_state' not in st.session_state:
            st.session_state.unified_dashboard_state = {
                'active_lead_id': None,
                'dashboard_mode': 'overview',
                'real_time_enabled': True,
                'auto_refresh_interval': 5,  # seconds
                'performance_metrics': {},
                'user_preferences': self._load_user_preferences()
            }

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def _init_claude_services(self):
        """Initialize Claude AI services for real-time data."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.claude_services = {
                'agent_service': loop.run_until_complete(get_claude_agent_service()),
                'semantic_analyzer': loop.run_until_complete(get_claude_semantic_analyzer()),
                'qualification_orchestrator': loop.run_until_complete(get_qualification_orchestrator()),
                'action_planner': loop.run_until_complete(get_claude_action_planner())
            }

            self.logger.info("Claude services initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing Claude services: {e}")
            self.claude_services = {}

    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences for dashboard customization."""
        default_preferences = {
            'theme': 'professional',
            'layout': 'tabbed',
            'auto_refresh': True,
            'notifications': True,
            'coaching_frequency': 'medium',
            'analytics_depth': 'detailed'
        }

        # In production, this would load from user settings storage
        return default_preferences

    def render_main_dashboard(self):
        """Render the main unified dashboard interface."""

        # Page configuration
        st.set_page_config(
            page_title="🧠 Unified Intelligence Dashboard",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Enhanced CSS styling
        self._apply_custom_styling()

        # Dashboard header with real-time status
        self._render_dashboard_header()

        # Sidebar navigation and controls
        self._render_sidebar_navigation()

        # Main dashboard content based on selected mode
        dashboard_mode = st.session_state.unified_dashboard_state.get('dashboard_mode', 'overview')

        if dashboard_mode == 'overview':
            self._render_overview_dashboard()
        elif dashboard_mode == 'real_time_coaching':
            self._render_real_time_coaching()
        elif dashboard_mode == 'lead_journey':
            self._render_lead_journey_intelligence()
        elif dashboard_mode == 'sentiment_analysis':
            self._render_sentiment_intelligence()
        elif dashboard_mode == 'competitive_intel':
            self._render_competitive_intelligence()
        elif dashboard_mode == 'content_engine':
            self._render_content_intelligence()
        elif dashboard_mode == 'performance_analytics':
            self._render_performance_analytics()
        elif dashboard_mode == 'unified_view':
            self._render_unified_intelligence_view()

        # Real-time updates footer
        self._render_real_time_footer()

    def _apply_custom_styling(self):
        """Apply enhanced CSS styling for unified experience."""
        st.markdown("""
        <style>
        /* Unified Dashboard Theme */
        .unified-header {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 25%, #8b5cf6 50%, #ec4899 75%, #f59e0b 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        .status-live { background: #10b981; }
        .status-warning { background: #f59e0b; }
        .status-error { background: #ef4444; }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .intelligence-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid var(--primary-color, #3b82f6);
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .intelligence-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }

        .nav-button {
            width: 100%;
            padding: 0.75rem;
            margin: 0.25rem 0;
            border: none;
            border-radius: 8px;
            background: #f8fafc;
            border-left: 4px solid transparent;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .nav-button:hover {
            background: #e2e8f0;
            border-left-color: #3b82f6;
            transform: translateX(4px);
        }

        .nav-button.active {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            border-left-color: #1e293b;
        }

        .real-time-badge {
            background: #10b981;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .performance-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: #64748b;
        }

        /* Advanced Animation Effects */
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .slide-in-left {
            animation: slideInLeft 0.3s ease-out;
        }

        @keyframes slideInLeft {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .unified-header {
                padding: 1rem;
                text-align: center;
            }

            .metric-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def _render_dashboard_header(self):
        """Render enhanced dashboard header with status indicators."""
        # Get real-time status
        claude_status = "live" if CLAUDE_SERVICES_AVAILABLE else "warning"
        services_status = "live" if len(self.claude_services) > 0 else "error"

        current_time = datetime.now().strftime("%H:%M:%S")

        st.markdown(f"""
        <div class="unified-header fade-in">
            <h1 style="color: white; margin: 0; font-size: 2.5rem;">🧠 Unified Intelligence Dashboard</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0; font-size: 1.1rem;">
                Complete Lead Intelligence Command Center
            </p>
            <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
                <div class="real-time-badge">
                    <span class="status-indicator status-{claude_status}"></span>
                    Claude AI: {'Online' if claude_status == 'live' else 'Limited'}
                </div>
                <div class="real-time-badge">
                    <span class="status-indicator status-{services_status}"></span>
                    Services: {len(self.claude_services)}/4 Active
                </div>
                <div class="real-time-badge">
                    <span class="status-indicator status-live"></span>
                    Last Update: {current_time}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_sidebar_navigation(self):
        """Render enhanced sidebar navigation with user preferences."""
        st.sidebar.markdown("## 🎛️ Intelligence Center")

        # Navigation modes
        navigation_options = {
            'overview': '🏠 Dashboard Overview',
            'real_time_coaching': '⚡ Real-Time Coaching',
            'lead_journey': '🗺️ Lead Journey Intelligence',
            'sentiment_analysis': '🎭 Sentiment Analysis',
            'competitive_intel': '🏆 Competitive Intelligence',
            'content_engine': '🎨 Content Intelligence',
            'performance_analytics': '📊 Performance Analytics',
            'unified_view': '🌟 Unified Intelligence View'
        }

        # Custom navigation with enhanced styling
        st.sidebar.markdown("### Navigation")
        for mode_key, mode_label in navigation_options.items():
            if st.sidebar.button(mode_label, key=f"nav_{mode_key}"):
                st.session_state.unified_dashboard_state['dashboard_mode'] = mode_key
                st.rerun()

        st.sidebar.markdown("---")

        # Active lead selection
        st.sidebar.markdown("### 👤 Active Lead")
        lead_options = ["Select Lead...", "LEAD_001 - John Smith", "LEAD_002 - Sarah Jones", "LEAD_003 - Mike Wilson"]
        selected_lead = st.sidebar.selectbox("Current Lead", lead_options)

        if selected_lead != "Select Lead...":
            st.session_state.unified_dashboard_state['active_lead_id'] = selected_lead.split(' - ')[0]

        # Real-time controls
        st.sidebar.markdown("### ⚙️ Real-Time Controls")

        real_time_enabled = st.sidebar.toggle(
            "Enable Real-Time Updates",
            value=st.session_state.unified_dashboard_state.get('real_time_enabled', True)
        )
        st.session_state.unified_dashboard_state['real_time_enabled'] = real_time_enabled

        if real_time_enabled:
            refresh_interval = st.sidebar.slider(
                "Update Interval (seconds)",
                min_value=1,
                max_value=30,
                value=st.session_state.unified_dashboard_state.get('auto_refresh_interval', 5)
            )
            st.session_state.unified_dashboard_state['auto_refresh_interval'] = refresh_interval

        # Performance metrics
        st.sidebar.markdown("### 📈 Quick Metrics")

        # Simulated real-time metrics
        response_time = 45 + (time.time() % 10) * 2  # Simulate variance
        active_sessions = 12 + int(time.time() % 5)

        st.sidebar.metric("Avg Response Time", f"{response_time:.0f}ms", "↓8ms")
        st.sidebar.metric("Active Sessions", str(active_sessions), f"↑{int(time.time() % 3)}")
        st.sidebar.metric("Claude Accuracy", "98.3%", "↑0.2%")

        # User preferences
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎨 Preferences")

        theme_preference = st.sidebar.selectbox(
            "Dashboard Theme",
            ["Professional", "Dark Mode", "High Contrast"],
            index=0
        )

        notification_level = st.sidebar.selectbox(
            "Notification Level",
            ["All Alerts", "Important Only", "Quiet Mode"],
            index=1
        )

    def _render_overview_dashboard(self):
        """Render comprehensive overview dashboard."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Key metrics overview
        if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
            enterprise_section_header(
                title="🎯 Intelligence Overview",
                subtitle="Unified metrics and insights across all lead intelligence capabilities",
                icon="🎯"
            )

            # Prepare intelligence overview metrics for unified enterprise display
            overview_metrics = [
                {
                    "label": "👥 Active Leads",
                    "value": "47",
                    "delta": "↑12% this week",
                    "delta_type": "positive",
                    "icon": "👥"
                },
                {
                    "label": "⚡ Coaching Sessions",
                    "value": "156",
                    "delta": "↑15% today",
                    "delta_type": "positive",
                    "icon": "⚡"
                },
                {
                    "label": "🎯 Conversion Rate",
                    "value": "34.2%",
                    "delta": "↑8.5% vs last month",
                    "delta_type": "positive",
                    "icon": "🎯"
                },
                {
                    "label": "📈 Agent Efficiency",
                    "value": "94.7%",
                    "delta": "↑6.2% with AI",
                    "delta_type": "positive",
                    "icon": "📈"
                }
            ]

            enterprise_kpi_grid(overview_metrics, columns=4)
        else:
            # Legacy fallback styling
            st.markdown("## 🎯 Intelligence Overview")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Active Leads", "47", "↑12%")

            with col2:
                st.metric("Coaching Sessions", "156", "↑15%")

            with col3:
                st.metric("Conversion Rate", "34.2%", "↑8.5%")

            with col4:
                st.metric("Agent Efficiency", "94.7%", "↑6.2%")

        # Intelligence capabilities status
        st.markdown("### 🚀 Intelligence Capabilities Status")

        capabilities = [
            {"name": "Real-Time Coaching", "status": "active", "performance": "98.5%", "last_used": "2 min ago"},
            {"name": "Lead Journey Mapping", "status": "active", "performance": "96.2%", "last_used": "5 min ago"},
            {"name": "Sentiment Analysis", "status": "active", "performance": "94.8%", "last_used": "1 min ago"},
            {"name": "Competitive Intelligence", "status": "active", "performance": "91.3%", "last_used": "15 min ago"},
            {"name": "Content Recommendations", "status": "active", "performance": "89.7%", "last_used": "8 min ago"}
        ]

        for capability in capabilities:
            status_color = "#10b981" if capability["status"] == "active" else "#f59e0b"

            st.markdown(f"""
            <div class="intelligence-card slide-in-left">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #1e293b;">{capability["name"]}</h4>
                        <div class="performance-indicator">
                            <span class="status-indicator" style="background: {status_color};"></span>
                            Performance: {capability["performance"]} | Last Used: {capability["last_used"]}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {status_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">
                            {capability["status"].upper()}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Recent activity and insights
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 Recent Intelligence Activity")

            recent_activities = [
                "🎯 High-intent lead identified: LEAD_003 (Score: 94)",
                "💬 Real-time coaching delivered: Objection handling",
                "🗺️ Journey progression: LEAD_001 → Property Evaluation",
                "🎭 Sentiment shift detected: Positive → Highly Engaged",
                "🏆 Competitive advantage identified: AI technology edge"
            ]

            for activity in recent_activities:
                st.markdown(f"• {activity}")

        with col2:
            st.markdown("### 🧠 AI Insights Summary")

            insights = [
                "💡 15% increase in conversion when coaching is applied within 30 seconds",
                "📊 Morning calls show 23% higher engagement rates",
                "🎯 Leads mentioning timeline show 67% higher urgency",
                "💬 Empathetic coaching approach performs 34% better for objections",
                "🏠 Property matching accuracy improved to 95.2% with sentiment data"
            ]

            for insight in insights:
                st.markdown(f"• {insight}")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_real_time_coaching(self):
        """Render real-time coaching interface with live data."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        st.markdown("## ⚡ Real-Time Coaching Intelligence")

        # Check for active lead
        active_lead_id = st.session_state.unified_dashboard_state.get('active_lead_id')

        if not active_lead_id:
            st.warning("👤 Please select an active lead from the sidebar to begin real-time coaching.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Get real-time coaching data
        coaching_data = self._get_real_time_coaching_data(active_lead_id)

        # Render coaching interface using existing agent dashboard
        if coaching_data:
            # Live coaching suggestions
            self.advanced_viz.render_live_coaching_panel(
                agent_id=self.agent_id or "AGENT_DEMO",
                coaching_suggestions=coaching_data.get('suggestions', []),
                urgency=coaching_data.get('urgency', 'medium'),
                conversation_stage=coaching_data.get('stage', 'discovery'),
                last_updated=datetime.now()
            )

            # Objection analysis if detected
            if coaching_data.get('objection_detected'):
                self.advanced_viz.render_claude_objection_assistant(
                    objection_type=coaching_data.get('objection_type', 'price'),
                    severity=coaching_data.get('objection_severity', 'medium'),
                    suggested_responses=coaching_data.get('objection_responses', []),
                    talking_points=coaching_data.get('talking_points', []),
                    follow_up_strategy=coaching_data.get('follow_up_strategy', 'Address concerns with empathy')
                )

            # Next question recommendations
            if coaching_data.get('next_question'):
                self.advanced_viz.render_claude_question_guide(
                    suggested_question=coaching_data['next_question'],
                    purpose=coaching_data.get('question_purpose', 'qualification'),
                    priority=coaching_data.get('question_priority', 'high'),
                    expected_info=coaching_data.get('expected_info', 'Lead qualification data'),
                    follow_up_questions=coaching_data.get('follow_up_questions', [])
                )

        else:
            st.info("🎯 Ready to provide real-time coaching. Start a conversation with the lead.")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_lead_journey_intelligence(self):
        """Render advanced lead journey mapping with real-time data."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Get active lead
        active_lead_id = st.session_state.unified_dashboard_state.get('active_lead_id')

        if not active_lead_id:
            st.warning("👤 Please select an active lead from the sidebar to view journey intelligence.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Get journey data (simulate for demo, would be real data in production)
        journey_stages = self._get_lead_journey_data(active_lead_id)
        lead_name = self._get_lead_name(active_lead_id)

        # Render advanced journey map
        self.advanced_viz.render_advanced_lead_journey_map(
            lead_id=active_lead_id,
            lead_name=lead_name,
            journey_stages=journey_stages,
            real_time_updates=st.session_state.unified_dashboard_state.get('real_time_enabled', True)
        )

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_sentiment_intelligence(self):
        """Render sentiment analysis with real-time emotional intelligence."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Get active lead
        active_lead_id = st.session_state.unified_dashboard_state.get('active_lead_id')

        if not active_lead_id:
            st.warning("👤 Please select an active lead from the sidebar to view sentiment analysis.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Get sentiment data
        sentiment_data = self._get_sentiment_data(active_lead_id)

        # Render sentiment dashboard
        self.advanced_viz.render_realtime_sentiment_dashboard(
            sentiment_data=sentiment_data,
            current_conversation="Active conversation analysis"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_competitive_intelligence(self):
        """Render competitive intelligence dashboard."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Get competitive data
        competitive_data = self._get_competitive_intelligence_data()

        # Render competitive dashboard
        self.advanced_viz.render_competitive_intelligence_dashboard(
            competitive_data=competitive_data,
            market_trends=self._get_market_trends()
        )

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_content_intelligence(self):
        """Render intelligent content recommendation engine."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Get active lead
        active_lead_id = st.session_state.unified_dashboard_state.get('active_lead_id')

        if not active_lead_id:
            st.warning("👤 Please select an active lead from the sidebar to view content recommendations.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Get lead profile and content recommendations
        lead_profile = self._get_lead_profile(active_lead_id)
        content_recommendations = self._get_content_recommendations(active_lead_id, lead_profile)

        # Render content engine
        self.advanced_viz.render_intelligent_content_engine(
            lead_profile=lead_profile,
            content_recommendations=content_recommendations
        )

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_performance_analytics(self):
        """Render comprehensive performance analytics."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        st.markdown("## 📊 Performance Analytics Dashboard")

        # Performance overview metrics
        if UNIFIED_ENTERPRISE_THEME_AVAILABLE:
            # Prepare performance metrics for unified enterprise display
            performance_metrics = [
                {
                    "label": "⚡ Dashboard Load Time",
                    "value": "0.42s",
                    "delta": "↓0.18s",
                    "delta_type": "positive",
                    "icon": "⚡"
                },
                {
                    "label": "🧠 Claude Response Time",
                    "value": "45ms",
                    "delta": "↓8ms",
                    "delta_type": "positive",
                    "icon": "🧠"
                },
                {
                    "label": "🔧 Data Processing",
                    "value": "125ms",
                    "delta": "↓35ms",
                    "delta_type": "positive",
                    "icon": "🔧"
                },
                {
                    "label": "💾 Cache Hit Rate",
                    "value": "94.2%",
                    "delta": "↑3.1%",
                    "delta_type": "positive",
                    "icon": "💾"
                }
            ]

            enterprise_kpi_grid(performance_metrics, columns=4)
        else:
            # Legacy fallback styling
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Dashboard Load Time", "0.42s", "↓0.18s")

            with col2:
                st.metric("Claude Response Time", "45ms", "↓8ms")

            with col3:
                st.metric("Data Processing", "125ms", "↓35ms")

            with col4:
                st.metric("Cache Hit Rate", "94.2%", "↑3.1%")

        # Performance trends chart
        st.markdown("### 📈 Performance Trends (Last 24 Hours)")

        # Generate sample performance data
        hours = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='H')
        response_times = [45 + 10 * (0.5 - abs(h.hour - 12) / 24) + 5 * (h.hour % 3) for h in hours]
        accuracy_scores = [94 + 4 * (0.5 - abs(h.hour - 14) / 24) + 2 * (h.hour % 4) for h in hours]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=hours,
            y=response_times,
            mode='lines+markers',
            name='Response Time (ms)',
            line=dict(color='#ef4444', width=3),
            yaxis='y'
        ))

        fig.add_trace(go.Scatter(
            x=hours,
            y=accuracy_scores,
            mode='lines+markers',
            name='Accuracy (%)',
            line=dict(color='#10b981', width=3),
            yaxis='y2'
        ))

        fig.update_layout(
            title='System Performance Over Time',
            xaxis_title='Time',
            yaxis=dict(title='Response Time (ms)', side='left'),
            yaxis2=dict(title='Accuracy (%)', side='right', overlaying='y'),
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Component performance breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🔧 Component Performance")

            component_data = {
                'Component': ['Claude API', 'Sentiment Analysis', 'Journey Mapping', 'Content Engine'],
                'Response Time': [45, 67, 123, 89],
                'Accuracy': [98.3, 94.8, 96.2, 89.7],
                'Uptime': [99.9, 99.7, 99.8, 99.4]
            }

            component_df = pd.DataFrame(component_data)
            st.dataframe(component_df, use_container_width=True)

        with col2:
            st.markdown("### 💡 Performance Insights")

            insights = [
                "✅ All systems operating within optimal parameters",
                "🚀 Response time improved 18% with new optimizations",
                "📈 Cache hit rate increased 3.1% reducing API calls",
                "⚠️ Peak hour performance shows slight degradation",
                "🎯 Accuracy maintained above 94% across all components"
            ]

            for insight in insights:
                st.markdown(f"• {insight}")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_unified_intelligence_view(self):
        """Render unified view combining all intelligence capabilities."""
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        st.markdown("## 🌟 Unified Intelligence View")
        st.info("🎯 **Complete Intelligence Overview**: All capabilities in one unified interface")

        # Get active lead
        active_lead_id = st.session_state.unified_dashboard_state.get('active_lead_id')

        if not active_lead_id:
            st.warning("👤 Please select an active lead from the sidebar to view unified intelligence.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Create tabbed interface for unified view
        tab1, tab2, tab3 = st.tabs(["🎯 Live Intelligence", "📊 Deep Analytics", "🚀 Action Center"])

        with tab1:
            # Real-time coaching + sentiment in compact view
            col1, col2 = st.columns(2)

            with col1:
                coaching_data = self._get_real_time_coaching_data(active_lead_id)
                if coaching_data:
                    st.markdown("#### ⚡ Live Coaching")
                    for suggestion in coaching_data.get('suggestions', [])[:2]:
                        st.success(f"💡 {suggestion}")

            with col2:
                sentiment_data = self._get_sentiment_data(active_lead_id)
                if sentiment_data:
                    latest_sentiment = sentiment_data[-1]
                    st.markdown("#### 🎭 Current Sentiment")
                    st.metric("Overall Sentiment", f"{latest_sentiment.overall_sentiment:.1%}")
                    st.metric("Engagement", f"{latest_sentiment.engagement_level:.1%}")

        with tab2:
            # Journey + competitive intelligence
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🗺️ Journey Progress")
                journey_stages = self._get_lead_journey_data(active_lead_id)
                if journey_stages:
                    current_stage = journey_stages[-1]
                    st.metric("Current Stage", current_stage.stage_name)
                    st.metric("Conversion Probability", f"{current_stage.conversion_probability:.1%}")

            with col2:
                st.markdown("#### 🏆 Competitive Position")
                competitive_data = self._get_competitive_intelligence_data()
                st.metric("Market Position", competitive_data.competitive_position)
                st.metric("Market Share", f"{competitive_data.market_share:.1%}")

        with tab3:
            # Content recommendations + action planning
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🎨 Top Content Recommendation")
                lead_profile = self._get_lead_profile(active_lead_id)
                content_recs = self._get_content_recommendations(active_lead_id, lead_profile)
                if content_recs:
                    top_content = content_recs[0]
                    st.success(f"📄 **{top_content.title}**")
                    st.write(f"Relevance: {top_content.relevance_score:.1%}")
                    st.write(f"Best time: {top_content.optimal_timing}")

            with col2:
                st.markdown("#### 🚀 Recommended Actions")
                actions = [
                    "📞 Schedule follow-up call within 2 hours",
                    "📧 Send personalized market report",
                    "🏠 Share 3 matched property listings",
                    "📅 Book property viewing appointment"
                ]

                for action in actions[:3]:
                    st.markdown(f"• {action}")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_real_time_footer(self):
        """Render real-time updates footer."""
        if st.session_state.unified_dashboard_state.get('real_time_enabled', True):

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown("---")
                last_update = datetime.now().strftime("%H:%M:%S")
                st.caption(f"🔄 Real-time updates active • Last refresh: {last_update}")

            with col2:
                if st.button("🔄 Refresh Now"):
                    st.rerun()

            with col3:
                auto_refresh = st.toggle("Auto-refresh", value=True)
                if auto_refresh:
                    refresh_interval = st.session_state.unified_dashboard_state.get('auto_refresh_interval', 5)
                    time.sleep(refresh_interval)
                    st.rerun()

    # Data access methods (would connect to real services in production)

    def _get_real_time_coaching_data(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time coaching data for active lead."""
        # Simulate coaching data (would use real Claude service in production)
        return {
            'suggestions': [
                "Ask about their timeline flexibility - they mentioned urgency earlier",
                "Address budget concerns by highlighting value proposition",
                "Transition to scheduling a property viewing to maintain momentum"
            ],
            'urgency': 'high',
            'stage': 'evaluation',
            'objection_detected': False,
            'next_question': "What's most important to you in your final decision?",
            'question_purpose': 'closing',
            'question_priority': 'high',
            'expected_info': 'Decision criteria and final concerns'
        }

    def _get_lead_journey_data(self, lead_id: str) -> List[LeadJourneyStage]:
        """Get lead journey data."""
        return generate_sample_journey_stages()

    def _get_sentiment_data(self, lead_id: str) -> List[SentimentAnalysis]:
        """Get sentiment analysis data."""
        return generate_sample_sentiment_data()

    def _get_competitive_intelligence_data(self) -> CompetitiveIntelligence:
        """Get competitive intelligence data."""
        return generate_sample_competitive_data()

    def _get_content_recommendations(self, lead_id: str, lead_profile: Dict) -> List[ContentRecommendation]:
        """Get content recommendations."""
        return generate_sample_content_recommendations()

    def _get_lead_name(self, lead_id: str) -> str:
        """Get lead display name."""
        lead_names = {
            "LEAD_001": "John Smith",
            "LEAD_002": "Sarah Jones",
            "LEAD_003": "Mike Wilson"
        }
        return lead_names.get(lead_id, "Unknown Lead")

    def _get_lead_profile(self, lead_id: str) -> Dict[str, Any]:
        """Get lead profile data."""
        profiles = {
            "LEAD_001": {
                "age_range": "28-35",
                "interests": ["Modern design", "Smart home technology", "Urban living"],
                "communication_style": "Direct and efficient",
                "income_level": "High",
                "family_status": "Single professional"
            },
            "LEAD_002": {
                "age_range": "30-40",
                "interests": ["School districts", "Family safety", "Suburban amenities"],
                "communication_style": "Detail-oriented",
                "income_level": "Medium-High",
                "family_status": "Growing family"
            },
            "LEAD_003": {
                "age_range": "40-55",
                "interests": ["Investment potential", "Market analysis", "ROI optimization"],
                "communication_style": "Data-driven",
                "income_level": "High",
                "family_status": "Investment buyer"
            }
        }
        return profiles.get(lead_id, {})

    def _get_market_trends(self) -> Optional[Dict[str, Any]]:
        """Get market trend data."""
        return {
            "market_direction": "trending_up",
            "price_growth": 0.067,
            "inventory_levels": "low",
            "buyer_demand": "high"
        }


# Factory function
def create_unified_dashboard(location_id: Optional[str] = None, agent_id: Optional[str] = None) -> UnifiedIntelligenceDashboard:
    """Create and return a UnifiedIntelligenceDashboard instance."""
    return UnifiedIntelligenceDashboard(location_id=location_id, agent_id=agent_id)


# Main application entry point
if __name__ == "__main__":
    dashboard = create_unified_dashboard()
    dashboard.render_main_dashboard()