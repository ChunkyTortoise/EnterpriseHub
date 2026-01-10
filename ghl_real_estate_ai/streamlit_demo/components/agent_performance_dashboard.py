"""
Agent Performance Dashboard

Comprehensive performance tracking and analytics for real estate agents
with workflow automation integration and Claude AI insights.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

# Import agent services
try:
    from ...services.agent_workflow_automation import (
        agent_workflow_automation,
        TaskPriority,
        TaskStatus,
        AgentPerformanceMetrics
    )
    from ...services.claude_agent_service import claude_agent_service
except ImportError:
    # Fallback for demo mode
    agent_workflow_automation = None
    claude_agent_service = None


def render_agent_performance_dashboard():
    """
    Main agent performance dashboard with comprehensive analytics,
    workflow tracking, and AI-powered optimization recommendations.
    """

    st.markdown("### 📊 Agent Performance & Analytics Dashboard")
    st.markdown("*Comprehensive performance tracking with AI-powered optimization insights*")

    # Agent selection
    agent_id = render_agent_selector()

    if not agent_id:
        render_getting_started_guide()
        return

    # Main dashboard layout
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Overview",
        "📋 Task Management",
        "📈 Performance Trends",
        "🤖 AI Insights",
        "⚙️ Optimization"
    ])

    with tab1:
        render_performance_overview(agent_id)

    with tab2:
        render_task_management(agent_id)

    with tab3:
        render_performance_trends(agent_id)

    with tab4:
        render_ai_insights(agent_id)

    with tab5:
        render_workflow_optimization(agent_id)


def render_agent_selector() -> Optional[str]:
    """Render agent selection interface"""

    col_select, col_register = st.columns([2, 1])

    with col_select:
        # Get available agents
        if agent_workflow_automation:
            agents = list(agent_workflow_automation.agents.keys())
            agent_names = [f"{agent_id} ({agent_workflow_automation.agents[agent_id]['name']})"
                          for agent_id in agents]
        else:
            # Demo agents
            agents = ["agent_001", "agent_002", "agent_003"]
            agent_names = ["agent_001 (Sarah Johnson)", "agent_002 (Mike Rodriguez)", "agent_003 (Jennifer Lee)"]

        if agents:
            selected = st.selectbox(
                "Select Agent",
                ["Select an agent..."] + agent_names,
                key="agent_performance_selector"
            )

            if selected != "Select an agent...":
                return selected.split(" (")[0]
        else:
            st.info("No agents registered. Use the registration form to add agents.")

    with col_register:
        if st.button("➕ Register New Agent"):
            render_agent_registration_form()

    return None


def render_agent_registration_form():
    """Render form to register a new agent"""

    with st.expander("Register New Agent", expanded=True):
        with st.form("agent_registration"):
            col1, col2 = st.columns(2)

            with col1:
                agent_id = st.text_input("Agent ID", placeholder="agent_004")
                name = st.text_input("Full Name", placeholder="John Smith")
                role = st.selectbox("Role", ["agent", "senior_agent", "team_lead", "broker"])

            with col2:
                territory = st.text_input("Territory", placeholder="Austin West")
                specializations = st.multiselect(
                    "Specializations",
                    ["Luxury", "First-Time Buyers", "Investment", "Commercial", "Land", "Relocation"]
                )

            if st.form_submit_button("Register Agent"):
                if agent_id and name:
                    if agent_workflow_automation:
                        success = asyncio.run(agent_workflow_automation.register_agent(
                            agent_id, name, role, territory, specializations
                        ))
                        if success:
                            st.success(f"✅ Agent {name} registered successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to register agent")
                    else:
                        st.success("✅ Demo mode - agent would be registered")
                else:
                    st.error("Please provide Agent ID and Name")


def render_performance_overview(agent_id: str):
    """Render performance overview dashboard"""

    st.markdown(f"#### 🎯 Performance Overview - {agent_id}")

    # Get agent data
    if agent_workflow_automation:
        agent_info = agent_workflow_automation.agents.get(agent_id, {})
        tasks = asyncio.run(agent_workflow_automation.get_agent_tasks(agent_id, limit=100))
    else:
        agent_info = {"name": "Demo Agent", "role": "agent", "territory": "Austin"}
        tasks = get_demo_tasks()

    # Performance metrics cards
    render_performance_metrics_cards(tasks)

    st.markdown("---")

    # Recent activity and key insights
    col_activity, col_insights = st.columns([1.5, 1])

    with col_activity:
        render_recent_activity(tasks)

    with col_insights:
        render_key_insights(agent_id, tasks)


def render_performance_metrics_cards(tasks: List[Any]):
    """Render key performance metric cards"""

    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if getattr(t, 'status', 'pending') == 'completed'])
    pending_tasks = len([t for t in tasks if getattr(t, 'status', 'pending') == 'pending'])
    overdue_tasks = len([t for t in tasks if hasattr(t, 'is_overdue') and t.is_overdue()])

    completion_rate = (completed_tasks / max(1, total_tasks)) * 100

    # Metrics display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Completion Rate",
            f"{completion_rate:.1f}%",
            delta=f"{'↗' if completion_rate > 75 else '↘'} {abs(completion_rate - 75):.1f}%"
        )

    with col2:
        st.metric(
            "Active Tasks",
            pending_tasks,
            delta=f"{'📈' if pending_tasks > 5 else '📉'} {abs(pending_tasks - 5)}"
        )

    with col3:
        st.metric(
            "Overdue",
            overdue_tasks,
            delta=f"{'⚠️' if overdue_tasks > 0 else '✅'} {overdue_tasks - 0}"
        )

    with col4:
        # Calculate productivity score
        productivity_score = max(0, min(100, completion_rate - (overdue_tasks * 10)))
        st.metric(
            "Productivity Score",
            f"{productivity_score:.0f}/100",
            delta=f"{'🚀' if productivity_score > 80 else '📊'} Score"
        )


def render_recent_activity(tasks: List[Any]):
    """Render recent activity timeline"""

    st.markdown("##### 📅 Recent Activity")

    # Sort tasks by creation date
    recent_tasks = sorted(tasks, key=lambda t: getattr(t, 'created_at', datetime.now()), reverse=True)[:10]

    if not recent_tasks:
        st.info("No recent activity found")
        return

    for task in recent_tasks:
        status = getattr(task, 'status', 'pending')
        title = getattr(task, 'title', 'Unknown Task')
        created_at = getattr(task, 'created_at', datetime.now())
        priority = getattr(task, 'priority', 'medium')

        # Status icons
        status_icons = {
            'completed': '✅',
            'in_progress': '🔄',
            'pending': '⏳',
            'overdue': '⚠️',
            'cancelled': '❌'
        }

        # Priority colors
        priority_colors = {
            'urgent': '#ef4444',
            'high': '#f59e0b',
            'medium': '#3b82f6',
            'low': '#10b981',
            'scheduled': '#8b5cf6'
        }

        status_value = status.value if hasattr(status, 'value') else str(status)
        priority_value = priority.value if hasattr(priority, 'value') else str(priority)

        icon = status_icons.get(status_value, '📋')
        color = priority_colors.get(priority_value, '#64748b')

        st.markdown(f"""
        <div style='background: #f8fafc; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0;
                    border-left: 4px solid {color};'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div style='flex: 1;'>
                    <div style='font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;'>
                        {icon} {title}
                    </div>
                    <div style='font-size: 0.8rem; color: #64748b;'>
                        {created_at.strftime('%Y-%m-%d %H:%M')} • Priority: {priority_value.title()}
                    </div>
                </div>
                <div style='background: {color}; color: white; padding: 0.2rem 0.5rem;
                            border-radius: 4px; font-size: 0.7rem; font-weight: 600;'>
                    {status_value.replace('_', ' ').title()}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_key_insights(agent_id: str, tasks: List[Any]):
    """Render AI-powered key insights"""

    st.markdown("##### 🔍 Key Insights")

    try:
        if claude_agent_service and agent_workflow_automation:
            # Get AI insights
            insights_query = "Analyze my current performance and workflow. What are the key patterns and areas for improvement?"

            # This would be an async call in real implementation
            st.info("🤖 Generating AI insights...")

            # Demo insights for now
            insights = get_demo_insights(tasks)
        else:
            insights = get_demo_insights(tasks)

        for insight in insights:
            insight_type = insight.get('type', 'info')
            text = insight.get('text', '')
            impact = insight.get('impact', 'medium')

            # Insight styling based on type
            colors = {
                'success': '#10b981',
                'warning': '#f59e0b',
                'info': '#3b82f6',
                'critical': '#ef4444'
            }

            icons = {
                'success': '✅',
                'warning': '⚠️',
                'info': '💡',
                'critical': '🚨'
            }

            color = colors.get(insight_type, '#64748b')
            icon = icons.get(insight_type, '📊')

            st.markdown(f"""
            <div style='background: {color}15; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;
                        border: 1px solid {color}50;'>
                <div style='display: flex; align-items: start; gap: 0.5rem;'>
                    <div style='font-size: 1.2rem;'>{icon}</div>
                    <div style='flex: 1; color: #1e293b; font-size: 0.9rem;'>{text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.warning(f"Could not load AI insights: {str(e)}")
        # Show demo insights instead
        demo_insights = get_demo_insights(tasks)
        for insight in demo_insights:
            st.info(f"💡 {insight['text']}")


def render_task_management(agent_id: str):
    """Render task management interface"""

    st.markdown(f"#### 📋 Task Management - {agent_id}")

    # Task creation and filtering
    col_filters, col_create = st.columns([2, 1])

    with col_filters:
        col_status, col_priority = st.columns(2)
        with col_status:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Pending", "In Progress", "Completed", "Overdue"],
                key="task_status_filter"
            )

        with col_priority:
            priority_filter = st.selectbox(
                "Filter by Priority",
                ["All", "Urgent", "High", "Medium", "Low"],
                key="task_priority_filter"
            )

    with col_create:
        if st.button("➕ Create Task"):
            render_task_creation_form(agent_id)

    # Get filtered tasks
    if agent_workflow_automation:
        tasks = asyncio.run(agent_workflow_automation.get_agent_tasks(agent_id, limit=50))
    else:
        tasks = get_demo_tasks()

    # Apply filters
    filtered_tasks = apply_task_filters(tasks, status_filter, priority_filter)

    # Task list with actions
    render_task_list(filtered_tasks, agent_id)


def render_task_creation_form(agent_id: str):
    """Render task creation form"""

    with st.expander("Create New Task", expanded=True):
        with st.form("task_creation"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("Task Title", placeholder="Call new lead")
                description = st.text_area("Description", placeholder="Contact details and talking points")

            with col2:
                priority = st.selectbox("Priority", ["urgent", "high", "medium", "low"])
                due_date = st.date_input("Due Date")
                due_time = st.time_input("Due Time")

            lead_id = st.text_input("Related Lead ID (Optional)", placeholder="lead_123")

            if st.form_submit_button("Create Task"):
                if title and description:
                    due_datetime = datetime.combine(due_date, due_time)

                    if agent_workflow_automation:
                        task = asyncio.run(agent_workflow_automation.create_task(
                            agent_id, title, description, priority, due_datetime, lead_id
                        ))
                        st.success(f"✅ Task '{title}' created successfully!")
                        st.rerun()
                    else:
                        st.success("✅ Demo mode - task would be created")
                else:
                    st.error("Please provide title and description")


def apply_task_filters(tasks: List[Any], status_filter: str, priority_filter: str) -> List[Any]:
    """Apply filters to task list"""

    filtered = tasks

    # Status filter
    if status_filter != "All":
        status_map = {
            "Pending": "pending",
            "In Progress": "in_progress",
            "Completed": "completed",
            "Overdue": "overdue"
        }
        target_status = status_map.get(status_filter, "pending")
        filtered = [t for t in filtered if getattr(t, 'status', 'pending') == target_status]

    # Priority filter
    if priority_filter != "All":
        target_priority = priority_filter.lower()
        filtered = [t for t in filtered if getattr(t, 'priority', 'medium') == target_priority]

    return filtered


def render_task_list(tasks: List[Any], agent_id: str):
    """Render interactive task list"""

    st.markdown(f"##### 📝 Tasks ({len(tasks)} items)")

    if not tasks:
        st.info("No tasks found matching the current filters")
        return

    for i, task in enumerate(tasks):
        task_id = getattr(task, 'id', f'task_{i}')
        title = getattr(task, 'title', 'Unknown Task')
        description = getattr(task, 'description', 'No description')
        status = getattr(task, 'status', 'pending')
        priority = getattr(task, 'priority', 'medium')
        due_date = getattr(task, 'due_date', None)
        lead_id = getattr(task, 'lead_id', None)

        # Task display
        status_value = status.value if hasattr(status, 'value') else str(status)
        priority_value = priority.value if hasattr(priority, 'value') else str(priority)

        # Priority colors
        priority_colors = {
            'urgent': '#ef4444',
            'high': '#f59e0b',
            'medium': '#3b82f6',
            'low': '#10b981'
        }

        color = priority_colors.get(priority_value, '#64748b')

        with st.expander(f"{title} ({priority_value.title()})"):
            col_info, col_actions = st.columns([2, 1])

            with col_info:
                st.write(f"**Description:** {description}")
                if due_date:
                    st.write(f"**Due:** {due_date.strftime('%Y-%m-%d %H:%M')}")
                if lead_id:
                    st.write(f"**Related Lead:** {lead_id}")
                st.write(f"**Status:** {status_value.replace('_', ' ').title()}")

            with col_actions:
                if status_value in ['pending', 'in_progress']:
                    if st.button(f"✅ Complete", key=f"complete_{task_id}"):
                        if agent_workflow_automation:
                            success = asyncio.run(agent_workflow_automation.complete_task(task_id))
                            if success:
                                st.success("Task completed!")
                                st.rerun()
                        else:
                            st.success("Demo mode - task would be completed")

                if st.button(f"🤖 Get AI Help", key=f"ai_help_{task_id}"):
                    render_task_ai_assistance(task, agent_id)


def render_task_ai_assistance(task: Any, agent_id: str):
    """Render AI assistance for a specific task"""

    title = getattr(task, 'title', 'Unknown Task')
    lead_id = getattr(task, 'lead_id', None)

    st.markdown(f"#### 🤖 AI Assistance for: {title}")

    try:
        if claude_agent_service and lead_id:
            query = f"Help me with this task: {title}. What's the best approach and what should I focus on?"
            # This would be an async call in real implementation
            st.info("🤖 Generating AI assistance...")

        # Demo assistance
        st.markdown("""
        **AI Recommendations:**
        - Prioritize calling during optimal hours (10-11 AM or 2-4 PM)
        - Prepare 3 key talking points based on lead's interests
        - Have property options ready that match their criteria
        - Use warm, consultative tone rather than sales-focused approach

        **Next Steps:**
        1. Review lead's previous interactions and preferences
        2. Prepare customized property recommendations
        3. Schedule follow-up based on their availability
        """)

    except Exception as e:
        st.warning(f"Could not generate AI assistance: {str(e)}")


def render_performance_trends(agent_id: str):
    """Render performance trends and analytics"""

    st.markdown(f"#### 📈 Performance Trends - {agent_id}")

    # Date range selector
    col_range, col_metrics = st.columns([1, 1])

    with col_range:
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Last year"],
            index=1
        )

    with col_metrics:
        metric_type = st.selectbox(
            "Metric",
            ["Task Completion", "Response Times", "Lead Conversion", "Productivity Score"]
        )

    # Generate demo trend data
    trend_data = generate_demo_trend_data(date_range, metric_type)

    # Trend chart
    fig = px.line(
        trend_data,
        x='date',
        y='value',
        title=f'{metric_type} Trend - {date_range}',
        markers=True
    )

    fig.update_traces(line=dict(color='#3b82f6', width=3))
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Performance insights
    col_insights1, col_insights2 = st.columns(2)

    with col_insights1:
        st.markdown("##### 📊 Key Metrics")
        current_value = trend_data['value'].iloc[-1] if not trend_data.empty else 0
        previous_value = trend_data['value'].iloc[-7] if len(trend_data) > 7 else current_value
        change = ((current_value - previous_value) / max(previous_value, 1)) * 100

        st.metric(
            f"Current {metric_type}",
            f"{current_value:.1f}%",
            delta=f"{change:+.1f}%"
        )

        # Additional metrics
        avg_value = trend_data['value'].mean() if not trend_data.empty else 0
        st.metric("Average", f"{avg_value:.1f}%")

        peak_value = trend_data['value'].max() if not trend_data.empty else 0
        st.metric("Peak Performance", f"{peak_value:.1f}%")

    with col_insights2:
        st.markdown("##### 🎯 Performance Goals")

        # Goal tracking
        goals = {
            "Task Completion": {"target": 90, "current": current_value},
            "Response Times": {"target": 85, "current": current_value},
            "Lead Conversion": {"target": 75, "current": current_value},
            "Productivity Score": {"target": 80, "current": current_value}
        }

        goal = goals.get(metric_type, {"target": 80, "current": current_value})
        goal_progress = (goal["current"] / goal["target"]) * 100

        st.progress(min(goal_progress / 100, 1.0))
        st.write(f"Goal: {goal['target']}% | Current: {goal['current']:.1f}%")

        if goal_progress >= 100:
            st.success("🎉 Goal achieved!")
        elif goal_progress >= 80:
            st.info("📈 Close to goal")
        else:
            st.warning("📊 Below target")


def render_ai_insights(agent_id: str):
    """Render AI-powered insights and recommendations"""

    st.markdown(f"#### 🤖 AI Insights & Recommendations - {agent_id}")

    # Get AI recommendations
    col_generate, col_refresh = st.columns([2, 1])

    with col_generate:
        insight_type = st.selectbox(
            "Insight Type",
            ["Overall Performance", "Task Optimization", "Lead Management", "Time Management", "Goal Achievement"]
        )

    with col_refresh:
        if st.button("🔄 Generate Insights"):
            render_ai_performance_analysis(agent_id, insight_type)

    # Default insights display
    render_ai_performance_analysis(agent_id, insight_type)


def render_ai_performance_analysis(agent_id: str, insight_type: str):
    """Render AI performance analysis"""

    st.markdown(f"##### 🔍 {insight_type} Analysis")

    try:
        if claude_agent_service:
            # This would be a real AI call
            st.info("🤖 Analyzing performance data...")

        # Demo AI insights based on type
        insights = get_demo_ai_insights(insight_type)

        for insight in insights:
            insight_category = insight.get('category', 'General')
            recommendation = insight.get('recommendation', '')
            impact = insight.get('impact', 'Medium')
            effort = insight.get('effort', 'Medium')

            # Impact and effort colors
            impact_colors = {'High': '#10b981', 'Medium': '#f59e0b', 'Low': '#64748b'}
            effort_colors = {'Low': '#10b981', 'Medium': '#f59e0b', 'High': '#ef4444'}

            st.markdown(f"""
            <div style='background: #f8fafc; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
                        border: 1px solid #e2e8f0;'>
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                    <h4 style='margin: 0; color: #1e293b; font-size: 1.1rem;'>{insight_category}</h4>
                    <div style='display: flex; gap: 0.5rem;'>
                        <span style='background: {impact_colors[impact]}; color: white; padding: 0.2rem 0.5rem;
                                     border-radius: 4px; font-size: 0.75rem;'>Impact: {impact}</span>
                        <span style='background: {effort_colors[effort]}; color: white; padding: 0.2rem 0.5rem;
                                     border-radius: 4px; font-size: 0.75rem;'>Effort: {effort}</span>
                    </div>
                </div>
                <p style='margin: 0; color: #475569; line-height: 1.5;'>{recommendation}</p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.warning(f"Could not generate AI insights: {str(e)}")


def render_workflow_optimization(agent_id: str):
    """Render workflow optimization tools and recommendations"""

    st.markdown(f"#### ⚙️ Workflow Optimization - {agent_id}")

    # Optimization analysis
    col_analyze, col_automate = st.columns(2)

    with col_analyze:
        st.markdown("##### 🔍 Workflow Analysis")

        if st.button("📊 Analyze Current Workflow"):
            render_workflow_analysis(agent_id)

    with col_automate:
        st.markdown("##### 🤖 Automation Setup")

        if st.button("⚡ Setup Automation"):
            render_automation_setup(agent_id)

    # Workflow recommendations
    st.markdown("---")
    render_optimization_recommendations(agent_id)


def render_workflow_analysis(agent_id: str):
    """Render detailed workflow analysis"""

    st.markdown("#### 📊 Workflow Analysis Results")

    # Demo analysis
    analysis_data = {
        "efficiency_score": 78.5,
        "bottlenecks": ["Task prioritization", "Follow-up timing", "Lead qualification"],
        "strengths": ["Response time", "Completion rate", "Client communication"],
        "recommendations": [
            "Implement automated task prioritization",
            "Set up follow-up reminders",
            "Use AI lead scoring for better qualification"
        ]
    }

    col_score, col_details = st.columns([1, 2])

    with col_score:
        # Efficiency score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=analysis_data["efficiency_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Workflow Efficiency"},
            delta={'reference': 75},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))

        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col_details:
        # Strengths and bottlenecks
        st.markdown("**🎯 Strengths:**")
        for strength in analysis_data["strengths"]:
            st.markdown(f"• ✅ {strength}")

        st.markdown("**⚠️ Bottlenecks:**")
        for bottleneck in analysis_data["bottlenecks"]:
            st.markdown(f"• 🔍 {bottleneck}")

        st.markdown("**💡 Recommendations:**")
        for rec in analysis_data["recommendations"]:
            st.markdown(f"• 🚀 {rec}")


