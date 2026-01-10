"""
Agent Goal Setting & Achievement Tracking Service

A comprehensive goal management system for real estate agents that provides:
- SMART goal creation and validation
- Performance milestone monitoring and analytics
- AI-powered goal recommendations and insights
- Achievement recognition and reward systems
- Team and individual goal alignment tracking
- Progress visualization and reporting

Created: January 2026
Author: GHL Real Estate AI Platform
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import json

# Configure logging
logger = logging.getLogger(__name__)

class GoalType(Enum):
    """Types of goals agents can set."""
    REVENUE = "revenue"
    LEADS = "leads"
    CONVERSIONS = "conversions"
    LISTINGS = "listings"
    CLOSINGS = "closings"
    CLIENT_SATISFACTION = "client_satisfaction"
    SKILLS_DEVELOPMENT = "skills_development"
    TEAM_COLLABORATION = "team_collaboration"
    MARKET_EXPANSION = "market_expansion"
    CUSTOM = "custom"

class GoalStatus(Enum):
    """Current status of a goal."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    ACHIEVED = "achieved"
    EXCEEDED = "exceeded"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class GoalPriority(Enum):
    """Priority level of goals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TimeFrame(Enum):
    """Time frames for goals."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class AchievementType(Enum):
    """Types of achievements and recognitions."""
    GOAL_COMPLETED = "goal_completed"
    MILESTONE_REACHED = "milestone_reached"
    STREAK_ACHIEVED = "streak_achieved"
    PERFORMANCE_EXCELLENCE = "performance_excellence"
    TEAM_CONTRIBUTION = "team_contribution"
    SKILL_MASTERY = "skill_mastery"
    CLIENT_RECOGNITION = "client_recognition"

@dataclass
class SMARTCriteria:
    """SMART goal criteria validation."""
    specific: bool = False
    measurable: bool = False
    achievable: bool = False
    relevant: bool = False
    time_bound: bool = False
    score: float = 0.0
    feedback: List[str] = field(default_factory=list)

@dataclass
class GoalMilestone:
    """Represents a milestone within a goal."""
    milestone_id: str
    title: str
    description: str
    target_value: float
    target_date: datetime
    status: GoalStatus
    completion_date: Optional[datetime] = None
    actual_value: Optional[float] = None
    notes: str = ""

    def calculate_progress(self) -> float:
        """Calculate milestone progress percentage."""
        if self.actual_value is None:
            return 0.0
        return min(100.0, (self.actual_value / self.target_value) * 100)

    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        return datetime.now() > self.target_date and self.status not in [GoalStatus.ACHIEVED, GoalStatus.EXCEEDED]

@dataclass
class Goal:
    """Represents an agent's goal with SMART criteria."""
    goal_id: str
    agent_id: str
    title: str
    description: str
    goal_type: GoalType
    priority: GoalPriority
    time_frame: TimeFrame
    target_value: float
    target_date: datetime
    status: GoalStatus
    created_date: datetime
    updated_date: datetime
    current_value: float = 0.0
    milestones: List[GoalMilestone] = field(default_factory=list)
    smart_criteria: Optional[SMARTCriteria] = None
    category: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    parent_goal_id: Optional[str] = None  # For sub-goals
    team_goal: bool = False

    def calculate_progress(self) -> float:
        """Calculate overall goal progress percentage."""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def days_remaining(self) -> int:
        """Calculate days remaining to achieve goal."""
        delta = self.target_date - datetime.now()
        return max(0, delta.days)

    def is_overdue(self) -> bool:
        """Check if goal is overdue."""
        return datetime.now() > self.target_date and self.status not in [GoalStatus.ACHIEVED, GoalStatus.EXCEEDED]

    def completion_rate(self) -> float:
        """Calculate completion rate based on time elapsed."""
        total_time = (self.target_date - self.created_date).days
        elapsed_time = (datetime.now() - self.created_date).days
        return min(100.0, (elapsed_time / total_time) * 100) if total_time > 0 else 0.0

@dataclass
class Achievement:
    """Represents an achievement or recognition."""
    achievement_id: str
    agent_id: str
    title: str
    description: str
    achievement_type: AchievementType
    earned_date: datetime
    goal_id: Optional[str] = None
    value: Optional[float] = None
    badge_icon: str = "🏆"
    points_awarded: int = 0
    public: bool = True

