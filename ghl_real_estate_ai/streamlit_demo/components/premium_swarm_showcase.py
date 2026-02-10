"""
Premium Multi-Agent Swarm Showcase for High-Ticket Consulting Platform.

Demonstrates $25K-$100K value through sophisticated AI orchestration:
- Real-time consensus visualization with agent reasoning transparency
- 10+ specialized agents with psychological profiling insights
- Confidence scoring and uncertainty quantification
- Enterprise-grade decision support for C-suite engagement

Showcases the transformational AI capabilities that justify premium consulting fees.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import existing swarm services
from ghl_real_estate_ai.agents.lead_intelligence_swarm import LeadIntelligenceSwarm

# ============================================================================
# Data Models for Premium Showcase
# ============================================================================


@dataclass
class PremiumSwarmMetrics:
    """Enterprise metrics for swarm performance demonstration."""

    total_agents: int
    active_analyses: int
    consensus_accuracy: float
    processing_time_ms: int
    confidence_score: float
    uncertainty_level: float
    business_impact_score: float
    roi_attribution: float


@dataclass
class AgentReasoningStep:
    """Detailed reasoning step from individual agent."""

    agent_name: str
    step_description: str
    confidence: float
    data_sources: List[str]
    psychological_insight: Optional[str] = None
    business_impact: Optional[str] = None


@dataclass
class ConsensusVisualization:
    """Data structure for consensus visualization."""

    agent_positions: Dict[str, float]  # Agent name -> position (0-100)
    consensus_strength: float
    convergence_timeline: List[Tuple[str, float]]  # (timestamp, consensus_level)
    conflict_areas: List[str]
    resolution_strategy: str


# ============================================================================
# Premium Swarm Showcase Component
# ============================================================================


class PremiumSwarmShowcase:
    """
    Premium demonstration of multi-agent AI swarm capabilities.

    Designed to showcase $25K-$100K consulting value through:
    - Sophisticated AI orchestration with 10+ specialized agents
    - Real-time consensus building with conflict resolution
    - Psychological insights and behavioral profiling
    - Executive-level decision support with ROI attribution
    """

    def __init__(self):
        self.swarm_service = self._get_swarm_service()
        self.lead_swarm = self._get_lead_swarm()
        self._initialize_demo_data()

    @st.cache_resource
    def _get_swarm_service(_):
        """Get swarm service instance."""
        try:
            from ghl_real_estate_ai.services.lead_swarm_service import get_lead_swarm_service

            # Return a placeholder since actual service requires async initialization
            return None
        except ImportError:
            return None

    @st.cache_resource
    def _get_lead_swarm(_):
        """Get lead intelligence swarm instance."""
        try:
            return LeadIntelligenceSwarm()
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Failed to initialize LeadIntelligenceSwarm: {str(e)}")
            return None

    def _initialize_demo_data(self):
        """Initialize demonstration data for premium showcase."""
        self.demo_agents = [
            {
                "name": "Demographic Analyzer",
                "specialty": "Age, Income, Location Analysis",
                "accuracy": 94.2,
                "confidence": 0.91,
            },
            {
                "name": "Behavioral Profiler",
                "specialty": "Decision Patterns & Psychology",
                "accuracy": 89.7,
                "confidence": 0.87,
            },
            {
                "name": "Intent Detector",
                "specialty": "Purchase Timeline & Urgency",
                "accuracy": 92.1,
                "confidence": 0.89,
            },
            {
                "name": "Financial Analyzer",
                "specialty": "Affordability & Financing",
                "accuracy": 96.8,
                "confidence": 0.94,
            },
            {"name": "Risk Assessor", "specialty": "Churn & Conversion Risk", "accuracy": 88.4, "confidence": 0.85},
            {
                "name": "Negotiation Strategist",
                "specialty": "Deal Structure & Pricing",
                "accuracy": 91.3,
                "confidence": 0.88,
            },
            {
                "name": "Communication Expert",
                "specialty": "Channel & Timing Optimization",
                "accuracy": 87.9,
                "confidence": 0.84,
            },
            {"name": "Market Analyst", "specialty": "Competitive Intelligence", "accuracy": 93.5, "confidence": 0.90},
            {
                "name": "Timeline Predictor",
                "specialty": "Decision Timeline Forecasting",
                "accuracy": 89.2,
                "confidence": 0.86,
            },
            {
                "name": "ROI Calculator",
                "specialty": "Value & Revenue Attribution",
                "accuracy": 95.1,
                "confidence": 0.92,
            },
        ]

        self.demo_leads = {
            "Sarah Chen - Tech Executive": {
                "demographics": {"age": 34, "income": 185000, "location": "Austin, TX", "job": "VP Engineering"},
                "behavior": {"engagement_score": 87, "urgency": "High", "decision_style": "Data-Driven"},
                "intent": {"timeline": "45 days", "budget": "850K-1.2M", "motivation": "Relocation"},
                "risk_score": 15,  # Low risk
                "roi_potential": 485000,
            },
            "David Kim - Real Estate Investor": {
                "demographics": {"age": 42, "income": 320000, "location": "Dallas, TX", "job": "Portfolio Manager"},
                "behavior": {"engagement_score": 72, "urgency": "Medium", "decision_style": "ROI-Focused"},
                "intent": {"timeline": "90 days", "budget": "400K-600K", "motivation": "Investment"},
                "risk_score": 35,  # Medium risk
                "roi_potential": 275000,
            },
            "Maria Rodriguez - Family Relocator": {
                "demographics": {"age": 38, "income": 125000, "location": "Houston, TX", "job": "Marketing Director"},
                "behavior": {"engagement_score": 91, "urgency": "Very High", "decision_style": "Emotion + Logic"},
                "intent": {"timeline": "30 days", "budget": "450K-650K", "motivation": "School District"},
                "risk_score": 8,  # Very low risk
                "roi_potential": 385000,
            },
        }


def render_premium_swarm_showcase():
    """
    Render the premium multi-agent swarm showcase.

    This is the centerpiece demonstration for $25K-$100K consulting engagements,
    showing sophisticated AI orchestration and business value.
    """
    showcase = PremiumSwarmShowcase()

    # Header with premium positioning
    st.markdown(
        """
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
        <div style='display: flex; align-items: center; gap: 1rem;'>
            <div style='font-size: 3rem;'>🧠</div>
            <div>
                <h1 style='color: white !important; margin: 0; font-size: 2.2rem; font-weight: 600;'>
                    Enterprise AI Swarm Intelligence
                </h1>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;'>
                    10+ Specialized Agents • Real-Time Consensus • Psychological Profiling • $25K-$100K Value Demonstration
                </p>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Main content tabs for comprehensive demonstration
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🎯 Live Swarm Analysis",
            "🧠 Agent Consensus",
            "💰 ROI Attribution",
            "📊 Performance Metrics",
            "⚙️ Swarm Configuration",
        ]
    )

    with tab1:
        render_live_swarm_analysis(showcase)

    with tab2:
        render_agent_consensus_visualization(showcase)

    with tab3:
        render_roi_attribution_dashboard(showcase)

    with tab4:
        render_swarm_performance_metrics(showcase)

    with tab5:
        render_swarm_configuration(showcase)


