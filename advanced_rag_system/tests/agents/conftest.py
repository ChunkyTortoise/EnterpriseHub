"""Pytest configuration and shared fixtures for agentic RAG tests."""

from unittest.mock import Mock

import pytest
from src.agents.agentic_rag import AgenticRAG
from src.agents.query_planner import IntentAnalysis, QueryIntent, QueryPlan, QueryPlanner
from src.agents.reflection import ReflectionEngine
from src.agents.tool_registry import CalculatorTool, ToolRegistry, VectorSearchTool


@pytest.fixture
def query_planner():
    """Provide a query planner instance."""
    return QueryPlanner()


@pytest.fixture
def tool_registry():
    """Provide a tool registry with default tools."""
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(VectorSearchTool())
    return registry


@pytest.fixture
def reflection_engine():
    """Provide a reflection engine instance."""
    return ReflectionEngine()


@pytest.fixture
async def agentic_rag():
    """Provide an initialized agentic RAG instance."""
    rag = AgenticRAG()
    await rag.initialize()
    yield rag
    await rag.close()


@pytest.fixture
def mock_query_plan():
    """Provide a mock query plan."""
    plan = Mock(spec=QueryPlan)
    plan.intent_analysis = Mock(spec=IntentAnalysis)
    plan.intent_analysis.intent = QueryIntent.RETRIEVAL
    plan.intent_analysis.keywords = ["test", "query"]
    plan.intent_analysis.entities = ["Entity"]
    plan.steps = []
    return plan


@pytest.fixture
def sample_tool_results():
    """Provide sample tool results for testing."""
    from src.agents.tool_registry import ToolResult

    return [
        ToolResult(
            tool_name="vector_search",
            success=True,
            data={"results": [{"content": "Result 1"}, {"content": "Result 2"}]},
        ),
        ToolResult(
            tool_name="calculator",
            success=True,
            data={"result": 42},
        ),
    ]
