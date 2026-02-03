"""Tests for the tool registry module."""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.agents.tool_registry import (
    CalculatorTool,
    ToolExecutionError,
    ToolMetadata,
    ToolRegistry,
    ToolResult,
    VectorSearchTool,
    WebSearchTool,
)


class TestToolResult:
    """Tests for ToolResult model."""
    
    def test_tool_result_success(self):
        """Test successful tool result."""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            data={"key": "value"},
            execution_time_ms=100.0,
        )
        
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
    
    def test_tool_result_failure(self):
        """Test failed tool result."""
        result = ToolResult(
            tool_name="test_tool",
            success=False,
            error="Something went wrong",
            execution_time_ms=50.0,
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
    
    def test_tool_result_error_validation(self):
        """Test that error is required for failed results."""
        # This should auto-set error to "Unknown error"
        result = ToolResult(
            tool_name="test_tool",
            success=False,
        )
        
        assert result.error == "Unknown error"


class TestToolMetadata:
    """Tests for ToolMetadata model."""
    
    def test_metadata_defaults(self):
        """Test default metadata values."""
        metadata = ToolMetadata(
            name="test_tool",
            description="A test tool",
        )
        
        assert metadata.version == "1.0.0"
        assert metadata.rate_limit_per_minute == 60
        assert metadata.timeout_seconds == 30.0
        assert metadata.required_credentials == []


class TestVectorSearchTool:
    """Tests for VectorSearchTool."""
    
    @pytest.mark.asyncio
    async def test_vector_search_tool_execution(self):
        """Test vector search tool execution."""
        tool = VectorSearchTool()
        
        result = await tool.execute(query="machine learning", top_k=5)
        
        assert result.success is True
        assert result.tool_name == "vector_search"
        assert "results" in result.data
        assert result.data["query"] == "machine learning"
    
    @pytest.mark.asyncio
    async def test_vector_search_tool_with_filters(self):
        """Test vector search with filters."""
        tool = VectorSearchTool()
        
        result = await tool.execute(
            query="python",
            top_k=3,
            filters={"category": "programming"},
        )
        
        assert result.success is True
        assert result.metadata["filters"] == {"category": "programming"}
    
    def test_vector_search_metadata(self):
        """Test vector search tool metadata."""
        tool = VectorSearchTool()
        metadata = tool.metadata
        
        assert metadata.name == "vector_search"
        assert "vector" in metadata.description.lower()
        assert "query" in metadata.parameters["properties"]


class TestWebSearchTool:
    """Tests for WebSearchTool."""
    
    @pytest.mark.asyncio
    async def test_web_search_mock_results(self):
        """Test web search returns mock results without API key."""
        tool = WebSearchTool()
        
        result = await tool.execute(query="python programming", num_results=3)
        
        assert result.success is True
        assert result.tool_name == "web_search"
        assert "results" in result.data
        assert result.data["provider"] == "mock"
    
    @pytest.mark.asyncio
    async def test_web_search_with_api_key(self):
        """Test web search with mock API key."""
        with patch.dict("os.environ", {"SERPER_API_KEY": "test_key"}):
            tool = WebSearchTool()
            
            # Mock the actual API call
            with patch.object(tool, '_search_serper', return_value=[
                {"title": "Test", "link": "http://test.com", "snippet": "Test result"}
            ]):
                result = await tool.execute(query="test query")
                
                assert result.success is True
                assert "results" in result.data
    
    def test_web_search_metadata(self):
        """Test web search tool metadata."""
        tool = WebSearchTool()
        metadata = tool.metadata
        
        assert metadata.name == "web_search"
        assert "web" in metadata.description.lower()
        assert "SERPER_API_KEY" in metadata.required_credentials
    
    @pytest.mark.asyncio
    async def test_web_search_close_session(self):
        """Test closing web search tool session."""
        tool = WebSearchTool()
        
        # Execute to potentially create session
        await tool.execute(query="test")
        
        # Should not raise
        await tool.close()


class TestCalculatorTool:
    """Tests for CalculatorTool."""
    
    @pytest.mark.asyncio
    async def test_calculator_basic_math(self):
        """Test basic mathematical operations."""
        tool = CalculatorTool()
        
        result = await tool.execute(expression="2 + 2")
        
        assert result.success is True
        assert result.data["result"] == 4
    
    @pytest.mark.asyncio
    async def test_calculator_advanced(self):
        """Test advanced mathematical expressions."""
        tool = CalculatorTool()
        
        result = await tool.execute(expression="sqrt(16) + pow(2, 3)")
        
        assert result.success is True
        assert result.data["result"] == 12.0  # 4 + 8
    
    @pytest.mark.asyncio
    async def test_calculator_with_variables(self):
        """Test calculator with variables."""
        tool = CalculatorTool()
        
        result = await tool.execute(
            expression="x + y",
            variables={"x": 10, "y": 20},
        )
        
        assert result.success is True
        assert result.data["result"] == 30
    
    @pytest.mark.asyncio
    async def test_calculator_safety_forbidden_patterns(self):
        """Test calculator rejects dangerous patterns."""
        tool = CalculatorTool()
        
        # Test import statement
        result = await tool.execute(expression="__import__('os')")
        assert result.success is False
        assert "Forbidden" in result.error or "Validation failed" in result.error
    
    @pytest.mark.asyncio
    async def test_calculator_safety_exec(self):
        """Test calculator rejects exec."""
        tool = CalculatorTool()
        
        result = await tool.execute(expression="exec('print(1)')")
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_calculator_division_by_zero(self):
        """Test calculator handles division by zero."""
        tool = CalculatorTool()
        
        result = await tool.execute(expression="1 / 0")
        
        assert result.success is False
        assert "zero" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_calculator_word_replacement(self):
        """Test calculator replaces words with operators."""
        tool = CalculatorTool()
        
        result = await tool.execute(expression="10 plus 5")
        
        assert result.success is True
        assert result.data["result"] == 15
    
    def test_calculator_metadata(self):
        """Test calculator tool metadata."""
        tool = CalculatorTool()
        metadata = tool.metadata
        
        assert metadata.name == "calculator"
        assert "math" in metadata.description.lower()
        assert "expression" in metadata.parameters["properties"]


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        
        registry.register(tool)
        
        assert "calculator" in registry.list_tools()
    
    def test_register_duplicate_tool_raises(self):
        """Test registering duplicate tool raises error."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        
        registry.register(tool)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)
    
    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        
        registry.register(tool)
        result = registry.unregister("calculator")
        
        assert result is True
        assert "calculator" not in registry.list_tools()
    
    def test_unregister_nonexistent_tool(self):
        """Test unregistering non-existent tool."""
        registry = ToolRegistry()
        
        result = registry.unregister("nonexistent")
        
        assert result is False
    
    def test_get_tool(self):
        """Test getting a tool by name."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        
        registry.register(tool)
        retrieved = registry.get_tool("calculator")
        
        assert retrieved is not None
        assert retrieved.metadata.name == "calculator"
    
    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool returns None."""
        registry = ToolRegistry()
        
        retrieved = registry.get_tool("nonexistent")
        
        assert retrieved is None
    
    def test_get_tool_schemas(self):
        """Test getting all tool schemas."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(VectorSearchTool())
        
        schemas = registry.get_tool_schemas()
        
        assert len(schemas) == 2
        names = [s["name"] for s in schemas]
        assert "calculator" in names
        assert "vector_search" in names
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a registered tool."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        
        result = await registry.execute("calculator", expression="5 * 5")
        
        assert result.success is True
        assert result.data["result"] == 25
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing non-existent tool."""
        registry = ToolRegistry()
        
        result = await registry.execute("nonexistent", param="value")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_multiple_tools(self):
        """Test executing multiple tools in parallel."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        
        executions = [
            ("calculator", {"expression": "1 + 1"}),
            ("calculator", {"expression": "2 + 2"}),
        ]
        
        results = await registry.execute_multiple(executions)
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].data["result"] == 2
        assert results[1].data["result"] == 4
    
    def test_aggregate_results_concatenate(self):
        """Test result aggregation with concatenate strategy."""
        registry = ToolRegistry()
        
        results = [
            ToolResult(
                tool_name="tool1",
                success=True,
                data={"results": [{"content": "A"}]},
            ),
            ToolResult(
                tool_name="tool2",
                success=True,
                data={"results": [{"content": "B"}]},
            ),
        ]
        
        aggregated = registry.aggregate_results(results, strategy="concatenate")
        
        assert "items" in aggregated
        assert len(aggregated["items"]) == 2
    
    def test_aggregate_results_merge(self):
        """Test result aggregation with merge strategy."""
        registry = ToolRegistry()
        
        results = [
            ToolResult(
                tool_name="tool1",
                success=True,
                data={"key1": ["A"]},
            ),
            ToolResult(
                tool_name="tool2",
                success=True,
                data={"key1": ["B"]},
            ),
        ]
        
        aggregated = registry.aggregate_results(results, strategy="merge")
        
        assert "key1" in aggregated
        assert len(aggregated["key1"]) == 2
    
    def test_aggregate_results_rank(self):
        """Test result aggregation with rank strategy."""
        registry = ToolRegistry()
        
        results = [
            ToolResult(
                tool_name="tool1",
                success=True,
                data={"results": [{"content": "A", "score": 0.9}]},
            ),
            ToolResult(
                tool_name="tool2",
                success=True,
                data={"results": [{"content": "B", "score": 0.8}]},
            ),
        ]
        
        aggregated = registry.aggregate_results(results, strategy="rank")
        
        assert "items" in aggregated
        assert aggregated["total_before_dedup"] == 2
    
    def test_aggregate_results_unknown_strategy(self):
        """Test aggregation with unknown strategy raises error."""
        registry = ToolRegistry()
        
        with pytest.raises(ValueError, match="Unknown aggregation strategy"):
            registry.aggregate_results([], strategy="unknown")
    
    @pytest.mark.asyncio
    async def test_execution_history(self):
        """Test execution history tracking."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        
        await registry.execute("calculator", expression="1 + 1")
        
        history = registry.get_execution_history()
        
        assert len(history) == 1
        assert history[0]["tool_name"] == "calculator"
    
    @pytest.mark.asyncio
    async def test_execution_history_filter(self):
        """Test filtering execution history by tool name."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(VectorSearchTool())
        
        await registry.execute("calculator", expression="1 + 1")
        await registry.execute("vector_search", query="test")
        
        history = registry.get_execution_history(tool_name="calculator")
        
        assert len(history) == 1
        assert history[0]["tool_name"] == "calculator"
    
    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing execution history."""
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        
        await registry.execute("calculator", expression="1 + 1")
        registry.clear_history()
        
        history = registry.get_execution_history()
        
        assert len(history) == 0