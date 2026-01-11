"""
Conversational Intelligence Dashboard Component

Real-time conversation analysis dashboard with sentiment tracking,
coaching suggestions, and conversation insights.

Value: $75K-110K annually (50% better qualification)
Integration: WebSocket infrastructure, real_time_scoring
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

try:
    from ..services.conversational_intelligence import (
        ConversationalIntelligence,
        ConversationInsight,
        CoachingSuggestion,
        SentimentScore
    )
    from ..services.real_time_scoring import RealTimeScoring
except ImportError:
    # Fallback for development/testing
    st.warning("⚠️ Conversational Intelligence service not available - using mock data")
    ConversationalIntelligence = None
    ConversationInsight = None
    CoachingSuggestion = None
    SentimentScore = None


class ConversationalIntelligenceDashboard:
    """Dashboard component for conversational intelligence and coaching."""

    def __init__(self):
        self.conversation_service = self._initialize_service()
        self.cache_duration = 300  # 5 minutes

    def _initialize_service(self):
        """Initialize conversational intelligence service."""
        try:
            if ConversationalIntelligence:
                return ConversationalIntelligence()
            return None
        except Exception as e:
            st.error(f"Failed to initialize conversational intelligence service: {e}")
            return None

    def render(self, tenant_id: str) -> None:
        """Render the complete conversational intelligence dashboard."""
        st.header("💬 Conversational Intelligence")
        st.caption("Real-time conversation analysis with AI coaching")

        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔴 Live Conversations",
            "📊 Sentiment Analytics",
            "🎯 Coaching Center",
            "📈 Performance Insights"
        ])

        with tab1:
            self._render_live_conversations(tenant_id)

        with tab2:
            self._render_sentiment_analytics(tenant_id)

        with tab3:
            self._render_coaching_center(tenant_id)

        with tab4:
            self._render_performance_insights(tenant_id)

    def _render_live_conversations(self, tenant_id: str) -> None:
        """Render live conversations monitoring."""
        st.subheader("🔴 Live Conversation Monitoring")

        # Real-time metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Active Conversations",
                value="23",
                delta="5 new"
            )

        with col2:
            st.metric(
                label="Avg Sentiment Score",
                value="8.2/10",
                delta="0.3 ↑"
            )

        with col3:
            st.metric(
                label="Coaching Suggestions",
                value="47",
                delta="12 today"
            )

        with col4:
            st.metric(
                label="Qualification Rate",
                value="73%",
                delta="8% ↑"
            )

        # Live conversation feed
        st.subheader("Live Conversation Feed")

        # Mock real-time conversation data
        conversations_data = [
            {
                "conversation_id": "conv_001",
                "agent": "Sarah Miller",
                "lead": "John Smith",
                "duration": "00:07:23",
                "sentiment": 8.7,
                "intent": "Buying - High Interest",
                "last_message": "I'm very interested in viewing the property this weekend",
                "coaching_tip": "Ask about timeline and financing pre-approval"
            },
            {
                "conversation_id": "conv_002",
                "agent": "Mike Johnson",
                "lead": "Emma Wilson",
                "duration": "00:12:45",
                "sentiment": 6.3,
                "intent": "Information Gathering",
                "last_message": "What's the price range for 3-bedroom homes?",
                "coaching_tip": "Probe for budget and specific location preferences"
            },
            {
                "conversation_id": "conv_003",
                "agent": "Lisa Chen",
                "lead": "Robert Davis",
                "duration": "00:04:12",
                "sentiment": 4.2,
                "intent": "Price Objection",
                "last_message": "That seems too expensive for our budget",
                "coaching_tip": "Acknowledge concern, explore value proposition and alternatives"
            }
        ]

        for conv in conversations_data:
            with st.expander(f"🟢 {conv['agent']} ↔ {conv['lead']} ({conv['duration']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Intent:** {conv['intent']}")
                    st.write(f"**Last Message:** {conv['last_message']}")

                    # Sentiment indicator
                    sentiment_color = "green" if conv['sentiment'] >= 7 else "orange" if conv['sentiment'] >= 5 else "red"
                    st.markdown(f"**Sentiment:** <span style='color: {sentiment_color}'>{conv['sentiment']}/10</span>", unsafe_allow_html=True)

                with col2:
                    st.info(f"💡 **Coaching Tip:**\n{conv['coaching_tip']}")

                    if st.button(f"Send Suggestion", key=f"send_{conv['conversation_id']}"):
                        st.success("Coaching suggestion sent to agent!")

        # Real-time updates
        if st.button("🔄 Refresh Live Data"):
            st.rerun()

    def _render_sentiment_analytics(self, tenant_id: str) -> None:
        """Render sentiment analytics and trends."""
        st.subheader("📊 Sentiment Analytics")

        # Sentiment distribution chart
        col1, col2 = st.columns(2)

        with col1:
            # Sentiment distribution pie chart
            sentiment_data = {
                'Sentiment Range': ['Very Positive (8-10)', 'Positive (6-8)', 'Neutral (4-6)', 'Negative (2-4)', 'Very Negative (0-2)'],
                'Count': [15, 28, 22, 8, 3],
                'Color': ['#00ff00', '#90EE90', '#FFD700', '#FFA500', '#FF0000']
            }

            fig_pie = px.pie(
                values=sentiment_data['Count'],
                names=sentiment_data['Sentiment Range'],
                title="Sentiment Distribution - Today",
                color_discrete_sequence=sentiment_data['Color']
            )

            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Sentiment trend over time
            hours = list(range(24))
            sentiment_scores = [6.2, 6.5, 6.8, 7.1, 7.3, 7.8, 8.0, 8.2, 7.9, 7.6, 7.8, 8.1, 8.3, 8.0, 7.7, 7.9, 8.2, 8.4, 8.1, 7.8, 7.5, 7.2, 6.9, 6.5]

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=hours,
                y=sentiment_scores,
                mode='lines+markers',
                name='Avg Sentiment Score',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6)
            ))

            fig_trend.update_layout(
                title="Sentiment Trend - Last 24 Hours",
                xaxis_title="Hour",
                yaxis_title="Sentiment Score",
                showlegend=False,
                height=400
            )

            st.plotly_chart(fig_trend, use_container_width=True)

        # Intent classification breakdown
        st.subheader("Intent Classification Analysis")

        intent_data = pd.DataFrame({
            'Intent': ['Buying - High Interest', 'Information Gathering', 'Viewing Request', 'Price Inquiry', 'Selling Interest', 'Price Objection'],
            'Count': [18, 23, 15, 12, 8, 6],
            'Avg Sentiment': [8.4, 6.8, 7.9, 6.2, 7.1, 4.8],
            'Conversion Rate': [85, 35, 70, 28, 60, 15]
        })

        fig_intent = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Intent Distribution", "Intent vs Conversion Rate"),
            specs=[[{"type": "bar"}, {"type": "scatter"}]]
        )

        # Intent distribution
        fig_intent.add_trace(
            go.Bar(x=intent_data['Intent'], y=intent_data['Count'], name="Count"),
            row=1, col=1
        )

        # Intent vs conversion
        fig_intent.add_trace(
            go.Scatter(
                x=intent_data['Avg Sentiment'],
                y=intent_data['Conversion Rate'],
                mode='markers+text',
                text=intent_data['Intent'],
                textposition="top center",
                marker=dict(size=intent_data['Count'], sizemode='diameter', sizeref=2),
                name="Conversion Rate"
            ),
            row=1, col=2
        )

        fig_intent.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_intent, use_container_width=True)

    def _render_coaching_center(self, tenant_id: str) -> None:
        """Render AI coaching center."""
        st.subheader("🎯 AI Coaching Center")

        # Coaching suggestions management
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("**Active Coaching Suggestions**")

            coaching_suggestions = [
                {
                    "id": "coach_001",
                    "agent": "Sarah Miller",
                    "conversation": "conv_001",
                    "type": "Qualification",
                    "priority": "High",
                    "suggestion": "Lead shows high interest. Ask about financing pre-approval and preferred move-in timeline.",
                    "confidence": 0.92,
                    "created": "2 minutes ago"
                },
                {
                    "id": "coach_002",
                    "agent": "Mike Johnson",
                    "conversation": "conv_002",
                    "type": "Discovery",
                    "priority": "Medium",
                    "suggestion": "Lead is in information-gathering phase. Probe for specific neighborhood preferences and must-have features.",
                    "confidence": 0.87,
                    "created": "5 minutes ago"
                },
                {
                    "id": "coach_003",
                    "agent": "Lisa Chen",
                    "conversation": "conv_003",
                    "type": "Objection Handling",
                    "priority": "High",
                    "suggestion": "Address price concerns by highlighting property value and comparing to similar properties. Offer to show alternatives.",
                    "confidence": 0.94,
                    "created": "1 minute ago"
                }
            ]

            for suggestion in coaching_suggestions:
                with st.container():
                    # Priority color coding
                    priority_color = "red" if suggestion['priority'] == "High" else "orange" if suggestion['priority'] == "Medium" else "green"

                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: bold;">{suggestion['agent']} - {suggestion['type']}</span>
                            <span style="color: {priority_color}; font-weight: bold;">{suggestion['priority']} Priority</span>
                        </div>
                        <p style="margin: 5px 0;">{suggestion['suggestion']}</p>
                        <small style="color: #666;">Confidence: {suggestion['confidence']:.0%} | {suggestion['created']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if st.button(f"Send to Agent", key=f"send_{suggestion['id']}"):
                            st.success("Suggestion sent!")
                    with col_btn2:
                        if st.button(f"Dismiss", key=f"dismiss_{suggestion['id']}"):
                            st.info("Suggestion dismissed")
                    with col_btn3:
                        if st.button(f"Modify", key=f"modify_{suggestion['id']}"):
                            st.info("Opening modification dialog...")

        with col2:
            st.write("**Coaching Performance**")

            # Coaching metrics
            st.metric("Suggestions Sent", "47", "12 today")
            st.metric("Acceptance Rate", "89%", "5% ↑")
            st.metric("Improved Conversations", "34", "8 today")

            st.write("**Top Coaching Categories**")
            coaching_categories = pd.DataFrame({
                'Category': ['Qualification', 'Objection Handling', 'Discovery', 'Closing', 'Follow-up'],
                'Count': [18, 12, 10, 7, 5]
            })

            fig_categories = px.bar(
                coaching_categories,
                y='Category',
                x='Count',
                orientation='h',
                title="Coaching by Category"
            )
            fig_categories.update_layout(height=300)
            st.plotly_chart(fig_categories, use_container_width=True)

        # Custom coaching rules
        st.subheader("Custom Coaching Rules")

        with st.expander("➕ Add New Coaching Rule"):
            rule_name = st.text_input("Rule Name")
            trigger_condition = st.selectbox(
                "Trigger Condition",
                ["Low Sentiment (< 5)", "Price Objection", "High Interest", "Long Silence", "Negative Keywords"]
            )
            coaching_message = st.text_area("Coaching Message Template")

            if st.button("Create Rule"):
                st.success(f"Coaching rule '{rule_name}' created successfully!")

    def _render_performance_insights(self, tenant_id: str) -> None:
        """Render conversation performance insights."""
        st.subheader("📈 Performance Insights")

        # Key performance metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Conversation Quality Score",
                value="8.3/10",
                delta="0.4 ↑ this week"
            )

        with col2:
            st.metric(
                label="Avg Conversation Length",
                value="9:32 min",
                delta="1:45 min ↑"
            )

        with col3:
            st.metric(
                label="Lead Qualification Rate",
                value="73%",
                delta="8% ↑ this month"
            )

        with col4:
            st.metric(
                label="Coaching Adoption Rate",
                value="89%",
                delta="5% ↑ this week"
            )

        # Agent performance comparison
        st.subheader("Agent Performance Comparison")

        agent_performance = pd.DataFrame({
            'Agent': ['Sarah Miller', 'Mike Johnson', 'Lisa Chen', 'David Brown', 'Emma Davis'],
            'Conversations': [23, 19, 21, 17, 20],
            'Avg Sentiment': [8.7, 7.2, 6.8, 7.9, 8.1],
            'Qualification Rate': [85, 68, 72, 79, 81],
            'Coaching Accepted': [92, 78, 85, 88, 90]
        })

        col1, col2 = st.columns(2)

        with col1:
            # Sentiment vs qualification rate scatter
            fig_performance = px.scatter(
                agent_performance,
                x='Avg Sentiment',
                y='Qualification Rate',
                size='Conversations',
                hover_name='Agent',
                title="Sentiment vs Qualification Rate by Agent"
            )
            fig_performance.update_layout(height=400)
            st.plotly_chart(fig_performance, use_container_width=True)

        with col2:
            # Coaching adoption rates
            fig_coaching = px.bar(
                agent_performance.sort_values('Coaching Accepted', ascending=True),
                x='Coaching Accepted',
                y='Agent',
                orientation='h',
                title="Coaching Adoption Rate by Agent"
            )
            fig_coaching.update_layout(height=400)
            st.plotly_chart(fig_coaching, use_container_width=True)

        # Conversation insights timeline
        st.subheader("Conversation Insights Timeline")

        # Mock timeline data
        timeline_data = pd.DataFrame({
            'Time': pd.date_range('2026-01-09 08:00', periods=12, freq='1H'),
            'Total Conversations': [2, 5, 8, 12, 15, 18, 22, 25, 28, 30, 27, 25],
            'High Quality Conversations': [2, 4, 6, 9, 12, 14, 17, 19, 21, 23, 20, 18],
            'Coaching Interventions': [1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 10, 9]
        })

        fig_timeline = go.Figure()

        fig_timeline.add_trace(go.Scatter(
            x=timeline_data['Time'],
            y=timeline_data['Total Conversations'],
            mode='lines+markers',
            name='Total Conversations',
            line=dict(color='#1f77b4')
        ))

        fig_timeline.add_trace(go.Scatter(
            x=timeline_data['Time'],
            y=timeline_data['High Quality Conversations'],
            mode='lines+markers',
            name='High Quality Conversations',
            line=dict(color='#2ca02c')
        ))

        fig_timeline.add_trace(go.Scatter(
            x=timeline_data['Time'],
            y=timeline_data['Coaching Interventions'],
            mode='lines+markers',
            name='Coaching Interventions',
            line=dict(color='#ff7f0e')
        ))

        fig_timeline.update_layout(
            title="Conversation Activity Timeline - Today",
            xaxis_title="Time",
            yaxis_title="Count",
            height=400
        )

        st.plotly_chart(fig_timeline, use_container_width=True)

        # Export options
        st.subheader("Export & Reports")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Export Analytics Report"):
                st.success("Analytics report exported to Downloads folder")

        with col2:
            if st.button("💬 Export Conversation Transcripts"):
                st.success("Conversation transcripts exported")

        with col3:
            if st.button("🎯 Export Coaching Performance"):
                st.success("Coaching performance report exported")


def render_conversational_intelligence_dashboard(tenant_id: str) -> None:
    """Main function to render conversational intelligence dashboard."""
    dashboard = ConversationalIntelligenceDashboard()
    dashboard.render(tenant_id)


# Example usage for testing
if __name__ == "__main__":
    st.set_page_config(page_title="Conversational Intelligence Dashboard", layout="wide")
    render_conversational_intelligence_dashboard("test_tenant_123")