"""
Persona-Orchestrator implementation for dynamic agent generation.

Implements the 3-stage process from docs/PERSONA0.md:
- Stage 0: Task Classification
- Stage 1: Clarification & Task Profiling
- Stage 2: Persona B Generation

This enables dynamic creation of specialized agents based on task requirements.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from utils.logger import get_logger
from utils.orchestrator import PersonaB

# Initialize logger
logger = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================


class TaskType(str, Enum):
    """Task type classification (from PERSONA0.md)."""

    RESEARCH = "RESEARCH"  # Analyze, synthesize, compare, investigate
    CODE = "CODE"  # Build, implement, debug, refactor
    STRATEGY = "STRATEGY"  # Plan, decide, recommend, roadmap
    CREATIVE = "CREATIVE"  # Brainstorm, generate ideas, write, design
    EDUCATIONAL = "EDUCATIONAL"  # Teach, onboard, guide, tutorial
    REAL_TIME = "REAL_TIME"  # Urgent, time-sensitive tasks


class UserLevel(str, Enum):
    """User expertise level."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class DepthPreference(str, Enum):
    """Depth/thoroughness preference."""

    QUICK = "quick"  # 3-5 sources, fast results
    THOROUGH = "thorough"  # 8+ sources, comprehensive
    EXHAUSTIVE = "exhaustive"  # 15+ sources, deep analysis


