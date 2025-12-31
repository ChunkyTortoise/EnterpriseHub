"""
Core orchestration framework for agent swarm execution.

This module provides the foundational classes for defining agents, workflows,
and orchestrating multi-agent execution with validation, conditional branching,
and error handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from utils.exceptions import DataProcessingError, EnterpriseHubError
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class AgentExecutionError(EnterpriseHubError):
    """Raised when agent execution fails."""

    def __init__(self, agent_id: str, message: str):
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' execution failed: {message}")


class WorkflowExecutionError(EnterpriseHubError):
    """Raised when workflow execution fails."""

    pass


class ValidationError(DataProcessingError):
    """Raised when validation fails."""

    pass


# ============================================================================
# Enums
# ============================================================================


class AgentStatus(str, Enum):
    """Agent execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some agents failed but workflow continued


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    retryable_exceptions: List[type] = field(default_factory=list)


@dataclass
class PersonaB:
    """
    Persona B specification from Persona-Orchestrator pattern.

    This defines an agent's role, behavior, constraints, and workflow.
    See docs/PERSONA0.md for full specification.
    """

    role: str
    task_focus: str
    operating_principles: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    workflow: List[str] = field(default_factory=list)
    style: Dict[str, str] = field(default_factory=dict)
    behavioral_examples: Dict[str, str] = field(default_factory=dict)
    hard_do_dont: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class Agent:
    """Agent definition with Persona B template."""

    agent_id: str
    name: str
    description: str
    persona_b: Optional[PersonaB] = None
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Agent IDs
    timeout: float = 30.0
    retry_config: Optional[RetryConfig] = None


@dataclass
class AgentResult:
    """Result from agent execution."""

    agent_id: str
    status: AgentStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: float = 0.0  # seconds
    validation_result: Optional[Any] = None  # ValidationResult from validators.py


@dataclass
class ValidationRule:
    """Single validation rule for workflow."""

    rule_id: str
    name: str
    validator: Callable[[Dict[str, Any]], bool]
    threshold: float = 0.8  # Min confidence to pass
    severity: str = "ERROR"  # ERROR, WARNING, INFO
    action_on_fail: str = "HALT"  # HALT, WARN, CONTINUE


@dataclass
class WorkflowStage:
    """Single stage in a workflow."""

    stage_id: str
    agent_id: str
    depends_on: List[str] = field(default_factory=list)  # Stage IDs
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None  # Conditional execution
    required: bool = True  # Can workflow continue if this fails?
    timeout: Optional[float] = None  # Override agent timeout


