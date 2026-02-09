"""Tests for the agentic RAG pipeline orchestrator."""

import pytest
from src.agents.agentic_rag import (
    AgenticRAG,
    AgenticRAGConfig,
    AgenticRAGResponse,
    ExecutionStep,
    ExecutionTrace,
)
from src.agents.query_planner import QueryPlanner
from src.agents.reflection import (
    ConfidenceScore,
    ReflectionConfig,
    ReflectionEngine,
)
from src.agents.tool_registry import (
    CalculatorTool,
    ToolRegistry,
    ToolResult,
    VectorSearchTool,
    WebSearchTool,
)


def _build_registry():
    registry = ToolRegistry()
    registry.register(VectorSearchTool())
    registry.register(WebSearchTool())
    registry.register(CalculatorTool())
    return registry


def _build_rag(config=None, registry=None):
    return AgenticRAG(
        config=config or AgenticRAGConfig(enable_compression=False),
        tool_registry=registry or _build_registry(),
        query_planner=QueryPlanner(),
        reflection_engine=ReflectionEngine(),
    )


class TestModels:
    def test_execution_step_valid(self):
        step = ExecutionStep(
            step_number=1,
            description="Search for info",
            tool_name="vector_search",
            status="completed",
        )
        assert step.step_number == 1
        assert step.tool_result is None

    def test_execution_step_invalid_number(self):
        with pytest.raises(Exception):
            ExecutionStep(step_number=0, description="bad", tool_name="test")

    def test_execution_trace_defaults(self):
        trace = ExecutionTrace()
        assert trace.steps == []
        assert trace.total_duration_ms == 0.0
        assert trace.iterations_used == 1

    def test_execution_trace_custom(self):
        trace = ExecutionTrace(total_duration_ms=100.0, iterations_used=2)
        assert trace.iterations_used == 2

    def test_agentic_rag_response(self):
        response = AgenticRAGResponse(
            answer="test answer",
            confidence=ConfidenceScore(overall=0.8),
            sources=[],
            trace=ExecutionTrace(),
        )
        assert response.answer == "test answer"
        assert response.quality is None


class TestAgenticRAGConfig:
    def test_defaults(self):
        config = AgenticRAGConfig()
        assert config.max_iterations == 3
        assert config.quality_threshold == 0.7
        assert config.enable_reflection is True
        assert config.enable_compression is True
        assert config.top_k == 10

    def test_custom(self):
        config = AgenticRAGConfig(max_iterations=5, quality_threshold=0.9, enable_reflection=False)
        assert config.max_iterations == 5
        assert config.enable_reflection is False


class TestLifecycle:
    async def test_initialize_and_close(self):
        rag = _build_rag()
        assert rag._initialized is False
        await rag.initialize()
        assert rag._initialized is True
        await rag.close()
        assert rag._initialized is False


class TestSimpleQueries:
    async def test_basic_retrieval_query(self):
        rag = _build_rag()
        response = await rag.query("What is machine learning?")
        assert isinstance(response, AgenticRAGResponse)
        assert len(response.answer) > 0
        assert response.answer != "No information available to answer this query."
        assert response.confidence.overall > 0.0
        assert len(response.trace.steps) >= 1
        assert response.trace.total_duration_ms > 0

    async def test_definition_query(self):
        rag = _build_rag()
        response = await rag.query("What is Python?")
        assert len(response.answer) > 0
        assert any(s["tool"] == "vector_search" for s in response.sources)

    async def test_empty_query_raises(self):
        rag = _build_rag()
        with pytest.raises(ValueError, match="empty"):
            await rag.query("")

    async def test_whitespace_query_raises(self):
        rag = _build_rag()
        with pytest.raises(ValueError, match="empty"):
            await rag.query("   ")


class TestMultiStepQueries:
    async def test_comparison_query(self):
        rag = _build_rag()
        response = await rag.query("Compare Python vs Rust for web development")
        assert len(response.trace.steps) >= 1
        assert response.confidence.overall > 0.0

    async def test_calculation_query(self):
        rag = _build_rag()
        response = await rag.query("Calculate the average of 10 and 20")
        assert len(response.trace.steps) >= 1