@dataclass
class GoalRecommendation:
    """AI-powered goal recommendation."""
    recommendation_id: str
    agent_id: str
    title: str
    description: str
    goal_type: GoalType
    suggested_target: float
    time_frame: TimeFrame
    reasoning: str
    confidence_score: float
    priority_score: float
    created_date: datetime
    accepted: Optional[bool] = None

@dataclass
class TeamGoalAlignment:
    """Tracks alignment between individual and team goals."""
    alignment_id: str
    agent_id: str
    individual_goal_id: str
    team_goal_id: str
    alignment_percentage: float
    contribution_weight: float
    synergy_score: float

class AgentGoalTrackingService:
    """
    Comprehensive goal setting and achievement tracking service for real estate agents.

    Features:
    - SMART goal creation and validation
    - Performance milestone tracking
    - AI-powered recommendations
    - Achievement recognition system
    - Team goal alignment
    """

    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.achievements: Dict[str, Achievement] = {}
        self.recommendations: Dict[str, GoalRecommendation] = {}
        self.team_alignments: Dict[str, TeamGoalAlignment] = {}
        self.performance_data: Dict[str, Any] = {}

        # Initialize with demo data
        asyncio.create_task(self._initialize_demo_data())

    async def _initialize_demo_data(self) -> None:
        """Initialize service with demo goals and achievements."""
        try:
            # Create demo goals for different agents
            await self._create_demo_goals()
            await self._create_demo_achievements()
            await self._create_demo_recommendations()

            logger.info("Goal tracking service initialized with demo data")

        except Exception as e:
            logger.error(f"Error initializing demo data: {e}")

    async def _create_demo_goals(self) -> None:
        """Create demo goals for testing."""
        demo_goals = [
            {
                "goal_id": "goal_001",
                "agent_id": "agent_001",
                "title": "Q1 Revenue Target",
                "description": "Achieve $500,000 in total sales revenue for Q1 2026",
                "goal_type": GoalType.REVENUE,
                "priority": GoalPriority.HIGH,
                "time_frame": TimeFrame.QUARTERLY,
                "target_value": 500000.0,
                "target_date": datetime(2026, 3, 31),
                "current_value": 187500.0,
                "category": "Financial Performance"
            },
            {
                "goal_id": "goal_002",
                "agent_id": "agent_001",
                "title": "Monthly Lead Generation",
                "description": "Generate 50 qualified leads per month",
                "goal_type": GoalType.LEADS,
                "priority": GoalPriority.MEDIUM,
                "time_frame": TimeFrame.MONTHLY,
                "target_value": 50.0,
                "target_date": datetime(2026, 1, 31),
                "current_value": 32.0,
                "category": "Lead Generation"
            },
            {
                "goal_id": "goal_003",
                "agent_id": "agent_002",
                "title": "Client Satisfaction Excellence",
                "description": "Maintain 95%+ client satisfaction rating",
                "goal_type": GoalType.CLIENT_SATISFACTION,
                "priority": GoalPriority.HIGH,
                "time_frame": TimeFrame.YEARLY,
                "target_value": 95.0,
                "target_date": datetime(2026, 12, 31),
                "current_value": 92.5,
                "category": "Service Quality"
            }
        ]

        for goal_data in demo_goals:
            goal = Goal(
                **goal_data,
                status=self._determine_goal_status(goal_data["current_value"], goal_data["target_value"]),
                created_date=datetime.now() - timedelta(days=30),
                updated_date=datetime.now(),
                smart_criteria=await self._validate_smart_criteria(goal_data["title"], goal_data["description"])
            )

            # Add milestones for some goals
            if goal.goal_type == GoalType.REVENUE:
                goal.milestones = [
                    GoalMilestone(
                        milestone_id="mil_001",
                        title="Month 1 Target",
                        description="Achieve $166,667 in sales",
                        target_value=166667.0,
                        target_date=datetime(2026, 1, 31),
                        status=GoalStatus.ACHIEVED,
                        actual_value=175000.0,
                        completion_date=datetime(2026, 1, 30)
                    ),
                    GoalMilestone(
                        milestone_id="mil_002",
                        title="Month 2 Target",
                        description="Achieve cumulative $333,333 in sales",
                        target_value=333333.0,
                        target_date=datetime(2026, 2, 28),
                        status=GoalStatus.ON_TRACK,
                        actual_value=187500.0
                    )
                ]

            self.goals[goal.goal_id] = goal

    async def _create_demo_achievements(self) -> None:
        """Create demo achievements for testing."""
        demo_achievements = [
            {
                "achievement_id": "ach_001",
                "agent_id": "agent_001",
                "title": "First Quarter Milestone",
                "description": "Reached 37.5% of Q1 revenue target ahead of schedule",
                "achievement_type": AchievementType.MILESTONE_REACHED,
                "goal_id": "goal_001",
                "value": 187500.0,
                "badge_icon": "📈",
                "points_awarded": 100
            },
            {
                "achievement_id": "ach_002",
                "agent_id": "agent_002",
                "title": "Client Service Star",
                "description": "Maintained 92.5% client satisfaction rating",
                "achievement_type": AchievementType.PERFORMANCE_EXCELLENCE,
                "goal_id": "goal_003",
                "value": 92.5,
                "badge_icon": "⭐",
                "points_awarded": 75
            }
        ]

        for ach_data in demo_achievements:
            achievement = Achievement(
                **ach_data,
                earned_date=datetime.now() - timedelta(days=5)
            )
            self.achievements[achievement.achievement_id] = achievement

    async def _create_demo_recommendations(self) -> None:
        """Create demo goal recommendations."""
        recommendations = [
            {
                "recommendation_id": "rec_001",
                "agent_id": "agent_001",
                "title": "Increase Conversion Focus",
                "description": "Based on your lead generation success, consider setting a conversion rate improvement goal",
                "goal_type": GoalType.CONVERSIONS,
                "suggested_target": 25.0,
                "time_frame": TimeFrame.MONTHLY,
                "reasoning": "Your lead generation is 64% to target, but conversion tracking would optimize ROI",
                "confidence_score": 0.85,
                "priority_score": 0.78
            }
        ]

        for rec_data in recommendations:
            recommendation = GoalRecommendation(
                **rec_data,
                created_date=datetime.now() - timedelta(days=2)
            )
            self.recommendations[recommendation.recommendation_id] = recommendation

    def _determine_goal_status(self, current_value: float, target_value: float) -> GoalStatus:
        """Determine goal status based on progress."""
        if target_value == 0:
            return GoalStatus.ACTIVE

        progress = (current_value / target_value) * 100

        if progress >= 100:
            return GoalStatus.ACHIEVED
        elif progress >= 90:
            return GoalStatus.EXCEEDED if progress > 100 else GoalStatus.ON_TRACK
        elif progress >= 70:
            return GoalStatus.ON_TRACK
        elif progress >= 50:
            return GoalStatus.AT_RISK
        else:
            return GoalStatus.BEHIND

    async def _validate_smart_criteria(self, title: str, description: str) -> SMARTCriteria:
        """Validate and score SMART criteria for a goal."""
        criteria = SMARTCriteria()
        feedback = []

        # Check Specific
        if len(title) > 10 and len(description) > 20:
            criteria.specific = True
        else:
            feedback.append("Goal needs more specific details")

        # Check Measurable (look for numbers)
        import re
        if re.search(r'\d+', description) or re.search(r'\d+', title):
            criteria.measurable = True
        else:
            feedback.append("Goal should include measurable metrics")

        # Check Achievable (assume reasonable for demo)
        criteria.achievable = True

        # Check Relevant (assume business-relevant)
        criteria.relevant = True

        # Check Time-bound (look for dates/timeframes)
        time_keywords = ['quarter', 'month', 'year', 'week', 'daily', 'Q1', 'Q2', 'Q3', 'Q4']
        if any(keyword.lower() in description.lower() for keyword in time_keywords):
            criteria.time_bound = True
        else:
            feedback.append("Goal should specify clear deadline")

        # Calculate overall score
        criteria.score = sum([
            criteria.specific, criteria.measurable, criteria.achievable,
            criteria.relevant, criteria.time_bound
        ]) * 20.0  # Out of 100

        criteria.feedback = feedback
        return criteria

    # Core Goal Management Methods

    async def create_goal(
        self,
        agent_id: str,
        title: str,
        description: str,
        goal_type: GoalType,
        target_value: float,
        target_date: datetime,
        priority: GoalPriority = GoalPriority.MEDIUM,
        time_frame: TimeFrame = TimeFrame.MONTHLY,
        category: str = "",
        tags: List[str] = None,
        parent_goal_id: Optional[str] = None
    ) -> Goal:
        """Create a new goal for an agent."""
        goal_id = f"goal_{len(self.goals) + 1:03d}"

        # Validate SMART criteria
        smart_criteria = await self._validate_smart_criteria(title, description)

        goal = Goal(
            goal_id=goal_id,
            agent_id=agent_id,
            title=title,
            description=description,
            goal_type=goal_type,
            priority=priority,
            time_frame=time_frame,
            target_value=target_value,
            target_date=target_date,
            status=GoalStatus.ACTIVE,
            created_date=datetime.now(),
            updated_date=datetime.now(),
            smart_criteria=smart_criteria,
            category=category,
            tags=tags or [],
            parent_goal_id=parent_goal_id
        )

        self.goals[goal_id] = goal
        logger.info(f"Created goal {goal_id} for agent {agent_id}: {title}")

        return goal

    async def update_goal_progress(
        self,
        goal_id: str,
        current_value: float,
        notes: str = ""
    ) -> bool:
        """Update progress on a goal."""
        if goal_id not in self.goals:
            logger.warning(f"Goal {goal_id} not found")
            return False

        goal = self.goals[goal_id]
        old_value = goal.current_value
        goal.current_value = current_value
        goal.updated_date = datetime.now()

        if notes:
            goal.notes += f"\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {notes}"

        # Update status based on new progress
        goal.status = self._determine_goal_status(current_value, goal.target_value)

        # Check for milestone achievements
        await self._check_milestone_achievements(goal)

        # Check for goal completion
        if goal.status in [GoalStatus.ACHIEVED, GoalStatus.EXCEEDED]:
            await self._award_goal_completion(goal)

        logger.info(f"Updated goal {goal_id} progress: {old_value} -> {current_value}")
        return True

    async def _check_milestone_achievements(self, goal: Goal) -> None:
        """Check and award milestone achievements."""
        for milestone in goal.milestones:
            if (milestone.status not in [GoalStatus.ACHIEVED, GoalStatus.EXCEEDED] and
                goal.current_value >= milestone.target_value):

                milestone.status = GoalStatus.ACHIEVED
                milestone.completion_date = datetime.now()
                milestone.actual_value = goal.current_value

                # Award achievement
                await self._award_milestone_achievement(goal, milestone)

    async def _award_goal_completion(self, goal: Goal) -> None:
        """Award achievement for goal completion."""
        achievement = Achievement(
            achievement_id=f"ach_{len(self.achievements) + 1:03d}",
            agent_id=goal.agent_id,
            title=f"Goal Achieved: {goal.title}",
            description=f"Successfully completed goal with {goal.calculate_progress():.1f}% achievement",
            achievement_type=AchievementType.GOAL_COMPLETED,
            earned_date=datetime.now(),
            goal_id=goal.goal_id,
            value=goal.current_value,
            badge_icon="🎯",
            points_awarded=150 if goal.priority == GoalPriority.HIGH else 100
        )

        self.achievements[achievement.achievement_id] = achievement
        logger.info(f"Awarded goal completion achievement to {goal.agent_id}")

    async def _award_milestone_achievement(self, goal: Goal, milestone: GoalMilestone) -> None:
        """Award achievement for milestone completion."""
        achievement = Achievement(
            achievement_id=f"ach_{len(self.achievements) + 1:03d}",
            agent_id=goal.agent_id,
            title=f"Milestone: {milestone.title}",
            description=f"Reached milestone in goal: {goal.title}",
            achievement_type=AchievementType.MILESTONE_REACHED,
            earned_date=datetime.now(),
            goal_id=goal.goal_id,
            value=milestone.actual_value,
            badge_icon="🏁",
            points_awarded=50
        )

        self.achievements[achievement.achievement_id] = achievement
        logger.info(f"Awarded milestone achievement to {goal.agent_id}")

    # Goal Analysis & Recommendations

    async def generate_goal_recommendations(
        self,
        agent_id: str,
        max_recommendations: int = 5
    ) -> List[GoalRecommendation]:
        """Generate AI-powered goal recommendations for an agent."""
        agent_goals = [g for g in self.goals.values() if g.agent_id == agent_id]

        recommendations = []

        # Analyze current goals and performance
        performance_analysis = await self._analyze_agent_performance(agent_id)

        # Recommendation 1: Based on current progress
        if agent_goals:
            avg_progress = sum(g.calculate_progress() for g in agent_goals) / len(agent_goals)

            if avg_progress > 80:
                # Suggest stretch goals
                recommendations.append(GoalRecommendation(
                    recommendation_id=f"rec_{len(self.recommendations) + 1:03d}",
                    agent_id=agent_id,
                    title="Stretch Goal Opportunity",
                    description="Your current performance suggests you could handle more ambitious targets",
                    goal_type=GoalType.REVENUE,
                    suggested_target=performance_analysis.get("avg_monthly_revenue", 50000) * 1.25,
                    time_frame=TimeFrame.QUARTERLY,
                    reasoning="High achievement rate on current goals indicates capacity for growth",
                    confidence_score=0.82,
                    priority_score=0.75,
                    created_date=datetime.now()
                ))

        # Recommendation 2: Skills development
        if not any(g.goal_type == GoalType.SKILLS_DEVELOPMENT for g in agent_goals):
            recommendations.append(GoalRecommendation(
                recommendation_id=f"rec_{len(self.recommendations) + 1:03d}",
                agent_id=agent_id,
                title="Professional Development Focus",
                description="Consider setting learning goals to enhance your expertise",
                goal_type=GoalType.SKILLS_DEVELOPMENT,
                suggested_target=4.0,  # 4 new skills
                time_frame=TimeFrame.QUARTERLY,
                reasoning="No current skill development goals detected",
                confidence_score=0.90,
                priority_score=0.65,
                created_date=datetime.now()
            ))

        # Recommendation 3: Team collaboration
        if not any(g.goal_type == GoalType.TEAM_COLLABORATION for g in agent_goals):
            recommendations.append(GoalRecommendation(
                recommendation_id=f"rec_{len(self.recommendations) + 1:03d}",
                agent_id=agent_id,
                title="Team Collaboration Goal",
                description="Enhance team performance through collaboration initiatives",
                goal_type=GoalType.TEAM_COLLABORATION,
                suggested_target=10.0,  # 10 collaboration activities
                time_frame=TimeFrame.MONTHLY,
                reasoning="Team collaboration can improve overall performance and learning",
                confidence_score=0.75,
                priority_score=0.60,
                created_date=datetime.now()
            ))

        # Store recommendations
        for rec in recommendations[:max_recommendations]:
            self.recommendations[rec.recommendation_id] = rec

        return recommendations[:max_recommendations]

    async def _analyze_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Analyze agent performance for recommendations."""
        agent_goals = [g for g in self.goals.values() if g.agent_id == agent_id]

        if not agent_goals:
            return {"avg_monthly_revenue": 50000, "goal_completion_rate": 0}

        # Calculate performance metrics
        total_progress = sum(g.calculate_progress() for g in agent_goals)
        avg_progress = total_progress / len(agent_goals)

        revenue_goals = [g for g in agent_goals if g.goal_type == GoalType.REVENUE]
        avg_revenue = sum(g.current_value for g in revenue_goals) / max(len(revenue_goals), 1)

        return {
            "avg_progress": avg_progress,
            "avg_monthly_revenue": avg_revenue,
            "goal_completion_rate": avg_progress / 100,
            "active_goals": len(agent_goals),
            "revenue_focus": len(revenue_goals) / len(agent_goals)
        }

    # Query Methods

    async def get_agent_goals(
        self,
        agent_id: str,
        status_filter: Optional[GoalStatus] = None,
        goal_type_filter: Optional[GoalType] = None
    ) -> List[Goal]:
        """Get all goals for a specific agent with optional filters."""
        goals = [g for g in self.goals.values() if g.agent_id == agent_id]

        if status_filter:
            goals = [g for g in goals if g.status == status_filter]

        if goal_type_filter:
            goals = [g for g in goals if g.goal_type == goal_type_filter]

        return sorted(goals, key=lambda x: x.created_date, reverse=True)

    async def get_agent_achievements(self, agent_id: str) -> List[Achievement]:
        """Get all achievements for a specific agent."""
        achievements = [a for a in self.achievements.values() if a.agent_id == agent_id]
        return sorted(achievements, key=lambda x: x.earned_date, reverse=True)

    async def get_goal_analytics(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive goal analytics for an agent."""
        goals = await self.get_agent_goals(agent_id)
        achievements = await self.get_agent_achievements(agent_id)

        if not goals:
            return {"total_goals": 0, "message": "No goals found"}

        # Calculate analytics
        total_progress = sum(g.calculate_progress() for g in goals)
        avg_progress = total_progress / len(goals)

        status_counts = {}
        type_counts = {}

        for goal in goals:
            status_counts[goal.status.value] = status_counts.get(goal.status.value, 0) + 1
            type_counts[goal.goal_type.value] = type_counts.get(goal.goal_type.value, 0) + 1

        overdue_goals = [g for g in goals if g.is_overdue()]
        on_track_goals = [g for g in goals if g.status == GoalStatus.ON_TRACK]

        return {
            "total_goals": len(goals),
            "avg_progress": round(avg_progress, 2),
            "total_achievements": len(achievements),
            "total_points": sum(a.points_awarded for a in achievements),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "overdue_count": len(overdue_goals),
            "on_track_count": len(on_track_goals),
            "completion_rate": len([g for g in goals if g.status in [GoalStatus.ACHIEVED, GoalStatus.EXCEEDED]]) / len(goals) * 100
        }

    async def get_team_goal_alignment(self, agent_id: str) -> List[TeamGoalAlignment]:
        """Get team goal alignment data for an agent."""
        return [a for a in self.team_alignments.values() if a.agent_id == agent_id]

    async def get_goal_recommendations(self, agent_id: str) -> List[GoalRecommendation]:
        """Get pending goal recommendations for an agent."""
        agent_recs = [r for r in self.recommendations.values() if r.agent_id == agent_id and r.accepted is None]
        return sorted(agent_recs, key=lambda x: x.priority_score, reverse=True)