@dataclass
class Workflow:
    """Workflow definition with conditional logic."""

    workflow_id: str
    name: str
    description: str = ""
    stages: List[WorkflowStage] = field(default_factory=list)
    validation_rules: List[ValidationRule] = field(default_factory=list)
    branching_logic: Dict[str, Callable] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Result from workflow execution."""

    workflow_id: str
    status: WorkflowStatus
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)  # stage_id -> result
    outputs: Dict[str, Any] = field(default_factory=dict)  # Final aggregated outputs
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: float = 0.0  # seconds


# ============================================================================
# Agent Registry
# ============================================================================


class AgentRegistry:
    """Central registry for all agents."""

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        logger.info("AgentRegistry initialized")

    def register_agent(self, agent: Agent) -> None:
        """Register an agent in the registry."""
        if agent.agent_id in self._agents:
            logger.warning(f"Agent '{agent.agent_id}' already registered, overwriting")
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self, category: Optional[str] = None) -> List[Agent]:
        """List all registered agents."""
        agents = list(self._agents.values())
        if category:
            # Filter by category in description if needed
            agents = [a for a in agents if category.lower() in a.description.lower()]
        return agents

    def validate_workflow(self, workflow: Workflow) -> bool:
        """
        Validate that all agents in workflow are registered.

        Args:
            workflow: Workflow to validate

        Returns:
            True if valid

        Raises:
            ValueError: If workflow contains unregistered agents
        """
        for stage in workflow.stages:
            if stage.agent_id not in self._agents:
                raise ValueError(
                    f"Workflow '{workflow.workflow_id}' references "
                    f"unregistered agent '{stage.agent_id}'"
                )

        # Validate dependencies exist
        stage_ids = {stage.stage_id for stage in workflow.stages}
        for stage in workflow.stages:
            for dep in stage.depends_on:
                if dep not in stage_ids:
                    raise ValueError(
                        f"Stage '{stage.stage_id}' depends on non-existent stage '{dep}'"
                    )

        logger.info(f"Workflow '{workflow.workflow_id}' validated successfully")
        return True


# ============================================================================
# Orchestrator
# ============================================================================


class Orchestrator:
    """
    Main orchestration engine for agent swarm execution.

    Handles workflow execution, agent coordination, validation, and error recovery.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        status_callback: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            registry: AgentRegistry instance (creates default if None)
            status_callback: Optional callback for status updates (msg, status_type)
        """
        self.registry = registry or AgentRegistry()
        self.status_callback = status_callback
        self._agent_handlers: Dict[str, Callable] = {}
        logger.info("Orchestrator initialized")

    def register_handler(self, agent_id: str, handler: Callable) -> None:
        """
        Register a handler function for an agent.

        Args:
            agent_id: Agent ID to register handler for
            handler: Callable that takes (inputs: Dict, context: Dict) -> Dict
        """
        self._agent_handlers[agent_id] = handler
        logger.info(f"Registered handler for agent: {agent_id}")

    def _get_agent_handler(self, agent_id: str) -> Callable:
        """Get handler for agent."""
        if agent_id not in self._agent_handlers:
            raise ValueError(f"No handler registered for agent '{agent_id}'")
        return self._agent_handlers[agent_id]

    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status via callback if available."""
        if self.status_callback:
            self.status_callback(message, status_type)
        logger.info(f"[{status_type.upper()}] {message}")

    def validate_inputs(self, agent: Agent, inputs: Dict[str, Any]) -> bool:
        """
        Validate inputs against agent's input schema.

        Args:
            agent: Agent definition
            inputs: Input data

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not agent.input_schema:
            return True  # No schema defined, skip validation

        # Check required fields (those with non-None values in schema)
        for field_name, field_type in agent.input_schema.items():
            if field_name not in inputs:
                raise ValidationError(
                    f"Missing required input '{field_name}' for agent '{agent.agent_id}'"
                )

            # Type checking
            if field_type is not None and not isinstance(inputs[field_name], field_type):
                raise ValidationError(
                    f"Input '{field_name}' has wrong type for agent '{agent.agent_id}': "
                    f"expected {field_type}, got {type(inputs[field_name])}"
                )

        return True

    def validate_outputs(
        self, agent: Agent, outputs: Dict[str, Any]
    ) -> Optional[Any]:  # Returns ValidationResult
        """
        Validate outputs against agent's output schema.

        Args:
            agent: Agent definition
            outputs: Output data

        Returns:
            ValidationResult if validators module is available, else None
        """
        if not agent.output_schema:
            return None  # No schema defined, skip validation

        # Basic validation (detailed validation happens in validators.py)
        for field_name in agent.output_schema:
            if field_name not in outputs:
                logger.warning(
                    f"Agent '{agent.agent_id}' missing expected output field '{field_name}'"
                )

        return None  # Detailed validation handled by ValidatorBot

    def execute_agent(
        self, agent: Agent, inputs: Dict[str, Any], context: Dict[str, Any]
    ) -> AgentResult:
        """
        Execute single agent with validation.

        Args:
            agent: Agent to execute
            inputs: Input data for agent
            context: Shared context from previous agents

        Returns:
            AgentResult with outputs or error
        """
        start_time = datetime.now()
        self._update_status(f"🤖 {agent.name}: Starting execution...", "info")

        try:
            # 1. Validate inputs
            self.validate_inputs(agent, inputs)

            # 2. Get agent handler
            handler = self._get_agent_handler(agent.agent_id)

            # 3. Execute agent
            outputs = handler(inputs, context)

            # 4. Validate outputs
            validation_result = self.validate_outputs(agent, outputs)

            # 5. Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # 6. Return success result
            self._update_status(f"✅ {agent.name}: Completed successfully", "success")
            return AgentResult(
                agent_id=agent.agent_id,
                status=AgentStatus.SUCCESS,
                outputs=outputs,
                timestamp=datetime.now(),
                execution_time=execution_time,
                validation_result=validation_result,
            )

        except ValidationError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Validation failed: {str(e)}"
            self._update_status(f"❌ {agent.name}: {error_msg}", "error")
            logger.error(f"Agent {agent.agent_id} validation error: {e}", exc_info=True)

            return AgentResult(
                agent_id=agent.agent_id,
                status=AgentStatus.FAILED,
                error=error_msg,
                timestamp=datetime.now(),
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Execution failed: {str(e)}"
            self._update_status(f"❌ {agent.name}: {error_msg}", "error")
            logger.error(f"Agent {agent.agent_id} execution error: {e}", exc_info=True)

            return AgentResult(
                agent_id=agent.agent_id,
                status=AgentStatus.FAILED,
                error=error_msg,
                timestamp=datetime.now(),
                execution_time=execution_time,
            )

    def _evaluate_stage_condition(self, stage: WorkflowStage, context: Dict[str, Any]) -> bool:
        """
        Evaluate if a stage should execute based on its condition.

        Args:
            stage: WorkflowStage to evaluate
            context: Current workflow context

        Returns:
            True if stage should execute
        """
        if stage.condition is None:
            return True  # No condition, always execute

        try:
            result = stage.condition(context)
            logger.info(f"Stage '{stage.stage_id}' condition evaluated to: {result}")
            return result
        except Exception as e:
            logger.error(f"Error evaluating condition for stage '{stage.stage_id}': {e}")
            return False  # Fail safe: don't execute if condition errors

    def execute_workflow(self, workflow: Workflow, inputs: Dict[str, Any]) -> WorkflowResult:
        """
        Execute complete workflow with all stages.

        Args:
            workflow: Workflow to execute
            inputs: Initial inputs for workflow

        Returns:
            WorkflowResult with aggregated outputs
        """
        start_time = datetime.now()
        self._update_status(f"🚀 Starting workflow: {workflow.name}", "info")

        # Validate workflow
        try:
            self.registry.validate_workflow(workflow)
        except ValueError as e:
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e),
                timestamp=datetime.now(),
            )

        # Initialize context and results
        context: Dict[str, Any] = {**inputs}  # Copy inputs to context
        agent_results: Dict[str, AgentResult] = {}
        failed_stages: List[str] = []

        # Execute stages
        for stage in workflow.stages:
            # Check dependencies
            skip_stage = False
            for dep_stage_id in stage.depends_on:
                dep_result = agent_results.get(dep_stage_id)
                if not dep_result or dep_result.status != AgentStatus.SUCCESS:
                    # Dependency failed, skip this stage
                    self._update_status(
                        f"⏭️ Skipping '{stage.stage_id}' - dependency failed",
                        "warning",
                    )
                    agent_results[stage.stage_id] = AgentResult(
                        agent_id=stage.agent_id,
                        status=AgentStatus.SKIPPED,
                        error=f"Dependency '{dep_stage_id}' failed",
                        timestamp=datetime.now(),
                    )
                    failed_stages.append(stage.stage_id)
                    skip_stage = True
                    break

            if skip_stage:
                continue

            # Evaluate condition
            if not self._evaluate_stage_condition(stage, context):
                self._update_status(
                    f"⏭️ Skipping '{stage.stage_id}' - condition not met",
                    "info",
                )
                agent_results[stage.stage_id] = AgentResult(
                    agent_id=stage.agent_id,
                    status=AgentStatus.SKIPPED,
                    error="Condition not met",
                    timestamp=datetime.now(),
                )
                continue

            # Get agent
            agent = self.registry.get_agent(stage.agent_id)
            if not agent:
                error_msg = f"Agent '{stage.agent_id}' not found in registry"
                logger.error(error_msg)
                agent_results[stage.stage_id] = AgentResult(
                    agent_id=stage.agent_id,
                    status=AgentStatus.FAILED,
                    error=error_msg,
                    timestamp=datetime.now(),
                )
                failed_stages.append(stage.stage_id)
                if stage.required:
                    break  # Stop workflow
                continue

            # Execute agent
            result = self.execute_agent(agent, context, context)
            agent_results[stage.stage_id] = result

            # Update context with outputs
            if result.status == AgentStatus.SUCCESS:
                context.update(result.outputs)
                
                # Execute validation rules after each stage to catch issues early
                for rule in workflow.validation_rules:
                    try:
                        if not rule.validator(context):
                            self._update_status(
                                f"⚠️ Validation rule '{rule.name}' failed",
                                "warning" if rule.severity != "ERROR" else "error",
                            )
                            if rule.action_on_fail == "HALT":
                                self._update_status(
                                    f"❌ Validation gate '{rule.name}' halted workflow",
                                    "error",
                                )
                                return WorkflowResult(
                                    workflow_id=workflow.workflow_id,
                                    status=WorkflowStatus.FAILED,
                                    agent_results=agent_results,
                                    outputs=context,
                                    error=f"Validation failed: {rule.name}",
                                    timestamp=datetime.now(),
                                    execution_time=(datetime.now() - start_time).total_seconds(),
                                )
                    except Exception as e:
                        logger.error(f"Error executing validation rule '{rule.rule_id}': {e}")
            else:
                failed_stages.append(stage.stage_id)
                if stage.required:
                    self._update_status(
                        f"❌ Required stage '{stage.stage_id}' failed, halting workflow",
                        "error",
                    )
                    break  # Stop workflow on required stage failure

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Determine workflow status
        if not failed_stages:
            status = WorkflowStatus.SUCCESS
            self._update_status(
                f"✅ Workflow '{workflow.name}' completed successfully",
                "success",
            )
        elif all(agent_results[s].status == AgentStatus.FAILED for s in failed_stages):
            status = WorkflowStatus.FAILED
            self._update_status(
                f"❌ Workflow '{workflow.name}' failed",
                "error",
            )
        else:
            status = WorkflowStatus.PARTIAL
            self._update_status(
                f"⚠️ Workflow '{workflow.name}' partially completed",
                "warning",
            )

        return WorkflowResult(
            workflow_id=workflow.workflow_id,
            status=status,
            agent_results=agent_results,
            outputs=context,  # All accumulated outputs
            timestamp=datetime.now(),
            execution_time=execution_time,
        )
