"""Tests for AgentForge observability module.

Tests for:
- TracerConfig validation
- AgentTracer context managers
- TokenUsage aggregation
- MetricsCollector operations
- ASCIIDashboard rendering
- Global instances
"""

import asyncio
import inspect

from agentforge.observe.dashboard import (
    ASCIIDashboard,
    Dashboard,
    DashboardConfig,
    StructuredLogger,
    create_dashboard,
)
from agentforge.observe.metrics import (
    CostRecord,
    LatencyStats,
    MetricsCollector,
    TokenUsage,
    get_metrics,
    reset_metrics,
)
from agentforge.observe.tracer import (
    AgentTracer,
    TracerConfig,
    get_tracer,
    reset_tracer,
)


class TestTracerConfig:
    """Tests for TracerConfig validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TracerConfig()
        assert config.service_name == "agentforge"
        assert config.service_version == "0.2.0"
        assert config.export_console is True
        assert config.export_otlp is False
        assert config.otlp_endpoint is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TracerConfig(
            service_name="my-service",
            service_version="1.0.0",
            export_console=False,
            export_otlp=True,
            otlp_endpoint="http://localhost:4317",
        )
        assert config.service_name == "my-service"
        assert config.service_version == "1.0.0"
        assert config.export_console is False
        assert config.export_otlp is True
        assert config.otlp_endpoint == "http://localhost:4317"


class TestAgentTracer:
    """Tests for AgentTracer context managers."""

    def test_tracer_initialization(self):
        """Test tracer initializes correctly."""
        tracer = AgentTracer()
        assert tracer.config is not None
        assert tracer.tracer is not None

    def test_tracer_with_config(self):
        """Test tracer with custom config."""
        config = TracerConfig(service_name="test-service")
        tracer = AgentTracer(config)
        assert tracer.config.service_name == "test-service"

    def test_trace_agent_context_manager(self):
        """Test trace_agent context manager."""
        tracer = AgentTracer()

        with tracer.trace_agent("test-agent") as span:
            # Span should exist (may be no-op if OTel not available)
            assert span is not None

    def test_trace_tool_call_context_manager(self):
        """Test trace_tool_call context manager."""
        tracer = AgentTracer()

        with tracer.trace_tool_call("search", "test-agent") as span:
            assert span is not None

    def test_trace_llm_call_context_manager(self):
        """Test trace_llm_call context manager."""
        tracer = AgentTracer()

        with tracer.trace_llm_call("gpt-4o", "openai") as span:
            assert span is not None

    def test_trace_dag_execution_context_manager(self):
        """Test trace_dag_execution context manager."""
        tracer = AgentTracer()

        with tracer.trace_dag_execution("test-dag", 5) as span:
            assert span is not None

    def test_record_llm_usage(self):
        """Test record_llm_usage method."""
        tracer = AgentTracer()

        with tracer.trace_llm_call("gpt-4o") as span:
            tracer.record_llm_usage(span, 100, 50, 0.002)
            # Should not raise

    def test_record_error(self):
        """Test record_error method."""
        tracer = AgentTracer()

        with tracer.trace_agent("test-agent") as span:
            tracer.record_error(span, Exception("Test error"))
            # Should not raise

    def test_trace_function_decorator_async(self):
        """Test trace_function decorator with async function."""
        tracer = AgentTracer()

        @tracer.trace_function("test-operation")
        async def async_operation():
            return "result"

        # Should be a coroutine function
        assert inspect.iscoroutinefunction(async_operation)

        # Run it
        result = asyncio.run(async_operation())
        assert result == "result"

    def test_trace_function_decorator_sync(self):
        """Test trace_function decorator with sync function."""
        tracer = AgentTracer()

        @tracer.trace_function("test-operation")
        def sync_operation():
            return "result"

        # Should not be a coroutine function
        assert not inspect.iscoroutinefunction(sync_operation)

        # Run it
        result = sync_operation()
        assert result == "result"


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_default_values(self):
        """Test default token usage values."""
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_custom_values(self):
        """Test custom token usage values."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_addition(self):
        """Test TokenUsage addition."""
        usage1 = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        usage2 = TokenUsage(prompt_tokens=200, completion_tokens=100, total_tokens=300)

        result = usage1 + usage2

        assert result.prompt_tokens == 300
        assert result.completion_tokens == 150
        assert result.total_tokens == 450

    def test_from_dict(self):
        """Test TokenUsage.from_dict class method."""
        usage = TokenUsage.from_dict({
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        })

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_from_dict_missing_keys(self):
        """Test from_dict with missing keys."""
        usage = TokenUsage.from_dict({})

        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0


