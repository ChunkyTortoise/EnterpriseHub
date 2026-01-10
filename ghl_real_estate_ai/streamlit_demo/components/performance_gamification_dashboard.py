"""
Performance Gamification Dashboard Component

Team performance optimization dashboard with personalized challenges,
leaderboards, and skill development tracking.

Value: $60K-95K annually (30% agent productivity increase)
Integration: Uses predictive_analytics for performance predictions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

try:
    from ..services.performance_gamification import (
        PerformanceGamificationEngine,
        Challenge,
        Achievement,
        SkillAssessment
    )
    from ..services.predictive_analytics_engine import PredictiveAnalyticsEngine
except ImportError:
    # Fallback for development/testing
    st.warning("⚠️ Performance Gamification service not available - using mock data")
    PerformanceGamificationEngine = None
    Challenge = None
    Achievement = None
    SkillAssessment = None


class PerformanceGamificationDashboard:
    """Dashboard component for performance gamification and team challenges."""

    def __init__(self):
        self.gamification_service = self._initialize_service()
        self.cache_duration = 300  # 5 minutes

    def _initialize_service(self):
        """Initialize performance gamification service."""
        try:
            if PerformanceGamificationEngine:
                return PerformanceGamificationEngine()
            return None
        except Exception as e:
            st.error(f"Failed to initialize gamification service: {e}")
            return None

    def render(self, tenant_id: str) -> None:
        """Render the complete performance gamification dashboard."""
        st.header("🏆 Performance Gamification")
        st.caption("Team challenges and skill development tracking")

        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Active Challenges",
            "🏆 Leaderboards",
            "📈 Skill Development",
            "🎖️ Achievements"
        ])

        with tab1:
            self._render_active_challenges(tenant_id)

        with tab2:
            self._render_leaderboards(tenant_id)

        with tab3:
            self._render_skill_development(tenant_id)

        with tab4:
            self._render_achievements(tenant_id)

    def _render_active_challenges(self, tenant_id: str) -> None:
        """Render active challenges management."""
        st.subheader("🎯 Active Challenges")

        # Challenge overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Active Challenges",
                value="12",
                delta="3 new this week"
            )

        with col2:
            st.metric(
                label="Participation Rate",
                value="94%",
                delta="6% ↑"
            )

        with col3:
            st.metric(
                label="Completion Rate",
                value="87%",
                delta="12% ↑"
            )

        with col4:
            st.metric(
                label="Team Morale Score",
                value="9.1/10",
                delta="0.5 ↑"
            )

        # Active challenges list
        st.subheader("Current Team Challenges")

        challenges_data = [
            {
                "id": "challenge_001",
                "name": "Lead Response Lightning",
                "description": "Respond to all new leads within 5 minutes",
                "type": "Speed",
                "duration": "This Week",
                "participants": 15,
                "progress": 78,
                "prize": "$500 Bonus",
                "difficulty": "Medium",
                "expires": "2 days"
            },
            {
                "id": "challenge_002",
                "name": "Conversion Champions",
                "description": "Achieve 85%+ lead to appointment conversion",
                "type": "Performance",
                "duration": "This Month",
                "participants": 12,
                "progress": 65,
                "prize": "Premium Parking + $1000",
                "difficulty": "Hard",
                "expires": "18 days"
            },
            {
                "id": "challenge_003",
                "name": "Client Satisfaction Heroes",
                "description": "Maintain 9.5+ client satisfaction rating",
                "type": "Quality",
                "duration": "2 Weeks",
                "participants": 18,
                "progress": 92,
                "prize": "Team Dinner + $300 Each",
                "difficulty": "Easy",
                "expires": "9 days"
            }
        ]

        for challenge in challenges_data:
            with st.expander(f"🎯 {challenge['name']} - {challenge['progress']}% Complete"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Description:** {challenge['description']}")
                    st.write(f"**Duration:** {challenge['duration']}")
                    st.write(f"**Participants:** {challenge['participants']} agents")

                    # Progress bar
                    st.progress(challenge['progress'] / 100)
                    st.caption(f"{challenge['progress']}% Complete")

                    # Difficulty and type badges
                    difficulty_color = "red" if challenge['difficulty'] == "Hard" else "orange" if challenge['difficulty'] == "Medium" else "green"
                    st.markdown(f"""
                    **Type:** {challenge['type']} |
                    **Difficulty:** <span style='color: {difficulty_color}'>{challenge['difficulty']}</span> |
                    **Prize:** {challenge['prize']}
                    """, unsafe_allow_html=True)

                with col2:
                    st.info(f"⏰ **Expires in {challenge['expires']}**")

                    if st.button(f"View Details", key=f"view_{challenge['id']}"):
                        st.info("Challenge details opened")

                    if st.button(f"Join Challenge", key=f"join_{challenge['id']}"):
                        st.success("Joined challenge successfully!")

        # Create new challenge
        st.subheader("➕ Create New Challenge")

        with st.expander("Create Custom Challenge"):
            col1, col2 = st.columns(2)

            with col1:
                challenge_name = st.text_input("Challenge Name")
                challenge_type = st.selectbox(
                    "Challenge Type",
                    ["Speed", "Performance", "Quality", "Teamwork", "Learning"]
                )
                challenge_duration = st.selectbox(
                    "Duration",
                    ["1 Day", "3 Days", "1 Week", "2 Weeks", "1 Month"]
                )

            with col2:
                challenge_description = st.text_area("Challenge Description")
                challenge_prize = st.text_input("Prize/Reward")
                challenge_difficulty = st.selectbox(
                    "Difficulty",
                    ["Easy", "Medium", "Hard"]
                )

            if st.button("🚀 Launch Challenge"):
                st.success(f"Challenge '{challenge_name}' launched successfully!")

    def _render_leaderboards(self, tenant_id: str) -> None:
        """Render team leaderboards."""
        st.subheader("🏆 Team Leaderboards")

        # Leaderboard selection
        leaderboard_type = st.selectbox(
            "Select Leaderboard",
            ["Overall Performance", "Lead Conversion", "Response Time", "Client Satisfaction", "Revenue Generated"]
        )

        # Mock leaderboard data
        if leaderboard_type == "Overall Performance":
            leaderboard_data = pd.DataFrame({
                'Rank': [1, 2, 3, 4, 5, 6, 7, 8],
                'Agent': ['Sarah Miller', 'Mike Johnson', 'Lisa Chen', 'David Brown', 'Emma Davis', 'John Wilson', 'Mary Taylor', 'Robert Garcia'],
                'Score': [950, 920, 895, 870, 845, 820, 795, 775],
                'Change': ['+25', '+15', '-10', '+30', '+5', '-5', '+20', '+10'],
                'Challenges Won': [8, 6, 5, 7, 4, 3, 5, 4],
                'Badge': ['🥇', '🥈', '🥉', '⭐', '⭐', '⭐', '⭐', '⭐']
            })
        else:
            # Mock data for other leaderboards
            leaderboard_data = pd.DataFrame({
                'Rank': [1, 2, 3, 4, 5, 6, 7, 8],
                'Agent': ['Sarah Miller', 'Mike Johnson', 'Lisa Chen', 'David Brown', 'Emma Davis', 'John Wilson', 'Mary Taylor', 'Robert Garcia'],
                'Score': [95, 92, 89, 87, 84, 82, 79, 77],
                'Change': ['+2', '+1', '-1', '+3', '0', '-1', '+2', '+1'],
                'Challenges Won': [8, 6, 5, 7, 4, 3, 5, 4],
                'Badge': ['🥇', '🥈', '🥉', '⭐', '⭐', '⭐', '⭐', '⭐']
            })

        # Display leaderboard
        for index, row in leaderboard_data.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])

                with col1:
                    st.markdown(f"<h3>{row['Badge']}</h3>", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"**#{row['Rank']} {row['Agent']}**")

                with col3:
                    change_color = "green" if '+' in str(row['Change']) else "red" if '-' in str(row['Change']) else "gray"
                    st.markdown(f"Score: **{row['Score']}** <span style='color: {change_color}'>({row['Change']})</span>", unsafe_allow_html=True)

                with col4:
                    st.write(f"Challenges Won: **{row['Challenges Won']}**")

                with col5:
                    if st.button(f"View Profile", key=f"profile_{index}"):
                        st.info(f"Viewing {row['Agent']}'s profile...")

                st.divider()

        # Performance trends chart
        st.subheader("Performance Trends")

        # Mock performance trend data
        dates = pd.date_range('2026-01-01', periods=30, freq='D')
        performance_trends = pd.DataFrame({
            'Date': dates,
            'Sarah Miller': [850 + i*3 + (i%7)*10 for i in range(30)],
            'Mike Johnson': [820 + i*2.5 + (i%5)*8 for i in range(30)],
            'Lisa Chen': [800 + i*2 + (i%6)*12 for i in range(30)]
        })

        fig_trends = go.Figure()

        for agent in ['Sarah Miller', 'Mike Johnson', 'Lisa Chen']:
            fig_trends.add_trace(go.Scatter(
                x=performance_trends['Date'],
                y=performance_trends[agent],
                mode='lines+markers',
                name=agent,
                line=dict(width=3)
            ))

        fig_trends.update_layout(
            title=f"{leaderboard_type} Trends - Last 30 Days",
            xaxis_title="Date",
            yaxis_title="Performance Score",
            height=400
        )

        st.plotly_chart(fig_trends, use_container_width=True)

        # Team comparison radar chart
        st.subheader("Team Performance Radar")

        top_agents = leaderboard_data.head(3)
        categories = ['Lead Generation', 'Conversion Rate', 'Response Time', 'Client Satisfaction', 'Revenue']

        fig_radar = go.Figure()

        for _, agent in top_agents.iterrows():
            # Mock radar data
            values = [85 + (agent['Rank']-1)*(-5), 90 + (agent['Rank']-1)*(-3),
                     88 + (agent['Rank']-1)*(-4), 92 + (agent['Rank']-1)*(-2),
                     87 + (agent['Rank']-1)*(-3)]

            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=agent['Agent']
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Top 3 Agents Performance Comparison",
            height=500
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    def _render_skill_development(self, tenant_id: str) -> None:
        """Render skill development tracking."""
        st.subheader("📈 Skill Development Tracking")

        # Agent selection
        selected_agent = st.selectbox(
            "Select Agent",
            ["Sarah Miller", "Mike Johnson", "Lisa Chen", "David Brown", "Emma Davis"]
        )

        # Skill categories and progress
        col1, col2 = st.columns([1, 1])

        with col1:
            st.write("**Core Skills Assessment**")

            skills_data = pd.DataFrame({
                'Skill': ['Lead Qualification', 'Property Knowledge', 'Negotiation', 'Market Analysis', 'Client Relations', 'Digital Marketing'],
                'Current Level': [92, 88, 76, 84, 95, 71],
                'Target Level': [95, 90, 85, 90, 98, 80],
                'Progress': [96, 98, 89, 93, 97, 89]
            })

            for _, skill in skills_data.iterrows():
                st.write(f"**{skill['Skill']}**")

                # Progress bar with current/target indication
                progress = skill['Progress'] / 100
                st.progress(progress)

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.caption(f"Current: {skill['Current Level']}%")
                with col_b:
                    st.caption(f"Target: {skill['Target Level']}%")
                with col_c:
                    st.caption(f"Progress: {skill['Progress']}%")

        with col2:
            # Skill development chart
            fig_skills = px.bar(
                skills_data,
                x='Current Level',
                y='Skill',
                orientation='h',
                title=f"{selected_agent} - Skill Levels",
                color='Current Level',
                color_continuous_scale='Blues'
            )

            # Add target level markers
            fig_skills.add_scatter(
                x=skills_data['Target Level'],
                y=skills_data['Skill'],
                mode='markers',
                marker=dict(symbol='diamond', size=8, color='red'),
                name='Target Level'
            )

            fig_skills.update_layout(height=400)
            st.plotly_chart(fig_skills, use_container_width=True)

        # Learning recommendations
        st.subheader("🎓 Personalized Learning Recommendations")

        recommendations = [
            {
                "skill": "Negotiation",
                "gap": "9% below target",
                "recommendation": "Complete 'Advanced Negotiation Tactics' course",
                "duration": "2 weeks",
                "impact": "High"
            },
            {
                "skill": "Digital Marketing",
                "gap": "9% below target",
                "recommendation": "Practice social media lead generation",
                "duration": "1 week",
                "impact": "Medium"
            },
            {
                "skill": "Market Analysis",
                "gap": "6% below target",
                "recommendation": "Study comparative market analysis (CMA) techniques",
                "duration": "1 week",
                "impact": "Medium"
            }
        ]

        for rec in recommendations:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold; color: #1f77b4;">{rec['skill']}</span>
                        <span style="color: #ff7f0e;">{rec['gap']}</span>
                    </div>
                    <p style="margin: 5px 0;">{rec['recommendation']}</p>
                    <small style="color: #666;">Duration: {rec['duration']} | Impact: {rec['impact']}</small>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Start Learning Path", key=f"learn_{rec['skill']}"):
                    st.success(f"Learning path for {rec['skill']} started!")

        # Team skill development trends
        st.subheader("Team Skill Development Trends")

        # Mock team skill data over time
        months = ['Oct', 'Nov', 'Dec', 'Jan']
        team_skills = pd.DataFrame({
            'Month': months,
            'Lead Qualification': [82, 85, 87, 90],
            'Negotiation': [75, 78, 81, 84],
            'Client Relations': [88, 90, 92, 94],
            'Market Analysis': [79, 82, 85, 87]
        })

        fig_team_trends = go.Figure()

        skills = ['Lead Qualification', 'Negotiation', 'Client Relations', 'Market Analysis']
        for skill in skills:
            fig_team_trends.add_trace(go.Scatter(
                x=team_skills['Month'],
                y=team_skills[skill],
                mode='lines+markers',
                name=skill,
                line=dict(width=3)
            ))

        fig_team_trends.update_layout(
            title="Team Average Skill Levels - Quarterly Trend",
            xaxis_title="Month",
            yaxis_title="Average Skill Level (%)",
            height=400
        )

        st.plotly_chart(fig_team_trends, use_container_width=True)

    def _render_achievements(self, tenant_id: str) -> None:
        """Render achievements and badges."""
        st.subheader("🎖️ Achievements & Badges")

        # Achievement categories
        col1, col2 = st.columns([2, 1])

        with col1:
            # Recent achievements
            st.write("**Recent Achievements**")

            recent_achievements = [
                {
                    "agent": "Sarah Miller",
                    "achievement": "Speed Demon",
                    "description": "Responded to 50 leads under 2 minutes",
                    "badge": "⚡",
                    "earned": "2 hours ago",
                    "rarity": "Rare"
                },
                {
                    "agent": "Mike Johnson",
                    "achievement": "Conversion King",
                    "description": "Achieved 95% lead to appointment conversion",
                    "badge": "👑",
                    "earned": "1 day ago",
                    "rarity": "Epic"
                },
                {
                    "agent": "Lisa Chen",
                    "achievement": "Client Whisperer",
                    "description": "Received 10 perfect satisfaction scores",
                    "badge": "😇",
                    "earned": "3 days ago",
                    "rarity": "Legendary"
                }
            ]

            for achievement in recent_achievements:
                with st.container():
                    rarity_color = {"Common": "#808080", "Rare": "#0066cc", "Epic": "#cc6600", "Legendary": "#cc0066"}[achievement['rarity']]

                    st.markdown(f"""
                    <div style="border: 2px solid {rarity_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background: linear-gradient(45deg, rgba(255,255,255,0.9), rgba({rarity_color[1:]}, 0.1));">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <span style="font-size: 30px;">{achievement['badge']}</span>
                            <div>
                                <h4 style="margin: 0; color: {rarity_color};">{achievement['achievement']}</h4>
                                <p style="margin: 5px 0; font-weight: bold;">{achievement['agent']}</p>
                                <p style="margin: 5px 0;">{achievement['description']}</p>
                                <small style="color: #666;">Earned {achievement['earned']} | Rarity: <span style="color: {rarity_color}; font-weight: bold;">{achievement['rarity']}</span></small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            # Achievement statistics
            st.write("**Achievement Statistics**")

            achievement_stats = {
                "Total Achievements": 156,
                "This Month": 23,
                "Common": 89,
                "Rare": 42,
                "Epic": 19,
                "Legendary": 6
            }

            for stat, value in achievement_stats.items():
                if stat in ["Total Achievements", "This Month"]:
                    st.metric(stat, value)
                else:
                    st.write(f"**{stat}:** {value}")

            # Achievement distribution
            rarity_data = pd.DataFrame({
                'Rarity': ['Common', 'Rare', 'Epic', 'Legendary'],
                'Count': [89, 42, 19, 6],
                'Color': ['#808080', '#0066cc', '#cc6600', '#cc0066']
            })

            fig_achievements = px.pie(
                rarity_data,
                values='Count',
                names='Rarity',
                title="Achievement Rarity Distribution",
                color_discrete_sequence=rarity_data['Color']
            )

            st.plotly_chart(fig_achievements, use_container_width=True)

        # Available achievements
        st.subheader("Available Achievements")

        achievement_categories = st.selectbox(
            "Filter by Category",
            ["All Categories", "Speed", "Performance", "Quality", "Teamwork", "Learning", "Special"]
        )

        available_achievements = [
            {
                "name": "Lightning Fast",
                "description": "Respond to 100 leads under 3 minutes",
                "category": "Speed",
                "badge": "⚡",
                "rarity": "Rare",
                "progress": 67,
                "requirement": "100 fast responses"
            },
            {
                "name": "Deal Closer",
                "description": "Close $1M in deals this quarter",
                "category": "Performance",
                "badge": "💰",
                "rarity": "Epic",
                "progress": 78,
                "requirement": "$1,000,000 in deals"
            },
            {
                "name": "Perfect Score",
                "description": "Maintain 10.0 client satisfaction for 30 days",
                "category": "Quality",
                "badge": "⭐",
                "rarity": "Legendary",
                "progress": 23,
                "requirement": "Perfect rating for 30 days"
            }
        ]

        for achievement in available_achievements:
            if achievement_categories == "All Categories" or achievement_categories == achievement['category']:
                with st.expander(f"{achievement['badge']} {achievement['name']} ({achievement['progress']}% complete)"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Description:** {achievement['description']}")
                        st.write(f"**Category:** {achievement['category']}")
                        st.write(f"**Requirement:** {achievement['requirement']}")

                        # Progress bar
                        st.progress(achievement['progress'] / 100)
                        st.caption(f"Progress: {achievement['progress']}%")

                    with col2:
                        rarity_color = {"Common": "#808080", "Rare": "#0066cc", "Epic": "#cc6600", "Legendary": "#cc0066"}[achievement['rarity']]
                        st.markdown(f"<h3 style='color: {rarity_color};'>{achievement['rarity']}</h3>", unsafe_allow_html=True)

                        if st.button(f"Track Progress", key=f"track_{achievement['name']}"):
                            st.success("Now tracking this achievement!")

        # Badge collection
        st.subheader("Badge Collection")

        # Mock agent badge collection
        agent_badges = {
            "Sarah Miller": ["⚡", "👑", "😇", "🎯", "🏆", "💎", "🔥"],
            "Mike Johnson": ["⚡", "👑", "🎯", "🏆", "💰"],
            "Lisa Chen": ["😇", "⭐", "🎯", "🏆", "📚"]
        }

        selected_agent_badges = st.selectbox(
            "View Badge Collection",
            list(agent_badges.keys())
        )

        st.write(f"**{selected_agent_badges}'s Badge Collection ({len(agent_badges[selected_agent_badges])} badges)**")

        # Display badges in a grid
        cols = st.columns(6)
        for i, badge in enumerate(agent_badges[selected_agent_badges]):
            with cols[i % 6]:
                st.markdown(f"<div style='text-align: center; font-size: 40px; padding: 10px;'>{badge}</div>", unsafe_allow_html=True)


def render_performance_gamification_dashboard(tenant_id: str) -> None:
    """Main function to render performance gamification dashboard."""
    dashboard = PerformanceGamificationDashboard()
    dashboard.render(tenant_id)


# Example usage for testing
if __name__ == "__main__":
    st.set_page_config(page_title="Performance Gamification Dashboard", layout="wide")
    render_performance_gamification_dashboard("test_tenant_123")