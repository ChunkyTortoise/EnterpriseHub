"""
Intelligent Nurturing Dashboard Component

Real-time dashboard for AI-powered lead nurturing with personalized sequences,
performance tracking, and adaptive campaign management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import json
from typing import Dict, List, Optional, Any

# Import the nurturing engine
try:
    from ..services.intelligent_nurturing_engine import (
        intelligent_nurturing,
        NurturingStage,
        MessageType
    )
    NURTURING_AVAILABLE = True
except ImportError:
    NURTURING_AVAILABLE = False


def render_intelligent_nurturing_dashboard():
    """Render the intelligent nurturing dashboard with real-time updates"""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    ">
        <h2 style="margin: 0; font-size: 1.8rem;">🤖 Intelligent Nurturing Engine</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">AI-Powered Personalized Lead Nurturing</p>
    </div>
    """, unsafe_allow_html=True)

    if not NURTURING_AVAILABLE:
        st.error("🔧 Intelligent Nurturing Engine not available. Please ensure the service is running.")
        return

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Active Campaigns",
        "📊 Performance Analytics",
        "⚙️ Sequence Management",
        "🔮 AI Insights"
    ])

    with tab1:
        render_active_campaigns_tab()

    with tab2:
        render_performance_analytics_tab()

    with tab3:
        render_sequence_management_tab()

    with tab4:
        render_ai_insights_tab()