class TestCostRecord:
    """Tests for CostRecord model."""

    def test_default_values(self):
        """Test default cost record values."""
        cost = CostRecord(amount=0.002, model="gpt-4o")

        assert cost.amount == 0.002
        assert cost.model == "gpt-4o"
        assert cost.provider == "unknown"
        assert cost.timestamp is not None
        assert cost.tokens is None
        assert cost.metadata is None

    def test_custom_values(self):
        """Test custom cost record values."""
        tokens = TokenUsage(prompt_tokens=100, completion_tokens=50)
        cost = CostRecord(
            amount=0.005,
            model="claude-3-opus",
            provider="anthropic",
            tokens=tokens,
            metadata={"request_id": "abc123"},
        )

        assert cost.amount == 0.005
        assert cost.model == "claude-3-opus"
        assert cost.provider == "anthropic"
        assert cost.tokens == tokens
        assert cost.metadata == {"request_id": "abc123"}


class TestLatencyStats:
    """Tests for LatencyStats model."""

    def test_default_values(self):
        """Test default latency stats values."""
        stats = LatencyStats()

        assert stats.p50 == 0.0
        assert stats.p95 == 0.0
        assert stats.p99 == 0.0
        assert stats.avg == 0.0
        assert stats.count == 0


class TestMetricsCollector:
    """Tests for MetricsCollector operations."""

    def setup_method(self):
        """Reset metrics before each test."""
        reset_metrics()

    def test_initialization(self):
        """Test collector initializes correctly."""
        collector = MetricsCollector()

        assert collector.agent_count == 0
        assert collector.cost_count == 0

    def test_record_tokens(self):
        """Test recording token usage."""
        collector = MetricsCollector()

        collector.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))

        assert collector.agent_count == 1
        agent_tokens = collector.get_agent_tokens("agent-1")
        assert agent_tokens is not None
        assert agent_tokens.prompt_tokens == 100
        assert agent_tokens.completion_tokens == 50

    def test_record_tokens_multiple_agents(self):
        """Test recording tokens for multiple agents."""
        collector = MetricsCollector()

        collector.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))
        collector.record_tokens("agent-2", TokenUsage(prompt_tokens=200, completion_tokens=100, total_tokens=300))

        assert collector.agent_count == 2
        total = collector.get_total_tokens()
        assert total.prompt_tokens == 300
        assert total.completion_tokens == 150

    def test_record_tokens_accumulates(self):
        """Test that recording tokens accumulates for same agent."""
        collector = MetricsCollector()

        collector.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))
        collector.record_tokens("agent-1", TokenUsage(prompt_tokens=50, completion_tokens=25, total_tokens=75))

        agent_tokens = collector.get_agent_tokens("agent-1")
        assert agent_tokens.prompt_tokens == 150
        assert agent_tokens.completion_tokens == 75

    def test_record_cost(self):
        """Test recording cost."""
        collector = MetricsCollector()

        collector.record_cost(CostRecord(amount=0.002, model="gpt-4o"))

        assert collector.cost_count == 1
        assert collector.get_total_cost() == 0.002

    def test_record_cost_simple(self):
        """Test simplified cost recording."""
        collector = MetricsCollector()

        collector.record_cost_simple(0.005, "claude-3-opus", "anthropic")

        assert collector.cost_count == 1
        assert collector.get_total_cost() == 0.005

    def test_get_cost_by_model(self):
        """Test grouping costs by model."""
        collector = MetricsCollector()

        collector.record_cost_simple(0.002, "gpt-4o")
        collector.record_cost_simple(0.003, "gpt-4o")
        collector.record_cost_simple(0.005, "claude-3-opus")

        costs = collector.get_cost_by_model()
        assert costs["gpt-4o"] == 0.005
        assert costs["claude-3-opus"] == 0.005

    def test_latency_timing(self):
        """Test latency timing."""
        collector = MetricsCollector()

        collector.start_timer("llm_call")
        import time
        time.sleep(0.01)  # 10ms
        latency = collector.end_timer("llm_call")

        assert latency >= 0.01
        stats = collector.get_latency_stats("llm_call")
        assert stats.count == 1
        assert stats.avg >= 0.01

    def test_get_latency_stats_empty(self):
        """Test latency stats for unknown operation."""
        collector = MetricsCollector()

        stats = collector.get_latency_stats("unknown")

        assert stats.p50 == 0.0
        assert stats.count == 0

    def test_get_summary(self):
        """Test get_summary method."""
        collector = MetricsCollector()

        collector.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))
        collector.record_cost_simple(0.002, "gpt-4o")

        summary = collector.get_summary()

        assert "tokens" in summary
        assert "cost_usd" in summary
        assert "latencies" in summary
        assert "agent_tokens" in summary
        assert summary["cost_usd"] == 0.002

    def test_clear(self):
        """Test clearing metrics."""
        collector = MetricsCollector()

        collector.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))
        collector.record_cost_simple(0.002, "gpt-4o")

        collector.clear()

        assert collector.agent_count == 0
        assert collector.cost_count == 0


