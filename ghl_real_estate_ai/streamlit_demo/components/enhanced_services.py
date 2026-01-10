"""
Enhanced UI Components for GHL Real Estate AI.
Renders the "Wow Factor" features: Lead Insights, Agent Coaching, and Smart Automation.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the services
try:
    from ghl_real_estate_ai.services.ai_lead_insights import AILeadInsightsService
    from ghl_real_estate_ai.services.agent_coaching import AgentCoachingService
    from ghl_real_estate_ai.services.smart_automation import SmartAutomationEngine
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False


def card_metric(title: str, value: str, subtitle: str):
    """Simple metric card component."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: #1e293b; font-size: 0.9rem; font-weight: 600;">
            {title}
        </h4>
        <div style="font-size: 1.5rem; font-weight: 700; color: #059669; margin-bottom: 0.5rem;">
            {value}
        </div>
        <p style="margin: 0; font-size: 0.8rem; color: #64748b;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_ai_lead_insights(lead_data):
    """Render the AI Lead Insights panel."""

    st.markdown("### 🧠 AI Lead Intelligence")

    # Use mock data when services aren't available
    if not SERVICES_AVAILABLE:
        render_mock_ai_lead_insights(lead_data)
        return

    try:
        service = AILeadInsightsService()

        # Get health score with error handling
        try:
            health = service.get_lead_health_score(lead_data)
            # If we get here, render the real service data
            # (Implementation would go here for production)
            st.info("Real AI service data would display here")
        except Exception:
            render_mock_ai_lead_insights(lead_data)
            return
    except Exception:
        render_mock_ai_lead_insights(lead_data)
        return


def render_mock_ai_lead_insights(lead_data: Dict[str, Any]):
    """Render mock AI Lead Insights when services unavailable."""

    # Extract lead data with fallbacks
    lead_health = lead_data.get('health_score', 87)
    lead_name = lead_data.get('name', 'Demo Lead')
    engagement_level = lead_data.get('engagement_level', 'high')

    # Mock health data
    health = {
        'overall_health': lead_health,
        'status': 'Hot Lead' if lead_health > 80 else 'Warm Lead',
        'trend': 'Increasing' if engagement_level == 'high' else 'Stable',
        'recommendation': 'Schedule immediate follow-up call' if lead_health > 80 else 'Continue nurturing sequence'
    }

    # Health Gauge
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=health['overall_health'],
            title={'text': "Lead Health"},
            delta={'reference': 75, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': _get_color(health['overall_health'])},
                'steps': [
                    {'range': [0, 50], 'color': "#f1f5f9"},
                    {'range': [50, 80], 'color': "#e2e8f0"}
                ]
            }
        ))
        fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width='stretch')

    with c2:
        st.markdown(f"#### Status: {health['status']}")
        st.markdown(f"**Trend:** {health['trend']}")
        st.info(f"💡 {health['recommendation']}")

    with c3:
        # Mock next best action
        action = {
            'action': 'schedule_call',
            'expected_impact': 'High',
            'reason': 'Lead showing strong buying signals'
        }

        card_metric(
            "🚀 Next Best Action",
            action['action'].replace('_', ' ').title(),
            f"Impact: {action['expected_impact']} | {action['reason']}"
        )
        if st.button("Execute Action Now", key="exec_nba_mock"):
            st.success(f"Initiated: {action['action']}")

    st.divider()

    # Mock detailed insights
    insights = [
        {
            'insight_type': 'opportunity',
            'title': 'High Engagement Window',
            'description': f'{lead_name} has shown 3x higher response rates in afternoons',
            'recommended_action': 'Schedule follow-up for 2-4pm window',
            'confidence': 0.89
        },
        {
            'insight_type': 'risk',
            'title': 'Competitor Contact Detected',
            'description': 'Lead mentioned speaking with another agent recently',
            'recommended_action': 'Emphasize unique value propositions immediately',
            'confidence': 0.76
        },
        {
            'insight_type': 'action',
            'title': 'Optimal Follow-Up Window',
            'description': 'Based on response patterns, best time to reach this lead is Afternoon (2-4pm)',
            'recommended_action': 'Schedule follow-up for Afternoon (2-4pm)',
            'confidence': 0.92
        }
    ]

    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("#### 🔥 Opportunities & Risks")
        for i in insights:
            if i['insight_type'] in ['opportunity', 'risk']:
                icon = "🟢" if i['insight_type'] == 'opportunity' else "🔴"
                with st.expander(f"{icon} {i['title']} ({int(i['confidence']*100)}%)", expanded=True):
                    st.write(i['description'])
                    st.caption(f"Recommendation: {i['recommended_action']}")

    with c_right:
        st.markdown("#### ⚡ Urgency & Timing")
        for i in insights:
            if i['insight_type'] == 'action':
                with st.expander(f"⏰ {i['title']}", expanded=True):
                    st.write(i['description'])
                    st.caption(f"Recommendation: {i['recommended_action']}")


def render_agent_coaching(conversation_history, context):
    """Render the Agent Coaching panel."""
    if not SERVICES_AVAILABLE:
        return render_mock_agent_coaching(conversation_history, context)

    try:
        service = AgentCoachingService()
        tips = service.analyze_conversation_live(conversation_history, context)
    except Exception:
        return render_mock_agent_coaching(conversation_history, context)


