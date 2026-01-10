"""
Goal Achievement Dashboard Component

A comprehensive Streamlit interface for agent goal setting, tracking, and achievement management.
Provides role-based interfaces for agents, managers, and administrators.

Features:
- Goal creation with SMART criteria validation
- Progress tracking and milestone management
- Achievement gallery and recognition system
- AI-powered goal recommendations
- Team goal alignment visualization
- Performance analytics and insights

Created: January 2026
Author: GHL Real Estate AI Platform
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

# Import the goal tracking service
try:
    from services.agent_goal_tracking_service import (
        goal_tracking_service,
        GoalType,
        GoalStatus,
        GoalPriority,
        TimeFrame,
        AchievementType,
        Goal,
        Achievement,
        GoalRecommendation
    )
except ImportError:
    st.error("Goal tracking service not found. Please check the service installation.")

# Configure logging
logger = logging.getLogger(__name__)

def render_goal_achievement_dashboard():
    """Render the goal achievement dashboard interface."""
    st.header("🎯 Goal Achievement Center")
    st.markdown("*AI-powered goal setting, tracking, and achievement management*")

    # User role selection for demo purposes
    user_role = st.selectbox(
        "Select Your Role",
        ["Agent", "Manager", "Administrator"],
        key="goal_dashboard_role"
    )

    # Agent selection
    agent_options = ["agent_001", "agent_002", "agent_003", "new_agent"]
    selected_agent = st.selectbox(
        "Select Agent",
        agent_options,
        key="goal_dashboard_agent"
    )

    if user_role == "Agent":
        render_agent_goal_interface(selected_agent)
    elif user_role == "Manager":
        render_manager_goal_interface(selected_agent)
    else:
        render_admin_goal_interface()

def render_agent_goal_interface(agent_id: str):
    """Render the agent-focused goal interface."""

    # Create tabs for different agent views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 My Goals", "🏆 Achievements", "💡 Recommendations",
        "🎯 Create Goal", "📈 Analytics"
    ])

    with tab1:
        render_agent_goals_overview(agent_id)

    with tab2:
        render_achievements_gallery(agent_id)

    with tab3:
        render_goal_recommendations(agent_id)

    with tab4:
        render_goal_creation_form(agent_id)

    with tab5:
        render_goal_analytics(agent_id)

def render_agent_goals_overview(agent_id: str):
    """Render overview of agent's current goals."""
    st.subheader("📊 My Current Goals")

    try:
        # Get agent goals
        goals = asyncio.run(goal_tracking_service.get_agent_goals(agent_id))

        if not goals:
            st.info("🎯 No goals set yet. Create your first goal to get started!")
            if st.button("Create My First Goal"):
                st.session_state.goal_create_tab = True
            return

        # Goals summary metrics
        col1, col2, col3, col4 = st.columns(4)

        total_goals = len(goals)
        active_goals = len([g for g in goals if g.status in [GoalStatus.ACTIVE, GoalStatus.ON_TRACK]])
        achieved_goals = len([g for g in goals if g.status in [GoalStatus.ACHIEVED, GoalStatus.EXCEEDED]])
        avg_progress = sum(g.calculate_progress() for g in goals) / len(goals) if goals else 0

        with col1:
            st.metric("Total Goals", total_goals)
        with col2:
            st.metric("Active Goals", active_goals)
        with col3:
            st.metric("Achieved", achieved_goals)
        with col4:
            st.metric("Avg Progress", f"{avg_progress:.1f}%")

        # Goals list with status
        st.subheader("Goal Details")

        for goal in goals:
            with st.expander(f"{get_status_emoji(goal.status)} {goal.title} - {goal.calculate_progress():.1f}%"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Description:** {goal.description}")
                    st.write(f"**Type:** {goal.goal_type.value.title()}")
                    st.write(f"**Priority:** {goal.priority.value.title()}")
                    st.write(f"**Target:** {goal.target_value:,.0f}")
                    st.write(f"**Current:** {goal.current_value:,.0f}")

                    # Progress bar
                    progress = goal.calculate_progress()
                    st.progress(min(progress / 100, 1.0))

                    # Days remaining
                    days_left = goal.days_remaining()
                    if days_left > 0:
                        st.write(f"**Days Remaining:** {days_left}")
                    elif goal.is_overdue():
                        st.write("**Status:** ⚠️ Overdue")

                with col2:
                    st.write(f"**Target Date:** {goal.target_date.strftime('%Y-%m-%d')}")
                    st.write(f"**Status:** {get_status_badge(goal.status)}")

                    # Update progress button
                    if goal.status in [GoalStatus.ACTIVE, GoalStatus.ON_TRACK, GoalStatus.AT_RISK, GoalStatus.BEHIND]:
                        if st.button(f"Update Progress", key=f"update_{goal.goal_id}"):
                            st.session_state.updating_goal = goal.goal_id

                # Show milestones if any
                if goal.milestones:
                    st.write("**Milestones:**")
                    for milestone in goal.milestones:
                        milestone_progress = milestone.calculate_progress()
                        status_emoji = get_status_emoji(milestone.status)
                        st.write(f"{status_emoji} {milestone.title}: {milestone_progress:.1f}%")

        # Goal update form
        if 'updating_goal' in st.session_state:
            goal_id = st.session_state.updating_goal
            goal = next((g for g in goals if g.goal_id == goal_id), None)

            if goal:
                render_goal_update_form(goal)

    except Exception as e:
        st.error(f"Error loading goals: {e}")
        logger.error(f"Error in render_agent_goals_overview: {e}")

def render_goal_update_form(goal: Goal):
    """Render form to update goal progress."""
    st.subheader(f"Update Goal: {goal.title}")

    with st.form(f"update_goal_{goal.goal_id}"):
        col1, col2 = st.columns(2)

        with col1:
            new_value = st.number_input(
                "Current Progress",
                min_value=0.0,
                max_value=goal.target_value * 2,  # Allow exceeding target
                value=float(goal.current_value),
                step=1.0
            )

        with col2:
            notes = st.text_area("Progress Notes (Optional)", placeholder="Add any notes about your progress...")

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("Update Progress"):
                try:
                    success = asyncio.run(
                        goal_tracking_service.update_goal_progress(goal.goal_id, new_value, notes)
                    )

                    if success:
                        st.success("✅ Goal progress updated successfully!")
                        st.session_state.pop('updating_goal', None)
                        st.rerun()
                    else:
                        st.error("Failed to update goal progress")

                except Exception as e:
                    st.error(f"Error updating goal: {e}")

        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.pop('updating_goal', None)
                st.rerun()

def render_achievements_gallery(agent_id: str):
    """Render achievements and recognition gallery."""
    st.subheader("🏆 My Achievements")

    try:
        achievements = asyncio.run(goal_tracking_service.get_agent_achievements(agent_id))

        if not achievements:
            st.info("🏆 No achievements yet. Keep working toward your goals to earn recognition!")
            return

        # Achievement summary
        total_points = sum(a.points_awarded for a in achievements)
        recent_achievements = [a for a in achievements if (datetime.now() - a.earned_date).days <= 7]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Achievements", len(achievements))
        with col2:
            st.metric("Total Points", total_points)
        with col3:
            st.metric("This Week", len(recent_achievements))

        # Achievement gallery
        st.subheader("Achievement Gallery")

        # Group achievements by type
        achievement_types = {}
        for achievement in achievements:
            achievement_type = achievement.achievement_type.value
            if achievement_type not in achievement_types:
                achievement_types[achievement_type] = []
            achievement_types[achievement_type].append(achievement)

        for achievement_type, type_achievements in achievement_types.items():
            st.write(f"**{achievement_type.replace('_', ' ').title()}**")

            # Display achievements in rows of 3
            for i in range(0, len(type_achievements), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(type_achievements):
                        achievement = type_achievements[i + j]
                        with col:
                            render_achievement_card(achievement)

    except Exception as e:
        st.error(f"Error loading achievements: {e}")

def render_achievement_card(achievement: Achievement):
    """Render individual achievement card."""
    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
            text-align: center;
        ">
            <div style="font-size: 2rem;">{achievement.badge_icon}</div>
            <div style="font-weight: bold; margin: 8px 0;">{achievement.title}</div>
            <div style="font-size: 0.9rem; color: #666; margin: 4px 0;">
                {achievement.description}
            </div>
            <div style="font-size: 0.8rem; color: #888; margin: 4px 0;">
                {achievement.earned_date.strftime('%Y-%m-%d')}
            </div>
            <div style="
                background: #4CAF50;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
                margin-top: 8px;
                display: inline-block;
            ">
                +{achievement.points_awarded} points
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_goal_recommendations(agent_id: str):
    """Render AI-powered goal recommendations."""
    st.subheader("💡 AI Goal Recommendations")

    try:
        # Generate fresh recommendations
        recommendations = asyncio.run(goal_tracking_service.generate_goal_recommendations(agent_id))

        if not recommendations:
            st.info("🤖 No new recommendations available. Check back after updating your goals!")
            return

        st.write("Based on your current performance and goals, here are AI-powered recommendations:")

        for i, recommendation in enumerate(recommendations):
            with st.expander(f"💡 {recommendation.title}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Description:** {recommendation.description}")
                    st.write(f"**Goal Type:** {recommendation.goal_type.value.title()}")
                    st.write(f"**Suggested Target:** {recommendation.suggested_target:,.0f}")
                    st.write(f"**Time Frame:** {recommendation.time_frame.value.title()}")
                    st.write(f"**AI Reasoning:** {recommendation.reasoning}")

                    confidence_color = "green" if recommendation.confidence_score > 0.8 else "orange" if recommendation.confidence_score > 0.6 else "red"
                    st.markdown(f"**Confidence Score:** <span style='color: {confidence_color}'>{recommendation.confidence_score:.1%}</span>", unsafe_allow_html=True)

                with col2:
                    if st.button("Accept Recommendation", key=f"accept_{recommendation.recommendation_id}"):
                        # Create goal from recommendation
                        try:
                            goal = asyncio.run(goal_tracking_service.create_goal(
                                agent_id=agent_id,
                                title=recommendation.title,
                                description=recommendation.description,
                                goal_type=recommendation.goal_type,
                                target_value=recommendation.suggested_target,
                                target_date=datetime.now() + timedelta(days=30 if recommendation.time_frame == TimeFrame.MONTHLY else 90),
                                priority=GoalPriority.MEDIUM
                            ))

                            # Mark recommendation as accepted
                            recommendation.accepted = True

                            st.success(f"✅ Created goal: {goal.title}")
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error creating goal: {e}")

                    if st.button("Dismiss", key=f"dismiss_{recommendation.recommendation_id}"):
                        recommendation.accepted = False
                        st.info("Recommendation dismissed")
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading recommendations: {e}")

def render_goal_creation_form(agent_id: str):
    """Render form for creating new goals."""
    st.subheader("🎯 Create New Goal")

    with st.form("create_goal_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Goal Title*", placeholder="e.g., Increase Monthly Revenue")
            goal_type = st.selectbox("Goal Type*", [e.value for e in GoalType])
            target_value = st.number_input("Target Value*", min_value=1.0, value=100.0, step=1.0)
            priority = st.selectbox("Priority", [e.value for e in GoalPriority])

        with col2:
            description = st.text_area("Description*", placeholder="Describe your goal in detail...")
            time_frame = st.selectbox("Time Frame*", [e.value for e in TimeFrame])
            target_date = st.date_input("Target Date*", value=datetime.now().date() + timedelta(days=30))
            category = st.text_input("Category (Optional)", placeholder="e.g., Professional Development")

        tags = st.text_input("Tags (Optional)", placeholder="Separate tags with commas")
        notes = st.text_area("Notes (Optional)", placeholder="Any additional notes...")

        # SMART criteria preview
        if title and description:
            st.subheader("SMART Criteria Preview")
            smart_preview = asyncio.run(goal_tracking_service._validate_smart_criteria(title, description))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("SMART Score", f"{smart_preview.score:.0f}%")
            with col2:
                criteria_met = sum([smart_preview.specific, smart_preview.measurable,
                                   smart_preview.achievable, smart_preview.relevant, smart_preview.time_bound])
                st.metric("Criteria Met", f"{criteria_met}/5")
            with col3:
                if smart_preview.feedback:
                    st.warning("Suggestions: " + ", ".join(smart_preview.feedback))
                else:
                    st.success("Great SMART goal!")

        # Submit button
        if st.form_submit_button("Create Goal"):
            if not all([title, description, goal_type, target_value, target_date]):
                st.error("Please fill in all required fields marked with *")
            else:
                try:
                    goal = asyncio.run(goal_tracking_service.create_goal(
                        agent_id=agent_id,
                        title=title,
                        description=description,
                        goal_type=GoalType(goal_type),
                        target_value=target_value,
                        target_date=datetime.combine(target_date, datetime.min.time()),
                        priority=GoalPriority(priority),
                        time_frame=TimeFrame(time_frame),
                        category=category,
                        tags=tags.split(",") if tags else []
                    ))

                    st.success(f"✅ Goal created successfully: {goal.title}")
                    st.info("Your new goal is now active and ready for tracking!")

                except Exception as e:
                    st.error(f"Error creating goal: {e}")
                    logger.error(f"Error in goal creation: {e}")

def render_goal_analytics(agent_id: str):
    """Render goal analytics and insights."""
    st.subheader("📈 Goal Analytics & Insights")

    try:
        analytics = asyncio.run(goal_tracking_service.get_goal_analytics(agent_id))
        goals = asyncio.run(goal_tracking_service.get_agent_goals(agent_id))

        if analytics.get("total_goals", 0) == 0:
            st.info("📊 Create some goals to see analytics and insights!")
            return

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Average Progress",
                f"{analytics.get('avg_progress', 0):.1f}%",
                delta=f"+{analytics.get('avg_progress', 0) - 65:.1f}%" if analytics.get('avg_progress', 0) > 65 else None
            )

        with col2:
            st.metric("Total Points", analytics.get('total_points', 0))

        with col3:
            completion_rate = analytics.get('completion_rate', 0)
            st.metric("Completion Rate", f"{completion_rate:.1f}%")

        with col4:
            st.metric("On Track", analytics.get('on_track_count', 0))

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            # Goal status distribution
            if analytics.get('status_distribution'):
                status_df = pd.DataFrame(
                    list(analytics['status_distribution'].items()),
                    columns=['Status', 'Count']
                )

                fig = px.pie(
                    status_df,
                    values='Count',
                    names='Status',
                    title="Goal Status Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Goal type distribution
            if analytics.get('type_distribution'):
                type_df = pd.DataFrame(
                    list(analytics['type_distribution'].items()),
                    columns=['Type', 'Count']
                )

                fig = px.bar(
                    type_df,
                    x='Type',
                    y='Count',
                    title="Goals by Type",
                    color='Count',
                    color_continuous_scale='viridis'
                )
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        # Progress timeline
        if goals:
            st.subheader("Goal Progress Timeline")

            progress_data = []
            for goal in goals:
                progress_data.append({
                    'Goal': goal.title[:30] + "..." if len(goal.title) > 30 else goal.title,
                    'Progress': goal.calculate_progress(),
                    'Status': goal.status.value,
                    'Priority': goal.priority.value,
                    'Target Date': goal.target_date.strftime('%Y-%m-%d')
                })

            progress_df = pd.DataFrame(progress_data)

            fig = px.bar(
                progress_df,
                x='Goal',
                y='Progress',
                color='Status',
                hover_data=['Priority', 'Target Date'],
                title="Progress by Goal",
                labels={'Progress': 'Progress (%)'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        # Insights and recommendations
        st.subheader("📊 Performance Insights")

        insights = generate_performance_insights(analytics, goals)
        for insight in insights:
            if insight['type'] == 'success':
                st.success(insight['message'])
            elif insight['type'] == 'warning':
                st.warning(insight['message'])
            else:
                st.info(insight['message'])

    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def render_manager_goal_interface(agent_id: str):
    """Render manager-focused interface for goal oversight."""
    st.subheader("👥 Team Goal Management")

    tab1, tab2, tab3 = st.tabs(["Team Overview", "Goal Approval", "Performance Review"])

    with tab1:
        render_team_goal_overview()

    with tab2:
        render_goal_approval_interface()

    with tab3:
        render_team_performance_review()

def render_team_goal_overview():
    """Render team-wide goal overview for managers."""
    st.write("### Team Goal Overview")

    # Mock team data for demonstration
    team_agents = ["agent_001", "agent_002", "agent_003"]

    team_data = []
    for agent_id in team_agents:
        try:
            analytics = asyncio.run(goal_tracking_service.get_goal_analytics(agent_id))
            team_data.append({
                'Agent': agent_id,
                'Total Goals': analytics.get('total_goals', 0),
                'Avg Progress': analytics.get('avg_progress', 0),
                'Achievements': analytics.get('total_achievements', 0),
                'Completion Rate': analytics.get('completion_rate', 0)
            })
        except:
            continue

    if team_data:
        team_df = pd.DataFrame(team_data)
        st.dataframe(team_df, use_container_width=True)

        # Team performance chart
        fig = px.bar(
            team_df,
            x='Agent',
            y='Avg Progress',
            color='Completion Rate',
            title="Team Goal Progress",
            labels={'Avg Progress': 'Average Progress (%)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No team data available")

def render_goal_approval_interface():
    """Render interface for approving/reviewing goals."""
    st.write("### Goal Approval & Review")
    st.info("Manager approval features would be implemented here for enterprise deployment.")

def render_team_performance_review():
    """Render team performance review interface."""
    st.write("### Team Performance Review")
    st.info("Comprehensive team performance analytics would be available here.")

def render_admin_goal_interface():
    """Render administrator interface for system-wide goal management."""
    st.subheader("⚙️ Goal System Administration")

    tab1, tab2, tab3 = st.tabs(["System Metrics", "Goal Templates", "Settings"])

    with tab1:
        render_system_metrics()

    with tab2:
        render_goal_templates()

    with tab3:
        render_goal_settings()

def render_system_metrics():
    """Render system-wide goal metrics."""
    st.write("### System-Wide Goal Metrics")
    st.info("Administrator metrics and system health monitoring would be displayed here.")

def render_goal_templates():
    """Render goal template management."""
    st.write("### Goal Templates")
    st.info("Goal template creation and management interface would be available here.")

def render_goal_settings():
    """Render goal system settings."""
    st.write("### Goal System Settings")
    st.info("System configuration and settings management would be implemented here.")

# Helper functions
def get_status_emoji(status: GoalStatus) -> str:
    """Get emoji for goal status."""
    emoji_map = {
        GoalStatus.DRAFT: "📝",
        GoalStatus.ACTIVE: "🔄",
        GoalStatus.ON_TRACK: "✅",
        GoalStatus.AT_RISK: "⚠️",
        GoalStatus.BEHIND: "🔴",
        GoalStatus.ACHIEVED: "🎯",
        GoalStatus.EXCEEDED: "🚀",
        GoalStatus.PAUSED: "⏸️",
        GoalStatus.CANCELLED: "❌"
    }
    return emoji_map.get(status, "❓")

def get_status_badge(status: GoalStatus) -> str:
    """Get colored status badge."""
    color_map = {
        GoalStatus.ACTIVE: "🟦 Active",
        GoalStatus.ON_TRACK: "🟢 On Track",
        GoalStatus.AT_RISK: "🟡 At Risk",
        GoalStatus.BEHIND: "🔴 Behind",
        GoalStatus.ACHIEVED: "✅ Achieved",
        GoalStatus.EXCEEDED: "🚀 Exceeded",
        GoalStatus.PAUSED: "⏸️ Paused",
        GoalStatus.CANCELLED: "❌ Cancelled"
    }
    return color_map.get(status, "❓ Unknown")

def generate_performance_insights(analytics: Dict, goals: List[Goal]) -> List[Dict]:
    """Generate performance insights based on analytics."""
    insights = []

    avg_progress = analytics.get('avg_progress', 0)
    completion_rate = analytics.get('completion_rate', 0)
    overdue_count = analytics.get('overdue_count', 0)

    # Progress insights
    if avg_progress > 85:
        insights.append({
            'type': 'success',
            'message': f"🎉 Excellent progress! You're averaging {avg_progress:.1f}% across all goals."
        })
    elif avg_progress > 70:
        insights.append({
            'type': 'info',
            'message': f"👍 Good momentum! {avg_progress:.1f}% average progress keeps you on track."
        })
    else:
        insights.append({
            'type': 'warning',
            'message': f"⚠️ Focus needed. {avg_progress:.1f}% average progress suggests some goals need attention."
        })

    # Completion rate insights
    if completion_rate > 80:
        insights.append({
            'type': 'success',
            'message': f"🏆 Outstanding completion rate of {completion_rate:.1f}%!"
        })
    elif completion_rate < 20:
        insights.append({
            'type': 'warning',
            'message': f"📈 Consider setting more achievable milestones to improve your {completion_rate:.1f}% completion rate."
        })

    # Overdue insights
    if overdue_count > 0:
        insights.append({
            'type': 'warning',
            'message': f"⏰ You have {overdue_count} overdue goal(s). Consider reviewing deadlines or adjusting targets."
        })

    return insights

# Export the render function for use in the main dashboard
if __name__ == "__main__":
    render_goal_achievement_dashboard()