class TestASCIIDashboard:
    """Tests for ASCIIDashboard rendering."""

    def test_initialization(self):
        """Test dashboard initializes correctly."""
        dashboard = ASCIIDashboard()

        assert dashboard.config is not None
        assert dashboard._metrics is None

    def test_with_config(self):
        """Test dashboard with custom config."""
        config = DashboardConfig(width=60, show_costs=False)
        dashboard = ASCIIDashboard(config)

        assert dashboard.config.width == 60
        assert dashboard.config.show_costs is False

    def test_render_no_metrics(self):
        """Test render without metrics attached."""
        dashboard = ASCIIDashboard()

        result = dashboard.render()

        assert result == "No metrics attached"

    def test_render_with_metrics(self):
        """Test render with metrics attached."""
        dashboard = ASCIIDashboard()
        metrics = MetricsCollector()

        metrics.record_tokens("agent-1", TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150))
        metrics.record_cost_simple(0.002, "gpt-4o")

        dashboard.attach(metrics)
        result = dashboard.render()

        assert "AgentForge Dashboard" in result
        assert "Token Usage" in result
        assert "Costs" in result

    def test_attach_detach(self):
        """Test attach and detach methods."""
        dashboard = ASCIIDashboard()
        metrics = MetricsCollector()

        dashboard.attach(metrics)
        assert dashboard._metrics is not None

        dashboard.detach()
        assert dashboard._metrics is None

    def test_str_representation(self):
        """Test string representation."""
        dashboard = ASCIIDashboard()
        metrics = MetricsCollector()

        dashboard.attach(metrics)

        str_result = str(dashboard)
        assert "AgentForge Dashboard" in str_result

    def test_repr(self):
        """Test developer representation."""
        dashboard = ASCIIDashboard()

        repr_result = repr(dashboard)
        assert "ASCIIDashboard" in repr_result
        assert "attached=False" in repr_result


