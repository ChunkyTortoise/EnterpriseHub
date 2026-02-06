import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import utils.ui as ui
from datetime import datetime, timedelta


def render():
    """
    Renders the ARETE DevOps Control Dashboard with comprehensive CI/CD monitoring.
    """
    # 1. Header Section
    ui.section_header(
        "🏗️ ARETE DevOps Control Center", "Self-Evolution Console & CI/CD Pipeline Monitor"
    )

    # 2. Enhanced Status & Metrics Row with Real-Time Data
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.animated_metric("Agent Status", "🟢 Active", delta="3 tasks", icon="🤖")
    with col2:
        ui.animated_metric("Build Pipeline", "✅ Passing", delta="2m 34s", icon="🏗️", color="success")
    with col3:
        ui.animated_metric("Test Coverage", "87.3%", delta="↑ 2.3%", icon="🧪", color="success")
    with col4:
        ui.animated_metric("Deployment", "Production", delta="v4.2.1", icon="🚀")

    ui.spacer(20)

    # 3. CI/CD Pipeline Visualization
    st.markdown("### 🔄 CI/CD Pipeline Status")

    # Pipeline stages with status
    pipeline_col1, pipeline_col2, pipeline_col3, pipeline_col4, pipeline_col5 = st.columns(5)
    
    success_bg = f"{ui.THEME['success']}15"
    success_border = ui.THEME['success']
    warning_bg = f"{ui.THEME['warning']}15"
    warning_border = ui.THEME['warning']

    with pipeline_col1:
        st.markdown(
            f"""
        <div style='text-align: center; padding: 20px; background: {success_bg}; border-radius: 8px; border-left: 4px solid {success_border};'>
            <div style='font-size: 2rem;'>✅</div>
            <div style='font-weight: 700; margin-top: 8px; color: {ui.THEME['text_main']};'>Build</div>
            <div style='font-size: 0.85rem; color: {ui.THEME['text_light']};'>2m 34s</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with pipeline_col2:
        st.markdown(
            f"""
        <div style='text-align: center; padding: 20px; background: {success_bg}; border-radius: 8px; border-left: 4px solid {success_border};'>
            <div style='font-size: 2rem;'>✅</div>
            <div style='font-weight: 700; margin-top: 8px; color: {ui.THEME['text_main']};'>Tests</div>
            <div style='font-size: 0.85rem; color: {ui.THEME['text_light']};'>220 passed</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with pipeline_col3:
        st.markdown(
            f"""
        <div style='text-align: center; padding: 20px; background: {success_bg}; border-radius: 8px; border-left: 4px solid {success_border};'>
            <div style='font-size: 2rem;'>✅</div>
            <div style='font-weight: 700; margin-top: 8px; color: {ui.THEME['text_main']};'>Security</div>
            <div style='font-size: 0.85rem; color: {ui.THEME['text_light']};'>0 vulnerabilities</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with pipeline_col4:
        st.markdown(
            f"""
        <div style='text-align: center; padding: 20px; background: {success_bg}; border-radius: 8px; border-left: 4px solid {success_border};'>
            <div style='font-size: 2rem;'>✅</div>
            <div style='font-weight: 700; margin-top: 8px; color: {ui.THEME['text_main']};'>Deploy</div>
            <div style='font-size: 0.85rem; color: {ui.THEME['text_light']};'>Staging</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with pipeline_col5:
        st.markdown(
            f"""
        <div style='text-align: center; padding: 20px; background: {warning_bg}; border-radius: 8px; border-left: 4px solid {warning_border};'>
            <div style='font-size: 2rem;'>⏳</div>
            <div style='font-weight: 700; margin-top: 8px; color: {ui.THEME['text_main']};'>Production</div>
            <div style='font-size: 0.85rem; color: {ui.THEME['text_light']};'>Awaiting approval</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    ui.spacer(30)

    # 4. Performance Metrics & Deployment History
    metrics_col, history_col = st.columns(2)
    plotly_template = ui.get_plotly_template()

    with metrics_col:
        st.markdown("### 📊 Build Performance Trends")

        # Generate sample build time data
        dates = [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14, -1, -1)
        ]
        build_times = [156, 142, 168, 134, 145, 152, 138, 154, 149, 143, 137, 145, 141, 148, 154]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=build_times,
                mode="lines+markers",
                name="Build Time",
                line=dict(color=ui.THEME["primary"], width=3),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor=f"{ui.THEME['primary']}10",
            )
        )

        fig.update_layout(
            template=plotly_template,
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Date",
            yaxis_title="Build Time (seconds)",
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

    with history_col:
        st.markdown("### 🚀 Recent Deployments")

        deployment_data = pd.DataFrame(
            {
                "Version": ["v4.2.1", "v4.2.0", "v4.1.9", "v4.1.8", "v4.1.7"],
                "Environment": ["Production", "Production", "Production", "Staging", "Production"],
                "Time": ["2 hours ago", "1 day ago", "3 days ago", "5 days ago", "1 week ago"],
                "Status": ["✅ Stable", "✅ Stable", "✅ Stable", "🧪 Testing", "✅ Stable"],
            }
        )

        st.dataframe(deployment_data, use_container_width=True, hide_index=True, height=300)

    ui.spacer(30)

    # 5. Main Control Interface with Enhanced Features
    main_col, side_col = st.columns([2, 1])

    with main_col:
        st.markdown("### 🤖 ARETE Agent Command Center")

        # Tabs for different agent functions
        agent_tab1, agent_tab2, agent_tab3 = st.tabs(
            ["💬 Task Executor", "📈 Performance Monitor", "🔍 Code Analysis"]
        )

        with agent_tab1:
            # Chat Interface
            st.info(
                "🟢 **System Ready:** Neural engine initialized. Connected to GitHub API & CI/CD pipelines."
            )

            task = st.chat_input(
                "Instruct ARETE to modify the codebase (e.g., 'Add a new feature to the pricing module')..."
            )

            if task:
                # 1. User Message
                with st.chat_message("user"):
                    st.write(task)

                # 2. Agent Thinking (Simulated connection to LangGraph)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing codebase architecture..."):
                        st.markdown("**Execution Plan:**")
                        st.code(
                            """
1. SEARCH: 'pricing_module.py' and 'test_pricing.py'
2. ANALYSIS: Identify extension points for requested feature
3. BRANCH: Create 'feature/pricing-update-v2'
4. IMPLEMENT: Apply changes with best practices
5. TEST: Run unit tests (220 tests)
6. VERIFY: Check code coverage (target: >85%)
7. PR: Create pull request with detailed description
                        """,
                            language="yaml",
                        )

                        st.success("✅ **Execution Complete:** PR #42 Created & Pipeline Triggered")
                        st.markdown(
                            "[View Pull Request →](https://github.com/ChunkyTortoise/enterprise-hub/pulls)"
                        )

        with agent_tab2:
            st.markdown("#### 🎯 Agent Performance Metrics")

            perf_col1, perf_col2, perf_col3 = st.columns(3)

            with perf_col1:
                ui.animated_metric("Tasks Completed", "1,247", delta="+12", icon="✅")
            with perf_col2:
                ui.animated_metric("Avg Response Time", "3.2s", delta="-0.4s", icon="⚡")
            with perf_col3:
                ui.animated_metric("Success Rate", "97.8%", delta="+1.2%", icon="📈", color="success")

            # Task completion over time
            task_dates = [
                (datetime.now() - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)
            ]
            tasks_completed = [42, 38, 45, 51, 47, 43, 49]

            fig_tasks = go.Figure()
            fig_tasks.add_trace(
                go.Bar(
                    x=task_dates, y=tasks_completed, marker_color=ui.THEME["accent"], name="Tasks Completed"
                )
            )

            fig_tasks.update_layout(
                template=plotly_template,
                title="Daily Task Completion",
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
            )

            st.plotly_chart(fig_tasks, use_container_width=True)

        with agent_tab3:
            st.markdown("#### 🔎 Codebase Health Analysis")

            # Code quality metrics
            quality_col1, quality_col2 = st.columns(2)

            with quality_col1:
                st.markdown("**Code Complexity Distribution**")

                complexity_data = pd.DataFrame(
                    {
                        "Complexity": ["Low", "Medium", "High", "Very High"],
                        "Files": [142, 38, 12, 3],
                    }
                )

                fig_complexity = px.pie(
                    complexity_data,
                    values="Files",
                    names="Complexity",
                    color_discrete_sequence=[ui.THEME["success"], ui.THEME["warning"], ui.THEME["danger"], ui.THEME["primary"]],
                )

                fig_complexity.update_layout(
                    template=plotly_template,
                    height=250, 
                    margin=dict(l=20, r=20, t=20, b=20)
                )

                st.plotly_chart(fig_complexity, use_container_width=True)

            with quality_col2:
                st.markdown("**Test Coverage by Module**")

                coverage_data = pd.DataFrame(
                    {
                        "Module": ["Financial", "Marketing", "Data", "UI", "Utils"],
                        "Coverage": [92, 88, 85, 79, 94],
                    }
                )

                fig_coverage = go.Figure()
                fig_coverage.add_trace(
                    go.Bar(
                        x=coverage_data["Module"],
                        y=coverage_data["Coverage"],
                        marker_color=[ui.THEME["success"] if x > 85 else ui.THEME["warning"] for x in coverage_data["Coverage"]],
                        text=coverage_data["Coverage"].apply(lambda x: f"{x}%"),
                        textposition="outside",
                    )
                )

                fig_coverage.update_layout(
                    template=plotly_template,
                    height=250,
                    margin=dict(l=20, r=20, t=20, b=20),
                    yaxis=dict(range=[0, 100], title="Coverage %"),
                )

                st.plotly_chart(fig_coverage, use_container_width=True)

        ui.spacer(20)

        # Activity Log with Enhanced Details
        st.markdown("### 📜 Recent Agent Actions & System Events")
        activity_data = pd.DataFrame(
            {
                "Timestamp": [
                    "10:42 AM",
                    "10:15 AM",
                    "09:47 AM",
                    "09:15 AM",
                    "08:52 AM",
                    "Yesterday 4:30 PM",
                ],
                "Action": [
                    "Code Commit",
                    "PR Merged",
                    "Security Scan",
                    "Test Run",
                    "Deployment",
                    "Self-Correction",
                ],
                "Details": [
                    "Updated utils/ui.py - Enhanced metric cards",
                    "Merged feature/pricing-update into main",
                    "Completed vulnerability scan - 0 issues found",
                    "Passed 220 tests in 2m 34s",
                    "Deployed v4.2.1 to staging environment",
                    "Fixed import error in modules/auth.py",
                ],
                "Status": [
                    "✅ Success",
                    "✅ Success",
                    "✅ Clean",
                    "✅ Success",
                    "✅ Deployed",
                    "✅ Resolved",
                ],
                "Impact": ["Low", "High", "Medium", "Medium", "High", "Low"],
            }
        )
        st.dataframe(
            activity_data.style.set_properties(**{'background-color': f"{ui.THEME['surface']}"}),
            use_container_width=True, 
            hide_index=True, 
            height=250
        )

    with side_col:
        st.markdown("### 🧠 System Memory")

        # Business Context Card
        ui.glassmorphic_card(
            title="Business Context",
            content="""
            **Goal:** Build self-maintaining AI<br>
            **Stack:** Claude 3.5, LangGraph, Flask<br>
            **Deploy:** AWS Lambda / Streamlit Cloud
            """,
            icon="🏢",
        )

        ui.spacer(20)

        # Tech Stack Card
        ui.glassmorphic_card(
            title="Capabilities",
            content="""
            ✅ **File I/O:** Read/Write Access<br>
            ✅ **Git:** Commit, Push, PR<br>
            ✅ **Tests:** Run pytest suite<br>
            ✅ **Deploy:** Trigger CI/CD
            """,
            icon="🛠️",
        )

    # 4. Footer Credentials
    ui.spacer(40)
    st.caption("🔒 Authenticated as Root Admin. All actions are logged and version-controlled.")
