"""Agentic RAG System - Autonomous query planning and tool use.

This module provides agentic capabilities for the RAG system, including:
- Query planning with intent analysis and decomposition
- Tool registry for vector search, web search, and calculations
- Reflection and self-correction mechanisms
- Orchestration of multi-step reasoning workflows
"""

from src.agents.agentic_rag import (
    AgenticRAG,
    AgenticRAGConfig,
    AgenticRAGResponse,
    ExecutionStep,
    ExecutionTrace,
)
from src.agents.query_planner import (
    IntentAnalysis,
    QueryIntent,
    QueryPlan,
    QueryPlanner,
    QueryStep,
    StepStatus,
    ToolSelection,
)
from src.agents.reflection import (
    AnswerQualityAssessment,
    ConfidenceScore,
    ConfidenceScorer,
    CorrectionStrategy,
    QualityDimension,
    ReflectionEngine,
)
from src.agents.tool_registry import (
    BaseTool,
    CalculatorTool,
    ToolExecutionError,
    ToolMetadata,
    ToolRegistry,
    ToolResult,
    VectorSearchTool,
    WebSearchTool,
)

__all__ = [
    # Query Planner
    "QueryPlanner",
    "QueryPlan",
    "QueryStep",
    "IntentAnalysis",
    "ToolSelection",
    "QueryIntent",
    "StepStatus",
    # Tool Registry
    "ToolRegistry",
    "BaseTool",
    "VectorSearchTool",
    "WebSearchTool",
    "CalculatorTool",
    "ToolResult",
    "ToolExecutionError",
    "ToolMetadata",
    # Reflection
    "ReflectionEngine",
    "AnswerQualityAssessment",
    "CorrectionStrategy",
    "ConfidenceScorer",
    "ConfidenceScore",
    "QualityDimension",
    # Agentic RAG
    "AgenticRAG",
    "AgenticRAGConfig",
    "AgenticRAGResponse",
    "ExecutionTrace",
    "ExecutionStep",
]