class TestDashboard:
    """Tests for the original Dashboard class."""

    def test_initialization(self):
        """Test dashboard initializes correctly."""
        dashboard = Dashboard()

        assert dashboard.title == "AgentForge Dashboard"
        assert dashboard.max_history == 100

    def test_record_execution(self):
        """Test recording execution."""
        dashboard = Dashboard()

        dashboard.record_execution(
            agent_id="agent-1",
            status="completed",
            duration_ms=150.5,
            tokens=100,
        )

        assert len(dashboard._executions) == 1
        assert dashboard._agent_status["agent-1"] == "completed"

    def test_update_agent_status(self):
        """Test updating agent status."""
        dashboard = Dashboard()

        dashboard.update_agent_status("agent-1", "running")

        assert dashboard._agent_status["agent-1"] == "running"

    def test_render(self):
        """Test render method."""
        dashboard = Dashboard()

        dashboard.record_execution(
            agent_id="agent-1",
            status="completed",
            duration_ms=150.5,
            tokens=100,
        )

        result = dashboard.render()

        assert "AgentForge Dashboard" in result
        assert "AGENT STATUS" in result
        assert "STATISTICS" in result

    def test_render_compact(self):
        """Test compact render."""
        dashboard = Dashboard()

        dashboard.record_execution(
            agent_id="agent-1",
            status="completed",
            duration_ms=150.5,
            tokens=100,
        )

        result = dashboard.render_compact()

        assert "[AgentForge]" in result
        assert "Execs:" in result

    def test_max_history(self):
        """Test max history trimming."""
        dashboard = Dashboard(max_history=10)

        for i in range(20):
            dashboard.record_execution(
                agent_id=f"agent-{i}",
                status="completed",
            )

        assert len(dashboard._executions) == 10


class TestStructuredLogger:
    """Tests for StructuredLogger."""

    def test_initialization(self):
        """Test logger initializes correctly."""
        logger = StructuredLogger("test-logger")

        assert logger.name == "test-logger"
        assert logger.level == "INFO"

    def test_info_log(self, capsys):
        """Test info logging."""
        logger = StructuredLogger("test-logger")

        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        assert '"level": "INFO"' in captured.out
        assert '"event": "test_event"' in captured.out
        assert '"key": "value"' in captured.out

    def test_error_log(self, capsys):
        """Test error logging."""
        logger = StructuredLogger("test-logger")

        logger.error("error_event", message="Something went wrong")

        captured = capsys.readouterr()
        assert '"level": "ERROR"' in captured.out

    def test_debug_filtered(self, capsys):
        """Test debug is filtered by default."""
        logger = StructuredLogger("test-logger", level="INFO")

        logger.debug("debug_event")

        captured = capsys.readouterr()
        assert "debug_event" not in captured.out


class TestGlobalInstances:
    """Tests for global instance management."""

    def setup_method(self):
        """Reset global instances before each test."""
        reset_tracer()
        reset_metrics()

    def test_get_tracer_singleton(self):
        """Test get_tracer returns singleton."""
        tracer1 = get_tracer()
        tracer2 = get_tracer()

        assert tracer1 is tracer2

    def test_get_metrics_singleton(self):
        """Test get_metrics returns singleton."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    def test_reset_tracer(self):
        """Test reset_tracer creates new instance."""
        tracer1 = get_tracer()
        reset_tracer()
        tracer2 = get_tracer()

        assert tracer1 is not tracer2

    def test_reset_metrics(self):
        """Test reset_metrics creates new instance."""
        metrics1 = get_metrics()
        reset_metrics()
        metrics2 = get_metrics()

        assert metrics1 is not metrics2


class TestCreateDashboard:
    """Tests for create_dashboard factory function."""

    def test_create_dashboard_no_metrics(self):
        """Test creating dashboard without metrics."""
        dashboard = create_dashboard()

        assert dashboard._metrics is None

    def test_create_dashboard_with_metrics(self):
        """Test creating dashboard with metrics."""
        metrics = MetricsCollector()
        dashboard = create_dashboard(metrics)

        assert dashboard._metrics is metrics

    def test_create_dashboard_with_config(self):
        """Test creating dashboard with config options."""
        dashboard = create_dashboard(width=60, show_costs=False)

        assert dashboard.config.width == 60
        assert dashboard.config.show_costs is False


class TestDashboardConfig:
    """Tests for DashboardConfig validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DashboardConfig()

        assert config.refresh_rate == 1.0
        assert config.show_tokens is True
        assert config.show_costs is True
        assert config.show_latencies is True
        assert config.show_agents is True
        assert config.width == 50

    def test_custom_config(self):
        """Test custom configuration values."""
        config = DashboardConfig(
            refresh_rate=2.0,
            show_tokens=False,
            width=60,
        )

        assert config.refresh_rate == 2.0
        assert config.show_tokens is False
        assert config.width == 60
