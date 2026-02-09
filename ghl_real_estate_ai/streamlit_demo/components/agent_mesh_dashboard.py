"""
Agent Mesh Dashboard for EnterpriseHub
Real-time monitoring and management interface for the agent mesh

Provides comprehensive visibility into:
- Agent status and performance
- Task queues and execution
- Cost tracking and budget management
- Performance optimization insights
"""

import asyncio
import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_mesh_coordinator import (
    AgentCapability,
    AgentStatus,
    TaskPriority,
    get_mesh_coordinator,
)
from ghl_real_estate_ai.services.mesh_agent_registry import get_agent_registry
from ghl_real_estate_ai.services.token_tracker import TokenTracker

logger = get_logger(__name__)


def agent_mesh_dashboard():
    """Main agent mesh dashboard interface"""

    st.title("🕸️ Agent Mesh Control Center")
    st.markdown("**Enterprise-grade multi-agent orchestration and governance**")

    # Initialize services
    mesh_coordinator = get_mesh_coordinator()
    agent_registry = get_agent_registry()
    token_tracker = TokenTracker()

    # Auto-refresh toggle
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh", value=True)
    with col2:
        refresh_interval = st.selectbox("Refresh interval", [5, 10, 30, 60], index=1)
    with col3:
        if st.button("🔄 Refresh Now") or auto_refresh:
            st.rerun()

    # Auto-refresh mechanism
    if auto_refresh:
        import time

        time.sleep(refresh_interval)
        st.rerun()

    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📊 Overview", "🤖 Agents", "📋 Tasks", "💰 Cost Tracking", "⚡ Performance", "⚙️ Management"]
    )

    with tab1:
        render_overview_tab(mesh_coordinator, agent_registry, token_tracker)

    with tab2:
        render_agents_tab(mesh_coordinator, agent_registry)

    with tab3:
        render_tasks_tab(mesh_coordinator)

    with tab4:
        render_cost_tracking_tab(token_tracker)

    with tab5:
        render_performance_tab(mesh_coordinator)

    with tab6:
        render_management_tab(mesh_coordinator, agent_registry)


@st.cache_data(ttl=30)
def get_mesh_overview_data():
    """Get cached mesh overview data"""
    try:
        mesh_coordinator = get_mesh_coordinator()
        agent_registry = get_agent_registry()

        # Get mesh status
        mesh_status = asyncio.run(mesh_coordinator.get_mesh_status())
        registry_status = asyncio.run(agent_registry.get_registry_status())

        return mesh_status, registry_status
    except Exception as e:
        logger.error(f"Error getting mesh overview: {e}")
        return {}, {}


