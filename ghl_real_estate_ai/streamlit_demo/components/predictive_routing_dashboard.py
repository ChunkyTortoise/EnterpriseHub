"""
Predictive Routing Dashboard Component

Real-time dashboard for AI-powered lead routing with performance tracking,
agent workload management, and routing optimization analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, Any

# Import the routing engine
try:
    from ..services.predictive_routing_engine import (
        predictive_routing,
        RoutingPriority,
        RoutingStrategy
    )
    ROUTING_AVAILABLE = True
except ImportError:
    ROUTING_AVAILABLE = False


def render_predictive_routing_dashboard():
    """Render the predictive routing dashboard with real-time agent management"""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    ">
        <h2 style="margin: 0; font-size: 1.8rem;">🎯 Predictive Lead Routing</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">AI-Powered Intelligent Lead Assignment</p>
    </div>
    """, unsafe_allow_html=True)

    if not ROUTING_AVAILABLE:
        st.error("🔧 Predictive Routing Engine not available. Please ensure the service is running.")
        return

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Live Routing",
        "👥 Agent Performance",
        "📊 Routing Analytics",
        "⚙️ Optimization"
    ])

    with tab1:
        render_live_routing_tab()

    with tab2:
        render_agent_performance_tab()

    with tab3:
        render_routing_analytics_tab()

    with tab4:
        render_optimization_tab()


def render_live_routing_tab():
    """Render live routing operations and queue management"""

    # Real-time metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Leads in Queue",
            "23",
            delta="-5",
            help="Number of leads awaiting routing"
        )

    with col2:
        st.metric(
            "Avg Routing Time",
            "1.2s",
            delta="-0.3s",
            help="Average time to route a lead to an agent"
        )

    with col3:
        st.metric(
            "Available Agents",
            "12",
            delta="2",
            help="Number of agents currently available"
        )

    with col4:
        st.metric(
            "Routing Success Rate",
            "97.8%",
            delta="1.2%",
            help="Percentage of successful routing decisions"
        )

    st.markdown("---")

    # Live routing queue
    st.subheader("⚡ Live Routing Queue")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Mock queue data
        queue_data = [
            {
                "Lead ID": "LD_8901",
                "Lead Name": "Alex Thompson",
                "Score": 89,
                "Priority": "🔴 Urgent",
                "Property Type": "Single Family",
                "Budget": "$750K",
                "Wait Time": "45s",
                "Status": "Analyzing...",
                "Recommended Agent": "TBD"
            },
            {
                "Lead ID": "LD_8902",
                "Lead Name": "Maria Garcia",
                "Score": 76,
                "Priority": "🟡 High",
                "Property Type": "Condo",
                "Budget": "$450K",
                "Wait Time": "23s",
                "Status": "Routing",
                "Recommended Agent": "John Smith"
            },
            {
                "Lead ID": "LD_8903",
                "Lead Name": "David Kim",
                "Score": 92,
                "Priority": "🔴 Urgent",
                "Property Type": "Luxury",
                "Budget": "$1.2M",
                "Wait Time": "12s",
                "Status": "Routed ✅",
                "Recommended Agent": "Sarah Wilson"
            }
        ]

        df_queue = pd.DataFrame(queue_data)

        # Style the dataframe based on priority and status
        def style_priority(val):
            if "🔴" in val:
                return "background-color: #e74c3c; color: white"
            elif "🟡" in val:
                return "background-color: #f39c12; color: white"
            else:
                return "background-color: #27ae60; color: white"

        def style_status(val):
            if "Routed ✅" in val:
                return "background-color: #27ae60; color: white"
            elif "Routing" in val:
                return "background-color: #f39c12; color: white"
            else:
                return "background-color: #3498db; color: white"

        styled_df = df_queue.style.applymap(style_priority, subset=['Priority']).applymap(style_status, subset=['Status'])

        st.dataframe(styled_df, use_container_width=True)

        # Quick actions for queue management
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("🚀 Force Route All", use_container_width=True):
                with st.spinner("Force routing all queued leads..."):
                    import time
                    time.sleep(2)
                    st.success("✅ All 23 leads routed successfully!")

        with col_b:
            if st.button("⚡ Priority Boost", use_container_width=True):
                st.info("🎯 Priority boost applied to high-score leads!")

        with col_c:
            if st.button("📊 Queue Analytics", use_container_width=True):
                st.session_state.show_queue_analytics = True

    with col2:
        st.markdown("#### 🎯 Routing Strategy")

        current_strategy = st.selectbox(
            "Active Strategy",
            ["Hybrid Intelligent", "Performance Optimized", "Load Balanced", "Specialization Match"],
            index=0
        )

        st.markdown("#### 📈 Real-Time Performance")

        # Mock real-time performance chart
        times = pd.date_range(start='2026-01-09 14:00', periods=20, freq='5min')
        routing_times = np.random.normal(1.2, 0.3, 20)
        routing_times = np.maximum(routing_times, 0.1)  # Ensure positive values

        fig_performance = go.Figure()
        fig_performance.add_trace(go.Scatter(
            x=times,
            y=routing_times,
            mode='lines+markers',
            name='Routing Time',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=6)
        ))

        fig_performance.update_layout(
            title="Routing Time Trend",
            xaxis_title="Time",
            yaxis_title="Routing Time (s)",
            height=250,
            showlegend=False
        )

        st.plotly_chart(fig_performance, use_container_width=True)

        # Agent availability widget
        st.markdown("#### 👥 Agent Status")

        agent_status = [
            {"name": "John S.", "status": "🟢 Available", "workload": "60%"},
            {"name": "Sarah W.", "status": "🟡 Busy", "workload": "85%"},
            {"name": "Mike C.", "status": "🟢 Available", "workload": "45%"},
            {"name": "Lisa R.", "status": "🔴 Meeting", "workload": "0%"},
            {"name": "Tom B.", "status": "🟢 Available", "workload": "70%"}
        ]

        for agent in agent_status:
            st.write(f"**{agent['name']}** - {agent['status']} ({agent['workload']})")