class TestReflectionLoop:
    async def test_reflection_enabled(self):
        config = AgenticRAGConfig(enable_reflection=True, enable_compression=False)
        rag = _build_rag(config=config)
        response = await rag.query("Tell me about artificial intelligence")
        assert response.quality is not None or response.trace.iterations_used >= 1

    async def test_reflection_disabled(self):
        config = AgenticRAGConfig(enable_reflection=False, enable_compression=False)
        rag = _build_rag(config=config)
        response = await rag.query("What is deep learning?")
        assert response.quality is None
        assert response.trace.iterations_used == 1

    async def test_max_iterations_respected(self):
        config = AgenticRAGConfig(max_iterations=1, enable_reflection=True, enable_compression=False)
        rag = _build_rag(config=config)
        response = await rag.query("Tell me about unknown topics in science")
        assert response.trace.iterations_used <= 2

    async def test_forced_iteration_with_high_threshold(self):
        reflection_config = ReflectionConfig(quality_threshold=0.99, max_iterations=2)
        config = AgenticRAGConfig(
            max_iterations=2,
            enable_reflection=True,
            enable_compression=False,
            quality_threshold=0.99,
        )
        rag = AgenticRAG(
            config=config,
            tool_registry=_build_registry(),
            query_planner=QueryPlanner(),
            reflection_engine=ReflectionEngine(reflection_config),
        )
        response = await rag.query("Tell me about quantum computing applications")
        assert response.quality is not None
        assert response.trace.iterations_used >= 1


class TestToolFailures:
    async def test_unregistered_tool_handled(self):
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        rag = AgenticRAG(
            config=AgenticRAGConfig(enable_reflection=False, enable_compression=False),
            tool_registry=registry,
            query_planner=QueryPlanner(),
            reflection_engine=ReflectionEngine(),
        )
        response = await rag.query("What is machine learning?")
        assert isinstance(response, AgenticRAGResponse)

    async def test_all_tools_fail(self):
        registry = ToolRegistry()
        rag = AgenticRAG(
            config=AgenticRAGConfig(enable_reflection=False, enable_compression=False),
            tool_registry=registry,
            query_planner=QueryPlanner(),
        )
        response = await rag.query("What is anything?")
        assert "no" in response.answer.lower() or "No" in response.answer


class TestSources:
    async def test_sources_collected(self):
        rag = _build_rag()
        response = await rag.query("What is neural network architecture?")
        assert len(response.sources) > 0
        for source in response.sources:
            assert "tool" in source
            assert "content" in source

    async def test_sources_empty_on_failure(self):
        registry = ToolRegistry()
        rag = AgenticRAG(
            config=AgenticRAGConfig(enable_reflection=False, enable_compression=False),
            tool_registry=registry,
        )
        response = await rag.query("Anything")
        assert response.sources == []


class TestExecutionTraceTests:
    async def test_trace_records_steps(self):
        rag = _build_rag()
        response = await rag.query("Explain transformers in NLP")
        trace = response.trace
        assert len(trace.steps) >= 1
        for step in trace.steps:
            assert step.step_number >= 1
            assert step.tool_name
            assert step.status in ("completed", "failed", "pending")

    async def test_trace_duration_positive(self):
        rag = _build_rag()
        response = await rag.query("What is reinforcement learning?")
        assert response.trace.total_duration_ms > 0

    async def test_step_tool_result_recorded(self):
        rag = _build_rag()
        response = await rag.query("What is NLP?")
        completed = [s for s in response.trace.steps if s.status == "completed"]
        assert len(completed) >= 1
        for step in completed:
            assert step.tool_result is not None
            assert step.tool_result.success is True


