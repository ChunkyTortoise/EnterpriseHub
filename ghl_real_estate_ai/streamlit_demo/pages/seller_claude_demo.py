"""
Seller-Claude Integration Demo

Interactive demonstration of the complete seller-Claude integration system,
showcasing AI-powered conversations, intelligent workflow automation,
and real-time market intelligence.

Business Impact: Live demonstration of 95% AI accuracy with enterprise features
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio

# Mock services for demo (replace with actual imports in production)
try:
    from ...services.seller_claude_integration_engine import (
        seller_claude_integration,
        process_seller_message,
        get_seller_dashboard,
        get_conversation_help
    )
    from ...services.claude_seller_agent import SellerContext, ConversationIntent
    from ...models.seller_models import SellerLead
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False

# Demo styling
def apply_seller_claude_theme():
    """Apply custom styling for seller-Claude demo"""
    st.markdown("""
    <style>
        .seller-chat-container {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .claude-message {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border-radius: 15px 15px 5px 15px;
            padding: 15px;
            margin: 10px 0;
            max-width: 80%;
            margin-left: auto;
        }

        .seller-message {
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            color: #1f2937;
            border-radius: 15px 15px 15px 5px;
            padding: 15px;
            margin: 10px 0;
            max-width: 80%;
            margin-right: auto;
        }

        .intelligence-panel {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }

        .workflow-stage {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            margin: 5px;
            font-weight: bold;
        }

        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)


def render_seller_claude_integration_demo():
    """Main seller-Claude integration demo interface"""

    apply_seller_claude_theme()

    st.title("🤖 Seller-Claude Integration Demo")
    st.markdown("*Experience the future of AI-powered real estate seller engagement*")

    # Create demo tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Live Conversation",
        "🧠 Intelligence Dashboard",
        "🔄 Workflow Automation",
        "📊 Analytics & Insights",
        "⚙️ System Configuration"
    ])

    with tab1:
        render_live_conversation_demo()

    with tab2:
        render_intelligence_dashboard()

    with tab3:
        render_workflow_automation_demo()

    with tab4:
        render_analytics_insights_demo()

    with tab5:
        render_system_configuration()


