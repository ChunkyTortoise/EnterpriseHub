"""Unit tests for the orchestrator module.

Tests the core orchestration framework including Agent, Workflow, WorkflowStage,
AgentRegistry, and Orchestrator classes.
"""

from typing import Any, Dict

import pytest

pytestmark = pytest.mark.unit

from utils.orchestrator import (
    Agent,
    AgentExecutionError,
    AgentRegistry,
    AgentResult,
    AgentStatus,
    Orchestrator,
    PersonaB,
    RetryConfig,
    ValidationError,
    ValidationRule,
    Workflow,
    WorkflowExecutionError,
    WorkflowResult,
    WorkflowStage,
    WorkflowStatus,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_persona_b() -> PersonaB:
    """Create a sample PersonaB for testing."""
    return PersonaB(
        role="Data Analyst",
        task_focus="Fetch and validate market data",
        operating_principles=["Be precise", "Validate all inputs"],
        constraints=["Max 1000 rows per request"],
        workflow=["Validate input", "Fetch data", "Return results"],
        style={"tone": "technical", "detail_level": "high"},
        behavioral_examples={"success": "Data fetched successfully"},
        hard_do_dont={"do": ["Log all operations"], "dont": ["Skip validation"]},
    )


@pytest.fixture
def sample_agent(sample_persona_b: PersonaB) -> Agent:
    """Create a sample Agent for testing."""
    return Agent(
        agent_id="test_agent",
        name="Test Agent",
        description="A test agent for unit testing",
        persona_b=sample_persona_b,
        input_schema={"ticker": str, "period": str},
        output_schema={"data": dict, "status": str},
        dependencies=[],
        timeout=30.0,
        retry_config=RetryConfig(max_attempts=3),
    )


@pytest.fixture
def data_agent() -> Agent:
    """Create a data agent for workflow testing."""
    return Agent(
        agent_id="data_bot",
        name="Data Bot",
        description="Fetches market data",
        input_schema={"ticker": str},
        output_schema={"df": object, "company_info": dict},
        dependencies=[],
    )


@pytest.fixture
def tech_agent() -> Agent:
    """Create a tech agent that depends on data agent."""
    return Agent(
        agent_id="tech_bot",
        name="Tech Bot",
        description="Calculates technical indicators",
        input_schema={"df": object},
        output_schema={"rsi": float, "macd_signal": str},
        dependencies=["data_bot"],
    )


@pytest.fixture
def sample_workflow(data_agent: Agent, tech_agent: Agent) -> Workflow:
    """Create a sample workflow with two stages."""
    return Workflow(
        workflow_id="test_workflow",
        name="Test Workflow",
        description="A test workflow for unit testing",
        stages=[
            WorkflowStage(stage_id="data", agent_id="data_bot", depends_on=[]),
            WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
        ],
    )


@pytest.fixture
def registry_with_agents(data_agent: Agent, tech_agent: Agent) -> AgentRegistry:
    """Create a registry with pre-registered agents."""
    registry = AgentRegistry()
    registry.register_agent(data_agent)
    registry.register_agent(tech_agent)
    return registry


# ============================================================================
# Test Agent Dataclass
# ============================================================================


class TestAgent:
    """Tests for the Agent dataclass."""

    def test_agent_creation(self, sample_agent: Agent) -> None:
        """Test basic agent creation."""
        assert sample_agent.agent_id == "test_agent"
        assert sample_agent.name == "Test Agent"
        assert sample_agent.timeout == 30.0

    def test_agent_with_persona_b(self, sample_agent: Agent) -> None:
        """Test agent with PersonaB specification."""
        assert sample_agent.persona_b is not None
        assert sample_agent.persona_b.role == "Data Analyst"
        assert len(sample_agent.persona_b.operating_principles) == 2

    def test_agent_default_values(self) -> None:
        """Test agent with default values."""
        agent = Agent(
            agent_id="minimal",
            name="Minimal Agent",
            description="Agent with defaults",
        )
        assert agent.dependencies == []
        assert agent.timeout == 30.0
        assert agent.retry_config is None
        assert agent.input_schema == {}
        assert agent.output_schema == {}


# ============================================================================
# Test AgentResult Dataclass
# ============================================================================


class TestAgentResult:
    """Tests for the AgentResult dataclass."""

    def test_agent_result_success(self) -> None:
        """Test successful agent result."""
        result = AgentResult(
            agent_id="test_agent",
            status=AgentStatus.SUCCESS,
            outputs={"data": {"value": 100}},
            execution_time=1.5,
        )
        assert result.status == AgentStatus.SUCCESS
        assert result.error is None
        assert result.outputs["data"]["value"] == 100

    def test_agent_result_failure(self) -> None:
        """Test failed agent result."""
        result = AgentResult(
            agent_id="test_agent",
            status=AgentStatus.FAILED,
            error="Connection timeout",
            execution_time=30.0,
        )
        assert result.status == AgentStatus.FAILED
        assert result.error == "Connection timeout"
        assert result.outputs == {}


# ============================================================================
# Test AgentRegistry
# ============================================================================


class TestAgentRegistry:
    """Tests for the AgentRegistry class."""

    def test_register_agent(self, sample_agent: Agent) -> None:
        """Test registering an agent."""
        registry = AgentRegistry()
        registry.register_agent(sample_agent)

        retrieved = registry.get_agent("test_agent")
        assert retrieved is not None
        assert retrieved.name == "Test Agent"

    def test_register_overwrites_existing(self, sample_agent: Agent) -> None:
        """Test that registering same ID overwrites."""
        registry = AgentRegistry()
        registry.register_agent(sample_agent)

        new_agent = Agent(
            agent_id="test_agent",
            name="New Agent",
            description="Replacement agent",
        )
        registry.register_agent(new_agent)

        retrieved = registry.get_agent("test_agent")
        assert retrieved is not None
        assert retrieved.name == "New Agent"

    def test_get_nonexistent_agent(self) -> None:
        """Test getting non-existent agent returns None."""
        registry = AgentRegistry()
        result = registry.get_agent("nonexistent")
        assert result is None

    def test_list_agents(self, registry_with_agents: AgentRegistry) -> None:
        """Test listing all agents."""
        agents = registry_with_agents.list_agents()
        assert len(agents) == 2

        agent_ids = [a.agent_id for a in agents]
        assert "data_bot" in agent_ids
        assert "tech_bot" in agent_ids

    def test_list_agents_by_category(self, registry_with_agents: AgentRegistry) -> None:
        """Test filtering agents by category in description."""
        agents = registry_with_agents.list_agents(category="technical")
        assert len(agents) == 1
        assert agents[0].agent_id == "tech_bot"

    def test_validate_workflow_success(self, registry_with_agents: AgentRegistry, sample_workflow: Workflow) -> None:
        """Test workflow validation with all agents registered."""
        result = registry_with_agents.validate_workflow(sample_workflow)
        assert result is True

    def test_validate_workflow_missing_agent(self, registry_with_agents: AgentRegistry) -> None:
        """Test workflow validation fails with missing agent."""
        workflow = Workflow(
            workflow_id="bad_workflow",
            name="Bad Workflow",
            stages=[
                WorkflowStage(stage_id="missing", agent_id="nonexistent_agent"),
            ],
        )

        with pytest.raises(ValueError, match="unregistered agent"):
            registry_with_agents.validate_workflow(workflow)

    def test_validate_workflow_missing_dependency(self, registry_with_agents: AgentRegistry) -> None:
        """Test workflow validation fails with missing stage dependency."""
        workflow = Workflow(
            workflow_id="bad_workflow",
            name="Bad Workflow",
            stages=[
                WorkflowStage(
                    stage_id="data",
                    agent_id="data_bot",
                    depends_on=["nonexistent_stage"],
                ),
            ],
        )

        with pytest.raises(ValueError, match="non-existent stage"):
            registry_with_agents.validate_workflow(workflow)


# ============================================================================
# Test Orchestrator
# ============================================================================


class TestOrchestrator:
    """Tests for the Orchestrator class."""

    def test_orchestrator_initialization(self) -> None:
        """Test orchestrator initialization."""
        orchestrator = Orchestrator()
        assert orchestrator.registry is not None

    def test_orchestrator_with_registry(self, registry_with_agents: AgentRegistry) -> None:
        """Test orchestrator with pre-built registry."""
        orchestrator = Orchestrator(registry=registry_with_agents)
        assert orchestrator.registry.get_agent("data_bot") is not None

    def test_orchestrator_with_status_callback(self) -> None:
        """Test orchestrator status callback."""
        messages = []

        def callback(msg: str, status: str) -> None:
            messages.append((msg, status))

        orchestrator = Orchestrator(status_callback=callback)
        orchestrator._update_status("Test message", "info")

        assert len(messages) == 1
        assert messages[0] == ("Test message", "info")

    def test_register_handler(self) -> None:
        """Test registering agent handlers."""
        orchestrator = Orchestrator()

        def mock_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        orchestrator.register_handler("test_agent", mock_handler)
        handler = orchestrator._get_agent_handler("test_agent")
        assert handler is mock_handler

    def test_get_handler_not_found(self) -> None:
        """Test getting non-existent handler raises error."""
        orchestrator = Orchestrator()

        with pytest.raises(ValueError, match="No handler registered"):
            orchestrator._get_agent_handler("nonexistent")

    def test_validate_inputs_success(self, sample_agent: Agent) -> None:
        """Test input validation success."""
        orchestrator = Orchestrator()
        inputs = {"ticker": "AAPL", "period": "1y"}

        result = orchestrator.validate_inputs(sample_agent, inputs)
        assert result is True

    def test_validate_inputs_missing_field(self, sample_agent: Agent) -> None:
        """Test input validation fails on missing field."""
        orchestrator = Orchestrator()
        inputs = {"ticker": "AAPL"}  # Missing 'period'

        with pytest.raises(ValidationError, match="Missing required input"):
            orchestrator.validate_inputs(sample_agent, inputs)

    def test_validate_inputs_wrong_type(self, sample_agent: Agent) -> None:
        """Test input validation fails on wrong type."""
        orchestrator = Orchestrator()
        inputs = {"ticker": 123, "period": "1y"}  # ticker should be str

        with pytest.raises(ValidationError, match="wrong type"):
            orchestrator.validate_inputs(sample_agent, inputs)

    def test_validate_inputs_no_schema(self) -> None:
        """Test input validation skipped when no schema."""
        agent = Agent(
            agent_id="no_schema",
            name="No Schema Agent",
            description="Agent without schema",
        )
        orchestrator = Orchestrator()

        result = orchestrator.validate_inputs(agent, {"any": "input"})
        assert result is True

    def test_execute_agent_success(self, sample_agent: Agent) -> None:
        """Test successful agent execution."""
        orchestrator = Orchestrator()
        orchestrator.registry.register_agent(sample_agent)

        def mock_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {"price": 150.0}, "status": "ok"}

        orchestrator.register_handler("test_agent", mock_handler)

        result = orchestrator.execute_agent(
            sample_agent,
            inputs={"ticker": "AAPL", "period": "1y"},
            context={},
        )

        assert result.status == AgentStatus.SUCCESS
        assert result.outputs["data"]["price"] == 150.0
        assert result.execution_time > 0

    def test_execute_agent_validation_failure(self, sample_agent: Agent) -> None:
        """Test agent execution fails on validation error."""
        orchestrator = Orchestrator()
        orchestrator.registry.register_agent(sample_agent)

        def mock_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": {}, "status": "ok"}

        orchestrator.register_handler("test_agent", mock_handler)

        result = orchestrator.execute_agent(
            sample_agent,
            inputs={"ticker": "AAPL"},  # Missing 'period'
            context={},
        )

        assert result.status == AgentStatus.FAILED
        assert result.error is not None
        assert "Validation failed" in result.error

    def test_execute_agent_handler_exception(self, sample_agent: Agent) -> None:
        """Test agent execution handles handler exception."""
        orchestrator = Orchestrator()
        orchestrator.registry.register_agent(sample_agent)

        def failing_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            raise RuntimeError("Handler crashed")

        orchestrator.register_handler("test_agent", failing_handler)

        result = orchestrator.execute_agent(
            sample_agent,
            inputs={"ticker": "AAPL", "period": "1y"},
            context={},
        )

        assert result.status == AgentStatus.FAILED
        assert result.error is not None
        assert "Handler crashed" in result.error


