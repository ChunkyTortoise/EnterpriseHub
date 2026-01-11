"""
User Onboarding Service for GHL Real Estate AI

Provides comprehensive onboarding experience including:
- 5-minute executive value demonstration
- Role-based onboarding paths (executive, agent, manager)
- Progressive feature introduction with guided tours
- Contextual help system with smart hints
- Achievement-based progression tracking
- User adoption analytics and optimization
- Interactive tutorials with completion tracking

Designed to accelerate time-to-productivity and maximize user adoption
while providing measurable insights into onboarding effectiveness.
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
from pathlib import Path
from enum import Enum

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class UserRole(Enum):
    """User role types for onboarding customization."""
    EXECUTIVE = "executive"
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"


class OnboardingStage(Enum):
    """Onboarding progress stages."""
    WELCOME = "welcome"
    ROLE_SELECTION = "role_selection"
    QUICK_TOUR = "quick_tour"
    VALUE_DEMO = "value_demo"
    GUIDED_SETUP = "guided_setup"
    FEATURE_EXPLORATION = "feature_exploration"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    COMPLETION = "completion"


@dataclass
class OnboardingStep:
    """Individual onboarding step configuration."""

    id: str
    title: str
    description: str
    content: str
    duration_seconds: int
    target_element: Optional[str] = None
    action_required: bool = False
    completion_criteria: Optional[str] = None
    next_step: Optional[str] = None
    role_specific: List[UserRole] = None

    def __post_init__(self):
        if self.role_specific is None:
            self.role_specific = list(UserRole)


@dataclass
class Achievement:
    """User achievement for gamification."""

    id: str
    title: str
    description: str
    icon: str
    criteria: Dict[str, Any]
    points: int = 100
    unlocked: bool = False
    unlocked_at: Optional[str] = None


@dataclass
class OnboardingProgress:
    """User onboarding progress tracking."""

    user_id: str
    role: UserRole
    current_stage: OnboardingStage
    completed_steps: List[str]
    achievements: List[Achievement]
    start_time: str
    completion_time: Optional[str] = None
    time_spent_seconds: int = 0
    engagement_score: float = 0.0
    completion_percentage: float = 0.0

    def __post_init__(self):
        if not self.completed_steps:
            self.completed_steps = []
        if not self.achievements:
            self.achievements = []


class OnboardingAnalytics:
    """Analytics tracking for onboarding optimization."""

    def __init__(self):
        self.analytics_file = Path("data/onboarding_analytics.json")
        self.analytics_file.parent.mkdir(parents=True, exist_ok=True)

    def track_step_completion(
        self,
        user_id: str,
        step_id: str,
        completion_time: float,
        engagement_score: float = 1.0
    ):
        """Track completion of onboarding step."""
        analytics_data = self._load_analytics()

        event = {
            "user_id": user_id,
            "step_id": step_id,
            "completion_time": completion_time,
            "engagement_score": engagement_score,
            "timestamp": datetime.now().isoformat()
        }

        analytics_data.setdefault("step_completions", []).append(event)
        self._save_analytics(analytics_data)

    def track_user_drop_off(self, user_id: str, step_id: str, reason: str = "unknown"):
        """Track user drop-off point for optimization."""
        analytics_data = self._load_analytics()

        event = {
            "user_id": user_id,
            "step_id": step_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        analytics_data.setdefault("drop_offs", []).append(event)
        self._save_analytics(analytics_data)

    def get_completion_metrics(self) -> Dict[str, Any]:
        """Get onboarding completion metrics."""
        analytics_data = self._load_analytics()

        step_completions = analytics_data.get("step_completions", [])
        drop_offs = analytics_data.get("drop_offs", [])

        # Calculate completion rates
        total_starts = len(set(event["user_id"] for event in step_completions + drop_offs))
        completed = len(set(event["user_id"] for event in step_completions if "completion" in event["step_id"]))

        completion_rate = (completed / total_starts) * 100 if total_starts > 0 else 0

        # Calculate average time to complete
        completion_times = [
            event["completion_time"] for event in step_completions
            if "completion" in event["step_id"]
        ]
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

        return {
            "total_starts": total_starts,
            "completed": completed,
            "completion_rate": completion_rate,
            "avg_completion_time": avg_completion_time,
            "drop_off_points": self._analyze_drop_off_points(drop_offs)
        }

    def _analyze_drop_off_points(self, drop_offs: List[Dict]) -> Dict[str, int]:
        """Analyze common drop-off points."""
        drop_off_counts = {}
        for event in drop_offs:
            step = event["step_id"]
            drop_off_counts[step] = drop_off_counts.get(step, 0) + 1
        return drop_off_counts

    def _load_analytics(self) -> Dict[str, Any]:
        """Load analytics data from file."""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load analytics: {e}")
        return {}

    def _save_analytics(self, data: Dict[str, Any]):
        """Save analytics data to file."""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save analytics: {e}")


class OnboardingTour:
    """Interactive onboarding tour with step-by-step guidance."""

    def __init__(self):
        self.steps = self._initialize_onboarding_steps()
        self.achievements = self._initialize_achievements()

    def _initialize_onboarding_steps(self) -> Dict[str, OnboardingStep]:
        """Initialize onboarding steps for different user roles."""
        return {
            # Welcome and role selection
            "welcome": OnboardingStep(
                id="welcome",
                title="Welcome to GHL Real Estate AI",
                description="Your AI-powered real estate command center",
                content="Welcome to the most advanced real estate AI platform. In the next 5 minutes, we'll show you how this platform can transform your business.",
                duration_seconds=30,
                next_step="role_selection"
            ),

            "role_selection": OnboardingStep(
                id="role_selection",
                title="Tell Us About Your Role",
                description="Customize your experience based on your role",
                content="Select your primary role to get a personalized onboarding experience tailored to your needs.",
                duration_seconds=15,
                action_required=True,
                next_step="executive_value_demo"
            ),

            # Executive 5-minute value demo
            "executive_value_demo": OnboardingStep(
                id="executive_value_demo",
                title="5-Minute Executive Value Demo",
                description="See the immediate business impact",
                content="Let us show you the key metrics and insights that matter most to your business.",
                duration_seconds=300,
                role_specific=[UserRole.EXECUTIVE, UserRole.MANAGER],
                next_step="executive_dashboard_tour"
            ),

            "executive_dashboard_tour": OnboardingStep(
                id="executive_dashboard_tour",
                title="Executive Dashboard Tour",
                description="Navigate your command center",
                content="This is your executive command center. Here you can monitor revenue, track performance, and make data-driven decisions.",
                duration_seconds=60,
                target_element="executive_metrics",
                role_specific=[UserRole.EXECUTIVE, UserRole.MANAGER],
                next_step="ai_insights_intro"
            ),

            # AI insights and automation
            "ai_insights_intro": OnboardingStep(
                id="ai_insights_intro",
                title="AI Insights & Recommendations",
                description="Let AI guide your decisions",
                content="Our AI analyzes your data 24/7 to provide actionable insights and recommendations.",
                duration_seconds=45,
                target_element="ai_insights",
                next_step="automation_studio_intro"
            ),

            "automation_studio_intro": OnboardingStep(
                id="automation_studio_intro",
                title="Automation Studio",
                description="Set up intelligent workflows",
                content="Automate your lead qualification, follow-ups, and client communications with AI-powered workflows.",
                duration_seconds=60,
                target_element="automation_controls",
                next_step="lead_scoring_demo"
            ),

            # Lead management and scoring
            "lead_scoring_demo": OnboardingStep(
                id="lead_scoring_demo",
                title="AI Lead Scoring in Action",
                description="Watch AI qualify leads instantly",
                content="See how our AI scores and prioritizes leads in real-time, helping you focus on the highest-value opportunities.",
                duration_seconds=45,
                target_element="lead_scoring",
                next_step="geographic_insights"
            ),

            "geographic_insights": OnboardingStep(
                id="geographic_insights",
                title="Geographic Market Intelligence",
                description="Visualize opportunities on the map",
                content="Our geographic intelligence shows you where the hottest leads and market opportunities are located.",
                duration_seconds=30,
                target_element="lead_heatmap",
                next_step="achievement_first_tour"
            ),

            # Achievement unlocks
            "achievement_first_tour": OnboardingStep(
                id="achievement_first_tour",
                title="🏆 Achievement Unlocked: Tour Complete!",
                description="You've completed your first platform tour",
                content="Congratulations! You've unlocked your first achievement. Continue exploring to unlock more features and insights.",
                duration_seconds=20,
                next_step="customization_options"
            ),

            # Customization and setup
            "customization_options": OnboardingStep(
                id="customization_options",
                title="Customize Your Experience",
                description="Configure the platform for your market",
                content="Let's configure the platform for your specific market, preferences, and business needs.",
                duration_seconds=90,
                action_required=True,
                next_step="integration_setup"
            ),

            "integration_setup": OnboardingStep(
                id="integration_setup",
                title="Connect Your Systems",
                description="Integrate with GoHighLevel and other tools",
                content="Connect your existing tools and CRM to maximize the platform's effectiveness.",
                duration_seconds=120,
                action_required=True,
                next_step="first_automation"
            ),

            # Guided actions
            "first_automation": OnboardingStep(
                id="first_automation",
                title="Create Your First Automation",
                description="Set up an intelligent workflow",
                content="Let's create your first automated workflow to start saving time and improving conversions.",
                duration_seconds=180,
                action_required=True,
                completion_criteria="automation_created",
                next_step="onboarding_complete"
            ),

            # Completion
            "onboarding_complete": OnboardingStep(
                id="onboarding_complete",
                title="🎉 Welcome to Your AI-Powered Future",
                description="You're all set! Start growing your business",
                content="You've successfully completed onboarding! You're now ready to leverage AI to grow your real estate business.",
                duration_seconds=30
            )
        }

    def _initialize_achievements(self) -> List[Achievement]:
        """Initialize gamification achievements."""
        return [
            Achievement(
                id="tour_complete",
                title="Platform Explorer",
                description="Completed the platform tour",
                icon="🗺️",
                criteria={"step_completed": "geographic_insights"},
                points=100
            ),
            Achievement(
                id="first_automation",
                title="Automation Master",
                description="Created your first automation workflow",
                icon="🤖",
                criteria={"automation_created": True},
                points=200
            ),
            Achievement(
                id="dashboard_expert",
                title="Dashboard Expert",
                description="Explored all dashboard features",
                icon="📊",
                criteria={"dashboard_sections_visited": 5},
                points=150
            ),
            Achievement(
                id="ai_advocate",
                title="AI Advocate",
                description="Used AI recommendations 5 times",
                icon="🧠",
                criteria={"ai_recommendations_used": 5},
                points=150
            ),
            Achievement(
                id="power_user",
                title="Power User",
                description="Used the platform for 7 consecutive days",
                icon="⚡",
                criteria={"consecutive_days": 7},
                points=300
            )
        ]


class UserOnboardingService:
    """
    Comprehensive User Onboarding Service

    Provides:
    - Role-based onboarding flows
    - 5-minute executive value demonstration
    - Progressive feature introduction
    - Achievement-based gamification
    - Analytics and optimization
    - Contextual help system
    """

    def __init__(self):
        self.tour = OnboardingTour()
        self.analytics = OnboardingAnalytics()
        self.progress_file = Path("data/onboarding_progress.json")
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_session_state()

        logger.info("User Onboarding Service initialized")

    def _initialize_session_state(self):
        """Initialize session state for onboarding."""
        if "onboarding_active" not in st.session_state:
            st.session_state.onboarding_active = False

        if "onboarding_progress" not in st.session_state:
            st.session_state.onboarding_progress = None

        if "current_step" not in st.session_state:
            st.session_state.current_step = None

        if "onboarding_start_time" not in st.session_state:
            st.session_state.onboarding_start_time = None

    def start_onboarding(self, user_id: str = "demo_user") -> bool:
        """Start the onboarding process for a user."""
        try:
            # Check if user has already completed onboarding
            if self._is_onboarding_complete(user_id):
                return False

            # Initialize onboarding progress
            progress = OnboardingProgress(
                user_id=user_id,
                role=UserRole.EXECUTIVE,  # Default, will be updated
                current_stage=OnboardingStage.WELCOME,
                completed_steps=[],
                achievements=self.tour.achievements.copy(),
                start_time=datetime.now().isoformat()
            )

            st.session_state.onboarding_active = True
            st.session_state.onboarding_progress = progress
            st.session_state.current_step = "welcome"
            st.session_state.onboarding_start_time = datetime.now()

            logger.info(f"Started onboarding for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start onboarding: {e}")
            return False

    def render_onboarding_step(self) -> bool:
        """
        Render the current onboarding step.

        Returns:
            bool: True if onboarding should continue, False if complete
        """
        if not st.session_state.onboarding_active or not st.session_state.current_step:
            return False

        current_step_id = st.session_state.current_step
        step = self.tour.steps.get(current_step_id)

        if not step:
            self._complete_onboarding()
            return False

        # Render step content
        self._render_step_ui(step)

        # Handle step completion
        if self._check_step_completion(step):
            self._advance_to_next_step(step)

        return st.session_state.onboarding_active

    def _render_step_ui(self, step: OnboardingStep):
        """Render the UI for a specific onboarding step."""
        # Create onboarding overlay
        with st.container():
            st.markdown(f"""
            <div style='
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
            '>
                <div style='
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    padding: 2rem;
                    border-radius: 16px;
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    max-width: 600px;
                    width: 90%;
                    color: white;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
                '>
                    <div style='text-align: center; margin-bottom: 1.5rem;'>
                        <h2 style='color: #3b82f6; margin-bottom: 0.5rem; font-size: 1.5rem;'>
                            {step.title}
                        </h2>
                        <p style='color: #94a3b8; margin: 0; font-size: 1rem;'>
                            {step.description}
                        </p>
                    </div>

                    <div style='margin-bottom: 1.5rem;'>
                        <p style='color: #f8fafc; line-height: 1.6; margin: 0;'>
                            {step.content}
                        </p>
                    </div>

                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='display: flex; gap: 1rem;'>
                            <button onclick='skipOnboarding()' style='
                                background: transparent;
                                border: 1px solid #64748b;
                                color: #94a3b8;
                                padding: 0.5rem 1rem;
                                border-radius: 8px;
                                cursor: pointer;
                            '>Skip Tour</button>
                        </div>
                        <div>
                            <span style='color: #64748b; font-size: 0.875rem; margin-right: 1rem;'>
                                Step {len(st.session_state.onboarding_progress.completed_steps) + 1} of {len(self.tour.steps)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Render action buttons in sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🎯 Onboarding Progress")

            # Progress bar
            progress_pct = (len(st.session_state.onboarding_progress.completed_steps) / len(self.tour.steps)) * 100
            st.progress(progress_pct / 100)
            st.caption(f"Progress: {progress_pct:.0f}%")

            # Step controls
            col1, col2 = st.columns(2)

            with col1:
                if st.button("⏭️ Next", key="onboarding_next"):
                    self._advance_to_next_step(step)

            with col2:
                if st.button("❌ Skip", key="onboarding_skip"):
                    self._complete_onboarding()

            # Show achievements
            if st.session_state.onboarding_progress.achievements:
                unlocked = [a for a in st.session_state.onboarding_progress.achievements if a.unlocked]
                if unlocked:
                    st.markdown("### 🏆 Achievements")
                    for achievement in unlocked[-3:]:  # Show last 3
                        st.success(f"{achievement.icon} {achievement.title}")

    def _render_role_selection(self):
        """Render role selection step."""
        st.markdown("### Select Your Role")

        role_options = {
            "Executive/Owner": UserRole.EXECUTIVE,
            "Real Estate Agent": UserRole.AGENT,
            "Team Manager": UserRole.MANAGER,
            "System Administrator": UserRole.ADMIN
        }

        selected_role = st.selectbox(
            "What's your primary role?",
            options=list(role_options.keys()),
            key="role_selection"
        )

        if st.button("Continue with Selected Role", key="confirm_role"):
            st.session_state.onboarding_progress.role = role_options[selected_role]
            return True

        return False

    def _render_executive_value_demo(self):
        """Render the 5-minute executive value demonstration."""
        st.markdown("### 🎯 5-Minute Executive Value Demo")

        demo_steps = [
            {
                "title": "Revenue Dashboard",
                "content": "See your revenue pipeline, conversion rates, and growth trends in real-time.",
                "metric": "$2.4M Pipeline Value",
                "improvement": "+15% vs last month"
            },
            {
                "title": "AI Lead Scoring",
                "content": "AI automatically scores and prioritizes your leads for maximum conversion.",
                "metric": "95% Accuracy",
                "improvement": "87% more qualified leads"
            },
            {
                "title": "Automated Workflows",
                "content": "Save 15+ hours per week with intelligent automation and follow-ups.",
                "metric": "15 Hours Saved/Week",
                "improvement": "40% faster response times"
            },
            {
                "title": "Geographic Intelligence",
                "content": "Identify hot markets and opportunity zones with heat map analysis.",
                "metric": "23 Hot Leads",
                "improvement": "3x concentration in downtown"
            }
        ]

        for i, demo_step in enumerate(demo_steps):
            with st.expander(f"🔍 {demo_step['title']}", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(demo_step['content'])

                with col2:
                    st.metric(
                        label="Impact",
                        value=demo_step['metric'],
                        delta=demo_step['improvement']
                    )

        # Auto-advance after showing all demo steps
        if st.button("See This In Action →", key="demo_continue"):
            return True

        return False

    def _check_step_completion(self, step: OnboardingStep) -> bool:
        """Check if the current step has been completed."""
        if step.id == "role_selection":
            return self._render_role_selection()

        if step.id == "executive_value_demo":
            return self._render_executive_value_demo()

        # For other steps, check if enough time has passed or action completed
        if step.action_required:
            return False  # Require explicit action

        # Auto-advance based on duration (for demo purposes)
        if st.session_state.onboarding_start_time:
            elapsed = (datetime.now() - st.session_state.onboarding_start_time).seconds
            return elapsed >= 3  # Reduced for demo

        return False

    def _advance_to_next_step(self, current_step: OnboardingStep):
        """Advance to the next onboarding step."""
        # Mark current step as completed
        if current_step.id not in st.session_state.onboarding_progress.completed_steps:
            st.session_state.onboarding_progress.completed_steps.append(current_step.id)

        # Track analytics
        elapsed_time = 0
        if st.session_state.onboarding_start_time:
            elapsed_time = (datetime.now() - st.session_state.onboarding_start_time).seconds

        self.analytics.track_step_completion(
            st.session_state.onboarding_progress.user_id,
            current_step.id,
            elapsed_time,
            engagement_score=1.0
        )

        # Check for achievements
        self._check_achievements(current_step.id)

        # Move to next step
        if current_step.next_step:
            st.session_state.current_step = current_step.next_step
            st.session_state.onboarding_start_time = datetime.now()
        else:
            self._complete_onboarding()

        st.rerun()

    def _check_achievements(self, completed_step_id: str):
        """Check if any achievements should be unlocked."""
        progress = st.session_state.onboarding_progress

        for achievement in progress.achievements:
            if not achievement.unlocked:
                # Check achievement criteria
                if self._meets_achievement_criteria(achievement, completed_step_id):
                    achievement.unlocked = True
                    achievement.unlocked_at = datetime.now().isoformat()

                    # Show achievement notification
                    st.toast(f"🏆 Achievement Unlocked: {achievement.title}!", icon="🎉")

    def _meets_achievement_criteria(self, achievement: Achievement, completed_step: str) -> bool:
        """Check if achievement criteria are met."""
        criteria = achievement.criteria

        if "step_completed" in criteria:
            return completed_step == criteria["step_completed"]

        if "steps_completed_count" in criteria:
            return len(st.session_state.onboarding_progress.completed_steps) >= criteria["steps_completed_count"]

        return False

    def _complete_onboarding(self):
        """Complete the onboarding process."""
        progress = st.session_state.onboarding_progress

        if progress:
            progress.completion_time = datetime.now().isoformat()
            progress.current_stage = OnboardingStage.COMPLETION
            progress.completion_percentage = 100.0

            # Calculate final engagement score
            total_time = 0
            if st.session_state.onboarding_start_time:
                total_time = (datetime.now() - st.session_state.onboarding_start_time).seconds

            progress.time_spent_seconds = total_time
            progress.engagement_score = self._calculate_engagement_score(progress)

            # Save progress
            self._save_progress(progress)

            # Track completion
            self.analytics.track_step_completion(
                progress.user_id,
                "onboarding_complete",
                total_time,
                progress.engagement_score
            )

        st.session_state.onboarding_active = False
        st.session_state.current_step = None

        # Show completion message
        st.success("🎉 Onboarding completed! Welcome to GHL Real Estate AI!")

        logger.info(f"Completed onboarding for user: {progress.user_id if progress else 'unknown'}")

    def _calculate_engagement_score(self, progress: OnboardingProgress) -> float:
        """Calculate user engagement score during onboarding."""
        # Base score from completion percentage
        completion_score = progress.completion_percentage / 100

        # Bonus for achievements unlocked
        unlocked_achievements = sum(1 for a in progress.achievements if a.unlocked)
        achievement_bonus = min(unlocked_achievements * 0.1, 0.5)

        # Time penalty for rushing through (too fast might indicate low engagement)
        time_factor = 1.0
        if progress.time_spent_seconds < 180:  # Less than 3 minutes
            time_factor = 0.8

        final_score = min((completion_score + achievement_bonus) * time_factor, 1.0)
        return round(final_score, 2)

    def _is_onboarding_complete(self, user_id: str) -> bool:
        """Check if user has already completed onboarding."""
        try:
            progress = self._load_progress(user_id)
            return progress and progress.completion_time is not None
        except Exception:
            return False

    def _save_progress(self, progress: OnboardingProgress):
        """Save onboarding progress to file."""
        try:
            all_progress = {}
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    all_progress = json.load(f)

            all_progress[progress.user_id] = asdict(progress)

            with open(self.progress_file, 'w') as f:
                json.dump(all_progress, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save onboarding progress: {e}")

    def _load_progress(self, user_id: str) -> Optional[OnboardingProgress]:
        """Load onboarding progress from file."""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    all_progress = json.load(f)

                if user_id in all_progress:
                    data = all_progress[user_id]
                    return OnboardingProgress(**data)

        except Exception as e:
            logger.error(f"Failed to load onboarding progress: {e}")

        return None

    def show_quick_help(self, context: str):
        """Show contextual help based on current page/context."""
        help_content = {
            "executive": "💡 **Quick Tip**: Use the revenue waterfall chart to identify which deals contributed most to your growth this month.",
            "leads": "💡 **Quick Tip**: Click on any lead in the map to see detailed scoring and recommendations.",
            "automation": "💡 **Quick Tip**: Start with the 'New Lead Follow-up' template - it's our most popular automation.",
            "sales": "💡 **Quick Tip**: Use the Deal Closer AI when you need help overcoming objections in real-time.",
            "operations": "💡 **Quick Tip**: Check the Quality tab regularly to maintain high standards and identify coaching opportunities."
        }

        content = help_content.get(context, "💡 **Quick Tip**: Explore the navigation menu to discover all platform features.")

        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🔍 Contextual Help")
            st.info(content)

            if st.button("📚 Full Tutorial", key=f"help_tutorial_{context}"):
                self.start_onboarding()

    def get_onboarding_metrics(self) -> Dict[str, Any]:
        """Get onboarding completion metrics for optimization."""
        return self.analytics.get_completion_metrics()


# Helper functions for easy integration
def initialize_onboarding():
    """Initialize onboarding service in session state."""
    if "onboarding_service" not in st.session_state:
        st.session_state.onboarding_service = UserOnboardingService()
    return st.session_state.onboarding_service

def render_onboarding_trigger():
    """Render onboarding trigger button."""
    onboarding = initialize_onboarding()

    # Check if user needs onboarding
    if not st.session_state.get("onboarding_dismissed", False):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🚀 Get Started")

            if st.button("📺 5-Minute Platform Tour", use_container_width=True, key="start_onboarding"):
                onboarding.start_onboarding()
                st.rerun()

            if st.button("❌ Not now", key="dismiss_onboarding"):
                st.session_state.onboarding_dismissed = True
                st.rerun()

def render_contextual_help(context: str):
    """Render contextual help for current location."""
    onboarding = initialize_onboarding()
    onboarding.show_quick_help(context)

def handle_onboarding_flow():
    """Handle active onboarding flow."""
    onboarding = initialize_onboarding()

    if st.session_state.get("onboarding_active", False):
        onboarding.render_onboarding_step()


# Export main components
__all__ = [
    "UserOnboardingService",
    "UserRole",
    "OnboardingStage",
    "initialize_onboarding",
    "render_onboarding_trigger",
    "render_contextual_help",
    "handle_onboarding_flow"
]