"""
Advanced Intelligence Visualization Components - Next-Generation Real Estate AI Dashboard

Cutting-edge visualization components that showcase the full power of Claude AI integration
with advanced real-time intelligence, predictive analytics, and multi-modal insights.

New Features:
- Advanced Lead Journey Mapping with AI Predictions
- Real-Time Voice & Sentiment Analysis Dashboard
- Competitive Intelligence & Market Positioning
- Intelligent Content Recommendation Engine
- Multi-Modal Document Analysis Interface
- Predictive Lead Behavior Timeline
- AI-Powered Property Matching Visualization
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import asyncio
from dataclasses import dataclass

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


# Enhanced enterprise design imports
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
    ENTERPRISE_THEME_AVAILABLE = True
except ImportError:
    ENTERPRISE_THEME_AVAILABLE = False


@dataclass
class LeadJourneyStage:
    """Represents a stage in the lead journey with AI insights."""
    stage_name: str
    stage_order: int
    entry_time: datetime
    predicted_exit_time: Optional[datetime]
    conversion_probability: float
    risk_factors: List[str]
    opportunities: List[str]
    claude_insights: List[str]
    recommended_actions: List[str]


@dataclass
class SentimentAnalysis:
    """Real-time sentiment analysis results."""
    timestamp: datetime
    overall_sentiment: float  # -1.0 to 1.0
    emotion_breakdown: Dict[str, float]  # emotion: intensity
    voice_tone: str
    confidence: float
    engagement_level: float
    communication_style: str
    recommended_response: str


@dataclass
class CompetitiveIntelligence:
    """Market competitive intelligence data."""
    market_segment: str
    competitive_position: str  # "Leader", "Challenger", "Follower", "Niche"
    market_share: float
    key_differentiators: List[str]
    competitive_threats: List[str]
    market_opportunities: List[str]
    pricing_position: str
    recommendation: str


@dataclass
class ContentRecommendation:
    """AI-powered content recommendation."""
    content_type: str  # "listing", "market_report", "educational", "proposal"
    title: str
    relevance_score: float
    predicted_engagement: float
    optimal_timing: str
    delivery_channel: str
    personalization_notes: List[str]
    claude_rationale: str


class AdvancedIntelligenceVisualizations(EnterpriseDashboardComponent):
    """
    Advanced visualization components for next-generation lead intelligence.

    Provides cutting-edge visual interfaces for AI insights, predictions,
    and multi-modal analysis capabilities.
    """

    def __init__(self):
        """Initialize advanced visualization system."""
        self.colors = self._get_colors()

        # Initialize session state for advanced features
        try:
            if 'advanced_intelligence_state' not in st.session_state:
                st.session_state.advanced_intelligence_state = {
                    'active_lead_journeys': {},
                    'sentiment_history': [],
                    'competitive_data': {},
                    'content_recommendations': [],
                    'document_analysis': {},
                    'voice_analysis': {}
                }
        except AttributeError:
            # Handle case when running outside streamlit context (testing)
            pass

    def _get_colors(self) -> Dict[str, str]:
        """Get color scheme (enterprise or fallback)."""
        if ENTERPRISE_THEME_AVAILABLE:
            return {
                'primary': ENTERPRISE_COLORS['navy']['600'],
                'success': ENTERPRISE_COLORS['success']['500'],
                'warning': ENTERPRISE_COLORS['warning']['500'],
                'danger': ENTERPRISE_COLORS['danger']['500'],
                'info': ENTERPRISE_COLORS['info']['500'],
                'neutral': ENTERPRISE_COLORS['neutral']['400']
            }
        else:
            return {
                'primary': '#1e3a8a',
                'success': '#10b981',
                'warning': '#f59e0b',
                'danger': '#ef4444',
                'info': '#3b82f6',
                'neutral': '#6b7280'
            }

    def render_advanced_lead_journey_map(
        self,
        lead_id: str,
        lead_name: str,
        journey_stages: List[LeadJourneyStage],
        real_time_updates: bool = True
    ) -> None:
        """
        Render advanced lead journey visualization with AI predictions.

        Args:
            lead_id: Lead identifier
            lead_name: Lead display name
            journey_stages: List of journey stages with AI insights
            real_time_updates: Enable real-time updates
        """
        # Advanced journey header
        if ENTERPRISE_THEME_AVAILABLE:
            enterprise_section_header(
                title=f"🗺️ AI-Powered Lead Journey: {lead_name}",
                subtitle="Real-time progression tracking with predictive insights",
                icon="🗺️"
            )
        else:
            st.markdown(f"""
            ### 🗺️ AI-Powered Lead Journey: {lead_name}
            *Real-time progression tracking with predictive insights*
            """)

        # Journey timeline visualization
        st.markdown("#### 📈 Intelligent Journey Timeline")

        # Create journey timeline chart
        fig = go.Figure()

        # Timeline data
        stage_names = [stage.stage_name for stage in journey_stages]
        stage_orders = [stage.stage_order for stage in journey_stages]
        conversion_probs = [stage.conversion_probability * 100 for stage in journey_stages]

        # Current stage indicator
        current_stage_idx = max(range(len(journey_stages)), key=lambda i: journey_stages[i].entry_time)

        # Add journey progression line
        fig.add_trace(go.Scatter(
            x=stage_orders,
            y=conversion_probs,
            mode='lines+markers',
            name='Conversion Probability',
            line=dict(color=self.colors['primary'], width=4),
            marker=dict(
                size=[20 if i == current_stage_idx else 12 for i in range(len(stage_orders))],
                color=[self.colors['warning'] if i == current_stage_idx else self.colors['primary']
                       for i in range(len(stage_orders))],
                symbol=['diamond' if i == current_stage_idx else 'circle'
                        for i in range(len(stage_orders))]
            ),
            text=[f"{name}<br>Probability: {prob:.1f}%" for name, prob in zip(stage_names, conversion_probs)],
            textposition="top center",
            hovertemplate="<b>%{text}</b><br>Stage: %{x}<extra></extra>"
        ))

        # Add prediction trajectory
        if len(journey_stages) > 1:
            future_stages = list(range(stage_orders[-1] + 1, stage_orders[-1] + 4))
            future_probs = []

            # Predict future probabilities based on trajectory
            trend = (conversion_probs[-1] - conversion_probs[-2]) if len(conversion_probs) > 1 else 5
            for i, stage in enumerate(future_stages):
                future_prob = min(95, max(5, conversion_probs[-1] + trend * (i + 1)))
                future_probs.append(future_prob)

            fig.add_trace(go.Scatter(
                x=future_stages,
                y=future_probs,
                mode='lines+markers',
                name='AI Prediction',
                line=dict(color=self.colors['success'], width=2, dash='dash'),
                marker=dict(size=8, color=self.colors['success'], symbol='diamond-open'),
                opacity=0.7,
                hovertemplate="<b>Predicted</b><br>Probability: %{y:.1f}%<extra></extra>"
            ))

        fig.update_layout(
            title="Lead Journey Progression with AI Predictions",
            xaxis_title="Journey Stage",
            yaxis_title="Conversion Probability (%)",
            height=400,
            showlegend=True,
            hovermode='x unified'
        )

        # Apply enterprise theme if available
        if ENTERPRISE_THEME_AVAILABLE:
            fig = apply_plotly_theme(fig)

        st.plotly_chart(fig, use_container_width=True)

        # Current stage insights
        current_stage = journey_stages[current_stage_idx]

        st.markdown("#### 🧠 Current Stage AI Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Risk factors
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['danger']}15, {self.colors['danger']}10);
                border-left: 4px solid {self.colors['danger']};
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: {self.colors['danger']}; margin: 0 0 0.5rem 0;">⚠️ Risk Factors</h4>
                <ul style="margin: 0; padding-left: 1rem;">
            """, unsafe_allow_html=True)

            for risk in current_stage.risk_factors:
                st.markdown(f"<li>{risk}</li>", unsafe_allow_html=True)

            st.markdown("</ul></div>", unsafe_allow_html=True)

        with col2:
            # Opportunities
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['success']}15, {self.colors['success']}10);
                border-left: 4px solid {self.colors['success']};
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: {self.colors['success']}; margin: 0 0 0.5rem 0;">🎯 Opportunities</h4>
                <ul style="margin: 0; padding-left: 1rem;">
            """, unsafe_allow_html=True)

            for opportunity in current_stage.opportunities:
                st.markdown(f"<li>{opportunity}</li>", unsafe_allow_html=True)

            st.markdown("</ul></div>", unsafe_allow_html=True)

        with col3:
            # Recommended actions
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['primary']}15, {self.colors['primary']}10);
                border-left: 4px solid {self.colors['primary']};
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: {self.colors['primary']}; margin: 0 0 0.5rem 0;">🚀 Next Actions</h4>
                <ul style="margin: 0; padding-left: 1rem;">
            """, unsafe_allow_html=True)

            for action in current_stage.recommended_actions:
                st.markdown(f"<li>{action}</li>", unsafe_allow_html=True)

            st.markdown("</ul></div>", unsafe_allow_html=True)

        # Claude insights
        if current_stage.claude_insights:
            st.markdown("#### 🤖 Claude's Strategic Insights")

            for i, insight in enumerate(current_stage.claude_insights, 1):
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(124, 58, 237, 0.05));
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    border-left: 3px solid #8b5cf6;
                ">
                    <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                        <div style="
                            background: #8b5cf6;
                            color: white;
                            width: 1.5rem;
                            height: 1.5rem;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 0.75rem;
                            font-weight: bold;
                            flex-shrink: 0;
                        ">{i}</div>
                        <p style="margin: 0; line-height: 1.5; color: #1e293b;">
                            {insight}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    def render_realtime_sentiment_dashboard(
        self,
        sentiment_data: List[SentimentAnalysis],
        current_conversation: Optional[str] = None
    ) -> None:
        """
        Render real-time voice and sentiment analysis dashboard.

        Args:
            sentiment_data: Historical sentiment analysis data
            current_conversation: Current conversation context
        """
        # Dashboard header
        if ENTERPRISE_THEME_AVAILABLE:
            enterprise_section_header(
                title="🎭 Real-Time Sentiment & Voice Analysis",
                subtitle="AI-powered emotional intelligence monitoring",
                icon="🎭"
            )
        else:
            st.markdown("""
            ### 🎭 Real-Time Sentiment & Voice Analysis
            *AI-powered emotional intelligence monitoring*
            """)

        if not sentiment_data:
            st.info("🎯 Start a conversation to see real-time sentiment analysis")
            return

        # Current sentiment overview
        latest_sentiment = sentiment_data[-1]

        st.markdown("#### 📊 Current Conversation State")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Overall sentiment gauge
            sentiment_color = (
                self.colors['success'] if latest_sentiment.overall_sentiment > 0.3 else
                self.colors['warning'] if latest_sentiment.overall_sentiment > -0.3 else
                self.colors['danger']
            )

            sentiment_text = (
                "Very Positive" if latest_sentiment.overall_sentiment > 0.6 else
                "Positive" if latest_sentiment.overall_sentiment > 0.3 else
                "Neutral" if latest_sentiment.overall_sentiment > -0.3 else
                "Negative" if latest_sentiment.overall_sentiment > -0.6 else
                "Very Negative"
            )

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Overall Sentiment",
                    value=sentiment_text,
                    delta=f"{latest_sentiment.overall_sentiment:+.2f}",
                    delta_type="positive" if latest_sentiment.overall_sentiment > 0 else "negative",
                    icon="😊" if latest_sentiment.overall_sentiment > 0 else "😐" if latest_sentiment.overall_sentiment == 0 else "😟"
                )
            else:
                st.metric(
                    "Overall Sentiment",
                    sentiment_text,
                    f"{latest_sentiment.overall_sentiment:+.2f}"
                )

        with col2:
            # Voice tone
            tone_icon = {
                "Calm": "😌", "Excited": "🤩", "Concerned": "😟",
                "Frustrated": "😤", "Professional": "💼", "Friendly": "😊"
            }.get(latest_sentiment.voice_tone, "🎭")

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Voice Tone",
                    value=latest_sentiment.voice_tone,
                    delta=f"Confidence: {latest_sentiment.confidence:.1%}",
                    delta_type="neutral",
                    icon=tone_icon
                )
            else:
                st.metric("Voice Tone", latest_sentiment.voice_tone, f"{latest_sentiment.confidence:.1%}")

        with col3:
            # Engagement level
            engagement_color = (
                self.colors['success'] if latest_sentiment.engagement_level > 0.7 else
                self.colors['warning'] if latest_sentiment.engagement_level > 0.4 else
                self.colors['danger']
            )

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Engagement Level",
                    value=f"{latest_sentiment.engagement_level:.1%}",
                    delta="High engagement" if latest_sentiment.engagement_level > 0.7 else "Monitor closely",
                    delta_type="positive" if latest_sentiment.engagement_level > 0.7 else "warning",
                    icon="🔥" if latest_sentiment.engagement_level > 0.7 else "📈"
                )
            else:
                st.metric("Engagement Level", f"{latest_sentiment.engagement_level:.1%}")

        with col4:
            # Communication style
            style_icon = {
                "Direct": "🎯", "Analytical": "📊", "Emotional": "❤️",
                "Questioning": "❓", "Storytelling": "📖", "Technical": "🔧"
            }.get(latest_sentiment.communication_style, "💬")

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Communication Style",
                    value=latest_sentiment.communication_style,
                    delta="Adaptive response ready",
                    delta_type="info",
                    icon=style_icon
                )
            else:
                st.metric("Communication Style", latest_sentiment.communication_style)

        # Emotion breakdown radar chart
        st.markdown("#### 🎨 Emotional Profile Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Emotion radar chart
            emotions = list(latest_sentiment.emotion_breakdown.keys())
            intensities = list(latest_sentiment.emotion_breakdown.values())

            fig = go.Figure(data=go.Scatterpolar(
                r=intensities,
                theta=emotions,
                fill='toself',
                fillcolor=f'{self.colors["primary"]}40',
                line_color=self.colors['primary'],
                marker=dict(size=8, color=self.colors['primary'])
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        tickmode='linear',
                        tick0=0,
                        dtick=0.25
                    )
                ),
                showlegend=False,
                title="Real-Time Emotional Profile",
                height=350
            )

            if ENTERPRISE_THEME_AVAILABLE:
                fig = apply_plotly_theme(fig)

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Recommended response
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['success']}15, {self.colors['success']}10);
                border-left: 4px solid {self.colors['success']};
                border-radius: 8px;
                padding: 1rem;
                height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <h4 style="color: {self.colors['success']}; margin: 0 0 1rem 0;">🎯 Claude's Response Strategy</h4>
                <p style="margin: 0; line-height: 1.6; color: #1e293b; font-style: italic;">
                    "{latest_sentiment.recommended_response}"
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Sentiment timeline
        st.markdown("#### 📈 Conversation Sentiment Timeline")

        if len(sentiment_data) > 1:
            timestamps = [s.timestamp for s in sentiment_data]
            sentiment_scores = [s.overall_sentiment for s in sentiment_data]
            engagement_scores = [s.engagement_level for s in sentiment_data]

            fig = go.Figure()

            # Sentiment line
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=sentiment_scores,
                mode='lines+markers',
                name='Sentiment Score',
                line=dict(color=self.colors['primary'], width=3),
                marker=dict(size=6),
                yaxis='y'
            ))

            # Engagement line
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=engagement_scores,
                mode='lines+markers',
                name='Engagement Level',
                line=dict(color=self.colors['success'], width=3),
                marker=dict(size=6),
                yaxis='y2'
            ))

            # Add sentiment zones
            fig.add_hrect(y0=0.3, y1=1, fillcolor=self.colors['success'], opacity=0.1,
                         annotation_text="Positive Zone", yref="y")
            fig.add_hrect(y0=-0.3, y1=0.3, fillcolor=self.colors['warning'], opacity=0.1,
                         annotation_text="Neutral Zone", yref="y")
            fig.add_hrect(y0=-1, y1=-0.3, fillcolor=self.colors['danger'], opacity=0.1,
                         annotation_text="Negative Zone", yref="y")

            fig.update_layout(
                title="Conversation Emotional Journey",
                xaxis_title="Time",
                yaxis=dict(title="Sentiment Score", range=[-1, 1]),
                yaxis2=dict(title="Engagement Level", overlaying="y", side="right", range=[0, 1]),
                height=400,
                hovermode='x unified'
            )

            if ENTERPRISE_THEME_AVAILABLE:
                fig = apply_plotly_theme(fig)

            st.plotly_chart(fig, use_container_width=True)

        # Insights and alerts
        st.markdown("#### 🚨 AI-Powered Conversation Alerts")

        # Generate insights based on sentiment data
        insights = self._generate_sentiment_insights(sentiment_data)

        for insight in insights:
            if insight['type'] == 'warning':
                st.warning(f"⚠️ **{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'success':
                st.success(f"✅ **{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'info':
                st.info(f"💡 **{insight['title']}**: {insight['message']}")

    def render_competitive_intelligence_dashboard(
        self,
        competitive_data: CompetitiveIntelligence,
        market_trends: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Render competitive intelligence and market positioning dashboard.

        Args:
            competitive_data: Competitive intelligence analysis
            market_trends: Optional market trend data
        """
        # Header
        if ENTERPRISE_THEME_AVAILABLE:
            enterprise_section_header(
                title="🏆 Competitive Intelligence & Market Position",
                subtitle="AI-driven market analysis and competitive insights",
                icon="🏆"
            )
        else:
            st.markdown("""
            ### 🏆 Competitive Intelligence & Market Position
            *AI-driven market analysis and competitive insights*
            """)

        # Competitive positioning overview
        st.markdown("#### 📊 Market Positioning Analysis")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            position_color = {
                "Leader": self.colors['success'],
                "Challenger": self.colors['warning'],
                "Follower": self.colors['info'],
                "Niche": self.colors['primary']
            }.get(competitive_data.competitive_position, self.colors['neutral'])

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Market Position",
                    value=competitive_data.competitive_position,
                    delta=f"in {competitive_data.market_segment}",
                    delta_type="neutral",
                    icon="🏆"
                )
            else:
                st.metric("Market Position", competitive_data.competitive_position)

        with col2:
            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Market Share",
                    value=f"{competitive_data.market_share:.1%}",
                    delta="vs. competitors",
                    delta_type="neutral",
                    icon="📈"
                )
            else:
                st.metric("Market Share", f"{competitive_data.market_share:.1%}")

        with col3:
            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Pricing Position",
                    value=competitive_data.pricing_position,
                    delta="relative to market",
                    delta_type="neutral",
                    icon="💰"
                )
            else:
                st.metric("Pricing Position", competitive_data.pricing_position)

        with col4:
            # Calculate competitive strength score
            strength_score = (
                len(competitive_data.key_differentiators) * 20 +
                (100 - len(competitive_data.competitive_threats) * 15) +
                len(competitive_data.market_opportunities) * 15
            ) / 100

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Competitive Strength",
                    value=f"{strength_score:.1%}",
                    delta="AI assessment",
                    delta_type="positive" if strength_score > 0.7 else "warning",
                    icon="💪"
                )
            else:
                st.metric("Competitive Strength", f"{strength_score:.1%}")

        # Competitive matrix visualization
        st.markdown("#### 🎯 Competitive Analysis Matrix")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Create competitive positioning matrix
            competitors = ["Your Brokerage", "Competitor A", "Competitor B", "Competitor C", "Competitor D"]
            market_share = [competitive_data.market_share * 100, 28.5, 22.1, 18.9, 12.3]
            innovation_score = [85, 72, 78, 65, 70]  # Sample data

            fig = px.scatter(
                x=market_share,
                y=innovation_score,
                size=[20, 15, 17, 12, 13],
                color=competitors,
                title="Competitive Positioning Matrix",
                labels={
                    'x': 'Market Share (%)',
                    'y': 'Innovation Score'
                },
                hover_data={'x': True, 'y': True}
            )

            # Add quadrant lines
            fig.add_hline(y=75, line_dash="dash", line_color="gray")
            fig.add_vline(x=20, line_dash="dash", line_color="gray")

            # Add quadrant labels
            fig.add_annotation(x=35, y=90, text="Leaders", showarrow=False, font_size=14, font_color="green")
            fig.add_annotation(x=10, y=90, text="Challengers", showarrow=False, font_size=14, font_color="orange")
            fig.add_annotation(x=35, y=60, text="Followers", showarrow=False, font_size=14, font_color="blue")
            fig.add_annotation(x=10, y=60, text="Niche Players", showarrow=False, font_size=14, font_color="purple")

            fig.update_layout(height=400)

            if ENTERPRISE_THEME_AVAILABLE:
                fig = apply_plotly_theme(fig)

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Key differentiators
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['success']}15, {self.colors['success']}10);
                border-left: 4px solid {self.colors['success']};
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                height: 320px;
                overflow-y: auto;
            ">
                <h4 style="color: {self.colors['success']}; margin: 0 0 1rem 0;">🎯 Key Differentiators</h4>
                <ul style="margin: 0; padding-left: 1rem;">
            """, unsafe_allow_html=True)

            for diff in competitive_data.key_differentiators:
                st.markdown(f"<li style='margin-bottom: 0.5rem;'>{diff}</li>", unsafe_allow_html=True)

            st.markdown("</ul></div>", unsafe_allow_html=True)

        # Threats and opportunities
        st.markdown("#### ⚖️ Strategic Assessment")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['danger']}15, {self.colors['danger']}10);
                border-left: 4px solid {self.colors['danger']};
                border-radius: 8px;
                padding: 1rem;
            ">
                <h4 style="color: {self.colors['danger']}; margin: 0 0 1rem 0;">⚠️ Competitive Threats</h4>
                <ul style="margin: 0; padding-left: 1rem;">
            """, unsafe_allow_html=True)

            for threat in competitive_data.competitive_threats:
                st.markdown(f"<li style='margin-bottom: 0.5rem;'>{threat}</li>", unsafe_allow_html=True)

            st.markdown("</ul></div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {self.colors['info']}15, {self.colors['info']}10);
                border-left: 4px solid {self.colors['info']};
                border-radius: 8px;
                padding: 1rem;
            ">
                <h4 style="color: {self.colors['info']}; margin: 0 0 1rem 0;">🚀 Market Opportunities</h4>
                <ul style="margin: 0; padding-left: 1rem;">
            """, unsafe_allow_html=True)

            for opportunity in competitive_data.market_opportunities:
                st.markdown(f"<li style='margin-bottom: 0.5rem;'>{opportunity}</li>", unsafe_allow_html=True)

            st.markdown("</ul></div>", unsafe_allow_html=True)

        # Strategic recommendation
        st.markdown("#### 🧠 Claude's Strategic Recommendation")

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(124, 58, 237, 0.05));
            border-radius: 8px;
            padding: 1.5rem;
            border-left: 4px solid #8b5cf6;
        ">
            <h4 style="color: #8b5cf6; margin: 0 0 1rem 0;">💡 Strategic Insight</h4>
            <p style="margin: 0; line-height: 1.6; color: #1e293b; font-size: 1.1rem; font-style: italic;">
                {competitive_data.recommendation}
            </p>
        </div>
        """, unsafe_allow_html=True)

    def render_intelligent_content_engine(
        self,
        lead_profile: Dict[str, Any],
        content_recommendations: List[ContentRecommendation]
    ) -> None:
        """
        Render intelligent content recommendation engine.

        Args:
            lead_profile: Lead profile data for personalization
            content_recommendations: AI-generated content recommendations
        """
        # Header
        if ENTERPRISE_THEME_AVAILABLE:
            enterprise_section_header(
                title="🎨 Intelligent Content Recommendation Engine",
                subtitle="AI-powered content strategy and personalization",
                icon="🎨"
            )
        else:
            st.markdown("""
            ### 🎨 Intelligent Content Recommendation Engine
            *AI-powered content strategy and personalization*
            """)

        # Content performance overview
        st.markdown("#### 📊 Content Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        avg_relevance = sum(c.relevance_score for c in content_recommendations) / len(content_recommendations) if content_recommendations else 0
        avg_engagement = sum(c.predicted_engagement for c in content_recommendations) / len(content_recommendations) if content_recommendations else 0

        with col1:
            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Content Relevance",
                    value=f"{avg_relevance:.1%}",
                    delta="AI-calculated match",
                    delta_type="positive" if avg_relevance > 0.8 else "warning",
                    icon="🎯"
                )
            else:
                st.metric("Content Relevance", f"{avg_relevance:.1%}")

        with col2:
            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Predicted Engagement",
                    value=f"{avg_engagement:.1%}",
                    delta="Expected response rate",
                    delta_type="positive" if avg_engagement > 0.7 else "neutral",
                    icon="📈"
                )
            else:
                st.metric("Predicted Engagement", f"{avg_engagement:.1%}")

        with col3:
            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Recommendations",
                    value=str(len(content_recommendations)),
                    delta="personalized items",
                    delta_type="neutral",
                    icon="📝"
                )
            else:
                st.metric("Recommendations", len(content_recommendations))

        with col4:
            # Calculate content diversity score
            content_types = set(c.content_type for c in content_recommendations)
            diversity_score = len(content_types) / 4  # Assuming 4 main content types

            if ENTERPRISE_THEME_AVAILABLE:
                enterprise_metric(
                    label="Content Diversity",
                    value=f"{diversity_score:.1%}",
                    delta="type variety",
                    delta_type="positive" if diversity_score > 0.5 else "warning",
                    icon="🌈"
                )
            else:
                st.metric("Content Diversity", f"{diversity_score:.1%}")

        # Personalized content recommendations
        st.markdown("#### 🎯 Personalized Content Recommendations")

        if content_recommendations:
            # Sort by relevance score
            sorted_recommendations = sorted(content_recommendations, key=lambda x: x.relevance_score, reverse=True)

            for i, content in enumerate(sorted_recommendations[:5], 1):
                relevance_color = (
                    self.colors['success'] if content.relevance_score > 0.8 else
                    self.colors['warning'] if content.relevance_score > 0.6 else
                    self.colors['info']
                )

                content_type_icon = {
                    "listing": "🏠",
                    "market_report": "📊",
                    "educational": "📚",
                    "proposal": "📋",
                    "newsletter": "📰",
                    "video": "🎥"
                }.get(content.content_type, "📄")

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
                    border: 1px solid {relevance_color}40;
                    border-left: 4px solid {relevance_color};
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #1e293b; display: flex; align-items: center; gap: 0.5rem;">
                                {content_type_icon} {content.title}
                                <span style="
                                    background: {relevance_color};
                                    color: white;
                                    padding: 0.2rem 0.5rem;
                                    border-radius: 1rem;
                                    font-size: 0.7rem;
                                    font-weight: 600;
                                ">#{i}</span>
                            </h4>
                            <p style="margin: 0 0 1rem 0; color: #64748b; font-size: 0.9rem;">
                                {content.content_type.replace('_', ' ').title()} •
                                Relevance: {content.relevance_score:.1%} •
                                Engagement: {content.predicted_engagement:.1%}
                            </p>
                        </div>
                        <div style="text-align: right; margin-left: 1rem;">
                            <div style="font-size: 0.8rem; color: #64748b;">Best time:</div>
                            <div style="font-weight: 600; color: #1e293b;">{content.optimal_timing}</div>
                            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">via {content.delivery_channel}</div>
                        </div>
                    </div>

                    <div style="
                        background: rgba(139, 92, 246, 0.05);
                        border-radius: 6px;
                        padding: 1rem;
                        margin-bottom: 1rem;
                    ">
                        <h5 style="margin: 0 0 0.5rem 0; color: #8b5cf6;">🧠 Claude's Rationale</h5>
                        <p style="margin: 0; color: #1e293b; font-style: italic; line-height: 1.5;">
                            {content.claude_rationale}
                        </p>
                    </div>

                    <div>
                        <h5 style="margin: 0 0 0.5rem 0; color: #1e293b;">🎨 Personalization Notes</h5>
                        <ul style="margin: 0; padding-left: 1rem; color: #64748b;">
                """, unsafe_allow_html=True)

                for note in content.personalization_notes:
                    st.markdown(f"<li style='margin-bottom: 0.25rem;'>{note}</li>", unsafe_allow_html=True)

                st.markdown("</ul></div></div>", unsafe_allow_html=True)

        # Content performance analytics
        st.markdown("#### 📈 Content Performance Analytics")

        # Create content type distribution chart
        if content_recommendations:
            content_type_counts = {}
            for content in content_recommendations:
                content_type_counts[content.content_type] = content_type_counts.get(content.content_type, 0) + 1

            col1, col2 = st.columns(2)

            with col1:
                # Content type distribution
                fig = px.pie(
                    values=list(content_type_counts.values()),
                    names=list(content_type_counts.keys()),
                    title="Content Type Distribution"
                )

                if ENTERPRISE_THEME_AVAILABLE:
                    fig = apply_plotly_theme(fig)

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Relevance vs Engagement scatter
                relevance_scores = [c.relevance_score for c in content_recommendations]
                engagement_scores = [c.predicted_engagement for c in content_recommendations]
                content_types = [c.content_type for c in content_recommendations]

                fig = px.scatter(
                    x=relevance_scores,
                    y=engagement_scores,
                    color=content_types,
                    title="Relevance vs Predicted Engagement",
                    labels={'x': 'Relevance Score', 'y': 'Predicted Engagement'}
                )

                if ENTERPRISE_THEME_AVAILABLE:
                    fig = apply_plotly_theme(fig)

                st.plotly_chart(fig, use_container_width=True)

    def _generate_sentiment_insights(self, sentiment_data: List[SentimentAnalysis]) -> List[Dict[str, str]]:
        """Generate AI insights from sentiment analysis data."""
        insights = []

        if not sentiment_data:
            return insights

        latest = sentiment_data[-1]

        # Check for concerning patterns
        if latest.overall_sentiment < -0.5:
            insights.append({
                'type': 'warning',
                'title': 'Negative Sentiment Alert',
                'message': 'Strong negative sentiment detected. Consider empathetic approach and active listening.'
            })

        # Check engagement levels
        if latest.engagement_level < 0.4:
            insights.append({
                'type': 'warning',
                'title': 'Low Engagement Warning',
                'message': 'Engagement is dropping. Try changing conversation style or asking open-ended questions.'
            })

        # Check for positive trends
        if len(sentiment_data) > 2:
            recent_trend = sentiment_data[-1].overall_sentiment - sentiment_data[-3].overall_sentiment
            if recent_trend > 0.3:
                insights.append({
                    'type': 'success',
                    'title': 'Positive Sentiment Trend',
                    'message': 'Sentiment is improving! Continue with current approach and prepare for next steps.'
                })

        # Voice tone insights
        if latest.voice_tone in ['Frustrated', 'Concerned']:
            insights.append({
                'type': 'info',
                'title': 'Voice Tone Guidance',
                'message': f'Detected {latest.voice_tone.lower()} tone. Use calm, reassuring language and validate concerns.'
            })

        return insights