class TestAnswerSynthesis:
    def test_synthesize_empty_results(self):
        rag = _build_rag()
        answer = rag._synthesize_answer("query", [])
        assert answer == "No information available to answer this query."

    def test_synthesize_all_failures(self):
        rag = _build_rag()
        results = [ToolResult(tool_name="test", success=False, data=None)]
        answer = rag._synthesize_answer("query", results)
        assert answer == "No relevant information found for the query."

    def test_synthesize_with_search_results(self):
        rag = _build_rag()
        results = [
            ToolResult(
                tool_name="vector_search",
                success=True,
                data={
                    "results": [
                        {"content": "ML is a field of AI.", "score": 0.9},
                        {"content": "It uses statistical methods.", "score": 0.8},
                    ]
                },
            ),
        ]
        answer = rag._synthesize_answer("What is ML?", results)
        assert "ML is a field of AI" in answer
        assert "statistical methods" in answer

    def test_synthesize_with_calculation(self):
        rag = _build_rag()
        results = [
            ToolResult(
                tool_name="calculator",
                success=True,
                data={"result": 42, "expression": "6 * 7"},
            ),
        ]
        answer = rag._synthesize_answer("calculate 6*7", results)
        assert "42" in answer

    def test_synthesize_deduplicates(self):
        rag = _build_rag()
        results = [
            ToolResult(
                tool_name="vector_search",
                success=True,
                data={"results": [{"content": "Same content.", "score": 0.9}]},
            ),
            ToolResult(
                tool_name="vector_search",
                success=True,
                data={"results": [{"content": "Same content.", "score": 0.8}]},
            ),
        ]
        answer = rag._synthesize_answer("query", results)
        assert answer.count("Same content.") == 1


class TestCollectSources:
    def test_collect_from_search(self):
        rag = _build_rag()
        results = [
            ToolResult(
                tool_name="vector_search",
                success=True,
                data={
                    "results": [
                        {"content": "result 1", "score": 0.9, "metadata": {"source": "a"}},
                    ]
                },
            ),
        ]
        sources = rag._collect_sources(results)
        assert len(sources) == 1
        assert sources[0]["tool"] == "vector_search"
        assert sources[0]["score"] == 0.9

    def test_collect_skips_failures(self):
        rag = _build_rag()
        results = [ToolResult(tool_name="web_search", success=False, data=None)]
        sources = rag._collect_sources(results)
        assert sources == []

    def test_collect_from_multiple_tools(self):
        rag = _build_rag()
        results = [
            ToolResult(
                tool_name="vector_search",
                success=True,
                data={"results": [{"content": "a", "score": 0.9}]},
            ),
            ToolResult(
                tool_name="web_search",
                success=True,
                data={"results": [{"snippet": "b", "score": 0.7}]},
            ),
        ]
        sources = rag._collect_sources(results)
        assert len(sources) == 2


class TestFullPipeline:
    async def test_end_to_end_retrieval(self):
        rag = _build_rag()
        await rag.initialize()
        response = await rag.query("What is machine learning?")
        assert isinstance(response, AgenticRAGResponse)
        assert len(response.answer) > 0
        assert response.confidence.overall > 0.0
        assert len(response.trace.steps) >= 1
        assert len(response.sources) > 0
        await rag.close()

    async def test_end_to_end_comparison(self):
        rag = _build_rag()
        response = await rag.query("Compare Python versus Java for backend")
        assert len(response.trace.steps) >= 1
        assert response.confidence.overall > 0.0

    async def test_end_to_end_with_reflection(self):
        reflection_config = ReflectionConfig(quality_threshold=0.99, max_iterations=2)
        config = AgenticRAGConfig(
            max_iterations=2,
            enable_reflection=True,
            enable_compression=False,
            quality_threshold=0.99,
        )
        rag = AgenticRAG(
            config=config,
            tool_registry=_build_registry(),
            query_planner=QueryPlanner(),
            reflection_engine=ReflectionEngine(reflection_config),
        )
        response = await rag.query("Tell me about quantum computing applications")
        assert response.quality is not None
        assert response.trace.iterations_used >= 1

    async def test_end_to_end_no_reflection(self):
        config = AgenticRAGConfig(enable_reflection=False, enable_compression=False)
        rag = _build_rag(config=config)
        response = await rag.query("Define gradient descent")
        assert response.quality is None
        assert response.answer

    async def test_imports_from_package(self):
        from src.agents import (
            AgenticRAG,
            AgenticRAGConfig,
        )

        assert AgenticRAG is not None
        assert AgenticRAGConfig is not None
