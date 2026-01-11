"""
Real-Time Agent Assistance Dashboard Components

Streamlit components that provide live insights and guidance to real estate agents
during conversations with prospects. Integrates with the Lead Evaluation Orchestrator
and Claude Semantic Analyzer for comprehensive real-time assistance.

Components:
- Live Lead Score Dashboard
- Objection Detection and Response Panel
- Qualification Progress Tracker
- Real-Time Conversation Analysis
- Next Best Action Recommendations
- Market Intelligence Panel
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Local imports
from models.evaluation_models import (
    LeadEvaluationResult,
    ObjectionAnalysis,
    RecommendedAction,
    QualificationProgress,
    AgentAssistanceData,
    SentimentType,
    EngagementLevel,
    ActionPriority
)


class AgentAssistanceDashboard:
    """
    Comprehensive real-time agent assistance dashboard for lead conversations.
    """

    def __init__(self):
        """Initialize dashboard with default settings."""
        self.refresh_interval = 2  # seconds
        self.max_history_items = 50
        self.color_scheme = {
            'primary': '#d4af37',  # Luxury gold
            'secondary': '#1e3a8a',  # Deep blue
            'success': '#059669',  # Emerald
            'warning': '#f59e0b',  # Amber
            'danger': '#dc2626',  # Red
            'background': '#f8fafc',  # Light gray
            'card': '#ffffff',  # White
            'text': '#1e293b'  # Charcoal
        }

    def render_main_dashboard(
        self,
        evaluation_result: LeadEvaluationResult,
        conversation_context: Optional[Dict[str, Any]] = None,
        live_mode: bool = True
    ) -> None:
        """
        Render the main agent assistance dashboard.

        Args:
            evaluation_result: Latest lead evaluation result
            conversation_context: Current conversation context
            live_mode: Whether to enable live updates
        """
        st.markdown("""
        <div class="agent-dashboard-header">
            <h1 style="
                font-family: 'Playfair Display', serif;
                color: var(--luxury-charcoal, #1e293b);
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            ">🎯 Agent Intelligence Dashboard</h1>
            <p style="color: var(--luxury-slate, #64748b); font-size: 1rem;">
                Real-time lead insights and conversation guidance
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Create layout columns
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            self._render_lead_score_card(evaluation_result)
            self._render_qualification_progress(evaluation_result.qualification_progress)

        with col2:
            self._render_conversation_analysis(evaluation_result.agent_assistance)
            self._render_objection_alerts(evaluation_result.agent_assistance.detected_objections)

        with col3:
            self._render_recommended_actions(evaluation_result.recommended_actions)
            self._render_suggested_questions(evaluation_result.agent_assistance.suggested_questions)

        # Bottom row - comprehensive panels
        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Detailed Analytics",
            "💬 Conversation Flow",
            "🎯 Action Plan",
            "📈 Performance Metrics"
        ])

        with tab1:
            self._render_detailed_analytics(evaluation_result)

        with tab2:
            self._render_conversation_flow_analysis(evaluation_result.agent_assistance)

        with tab3:
            self._render_action_plan_panel(evaluation_result)

        with tab4:
            self._render_performance_metrics(evaluation_result)

        # Live update controls
        if live_mode:
            self._render_live_update_controls()

    def _render_lead_score_card(self, evaluation_result: LeadEvaluationResult) -> None:
        """Render lead score card with visual indicators."""
        score = evaluation_result.scoring_breakdown.composite_score
        tier = evaluation_result.qualification_progress.qualification_tier

        # Determine color based on score
        if score >= 85:
            color = self.color_scheme['success']
            icon = "🔥"
            status = "HOT LEAD"
        elif score >= 70:
            color = self.color_scheme['warning']
            icon = "⭐"
            status = "WARM LEAD"
        elif score >= 50:
            color = self.color_scheme['secondary']
            icon = "📈"
            status = "DEVELOPING"
        else:
            color = self.color_scheme['danger']
            icon = "❄️"
            status = "COLD LEAD"

        st.markdown(f"""
        <div class="luxury-card" style="
            text-align: center;
            padding: 1.5rem;
            background: linear-gradient(135deg, {color}15, {color}05);
            border: 1px solid {color}40;
            border-radius: 12px;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="
                font-size: 2.5rem;
                font-weight: 800;
                color: {color};
                margin-bottom: 0.5rem;
            ">{score:.1f}</div>
            <div style="
                font-size: 0.875rem;
                font-weight: 600;
                color: {color};
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.25rem;
            ">{status}</div>
            <div style="
                font-size: 0.75rem;
                color: var(--luxury-slate, #64748b);
                text-transform: capitalize;
            ">Tier: {tier.replace('_', ' ')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Score breakdown
        with st.expander("📊 Score Breakdown", expanded=False):
            breakdown = evaluation_result.scoring_breakdown

            breakdown_data = {
                "Budget Alignment": breakdown.budget_alignment,
                "Timeline Urgency": breakdown.timeline_urgency,
                "Location Match": breakdown.location_preference,
                "Engagement Level": breakdown.engagement_level,
                "Qualification Complete": breakdown.qualification_completeness,
                "Communication Quality": breakdown.communication_quality
            }

            for component, value in breakdown_data.items():
                progress_color = self._get_progress_color(value)
                st.markdown(f"""
                <div style="margin-bottom: 0.75rem;">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        font-size: 0.875rem;
                        font-weight: 500;
                        margin-bottom: 0.25rem;
                    ">
                        <span>{component}</span>
                        <span style="color: {progress_color}; font-weight: 600;">{value:.1f}</span>
                    </div>
                    <div style="
                        width: 100%;
                        height: 6px;
                        background-color: #e2e8f0;
                        border-radius: 3px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: {value}%;
                            height: 100%;
                            background-color: {progress_color};
                            border-radius: 3px;
                            transition: width 0.3s ease;
                        "></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    def _render_qualification_progress(self, progress: QualificationProgress) -> None:
        """Render qualification progress tracker."""
        completion_pct = progress.completion_percentage
        color = self._get_progress_color(completion_pct)

        st.markdown(f"""
        <div class="luxury-card" style="
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
            ">
                <h3 style="
                    font-family: var(--font-body, Inter);
                    font-size: 1rem;
                    font-weight: 600;
                    color: var(--luxury-charcoal, #1e293b);
                    margin: 0;
                ">📋 Qualification Progress</h3>
                <span style="
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: {color};
                ">{completion_pct:.0f}%</span>
            </div>

            <!-- Progress Ring -->
            <div style="
                display: flex;
                justify-content: center;
                margin-bottom: 1rem;
            ">
                <svg width="80" height="80" style="transform: rotate(-90deg);">
                    <circle
                        cx="40" cy="40" r="30"
                        fill="none"
                        stroke="#e2e8f0"
                        stroke-width="8"
                    />
                    <circle
                        cx="40" cy="40" r="30"
                        fill="none"
                        stroke="{color}"
                        stroke-width="8"
                        stroke-dasharray="{2 * 3.14159 * 30}"
                        stroke-dashoffset="{2 * 3.14159 * 30 * (1 - completion_pct/100)}"
                        stroke-linecap="round"
                        style="transition: stroke-dashoffset 1s ease-in-out;"
                    />
                </svg>
            </div>

            <div style="text-align: center; font-size: 0.875rem; color: var(--luxury-slate, #64748b);">
                {progress.completed_fields} of {progress.total_fields} critical fields complete
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Next priority fields
        if progress.next_priority_fields:
            st.markdown("**🎯 Next Priority Fields:**")
            for field in progress.next_priority_fields[:3]:
                st.markdown(f"• {field.replace('_', ' ').title()}")

    def _render_conversation_analysis(self, assistance_data: AgentAssistanceData) -> None:
        """Render real-time conversation analysis panel."""
        st.markdown("""
        <div class="luxury-card" style="padding: 1.5rem; margin-bottom: 1rem;">
            <h3 style="
                font-family: var(--font-body, Inter);
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
            ">💬 Live Conversation Analysis</h3>
        """, unsafe_allow_html=True)

        # Sentiment and engagement indicators
        col1, col2 = st.columns(2)

        with col1:
            sentiment_color = self._get_sentiment_color(assistance_data.current_sentiment)
            sentiment_icon = self._get_sentiment_icon(assistance_data.current_sentiment)

            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 1rem;
                background: {sentiment_color}15;
                border-radius: 8px;
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{sentiment_icon}</div>
                <div style="
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: {sentiment_color};
                    text-transform: uppercase;
                ">Sentiment</div>
                <div style="
                    font-size: 0.75rem;
                    color: var(--luxury-slate, #64748b);
                    text-transform: capitalize;
                ">{assistance_data.current_sentiment.replace('_', ' ')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            engagement_color = self._get_engagement_color(assistance_data.engagement_level)
            engagement_icon = self._get_engagement_icon(assistance_data.engagement_level)

            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 1rem;
                background: {engagement_color}15;
                border-radius: 8px;
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{engagement_icon}</div>
                <div style="
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: {engagement_color};
                    text-transform: uppercase;
                ">Engagement</div>
                <div style="
                    font-size: 0.75rem;
                    color: var(--luxury-slate, #64748b);
                    text-transform: capitalize;
                ">{assistance_data.engagement_level.replace('_', ' ')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Conversation stage and flow
        st.markdown(f"""
        <div style="
            padding: 0.75rem;
            background: var(--luxury-background, #f8fafc);
            border-radius: 6px;
            margin-top: 1rem;
        ">
            <div style="
                font-size: 0.875rem;
                font-weight: 500;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 0.25rem;
            ">Current Stage:</div>
            <div style="
                font-size: 0.75rem;
                color: var(--luxury-slate, #64748b);
                text-transform: capitalize;
            ">{assistance_data.conversation_flow_stage.replace('_', ' ')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_objection_alerts(self, objections: List[ObjectionAnalysis]) -> None:
        """Render objection detection alerts."""
        st.markdown("""
        <div class="luxury-card" style="padding: 1.5rem; margin-bottom: 1rem;">
            <h3 style="
                font-family: var(--font-body, Inter);
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 1rem;
            ">⚠️ Objection Alerts</h3>
        """, unsafe_allow_html=True)

        if not objections:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 2rem;
                color: var(--luxury-slate, #64748b);
                font-style: italic;
            ">
                ✅ No objections detected<br>
                <span style="font-size: 0.875rem;">Conversation flowing smoothly</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            for objection in objections:
                severity_color = self._get_severity_color(objection.severity)
                icon = self._get_objection_icon(objection.objection_type)

                st.markdown(f"""
                <div style="
                    padding: 1rem;
                    border: 1px solid {severity_color}40;
                    border-left: 4px solid {severity_color};
                    border-radius: 8px;
                    margin-bottom: 0.75rem;
                    background: {severity_color}10;
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        margin-bottom: 0.5rem;
                    ">
                        <span style="font-size: 1.25rem; margin-right: 0.5rem;">{icon}</span>
                        <span style="
                            font-weight: 600;
                            color: {severity_color};
                            text-transform: capitalize;
                        ">{objection.objection_type.replace('_', ' ')} Objection</span>
                        <span style="
                            margin-left: auto;
                            font-size: 0.75rem;
                            background: {severity_color};
                            color: white;
                            padding: 0.25rem 0.5rem;
                            border-radius: 12px;
                        ">Severity: {objection.severity:.1f}</span>
                    </div>

                    <div style="
                        font-size: 0.875rem;
                        color: var(--luxury-charcoal, #1e293b);
                        margin-bottom: 0.75rem;
                        font-style: italic;
                    ">"{objection.raw_text}"</div>

                    {self._render_objection_responses(objection.suggested_responses)}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_objection_responses(self, responses: List[str]) -> str:
        """Render suggested responses for objections."""
        if not responses:
            return ""

        response_html = """
        <div style="margin-top: 0.5rem;">
            <div style="
                font-size: 0.75rem;
                font-weight: 600;
                color: var(--luxury-deep-blue, #1e3a8a);
                text-transform: uppercase;
                margin-bottom: 0.5rem;
            ">Suggested Responses:</div>
        """

        for i, response in enumerate(responses[:3]):  # Show top 3 responses
            response_html += f"""
            <div style="
                font-size: 0.75rem;
                color: var(--luxury-slate, #64748b);
                margin-bottom: 0.25rem;
                padding-left: 0.75rem;
                border-left: 2px solid var(--luxury-gold, #d4af37);
            ">• {response}</div>
            """

        response_html += "</div>"
        return response_html

    def _render_recommended_actions(self, actions: List[RecommendedAction]) -> None:
        """Render recommended actions panel."""
        st.markdown("""
        <div class="luxury-card" style="padding: 1.5rem; margin-bottom: 1rem;">
            <h3 style="
                font-family: var(--font-body, Inter);
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 1rem;
            ">🎯 Recommended Actions</h3>
        """, unsafe_allow_html=True)

        if not actions:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 1.5rem;
                color: var(--luxury-slate, #64748b);
                font-style: italic;
            ">Continue current conversation flow</div>
            """, unsafe_allow_html=True)
        else:
            # Sort actions by priority
            sorted_actions = sorted(actions, key=lambda x: self._priority_order(x.priority))

            for action in sorted_actions[:5]:  # Show top 5 actions
                priority_color = self._get_priority_color(action.priority)
                priority_icon = self._get_priority_icon(action.priority)

                st.markdown(f"""
                <div style="
                    padding: 1rem;
                    border: 1px solid {priority_color}40;
                    border-radius: 8px;
                    margin-bottom: 0.75rem;
                    background: {priority_color}10;
                    cursor: pointer;
                    transition: all 0.2s ease;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                    <div style="
                        display: flex;
                        align-items: center;
                        margin-bottom: 0.5rem;
                    ">
                        <span style="font-size: 1rem; margin-right: 0.5rem;">{priority_icon}</span>
                        <span style="
                            font-weight: 600;
                            color: {priority_color};
                            text-transform: uppercase;
                            font-size: 0.75rem;
                        ">{action.priority.value}</span>
                        <span style="
                            margin-left: auto;
                            font-size: 0.75rem;
                            color: var(--luxury-slate, #64748b);
                        ">{action.estimated_duration}min</span>
                    </div>

                    <div style="
                        font-size: 0.875rem;
                        font-weight: 500;
                        color: var(--luxury-charcoal, #1e293b);
                        margin-bottom: 0.5rem;
                    ">{action.description}</div>

                    <div style="
                        font-size: 0.75rem;
                        color: var(--luxury-slate, #64748b);
                    ">{action.reasoning}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_suggested_questions(self, questions: List[str]) -> None:
        """Render suggested questions panel."""
        st.markdown("""
        <div class="luxury-card" style="padding: 1.5rem;">
            <h3 style="
                font-family: var(--font-body, Inter);
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 1rem;
            ">❓ Suggested Questions</h3>
        """, unsafe_allow_html=True)

        if not questions:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 1.5rem;
                color: var(--luxury-slate, #64748b);
                font-style: italic;
            ">Let the conversation flow naturally</div>
            """, unsafe_allow_html=True)
        else:
            for i, question in enumerate(questions[:5]):
                st.markdown(f"""
                <div style="
                    padding: 0.75rem;
                    background: var(--luxury-background, #f8fafc);
                    border-radius: 6px;
                    margin-bottom: 0.5rem;
                    border-left: 3px solid var(--luxury-gold, #d4af37);
                    cursor: pointer;
                    transition: background 0.2s ease;
                " onmouseover="this.style.background='#e2e8f0';"
                   onmouseout="this.style.background='#f8fafc';">
                    <div style="
                        font-size: 0.875rem;
                        color: var(--luxury-charcoal, #1e293b);
                        line-height: 1.4;
                    ">"{question}"</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Additional dashboard panels for tabs
    def _render_detailed_analytics(self, evaluation_result: LeadEvaluationResult) -> None:
        """Render detailed analytics tab."""
        col1, col2 = st.columns(2)

        with col1:
            # Scoring components chart
            breakdown = evaluation_result.scoring_breakdown
            components = {
                'Budget': breakdown.budget_alignment,
                'Timeline': breakdown.timeline_urgency,
                'Location': breakdown.location_preference,
                'Engagement': breakdown.engagement_level,
                'Qualification': breakdown.qualification_completeness,
                'Communication': breakdown.communication_quality
            }

            fig = go.Figure(data=go.Bar(
                x=list(components.values()),
                y=list(components.keys()),
                orientation='h',
                marker_color=self.color_scheme['primary']
            ))

            fig.update_layout(
                title="Scoring Components",
                xaxis_title="Score",
                yaxis_title="Components",
                height=400,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Confidence intervals
            confidence_data = {
                'Component': ['Overall Score', 'Data Quality', 'Model Confidence'],
                'Confidence': [
                    evaluation_result.confidence_score * 100,
                    evaluation_result.data_freshness_score * 100,
                    evaluation_result.evaluation_quality_score * 100
                ]
            }

            fig = px.bar(
                confidence_data,
                x='Component',
                y='Confidence',
                title="Confidence Metrics",
                color='Confidence',
                color_continuous_scale='Viridis'
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Performance metrics
        st.markdown("### 📊 Evaluation Performance")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Evaluation Time",
                f"{evaluation_result.evaluation_duration_ms}ms",
                delta=None
            )

        with col2:
            st.metric(
                "Cache Hit Rate",
                f"{evaluation_result.cache_hit_rate * 100:.1f}%",
                delta=None
            )

        with col3:
            st.metric(
                "API Calls",
                str(evaluation_result.api_calls_made),
                delta=None
            )

        with col4:
            st.metric(
                "Model Version",
                evaluation_result.orchestrator_version,
                delta=None
            )

    def _render_conversation_flow_analysis(self, assistance_data: AgentAssistanceData) -> None:
        """Render conversation flow analysis."""
        st.markdown("### 📈 Conversation Effectiveness")

        # Create metrics display
        col1, col2, col3 = st.columns(3)

        with col1:
            effectiveness = assistance_data.conversation_effectiveness
            color = self._get_progress_color(effectiveness * 10)

            st.markdown(f"""
            <div style="text-align: center;">
                <div style="
                    font-size: 2rem;
                    color: {color};
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                ">{effectiveness:.1f}/10</div>
                <div style="
                    font-size: 0.875rem;
                    color: var(--luxury-slate, #64748b);
                ">Conversation Effectiveness</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            rapport = assistance_data.rapport_building_score
            color = self._get_progress_color(rapport * 10)

            st.markdown(f"""
            <div style="text-align: center;">
                <div style="
                    font-size: 2rem;
                    color: {color};
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                ">{rapport:.1f}/10</div>
                <div style="
                    font-size: 0.875rem;
                    color: var(--luxury-slate, #64748b);
                ">Rapport Building</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            info_rate = assistance_data.information_gathering_rate
            color = self._get_progress_color(info_rate * 10)

            st.markdown(f"""
            <div style="text-align: center;">
                <div style="
                    font-size: 2rem;
                    color: {color};
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                ">{info_rate:.1f}/10</div>
                <div style="
                    font-size: 0.875rem;
                    color: var(--luxury-slate, #64748b);
                ">Info Gathering Rate</div>
            </div>
            """, unsafe_allow_html=True)

        # Conversation insights
        st.markdown("### 💡 Key Insights")

        insights = []
        if assistance_data.conversation_effectiveness > 8.0:
            insights.append("✅ Excellent conversation flow - keep current approach")
        elif assistance_data.conversation_effectiveness < 5.0:
            insights.append("⚠️ Consider changing conversation strategy")

        if assistance_data.rapport_building_score > 8.0:
            insights.append("✅ Strong rapport established")
        elif assistance_data.rapport_building_score < 5.0:
            insights.append("💡 Focus more on relationship building")

        if assistance_data.information_gathering_rate > 7.0:
            insights.append("✅ Excellent qualification progress")
        else:
            insights.append("🎯 Increase focus on gathering key information")

        for insight in insights:
            st.markdown(f"• {insight}")

    def _render_action_plan_panel(self, evaluation_result: LeadEvaluationResult) -> None:
        """Render action plan panel."""
        st.markdown("### 📋 Comprehensive Action Plan")

        # Immediate actions
        immediate_actions = [
            action for action in evaluation_result.recommended_actions
            if action.priority == ActionPriority.IMMEDIATE
        ]

        if immediate_actions:
            st.markdown("#### 🚨 Immediate Actions")
            for action in immediate_actions:
                st.markdown(f"• **{action.action_type.replace('_', ' ').title()}**: {action.description}")

        # Short-term actions
        short_term_actions = [
            action for action in evaluation_result.recommended_actions
            if action.priority in [ActionPriority.HIGH, ActionPriority.MEDIUM]
        ]

        if short_term_actions:
            st.markdown("#### ⏰ Next Steps")
            for action in short_term_actions:
                st.markdown(f"• {action.description} ({action.estimated_duration} min)")

        # Qualification gaps
        gaps = evaluation_result.agent_assistance.qualification_gaps
        if gaps:
            st.markdown("#### 📝 Information Needed")
            for gap in gaps:
                st.markdown(f"• {gap.replace('_', ' ').title()}")

    def _render_performance_metrics(self, evaluation_result: LeadEvaluationResult) -> None:
        """Render performance metrics."""
        st.markdown("### 📊 System Performance")

        metrics_data = {
            'Metric': [
                'Evaluation Duration',
                'Cache Hit Rate',
                'Confidence Score',
                'Data Freshness',
                'Evaluation Quality'
            ],
            'Value': [
                evaluation_result.evaluation_duration_ms,
                evaluation_result.cache_hit_rate * 100,
                evaluation_result.confidence_score * 100,
                evaluation_result.data_freshness_score * 100,
                evaluation_result.evaluation_quality_score * 100
            ],
            'Unit': ['ms', '%', '%', '%', '%']
        }

        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)

        # Model versions
        st.markdown("#### 🔧 Model Versions")
        for model, version in evaluation_result.model_versions.items():
            st.markdown(f"• **{model.replace('_', ' ').title()}**: {version}")

    def _render_live_update_controls(self) -> None:
        """Render live update controls."""
        st.markdown("---")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("**🔄 Live Updates**")

        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=True)

        with col3:
            if st.button("🔄 Refresh Now"):
                st.rerun()

        if auto_refresh:
            time.sleep(self.refresh_interval)
            st.rerun()

    # Helper methods for styling and colors
    def _get_progress_color(self, value: float) -> str:
        """Get color based on progress value."""
        if value >= 80:
            return self.color_scheme['success']
        elif value >= 60:
            return self.color_scheme['warning']
        elif value >= 40:
            return self.color_scheme['secondary']
        else:
            return self.color_scheme['danger']

    def _get_sentiment_color(self, sentiment: SentimentType) -> str:
        """Get color for sentiment."""
        sentiment_colors = {
            SentimentType.VERY_POSITIVE: self.color_scheme['success'],
            SentimentType.POSITIVE: self.color_scheme['success'],
            SentimentType.NEUTRAL: self.color_scheme['secondary'],
            SentimentType.CONCERNED: self.color_scheme['warning'],
            SentimentType.FRUSTRATED: self.color_scheme['danger'],
            SentimentType.ANGRY: self.color_scheme['danger']
        }
        return sentiment_colors.get(sentiment, self.color_scheme['secondary'])

    def _get_sentiment_icon(self, sentiment: SentimentType) -> str:
        """Get icon for sentiment."""
        sentiment_icons = {
            SentimentType.VERY_POSITIVE: "😍",
            SentimentType.POSITIVE: "😊",
            SentimentType.NEUTRAL: "😐",
            SentimentType.CONCERNED: "😟",
            SentimentType.FRUSTRATED: "😤",
            SentimentType.ANGRY: "😡"
        }
        return sentiment_icons.get(sentiment, "😐")

    def _get_engagement_color(self, engagement: EngagementLevel) -> str:
        """Get color for engagement level."""
        engagement_colors = {
            EngagementLevel.HIGHLY_ENGAGED: self.color_scheme['success'],
            EngagementLevel.ENGAGED: self.color_scheme['success'],
            EngagementLevel.MODERATELY_ENGAGED: self.color_scheme['warning'],
            EngagementLevel.PASSIVE: self.color_scheme['secondary'],
            EngagementLevel.DISENGAGED: self.color_scheme['danger']
        }
        return engagement_colors.get(engagement, self.color_scheme['secondary'])

    def _get_engagement_icon(self, engagement: EngagementLevel) -> str:
        """Get icon for engagement level."""
        engagement_icons = {
            EngagementLevel.HIGHLY_ENGAGED: "🔥",
            EngagementLevel.ENGAGED: "⭐",
            EngagementLevel.MODERATELY_ENGAGED: "👍",
            EngagementLevel.PASSIVE: "😴",
            EngagementLevel.DISENGAGED: "💤"
        }
        return engagement_icons.get(engagement, "😐")

    def _get_severity_color(self, severity: float) -> str:
        """Get color based on objection severity."""
        if severity >= 7.0:
            return self.color_scheme['danger']
        elif severity >= 4.0:
            return self.color_scheme['warning']
        else:
            return self.color_scheme['secondary']

    def _get_objection_icon(self, objection_type) -> str:
        """Get icon for objection type."""
        objection_icons = {
            "price": "💰",
            "timeline": "⏰",
            "location": "📍",
            "financing": "🏦",
            "features": "🏠",
            "market_conditions": "📈",
            "trust": "🤝",
            "competition": "🏆",
            "family_decision": "👨‍👩‍👧‍👦",
            "other": "❓"
        }
        return objection_icons.get(str(objection_type), "❓")

    def _get_priority_color(self, priority: ActionPriority) -> str:
        """Get color for action priority."""
        priority_colors = {
            ActionPriority.IMMEDIATE: self.color_scheme['danger'],
            ActionPriority.HIGH: self.color_scheme['warning'],
            ActionPriority.MEDIUM: self.color_scheme['secondary'],
            ActionPriority.LOW: self.color_scheme['success'],
            ActionPriority.DEFERRED: self.color_scheme['background']
        }
        return priority_colors.get(priority, self.color_scheme['secondary'])

    def _get_priority_icon(self, priority: ActionPriority) -> str:
        """Get icon for action priority."""
        priority_icons = {
            ActionPriority.IMMEDIATE: "🚨",
            ActionPriority.HIGH: "⚡",
            ActionPriority.MEDIUM: "📌",
            ActionPriority.LOW: "📝",
            ActionPriority.DEFERRED: "📋"
        }
        return priority_icons.get(priority, "📋")

    def _priority_order(self, priority: ActionPriority) -> int:
        """Get numeric order for priority sorting."""
        order = {
            ActionPriority.IMMEDIATE: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3,
            ActionPriority.DEFERRED: 4
        }
        return order.get(priority, 5)

    # =================== CLAUDE COACHING COMPONENTS ===================

    def render_live_coaching_panel(
        self,
        agent_id: str,
        coaching_suggestions: List[str],
        urgency: str = "medium",
        conversation_stage: str = "discovery",
        last_updated: Optional[datetime] = None
    ) -> None:
        """
        Render real-time Claude coaching panel with live suggestions.

        Args:
            agent_id: Agent identifier
            coaching_suggestions: Current coaching suggestions from Claude
            urgency: Urgency level (low, medium, high, critical)
            conversation_stage: Current conversation stage
            last_updated: When suggestions were last updated
        """
        # Urgency styling
        urgency_colors = {
            "low": "#10b981",      # emerald-500
            "medium": "#f59e0b",   # amber-500
            "high": "#ef4444",     # red-500
            "critical": "#dc2626"  # red-600
        }
        urgency_icons = {
            "low": "💡",
            "medium": "⚡",
            "high": "🔥",
            "critical": "🚨"
        }

        urgency_color = urgency_colors.get(urgency, "#f59e0b")
        urgency_icon = urgency_icons.get(urgency, "💡")

        st.markdown(f"""
        <div class="luxury-card" style="
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid {urgency_color};
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="
                    font-family: var(--font-body, Inter);
                    font-size: 1.125rem;
                    font-weight: 600;
                    color: var(--luxury-charcoal, #1e293b);
                    margin: 0;
                ">{urgency_icon} Live Claude Coaching</h3>
                <div style="
                    background: {urgency_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                ">{urgency}</div>
            </div>
            <div style="
                background: rgba(59, 130, 246, 0.05);
                border-radius: 0.5rem;
                padding: 0.75rem;
                margin-bottom: 1rem;
            ">
                <p style="margin: 0; font-size: 0.875rem; color: #3b82f6;">
                    <strong>Conversation Stage:</strong> {conversation_stage.replace('_', ' ').title()}
                </p>
            </div>
        """, unsafe_allow_html=True)

        if not coaching_suggestions:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 2rem;
                color: var(--luxury-slate, #64748b);
                font-style: italic;
            ">
                🎯 Conversation flowing well<br>
                <span style="font-size: 0.875rem;">Claude is monitoring for coaching opportunities</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("#### 🎯 Current Coaching Guidance")
            for i, suggestion in enumerate(coaching_suggestions[:3], 1):
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.05));
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    border-left: 3px solid #10b981;
                ">
                    <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                        <div style="
                            background: #10b981;
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
                            {suggestion}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Last updated timestamp
        if last_updated:
            time_ago = datetime.now() - last_updated
            if time_ago.total_seconds() < 60:
                time_text = "Just now"
            elif time_ago.total_seconds() < 3600:
                time_text = f"{int(time_ago.total_seconds() / 60)} minutes ago"
            else:
                time_text = last_updated.strftime("%H:%M")

            st.markdown(f"""
            <div style="
                text-align: right;
                font-size: 0.75rem;
                color: #64748b;
                margin-top: 1rem;
                padding-top: 0.75rem;
                border-top: 1px solid #e2e8f0;
            ">
                Last updated: {time_text}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def render_claude_objection_assistant(
        self,
        objection_type: str,
        severity: str,
        suggested_responses: List[str],
        talking_points: List[str],
        follow_up_strategy: str
    ) -> None:
        """
        Render enhanced Claude objection assistant with strategic guidance.

        Args:
            objection_type: Type of objection detected
            severity: Severity level (low, medium, high)
            suggested_responses: Claude's suggested responses
            talking_points: Key talking points to address
            follow_up_strategy: Recommended follow-up approach
        """
        severity_colors = {
            "low": "#10b981",
            "medium": "#f59e0b",
            "high": "#ef4444"
        }

        objection_icons = {
            "price": "💰", "timeline": "⏰", "location": "📍",
            "financing": "🏦", "features": "🏠", "market": "📈",
            "trust": "🤝", "competition": "🏆", "family": "👨‍👩‍👧‍👦"
        }

        severity_color = severity_colors.get(severity, "#f59e0b")
        objection_icon = objection_icons.get(objection_type, "❓")

        st.markdown(f"""
        <div class="luxury-card" style="
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid {severity_color};
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="
                    font-family: var(--font-body, Inter);
                    font-size: 1.125rem;
                    font-weight: 600;
                    color: var(--luxury-charcoal, #1e293b);
                    margin: 0;
                ">{objection_icon} Claude Objection Assistant</h3>
                <div style="
                    background: {severity_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.75rem;
                    font-weight: 600;
                ">{severity.upper()}</div>
            </div>

            <div style="
                background: rgba(239, 68, 68, 0.05);
                border-radius: 0.5rem;
                padding: 0.75rem;
                margin-bottom: 1rem;
            ">
                <p style="margin: 0; font-size: 0.875rem; color: #ef4444;">
                    <strong>Objection Type:</strong> {objection_type.replace('_', ' ').title()}
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Suggested responses
        if suggested_responses:
            st.markdown("#### 💬 Claude's Suggested Responses")
            for i, response in enumerate(suggested_responses, 1):
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(37, 99, 235, 0.05));
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    border-left: 3px solid #3b82f6;
                ">
                    <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                        <div style="
                            background: #3b82f6;
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
                            "{response}"
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Talking points
        if talking_points:
            st.markdown("#### 🎯 Key Talking Points")
            for point in talking_points:
                st.markdown(f"• {point}")

        # Follow-up strategy
        if follow_up_strategy:
            st.markdown(f"""
            <div style="
                background: rgba(16, 185, 129, 0.05);
                border-radius: 0.5rem;
                padding: 1rem;
                margin-top: 1rem;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #10b981;">🎲 Follow-Up Strategy</h4>
                <p style="margin: 0; color: #1e293b; line-height: 1.5;">{follow_up_strategy}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def render_claude_question_guide(
        self,
        suggested_question: str,
        purpose: str,
        priority: str,
        expected_info: str,
        follow_up_questions: List[str]
    ) -> None:
        """
        Render Claude's intelligent question guide with contextual recommendations.

        Args:
            suggested_question: The recommended question to ask
            purpose: Question purpose (qualification, discovery, objection_handling, closing)
            priority: Priority level (high, medium, low)
            expected_info: What information this question should reveal
            follow_up_questions: Potential follow-up questions
        """
        priority_colors = {
            "high": "#ef4444",
            "medium": "#f59e0b",
            "low": "#10b981"
        }

        purpose_icons = {
            "qualification": "📋",
            "discovery": "🔍",
            "objection_handling": "🛡️",
            "closing": "🎯"
        }

        priority_color = priority_colors.get(priority, "#f59e0b")
        purpose_icon = purpose_icons.get(purpose, "❓")

        st.markdown(f"""
        <div class="luxury-card" style="
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid {priority_color};
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="
                    font-family: var(--font-body, Inter);
                    font-size: 1.125rem;
                    font-weight: 600;
                    color: var(--luxury-charcoal, #1e293b);
                    margin: 0;
                ">{purpose_icon} Claude Question Guide</h3>
                <div style="
                    background: {priority_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.75rem;
                    font-weight: 600;
                ">{priority.upper()}</div>
            </div>
        """, unsafe_allow_html=True)

        # Main suggested question
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(124, 58, 237, 0.05));
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 2px solid rgba(139, 92, 246, 0.2);
        ">
            <h4 style="margin: 0 0 1rem 0; color: #8b5cf6; display: flex; align-items: center; gap: 0.5rem;">
                💬 Recommended Question
            </h4>
            <p style="
                margin: 0;
                font-size: 1.125rem;
                color: #1e293b;
                font-weight: 500;
                line-height: 1.5;
                font-style: italic;
            ">"{suggested_question}"</p>
        </div>
        """, unsafe_allow_html=True)

        # Purpose and expected info
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div style="
                background: rgba(59, 130, 246, 0.05);
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #3b82f6;">🎯 Purpose</h4>
                <p style="margin: 0; color: #1e293b;">
                    {purpose.replace('_', ' ').title()}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="
                background: rgba(16, 185, 129, 0.05);
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #10b981;">🔍 Expected Info</h4>
                <p style="margin: 0; color: #1e293b; font-size: 0.9rem;">
                    {expected_info}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Follow-up questions
        if follow_up_questions:
            st.markdown("#### 🔗 Potential Follow-Up Questions")
            for i, follow_up in enumerate(follow_up_questions, 1):
                st.markdown(f"**{i}.** {follow_up}")

        st.markdown("</div>", unsafe_allow_html=True)

    def render_enhanced_qualification_progress(
        self,
        qualification_data: Dict[str, Any],
        semantic_completeness: float,
        claude_insights: List[str],
        missing_elements: List[str]
    ) -> None:
        """
        Render enhanced qualification progress with Claude's semantic understanding.

        Args:
            qualification_data: Current qualification status
            semantic_completeness: Claude's assessment of qualification completeness
            claude_insights: Claude's insights about the qualification
            missing_elements: Important elements Claude identifies as missing
        """
        # Progress color based on semantic completeness
        if semantic_completeness >= 80:
            progress_color = "#10b981"
            status_text = "Well Qualified"
            status_icon = "✅"
        elif semantic_completeness >= 60:
            progress_color = "#f59e0b"
            status_text = "Partially Qualified"
            status_icon = "⚠️"
        else:
            progress_color = "#ef4444"
            status_text = "Needs More Info"
            status_icon = "🔍"

        st.markdown(f"""
        <div class="luxury-card" style="
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid {progress_color};
        ">
            <h3 style="
                font-family: var(--font-body, Inter);
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--luxury-charcoal, #1e293b);
                margin-bottom: 1rem;
            ">{status_icon} Enhanced Qualification Progress</h3>
        """, unsafe_allow_html=True)

        # Semantic completeness gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=semantic_completeness,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Claude's Semantic Assessment"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': progress_color},
                'steps': [
                    {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.2)"},
                    {'range': [50, 80], 'color': "rgba(245, 158, 11, 0.2)"},
                    {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.2)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # Claude insights
        if claude_insights:
            st.markdown("#### 🧠 Claude's Insights")
            for insight in claude_insights:
                st.markdown(f"""
                <div style="
                    background: rgba(139, 92, 246, 0.05);
                    border-radius: 0.5rem;
                    padding: 0.75rem;
                    margin-bottom: 0.5rem;
                    border-left: 3px solid #8b5cf6;
                ">
                    <p style="margin: 0; color: #1e293b;">💡 {insight}</p>
                </div>
                """, unsafe_allow_html=True)

        # Missing elements
        if missing_elements:
            st.markdown("#### 🎯 Priority Information Gaps")
            for element in missing_elements:
                st.markdown(f"• **{element.replace('_', ' ').title()}**")

        st.markdown("</div>", unsafe_allow_html=True)


# Factory function for easy use
def create_agent_dashboard() -> AgentAssistanceDashboard:
    """Create and return an AgentAssistanceDashboard instance."""
    return AgentAssistanceDashboard()


# Usage example:
"""
# In your main Streamlit app
dashboard = create_agent_dashboard()

# Render main dashboard (assuming you have evaluation_result)
dashboard.render_main_dashboard(
    evaluation_result=your_evaluation_result,
    conversation_context=your_conversation_context,
    live_mode=True
)
"""