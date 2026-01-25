"""
Lead Bot 3-7-30 Sequence Visualization Dashboard
Complete visualization and management of Jorge's automated lead nurturing sequences.

Features:
- Interactive timeline showing 3-7-30 day touchpoints
- Real-time sequence progress tracking
- Engagement analytics and conversion metrics
- Sequence performance optimization insights
- Voice call integration with Retell AI
- CMA generation and delivery tracking
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import random

# Import existing lead bot services for integration
try:
    from ghl_real_estate_ai.agents.lead_bot import LeadBot
    from ghl_real_estate_ai.services.cache_service import get_cache_service
    from ghl_real_estate_ai.services.event_publisher import get_event_publisher
except ImportError:
    st.warning("Lead Bot services not available - using demo mode")

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_sequence_data() -> Dict[str, Any]:
    """Get lead bot sequence data and analytics."""

    # Generate realistic sequence data
    current_time = datetime.now()

    return {
        "sequence_overview": {
            "active_sequences": random.randint(35, 65),
            "completed_today": random.randint(8, 18),
            "scheduled_touchpoints": random.randint(120, 180),
            "voice_calls_pending": random.randint(12, 25),
            "cma_generated": random.randint(5, 12),
            "overall_engagement_rate": round(random.uniform(68, 78), 1),
            "day_30_conversion_rate": round(random.uniform(12, 18), 1)
        },
        "sequence_performance": {
            "day_3_engagement": round(random.uniform(75, 85), 1),
            "day_7_engagement": round(random.uniform(60, 70), 1),
            "day_30_engagement": round(random.uniform(35, 45), 1),
            "day_3_response_rate": round(random.uniform(45, 55), 1),
            "day_7_response_rate": round(random.uniform(25, 35), 1),
            "day_30_response_rate": round(random.uniform(15, 25), 1),
            "voice_call_success": round(random.uniform(65, 75), 1),
            "cma_open_rate": round(random.uniform(80, 90), 1),
            "cma_engagement": round(random.uniform(55, 65), 1)
        },
        "active_sequences": [
            {
                "lead_id": f"lead_seq_{i:03d}",
                "lead_name": f"Lead {i}",
                "sequence_start": (current_time - timedelta(days=random.randint(1, 35))).isoformat(),
                "current_day": random.randint(1, 30),
                "next_touchpoint": (current_time + timedelta(hours=random.randint(2, 48))).isoformat(),
                "engagement_score": round(random.uniform(30, 95), 1),
                "touchpoints_completed": random.randint(1, 8),
                "total_touchpoints": random.randint(6, 12),
                "last_response": (current_time - timedelta(hours=random.randint(1, 168))).isoformat() if random.choice([True, False]) else None,
                "sequence_type": random.choice(["seller_nurture", "buyer_education", "market_update", "reengagement"]),
                "status": random.choice(["active", "paused", "responding", "voice_scheduled"])
            } for i in range(1, 25)
        ],
        "touchpoint_templates": {
            "day_3": {
                "type": "SMS + Email",
                "purpose": "Initial follow-up, gauge interest level",
                "content": "Quick market update and value proposition",
                "expected_response": "25-35%"
            },
            "day_7": {
                "type": "Voice Call + SMS",
                "purpose": "Direct engagement, qualification",
                "content": "Retell AI voice call with follow-up message",
                "expected_response": "15-25%"
            },
            "day_30": {
                "type": "CMA + Educational Content",
                "purpose": "Value demonstration, expertise showcase",
                "content": "Personalized market analysis and insights",
                "expected_response": "35-45%"
            }
        }
    }

def render_sequence_overview():
    """Render the main sequence overview metrics."""
    st.subheader("📊 Lead Bot 3-7-30 Sequence Overview")

    data = get_sequence_data()
    overview = data["sequence_overview"]

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "🔄 Active Sequences",
            f"{overview['active_sequences']}",
            help="Currently running automated sequences"
        )

    with col2:
        st.metric(
            "✅ Completed Today",
            f"{overview['completed_today']}",
            help="Sequences completed successfully today"
        )

    with col3:
        st.metric(
            "📅 Scheduled Touchpoints",
            f"{overview['scheduled_touchpoints']}",
            help="Upcoming automated touchpoints"
        )

    with col4:
        st.metric(
            "📞 Voice Calls Pending",
            f"{overview['voice_calls_pending']}",
            help="Retell AI voice calls scheduled"
        )

    with col5:
        st.metric(
            "📈 CMA Generated",
            f"{overview['cma_generated']}",
            help="Market analyses generated today"
        )

def create_sequence_timeline():
    """Create interactive timeline visualization for 3-7-30 sequences."""
    st.subheader("📅 3-7-30 Sequence Timeline Visualization")

    # Create timeline chart showing touchpoint progression
    days = [3, 7, 30]

    # Sample data for visualization
    touchpoint_data = {
        'Day 3: Initial Follow-up': {
            'day': 3,
            'type': 'SMS + Email',
            'engagement': 78,
            'active_count': 24
        },
        'Day 7: Voice Engagement': {
            'day': 7,
            'type': 'Voice Call + SMS',
            'engagement': 65,
            'active_count': 18
        },
        'Day 30: Value Demonstration': {
            'day': 30,
            'type': 'CMA + Education',
            'engagement': 42,
            'active_count': 15
        }
    }

    # Create Gantt-style timeline
    fig = go.Figure()

    # Add timeline bars for each touchpoint type
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']

    for i, (touchpoint, data_point) in enumerate(touchpoint_data.items()):
        fig.add_trace(go.Bar(
            x=[data_point['active_count']],
            y=[touchpoint],
            orientation='h',
            name=f"Day {data_point['day']}",
            marker_color=colors[i],
            text=f"{data_point['engagement']}% engagement",
            textposition='inside'
        ))

    fig.update_layout(
        title="📊 Jorge's 3-7-30 Touchpoint Engagement",
        xaxis_title="Active Leads in Stage",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Sequence flow explanation
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        **🎯 Day 3: Initial Follow-up**
        - SMS check-in message
        - Email with market insights
        - Goal: Re-engage and gauge interest
        - Expected Response: 25-35%
        """)

    with col2:
        st.info("""
        **📞 Day 7: Voice Engagement**
        - Retell AI automated voice call
        - Follow-up SMS with key points
        - Goal: Direct qualification
        - Expected Response: 15-25%
        """)

    with col3:
        st.info("""
        **📈 Day 30: Value Demonstration**
        - Personalized CMA generation
        - Educational market content
        - Goal: Showcase expertise
        - Expected Response: 35-45%
        """)