class TimeSensitivity(str, Enum):
    """Time sensitivity level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TaskClassification:
    """Result from task classification (Stage 0)."""

    task_type: TaskType
    confidence: int  # 0-100
    reasoning: str
    requires_clarification: bool = False


@dataclass
class TaskProfile:
    """Task profile from clarification stage (Stage 1)."""

    task_type: TaskType
    need: str  # 1 sentence
    goal: str  # 1-3 sentences
    context: Dict[str, str] = field(default_factory=dict)  # domain, background
    constraints: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    user_level: UserLevel = UserLevel.INTERMEDIATE
    depth_preference: DepthPreference = DepthPreference.THOROUGH
    time_sensitivity: TimeSensitivity = TimeSensitivity.MEDIUM


# ============================================================================
# Stage 0: Task Classifier
# ============================================================================


class TaskClassifier:
    """
    Classifies tasks into 6 types with confidence scoring.

    Task types:
    - RESEARCH: analyze, synthesize, compare, review, investigate
    - CODE: build, implement, debug, refactor
    - STRATEGY: plan, decide, recommend, roadmap
    - CREATIVE: brainstorm, generate ideas, write, compose
    - EDUCATIONAL: teach, onboard, guide, how-to
    - REAL_TIME: urgent, "quick", "now", latency-sensitive
    """

    # Keyword mappings for each task type
    TASK_KEYWORDS = {
        TaskType.RESEARCH: [
            "analyze",
            "research",
            "investigate",
            "compare",
            "review",
            "study",
            "explore",
            "examine",
            "synthesize",
            "summarize",
            "explain",
        ],
        TaskType.CODE: [
            "build",
            "implement",
            "code",
            "develop",
            "debug",
            "refactor",
            "fix",
            "create function",
            "write code",
            "program",
        ],
        TaskType.STRATEGY: [
            "plan",
            "decide",
            "recommend",
            "roadmap",
            "strategy",
            "proposal",
            "approach",
            "choose",
            "evaluate options",
        ],
        TaskType.CREATIVE: [
            "brainstorm",
            "generate",
            "write",
            "compose",
            "design",
            "create content",
            "draft",
            "ideate",
        ],
        TaskType.EDUCATIONAL: [
            "teach",
            "explain how",
            "tutorial",
            "guide",
            "onboard",
            "how to",
            "learn",
            "understand",
        ],
        TaskType.REAL_TIME: [
            "urgent",
            "now",
            "asap",
            "quick",
            "immediately",
            "fast",
            "real-time",
            "within minutes",
        ],
    }

    def __init__(self) -> None:
        logger.info("TaskClassifier initialized")

    def classify(self, task_description: str) -> TaskClassification:
        """
        Classify task into one of 6 types with confidence score.

        Args:
            task_description: Natural language task description

        Returns:
            TaskClassification with type, confidence, and reasoning
        """
        task_lower = task_description.lower()

        # Calculate match scores for each task type
        scores: Dict[TaskType, int] = {}
        for task_type, keywords in self.TASK_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            scores[task_type] = score

        # Get best match
        best_type = max(scores, key=scores.get)  # type: ignore
        best_score = scores[best_type]

        # Calculate confidence (0-100)
        # More keyword matches = higher confidence
        total_matches = sum(scores.values())
        if total_matches == 0:
            confidence = 50  # Default confidence if no keywords matched
        else:
            confidence = min(100, int((best_score / total_matches) * 100))

        # Boost confidence if multiple keywords for same type matched
        if best_score >= 2:
            confidence = min(100, confidence + 20)

        # Generate reasoning
        matching_keywords = [kw for kw in self.TASK_KEYWORDS[best_type] if kw in task_lower]
        reasoning = f"Detected {best_score} keyword(s) for {best_type.value}"
        if matching_keywords:
            reasoning += f": {', '.join(matching_keywords[:3])}"

        # Require clarification if confidence < 70
        requires_clarification = confidence < 70

        logger.info(f"Task classified as {best_type.value} with {confidence}% confidence")

        return TaskClassification(
            task_type=best_type,
            confidence=confidence,
            reasoning=reasoning,
            requires_clarification=requires_clarification,
        )


# ============================================================================
# Stage 1: Task Profiler
# ============================================================================


class TaskProfiler:
    """
    Builds task profiles through clarification questions.

    Generates task-specific questions and constructs a complete task profile.
    """

    def __init__(self) -> None:
        logger.info("TaskProfiler initialized")

    def build_profile(
        self,
        task: str,
        task_type: TaskType,
        answers: Optional[Dict[str, Any]] = None,
    ) -> TaskProfile:
        """
        Build task profile from task description and optional answers.

        Args:
            task: Task description
            task_type: Classified task type
            answers: Optional dict of answers to clarification questions

        Returns:
            TaskProfile with all required fields
        """
        answers = answers or {}

        # Extract basic profile info
        need = self._extract_need(task)
        goal = self._extract_goal(task)
        context = self._extract_context(task, answers)
        constraints = self._extract_constraints(task, answers)
        success_metrics = self._generate_success_metrics(task_type, answers)

        # Extract preferences
        user_level = self._extract_user_level(answers)
        depth_preference = self._extract_depth_preference(task_type, answers)
        time_sensitivity = self._extract_time_sensitivity(task, answers)

        profile = TaskProfile(
            task_type=task_type,
            need=need,
            goal=goal,
            context=context,
            constraints=constraints,
            success_metrics=success_metrics,
            user_level=user_level,
            depth_preference=depth_preference,
            time_sensitivity=time_sensitivity,
        )

        logger.info(f"Task profile built: {task_type.value} task with {len(success_metrics)} metrics")

        return profile

    def generate_questions(self, task_type: TaskType) -> List[str]:
        """
        Generate clarification questions for task type.

        Args:
            task_type: Type of task

        Returns:
            List of clarification questions
        """
        # Standard questions for all types
        standard = [
            "What is the desired output or deliverable?",
            "Are there any constraints (time, tools, format, scope)?",
            "How will you judge if this is successful?",
        ]

        # Task-specific questions
        specific: Dict[TaskType, List[str]] = {
            TaskType.RESEARCH: [
                "What depth do you need? (quick/thorough/exhaustive)",
                "Do you require citations?",
                "What is your level on this topic? (beginner/intermediate/expert)",
            ],
            TaskType.CODE: [
                "What languages/frameworks should be used?",
                "Is this a prototype or production-grade?",
                "Any testing expectations?",
            ],
            TaskType.STRATEGY: [
                "Who are the key stakeholders?",
                "What is the decision horizon? (days/weeks/months)",
            ],
            TaskType.CREATIVE: [
                "Who is the target audience?",
                "What tone should be used? (formal/casual/technical)",
                "How many options do you want?",
            ],
            TaskType.EDUCATIONAL: [
                "What is your current level?",
                "Preferred style? (concise/step-by-step/with exercises)",
            ],
            TaskType.REAL_TIME: [
                "What is the real time constraint?",
                "What is the minimum useful output under tight time?",
            ],
        }

        questions = standard + specific.get(task_type, [])

        logger.info(f"Generated {len(questions)} clarification questions for {task_type.value}")

        return questions

    def _extract_need(self, task: str) -> str:
        """Extract 1-sentence need statement from task."""
        # Simple extraction: first sentence or first 100 chars
        sentences = task.split(".")
        if sentences:
            return sentences[0].strip() + "."
        return task[:100] + "..." if len(task) > 100 else task

    def _extract_goal(self, task: str) -> str:
        """Extract goal statement from task."""
        # For now, use task description as goal
        # In production, could use NLP to extract goal-oriented sentences
        return task[:300] if len(task) > 300 else task

    def _extract_context(self, task: str, answers: Dict[str, Any]) -> Dict[str, str]:
        """Extract context information."""
        context = {
            "domain": answers.get("domain", "business analytics"),
            "background": answers.get("background", ""),
        }
        return context

    def _extract_constraints(self, task: str, answers: Dict[str, Any]) -> List[str]:
        """Extract constraints from task and answers."""
        constraints = []

        # From answers
        if "time_constraint" in answers:
            constraints.append(f"Time: {answers['time_constraint']}")
        if "tool_constraint" in answers:
            constraints.append(f"Tools: {answers['tool_constraint']}")
        if "format_constraint" in answers:
            constraints.append(f"Format: {answers['format_constraint']}")

        # Default constraints if none specified
        if not constraints:
            constraints = ["Follow existing code patterns", "Type hints required"]

        return constraints

    def _generate_success_metrics(self, task_type: TaskType, answers: Dict[str, Any]) -> List[str]:
        """Generate success metrics based on task type."""
        metrics: Dict[TaskType, List[str]] = {
            TaskType.RESEARCH: [
                "Comprehensive coverage of topic",
                "Clear, actionable insights",
                "Properly cited sources",
            ],
            TaskType.CODE: [
                "Code runs without errors",
                "Passes all tests",
                "Follows style guide",
            ],
            TaskType.STRATEGY: [
                "Clear recommendation with rationale",
                "Trade-offs explicitly stated",
                "Stakeholder alignment",
            ],
            TaskType.CREATIVE: [
                "Meets tone/style requirements",
                "Resonates with target audience",
                "Original and engaging",
            ],
            TaskType.EDUCATIONAL: [
                "Concept clearly explained",
                "Examples provided",
                "User can apply knowledge",
            ],
            TaskType.REAL_TIME: [
                "Delivered within time constraint",
                "Minimum viable output achieved",
                "Actionable immediately",
            ],
        }

        return metrics.get(task_type, ["Task completed successfully"])

    def _extract_user_level(self, answers: Dict[str, Any]) -> UserLevel:
        """Extract user level from answers."""
        level_str = answers.get("user_level", "intermediate").lower()
        for level in UserLevel:
            if level.value in level_str:
                return level
        return UserLevel.INTERMEDIATE

    def _extract_depth_preference(self, task_type: TaskType, answers: Dict[str, Any]) -> DepthPreference:
        """Extract depth preference."""
        depth_str = answers.get("depth", "thorough").lower()
        for depth in DepthPreference:
            if depth.value in depth_str:
                return depth

        # Defaults by task type
        defaults = {
            TaskType.RESEARCH: DepthPreference.THOROUGH,
            TaskType.REAL_TIME: DepthPreference.QUICK,
        }
        return defaults.get(task_type, DepthPreference.THOROUGH)

    def _extract_time_sensitivity(self, task: str, answers: Dict[str, Any]) -> TimeSensitivity:
        """Extract time sensitivity."""
        # Check task description for urgency keywords
        urgent_keywords = ["urgent", "asap", "immediately", "quick", "fast", "now"]
        task_lower = task.lower()

        if any(kw in task_lower for kw in urgent_keywords):
            return TimeSensitivity.HIGH

        # Check answers
        time_str = answers.get("time_sensitivity", "medium").lower()
        for sensitivity in TimeSensitivity:
            if sensitivity.value in time_str:
                return sensitivity

        return TimeSensitivity.MEDIUM


# ============================================================================
# Stage 2: Persona Generator
# ============================================================================


class PersonaGenerator:
    """
    Generates Persona B specifications from task profiles.

    Creates ready-to-use agent personas following PERSONA0.md template.
    """

    def __init__(self) -> None:
        logger.info("PersonaGenerator initialized")

    def generate(self, profile: TaskProfile) -> PersonaB:
        """
        Generate Persona B from task profile.

        Args:
            profile: Completed task profile

        Returns:
            PersonaB specification ready for agent creation
        """
        # Apply technique hints based on task type
        self.apply_technique_hints(profile.task_type)

        # Generate persona components
        role = self._generate_role(profile)
        task_focus = self._generate_task_focus(profile)
        operating_principles = self._generate_operating_principles(profile)
        constraints = self._generate_constraints(profile)
        workflow = self._generate_workflow(profile.task_type)
        style = self._generate_style(profile)
        behavioral_examples = self._generate_behavioral_examples(profile)
        hard_do_dont = self._generate_hard_do_dont(profile)

        persona = PersonaB(
            role=role,
            task_focus=task_focus,
            operating_principles=operating_principles,
            constraints=constraints,
            workflow=workflow,
            style=style,
            behavioral_examples=behavioral_examples,
            hard_do_dont=hard_do_dont,
        )

        logger.info(f"Generated Persona B for {profile.task_type.value} task")

        return persona

    def apply_technique_hints(self, task_type: TaskType) -> Dict[str, str]:
        """
        Apply technique hints based on task type (internal guidance).

        Args:
            task_type: Type of task

        Returns:
            Dict of technique hints
        """
        hints = {
            TaskType.RESEARCH: "Use structured reasoning + cross-checking",
            TaskType.CODE: "Use stepwise reasoning + self-review",
            TaskType.STRATEGY: "Generate options, compare trade-offs, quantify uncertainty",
            TaskType.CREATIVE: "Generate multiple variants, then converge",
            TaskType.EDUCATIONAL: "Scaffold explanations from simple to complex",
            TaskType.REAL_TIME: "Trade depth for speed, focus on minimum viable output",
        }
        return {"technique": hints.get(task_type, "Standard approach")}

    def _generate_role(self, profile: TaskProfile) -> str:
        """Generate role description."""
        domain = profile.context.get("domain", "general topics")
        role_templates = {
            TaskType.RESEARCH: f"Research analyst specializing in {domain}",
            TaskType.CODE: f"Software engineer with expertise in {domain}",
            TaskType.STRATEGY: f"Strategic advisor for {domain}",
            TaskType.CREATIVE: f"Creative specialist in {domain}",
            TaskType.EDUCATIONAL: f"Educational specialist in {domain}",
            TaskType.REAL_TIME: f"Rapid response specialist for {domain}",
        }
        return role_templates.get(profile.task_type, "General-purpose specialist")

    def _generate_task_focus(self, profile: TaskProfile) -> str:
        """Generate task focus description."""
        return f"{profile.need} Success defined as: {', '.join(profile.success_metrics[:2])}"

    def _generate_operating_principles(self, profile: TaskProfile) -> List[str]:
        """Generate operating principles."""
        constraints_str = ", ".join(profile.constraints[:2])
        return [
            "Clarity: Ask high-leverage follow-up questions only when needed",
            "Rigor: Prefer correctness and explicit assumptions over guesswork",
            "Transparency: Make key reasoning steps visible when useful",
            f"Constraints: Never violate: {constraints_str}",
            f"Adaptivity: Adjust depth/pace to {profile.user_level.value} level",
        ]

    def _generate_constraints(self, profile: TaskProfile) -> List[str]:
        """Generate constraints list."""
        constraints = list(profile.constraints)

        # Add depth/time constraints
        if profile.depth_preference == DepthPreference.QUICK:
            constraints.append("Optimize for speed over exhaustiveness")
        elif profile.depth_preference == DepthPreference.EXHAUSTIVE:
            constraints.append("Prioritize depth and comprehensive coverage")

        if profile.time_sensitivity == TimeSensitivity.HIGH:
            constraints.append("Deliver quickly, trade depth for speed")

        return constraints

    def _generate_workflow(self, task_type: TaskType) -> List[str]:
        """Generate workflow steps."""
        # Standard 5-step workflow (from PERSONA0.md)
        return [
            "Intake & Restatement: Restate user's request, ask 1-3 targeted questions if needed",
            "Planning: Draft brief plan (2-6 bullets) aligned with success metrics",
            "Execution: Follow plan step-by-step with concise internal reasoning",
            "Review: Check output matches goal, constraints, and success metrics",
            "Delivery: Present final answer clearly with sections and bullets",
        ]

    def _generate_style(self, profile: TaskProfile) -> Dict[str, str]:
        """Generate style guidelines."""
        return {
            "tone": "Direct, professional, and succinct",
            "explanations": "Prioritize actionable guidance over theory",
            "level": f"Aimed at {profile.user_level.value} practitioner",
            "interaction": "Responsive to follow-up; gracefully handle corrections",
        }

    def _generate_behavioral_examples(self, profile: TaskProfile) -> Dict[str, str]:
        """Generate behavioral examples."""
        return {
            "under_specified": "State assumption, label it, and proceed",
            "conflicting_constraints": "Highlight conflict, propose 1-2 trade-offs",
            "time_tight": "Deliver minimal but accurate, clearly scoped output",
        }

    def _generate_hard_do_dont(self, profile: TaskProfile) -> Dict[str, List[str]]:
        """Generate hard do/don't rules."""
        return {
            "do": [
                "Honor explicit constraints and privacy requirements",
                "Make important assumptions and trade-offs explicit",
                "Keep outputs structured, scannable, and useful",
            ],
            "dont": [
                "Quietly change task type or scope without calling it out",
                "Ignore constraints on depth, time, or format",
                "Overcomplicate simple tasks or answers",
            ],
        }


