"""
Claude Agent Performance Analytics Engine (Advanced Feature #5)

Advanced performance analytics system that tracks agent effectiveness, coaching impact,
and improvement opportunities using Claude AI analysis for comprehensive performance
optimization and coaching recommendations.

Features:
- Real-time agent performance monitoring
- Coaching effectiveness measurement and optimization
- Behavioral pattern analysis for performance improvement
- Comparative performance benchmarking
- Personalized coaching recommendations
- Skills gap identification and training plans
- Performance prediction and trend analysis
- Team performance optimization insights
"""

import asyncio
import json
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from anthropic import AsyncAnthropic

from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.claude_predictive_analytics_engine import claude_predictive_analytics
from ghl_real_estate_ai.ghl_utils.config import settings

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """Types of performance metrics to track."""
    CONVERSION_RATE = "conversion_rate"
    RESPONSE_TIME = "response_time"
    LEAD_QUALITY_SCORE = "lead_quality_score"
    CLIENT_SATISFACTION = "client_satisfaction"
    SALES_VOLUME = "sales_volume"
    TRANSACTION_COUNT = "transaction_count"
    COACHING_RECEPTIVITY = "coaching_receptivity"
    SKILL_IMPROVEMENT_RATE = "skill_improvement_rate"
    LEAD_NURTURING_EFFECTIVENESS = "lead_nurturing_effectiveness"
    OBJECTION_HANDLING_SUCCESS = "objection_handling_success"


class CoachingFocusArea(Enum):
    """Areas of focus for agent coaching."""
    LEAD_QUALIFICATION = "lead_qualification"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING_TECHNIQUES = "closing_techniques"
    COMMUNICATION_SKILLS = "communication_skills"
    TIME_MANAGEMENT = "time_management"
    MARKET_KNOWLEDGE = "market_knowledge"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    CLIENT_RELATIONSHIP = "client_relationship"
    NEGOTIATION_SKILLS = "negotiation_skills"
    PRESENTATION_SKILLS = "presentation_skills"


class PerformanceLevel(Enum):
    """Performance level classifications."""
    EXCEPTIONAL = "exceptional"  # Top 10%
    HIGH_PERFORMER = "high_performer"  # Top 25%
    SOLID_PERFORMER = "solid_performer"  # Average
    NEEDS_IMPROVEMENT = "needs_improvement"  # Below average
    CRITICAL_ATTENTION = "critical_attention"  # Bottom 10%


class CoachingEffectiveness(Enum):
    """Coaching effectiveness levels."""
    HIGHLY_EFFECTIVE = "highly_effective"
    MODERATELY_EFFECTIVE = "moderately_effective"
    MINIMALLY_EFFECTIVE = "minimally_effective"
    INEFFECTIVE = "ineffective"


@dataclass
class PerformanceDataPoint:
    """Single performance data point."""
    agent_id: str
    metric: PerformanceMetric
    value: float
    benchmark_value: Optional[float]
    context: Dict[str, Any]
    coaching_session_id: Optional[str]
    timestamp: datetime


@dataclass
class CoachingSession:
    """Coaching session record."""
    session_id: str
    agent_id: str
    coach_id: str
    focus_areas: List[CoachingFocusArea]
    session_type: str
    duration_minutes: int
    topics_covered: List[str]
    action_items: List[str]
    agent_feedback: Dict[str, Any]
    pre_session_metrics: Dict[str, float]
    post_session_metrics: Dict[str, float]
    effectiveness_score: Optional[float]
    follow_up_required: bool
    session_date: datetime


@dataclass
class AgentPerformanceProfile:
    """Comprehensive agent performance profile."""
    agent_id: str
    agent_name: str
    hire_date: datetime
    team_id: Optional[str]
    performance_level: PerformanceLevel
    current_metrics: Dict[PerformanceMetric, float]
    performance_trends: Dict[PerformanceMetric, List[float]]
    strengths: List[str]
    improvement_areas: List[CoachingFocusArea]
    coaching_history: List[str]  # Session IDs
    skill_assessments: Dict[str, float]
    career_progression: List[Dict[str, Any]]
    performance_goals: Dict[str, Any]
    coaching_preferences: Dict[str, Any]
    last_updated: datetime


@dataclass
class PerformanceAnalysis:
    """Results of performance analysis."""
    analysis_id: str
    agent_id: str
    analysis_period: str
    performance_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    comparative_analysis: Dict[str, Any]
    coaching_effectiveness: Dict[str, Any]
    improvement_recommendations: List[str]
    coaching_plan: Dict[str, Any]
    predicted_performance: Dict[str, float]
    risk_indicators: List[str]
    opportunity_areas: List[str]
    confidence_score: float
    analyzed_at: datetime


@dataclass
class TeamPerformanceInsights:
    """Team-level performance insights."""
    team_id: str
    team_name: str
    analysis_period: str
    team_metrics: Dict[str, float]
    individual_performances: Dict[str, Dict[str, float]]
    performance_distribution: Dict[PerformanceLevel, int]
    coaching_effectiveness: Dict[str, float]
    skill_gap_analysis: Dict[str, List[str]]
    team_strengths: List[str]
    team_challenges: List[str]
    resource_optimization: Dict[str, Any]
    performance_predictions: Dict[str, float]
    recommended_interventions: List[str]
    generated_at: datetime


