"""
Agent Onboarding and Training Service with Claude Integration

Provides comprehensive onboarding workflows, training modules, skill assessments,
and AI-powered coaching for new and existing real estate agents.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)


class OnboardingStage(Enum):
    """Different stages of agent onboarding."""
    REGISTRATION = "registration"
    PROFILE_SETUP = "profile_setup"
    SYSTEM_ORIENTATION = "system_orientation"
    ROLE_TRAINING = "role_training"
    SKILL_ASSESSMENT = "skill_assessment"
    PRACTICAL_TRAINING = "practical_training"
    MENTORSHIP = "mentorship"
    CERTIFICATION = "certification"
    ONGOING_DEVELOPMENT = "ongoing_development"


class TrainingModule(Enum):
    """Different training modules available."""
    LEAD_QUALIFICATION = "lead_qualification"
    PROPERTY_PRESENTATION = "property_presentation"
    OBJECTION_HANDLING = "objection_handling"
    NEGOTIATION_SKILLS = "negotiation_skills"
    MARKET_ANALYSIS = "market_analysis"
    CLIENT_COMMUNICATION = "client_communication"
    TECHNOLOGY_TOOLS = "technology_tools"
    COMPLIANCE_LEGAL = "compliance_legal"
    CLOSING_PROCESS = "closing_process"
    PROSPECTING = "prospecting"


class SkillLevel(Enum):
    """Skill proficiency levels."""
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    PROFICIENT = "proficient"
    EXPERT = "expert"


class AssessmentType(Enum):
    """Types of skill assessments."""
    KNOWLEDGE_TEST = "knowledge_test"
    ROLE_PLAY = "role_play"
    SCENARIO_SIMULATION = "scenario_simulation"
    CONVERSATION_ANALYSIS = "conversation_analysis"
    PRACTICAL_EXERCISE = "practical_exercise"


@dataclass
class TrainingContent:
    """Training content structure."""
    id: str
    module: TrainingModule
    title: str
    description: str
    content_type: str  # "video", "text", "interactive", "claude_session"
    content_url: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None
    estimated_duration: int = 0  # minutes
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    difficulty_level: SkillLevel = SkillLevel.BEGINNER
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SkillAssessment:
    """Skill assessment definition."""
    id: str
    module: TrainingModule
    assessment_type: AssessmentType
    title: str
    description: str
    questions: List[Dict[str, Any]]
    scoring_criteria: Dict[str, Any]
    passing_score: float = 0.7
    max_attempts: int = 3
    time_limit: Optional[int] = None  # minutes
    claude_evaluation: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentProgress:
    """Agent training progress tracking."""
    agent_id: str
    current_stage: OnboardingStage
    completed_modules: List[str] = field(default_factory=list)
    completed_assessments: List[str] = field(default_factory=list)
    skill_levels: Dict[str, SkillLevel] = field(default_factory=dict)
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)
    total_training_hours: float = 0.0
    completion_percentage: float = 0.0
    certification_earned: Optional[datetime] = None
    next_recommended_modules: List[str] = field(default_factory=list)
    mentor_assignments: List[str] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    custom_training_path: Optional[List[str]] = None


@dataclass
class TrainingSession:
    """Individual training session record."""
    id: str
    agent_id: str
    module: TrainingModule
    content_id: str
    session_type: str  # "content_review", "claude_coaching", "assessment", "practice"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: float = 0.0
    completion_status: str = "in_progress"  # "completed", "abandoned", "failed"
    score: Optional[float] = None
    notes: Optional[str] = None
    claude_interactions: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    feedback_provided: Optional[str] = None
    follow_up_actions: List[str] = field(default_factory=list)


@dataclass
class OnboardingWorkflow:
    """Complete onboarding workflow definition."""
    id: str
    name: str
    description: str
    target_role: str  # "new_agent", "experienced_transfer", "team_lead"
    stages: List[Dict[str, Any]]
    estimated_duration_weeks: int
    required_modules: List[str]
    optional_modules: List[str]
    assessment_checkpoints: List[str]
    success_criteria: Dict[str, Any]
    customization_options: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MentorshipAssignment:
    """Mentorship pairing and tracking."""
    id: str
    mentee_agent_id: str
    mentor_agent_id: str
    assignment_date: datetime
    focus_areas: List[str]
    meeting_schedule: str
    goals: List[str]
    progress_notes: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"  # "active", "completed", "paused", "ended"
    effectiveness_rating: Optional[float] = None
    end_date: Optional[datetime] = None


class AgentOnboardingService:
    """Service for managing agent onboarding and training with Claude integration."""

    def __init__(self):
        """Initialize the onboarding service."""
        self.training_content: Dict[str, TrainingContent] = {}
        self.skill_assessments: Dict[str, SkillAssessment] = {}
        self.agent_progress: Dict[str, AgentProgress] = {}
        self.training_sessions: Dict[str, TrainingSession] = {}
        self.onboarding_workflows: Dict[str, OnboardingWorkflow] = {}
        self.mentorship_assignments: Dict[str, MentorshipAssignment] = {}

        # Initialize default content and workflows
        self._initialize_training_content()
        self._initialize_skill_assessments()
        self._initialize_onboarding_workflows()

    def _initialize_training_content(self):
        """Initialize default training content."""
        content_items = [
            TrainingContent(
                id="lead_qual_basics",
                module=TrainingModule.LEAD_QUALIFICATION,
                title="Lead Qualification Fundamentals",
                description="Master the art of qualifying real estate leads effectively",
                content_type="claude_session",
                content_data={
                    "scenario": "lead_qualification_training",
                    "conversation_template": "lead_qual_rookie",
                    "practice_scenarios": [
                        "First-time homebuyer inquiry",
                        "Investment property interest",
                        "Relocation lead",
                        "Luxury market prospect"
                    ]
                },
                estimated_duration=45,
                learning_objectives=[
                    "Identify key qualifying questions",
                    "Understand buyer motivation psychology",
                    "Learn to handle budget discussions",
                    "Master timeline establishment techniques"
                ],
                difficulty_level=SkillLevel.BEGINNER,
                tags=["fundamentals", "qualification", "claude_training"]
            ),
            TrainingContent(
                id="objection_handling_advanced",
                module=TrainingModule.OBJECTION_HANDLING,
                title="Advanced Objection Handling with Claude",
                description="Learn sophisticated objection handling techniques through AI-powered practice",
                content_type="claude_session",
                content_data={
                    "scenario": "objection_handling_training",
                    "conversation_template": "objection_handling_relationship",
                    "objection_types": [
                        "Price too high",
                        "Need to think about it",
                        "Want to see more properties",
                        "Market timing concerns",
                        "Financing worries"
                    ]
                },
                estimated_duration=60,
                prerequisites=["lead_qual_basics"],
                learning_objectives=[
                    "Identify underlying objection causes",
                    "Practice empathetic response techniques",
                    "Learn to pivot conversations positively",
                    "Master the feel-felt-found technique"
                ],
                difficulty_level=SkillLevel.DEVELOPING,
                tags=["advanced", "objections", "psychology", "claude_training"]
            ),
            TrainingContent(
                id="market_analysis_mastery",
                module=TrainingModule.MARKET_ANALYSIS,
                title="Market Analysis Mastery",
                description="Become expert at analyzing and presenting market data",
                content_type="claude_session",
                content_data={
                    "scenario": "market_analysis_training",
                    "conversation_template": "market_analysis_data_driven",
                    "analysis_types": [
                        "Neighborhood trend analysis",
                        "Comparative market analysis (CMA)",
                        "Investment property evaluation",
                        "Market timing recommendations"
                    ]
                },
                estimated_duration=90,
                prerequisites=["lead_qual_basics"],
                learning_objectives=[
                    "Interpret market statistics effectively",
                    "Create compelling market presentations",
                    "Identify market opportunities",
                    "Communicate value propositions clearly"
                ],
                difficulty_level=SkillLevel.COMPETENT,
                tags=["data_analysis", "presentation", "market_knowledge", "claude_training"]
            ),
            TrainingContent(
                id="technology_tools_overview",
                module=TrainingModule.TECHNOLOGY_TOOLS,
                title="Technology Stack Overview",
                description="Master the real estate technology tools and platforms",
                content_type="interactive",
                content_data={
                    "platform_tutorials": [
                        "GHL CRM Navigation",
                        "Lead Intelligence Hub",
                        "Claude AI Assistant Usage",
                        "Property Search Integration",
                        "Analytics Dashboard"
                    ]
                },
                estimated_duration=120,
                learning_objectives=[
                    "Navigate the GHL platform efficiently",
                    "Use Claude AI for lead insights",
                    "Leverage analytics for decision making",
                    "Integrate multiple data sources"
                ],
                difficulty_level=SkillLevel.BEGINNER,
                tags=["technology", "tools", "platform", "efficiency"]
            )
        ]

        for content in content_items:
            self.training_content[content.id] = content

    def _initialize_skill_assessments(self):
        """Initialize default skill assessments."""
        assessments = [
            SkillAssessment(
                id="lead_qual_assessment",
                module=TrainingModule.LEAD_QUALIFICATION,
                assessment_type=AssessmentType.ROLE_PLAY,
                title="Lead Qualification Role-Play Assessment",
                description="Practice lead qualification through realistic scenarios",
                questions=[
                    {
                        "scenario": "A potential buyer calls asking about a property but seems hesitant about their budget",
                        "prompt": "How would you handle this conversation to qualify the lead effectively?",
                        "evaluation_criteria": [
                            "Asks appropriate qualifying questions",
                            "Demonstrates empathy and relationship building",
                            "Identifies budget range tactfully",
                            "Establishes timeline and motivation",
                            "Sets appropriate next steps"
                        ]
                    },
                    {
                        "scenario": "An investor contacts you about potential rental properties in the area",
                        "prompt": "Demonstrate how you would qualify this investment-focused lead",
                        "evaluation_criteria": [
                            "Understands investment criteria",
                            "Asks about cash flow requirements",
                            "Discusses market analysis needs",
                            "Identifies financing approach",
                            "Assesses experience level"
                        ]
                    }
                ],
                scoring_criteria={
                    "communication_skills": 0.25,
                    "questioning_technique": 0.25,
                    "rapport_building": 0.20,
                    "information_gathering": 0.20,
                    "next_steps": 0.10
                },
                passing_score=0.75,
                claude_evaluation=True,
                time_limit=45
            ),
            SkillAssessment(
                id="market_analysis_test",
                module=TrainingModule.MARKET_ANALYSIS,
                assessment_type=AssessmentType.PRACTICAL_EXERCISE,
                title="Market Analysis Practical Exercise",
                description="Create and present a comprehensive market analysis",
                questions=[
                    {
                        "task": "analyze_neighborhood_trends",
                        "prompt": "Using the provided market data, analyze trends for the Downtown district and create a presentation for a client considering a $750K condo purchase",
                        "data_provided": True,
                        "deliverable": "Market analysis presentation with recommendations"
                    }
                ],
                scoring_criteria={
                    "data_accuracy": 0.30,
                    "trend_interpretation": 0.25,
                    "presentation_quality": 0.20,
                    "client_relevance": 0.15,
                    "recommendations": 0.10
                },
                passing_score=0.80,
                claude_evaluation=True,
                time_limit=90
            )
        ]

        for assessment in assessments:
            self.skill_assessments[assessment.id] = assessment

    def _initialize_onboarding_workflows(self):
        """Initialize default onboarding workflows."""
        workflows = [
            OnboardingWorkflow(
                id="new_agent_onboarding",
                name="New Agent Complete Onboarding",
                description="Comprehensive onboarding for agents new to real estate",
                target_role="new_agent",
                stages=[
                    {
                        "stage": OnboardingStage.REGISTRATION.value,
                        "name": "Registration and Welcome",
                        "description": "Complete profile and receive welcome materials",
                        "duration_days": 1,
                        "tasks": ["Complete profile", "Watch welcome video", "Meet with HR"]
                    },
                    {
                        "stage": OnboardingStage.SYSTEM_ORIENTATION.value,
                        "name": "System and Tools Orientation",
                        "description": "Learn the technology stack and tools",
                        "duration_days": 3,
                        "tasks": ["Technology overview", "Platform navigation", "Claude AI introduction"]
                    },
                    {
                        "stage": OnboardingStage.ROLE_TRAINING.value,
                        "name": "Real Estate Fundamentals Training",
                        "description": "Core real estate knowledge and skills",
                        "duration_days": 10,
                        "tasks": ["Lead qualification", "Property presentation", "Legal compliance"]
                    },
                    {
                        "stage": OnboardingStage.PRACTICAL_TRAINING.value,
                        "name": "Hands-on Practice and Coaching",
                        "description": "Practice with Claude AI and real scenarios",
                        "duration_days": 14,
                        "tasks": ["Claude coaching sessions", "Role-play exercises", "Shadow experienced agents"]
                    },
                    {
                        "stage": OnboardingStage.CERTIFICATION.value,
                        "name": "Final Assessment and Certification",
                        "description": "Complete assessments and earn certification",
                        "duration_days": 5,
                        "tasks": ["Skills assessments", "Final evaluation", "Certification ceremony"]
                    }
                ],
                estimated_duration_weeks=5,
                required_modules=[
                    "lead_qual_basics",
                    "technology_tools_overview",
                    "compliance_legal_basics",
                    "client_communication_fundamentals"
                ],
                optional_modules=[
                    "market_analysis_mastery",
                    "objection_handling_advanced"
                ],
                assessment_checkpoints=[
                    "lead_qual_assessment",
                    "technology_proficiency_test",
                    "final_comprehensive_exam"
                ],
                success_criteria={
                    "minimum_score": 0.75,
                    "completion_rate": 0.90,
                    "mentor_approval": True,
                    "client_readiness": True
                }
            ),
            OnboardingWorkflow(
                id="experienced_agent_onboarding",
                name="Experienced Agent Platform Training",
                description="Accelerated onboarding for experienced agents",
                target_role="experienced_transfer",
                stages=[
                    {
                        "stage": OnboardingStage.SYSTEM_ORIENTATION.value,
                        "name": "Platform Orientation",
                        "description": "Learn our specific tools and processes",
                        "duration_days": 2,
                        "tasks": ["Platform overview", "Claude AI training", "Process differences"]
                    },
                    {
                        "stage": OnboardingStage.SKILL_ASSESSMENT.value,
                        "name": "Skill Assessment and Gap Analysis",
                        "description": "Identify strengths and development areas",
                        "duration_days": 2,
                        "tasks": ["Skills evaluation", "Gap analysis", "Custom training plan"]
                    },
                    {
                        "stage": OnboardingStage.PRACTICAL_TRAINING.value,
                        "name": "Platform-Specific Practice",
                        "description": "Practice with our tools and AI assistance",
                        "duration_days": 5,
                        "tasks": ["Advanced Claude usage", "Integration practice", "Workflow optimization"]
                    }
                ],
                estimated_duration_weeks=2,
                required_modules=[
                    "technology_tools_overview",
                    "claude_advanced_usage",
                    "platform_specific_processes"
                ],
                optional_modules=[
                    "market_analysis_mastery",
                    "advanced_automation_techniques"
                ],
                assessment_checkpoints=[
                    "platform_proficiency_test",
                    "claude_usage_assessment"
                ],
                success_criteria={
                    "minimum_score": 0.80,
                    "platform_fluency": True,
                    "process_adherence": True
                }
            )
        ]

        for workflow in workflows:
            self.onboarding_workflows[workflow.id] = workflow

    async def start_agent_onboarding(
        self,
        agent_id: str,
        workflow_type: str = "new_agent_onboarding",
        custom_options: Optional[Dict[str, Any]] = None
    ) -> AgentProgress:
        """Start the onboarding process for a new agent."""
        try:
            # Get the onboarding workflow
            if workflow_type not in self.onboarding_workflows:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            workflow = self.onboarding_workflows[workflow_type]

            # Create agent progress record
            progress = AgentProgress(
                agent_id=agent_id,
                current_stage=OnboardingStage.REGISTRATION,
                next_recommended_modules=workflow.required_modules[:3]  # First 3 modules
            )

            # Apply custom options if provided
            if custom_options:
                if "focus_areas" in custom_options:
                    progress.custom_training_path = self._create_custom_path(
                        workflow.required_modules,
                        custom_options["focus_areas"]
                    )

            self.agent_progress[agent_id] = progress

            # Create initial welcome session
            await self._create_welcome_session(agent_id, workflow)

            logger.info(f"Started onboarding for agent {agent_id} with workflow {workflow_type}")
            return progress

        except Exception as e:
            logger.error(f"Error starting onboarding for agent {agent_id}: {str(e)}")
            raise

    async def get_agent_progress(self, agent_id: str) -> Optional[AgentProgress]:
        """Get current onboarding progress for an agent."""
        return self.agent_progress.get(agent_id)

    async def update_agent_progress(
        self,
        agent_id: str,
        completed_module: Optional[str] = None,
        completed_assessment: Optional[str] = None,
        skill_update: Optional[Dict[str, SkillLevel]] = None
    ) -> AgentProgress:
        """Update agent progress after completing training activities."""
        try:
            progress = self.agent_progress.get(agent_id)
            if not progress:
                raise ValueError(f"No onboarding record found for agent {agent_id}")

            # Update completed modules
            if completed_module and completed_module not in progress.completed_modules:
                progress.completed_modules.append(completed_module)

            # Update completed assessments
            if completed_assessment and completed_assessment not in progress.completed_assessments:
                progress.completed_assessments.append(completed_assessment)

            # Update skill levels
            if skill_update:
                progress.skill_levels.update(skill_update)

            # Recalculate progress
            await self._calculate_progress_metrics(agent_id)

            # Update recommendations
            await self._update_next_recommendations(agent_id)

            # Check for stage progression
            await self._check_stage_progression(agent_id)

            progress.last_activity = datetime.utcnow()

            logger.info(f"Updated progress for agent {agent_id}")
            return progress

        except Exception as e:
            logger.error(f"Error updating progress for agent {agent_id}: {str(e)}")
            raise

    async def start_training_session(
        self,
        agent_id: str,
        module: TrainingModule,
        content_id: str,
        session_type: str = "content_review"
    ) -> TrainingSession:
        """Start a new training session."""
        try:
            session = TrainingSession(
                id=f"session_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                module=module,
                content_id=content_id,
                session_type=session_type,
                start_time=datetime.utcnow()
            )

            self.training_sessions[session.id] = session

            # If this is a Claude session, prepare the conversation
            if session_type == "claude_coaching":
                await self._initialize_claude_session(session)

            logger.info(f"Started training session {session.id} for agent {agent_id}")
            return session

        except Exception as e:
            logger.error(f"Error starting training session: {str(e)}")
            raise

    async def complete_training_session(
        self,
        session_id: str,
        completion_status: str = "completed",
        score: Optional[float] = None,
        notes: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> TrainingSession:
        """Complete a training session and record results."""
        try:
            session = self.training_sessions.get(session_id)
            if not session:
                raise ValueError(f"Training session {session_id} not found")

            # Update session
            session.end_time = datetime.utcnow()
            session.duration_minutes = (session.end_time - session.start_time).total_seconds() / 60
            session.completion_status = completion_status
            session.score = score
            session.notes = notes
            session.performance_metrics = performance_metrics or {}

            # Update agent progress
            if completion_status == "completed":
                await self.update_agent_progress(
                    session.agent_id,
                    completed_module=session.content_id if session.session_type != "assessment" else None
                )

                # Update total training hours
                progress = self.agent_progress.get(session.agent_id)
                if progress:
                    progress.total_training_hours += session.duration_minutes / 60

            logger.info(f"Completed training session {session_id}")
            return session

        except Exception as e:
            logger.error(f"Error completing training session {session_id}: {str(e)}")
            raise

    async def conduct_skill_assessment(
        self,
        agent_id: str,
        assessment_id: str,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Conduct a skill assessment and evaluate results."""
        try:
            assessment = self.skill_assessments.get(assessment_id)
            if not assessment:
                raise ValueError(f"Assessment {assessment_id} not found")

            # Start assessment session
            session = await self.start_training_session(
                agent_id,
                assessment.module,
                assessment_id,
                "assessment"
            )

            results = {
                "assessment_id": assessment_id,
                "agent_id": agent_id,
                "session_id": session.id,
                "scores": {},
                "overall_score": 0.0,
                "passed": False,
                "feedback": [],
                "recommendations": []
            }

            # Evaluate responses
            if assessment.claude_evaluation:
                results = await self._claude_evaluate_assessment(assessment, responses)
            else:
                results = await self._standard_evaluate_assessment(assessment, responses)

            # Update session with results
            await self.complete_training_session(
                session.id,
                "completed" if results["passed"] else "failed",
                results["overall_score"],
                json.dumps(results["feedback"]),
                {"assessment_results": results}
            )

            # Update agent progress
            if results["passed"]:
                await self.update_agent_progress(
                    agent_id,
                    completed_assessment=assessment_id,
                    skill_update={assessment.module.value: self._determine_skill_level(results["overall_score"])}
                )

            logger.info(f"Completed assessment {assessment_id} for agent {agent_id}")
            return results

        except Exception as e:
            logger.error(f"Error conducting assessment: {str(e)}")
            raise

    async def assign_mentor(
        self,
        mentee_agent_id: str,
        mentor_agent_id: str,
        focus_areas: List[str],
        goals: List[str]
    ) -> MentorshipAssignment:
        """Assign a mentor to an agent."""
        try:
            assignment = MentorshipAssignment(
                id=f"mentorship_{uuid.uuid4().hex[:8]}",
                mentee_agent_id=mentee_agent_id,
                mentor_agent_id=mentor_agent_id,
                assignment_date=datetime.utcnow(),
                focus_areas=focus_areas,
                meeting_schedule="Weekly 1-hour sessions",
                goals=goals
            )

            self.mentorship_assignments[assignment.id] = assignment

            # Update agent progress
            progress = self.agent_progress.get(mentee_agent_id)
            if progress:
                progress.mentor_assignments.append(assignment.id)

            logger.info(f"Assigned mentor {mentor_agent_id} to agent {mentee_agent_id}")
            return assignment

        except Exception as e:
            logger.error(f"Error assigning mentor: {str(e)}")
            raise

    async def get_personalized_training_plan(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Generate a personalized training plan based on agent progress and needs."""
        try:
            progress = self.agent_progress.get(agent_id)
            if not progress:
                raise ValueError(f"No progress record found for agent {agent_id}")

            # Analyze current state
            analysis = await self._analyze_agent_needs(agent_id)

            # Generate recommendations
            training_plan = {
                "agent_id": agent_id,
                "current_stage": progress.current_stage.value,
                "completion_percentage": progress.completion_percentage,
                "analysis": analysis,
                "recommended_modules": [],
                "priority_areas": progress.weak_areas,
                "strengths": progress.strong_areas,
                "estimated_completion": None,
                "custom_path": progress.custom_training_path
            }

            # Determine next modules
            if progress.next_recommended_modules:
                for module_id in progress.next_recommended_modules:
                    module = self.training_content.get(module_id)
                    if module:
                        training_plan["recommended_modules"].append({
                            "id": module_id,
                            "title": module.title,
                            "module": module.module.value,
                            "estimated_duration": module.estimated_duration,
                            "priority": self._calculate_module_priority(agent_id, module)
                        })

            # Calculate estimated completion
            remaining_modules = len(training_plan["recommended_modules"])
            if remaining_modules > 0:
                avg_duration = sum(m["estimated_duration"] for m in training_plan["recommended_modules"]) / remaining_modules
                estimated_weeks = (remaining_modules * avg_duration) / (60 * 20)  # 20 hours per week
                training_plan["estimated_completion"] = datetime.utcnow() + timedelta(weeks=estimated_weeks)

            return training_plan

        except Exception as e:
            logger.error(f"Error generating training plan for agent {agent_id}: {str(e)}")
            raise

    async def get_onboarding_analytics(
        self,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get analytics on onboarding performance."""
        try:
            # Filter data by date range if provided
            agents_data = list(self.agent_progress.values())
            sessions_data = list(self.training_sessions.values())

            if date_range:
                start_date, end_date = date_range
                agents_data = [a for a in agents_data if start_date <= a.last_activity <= end_date]
                sessions_data = [s for s in sessions_data if start_date <= s.start_time <= end_date]

            analytics = {
                "total_agents_onboarding": len(agents_data),
                "completion_rates": {},
                "average_training_hours": 0.0,
                "stage_distribution": {},
                "module_completion_rates": {},
                "assessment_pass_rates": {},
                "training_effectiveness": {},
                "mentor_impact": {}
            }

            # Calculate completion rates by stage
            stage_counts = {}
            total_hours = 0
            completed_agents = 0

            for progress in agents_data:
                stage = progress.current_stage.value
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
                total_hours += progress.total_training_hours

                if progress.completion_percentage >= 100:
                    completed_agents += 1

            analytics["stage_distribution"] = stage_counts
            analytics["overall_completion_rate"] = completed_agents / max(len(agents_data), 1)
            analytics["average_training_hours"] = total_hours / max(len(agents_data), 1)

            # Module completion analysis
            all_modules = set()
            module_completions = {}

            for progress in agents_data:
                all_modules.update(progress.completed_modules)
                for module in progress.completed_modules:
                    module_completions[module] = module_completions.get(module, 0) + 1

            for module in all_modules:
                completion_rate = module_completions[module] / len(agents_data)
                analytics["module_completion_rates"][module] = completion_rate

            # Session effectiveness analysis
            session_scores = []
            for session in sessions_data:
                if session.score is not None:
                    session_scores.append(session.score)

            if session_scores:
                analytics["average_session_score"] = sum(session_scores) / len(session_scores)
                analytics["session_pass_rate"] = len([s for s in session_scores if s >= 0.7]) / len(session_scores)

            return analytics

        except Exception as e:
            logger.error(f"Error generating onboarding analytics: {str(e)}")
            raise

    # Helper methods

    async def _calculate_progress_metrics(self, agent_id: str):
        """Calculate completion percentage and other progress metrics."""
        try:
            progress = self.agent_progress[agent_id]

            # Get appropriate workflow
            workflow = self.onboarding_workflows.get("new_agent_onboarding")  # Default
            if not workflow:
                return

            # Calculate completion percentage
            total_required = len(workflow.required_modules)
            completed = len(progress.completed_modules)
            progress.completion_percentage = (completed / total_required) * 100

            # Analyze weak/strong areas based on assessments
            await self._analyze_performance_areas(agent_id)

        except Exception as e:
            logger.error(f"Error calculating progress metrics: {str(e)}")

    async def _update_next_recommendations(self, agent_id: str):
        """Update next recommended modules based on progress."""
        try:
            progress = self.agent_progress[agent_id]
            workflow = self.onboarding_workflows.get("new_agent_onboarding")

            if not workflow:
                return

            # Find next modules based on prerequisites and current progress
            available_modules = []

            for module_id in workflow.required_modules:
                if module_id in progress.completed_modules:
                    continue

                module = self.training_content.get(module_id)
                if not module:
                    continue

                # Check if prerequisites are met
                prerequisites_met = all(
                    prereq in progress.completed_modules
                    for prereq in module.prerequisites
                )

                if prerequisites_met:
                    available_modules.append(module_id)

            # Sort by priority and take top 3
            progress.next_recommended_modules = available_modules[:3]

        except Exception as e:
            logger.error(f"Error updating recommendations: {str(e)}")

    async def _check_stage_progression(self, agent_id: str):
        """Check if agent should progress to next onboarding stage."""
        try:
            progress = self.agent_progress[agent_id]
            current_stage = progress.current_stage

            # Define stage progression criteria
            stage_criteria = {
                OnboardingStage.REGISTRATION: lambda p: len(p.completed_modules) >= 1,
                OnboardingStage.SYSTEM_ORIENTATION: lambda p: len(p.completed_modules) >= 3,
                OnboardingStage.ROLE_TRAINING: lambda p: len(p.completed_modules) >= 6,
                OnboardingStage.PRACTICAL_TRAINING: lambda p: len(p.completed_assessments) >= 2,
                OnboardingStage.CERTIFICATION: lambda p: p.completion_percentage >= 90
            }

            criteria_func = stage_criteria.get(current_stage)
            if criteria_func and criteria_func(progress):
                # Progress to next stage
                stages = list(OnboardingStage)
                current_index = stages.index(current_stage)
                if current_index + 1 < len(stages):
                    progress.current_stage = stages[current_index + 1]
                    logger.info(f"Agent {agent_id} progressed to stage {progress.current_stage.value}")

        except Exception as e:
            logger.error(f"Error checking stage progression: {str(e)}")

    async def _analyze_agent_needs(self, agent_id: str) -> Dict[str, Any]:
        """Analyze agent needs and performance to inform training recommendations."""
        try:
            progress = self.agent_progress[agent_id]
            agent_sessions = [s for s in self.training_sessions.values() if s.agent_id == agent_id]

            analysis = {
                "learning_pace": "average",
                "preferred_learning_style": "mixed",
                "struggle_areas": [],
                "strength_areas": [],
                "engagement_level": "high",
                "time_investment": progress.total_training_hours
            }

            # Analyze session performance
            session_scores = [s.score for s in agent_sessions if s.score is not None]
            if session_scores:
                avg_score = sum(session_scores) / len(session_scores)
                analysis["average_performance"] = avg_score

                if avg_score >= 0.85:
                    analysis["learning_pace"] = "fast"
                elif avg_score <= 0.65:
                    analysis["learning_pace"] = "needs_support"

            # Analyze module performance
            module_performance = {}
            for session in agent_sessions:
                if session.module and session.score:
                    module = session.module.value
                    if module not in module_performance:
                        module_performance[module] = []
                    module_performance[module].append(session.score)

            for module, scores in module_performance.items():
                avg_score = sum(scores) / len(scores)
                if avg_score >= 0.80:
                    analysis["strength_areas"].append(module)
                elif avg_score <= 0.65:
                    analysis["struggle_areas"].append(module)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing agent needs: {str(e)}")
            return {"error": str(e)}

    async def _claude_evaluate_assessment(
        self,
        assessment: SkillAssessment,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use Claude to evaluate assessment responses."""
        try:
            from services.claude_agent_service import ClaudeAgentService

            claude_service = ClaudeAgentService()

            evaluation_prompt = f"""
            Evaluate this {assessment.title} assessment response.

            Assessment Criteria:
            {json.dumps(assessment.scoring_criteria, indent=2)}

            Agent Responses:
            {json.dumps(responses, indent=2)}

            Please provide:
            1. Detailed scores for each criterion (0.0-1.0)
            2. Overall score (0.0-1.0)
            3. Specific feedback for improvement
            4. Recommendations for additional training
            5. Pass/fail determination (passing score: {assessment.passing_score})
            """

            # Get Claude's evaluation
            claude_response = await claude_service.chat_with_agent(
                "assessment_evaluator",
                evaluation_prompt
            )

            # Parse Claude's response (simplified)
            # In production, this would use structured prompts
            results = {
                "scores": assessment.scoring_criteria,  # Would parse from Claude
                "overall_score": 0.75,  # Would extract from Claude
                "passed": True,  # Would determine from score
                "feedback": [claude_response.response],
                "recommendations": claude_response.recommendations or []
            }

            return results

        except Exception as e:
            logger.error(f"Error in Claude assessment evaluation: {str(e)}")
            # Fallback to standard evaluation
            return await self._standard_evaluate_assessment(assessment, responses)

    async def _standard_evaluate_assessment(
        self,
        assessment: SkillAssessment,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Standard assessment evaluation without Claude."""
        # Simplified scoring logic
        # In production, this would have more sophisticated evaluation
        total_score = 0.75  # Placeholder
        passed = total_score >= assessment.passing_score

        return {
            "scores": {criterion: 0.75 for criterion in assessment.scoring_criteria},
            "overall_score": total_score,
            "passed": passed,
            "feedback": ["Standard evaluation completed"],
            "recommendations": ["Continue with training modules"]
        }

    def _determine_skill_level(self, score: float) -> SkillLevel:
        """Determine skill level based on assessment score."""
        if score >= 0.90:
            return SkillLevel.EXPERT
        elif score >= 0.80:
            return SkillLevel.PROFICIENT
        elif score >= 0.70:
            return SkillLevel.COMPETENT
        elif score >= 0.60:
            return SkillLevel.DEVELOPING
        else:
            return SkillLevel.BEGINNER

    def _calculate_module_priority(self, agent_id: str, module: TrainingContent) -> str:
        """Calculate priority level for a training module."""
        progress = self.agent_progress.get(agent_id)
        if not progress:
            return "medium"

        # Check if module addresses weak areas
        if module.module.value in progress.weak_areas:
            return "high"

        # Check if module is prerequisite for others
        dependent_modules = [
            m for m in self.training_content.values()
            if module.id in m.prerequisites
        ]
        if dependent_modules:
            return "high"

        return "medium"

    def _create_custom_path(self, required_modules: List[str], focus_areas: List[str]) -> List[str]:
        """Create a custom training path based on focus areas."""
        # Prioritize modules that match focus areas
        prioritized = []
        standard = []

        for module_id in required_modules:
            module = self.training_content.get(module_id)
            if module and any(area.lower() in module.title.lower() or area.lower() in ' '.join(module.tags) for area in focus_areas):
                prioritized.append(module_id)
            else:
                standard.append(module_id)

        return prioritized + standard

    async def _create_welcome_session(self, agent_id: str, workflow: OnboardingWorkflow):
        """Create initial welcome training session."""
        try:
            welcome_session = TrainingSession(
                id=f"welcome_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                module=TrainingModule.TECHNOLOGY_TOOLS,
                content_id="welcome_orientation",
                session_type="orientation",
                start_time=datetime.utcnow(),
                completion_status="scheduled"
            )

            self.training_sessions[welcome_session.id] = welcome_session
            logger.info(f"Created welcome session for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error creating welcome session: {str(e)}")

    async def _initialize_claude_session(self, session: TrainingSession):
        """Initialize a Claude-powered training session."""
        try:
            content = self.training_content.get(session.content_id)
            if not content or content.content_type != "claude_session":
                return

            # Prepare Claude conversation context
            session.claude_interactions = [{
                "timestamp": datetime.utcnow().isoformat(),
                "type": "session_start",
                "content": f"Starting {content.title} training session",
                "learning_objectives": content.learning_objectives
            }]

            logger.info(f"Initialized Claude session {session.id}")

        except Exception as e:
            logger.error(f"Error initializing Claude session: {str(e)}")

    async def _analyze_performance_areas(self, agent_id: str):
        """Analyze performance to identify strong and weak areas."""
        try:
            progress = self.agent_progress[agent_id]
            agent_sessions = [s for s in self.training_sessions.values() if s.agent_id == agent_id]

            # Reset areas
            progress.weak_areas = []
            progress.strong_areas = []

            # Analyze by module
            module_scores = {}
            for session in agent_sessions:
                if session.module and session.score is not None:
                    module = session.module.value
                    if module not in module_scores:
                        module_scores[module] = []
                    module_scores[module].append(session.score)

            for module, scores in module_scores.items():
                avg_score = sum(scores) / len(scores)
                if avg_score >= 0.80:
                    progress.strong_areas.append(module)
                elif avg_score <= 0.65:
                    progress.weak_areas.append(module)

        except Exception as e:
            logger.error(f"Error analyzing performance areas: {str(e)}")


# Global service instance
agent_onboarding_service = AgentOnboardingService()


# Convenience functions for easy import
async def start_agent_onboarding(
    agent_id: str,
    workflow_type: str = "new_agent_onboarding",
    custom_options: Optional[Dict[str, Any]] = None
) -> AgentProgress:
    """Start onboarding process for an agent."""
    return await agent_onboarding_service.start_agent_onboarding(agent_id, workflow_type, custom_options)


async def get_training_plan(agent_id: str) -> Dict[str, Any]:
    """Get personalized training plan for an agent."""
    return await agent_onboarding_service.get_personalized_training_plan(agent_id)


async def conduct_assessment(
    agent_id: str,
    assessment_id: str,
    responses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Conduct a skill assessment for an agent."""
    return await agent_onboarding_service.conduct_skill_assessment(agent_id, assessment_id, responses)


async def assign_agent_mentor(
    mentee_agent_id: str,
    mentor_agent_id: str,
    focus_areas: List[str],
    goals: List[str]
) -> MentorshipAssignment:
    """Assign a mentor to an agent."""
    return await agent_onboarding_service.assign_mentor(mentee_agent_id, mentor_agent_id, focus_areas, goals)