"""
Enhanced UI Components for GHL Real Estate AI.
Renders the "Wow Factor" features: Lead Insights, Agent Coaching, and Smart Automation.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import the services
try:
    from ghl_real_estate_ai.services.ai_lead_insights import AILeadInsightsService
    from ghl_real_estate_ai.services.agent_coaching import AgentCoachingService
    from ghl_real_estate_ai.services.smart_automation import SmartAutomationEngine
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False

import utils.ui as ui

def render_ai_lead_insights(lead_data):
    """Render the AI Lead Insights panel."""
    if not SERVICES_AVAILABLE:
        st.error("AI Services not found.")
        return

    service = AILeadInsightsService()
    
    # 1. Health Score Header
    health = service.get_lead_health_score(lead_data)
    
    st.markdown("### 🧠 AI Lead Intelligence")
    
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
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown(f"#### Status: {health['status']}")
        st.markdown(f"**Trend:** {health['trend']}")
        st.info(f"💡 {health['recommendation']}")

    with c3:
        # 2. Next Best Action
        nba = service.predict_next_best_action(lead_data)
        if nba['next_best_action']:
            action = nba['next_best_action']
            ui.card_metric(
                "🚀 Next Best Action", 
                action['action'].replace('_', ' ').title(),
                f"Impact: {action['expected_impact']} | {action['reason']}"
            )
            if st.button("Execute Action Now", key="exec_nba"):
                st.success(f"Initiated: {action['action']}")

    st.divider()
    
    # 3. Detailed Insights
    insights = service.analyze_lead(lead_data)
    
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.markdown("#### 🔥 Opportunities & Risks")
        for i in insights:
            if i.insight_type in ['opportunity', 'risk']:
                icon = "🟢" if i.insight_type == 'opportunity' else "🔴"
                with st.expander(f"{icon} {i.title} ({int(i.confidence*100)}%)", expanded=True):
                    st.write(i.description)
                    st.caption(f"Recommendation: {i.recommended_action}")

    with c_right:
        st.markdown("#### ⚡ Urgency & Timing")
        for i in insights:
            if i.insight_type == 'action':
                with st.expander(f"⏰ {i.title}", expanded=True):
                    st.write(i.description)
                    st.caption(f"Recommendation: {i.recommended_action}")


def render_agent_coaching(conversation_history, context):
    """Render the Agent Coaching panel."""
    if not SERVICES_AVAILABLE: return

    service = AgentCoachingService()
    tips = service.analyze_conversation_live(conversation_history, context)
    
    st.markdown("### 🎓 Real-Time Agent Coach")
    
    if not tips:
        st.info("Listening for coaching opportunities...")
        return

    for tip in tips:
        # Color code based on urgency
        border_color = "#ef4444" if tip.urgency == 1 else "#3b82f6"
        bg_color = "#fef2f2" if tip.urgency == 1 else "#eff6ff"
        
        st.markdown(
            f"""
            <div style=\"border-left: 4px solid {border_color}; background-color: {bg_color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                <h4 style=\"margin:0; color: #1e293b;">{tip.title}</h4>
                <p style=\"margin:5px 0 10px 0; color: #475569;">{tip.suggestion}</p>
                <div style=\"background: white; padding: 10px; border-radius: 5px; border: 1px dashed #cbd5e1;">
                    <strong>Try saying:</strong><br>
                    <em>"{tip.example}"</em>
                </div>
                <div style=\"margin-top: 5px; font-size: 0.8em; color: #64748b;">
                    Why: {tip.why_it_works}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Closing Techniques
    st.markdown("#### 🎯 Closing Techniques")
    closer = service.get_closing_technique(context.get('score', 0), 'high')
    if closer['recommended']:
        rec = closer['recommended']
        st.info(f"**Recommended: {rec['name']}**\n\nScript: \"{rec['script']}\"")


def render_smart_automation(lead_data):
    """Render the Smart Automation panel."""
    if not SERVICES_AVAILABLE: return

    service = SmartAutomationEngine()
    
    st.markdown("### 🤖 Smart Automation Engine")
    
    tabs = st.tabs(["Scheduled Actions", "Optimization", "A/B Tests"])
    
    with tabs[0]:
        actions = service.analyze_and_schedule(lead_data)
        if actions:
            for action in actions:
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{action.action_type.upper()}**: {action.message_template[:60]}...")
                        st.caption(f"Trigger: {action.trigger} | Goal: {action.expected_outcome}")
                    with c2:
                        st.markdown(f"**{action.scheduled_time.strftime('%I:%M %p')}**")
                        if st.button("Approve", key=f"app_{action.action_id}"):
                            st.toast("Action approved!")
                    st.divider()
        else:
            st.success("✅ No pending actions needed.")

    with tabs[1]:
        opt = service.get_optimal_send_time(lead_data)
        c1, c2 = st.columns(2)
        with c1:
            ui.card_metric("Best Send Time", opt['best_time'], opt['window'])
        with c2:
            ui.card_metric("Confidence", f"{int(opt['confidence']*100)}%", opt['reason'])
            
    with tabs[2]:
        res = service.get_ab_test_results("breakup_text_v1_v2")
        st.markdown(f"#### Test: {res.get('name', 'N/A')}")
        if 'winner' in res:
            st.success(f"🏆 Winner: {res['winner'].replace('_', ' ').title()} (+{int(res['improvement']*100)}% better)")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Variant A**")
                st.write(f"Response Rate: {res['variant_a']['response_rate']:.1%}")
                st.caption(res['variant_a']['message'])
            with c2:
                st.markdown("**Variant B**")
                st.write(f"Response Rate: {res['variant_b']['response_rate']:.1%}")
                st.caption(res['variant_b']['message'])

def _get_color(value):
    if value >= 80: return "#22c55e"
    if value >= 60: return "#eab308"
    return "#ef4444"
