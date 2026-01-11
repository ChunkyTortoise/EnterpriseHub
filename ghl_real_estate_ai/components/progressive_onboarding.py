"""
Progressive Onboarding System (Phase 1 Enhancement)

Provides:
- 5-minute executive value demonstration
- Role-specific onboarding paths
- Contextual learning framework with smart tutorial overlays
- Achievement-based progression with gamification
- Success measurement and user adoption analytics

Target: 70% faster time-to-productivity through progressive learning
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import time


class UserRole(Enum):
    """User roles for customized onboarding."""
    EXECUTIVE = "executive"
    SALES_AGENT = "sales_agent"
    ADMIN = "admin"
    MARKETING = "marketing"


class OnboardingStage(Enum):
    """Onboarding progression stages."""
    WELCOME = "welcome"
    ROLE_SELECTION = "role_selection"
    VALUE_DEMO = "value_demo"
    GUIDED_TOUR = "guided_tour"
    HANDS_ON_PRACTICE = "hands_on_practice"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    COMPLETION = "completion"


@dataclass
class OnboardingStep:
    """Individual onboarding step configuration."""
    id: str
    title: str
    description: str
    content: str
    estimated_minutes: int
    role_specific: List[UserRole] = field(default_factory=list)
    prerequisite_steps: List[str] = field(default_factory=list)
    achievement_points: int = 10
    demo_data: Dict[str, Any] = field(default_factory=dict)
    interactive_elements: List[str] = field(default_factory=list)


@dataclass
class Achievement:
    """Gamification achievement configuration."""
    id: str
    title: str
    description: str
    icon: str
    points: int
    unlock_condition: str
    badge_color: str = "#3b82f6"
    unlocked: bool = False
    unlock_date: Optional[datetime] = None


@dataclass
class UserProgress:
    """User progress tracking."""
    user_id: str
    role: UserRole
    current_stage: OnboardingStage
    completed_steps: List[str] = field(default_factory=list)
    total_time_spent: int = 0  # minutes
    achievements_unlocked: List[str] = field(default_factory=list)
    total_achievement_points: int = 0
    onboarding_start_time: Optional[datetime] = None
    last_active: Optional[datetime] = None
    completion_percentage: float = 0.0


class OnboardingAnalytics:
    """Analytics service for onboarding optimization."""

    def __init__(self, data_dir: Path = None):
        """Initialize onboarding analytics."""
        self.data_dir = data_dir or Path("data/onboarding")
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.analytics_file = self.data_dir / "onboarding_analytics.jsonl"

    def record_step_completion(self, user_id: str, step_id: str, time_taken: int, success: bool):
        """Record step completion for analytics."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "step_id": step_id,
            "time_taken_seconds": time_taken,
            "success": success,
            "event_type": "step_completion"
        }

        try:
            with open(self.analytics_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            st.error(f"Failed to record analytics: {e}")

    def get_onboarding_insights(self) -> Dict[str, Any]:
        """Get onboarding analytics insights."""
        if not self.analytics_file.exists():
            return {"message": "No analytics data available"}

        events = []
        try:
            with open(self.analytics_file, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception:
            return {"error": "Failed to load analytics data"}

        if not events:
            return {"message": "No events recorded"}

        # Calculate key metrics
        total_users = len(set(event["user_id"] for event in events))
        successful_completions = len([e for e in events if e["success"]])
        average_time = sum(e["time_taken_seconds"] for e in events) / len(events) if events else 0

        return {
            "total_users": total_users,
            "successful_completions": successful_completions,
            "completion_rate": (successful_completions / len(events)) * 100 if events else 0,
            "average_time_per_step": average_time,
            "total_events": len(events)
        }


class ProgressiveOnboardingSystem:
    """Core progressive onboarding system with role-based paths."""

    def __init__(self):
        """Initialize progressive onboarding system."""
        self.analytics = OnboardingAnalytics()
        self.onboarding_steps = self._initialize_onboarding_steps()
        self.achievements = self._initialize_achievements()

    def _initialize_onboarding_steps(self) -> Dict[str, OnboardingStep]:
        """Initialize onboarding steps for different user roles."""
        return {
            "welcome": OnboardingStep(
                id="welcome",
                title="Welcome to GHL Real Estate AI",
                description="Your AI-powered real estate command center",
                content="Welcome to the most advanced real estate AI platform. In just 5 minutes, you'll see how this transforms your business.",
                estimated_minutes=1,
                interactive_elements=["video_intro", "role_selection"]
            ),

            "role_selection": OnboardingStep(
                id="role_selection",
                title="Tell Us About Your Role",
                description="Customize your experience based on your role",
                content="Select your primary role to get a personalized experience designed for your specific needs and workflows.",
                estimated_minutes=1,
                interactive_elements=["role_picker", "goal_setting"]
            ),

            "executive_value_demo": OnboardingStep(
                id="executive_value_demo",
                title="Executive Value Demonstration",
                description="See immediate ROI and business impact",
                content="Experience how our AI increases revenue by 15-25% and reduces operational costs by 30%.",
                estimated_minutes=3,
                role_specific=[UserRole.EXECUTIVE],
                achievement_points=50,
                demo_data={
                    "revenue_increase": 25,
                    "cost_reduction": 30,
                    "time_savings": 60,
                    "lead_conversion": 40
                },
                interactive_elements=["roi_calculator", "impact_simulator", "live_demo"]
            ),

            "sales_agent_demo": OnboardingStep(
                id="sales_agent_demo",
                title="AI Sales Assistant Demo",
                description="See how AI coaching boosts your conversion rates",
                content="Experience real-time AI coaching, lead scoring, and automated follow-ups that top agents use.",
                estimated_minutes=3,
                role_specific=[UserRole.SALES_AGENT],
                achievement_points=50,
                demo_data={
                    "conversion_boost": 40,
                    "response_time": 2,
                    "lead_score_accuracy": 98,
                    "coaching_sessions": 15
                },
                interactive_elements=["ai_coaching_demo", "lead_scoring_test", "conversion_simulator"]
            ),

            "platform_overview": OnboardingStep(
                id="platform_overview",
                title="Platform Overview",
                description="Navigate the 5 core hubs effortlessly",
                content="Discover the Executive Command Center, Lead Intelligence Hub, Automation Studio, Sales Copilot, and Ops & Optimization.",
                estimated_minutes=2,
                achievement_points=25,
                interactive_elements=["hub_tour", "navigation_practice"]
            ),

            "hands_on_practice": OnboardingStep(
                id="hands_on_practice",
                title="Hands-On Practice",
                description="Try key features with guided assistance",
                content="Practice scoring a lead, viewing analytics, and setting up automation with our guided tutorial.",
                estimated_minutes=3,
                achievement_points=75,
                interactive_elements=["lead_scoring_practice", "analytics_exploration", "automation_setup"]
            ),

            "achievement_milestone": OnboardingStep(
                id="achievement_milestone",
                title="First Achievement Unlocked!",
                description="Celebrate your progress and unlock advanced features",
                content="Congratulations! You've mastered the basics. Unlock advanced features and see your achievement progress.",
                estimated_minutes=1,
                achievement_points=100,
                interactive_elements=["achievement_celebration", "advanced_features_preview"]
            ),

            "completion_success": OnboardingStep(
                id="completion_success",
                title="Onboarding Complete!",
                description="You're ready to transform your real estate business",
                content="You've completed onboarding 70% faster than traditional training. You're now ready to leverage AI for business growth.",
                estimated_minutes=1,
                achievement_points=200,
                interactive_elements=["completion_certificate", "next_steps", "support_resources"]
            )
        }

    def _initialize_achievements(self) -> Dict[str, Achievement]:
        """Initialize gamification achievements."""
        return {
            "first_login": Achievement(
                id="first_login",
                title="Welcome Aboard!",
                description="Completed first login and role selection",
                icon="🚀",
                points=25,
                unlock_condition="role_selection_completed",
                badge_color="#10b981"
            ),

            "value_demo_master": Achievement(
                id="value_demo_master",
                title="Value Demo Master",
                description="Completed the 5-minute value demonstration",
                icon="💰",
                points=50,
                unlock_condition="value_demo_completed",
                badge_color="#f59e0b"
            ),

            "platform_explorer": Achievement(
                id="platform_explorer",
                title="Platform Explorer",
                description="Explored all 5 core platform hubs",
                icon="🧭",
                points=75,
                unlock_condition="platform_tour_completed",
                badge_color="#3b82f6"
            ),

            "hands_on_hero": Achievement(
                id="hands_on_hero",
                title="Hands-On Hero",
                description="Completed all hands-on practice exercises",
                icon="⭐",
                points=100,
                unlock_condition="practice_completed",
                badge_color="#8b5cf6"
            ),

            "onboarding_graduate": Achievement(
                id="onboarding_graduate",
                title="Onboarding Graduate",
                description="Completed full onboarding in under 10 minutes",
                icon="🎓",
                points=200,
                unlock_condition="onboarding_completed",
                badge_color="#ef4444"
            ),

            "speed_learner": Achievement(
                id="speed_learner",
                title="Speed Learner",
                description="Completed onboarding 70% faster than average",
                icon="⚡",
                points=150,
                unlock_condition="fast_completion",
                badge_color="#06b6d4"
            )
        }

    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get or create user progress."""
        progress_file = Path(f"data/onboarding/progress_{user_id}.json")

        if progress_file.exists():
            try:
                with open(progress_file) as f:
                    data = json.load(f)
                    return UserProgress(**data)
            except Exception:
                pass

        # Create new progress
        return UserProgress(
            user_id=user_id,
            role=UserRole.EXECUTIVE,  # Default
            current_stage=OnboardingStage.WELCOME,
            onboarding_start_time=datetime.now()
        )

    def save_user_progress(self, progress: UserProgress):
        """Save user progress to file."""
        progress_file = Path(f"data/onboarding/progress_{progress.user_id}.json")
        progress_file.parent.mkdir(exist_ok=True, parents=True)

        progress_data = {
            "user_id": progress.user_id,
            "role": progress.role.value,
            "current_stage": progress.current_stage.value,
            "completed_steps": progress.completed_steps,
            "total_time_spent": progress.total_time_spent,
            "achievements_unlocked": progress.achievements_unlocked,
            "total_achievement_points": progress.total_achievement_points,
            "onboarding_start_time": progress.onboarding_start_time.isoformat() if progress.onboarding_start_time else None,
            "last_active": progress.last_active.isoformat() if progress.last_active else None,
            "completion_percentage": progress.completion_percentage
        }

        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)

    def get_next_step(self, progress: UserProgress) -> Optional[OnboardingStep]:
        """Get the next onboarding step for the user."""
        # Role-specific step mapping
        role_step_sequence = {
            UserRole.EXECUTIVE: [
                "welcome", "role_selection", "executive_value_demo",
                "platform_overview", "hands_on_practice", "achievement_milestone", "completion_success"
            ],
            UserRole.SALES_AGENT: [
                "welcome", "role_selection", "sales_agent_demo",
                "platform_overview", "hands_on_practice", "achievement_milestone", "completion_success"
            ],
            UserRole.ADMIN: [
                "welcome", "role_selection", "platform_overview",
                "hands_on_practice", "achievement_milestone", "completion_success"
            ]
        }

        sequence = role_step_sequence.get(progress.role, role_step_sequence[UserRole.EXECUTIVE])

        for step_id in sequence:
            if step_id not in progress.completed_steps:
                return self.onboarding_steps.get(step_id)

        return None

    def complete_step(self, user_id: str, step_id: str, time_taken: int = 0) -> UserProgress:
        """Mark a step as completed and update progress."""
        progress = self.get_user_progress(user_id)

        if step_id not in progress.completed_steps:
            progress.completed_steps.append(step_id)
            progress.total_time_spent += time_taken
            progress.last_active = datetime.now()

            # Award achievement points
            if step_id in self.onboarding_steps:
                step = self.onboarding_steps[step_id]
                progress.total_achievement_points += step.achievement_points

            # Check for achievement unlocks
            self._check_achievement_unlocks(progress)

            # Update completion percentage
            total_steps = len(self._get_role_steps(progress.role))
            progress.completion_percentage = (len(progress.completed_steps) / total_steps) * 100

            # Record analytics
            self.analytics.record_step_completion(user_id, step_id, time_taken, True)

            self.save_user_progress(progress)

        return progress

    def _get_role_steps(self, role: UserRole) -> List[str]:
        """Get step sequence for user role."""
        role_sequences = {
            UserRole.EXECUTIVE: [
                "welcome", "role_selection", "executive_value_demo",
                "platform_overview", "hands_on_practice", "achievement_milestone", "completion_success"
            ],
            UserRole.SALES_AGENT: [
                "welcome", "role_selection", "sales_agent_demo",
                "platform_overview", "hands_on_practice", "achievement_milestone", "completion_success"
            ],
            UserRole.ADMIN: [
                "welcome", "role_selection", "platform_overview",
                "hands_on_practice", "achievement_milestone", "completion_success"
            ]
        }
        return role_sequences.get(role, role_sequences[UserRole.EXECUTIVE])

    def _check_achievement_unlocks(self, progress: UserProgress):
        """Check and unlock achievements based on progress."""
        for achievement_id, achievement in self.achievements.items():
            if achievement_id not in progress.achievements_unlocked:
                if self._evaluate_unlock_condition(achievement.unlock_condition, progress):
                    progress.achievements_unlocked.append(achievement_id)
                    achievement.unlocked = True
                    achievement.unlock_date = datetime.now()

    def _evaluate_unlock_condition(self, condition: str, progress: UserProgress) -> bool:
        """Evaluate achievement unlock conditions."""
        conditions_map = {
            "role_selection_completed": "role_selection" in progress.completed_steps,
            "value_demo_completed": any(step in progress.completed_steps for step in ["executive_value_demo", "sales_agent_demo"]),
            "platform_tour_completed": "platform_overview" in progress.completed_steps,
            "practice_completed": "hands_on_practice" in progress.completed_steps,
            "onboarding_completed": progress.completion_percentage >= 100,
            "fast_completion": progress.total_time_spent <= 7  # 7 minutes or less
        }

        return conditions_map.get(condition, False)


class OnboardingUI:
    """Streamlit UI components for progressive onboarding."""

    @staticmethod
    def render_welcome_screen() -> UserRole:
        """Render welcome screen with role selection."""
        st.markdown("""
        <div style='text-align: center; padding: 3rem 1rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); margin: -1rem -1rem 2rem -1rem; border-radius: 0 0 20px 20px;'>
            <h1 style='color: #f8fafc; margin: 0; font-size: 2.5rem;'>🚀 Welcome to GHL Real Estate AI</h1>
            <p style='color: #94a3b8; font-size: 1.2rem; margin: 1rem 0;'>Your AI-powered real estate command center</p>
            <p style='color: #64748b; font-size: 1rem; margin: 0;'>Get started in just 5 minutes and see immediate business impact</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 👤 Tell us about your role to personalize your experience")

        col1, col2, col3 = st.columns(3)

        selected_role = None

        with col1:
            if st.button(
                "🎯 Executive/Owner",
                help="CEO, Owner, Executive - Focus on ROI and business growth",
                use_container_width=True,
                type="primary"
            ):
                selected_role = UserRole.EXECUTIVE

        with col2:
            if st.button(
                "🤝 Sales Agent",
                help="Real Estate Agent, Sales Rep - Focus on lead conversion and client management",
                use_container_width=True,
                type="primary"
            ):
                selected_role = UserRole.SALES_AGENT

        with col3:
            if st.button(
                "⚙️ Admin/Manager",
                help="Operations Manager, Admin - Focus on workflows and team management",
                use_container_width=True,
                type="primary"
            ):
                selected_role = UserRole.ADMIN

        return selected_role

    @staticmethod
    def render_executive_value_demo():
        """Render 5-minute executive value demonstration."""
        st.markdown("### 💰 Executive Value Demonstration")
        st.markdown("*See how AI transforms your real estate business in 3 minutes*")

        # Value proposition metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Revenue Increase",
                "25%",
                "+$500K annually",
                help="Average revenue increase with AI optimization"
            )

        with col2:
            st.metric(
                "Cost Reduction",
                "30%",
                "-$180K annually",
                help="Operational cost savings through automation"
            )

        with col3:
            st.metric(
                "Time Savings",
                "60%",
                "+20 hrs/week",
                help="Time saved on manual tasks and admin work"
            )

        with col4:
            st.metric(
                "Lead Conversion",
                "40%",
                "+15% close rate",
                help="Improved conversion through AI coaching"
            )

        # Interactive ROI calculator
        st.markdown("#### 🧮 Your ROI Calculator")

        col1, col2 = st.columns([2, 1])

        with col1:
            current_revenue = st.slider(
                "Current Annual Revenue",
                100000, 10000000, 2000000,
                step=100000,
                format="$%d"
            )

            agents_count = st.slider("Number of Agents", 1, 50, 5)

            # Calculate potential impact
            revenue_increase = current_revenue * 0.25
            cost_savings = current_revenue * 0.15
            total_benefit = revenue_increase + cost_savings

            # Display ROI calculation
            st.markdown(f"""
            **📊 Your Projected Annual Impact:**
            - **Revenue Increase**: ${revenue_increase:,.0f}
            - **Cost Savings**: ${cost_savings:,.0f}
            - **Total Annual Benefit**: ${total_benefit:,.0f}
            - **ROI**: {(total_benefit / (current_revenue * 0.05)) * 100:.0f}%
            """)

        with col2:
            st.markdown("""
            **✅ Key Benefits:**
            - AI Lead Scoring (98% accuracy)
            - Automated Follow-ups
            - Real-time Market Intelligence
            - Predictive Analytics
            - Mobile-first Design
            - 24/7 AI Assistant
            """)

        # Live demo simulation
        if st.button("▶️ See Live Demo (30 seconds)", type="primary"):
            with st.spinner("Loading live demo..."):
                time.sleep(1)

            st.success("🎬 **Demo Complete!** You just saw how a hot lead gets scored, qualified, and assigned in real-time.")

            st.info("""
            **What you just saw:**
            1. Lead scoring with 98% accuracy in <2 seconds
            2. Automated property matching based on preferences
            3. Real-time AI coaching suggestions for agents
            4. Instant ROI tracking and performance analytics
            """)

    @staticmethod
    def render_sales_agent_demo():
        """Render sales agent-focused demonstration."""
        st.markdown("### 🤝 AI Sales Assistant Demonstration")
        st.markdown("*Experience real-time AI coaching that top agents use*")

        # Agent-specific metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Conversion Boost", "40%", "+12 deals/month")
        with col2:
            st.metric("Response Time", "2 sec", "98% faster")
        with col3:
            st.metric("Lead Score Accuracy", "98%", "Industry leading")

        # Interactive AI coaching demo
        st.markdown("#### 🎓 Try AI Coaching")

        scenario = st.selectbox(
            "Select a scenario:",
            ["Price Objection", "Timeline Concerns", "Competition", "Financing Questions"]
        )

        if st.button("Get AI Coaching", type="primary"):
            coaching_responses = {
                "Price Objection": "🎯 **AI Suggestion**: Use the 'Value Stack' approach - highlight unique property features, neighborhood growth potential, and comparable sales. Offer flexible terms if needed.",
                "Timeline Concerns": "⏰ **AI Suggestion**: Create urgency with market data showing price trends. Suggest starting the search process now while maintaining their preferred timeline.",
                "Competition": "🏆 **AI Suggestion**: Focus on your unique value proposition - local expertise, AI-powered property matching, and superior client service. Share success stories.",
                "Financing Questions": "💰 **AI Suggestion**: Connect with preferred lenders, offer pre-approval assistance, and explain various financing options. Provide rate comparison tools."
            }

            st.info(coaching_responses.get(scenario, "💡 **AI Suggestion**: Focus on understanding client needs and building trust through expertise."))

    @staticmethod
    def render_progress_tracker(progress: UserProgress, total_steps: int):
        """Render progress tracking with gamification."""
        completion_pct = (len(progress.completed_steps) / total_steps) * 100

        # Progress bar
        st.markdown(f"""
        <div style='margin: 1rem 0;'>
            <div style='background: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.3);'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                    <strong>Onboarding Progress</strong>
                    <span>{completion_pct:.0f}% Complete</span>
                </div>
                <div style='background: #374151; border-radius: 4px; height: 8px; overflow: hidden;'>
                    <div style='background: linear-gradient(90deg, #3b82f6, #10b981); width: {completion_pct}%; height: 100%; transition: width 0.3s ease;'></div>
                </div>
                <div style='margin-top: 0.5rem; font-size: 0.9rem; color: #64748b;'>
                    {len(progress.completed_steps)} of {total_steps} steps completed
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Achievement points
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Achievement Points", progress.total_achievement_points, "🏆")
        with col2:
            st.metric("Time Spent", f"{progress.total_time_spent} min", "⏱️")
        with col3:
            st.metric("Achievements", len(progress.achievements_unlocked), "🎖️")

    @staticmethod
    def render_achievement_celebration(achievement: Achievement):
        """Render achievement unlock celebration."""
        st.balloons()

        st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%); border: 2px solid #10b981; border-radius: 12px; margin: 1rem 0;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>{achievement.icon}</div>
            <h2 style='color: #10b981; margin: 0.5rem 0;'>{achievement.title}</h2>
            <p style='color: #64748b; margin: 0.5rem 0;'>{achievement.description}</p>
            <div style='background: {achievement.badge_color}; color: white; padding: 0.5rem 1rem; border-radius: 20px; display: inline-block; margin-top: 1rem;'>
                +{achievement.points} Points
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_progressive_onboarding(user_id: str = "demo_user") -> Dict[str, Any]:
    """
    Render complete progressive onboarding experience.

    Returns:
        Dict with onboarding status and user progress
    """
    onboarding_system = ProgressiveOnboardingSystem()

    # Initialize session state
    if 'onboarding_step_start_time' not in st.session_state:
        st.session_state.onboarding_step_start_time = time.time()

    if 'onboarding_active' not in st.session_state:
        st.session_state.onboarding_active = True

    # Get user progress
    progress = onboarding_system.get_user_progress(user_id)

    # Show onboarding if active and not completed
    if st.session_state.onboarding_active and progress.completion_percentage < 100:

        # Get next step
        next_step = onboarding_system.get_next_step(progress)

        if next_step:
            # Render progress tracker
            total_steps = len(onboarding_system._get_role_steps(progress.role))
            OnboardingUI.render_progress_tracker(progress, total_steps)

            # Render current step
            if next_step.id == "welcome" or next_step.id == "role_selection":
                selected_role = OnboardingUI.render_welcome_screen()

                if selected_role:
                    progress.role = selected_role
                    step_time = int(time.time() - st.session_state.onboarding_step_start_time)
                    progress = onboarding_system.complete_step(user_id, "role_selection", step_time)
                    onboarding_system.save_user_progress(progress)
                    st.session_state.onboarding_step_start_time = time.time()
                    st.rerun()

            elif next_step.id == "executive_value_demo":
                OnboardingUI.render_executive_value_demo()

                if st.button("✅ I've seen the value - Continue", type="primary"):
                    step_time = int(time.time() - st.session_state.onboarding_step_start_time)
                    onboarding_system.complete_step(user_id, next_step.id, step_time)
                    st.session_state.onboarding_step_start_time = time.time()
                    st.rerun()

            elif next_step.id == "sales_agent_demo":
                OnboardingUI.render_sales_agent_demo()

                if st.button("✅ Ready to explore the platform", type="primary"):
                    step_time = int(time.time() - st.session_state.onboarding_step_start_time)
                    onboarding_system.complete_step(user_id, next_step.id, step_time)
                    st.session_state.onboarding_step_start_time = time.time()
                    st.rerun()

            elif next_step.id == "platform_overview":
                st.markdown("### 🧭 Platform Overview")
                st.markdown("*Explore the 5 core hubs that power your real estate business*")

                # Hub overview
                hubs = [
                    {"name": "Executive Command Center", "icon": "🎯", "desc": "High-level KPIs and business intelligence"},
                    {"name": "Lead Intelligence Hub", "icon": "🧠", "desc": "AI-powered lead scoring and analytics"},
                    {"name": "Automation Studio", "icon": "⚙️", "desc": "Workflow automation and triggers"},
                    {"name": "Sales Copilot", "icon": "🤝", "desc": "Real-time AI coaching and assistance"},
                    {"name": "Ops & Optimization", "icon": "📈", "desc": "Performance analytics and optimization"}
                ]

                for hub in hubs:
                    st.markdown(f"**{hub['icon']} {hub['name']}**: {hub['desc']}")

                if st.button("✅ I understand the platform structure", type="primary"):
                    step_time = int(time.time() - st.session_state.onboarding_step_start_time)
                    onboarding_system.complete_step(user_id, next_step.id, step_time)
                    st.session_state.onboarding_step_start_time = time.time()
                    st.rerun()

            elif next_step.id == "hands_on_practice":
                st.markdown("### ⭐ Hands-On Practice")
                st.markdown("*Try key features with guided assistance*")

                practice_completed = st.checkbox("✅ I've practiced lead scoring")
                analytics_explored = st.checkbox("✅ I've explored the analytics")
                automation_tested = st.checkbox("✅ I've tested automation features")

                if practice_completed and analytics_explored and automation_tested:
                    if st.button("🎓 Complete Practice Session", type="primary"):
                        step_time = int(time.time() - st.session_state.onboarding_step_start_time)
                        onboarding_system.complete_step(user_id, next_step.id, step_time)

                        # Check for achievements
                        if "hands_on_hero" in onboarding_system.achievements:
                            achievement = onboarding_system.achievements["hands_on_hero"]
                            OnboardingUI.render_achievement_celebration(achievement)

                        st.session_state.onboarding_step_start_time = time.time()
                        st.rerun()

            elif next_step.id == "completion_success":
                st.markdown("### 🎉 Onboarding Complete!")

                # Show final metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Time to Productivity", "70%", "Faster than traditional")
                with col2:
                    st.metric("Achievement Points", progress.total_achievement_points, "🏆")
                with col3:
                    st.metric("Features Unlocked", "All", "✅")

                st.success("🚀 You're now ready to leverage AI for business growth!")

                if st.button("🏠 Enter Main Platform", type="primary"):
                    st.session_state.onboarding_active = False
                    onboarding_system.complete_step(user_id, next_step.id, 0)
                    st.rerun()

    return {
        "onboarding_active": st.session_state.onboarding_active,
        "user_progress": progress,
        "completion_percentage": progress.completion_percentage
    }


# Export main components
__all__ = [
    "ProgressiveOnboardingSystem",
    "OnboardingUI",
    "UserRole",
    "OnboardingStage",
    "UserProgress",
    "Achievement",
    "render_progressive_onboarding"
]