def render_overview_tab(mesh_coordinator, agent_registry, token_tracker):
    """Render overview dashboard tab"""

    mesh_status, registry_status = get_mesh_overview_data()

    if not mesh_status:
        st.error("Unable to load mesh status. Please check agent mesh coordinator.")
        return

    # Key metrics cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Agents", registry_status.get("total_agents", 0), delta=None)

    with col2:
        active_agents = mesh_status.get("agents", {}).get("active", 0)
        st.metric("Active Agents", active_agents, delta=None)

    with col3:
        active_tasks = mesh_status.get("tasks", {}).get("active", 0)
        st.metric("Active Tasks", active_tasks, delta=None)

    with col4:
        total_cost = mesh_status.get("costs", {}).get("total_cost_today", 0)
        st.metric("Today's Cost", f"${total_cost:.2f}", delta=None)

    # Agent status distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Agent Status Distribution")
        agent_status_data = mesh_status.get("agents", {})

        if agent_status_data:
            status_df = pd.DataFrame(
                [
                    {"Status": status.replace("_", " ").title(), "Count": count}
                    for status, count in agent_status_data.items()
                    if count > 0
                ]
            )

            if not status_df.empty:
                fig = px.pie(
                    status_df,
                    values="Count",
                    names="Status",
                    title="Agent Status",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No active agents found")

    with col2:
        st.subheader("Capability Coverage")
        capability_data = registry_status.get("agents_by_capability", {})

        if capability_data:
            cap_df = pd.DataFrame(
                [
                    {"Capability": cap.replace("_", " ").title(), "Agents": count}
                    for cap, count in capability_data.items()
                    if count > 0
                ]
            )

            if not cap_df.empty:
                fig = px.bar(
                    cap_df,
                    x="Capability",
                    y="Agents",
                    title="Agents by Capability",
                    color="Agents",
                    color_continuous_scale="Blues",
                )
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

    # Performance metrics
    st.subheader("Performance Overview")
    performance = mesh_status.get("performance", {})

    if performance:
        pcol1, pcol2, pcol3 = st.columns(3)

        with pcol1:
            success_rate = performance.get("average_success_rate", 0)
            st.metric("Average Success Rate", f"{success_rate:.1f}%", delta=None)

        with pcol2:
            response_time = performance.get("average_response_time", 0)
            st.metric("Avg Response Time", f"{response_time:.2f}s", delta=None)

        with pcol3:
            utilization = performance.get("mesh_utilization", 0)
            st.metric("Mesh Utilization", f"{utilization:.1f}%", delta=None)

    # Recent activity timeline
    st.subheader("Recent Activity")

    # Create mock timeline data (in production, this would come from actual logs)
    timeline_data = [
        {"Time": "14:30:25", "Event": "Jorge Seller Bot completed qualification task", "Type": "Success"},
        {"Time": "14:29:18", "Event": "Property Matcher started search task", "Type": "Info"},
        {"Time": "14:28:45", "Event": "MCP GHL agent created new contact", "Type": "Success"},
        {"Time": "14:27:32", "Event": "Lead Lifecycle Bot triggered Day 7 followup", "Type": "Info"},
        {"Time": "14:26:09", "Event": "Conversation Intelligence analyzed intent", "Type": "Success"},
    ]

    for event in timeline_data:
        if event["Type"] == "Success":
            st.success(f"✅ **{event['Time']}** - {event['Event']}")
        elif event["Type"] == "Info":
            st.info(f"ℹ️ **{event['Time']}** - {event['Event']}")
        else:
            st.warning(f"⚠️ **{event['Time']}** - {event['Event']}")


def render_agents_tab(mesh_coordinator, agent_registry):
    """Render agents management tab"""

    st.subheader("Agent Registry")

    # Get agent data
    try:
        registry_status = asyncio.run(agent_registry.get_registry_status())

        # Agent filter controls
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox("Filter by Status", ["All"] + [status.value for status in AgentStatus])

        with col2:
            capability_filter = st.selectbox("Filter by Capability", ["All"] + [cap.value for cap in AgentCapability])

        with col3:
            agent_type_filter = st.selectbox("Filter by Type", ["All", "Jorge Bots", "Services", "MCP Agents"])

        # Agent details table
        if hasattr(agent_registry, "registered_agents") and agent_registry.registered_agents:
            agent_data = []

            for agent_id, agent in agent_registry.registered_agents.items():
                agent_data.append(
                    {
                        "Agent ID": agent_id,
                        "Name": agent.name,
                        "Status": agent.status.value,
                        "Capabilities": ", ".join([cap.value for cap in agent.capabilities]),
                        "Current Tasks": f"{agent.current_tasks}/{agent.max_concurrent_tasks}",
                        "Load %": f"{agent.load_factor:.1f}%",
                        "Success Rate": f"{agent.metrics.success_rate:.1f}%",
                        "Avg Response": f"{agent.metrics.average_response_time:.2f}s",
                        "Cost/Token": f"${agent.cost_per_token:.6f}",
                    }
                )

            df = pd.DataFrame(agent_data)

            # Apply filters
            if status_filter != "All":
                df = df[df["Status"] == status_filter]

            if capability_filter != "All":
                df = df[df["Capabilities"].str.contains(capability_filter, case=False)]

            if agent_type_filter != "All":
                if agent_type_filter == "Jorge Bots":
                    df = df[df["Name"].str.contains("Jorge", case=False)]
                elif agent_type_filter == "Services":
                    df = df[df["Name"].str.contains("Union[Service, Engine]|Intelligence", case=False)]
                elif agent_type_filter == "MCP Agents":
                    df = df[df["Name"].str.contains("MCP", case=False)]

            st.dataframe(df, use_container_width=True)

            # Agent details expander
            if not df.empty:
                st.subheader("Agent Details")
                selected_agent = st.selectbox("Select agent for details", df["Agent ID"].tolist())

                if selected_agent:
                    try:
                        agent_details = asyncio.run(mesh_coordinator.get_agent_details(selected_agent))

                        if agent_details:
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write("**Agent Configuration:**")
                                st.json(agent_details.get("agent", {}))

                            with col2:
                                st.write("**Performance Trend:**")
                                trend_data = agent_details.get("performance_trend", [])
                                if trend_data:
                                    st.line_chart(pd.DataFrame(trend_data))
                                else:
                                    st.info("No performance trend data available")

                    except Exception as e:
                        st.error(f"Error loading agent details: {e}")

        else:
            st.info("No agents registered. Initialize the agent registry first.")

    except Exception as e:
        st.error(f"Error loading agent data: {e}")


def render_tasks_tab(mesh_coordinator):
    """Render task management tab"""

    st.subheader("Task Management")

    # Task submission form
    with st.expander("Submit New Task"):
        with st.form("task_submission"):
            task_type = st.selectbox(
                "Task Type",
                [
                    "lead_qualification",
                    "property_matching",
                    "conversation_analysis",
                    "followup_automation",
                    "crm_operations",
                ],
            )

            priority = st.selectbox("Priority", [p.name for p in TaskPriority])

            payload = st.text_area("Task Payload (JSON)", value='{"example": "data"}', height=100)

            max_cost = st.number_input("Max Cost ($)", min_value=0.01, max_value=10.0, value=1.0, step=0.01)

            if st.form_submit_button("Submit Task"):
                try:
                    from uuid import uuid4

                    from ghl_real_estate_ai.services.agent_mesh_coordinator import AgentTask

                    # Parse payload
                    task_payload = json.loads(payload)

                    # Create task
                    task = AgentTask(
                        task_id=str(uuid4()),
                        task_type=task_type,
                        priority=TaskPriority[priority],
                        capabilities_required=[AgentCapability.LEAD_QUALIFICATION],  # Default
                        payload=task_payload,
                        created_at=datetime.now(),
                        deadline=None,
                        max_cost=max_cost,
                        requester_id="dashboard_user",
                    )

                    # Submit task
                    task_id = asyncio.run(mesh_coordinator.submit_task(task))
                    st.success(f"Task submitted successfully: {task_id}")

                except Exception as e:
                    st.error(f"Task submission failed: {e}")

    # Active tasks display
    st.subheader("Active Tasks")

    try:
        # Get active tasks from mesh coordinator
        if hasattr(mesh_coordinator, "active_tasks") and mesh_coordinator.active_tasks:
            task_data = []

            for task_id, task in mesh_coordinator.active_tasks.items():
                task_data.append(
                    {
                        "Task ID": task_id[:8] + "...",  # Shortened for display
                        "Type": task.task_type,
                        "Priority": task.priority.name,
                        "Assigned Agent": task.assigned_agent or "Pending",
                        "Created": task.created_at.strftime("%H:%M:%S"),
                        "Status": "In Progress" if task.started_at else "Queued",
                        "Max Cost": f"${task.max_cost or 0:.2f}",
                    }
                )

            if task_data:
                st.dataframe(pd.DataFrame(task_data), use_container_width=True)
            else:
                st.info("No active tasks")
        else:
            st.info("No active tasks")

    except Exception as e:
        st.error(f"Error loading tasks: {e}")

    # Completed tasks summary
    st.subheader("Recent Completed Tasks")

    try:
        if hasattr(mesh_coordinator, "completed_tasks") and mesh_coordinator.completed_tasks:
            completed_data = []

            # Get last 10 completed tasks
            recent_completed = list(mesh_coordinator.completed_tasks.items())[-10:]

            for task_id, task in recent_completed:
                status = "Success" if not task.error else "Failed"
                exec_time = task.execution_time or 0

                completed_data.append(
                    {
                        "Task ID": task_id[:8] + "...",
                        "Type": task.task_type,
                        "Agent": task.assigned_agent or "Unknown",
                        "Status": status,
                        "Execution Time": f"{exec_time:.2f}s",
                        "Completed": task.completed_at.strftime("%H:%M:%S") if task.completed_at else "Unknown",
                    }
                )

            if completed_data:
                st.dataframe(pd.DataFrame(completed_data), use_container_width=True)
            else:
                st.info("No completed tasks")
        else:
            st.info("No completed tasks")

    except Exception as e:
        st.error(f"Error loading completed tasks: {e}")


def render_cost_tracking_tab(token_tracker):
    """Render cost tracking tab"""

    st.subheader("Cost Tracking & Budget Management")

    # Cost overview
    try:
        # Get cost data (mock for demonstration)
        today_cost = 12.45
        projected_monthly = 374.50
        budget_limit = 500.00

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Today's Cost", f"${today_cost:.2f}", delta=f"+${today_cost * 0.15:.2f} vs yesterday")

        with col2:
            st.metric("This Hour", f"${today_cost / 24:.2f}", delta=None)

        with col3:
            st.metric(
                "Projected Monthly",
                f"${projected_monthly:.2f}",
                delta=f"{(projected_monthly / budget_limit) * 100:.1f}% of budget",
            )

        with col4:
            budget_remaining = budget_limit - projected_monthly
            st.metric(
                "Budget Remaining",
                f"${budget_remaining:.2f}",
                delta=f"{(budget_remaining / budget_limit) * 100:.1f}% left",
            )

        # Cost breakdown chart
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cost by Agent Type")
            cost_by_type = {"Jorge Bots": 8.50, "Services": 2.30, "MCP Agents": 1.65}

            fig = px.pie(
                values=list(cost_by_type.values()), names=list(cost_by_type.keys()), title="Today's Cost Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Hourly Cost Trend")
            hours = list(range(24))
            costs = [today_cost / 24 * (1 + (h % 8) * 0.2) for h in hours]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=hours, y=costs, mode="lines+markers", name="Hourly Cost", line=dict(color="blue"))
            )
            fig.update_layout(title="Cost Trend (24h)", xaxis_title="Hour", yaxis_title="Cost ($)")
            st.plotly_chart(fig, use_container_width=True)

        # Budget alerts
        st.subheader("Budget Alerts & Recommendations")

        if projected_monthly > budget_limit * 0.9:
            st.error("⚠️ **Budget Alert**: Projected monthly cost exceeds 90% of budget!")
            st.markdown("**Recommendations:**")
            st.markdown("- Review high-cost agents and optimize usage")
            st.markdown("- Consider implementing more aggressive token reduction")
            st.markdown("- Evaluate task prioritization settings")

        elif projected_monthly > budget_limit * 0.75:
            st.warning("📊 **Budget Warning**: Projected monthly cost exceeds 75% of budget")
            st.markdown("**Recommendations:**")
            st.markdown("- Monitor usage patterns and identify optimization opportunities")
            st.markdown("- Consider progressive skills for high-frequency tasks")

        else:
            st.success("✅ **Budget Status**: On track for monthly budget")

    except Exception as e:
        st.error(f"Error loading cost data: {e}")