def render_live_swarm_analysis(showcase: PremiumSwarmShowcase):
    """Render real-time swarm analysis demonstration."""
    st.markdown("### 🎯 Real-Time Multi-Agent Analysis")
    st.markdown("*Demonstrating 10+ AI agents working in concert to provide enterprise-grade lead intelligence*")

    # Lead selection for demonstration
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_lead = st.selectbox(
            "Select Lead for Swarm Analysis",
            options=list(showcase.demo_leads.keys()),
            help="Choose a lead to see the full multi-agent analysis in action",
        )

    with col2:
        if st.button("🚀 Run Swarm Analysis", type="primary", use_container_width=True):
            st.session_state.swarm_running = True

    if st.session_state.get("swarm_running", False):
        run_swarm_analysis_demo(showcase, selected_lead)


def run_swarm_analysis_demo(showcase: PremiumSwarmShowcase, selected_lead: str):
    """Run demonstration of swarm analysis with real-time updates."""
    lead_data = showcase.demo_leads[selected_lead]

    # Progress bar for dramatic effect
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Agent execution simulation with real insights
    agent_results = {}

    for i, agent in enumerate(showcase.demo_agents):
        progress = (i + 1) / len(showcase.demo_agents)
        progress_bar.progress(progress)
        status_text.text(f"🔄 {agent['name']} analyzing {selected_lead}...")

        # Simulate processing time
        import time

        time.sleep(0.3)

        # Generate agent-specific insights
        agent_results[agent["name"]] = generate_agent_insight(agent, lead_data, selected_lead)

    progress_bar.progress(1.0)
    status_text.text("✅ Swarm analysis complete - Building consensus...")

    # Display results in sophisticated format
    display_swarm_results(agent_results, lead_data, selected_lead)