# Factory function
def create_advanced_visualizations() -> AdvancedIntelligenceVisualizations:
    """Create and return an AdvancedIntelligenceVisualizations instance."""
    return AdvancedIntelligenceVisualizations()


# Sample data generators for testing
def generate_sample_journey_stages() -> List[LeadJourneyStage]:
    """Generate sample journey stages for testing."""
    return [
        LeadJourneyStage(
            stage_name="Initial Contact",
            stage_order=1,
            entry_time=datetime.now() - timedelta(days=7),
            predicted_exit_time=datetime.now() - timedelta(days=6),
            conversion_probability=0.25,
            risk_factors=["Cold outreach", "No prior relationship"],
            opportunities=["High-intent keywords in inquiry", "Specific property interest"],
            claude_insights=["Lead shows genuine interest in downtown condos", "Mentioned timeline of 3-6 months"],
            recommended_actions=["Send personalized market overview", "Schedule property viewing"]
        ),
        LeadJourneyStage(
            stage_name="Qualification",
            stage_order=2,
            entry_time=datetime.now() - timedelta(days=6),
            predicted_exit_time=datetime.now() - timedelta(days=4),
            conversion_probability=0.65,
            risk_factors=["Financing unclear", "First-time buyer concerns"],
            opportunities=["Pre-qualified budget range", "Motivated by life event"],
            claude_insights=["Strong qualification signals", "Job relocation driving urgency"],
            recommended_actions=["Connect with lender", "Show similar properties"]
        ),
        LeadJourneyStage(
            stage_name="Property Evaluation",
            stage_order=3,
            entry_time=datetime.now() - timedelta(days=4),
            predicted_exit_time=datetime.now() - timedelta(days=1),
            conversion_probability=0.85,
            risk_factors=["Competitive market", "Multiple offers possible"],
            opportunities=["Exclusive pocket listing match", "Seller flexibility on terms"],
            claude_insights=["Ready to move quickly on right property", "Values school district highly"],
            recommended_actions=["Present best matches", "Prepare offer strategy"]
        )
    ]


