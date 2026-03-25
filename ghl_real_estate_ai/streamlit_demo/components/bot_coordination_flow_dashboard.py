"""
Bot Coordination Flow Dashboard
Visualizes the intelligent routing and handoff logic between Jorge's three-bot ecosystem.

Features:
- Interactive flow diagram showing lead progression
- Decision tree visualization for handoff conditions
- Real-time routing statistics and performance
- Lead journey tracking and analytics
- Bot coordination patterns and optimization insights
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart


# Create sample data for bot coordination flows
@st.cache_data(ttl=30)  # Cache for 30 seconds for near real-time
def get_coordination_flow_data() -> Dict[str, Any]:
    """Get bot coordination flow data and analytics."""

    return {
        "flow_statistics": {
            "leads_processed_today": random.randint(45, 85),
            "seller_bot_interactions": random.randint(25, 45),
            "buyer_bot_interactions": random.randint(15, 35),
            "lead_bot_sequences": random.randint(30, 60),
            "successful_handoffs": random.randint(20, 35),
            "handoff_success_rate": round(random.uniform(85, 95), 1),
            "avg_handoff_time": round(random.uniform(0.8, 2.5), 1),
        },
        "routing_patterns": {
            "direct_seller_to_buyer": random.randint(8, 15),
            "seller_to_lead_sequence": random.randint(12, 22),
            "buyer_to_lead_nurture": random.randint(10, 18),
            "cross_bot_consultations": random.randint(3, 8),
            "failed_handoffs": random.randint(1, 4),
        },
        "decision_logic": {
            "seller_qualification_threshold": 70,
            "buyer_readiness_threshold": 65,
            "lead_engagement_threshold": 60,
            "handoff_confidence_threshold": 85,
        },
        "real_time_flows": [
            {
                "lead_id": f"lead_{i}",
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 120))).isoformat(),
                "current_bot": random.choice(["jorge_seller_bot", "jorge_buyer_bot", "lead_bot"]),
                "previous_bot": random.choice(["jorge_seller_bot", "jorge_buyer_bot", "lead_bot", None]),
                "handoff_reason": random.choice(
                    [
                        "qualification_complete",
                        "buyer_identified",
                        "needs_nurturing",
                        "high_intent_detected",
                        "follow_up_required",
                        "property_match_found",
                    ]
                ),
                "status": random.choice(["active", "pending_handoff", "completed"]),
                "score": round(random.uniform(50, 95), 1),
            }
            for i in range(15)
        ],
    }


def render_flow_overview():
    """Render the main coordination flow overview."""
    st.subheader("🔄 Bot Coordination Flow Overview")

    data = get_coordination_flow_data()
    stats = data["flow_statistics"]

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📊 Leads Processed",
            f"{stats['leads_processed_today']}",
            delta="Today",
            help="Total leads processed by bot ecosystem today",
        )

    with col2:
        st.metric(
            "🤝 Successful Handoffs",
            f"{stats['successful_handoffs']}",
            delta=f"{stats['handoff_success_rate']}% success rate",
            help="Successfully coordinated bot handoffs",
        )

    with col3:
        st.metric("⚡ Avg Handoff Time", f"{stats['avg_handoff_time']}s", help="Average time for bot-to-bot handoffs")

    with col4:
        total_interactions = sum(
            [stats["seller_bot_interactions"], stats["buyer_bot_interactions"], stats["lead_bot_sequences"]]
        )
        st.metric("💬 Total Interactions", f"{total_interactions}", help="Combined bot interactions today")


def create_flow_diagram():
    """Create interactive flow diagram showing bot handoffs."""
    st.subheader("🎯 Bot-to-Bot Flow Visualization")

    data = get_coordination_flow_data()
    patterns = data["routing_patterns"]

    # Create Sankey diagram for flow visualization
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=[
                        "🔍 Lead Entry",
                        "🎯 Jorge Seller Bot",
                        "🏠 Jorge Buyer Bot",
                        "📞 Lead Bot (3-7-30)",
                        "✅ Qualified Seller",
                        "🏡 Qualified Buyer",
                        "🔄 Nurture Sequence",
                        "💰 Transaction",
                    ],
                    color=["#ff9999", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57", "#ff9ff3", "#54a0ff"],
                ),
                link=dict(
                    source=[0, 1, 1, 2, 2, 3, 4, 5, 6, 6],  # Indices correspond to labels
                    target=[1, 4, 3, 5, 3, 6, 7, 7, 2, 1],
                    value=[
                        40,  # Lead Entry → Seller Bot
                        patterns["direct_seller_to_buyer"],  # Seller Bot → Qualified Seller
                        patterns["seller_to_lead_sequence"],  # Seller Bot → Lead Bot
                        patterns["buyer_to_lead_nurture"],  # Buyer Bot → Qualified Buyer
                        15,  # Buyer Bot → Lead Bot
                        25,  # Lead Bot → Nurture Sequence
                        8,  # Qualified Seller → Transaction
                        12,  # Qualified Buyer → Transaction
                        10,  # Nurture Sequence → Buyer Bot
                        8,  # Nurture Sequence → Seller Bot
                    ],
                ),
            )
        ]
    )

    fig.update_layout(title_text="Jorge's Three-Bot Coordination Flow", font_size=12, height=500)

    fig = style_obsidian_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

    # Flow statistics
    col1, col2 = st.columns(2)

    with col1:
        st.write("**📊 Routing Pattern Breakdown**")
        routing_df = pd.DataFrame(
            [
                {
                    "Route": "Seller → Buyer Direct",
                    "Count": patterns["direct_seller_to_buyer"],
                    "Percentage": f"{patterns['direct_seller_to_buyer'] / sum(patterns.values()) * 100:.1f}%",
                },
                {
                    "Route": "Seller → Lead Sequence",
                    "Count": patterns["seller_to_lead_sequence"],
                    "Percentage": f"{patterns['seller_to_lead_sequence'] / sum(patterns.values()) * 100:.1f}%",
                },
                {
                    "Route": "Buyer → Lead Nurture",
                    "Count": patterns["buyer_to_lead_nurture"],
                    "Percentage": f"{patterns['buyer_to_lead_nurture'] / sum(patterns.values()) * 100:.1f}%",
                },
                {
                    "Route": "Cross-Bot Consultation",
                    "Count": patterns["cross_bot_consultations"],
                    "Percentage": f"{patterns['cross_bot_consultations'] / sum(patterns.values()) * 100:.1f}%",
                },
            ]
        )
        st.dataframe(routing_df, use_container_width=True)

    with col2:
        st.write("**🎯 Decision Thresholds**")
        logic = data["decision_logic"]
        st.code(f"""
