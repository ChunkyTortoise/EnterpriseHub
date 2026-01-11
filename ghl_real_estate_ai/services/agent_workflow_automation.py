"""
Agent Workflow Automation Service

Advanced workflow automation system for real estate agents with Claude AI integration.
Automates task creation, follow-up sequences, and provides intelligent workflow optimization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from .claude_agent_service import claude_agent_service
from .lead_intelligence_integration import get_lead_analytics
from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    URGENT = "urgent"           # Within 1 hour
    HIGH = "high"              # Within 4 hours
    MEDIUM = "medium"          # Within 24 hours
    LOW = "low"                # Within 3 days
    SCHEDULED = "scheduled"    # Specific time


class TaskStatus(Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class WorkflowType(Enum):
    """Types of agent workflows"""
    NEW_LEAD = "new_lead"
    HOT_LEAD = "hot_lead"
    COLD_LEAD_NURTURE = "cold_lead_nurture"
    PROPERTY_SHOWING = "property_showing"
    LISTING_PRESENTATION = "listing_presentation"
    CLOSING_FOLLOWUP = "closing_followup"
    MARKET_UPDATE = "market_update"
    CUSTOM = "custom"


@dataclass
class AgentTask:
    """Individual task in an agent's workflow"""
    id: str
    agent_id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    lead_id: Optional[str] = None
    property_id: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    workflow_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_duration_minutes: int = 15
    actual_duration_minutes: Optional[int] = None
    auto_generated: bool = False

    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.due_date and self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            return datetime.now() > self.due_date
        return False

    def get_priority_score(self) -> int:
        """Get numerical priority score for sorting"""
        priority_scores = {
            TaskPriority.URGENT: 100,
            TaskPriority.HIGH: 75,
            TaskPriority.MEDIUM: 50,
            TaskPriority.LOW: 25,
            TaskPriority.SCHEDULED: 40
        }
        score = priority_scores.get(self.priority, 25)

        # Boost score if overdue
        if self.is_overdue():
            score += 50

        # Boost score for high-value leads
        if self.lead_id and self.metadata.get('lead_score', 0) >= 80:
            score += 25

        return score


@dataclass
class Workflow:
    """Automated workflow template"""
    id: str
    name: str
    workflow_type: WorkflowType
    description: str
    trigger_conditions: Dict[str, Any]
    task_templates: List[Dict[str, Any]]
    agent_types: List[str] = field(default_factory=list)  # Which agent roles can use this
    active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentPerformanceMetrics:
    """Agent performance tracking"""
    agent_id: str
    date: datetime
    tasks_completed: int = 0
    tasks_overdue: int = 0
    average_task_duration: float = 0.0
    lead_conversion_rate: float = 0.0
    workflow_efficiency_score: float = 0.0
    ai_recommendations_followed: int = 0
    total_ai_recommendations: int = 0