def generate_sample_sentiment_data() -> List[SentimentAnalysis]:
    """Generate sample sentiment data for testing."""
    base_time = datetime.now() - timedelta(minutes=30)
    sentiment_data = []

    for i in range(6):
        sentiment_data.append(SentimentAnalysis(
            timestamp=base_time + timedelta(minutes=i*5),
            overall_sentiment=np.random.uniform(-0.2, 0.8),
            emotion_breakdown={
                "Joy": np.random.uniform(0.2, 0.9),
                "Trust": np.random.uniform(0.3, 0.8),
                "Anticipation": np.random.uniform(0.1, 0.7),
                "Surprise": np.random.uniform(0.0, 0.4),
                "Fear": np.random.uniform(0.0, 0.3),
                "Sadness": np.random.uniform(0.0, 0.2)
            },
            voice_tone=np.random.choice(["Friendly", "Professional", "Excited", "Calm"]),
            confidence=np.random.uniform(0.8, 0.95),
            engagement_level=np.random.uniform(0.4, 0.9),
            communication_style=np.random.choice(["Direct", "Analytical", "Emotional"]),
            recommended_response="Match their energy level and provide specific, actionable next steps."
        ))

    return sentiment_data


def generate_sample_competitive_data() -> CompetitiveIntelligence:
    """Generate sample competitive intelligence data."""
    return CompetitiveIntelligence(
        market_segment="Luxury Residential Real Estate",
        competitive_position="Challenger",
        market_share=0.185,
        key_differentiators=[
            "Claude AI-powered lead intelligence",
            "Sub-24 hour response times",
            "Exclusive pocket listing network",
            "Personalized market analysis reports",
            "First-time buyer specialization program"
        ],
        competitive_threats=[
            "Large franchise network expansion",
            "Tech-enabled competitors with VC funding",
            "Commission compression pressures"
        ],
        market_opportunities=[
            "Growing tech professional demographic",
            "Underserved first-time buyer market",
            "Corporate relocation partnerships",
            "Luxury condo development projects"
        ],
        pricing_position="Premium",
        recommendation="Leverage AI capabilities and personalized service as primary differentiators. Focus on tech-savvy professional market segment where premium pricing is justified by superior service delivery."
    )


