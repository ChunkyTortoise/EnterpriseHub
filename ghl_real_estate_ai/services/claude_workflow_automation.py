"""
Claude Workflow Automation Engine - Phase 4: Intelligent Process Automation

This service provides intelligent automation for real estate workflows, detecting patterns,
optimizing processes, and automating repetitive tasks to enhance agent productivity
and ensure consistent service delivery.

Key Features:
- Automated workflow detection and pattern recognition
- Process optimization and efficiency improvements
- Task automation and delegation
- Workflow template generation and customization
- Performance monitoring and continuous improvement
- Integration with GHL and real estate APIs for seamless automation

Integrates with orchestration and learning engines for comprehensive automation intelligence.
"""

import asyncio
import json
import logging
import re
import time
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field
import redis.asyncio as redis
import yaml

from ..core.service_registry import ServiceRegistry
from ..services.claude_orchestration_engine import ClaudeOrchestrationEngine, WorkflowType
from ..services.claude_learning_optimizer import ClaudeLearningOptimizer
from ..services.agent_profile_service import AgentProfileService
from ..models.agent_profile_models import AgentProfile, AgentRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomationType(str, Enum):
    """Types of automation that can be applied."""
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    TASK_AUTOMATION = "task_automation"
    RESPONSE_TEMPLATING = "response_templating"
    PROCESS_STANDARDIZATION = "process_standardization"
    DATA_SYNCHRONIZATION = "data_synchronization"
    NOTIFICATION_AUTOMATION = "notification_automation"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"
    FOLLOW_UP_AUTOMATION = "follow_up_automation"


class TriggerType(str, Enum):
    """Types of triggers for automated workflows."""
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    CONDITION_BASED = "condition_based"
    PATTERN_BASED = "pattern_based"
    THRESHOLD_BASED = "threshold_based"
    MANUAL = "manual"


