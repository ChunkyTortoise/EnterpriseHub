"""
Advanced Workflow Engine with Conditional Branching and Decision Trees

This module provides intelligent workflow execution with:
- Conditional branching based on lead data/behavior
- Decision trees for complex logic
- Event-driven triggers
- Performance tracking integration
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConditionOperator(Enum):
    """Operators for condition evaluation"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class TriggerType(Enum):
    """Types of workflow triggers"""

    MANUAL = "manual"
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    BEHAVIOR_BASED = "behavior_based"
    SCORE_BASED = "score_based"


@dataclass
class WorkflowCondition:
    """Represents a condition for branching logic"""

    field: str
    operator: ConditionOperator
    value: Any
    description: str = ""

    def evaluate(self, lead_data: Dict[str, Any]) -> bool:
        """Evaluate condition against lead data"""
        try:
            field_value = self._get_nested_field(lead_data, self.field)

            if self.operator == ConditionOperator.EQUALS:
                return field_value == self.value
            elif self.operator == ConditionOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == ConditionOperator.GREATER_THAN:
                return float(field_value) > float(self.value)
            elif self.operator == ConditionOperator.LESS_THAN:
                return float(field_value) < float(self.value)
            elif self.operator == ConditionOperator.CONTAINS:
                return str(self.value).lower() in str(field_value).lower()
            elif self.operator == ConditionOperator.IN:
                return field_value in self.value
            elif self.operator == ConditionOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == ConditionOperator.IS_TRUE:
                return bool(field_value) is True
            elif self.operator == ConditionOperator.IS_FALSE:
                return bool(field_value) is False
            elif self.operator == ConditionOperator.EXISTS:
                return field_value is not None
            elif self.operator == ConditionOperator.NOT_EXISTS:
                return field_value is None

            return False

        except Exception as e:
            logger.warning(f"Condition evaluation failed: {e}")
            return False

    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field path (e.g., 'lead_score.behavioral')"""
        try:
            keys = field_path.split(".")
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Failed to get nested field '{field_path}': {e}")
            return None


@dataclass
class WorkflowBranch:
    """Represents a conditional branch in workflow"""

    name: str
    conditions: List[WorkflowCondition]
    logic_operator: str = "AND"  # "AND" or "OR"
    actions: List[Dict[str, Any]] = field(default_factory=list)
    next_step_id: Optional[str] = None

    def evaluate(self, lead_data: Dict[str, Any]) -> bool:
        """Evaluate all conditions in branch"""
        if not self.conditions:
            return True

        results = [condition.evaluate(lead_data) for condition in self.conditions]

        if self.logic_operator == "OR":
            return any(results)
        else:  # AND
            return all(results)


@dataclass
class WorkflowStep:
    """Enhanced workflow step with branching support"""

    id: str
    name: str
    type: str
    config: Dict[str, Any] = field(default_factory=dict)
    branches: List[WorkflowBranch] = field(default_factory=list)
    default_next_step_id: Optional[str] = None
    delay_config: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None

    def get_next_step_id(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """Determine next step based on conditions"""
        # Evaluate branches in order
        for branch in self.branches:
            if branch.evaluate(lead_data):
                return branch.next_step_id

        # Fall back to default
        return self.default_next_step_id


@dataclass
class WorkflowTrigger:
    """Workflow trigger configuration"""

    type: TriggerType
    config: Dict[str, Any]
    conditions: List[WorkflowCondition] = field(default_factory=list)

    def should_trigger(self, event_data: Dict[str, Any]) -> bool:
        """Check if trigger conditions are met"""
        if not self.conditions:
            return True

        return all(condition.evaluate(event_data) for condition in self.conditions)


@dataclass
class AdvancedWorkflow:
    """Advanced workflow with branching and intelligence"""

    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    global_config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get workflow step by ID"""
        return next((step for step in self.steps if step.id == step_id), None)

    def get_first_step(self) -> Optional[WorkflowStep]:
        """Get the first step in workflow"""
        return self.steps[0] if self.steps else None