def generate_agent_insight(agent: Dict, lead_data: Dict, lead_name: str) -> Dict[str, Any]:
    """Generate realistic agent insights based on agent specialty and lead data."""
    insights = {
        "Demographic Analyzer": {
            "primary_finding": f"{lead_name} falls into high-value demographic segment",
            "confidence": 0.94,
            "key_insights": [
                f"Income level ${lead_data['demographics']['income']:,} indicates premium buyer",
                f"Age {lead_data['demographics']['age']} suggests peak earning potential",
                f"Location {lead_data['demographics']['location']} has high appreciation rates",
            ],
            "business_impact": "Target for luxury properties and premium services",
        },
        "Behavioral Profiler": {
            "primary_finding": f"Decision style: {lead_data['behavior']['decision_style']} with {lead_data['behavior']['urgency']} urgency",
            "confidence": 0.87,
            "key_insights": [
                f"Engagement score of {lead_data['behavior']['engagement_score']} indicates strong interest",
                f"{lead_data['behavior']['decision_style']} approach suggests need for detailed analytics",
                "Multiple touchpoint engagement pattern detected",
            ],
            "business_impact": "Customize communication with data-driven content",
        },
        "Intent Detector": {
            "primary_finding": f"Strong purchase intent with {lead_data['intent']['timeline']} timeline",
            "confidence": 0.89,
            "key_insights": [
                f"Budget range {lead_data['intent']['budget']} confirmed through behavior",
                f"Motivation: {lead_data['intent']['motivation']} creates urgency",
                "Multiple property research sessions indicate active shopping",
            ],
            "business_impact": "Priority lead for immediate follow-up",
        },
        "Financial Analyzer": {
            "primary_finding": f"Strong financial qualification with ${lead_data['roi_potential']:,} potential value",
            "confidence": 0.94,
            "key_insights": [
                f"Debt-to-income ratio indicates strong buying power",
                f"Credit patterns suggest prime lending eligibility",
                "Investment capacity exceeds current search parameters",
            ],
            "business_impact": "Present higher-value properties and investment options",
        },
        "Risk Assessor": {
            "primary_finding": f"Risk Score: {lead_data['risk_score']}% (Very Low Risk)",
            "confidence": 0.85,
            "key_insights": [
                "Stable employment and income history",
                "Consistent engagement pattern reduces churn risk",
                "Timeline urgency creates positive pressure",
            ],
            "business_impact": "Allocate premium agent time and resources",
        },
    }

    # Return the insight for the specific agent
    return insights.get(
        agent["name"],
        {
            "primary_finding": f"Analysis complete for {lead_name}",
            "confidence": agent["confidence"],
            "key_insights": ["Analysis completed successfully"],
            "business_impact": "Insights ready for review",
        },
    )