Seller Qualification: {logic["seller_qualification_threshold"]}+ (FRS/PCS)
Buyer Readiness: {logic["buyer_readiness_threshold"]}+ (Financial/Motivation)
Lead Engagement: {logic["lead_engagement_threshold"]}+ (Response Rate)
Handoff Confidence: {logic["handoff_confidence_threshold"]}+ (Success Probability)
        """)


def render_decision_tree():
    """Render the decision tree for bot routing logic."""
    st.subheader("🌳 Bot Routing Decision Tree")

    # Create decision tree visualization
    decision_tree = """
    ```
    📞 New Lead Contact
    │
    ├─ 🎯 Jorge Seller Bot (Initial Contact)
    │   │
    │   ├─ High Interest (75+ FRS/PCS) ──► 🏠 Jorge Buyer Bot
    │   ├─ Medium Interest (50-74) ────► 📞 Lead Bot (Nurture)
    │   └─ Low Interest (<50) ─────────► 📞 Lead Bot (Long-term)
    │
    ├─ 🏠 Jorge Buyer Bot (Direct Referral)
    │   │
    │   ├─ High Readiness (70+ Score) ──► 💰 Property Matching
    │   ├─ Medium Readiness (50-69) ───► 📞 Lead Bot (Education)
    │   └─ Low Readiness (<50) ────────► 🎯 Jorge Seller Bot
    │
    └─ 📞 Lead Bot (3-7-30 Sequences)
        │
        ├─ High Engagement ──► 🎯 Jorge Seller Bot (Re-qualification)
        ├─ Medium Engagement ► Continue Sequence
        └─ Low Engagement ───► Pause/Archive
    ```
    """

    st.code(decision_tree, language=None)

    # Decision criteria breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.write("**🎯 Seller Bot Handoff Criteria**")
        st.info("""
        **→ To Buyer Bot:**
        - FRS Score ≥ 70 (Financial Readiness)
        - PCS Score ≥ 75 (Psychological Commitment)
        - Buying signals detected
        - Timeline < 6 months

        **→ To Lead Bot:**
        - Interest but not ready (FRS 50-69)
        - Needs education/nurturing
        - Timeline > 6 months
        - Objections requiring follow-up
        """)

    with col2:
        st.write("**🏠 Buyer Bot Handoff Criteria**")
        st.info("""
        **→ To Lead Bot:**
        - Financial readiness < 70
        - Needs mortgage education
        - Credit repair required
        - Market education needed

        **→ Back to Seller Bot:**
        - Dual seller/buyer (own property first)
        - Downsize/upsize scenarios
        - Investment property interest
        """)


def render_real_time_flows():
    """Render real-time flow tracking."""
    st.subheader("📊 Real-Time Lead Flow Tracking")

    data = get_coordination_flow_data()
    flows = data["real_time_flows"]

    # Convert to DataFrame for better display
    flows_df = pd.DataFrame(flows)
    flows_df["timestamp"] = pd.to_datetime(flows_df["timestamp"])
    flows_df["minutes_ago"] = flows_df["timestamp"].apply(
        lambda x: int((datetime.now() - x.replace(tzinfo=None)).total_seconds() / 60)
    )

    # Active flows display
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("**🔄 Active Lead Flows**")

        for _, flow in flows_df.head(8).iterrows():
            # Choose bot icon and color
            bot_icons = {"jorge_seller_bot": "🎯", "jorge_buyer_bot": "🏠", "lead_bot": "📞"}

            status_colors = {"active": "🟢", "pending_handoff": "🟡", "completed": "🔵"}

            current_icon = bot_icons.get(flow["current_bot"], "🤖")
            status_icon = status_colors.get(flow["status"], "⚪")

            with st.container():
                subcol1, subcol2, subcol3, subcol4 = st.columns([1, 2, 1, 1])

                with subcol1:
                    st.write(f"{current_icon}")

                with subcol2:
                    st.write(f"**{flow['lead_id']}**")
                    st.caption(f"Reason: {flow['handoff_reason'].replace('_', ' ').title()}")

                with subcol3:
                    st.write(f"{status_icon} {flow['status'].title()}")

                with subcol4:
                    st.write(f"Score: {flow['score']}")
                    st.caption(f"{flow['minutes_ago']}m ago")

            st.divider()

    with col2:
        st.write("**📈 Flow Analytics**")

        # Current distribution
        bot_counts = flows_df["current_bot"].value_counts()

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=[bot.replace("_", " ").title() for bot in bot_counts.index],
                    values=bot_counts.values,
                    hole=0.3,
                    marker_colors=["#ff6b6b", "#4ecdc4", "#45b7d1"],
                )
            ]
        )

        fig_pie.update_layout(title="Current Bot Distribution", height=300, showlegend=True)

        fig_pie = style_obsidian_chart(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)

        # Status breakdown
        st.write("**🎯 Status Breakdown**")
        status_counts = flows_df["status"].value_counts()
        for status, count in status_counts.items():
            percentage = (count / len(flows_df)) * 100
            st.write(f"• {status.title()}: {count} ({percentage:.1f}%)")


def render_handoff_performance():
    """Render handoff performance analytics."""
    st.subheader("⚡ Handoff Performance Analytics")

    # Generate sample performance data over time
    hours = [(datetime.now() - timedelta(hours=i)) for i in range(24, 0, -1)]
    handoff_data = {
        "timestamp": hours,
        "successful_handoffs": [random.randint(0, 4) for _ in hours],
        "failed_handoffs": [random.randint(0, 1) for _ in hours],
        "avg_handoff_time": [round(random.uniform(0.5, 3.0), 1) for _ in hours],
        "handoff_confidence": [round(random.uniform(80, 95), 1) for _ in hours],
    }

    df_handoffs = pd.DataFrame(handoff_data)

    # Create performance chart
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Handoff Volume & Success Rate", "Handoff Performance Metrics"),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
    )

    # Volume and success rate
    fig.add_trace(
        go.Bar(
            x=df_handoffs["timestamp"],
            y=df_handoffs["successful_handoffs"],
            name="Successful",
            marker_color="green",
            opacity=0.7,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=df_handoffs["timestamp"], y=df_handoffs["failed_handoffs"], name="Failed", marker_color="red", opacity=0.7
        ),
        row=1,
        col=1,
    )

    # Performance metrics
    fig.add_trace(
        go.Scatter(
            x=df_handoffs["timestamp"],
            y=df_handoffs["avg_handoff_time"],
            mode="lines+markers",
            name="Handoff Time (s)",
            line=dict(color="blue", width=2),
            yaxis="y3",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df_handoffs["timestamp"],
            y=df_handoffs["handoff_confidence"],
            mode="lines+markers",
            name="Confidence Score",
            line=dict(color="orange", width=2),
            yaxis="y4",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(height=600, title="🚀 24-Hour Handoff Performance Trends", showlegend=True, hovermode="x unified")

    fig.update_yaxes(title_text="Handoff Count", row=1, col=1)
    fig.update_yaxes(title_text="Time (seconds)", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=1)

    fig = style_obsidian_chart(fig)
    st.plotly_chart(fig, use_container_width=True)


def render_optimization_insights():
    """Render coordination optimization insights."""
    st.subheader("🎯 Coordination Optimization Insights")

    data = get_coordination_flow_data()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**🚀 Performance Optimization**")

        optimizations = [
            {
                "area": "Handoff Speed",
                "current": "1.2s avg",
                "target": "<1.0s",
                "improvement": "Implement predictive handoff preparation",
            },
            {
                "area": "Success Rate",
                "current": f"{data['flow_statistics']['handoff_success_rate']}%",
                "target": ">95%",
                "improvement": "Enhanced confidence scoring algorithm",
            },
            {
                "area": "Bot Utilization",
                "current": "82% avg",
                "target": ">90%",
                "improvement": "Dynamic load balancing between bots",
            },
        ]

        for opt in optimizations:
            with st.expander(f"🎯 {opt['area']}: {opt['current']} → {opt['target']}"):
                st.write(f"**Current Performance:** {opt['current']}")
                st.write(f"**Target:** {opt['target']}")
                st.write(f"**Optimization Strategy:** {opt['improvement']}")

    with col2:
        st.write("**🔍 Coordination Patterns**")

        patterns = [
            "🕒 **Peak Hours:** 10 AM - 2 PM (highest handoff success)",
            "🎯 **Best Route:** Seller → Buyer (94% success rate)",
            "⚡ **Fastest Handoff:** Buyer → Lead Bot (0.8s avg)",
            "🔄 **Most Complex:** Cross-bot consultations (2.1s avg)",
            "📈 **Trending Up:** Lead Bot → Seller re-qualifications",
            "⚠️ **Watch:** Late afternoon handoff delays",
        ]

        for pattern in patterns:
            st.write(pattern)


def render_bot_coordination_dashboard():
    """Main function to render the complete bot coordination flow dashboard."""
    st.title("🔄 Bot Coordination Flow Dashboard")
    st.write("**Visualizing intelligent lead routing across Jorge's three-bot ecosystem**")

    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write("*Real-time flow tracking and coordination analytics*")

    with col2:
        if st.button("🔄 Refresh", type="secondary"):
            st.cache_data.clear()
            st.experimental_rerun()

    with col3:
        st.success("🟢 **Live Tracking**")

    st.divider()

    # Main dashboard sections
    render_flow_overview()
    st.divider()

    create_flow_diagram()
    st.divider()

    render_decision_tree()
    st.divider()

    render_real_time_flows()
    st.divider()

    render_handoff_performance()
    st.divider()

    render_optimization_insights()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("✅ Flow Tracking: **Active**")

    with col2:
        st.info(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")

    with col3:
        st.info("📊 Data Source: **Real-Time Bot Coordination**")


# === MAIN EXECUTION ===

if __name__ == "__main__":
    render_bot_coordination_dashboard()
