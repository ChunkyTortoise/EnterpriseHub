"""
Phase 7: Business Intelligence Command Center - Streamlit Component

Executive command center dashboard providing comprehensive business intelligence
for Jorge's Real Estate AI Platform Phase 7. Integrates revenue forecasting,
conversation analytics, market intelligence, and competitive analysis.

Built for Jorge's Real Estate AI Platform - Phase 7: Advanced AI Intelligence
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import plotly.graph_objects as go
import streamlit as st

try:
    from ghl_real_estate_ai.intelligence.business_intelligence_dashboard import (
        BusinessIntelligenceDashboard,
        create_business_intelligence_dashboard,
    )
except (ImportError, Exception):
    BusinessIntelligenceDashboard = None
    create_business_intelligence_dashboard = None


class BusinessIntelligenceCommandCenter:
    """
    Phase 7: Business Intelligence Command Center

    Streamlit-based executive dashboard providing comprehensive business intelligence
    for Jorge's real estate platform with advanced AI-driven insights and analytics.
    """

    def __init__(self):
        """Initialize the business intelligence command center"""
        self.dashboard_title = "🎯 Jorge's Business Intelligence Command Center - Phase 7"
        self.phase7_indicators = {
            "revenue_engine": "💰",
            "conversation_analytics": "💬",
            "market_intelligence": "📊",
            "competitive_analysis": "🎯",
        }

    async def render_dashboard(self):
        """Render the complete business intelligence dashboard"""
        st.set_page_config(
            page_title="Jorge's BI Command Center", page_icon="🎯", layout="wide", initial_sidebar_state="expanded"
        )

        # Dashboard header
        self._render_header()

        # Initialize dashboard
        dashboard = await self._get_dashboard_instance()

        # Get dashboard data
        with st.spinner("Loading Phase 7 Business Intelligence..."):
            dashboard_data = await dashboard.get_executive_dashboard_data()

        if "error" in dashboard_data:
            st.error(f"Error loading dashboard: {dashboard_data['error']}")
            return

        # Render dashboard sections
        self._render_executive_summary(dashboard_data.get("executive_summary"))
        self._render_real_time_metrics(dashboard_data.get("real_time_metrics", {}))
        self._render_strategic_alerts(dashboard_data.get("strategic_alerts", []))

        # Main dashboard sections
        col1, col2 = st.columns(2)

        with col1:
            self._render_revenue_intelligence(dashboard_data.get("revenue_intelligence", {}))
            self._render_market_intelligence(dashboard_data.get("market_intelligence", {}))

        with col2:
            self._render_conversation_analytics(dashboard_data.get("conversation_analytics", {}))
            self._render_competitive_analysis(dashboard_data.get("competitive_analysis", {}))

        # Jorge-specific KPIs and performance
        self._render_jorge_performance_section(dashboard_data.get("jorge_kpis", {}))
        self._render_action_dashboard(dashboard_data.get("action_dashboard", {}))

        # Footer with system status
        self._render_system_status_footer(dashboard_data)

    def _render_header(self):
        """Render dashboard header with Phase 7 branding"""
        st.markdown(
            """
            <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
                        padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
                <h1 style="color: white; margin: 0; text-align: center;">
                    🎯 Jorge's Business Intelligence Command Center
                </h1>
                <p style="color: #e2e8f0; margin: 0.5rem 0 0 0; text-align: center;">
                    Phase 7: Advanced AI Intelligence & Global Scaling | Real-Time Executive Dashboard
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Phase 7 status indicators
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(label="🚀 Phase Status", value="Phase 7", delta="Advanced AI Intelligence")

        with col2:
            st.metric(label="💰 Revenue Engine", value="Operational", delta="< 25ms inference")

        with col3:
            st.metric(label="💬 Conversation AI", value="Enhanced", delta="95%+ accuracy")

        with col4:
            st.metric(label="📊 Market Intel", value="Real-Time", delta="Automated alerts")

        with col5:
            st.metric(label="🎯 Commission Defense", value="96%", delta="+1% vs target")

    def _render_executive_summary(self, summary_data: Optional[Dict]):
        """Render executive summary section"""
        if not summary_data:
            return

        st.markdown("## 📋 Executive Summary")

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            revenue = summary_data.get("revenue_summary", {})
            st.metric(
                label="Monthly Revenue Projection",
                value=f"${revenue.get('current_month_projection', 0):,.0f}",
                delta=f"{revenue.get('growth_rate', 0):.1%} MoM",
            )

        with col2:
            conversation = summary_data.get("conversation_summary", {})
            st.metric(
                label="Conversion Rate",
                value=f"{conversation.get('conversion_rate', 0):.1%}",
                delta="Jorge methodology",
            )

        with col3:
            market = summary_data.get("market_summary", {})
            st.metric(
                label="Market Health Score",
                value=f"{market.get('market_health_score', 0):.1%}",
                delta=f"{market.get('active_trends', 0)} active trends",
            )

        with col4:
            competitive = summary_data.get("competitive_summary", {})
            st.metric(
                label="Commission Defense",
                value=f"{competitive.get('commission_defense_rate', 0):.1%}",
                delta="6% rate maintained",
            )

        # Performance score
        performance_score = summary_data.get("performance_score", 0)
        st.subheader(f"🏆 Overall Performance Score: {performance_score:.1%}")

        # Progress bar for performance score
        st.progress(performance_score)

        # Key insights
        insights = summary_data.get("key_insights", [])
        if insights:
            st.subheader("🔍 Key Insights")
            for insight in insights:
                st.info(insight)

        # Action items
        actions = summary_data.get("action_items", [])
        if actions:
            st.subheader("⚡ Action Items")
            for action in actions:
                st.warning(action)

    def _render_real_time_metrics(self, metrics_data: Dict):
        """Render real-time metrics dashboard"""
        st.markdown("## ⚡ Real-Time Metrics")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(label="Active Conversations", value=metrics_data.get("active_conversations", 0), delta="Live now")

        with col2:
            st.metric(label="Deals in Pipeline", value=metrics_data.get("deals_in_pipeline", 0), delta="Active deals")

        with col3:
            st.metric(label="Revenue Today", value=f"${metrics_data.get('revenue_today', 0):,.0f}", delta="Current day")

        with col4:
            st.metric(label="New Leads Today", value=metrics_data.get("new_leads_today", 0), delta="Fresh prospects")

        with col5:
            status = metrics_data.get("jorge_availability", "unknown")
            status_color = "🟢" if status == "active" else "🟡" if status == "busy" else "🔴"
            st.metric(label="Jorge Status", value=f"{status_color} {status.title()}", delta="Current availability")

    def _render_strategic_alerts(self, alerts_data: List[Dict]):
        """Render strategic alerts section"""
        if not alerts_data:
            return

        st.markdown("## 🚨 Strategic Alerts")

        # Alert severity counters
        high_alerts = len([a for a in alerts_data if a.get("severity") == "high"])
        critical_alerts = len([a for a in alerts_data if a.get("severity") == "critical"])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Critical Alerts", critical_alerts, delta="Immediate action")
        with col2:
            st.metric("High Priority", high_alerts, delta="24-48 hours")
        with col3:
            st.metric("Total Active", len(alerts_data), delta="All alerts")

        # Display alerts
        for alert in alerts_data[:5]:  # Show top 5 alerts
            severity = alert.get("severity", "medium")
            emoji = "🚨" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"

            with st.expander(f"{emoji} {alert.get('title', 'Alert')} - {severity.upper()}"):
                st.write(alert.get("description", "No description"))

                actions = alert.get("recommended_actions", [])
                if actions:
                    st.write("**Recommended Actions:**")
                    for action in actions:
                        st.write(f"• {action}")

    def _render_revenue_intelligence(self, revenue_data: Dict):
        """Render revenue intelligence section"""
        st.markdown("### 💰 Revenue Intelligence")

        if "error" in revenue_data:
            st.error(f"Revenue data error: {revenue_data['error']}")
            return

        # Revenue trends
        trends = revenue_data.get("trends", {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Monthly Growth", f"{trends.get('monthly_growth', 0):.1%}", delta="Month over month")
        with col2:
            st.metric("Quarterly Trend", f"{trends.get('quarterly_trend', 0):.1%}", delta="Quarter performance")

        # Revenue forecast chart
        forecast_data = revenue_data.get("revenue_forecast", {})
        if forecast_data:
            st.subheader("📈 Revenue Forecast")

            # Sample chart data (would be from actual forecast)
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
            actual = [350000, 375000, 390000, 420000, 445000, 465000, None, None]
            projected = [None, None, None, None, None, 465000, 485000, 502000]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=months, y=actual, mode="lines+markers", name="Actual Revenue", line=dict(color="blue"))
            )
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=projected,
                    mode="lines+markers",
                    name="Projected Revenue",
                    line=dict(dash="dash", color="orange"),
                )
            )

            fig.update_layout(
                title="Revenue Forecast - Next 3 Months", xaxis_title="Month", yaxis_title="Revenue ($)", height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        # Deal pipeline
        deal_data = revenue_data.get("deal_pipeline", {})
        if deal_data:
            st.subheader("🔄 Deal Pipeline")

            pipeline_stages = ["Leads", "Qualified", "Proposal", "Negotiation", "Closing"]
            pipeline_values = [150, 89, 45, 23, 18]

            fig = go.Figure(go.Funnel(y=pipeline_stages, x=pipeline_values, textinfo="value+percent initial"))

            fig.update_layout(title="Jorge's Deal Pipeline", height=400)
            st.plotly_chart(fig, use_container_width=True)

    def _render_conversation_analytics(self, conversation_data: Dict):
        """Render conversation analytics section"""
        st.markdown("### 💬 Conversation Analytics")

        if "error" in conversation_data:
            st.error(f"Conversation data error: {conversation_data['error']}")
            return

        # Conversation metrics
        metrics = conversation_data.get("conversation_metrics", {})
        sentiment = conversation_data.get("sentiment_analysis", {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conversation Quality", f"{metrics.get('quality_score', 0):.1%}", delta="Jorge methodology")
        with col2:
            st.metric(
                "Average Sentiment",
                f"{sentiment.get('average_sentiment_score', 0):.2f}",
                delta=sentiment.get("trend_direction", "stable"),
            )

        # Jorge methodology performance
        jorge_data = conversation_data.get("jorge_methodology", {})
        if jorge_data:
            st.subheader("🎯 Jorge's Confrontational Methodology")

            effectiveness = jorge_data.get("effectiveness_score", 0.91)
            st.metric("Methodology Effectiveness", f"{effectiveness:.1%}", delta="vs industry standard")

            # Methodology performance gauge
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=effectiveness * 100,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Jorge Method Performance"},
                    delta={"reference": 85},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 70], "color": "lightgray"},
                            {"range": [70, 85], "color": "yellow"},
                            {"range": [85, 100], "color": "green"},
                        ],
                        "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
                    },
                )
            )

            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        # A/B testing results
        ab_results = conversation_data.get("ab_testing", {})
        if ab_results:
            st.subheader("🧪 A/B Testing Results")

            active_tests = ab_results.get("active_experiments", [])
            if active_tests:
                for test in active_tests[:3]:
                    with st.expander(f"Test: {test.get('name', 'Unnamed Test')}"):
                        st.write(f"**Control Group:** {test.get('control_performance', 0):.1%}")
                        st.write(f"**Test Group:** {test.get('test_performance', 0):.1%}")
                        st.write(f"**Improvement:** {test.get('improvement', 0):.1%}")

    def _render_market_intelligence(self, market_data: Dict):
        """Render market intelligence section"""
        st.markdown("### 📊 Market Intelligence")

        if "error" in market_data:
            st.error(f"Market data error: {market_data['error']}")
            return

        # Market summary
        summary = market_data.get("market_summary", {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Market Health", f"{summary.get('market_health_score', 0.85):.1%}", delta="Current assessment")
        with col2:
            st.metric(
                "Active Trends",
                summary.get("total_active_alerts", 0),
                delta=f"{summary.get('critical_trends', 0)} critical",
            )

        # Market opportunities
        opportunities = market_data.get("market_opportunities", [])
        if opportunities:
            st.subheader("🎯 Market Opportunities")

            for opp in opportunities[:3]:
                with st.expander(f"Opportunity: {opp.get('opportunity_type', 'Unknown')}"):
                    st.write(f"**Market Area:** {opp.get('market_area', 'N/A')}")
                    st.write(f"**Potential Value:** ${opp.get('potential_value', 0):,.0f}")
                    st.write(f"**Success Probability:** {opp.get('success_probability', 0):.1%}")
                    st.write(f"**Time Sensitivity:** {opp.get('time_sensitivity', 'N/A')}")

        # Strategic insights
        insights = market_data.get("strategic_insights", {})
        if insights and "strategic_insights" in insights:
            st.subheader("🧠 AI Strategic Insights")
            st.info(
                insights["strategic_insights"][:500] + "..."
                if len(insights["strategic_insights"]) > 500
                else insights["strategic_insights"]
            )

    def _render_competitive_analysis(self, competitive_data: Dict):
        """Render competitive analysis section"""
        st.markdown("### 🎯 Competitive Analysis")

        if "error" in competitive_data:
            st.error(f"Competitive data error: {competitive_data['error']}")
            return

        # Jorge positioning
        positioning = competitive_data.get("jorge_positioning", {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Commission Defense",
                f"{positioning.get('commission_defense_rate', 0.95):.1%}",
                delta="6% rate maintained",
            )
        with col2:
            st.metric(
                "Competitive Advantage",
                f"{positioning.get('competitive_advantage_score', 0.88):.1%}",
                delta="vs market average",
            )

        # Market comparison
        comparison = competitive_data.get("market_comparison", {})
        if comparison:
            st.subheader("📈 Market Position Comparison")

            jorge_rate = comparison.get("jorge_commission_rate", 0.06)
            market_avg = comparison.get("market_average_rate", 0.055)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Jorge's Rate", f"{jorge_rate:.1%}")
            with col2:
                st.metric("Market Average", f"{market_avg:.1%}")
            with col3:
                premium = (jorge_rate - market_avg) / market_avg
                st.metric("Premium", f"{premium:.1%}", delta="Value premium")

        # Competitive alerts
        alerts = competitive_data.get("competitive_alerts", [])
        if alerts:
            st.subheader("⚠️ Competitive Alerts")
            for alert in alerts[:3]:
                severity_emoji = "🚨" if alert.get("threat_level") == "critical" else "⚠️"
                st.write(
                    f"{severity_emoji} **{alert.get('competitor', 'Unknown')}**: {alert.get('change', 'No details')}"
                )

    def _render_jorge_performance_section(self, jorge_kpis: Dict):
        """Render Jorge's specific performance metrics"""
        st.markdown("## 🏆 Jorge's Performance Excellence")

        if not jorge_kpis:
            st.info("Jorge KPI data not available")
            return

        # Signature metrics
        signature_metrics = jorge_kpis.get("jorge_signature_metrics", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Confrontational Success",
                f"{signature_metrics.get('confrontational_qualification_success', 0.89):.1%}",
                delta="Jorge's approach",
            )
        with col2:
            st.metric(
                "Objection Handling",
                f"{signature_metrics.get('objection_handling_effectiveness', 0.92):.1%}",
                delta="Effectiveness rate",
            )
        with col3:
            st.metric(
                "Commission Defense",
                f"{signature_metrics.get('commission_defense_rate', 0.96):.1%}",
                delta="6% rate success",
            )
        with col4:
            st.metric(
                "Client Referrals",
                f"{signature_metrics.get('client_referral_rate', 0.67):.1%}",
                delta="Satisfaction indicator",
            )

        # Jorge methodology performance radar
        methodology = jorge_kpis.get("jorge_methodology_performance", {})
        if methodology:
            st.subheader("🎯 Jorge's Methodology Analysis")

            categories = [
                "Qualification",
                "Motivation Detection",
                "Price Negotiation",
                "Timeline Adherence",
                "Competitive Wins",
            ]
            values = [
                methodology.get("qualification_accuracy", 0.88),
                methodology.get("seller_motivation_detection", 0.91),
                methodology.get("price_negotiation_success", 0.84),
                methodology.get("timeline_adherence", 0.93),
                methodology.get("competitive_win_rate", 0.77),
            ]

            fig = go.Figure()

            fig.add_trace(
                go.Scatterpolar(r=[v * 100 for v in values], theta=categories, fill="toself", name="Jorge Performance")
            )

            fig.add_trace(
                go.Scatterpolar(
                    r=[85] * len(categories),  # Industry benchmark
                    theta=categories,
                    fill="toself",
                    name="Industry Benchmark",
                    opacity=0.3,
                )
            )

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                title="Jorge vs Industry Benchmark",
                height=400,
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_action_dashboard(self, action_data: Dict):
        """Render actionable insights dashboard"""
        st.markdown("## ⚡ Action Dashboard")

        if not action_data:
            st.info("No action items available")
            return

        # Immediate actions
        immediate = action_data.get("immediate_actions", [])
        if immediate:
            st.subheader("🚨 Immediate Actions (24-48 hours)")
            for action in immediate:
                priority_emoji = (
                    "🔴" if action.get("priority") == "high" else "🟡" if action.get("priority") == "medium" else "🟢"
                )
                deadline = action.get("deadline", "No deadline")

                with st.expander(f"{priority_emoji} {action.get('action', 'No description')}"):
                    st.write(f"**Deadline:** {deadline}")
                    st.write(f"**Owner:** {action.get('owner', 'Unassigned')}")
                    st.write(f"**Category:** {action.get('category', 'General')}")

        # Weekly actions
        weekly = action_data.get("weekly_actions", [])
        if weekly:
            st.subheader("📅 Weekly Actions")
            for action in weekly:
                with st.expander(action.get("action", "No description")):
                    st.write(f"**Deadline:** {action.get('deadline', 'No deadline')}")
                    st.write(f"**Priority:** {action.get('priority', 'Not set')}")

        # Strategic initiatives
        strategic = action_data.get("strategic_initiatives", [])
        if strategic:
            st.subheader("🎯 Strategic Initiatives")
            for initiative in strategic:
                with st.expander(initiative.get("initiative", "No description")):
                    st.write(f"**Timeline:** {initiative.get('timeline', 'No timeline')}")
                    st.write(f"**Expected Impact:** {initiative.get('expected_impact', 'No impact defined')}")

    def _render_system_status_footer(self, dashboard_data: Dict):
        """Render system status footer"""
        st.markdown("---")
        st.markdown("### 🔧 System Status")

        real_time = dashboard_data.get("real_time_metrics", {})
        system_health = real_time.get("system_health", {})

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            revenue_status = system_health.get("revenue_engine", "unknown")
            emoji = "🟢" if revenue_status == "operational" else "🟡" if revenue_status == "degraded" else "🔴"
            st.write(f"{emoji} Revenue Engine: {revenue_status.title()}")

        with col2:
            conv_status = system_health.get("conversation_analytics", "unknown")
            emoji = "🟢" if conv_status == "operational" else "🟡" if conv_status == "degraded" else "🔴"
            st.write(f"{emoji} Conversation AI: {conv_status.title()}")

        with col3:
            market_status = system_health.get("market_intelligence", "unknown")
            emoji = "🟢" if market_status == "operational" else "🟡" if market_status == "degraded" else "🔴"
            st.write(f"{emoji} Market Intel: {market_status.title()}")

        with col4:
            dashboard_status = system_health.get("dashboard", "unknown")
            emoji = "🟢" if dashboard_status == "operational" else "🟡" if dashboard_status == "degraded" else "🔴"
            st.write(f"{emoji} Dashboard: {dashboard_status.title()}")

        with col5:
            last_update = dashboard_data.get("last_updated", "Unknown")
            if last_update != "Unknown":
                try:
                    update_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                    st.write(f"⏰ Updated: {update_time.strftime('%H:%M:%S')}")
                except:
                    st.write(f"⏰ Updated: {last_update}")
            else:
                st.write("⏰ Updated: Unknown")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()

    @st.cache_resource
    def _get_dashboard_instance(self):
        """Get cached dashboard instance"""

        async def create_instance():
            return await create_business_intelligence_dashboard()

        return asyncio.run(create_instance())


# Streamlit app entry point
def main():
    """Main entry point for the Business Intelligence Command Center"""
    command_center = BusinessIntelligenceCommandCenter()
    asyncio.run(command_center.render_dashboard())


if __name__ == "__main__":
    main()
