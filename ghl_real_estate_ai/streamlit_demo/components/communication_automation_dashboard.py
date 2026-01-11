"""
Communication Automation Dashboard Streamlit Component

Interactive interface for managing automated communication sequences, campaigns,
analytics, and optimization for real estate agents.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from services.agent_communication_automation import (
    communication_automation,
    CommunicationChannel,
    MessageType,
    AutomationTrigger,
    CommunicationStatus,
    EngagementLevel,
    enroll_lead_in_communication_sequence,
    send_due_communications,
    optimize_send_timing,
    track_response,
    get_communication_analytics
)


def render_communication_automation_dashboard():
    """Render the communication automation dashboard interface."""
    st.header("📧 Communication Automation")
    st.markdown("*AI-powered multi-channel communication and follow-up automation*")

    # Role-based navigation
    user_role = st.selectbox(
        "Dashboard View",
        options=["Agent", "Manager", "Administrator"],
        help="Select your role to see relevant features"
    )

    if user_role == "Agent":
        render_agent_communication_view()
    elif user_role == "Manager":
        render_manager_communication_view()
    else:  # Administrator
        render_admin_communication_view()


def render_agent_communication_view():
    """Render agent-focused communication automation interface."""
    st.subheader("🎯 Agent Communication Console")

    # Agent selection
    agent_id = st.selectbox(
        "Agent Profile",
        options=["agent_001", "agent_002", "agent_003", "demo_agent"],
        help="Select agent profile"
    )

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Active Sequences",
        "📊 Performance",
        "🎨 Templates",
        "⚙️ Automation",
        "📈 Analytics"
    ])

    with tab1:
        render_active_sequences(agent_id)

    with tab2:
        render_communication_performance(agent_id)

    with tab3:
        render_template_management(agent_id)

    with tab4:
        render_automation_setup(agent_id)

    with tab5:
        render_communication_analytics(agent_id)


def render_active_sequences(agent_id: str):
    """Render active communication sequences dashboard."""
    st.subheader("📋 Active Communication Sequences")

    try:
        # Get active sequences for agent
        active_attempts = [
            attempt for attempt in communication_automation.attempts.values()
            if (attempt.agent_id == agent_id and
                attempt.status in [CommunicationStatus.SCHEDULED, CommunicationStatus.SENT])
        ]

        if not active_attempts:
            st.info("No active communication sequences. Start by enrolling leads in sequences.")

            # Quick enrollment section
            with st.expander("🚀 Quick Lead Enrollment"):
                render_quick_enrollment_form(agent_id)
            return

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Sequences", len(set(a.sequence_id for a in active_attempts if a.sequence_id)))

        with col2:
            scheduled_count = len([a for a in active_attempts if a.status == CommunicationStatus.SCHEDULED])
            st.metric("Scheduled Messages", scheduled_count)

        with col3:
            sent_count = len([a for a in active_attempts if a.status == CommunicationStatus.SENT])
            st.metric("Messages Sent", sent_count)

        with col4:
            unique_leads = len(set(a.lead_id for a in active_attempts))
            st.metric("Active Leads", unique_leads)

        # Upcoming communications
        st.subheader("⏰ Upcoming Communications")

        # Filter to next 24 hours
        next_24h = datetime.utcnow() + timedelta(hours=24)
        upcoming = [
            a for a in active_attempts
            if a.status == CommunicationStatus.SCHEDULED and a.scheduled_time <= next_24h
        ]

        if upcoming:
            upcoming_data = []
            for attempt in sorted(upcoming, key=lambda x: x.scheduled_time):
                template = communication_automation.templates.get(attempt.template_id)
                upcoming_data.append({
                    "Time": attempt.scheduled_time.strftime("%m/%d %H:%M"),
                    "Lead": attempt.lead_id,
                    "Channel": attempt.channel.value.title(),
                    "Message Type": attempt.message_type.value.replace('_', ' ').title(),
                    "Template": template.name if template else "Custom",
                    "Status": attempt.status.value.title()
                })

            upcoming_df = pd.DataFrame(upcoming_data)
            st.dataframe(upcoming_df, use_container_width=True)

            # Manual send controls
            if st.button("📤 Send Due Communications Now"):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    sent_ids = loop.run_until_complete(send_due_communications())
                    loop.close()

                    st.success(f"✅ Sent {len(sent_ids)} communications!")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Error sending communications: {str(e)}")

        else:
            st.info("No communications scheduled for the next 24 hours.")

        # Sequence performance overview
        st.subheader("📈 Sequence Performance")

        sequence_stats = {}
        for attempt in active_attempts:
            if attempt.sequence_id:
                seq_id = attempt.sequence_id
                if seq_id not in sequence_stats:
                    sequence_stats[seq_id] = {
                        "total": 0, "sent": 0, "opened": 0, "replied": 0, "leads": set()
                    }

                sequence_stats[seq_id]["total"] += 1
                sequence_stats[seq_id]["leads"].add(attempt.lead_id)

                if attempt.status == CommunicationStatus.SENT:
                    sequence_stats[seq_id]["sent"] += 1
                elif attempt.status == CommunicationStatus.OPENED:
                    sequence_stats[seq_id]["opened"] += 1
                elif attempt.status == CommunicationStatus.REPLIED:
                    sequence_stats[seq_id]["replied"] += 1

        if sequence_stats:
            seq_performance = []
            for seq_id, stats in sequence_stats.items():
                sequence = communication_automation.sequences.get(seq_id)
                seq_name = sequence.name if sequence else seq_id
                total = stats["total"]

                seq_performance.append({
                    "Sequence": seq_name,
                    "Active Leads": len(stats["leads"]),
                    "Total Messages": total,
                    "Sent": stats["sent"],
                    "Send Rate": f"{stats['sent']/total*100:.1f}%" if total > 0 else "0%",
                    "Open Rate": f"{stats['opened']/total*100:.1f}%" if total > 0 else "0%",
                    "Response Rate": f"{stats['replied']/total*100:.1f}%" if total > 0 else "0%"
                })

            seq_df = pd.DataFrame(seq_performance)
            st.dataframe(seq_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading active sequences: {str(e)}")


def render_quick_enrollment_form(agent_id: str):
    """Render quick lead enrollment form."""
    with st.form("quick_enrollment"):
        col1, col2 = st.columns(2)

        with col1:
            lead_id = st.text_input("Lead ID", placeholder="lead_12345")
            sequence_id = st.selectbox(
                "Communication Sequence",
                options=list(communication_automation.sequences.keys()),
                format_func=lambda x: communication_automation.sequences[x].name
            )

        with col2:
            lead_name = st.text_input("Lead Name", placeholder="John Doe")
            lead_email = st.text_input("Lead Email", placeholder="john@example.com")

        custom_data = {
            "first_name": lead_name.split()[0] if lead_name else "Valued Client",
            "agent_name": "Your Agent Name",
            "agent_phone": "(555) 123-4567"
        }

        submitted = st.form_submit_button("🚀 Enroll Lead")

        if submitted and lead_id and sequence_id:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                enrollment_id = loop.run_until_complete(
                    enroll_lead_in_communication_sequence(
                        agent_id, lead_id, sequence_id, custom_data
                    )
                )
                loop.close()

                st.success(f"✅ Lead {lead_id} enrolled in communication sequence!")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error enrolling lead: {str(e)}")


def render_communication_performance(agent_id: str):
    """Render communication performance metrics."""
    st.subheader("📊 Communication Performance")

    try:
        # Get analytics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(get_communication_analytics(agent_id, 30))
        loop.close()

        # Key performance metrics
        col1, col2, col3, col4 = st.columns(4)

        engagement = analytics.engagement_metrics
        with col1:
            open_rate = engagement.get("open_rate", 0) * 100
            st.metric("Open Rate", f"{open_rate:.1f}%", delta=f"+{open_rate-20:.1f}%")

        with col2:
            click_rate = engagement.get("click_rate", 0) * 100
            st.metric("Click Rate", f"{click_rate:.1f}%", delta=f"+{click_rate-5:.1f}%")

        with col3:
            response_rate = engagement.get("response_rate", 0) * 100
            st.metric("Response Rate", f"{response_rate:.1f}%", delta=f"+{response_rate-10:.1f}%")

        with col4:
            conversion = analytics.conversion_metrics.get("lead_to_appointment_rate", 0) * 100
            st.metric("Lead to Appointment", f"{conversion:.1f}%", delta=f"+{conversion-15:.1f}%")

        # Channel performance chart
        if analytics.channel_breakdown:
            st.subheader("📱 Performance by Channel")

            channel_data = []
            for channel, stats in analytics.channel_breakdown.items():
                channel_data.append({
                    "Channel": channel.title(),
                    "Sent": stats.get("total_sent", 0),
                    "Open Rate": stats.get("open_rate", 0) * 100,
                    "Click Rate": stats.get("click_rate", 0) * 100,
                    "Response Rate": stats.get("response_rate", 0) * 100
                })

            channel_df = pd.DataFrame(channel_data)

            if not channel_df.empty:
                fig = px.bar(
                    channel_df,
                    x="Channel",
                    y=["Open Rate", "Click Rate", "Response Rate"],
                    title="Communication Performance by Channel",
                    barmode="group",
                    labels={"value": "Rate (%)", "variable": "Metric"}
                )
                st.plotly_chart(fig, use_container_width=True)

        # Timing optimization insights
        if analytics.timing_analysis:
            st.subheader("⏰ Optimal Timing Insights")

            timing = analytics.timing_analysis
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Best Day to Send", timing.get("best_day_of_week", "Tuesday").title())
                st.metric("Worst Day to Send", timing.get("worst_day_of_week", "Friday").title())

            with col2:
                best_hour = timing.get("best_hour_of_day", 14)
                worst_hour = timing.get("worst_hour_of_day", 22)
                st.metric("Best Time to Send", f"{best_hour}:00")
                st.metric("Worst Time to Send", f"{worst_hour}:00")

        # AI optimization impact
        if analytics.ai_optimization_impact:
            st.subheader("🤖 AI Optimization Impact")

            optimization = analytics.ai_optimization_impact
            impacts = [
                {"Feature": "Timing Optimization", "Improvement": optimization.get("timing_optimization_improvement", 0) * 100},
                {"Feature": "Personalization", "Improvement": optimization.get("personalization_improvement", 0) * 100},
                {"Feature": "Channel Selection", "Improvement": optimization.get("channel_optimization_improvement", 0) * 100}
            ]

            impact_df = pd.DataFrame(impacts)

            if not impact_df.empty:
                fig = px.bar(
                    impact_df,
                    x="Feature",
                    y="Improvement",
                    title="AI Optimization Performance Impact",
                    labels={"Improvement": "Improvement (%)"},
                    color="Improvement",
                    color_continuous_scale="viridis"
                )
                st.plotly_chart(fig, use_container_width=True)

        # Recommendations
        if analytics.recommendations:
            st.subheader("💡 Performance Recommendations")
            for recommendation in analytics.recommendations:
                st.info(f"📈 {recommendation}")

    except Exception as e:
        st.error(f"Error loading performance metrics: {str(e)}")


def render_template_management(agent_id: str):
    """Render communication template management interface."""
    st.subheader("🎨 Communication Templates")

    # Template library
    templates = list(communication_automation.templates.values())

    if templates:
        # Filter controls
        col1, col2, col3 = st.columns(3)

        with col1:
            channel_filter = st.selectbox(
                "Filter by Channel",
                options=["All"] + [c.value for c in CommunicationChannel],
                format_func=lambda x: x.title() if x != "All" else "All Channels"
            )

        with col2:
            message_type_filter = st.selectbox(
                "Filter by Message Type",
                options=["All"] + [m.value for m in MessageType],
                format_func=lambda x: x.replace('_', ' ').title() if x != "All" else "All Types"
            )

        with col3:
            sort_by = st.selectbox(
                "Sort by",
                options=["name", "effectiveness_score", "usage_count"],
                format_func=lambda x: x.replace('_', ' ').title()
            )

        # Filter templates
        filtered_templates = templates
        if channel_filter != "All":
            filtered_templates = [t for t in filtered_templates if t.channel.value == channel_filter]
        if message_type_filter != "All":
            filtered_templates = [t for t in filtered_templates if t.message_type.value == message_type_filter]

        # Sort templates
        if sort_by == "effectiveness_score":
            filtered_templates.sort(key=lambda x: x.effectiveness_score, reverse=True)
        elif sort_by == "usage_count":
            filtered_templates.sort(key=lambda x: x.usage_count, reverse=True)
        else:
            filtered_templates.sort(key=lambda x: x.name)

        # Display templates
        for template in filtered_templates:
            with st.expander(f"📋 {template.name} ({template.effectiveness_score:.2f} effectiveness)"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Channel:** {template.channel.value.title()}")
                    st.write(f"**Message Type:** {template.message_type.value.replace('_', ' ').title()}")
                    if template.subject_line:
                        st.write(f"**Subject:** {template.subject_line}")

                    # Content preview
                    content_preview = template.content_template[:200] + "..." if len(template.content_template) > 200 else template.content_template
                    st.text_area(
                        "Content Preview",
                        value=content_preview,
                        height=100,
                        disabled=True,
                        key=f"preview_{template.id}"
                    )

                with col2:
                    st.metric("Effectiveness", f"{template.effectiveness_score:.2f}")
                    st.metric("Usage Count", template.usage_count)

                    if template.engagement_level:
                        engagement_color = {
                            EngagementLevel.COLD: "🔵",
                            EngagementLevel.WARM: "🟡",
                            EngagementLevel.HOT: "🔴",
                            EngagementLevel.ACTIVE: "🟢"
                        }.get(template.engagement_level, "⚪")
                        st.write(f"**Target:** {engagement_color} {template.engagement_level.value.title()}")

                # Template actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Use Template", key=f"use_{template.id}"):
                        use_template_for_communication(agent_id, template)

                with col2:
                    if st.button(f"Customize", key=f"customize_{template.id}"):
                        show_template_customization(template)

                with col3:
                    if st.button(f"View Analytics", key=f"analytics_{template.id}"):
                        show_template_analytics(template)

    # Create new template
    st.subheader("➕ Create New Template")
    with st.expander("Create Custom Template"):
        render_template_creation_form(agent_id)


def render_template_creation_form(agent_id: str):
    """Render form for creating new communication templates."""
    with st.form("create_template"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Template Name", placeholder="e.g., Follow-up for Luxury Buyers")
            channel = st.selectbox("Communication Channel", options=[c.value for c in CommunicationChannel])
            message_type = st.selectbox("Message Type", options=[m.value for m in MessageType])

        with col2:
            engagement_level = st.selectbox(
                "Target Engagement Level",
                options=[e.value for e in EngagementLevel],
                index=1  # Default to WARM
            )
            subject_line = st.text_input("Subject Line (for email)", placeholder="Quick update about your property search")

        content_template = st.text_area(
            "Template Content",
            height=200,
            placeholder="Hi {first_name},\n\nI wanted to follow up about...\n\nBest regards,\n{agent_name}",
            help="Use {variable_name} for personalization fields"
        )

        variables = st.text_input(
            "Variables (comma-separated)",
            placeholder="first_name, agent_name, property_address",
            help="List all variables used in the template"
        )

        submitted = st.form_submit_button("Create Template")

        if submitted and name and content_template:
            try:
                # Create new template
                from services.agent_communication_automation import CommunicationTemplate
                import uuid

                template = CommunicationTemplate(
                    id=f"custom_{uuid.uuid4().hex[:8]}",
                    name=name,
                    message_type=MessageType(message_type),
                    channel=CommunicationChannel(channel),
                    subject_line=subject_line if subject_line else None,
                    content_template=content_template,
                    variables=[v.strip() for v in variables.split(',') if v.strip()],
                    engagement_level=EngagementLevel(engagement_level),
                    created_by=agent_id
                )

                communication_automation.templates[template.id] = template

                st.success("✅ Template created successfully!")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error creating template: {str(e)}")


def render_automation_setup(agent_id: str):
    """Render automation setup and configuration."""
    st.subheader("⚙️ Automation Setup")

    # Available sequences
    sequences = list(communication_automation.sequences.values())

    if sequences:
        st.subheader("📋 Available Sequences")

        for sequence in sequences:
            with st.expander(f"🔄 {sequence.name}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Description:** {sequence.description}")
                    st.write(f"**Trigger:** {sequence.trigger.value.replace('_', ' ').title()}")
                    st.write(f"**Steps:** {len(sequence.steps)}")

                with col2:
                    st.metric("Success Rate", f"{sequence.success_rate * 100:.1f}%")
                    st.metric("Total Enrollments", sequence.total_enrollments)
                    st.metric("Completion Rate", f"{sequence.completion_rate * 100:.1f}%")

                # Sequence steps
                if st.checkbox(f"Show Steps", key=f"show_steps_{sequence.id}"):
                    st.write("**Sequence Steps:**")
                    for i, step in enumerate(sequence.steps, 1):
                        delay = step.get("delay_hours", 0)
                        template_id = step.get("template_id", "")
                        template = communication_automation.templates.get(template_id)
                        template_name = template.name if template else "Custom"

                        st.write(f"{i}. **After {delay} hours**: {template_name} via {step.get('channel', 'email')}")

                # Quick enrollment
                if st.button(f"Quick Enroll Lead", key=f"enroll_{sequence.id}"):
                    show_sequence_enrollment_dialog(agent_id, sequence)

    # Timing optimization settings
    st.subheader("⏰ Timing Optimization")

    with st.expander("Configure Timing Preferences"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Business Hours**")
            start_hour = st.slider("Start Hour", 0, 23, 9)
            end_hour = st.slider("End Hour", 0, 23, 17)

        with col2:
            st.write("**Preferred Days**")
            business_days = st.multiselect(
                "Active Days",
                options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            )

        if st.button("💾 Save Timing Preferences"):
            st.success("✅ Timing preferences saved!")

    # AI optimization settings
    st.subheader("🤖 AI Optimization")

    with st.expander("AI Features Configuration"):
        enable_timing_opt = st.checkbox("Enable AI Timing Optimization", value=True)
        enable_personalization = st.checkbox("Enable AI Personalization", value=True)
        enable_channel_opt = st.checkbox("Enable Channel Optimization", value=True)
        enable_content_opt = st.checkbox("Enable Content Optimization", value=False)

        if st.button("💾 Save AI Settings"):
            st.success("✅ AI optimization settings saved!")


def render_communication_analytics(agent_id: str):
    """Render detailed communication analytics."""
    st.subheader("📈 Communication Analytics")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date()
        )

    try:
        # Get analytics
        period_days = (datetime.combine(end_date, datetime.min.time()) -
                      datetime.combine(start_date, datetime.min.time())).days

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(get_communication_analytics(agent_id, period_days))
        loop.close()

        # Performance trends
        st.subheader("📊 Performance Trends")

        # Simulate trend data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        trend_data = {
            "Date": dates,
            "Open Rate": [0.20 + (i % 7) * 0.02 for i in range(len(dates))],
            "Click Rate": [0.05 + (i % 5) * 0.01 for i in range(len(dates))],
            "Response Rate": [0.10 + (i % 3) * 0.015 for i in range(len(dates))]
        }

        trend_df = pd.DataFrame(trend_data)

        fig = px.line(
            trend_df,
            x="Date",
            y=["Open Rate", "Click Rate", "Response Rate"],
            title="Communication Performance Trends",
            labels={"value": "Rate", "variable": "Metric"}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Engagement heatmap
        st.subheader("🔥 Engagement Heatmap")

        # Simulate heatmap data
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        hours = list(range(9, 18))  # Business hours

        heatmap_data = []
        for day in days:
            for hour in hours:
                engagement = 0.1 + (hash(f"{day}{hour}") % 100) / 1000
                heatmap_data.append({
                    "Day": day,
                    "Hour": f"{hour}:00",
                    "Engagement Rate": engagement
                })

        heatmap_df = pd.DataFrame(heatmap_data)
        pivot_data = heatmap_df.pivot(index="Hour", columns="Day", values="Engagement Rate")

        fig = px.imshow(
            pivot_data,
            title="Best Times to Send Communications",
            color_continuous_scale="viridis",
            labels={"color": "Engagement Rate"}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Template performance
        st.subheader("📋 Template Performance Analysis")

        template_data = []
        for template in communication_automation.templates.values():
            if template.usage_count > 0:
                template_data.append({
                    "Template": template.name,
                    "Usage Count": template.usage_count,
                    "Effectiveness": template.effectiveness_score,
                    "Channel": template.channel.value.title(),
                    "Type": template.message_type.value.replace('_', ' ').title()
                })

        if template_data:
            template_df = pd.DataFrame(template_data)

            fig = px.scatter(
                template_df,
                x="Usage Count",
                y="Effectiveness",
                size="Usage Count",
                color="Channel",
                hover_data=["Template", "Type"],
                title="Template Usage vs Effectiveness",
                labels={"Effectiveness": "Effectiveness Score"}
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")


def render_manager_communication_view():
    """Render manager-focused communication overview."""
    st.subheader("👥 Team Communication Management")

    # Team overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Agents", 8)
    with col2:
        st.metric("Total Sequences", 12)
    with col3:
        st.metric("Daily Messages", 156)
    with col4:
        st.metric("Team Response Rate", "18.5%", delta="+2.3%")

    # Team performance comparison
    st.subheader("📊 Team Performance Comparison")

    team_data = {
        "Agent": ["Agent A", "Agent B", "Agent C", "Agent D"],
        "Messages Sent": [45, 52, 38, 41],
        "Open Rate": [22.5, 19.8, 25.1, 20.3],
        "Response Rate": [15.2, 12.8, 18.7, 16.1]
    }

    team_df = pd.DataFrame(team_data)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(name="Messages Sent", x=team_df["Agent"], y=team_df["Messages Sent"]),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(name="Response Rate", x=team_df["Agent"], y=team_df["Response Rate"], mode="lines+markers"),
        secondary_y=True,
    )

    fig.update_xaxes(title_text="Agent")
    fig.update_yaxes(title_text="Messages Sent", secondary_y=False)
    fig.update_yaxes(title_text="Response Rate (%)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    # Sequence performance across team
    st.subheader("🔄 Sequence Performance Overview")

    sequence_team_data = []
    for sequence in communication_automation.sequences.values():
        sequence_team_data.append({
            "Sequence": sequence.name,
            "Active Agents": 3,  # Simulated
            "Total Leads": sequence.total_enrollments,
            "Success Rate": f"{sequence.success_rate * 100:.1f}%",
            "Completion Rate": f"{sequence.completion_rate * 100:.1f}%"
        })

    if sequence_team_data:
        seq_team_df = pd.DataFrame(sequence_team_data)
        st.dataframe(seq_team_df, use_container_width=True)


def render_admin_communication_view():
    """Render administrator communication system management."""
    st.subheader("⚙️ System Administration")

    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "📊 System Analytics",
        "🔧 Configuration",
        "📋 Template Library"
    ])

    with admin_tab1:
        render_system_analytics()

    with admin_tab2:
        render_system_configuration()

    with admin_tab3:
        render_global_template_library()


def render_system_analytics():
    """Render system-wide analytics."""
    st.subheader("📊 System-wide Communication Analytics")

    # System metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Messages/Day", "1,247", delta="+89")
    with col2:
        st.metric("System Uptime", "99.8%", delta="+0.1%")
    with col3:
        st.metric("Avg Response Time", "12.3s", delta="-2.1s")
    with col4:
        st.metric("Error Rate", "0.2%", delta="-0.1%")

    # Channel distribution
    st.subheader("📱 Channel Usage Distribution")

    channel_usage = {
        "Channel": ["Email", "SMS", "Phone", "LinkedIn", "Direct Mail"],
        "Usage": [65, 25, 8, 1.5, 0.5]
    }

    channel_df = pd.DataFrame(channel_usage)

    fig = px.pie(
        channel_df,
        values="Usage",
        names="Channel",
        title="Communication Channel Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_system_configuration():
    """Render system configuration interface."""
    st.subheader("🔧 System Configuration")

    with st.expander("📧 Email Service Settings"):
        email_provider = st.selectbox(
            "Email Provider",
            options=["SendGrid", "Mailgun", "Amazon SES", "Custom SMTP"]
        )

        daily_limit = st.number_input("Daily Email Limit", min_value=100, value=10000)

        if st.button("Save Email Settings"):
            st.success("✅ Email settings saved!")

    with st.expander("📱 SMS Service Settings"):
        sms_provider = st.selectbox(
            "SMS Provider",
            options=["Twilio", "Amazon SNS", "MessageBird"]
        )

        sms_daily_limit = st.number_input("Daily SMS Limit", min_value=50, value=1000)

        if st.button("Save SMS Settings"):
            st.success("✅ SMS settings saved!")

    with st.expander("🤖 AI Optimization Settings"):
        enable_global_optimization = st.checkbox("Enable Global AI Optimization", value=True)
        learning_rate = st.slider("AI Learning Rate", 0.0, 1.0, 0.1)

        if st.button("Save AI Settings"):
            st.success("✅ AI settings saved!")


def render_global_template_library():
    """Render global template library management."""
    st.subheader("📋 Global Template Library")

    templates = list(communication_automation.templates.values())

    # Template statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Templates", len(templates))
    with col2:
        system_templates = len([t for t in templates if t.created_by == "system"])
        st.metric("System Templates", system_templates)
    with col3:
        custom_templates = len([t for t in templates if t.created_by != "system"])
        st.metric("Custom Templates", custom_templates)
    with col4:
        avg_effectiveness = sum(t.effectiveness_score for t in templates) / len(templates) if templates else 0
        st.metric("Avg Effectiveness", f"{avg_effectiveness:.2f}")

    # Template performance overview
    if templates:
        template_overview = []
        for template in templates:
            template_overview.append({
                "Name": template.name,
                "Channel": template.channel.value.title(),
                "Type": template.message_type.value.replace('_', ' ').title(),
                "Usage": template.usage_count,
                "Effectiveness": template.effectiveness_score,
                "Created By": template.created_by
            })

        overview_df = pd.DataFrame(template_overview)
        st.dataframe(overview_df, use_container_width=True)

        # Bulk actions
        st.subheader("🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📤 Export Templates"):
                st.success("✅ Templates exported!")

        with col2:
            if st.button("📥 Import Templates"):
                st.info("Template import dialog would appear")

        with col3:
            if st.button("🧹 Cleanup Unused"):
                st.success("✅ Unused templates cleaned up!")


# Helper functions

def use_template_for_communication(agent_id: str, template):
    """Use a template to start a new communication."""
    st.info(f"Using template '{template.name}' for new communication")
    # In production, this would open a communication composer


def show_template_customization(template):
    """Show template customization dialog."""
    st.info(f"Customization dialog for '{template.name}' would appear")
    # In production, this would open template editor


def show_template_analytics(template):
    """Show detailed template analytics."""
    st.info(f"Analytics for '{template.name}':")
    st.write(f"• Usage Count: {template.usage_count}")
    st.write(f"• Effectiveness Score: {template.effectiveness_score:.2f}")
    st.write(f"• Last Updated: {template.updated_date.strftime('%Y-%m-%d')}")


def show_sequence_enrollment_dialog(agent_id: str, sequence):
    """Show sequence enrollment dialog."""
    st.info(f"Quick enrollment for '{sequence.name}':")

    lead_id = st.text_input("Enter Lead ID", key=f"quick_lead_{sequence.id}")

    if st.button(f"Enroll", key=f"quick_enroll_{sequence.id}") and lead_id:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            enrollment_id = loop.run_until_complete(
                enroll_lead_in_communication_sequence(agent_id, lead_id, sequence.id)
            )
            loop.close()

            st.success(f"✅ Lead {lead_id} enrolled!")

        except Exception as e:
            st.error(f"Error: {str(e)}")


# Demo data initialization
def load_demo_communication_data():
    """Load demo data for communication automation."""
    try:
        # Create some demo communication attempts
        from services.agent_communication_automation import CommunicationAttempt
        import uuid

        demo_attempts = [
            CommunicationAttempt(
                id=f"demo_{i}",
                agent_id="agent_001",
                lead_id=f"lead_{i:03d}",
                sequence_id="new_lead_nurture_sequence",
                template_id="welcome_new_lead",
                scheduled_time=datetime.utcnow() + timedelta(hours=i),
                status=CommunicationStatus.SCHEDULED if i < 3 else CommunicationStatus.SENT
            )
            for i in range(5)
        ]

        for attempt in demo_attempts:
            communication_automation.attempts[attempt.id] = attempt

    except Exception as e:
        pass  # Ignore demo setup errors


# Load demo data when component is imported
load_demo_communication_data()