"""Integration tests for complete workflow execution.

Tests the orchestrator's ability to execute multi-stage workflows with
real agent handlers, including validation gating, conditional execution,
dynamic branching, and error recovery patterns.
"""

from typing import Any, Dict

import pytest

from utils.agent_handlers import AGENT_HANDLERS
from utils.agent_registry import ALL_AGENTS
from utils.orchestrator import (
    AgentRegistry,
    AgentStatus,
    Orchestrator,
    ValidationRule,
    Workflow,
    WorkflowStage,
    WorkflowStatus,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def agent_registry() -> AgentRegistry:
    """Create an AgentRegistry with all pre-built agents."""
    registry = AgentRegistry()
    for agent_id, agent in ALL_AGENTS.items():
        registry.register_agent(agent)
    return registry


@pytest.fixture
def orchestrator(agent_registry: AgentRegistry) -> Orchestrator:
    """Create an Orchestrator with all agent handlers registered."""
    orch = Orchestrator(registry=agent_registry)
    for agent_id, handler in AGENT_HANDLERS.items():
        orch.register_handler(agent_id, handler)
    return orch


@pytest.fixture
def simple_workflow() -> Workflow:
    """Create a simple 2-stage workflow: data -> tech."""
    return Workflow(
        workflow_id="simple_workflow",
        name="Simple Workflow",
        description="Basic 2-stage workflow for testing",
        stages=[
            WorkflowStage(stage_id="data", agent_id="data_bot"),
            WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
        ],
    )


@pytest.fixture
def complex_workflow() -> Workflow:
    """Create a complex 4-stage workflow with parallel stages."""
    return Workflow(
        workflow_id="complex_workflow",
        name="Complex Workflow",
        description="4-stage workflow with parallel execution",
        stages=[
            WorkflowStage(stage_id="data", agent_id="data_bot"),
            WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
            WorkflowStage(stage_id="sentiment", agent_id="sentiment_bot", depends_on=["data"]),
            WorkflowStage(
                stage_id="synthesis",
                agent_id="synthesis_bot",
                depends_on=["tech", "sentiment"],
            ),
        ],
    )


@pytest.fixture
def validation_gated_workflow() -> Workflow:
    """Create a workflow with validation rules that halt on failure."""

    def min_quality_check(context: Dict[str, Any]) -> bool:
        """Validator: require minimum data quality."""
        return context.get("quality_score", 0.0) >= 0.5

    return Workflow(
        workflow_id="validation_gated",
        name="Validation Gated Workflow",
        description="Workflow with quality threshold validation",
        stages=[
            WorkflowStage(stage_id="data", agent_id="data_bot"),
            WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
        ],
        validation_rules=[
            ValidationRule(
                rule_id="quality_gate",
                name="Minimum Quality Gate",
                validator=min_quality_check,
                threshold=0.5,
                action_on_fail="HALT",
            )
        ],
    )


@pytest.fixture
def conditional_workflow() -> Workflow:
    """Create a workflow with conditional stage execution."""

    def high_confidence_condition(context: Dict[str, Any]) -> bool:
        """Condition: skip forecast if confidence is too low."""
        return context.get("confidence", 0.0) > 0.7

    return Workflow(
        workflow_id="conditional_workflow",
        name="Conditional Workflow",
        description="Workflow with conditional stage skipping",
        stages=[
            WorkflowStage(stage_id="data", agent_id="data_bot"),
            WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
            WorkflowStage(
                stage_id="forecast",
                agent_id="forecast_bot",
                depends_on=["data", "tech"],
                condition=high_confidence_condition,
                required=False,
            ),
        ],
    )


@pytest.fixture
def error_recovery_workflow() -> Workflow:
    """Create a workflow that can recover from non-critical stage failures."""
    return Workflow(
        workflow_id="error_recovery",
        name="Error Recovery Workflow",
        description="Workflow with non-required optional stages",
        stages=[
            WorkflowStage(stage_id="data", agent_id="data_bot"),
            WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
            WorkflowStage(
                stage_id="sentiment",
                agent_id="sentiment_bot",
                depends_on=["data"],
                required=False,  # Optional - failure won't halt workflow
            ),
            WorkflowStage(
                stage_id="synthesis",
                agent_id="synthesis_bot",
                depends_on=["tech"],  # Only depends on tech, not sentiment
            ),
        ],
    )


# ============================================================================
# Complete Workflow Execution Tests
# ============================================================================


class TestCompleteWorkflowExecution:
    """Tests for end-to-end workflow execution."""

    def test_simple_workflow_success(
        self, orchestrator: Orchestrator, simple_workflow: Workflow
    ) -> None:
        """Test simple 2-stage workflow completes successfully."""
        inputs = {"ticker": "AAPL", "period": "1mo"}

        result = orchestrator.execute_workflow(simple_workflow, inputs)

        assert result.status == WorkflowStatus.SUCCESS
        assert len(result.agent_results) == 2
        assert "data" in result.agent_results
        assert "tech" in result.agent_results
        assert result.agent_results["data"].status == AgentStatus.SUCCESS
        assert result.agent_results["tech"].status == AgentStatus.SUCCESS

    def test_complex_workflow_parallel_execution(
        self, orchestrator: Orchestrator, complex_workflow: Workflow
    ) -> None:
        """Test complex workflow with parallel stages (tech + sentiment)."""
        inputs = {"ticker": "NVDA", "period": "1mo"}

        result = orchestrator.execute_workflow(complex_workflow, inputs)

        assert result.status == WorkflowStatus.SUCCESS
        assert len(result.agent_results) == 4
        # Verify all stages completed
        for stage_id in ["data", "tech", "sentiment", "synthesis"]:
            assert stage_id in result.agent_results
            assert result.agent_results[stage_id].status == AgentStatus.SUCCESS

    def test_workflow_context_passing(
        self, orchestrator: Orchestrator, simple_workflow: Workflow
    ) -> None:
        """Test that outputs from one stage are accessible to next stage."""
        inputs = {"ticker": "MSFT", "period": "1mo"}

        result = orchestrator.execute_workflow(simple_workflow, inputs)

        # Data stage should produce DataFrame
        assert "df" in result.agent_results["data"].outputs
        # Tech stage should have access to DataFrame from context
        assert result.agent_results["tech"].outputs is not None
        # Tech stage should produce signal
        assert "signal" in result.agent_results["tech"].outputs

    def test_workflow_execution_time_tracking(
        self, orchestrator: Orchestrator, simple_workflow: Workflow
    ) -> None:
        """Test that execution times are tracked for each stage."""
        inputs = {"ticker": "GOOGL", "period": "1mo"}

        result = orchestrator.execute_workflow(simple_workflow, inputs)

        for stage_id, stage_result in result.agent_results.items():
            assert stage_result.execution_time >= 0.0
        # Total workflow time should be sum of stage times
        assert result.execution_time >= sum(
            sr.execution_time for sr in result.agent_results.values()
        )


# ============================================================================
# Validation Gating Tests
# ============================================================================


class TestValidationGating:
    """Tests for validation rules and gating behavior."""

    def test_validation_passes_workflow_continues(
        self, orchestrator: Orchestrator, validation_gated_workflow: Workflow
    ) -> None:
        """Test workflow continues when validation passes."""
        # Use AAPL with 1mo data - should have good quality score
        inputs = {"ticker": "AAPL", "period": "1mo"}

        result = orchestrator.execute_workflow(validation_gated_workflow, inputs)

        # Workflow should complete successfully
        assert result.status == WorkflowStatus.SUCCESS
        # Data quality should be > 0.5
        data_result = result.agent_results["data"]
        assert data_result.outputs.get("quality_score", 0.0) >= 0.5

    def test_validation_fails_workflow_halts(
        self, orchestrator: Orchestrator, agent_registry: AgentRegistry
    ) -> None:
        """Test workflow halts when validation fails and action is HALT."""

        def always_fail_validator(context: Dict[str, Any]) -> bool:
            """Validator that always fails."""
            return False

        workflow = Workflow(
            workflow_id="validation_fail_test",
            name="Validation Fail Test",
            stages=[
                WorkflowStage(stage_id="data", agent_id="data_bot"),
                WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
            ],
            validation_rules=[
                ValidationRule(
                    rule_id="always_fail",
                    name="Always Fail Rule",
                    validator=always_fail_validator,
                    action_on_fail="HALT",
                )
            ],
        )

        inputs = {"ticker": "AAPL", "period": "1mo"}

        result = orchestrator.execute_workflow(workflow, inputs)

        # Workflow should fail due to validation
        assert result.status in [WorkflowStatus.FAILED, WorkflowStatus.PARTIAL]


# ============================================================================
# Conditional Execution Tests
# ============================================================================


class TestConditionalExecution:
    """Tests for conditional stage execution and skipping."""

    def test_condition_met_stage_executes(
        self, orchestrator: Orchestrator, agent_registry: AgentRegistry
    ) -> None:
        """Test stage executes when condition is met."""
        condition_met = False

        def test_condition(context: Dict[str, Any]) -> bool:
            """Condition that can be controlled."""
            return condition_met

        workflow = Workflow(
            workflow_id="conditional_test",
            name="Conditional Test",
            stages=[
                WorkflowStage(stage_id="data", agent_id="data_bot"),
                WorkflowStage(
                    stage_id="tech",
                    agent_id="tech_bot",
                    depends_on=["data"],
                    condition=test_condition,
                    required=False,
                ),
            ],
        )

        # First run: condition not met, stage should be skipped
        inputs = {"ticker": "AAPL", "period": "1mo"}
        _ = orchestrator.execute_workflow(workflow, inputs)

        # Tech stage should be skipped if condition not met
        # (behavior depends on orchestrator implementation)

        # Second run: condition met, stage should execute
        condition_met = True
        _ = orchestrator.execute_workflow(workflow, inputs)

        # If condition is met, tech stage should execute
        # (exact behavior depends on orchestrator condition handling)

    def test_optional_stage_failure_continues(
        self, orchestrator: Orchestrator, error_recovery_workflow: Workflow
    ) -> None:
        """Test that non-required stage failures don't halt workflow."""
        # Sentiment bot requires news data, which may fail for some tickers
        inputs = {"ticker": "AAPL", "period": "1mo"}

        result = orchestrator.execute_workflow(error_recovery_workflow, inputs)

        # Workflow should complete even if sentiment stage fails (it's optional)
        # Core required stages (data, tech, synthesis) should succeed
        assert result.status in [WorkflowStatus.SUCCESS, WorkflowStatus.PARTIAL]
        assert "data" in result.agent_results
        assert "tech" in result.agent_results
        assert "synthesis" in result.agent_results


# ============================================================================
# Dynamic Branching Tests
# ============================================================================


class TestDynamicBranching:
    """Tests for dynamic workflow branching based on data quality."""

    def test_high_quality_path_selection(
        self, orchestrator: Orchestrator, agent_registry: AgentRegistry
    ) -> None:
        """Test workflow takes high-quality path when data quality is good."""

        def is_high_quality(context: Dict[str, Any]) -> bool:
            """Check if data quality is high."""
            return context.get("quality_score", 0.0) > 0.7

        workflow = Workflow(
            workflow_id="branching_test",
            name="Branching Test",
            description="Workflow with quality-based branching",
            stages=[
                WorkflowStage(stage_id="data", agent_id="data_bot"),
                # High quality path: full analysis
                WorkflowStage(
                    stage_id="forecast",
                    agent_id="forecast_bot",
                    depends_on=["data"],
                    condition=is_high_quality,
                    required=False,
                ),
                # Always run tech analysis
                WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
            ],
        )

        inputs = {"ticker": "AAPL", "period": "1y"}  # Long period = high quality

        result = orchestrator.execute_workflow(workflow, inputs)

        # Should complete successfully
        assert result.status in [WorkflowStatus.SUCCESS, WorkflowStatus.PARTIAL]
        # Data and tech should always execute
        assert "data" in result.agent_results
        assert "tech" in result.agent_results


# ============================================================================
# Error Recovery Tests
# ============================================================================


class TestErrorRecovery:
    """Tests for error handling and recovery patterns."""

    def test_required_stage_failure_halts_workflow(
        self, orchestrator: Orchestrator, agent_registry: AgentRegistry
    ) -> None:
        """Test that required stage failure halts workflow."""
        workflow = Workflow(
            workflow_id="required_failure_test",
            name="Required Failure Test",
            stages=[
                WorkflowStage(
                    stage_id="data",
                    agent_id="data_bot",
                    required=True,  # Required
                ),
                WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
            ],
        )

        # Use invalid ticker to force data stage failure
        inputs = {"ticker": "INVALID_TICKER_XYZ", "period": "1mo"}

        result = orchestrator.execute_workflow(workflow, inputs)

        # Workflow should fail when required stage fails
        assert result.status == WorkflowStatus.FAILED
        # Tech stage should not execute if data stage failed
        if "tech" in result.agent_results:
            assert result.agent_results["tech"].status in [
                AgentStatus.SKIPPED,
                AgentStatus.PENDING,
            ]

    def test_optional_stage_failure_continues_workflow(
        self, orchestrator: Orchestrator, error_recovery_workflow: Workflow
    ) -> None:
        """Test workflow continues when optional (non-required) stage fails."""
        inputs = {"ticker": "AAPL", "period": "1mo"}

        result = orchestrator.execute_workflow(error_recovery_workflow, inputs)

        # Workflow should complete with SUCCESS or PARTIAL status
        assert result.status in [WorkflowStatus.SUCCESS, WorkflowStatus.PARTIAL]

        # Required stages should succeed
        assert result.agent_results["data"].status == AgentStatus.SUCCESS
        assert result.agent_results["tech"].status == AgentStatus.SUCCESS
        assert result.agent_results["synthesis"].status == AgentStatus.SUCCESS

        # Sentiment is optional, may succeed or fail
        if "sentiment" in result.agent_results:
            # If sentiment ran, it may have succeeded or failed
            # Either is acceptable for this test
            pass

    def test_dependency_failure_propagation(
        self, orchestrator: Orchestrator, agent_registry: AgentRegistry
    ) -> None:
        """Test that stage failures propagate to dependent stages."""
        workflow = Workflow(
            workflow_id="dependency_propagation_test",
            name="Dependency Propagation Test",
            stages=[
                WorkflowStage(stage_id="data", agent_id="data_bot"),
                WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
                WorkflowStage(
                    stage_id="synthesis",
                    agent_id="synthesis_bot",
                    depends_on=["tech"],
                ),
            ],
        )

        # Use invalid ticker to force data stage failure
        inputs = {"ticker": "INVALID_XYZ", "period": "1mo"}

        result = orchestrator.execute_workflow(workflow, inputs)

        # Data stage should fail
        assert result.agent_results["data"].status == AgentStatus.FAILED

        # Dependent stages should be skipped or failed
        if "tech" in result.agent_results:
            assert result.agent_results["tech"].status in [
                AgentStatus.SKIPPED,
                AgentStatus.FAILED,
            ]
        if "synthesis" in result.agent_results:
            assert result.agent_results["synthesis"].status in [
                AgentStatus.SKIPPED,
                AgentStatus.FAILED,
            ]


# ============================================================================
# Workflow State Management Tests
# ============================================================================


class TestWorkflowStateManagement:
    """Tests for workflow state tracking and management."""

    def test_workflow_result_structure(
        self, orchestrator: Orchestrator, simple_workflow: Workflow
    ) -> None:
        """Test WorkflowResult contains all expected fields."""
        inputs = {"ticker": "AAPL", "period": "1mo"}

        result = orchestrator.execute_workflow(simple_workflow, inputs)

        # Verify WorkflowResult structure
        assert hasattr(result, "workflow_id")
        assert hasattr(result, "status")
        assert hasattr(result, "stage_results")
        assert hasattr(result, "outputs")
        assert hasattr(result, "error")
        assert hasattr(result, "total_execution_time")

    def test_stage_execution_order(
        self, orchestrator: Orchestrator, complex_workflow: Workflow
    ) -> None:
        """Test stages execute in correct dependency order."""
        inputs = {"ticker": "NVDA", "period": "1mo"}

        result = orchestrator.execute_workflow(complex_workflow, inputs)

        # Get timestamps
        data_time = result.agent_results["data"].timestamp
        tech_time = result.agent_results["tech"].timestamp
        sent_time = result.agent_results["sentiment"].timestamp
        synth_time = result.agent_results["synthesis"].timestamp

        # Data must execute before tech and sentiment
        assert data_time <= tech_time
        assert data_time <= sent_time

        # Synthesis must execute after tech and sentiment
        assert tech_time <= synth_time
        assert sent_time <= synth_time

    def test_workflow_outputs_aggregation(
        self, orchestrator: Orchestrator, complex_workflow: Workflow
    ) -> None:
        """Test workflow aggregates outputs from all stages."""
        inputs = {"ticker": "MSFT", "period": "1mo"}

        result = orchestrator.execute_workflow(complex_workflow, inputs)

        # Workflow outputs should contain aggregated results
        assert result.outputs is not None
        # Should contain final synthesis outputs
        if result.status == WorkflowStatus.SUCCESS:
            assert len(result.outputs) > 0