def render_active_campaigns_tab():
    """Render active nurturing campaigns overview"""

    col1, col2, col3, col4 = st.columns(4)

    # Mock data - in production, fetch from intelligent_nurturing service
    with col1:
        st.metric(
            "Active Sequences",
            "247",
            delta="12",
            help="Total number of active nurturing sequences"
        )

    with col2:
        st.metric(
            "Avg Conversion Rate",
            "34.2%",
            delta="8.1%",
            help="Average conversion rate across all sequences"
        )

    with col3:
        st.metric(
            "Messages Sent Today",
            "1,456",
            delta="203",
            help="Total nurturing messages sent today"
        )

    with col4:
        st.metric(
            "AI Adaptations",
            "89",
            delta="15",
            help="Real-time sequence adaptations made by AI"
        )

    st.markdown("---")

    # Active campaigns table
    st.subheader("🎯 Top Performing Active Campaigns")

    # Mock campaign data
    campaigns_data = [
        {
            "Lead ID": "LD_4321",
            "Lead Name": "Sarah Johnson",
            "Sequence": "First-Time Buyer Journey",
            "Stage": "Education",
            "Messages Sent": 3,
            "Last Interaction": "2 hours ago",
            "Engagement Score": 87,
            "Next Message": "Tomorrow 10:00 AM",
            "Conversion Probability": "78%"
        },
        {
            "Lead ID": "LD_5678",
            "Lead Name": "Mike Chen",
            "Sequence": "Luxury Property Explorer",
            "Stage": "Consideration",
            "Messages Sent": 5,
            "Last Interaction": "45 minutes ago",
            "Engagement Score": 92,
            "Next Message": "Today 3:00 PM",
            "Conversion Probability": "84%"
        },
        {
            "Lead ID": "LD_9012",
            "Lead Name": "Jennifer Martinez",
            "Sequence": "Investment Opportunity",
            "Stage": "Decision Support",
            "Messages Sent": 7,
            "Last Interaction": "15 minutes ago",
            "Engagement Score": 95,
            "Next Message": "Manual Review",
            "Conversion Probability": "91%"
        }
    ]

    df_campaigns = pd.DataFrame(campaigns_data)

    # Style the dataframe
    def style_conversion_probability(val):
        if val == "Manual Review":
            return "background-color: #ffeaa7; color: #2d3436"
        prob = float(val.strip('%'))
        if prob >= 80:
            return "background-color: #00b894; color: white"
        elif prob >= 60:
            return "background-color: #fdcb6e; color: #2d3436"
        else:
            return "background-color: #e17055; color: white"

    styled_df = df_campaigns.style.applymap(
        style_conversion_probability,
        subset=['Conversion Probability']
    )

    st.dataframe(styled_df, use_container_width=True)

    # Quick actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Create New Sequence", use_container_width=True):
            st.session_state.show_create_sequence = True

    with col2:
        if st.button("⚡ Run AI Optimization", use_container_width=True):
            with st.spinner("Running AI optimization..."):
                # Simulate optimization
                import time
                time.sleep(2)
                st.success("✅ AI optimization complete! 12 sequences improved.")

    with col3:
        if st.button("📊 Export Performance Report", use_container_width=True):
            st.download_button(
                "📥 Download Report",
                data=json.dumps(campaigns_data, indent=2),
                file_name=f"nurturing_performance_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def render_performance_analytics_tab():
    """Render performance analytics and metrics"""

    st.subheader("📈 Performance Analytics")

    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        ["Last 7 days", "Last 30 days", "Last 90 days", "Last year"],
        index=1
    )

    col1, col2 = st.columns(2)

    with col1:
        # Conversion rate trend
        dates = pd.date_range(start='2026-01-02', end='2026-01-09', freq='D')
        conversion_rates = [28.5, 31.2, 29.8, 33.1, 35.4, 34.2, 36.8, 34.2]

        fig_conversion = go.Figure()
        fig_conversion.add_trace(go.Scatter(
            x=dates,
            y=conversion_rates,
            mode='lines+markers',
            name='Conversion Rate',
            line=dict(color='#00b894', width=3),
            marker=dict(size=8)
        ))

        fig_conversion.update_layout(
            title="🎯 Conversion Rate Trend",
            xaxis_title="Date",
            yaxis_title="Conversion Rate (%)",
            height=300,
            showlegend=False
        )

        st.plotly_chart(fig_conversion, use_container_width=True)

    with col2:
        # Message engagement by type
        message_types = ['Email', 'SMS', 'Voice Drop', 'Social Media']
        engagement_rates = [45.2, 78.9, 62.3, 34.7]

        fig_engagement = px.bar(
            x=message_types,
            y=engagement_rates,
            title="💬 Engagement Rate by Message Type",
            color=engagement_rates,
            color_continuous_scale='viridis'
        )

        fig_engagement.update_layout(
            height=300,
            showlegend=False,
            yaxis_title="Engagement Rate (%)"
        )

        st.plotly_chart(fig_engagement, use_container_width=True)

    # Sequence performance breakdown
    st.subheader("🔍 Sequence Performance Breakdown")

    sequence_performance = [
        {"Sequence Type": "First-Time Buyer", "Active": 89, "Conversion Rate": "32.1%", "Avg Messages": 4.2, "Revenue Impact": "$425K"},
        {"Sequence Type": "Luxury Explorer", "Active": 34, "Conversion Rate": "28.7%", "Avg Messages": 6.1, "Revenue Impact": "$780K"},
        {"Sequence Type": "Investment Focus", "Active": 52, "Conversion Rate": "41.3%", "Avg Messages": 5.8, "Revenue Impact": "$1.2M"},
        {"Sequence Type": "Relocation", "Active": 67, "Conversion Rate": "35.9%", "Avg Messages": 3.9, "Revenue Impact": "$380K"},
        {"Sequence Type": "Downsizing", "Active": 23, "Conversion Rate": "29.4%", "Avg Messages": 4.7, "Revenue Impact": "$190K"}
    ]

    df_performance = pd.DataFrame(sequence_performance)

    # Create metrics visualization
    col1, col2, col3 = st.columns(3)

    with col1:
        fig_active = px.pie(
            df_performance,
            values='Active',
            names='Sequence Type',
            title="Active Sequences Distribution"
        )
        fig_active.update_layout(height=300)
        st.plotly_chart(fig_active, use_container_width=True)

    with col2:
        # Convert conversion rate to numeric
        df_performance['Conversion Rate Numeric'] = df_performance['Conversion Rate'].str.rstrip('%').astype(float)

        fig_conversion = px.bar(
            df_performance,
            x='Sequence Type',
            y='Conversion Rate Numeric',
            title="Conversion Rate by Sequence",
            color='Conversion Rate Numeric',
            color_continuous_scale='RdYlGn'
        )
        fig_conversion.update_layout(height=300, xaxis_tickangle=45)
        st.plotly_chart(fig_conversion, use_container_width=True)

    with col3:
        # Revenue impact
        df_performance['Revenue Numeric'] = df_performance['Revenue Impact'].str.replace('$', '').str.replace('K', '000').str.replace('M', '000000').astype(float)

        fig_revenue = px.treemap(
            df_performance,
            path=['Sequence Type'],
            values='Revenue Numeric',
            title="Revenue Impact Breakdown"
        )
        fig_revenue.update_layout(height=300)
        st.plotly_chart(fig_revenue, use_container_width=True)

    # Performance insights
    st.markdown("---")
    st.subheader("🧠 AI Performance Insights")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        st.info("""
        **🎯 Top Insight**: Investment-focused sequences have the highest conversion rate (41.3%)
        but represent only 20% of active campaigns. Consider creating more investment-targeted content.
        """)

        st.success("""
        **⚡ Optimization Opportunity**: SMS messages show 78.9% engagement rate vs 45.2% for email.
        AI recommends increasing SMS usage in high-priority sequences.
        """)

    with insights_col2:
        st.warning("""
        **📱 Mobile Trend**: 67% of message opens occur on mobile devices.
        Ensure all nurturing content is mobile-optimized.
        """)

        st.info("""
        **🕐 Timing Insight**: Messages sent between 10-11 AM show 23% higher engagement.
        AI is auto-optimizing send times for maximum impact.
        """)


