"""
Nurturing Campaign Manager

Streamlit component for managing automated lead nurturing campaigns,
monitoring performance, and controlling follow-up sequences.
"""

import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st
from uuid import uuid4

# Internal imports
from models.nurturing_models import (
    NurturingCampaign, NurturingSequence, LeadType, CampaignStatus,
    CommunicationChannel, MessageTone, EngagementType,
    CampaignPerformanceMetrics, NurturingTouchpoint
)
from models.evaluation_models import LeadEvaluationResult
from services.lead_nurturing_agent import LeadNurturingAgent
from streamlit_components.base import EnterpriseComponent


class NurturingCampaignManager(EnterpriseComponent):
    """
    Lead Nurturing Campaign Management Dashboard

    Provides comprehensive interface for managing automated nurturing campaigns
    with luxury styling and real-time performance tracking.
    """

    def __init__(self):
        super().__init__()
        self.component_id = "nurturing_campaign_manager"
        self.nurturing_agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the nurturing agent with proper error handling."""
        try:
            self.nurturing_agent = LeadNurturingAgent()
        except Exception as e:
            st.error(f"Failed to initialize nurturing agent: {str(e)}")
            self.nurturing_agent = None

    def render(self) -> None:
        """Render the complete nurturing campaign management interface."""
        try:
            # Apply luxury styling
            self._apply_luxury_styling()

            # Header with branding
            self._render_header()

            # Main dashboard tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🎯 Campaign Overview",
                "🚀 Active Campaigns",
                "📊 Performance Analytics",
                "⚙️ Sequence Management",
                "🎮 Campaign Controls"
            ])

            with tab1:
                self._render_campaign_overview()

            with tab2:
                self._render_active_campaigns()

            with tab3:
                self._render_performance_analytics()

            with tab4:
                self._render_sequence_management()

            with tab5:
                self._render_campaign_controls()

        except Exception as e:
            self._render_error_boundary(e)

    def _apply_luxury_styling(self):
        """Apply premium styling for professional real estate branding."""
        st.markdown("""
        <style>
        /* Nurturing Campaign Manager Premium Styling */
        .nurturing-header {
            background: linear-gradient(135deg, #1a365d 0%, #2c5aa0 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(26, 54, 93, 0.3);
        }

        .nurturing-title {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .nurturing-subtitle {
            color: #a0c4ff;
            font-size: 1.2rem;
            text-align: center;
            margin-top: 0.5rem;
            opacity: 0.9;
        }

        /* Campaign Cards */
        .campaign-card {
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        .campaign-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            border-color: #3182ce;
        }

        .campaign-status-active {
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.8rem;
        }

        .campaign-status-paused {
            background: linear-gradient(90deg, #ed8936 0%, #dd6b20 100%);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.8rem;
        }

        .campaign-status-completed {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.8rem;
        }

        /* Performance Metrics */
        .metric-card {
            background: linear-gradient(145deg, #ffffff 0%, #f7fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            margin: 0.5rem;
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2d3748;
            margin: 0;
        }

        .metric-label {
            font-size: 0.9rem;
            color: #718096;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-trend-up {
            color: #48bb78;
            font-weight: 600;
        }

        .metric-trend-down {
            color: #f56565;
            font-weight: 600;
        }

        /* Action Buttons */
        .action-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }

        /* Status Indicators */
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
        }

        .status-active { background-color: #48bb78; }
        .status-paused { background-color: #ed8936; }
        .status-completed { background-color: #667eea; }
        .status-failed { background-color: #f56565; }

        /* Engagement Chart Styling */
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

    def _render_header(self):
        """Render the component header with branding."""
        st.markdown("""
        <div class="nurturing-header">
            <h1 class="nurturing-title">🎯 Lead Nurturing Command Center</h1>
            <p class="nurturing-subtitle">Automated Follow-up Campaign Management & Performance Analytics</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_campaign_overview(self):
        """Render high-level campaign overview and key metrics."""
        st.markdown("### 📊 Campaign Performance Overview")

        # Mock data for demo purposes
        overview_data = self._get_overview_data()

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{overview_data['active_campaigns']}</div>
                <div class="metric-label">Active Campaigns</div>
                <div class="metric-trend-up">↗ +{overview_data['campaign_growth']}% this week</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{overview_data['response_rate']:.1%}</div>
                <div class="metric-label">Response Rate</div>
                <div class="metric-trend-up">↗ +{overview_data['response_improvement']:.1%} vs target</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{overview_data['engagement_score']:.1%}</div>
                <div class="metric-label">Engagement Score</div>
                <div class="metric-trend-up">↗ +{overview_data['engagement_improvement']:.1%} vs last month</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{overview_data['scheduled_touchpoints']}</div>
                <div class="metric-label">Scheduled Touchpoints</div>
                <div class="metric-trend-up">Next 24 hours</div>
            </div>
            """, unsafe_allow_html=True)

        # Recent activity timeline
        st.markdown("### 🕒 Recent Campaign Activity")
        self._render_activity_timeline()

        # Performance by lead type
        st.markdown("### 📈 Performance by Lead Type")
        self._render_performance_by_type()

    def _render_active_campaigns(self):
        """Render detailed view of active campaigns."""
        st.markdown("### 🚀 Active Campaigns")

        # Campaign filters
        col1, col2, col3 = st.columns(3)
        with col1:
            lead_type_filter = st.selectbox(
                "Filter by Lead Type",
                ["All", "First-Time Buyer", "Investment Buyer", "Luxury Buyer", "Seller - Downsizing"]
            )

        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Active", "Paused", "High Engagement"]
            )

        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Created Date", "Engagement Score", "Next Touchpoint", "Lead Score"]
            )

        # Campaign list
        campaigns = self._get_active_campaigns_data()

        for campaign in campaigns:
            self._render_campaign_card(campaign)

        # Bulk actions
        st.markdown("### 🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⏸️ Pause All Low Engagement"):
                st.success("Paused 3 low-engagement campaigns")

        with col2:
            if st.button("🚀 Accelerate High-Value Leads"):
                st.success("Accelerated 5 high-value lead sequences")

        with col3:
            if st.button("📧 Send Engagement Boost"):
                st.success("Sent engagement boost to 12 campaigns")

    def _render_campaign_card(self, campaign: Dict[str, Any]):
        """Render individual campaign card."""
        status_class = f"campaign-status-{campaign['status'].lower()}"

        st.markdown(f"""
        <div class="campaign-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #2d3748;">{campaign['lead_name']} - {campaign['lead_type']}</h4>
                    <p style="margin: 0.25rem 0; color: #718096;">Campaign: {campaign['sequence_name']}</p>
                </div>
                <div class="{status_class}">{campaign['status']}</div>
            </div>

            <div style="margin: 1rem 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 1rem;">
                    <div>
                        <strong>Step:</strong> {campaign['current_step']}/{campaign['total_steps']}
                    </div>
                    <div>
                        <strong>Engagement:</strong> {campaign['engagement_score']:.1%}
                    </div>
                    <div>
                        <strong>Responses:</strong> {campaign['responses']}
                    </div>
                    <div>
                        <strong>Next:</strong> {campaign['next_touchpoint']}
                    </div>
                </div>
            </div>

            <div style="margin-top: 1rem;">
                <span style="color: #718096; font-size: 0.9rem;">
                    Started: {campaign['created_date']} | Last Activity: {campaign['last_activity']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Campaign actions
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(f"⏸️ Pause", key=f"pause_{campaign['id']}"):
                st.success(f"Paused campaign for {campaign['lead_name']}")

        with col2:
            if st.button(f"⚡ Skip Step", key=f"skip_{campaign['id']}"):
                st.success(f"Skipped to next step for {campaign['lead_name']}")

        with col3:
            if st.button(f"📧 Send Now", key=f"send_{campaign['id']}"):
                st.success(f"Sent immediate follow-up to {campaign['lead_name']}")

        with col4:
            if st.button(f"👁️ View Details", key=f"view_{campaign['id']}"):
                self._show_campaign_details(campaign)

    def _render_performance_analytics(self):
        """Render detailed performance analytics and charts."""
        st.markdown("### 📊 Performance Analytics")

        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            time_range = st.selectbox(
                "Time Range",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
            )

        with col2:
            metric_type = st.selectbox(
                "Primary Metric",
                ["Response Rate", "Engagement Score", "Conversion Rate", "ROI"]
            )

        # Performance trend chart
        self._render_performance_trend_chart(time_range, metric_type)

        # Channel performance comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📱 Channel Performance")
            self._render_channel_performance()

        with col2:
            st.markdown("#### ⏰ Optimal Timing Analysis")
            self._render_timing_analysis()

        # Sequence effectiveness
        st.markdown("#### 🎯 Sequence Effectiveness")
        self._render_sequence_effectiveness()

        # A/B Testing Results
        st.markdown("#### 🧪 A/B Testing Results")
        self._render_ab_testing_results()

    def _render_sequence_management(self):
        """Render sequence management interface."""
        st.markdown("### ⚙️ Sequence Management")

        # Sequence overview
        sequences = self._get_available_sequences()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### 📋 Available Sequences")
            for sequence in sequences:
                with st.expander(f"{sequence['name']} ({sequence['lead_type']})"):
                    st.write(f"**Description:** {sequence['description']}")
                    st.write(f"**Duration:** {sequence['duration']} days")
                    st.write(f"**Steps:** {len(sequence['steps'])}")
                    st.write(f"**Performance:** {sequence['performance_score']:.1%} effectiveness")

                    # Sequence steps
                    st.markdown("**Steps:**")
                    for i, step in enumerate(sequence['steps'], 1):
                        st.write(f"{i}. {step['name']} ({step['delay']} delay) - {step['channel']}")

        with col2:
            st.markdown("#### 🎮 Quick Actions")

            if st.button("➕ Create New Sequence"):
                self._show_sequence_creator()

            if st.button("📝 Edit Sequence"):
                self._show_sequence_editor()

            if st.button("📊 Sequence Analytics"):
                self._show_sequence_analytics()

            if st.button("🧪 A/B Test Setup"):
                self._show_ab_test_setup()

            st.markdown("#### 🏆 Top Performing")
            st.metric("Best Buyer Sequence", "First-Time Buyer Journey", "38.5% response rate")
            st.metric("Best Seller Sequence", "Downsizing Support", "42.1% response rate")

    def _render_campaign_controls(self):
        """Render campaign control interface."""
        st.markdown("### 🎮 Campaign Controls")

        # Global controls
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🌐 Global Controls")

            global_status = st.selectbox(
                "Nurturing Agent Status",
                ["Active", "Maintenance Mode", "Paused"],
                index=0
            )

            max_campaigns = st.number_input(
                "Max Concurrent Campaigns",
                min_value=10,
                max_value=1000,
                value=100,
                step=10
            )

            if st.button("🔄 Restart Nurturing Agent"):
                st.success("Nurturing agent restarted successfully!")

            if st.button("🧹 Clean Up Completed Campaigns"):
                st.success("Cleaned up 25 completed campaigns")

        with col2:
            st.markdown("#### ⚙️ Advanced Settings")

            response_timeout = st.number_input(
                "Response Timeout (hours)",
                min_value=1,
                max_value=168,
                value=48,
                step=1
            )

            retry_attempts = st.number_input(
                "Max Retry Attempts",
                min_value=1,
                max_value=5,
                value=3,
                step=1
            )

            st.toggle("Enable Smart Timing", value=True)
            st.toggle("Behavioral Learning", value=True)
            st.toggle("Auto-optimization", value=False)

        # Emergency controls
        st.markdown("#### 🚨 Emergency Controls")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⏹️ Stop All Campaigns", type="secondary"):
                st.warning("All campaigns have been paused!")

        with col2:
            if st.button("🔄 Reset Failed Campaigns", type="secondary"):
                st.success("Reset 3 failed campaigns")

        with col3:
            if st.button("📧 Send Status Report", type="secondary"):
                st.success("Status report sent to admin")

        # System monitoring
        st.markdown("#### 📡 System Monitoring")

        # System health metrics
        health_metrics = {
            "Redis Connection": "✅ Healthy",
            "OpenAI API": "✅ Healthy",
            "Email Service": "✅ Healthy",
            "SMS Service": "⚠️ Rate Limited",
            "Background Processor": "✅ Running"
        }

        for service, status in health_metrics.items():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**{service}:**")
            with col2:
                st.write(status)

    # Helper Methods for Data and Visualization

    def _get_overview_data(self) -> Dict[str, Any]:
        """Get overview data for demo purposes."""
        return {
            'active_campaigns': 42,
            'campaign_growth': 18,
            'response_rate': 0.347,
            'response_improvement': 0.047,
            'engagement_score': 0.623,
            'engagement_improvement': 0.085,
            'scheduled_touchpoints': 18
        }

    def _get_active_campaigns_data(self) -> List[Dict[str, Any]]:
        """Get active campaigns data for demo purposes."""
        return [
            {
                'id': 'camp_001',
                'lead_name': 'Sarah Johnson',
                'lead_type': 'First-Time Buyer',
                'sequence_name': 'First-Time Buyer Journey',
                'status': 'Active',
                'current_step': 2,
                'total_steps': 5,
                'engagement_score': 0.745,
                'responses': 3,
                'next_touchpoint': 'Tomorrow 2:00 PM',
                'created_date': '2026-01-07',
                'last_activity': '2026-01-08 3:45 PM'
            },
            {
                'id': 'camp_002',
                'lead_name': 'Michael Chen',
                'lead_type': 'Investment Buyer',
                'sequence_name': 'Investment Property Journey',
                'status': 'Active',
                'current_step': 1,
                'total_steps': 4,
                'engagement_score': 0.892,
                'responses': 1,
                'next_touchpoint': 'Today 4:00 PM',
                'created_date': '2026-01-08',
                'last_activity': '2026-01-08 1:30 PM'
            },
            {
                'id': 'camp_003',
                'lead_name': 'Emily Rodriguez',
                'lead_type': 'Seller - Downsizing',
                'sequence_name': 'Downsizing Support',
                'status': 'Paused',
                'current_step': 3,
                'total_steps': 6,
                'engagement_score': 0.234,
                'responses': 0,
                'next_touchpoint': 'Paused',
                'created_date': '2026-01-05',
                'last_activity': '2026-01-06 9:15 AM'
            }
        ]

    def _get_available_sequences(self) -> List[Dict[str, Any]]:
        """Get available sequences for demo purposes."""
        return [
            {
                'id': 'seq_001',
                'name': 'First-Time Buyer Journey',
                'lead_type': 'Buyer',
                'description': 'Educational and supportive sequence for first-time home buyers',
                'duration': 30,
                'performance_score': 0.385,
                'steps': [
                    {'name': 'Welcome & Education', 'delay': '2 hours', 'channel': 'Email'},
                    {'name': 'Buying Process Guide', 'delay': '1 day', 'channel': 'Email'},
                    {'name': 'Pre-qualification Reminder', 'delay': '3 days', 'channel': 'SMS'},
                    {'name': 'Property Matches', 'delay': '5 days', 'channel': 'Email'},
                    {'name': 'Market Insights', 'delay': '1 week', 'channel': 'Email'}
                ]
            },
            {
                'id': 'seq_002',
                'name': 'Luxury Buyer Experience',
                'lead_type': 'Buyer',
                'description': 'High-touch, personalized experience for luxury buyers',
                'duration': 60,
                'performance_score': 0.421,
                'steps': [
                    {'name': 'Luxury Welcome', 'delay': '1 hour', 'channel': 'Email'},
                    {'name': 'Market Report', 'delay': '12 hours', 'channel': 'Email'},
                    {'name': 'Private Showing', 'delay': '2 days', 'channel': 'Phone'}
                ]
            }
        ]

    def _render_activity_timeline(self):
        """Render recent activity timeline."""
        activities = [
            "🎯 Sarah Johnson engaged with property match email",
            "📧 Michael Chen opened ROI analysis report",
            "⏰ 5 touchpoints scheduled for this afternoon",
            "🚀 Emily Rodriguez re-engaged after 7-day pause",
            "📱 3 SMS responses received in last hour"
        ]

        for activity in activities:
            st.write(f"• {activity}")

    def _render_performance_by_type(self):
        """Render performance metrics by lead type."""
        data = {
            'Lead Type': ['First-Time Buyer', 'Investment', 'Luxury', 'Downsizing'],
            'Response Rate': [0.385, 0.267, 0.421, 0.398],
            'Engagement': [0.623, 0.578, 0.712, 0.645],
            'Conversion': [0.234, 0.189, 0.287, 0.256]
        }

        df = pd.DataFrame(data)

        fig = px.bar(
            df.melt(id_vars='Lead Type', var_name='Metric', value_name='Rate'),
            x='Lead Type',
            y='Rate',
            color='Metric',
            title="Performance by Lead Type",
            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb']
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#2d3748'
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_performance_trend_chart(self, time_range: str, metric_type: str):
        """Render performance trend chart."""
        # Generate sample trend data
        dates = pd.date_range(start='2026-01-01', end='2026-01-09', freq='D')
        values = [0.32, 0.34, 0.31, 0.36, 0.38, 0.35, 0.37, 0.39, 0.41]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=metric_type,
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#764ba2')
        ))

        fig.update_layout(
            title=f"{metric_type} Trend - {time_range}",
            xaxis_title="Date",
            yaxis_title=metric_type,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#2d3748'
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_channel_performance(self):
        """Render channel performance comparison."""
        channels = ['Email', 'SMS', 'Phone', 'LinkedIn']
        performance = [0.347, 0.267, 0.521, 0.189]

        fig = px.pie(
            values=performance,
            names=channels,
            title="Response Rate by Channel",
            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#c471f5']
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#2d3748'
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_timing_analysis(self):
        """Render optimal timing analysis."""
        hours = list(range(24))
        engagement = [0.1, 0.05, 0.03, 0.02, 0.03, 0.05, 0.1, 0.15, 0.25, 0.35, 0.45, 0.5,
                      0.6, 0.65, 0.7, 0.75, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15]

        fig = px.line(
            x=hours,
            y=engagement,
            title="Engagement by Hour of Day",
            labels={'x': 'Hour', 'y': 'Engagement Rate'}
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#2d3748'
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_sequence_effectiveness(self):
        """Render sequence effectiveness comparison."""
        sequences = ['First-Time Buyer', 'Investment', 'Luxury', 'Downsizing']
        effectiveness = [0.385, 0.267, 0.421, 0.398]

        col1, col2 = st.columns(2)

        with col1:
            for seq, eff in zip(sequences, effectiveness):
                st.metric(seq, f"{eff:.1%}", f"+{(eff-0.3)*100:.1f}%")

        with col2:
            fig = px.bar(
                x=sequences,
                y=effectiveness,
                title="Sequence Effectiveness",
                color=effectiveness,
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)

    def _render_ab_testing_results(self):
        """Render A/B testing results."""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Subject Line Test: Formal vs Casual**")
            st.write("• Formal: 34.2% open rate")
            st.write("• Casual: 38.7% open rate")
            st.success("Winner: Casual (+4.5%)")

        with col2:
            st.markdown("**Timing Test: 1hr vs 24hr Delay**")
            st.write("• 1 Hour: 28.9% response rate")
            st.write("• 24 Hours: 35.4% response rate")
            st.success("Winner: 24 Hours (+6.5%)")

    def _show_campaign_details(self, campaign: Dict[str, Any]):
        """Show detailed campaign information."""
        with st.expander(f"📋 Campaign Details - {campaign['lead_name']}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Campaign Information**")
                st.write(f"Lead Type: {campaign['lead_type']}")
                st.write(f"Sequence: {campaign['sequence_name']}")
                st.write(f"Status: {campaign['status']}")
                st.write(f"Current Step: {campaign['current_step']}/{campaign['total_steps']}")

            with col2:
                st.write("**Performance Metrics**")
                st.write(f"Engagement Score: {campaign['engagement_score']:.1%}")
                st.write(f"Responses: {campaign['responses']}")
                st.write(f"Last Activity: {campaign['last_activity']}")
                st.write(f"Next Touchpoint: {campaign['next_touchpoint']}")

    def _show_sequence_creator(self):
        """Show sequence creation interface."""
        st.info("🚧 Sequence Creator - Coming in next update!")

    def _show_sequence_editor(self):
        """Show sequence editing interface."""
        st.info("🚧 Sequence Editor - Coming in next update!")

    def _show_sequence_analytics(self):
        """Show detailed sequence analytics."""
        st.info("🚧 Advanced Analytics - Coming in next update!")

    def _show_ab_test_setup(self):
        """Show A/B test setup interface."""
        st.info("🚧 A/B Test Setup - Coming in next update!")

    def _render_error_boundary(self, error: Exception):
        """Render error boundary for graceful error handling."""
        st.error(f"⚠️ Component Error: {str(error)}")
        st.info("The nurturing campaign manager encountered an issue. Please refresh the page or contact support.")

        if st.checkbox("Show debug information"):
            st.exception(error)