# ============================================================================
# Test Workflow Execution
# ============================================================================


class TestWorkflowExecution:
    """Tests for workflow execution through Orchestrator."""

    def test_execute_workflow_success(self, registry_with_agents: AgentRegistry, sample_workflow: Workflow) -> None:
        """Test successful workflow execution."""
        orchestrator = Orchestrator(registry=registry_with_agents)

        # Register handlers
        def data_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"df": {"close": [100, 101, 102]}, "company_info": {"name": "Apple"}}

        def tech_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"rsi": 55.0, "macd_signal": "BULLISH"}

        orchestrator.register_handler("data_bot", data_handler)
        orchestrator.register_handler("tech_bot", tech_handler)

        result = orchestrator.execute_workflow(sample_workflow, {"ticker": "AAPL"})

        assert result.status == WorkflowStatus.SUCCESS
        assert len(result.agent_results) == 2
        assert result.agent_results["data"].status == AgentStatus.SUCCESS
        assert result.agent_results["tech"].status == AgentStatus.SUCCESS
        assert result.execution_time > 0

    def test_execute_workflow_stage_failure(
        self, registry_with_agents: AgentRegistry, sample_workflow: Workflow
    ) -> None:
        """Test workflow halts on required stage failure."""
        orchestrator = Orchestrator(registry=registry_with_agents)

        def failing_data_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            raise RuntimeError("Data fetch failed")

        def tech_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"rsi": 55.0, "macd_signal": "BULLISH"}

        orchestrator.register_handler("data_bot", failing_data_handler)
        orchestrator.register_handler("tech_bot", tech_handler)

        result = orchestrator.execute_workflow(sample_workflow, {"ticker": "AAPL"})

        assert result.status == WorkflowStatus.FAILED
        assert result.agent_results["data"].status == AgentStatus.FAILED

    def test_execute_workflow_dependency_skip(
        self, registry_with_agents: AgentRegistry, sample_workflow: Workflow
    ) -> None:
        """Test dependent stages are skipped when dependency fails."""
        orchestrator = Orchestrator(registry=registry_with_agents)

        def failing_data_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            raise RuntimeError("Data fetch failed")

        def tech_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"rsi": 55.0, "macd_signal": "BULLISH"}

        orchestrator.register_handler("data_bot", failing_data_handler)
        orchestrator.register_handler("tech_bot", tech_handler)

        # Make data stage not required so workflow continues
        sample_workflow.stages[0].required = False

        result = orchestrator.execute_workflow(sample_workflow, {"ticker": "AAPL"})

        # Tech stage should be skipped due to failed dependency
        assert result.agent_results["tech"].status == AgentStatus.SKIPPED
        tech_error = result.agent_results["tech"].error
        assert tech_error is not None
        assert "dependency" in tech_error.lower()

    def test_execute_workflow_with_condition(self, registry_with_agents: AgentRegistry) -> None:
        """Test conditional stage execution."""
        orchestrator = Orchestrator(registry=registry_with_agents)

        def data_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"df": {"close": [100]}, "company_info": {}, "quality": 0.3}

        def tech_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"rsi": 55.0, "macd_signal": "BULLISH"}

        orchestrator.register_handler("data_bot", data_handler)
        orchestrator.register_handler("tech_bot", tech_handler)

        # Create workflow with conditional tech stage
        workflow = Workflow(
            workflow_id="conditional_workflow",
            name="Conditional Workflow",
            stages=[
                WorkflowStage(stage_id="data", agent_id="data_bot"),
                WorkflowStage(
                    stage_id="tech",
                    agent_id="tech_bot",
                    depends_on=["data"],
                    # Only run tech if quality > 0.5
                    condition=lambda ctx: ctx.get("quality", 0) > 0.5,
                ),
            ],
        )

        result = orchestrator.execute_workflow(workflow, {"ticker": "AAPL"})

        # Tech stage should be skipped because quality is 0.3
        assert result.agent_results["tech"].status == AgentStatus.SKIPPED
        tech_error = result.agent_results["tech"].error
        assert tech_error is not None
        assert "condition" in tech_error.lower()

    def test_execute_workflow_invalid(self, registry_with_agents: AgentRegistry) -> None:
        """Test workflow validation failure."""
        orchestrator = Orchestrator(registry=registry_with_agents)

        # Workflow with unregistered agent
        workflow = Workflow(
            workflow_id="invalid_workflow",
            name="Invalid Workflow",
            stages=[
                WorkflowStage(stage_id="missing", agent_id="unregistered_agent"),
            ],
        )

        result = orchestrator.execute_workflow(workflow, {})

        assert result.status == WorkflowStatus.FAILED
        assert result.error is not None
        assert "unregistered agent" in result.error

    def test_execute_workflow_context_accumulation(
        self, registry_with_agents: AgentRegistry, sample_workflow: Workflow
    ) -> None:
        """Test that outputs accumulate in context."""
        orchestrator = Orchestrator(registry=registry_with_agents)

        received_context = {}

        def data_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            return {"df": {"close": [100]}, "company_info": {"name": "Apple"}}

        def tech_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal received_context
            received_context = context.copy()
            return {"rsi": 55.0, "macd_signal": "BULLISH"}

        orchestrator.register_handler("data_bot", data_handler)
        orchestrator.register_handler("tech_bot", tech_handler)

        orchestrator.execute_workflow(sample_workflow, {"ticker": "AAPL"})

        # Tech handler should have received data handler outputs in context
        assert "df" in received_context
        assert "company_info" in received_context
        assert "ticker" in received_context