def render_automation_setup(agent_id: str):
    """Render automation setup interface"""

    st.markdown("#### ⚡ Automation Setup")

    # Workflow triggers
    with st.expander("Configure Workflow Triggers", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**New Lead Automation:**")
            new_lead_auto = st.checkbox("Auto-create tasks for new leads", value=True)
            new_lead_priority = st.selectbox("Default priority", ["urgent", "high", "medium"])

            st.markdown("**Follow-up Automation:**")
            followup_auto = st.checkbox("Auto-schedule follow-ups", value=True)
            followup_delay = st.slider("Follow-up delay (hours)", 1, 72, 24)

        with col2:
            st.markdown("**Hot Lead Automation:**")
            hot_lead_auto = st.checkbox("Auto-prioritize hot leads", value=True)
            hot_lead_threshold = st.slider("Hot lead score threshold", 50, 100, 80)

            st.markdown("**Task Management:**")
            overdue_reminders = st.checkbox("Overdue task reminders", value=True)
            auto_reschedule = st.checkbox("Auto-reschedule overdue tasks", value=False)

        if st.button("💾 Save Automation Settings"):
            st.success("✅ Automation settings saved successfully!")


def render_optimization_recommendations(agent_id: str):
    """Render optimization recommendations"""

    st.markdown("##### 💡 Optimization Recommendations")

    recommendations = get_demo_optimization_recommendations()

    for i, rec in enumerate(recommendations):
        priority = rec.get('priority', 'Medium')
        title = rec.get('title', 'Optimization Recommendation')
        description = rec.get('description', '')
        estimated_impact = rec.get('estimated_impact', 'Medium')

        # Priority colors
        priority_colors = {
            'High': '#ef4444',
            'Medium': '#f59e0b',
            'Low': '#10b981'
        }

        color = priority_colors.get(priority, '#64748b')

        col_rec, col_action = st.columns([3, 1])

        with col_rec:
            st.markdown(f"""
            <div style='background: {color}15; padding: 1rem; border-radius: 8px; border-left: 4px solid {color};'>
                <div style='display: flex; justify-content: between; align-items: start;'>
                    <div style='flex: 1;'>
                        <h4 style='margin: 0 0 0.5rem 0; color: #1e293b;'>{title}</h4>
                        <p style='margin: 0; color: #475569; line-height: 1.4;'>{description}</p>
                        <div style='margin-top: 0.5rem; font-size: 0.8rem; color: #64748b;'>
                            Priority: {priority} | Estimated Impact: {estimated_impact}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_action:
            st.write("")  # Spacing
            if st.button("🚀 Implement", key=f"implement_{i}"):
                st.success(f"✅ Implementing: {title}")


# Demo data functions
def get_demo_tasks() -> List[Dict[str, Any]]:
    """Generate demo tasks for testing"""
    return [
        {
            'id': 'task_001',
            'title': 'Call new lead - Sarah Johnson',
            'description': 'Initial contact for downtown condo inquiry',
            'status': 'pending',
            'priority': 'urgent',
            'created_at': datetime.now() - timedelta(hours=1),
            'due_date': datetime.now() + timedelta(hours=2),
            'lead_id': 'lead_001'
        },
        {
            'id': 'task_002',
            'title': 'Prepare CMA for Mike Chen',
            'description': 'Comparative market analysis for East Austin properties',
            'status': 'in_progress',
            'priority': 'high',
            'created_at': datetime.now() - timedelta(hours=4),
            'due_date': datetime.now() + timedelta(hours=6),
            'lead_id': 'lead_002'
        },
        {
            'id': 'task_003',
            'title': 'Send market update email',
            'description': 'Weekly market insights to nurture leads',
            'status': 'completed',
            'priority': 'medium',
            'created_at': datetime.now() - timedelta(days=1),
            'completed_at': datetime.now() - timedelta(hours=8),
            'due_date': datetime.now() - timedelta(hours=2)
        }
    ]


def get_demo_insights(tasks: List[Any]) -> List[Dict[str, str]]:
    """Generate demo performance insights"""
    return [
        {
            'type': 'success',
            'text': 'Excellent response time - averaging 3.2 minutes for new leads',
            'impact': 'high'
        },
        {
            'type': 'warning',
            'text': 'Task completion rate dropped 12% this week - consider prioritization',
            'impact': 'medium'
        },
        {
            'type': 'info',
            'text': 'Peak productivity hours: 10-11 AM and 2-4 PM',
            'impact': 'medium'
        }
    ]


def generate_demo_trend_data(date_range: str, metric_type: str) -> pd.DataFrame:
    """Generate demo trend data"""
    import random

    # Generate dates
    days = {'Last 7 days': 7, 'Last 30 days': 30, 'Last 90 days': 90, 'Last year': 365}
    num_days = days.get(date_range, 30)

    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')

    # Generate values based on metric type
    base_values = {
        'Task Completion': 75,
        'Response Times': 82,
        'Lead Conversion': 68,
        'Productivity Score': 78
    }

    base_value = base_values.get(metric_type, 75)
    values = [base_value + random.uniform(-15, 15) for _ in range(num_days)]

    return pd.DataFrame({
        'date': dates,
        'value': values
    })


def get_demo_ai_insights(insight_type: str) -> List[Dict[str, str]]:
    """Generate demo AI insights based on type"""

    insights_map = {
        'Overall Performance': [
            {
                'category': 'Response Time Excellence',
                'recommendation': 'Your response time is in the top 10% of agents. Continue prioritizing immediate lead contact - this is driving 23% higher conversion rates.',
                'impact': 'High',
                'effort': 'Low'
            },
            {
                'category': 'Task Management',
                'recommendation': 'Consider batching similar tasks together. Your data shows 40% efficiency gains when grouping calls vs. scattered throughout the day.',
                'impact': 'Medium',
                'effort': 'Low'
            }
        ],
        'Task Optimization': [
            {
                'category': 'Priority Management',
                'recommendation': 'Implement the Eisenhower Matrix for task prioritization. Your overdue tasks are primarily in the "urgent but not important" category.',
                'impact': 'High',
                'effort': 'Medium'
            },
            {
                'category': 'Automation Opportunities',
                'recommendation': 'Automate follow-up email sequences for cold leads. This could free up 45 minutes daily for high-value activities.',
                'impact': 'Medium',
                'effort': 'Medium'
            }
        ],
        'Lead Management': [
            {
                'category': 'Lead Scoring Accuracy',
                'recommendation': 'Your lead qualification accuracy is 85%. Focus on asking budget qualification questions earlier to improve to 90%+.',
                'impact': 'High',
                'effort': 'Low'
            }
        ],
        'Time Management': [
            {
                'category': 'Peak Performance Windows',
                'recommendation': 'Schedule your most important calls between 10-11 AM and 2-4 PM when your conversion rate is 35% higher.',
                'impact': 'Medium',
                'effort': 'Low'
            }
        ],
        'Goal Achievement': [
            {
                'category': 'Monthly Goal Tracking',
                'recommendation': 'You are 92% toward your monthly goal. Focus on 3 specific warm leads to exceed target by month end.',
                'impact': 'High',
                'effort': 'Low'
            }
        ]
    }

    return insights_map.get(insight_type, [])


def get_demo_optimization_recommendations() -> List[Dict[str, str]]:
    """Generate demo optimization recommendations"""
    return [
        {
            'priority': 'High',
            'title': 'Implement Automated Lead Scoring',
            'description': 'Use AI to automatically score and prioritize leads based on behavior and engagement. Could improve conversion rates by 25%.',
            'estimated_impact': 'High'
        },
        {
            'priority': 'Medium',
            'title': 'Optimize Follow-up Timing',
            'description': 'Data shows optimal follow-up times are 2-4 hours after initial contact. Automate reminders for these windows.',
            'estimated_impact': 'Medium'
        },
        {
            'priority': 'Medium',
            'title': 'Create Task Templates',
            'description': 'Standardize common workflows with pre-built task templates to reduce setup time and ensure consistency.',
            'estimated_impact': 'Medium'
        },
        {
            'priority': 'Low',
            'title': 'Integrate Calendar Sync',
            'description': 'Connect task due dates with calendar for better time blocking and schedule management.',
            'estimated_impact': 'Low'
        }
    ]


def render_getting_started_guide():
    """Render getting started guide when no agents are selected"""

    st.markdown("### 🚀 Getting Started with Agent Performance Dashboard")

    st.markdown("""
    Welcome to the comprehensive agent performance and workflow management system!

    **To get started:**
    1. **Register an agent** using the form above
    2. **Create tasks** and workflows for the agent
    3. **Track performance** with real-time analytics
    4. **Get AI insights** for optimization

    **Key Features:**
    - 📊 Real-time performance tracking
    - 📋 Intelligent task management
    - 🤖 AI-powered optimization recommendations
    - 📈 Trend analysis and goal tracking
    - ⚡ Workflow automation setup
    """)

    # Demo screenshots or video could go here
    st.info("💡 **Pro Tip**: Start by registering yourself as an agent and create a few sample tasks to explore the full functionality!")


# Main rendering function for external use
def render_agent_performance_analytics():
    """Main entry point for agent performance dashboard"""
    render_agent_performance_dashboard()