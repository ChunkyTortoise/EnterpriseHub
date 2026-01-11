"""
Agent Onboarding Dashboard Streamlit Component

Interactive interface for managing agent onboarding, training progress,
skill assessments, and mentorship programs with Claude integration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from services.agent_onboarding_service import (
    agent_onboarding_service,
    OnboardingStage,
    TrainingModule,
    SkillLevel,
    AssessmentType,
    start_agent_onboarding,
    get_training_plan,
    conduct_assessment,
    assign_agent_mentor
)


def render_agent_onboarding_dashboard():
    """Render the agent onboarding dashboard interface."""
    st.header("🎓 Agent Onboarding & Training")
    st.markdown("*AI-powered onboarding and skill development platform*")

    # Role-based view selection
    user_role = st.selectbox(
        "Select Your Role",
        options=["New Agent", "Training Manager", "Mentor", "Administrator"],
        help="Choose your role to see relevant features"
    )

    if user_role == "New Agent":
        render_agent_view()
    elif user_role == "Training Manager":
        render_manager_view()
    elif user_role == "Mentor":
        render_mentor_view()
    else:  # Administrator
        render_admin_view()


def render_agent_view():
    """Render the new agent onboarding view."""
    st.subheader("👋 Welcome to Your Training Journey")

    # Agent selection (in real app, this would be the logged-in user)
    agent_id = st.selectbox(
        "Agent Profile",
        options=["new_agent_001", "new_agent_002", "new_agent_003", "trainee_agent_004"],
        help="Select agent profile (in production, this would be automatic)"
    )

    # Get or create agent progress
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        progress = loop.run_until_complete(agent_onboarding_service.get_agent_progress(agent_id))

        # If no progress exists, show onboarding start
        if not progress:
            st.info("🚀 Ready to start your real estate career journey!")

            col1, col2 = st.columns(2)
            with col1:
                workflow_type = st.selectbox(
                    "Training Path",
                    options=["new_agent_onboarding", "experienced_agent_onboarding"],
                    format_func=lambda x: {
                        "new_agent_onboarding": "Complete New Agent Program",
                        "experienced_agent_onboarding": "Experienced Agent Fast-Track"
                    }.get(x, x)
                )

            with col2:
                focus_areas = st.multiselect(
                    "Areas of Interest",
                    options=[
                        "Residential Sales", "Luxury Properties", "Investment Properties",
                        "Commercial Real Estate", "First-Time Buyers", "Market Analysis"
                    ],
                    help="Select areas you want to focus on"
                )

            if st.button("🎯 Start My Training Journey", type="primary"):
                custom_options = {"focus_areas": focus_areas} if focus_areas else None
                progress = loop.run_until_complete(
                    start_agent_onboarding(agent_id, workflow_type, custom_options)
                )
                st.success("✅ Onboarding started! Refresh the page to see your progress.")
                st.experimental_rerun()

        else:
            # Show existing progress
            render_agent_progress(agent_id, progress)

        loop.close()

    except Exception as e:
        st.error(f"Error loading agent progress: {str(e)}")


def render_agent_progress(agent_id: str, progress):
    """Render individual agent progress dashboard."""
    # Progress overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Training Progress",
            f"{progress.completion_percentage:.0f}%",
            delta=f"{progress.completion_percentage - 75:.0f}%" if progress.completion_percentage > 75 else None
        )

    with col2:
        st.metric(
            "Current Stage",
            progress.current_stage.value.replace('_', ' ').title(),
            delta="Active"
        )

    with col3:
        st.metric(
            "Training Hours",
            f"{progress.total_training_hours:.1f}",
            delta=f"+{progress.total_training_hours - 20:.1f}" if progress.total_training_hours > 20 else None
        )

    with col4:
        st.metric(
            "Modules Completed",
            len(progress.completed_modules),
            delta=f"+{len(progress.completed_modules)}"
        )

    # Progress visualization
    st.subheader("📊 Your Training Progress")

    # Create progress bar
    progress_data = {
        "Stage": [stage.value.replace('_', ' ').title() for stage in OnboardingStage],
        "Status": []
    }

    current_stage_index = list(OnboardingStage).index(progress.current_stage)
    for i, stage in enumerate(OnboardingStage):
        if i < current_stage_index:
            progress_data["Status"].append("Completed")
        elif i == current_stage_index:
            progress_data["Status"].append("Current")
        else:
            progress_data["Status"].append("Upcoming")

    progress_df = pd.DataFrame(progress_data)

    # Color mapping
    color_map = {"Completed": "#10b981", "Current": "#3b82f6", "Upcoming": "#e5e7eb"}
    fig = px.bar(
        progress_df,
        x="Stage",
        color="Status",
        color_discrete_map=color_map,
        title="Onboarding Stage Progress"
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    # Current recommendations
    st.subheader("🎯 Recommended Next Steps")

    if progress.next_recommended_modules:
        for i, module_id in enumerate(progress.next_recommended_modules):
            module = agent_onboarding_service.training_content.get(module_id)
            if module:
                with st.expander(f"📚 {module.title}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Description:** {module.description}")
                        st.write(f"**Module:** {module.module.value.replace('_', ' ').title()}")
                        st.write(f"**Duration:** {module.estimated_duration} minutes")

                        if module.learning_objectives:
                            st.write("**Learning Objectives:**")
                            for objective in module.learning_objectives:
                                st.write(f"• {objective}")

                    with col2:
                        difficulty_color = {
                            SkillLevel.BEGINNER: "green",
                            SkillLevel.DEVELOPING: "blue",
                            SkillLevel.COMPETENT: "orange",
                            SkillLevel.PROFICIENT: "red",
                            SkillLevel.EXPERT: "purple"
                        }.get(module.difficulty_level, "gray")

                        st.markdown(
                            f"<span style='color: {difficulty_color}; font-weight: bold;'>"
                            f"Level: {module.difficulty_level.value.title()}</span>",
                            unsafe_allow_html=True
                        )

                        if st.button(f"▶️ Start Module", key=f"start_module_{i}"):
                            start_training_module(agent_id, module)

    else:
        st.info("🎉 Great job! You've completed all current recommendations. Check back for new content!")

    # Skill levels overview
    if progress.skill_levels:
        st.subheader("🏆 Your Skills Profile")

        skills_data = {
            "Skill": [skill.replace('_', ' ').title() for skill in progress.skill_levels.keys()],
            "Level": [level.value.title() for level in progress.skill_levels.values()],
            "Score": [
                {"beginner": 1, "developing": 2, "competent": 3, "proficient": 4, "expert": 5}[level.value]
                for level in progress.skill_levels.values()
            ]
        }

        skills_df = pd.DataFrame(skills_data)

        fig = px.bar(
            skills_df,
            x="Skill",
            y="Score",
            color="Level",
            title="Current Skill Levels",
            labels={"Score": "Skill Level (1-5)"}
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    # Areas for improvement
    if progress.weak_areas or progress.strong_areas:
        col1, col2 = st.columns(2)

        with col1:
            if progress.strong_areas:
                st.subheader("💪 Your Strengths")
                for area in progress.strong_areas:
                    st.success(f"✓ {area.replace('_', ' ').title()}")

        with col2:
            if progress.weak_areas:
                st.subheader("🎯 Focus Areas")
                for area in progress.weak_areas:
                    st.warning(f"📈 {area.replace('_', ' ').title()}")

    # Training calendar/schedule
    st.subheader("📅 Training Schedule")
    render_training_schedule(agent_id)


def render_training_schedule(agent_id: str):
    """Render training schedule for an agent."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        training_plan = loop.run_until_complete(get_training_plan(agent_id))
        loop.close()

        if training_plan and training_plan.get("recommended_modules"):
            # Create schedule
            today = datetime.now().date()
            schedule_data = []

            for i, module in enumerate(training_plan["recommended_modules"]):
                start_date = today + timedelta(days=i * 2)  # Space modules 2 days apart
                schedule_data.append({
                    "Module": module["title"],
                    "Start Date": start_date,
                    "Duration (hours)": module["estimated_duration"] / 60,
                    "Priority": module["priority"],
                    "Status": "Scheduled"
                })

            schedule_df = pd.DataFrame(schedule_data)
            st.dataframe(schedule_df, use_container_width=True)

            if training_plan.get("estimated_completion"):
                completion_date = training_plan["estimated_completion"].date()
                st.info(f"🎯 Estimated completion date: {completion_date}")

    except Exception as e:
        st.error(f"Error loading training schedule: {str(e)}")