# ============================================================================
# Test Workflow and Stage Dataclasses
# ============================================================================


class TestWorkflowDataclasses:
    """Tests for Workflow and WorkflowStage dataclasses."""

    def test_workflow_stage_defaults(self) -> None:
        """Test WorkflowStage default values."""
        stage = WorkflowStage(stage_id="test", agent_id="test_agent")

        assert stage.depends_on == []
        assert stage.condition is None
        assert stage.required is True
        assert stage.timeout is None

    def test_workflow_defaults(self) -> None:
        """Test Workflow default values."""
        workflow = Workflow(workflow_id="test", name="Test")

        assert workflow.description == ""
        assert workflow.stages == []
        assert workflow.validation_rules == []
        assert workflow.branching_logic == {}

    def test_workflow_result_defaults(self) -> None:
        """Test WorkflowResult default values."""
        result = WorkflowResult(
            workflow_id="test",
            status=WorkflowStatus.SUCCESS,
        )

        assert result.agent_results == {}
        assert result.outputs == {}
        assert result.error is None
        assert result.execution_time == 0.0

    def test_validation_rule(self) -> None:
        """Test ValidationRule dataclass."""
        rule = ValidationRule(
            rule_id="check_quality",
            name="Quality Check",
            validator=lambda data: data.get("quality", 0) > 0.5,
            threshold=0.8,
            severity="ERROR",
            action_on_fail="HALT",
        )

        assert rule.rule_id == "check_quality"
        assert rule.validator({"quality": 0.9}) is True
        assert rule.validator({"quality": 0.3}) is False


# ============================================================================
# Test Exception Classes
# ============================================================================


class TestExceptions:
    """Tests for custom exception classes."""

    def test_agent_execution_error(self) -> None:
        """Test AgentExecutionError creation."""
        error = AgentExecutionError("test_agent", "Handler crashed")

        assert error.agent_id == "test_agent"
        assert "test_agent" in str(error)
        assert "Handler crashed" in str(error)

    def test_workflow_execution_error(self) -> None:
        """Test WorkflowExecutionError creation."""
        error = WorkflowExecutionError("Workflow validation failed")

        assert "Workflow validation failed" in str(error)

    def test_validation_error(self) -> None:
        """Test ValidationError creation."""
        error = ValidationError("Missing required field: ticker")

        assert "Missing required field" in str(error)


# ============================================================================
# Test Status Enums
# ============================================================================


class TestStatusEnums:
    """Tests for status enumerations."""

    def test_agent_status_values(self) -> None:
        """Test AgentStatus enum values."""
        assert AgentStatus.PENDING.value == "pending"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.SUCCESS.value == "success"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.SKIPPED.value == "skipped"

    def test_workflow_status_values(self) -> None:
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.SUCCESS.value == "success"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.PARTIAL.value == "partial"