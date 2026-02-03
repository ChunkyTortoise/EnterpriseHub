"""Tests for the query planner module."""

import pytest
from uuid import uuid4

from src.agents.query_planner import (
    IntentAnalysis,
    QueryIntent,
    QueryPlan,
    QueryPlanner,
    QueryPlannerConfig,
    QueryStep,
    StepStatus,
    ToolSelection,
)


class TestIntentAnalysis:
    """Tests for intent analysis functionality."""
    
    def test_intent_analysis_factual(self):
        """Test factual query classification."""
        planner = QueryPlanner()
        result = planner.analyze_intent("What is the capital of France?")
        
        assert result.intent == QueryIntent.DEFINITION
        assert result.confidence > 0.5
        assert "France" in result.entities
    
    def test_intent_analysis_analytical(self):
        """Test analytical query classification."""
        planner = QueryPlanner()
        result = planner.analyze_intent("How does machine learning work?")
        
        assert result.intent in [QueryIntent.PROCEDURAL, QueryIntent.DEFINITION]
        assert result.confidence > 0.0
    
    def test_intent_analysis_comparative(self):
        """Test comparative query classification."""
        planner = QueryPlanner()
        result = planner.analyze_intent("Compare Python and JavaScript")
        
        assert result.intent == QueryIntent.COMPARISON
        assert result.requires_comparison is True
        assert result.confidence >= 0.3
    
    def test_intent_analysis_with_calculation(self):
        """Test intent analysis detects calculation needs."""
        planner = QueryPlanner()
        result = planner.analyze_intent("What is the average price of houses?")
        
        assert result.requires_calculation is True
        assert "average" in result.keywords or "price" in result.keywords
    
    def test_intent_analysis_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        planner = QueryPlanner()
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            planner.analyze_intent("")
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            planner.analyze_intent("   ")


class TestQueryDecomposition:
    """Tests for query decomposition functionality."""
    
    def test_query_decomposition_simple(self):
        """Test simple query returns single sub-query."""
        planner = QueryPlanner()
        sub_queries = planner.decompose_query("What is Python?")
        
        assert len(sub_queries) == 1
        assert sub_queries[0] == "What is Python?"
    
    def test_query_decomposition_comparison(self):
        """Test comparison query decomposition."""
        planner = QueryPlanner()
        query = "Compare Austin and Dallas housing prices"
        sub_queries = planner.decompose_query(query)
        
        assert len(sub_queries) >= 2
        # Should have sub-queries for each city
        assert any("Austin" in sq for sq in sub_queries)
        assert any("Dallas" in sq for sq in sub_queries)
    
    def test_query_decomposition_calculation(self):
        """Test calculation query decomposition."""
        planner = QueryPlanner()
        query = "Calculate the average of 10, 20, and 30"
        sub_queries = planner.decompose_query(query)
        
        assert len(sub_queries) >= 1
    
    def test_query_decomposition_multi_part(self):
        """Test multi-part query decomposition."""
        planner = QueryPlanner()
        query = "What is Python and how do I install it?"
        sub_queries = planner.decompose_query(query)
        
        # Should decompose into at least 2 parts
        assert len(sub_queries) >= 1
    
    def test_query_decomposition_disabled(self):
        """Test decomposition can be disabled."""
        config = QueryPlannerConfig(enable_decomposition=False)
        planner = QueryPlanner(config)
        
        sub_queries = planner.decompose_query("Compare A and B and C")
        
        assert len(sub_queries) == 1


class TestToolSelection:
    """Tests for tool selection functionality."""
    
    def test_tool_selection_vector_search(self):
        """Test vector search tool selection."""
        planner = QueryPlanner()
        selections = planner.select_tools("What is machine learning?")
        
        assert len(selections) >= 1
        assert any(s.tool_name == "vector_search" for s in selections)
    
    def test_tool_selection_web_search(self):
        """Test web search tool selection for fact checking."""
        planner = QueryPlanner()
        query = "Is it true that the earth is flat?"
        intent = planner.analyze_intent(query)
        selections = planner.select_tools(query, intent)
        
        # Should include web search for fact checking
        assert any(s.tool_name in ["web_search", "vector_search"] for s in selections)
    
    def test_tool_selection_calculator(self):
        """Test calculator tool selection for calculations."""
        planner = QueryPlanner()
        query = "Calculate 2 + 2"
        intent = planner.analyze_intent(query)
        selections = planner.select_tools(query, intent)
        
        # Should include calculator
        assert any(s.tool_name == "calculator" for s in selections)
    
    def test_tool_selection_multi_tool(self):
        """Test multiple tool selection."""
        planner = QueryPlanner()
        query = "What is the average price difference between Austin and Dallas?"
        intent = planner.analyze_intent(query)
        selections = planner.select_tools(query, intent)
        
        # Should have multiple tools
        assert len(selections) >= 2
        tool_names = [s.tool_name for s in selections]
        assert "vector_search" in tool_names
        assert "calculator" in tool_names