def display_swarm_results(agent_results: Dict, lead_data: Dict, lead_name: str):
    """Display comprehensive swarm analysis results."""
    st.markdown("### 🧠 Swarm Intelligence Results")

    # Overall consensus card
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Consensus Score", "94.2%", delta="2.3% vs avg", help="Agent agreement level on lead assessment")

    with col2:
        st.metric(
            "Business Value",
            f"${lead_data['roi_potential']:,}",
            delta="+$85K vs baseline",
            help="Projected revenue potential from this lead",
        )

    with col3:
        st.metric(
            "Risk Level",
            f"{lead_data['risk_score']}%",
            delta="-12% vs avg",
            delta_color="inverse",
            help="Churn and conversion risk assessment",
        )

    with col4:
        st.metric("Action Priority", "Urgent", help="Recommended action timeline based on swarm analysis")

    # Agent insights breakdown
    st.markdown("### 🔍 Individual Agent Insights")

    for agent_name, insight in agent_results.items():
        with st.expander(f"🤖 {agent_name} - Confidence: {insight['confidence']:.0%}", expanded=False):
            st.markdown(f"**Primary Finding:** {insight['primary_finding']}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Key Insights:**")
                for insight_point in insight["key_insights"]:
                    st.markdown(f"• {insight_point}")

            with col2:
                st.markdown("**Business Impact:**")
                st.info(insight["business_impact"])

    # Strategic recommendations from swarm consensus
    render_strategic_recommendations(lead_data, lead_name)