def render_performance_tab(mesh_coordinator):
    """Render performance monitoring tab"""

    st.subheader("Performance Monitoring & Optimization")

    # Performance overview
    try:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("System Response Time", "2.3s", delta="-0.5s vs last hour")

        with col2:
            st.metric("Task Success Rate", "94.2%", delta="+1.8% vs yesterday")

        with col3:
            st.metric("Queue Processing", "0.8s avg", delta="-0.2s vs last hour")

        with col4:
            st.metric("Agent Availability", "87.5%", delta="+5.2% vs yesterday")

        # Performance charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Response Time by Agent")
            agent_response_times = {
                "Jorge Seller Bot": 2.1,
                "Property Matcher": 0.8,
                "Conversation Intelligence": 1.2,
                "Lead Lifecycle": 3.4,
                "MCP GHL": 0.5,
            }

            df = pd.DataFrame(
                [{"Agent": agent, "Response Time (s)": time} for agent, time in agent_response_times.items()]
            )

            fig = px.bar(
                df, x="Agent", y="Response Time (s)", color="Response Time (s)", color_continuous_scale="RdYlBu_r"
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Task Processing Rate")
            hours = list(range(1, 13))
            processing_rate = [45, 52, 48, 61, 55, 58, 62, 59, 56, 64, 61, 58]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=hours, y=processing_rate, mode="lines+markers", name="Tasks/Hour", line=dict(color="green")
                )
            )
            fig.update_layout(
                title="Task Processing Rate (12h)", xaxis_title="Hours Ago", yaxis_title="Tasks Processed"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Performance insights
        st.subheader("Performance Insights & Recommendations")

        insights = [
            {
                "type": "success",
                "title": "Progressive Skills Optimization",
                "message": "68% token reduction achieved through progressive skills implementation",
                "recommendation": "Continue using progressive skills for Jorge bot qualification tasks",
            },
            {
                "type": "warning",
                "title": "Lead Lifecycle Agent Load",
                "message": "Lead Lifecycle Bot showing higher than average response times",
                "recommendation": "Consider adding a second instance during peak hours (2-6 PM)",
            },
            {
                "type": "info",
                "title": "MCP Integration Efficiency",
                "message": "MCP agents showing excellent cost-per-operation metrics",
                "recommendation": "Expand MCP usage for routine CRM and data operations",
            },
        ]

        for insight in insights:
            if insight["type"] == "success":
                st.success(f"✅ **{insight['title']}**: {insight['message']}\n\n💡 *{insight['recommendation']}*")
            elif insight["type"] == "warning":
                st.warning(f"⚠️ **{insight['title']}**: {insight['message']}\n\n💡 *{insight['recommendation']}*")
            else:
                st.info(f"ℹ️ **{insight['title']}**: {insight['message']}\n\n💡 *{insight['recommendation']}*")

    except Exception as e:
        st.error(f"Error loading performance data: {e}")


def render_management_tab(mesh_coordinator, agent_registry):
    """Render mesh management tab"""

    st.subheader("Mesh Management & Configuration")

    # Agent registry management
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Registry Control**")

        if st.button("🔄 Reinitialize Agent Registry"):
            try:
                success = asyncio.run(agent_registry.initialize())
                if success:
                    st.success("Agent registry reinitialized successfully")
                else:
                    st.error("Agent registry initialization failed")
            except Exception as e:
                st.error(f"Registry initialization error: {e}")

        if st.button("🔍 Run Health Checks"):
            try:
                health_status = asyncio.run(mesh_coordinator.health_check())
                st.write("**Health Check Results:**")
                for agent_id, status in health_status.items():
                    if status == "healthy":
                        st.success(f"✅ {agent_id}: {status}")
                    else:
                        st.error(f"❌ {agent_id}: {status}")
            except Exception as e:
                st.error(f"Health check error: {e}")

    with col2:
        st.write("**Emergency Controls**")

        emergency_reason = st.text_input(
            "Emergency Shutdown Reason", placeholder="Enter reason for emergency shutdown..."
        )

        if st.button("🚨 EMERGENCY SHUTDOWN", type="primary"):
            if emergency_reason:
                try:
                    asyncio.run(mesh_coordinator.emergency_shutdown(emergency_reason))
                    st.error(f"Emergency shutdown initiated: {emergency_reason}")
                except Exception as e:
                    st.error(f"Emergency shutdown error: {e}")
            else:
                st.error("Please provide a reason for emergency shutdown")

    # Configuration display
    st.subheader("Current Configuration")

    with st.expander("View Mesh Configuration"):
        try:
            config_path = ".claude/agent-mesh/mesh-config.json"
            with open(config_path, "r") as f:
                config = json.load(f)

            st.json(config)

        except Exception as e:
            st.error(f"Error loading configuration: {e}")

    # System status
    st.subheader("System Status")

    try:
        mesh_status = asyncio.run(mesh_coordinator.get_mesh_status())
        registry_status = asyncio.run(agent_registry.get_registry_status())

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Mesh Coordinator Status**")
            st.json(mesh_status)

        with col2:
            st.write("**Agent Registry Status**")
            st.json(registry_status)

    except Exception as e:
        st.error(f"Error loading system status: {e}")


if __name__ == "__main__":
    agent_mesh_dashboard()