def generate_sample_content_recommendations() -> List[ContentRecommendation]:
    """Generate sample content recommendations."""
    return [
        ContentRecommendation(
            content_type="market_report",
            title="Q1 2026 Downtown Condo Market Analysis",
            relevance_score=0.92,
            predicted_engagement=0.78,
            optimal_timing="Tuesday 10:00 AM",
            delivery_channel="Email",
            personalization_notes=[
                "Focus on appreciation trends in target neighborhood",
                "Include school district ratings (high priority for lead)",
                "Highlight upcoming transit improvements"
            ],
            claude_rationale="Lead expressed strong interest in downtown condos and mentioned school quality concerns. Market report addresses both interests with relevant data."
        ),
        ContentRecommendation(
            content_type="listing",
            title="Exclusive: 2BR Condo with City Views - Perfect Match",
            relevance_score=0.89,
            predicted_engagement=0.85,
            optimal_timing="Today 4:30 PM",
            delivery_channel="SMS",
            personalization_notes=[
                "Matches budget range exactly",
                "Located in preferred school district",
                "Has the modern finishes mentioned as priority"
            ],
            claude_rationale="Property matches 95% of stated preferences and is priced within qualified range. High urgency due to market conditions."
        ),
        ContentRecommendation(
            content_type="educational",
            title="First-Time Buyer's Guide to Condo Ownership",
            relevance_score=0.76,
            predicted_engagement=0.71,
            optimal_timing="This Weekend",
            delivery_channel="Email",
            personalization_notes=[
                "Address HOA fees and assessments",
                "Explain condo insurance requirements",
                "Include financing options for first-time buyers"
            ],
            claude_rationale="Lead is first-time buyer with some anxiety about process. Educational content builds trust and addresses common concerns."
        )
    ]