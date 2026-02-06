"""
Jorge's Friendly Customer Service Dashboard - Rancho Cucamonga Edition
======================================================================

Customer service focused dashboard for tracking relationship quality, satisfaction
metrics, and friendly approach effectiveness. Replaces confrontational KPIs with
customer success and relationship building metrics.

Key Features:
- Customer satisfaction tracking
- Relationship quality metrics
- Rancho Cucamonga market insights
- Family-focused engagement analysis
- California DRE compliance monitoring
- Consultation success rates
- Customer experience optimization

Author: Claude Code Assistant
Created: 2026-01-25 for Friendly CA Approach
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JorgeFriendlyDashboard:
    """Customer service focused dashboard for Jorge's friendly approach"""

    def __init__(self):
        self.title = "Jorge's Customer Service Excellence Dashboard"
        self.subtitle = "Rancho Cucamonga Real Estate - Relationship Building Analytics"

        # Initialize session state
        if 'dashboard_data' not in st.session_state:
            st.session_state.dashboard_data = self._load_demo_data()

    def render(self):
        """Render the complete friendly dashboard"""

        # Dashboard Header
        self._render_header()

        # Main metrics overview
        self._render_customer_satisfaction_overview()

        # Detailed sections
        col1, col2 = st.columns([2, 1])

        with col1:
            self._render_relationship_quality_metrics()
            self._render_customer_journey_analysis()
            self._render_rancho_cucamonga_market_insights()

        with col2:
            self._render_consultation_pipeline()
            self._render_customer_feedback_summary()
            self._render_friendly_performance_metrics()

        # Bottom section
        self._render_customer_experience_optimization()

    def _render_header(self):
        """Render friendly dashboard header"""
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #4CAF50 0%, #2E7D32 100%); border-radius: 10px; margin-bottom: 30px;">
            <h1 style="color: white; margin: 0;">🤝 Jorge's Customer Service Excellence</h1>
            <h3 style="color: #E8F5E8; margin: 10px 0;">Rancho Cucamonga Real Estate - Building Relationships, Creating Success</h3>
        </div>
        """, unsafe_allow_html=True)

        # Quick stats row
        col1, col2, col3, col4, col5 = st.columns(5)

        data = st.session_state.dashboard_data

        with col1:
            st.metric("Customer Satisfaction", "4.8/5.0", "↗️ +0.2")

        with col2:
            st.metric("Consultation Ready", f"{data['consultation_ready']}", f"↗️ +{data['consultation_growth']}")

        with col3:
            st.metric("Avg Relationship Score", "8.4/10", "↗️ +0.6")

        with col4:
            st.metric("Response Rate", "94%", "↗️ +8%")

        with col5:
            st.metric("Referral Rate", "23%", "↗️ +5%")

    def _render_customer_satisfaction_overview(self):
        """Render customer satisfaction metrics overview"""
        st.markdown("### 😊 Customer Satisfaction Overview")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Customer satisfaction gauge
            fig_satisfaction = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=4.8,
                title={'text': "Overall Satisfaction (5.0 Scale)"},
                delta={'reference': 4.6},
                gauge={
                    'axis': {'range': [None, 5]},
                    'bar': {'color': "#4CAF50"},
                    'steps': [
                        {'range': [0, 3], 'color': "#ffebee"},
                        {'range': [3, 4], 'color': "#fff3e0"},
                        {'range': [4, 5], 'color': "#e8f5e8"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 4.5
                    }
                }
            ))
            fig_satisfaction.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
            st.plotly_chart(fig_satisfaction, use_container_width=True)

        with col2:
            # Response quality distribution
            response_data = {
                'Quality Level': ['Excellent', 'Good', 'Fair', 'Poor'],
                'Percentage': [68, 24, 7, 1],
                'Count': [142, 50, 15, 2]
            }
            fig_quality = px.pie(
                values=response_data['Percentage'],
                names=response_data['Quality Level'],
                title="Response Quality Distribution",
                color_discrete_map={
                    'Excellent': '#4CAF50',
                    'Good': '#8BC34A',
                    'Fair': '#FFC107',
                    'Poor': '#F44336'
                }
            )
            fig_quality.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
            st.plotly_chart(fig_quality, use_container_width=True)

        with col3:
            # Customer journey completion
            journey_data = {
                'Stage': ['Initial Contact', 'Engaged', 'Interested', 'Ready to Move', 'Consultation'],
                'Count': [250, 195, 142, 67, 48],
                'Conversion': [100, 78, 57, 27, 19]
            }
            fig_journey = px.funnel(
                y=journey_data['Stage'],
                x=journey_data['Count'],
                title="Customer Journey Completion",
                color_discrete_sequence=['#4CAF50']
            )
            fig_journey.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
            st.plotly_chart(fig_journey, use_container_width=True)

    def _render_relationship_quality_metrics(self):
        """Render relationship quality tracking"""
        st.markdown("### 💖 Relationship Quality Metrics")

        # Relationship score trends over time
        dates = pd.date_range(start='2026-01-01', end='2026-01-25', freq='D')
        relationship_scores = np.random.normal(8.2, 0.8, len(dates))
        relationship_scores = np.clip(relationship_scores, 5.0, 10.0)  # Keep within bounds

        engagement_scores = np.random.normal(7.8, 0.6, len(dates))
        engagement_scores = np.clip(engagement_scores, 5.0, 10.0)

        fig_relationship = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Relationship Quality Score Trend', 'Customer Engagement Level'),
            shared_xaxes=True
        )

        fig_relationship.add_trace(
            go.Scatter(
                x=dates,
                y=relationship_scores,
                name='Relationship Score',
                line=dict(color='#4CAF50', width=3),
                fill='tonexty'
            ),
            row=1, col=1
        )

        fig_relationship.add_trace(
            go.Scatter(
                x=dates,
                y=engagement_scores,
                name='Engagement Level',
                line=dict(color='#2196F3', width=3)
            ),
            row=2, col=1
        )

        fig_relationship.update_layout(
            height=400,
            title="Relationship Building Performance",
            showlegend=False
        )

        st.plotly_chart(fig_relationship, use_container_width=True)

        # Relationship quality breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🌟 Top Relationship Factors")
            relationship_factors = {
                'Factor': ['Helpful Guidance', 'Market Knowledge', 'Responsiveness', 'Family Focus', 'No Pressure'],
                'Score': [9.2, 8.9, 8.7, 8.5, 8.8]
            }
            factor_df = pd.DataFrame(relationship_factors)
            st.bar_chart(factor_df.set_index('Factor')['Score'])

        with col2:
            st.markdown("#### 📈 Satisfaction Trends")
            satisfaction_trends = {
                'Month': ['Nov', 'Dec', 'Jan'],
                'Score': [4.6, 4.7, 4.8],
                'Responses': [156, 203, 209]
            }
            trend_df = pd.DataFrame(satisfaction_trends)
            st.line_chart(trend_df.set_index('Month')['Score'])

    def _render_customer_journey_analysis(self):
        """Render customer journey analysis"""
        st.markdown("### 🗺️ Customer Journey Analysis")

        # Journey stage analysis
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Stage Progression Times")
            progression_data = {
                'Stage Transition': [
                    'Contact → Engaged',
                    'Engaged → Interested',
                    'Interested → Ready',
                    'Ready → Consultation'
                ],
                'Avg Days': [1.2, 3.4, 5.8, 2.1],
                'Target Days': [1.5, 4.0, 7.0, 3.0]
            }

            prog_df = pd.DataFrame(progression_data)
            fig_progression = px.bar(
                prog_df,
                x='Stage Transition',
                y=['Avg Days', 'Target Days'],
                title="Stage Progression Performance",
                barmode='group',
                color_discrete_map={'Avg Days': '#4CAF50', 'Target Days': '#FFC107'}
            )
            fig_progression.update_layout(height=300)
            st.plotly_chart(fig_progression, use_container_width=True)

        with col2:
            st.markdown("#### Engagement Quality by Stage")
            engagement_by_stage = {
                'Stage': ['Exploring', 'Interested', 'Ready to Move'],
                'Avg Quality': [7.2, 8.1, 8.9],
                'Count': [95, 67, 48]
            }

            eng_df = pd.DataFrame(engagement_by_stage)
            fig_engagement = px.scatter(
                eng_df,
                x='Stage',
                y='Avg Quality',
                size='Count',
                title="Engagement Quality vs Stage",
                color='Avg Quality',
                color_continuous_scale='Greens'
            )
            fig_engagement.update_layout(height=300)
            st.plotly_chart(fig_engagement, use_container_width=True)

    def _render_rancho_cucamonga_market_insights(self):
        """Render Rancho Cucamonga market specific insights"""
        st.markdown("### 🏘️ Rancho Cucamonga Market Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 📍 Neighborhood Interest")
            neighborhood_data = {
                'Neighborhood': ['Alta Loma', 'Etiwanda', 'Central RC', 'North RC'],
                'Interest Level': [32, 28, 24, 16],
                'Avg Price': [825000, 780000, 720000, 890000]
            }
            neigh_df = pd.DataFrame(neighborhood_data)
            fig_neighborhoods = px.bar(
                neigh_df,
                x='Neighborhood',
                y='Interest Level',
                title="Neighborhood Interest Distribution",
                color='Interest Level',
                color_continuous_scale='Greens'
            )
            fig_neighborhoods.update_layout(height=300)
            st.plotly_chart(fig_neighborhoods, use_container_width=True)

        with col2:
            st.markdown("#### 👨‍👩‍👧‍👦 Family Priorities")
            family_priorities = {
                'Priority': ['Schools', 'Safety', 'Commute', 'Recreation', 'Value'],
                'Importance': [95, 88, 76, 71, 82]
            }
            priority_df = pd.DataFrame(family_priorities)
            st.bar_chart(priority_df.set_index('Priority')['Importance'])

        with col3:
            st.markdown("#### 💰 Price Range Interest")
            price_ranges = {
                'Range': ['$500-700k', '$700-900k', '$900k-1.2M', '$1.2M+'],
                'Inquiries': [45, 67, 32, 15]
            }
            price_df = pd.DataFrame(price_ranges)
            fig_prices = px.pie(
                values=price_df['Inquiries'],
                names=price_df['Range'],
                title="Price Range Distribution"
            )
            fig_prices.update_layout(height=250)
            st.plotly_chart(fig_prices, use_container_width=True)

        # Market trends
        st.markdown("#### 📊 Local Market Trends")
        market_metrics = {
            'Metric': ['Avg Days on Market', 'Price Appreciation (YoY)', 'Inventory Level', 'Buyer Activity'],
            'Current': [28, '6.2%', 'Balanced', 'Active'],
            'Trend': ['↗️ +3 days', '↗️ +1.1%', '→ Stable', '↗️ +15%'],
            'Assessment': ['Healthy', 'Strong', 'Good', 'Positive']
        }
        market_df = pd.DataFrame(market_metrics)
        st.table(market_df)

    def _render_consultation_pipeline(self):
        """Render consultation pipeline tracking"""
        st.markdown("### 📅 Consultation Pipeline")

        # Pipeline stages
        pipeline_data = {
            'Stage': ['Ready to Move', 'Scheduled', 'Completed', 'Follow-up'],
            'Count': [67, 48, 34, 28],
            'Value': ['$45M', '$32M', '$23M', '$19M']
        }

        for i, (stage, count, value) in enumerate(zip(pipeline_data['Stage'], pipeline_data['Count'], pipeline_data['Value'])):
            st.metric(stage, f"{count} clients", value)

        # Consultation success rate
        st.markdown("#### 📈 Consultation Outcomes")
        outcomes = {
            'Outcome': ['Listing Signed', 'Follow-up Scheduled', 'Referral Made', 'Not Ready'],
            'Count': [28, 15, 8, 3],
            'Percentage': [52, 28, 15, 5]
        }

        outcome_df = pd.DataFrame(outcomes)
        fig_outcomes = px.bar(
            outcome_df,
            x='Outcome',
            y='Percentage',
            title="Consultation Success Rate",
            color='Percentage',
            color_continuous_scale='Greens'
        )
        fig_outcomes.update_layout(height=300)
        st.plotly_chart(fig_outcomes, use_container_width=True)

    def _render_customer_feedback_summary(self):
        """Render customer feedback and testimonials"""
        st.markdown("### 💬 Customer Feedback")

        # Recent feedback highlights
        st.markdown("#### ⭐ Recent Testimonials")
        testimonials = [
            "Jorge's team was incredibly helpful and patient with our questions. They made selling our home stress-free!",
            "The market knowledge they provided was invaluable. We felt confident in our decisions.",
            "Professional, friendly, and always available. Highly recommend for anyone in Rancho Cucamonga.",
            "They understood our family's needs and timeline perfectly. Great customer service!"
        ]

        for testimonial in testimonials:
            st.info(f"💭 \"{testimonial}\"")

        # Feedback categories
        st.markdown("#### 📊 Feedback Categories")
        feedback_categories = {
            'Category': ['Communication', 'Market Knowledge', 'Process Guidance', 'Responsiveness'],
            'Positive %': [96, 94, 92, 98],
            'Rating': [4.8, 4.7, 4.6, 4.9]
        }

        feedback_df = pd.DataFrame(feedback_categories)
        fig_feedback = px.bar(
            feedback_df,
            x='Category',
            y='Positive %',
            title="Customer Feedback by Category",
            color='Rating',
            color_continuous_scale='Greens'
        )
        fig_feedback.update_layout(height=300)
        st.plotly_chart(fig_feedback, use_container_width=True)

    def _render_friendly_performance_metrics(self):
        """Render friendly approach specific performance metrics"""
        st.markdown("### 🎯 Friendly Approach Performance")

        # Key friendly metrics
        friendly_metrics = {
            'Metric': [
                'Response Rate',
                'Conversation Completion',
                'Referral Rate',
                'Repeat Business',
                'Customer Satisfaction'
            ],
            'Current': ['94%', '78%', '23%', '31%', '4.8/5.0'],
            'Target': ['90%', '70%', '20%', '25%', '4.5/5.0'],
            'Status': ['✅', '✅', '✅', '✅', '✅']
        }

        metrics_df = pd.DataFrame(friendly_metrics)
        st.table(metrics_df)

        # Comparison with industry benchmarks
        st.markdown("#### 📊 vs Industry Benchmarks")
        comparison = {
            'Metric': ['Customer Satisfaction', 'Response Rate', 'Consultation Rate'],
            'Jorge Friendly': [4.8, 94, 27],
            'Industry Average': [4.2, 68, 18]
        }

        comp_df = pd.DataFrame(comparison)
        fig_comparison = px.bar(
            comp_df,
            x='Metric',
            y=['Jorge Friendly', 'Industry Average'],
            title="Performance vs Industry",
            barmode='group',
            color_discrete_map={'Jorge Friendly': '#4CAF50', 'Industry Average': '#9E9E9E'}
        )
        fig_comparison.update_layout(height=300)
        st.plotly_chart(fig_comparison, use_container_width=True)

    def _render_customer_experience_optimization(self):
        """Render customer experience optimization insights"""
        st.markdown("### 🚀 Customer Experience Optimization")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔍 Optimization Opportunities")

            optimization_data = {
                'Area': ['Response Time', 'Market Insights', 'Family Focus', 'Follow-up Timing'],
                'Current Score': [8.7, 8.9, 8.5, 8.2],
                'Potential Gain': [0.3, 0.1, 0.5, 0.8]
            }

            opt_df = pd.DataFrame(optimization_data)
            fig_optimization = px.scatter(
                opt_df,
                x='Current Score',
                y='Potential Gain',
                size=[abs(x) * 10 + 20 for x in opt_df['Potential Gain']],
                text='Area',
                title="Optimization Opportunity Matrix"
            )
            fig_optimization.update_layout(height=400)
            st.plotly_chart(fig_optimization, use_container_width=True)

        with col2:
            st.markdown("#### 🎯 Action Items")

            action_items = [
                {
                    "Priority": "High",
                    "Action": "Implement 2-hour response guarantee",
                    "Impact": "Customer satisfaction +0.2"
                },
                {
                    "Priority": "Medium",
                    "Action": "Enhance family-focused messaging",
                    "Impact": "Engagement +12%"
                },
                {
                    "Priority": "Medium",
                    "Action": "Add school district insights",
                    "Impact": "Neighborhood interest +15%"
                },
                {
                    "Priority": "Low",
                    "Action": "Expand market trend sharing",
                    "Impact": "Trust score +0.1"
                }
            ]

            for item in action_items:
                color = "🔴" if item["Priority"] == "High" else "🟡" if item["Priority"] == "Medium" else "🟢"
                st.markdown(f"{color} **{item['Priority']}**: {item['Action']}")
                st.markdown(f"   📈 Expected impact: {item['Impact']}")
                st.markdown("---")

        # Summary insights
        st.markdown("#### 💡 Key Insights")
        insights = [
            "🤝 Friendly approach shows 23% higher customer satisfaction than industry average",
            "👨‍👩‍👧‍👦 Family-focused messaging resonates strongly with Rancho Cucamonga demographics",
            "📞 Quick response times are the #1 driver of positive customer experience",
            "🏠 Local market expertise builds trust and drives referral rates",
            "⭐ Customer service excellence leads to 31% repeat business rate"
        ]

        for insight in insights:
            st.info(insight)

    def _load_demo_data(self) -> Dict[str, Any]:
        """Load demo data for dashboard display"""
        return {
            'total_conversations': 209,
            'consultation_ready': 67,
            'consultation_growth': 15,
            'avg_satisfaction': 4.8,
            'response_rate': 94,
            'referral_rate': 23,
            'relationship_score': 8.4,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
        }


def main():
    """Main function to run the friendly dashboard"""
    st.set_page_config(
        page_title="Jorge's Friendly Customer Service Dashboard",
        page_icon="🤝",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for friendly styling
    st.markdown("""
    <style>
    .stMetric > label {
        font-size: 16px !important;
        font-weight: bold !important;
        color: #2E7D32 !important;
    }
    .stMetric > div > div {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #4CAF50 !important;
    }
    .stInfo {
        background-color: #E8F5E8 !important;
        border-left: 4px solid #4CAF50 !important;
    }
    h3 {
        color: #2E7D32 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize and render dashboard
    dashboard = JorgeFriendlyDashboard()
    dashboard.render()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 20px;">
        <p>Jorge's Friendly Customer Service Dashboard - Rancho Cucamonga Edition</p>
        <p>Built with customer satisfaction and relationship excellence in mind 🤝</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()