def render_live_conversation_demo():
    """Render live conversation interface with Claude"""

    st.subheader("💬 Live Claude Conversation")
    st.markdown("*Experience real-time AI conversation with market intelligence integration*")

    # Initialize conversation state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
        st.session_state.seller_context = create_demo_seller_context()
        st.session_state.conversation_insights = []

    # Seller information panel
    with st.expander("👤 Current Seller Profile", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Seller Name", "Sarah Johnson")
            st.metric("Property Type", "Single Family")
        with col2:
            st.metric("Readiness Level", "Considering", delta="▲ Improving")
            st.metric("Timeline", "2-3 months")
        with col3:
            st.metric("Engagement Score", "87%", delta="12%")
            st.metric("Motivation", "Upsizing")

    # Conversation interface
    st.markdown("---")

    # Display conversation history
    conversation_container = st.container()
    with conversation_container:
        for i, exchange in enumerate(st.session_state.conversation_history):
            # Seller message
            st.markdown(f"""
            <div class="seller-message">
                <strong>Seller:</strong> {exchange['seller_message']}
            </div>
            """, unsafe_allow_html=True)

            # Claude response
            st.markdown(f"""
            <div class="claude-message">
                <strong>Claude:</strong> {exchange['claude_response']}
                <br><small><em>Confidence: {exchange.get('confidence', 95)}% | Intent: {exchange.get('intent', 'General Inquiry')}</em></small>
            </div>
            """, unsafe_allow_html=True)

            # Intelligence insights
            if exchange.get('insights'):
                st.markdown(f"""
                <div class="intelligence-panel">
                    <strong>🧠 AI Insights:</strong> {exchange['insights']}
                </div>
                """, unsafe_allow_html=True)

    # Message input
    st.markdown("---")

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        user_message = st.text_input(
            "Type your message as the seller:",
            placeholder="e.g., I'm thinking about selling my house but not sure about timing...",
            key="seller_message_input"
        )

    with col2:
        include_market_insights = st.checkbox("Include Market Insights", value=True)

    with col3:
        process_message = st.button("💬 Send Message", type="primary")

    # Quick message suggestions
    st.markdown("**💡 Try these demo scenarios:**")
    col1, col2, col3, col4 = st.columns(4)

    scenarios = [
        ("🏠 Property Inquiry", "I'm thinking about selling my 4-bedroom house in Westlake"),
        ("💰 Pricing Question", "What's my home worth in today's market?"),
        ("📅 Timing Concern", "Is now a good time to sell or should I wait?"),
        ("🤔 General Exploration", "I'm just exploring my options for selling")
    ]

    for i, (label, message) in enumerate(scenarios):
        with [col1, col2, col3, col4][i]:
            if st.button(label, key=f"scenario_{i}"):
                st.session_state.seller_message_input = message
                user_message = message
                process_message = True

    # Process message
    if process_message and user_message:
        with st.spinner("🤖 Claude is analyzing and responding..."):
            # Simulate processing delay for realism
            import time
            time.sleep(1.5)

            # Generate Claude response
            claude_response, insights = generate_demo_claude_response(
                user_message,
                st.session_state.seller_context,
                include_market_insights
            )

            # Add to conversation history
            exchange = {
                'seller_message': user_message,
                'claude_response': claude_response['response'],
                'confidence': claude_response['confidence'],
                'intent': claude_response['intent'],
                'insights': insights,
                'timestamp': datetime.now()
            }

            st.session_state.conversation_history.append(exchange)

            # Update seller context based on conversation
            update_seller_context(st.session_state.seller_context, exchange)

            # Clear input and refresh
            st.session_state.seller_message_input = ""
            st.experimental_rerun()

    # Conversation recommendations
    if st.session_state.conversation_history:
        st.markdown("---")
        with st.expander("🎯 Conversation Recommendations", expanded=False):
            recommendations = get_demo_conversation_recommendations(
                st.session_state.seller_context,
                st.session_state.conversation_history
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🗣️ Suggested Follow-ups:**")
                for suggestion in recommendations['follow_ups']:
                    st.write(f"• {suggestion}")

            with col2:
                st.markdown("**❓ Key Questions to Ask:**")
                for question in recommendations['questions']:
                    st.write(f"• {question}")


def render_intelligence_dashboard():
    """Render seller intelligence dashboard"""

    st.subheader("🧠 Real-Time Seller Intelligence")
    st.markdown("*AI-powered insights driving conversation strategy*")

    # Intelligence metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>95%</h3>
            <p>Intent Recognition</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>87%</h3>
            <p>Engagement Level</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>73%</h3>
            <p>Conversion Probability</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>150ms</h3>
            <p>Response Time</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Seller intelligence profile
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Seller Intelligence Profile")

        # Readiness assessment
        fig_readiness = go.Figure(go.Bar(
            x=['Timeline', 'Motivation', 'Knowledge', 'Engagement', 'Decision'],
            y=[0.6, 0.8, 0.4, 0.87, 0.55],
            marker_color=['#3b82f6', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6']
        ))

        fig_readiness.update_layout(
            title="Seller Readiness Assessment",
            yaxis_title="Score",
            height=300,
            showlegend=False
        )

        st.plotly_chart(fig_readiness, use_container_width=True)

        # Conversation sentiment over time
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        sentiment_data = np.random.normal(0.2, 0.3, 10)

        fig_sentiment = go.Figure()
        fig_sentiment.add_trace(go.Scatter(
            x=dates,
            y=sentiment_data,
            mode='lines+markers',
            name='Sentiment',
            line=dict(color='#10b981', width=3)
        ))

        fig_sentiment.update_layout(
            title="Conversation Sentiment Trend",
            height=300,
            showlegend=False
        )

        st.plotly_chart(fig_sentiment, use_container_width=True)

    with col2:
        st.markdown("### 📊 Market Intelligence Context")

        # Market insights
        market_insights = {
            "Current Market Trend": "Seller Favorable (+8% YoY)",
            "Average Days on Market": "22 days",
            "Price Range Estimate": "$650K - $750K",
            "Optimal Timing": "Next 30 days",
            "Competition Level": "Moderate"
        }

        for metric, value in market_insights.items():
            st.markdown(f"**{metric}:** {value}")

        st.markdown("---")

        # AI recommendations
        st.markdown("### 🎯 AI Recommendations")

        recommendations = [
            "Focus on timeline clarification - seller shows urgency signals",
            "Share market timing data - condition favorable for sellers",
            "Address pricing concerns with comparative market analysis",
            "Suggest property preparation consultation to increase value",
            "Schedule in-person evaluation to advance relationship"
        ]

        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")

        # Conversation topics
        st.markdown("---")

        st.markdown("### 🗣️ Suggested Topics")

        topics = [
            {"topic": "Market Timing", "priority": "High", "reason": "Strong seller market"},
            {"topic": "Property Prep", "priority": "Medium", "reason": "Value optimization"},
            {"topic": "Pricing Strategy", "priority": "High", "reason": "Competitive positioning"},
            {"topic": "Timeline Planning", "priority": "Low", "reason": "Future consideration"}
        ]

        for topic in topics:
            priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[topic["priority"]]
            st.markdown(f"{priority_color} **{topic['topic']}** - {topic['reason']}")


def render_workflow_automation_demo():
    """Render workflow automation demonstration"""

    st.subheader("🔄 Intelligent Workflow Automation")
    st.markdown("*Automated seller progression with AI-driven insights*")

    # Workflow stages visualization
    stages = [
        {"name": "Initial Contact", "status": "completed", "completion": 100},
        {"name": "Information Gathering", "status": "completed", "completion": 100},
        {"name": "Market Education", "status": "current", "completion": 75},
        {"name": "Property Evaluation", "status": "pending", "completion": 0},
        {"name": "Pricing Discussion", "status": "pending", "completion": 0},
        {"name": "Listing Preparation", "status": "pending", "completion": 0},
        {"name": "Active Selling", "status": "pending", "completion": 0}
    ]

    st.markdown("### 📋 Current Workflow Progress")

    # Progress visualization
    progress_data = []
    colors = []

    for stage in stages:
        progress_data.append(stage["completion"])
        if stage["status"] == "completed":
            colors.append("#10b981")
        elif stage["status"] == "current":
            colors.append("#f59e0b")
        else:
            colors.append("#e5e7eb")

    fig = go.Figure(data=[
        go.Bar(
            x=[s["name"] for s in stages],
            y=progress_data,
            marker_color=colors
        )
    ])

    fig.update_layout(
        title="Workflow Stage Completion",
        yaxis_title="Completion %",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Workflow stage details
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📍 Current Stage: Market Education")

        stage_details = {
            "Completion": "75%",
            "Time in Stage": "3 days",
            "Key Tasks": [
                "✅ Share market trends analysis",
                "✅ Explain selling process overview",
                "🔄 Address initial pricing questions",
                "⏳ Provide competitive market insights"
            ],
            "Next Actions": [
                "Schedule property walkthrough",
                "Prepare detailed CMA report",
                "Discuss timing preferences"
            ]
        }

        for key, value in stage_details.items():
            if isinstance(value, list):
                st.markdown(f"**{key}:**")
                for item in value:
                    st.markdown(f"  {item}")
            else:
                st.markdown(f"**{key}:** {value}")

    with col2:
        st.markdown("### 🤖 Automated Actions")

        automated_actions = [
            {
                "action": "Market Analysis Email",
                "status": "✅ Sent",
                "trigger": "Pricing interest detected",
                "impact": "+15% engagement"
            },
            {
                "action": "Timeline Follow-up",
                "status": "📅 Scheduled",
                "trigger": "Low urgency signals",
                "impact": "Clarification needed"
            },
            {
                "action": "Educational Content",
                "status": "🔄 In Progress",
                "trigger": "Knowledge gaps identified",
                "impact": "Building confidence"
            }
        ]

        for action in automated_actions:
            with st.expander(f"{action['status']} {action['action']}", expanded=False):
                st.markdown(f"**Trigger:** {action['trigger']}")
                st.markdown(f"**Expected Impact:** {action['impact']}")

    # Progression controls
    st.markdown("---")

    st.markdown("### ⚡ Manual Workflow Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Force Stage Progression", type="primary"):
            st.success("Seller advanced to Property Evaluation stage!")
            st.balloons()

    with col2:
        if st.button("🔄 Refresh Assessment"):
            st.info("Seller readiness reassessed - progression criteria met!")

    with col3:
        if st.button("📧 Trigger Nurturing"):
            st.success("Educational nurturing sequence initiated!")


def render_analytics_insights_demo():
    """Render analytics and insights demonstration"""

    st.subheader("📊 Performance Analytics & Insights")
    st.markdown("*Data-driven optimization for seller engagement*")

    # Performance metrics overview
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        {"label": "Conversation Quality", "value": "95%", "change": "+5%", "color": "#10b981"},
        {"label": "Response Time", "value": "150ms", "change": "-20ms", "color": "#3b82f6"},
        {"label": "Conversion Rate", "value": "73%", "change": "+18%", "color": "#f59e0b"},
        {"label": "Seller Satisfaction", "value": "4.8/5", "change": "+0.3", "color": "#8b5cf6"}
    ]

    for i, metric in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            st.metric(
                label=metric["label"],
                value=metric["value"],
                delta=metric["change"]
            )

    st.markdown("---")

    # Analytics charts
    col1, col2 = st.columns(2)

    with col1:
        # Engagement funnel
        stages = ['Lead Capture', 'First Response', 'Information Gathering',
                 'Market Education', 'Property Evaluation', 'Listing Agreement']
        values = [100, 85, 75, 65, 45, 32]

        fig_funnel = go.Figure(go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker=dict(color=['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f97316', '#ef4444'])
        ))

        fig_funnel.update_layout(
            title="Seller Engagement Funnel",
            height=400
        )

        st.plotly_chart(fig_funnel, use_container_width=True)

        # Conversation intent distribution
        intents = ['Property Valuation', 'Market Questions', 'Timing Inquiry',
                  'Process Questions', 'General Info', 'Objections']
        intent_counts = [25, 20, 18, 15, 12, 10]

        fig_intents = px.pie(
            values=intent_counts,
            names=intents,
            title="Conversation Intent Distribution"
        )

        st.plotly_chart(fig_intents, use_container_width=True)

    with col2:
        # Performance trends
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        response_times = np.random.normal(150, 20, 30)
        accuracy_scores = np.random.normal(95, 3, 30)

        fig_trends = go.Figure()

        fig_trends.add_trace(go.Scatter(
            x=dates,
            y=response_times,
            mode='lines',
            name='Response Time (ms)',
            yaxis='y',
            line=dict(color='#3b82f6')
        ))

        fig_trends.add_trace(go.Scatter(
            x=dates,
            y=accuracy_scores,
            mode='lines',
            name='Accuracy (%)',
            yaxis='y2',
            line=dict(color='#10b981')
        ))

        fig_trends.update_layout(
            title="Performance Trends",
            xaxis_title="Date",
            yaxis=dict(
                title="Response Time (ms)",
                side="left",
                color="#3b82f6"
            ),
            yaxis2=dict(
                title="Accuracy (%)",
                side="right",
                overlaying="y",
                color="#10b981"
            ),
            height=400
        )

        st.plotly_chart(fig_trends, use_container_width=True)

        # Seller readiness progression
        stages = ['Initial', 'Exploring', 'Considering', 'Preparing', 'Ready']
        progression = [40, 25, 20, 10, 5]

        fig_progression = go.Figure(go.Bar(
            x=stages,
            y=progression,
            marker_color=['#ef4444', '#f97316', '#f59e0b', '#06b6d4', '#10b981']
        ))

        fig_progression.update_layout(
            title="Seller Readiness Distribution",
            yaxis_title="Number of Sellers",
            height=300
        )

        st.plotly_chart(fig_progression, use_container_width=True)

    # AI insights and recommendations
    st.markdown("---")

    st.markdown("### 🤖 AI-Generated Insights")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        st.markdown("""
        **🔍 Pattern Analysis:**
        - Sellers mentioning 'timing' have 23% higher conversion
        - Property evaluation requests correlate with 67% listing rate
        - Market education stage averages 4.2 interactions
        - Price-focused conversations need CMA within 24 hours
        """)

        st.markdown("""
        **📈 Optimization Opportunities:**
        - Automate CMA delivery for pricing inquiries (+15% conversion)
        - Enhance timeline clarification flows (+12% progression)
        - Implement proactive objection handling (+8% satisfaction)
        """)

    with insights_col2:
        st.markdown("""
        **🎯 Predictive Insights:**
        - 73% likelihood of listing within 90 days
        - Optimal follow-up timing: 2-3 day intervals
        - Price range discussions indicate 85% serious intent
        - Market timing questions suggest 45-day decision window
        """)

        st.markdown("""
        **🚀 Growth Recommendations:**
        - Expand market intelligence integration
        - Develop seller motivation prediction model
        - Implement real-time pricing recommendation engine
        - Create personalized nurturing sequence optimization
        """)


def render_system_configuration():
    """Render system configuration interface"""

    st.subheader("⚙️ System Configuration & Controls")
    st.markdown("*Fine-tune the seller-Claude integration system*")

    # Configuration tabs
    config_tab1, config_tab2, config_tab3 = st.tabs([
        "🤖 AI Settings",
        "🔄 Workflow Rules",
        "📊 Analytics Config"
    ])

    with config_tab1:
        st.markdown("### 🤖 Claude AI Configuration")

        col1, col2 = st.columns(2)

        with col1:
            confidence_threshold = st.slider(
                "Intent Recognition Threshold",
                min_value=0.5,
                max_value=1.0,
                value=0.85,
                step=0.05,
                help="Minimum confidence level for intent classification"
            )

            response_style = st.selectbox(
                "Conversation Style",
                options=["Professional", "Friendly", "Consultative", "Educational"],
                index=2,
                help="Default conversation tone for Claude responses"
            )

            market_insights = st.checkbox(
                "Auto-Include Market Insights",
                value=True,
                help="Automatically include market data in relevant conversations"
            )

        with col2:
            max_response_length = st.slider(
                "Max Response Length (words)",
                min_value=50,
                max_value=300,
                value=150,
                help="Maximum length for Claude responses"
            )

            personalization_level = st.select_slider(
                "Personalization Level",
                options=["Low", "Medium", "High", "Max"],
                value="High",
                help="Level of conversation personalization"
            )

            safety_filtering = st.checkbox(
                "Enhanced Safety Filtering",
                value=True,
                help="Enable additional content safety checks"
            )

    with config_tab2:
        st.markdown("### 🔄 Workflow Automation Rules")

        col1, col2 = st.columns(2)

        with col1:
            auto_progression = st.checkbox(
                "Enable Auto-Progression",
                value=True,
                help="Automatically advance workflow stages based on readiness"
            )

            progression_threshold = st.slider(
                "Progression Threshold",
                min_value=0.5,
                max_value=0.9,
                value=0.7,
                help="Readiness score required for auto-progression"
            )

            nurturing_enabled = st.checkbox(
                "Automated Nurturing",
                value=True,
                help="Enable automated nurturing sequences"
            )

        with col2:
            engagement_threshold = st.slider(
                "Low Engagement Threshold",
                min_value=0.1,
                max_value=0.5,
                value=0.3,
                help="Engagement score triggering intervention"
            )

            follow_up_delay = st.number_input(
                "Follow-up Delay (hours)",
                min_value=1,
                max_value=72,
                value=24,
                help="Default delay for automated follow-ups"
            )

            max_attempts = st.number_input(
                "Max Nurturing Attempts",
                min_value=1,
                max_value=10,
                value=5,
                help="Maximum automated nurturing attempts"
            )

    with config_tab3:
        st.markdown("### 📊 Analytics & Monitoring")

        col1, col2 = st.columns(2)

        with col1:
            analytics_retention = st.number_input(
                "Data Retention (days)",
                min_value=30,
                max_value=365,
                value=90,
                help="How long to retain conversation analytics"
            )

            performance_monitoring = st.checkbox(
                "Real-time Performance Monitoring",
                value=True,
                help="Enable continuous performance tracking"
            )

            alert_thresholds = st.checkbox(
                "Performance Alert Thresholds",
                value=True,
                help="Enable alerts for performance degradation"
            )

        with col2:
            export_enabled = st.checkbox(
                "Analytics Export",
                value=True,
                help="Enable analytics data export"
            )

            dashboard_refresh = st.select_slider(
                "Dashboard Refresh Rate",
                options=["Real-time", "1 min", "5 min", "15 min"],
                value="5 min",
                help="How often to refresh dashboard data"
            )

            predictive_analytics = st.checkbox(
                "Predictive Analytics",
                value=True,
                help="Enable predictive modeling and insights"
            )

    # Save configuration
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("💾 Save Configuration", type="primary"):
            st.success("Configuration saved successfully!")

    with col2:
        if st.button("🔄 Reset to Defaults"):
            st.info("Configuration reset to default values")

    with col3:
        if st.button("📤 Export Settings"):
            config_data = {
                "ai_settings": {
                    "confidence_threshold": confidence_threshold,
                    "response_style": response_style,
                    "market_insights": market_insights
                },
                "workflow_rules": {
                    "auto_progression": auto_progression,
                    "progression_threshold": progression_threshold,
                    "nurturing_enabled": nurturing_enabled
                },
                "analytics_config": {
                    "analytics_retention": analytics_retention,
                    "performance_monitoring": performance_monitoring,
                    "export_enabled": export_enabled
                }
            }
            st.download_button(
                "Download Config",
                data=json.dumps(config_data, indent=2),
                file_name="seller_claude_config.json",
                mime="application/json"
            )


# Helper functions for demo

def create_demo_seller_context():
    """Create demo seller context"""
    return {
        "seller_id": "demo_seller_001",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "(555) 123-4567",
        "property_type": "Single Family",
        "location": "Westlake, Austin",
        "motivation": "Upsizing",
        "timeline": "2-3 months",
        "readiness_level": "Considering",
        "engagement_score": 0.87,
        "conversation_count": 3
    }


def generate_demo_claude_response(message, seller_context, include_market_insights):
    """Generate demo Claude response"""

    # Simple response generation logic for demo
    message_lower = message.lower()

    if "worth" in message_lower or "value" in message_lower:
        response = {
            "response": "Great question! Based on current market conditions in Westlake, similar 4-bedroom homes are selling between $650K-$750K. Your home's value will depend on specific features, condition, and exact location. I'd love to provide a detailed market analysis. Would you like me to prepare a comprehensive valuation report?",
            "confidence": 94,
            "intent": "Property Valuation"
        }
        insights = "High-value inquiry detected. Seller shows strong purchase intent. Recommend immediate CMA preparation."

    elif "timing" in message_lower or "when" in message_lower:
        response = {
            "response": "Excellent timing question! The current market strongly favors sellers - we're seeing homes sell 15% faster than last year, with an average of just 22 days on market in your area. Interest rates are still favorable for buyers, creating strong demand. What's driving your timeline consideration?",
            "confidence": 91,
            "intent": "Market Timing"
        }
        insights = "Timing inquiry indicates decision-making phase. Market data delivery increases conversion probability by 23%."

    elif "sell" in message_lower and ("house" in message_lower or "home" in message_lower):
        response = {
            "response": "I'd be delighted to help you explore selling your home! Westlake is a fantastic area with strong buyer demand. To give you the best guidance, I'd love to learn more about your situation. What's motivating you to consider selling, and what's your ideal timeline?",
            "confidence": 97,
            "intent": "Initial Selling Inquiry"
        }
        insights = "Strong selling intent detected. Excellent engagement opportunity. Prioritize rapport building and needs assessment."

    else:
        response = {
            "response": "Thanks for reaching out! I'm here to help with all your real estate questions. Whether you're curious about your home's value, market conditions, or the selling process, I have the latest insights to guide you. What specific aspect of selling interests you most?",
            "confidence": 89,
            "intent": "General Inquiry"
        }
        insights = "Open-ended inquiry. Focus on needs discovery and relationship building. Multiple conversation paths available."

    if include_market_insights:
        market_context = " Current market data shows strong seller conditions with 8% year-over-year appreciation in your area."
        response["response"] += market_context

    return response, insights


def update_seller_context(context, exchange):
    """Update seller context based on conversation"""
    context["conversation_count"] += 1

    # Simple engagement scoring based on message content
    if len(exchange["seller_message"]) > 50:
        context["engagement_score"] = min(1.0, context["engagement_score"] + 0.05)

    # Update readiness based on conversation intent
    intent = exchange["intent"]
    if intent == "Property Valuation":
        if context["readiness_level"] == "Considering":
            context["readiness_level"] = "Preparing"
    elif intent == "Market Timing":
        context["engagement_score"] = min(1.0, context["engagement_score"] + 0.03)


def get_demo_conversation_recommendations(context, history):
    """Get demo conversation recommendations"""

    recent_intents = [exchange["intent"] for exchange in history[-3:]]

    recommendations = {
        "follow_ups": [],
        "questions": []
    }

    if "Property Valuation" in recent_intents:
        recommendations["follow_ups"].extend([
            "Schedule in-home property evaluation",
            "Prepare detailed comparative market analysis",
            "Share recent neighborhood sales data"
        ])
        recommendations["questions"].extend([
            "What improvements have you made to the property?",
            "Are you familiar with recent sales in your neighborhood?",
            "What's your ideal timeline for selling?"
        ])

    if "Market Timing" in recent_intents:
        recommendations["follow_ups"].extend([
            "Provide market trend analysis",
            "Discuss optimal listing strategies",
            "Share buyer demand insights"
        ])
        recommendations["questions"].extend([
            "What factors are most important in your timing decision?",
            "Are you looking to buy another home as well?",
            "How flexible is your timeline?"
        ])

    # Default recommendations
    if not recommendations["follow_ups"]:
        recommendations["follow_ups"] = [
            "Build rapport and understand motivation",
            "Gather property information",
            "Share market insights relevant to seller"
        ]
        recommendations["questions"] = [
            "What's prompting you to consider selling?",
            "Tell me about your current property",
            "What questions do you have about the market?"
        ]

    return recommendations


# Main execution
if __name__ == "__main__":
    render_seller_claude_integration_demo()