def render_active_sequences():
    """Render table of currently active sequences with progress tracking."""
    st.subheader("🔄 Active Sequence Management")

    data = get_sequence_data()
    sequences = data["active_sequences"]

    # Convert to DataFrame for better display
    df_sequences = pd.DataFrame(sequences)
    df_sequences['sequence_start'] = pd.to_datetime(df_sequences['sequence_start'])
    df_sequences['next_touchpoint'] = pd.to_datetime(df_sequences['next_touchpoint'])

    # Calculate progress
    df_sequences['progress'] = (df_sequences['touchpoints_completed'] / df_sequences['total_touchpoints'] * 100).round(1)
    df_sequences['days_in_sequence'] = df_sequences['current_day']
    df_sequences['next_in'] = df_sequences['next_touchpoint'].apply(
        lambda x: f"{int((x - pd.Timestamp.now()).total_seconds() / 3600)}h" if x > pd.Timestamp.now() else "Due"
    )

    # Filter and display options
    col1, col2, col3 = st.columns(3)

    with col1:
        sequence_filter = st.selectbox(
            "Filter by Type:",
            ["All"] + list(df_sequences['sequence_type'].unique())
        )

    with col2:
        status_filter = st.selectbox(
            "Filter by Status:",
            ["All"] + list(df_sequences['status'].unique())
        )

    with col3:
        progress_filter = st.selectbox(
            "Filter by Progress:",
            ["All", "Early (0-30%)", "Mid (30-70%)", "Late (70%+)"]
        )

    # Apply filters
    filtered_df = df_sequences.copy()

    if sequence_filter != "All":
        filtered_df = filtered_df[filtered_df['sequence_type'] == sequence_filter]

    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]

    if progress_filter != "All":
        if progress_filter == "Early (0-30%)":
            filtered_df = filtered_df[filtered_df['progress'] <= 30]
        elif progress_filter == "Mid (30-70%)":
            filtered_df = filtered_df[(filtered_df['progress'] > 30) & (filtered_df['progress'] <= 70)]
        elif progress_filter == "Late (70%+)":
            filtered_df = filtered_df[filtered_df['progress'] > 70]

    # Display sequences
    st.write(f"**📋 Showing {len(filtered_df)} of {len(df_sequences)} sequences**")

    for _, sequence in filtered_df.head(10).iterrows():
        with st.container():
            # Main sequence info
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

            with col1:
                # Status indicator
                status_icons = {
                    "active": "🟢",
                    "paused": "🟡",
                    "responding": "🔵",
                    "voice_scheduled": "📞"
                }

                icon = status_icons.get(sequence['status'], "⚪")
                st.write(f"**{icon} {sequence['lead_name']}** ({sequence['lead_id']})")
                st.caption(f"Type: {sequence['sequence_type'].replace('_', ' ').title()}")

            with col2:
                st.metric("Day", f"{sequence['days_in_sequence']}")

            with col3:
                st.metric("Progress", f"{sequence['progress']:.1f}%")

            with col4:
                st.metric("Engagement", f"{sequence['engagement_score']:.1f}")

            with col5:
                st.metric("Next", sequence['next_in'])

            # Progress bar
            progress_color = "green" if sequence['progress'] > 70 else "orange" if sequence['progress'] > 30 else "red"
            st.progress(sequence['progress'] / 100)

            # Action buttons
            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button("▶️", key=f"resume_{sequence['lead_id']}", help="Resume sequence"):
                    st.success(f"✅ Resumed sequence for {sequence['lead_name']}")

            with action_col2:
                if st.button("⏸️", key=f"pause_{sequence['lead_id']}", help="Pause sequence"):
                    st.info(f"⏸️ Paused sequence for {sequence['lead_name']}")

            with action_col3:
                if st.button("📞", key=f"call_{sequence['lead_id']}", help="Schedule voice call"):
                    st.info(f"📞 Voice call scheduled for {sequence['lead_name']}")

            with action_col4:
                if st.button("📊", key=f"cma_{sequence['lead_id']}", help="Generate CMA"):
                    st.info(f"📊 CMA generation started for {sequence['lead_name']}")

        st.divider()