class ClaudeAgentPerformanceAnalytics:
    """
    Advanced agent performance analytics system using Claude AI for comprehensive
    performance monitoring, coaching effectiveness analysis, and improvement optimization.
    """

    def __init__(self, location_id: str = "default"):
        """Initialize agent performance analytics engine."""
        self.location_id = location_id
        self.data_dir = Path(__file__).parent.parent / "data" / "performance" / location_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File storage
        self.performance_data_file = self.data_dir / "performance_data.json"
        self.coaching_sessions_file = self.data_dir / "coaching_sessions.json"
        self.agent_profiles_file = self.data_dir / "agent_profiles.json"
        self.analyses_file = self.data_dir / "performance_analyses.json"
        self.benchmarks_file = self.data_dir / "benchmarks.json"

        # Initialize services
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.claude_analyzer = ClaudeSemanticAnalyzer()
        self.predictive_engine = claude_predictive_analytics

        # Load data
        self.performance_data = self._load_performance_data()
        self.coaching_sessions = self._load_coaching_sessions()
        self.agent_profiles = self._load_agent_profiles()
        self.analysis_history = self._load_analysis_history()
        self.benchmarks = self._load_benchmarks()

        # Runtime state
        self.real_time_metrics = defaultdict(lambda: defaultdict(deque))
        self.coaching_impact_tracking = defaultdict(dict)
        self.performance_alerts = deque()

        # Initialize benchmarks and standards
        self._initialize_performance_benchmarks()

        logger.info(f"Claude Agent Performance Analytics initialized for location {location_id}")

    def _load_performance_data(self) -> List[PerformanceDataPoint]:
        """Load performance data from file."""
        if self.performance_data_file.exists():
            try:
                with open(self.performance_data_file, 'r') as f:
                    data = json.load(f)
                    performance_points = []
                    for point_data in data:
                        performance_points.append(self._dict_to_performance_data_point(point_data))
                    return performance_points
            except Exception as e:
                logger.error(f"Error loading performance data: {e}")
        return []

    def _save_performance_data(self) -> None:
        """Save performance data to file."""
        try:
            # Keep only last 1000 data points per agent
            agent_data_counts = defaultdict(int)
            filtered_data = []

            for point in reversed(self.performance_data):
                if agent_data_counts[point.agent_id] < 1000:
                    filtered_data.append(point)
                    agent_data_counts[point.agent_id] += 1

            data = [asdict(point) for point in reversed(filtered_data)]
            with open(self.performance_data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")

    def _load_coaching_sessions(self) -> Dict[str, CoachingSession]:
        """Load coaching sessions from file."""
        if self.coaching_sessions_file.exists():
            try:
                with open(self.coaching_sessions_file, 'r') as f:
                    data = json.load(f)
                    sessions = {}
                    for session_id, session_data in data.items():
                        sessions[session_id] = self._dict_to_coaching_session(session_data)
                    return sessions
            except Exception as e:
                logger.error(f"Error loading coaching sessions: {e}")
        return {}

    def _save_coaching_sessions(self) -> None:
        """Save coaching sessions to file."""
        try:
            sessions_data = {}
            for session_id, session in self.coaching_sessions.items():
                sessions_data[session_id] = asdict(session)

            with open(self.coaching_sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving coaching sessions: {e}")

    def _load_agent_profiles(self) -> Dict[str, AgentPerformanceProfile]:
        """Load agent profiles from file."""
        if self.agent_profiles_file.exists():
            try:
                with open(self.agent_profiles_file, 'r') as f:
                    data = json.load(f)
                    profiles = {}
                    for agent_id, profile_data in data.items():
                        profiles[agent_id] = self._dict_to_agent_profile(profile_data)
                    return profiles
            except Exception as e:
                logger.error(f"Error loading agent profiles: {e}")
        return {}

    def _save_agent_profiles(self) -> None:
        """Save agent profiles to file."""
        try:
            profiles_data = {}
            for agent_id, profile in self.agent_profiles.items():
                profiles_data[agent_id] = asdict(profile)

            with open(self.agent_profiles_file, 'w') as f:
                json.dump(profiles_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving agent profiles: {e}")

    def _load_analysis_history(self) -> List[PerformanceAnalysis]:
        """Load analysis history from file."""
        if self.analyses_file.exists():
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                    analyses = []
                    for analysis_data in data:
                        analyses.append(self._dict_to_performance_analysis(analysis_data))
                    return analyses
            except Exception as e:
                logger.error(f"Error loading analysis history: {e}")
        return []

    def _save_analysis_history(self) -> None:
        """Save analysis history to file."""
        try:
            # Keep only last 100 analyses
            recent_analyses = self.analysis_history[-100:]
            analyses_data = [asdict(analysis) for analysis in recent_analyses]

            with open(self.analyses_file, 'w') as f:
                json.dump(analyses_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving analysis history: {e}")

    def _load_benchmarks(self) -> Dict[str, Any]:
        """Load performance benchmarks."""
        if self.benchmarks_file.exists():
            try:
                with open(self.benchmarks_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading benchmarks: {e}")
        return {}

    def _save_benchmarks(self) -> None:
        """Save performance benchmarks."""
        try:
            with open(self.benchmarks_file, 'w') as f:
                json.dump(self.benchmarks, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving benchmarks: {e}")

    def _initialize_performance_benchmarks(self) -> None:
        """Initialize default performance benchmarks."""
        if not self.benchmarks:
            self.benchmarks = {
                "industry_standards": {
                    PerformanceMetric.CONVERSION_RATE.value: {
                        "excellent": 0.25, "good": 0.18, "average": 0.12, "needs_improvement": 0.08
                    },
                    PerformanceMetric.RESPONSE_TIME.value: {
                        "excellent": 15, "good": 30, "average": 60, "needs_improvement": 120  # minutes
                    },
                    PerformanceMetric.CLIENT_SATISFACTION.value: {
                        "excellent": 4.5, "good": 4.0, "average": 3.5, "needs_improvement": 3.0
                    },
                    PerformanceMetric.LEAD_QUALITY_SCORE.value: {
                        "excellent": 85, "good": 75, "average": 65, "needs_improvement": 55
                    }
                },
                "coaching_effectiveness_thresholds": {
                    "highly_effective": 0.8,
                    "moderately_effective": 0.6,
                    "minimally_effective": 0.4,
                    "ineffective": 0.2
                },
                "performance_level_thresholds": {
                    "exceptional": 90,
                    "high_performer": 75,
                    "solid_performer": 60,
                    "needs_improvement": 40,
                    "critical_attention": 25
                }
            }
            self._save_benchmarks()

    async def analyze_agent_performance(
        self,
        agent_id: str,
        analysis_period: str = "30_days",
        include_coaching_analysis: bool = True,
        include_predictions: bool = True
    ) -> PerformanceAnalysis:
        """
        Perform comprehensive performance analysis for an agent.

        Args:
            agent_id: Agent identifier
            analysis_period: Period for analysis (7_days, 30_days, 90_days, etc.)
            include_coaching_analysis: Include coaching effectiveness analysis
            include_predictions: Include performance predictions

        Returns:
            PerformanceAnalysis with comprehensive insights and recommendations
        """
        try:
            analysis_start = datetime.now()
            analysis_id = f"perf_analysis_{agent_id}_{int(analysis_start.timestamp())}"

            logger.info(f"Starting performance analysis {analysis_id} for agent {agent_id}")

            # Get agent profile
            agent_profile = self.agent_profiles.get(agent_id)
            if not agent_profile:
                raise ValueError(f"Agent profile for {agent_id} not found")

            # Gather performance data for analysis period
            performance_data = await self._gather_agent_performance_data(
                agent_id, analysis_period
            )

            # Perform trend analysis
            trend_analysis = await self._analyze_performance_trends(
                agent_id, performance_data, analysis_period
            )

            # Perform comparative analysis
            comparative_analysis = await self._perform_comparative_analysis(
                agent_id, performance_data, agent_profile
            )

            # Analyze coaching effectiveness if requested
            coaching_effectiveness = {}
            if include_coaching_analysis:
                coaching_effectiveness = await self._analyze_coaching_effectiveness(
                    agent_id, analysis_period
                )

            # Create comprehensive analysis prompt for Claude
            analysis_prompt = await self._create_performance_analysis_prompt(
                agent_id, agent_profile, performance_data, trend_analysis,
                comparative_analysis, coaching_effectiveness
            )

            # Get Claude's performance analysis
            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1200,
                temperature=0.3,
                system="""You are an expert performance analytics specialist for real estate agents.
                Analyze performance data, trends, and coaching effectiveness to provide
                comprehensive insights and actionable improvement recommendations.""",
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            claude_analysis = response.content[0].text

            # Parse Claude's analysis
            analysis_results = await self._parse_performance_analysis_response(
                claude_analysis, agent_id, performance_data, trend_analysis
            )

            # Generate performance predictions if requested
            predicted_performance = {}
            if include_predictions:
                predicted_performance = await self._predict_future_performance(
                    agent_id, performance_data, trend_analysis
                )

            # Create performance analysis object
            performance_analysis = PerformanceAnalysis(
                analysis_id=analysis_id,
                agent_id=agent_id,
                analysis_period=analysis_period,
                performance_summary=analysis_results.get("performance_summary", {}),
                trend_analysis=trend_analysis,
                comparative_analysis=comparative_analysis,
                coaching_effectiveness=coaching_effectiveness,
                improvement_recommendations=analysis_results.get("improvement_recommendations", []),
                coaching_plan=analysis_results.get("coaching_plan", {}),
                predicted_performance=predicted_performance,
                risk_indicators=analysis_results.get("risk_indicators", []),
                opportunity_areas=analysis_results.get("opportunity_areas", []),
                confidence_score=analysis_results.get("confidence_score", 0.75),
                analyzed_at=analysis_start
            )

            # Store analysis
            self.analysis_history.append(performance_analysis)
            self._save_analysis_history()

            # Update agent profile with insights
            await self._update_agent_profile_from_analysis(agent_id, performance_analysis)

            analysis_time = (datetime.now() - analysis_start).total_seconds()
            logger.info(f"Completed performance analysis {analysis_id} in {analysis_time:.2f}s")

            return performance_analysis

        except Exception as e:
            logger.error(f"Error analyzing agent performance for {agent_id}: {e}")
            return PerformanceAnalysis(
                analysis_id=f"error_{int(datetime.now().timestamp())}",
                agent_id=agent_id,
                analysis_period=analysis_period,
                performance_summary={},
                trend_analysis={},
                comparative_analysis={},
                coaching_effectiveness={},
                improvement_recommendations=[f"Analysis error: {str(e)}"],
                coaching_plan={},
                predicted_performance={},
                risk_indicators=["Analysis system error"],
                opportunity_areas=[],
                confidence_score=0.1,
                analyzed_at=datetime.now()
            )

    async def track_coaching_effectiveness(
        self,
        session_id: str,
        pre_metrics: Dict[str, float],
        post_metrics: Dict[str, float],
        follow_up_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Track and analyze the effectiveness of a coaching session.

        Args:
            session_id: Coaching session identifier
            pre_metrics: Performance metrics before coaching
            post_metrics: Performance metrics after coaching
            follow_up_period_days: Period to track improvement

        Returns:
            Coaching effectiveness analysis and recommendations
        """
        try:
            if session_id not in self.coaching_sessions:
                raise ValueError(f"Coaching session {session_id} not found")

            session = self.coaching_sessions[session_id]
            effectiveness_start = datetime.now()

            logger.info(f"Tracking coaching effectiveness for session {session_id}")

            # Calculate immediate effectiveness metrics
            immediate_effectiveness = await self._calculate_immediate_coaching_effectiveness(
                session, pre_metrics, post_metrics
            )

            # Get long-term effectiveness data if available
            long_term_effectiveness = await self._analyze_long_term_coaching_impact(
                session_id, follow_up_period_days
            )

            # Create coaching effectiveness analysis prompt
            effectiveness_prompt = f"""
            COACHING EFFECTIVENESS ANALYSIS

            Session: {session_id}
            Agent: {session.agent_id}
            Focus Areas: {[area.value for area in session.focus_areas]}
            Session Duration: {session.duration_minutes} minutes

            Pre-Coaching Metrics: {json.dumps(pre_metrics, indent=2)}
            Post-Coaching Metrics: {json.dumps(post_metrics, indent=2)}
            Immediate Effectiveness: {json.dumps(immediate_effectiveness, indent=2)}
            Long-term Impact: {json.dumps(long_term_effectiveness, indent=2)}

            Please analyze coaching effectiveness focusing on:

            1. IMMEDIATE IMPACT ASSESSMENT:
               - Metric improvements directly after coaching
               - Skill development evidence
               - Behavioral change indicators
               - Knowledge retention assessment

            2. COACHING METHODOLOGY EVALUATION:
               - Effectiveness of focus areas chosen
               - Session duration optimization
               - Teaching method success
               - Agent engagement and receptivity

            3. LONG-TERM IMPACT ANALYSIS:
               - Sustained performance improvements
               - Skill retention over time
               - Behavioral consistency maintenance
               - Performance trajectory changes

            4. COACHING OPTIMIZATION RECOMMENDATIONS:
               - Session structure improvements
               - Focus area prioritization
               - Follow-up timing optimization
               - Personalization enhancements

            5. AGENT-SPECIFIC INSIGHTS:
               - Learning style compatibility
               - Coaching preference alignment
               - Motivation factor effectiveness
               - Resistance area identification

            Provide specific recommendations for improving coaching effectiveness.
            """

            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                temperature=0.4,
                system="""You are an expert coaching effectiveness analyst for real estate.
                Evaluate coaching sessions and their impact to optimize agent development
                and performance improvement strategies.""",
                messages=[{"role": "user", "content": effectiveness_prompt}]
            )

            claude_analysis = response.content[0].text

            # Parse coaching effectiveness analysis
            effectiveness_results = await self._parse_coaching_effectiveness_response(
                claude_analysis, session, immediate_effectiveness, long_term_effectiveness
            )

            # Update coaching session with effectiveness data
            session.effectiveness_score = effectiveness_results.get("effectiveness_score", 0.0)
            session.post_session_metrics = post_metrics
            self.coaching_sessions[session_id] = session
            self._save_coaching_sessions()

            # Track coaching impact for future reference
            self.coaching_impact_tracking[session.agent_id][session_id] = {
                "effectiveness_score": effectiveness_results.get("effectiveness_score", 0.0),
                "improvement_areas": effectiveness_results.get("improvement_areas", []),
                "coaching_recommendations": effectiveness_results.get("coaching_recommendations", []),
                "tracked_at": effectiveness_start.isoformat()
            }

            effectiveness_time = (datetime.now() - effectiveness_start).total_seconds()
            logger.info(f"Completed coaching effectiveness tracking for {session_id} in {effectiveness_time:.2f}s")

            return effectiveness_results

        except Exception as e:
            logger.error(f"Error tracking coaching effectiveness for {session_id}: {e}")
            return {
                "effectiveness_score": 0.0,
                "immediate_impact": {},
                "long_term_impact": {},
                "improvement_areas": [f"Tracking error: {str(e)}"],
                "coaching_recommendations": ["Manual effectiveness review needed"],
                "confidence": 0.1
            }

    async def generate_team_performance_insights(
        self,
        team_id: str,
        analysis_period: str = "30_days"
    ) -> TeamPerformanceInsights:
        """
        Generate comprehensive team performance insights and recommendations.

        Args:
            team_id: Team identifier
            analysis_period: Period for analysis

        Returns:
            TeamPerformanceInsights with team-level analytics and recommendations
        """
        try:
            insights_start = datetime.now()

            logger.info(f"Generating team performance insights for team {team_id}")

            # Get team members
            team_agents = [
                agent for agent in self.agent_profiles.values()
                if agent.team_id == team_id
            ]

            if not team_agents:
                raise ValueError(f"No agents found for team {team_id}")

            # Gather team performance data
            team_data = await self._gather_team_performance_data(team_agents, analysis_period)

            # Analyze individual performances
            individual_analyses = {}
            for agent in team_agents:
                agent_performance = await self._get_agent_performance_summary(
                    agent.agent_id, analysis_period
                )
                individual_analyses[agent.agent_id] = agent_performance

            # Analyze team coaching effectiveness
            team_coaching_effectiveness = await self._analyze_team_coaching_effectiveness(
                team_agents, analysis_period
            )

            # Create team insights prompt
            team_insights_prompt = f"""
            TEAM PERFORMANCE INSIGHTS ANALYSIS

            Team: {team_id}
            Analysis Period: {analysis_period}
            Team Size: {len(team_agents)}

            Team Performance Data: {json.dumps(team_data, indent=2, default=str)}
            Individual Performances: {json.dumps(individual_analyses, indent=2, default=str)}
            Coaching Effectiveness: {json.dumps(team_coaching_effectiveness, indent=2, default=str)}

            Please analyze team performance and provide insights on:

            1. TEAM PERFORMANCE OVERVIEW:
               - Overall team metrics and trends
               - Performance distribution analysis
               - Team vs individual benchmark comparison
               - Collective achievement assessment

            2. INDIVIDUAL PERFORMANCE ANALYSIS:
               - Top performers and their strengths
               - Underperformers and improvement needs
               - Performance variation patterns
               - Skill complementarity assessment

            3. TEAM DYNAMICS AND COLLABORATION:
               - Collaboration effectiveness indicators
               - Knowledge sharing patterns
               - Peer coaching opportunities
               - Team cohesion assessment

            4. COACHING AND DEVELOPMENT:
               - Team coaching effectiveness
               - Skill gap identification
               - Training needs prioritization
               - Development resource allocation

            5. OPTIMIZATION OPPORTUNITIES:
               - Performance improvement potential
               - Resource reallocation recommendations
               - Process optimization areas
               - Technology adoption opportunities

            6. STRATEGIC RECOMMENDATIONS:
               - Team structure optimization
               - Role specialization opportunities
               - Performance incentive improvements
               - Long-term development planning

            Provide actionable insights for team performance optimization.
            """

            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1200,
                temperature=0.3,
                system="""You are an expert team performance analyst for real estate.
                Analyze team dynamics, individual contributions, and coaching effectiveness
                to provide comprehensive team optimization recommendations.""",
                messages=[{"role": "user", "content": team_insights_prompt}]
            )

            claude_analysis = response.content[0].text

            # Parse team insights response
            insights_results = await self._parse_team_insights_response(
                claude_analysis, team_agents, team_data, individual_analyses
            )

            # Create team performance insights object
            team_insights = TeamPerformanceInsights(
                team_id=team_id,
                team_name=f"Team {team_id}",
                analysis_period=analysis_period,
                team_metrics=insights_results.get("team_metrics", {}),
                individual_performances=individual_analyses,
                performance_distribution=insights_results.get("performance_distribution", {}),
                coaching_effectiveness=team_coaching_effectiveness,
                skill_gap_analysis=insights_results.get("skill_gap_analysis", {}),
                team_strengths=insights_results.get("team_strengths", []),
                team_challenges=insights_results.get("team_challenges", []),
                resource_optimization=insights_results.get("resource_optimization", {}),
                performance_predictions=insights_results.get("performance_predictions", {}),
                recommended_interventions=insights_results.get("recommended_interventions", []),
                generated_at=insights_start
            )

            insights_time = (datetime.now() - insights_start).total_seconds()
            logger.info(f"Generated team insights for {team_id} in {insights_time:.2f}s")

            return team_insights

        except Exception as e:
            logger.error(f"Error generating team insights for {team_id}: {e}")
            return TeamPerformanceInsights(
                team_id=team_id,
                team_name=f"Team {team_id}",
                analysis_period=analysis_period,
                team_metrics={},
                individual_performances={},
                performance_distribution={},
                coaching_effectiveness={},
                skill_gap_analysis={},
                team_strengths=[],
                team_challenges=[f"Analysis error: {str(e)}"],
                resource_optimization={},
                performance_predictions={},
                recommended_interventions=["Manual team analysis required"],
                generated_at=datetime.now()
            )

    def record_performance_data_point(
        self,
        agent_id: str,
        metric: PerformanceMetric,
        value: float,
        context: Optional[Dict[str, Any]] = None,
        coaching_session_id: Optional[str] = None
    ) -> None:
        """
        Record a single performance data point for an agent.

        Args:
            agent_id: Agent identifier
            metric: Performance metric type
            value: Metric value
            context: Additional context information
            coaching_session_id: Related coaching session if applicable
        """
        try:
            # Get benchmark value for comparison
            benchmark_value = self._get_benchmark_value(metric)

            # Create performance data point
            data_point = PerformanceDataPoint(
                agent_id=agent_id,
                metric=metric,
                value=value,
                benchmark_value=benchmark_value,
                context=context or {},
                coaching_session_id=coaching_session_id,
                timestamp=datetime.now()
            )

            # Store data point
            self.performance_data.append(data_point)

            # Update real-time tracking
            self.real_time_metrics[agent_id][metric].append((value, datetime.now()))

            # Keep only recent real-time data
            if len(self.real_time_metrics[agent_id][metric]) > 100:
                self.real_time_metrics[agent_id][metric].popleft()

            # Check for performance alerts
            self._check_performance_alerts(agent_id, metric, value, benchmark_value)

            # Periodically save data (every 10 data points)
            if len(self.performance_data) % 10 == 0:
                self._save_performance_data()

            logger.debug(f"Recorded {metric.value} = {value} for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error recording performance data point: {e}")

    def record_coaching_session(
        self,
        agent_id: str,
        coach_id: str,
        focus_areas: List[CoachingFocusArea],
        session_type: str,
        duration_minutes: int,
        topics_covered: List[str],
        action_items: List[str],
        agent_feedback: Dict[str, Any],
        pre_session_metrics: Dict[str, float]
    ) -> str:
        """
        Record a coaching session and return the session ID.

        Args:
            agent_id: Agent identifier
            coach_id: Coach identifier
            focus_areas: Areas of focus for the session
            session_type: Type of coaching session
            duration_minutes: Session duration
            topics_covered: Topics discussed
            action_items: Action items assigned
            agent_feedback: Feedback from agent
            pre_session_metrics: Performance metrics before session

        Returns:
            Session ID for tracking
        """
        try:
            session_id = f"coaching_{agent_id}_{int(datetime.now().timestamp())}"

            coaching_session = CoachingSession(
                session_id=session_id,
                agent_id=agent_id,
                coach_id=coach_id,
                focus_areas=focus_areas,
                session_type=session_type,
                duration_minutes=duration_minutes,
                topics_covered=topics_covered,
                action_items=action_items,
                agent_feedback=agent_feedback,
                pre_session_metrics=pre_session_metrics,
                post_session_metrics={},  # To be filled later
                effectiveness_score=None,
                follow_up_required=len(action_items) > 0,
                session_date=datetime.now()
            )

            # Store coaching session
            self.coaching_sessions[session_id] = coaching_session
            self._save_coaching_sessions()

            # Update agent profile
            if agent_id in self.agent_profiles:
                self.agent_profiles[agent_id].coaching_history.append(session_id)
                self._save_agent_profiles()

            logger.info(f"Recorded coaching session {session_id} for agent {agent_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error recording coaching session: {e}")
            return ""

    # Helper methods for data gathering and analysis

    async def _gather_agent_performance_data(
        self,
        agent_id: str,
        analysis_period: str
    ) -> Dict[str, Any]:
        """Gather comprehensive performance data for an agent."""
        try:
            # Calculate period start date
            days_back = self._parse_analysis_period(analysis_period)
            period_start = datetime.now() - timedelta(days=days_back)

            # Filter performance data for period
            period_data = [
                point for point in self.performance_data
                if point.agent_id == agent_id and point.timestamp >= period_start
            ]

            # Organize data by metric
            metrics_data = defaultdict(list)
            for point in period_data:
                metrics_data[point.metric].append({
                    "value": point.value,
                    "benchmark": point.benchmark_value,
                    "timestamp": point.timestamp.isoformat(),
                    "context": point.context
                })

            # Calculate summary statistics
            metrics_summary = {}
            for metric, values in metrics_data.items():
                if values:
                    metric_values = [v["value"] for v in values]
                    metrics_summary[metric.value] = {
                        "current": metric_values[-1] if metric_values else 0,
                        "average": statistics.mean(metric_values),
                        "trend": self._calculate_trend(metric_values),
                        "improvement": self._calculate_improvement(metric_values),
                        "data_points": len(metric_values)
                    }

            return {
                "period_start": period_start.isoformat(),
                "period_days": days_back,
                "total_data_points": len(period_data),
                "metrics_data": dict(metrics_data),
                "metrics_summary": metrics_summary
            }

        except Exception as e:
            logger.error(f"Error gathering performance data for {agent_id}: {e}")
            return {"error": str(e)}

    async def _analyze_performance_trends(
        self,
        agent_id: str,
        performance_data: Dict[str, Any],
        analysis_period: str
    ) -> Dict[str, Any]:
        """Analyze performance trends for an agent."""
        try:
            trends_analysis = {}
            metrics_summary = performance_data.get("metrics_summary", {})

            for metric_name, metric_data in metrics_summary.items():
                trend_direction = metric_data.get("trend", "stable")
                improvement_rate = metric_data.get("improvement", 0.0)

                trends_analysis[metric_name] = {
                    "trend_direction": trend_direction,
                    "improvement_rate": improvement_rate,
                    "trend_strength": abs(improvement_rate),
                    "trend_consistency": self._calculate_trend_consistency(
                        performance_data.get("metrics_data", {}).get(metric_name, [])
                    )
                }

            return {
                "overall_trend": self._determine_overall_trend(trends_analysis),
                "individual_trends": trends_analysis,
                "trend_stability": self._calculate_overall_stability(trends_analysis),
                "improvement_momentum": self._calculate_improvement_momentum(trends_analysis)
            }

        except Exception as e:
            logger.error(f"Error analyzing trends for {agent_id}: {e}")
            return {"error": str(e)}

    async def _perform_comparative_analysis(
        self,
        agent_id: str,
        performance_data: Dict[str, Any],
        agent_profile: AgentPerformanceProfile
    ) -> Dict[str, Any]:
        """Perform comparative analysis against benchmarks and peers."""
        try:
            metrics_summary = performance_data.get("metrics_summary", {})
            comparative_results = {}

            for metric_name, metric_data in metrics_summary.items():
                current_value = metric_data.get("current", 0)

                # Compare against benchmarks
                benchmark_comparison = self._compare_against_benchmarks(metric_name, current_value)

                # Compare against peer performance
                peer_comparison = await self._compare_against_peers(
                    agent_id, metric_name, current_value, agent_profile
                )

                comparative_results[metric_name] = {
                    "benchmark_comparison": benchmark_comparison,
                    "peer_comparison": peer_comparison,
                    "performance_percentile": self._calculate_performance_percentile(
                        metric_name, current_value
                    )
                }

            return {
                "individual_comparisons": comparative_results,
                "overall_ranking": self._calculate_overall_ranking(comparative_results),
                "strengths": self._identify_comparative_strengths(comparative_results),
                "improvement_opportunities": self._identify_improvement_opportunities(comparative_results)
            }

        except Exception as e:
            logger.error(f"Error performing comparative analysis for {agent_id}: {e}")
            return {"error": str(e)}

    # Additional helper methods for analysis and calculations

    def _parse_analysis_period(self, period: str) -> int:
        """Parse analysis period string to number of days."""
        period_map = {
            "7_days": 7,
            "30_days": 30,
            "90_days": 90,
            "180_days": 180,
            "365_days": 365
        }
        return period_map.get(period, 30)

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend calculation
        x = list(range(len(values)))
        n = len(values)

        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x_i * x_i for x_i in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0

        if slope > 0.05:
            return "increasing"
        elif slope < -0.05:
            return "decreasing"
        else:
            return "stable"

    def _calculate_improvement(self, values: List[float]) -> float:
        """Calculate improvement rate from values."""
        if len(values) < 2:
            return 0.0

        start_value = values[0]
        end_value = values[-1]

        if start_value == 0:
            return 1.0 if end_value > 0 else 0.0

        improvement = (end_value - start_value) / start_value
        return improvement

    def _get_benchmark_value(self, metric: PerformanceMetric) -> Optional[float]:
        """Get benchmark value for a metric."""
        industry_standards = self.benchmarks.get("industry_standards", {})
        metric_benchmarks = industry_standards.get(metric.value, {})
        return metric_benchmarks.get("average")

    def _check_performance_alerts(
        self,
        agent_id: str,
        metric: PerformanceMetric,
        value: float,
        benchmark_value: Optional[float]
    ) -> None:
        """Check if performance data triggers any alerts."""
        if benchmark_value and value < benchmark_value * 0.7:  # 30% below benchmark
            alert = {
                "agent_id": agent_id,
                "metric": metric.value,
                "value": value,
                "benchmark": benchmark_value,
                "alert_type": "performance_decline",
                "timestamp": datetime.now().isoformat()
            }
            self.performance_alerts.append(alert)

    def get_performance_analytics_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics dashboard data."""
        try:
            total_agents = len(self.agent_profiles)
            total_sessions = len(self.coaching_sessions)
            total_analyses = len(self.analysis_history)

            # Calculate performance distribution
            performance_distribution = defaultdict(int)
            for agent in self.agent_profiles.values():
                performance_distribution[agent.performance_level.value] += 1

            # Calculate coaching effectiveness metrics
            effective_sessions = sum(
                1 for session in self.coaching_sessions.values()
                if session.effectiveness_score and session.effectiveness_score > 0.6
            )
            coaching_success_rate = effective_sessions / len(self.coaching_sessions) if self.coaching_sessions else 0

            # Get recent alerts
            recent_alerts = len([
                alert for alert in self.performance_alerts
                if datetime.fromisoformat(alert["timestamp"]) > datetime.now() - timedelta(days=7)
            ])

            return {
                "overview": {
                    "total_agents": total_agents,
                    "total_coaching_sessions": total_sessions,
                    "total_analyses": total_analyses,
                    "recent_alerts": recent_alerts
                },
                "performance_distribution": dict(performance_distribution),
                "coaching_metrics": {
                    "coaching_success_rate": coaching_success_rate,
                    "avg_session_duration": statistics.mean([s.duration_minutes for s in self.coaching_sessions.values()]) if self.coaching_sessions else 0,
                    "follow_up_required_rate": sum(1 for s in self.coaching_sessions.values() if s.follow_up_required) / len(self.coaching_sessions) if self.coaching_sessions else 0
                },
                "trend_analysis": {
                    "improving_agents": len([a for a in self.agent_profiles.values() if a.performance_level in [PerformanceLevel.EXCEPTIONAL, PerformanceLevel.HIGH_PERFORMER]]),
                    "needs_attention": len([a for a in self.agent_profiles.values() if a.performance_level in [PerformanceLevel.NEEDS_IMPROVEMENT, PerformanceLevel.CRITICAL_ATTENTION]]),
                    "stable_performers": len([a for a in self.agent_profiles.values() if a.performance_level == PerformanceLevel.SOLID_PERFORMER])
                }
            }

        except Exception as e:
            logger.error(f"Error generating performance analytics dashboard: {e}")
            return {"error": str(e), "total_agents": 0}

    # Data conversion helper methods

    def _dict_to_performance_data_point(self, data: Dict) -> PerformanceDataPoint:
        """Convert dictionary to PerformanceDataPoint."""
        data["metric"] = PerformanceMetric(data["metric"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return PerformanceDataPoint(**data)

    def _dict_to_coaching_session(self, data: Dict) -> CoachingSession:
        """Convert dictionary to CoachingSession."""
        data["focus_areas"] = [CoachingFocusArea(area) for area in data["focus_areas"]]
        data["session_date"] = datetime.fromisoformat(data["session_date"])
        return CoachingSession(**data)

    def _dict_to_agent_profile(self, data: Dict) -> AgentPerformanceProfile:
        """Convert dictionary to AgentPerformanceProfile."""
        data["performance_level"] = PerformanceLevel(data["performance_level"])
        data["hire_date"] = datetime.fromisoformat(data["hire_date"])
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])

        # Convert current_metrics keys
        current_metrics = {}
        for key, value in data.get("current_metrics", {}).items():
            if isinstance(key, str):
                current_metrics[PerformanceMetric(key)] = value
            else:
                current_metrics[key] = value
        data["current_metrics"] = current_metrics

        # Convert performance_trends keys
        performance_trends = {}
        for key, value in data.get("performance_trends", {}).items():
            if isinstance(key, str):
                performance_trends[PerformanceMetric(key)] = value
            else:
                performance_trends[key] = value
        data["performance_trends"] = performance_trends

        # Convert improvement_areas
        improvement_areas = []
        for area in data.get("improvement_areas", []):
            if isinstance(area, str):
                improvement_areas.append(CoachingFocusArea(area))
            else:
                improvement_areas.append(area)
        data["improvement_areas"] = improvement_areas

        return AgentPerformanceProfile(**data)

    def _dict_to_performance_analysis(self, data: Dict) -> PerformanceAnalysis:
        """Convert dictionary to PerformanceAnalysis."""
        data["analyzed_at"] = datetime.fromisoformat(data["analyzed_at"])
        return PerformanceAnalysis(**data)

    # Additional placeholder methods for comprehensive implementation
    async def _analyze_coaching_effectiveness(self, agent_id: str, analysis_period: str) -> Dict[str, Any]:
        """Analyze coaching effectiveness for an agent."""
        return {"coaching_effectiveness_score": 0.75, "improvement_rate": 0.15}

    async def _predict_future_performance(self, agent_id: str, performance_data: Dict, trend_analysis: Dict) -> Dict[str, float]:
        """Predict future performance based on trends."""
        return {"predicted_30_day_improvement": 0.12}

    async def _create_performance_analysis_prompt(self, agent_id: str, agent_profile: AgentPerformanceProfile, performance_data: Dict, trend_analysis: Dict, comparative_analysis: Dict, coaching_effectiveness: Dict) -> str:
        """Create performance analysis prompt for Claude."""
        return f"Analyze performance for agent {agent_id}..."

    async def _parse_performance_analysis_response(self, claude_response: str, agent_id: str, performance_data: Dict, trend_analysis: Dict) -> Dict[str, Any]:
        """Parse Claude's performance analysis response."""
        return {"performance_summary": {}, "improvement_recommendations": [], "coaching_plan": {}, "confidence_score": 0.75}

    async def _update_agent_profile_from_analysis(self, agent_id: str, analysis: PerformanceAnalysis) -> None:
        """Update agent profile with analysis insights."""
        pass

    # Additional helper methods would be implemented here for complete functionality...


# Global instance for easy access
claude_performance_analytics = ClaudeAgentPerformanceAnalytics()