# Global service instance
goal_tracking_service = AgentGoalTrackingService()

# Helper functions for easy access
async def create_agent_goal(
    agent_id: str,
    title: str,
    description: str,
    goal_type: GoalType,
    target_value: float,
    target_date: datetime,
    priority: GoalPriority = GoalPriority.MEDIUM
) -> Goal:
    """Helper function to create a goal."""
    return await goal_tracking_service.create_goal(
        agent_id, title, description, goal_type, target_value, target_date, priority
    )

async def update_goal_progress(goal_id: str, current_value: float, notes: str = "") -> bool:
    """Helper function to update goal progress."""
    return await goal_tracking_service.update_goal_progress(goal_id, current_value, notes)

async def get_agent_goal_analytics(agent_id: str) -> Dict[str, Any]:
    """Helper function to get goal analytics."""
    return await goal_tracking_service.get_goal_analytics(agent_id)

async def generate_goal_recommendations(agent_id: str) -> List[GoalRecommendation]:
    """Helper function to generate recommendations."""
    return await goal_tracking_service.generate_goal_recommendations(agent_id)

if __name__ == "__main__":
    # Test the service
    async def test_service():
        service = AgentGoalTrackingService()
        await asyncio.sleep(1)  # Wait for demo data

        # Test goal analytics
        analytics = await service.get_goal_analytics("agent_001")
        print(f"Agent 001 Analytics: {analytics}")

        # Test recommendations
        recommendations = await service.generate_goal_recommendations("agent_001")
        print(f"Generated {len(recommendations)} recommendations")

        # Test goal creation
        new_goal = await service.create_goal(
            agent_id="agent_test",
            title="Test Goal",
            description="A test goal for validation",
            goal_type=GoalType.LEADS,
            target_value=100.0,
            target_date=datetime.now() + timedelta(days=30)
        )
        print(f"Created goal: {new_goal.title}")

    asyncio.run(test_service())