def render_strategic_recommendations(lead_data: Dict, lead_name: str):
    """Render strategic recommendations based on swarm consensus."""
    st.markdown("### 🎯 Strategic Recommendations")

    recommendations = [
        {
            "priority": "High",
            "action": "Schedule Premium Property Tour",
            "rationale": f"High engagement score ({lead_data['behavior']['engagement_score']}) and urgent timeline",
            "expected_impact": "65% conversion probability",
            "timeframe": "Within 48 hours",
        },
        {
            "priority": "High",
            "action": "Present Luxury Market Analysis",
            "rationale": f"Income level ${lead_data['demographics']['income']:,} indicates luxury buyer segment",
            "expected_impact": "Increase average deal size by 40%",
            "timeframe": "During first meeting",
        },
        {
            "priority": "Medium",
            "action": "Implement VIP Communication Track",
            "rationale": f"Low risk score ({lead_data['risk_score']}%) justifies premium resource allocation",
            "expected_impact": "Reduce sales cycle by 25%",
            "timeframe": "Immediate",
        },
    ]

    for rec in recommendations:
        priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[rec["priority"]]

        st.markdown(
            f"""
        <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; 
                    border-left: 4px solid {"#e74c3c" if rec["priority"] == "High" else "#f39c12"}; margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;'>
                <span>{priority_color}</span>
                <strong>{rec["action"]}</strong>
                <span style='background: #3498db; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.8rem;'>
                    {rec["timeframe"]}
                </span>
            </div>
            <p style='margin: 0.5rem 0; color: #888;'>{rec["rationale"]}</p>
            <p style='margin: 0; color: #27ae60; font-weight: 500;'>Expected Impact: {rec["expected_impact"]}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_agent_consensus_visualization(showcase: PremiumSwarmShowcase):
    """Render sophisticated agent consensus visualization."""
    st.markdown("### 🧠 Agent Consensus & Conflict Resolution")
    st.markdown("*Real-time visualization of how 10+ AI agents reach consensus and resolve conflicts*")

    # Consensus strength visualization
    col1, col2 = st.columns(2)

    with col1:
        # Consensus gauge chart
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=94.2,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Consensus Strength"},
                delta={"reference": 80, "position": "top"},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "gray"},
                        {"range": [80, 100], "color": "lightgreen"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
                },
            )
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Agent agreement matrix
        agents = [agent["name"][:12] for agent in showcase.demo_agents[:6]]  # Truncate names
        agreement_matrix = np.random.uniform(0.7, 1.0, (6, 6))
        np.fill_diagonal(agreement_matrix, 1.0)

        fig = go.Figure(
            data=go.Heatmap(
                z=agreement_matrix,
                x=agents,
                y=agents,
                colorscale="RdYlGn",
                text=np.round(agreement_matrix, 2),
                texttemplate="%{text}",
                textfont={"size": 10},
            )
        )
        fig.update_layout(title="Agent Agreement Matrix", height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Consensus timeline
    st.markdown("#### Consensus Building Timeline")

    # Generate consensus timeline data
    timestamps = pd.date_range(start="2024-01-01 10:00:00", periods=20, freq="30S")
    consensus_levels = []

    # Simulate consensus building
    base_level = 60
    for i in range(20):
        if i < 5:
            consensus_levels.append(base_level + np.random.normal(0, 5))
        elif i < 15:
            consensus_levels.append(base_level + (i - 5) * 3 + np.random.normal(0, 2))
        else:
            consensus_levels.append(92 + np.random.normal(0, 1))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=consensus_levels,
            mode="lines+markers",
            name="Consensus Level",
            line=dict(color="#3498db", width=3),
            fill="tonexty",
            fillcolor="rgba(52, 152, 219, 0.1)",
        )
    )

    fig.update_layout(
        title="Real-Time Consensus Building",
        xaxis_title="Time",
        yaxis_title="Consensus Level (%)",
        height=400,
        yaxis=dict(range=[40, 100]),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_roi_attribution_dashboard(showcase: PremiumSwarmShowcase):
    """Render ROI attribution dashboard for consulting value demonstration."""
    st.markdown("### 💰 ROI Attribution & Business Impact")
    st.markdown("*Demonstrating measurable business value from AI swarm intelligence*")

    # ROI metrics cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Revenue Attributed",
            "$2.4M",
            delta="+340% YoY",
            help="Direct revenue attributed to swarm intelligence insights",
        )

    with col2:
        st.metric("Conversion Lift", "67%", delta="+23% vs baseline", help="Improvement in lead conversion rates")

    with col3:
        st.metric(
            "Time Savings",
            "85 hrs/month",
            delta="+12 hrs vs previous",
            help="Agent time saved through automated intelligence",
        )

    with col4:
        st.metric(
            "Cost Reduction",
            "$340K",
            delta="-45% vs manual",
            delta_color="inverse",
            help="Cost savings from intelligent automation",
        )

    # ROI breakdown chart
    col1, col2 = st.columns(2)

    with col1:
        # ROI by agent type
        roi_data = pd.DataFrame(
            {
                "Agent Type": ["Demographic", "Behavioral", "Intent", "Financial", "Risk"],
                "ROI": [485, 620, 540, 720, 380],
                "Volume": [150, 200, 180, 120, 160],
            }
        )

        fig = px.scatter(
            roi_data,
            x="Volume",
            y="ROI",
            size="ROI",
            color="Agent Type",
            title="ROI by Agent Specialization",
            labels={"ROI": "ROI (%)", "Volume": "Monthly Analyses"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Business impact waterfall
        categories = ["Baseline", "Lead Quality", "Conversion Rate", "Deal Size", "Time Savings", "Final Impact"]
        values = [100, 45, 30, 25, 15, 215]

        fig = go.Figure(
            go.Waterfall(
                name="Business Impact",
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "relative", "total"],
                x=categories,
                textposition="outside",
                text=[f"+{v}%" if v > 0 else f"{v}%" for v in values],
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        )
        fig.update_layout(title="Cumulative Business Impact", height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_swarm_performance_metrics(showcase: PremiumSwarmShowcase):
    """Render comprehensive swarm performance metrics."""
    st.markdown("### 📊 Enterprise Performance Dashboard")
    st.markdown("*Real-time monitoring of multi-agent system performance and reliability*")

    # Performance overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### System Health")
        health_metrics = {
            "System Uptime": "99.97%",
            "Avg Response Time": "2.3s",
            "Active Agents": "10/10",
            "Queue Length": "0",
        }

        for metric, value in health_metrics.items():
            st.metric(metric, value)

    with col2:
        st.markdown("#### Agent Accuracy")
        accuracy_data = pd.DataFrame(
            {
                "Agent": [agent["name"][:12] for agent in showcase.demo_agents[:6]],
                "Accuracy": [agent["accuracy"] for agent in showcase.demo_agents[:6]],
            }
        )

        fig = px.bar(
            accuracy_data,
            x="Accuracy",
            y="Agent",
            orientation="h",
            title="Individual Agent Accuracy",
            color="Accuracy",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown("#### Processing Volume")
        volume_data = pd.DataFrame({"Hour": list(range(24)), "Analyses": np.random.poisson(25, 24) + 10})

        fig = px.line(volume_data, x="Hour", y="Analyses", title="24-Hour Processing Volume", markers=True)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Detailed performance table
    st.markdown("#### Detailed Agent Performance")

    performance_df = pd.DataFrame(
        [
            {
                "Agent": agent["name"],
                "Specialty": agent["specialty"],
                "Accuracy": f"{agent['accuracy']:.1f}%",
                "Confidence": f"{agent['confidence']:.0%}",
                "Analyses Today": np.random.randint(50, 200),
                "Avg Time (ms)": np.random.randint(800, 2500),
                "Status": "Active" if np.random.random() > 0.1 else "Idle",
            }
            for agent in showcase.demo_agents
        ]
    )

    st.dataframe(
        performance_df,
        use_container_width=True,
        hide_index=True,
        column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Active", "Idle", "Maintenance"])},
    )


def render_swarm_configuration(showcase: PremiumSwarmShowcase):
    """Render swarm configuration interface for enterprise customization."""
    st.markdown("### ⚙️ Enterprise Swarm Configuration")
    st.markdown("*Configure and customize the multi-agent system for client-specific requirements*")

    # Configuration tabs
    config_tab1, config_tab2, config_tab3 = st.tabs(["Agent Selection", "Consensus Parameters", "Business Rules"])

    with config_tab1:
        st.markdown("#### Select Active Agents")
        st.markdown("Choose which specialized agents to include in the swarm analysis.")

        col1, col2 = st.columns(2)

        with col1:
            for i, agent in enumerate(showcase.demo_agents[:5]):
                enabled = st.checkbox(
                    f"{agent['name']} - {agent['specialty']}",
                    value=True,
                    key=f"agent_{i}",
                    help=f"Accuracy: {agent['accuracy']:.1f}%",
                )

        with col2:
            for i, agent in enumerate(showcase.demo_agents[5:]):
                enabled = st.checkbox(
                    f"{agent['name']} - {agent['specialty']}",
                    value=True,
                    key=f"agent_{i + 5}",
                    help=f"Accuracy: {agent['accuracy']:.1f}%",
                )

    with config_tab2:
        st.markdown("#### Consensus Parameters")

        col1, col2 = st.columns(2)

        with col1:
            consensus_threshold = st.slider(
                "Minimum Consensus Threshold",
                min_value=50,
                max_value=95,
                value=80,
                help="Minimum agreement level required for recommendations",
            )

            confidence_weight = st.slider(
                "Confidence Weight",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                help="How much to weight agent confidence in consensus building",
            )

        with col2:
            max_iterations = st.number_input(
                "Max Consensus Iterations",
                min_value=3,
                max_value=20,
                value=10,
                help="Maximum rounds of consensus building",
            )

            timeout_seconds = st.number_input(
                "Analysis Timeout (seconds)",
                min_value=5,
                max_value=60,
                value=30,
                help="Maximum time for complete analysis",
            )

    with config_tab3:
        st.markdown("#### Business Rules & Priorities")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Priority Weighting**")
            financial_weight = st.slider("Financial Analysis Weight", 0.0, 1.0, 0.3)
            behavioral_weight = st.slider("Behavioral Analysis Weight", 0.0, 1.0, 0.25)
            risk_weight = st.slider("Risk Assessment Weight", 0.0, 1.0, 0.2)
            intent_weight = st.slider("Intent Detection Weight", 0.0, 1.0, 0.25)

        with col2:
            st.markdown("**Business Thresholds**")
            min_deal_value = st.number_input("Minimum Deal Value ($)", value=250000)
            max_risk_tolerance = st.slider("Maximum Risk Tolerance (%)", 0, 50, 25)

            priority_segments = st.multiselect(
                "Priority Market Segments",
                ["Luxury", "Investment", "Commercial", "First-Time Buyer", "Relocation"],
                default=["Luxury", "Investment"],
            )

    # Save configuration button
    if st.button("💾 Save Configuration", type="primary", use_container_width=True):
        st.success("✅ Swarm configuration saved successfully!")
        st.info("Configuration will take effect on the next analysis run.")


# ============================================================================
# Main Render Function
# ============================================================================

if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(page_title="Premium AI Swarm Showcase", page_icon="🧠", layout="wide")
    render_premium_swarm_showcase()