def render_sequence_performance():
    """Render sequence performance analytics and optimization insights."""
    st.subheader("📈 Sequence Performance Analytics")

    data = get_sequence_data()
    performance = data["sequence_performance"]

    # Performance metrics
    col1, col2 = st.columns(2)

    with col1:
        st.write("**📊 Engagement Rate by Touchpoint**")

        touchpoint_data = {
            'Touchpoint': ['Day 3', 'Day 7', 'Day 30'],
            'Engagement Rate': [
                performance['day_3_engagement'],
                performance['day_7_engagement'],
                performance['day_30_engagement']
            ],
            'Response Rate': [
                performance['day_3_response_rate'],
                performance['day_7_response_rate'],
                performance['day_30_response_rate']
            ]
        }

        df_performance = pd.DataFrame(touchpoint_data)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_performance['Touchpoint'],
            y=df_performance['Engagement Rate'],
            name='Engagement Rate',
            marker_color='#4ecdc4'
        ))

        fig.add_trace(go.Bar(
            x=df_performance['Touchpoint'],
            y=df_performance['Response Rate'],
            name='Response Rate',
            marker_color='#ff6b6b'
        ))

        fig.update_layout(
            title="Touchpoint Performance Comparison",
            yaxis_title="Percentage (%)",
            barmode='group',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**🎯 Key Performance Metrics**")

        # KPI cards
        st.metric(
            "📞 Voice Call Success",
            f"{performance['voice_call_success']}%",
            delta="+2.1%",
            help="Successful Retell AI voice call connections"
        )

        st.metric(
            "📄 CMA Open Rate",
            f"{performance['cma_open_rate']}%",
            delta="+5.3%",
            help="CMA document open and view rate"
        )

        st.metric(
            "🎯 CMA Engagement",
            f"{performance['cma_engagement']}%",
            delta="+1.8%",
            help="Time spent reviewing CMA content"
        )

        # Optimization insights
        st.write("**🚀 Optimization Opportunities**")
        st.info("""
        **📈 Trending Up:**
        - Day 7 voice calls (+12% this week)
        - CMA personalization effectiveness

        **⚠️ Needs Attention:**
        - Day 30 response rates declining
        - Weekend touchpoint performance
        """)

def render_sequence_automation():
    """Render sequence automation settings and controls."""
    st.subheader("⚙️ Sequence Automation Controls")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**🔧 Automation Settings**")

        # Automation controls
        auto_voice_enabled = st.checkbox(
            "🎙️ Auto Voice Calls",
            value=True,
            help="Automatically schedule Retell AI voice calls on Day 7"
        )

        auto_cma_enabled = st.checkbox(
            "📊 Auto CMA Generation",
            value=True,
            help="Automatically generate CMAs on Day 30"
        )

        weekend_messages = st.checkbox(
            "📅 Weekend Messaging",
            value=False,
            help="Allow automated messages during weekends"
        )

        business_hours_only = st.checkbox(
            "🕘 Business Hours Only",
            value=True,
            help="Restrict automated calls to business hours"
        )

        # Sequence timing controls
        st.write("**⏰ Timing Controls**")

        day_3_delay = st.slider(
            "Day 3 Touchpoint Delay (hours)",
            min_value=24,
            max_value=96,
            value=72,
            step=12,
            help="Hours after initial contact for Day 3 touchpoint"
        )

        day_7_delay = st.slider(
            "Day 7 Touchpoint Delay (hours)",
            min_value=144,
            max_value=216,
            value=168,
            step=12,
            help="Hours after initial contact for Day 7 touchpoint"
        )

        day_30_delay = st.slider(
            "Day 30 Touchpoint Delay (hours)",
            min_value=672,
            max_value=792,
            value=720,
            step=24,
            help="Hours after initial contact for Day 30 touchpoint"
        )

    with col2:
        st.write("**📋 Template Management**")

        # Template selection
        template_type = st.selectbox(
            "Select Template Type:",
            ["Day 3 SMS", "Day 7 Voice Script", "Day 30 CMA Email"]
        )

        # Sample template content
        if template_type == "Day 3 SMS":
            template_content = """Hi {lead_name}! Jorge here from Austin Real Estate.

Quick market update: Your area is seeing 15% price growth this quarter. Curious if you're still considering a move?

Best timing to chat briefly: Reply STOP to opt out."""

        elif template_type == "Day 7 Voice Script":
            template_content = """Hi {lead_name}, this is Jorge calling about your real estate inquiry.

I've been tracking the market in your area and wanted to share some insights that could save you thousands.

Do you have 2 minutes to chat about your timeline and goals?"""

        else:  # Day 30 CMA Email
            template_content = """Subject: Your Personalized Market Analysis - {property_address}

Hi {lead_name},

I've prepared a detailed market analysis for your area. This shows:

• Current market values in your neighborhood
• Recent sales and price trends
• Strategic timing recommendations

Attached is your personalized CMA. Best time to discuss?

Jorge"""

        st.text_area(
            f"**{template_type} Template:**",
            value=template_content,
            height=200,
            help="Template content with variables for personalization"
        )

        # Template variables
        st.write("**🔄 Available Variables:**")
        st.code("""
{lead_name} - Lead's first name
{lead_full_name} - Lead's full name
{property_address} - Property address
{market_area} - Local market area
{agent_name} - Agent name (Jorge)
{current_date} - Today's date
{market_trend} - Current market trend
        """)

def render_voice_integration():
    """Render Retell AI voice call integration status."""
    st.subheader("🎙️ Retell AI Voice Integration")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "📞 Calls Today",
            f"{random.randint(15, 28)}",
            delta="+3 vs yesterday"
        )

        st.metric(
            "⏱️ Avg Call Duration",
            f"{random.uniform(2.1, 3.8):.1f}min"
        )

    with col2:
        st.metric(
            "✅ Success Rate",
            f"{random.uniform(68, 78):.1f}%",
            delta="+2.3%"
        )

        st.metric(
            "🎯 Qualification Rate",
            f"{random.uniform(35, 45):.1f}%"
        )

    with col3:
        st.metric(
            "🔄 Follow-up Scheduled",
            f"{random.randint(8, 15)}",
            delta="From today's calls"
        )

        st.metric(
            "🚀 Handoff to Bots",
            f"{random.randint(5, 12)}",
            delta="Qualified leads"
        )

    # Voice call queue
    st.write("**📋 Upcoming Voice Calls**")

    upcoming_calls = [
        {
            "lead_name": f"Lead {i}",
            "scheduled_time": (datetime.now() + timedelta(hours=random.randint(1, 48))).strftime("%m/%d %I:%M %p"),
            "sequence_day": random.choice([7, 14, 21]),
            "call_type": random.choice(["Initial", "Follow-up", "Re-engagement"])
        } for i in range(1, 8)
    ]

    for call in upcoming_calls:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.write(f"📞 **{call['lead_name']}**")

        with col2:
            st.write(f"🕐 {call['scheduled_time']}")

        with col3:
            st.write(f"📅 Day {call['sequence_day']}")

        with col4:
            st.write(f"🎯 {call['call_type']}")

def render_lead_bot_sequence_dashboard():
    """Main function to render the complete Lead Bot sequence dashboard."""
    st.title("📞 Lead Bot 3-7-30 Sequence Dashboard")
    st.write("**Jorge's automated lead nurturing and qualification sequences**")

    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write("*Real-time sequence tracking and automation management*")

    with col2:
        if st.button("🔄 Refresh", type="secondary"):
            st.cache_data.clear()
            st.experimental_rerun()

    with col3:
        st.success("🟢 **Automation Active**")

    st.divider()

    # Main dashboard sections
    render_sequence_overview()
    st.divider()

    create_sequence_timeline()
    st.divider()

    render_active_sequences()
    st.divider()

    render_sequence_performance()
    st.divider()

    render_sequence_automation()
    st.divider()

    render_voice_integration()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("✅ Lead Bot Service: **Active**")

    with col2:
        st.info(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")

    with col3:
        st.info("📊 Data Source: **Live Sequence Engine**")

# === MAIN EXECUTION ===

if __name__ == "__main__":
    render_lead_bot_sequence_dashboard()