def render_mock_agent_coaching(conversation_history, context):
    """Render mock agent coaching when services unavailable."""

    st.markdown("### 🎓 Real-Time Agent Coach")

    # Mock coaching tips
    tips = [
        {
            'title': 'Ask About Timeline',
            'suggestion': 'The lead mentioned urgency but no specific timeline. Ask for clarification.',
            'example': 'When would you ideally like to be settled in your new home?',
            'why_it_works': 'Timeline questions help qualify urgency and show you\'re listening',
            'urgency': 1
        },
        {
            'title': 'Highlight Market Advantage',
            'suggestion': 'Lead seems price-conscious. Emphasize current market opportunities.',
            'example': 'With interest rates stabilizing, now is actually a great time to lock in a rate.',
            'why_it_works': 'Creates urgency while addressing price concerns',
            'urgency': 2
        }
    ]

    if not tips:
        st.info("Listening for coaching opportunities...")
        return

    for tip in tips:
        # Color code based on urgency
        border_color = "#ef4444" if tip['urgency'] == 1 else "#3b82f6"
        bg_color = "#fef2f2" if tip['urgency'] == 1 else "#eff6ff"

        st.markdown(
            f"""
            <div style="border-left: 4px solid {border_color}; background-color: {bg_color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                <h4 style="margin:0; color: #1e293b;">{tip['title']}</h4>
                <p style="margin:5px 0 10px 0; color: #475569;">{tip['suggestion']}</p>
                <div style="background: white; padding: 10px; border-radius: 5px; border: 1px dashed #cbd5e1;">
                    <strong>Try saying:</strong><br>
                    <em>"{tip['example']}"</em>
                </div>
                <div style="margin-top: 5px; font-size: 0.8em; color: #64748b;">
                    Why: {tip['why_it_works']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Mock closing techniques
    st.markdown("#### 🎯 Closing Techniques")
    score = context.get('score', 85)
    if score > 80:
        st.info("**Recommended: Assumptive Close**\n\nScript: \"I'll send you the listing details and we can schedule a showing for this weekend. Does Saturday or Sunday work better for you?\"")
    else:
        st.info("**Recommended: Trial Close**\n\nScript: \"If we found a property that met all your criteria, how quickly would you be ready to make an offer?\"")


def render_smart_automation(lead_data):
    """Render the Smart Automation panel."""
    if not SERVICES_AVAILABLE:
        return render_mock_smart_automation(lead_data)

    try:
        service = SmartAutomationEngine()
        # Original service code would go here
    except Exception:
        return render_mock_smart_automation(lead_data)


def render_mock_smart_automation(lead_data):
    """Render mock smart automation when services unavailable."""

    st.markdown("### 🤖 Smart Automation Engine")

    tabs = st.tabs(["Scheduled Actions", "Optimization", "A/B Tests"])

    with tabs[0]:
        st.markdown("#### ⏰ Upcoming Automated Actions")

        # Mock scheduled actions
        actions = [
            {
                'action_type': 'SMS',
                'message_template': 'Hi! Just wanted to follow up on the properties I sent...',
                'trigger': 'No response after 24 hours',
                'expected_outcome': 'Re-engage dormant lead',
                'scheduled_time': datetime.now() + timedelta(hours=2),
                'action_id': 'sms_001'
            },
            {
                'action_type': 'EMAIL',
                'message_template': 'Weekly market update for your area of interest...',
                'trigger': 'Weekly nurture sequence',
                'expected_outcome': 'Maintain engagement',
                'scheduled_time': datetime.now() + timedelta(days=1),
                'action_id': 'email_001'
            }
        ]

        if actions:
            for action in actions:
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{action['action_type']}**: {action['message_template'][:60]}...")
                        st.caption(f"Trigger: {action['trigger']} | Goal: {action['expected_outcome']}")
                    with c2:
                        st.markdown(f"**{action['scheduled_time'].strftime('%I:%M %p')}**")
                        if st.button("Approve", key=f"app_{action['action_id']}"):
                            st.toast("Action approved!")
                    st.divider()
        else:
            st.success("✅ No pending actions needed.")

    with tabs[1]:
        st.markdown("#### 📊 Send Time Optimization")

        # Mock optimization data
        c1, c2 = st.columns(2)
        with c1:
            card_metric("Best Send Time", "2:30 PM", "Weekdays, based on response patterns")
        with c2:
            card_metric("Confidence", "89%", "Based on 45+ interactions")

    with tabs[2]:
        st.markdown("#### 🧪 A/B Test Results")

        st.success("🏆 Winner: Variant B (+23% better response rate)")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Variant A**")
            st.write("Response Rate: 12.5%")
            st.caption("Hey! Checking in about your home search...")
        with c2:
            st.markdown("**Variant B**")
            st.write("Response Rate: 15.4%")
            st.caption("Found 3 new listings that match your criteria 🏡")


def _get_color(value):
    """Get color based on value."""
    if value >= 80:
        return "#22c55e"
    if value >= 60:
        return "#eab308"
    return "#ef4444"