class TestQueryPlan:
    """Tests for query plan functionality."""
    
    def test_create_plan(self):
        """Test plan creation."""
        planner = QueryPlanner()
        plan = planner.create_plan("What is Python?")
        
        assert plan.original_query == "What is Python?"
        assert len(plan.steps) >= 1
        assert plan.intent_analysis.intent is not None
    
    def test_plan_get_ready_steps(self):
        """Test getting ready steps."""
        planner = QueryPlanner()
        plan = planner.create_plan("Compare A and B")
        
        ready_steps = plan.get_ready_steps()
        
        # Initially, all steps should be ready (no dependencies)
        assert len(ready_steps) == len(plan.steps)
    
    def test_plan_update_step_status(self):
        """Test updating step status."""
        planner = QueryPlanner()
        plan = planner.create_plan("What is Python?")
        
        step_id = plan.steps[0].id
        result = plan.update_step_status(step_id, StepStatus.COMPLETED, {"data": "test"})
        
        assert result is True
        assert plan.steps[0].status == StepStatus.COMPLETED
        assert plan.steps[0].result == {"data": "test"}
    
    def test_plan_update_invalid_step(self):
        """Test updating non-existent step."""
        planner = QueryPlanner()
        plan = planner.create_plan("What is Python?")
        
        result = plan.update_step_status(uuid4(), StepStatus.COMPLETED)
        
        assert result is False
    
    def test_plan_is_complete(self):
        """Test plan completion detection."""
        planner = QueryPlanner()
        plan = planner.create_plan("What is Python?")
        
        assert plan.is_complete() is False
        
        # Complete all steps
        for step in plan.steps:
            plan.update_step_status(step.id, StepStatus.COMPLETED)
        
        assert plan.is_complete() is True
    
    def test_plan_completion_rate(self):
        """Test completion rate calculation."""
        planner = QueryPlanner()
        plan = planner.create_plan("What is Python?")
        
        assert plan.get_completion_rate() == 0.0
        
        # Complete one step if there are steps
        if plan.steps:
            plan.update_step_status(plan.steps[0].id, StepStatus.COMPLETED)
            assert plan.get_completion_rate() == 1.0 / len(plan.steps)
    
    def test_plan_get_step_by_id(self):
        """Test getting step by ID."""
        planner = QueryPlanner()
        plan = planner.create_plan("What is Python?")
        
        if plan.steps:
            step_id = plan.steps[0].id
            found_step = plan.get_step_by_id(step_id)
            
            assert found_step is not None
            assert found_step.id == step_id


class TestQueryStep:
    """Tests for QueryStep model."""
    
    def test_query_step_defaults(self):
        """Test QueryStep default values."""
        tool_selection = ToolSelection(
            tool_name="vector_search",
            confidence=0.9,
            reason="test",
        )
        
        step = QueryStep(
            step_number=1,
            description="Test step",
            sub_query="test query",
            tool_selection=tool_selection,
        )
        
        assert step.status == StepStatus.PENDING
        assert step.execution_time_ms == 0.0
        assert step.dependencies == []
        assert step.id is not None


class TestIntentAnalysisModel:
    """Tests for IntentAnalysis model."""
    
    def test_intent_analysis_validation(self):
        """Test confidence validation."""
        with pytest.raises(ValueError):
            IntentAnalysis(
                intent=QueryIntent.RETRIEVAL,
                confidence=1.5,  # Invalid > 1.0
            )
        
        with pytest.raises(ValueError):
            IntentAnalysis(
                intent=QueryIntent.RETRIEVAL,
                confidence=-0.1,  # Invalid < 0.0
            )
    
    def test_intent_analysis_valid_confidence(self):
        """Test valid confidence values."""
        analysis = IntentAnalysis(
            intent=QueryIntent.RETRIEVAL,
            confidence=0.8,
        )
        
        assert analysis.confidence == 0.8


class TestQueryPlannerConfig:
    """Tests for QueryPlannerConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = QueryPlannerConfig()
        
        assert config.min_confidence_threshold == 0.6
        assert config.max_steps == 10
        assert config.enable_decomposition is True
        assert config.enable_parallelization is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = QueryPlannerConfig(
            min_confidence_threshold=0.8,
            max_steps=5,
            enable_decomposition=False,
        )
        
        assert config.min_confidence_threshold == 0.8
        assert config.max_steps == 5
        assert config.enable_decomposition is False