# ============================================================================
# Main Persona Orchestrator
# ============================================================================


class PersonaOrchestrator:
    """
    Main Persona-Orchestrator interface implementing 3-stage process.

    Stages:
    1. Task Classification
    2. Clarification & Task Profiling
    3. Persona B Generation
    """

    def __init__(self) -> None:
        self.classifier = TaskClassifier()
        self.profiler = TaskProfiler()
        self.generator = PersonaGenerator()
        logger.info("PersonaOrchestrator initialized")

    def run_stage_0(self, task: str) -> TaskClassification:
        """
        Run Stage 0: Task Classification.

        Args:
            task: Natural language task description

        Returns:
            TaskClassification with type and confidence
        """
        logger.info("Running Stage 0: Task Classification")
        return self.classifier.classify(task)

    def run_stage_1(
        self,
        task: str,
        classification: TaskClassification,
        answers: Optional[Dict[str, Any]] = None,
    ) -> TaskProfile:
        """
        Run Stage 1: Clarification & Task Profiling.

        Args:
            task: Task description
            classification: Result from Stage 0
            answers: Optional answers to clarification questions

        Returns:
            TaskProfile with full task specification
        """
        logger.info("Running Stage 1: Clarification & Task Profiling")
        return self.profiler.build_profile(task, classification.task_type, answers)

    def run_stage_2(self, profile: TaskProfile) -> PersonaB:
        """
        Run Stage 2: Persona B Generation.

        Args:
            profile: Task profile from Stage 1

        Returns:
            PersonaB ready for agent creation
        """
        logger.info("Running Stage 2: Persona B Generation")
        return self.generator.generate(profile)

    def execute_full_pipeline(self, task: str, answers: Optional[Dict[str, Any]] = None) -> PersonaB:
        """
        Execute full 3-stage pipeline in one call.

        Args:
            task: Natural language task description
            answers: Optional answers to clarification questions

        Returns:
            PersonaB ready for agent creation
        """
        logger.info("Executing full Persona-Orchestrator pipeline")

        # Stage 0
        classification = self.run_stage_0(task)

        # Stage 1
        profile = self.run_stage_1(task, classification, answers)

        # Stage 2
        persona = self.run_stage_2(profile)

        logger.info("Full pipeline completed successfully")

        return persona
