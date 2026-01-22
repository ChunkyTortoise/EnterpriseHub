"""
Proactive Intelligence Dashboard - Smart Notifications & Predictive Analytics UI
Real-time alerts, predictions, and performance coaching interface.
"""

import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Helper for safe asyncio execution in Streamlit
def run_async(coro):
    
    return run_async(coro)

# Import proactive intelligence services
try:
    from ghl_real_estate_ai.services.proactive_intelligence_engine import (
        get_proactive_intelligence_engine,
        AlertPriority,
        AlertType
    )
    PROACTIVE_INTELLIGENCE_AVAILABLE = True
except ImportError:
    PROACTIVE_INTELLIGENCE_AVAILABLE = False

def render_proactive_intelligence_dashboard():
    """
    Proactive Intelligence Dashboard with real-time alerts and predictions.
    Obsidian Command Edition.
    """
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart, render_dossier_block

    st.markdown("""
        <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">🔮 PROACTIVE INTELLIGENCE</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">AI-powered alerts, multi-horizon predictions, and tactical coaching</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(99, 102, 241, 0.1); color: #6366F1; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(99, 102, 241, 0.3); letter-spacing: 0.1em; display: flex; align-items: center; gap: 10px;">
                    <div class="status-pulse" style="width: 10px; height: 10px; background: #6366F1; border-radius: 50%;"></div>
                    SENTINEL: ONLINE
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not PROACTIVE_INTELLIGENCE_AVAILABLE:
        st.error("Proactive Intelligence system not available. Please check configuration.")
        return

    # Initialize intelligence engine
    engine = get_proactive_intelligence_engine()

    # Dashboard tabs
    alert_tab, predict_tab, coach_tab, monitor_tab = st.tabs([
        "🚨 Smart Alerts",
        "🔮 Predictions",
        "💡 AI Coaching",
        "📡 Monitoring"
    ])

    # =======================
    # SMART ALERTS TAB
    # =======================
    with alert_tab:
        st.markdown("#### 🚨 Real-Time Smart Notifications")

        # Alert controls
        col_control1, col_control2, col_control3 = st.columns([1, 1, 1])

        with col_control1:
            if st.button("🔄 Refresh Alerts", use_container_width=True):
                st.rerun()

        with col_control2:
            priority_filter = st.selectbox(
                "Filter by Priority:",
                ["All", "Critical", "High", "Medium", "Low", "Info"],
                index=0
            )

        with col_control3:
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)

        # Generate sample alerts for demo
        if st.button("🎯 Generate Smart Alerts"):
            with st.spinner("Generating proactive alerts..."):
                # Get sample context and generate alerts
                sample_context = {
                    "leads": [
                        {"id": "lead_1", "name": "Sarah Martinez", "last_contact_hours": 76, "engagement_score": 0.65},
                        {"id": "lead_2", "name": "David Kim", "last_contact_hours": 12, "engagement_score": 0.87},
                        {"id": "lead_3", "name": "Maria Rodriguez", "last_contact_hours": 168, "engagement_score": 0.45}
                    ],
                    "performance": {"conversion_rate": 0.14},
                    "pipeline_value": 75000,
                    "monthly_target": 150000
                }
                
                alerts = run_async(engine.generate_smart_notifications(sample_context))

                st.success(f"Generated {len(alerts)} smart alerts!")
                time.sleep(1)
                st.rerun()

        # Display active alerts
        st.markdown("---")

        # Get active alerts
        filter_priority = None if priority_filter == "All" else getattr(AlertPriority, priority_filter.upper(), None)
        active_alerts = run_async(engine.get_active_alerts(filter_priority))

        if active_alerts:
            st.markdown(f"##### 📋 ACTIVE COMMAND ALERTS ({len(active_alerts)})")

            for alert in active_alerts:
                # Alert card styling based on priority - Obsidian Edition
                priority_colors = {
                    AlertPriority.CRITICAL: "#ef4444",
                    AlertPriority.HIGH: "#f97316",
                    AlertPriority.MEDIUM: "#f59e0b",
                    AlertPriority.LOW: "#10b981",
                    AlertPriority.INFO: "#6366F1"
                }

                alert_icons = {
                    AlertType.OPPORTUNITY: "🚀",
                    AlertType.RISK: "⚠️",
                    AlertType.PERFORMANCE: "📈",
                    AlertType.MARKET: "📊",
                    AlertType.LEAD_BEHAVIOR: "👤",
                    AlertType.TIMING: "⏰",
                    AlertType.SYSTEM: "⚙️"
                }

                color = priority_colors.get(alert.priority, "#6b7280")
                icon = alert_icons.get(alert.alert_type, "📢")

                # Alert card - Obsidian Command Style
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 1.5rem; margin: 1.25rem 0; background: rgba(22, 27, 34, 0.7); border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {color}; backdrop-filter: blur(10px);">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem; filter: drop-shadow(0 0 10px {color}40);">{icon}</span>
                        <span style="font-weight: 700; color: {color}; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">{alert.priority.value}</span>
                        <span style="color: #8B949E; font-size: 0.75rem; font-family: 'Inter', sans-serif;">• {alert.timestamp.strftime('%H:%M')}</span>
                        <div style="margin-left: auto;">
                            <span style="background: {color}15; color: {color}; padding: 4px 12px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; border: 1px solid {color}30; text-transform: uppercase;">{alert.alert_type.value.replace('_', ' ')}</span>
                        </div>
                    </div>
                    <h4 style="margin: 0 0 10px 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em;">{alert.title}</h4>
                    <p style="margin: 0 0 1.25rem 0; color: #E6EDF3; line-height: 1.6; font-size: 0.95rem; opacity: 0.9;">{alert.description}</p>
                    <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05);">
                        <strong style="color: #6366F1; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Operational Directives:</strong>
                        <ul style="margin: 0.75rem 0 0 0; padding-left: 1.25rem; color: #E6EDF3; font-size: 0.9rem;">
                            {''.join([f'<li style="margin: 4px 0;">{item}</li>' for item in alert.action_items])}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Alert actions
                alert_col1, alert_col2, alert_col3 = st.columns([1, 1, 1])

                with alert_col1:
                    if st.button(f"👀 Mark Seen", key=f"seen_{alert.alert_id}"):
                        run_async(engine.mark_alert_seen(alert.alert_id))
                        st.success("Alert marked as seen!")
                        time.sleep(0.5)
                        st.rerun()

                with alert_col2:
                    if st.button(f"✅ Take Action", key=f"action_{alert.alert_id}"):
                        run_async(engine.mark_alert_acted_upon(alert.alert_id))
                        st.success("Alert marked as acted upon!")
                        time.sleep(0.5)
                        st.rerun()

                with alert_col3:
                    if alert.lead_id:
                        if st.button(f"👤 View Lead", key=f"lead_{alert.alert_id}"):
                            st.info(f"Opening lead profile: {alert.lead_id}")

                st.markdown("---")

        else:
            st.info("🎯 No active alerts. Your system is running smoothly!")
            st.markdown("*Click 'Generate Smart Alerts' to see proactive intelligence in action.*")

    # =======================
    # PREDICTIONS TAB
    # =======================
    with predict_tab:
        st.markdown("#### 🔮 Predictive Analytics & Insights")

        # Prediction controls
        pred_col1, pred_col2 = st.columns([1, 1])

        with pred_col1:
            prediction_type = st.selectbox(
                "Prediction Type:",
                ["General Insights", "Lead-Specific", "Market Trends", "Performance Forecast"]
            )

        with pred_col2:
            if st.button("🔮 Generate Predictions", use_container_width=True):
                with st.spinner("Generating predictive insights..."):
                    try:
                        insights = run_async(engine.get_predictive_insights())
                        st.session_state.predictive_insights_cache = insights
                        st.success(f"Generated {len(insights)} predictive insights!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating predictions: {str(e)}")

        # Display predictions
        if 'predictive_insights_cache' in st.session_state:
            st.markdown("---")
            # In a real implementation, we would iterate over st.session_state.predictive_insights_cache
            # For this demo component, we'll continue using the visual sample below but now it only 
            # shows after 'generation' or if already in state.
            
            # Sample predictions display
            predictions_data = [
            {
                "type": "Closing Probability",
                "value": "73%",
                "confidence": "85%",
                "lead": "Sarah Martinez",
                "reasoning": "High engagement score, quick responses, budget alignment",
                "actions": ["Schedule in-person meeting", "Prepare premium options", "Draft purchase agreement"]
            },
            {
                "type": "Optimal Contact Time",
                "value": "Tuesday 10:00 AM",
                "confidence": "78%",
                "lead": "David Kim",
                "reasoning": "Analysis of past response patterns shows highest engagement Tuesday mornings",
                "actions": ["Schedule call for Tuesday 10 AM", "Prepare high-impact agenda", "Set 15-min reminder"]
            },
            {
                "type": "Market Trend",
                "value": "Buyer Activity ↗️",
                "confidence": "82%",
                "lead": "General",
                "reasoning": "Interest rate stabilization + seasonal patterns = increased buyer activity",
                "actions": ["Increase lead gen budget 20%", "Prepare additional inventory", "Schedule extra showings"]
            }
        ]
        for pred in predictions_data:
            # Prediction card - Obsidian Edition
            st.markdown(f"""
            <div style="border: 1px solid rgba(255,255,255,0.05); padding: 1.5rem; margin: 1.25rem 0; background: rgba(22, 27, 34, 0.7); border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); backdrop-filter: blur(10px);">
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 1.25rem;">
                    <div style="background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color: white; padding: 6px 16px; border-radius: 8px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">
                        {pred['type']}
                    </div>
                    <div style="font-size: 1.75rem; font-weight: 700; color: #10b981; font-family: 'Space Grotesk', sans-serif;">{pred['value']}</div>
                    <div style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.2);">
                        {pred['confidence']} CONFIDENCE
                    </div>
                    <div style="margin-left: auto; color: #8B949E; font-size: 0.8rem; font-family: 'Inter', sans-serif; font-weight: 600;">
                        NODE: {pred['lead'].upper()}
                    </div>
                </div>

                <div style="margin-bottom: 1.25rem;">
                    <strong style="color: #6366F1; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Analysis Log:</strong>
                    <p style="margin: 0.5rem 0 0 0; color: #E6EDF3; line-height: 1.6; font-size: 0.95rem; opacity: 0.9;">{pred['reasoning']}</p>
                </div>

                <div style="background: rgba(99, 102, 241, 0.05); padding: 1.25rem; border-radius: 10px; border-left: 4px solid #6366F1; border: 1px solid rgba(99, 102, 241, 0.1); border-left: 4px solid #6366F1;">
                    <strong style="color: #6366F1; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Strategic Directives:</strong>
                    <ul style="margin: 0.75rem 0 0 0; padding-left: 1.25rem; color: #E6EDF3; font-size: 0.9rem;">
                        {''.join([f'<li style="margin: 4px 0;">{action}</li>' for action in pred['actions']])}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Prediction accuracy chart
        st.markdown("##### 📊 Prediction Accuracy Trends")

        fig_accuracy = go.Figure()
        fig_accuracy.add_trace(go.Scatter(
            x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            y=[85, 87, 82, 89, 91, 86, 88],
            mode='lines+markers',
            name='Prediction Accuracy',
            line=dict(color='#059669', width=3),
            marker=dict(size=8)
        ))

        fig_accuracy.update_layout(
            title="AI Prediction Accuracy Over Time",
            yaxis_title="Accuracy (%)",
            height=300,
            showlegend=False
        )

        st.plotly_chart(fig_accuracy, use_container_width=True)

    # =======================
    # AI COACHING TAB
    # =======================
    with coach_tab:
        st.markdown("#### 💡 Real-Time Performance Coaching")

        # Coaching controls
        coach_col1, coach_col2 = st.columns([1, 1])

        with coach_col1:
            coaching_focus = st.selectbox(
                "Coaching Focus:",
                ["Communication", "Strategy", "Time Management", "Follow-up", "All Areas"]
            )

        with coach_col2:
            if st.button("🎯 Get AI Coaching", use_container_width=True):
                with st.spinner("Generating personalized coaching..."):
                    try:
                        performance_data = {
                            "avg_response_time_hours": 3.2,
                            "closing_rate": 0.16,
                            "followup_completion_rate": 0.73
                        }

                        tips = run_async(engine.get_performance_coaching(performance_data))
                        st.session_state.ai_coaching_cache = tips
                        st.success(f"Generated {len(tips)} coaching insights!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating coaching: {str(e)}")

        if 'ai_coaching_cache' in st.session_state:
            st.markdown("---")

            # Performance metrics overview
            st.markdown("##### 📈 Performance Overview")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric("Response Time", "3.2h", "-0.8h")
            with metric_col2:
                st.metric("Closing Rate", "16%", "+2%")
            with metric_col3:
                st.metric("Follow-up Rate", "73%", "-5%")
            with metric_col4:
                st.metric("Engagement Score", "82%", "+7%")

            st.markdown("---")

            # Coaching insights
            coaching_insights = [
                {
                    "category": "Communication",
                    "title": "⚡ Improve Response Speed",
                    "impact": "High",
                    "effort": "Immediate",
                    "description": "Your average response time (3.2 hours) could be improved. Faster responses increase engagement by 40%.",
                    "metrics": ["Response time under 2 hours", "Engagement rate increase", "Lead conversion improvement"],
                    "priority": "🔴 High Priority"
                },
                {
                    "category": "Strategy",
                    "title": "🎯 Enhance Closing Techniques",
                    "impact": "High",
                    "effort": "Short-term",
                    "description": "Your closing rate could be improved with advanced closing strategies and better objection handling.",
                    "metrics": ["Closing rate above 20%", "Objection handling confidence", "Deal velocity increase"],
                    "priority": "🟡 Medium Priority"
                },
                {
                    "category": "Follow-up",
                    "title": "📋 Improve Follow-up Consistency",
                    "impact": "Medium",
                    "effort": "Short-term",
                    "description": "Consistent follow-ups increase conversion by 50%. Automate reminders and templates.",
                    "metrics": ["Follow-up completion above 85%", "Lead nurturing improvement", "Conversion rate increase"],
                    "priority": "🟡 Medium Priority"
                }
            ]

            for insight in coaching_insights:
                # Filter by focus
                if coaching_focus != "All Areas" and insight['category'] != coaching_focus:
                    continue

                impact_colors = {
                    "High": "#ef4444",
                    "Medium": "#f59e0b",
                    "Low": "#10b981"
                }

                effort_colors = {
                    "Immediate": "#10b981",
                    "Short-term": "#f59e0b",
                    "Long-term": "#ef4444"
                }

                st.markdown(f"""
                <div style="border: 1px solid rgba(255,255,255,0.05); padding: 1.5rem; margin: 1.25rem 0; background: rgba(22, 27, 34, 0.7); border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); backdrop-filter: blur(10px);">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.25rem;">
                        <div style="background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 6px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">
                            {insight['category']}
                        </div>
                        <div style="background: {impact_colors[insight['impact']]}15; color: {impact_colors[insight['impact']]}; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; border: 1px solid {impact_colors[insight['impact']]}30; text-transform: uppercase;">
                            {insight['impact']} IMPACT
                        </div>
                        <div style="margin-left: auto; font-weight: 700; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-size: 0.75rem; letter-spacing: 0.05em;">
                            {insight['priority'].upper()}
                        </div>
                    </div>

                <h4 style="margin: 0 0 10px 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">{insight['title']}</h4>
                <p style="margin: 0 0 1.25rem 0; color: #E6EDF3; line-height: 1.6; font-size: 0.95rem; opacity: 0.9;">{insight['description']}</p>

                <div style="background: rgba(255,255,255,0.03); padding: 1.25rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);">
                    <strong style="color: #6366F1; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Optimization Metrics:</strong>
                    <ul style="margin: 0.75rem 0 0 0; padding-left: 1.25rem; color: #E6EDF3; font-size: 0.9rem;">
                        {''.join([f'<li style="margin: 4px 0;">{metric}</li>' for metric in insight['metrics']])}
                    </ul>
                </div>
                </div>
            """, unsafe_allow_html=True)

    # =======================
    # BACKGROUND MONITORING TAB
    # =======================
    with monitor_tab:
        st.markdown("#### 📡 Background Monitoring Status")

        # Monitoring controls
        monitor_col1, monitor_col2 = st.columns([1, 1])

        with monitor_col1:
            if st.button("▶️ Start Monitoring", use_container_width=True):
                success = run_async(engine.start_background_monitoring())
                if success:
                    st.success("Background monitoring started!")
                else:
                    st.error("Failed to start monitoring")
                time.sleep(1)
                st.rerun()

        with monitor_col2:
            if st.button("⏹️ Stop Monitoring", use_container_width=True):
                run_async(engine.stop_background_monitoring())
                st.info("Background monitoring stopped")
                time.sleep(1)
                st.rerun()

        st.markdown("---")

        # Monitoring status
        monitoring_active = engine.monitoring_active

        if monitoring_active:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0;">🟢 MONITORING ACTIVE</h3>
                <p style="margin: 0; font-size: 1.1rem;">Proactive Intelligence is continuously analyzing your business</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0;">⚫ MONITORING INACTIVE</h3>
                <p style="margin: 0; font-size: 1.1rem;">Click 'Start Monitoring' to begin proactive analysis</p>
            </div>
            """, unsafe_allow_html=True)

        # Monitoring metrics
        st.markdown("##### 📊 Monitoring Metrics")

        monitor_metrics_col1, monitor_metrics_col2, monitor_metrics_col3 = st.columns(3)

        with monitor_metrics_col1:
            st.metric("Monitoring Cycles", "1,247", "+23")
            st.metric("Alerts Generated", "156", "+12")

        with monitor_metrics_col2:
            st.metric("Predictions Made", "89", "+8")
            st.metric("Coaching Tips", "34", "+5")

        with monitor_metrics_col3:
            st.metric("System Uptime", "99.7%", "+0.1%")
            st.metric("Response Time", "142ms", "-18ms")

        # Monitoring activity chart
        st.markdown("##### 📈 Monitoring Activity (Last 24 Hours)")

        fig_monitoring = go.Figure()

        # Sample monitoring data
        hours = list(range(24))
        alerts_generated = [2, 1, 0, 0, 0, 1, 3, 5, 8, 6, 4, 7, 9, 11, 8, 6, 4, 7, 5, 3, 2, 1, 1, 0]
        predictions_made = [1, 0, 0, 0, 0, 0, 2, 3, 4, 3, 2, 4, 5, 6, 4, 3, 2, 4, 3, 2, 1, 0, 0, 0]

        fig_monitoring.add_trace(go.Scatter(
            x=hours,
            y=alerts_generated,
            mode='lines+markers',
            name='Alerts Generated',
            line=dict(color='#dc2626', width=2),
            marker=dict(size=6)
        ))

        fig_monitoring.add_trace(go.Scatter(
            x=hours,
            y=predictions_made,
            mode='lines+markers',
            name='Predictions Made',
            line=dict(color='#059669', width=2),
            marker=dict(size=6)
        ))

        fig_monitoring.update_layout(
            title="Proactive Intelligence Activity",
            xaxis_title="Hour of Day",
            yaxis_title="Count",
            height=350,
            hovermode='x unified'
        )

        st.plotly_chart(fig_monitoring, use_container_width=True)

def render_proactive_alerts_widget():
    """Compact proactive alerts widget for sidebar or embedded use."""

    if not PROACTIVE_INTELLIGENCE_AVAILABLE:
        st.warning("⚠️ Proactive Intelligence unavailable")
        return

    st.markdown("#### 🚨 Smart Alerts")

    # Quick alert summary
    alert_summary = {
        "critical": 0,
        "high": 2,
        "medium": 3,
        "total": 5
    }

    if alert_summary["total"] > 0:
        st.markdown(f"""
        <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 12px; border-radius: 8px; margin: 10px 0;">
            <div style="font-weight: 700; color: #dc2626; margin-bottom: 8px;">
                🚨 {alert_summary["total"]} Active Alerts
            </div>
            <div style="font-size: 0.9rem; color: #7f1d1d;">
                • {alert_summary["high"]} High Priority<br>
                • {alert_summary["medium"]} Medium Priority
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🎯 View All Alerts", use_container_width=True):
            st.switch_page("pages/proactive_intelligence.py")
    else:
        st.success("✅ All clear! No urgent alerts.")

if __name__ == "__main__":
    # For testing the component
    render_proactive_intelligence_dashboard()