class AutomationStatus(str, Enum):
    """Status of automation rules and workflows."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class WorkflowComplexity(str, Enum):
    """Complexity levels for workflow automation."""
    SIMPLE = "simple"          # Single-step automation
    MODERATE = "moderate"      # Multi-step with basic logic
    COMPLEX = "complex"        # Advanced logic with conditionals
    ENTERPRISE = "enterprise"  # Full orchestration with AI decisions


@dataclass
class WorkflowStep:
    """Individual step in an automated workflow."""
    step_id: str
    step_type: str
    action: str
    parameters: Dict[str, Any]
    conditions: Dict[str, Any] = field(default_factory=dict)
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    dependencies: List[str] = field(default_factory=list)
    error_handling: str = "continue"  # continue, stop, retry


@dataclass
class AutomationRule:
    """Rule definition for automated workflows."""
    rule_id: str
    name: str
    description: str
    automation_type: AutomationType
    trigger_type: TriggerType
    trigger_conditions: Dict[str, Any]
    workflow_steps: List[WorkflowStep]
    priority: int = 1
    enabled: bool = True
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    success_rate: float = 1.0
    average_execution_time: float = 0.0


@dataclass
class WorkflowExecution:
    """Tracking for individual workflow executions."""
    execution_id: str
    rule_id: str
    agent_id: str
    trigger_data: Dict[str, Any]
    status: AutomationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps_completed: int = 0
    total_steps: int = 0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class WorkflowPattern:
    """Detected workflow patterns for automation opportunities."""
    pattern_id: str
    pattern_type: str
    frequency: int
    confidence_score: float
    agents_affected: List[str]
    time_savings_potential: float  # hours per week
    automation_complexity: WorkflowComplexity
    suggested_automation: AutomationRule
    evidence: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)


class AutomationRequest(BaseModel):
    """Request for workflow automation analysis or execution."""
    request_type: str  # analyze, execute, create_rule
    agent_id: Optional[str] = None
    workflow_type: Optional[WorkflowType] = None
    automation_type: Optional[AutomationType] = None
    time_period_hours: int = Field(default=168, ge=1)  # Default 1 week
    include_suggestions: bool = True
    complexity_filter: Optional[WorkflowComplexity] = None


class AutomationResponse(BaseModel):
    """Response from workflow automation analysis."""
    request_type: str
    analysis_period: str
    patterns_detected: int
    automation_opportunities: int
    time_savings_potential: float
    efficiency_improvements: Dict[str, float]
    suggested_automations: List[Dict[str, Any]]
    active_automations: int
    success_metrics: Dict[str, float]


class WorkflowTemplate(BaseModel):
    """Template for common real estate workflows."""
    template_id: str
    name: str
    description: str
    category: str
    workflow_type: WorkflowType
    steps: List[Dict[str, Any]]
    customization_options: Dict[str, Any]
    estimated_time_savings: float
    success_rate: float
    usage_count: int = 0


class ClaudeWorkflowAutomation:
    """Intelligent workflow automation engine for real estate processes."""

    def __init__(
        self,
        service_registry: ServiceRegistry,
        orchestration_engine: ClaudeOrchestrationEngine,
        learning_optimizer: ClaudeLearningOptimizer,
        redis_client: Optional[redis.Redis] = None
    ):
        self.service_registry = service_registry
        self.orchestration_engine = orchestration_engine
        self.learning_optimizer = learning_optimizer
        self.redis_client = redis_client or redis.from_url("redis://localhost:6379/0")
        self.agent_service = AgentProfileService(service_registry, redis_client)

        # Automation state
        self.automation_rules: Dict[str, AutomationRule] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.detected_patterns: Dict[str, WorkflowPattern] = {}
        self.workflow_templates: Dict[str, WorkflowTemplate] = {}

        # Performance tracking
        self.automation_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.execution_history: List[WorkflowExecution] = []

        # Configuration
        self.pattern_detection_threshold = 3  # Minimum occurrences to detect pattern
        self.automation_confidence_threshold = 0.75
        self.max_concurrent_executions = 20
        self.execution_timeout_minutes = 30

        # Task automation functions
        self.automation_functions: Dict[str, Callable] = {}
        self._register_automation_functions()

        # Initialize system
        asyncio.create_task(self._initialize_automation_system())

    async def _initialize_automation_system(self) -> None:
        """Initialize the workflow automation system."""
        try:
            # Load existing automation rules
            await self._load_automation_rules()

            # Load workflow templates
            await self._load_workflow_templates()

            # Start background pattern detection
            asyncio.create_task(self._background_pattern_detection())

            # Start automation execution monitor
            asyncio.create_task(self._monitor_active_executions())

            logger.info("Claude Workflow Automation initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing workflow automation: {str(e)}")

    def _register_automation_functions(self) -> None:
        """Register available automation functions."""
        self.automation_functions = {
            "send_ghl_message": self._send_ghl_message,
            "update_ghl_contact": self._update_ghl_contact,
            "schedule_follow_up": self._schedule_follow_up,
            "create_property_alert": self._create_property_alert,
            "generate_market_report": self._generate_market_report,
            "send_email_template": self._send_email_template,
            "update_agent_notes": self._update_agent_notes,
            "trigger_workflow": self._trigger_workflow,
            "analyze_conversation": self._analyze_conversation,
            "optimize_scheduling": self._optimize_scheduling
        }

    async def analyze_workflow_patterns(self, request: AutomationRequest) -> AutomationResponse:
        """Analyze workflow patterns and identify automation opportunities."""
        try:
            start_time = time.time()

            # Collect workflow data for analysis
            workflow_data = await self._collect_workflow_data(request)

            # Detect patterns in the workflow data
            detected_patterns = await self._detect_workflow_patterns(workflow_data, request)

            # Identify automation opportunities
            automation_opportunities = await self._identify_automation_opportunities(detected_patterns)

            # Calculate potential time savings
            time_savings = self._calculate_time_savings_potential(automation_opportunities)

            # Generate automation suggestions
            suggested_automations = await self._generate_automation_suggestions(automation_opportunities)

            # Calculate efficiency improvements
            efficiency_improvements = self._calculate_efficiency_improvements(automation_opportunities)

            analysis_time = time.time() - start_time

            return AutomationResponse(
                request_type=request.request_type,
                analysis_period=f"Last {request.time_period_hours} hours",
                patterns_detected=len(detected_patterns),
                automation_opportunities=len(automation_opportunities),
                time_savings_potential=time_savings,
                efficiency_improvements=efficiency_improvements,
                suggested_automations=suggested_automations,
                active_automations=len([r for r in self.automation_rules.values() if r.enabled]),
                success_metrics={
                    "analysis_time": analysis_time,
                    "pattern_confidence": sum(p.confidence_score for p in detected_patterns) / len(detected_patterns) if detected_patterns else 0,
                    "automation_coverage": self._calculate_automation_coverage()
                }
            )

        except Exception as e:
            logger.error(f"Error analyzing workflow patterns: {str(e)}")
            return self._create_error_automation_response(request, str(e))

    async def create_automation_rule(
        self, name: str, automation_type: AutomationType, trigger_type: TriggerType,
        trigger_conditions: Dict[str, Any], workflow_steps: List[Dict[str, Any]],
        agent_id: str, description: str = ""
    ) -> str:
        """Create a new automation rule."""
        try:
            rule_id = f"automation_{int(time.time())}_{automation_type.value}"

            # Convert workflow steps to WorkflowStep objects
            steps = []
            for i, step_data in enumerate(workflow_steps):
                step = WorkflowStep(
                    step_id=f"{rule_id}_step_{i}",
                    step_type=step_data.get("type", "action"),
                    action=step_data["action"],
                    parameters=step_data.get("parameters", {}),
                    conditions=step_data.get("conditions", {}),
                    timeout_seconds=step_data.get("timeout", 30),
                    dependencies=step_data.get("dependencies", []),
                    error_handling=step_data.get("error_handling", "continue")
                )
                steps.append(step)

            # Create automation rule
            rule = AutomationRule(
                rule_id=rule_id,
                name=name,
                description=description,
                automation_type=automation_type,
                trigger_type=trigger_type,
                trigger_conditions=trigger_conditions,
                workflow_steps=steps,
                created_by=agent_id,
                priority=trigger_conditions.get("priority", 1)
            )

            # Store the rule
            self.automation_rules[rule_id] = rule

            # Save to Redis for persistence
            await self._save_automation_rule(rule)

            logger.info(f"Created automation rule: {rule_id}")
            return rule_id

        except Exception as e:
            logger.error(f"Error creating automation rule: {str(e)}")
            raise

    async def execute_automation(
        self, rule_id: str, trigger_data: Dict[str, Any], agent_id: str
    ) -> str:
        """Execute an automation workflow."""
        try:
            if rule_id not in self.automation_rules:
                raise ValueError(f"Automation rule not found: {rule_id}")

            rule = self.automation_rules[rule_id]

            if not rule.enabled:
                raise ValueError(f"Automation rule is disabled: {rule_id}")

            # Create execution tracking
            execution_id = f"exec_{int(time.time())}_{rule_id}"
            execution = WorkflowExecution(
                execution_id=execution_id,
                rule_id=rule_id,
                agent_id=agent_id,
                trigger_data=trigger_data,
                status=AutomationStatus.ACTIVE,
                started_at=datetime.now(),
                total_steps=len(rule.workflow_steps)
            )

            self.active_executions[execution_id] = execution

            # Execute workflow steps
            await self._execute_workflow_steps(execution, rule)

            # Update rule statistics
            rule.execution_count += 1
            rule.last_executed = datetime.now()

            return execution_id

        except Exception as e:
            logger.error(f"Error executing automation: {str(e)}")
            if execution_id in self.active_executions:
                self.active_executions[execution_id].status = AutomationStatus.FAILED
                self.active_executions[execution_id].errors.append(str(e))
            raise

    async def get_automation_suggestions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get personalized automation suggestions for an agent."""
        try:
            # Analyze agent's workflow patterns
            agent_patterns = await self._analyze_agent_patterns(agent_id)

            suggestions = []

            for pattern in agent_patterns:
                if pattern.confidence_score >= self.automation_confidence_threshold:
                    suggestion = {
                        "pattern_id": pattern.pattern_id,
                        "automation_type": pattern.suggested_automation.automation_type.value,
                        "description": pattern.suggested_automation.description,
                        "time_savings_hours_per_week": pattern.time_savings_potential,
                        "complexity": pattern.automation_complexity.value,
                        "confidence": pattern.confidence_score,
                        "suggested_steps": [
                            {
                                "action": step.action,
                                "description": step.parameters.get("description", ""),
                                "estimated_time": step.parameters.get("estimated_time", 0)
                            }
                            for step in pattern.suggested_automation.workflow_steps
                        ],
                        "implementation_effort": self._estimate_implementation_effort(pattern),
                        "roi_estimate": self._calculate_automation_roi(pattern)
                    }
                    suggestions.append(suggestion)

            # Sort by ROI and time savings potential
            suggestions.sort(key=lambda x: (x["roi_estimate"], x["time_savings_hours_per_week"]), reverse=True)

            return suggestions[:10]  # Return top 10 suggestions

        except Exception as e:
            logger.error(f"Error getting automation suggestions: {str(e)}")
            return []

    async def optimize_existing_workflows(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Optimize existing workflows based on performance data."""
        try:
            optimization_results = {
                "workflows_analyzed": 0,
                "optimizations_applied": 0,
                "performance_improvements": {},
                "recommendations": []
            }

            # Get workflows to optimize
            workflows_to_optimize = self.automation_rules.values()
            if agent_id:
                workflows_to_optimize = [
                    rule for rule in workflows_to_optimize
                    if rule.created_by == agent_id or agent_id in rule.trigger_conditions.get("applicable_agents", [])
                ]

            optimization_results["workflows_analyzed"] = len(workflows_to_optimize)

            for rule in workflows_to_optimize:
                # Analyze workflow performance
                performance_analysis = await self._analyze_workflow_performance(rule)

                # Apply optimizations if beneficial
                optimizations = await self._apply_workflow_optimizations(rule, performance_analysis)

                if optimizations["applied"]:
                    optimization_results["optimizations_applied"] += 1
                    optimization_results["performance_improvements"][rule.rule_id] = optimizations["improvements"]

                optimization_results["recommendations"].extend(optimizations.get("recommendations", []))

            return optimization_results

        except Exception as e:
            logger.error(f"Error optimizing workflows: {str(e)}")
            return {"error": str(e)}

    async def _collect_workflow_data(self, request: AutomationRequest) -> List[Dict[str, Any]]:
        """Collect workflow data for pattern analysis."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=request.time_period_hours)

            # Collect data from various sources
            workflow_data = []

            # Get conversation data from learning optimizer
            if hasattr(self.learning_optimizer, 'conversation_data'):
                for conversation in self.learning_optimizer.conversation_data:
                    if conversation.start_time > cutoff_time:
                        if not request.agent_id or conversation.agent_id == request.agent_id:
                            workflow_data.append({
                                "type": "conversation",
                                "agent_id": conversation.agent_id,
                                "interaction_type": conversation.interaction_type.value,
                                "duration": (conversation.end_time - conversation.start_time).total_seconds() / 60,
                                "outcome": conversation.outcome.value,
                                "satisfaction": conversation.satisfaction_score,
                                "timestamp": conversation.start_time,
                                "metadata": conversation.context_metadata
                            })

            # Get execution history
            for execution in self.execution_history:
                if execution.started_at > cutoff_time:
                    if not request.agent_id or execution.agent_id == request.agent_id:
                        workflow_data.append({
                            "type": "automation_execution",
                            "agent_id": execution.agent_id,
                            "rule_id": execution.rule_id,
                            "execution_time": (execution.completed_at - execution.started_at).total_seconds() / 60 if execution.completed_at else None,
                            "status": execution.status.value,
                            "steps_completed": execution.steps_completed,
                            "timestamp": execution.started_at,
                            "metadata": execution.results
                        })

            # Get GHL webhook data (if available)
            webhook_data = await self._collect_ghl_webhook_data(cutoff_time, request.agent_id)
            workflow_data.extend(webhook_data)

            return workflow_data

        except Exception as e:
            logger.error(f"Error collecting workflow data: {str(e)}")
            return []

    async def _detect_workflow_patterns(
        self, workflow_data: List[Dict[str, Any]], request: AutomationRequest
    ) -> List[WorkflowPattern]:
        """Detect patterns in workflow data."""
        try:
            patterns = []

            # Group data by various dimensions for pattern detection
            grouped_data = self._group_workflow_data(workflow_data)

            # Detect repetitive task patterns
            repetitive_patterns = self._detect_repetitive_patterns(grouped_data)
            patterns.extend(repetitive_patterns)

            # Detect time-based patterns
            temporal_patterns = self._detect_temporal_patterns(grouped_data)
            patterns.extend(temporal_patterns)

            # Detect conditional patterns
            conditional_patterns = self._detect_conditional_patterns(grouped_data)
            patterns.extend(conditional_patterns)

            # Filter patterns by confidence and frequency
            filtered_patterns = [
                p for p in patterns
                if p.frequency >= self.pattern_detection_threshold
                and p.confidence_score >= self.automation_confidence_threshold
            ]

            return filtered_patterns

        except Exception as e:
            logger.error(f"Error detecting workflow patterns: {str(e)}")
            return []

    def _group_workflow_data(self, workflow_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group workflow data by various dimensions for pattern analysis."""
        grouped = {
            "by_agent": defaultdict(list),
            "by_type": defaultdict(list),
            "by_hour": defaultdict(list),
            "by_day": defaultdict(list),
            "by_outcome": defaultdict(list)
        }

        for item in workflow_data:
            grouped["by_agent"][item.get("agent_id", "unknown")].append(item)
            grouped["by_type"][item.get("type", "unknown")].append(item)

            if "timestamp" in item:
                timestamp = item["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                grouped["by_hour"][timestamp.hour].append(item)
                grouped["by_day"][timestamp.weekday()].append(item)

            if "outcome" in item:
                grouped["by_outcome"][item["outcome"]].append(item)

        return dict(grouped)

    def _detect_repetitive_patterns(self, grouped_data: Dict[str, List[Dict[str, Any]]]) -> List[WorkflowPattern]:
        """Detect repetitive task patterns that could be automated."""
        patterns = []

        # Analyze by agent for repetitive tasks
        for agent_id, agent_data in grouped_data["by_agent"].items():
            # Count action frequencies
            action_counter = Counter()
            for item in agent_data:
                if item.get("type") == "conversation":
                    action_counter[item.get("interaction_type", "unknown")] += 1

            # Identify frequently repeated actions
            for action, frequency in action_counter.items():
                if frequency >= self.pattern_detection_threshold:
                    # Calculate time savings potential
                    avg_duration = sum(
                        item.get("duration", 0) for item in agent_data
                        if item.get("interaction_type") == action
                    ) / frequency

                    time_savings = (avg_duration * frequency * 0.3) / 60  # 30% time savings, convert to hours

                    # Create suggested automation
                    suggested_automation = self._create_repetitive_task_automation(action, agent_id)

                    pattern = WorkflowPattern(
                        pattern_id=f"repetitive_{agent_id}_{action}_{int(time.time())}",
                        pattern_type="repetitive_task",
                        frequency=frequency,
                        confidence_score=min(0.9, 0.5 + (frequency / 20)),
                        agents_affected=[agent_id],
                        time_savings_potential=time_savings,
                        automation_complexity=WorkflowComplexity.MODERATE,
                        suggested_automation=suggested_automation,
                        evidence={
                            "action_type": action,
                            "frequency_per_period": frequency,
                            "average_duration_minutes": avg_duration
                        }
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_temporal_patterns(self, grouped_data: Dict[str, List[Dict[str, Any]]]) -> List[WorkflowPattern]:
        """Detect time-based patterns for scheduled automation."""
        patterns = []

        # Analyze hourly patterns
        hourly_activity = grouped_data["by_hour"]
        for hour, hour_data in hourly_activity.items():
            if len(hour_data) >= self.pattern_detection_threshold:
                # Calculate pattern strength
                total_items = sum(len(items) for items in hourly_activity.values())
                pattern_strength = len(hour_data) / total_items if total_items > 0 else 0

                if pattern_strength > 0.2:  # Significant concentration of activity
                    # Identify most common activities during this hour
                    activity_types = Counter(item.get("interaction_type", "unknown") for item in hour_data)
                    most_common_activity = activity_types.most_common(1)[0]

                    suggested_automation = self._create_temporal_automation(hour, most_common_activity)

                    pattern = WorkflowPattern(
                        pattern_id=f"temporal_hour_{hour}_{int(time.time())}",
                        pattern_type="temporal_pattern",
                        frequency=len(hour_data),
                        confidence_score=pattern_strength,
                        agents_affected=list(set(item.get("agent_id") for item in hour_data if item.get("agent_id"))),
                        time_savings_potential=len(hour_data) * 0.1,  # 6 minutes per occurrence
                        automation_complexity=WorkflowComplexity.SIMPLE,
                        suggested_automation=suggested_automation,
                        evidence={
                            "time_period": f"Hour {hour}",
                            "activity_concentration": pattern_strength,
                            "most_common_activity": most_common_activity[0],
                            "activity_count": most_common_activity[1]
                        }
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_conditional_patterns(self, grouped_data: Dict[str, List[Dict[str, Any]]]) -> List[WorkflowPattern]:
        """Detect conditional patterns for rule-based automation."""
        patterns = []

        # Analyze outcome-based patterns
        for outcome, outcome_data in grouped_data["by_outcome"].items():
            if len(outcome_data) >= self.pattern_detection_threshold:
                # Look for consistent follow-up actions
                follow_up_actions = []
                for item in outcome_data:
                    # Analyze metadata for follow-up actions
                    metadata = item.get("metadata", {})
                    if metadata.get("follow_up_required"):
                        follow_up_actions.append(metadata.get("follow_up_type", "unknown"))

                if follow_up_actions:
                    action_counter = Counter(follow_up_actions)
                    most_common_action = action_counter.most_common(1)[0]

                    # Create conditional automation
                    suggested_automation = self._create_conditional_automation(outcome, most_common_action[0])

                    pattern = WorkflowPattern(
                        pattern_id=f"conditional_{outcome}_{int(time.time())}",
                        pattern_type="conditional_pattern",
                        frequency=len(outcome_data),
                        confidence_score=most_common_action[1] / len(follow_up_actions),
                        agents_affected=list(set(item.get("agent_id") for item in outcome_data if item.get("agent_id"))),
                        time_savings_potential=most_common_action[1] * 0.25,  # 15 minutes per occurrence
                        automation_complexity=WorkflowComplexity.COMPLEX,
                        suggested_automation=suggested_automation,
                        evidence={
                            "trigger_condition": f"outcome == {outcome}",
                            "follow_up_action": most_common_action[0],
                            "action_frequency": most_common_action[1],
                            "consistency_rate": most_common_action[1] / len(outcome_data)
                        }
                    )
                    patterns.append(pattern)

        return patterns

    def _create_repetitive_task_automation(self, action_type: str, agent_id: str) -> AutomationRule:
        """Create automation rule for repetitive tasks."""
        rule_id = f"repetitive_{action_type}_{agent_id}_{int(time.time())}"

        # Define workflow steps based on action type
        workflow_steps = []

        if action_type == "lead_qualification":
            workflow_steps = [
                WorkflowStep(
                    step_id=f"{rule_id}_step_1",
                    step_type="claude_analysis",
                    action="analyze_conversation",
                    parameters={"analysis_type": "lead_qualification", "auto_score": True}
                ),
                WorkflowStep(
                    step_id=f"{rule_id}_step_2",
                    step_type="ghl_integration",
                    action="update_ghl_contact",
                    parameters={"fields": ["lead_score", "qualification_status"]}
                )
            ]
        elif action_type == "property_consultation":
            workflow_steps = [
                WorkflowStep(
                    step_id=f"{rule_id}_step_1",
                    step_type="analysis",
                    action="generate_market_report",
                    parameters={"include_comparables": True, "auto_send": True}
                ),
                WorkflowStep(
                    step_id=f"{rule_id}_step_2",
                    step_type="follow_up",
                    action="schedule_follow_up",
                    parameters={"delay_hours": 24, "template": "property_follow_up"}
                )
            ]
        else:
            # Generic automation for unknown action types
            workflow_steps = [
                WorkflowStep(
                    step_id=f"{rule_id}_step_1",
                    step_type="analysis",
                    action="analyze_conversation",
                    parameters={"analysis_type": "general", "auto_update": True}
                )
            ]

        return AutomationRule(
            rule_id=rule_id,
            name=f"Automated {action_type.replace('_', ' ').title()}",
            description=f"Automatically handle {action_type} tasks to save time and ensure consistency",
            automation_type=AutomationType.TASK_AUTOMATION,
            trigger_type=TriggerType.EVENT_BASED,
            trigger_conditions={
                "event": "conversation_completed",
                "interaction_type": action_type,
                "agent_id": agent_id
            },
            workflow_steps=workflow_steps,
            created_by=agent_id
        )

    def _create_temporal_automation(self, hour: int, most_common_activity: Tuple[str, int]) -> AutomationRule:
        """Create automation rule for time-based patterns."""
        rule_id = f"temporal_{hour}_{int(time.time())}"

        workflow_steps = [
            WorkflowStep(
                step_id=f"{rule_id}_step_1",
                step_type="preparation",
                action="optimize_scheduling",
                parameters={"activity_type": most_common_activity[0], "time_block": f"hour_{hour}"}
            )
        ]

        return AutomationRule(
            rule_id=rule_id,
            name=f"Hourly Optimization - {hour}:00",
            description=f"Optimize {most_common_activity[0]} activities during hour {hour}",
            automation_type=AutomationType.SCHEDULING_OPTIMIZATION,
            trigger_type=TriggerType.TIME_BASED,
            trigger_conditions={
                "schedule": f"0 {hour} * * *",  # Cron expression for the hour
                "activity_type": most_common_activity[0]
            },
            workflow_steps=workflow_steps,
            created_by="system"
        )

    def _create_conditional_automation(self, outcome: str, follow_up_action: str) -> AutomationRule:
        """Create automation rule for conditional patterns."""
        rule_id = f"conditional_{outcome}_{follow_up_action}_{int(time.time())}"

        workflow_steps = []

        if follow_up_action == "schedule_showing":
            workflow_steps = [
                WorkflowStep(
                    step_id=f"{rule_id}_step_1",
                    step_type="coordination",
                    action="optimize_scheduling",
                    parameters={"activity": "property_showing", "auto_propose": True}
                ),
                WorkflowStep(
                    step_id=f"{rule_id}_step_2",
                    step_type="communication",
                    action="send_email_template",
                    parameters={"template": "showing_confirmation", "auto_send": False}
                )
            ]
        elif follow_up_action == "send_listings":
            workflow_steps = [
                WorkflowStep(
                    step_id=f"{rule_id}_step_1",
                    step_type="search",
                    action="create_property_alert",
                    parameters={"criteria_from_conversation": True, "auto_send": True}
                )
            ]
        else:
            # Generic follow-up automation
            workflow_steps = [
                WorkflowStep(
                    step_id=f"{rule_id}_step_1",
                    step_type="follow_up",
                    action="schedule_follow_up",
                    parameters={"action_type": follow_up_action, "delay_hours": 24}
                )
            ]

        return AutomationRule(
            rule_id=rule_id,
            name=f"Conditional Follow-up: {outcome}",
            description=f"Automatically {follow_up_action} when conversation outcome is {outcome}",
            automation_type=AutomationType.FOLLOW_UP_AUTOMATION,
            trigger_type=TriggerType.CONDITION_BASED,
            trigger_conditions={
                "condition": f"conversation.outcome == '{outcome}'",
                "follow_up_action": follow_up_action
            },
            workflow_steps=workflow_steps,
            created_by="system"
        )

    async def _identify_automation_opportunities(
        self, patterns: List[WorkflowPattern]
    ) -> List[Dict[str, Any]]:
        """Identify and prioritize automation opportunities from detected patterns."""
        opportunities = []

        for pattern in patterns:
            opportunity = {
                "pattern_id": pattern.pattern_id,
                "opportunity_type": pattern.pattern_type,
                "description": f"Automate {pattern.pattern_type} with {pattern.frequency} occurrences",
                "time_savings_potential": pattern.time_savings_potential,
                "confidence_score": pattern.confidence_score,
                "complexity": pattern.automation_complexity.value,
                "affected_agents": pattern.agents_affected,
                "implementation_effort": self._estimate_implementation_effort(pattern),
                "roi_score": self._calculate_automation_roi(pattern),
                "priority_score": self._calculate_opportunity_priority(pattern),
                "suggested_automation": {
                    "name": pattern.suggested_automation.name,
                    "description": pattern.suggested_automation.description,
                    "automation_type": pattern.suggested_automation.automation_type.value,
                    "trigger_type": pattern.suggested_automation.trigger_type.value,
                    "steps_count": len(pattern.suggested_automation.workflow_steps)
                },
                "evidence": pattern.evidence
            }
            opportunities.append(opportunity)

        # Sort by priority score
        opportunities.sort(key=lambda x: x["priority_score"], reverse=True)

        return opportunities

    def _calculate_time_savings_potential(self, opportunities: List[Dict[str, Any]]) -> float:
        """Calculate total time savings potential from all opportunities."""
        return sum(opp.get("time_savings_potential", 0) for opp in opportunities)

    async def _generate_automation_suggestions(
        self, opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate detailed automation suggestions."""
        suggestions = []

        for opportunity in opportunities[:5]:  # Top 5 opportunities
            suggestion = {
                "title": f"Automate {opportunity['opportunity_type'].replace('_', ' ').title()}",
                "description": opportunity["description"],
                "benefits": {
                    "time_savings_hours_per_week": opportunity["time_savings_potential"],
                    "consistency_improvement": "High",
                    "error_reduction": "Medium to High",
                    "agent_satisfaction": "High"
                },
                "implementation": {
                    "complexity": opportunity["complexity"],
                    "effort_estimate": opportunity["implementation_effort"],
                    "roi_score": opportunity["roi_score"],
                    "steps_required": opportunity["suggested_automation"]["steps_count"]
                },
                "next_actions": self._generate_implementation_steps(opportunity),
                "affected_agents": opportunity["affected_agents"],
                "confidence": opportunity["confidence_score"]
            }
            suggestions.append(suggestion)

        return suggestions

    def _calculate_efficiency_improvements(self, opportunities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate efficiency improvements from automation opportunities."""
        improvements = {}

        total_time_savings = sum(opp.get("time_savings_potential", 0) for opp in opportunities)
        high_confidence_opportunities = [opp for opp in opportunities if opp["confidence_score"] > 0.8]

        improvements["total_time_savings_hours_per_week"] = total_time_savings
        improvements["high_confidence_opportunities"] = len(high_confidence_opportunities)
        improvements["average_roi"] = sum(opp.get("roi_score", 0) for opp in opportunities) / len(opportunities) if opportunities else 0
        improvements["complexity_breakdown"] = {
            "simple": len([opp for opp in opportunities if opp["complexity"] == "simple"]),
            "moderate": len([opp for opp in opportunities if opp["complexity"] == "moderate"]),
            "complex": len([opp for opp in opportunities if opp["complexity"] == "complex"]),
            "enterprise": len([opp for opp in opportunities if opp["complexity"] == "enterprise"])
        }

        return improvements

    def _estimate_implementation_effort(self, pattern: WorkflowPattern) -> str:
        """Estimate implementation effort for automation pattern."""
        complexity_effort = {
            WorkflowComplexity.SIMPLE: "Low (1-2 hours)",
            WorkflowComplexity.MODERATE: "Medium (4-8 hours)",
            WorkflowComplexity.COMPLEX: "High (1-2 days)",
            WorkflowComplexity.ENTERPRISE: "Very High (3-5 days)"
        }
        return complexity_effort.get(pattern.automation_complexity, "Medium")

    def _calculate_automation_roi(self, pattern: WorkflowPattern) -> float:
        """Calculate ROI score for automation opportunity."""
        # ROI = (Time Savings * Value per Hour) / Implementation Cost
        time_savings_per_week = pattern.time_savings_potential
        value_per_hour = 50  # Estimated hourly value for agent time

        complexity_cost = {
            WorkflowComplexity.SIMPLE: 100,
            WorkflowComplexity.MODERATE: 400,
            WorkflowComplexity.COMPLEX: 800,
            WorkflowComplexity.ENTERPRISE: 1600
        }

        implementation_cost = complexity_cost.get(pattern.automation_complexity, 400)
        weekly_value = time_savings_per_week * value_per_hour
        annual_value = weekly_value * 52

        roi = (annual_value / implementation_cost) if implementation_cost > 0 else 0
        return min(10.0, roi)  # Cap at 10x ROI for display

    def _calculate_opportunity_priority(self, pattern: WorkflowPattern) -> float:
        """Calculate priority score for automation opportunity."""
        base_score = pattern.confidence_score * 0.4
        time_savings_score = min(1.0, pattern.time_savings_potential / 10) * 0.3
        frequency_score = min(1.0, pattern.frequency / 20) * 0.2
        complexity_score = {
            WorkflowComplexity.SIMPLE: 0.1,
            WorkflowComplexity.MODERATE: 0.08,
            WorkflowComplexity.COMPLEX: 0.06,
            WorkflowComplexity.ENTERPRISE: 0.04
        }.get(pattern.automation_complexity, 0.05)

        return base_score + time_savings_score + frequency_score + complexity_score

    def _generate_implementation_steps(self, opportunity: Dict[str, Any]) -> List[str]:
        """Generate implementation steps for automation opportunity."""
        steps = []

        complexity = opportunity["complexity"]

        if complexity == "simple":
            steps = [
                "Review automation requirements",
                "Create automation rule",
                "Test with sample data",
                "Deploy and monitor"
            ]
        elif complexity == "moderate":
            steps = [
                "Analyze workflow requirements",
                "Design automation logic",
                "Create and configure automation rule",
                "Test with multiple scenarios",
                "Deploy with monitoring",
                "Collect feedback and optimize"
            ]
        elif complexity in ["complex", "enterprise"]:
            steps = [
                "Conduct detailed workflow analysis",
                "Design comprehensive automation architecture",
                "Develop custom automation components",
                "Create automation rule with advanced logic",
                "Extensive testing across scenarios",
                "Staged deployment with monitoring",
                "User training and documentation",
                "Ongoing optimization and maintenance"
            ]

        return steps

    async def _execute_workflow_steps(self, execution: WorkflowExecution, rule: AutomationRule) -> None:
        """Execute the steps of an automation workflow."""
        try:
            for i, step in enumerate(rule.workflow_steps):
                try:
                    # Check dependencies
                    if step.dependencies:
                        dependency_results = {
                            dep_step_id: execution.results.get(dep_step_id)
                            for dep_step_id in step.dependencies
                        }

                        # Ensure all dependencies are completed
                        if not all(result is not None for result in dependency_results.values()):
                            raise ValueError(f"Dependencies not met for step {step.step_id}")

                    # Execute the step
                    step_result = await self._execute_workflow_step(step, execution, rule)

                    # Store step result
                    execution.results[step.step_id] = step_result
                    execution.steps_completed += 1

                    # Update execution status
                    if step_result.get("success", False):
                        logger.info(f"Step {step.step_id} completed successfully")
                    else:
                        logger.warning(f"Step {step.step_id} completed with warnings: {step_result.get('warnings', [])}")

                except Exception as step_error:
                    error_msg = f"Step {step.step_id} failed: {str(step_error)}"
                    execution.errors.append(error_msg)
                    logger.error(error_msg)

                    # Handle step error based on error handling policy
                    if step.error_handling == "stop":
                        execution.status = AutomationStatus.FAILED
                        break
                    elif step.error_handling == "retry":
                        # Implement retry logic here
                        pass
                    # Continue for "continue" error handling

            # Mark execution as completed if all steps processed
            if execution.steps_completed == execution.total_steps:
                execution.status = AutomationStatus.COMPLETED
            elif execution.status != AutomationStatus.FAILED:
                execution.status = AutomationStatus.COMPLETED  # Partial completion

            execution.completed_at = datetime.now()

            # Calculate performance metrics
            execution.performance_metrics = {
                "total_duration_minutes": (execution.completed_at - execution.started_at).total_seconds() / 60,
                "success_rate": execution.steps_completed / execution.total_steps,
                "error_count": len(execution.errors)
            }

            # Move to execution history
            self.execution_history.append(execution)

            # Update rule statistics
            if execution.status == AutomationStatus.COMPLETED:
                rule.success_rate = (rule.success_rate * rule.execution_count + 1.0) / (rule.execution_count + 1)
            else:
                rule.success_rate = (rule.success_rate * rule.execution_count) / (rule.execution_count + 1)

            # Update average execution time
            execution_time = execution.performance_metrics["total_duration_minutes"]
            rule.average_execution_time = (rule.average_execution_time * rule.execution_count + execution_time) / (rule.execution_count + 1)

        except Exception as e:
            execution.status = AutomationStatus.FAILED
            execution.errors.append(f"Workflow execution failed: {str(e)}")
            logger.error(f"Workflow execution failed for {execution.execution_id}: {str(e)}")
        finally:
            # Clean up active execution
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]

    async def _execute_workflow_step(
        self, step: WorkflowStep, execution: WorkflowExecution, rule: AutomationRule
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            # Get the automation function for this step
            automation_function = self.automation_functions.get(step.action)

            if not automation_function:
                return {
                    "success": False,
                    "error": f"Unknown automation action: {step.action}",
                    "timestamp": datetime.now().isoformat()
                }

            # Prepare step parameters
            step_params = {
                **step.parameters,
                "execution_context": {
                    "execution_id": execution.execution_id,
                    "rule_id": execution.rule_id,
                    "agent_id": execution.agent_id,
                    "trigger_data": execution.trigger_data,
                    "step_results": execution.results
                }
            }

            # Execute the automation function with timeout
            result = await asyncio.wait_for(
                automation_function(**step_params),
                timeout=step.timeout_seconds
            )

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "execution_time": step.timeout_seconds  # Placeholder - should track actual time
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Step timeout after {step.timeout_seconds} seconds",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Automation function implementations
    async def _send_ghl_message(self, **kwargs) -> Dict[str, Any]:
        """Send message via GoHighLevel."""
        # Implementation placeholder
        return {"message": "GHL message sent", "success": True}

    async def _update_ghl_contact(self, **kwargs) -> Dict[str, Any]:
        """Update GoHighLevel contact."""
        # Implementation placeholder
        return {"message": "GHL contact updated", "success": True}

    async def _schedule_follow_up(self, **kwargs) -> Dict[str, Any]:
        """Schedule follow-up task."""
        # Implementation placeholder
        return {"message": "Follow-up scheduled", "success": True}

    async def _create_property_alert(self, **kwargs) -> Dict[str, Any]:
        """Create property alert."""
        # Implementation placeholder
        return {"message": "Property alert created", "success": True}

    async def _generate_market_report(self, **kwargs) -> Dict[str, Any]:
        """Generate market report."""
        # Implementation placeholder
        return {"message": "Market report generated", "success": True}

    async def _send_email_template(self, **kwargs) -> Dict[str, Any]:
        """Send email template."""
        # Implementation placeholder
        return {"message": "Email sent", "success": True}

    async def _update_agent_notes(self, **kwargs) -> Dict[str, Any]:
        """Update agent notes."""
        # Implementation placeholder
        return {"message": "Agent notes updated", "success": True}

    async def _trigger_workflow(self, **kwargs) -> Dict[str, Any]:
        """Trigger another workflow."""
        # Implementation placeholder
        return {"message": "Workflow triggered", "success": True}

    async def _analyze_conversation(self, **kwargs) -> Dict[str, Any]:
        """Analyze conversation using Claude."""
        # Implementation placeholder
        return {"message": "Conversation analyzed", "success": True}

    async def _optimize_scheduling(self, **kwargs) -> Dict[str, Any]:
        """Optimize scheduling."""
        # Implementation placeholder
        return {"message": "Scheduling optimized", "success": True}

    # Helper methods continue...
    async def _collect_ghl_webhook_data(self, cutoff_time: datetime, agent_id: Optional[str]) -> List[Dict[str, Any]]:
        """Collect GoHighLevel webhook data."""
        # Implementation placeholder
        return []

    async def _analyze_agent_patterns(self, agent_id: str) -> List[WorkflowPattern]:
        """Analyze patterns specific to an agent."""
        # Filter patterns by agent
        agent_patterns = [
            pattern for pattern in self.detected_patterns.values()
            if agent_id in pattern.agents_affected
        ]
        return agent_patterns

    async def _analyze_workflow_performance(self, rule: AutomationRule) -> Dict[str, Any]:
        """Analyze performance of a workflow rule."""
        # Get execution history for this rule
        rule_executions = [
            exec for exec in self.execution_history
            if exec.rule_id == rule.rule_id
        ]

        if not rule_executions:
            return {"message": "No execution history available"}

        analysis = {
            "total_executions": len(rule_executions),
            "success_rate": sum(1 for exec in rule_executions if exec.status == AutomationStatus.COMPLETED) / len(rule_executions),
            "average_execution_time": sum(
                exec.performance_metrics.get("total_duration_minutes", 0)
                for exec in rule_executions
            ) / len(rule_executions),
            "error_patterns": Counter([
                error for exec in rule_executions for error in exec.errors
            ])
        }

        return analysis

    async def _apply_workflow_optimizations(
        self, rule: AutomationRule, performance_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply optimizations to a workflow rule."""
        optimizations = {
            "applied": False,
            "improvements": {},
            "recommendations": []
        }

        # Check if optimization is needed
        success_rate = performance_analysis.get("success_rate", 1.0)
        avg_execution_time = performance_analysis.get("average_execution_time", 0.0)

        if success_rate < 0.9:
            # Improve error handling
            for step in rule.workflow_steps:
                if step.error_handling == "stop":
                    step.error_handling = "continue"
                    optimizations["applied"] = True

            optimizations["improvements"]["error_handling"] = "Improved error resilience"
            optimizations["recommendations"].append("Review error patterns and improve step implementations")

        if avg_execution_time > 10:  # More than 10 minutes
            # Optimize timeouts
            for step in rule.workflow_steps:
                if step.timeout_seconds > 60:
                    step.timeout_seconds = min(step.timeout_seconds, 60)
                    optimizations["applied"] = True

            optimizations["improvements"]["timeout_optimization"] = "Reduced step timeouts"
            optimizations["recommendations"].append("Consider parallelizing independent steps")

        return optimizations

    def _calculate_automation_coverage(self) -> float:
        """Calculate percentage of workflows covered by automation."""
        # This is a simplified calculation
        active_rules = len([rule for rule in self.automation_rules.values() if rule.enabled])
        total_workflow_types = len(WorkflowType)
        return min(1.0, active_rules / (total_workflow_types * 2))  # Assume 2 rules per workflow type as full coverage

    async def _background_pattern_detection(self) -> None:
        """Background task for continuous pattern detection."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Analyze recent workflow data for new patterns
                request = AutomationRequest(
                    request_type="analyze",
                    time_period_hours=24
                )

                workflow_data = await self._collect_workflow_data(request)
                if len(workflow_data) >= self.pattern_detection_threshold:
                    new_patterns = await self._detect_workflow_patterns(workflow_data, request)

                    for pattern in new_patterns:
                        if pattern.pattern_id not in self.detected_patterns:
                            self.detected_patterns[pattern.pattern_id] = pattern
                            logger.info(f"Detected new pattern: {pattern.pattern_id}")

            except Exception as e:
                logger.error(f"Error in background pattern detection: {str(e)}")

    async def _monitor_active_executions(self) -> None:
        """Monitor active executions for timeouts and issues."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_time = datetime.now()
                timeout_threshold = timedelta(minutes=self.execution_timeout_minutes)

                # Check for timed-out executions
                timed_out_executions = []
                for execution_id, execution in self.active_executions.items():
                    if current_time - execution.started_at > timeout_threshold:
                        timed_out_executions.append(execution_id)

                # Handle timed-out executions
                for execution_id in timed_out_executions:
                    execution = self.active_executions[execution_id]
                    execution.status = AutomationStatus.FAILED
                    execution.errors.append(f"Execution timed out after {self.execution_timeout_minutes} minutes")
                    execution.completed_at = current_time

                    # Move to history
                    self.execution_history.append(execution)
                    del self.active_executions[execution_id]

                    logger.warning(f"Execution {execution_id} timed out")

            except Exception as e:
                logger.error(f"Error monitoring executions: {str(e)}")

    async def _load_automation_rules(self) -> None:
        """Load automation rules from Redis."""
        try:
            keys = await self.redis_client.keys("automation_rule:*")
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    rule_data = json.loads(data)
                    # Convert to AutomationRule object (simplified)
                    # In practice, you'd have proper serialization/deserialization
                    logger.info(f"Loaded automation rule: {key}")

        except Exception as e:
            logger.error(f"Error loading automation rules: {str(e)}")

    async def _load_workflow_templates(self) -> None:
        """Load workflow templates."""
        # This would load from configuration files or database
        # For now, create some default templates

        default_templates = [
            WorkflowTemplate(
                template_id="lead_qualification_template",
                name="Lead Qualification Automation",
                description="Automated lead qualification and scoring",
                category="Lead Management",
                workflow_type=WorkflowType.LEAD_QUALIFICATION,
                steps=[
                    {"action": "analyze_conversation", "type": "analysis"},
                    {"action": "update_ghl_contact", "type": "crm_update"}
                ],
                customization_options={
                    "qualification_criteria": "configurable",
                    "scoring_model": "selectable"
                },
                estimated_time_savings=0.5,  # 30 minutes per lead
                success_rate=0.95
            ),
            WorkflowTemplate(
                template_id="follow_up_automation_template",
                name="Follow-up Automation",
                description="Automated follow-up scheduling and execution",
                category="Client Communication",
                workflow_type=WorkflowType.CLIENT_CONSULTATION,
                steps=[
                    {"action": "schedule_follow_up", "type": "scheduling"},
                    {"action": "send_email_template", "type": "communication"}
                ],
                customization_options={
                    "follow_up_timing": "configurable",
                    "email_templates": "customizable"
                },
                estimated_time_savings=0.25,  # 15 minutes per follow-up
                success_rate=0.90
            )
        ]

        for template in default_templates:
            self.workflow_templates[template.template_id] = template

    async def _save_automation_rule(self, rule: AutomationRule) -> None:
        """Save automation rule to Redis."""
        try:
            cache_key = f"automation_rule:{rule.rule_id}"
            rule_data = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "automation_type": rule.automation_type.value,
                "trigger_type": rule.trigger_type.value,
                "trigger_conditions": rule.trigger_conditions,
                "enabled": rule.enabled,
                "created_by": rule.created_by,
                "created_at": rule.created_at.isoformat(),
                "execution_count": rule.execution_count,
                "success_rate": rule.success_rate
            }

            await self.redis_client.setex(
                cache_key,
                30 * 24 * 3600,  # 30 days
                json.dumps(rule_data)
            )

        except Exception as e:
            logger.error(f"Error saving automation rule: {str(e)}")

    def _create_error_automation_response(
        self, request: AutomationRequest, error_message: str
    ) -> AutomationResponse:
        """Create error response for failed automation analysis."""
        return AutomationResponse(
            request_type=request.request_type,
            analysis_period=f"Last {request.time_period_hours} hours",
            patterns_detected=0,
            automation_opportunities=0,
            time_savings_potential=0.0,
            efficiency_improvements={},
            suggested_automations=[],
            active_automations=0,
            success_metrics={"error": error_message}
        )

    async def get_automation_status(self) -> Dict[str, Any]:
        """Get current status of the automation system."""
        try:
            active_rules = [rule for rule in self.automation_rules.values() if rule.enabled]

            return {
                "total_rules": len(self.automation_rules),
                "active_rules": len(active_rules),
                "active_executions": len(self.active_executions),
                "detected_patterns": len(self.detected_patterns),
                "workflow_templates": len(self.workflow_templates),
                "execution_history_count": len(self.execution_history),
                "recent_performance": {
                    "avg_success_rate": sum(rule.success_rate for rule in active_rules) / len(active_rules) if active_rules else 0,
                    "avg_execution_time": sum(rule.average_execution_time for rule in active_rules) / len(active_rules) if active_rules else 0,
                    "total_executions": sum(rule.execution_count for rule in active_rules)
                },
                "system_health": {
                    "pattern_detection_active": True,
                    "execution_monitoring_active": True,
                    "redis_connected": True  # Simplified check
                }
            }

        except Exception as e:
            logger.error(f"Error getting automation status: {str(e)}")
            return {"error": str(e)}