def render_manager_view():
    """Render training manager dashboard."""
    st.subheader("📋 Training Management Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Agent Overview",
        "📊 Analytics",
        "📚 Content Management",
        "🎯 Assessments"
    ])

    with tab1:
        render_agents_overview()

    with tab2:
        render_training_analytics()

    with tab3:
        render_content_management()

    with tab4:
        render_assessment_management()


def render_agents_overview():
    """Render overview of all agents in training."""
    st.subheader("👥 Agents in Training")

    try:
        # Get all agent progress
        all_agents = list(agent_onboarding_service.agent_progress.values())

        if not all_agents:
            st.info("No agents currently in training. Start onboarding new agents!")
            return

        # Create agents summary
        agents_data = []
        for progress in all_agents:
            agents_data.append({
                "Agent ID": progress.agent_id,
                "Stage": progress.current_stage.value.replace('_', ' ').title(),
                "Progress": f"{progress.completion_percentage:.0f}%",
                "Training Hours": f"{progress.total_training_hours:.1f}",
                "Modules Completed": len(progress.completed_modules),
                "Last Activity": progress.last_activity.strftime('%Y-%m-%d') if progress.last_activity else "N/A",
                "Status": get_training_status(progress)
            })

        agents_df = pd.DataFrame(agents_data)

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Agents", len(agents_df))
        with col2:
            active_agents = len([a for a in agents_data if a["Status"] == "Active"])
            st.metric("Active Agents", active_agents)
        with col3:
            avg_progress = agents_df["Progress"].str.rstrip('%').astype(float).mean()
            st.metric("Avg Progress", f"{avg_progress:.0f}%")
        with col4:
            completed_agents = len([a for a in agents_data if a["Progress"] == "100%"])
            st.metric("Completed", completed_agents)

        # Agents table
        st.dataframe(agents_df, use_container_width=True)

        # Stage distribution chart
        stage_counts = agents_df["Stage"].value_counts()
        fig = px.pie(
            values=stage_counts.values,
            names=stage_counts.index,
            title="Agents by Training Stage"
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading agents overview: {str(e)}")


def render_training_analytics():
    """Render training analytics and insights."""
    st.subheader("📊 Training Analytics")

    try:
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=30),
                help="Analytics start date"
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                help="Analytics end date"
            )

        # Get analytics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(
            agent_onboarding_service.get_onboarding_analytics(
                (datetime.combine(start_date, datetime.min.time()),
                 datetime.combine(end_date, datetime.max.time()))
            )
        )
        loop.close()

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Agents in Training", analytics["total_agents_onboarding"])
        with col2:
            completion_rate = analytics.get("overall_completion_rate", 0) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        with col3:
            avg_hours = analytics.get("average_training_hours", 0)
            st.metric("Avg Training Hours", f"{avg_hours:.1f}")
        with col4:
            session_score = analytics.get("average_session_score", 0) * 100
            st.metric("Avg Session Score", f"{session_score:.1f}%")

        # Stage distribution
        if analytics.get("stage_distribution"):
            st.subheader("Stage Distribution")
            stage_data = analytics["stage_distribution"]
            fig = px.bar(
                x=list(stage_data.keys()),
                y=list(stage_data.values()),
                title="Agents by Training Stage",
                labels={"x": "Stage", "y": "Number of Agents"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        # Module completion rates
        if analytics.get("module_completion_rates"):
            st.subheader("Module Completion Rates")
            module_data = analytics["module_completion_rates"]
            modules_df = pd.DataFrame([
                {"Module": module, "Completion Rate": rate * 100}
                for module, rate in module_data.items()
            ])

            fig = px.bar(
                modules_df,
                x="Module",
                y="Completion Rate",
                title="Training Module Completion Rates",
                labels={"Completion Rate": "Completion Rate (%)"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        # Performance insights
        st.subheader("💡 Performance Insights")

        insights = generate_training_insights(analytics)
        for insight in insights:
            st.info(f"📈 {insight}")

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")


def render_content_management():
    """Render training content management interface."""
    st.subheader("📚 Training Content Management")

    # Content overview
    content_items = list(agent_onboarding_service.training_content.values())

    if not content_items:
        st.warning("No training content available. Add content to get started.")
        return

    # Content summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Content Items", len(content_items))
    with col2:
        claude_sessions = len([c for c in content_items if c.content_type == "claude_session"])
        st.metric("Claude Sessions", claude_sessions)
    with col3:
        total_duration = sum(c.estimated_duration for c in content_items)
        st.metric("Total Duration", f"{total_duration // 60}h {total_duration % 60}m")

    # Content by module
    module_content = {}
    for content in content_items:
        module = content.module.value
        if module not in module_content:
            module_content[module] = []
        module_content[module].append(content)

    # Display content by module
    for module_name, content_list in module_content.items():
        with st.expander(f"📖 {module_name.replace('_', ' ').title()} ({len(content_list)} items)"):
            for content in content_list:
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**{content.title}**")
                    st.write(content.description)

                with col2:
                    st.write(f"Type: {content.content_type}")
                    st.write(f"Duration: {content.estimated_duration}m")

                with col3:
                    difficulty_color = {
                        SkillLevel.BEGINNER: "🟢",
                        SkillLevel.DEVELOPING: "🔵",
                        SkillLevel.COMPETENT: "🟠",
                        SkillLevel.PROFICIENT: "🔴",
                        SkillLevel.EXPERT: "🟣"
                    }.get(content.difficulty_level, "⚪")

                    st.write(f"Level: {difficulty_color} {content.difficulty_level.value.title()}")

                    if st.button(f"Edit", key=f"edit_{content.id}"):
                        st.info("Edit functionality would open content editor")

    # Add new content
    st.subheader("➕ Add New Content")
    with st.expander("Create New Training Content"):
        render_content_creation_form()


def render_content_creation_form():
    """Render form for creating new training content."""
    with st.form("create_content"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Content Title")
            module = st.selectbox("Training Module", options=[m.value for m in TrainingModule])
            content_type = st.selectbox("Content Type", options=["claude_session", "video", "text", "interactive"])
            duration = st.number_input("Duration (minutes)", min_value=1, value=30)

        with col2:
            description = st.text_area("Description", height=100)
            difficulty = st.selectbox("Difficulty Level", options=[l.value for l in SkillLevel])
            tags = st.text_input("Tags (comma-separated)")

        learning_objectives = st.text_area(
            "Learning Objectives (one per line)",
            placeholder="Understand lead qualification principles\nPractice objection handling\nMaster closing techniques"
        )

        if content_type == "claude_session":
            st.write("**Claude Session Configuration**")
            scenario = st.text_input("Conversation Scenario")
            practice_scenarios = st.text_area(
                "Practice Scenarios (one per line)",
                placeholder="First-time buyer consultation\nLuxury property presentation\nInvestor property analysis"
            )

        submitted = st.form_submit_button("Create Content")

        if submitted and title and description:
            # Create content (simplified)
            st.success(f"✅ Content '{title}' would be created!")
            st.info("In production, this would integrate with the content management system")


def render_assessment_management():
    """Render assessment management interface."""
    st.subheader("🎯 Assessment Management")

    # Assessment overview
    assessments = list(agent_onboarding_service.skill_assessments.values())

    if assessments:
        # Assessment summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Assessments", len(assessments))
        with col2:
            claude_assessments = len([a for a in assessments if a.claude_evaluation])
            st.metric("Claude Evaluated", claude_assessments)
        with col3:
            avg_time = sum(a.time_limit or 0 for a in assessments) / len(assessments)
            st.metric("Avg Time Limit", f"{avg_time:.0f}m")

        # Assessment list
        for assessment in assessments:
            with st.expander(f"📝 {assessment.title}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Module:** {assessment.module.value.replace('_', ' ').title()}")
                    st.write(f"**Type:** {assessment.assessment_type.value.replace('_', ' ').title()}")
                    st.write(f"**Passing Score:** {assessment.passing_score * 100:.0f}%")

                with col2:
                    st.write(f"**Time Limit:** {assessment.time_limit or 'No limit'} minutes")
                    st.write(f"**Max Attempts:** {assessment.max_attempts}")
                    st.write(f"**Claude Evaluation:** {'Yes' if assessment.claude_evaluation else 'No'}")

                if st.button(f"View Details", key=f"view_assessment_{assessment.id}"):
                    show_assessment_details(assessment)

    else:
        st.info("No assessments configured. Create assessments to evaluate agent skills.")

    # Create new assessment
    st.subheader("➕ Create New Assessment")
    if st.button("Create Assessment"):
        st.info("Assessment creation form would appear here")


def render_mentor_view():
    """Render mentor dashboard."""
    st.subheader("🤝 Mentorship Dashboard")

    # Mentor selection
    mentor_id = st.selectbox(
        "Mentor Profile",
        options=["mentor_001", "mentor_002", "mentor_003"],
        help="Select mentor profile"
    )

    # Get mentorship assignments
    mentor_assignments = [
        assignment for assignment in agent_onboarding_service.mentorship_assignments.values()
        if assignment.mentor_agent_id == mentor_id
    ]

    if mentor_assignments:
        st.subheader("👥 Your Mentees")

        for assignment in mentor_assignments:
            with st.expander(f"Agent: {assignment.mentee_agent_id}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Assignment Date:** {assignment.assignment_date.strftime('%Y-%m-%d')}")
                    st.write(f"**Status:** {assignment.status.title()}")
                    st.write(f"**Meeting Schedule:** {assignment.meeting_schedule}")

                with col2:
                    if assignment.focus_areas:
                        st.write("**Focus Areas:**")
                        for area in assignment.focus_areas:
                            st.write(f"• {area}")

                if assignment.goals:
                    st.write("**Goals:**")
                    for goal in assignment.goals:
                        st.write(f"🎯 {goal}")

                # Progress tracking
                if st.button(f"Update Progress", key=f"update_{assignment.id}"):
                    render_mentorship_progress_form(assignment)

    else:
        st.info("No mentees assigned. Contact the training manager for assignments.")

    # Mentorship tools
    st.subheader("🛠️ Mentorship Tools")

    tool_tab1, tool_tab2, tool_tab3 = st.tabs([
        "📝 Progress Notes",
        "📊 Mentee Analytics",
        "💡 Coaching Resources"
    ])

    with tool_tab1:
        render_progress_notes_interface()

    with tool_tab2:
        render_mentee_analytics()

    with tool_tab3:
        render_coaching_resources()


def render_admin_view():
    """Render administrator dashboard."""
    st.subheader("⚙️ System Administration")

    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
        "🏗️ Workflow Management",
        "👥 User Management",
        "🔧 System Settings",
        "📈 Reports"
    ])

    with admin_tab1:
        render_workflow_management()

    with admin_tab2:
        render_user_management()

    with admin_tab3:
        render_system_settings()

    with admin_tab4:
        render_system_reports()


# Helper functions

def start_training_module(agent_id: str, module):
    """Start a training module for an agent."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session = loop.run_until_complete(
            agent_onboarding_service.start_training_session(
                agent_id,
                module.module,
                module.id,
                "claude_coaching" if module.content_type == "claude_session" else "content_review"
            )
        )
        loop.close()

        st.success(f"✅ Started training session for {module.title}")
        st.info("In production, this would launch the training interface")

        # Show module preview
        with st.expander("📖 Module Preview"):
            st.write(f"**Learning Objectives:**")
            for objective in module.learning_objectives:
                st.write(f"• {objective}")

            if module.content_type == "claude_session":
                st.info("🤖 This module includes AI-powered coaching with Claude")

    except Exception as e:
        st.error(f"Error starting training module: {str(e)}")


def get_training_status(progress) -> str:
    """Determine training status based on progress."""
    if progress.completion_percentage >= 100:
        return "Completed"
    elif progress.total_training_hours > 0:
        return "Active"
    else:
        return "Not Started"


def generate_training_insights(analytics: Dict[str, Any]) -> List[str]:
    """Generate insights from training analytics."""
    insights = []

    completion_rate = analytics.get("overall_completion_rate", 0)
    if completion_rate > 0.8:
        insights.append("High completion rate indicates effective training program")
    elif completion_rate < 0.5:
        insights.append("Low completion rate suggests need for program review")

    avg_hours = analytics.get("average_training_hours", 0)
    if avg_hours > 40:
        insights.append("Agents are investing significant time in training")

    session_score = analytics.get("average_session_score", 0)
    if session_score > 0.85:
        insights.append("High session scores indicate good learning outcomes")

    if not insights:
        insights.append("Gathering data to provide meaningful insights")

    return insights


def show_assessment_details(assessment):
    """Show detailed assessment information."""
    st.subheader(f"📝 {assessment.title} Details")

    st.write(f"**Description:** {assessment.description}")

    if assessment.questions:
        st.write("**Assessment Questions:**")
        for i, question in enumerate(assessment.questions, 1):
            st.write(f"{i}. {question.get('scenario', 'Question scenario')}")
            if question.get('evaluation_criteria'):
                st.write("   **Evaluation Criteria:**")
                for criterion in question['evaluation_criteria']:
                    st.write(f"   • {criterion}")

    if assessment.scoring_criteria:
        st.write("**Scoring Criteria:**")
        for criterion, weight in assessment.scoring_criteria.items():
            st.write(f"• {criterion}: {weight * 100:.0f}%")


def render_mentorship_progress_form(assignment):
    """Render form for updating mentorship progress."""
    st.subheader(f"Update Progress for {assignment.mentee_agent_id}")

    with st.form(f"progress_update_{assignment.id}"):
        meeting_date = st.date_input("Meeting Date", value=datetime.now().date())
        progress_notes = st.text_area("Progress Notes", height=100)
        achievements = st.text_area("Achievements", height=60)
        areas_for_improvement = st.text_area("Areas for Improvement", height=60)
        next_steps = st.text_area("Next Steps", height=60)

        submitted = st.form_submit_button("Save Progress Update")

        if submitted:
            st.success("✅ Progress update saved!")


def render_progress_notes_interface():
    """Render interface for managing progress notes."""
    st.write("📝 **Progress Notes Management**")
    st.info("Track detailed progress notes for all mentees")

    # Sample progress notes
    notes_data = [
        {
            "Date": "2024-01-15",
            "Mentee": "new_agent_001",
            "Topic": "Lead Qualification",
            "Notes": "Showed improvement in asking qualifying questions",
            "Rating": 4
        },
        {
            "Date": "2024-01-10",
            "Mentee": "new_agent_002",
            "Topic": "Objection Handling",
            "Notes": "Needs more practice with price objections",
            "Rating": 3
        }
    ]

    notes_df = pd.DataFrame(notes_data)
    st.dataframe(notes_df, use_container_width=True)


def render_mentee_analytics():
    """Render analytics for mentees."""
    st.write("📊 **Mentee Performance Analytics**")

    # Sample analytics
    mentee_data = {
        "Mentee": ["new_agent_001", "new_agent_002", "new_agent_003"],
        "Progress": [85, 65, 92],
        "Sessions": [8, 6, 10],
        "Avg Rating": [4.2, 3.5, 4.7]
    }

    mentee_df = pd.DataFrame(mentee_data)

    fig = px.bar(
        mentee_df,
        x="Mentee",
        y="Progress",
        color="Avg Rating",
        title="Mentee Progress Overview",
        labels={"Progress": "Progress (%)", "Avg Rating": "Average Rating"}
    )
    st.plotly_chart(fig, use_container_width=True)


def render_coaching_resources():
    """Render coaching resources for mentors."""
    st.write("💡 **Coaching Resources**")

    resources = [
        {
            "Title": "Effective Feedback Techniques",
            "Type": "Guide",
            "Description": "Best practices for giving constructive feedback"
        },
        {
            "Title": "Goal Setting Framework",
            "Type": "Template",
            "Description": "SMART goals template for agent development"
        },
        {
            "Title": "Role-Playing Scenarios",
            "Type": "Exercise",
            "Description": "Practice scenarios for skill development"
        }
    ]

    for resource in resources:
        with st.expander(f"📖 {resource['Title']}"):
            st.write(f"**Type:** {resource['Type']}")
            st.write(f"**Description:** {resource['Description']}")
            if st.button(f"Access Resource", key=f"resource_{resource['Title']}"):
                st.info("Resource would open in new window")


def render_workflow_management():
    """Render workflow management interface."""
    st.write("🏗️ **Onboarding Workflow Management**")

    workflows = list(agent_onboarding_service.onboarding_workflows.values())

    for workflow in workflows:
        with st.expander(f"📋 {workflow.name}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Target Role:** {workflow.target_role}")
                st.write(f"**Duration:** {workflow.estimated_duration_weeks} weeks")

            with col2:
                st.write(f"**Required Modules:** {len(workflow.required_modules)}")
                st.write(f"**Stages:** {len(workflow.stages)}")

            if st.button(f"Edit Workflow", key=f"edit_workflow_{workflow.id}"):
                st.info("Workflow editor would open")


def render_user_management():
    """Render user management interface."""
    st.write("👥 **User Management**")

    # Sample user data
    users_data = [
        {"User ID": "agent_001", "Role": "New Agent", "Status": "Active", "Onboarding": "In Progress"},
        {"User ID": "mentor_001", "Role": "Mentor", "Status": "Active", "Mentees": 3},
        {"User ID": "manager_001", "Role": "Training Manager", "Status": "Active", "Teams": 2}
    ]

    users_df = pd.DataFrame(users_data)
    st.dataframe(users_df, use_container_width=True)

    if st.button("Add New User"):
        st.info("User creation form would appear")


def render_system_settings():
    """Render system settings interface."""
    st.write("🔧 **System Settings**")

    with st.expander("⚙️ Training Configuration"):
        st.slider("Default Session Duration (minutes)", 15, 120, 45)
        st.slider("Assessment Passing Score (%)", 50, 95, 75)
        st.checkbox("Enable Claude Evaluations", value=True)
        st.checkbox("Automatic Progress Tracking", value=True)

    with st.expander("🔔 Notification Settings"):
        st.checkbox("Email Progress Updates", value=True)
        st.checkbox("Mentor Assignment Alerts", value=True)
        st.checkbox("Assessment Reminders", value=False)

    if st.button("Save Settings"):
        st.success("✅ Settings saved!")


def render_system_reports():
    """Render system reports interface."""
    st.write("📈 **System Reports**")

    report_type = st.selectbox(
        "Report Type",
        options=[
            "Training Effectiveness Report",
            "Agent Progress Summary",
            "Mentor Performance Report",
            "Content Usage Analytics",
            "Assessment Results Report"
        ]
    )

    date_range = st.date_input(
        "Report Period",
        value=[datetime.now().date() - timedelta(days=30), datetime.now().date()],
        help="Select date range for report"
    )

    if st.button("Generate Report"):
        st.success(f"✅ {report_type} generated for {date_range[0]} to {date_range[1]}")
        st.info("Report would be generated and displayed here")


# Initialize demo data
def load_demo_data():
    """Load demo data for the onboarding system."""
    try:
        # Create sample agent progress
        if "demo_agent_001" not in agent_onboarding_service.agent_progress:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                start_agent_onboarding("demo_agent_001", "new_agent_onboarding")
            )
            loop.close()

    except Exception as e:
        pass  # Ignore errors in demo setup


# Load demo data when component is imported
load_demo_data()