def render_sequence_management_tab():
    """Render sequence creation and management interface"""

    st.subheader("⚙️ Sequence Management")

    # Sequence template library
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 📚 Sequence Template Library")

        templates = [
            {
                "name": "First-Time Buyer Journey",
                "messages": 5,
                "avg_conversion": "32.1%",
                "best_for": "First-time homebuyers",
                "status": "Active"
            },
            {
                "name": "Luxury Property Explorer",
                "messages": 7,
                "avg_conversion": "28.7%",
                "best_for": "High-end property seekers",
                "status": "Active"
            },
            {
                "name": "Investment Opportunity Hunter",
                "messages": 6,
                "avg_conversion": "41.3%",
                "best_for": "Real estate investors",
                "status": "Active"
            },
            {
                "name": "Quick Sale Accelerator",
                "messages": 4,
                "avg_conversion": "25.8%",
                "best_for": "Urgent timeline buyers",
                "status": "Testing"
            }
        ]

        for i, template in enumerate(templates):
            with st.expander(f"🎯 {template['name']} - {template['avg_conversion']} conversion"):
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.write(f"**Messages:** {template['messages']}")
                    st.write(f"**Best for:** {template['best_for']}")

                with col_b:
                    st.write(f"**Status:** {template['status']}")
                    st.write(f"**Conversion:** {template['avg_conversion']}")

                with col_c:
                    if st.button(f"Use Template", key=f"use_template_{i}"):
                        st.success(f"✅ Template '{template['name']}' loaded for customization!")
                    if st.button(f"View Details", key=f"view_template_{i}"):
                        st.info(f"📋 Detailed view for '{template['name']}' would open here.")

    with col2:
        st.markdown("#### 🚀 Quick Actions")

        if st.button("➕ Create New Sequence", use_container_width=True):
            st.session_state.creating_sequence = True

        if st.button("🤖 AI Generate Sequence", use_container_width=True):
            with st.spinner("AI generating personalized sequence..."):
                import time
                time.sleep(3)
                st.success("✅ AI generated 'Tech Professional Relocation' sequence with 6 messages!")

        if st.button("📊 Sequence Analytics", use_container_width=True):
            st.info("📈 Advanced sequence analytics panel would open here.")

        if st.button("⚙️ A/B Testing", use_container_width=True):
            st.info("🧪 A/B testing configuration panel would open here.")

    # Sequence creator
    if st.session_state.get('creating_sequence', False):
        st.markdown("---")
        st.subheader("✨ Create New Nurturing Sequence")

        with st.form("sequence_creator"):
            col1, col2 = st.columns(2)

            with col1:
                sequence_name = st.text_input("Sequence Name", placeholder="e.g., Tech Professional Relocation")
                target_audience = st.selectbox(
                    "Target Audience",
                    ["First-time buyers", "Luxury seekers", "Investors", "Relocating professionals", "Downsizers", "Custom"]
                )
                urgency_level = st.selectbox("Urgency Level", ["Low", "Medium", "High", "Critical"])

            with col2:
                budget_range = st.selectbox(
                    "Budget Range",
                    ["Under $300K", "$300K-$500K", "$500K-$800K", "$800K-$1.2M", "Above $1.2M"]
                )
                property_type = st.selectbox(
                    "Property Type",
                    ["Single Family", "Condo", "Townhouse", "Multi-family", "Commercial", "Land"]
                )
                sequence_length = st.slider("Number of Messages", 3, 10, 5)

            sequence_description = st.text_area(
                "Sequence Description",
                placeholder="Describe the goals and strategy for this nurturing sequence..."
            )

            submitted = st.form_submit_button("🚀 Create AI-Powered Sequence")

            if submitted:
                with st.spinner("AI creating personalized sequence..."):
                    import time
                    time.sleep(2)

                st.success(f"✅ Created '{sequence_name}' with {sequence_length} AI-personalized messages!")
                st.session_state.creating_sequence = False
                st.rerun()