class AdvancedWorkflowEngine:
    """Advanced workflow execution engine"""

    def __init__(self, state_manager=None, analytics_service=None):
        self.state_manager = state_manager
        self.analytics_service = analytics_service
        self.active_executions: Dict[str, Dict] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self.event_listeners: List[Callable] = []

        # Register built-in action handlers
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        """Register built-in action handlers"""
        self.action_handlers.update(
            {
                "send_email": self._handle_send_email,
                "send_sms": self._handle_send_sms,
                "create_task": self._handle_create_task,
                "update_lead": self._handle_update_lead,
                "wait": self._handle_wait,
                "webhook": self._handle_webhook,
                "conditional_split": self._handle_conditional_split,
                "score_update": self._handle_score_update,
            }
        )

    async def start_workflow(
        self, workflow: AdvancedWorkflow, lead_data: Dict[str, Any], trigger_event: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start workflow execution for a lead"""
        execution_id = f"{workflow.id}_{lead_data.get('id', 'unknown')}_{datetime.now().timestamp()}"

        # Initialize execution context
        execution_context = {
            "id": execution_id,
            "workflow_id": workflow.id,
            "lead_id": lead_data.get("id"),
            "lead_data": lead_data.copy(),
            "current_step_id": None,
            "status": "running",
            "started_at": datetime.now(),
            "trigger_event": trigger_event,
            "execution_path": [],
            "variables": {},
            "retry_count": 0,
        }

        self.active_executions[execution_id] = execution_context

        # Save initial state
        if self.state_manager:
            await self.state_manager.save_execution_state(execution_id, execution_context)

        # Start execution
        await self._execute_workflow(workflow, execution_context)

        return execution_id

    async def _execute_workflow(self, workflow: AdvancedWorkflow, execution_context: Dict[str, Any]):
        """Execute workflow steps"""
        try:
            current_step = workflow.get_first_step()

            while current_step and execution_context["status"] == "running":
                execution_context["current_step_id"] = current_step.id
                execution_context["execution_path"].append(
                    {
                        "step_id": current_step.id,
                        "step_name": current_step.name,
                        "timestamp": datetime.now(),
                        "lead_data_snapshot": execution_context["lead_data"].copy(),
                    }
                )

                # Save state before step execution
                if self.state_manager:
                    await self.state_manager.save_execution_state(execution_context["id"], execution_context)

                # Execute step
                success = await self._execute_step(current_step, execution_context)

                if not success:
                    execution_context["status"] = "failed"
                    break

                # Determine next step
                next_step_id = current_step.get_next_step_id(execution_context["lead_data"])

                if next_step_id:
                    current_step = workflow.get_step_by_id(next_step_id)
                else:
                    # No next step, workflow complete
                    current_step = None
                    execution_context["status"] = "completed"

            execution_context["completed_at"] = datetime.now()

            # Final state save
            if self.state_manager:
                await self.state_manager.save_execution_state(execution_context["id"], execution_context)

            # Track analytics
            if self.analytics_service:
                await self.analytics_service.track_workflow_completion(execution_context)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution_context["status"] = "failed"
            execution_context["error"] = str(e)

            # Save error state
            if self.state_manager:
                await self.state_manager.save_execution_state(execution_context["id"], execution_context)

    async def _execute_step(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Execute individual workflow step"""
        try:
            logger.info(f"Executing step: {step.name} (ID: {step.id})")

            # Handle delay if configured
            if step.delay_config:
                delay_seconds = await self._calculate_delay(step.delay_config, execution_context)
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)

            # Get action handler
            handler = self.action_handlers.get(step.type)
            if not handler:
                logger.error(f"No handler found for step type: {step.type}")
                return False

            # Execute action with retry logic
            max_retries = step.retry_config.get("max_retries", 0) if step.retry_config else 0
            retry_delay = step.retry_config.get("delay_seconds", 1) if step.retry_config else 1

            for attempt in range(max_retries + 1):
                try:
                    result = await handler(step, execution_context)
                    if result:
                        return True
                except Exception as e:
                    logger.warning(f"Step execution attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

            return False

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return False

    async def _calculate_delay(self, delay_config: Dict[str, Any], execution_context: Dict[str, Any]) -> int:
        """Calculate delay for step execution"""
        delay_type = delay_config.get("type", "fixed")

        if delay_type == "fixed":
            return delay_config.get("seconds", 0)
        elif delay_type == "dynamic":
            # Calculate based on lead data or previous actions
            return delay_config.get("default_seconds", 0)
        elif delay_type == "optimal_timing":
            # Use timing optimizer if available
            return delay_config.get("default_seconds", 0)

        return 0

    # Action Handlers
    async def _handle_send_email(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle email sending action"""
        try:
            config = step.config
            lead_data = execution_context["lead_data"]

            # Template processing would go here
            email_data = {
                "to": lead_data.get("email"),
                "subject": config.get("subject", ""),
                "template_id": config.get("template_id"),
                "variables": {**lead_data, **execution_context.get("variables", {})},
            }

            # Mock email sending - integrate with actual email service
            logger.info(f"Sending email to {email_data['to']}")
            await asyncio.sleep(0.1)  # Simulate API call

            # Update execution context
            execution_context["variables"]["last_email_sent"] = datetime.now().isoformat()

            return True

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False

    async def _handle_send_sms(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle SMS sending action"""
        try:
            config = step.config
            lead_data = execution_context["lead_data"]

            sms_data = {
                "to": lead_data.get("phone"),
                "message": config.get("message", ""),
                "template_id": config.get("template_id"),
                "variables": {**lead_data, **execution_context.get("variables", {})},
            }

            # Mock SMS sending
            logger.info(f"Sending SMS to {sms_data['to']}")
            await asyncio.sleep(0.1)

            execution_context["variables"]["last_sms_sent"] = datetime.now().isoformat()

            return True

        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return False

    async def _handle_create_task(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle task creation action"""
        try:
            config = step.config
            lead_data = execution_context["lead_data"]

            task_data = {
                "title": config.get("title", ""),
                "description": config.get("description", ""),
                "assignee": config.get("assignee"),
                "due_date": config.get("due_date"),
                "lead_id": lead_data.get("id"),
            }

            # Mock task creation
            logger.info(f"Creating task: {task_data['title']}")
            await asyncio.sleep(0.1)

            execution_context["variables"]["last_task_created"] = datetime.now().isoformat()

            return True

        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            return False

    async def _handle_update_lead(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle lead data update action"""
        try:
            config = step.config
            updates = config.get("updates", {})

            # Apply updates to lead data
            execution_context["lead_data"].update(updates)

            logger.info(f"Updated lead data: {updates}")

            return True

        except Exception as e:
            logger.error(f"Lead update failed: {e}")
            return False

    async def _handle_wait(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle wait/delay action"""
        try:
            config = step.config
            delay_seconds = config.get("seconds", 0)

            if delay_seconds > 0:
                logger.info(f"Waiting {delay_seconds} seconds")
                await asyncio.sleep(delay_seconds)

            return True

        except Exception as e:
            logger.error(f"Wait action failed: {e}")
            return False

    async def _handle_webhook(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle webhook action"""
        try:
            config = step.config
            # Mock webhook call
            logger.info(f"Calling webhook: {config.get('url', '')}")
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Webhook call failed: {e}")
            return False

    async def _handle_conditional_split(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle conditional branching (no-op, logic handled in step execution)"""
        return True

    async def _handle_score_update(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> bool:
        """Handle lead score update action"""
        try:
            config = step.config
            score_changes = config.get("score_changes", {})

            # Apply score changes
            current_score = execution_context["lead_data"].get("lead_score", 0)
            new_score = current_score + score_changes.get("behavioral", 0)
            execution_context["lead_data"]["lead_score"] = new_score

            logger.info(f"Updated lead score: {current_score} -> {new_score}")

            return True

        except Exception as e:
            logger.error(f"Score update failed: {e}")
            return False

    def register_action_handler(self, action_type: str, handler: Callable):
        """Register custom action handler"""
        self.action_handlers[action_type] = handler

    def add_event_listener(self, listener: Callable):
        """Add event listener for workflow events"""
        self.event_listeners.append(listener)

    async def handle_external_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle external events that might trigger workflows"""
        try:
            # Notify listeners
            for listener in self.event_listeners:
                await listener(event_type, event_data)

            # Check for event-based triggers
            # This would integrate with active workflows and triggers

        except Exception as e:
            logger.error(f"Event handling failed: {e}")

    async def pause_workflow(self, execution_id: str):
        """Pause workflow execution"""
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = "paused"

            if self.state_manager:
                await self.state_manager.save_execution_state(execution_id, self.active_executions[execution_id])

    async def resume_workflow(self, execution_id: str):
        """Resume paused workflow execution"""
        if execution_id in self.active_executions:
            execution_context = self.active_executions[execution_id]
            if execution_context["status"] == "paused":
                execution_context["status"] = "running"

                # Resume from current step
                # This would require more complex state management

    async def stop_workflow(self, execution_id: str):
        """Stop workflow execution"""
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = "stopped"
            self.active_executions[execution_id]["stopped_at"] = datetime.now()

            if self.state_manager:
                await self.state_manager.save_execution_state(execution_id, self.active_executions[execution_id])

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        return self.active_executions.get(execution_id)

    async def cleanup_completed_executions(self, max_age_hours: int = 24):
        """Clean up old completed executions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        to_remove = []
        for execution_id, context in self.active_executions.items():
            if (
                context["status"] in ["completed", "failed", "stopped"]
                and context.get("completed_at", datetime.now()) < cutoff_time
            ):
                to_remove.append(execution_id)

        for execution_id in to_remove:
            del self.active_executions[execution_id]
            logger.info(f"Cleaned up execution: {execution_id}")