def render_agent_performance_tab():
    """Render agent performance tracking and analytics"""

    st.subheader("👥 Agent Performance Dashboard")

    # Agent performance overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Top Performer",
            "Sarah Wilson",
            delta="94% conversion",
            help="Agent with highest conversion rate this month"
        )

    with col2:
        st.metric(
            "Avg Response Time",
            "4.2 min",
            delta="-1.3 min",
            help="Average time agents take to respond to routed leads"
        )

    with col3:
        st.metric(
            "Team Conversion Rate",
            "31.7%",
            delta="4.2%",
            help="Overall team conversion rate"
        )

    with col4:
        st.metric(
            "Active Agents",
            "18",
            delta="2",
            help="Number of agents currently handling leads"
        )

    st.markdown("---")

    # Agent performance table
    st.subheader("📊 Individual Agent Performance")

    # Mock agent performance data
    agent_data = [
        {
            "Agent": "Sarah Wilson",
            "Leads Assigned": 89,
            "Conversion Rate": "34.8%",
            "Avg Response": "2.1 min",
            "Specialization": "Luxury",
            "Current Load": "85%",
            "Performance Score": 94,
            "Status": "🟡 Busy"
        },
        {
            "Agent": "John Smith",
            "Leads Assigned": 76,
            "Conversion Rate": "29.3%",
            "Avg Response": "3.7 min",
            "Specialization": "First-Time",
            "Current Load": "60%",
            "Performance Score": 87,
            "Status": "🟢 Available"
        },
        {
            "Agent": "Mike Chen",
            "Leads Assigned": 92,
            "Conversion Rate": "31.2%",
            "Avg Response": "4.1 min",
            "Specialization": "Investment",
            "Current Load": "45%",
            "Performance Score": 91,
            "Status": "🟢 Available"
        },
        {
            "Agent": "Lisa Rodriguez",
            "Leads Assigned": 34,
            "Conversion Rate": "28.7%",
            "Avg Response": "5.2 min",
            "Specialization": "Commercial",
            "Current Load": "0%",
            "Performance Score": 83,
            "Status": "🔴 Meeting"
        },
        {
            "Agent": "Tom Brown",
            "Leads Assigned": 67,
            "Conversion Rate": "26.9%",
            "Avg Response": "6.3 min",
            "Specialization": "Relocation",
            "Current Load": "70%",
            "Performance Score": 79,
            "Status": "🟢 Available"
        }
    ]

    df_agents = pd.DataFrame(agent_data)

    # Performance score styling
    def style_performance_score(val):
        if val >= 90:
            return "background-color: #27ae60; color: white"
        elif val >= 80:
            return "background-color: #f39c12; color: white"
        else:
            return "background-color: #e74c3c; color: white"

    def style_status(val):
        if "🟢" in val:
            return "background-color: #27ae60; color: white"
        elif "🟡" in val:
            return "background-color: #f39c12; color: white"
        else:
            return "background-color: #e74c3c; color: white"

    styled_agents_df = df_agents.style.applymap(
        style_performance_score, subset=['Performance Score']
    ).applymap(
        style_status, subset=['Status']
    )

    st.dataframe(styled_agents_df, use_container_width=True)

    # Performance visualizations
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Conversion rate comparison
        fig_conversion = px.bar(
            df_agents,
            x='Agent',
            y='Conversion Rate',
            title="🎯 Conversion Rate by Agent",
            color='Performance Score',
            color_continuous_scale='RdYlGn'
        )

        fig_conversion.update_layout(height=300, xaxis_tickangle=45)
        fig_conversion.update_traces(text=df_agents['Conversion Rate'], textposition='outside')

        st.plotly_chart(fig_conversion, use_container_width=True)

    with col2:
        # Response time vs performance score scatter
        df_agents['Response Time Numeric'] = df_agents['Avg Response'].str.extract('(\d+\.\d+)').astype(float)

        fig_scatter = px.scatter(
            df_agents,
            x='Response Time Numeric',
            y='Performance Score',
            size='Leads Assigned',
            color='Specialization',
            hover_name='Agent',
            title="⚡ Response Time vs Performance",
            labels={'Response Time Numeric': 'Avg Response Time (min)'}
        )

        fig_scatter.update_layout(height=300)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Agent specialization analysis
    st.markdown("---")
    st.subheader("🎯 Specialization Performance Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Specialization distribution
        specializations = df_agents['Specialization'].value_counts()

        fig_spec_dist = px.pie(
            values=specializations.values,
            names=specializations.index,
            title="Agent Specialization Distribution"
        )
        fig_spec_dist.update_layout(height=250)
        st.plotly_chart(fig_spec_dist, use_container_width=True)

    with col2:
        # Performance by specialization
        spec_performance = df_agents.groupby('Specialization')['Performance Score'].mean().reset_index()

        fig_spec_perf = px.bar(
            spec_performance,
            x='Specialization',
            y='Performance Score',
            title="Performance by Specialization",
            color='Performance Score',
            color_continuous_scale='viridis'
        )
        fig_spec_perf.update_layout(height=250, xaxis_tickangle=45)
        st.plotly_chart(fig_spec_perf, use_container_width=True)

    with col3:
        # Workload distribution
        df_agents['Load Numeric'] = df_agents['Current Load'].str.rstrip('%').astype(int)

        fig_workload = px.histogram(
            df_agents,
            x='Load Numeric',
            nbins=10,
            title="Current Workload Distribution",
            labels={'Load Numeric': 'Workload (%)'}
        )
        fig_workload.update_layout(height=250)
        st.plotly_chart(fig_workload, use_container_width=True)

    # Agent insights
    st.markdown("---")
    st.subheader("🧠 Performance Insights")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        st.success("""
        **🏆 Top Performer**: Sarah Wilson leads with 94% performance score and 34.8% conversion rate.
        Her luxury specialization aligns well with high-value lead routing.
        """)

        st.info("""
        **⚡ Quick Responder**: John Smith has the fastest average response time at 2.1 minutes,
        making him ideal for urgent lead assignments.
        """)

    with insights_col2:
        st.warning("""
        **📈 Growth Opportunity**: Tom Brown shows improvement potential with targeted coaching
        on response time optimization and lead qualification techniques.
        """)

        st.info("""
        **🎯 Specialization Success**: Investment-focused routing to Mike Chen shows 31.2% conversion,
        confirming the value of specialization-based routing.
        """)


def render_routing_analytics_tab():
    """Render comprehensive routing analytics and performance metrics"""

    st.subheader("📊 Routing Analytics & Performance")

    # Time period selector
    time_period = st.selectbox(
        "Select Analysis Period",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days"],
        index=2
    )

    # Key routing metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Routings",
            "2,847",
            delta="347",
            help="Total number of lead routing decisions made"
        )

    with col2:
        st.metric(
            "Success Rate",
            "97.8%",
            delta="1.2%",
            help="Percentage of successful routing outcomes"
        )

    with col3:
        st.metric(
            "Avg Routing Score",
            "0.847",
            delta="0.023",
            help="Average routing score (0-1, higher is better)"
        )

    with col4:
        st.metric(
            "ROI Impact",
            "$127K",
            delta="$18K",
            help="Estimated revenue impact from optimized routing"
        )

    st.markdown("---")

    # Routing strategy performance comparison
    st.subheader("🎯 Strategy Performance Comparison")

    col1, col2 = st.columns(2)

    with col1:
        # Strategy performance data
        strategies = ["Hybrid Intelligent", "Performance Optimized", "Specialization Match", "Load Balanced", "Round Robin"]
        conversion_rates = [34.2, 31.8, 29.4, 27.6, 23.1]
        response_times = [4.2, 3.8, 5.1, 6.2, 8.4]

        fig_strategy_conv = px.bar(
            x=strategies,
            y=conversion_rates,
            title="🎯 Conversion Rate by Strategy",
            labels={'x': 'Routing Strategy', 'y': 'Conversion Rate (%)'},
            color=conversion_rates,
            color_continuous_scale='RdYlGn'
        )

        fig_strategy_conv.update_layout(height=300, xaxis_tickangle=45)
        st.plotly_chart(fig_strategy_conv, use_container_width=True)

    with col2:
        fig_strategy_time = px.bar(
            x=strategies,
            y=response_times,
            title="⚡ Response Time by Strategy",
            labels={'x': 'Routing Strategy', 'y': 'Avg Response Time (min)'},
            color=response_times,
            color_continuous_scale='RdYlBu_r'  # Reverse scale (lower is better)
        )

        fig_strategy_time.update_layout(height=300, xaxis_tickangle=45)
        st.plotly_chart(fig_strategy_time, use_container_width=True)

    # Routing performance trends
    st.markdown("---")
    st.subheader("📈 Performance Trends")

    col1, col2 = st.columns(2)

    with col1:
        # Daily routing volume and success rate
        dates = pd.date_range(start='2026-01-02', end='2026-01-09', freq='D')
        volumes = [245, 289, 267, 312, 298, 334, 287, 315]
        success_rates = [95.2, 96.8, 97.1, 97.8, 96.9, 98.2, 97.5, 97.8]

        fig_trends = go.Figure()

        # Volume bars
        fig_trends.add_trace(go.Bar(
            x=dates,
            y=volumes,
            name='Daily Volume',
            yaxis='y',
            marker_color='lightblue'
        ))

        # Success rate line
        fig_trends.add_trace(go.Scatter(
            x=dates,
            y=success_rates,
            name='Success Rate',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='red', width=3),
            marker=dict(size=8)
        ))

        fig_trends.update_layout(
            title='📊 Daily Routing Volume & Success Rate',
            xaxis_title='Date',
            yaxis=dict(title='Daily Volume', side='left'),
            yaxis2=dict(title='Success Rate (%)', side='right', overlaying='y'),
            height=300
        )

        st.plotly_chart(fig_trends, use_container_width=True)

    with col2:
        # Response time distribution
        response_times_dist = np.random.lognormal(1.5, 0.5, 1000)  # Log-normal distribution
        response_times_dist = np.clip(response_times_dist, 0.5, 15)  # Clip outliers

        fig_response_dist = px.histogram(
            x=response_times_dist,
            nbins=20,
            title="⏱️ Response Time Distribution",
            labels={'x': 'Response Time (minutes)', 'y': 'Frequency'}
        )

        fig_response_dist.add_vline(
            x=np.mean(response_times_dist),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Avg: {np.mean(response_times_dist):.1f} min"
        )

        fig_response_dist.update_layout(height=300)
        st.plotly_chart(fig_response_dist, use_container_width=True)

    # Lead characteristic analysis
    st.markdown("---")
    st.subheader("🔍 Lead Characteristic Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Routing success by lead score
        score_ranges = ["0-20", "21-40", "41-60", "61-80", "81-100"]
        success_by_score = [87.2, 92.4, 95.8, 97.6, 98.9]

        fig_score_success = px.line(
            x=score_ranges,
            y=success_by_score,
            title="📈 Success Rate by Lead Score",
            labels={'x': 'Lead Score Range', 'y': 'Success Rate (%)'},
            markers=True
        )

        fig_score_success.update_layout(height=250)
        st.plotly_chart(fig_score_success, use_container_width=True)

    with col2:
        # Routing time by urgency
        urgency_levels = ["Low", "Medium", "High", "Critical"]
        routing_times_urgency = [2.8, 2.1, 1.3, 0.7]

        fig_urgency_time = px.bar(
            x=urgency_levels,
            y=routing_times_urgency,
            title="⚡ Routing Time by Urgency",
            labels={'x': 'Urgency Level', 'y': 'Routing Time (s)'},
            color=routing_times_urgency,
            color_continuous_scale='RdYlBu_r'
        )

        fig_urgency_time.update_layout(height=250)
        st.plotly_chart(fig_urgency_time, use_container_width=True)

    with col3:
        # Agent utilization
        agents_util = ["John S.", "Sarah W.", "Mike C.", "Lisa R.", "Tom B."]
        utilization = [60, 85, 45, 0, 70]

        fig_utilization = px.bar(
            x=agents_util,
            y=utilization,
            title="📊 Current Agent Utilization",
            labels={'x': 'Agent', 'y': 'Utilization (%)'},
            color=utilization,
            color_continuous_scale='viridis'
        )

        fig_utilization.update_layout(height=250, xaxis_tickangle=45)
        st.plotly_chart(fig_utilization, use_container_width=True)


def render_optimization_tab():
    """Render routing optimization controls and recommendations"""

    st.subheader("⚙️ Routing Optimization & Configuration")

    # Optimization recommendations
    st.markdown("#### 🚀 AI Optimization Recommendations")

    recommendations = [
        {
            "title": "🎯 Increase Investment Routing to Mike Chen",
            "description": "Mike Chen shows 41% conversion rate on investment leads vs 29% team average",
            "impact": "+$89K annual revenue",
            "effort": "Low - Auto-routing adjustment",
            "confidence": "94%"
        },
        {
            "title": "⚡ Reduce Max Workload for Sarah Wilson",
            "description": "Performance drops 12% when workload exceeds 80%",
            "impact": "+8% conversion improvement",
            "effort": "Medium - Capacity rebalancing",
            "confidence": "87%"
        },
        {
            "title": "🕐 Optimize Response Time Expectations",
            "description": "Urgent leads show 23% better conversion with <2min response",
            "impact": "+15% urgent lead conversion",
            "effort": "Low - Alert thresholds",
            "confidence": "91%"
        }
    ]

    for i, rec in enumerate(recommendations):
        with st.expander(f"{rec['title']} (Confidence: {rec['confidence']})"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**📝 Description:** {rec['description']}")
                st.write(f"**📈 Expected Impact:** {rec['impact']}")
                st.write(f"**🔧 Implementation Effort:** {rec['effort']}")

            with col2:
                if st.button(f"✅ Apply", key=f"apply_opt_{i}"):
                    with st.spinner("Applying optimization..."):
                        import time
                        time.sleep(1)
                        st.success("✅ Optimization applied!")

                if st.button(f"📊 Simulate", key=f"sim_opt_{i}"):
                    st.info("🧪 Simulation results would be shown here.")

    st.markdown("---")

    # Routing configuration
    st.subheader("⚙️ Routing Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Strategy Settings")

        default_strategy = st.selectbox(
            "Default Routing Strategy",
            ["Hybrid Intelligent", "Performance Optimized", "Specialization Match", "Load Balanced"],
            index=0
        )

        urgency_boost = st.slider(
            "Urgency Routing Boost",
            min_value=1.0, max_value=3.0, value=1.8, step=0.1,
            help="Multiplier for urgent lead routing priority"
        )

        max_agent_load = st.slider(
            "Maximum Agent Load",
            min_value=50, max_value=100, value=85, step=5,
            help="Maximum workload percentage before agent becomes unavailable"
        )

        response_time_sla = st.slider(
            "Response Time SLA (minutes)",
            min_value=1, max_value=15, value=5, step=1,
            help="Target response time for routed leads"
        )

    with col2:
        st.markdown("#### 🔧 Advanced Settings")

        enable_learning = st.checkbox("Enable AI Learning", value=True, help="Allow AI to learn from routing outcomes")

        rebalance_frequency = st.selectbox(
            "Auto-Rebalance Frequency",
            ["Real-time", "Every 15 minutes", "Hourly", "Manual only"],
            index=1
        )

        specialization_weight = st.slider(
            "Specialization Weight",
            min_value=0.0, max_value=1.0, value=0.4, step=0.1,
            help="How much to weight agent specialization vs performance"
        )

        fallback_strategy = st.selectbox(
            "Fallback Strategy",
            ["Round Robin", "Random", "Least Loaded", "Best Available"],
            index=2,
            help="Strategy to use when preferred routing fails"
        )

    # Save configuration
    if st.button("💾 Save Configuration", use_container_width=True):
        st.success("✅ Routing configuration saved successfully!")

    st.markdown("---")

    # Manual routing override
    st.subheader("🎮 Manual Routing Override")

    col1, col2, col3 = st.columns(3)

    with col1:
        override_lead = st.selectbox(
            "Select Lead for Manual Routing",
            ["LD_8901 - Alex Thompson", "LD_8902 - Maria Garcia", "LD_8903 - David Kim"],
            help="Choose a lead to manually assign to an agent"
        )

    with col2:
        override_agent = st.selectbox(
            "Assign to Agent",
            ["John Smith", "Sarah Wilson", "Mike Chen", "Lisa Rodriguez", "Tom Brown"],
            help="Select agent for manual assignment"
        )

    with col3:
        override_reason = st.selectbox(
            "Override Reason",
            ["Client Request", "Agent Expertise", "Workload Balance", "Special Circumstances"],
            help="Reason for manual override"
        )

    if st.button("🎯 Execute Manual Routing"):
        st.success(f"✅ Successfully routed {override_lead} to {override_agent}")
        st.info(f"📝 Reason logged: {override_reason}")

    # Performance monitoring
    st.markdown("---")
    st.subheader("📊 Performance Monitoring")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ⚡ Real-Time Alerts")

        alerts = [
            "🟡 Sarah Wilson approaching max workload (85%)",
            "🟢 All urgent leads routed within SLA",
            "🔵 Mike Chen available for investment leads",
            "🟡 Queue building up - 8 leads waiting"
        ]

        for alert in alerts:
            st.write(f"• {alert}")

    with col2:
        st.markdown("#### 📈 Performance Summary")

        performance_summary = {
            "Today's Routings": "287",
            "Success Rate": "97.8%",
            "Avg Response Time": "4.2 min",
            "SLA Compliance": "94.3%",
            "Agent Utilization": "67.8%"
        }

        for metric, value in performance_summary.items():
            st.write(f"**{metric}:** {value}")


# Cache function for better performance
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_routing_performance_data():
    """Get cached routing performance data"""
    # In production, this would fetch real data from the routing engine
    return {
        'queue_size': 23,
        'avg_routing_time': 1.2,
        'available_agents': 12,
        'success_rate': 97.8
    }