def render_ai_insights_tab():
    """Render AI insights and recommendations"""

    st.subheader("🔮 AI Insights & Recommendations")

    # AI performance summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        ">
            <h3 style="margin: 0;">🎯 AI Accuracy</h3>
            <h2 style="margin: 0.5rem 0;">94.2%</h2>
            <p style="margin: 0; opacity: 0.9;">Conversion Prediction</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fd79a8, #e84393);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        ">
            <h3 style="margin: 0;">⚡ Adaptations</h3>
            <h2 style="margin: 0.5rem 0;">1,247</h2>
            <p style="margin: 0; opacity: 0.9;">This Month</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #55a3ff, #2e86de);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        ">
            <h3 style="margin: 0;">💡 Insights</h3>
            <h2 style="margin: 0.5rem 0;">23</h2>
            <p style="margin: 0; opacity: 0.9;">New This Week</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Top AI recommendations
    st.subheader("🚀 Top AI Recommendations")

    recommendations = [
        {
            "priority": "🔴 High",
            "insight": "Investment sequences show 41% conversion vs 29% average",
            "recommendation": "Increase investment-focused content creation by 40%",
            "impact": "+$180K annual revenue",
            "effort": "Medium"
        },
        {
            "priority": "🟡 Medium",
            "insight": "SMS engagement 75% higher than email in luxury segment",
            "recommendation": "Shift luxury sequences to SMS-primary communication",
            "impact": "+23% engagement",
            "effort": "Low"
        },
        {
            "priority": "🟢 Low",
            "insight": "Morning send times (10-11 AM) show best engagement",
            "recommendation": "Auto-optimize all sequences for morning delivery",
            "impact": "+15% open rates",
            "effort": "Automated"
        }
    ]

    for i, rec in enumerate(recommendations):
        with st.expander(f"{rec['priority']} - {rec['insight']}", expanded=(i == 0)):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**💡 Insight:** {rec['insight']}")
                st.write(f"**🎯 Recommendation:** {rec['recommendation']}")
                st.write(f"**📈 Expected Impact:** {rec['impact']}")
                st.write(f"**🔧 Implementation Effort:** {rec['effort']}")

            with col2:
                if st.button(f"Implement", key=f"implement_{i}"):
                    st.success("✅ Implementation queued!")
                if st.button(f"Learn More", key=f"learn_{i}"):
                    st.info("📚 Detailed analysis would be shown here.")

    # AI learning and adaptation
    st.markdown("---")
    st.subheader("🧠 AI Learning & Adaptation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Learning Progress")

        # Mock learning progress data
        learning_areas = ["Message Timing", "Content Personalization", "Channel Selection", "Frequency Optimization", "Behavioral Triggers"]
        progress_scores = [92, 87, 94, 78, 85]

        fig_learning = go.Figure()

        fig_learning.add_trace(go.Scatterpolar(
            r=progress_scores,
            theta=learning_areas,
            fill='toself',
            name='AI Learning Progress'
        ))

        fig_learning.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            height=300
        )

        st.plotly_chart(fig_learning, use_container_width=True)

    with col2:
        st.markdown("#### 🎯 Recent AI Adaptations")

        adaptations = [
            "✨ Adjusted send timing for 'Tech Professional' segment to 9 AM based on engagement data",
            "🎯 Increased property detail focus for 'Investment' sequences after click analysis",
            "📱 Switched luxury leads to SMS-first after 78% mobile engagement spike",
            "⏰ Reduced message frequency for 'Downsizing' segment based on preference feedback",
            "💼 Added market insight content to high-value sequences for 15% better conversion"
        ]

        for adaptation in adaptations:
            st.write(f"• {adaptation}")

    # AI configuration
    st.markdown("---")
    st.subheader("⚙️ AI Configuration")

    with st.expander("🔧 Advanced AI Settings"):
        col1, col2 = st.columns(2)

        with col1:
            ai_aggressiveness = st.slider(
                "AI Adaptation Aggressiveness",
                min_value=1, max_value=10, value=7,
                help="How quickly AI adapts sequences based on new data"
            )

            personalization_depth = st.slider(
                "Personalization Depth",
                min_value=1, max_value=10, value=8,
                help="How deeply AI personalizes content for each lead"
            )

        with col2:
            learning_rate = st.slider(
                "Learning Rate",
                min_value=1, max_value=10, value=6,
                help="How quickly AI incorporates new patterns"
            )

            risk_tolerance = st.slider(
                "Risk Tolerance",
                min_value=1, max_value=10, value=5,
                help="AI willingness to try experimental approaches"
            )

        if st.button("💾 Save AI Configuration"):
            st.success("✅ AI configuration saved! Changes will take effect within 24 hours.")


# Cache functions for better performance
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_nurturing_performance_data():
    """Get cached nurturing performance data"""
    # In production, this would fetch real data from the nurturing engine
    return {
        'active_sequences': 247,
        'conversion_rate': 34.2,
        'messages_today': 1456,
        'ai_adaptations': 89
    }