class AgentWorkflowAutomation:
    """
    Advanced workflow automation system for real estate agents.

    Provides intelligent task management, automated workflow execution,
    and Claude AI-powered optimization recommendations.
    """

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.performance_metrics: Dict[str, List[AgentPerformanceMetrics]] = {}
        self.active_workflows: Dict[str, List[str]] = {}  # agent_id -> workflow_ids

        # Initialize default workflows
        self._initialize_default_workflows()

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        role: str = "agent",
        territory: Optional[str] = None,
        specializations: Optional[List[str]] = None
    ) -> bool:
        """Register a new agent in the workflow system"""

        self.agents[agent_id] = {
            "name": name,
            "role": role,
            "territory": territory or "general",
            "specializations": specializations or [],
            "active": True,
            "joined_at": datetime.now(),
            "last_activity": datetime.now(),
            "workflow_preferences": {},
            "ai_assistance_level": "standard"  # minimal, standard, advanced
        }

        # Initialize performance tracking
        self.performance_metrics[agent_id] = []
        self.active_workflows[agent_id] = []

        logger.info(f"Registered agent {agent_id} ({name}) with role {role}")
        return True

    async def create_task(
        self,
        agent_id: str,
        title: str,
        description: str,
        priority: TaskPriority,
        due_date: Optional[datetime] = None,
        lead_id: Optional[str] = None,
        property_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        auto_generated: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentTask:
        """Create a new task for an agent"""

        task_id = f"task_{agent_id}_{int(datetime.now().timestamp())}"

        # Calculate due date based on priority if not specified
        if due_date is None:
            due_date = self._calculate_due_date(priority)

        task = AgentTask(
            id=task_id,
            agent_id=agent_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            lead_id=lead_id,
            property_id=property_id,
            workflow_id=workflow_id,
            auto_generated=auto_generated,
            metadata=metadata or {}
        )

        self.tasks[task_id] = task

        # Get AI enhancement for the task if Claude is available
        if not auto_generated:  # Avoid infinite loops
            await self._enhance_task_with_ai(task)

        logger.info(f"Created task {task_id} for agent {agent_id}: {title}")
        return task

    async def trigger_workflow(
        self,
        workflow_type: WorkflowType,
        agent_id: str,
        trigger_data: Dict[str, Any]
    ) -> List[AgentTask]:
        """Trigger an automated workflow for an agent"""

        # Find applicable workflows
        applicable_workflows = [
            workflow for workflow in self.workflows.values()
            if (workflow.workflow_type == workflow_type and
                workflow.active and
                self._check_workflow_conditions(workflow, trigger_data))
        ]

        if not applicable_workflows:
            logger.warning(f"No applicable workflows found for {workflow_type} for agent {agent_id}")
            return []

        # Use the most specific workflow
        workflow = applicable_workflows[0]

        # Create tasks from workflow template
        created_tasks = []
        for task_template in workflow.task_templates:

            # Calculate delay from trigger
            delay_minutes = task_template.get('delay_minutes', 0)
            due_date = datetime.now() + timedelta(minutes=delay_minutes)

            # Personalize task with trigger data and AI
            enhanced_template = await self._personalize_task_template(
                task_template, trigger_data, agent_id
            )

            task = await self.create_task(
                agent_id=agent_id,
                title=enhanced_template.get('title', task_template['title']),
                description=enhanced_template.get('description', task_template['description']),
                priority=TaskPriority(task_template.get('priority', 'medium')),
                due_date=due_date,
                lead_id=trigger_data.get('lead_id'),
                property_id=trigger_data.get('property_id'),
                workflow_id=workflow.id,
                auto_generated=True,
                metadata=enhanced_template.get('metadata', {})
            )

            created_tasks.append(task)

        # Track workflow execution
        if agent_id not in self.active_workflows:
            self.active_workflows[agent_id] = []
        self.active_workflows[agent_id].append(workflow.id)

        logger.info(f"Triggered workflow {workflow.id} for agent {agent_id}, created {len(created_tasks)} tasks")
        return created_tasks

    async def get_agent_tasks(
        self,
        agent_id: str,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[TaskPriority] = None,
        limit: int = 50
    ) -> List[AgentTask]:
        """Get tasks for an agent with optional filtering"""

        agent_tasks = [
            task for task in self.tasks.values()
            if task.agent_id == agent_id
        ]

        # Apply filters
        if status_filter:
            agent_tasks = [task for task in agent_tasks if task.status == status_filter]

        if priority_filter:
            agent_tasks = [task for task in agent_tasks if task.priority == priority_filter]

        # Update overdue status
        for task in agent_tasks:
            if task.is_overdue() and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.OVERDUE

        # Sort by priority score and due date
        agent_tasks.sort(key=lambda t: (-t.get_priority_score(), t.due_date or datetime.max))

        return agent_tasks[:limit]

    async def complete_task(self, task_id: str, actual_duration_minutes: Optional[int] = None) -> bool:
        """Mark a task as completed"""

        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        if actual_duration_minutes:
            task.actual_duration_minutes = actual_duration_minutes

        # Update agent activity
        if task.agent_id in self.agents:
            self.agents[task.agent_id]["last_activity"] = datetime.now()

        # Check if this completes a workflow
        await self._check_workflow_completion(task)

        logger.info(f"Completed task {task_id} for agent {task.agent_id}")
        return True

    async def get_ai_task_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get AI-powered task recommendations for an agent"""

        try:
            # Get agent's current tasks and context
            current_tasks = await self.get_agent_tasks(agent_id, limit=20)
            agent_info = self.agents.get(agent_id, {})

            # Build context for Claude
            context = {
                "agent_info": agent_info,
                "current_tasks": [
                    {
                        "title": task.title,
                        "priority": task.priority.value,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "lead_id": task.lead_id,
                        "overdue": task.is_overdue()
                    }
                    for task in current_tasks
                ],
                "overdue_count": len([t for t in current_tasks if t.is_overdue()]),
                "high_priority_count": len([t for t in current_tasks if t.priority == TaskPriority.HIGH])
            }

            # Get recommendations from Claude
            query = f"Based on my current task load and priorities, what should I focus on today? What tasks should I add or modify to be more effective?"

            response = await claude_agent_service.chat_with_agent(
                agent_id, query, context=context
            )

            # Parse recommendations into actionable items
            recommendations = [
                {
                    "type": "optimization",
                    "title": insight,
                    "description": "AI-generated workflow optimization",
                    "confidence": response.confidence
                }
                for insight in response.insights[:3]
            ]

            recommendations.extend([
                {
                    "type": "action",
                    "title": rec,
                    "description": "Recommended next action",
                    "confidence": response.confidence
                }
                for rec in response.recommendations[:3]
            ])

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get AI recommendations for agent {agent_id}: {str(e)}")
            return []

    async def optimize_agent_workflow(self, agent_id: str) -> Dict[str, Any]:
        """Analyze and optimize an agent's workflow using AI"""

        try:
            # Get comprehensive agent data
            current_tasks = await self.get_agent_tasks(agent_id, limit=50)
            agent_metrics = await self._calculate_agent_metrics(agent_id)

            # Analyze patterns and bottlenecks
            analysis = {
                "task_completion_rate": len([t for t in current_tasks if t.status == TaskStatus.COMPLETED]) / max(1, len(current_tasks)),
                "average_task_overdue_time": self._calculate_average_overdue_time(current_tasks),
                "priority_distribution": self._analyze_priority_distribution(current_tasks),
                "workflow_efficiency": agent_metrics.workflow_efficiency_score if agent_metrics else 0.5
            }

            # Get AI optimization recommendations
            optimization_query = f"""
            Analyze my workflow efficiency based on these metrics:
            - Task completion rate: {analysis['task_completion_rate']:.1%}
            - Average overdue time: {analysis['average_task_overdue_time']} hours
            - Current tasks: {len(current_tasks)}

            What specific changes should I make to improve my productivity and effectiveness?
            """

            response = await claude_agent_service.chat_with_agent(
                agent_id, optimization_query, context={"analysis": analysis}
            )

            return {
                "current_metrics": analysis,
                "ai_insights": response.insights,
                "optimization_recommendations": response.recommendations,
                "confidence": response.confidence,
                "next_actions": [
                    {
                        "action": rec,
                        "impact": "high" if "priority" in rec.lower() or "urgent" in rec.lower() else "medium",
                        "effort": "low" if "schedule" in rec.lower() or "time" in rec.lower() else "medium"
                    }
                    for rec in response.recommendations[:5]
                ]
            }

        except Exception as e:
            logger.error(f"Failed to optimize workflow for agent {agent_id}: {str(e)}")
            return {"error": str(e)}

    def _initialize_default_workflows(self):
        """Initialize default workflow templates"""

        # New Lead Workflow
        new_lead_workflow = Workflow(
            id="new_lead_standard",
            name="New Lead Standard Process",
            workflow_type=WorkflowType.NEW_LEAD,
            description="Standard workflow for new lead intake and qualification",
            trigger_conditions={"lead_status": "new", "lead_source": ["website", "referral", "ad"]},
            task_templates=[
                {
                    "title": "Initial Lead Contact",
                    "description": "Make first contact within 5 minutes of lead generation",
                    "priority": "urgent",
                    "delay_minutes": 0,
                    "estimated_duration": 15
                },
                {
                    "title": "Lead Qualification Call",
                    "description": "Conduct comprehensive lead qualification interview",
                    "priority": "high",
                    "delay_minutes": 60,
                    "estimated_duration": 30
                },
                {
                    "title": "Send Welcome Package",
                    "description": "Send personalized welcome package with market information",
                    "priority": "medium",
                    "delay_minutes": 120,
                    "estimated_duration": 10
                },
                {
                    "title": "Schedule Follow-up",
                    "description": "Schedule next touchpoint based on lead timeline",
                    "priority": "medium",
                    "delay_minutes": 180,
                    "estimated_duration": 5
                }
            ]
        )

        # Hot Lead Workflow
        hot_lead_workflow = Workflow(
            id="hot_lead_acceleration",
            name="Hot Lead Acceleration Process",
            workflow_type=WorkflowType.HOT_LEAD,
            description="Intensive workflow for high-probability leads",
            trigger_conditions={"lead_score": {"min": 80}, "engagement": "high"},
            task_templates=[
                {
                    "title": "Immediate Priority Contact",
                    "description": "Call hot lead immediately - drop current activity",
                    "priority": "urgent",
                    "delay_minutes": 0,
                    "estimated_duration": 20
                },
                {
                    "title": "Property Preview Preparation",
                    "description": "Prepare customized property presentation",
                    "priority": "high",
                    "delay_minutes": 30,
                    "estimated_duration": 45
                },
                {
                    "title": "Schedule Showing ASAP",
                    "description": "Schedule property showing within 24 hours",
                    "priority": "urgent",
                    "delay_minutes": 45,
                    "estimated_duration": 15
                },
                {
                    "title": "Pre-approval Coordination",
                    "description": "Connect with preferred lender for pre-approval",
                    "priority": "high",
                    "delay_minutes": 120,
                    "estimated_duration": 20
                }
            ]
        )

        # Cold Lead Nurture Workflow
        cold_lead_workflow = Workflow(
            id="cold_lead_nurture",
            name="Cold Lead Nurturing Sequence",
            workflow_type=WorkflowType.COLD_LEAD_NURTURE,
            description="Long-term nurturing for cold or unqualified leads",
            trigger_conditions={"lead_score": {"max": 49}, "engagement": "low"},
            task_templates=[
                {
                    "title": "Educational Content Follow-up",
                    "description": "Send relevant market education and property insights",
                    "priority": "low",
                    "delay_minutes": 1440,  # 24 hours
                    "estimated_duration": 10
                },
                {
                    "title": "Market Update Check-in",
                    "description": "Share personalized market updates and trends",
                    "priority": "low",
                    "delay_minutes": 10080,  # 1 week
                    "estimated_duration": 15
                },
                {
                    "title": "Quarterly Touch Base",
                    "description": "Quarterly check-in to assess changing needs",
                    "priority": "scheduled",
                    "delay_minutes": 129600,  # 90 days
                    "estimated_duration": 20
                }
            ]
        )

        self.workflows = {
            new_lead_workflow.id: new_lead_workflow,
            hot_lead_workflow.id: hot_lead_workflow,
            cold_lead_workflow.id: cold_lead_workflow
        }

    def _calculate_due_date(self, priority: TaskPriority) -> datetime:
        """Calculate due date based on task priority"""
        now = datetime.now()

        due_dates = {
            TaskPriority.URGENT: now + timedelta(hours=1),
            TaskPriority.HIGH: now + timedelta(hours=4),
            TaskPriority.MEDIUM: now + timedelta(hours=24),
            TaskPriority.LOW: now + timedelta(days=3),
            TaskPriority.SCHEDULED: now + timedelta(days=1)  # Default, should be overridden
        }

        return due_dates.get(priority, now + timedelta(days=1))

    def _check_workflow_conditions(self, workflow: Workflow, trigger_data: Dict[str, Any]) -> bool:
        """Check if trigger data meets workflow conditions"""

        conditions = workflow.trigger_conditions

        for key, condition_value in conditions.items():
            if key not in trigger_data:
                continue

            trigger_value = trigger_data[key]

            # Handle different condition types
            if isinstance(condition_value, dict):
                # Range conditions (min/max)
                if "min" in condition_value and trigger_value < condition_value["min"]:
                    return False
                if "max" in condition_value and trigger_value > condition_value["max"]:
                    return False
            elif isinstance(condition_value, list):
                # List inclusion
                if trigger_value not in condition_value:
                    return False
            else:
                # Exact match
                if trigger_value != condition_value:
                    return False

        return True

    async def _enhance_task_with_ai(self, task: AgentTask):
        """Enhance task with AI-generated insights and recommendations"""

        try:
            if not task.lead_id:
                return

            # Get lead context
            context_query = f"What should I know about lead {task.lead_id} for this task: {task.title}?"

            response = await claude_agent_service.chat_with_agent(
                task.agent_id, context_query, task.lead_id
            )

            # Enhance task metadata with AI insights
            task.metadata.update({
                "ai_insights": response.insights[:2],  # Top 2 insights
                "ai_recommendations": response.recommendations[:1],  # Top recommendation
                "ai_confidence": response.confidence,
                "enhanced_at": datetime.now().isoformat()
            })

        except Exception as e:
            logger.warning(f"Failed to enhance task {task.id} with AI: {str(e)}")

    async def _personalize_task_template(
        self,
        template: Dict[str, Any],
        trigger_data: Dict[str, Any],
        agent_id: str
    ) -> Dict[str, Any]:
        """Personalize task template with trigger data and AI"""

        try:
            personalized = template.copy()

            # Basic template variable replacement
            for key in ['title', 'description']:
                if key in personalized:
                    text = personalized[key]
                    # Replace common variables
                    if 'lead_name' in trigger_data:
                        text = text.replace('{lead_name}', trigger_data['lead_name'])
                    if 'property_address' in trigger_data:
                        text = text.replace('{property_address}', trigger_data['property_address'])

                    personalized[key] = text

            # Add AI personalization if lead_id available
            if trigger_data.get('lead_id'):
                ai_query = f"How should I personalize this task for this specific lead: {template['title']}?"

                response = await claude_agent_service.chat_with_agent(
                    agent_id, ai_query, trigger_data.get('lead_id')
                )

                # Add AI suggestions to metadata
                personalized['metadata'] = personalized.get('metadata', {})
                personalized['metadata'].update({
                    'ai_personalization': response.insights[:1],
                    'ai_approach': response.recommendations[:1]
                })

            return personalized

        except Exception as e:
            logger.warning(f"Failed to personalize task template: {str(e)}")
            return template

    async def _check_workflow_completion(self, completed_task: AgentTask):
        """Check if completing this task finishes a workflow"""

        if not completed_task.workflow_id:
            return

        # Get all tasks in this workflow
        workflow_tasks = [
            task for task in self.tasks.values()
            if (task.workflow_id == completed_task.workflow_id and
                task.agent_id == completed_task.agent_id)
        ]

        # Check if all tasks are completed
        all_completed = all(task.status == TaskStatus.COMPLETED for task in workflow_tasks)

        if all_completed:
            # Workflow completed - trigger next phase or completion actions
            logger.info(f"Workflow {completed_task.workflow_id} completed for agent {completed_task.agent_id}")

            # Remove from active workflows
            if completed_task.agent_id in self.active_workflows:
                self.active_workflows[completed_task.agent_id] = [
                    wf_id for wf_id in self.active_workflows[completed_task.agent_id]
                    if wf_id != completed_task.workflow_id
                ]

    async def _calculate_agent_metrics(self, agent_id: str) -> Optional[AgentPerformanceMetrics]:
        """Calculate current performance metrics for an agent"""

        agent_tasks = await self.get_agent_tasks(agent_id, limit=100)

        if not agent_tasks:
            return None

        completed_tasks = [t for t in agent_tasks if t.status == TaskStatus.COMPLETED]
        overdue_tasks = [t for t in agent_tasks if t.is_overdue()]

        # Calculate average task duration
        durations = [t.actual_duration_minutes for t in completed_tasks if t.actual_duration_minutes]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        # Calculate workflow efficiency score (0-1)
        total_tasks = len(agent_tasks)
        completed_count = len(completed_tasks)
        overdue_count = len(overdue_tasks)

        efficiency_score = 0.0
        if total_tasks > 0:
            completion_rate = completed_count / total_tasks
            overdue_penalty = min(0.5, overdue_count / total_tasks)
            efficiency_score = max(0.0, completion_rate - overdue_penalty)

        return AgentPerformanceMetrics(
            agent_id=agent_id,
            date=datetime.now(),
            tasks_completed=completed_count,
            tasks_overdue=overdue_count,
            average_task_duration=avg_duration,
            workflow_efficiency_score=efficiency_score
        )

    def _calculate_average_overdue_time(self, tasks: List[AgentTask]) -> float:
        """Calculate average hours tasks are overdue"""

        overdue_tasks = [t for t in tasks if t.is_overdue() and t.due_date]

        if not overdue_tasks:
            return 0.0

        total_overdue_hours = sum(
            (datetime.now() - t.due_date).total_seconds() / 3600
            for t in overdue_tasks
        )

        return total_overdue_hours / len(overdue_tasks)

    def _analyze_priority_distribution(self, tasks: List[AgentTask]) -> Dict[str, int]:
        """Analyze distribution of task priorities"""

        distribution = {priority.value: 0 for priority in TaskPriority}

        for task in tasks:
            distribution[task.priority.value] += 1

        return distribution


# Global instance for easy access
agent_workflow_automation = AgentWorkflowAutomation()


# Convenience functions
async def register_agent(agent_id: str, name: str, role: str = "agent") -> bool:
    """Register a new agent"""
    return await agent_workflow_automation.register_agent(agent_id, name, role)


async def create_agent_task(
    agent_id: str,
    title: str,
    description: str,
    priority: str = "medium",
    lead_id: Optional[str] = None
) -> AgentTask:
    """Create a task for an agent"""
    return await agent_workflow_automation.create_task(
        agent_id, title, description, TaskPriority(priority), lead_id=lead_id
    )


async def trigger_agent_workflow(
    workflow_type: str,
    agent_id: str,
    trigger_data: Dict[str, Any]
) -> List[AgentTask]:
    """Trigger a workflow for an agent"""
    return await agent_workflow_automation.trigger_workflow(
        WorkflowType(workflow_type), agent_id, trigger_data
    )


async def get_agent_task_recommendations(agent_id: str) -> List[Dict[str, Any]]:
    """Get AI-powered task recommendations"""
    return await agent_workflow_automation.get_ai_task_recommendations(agent_id)