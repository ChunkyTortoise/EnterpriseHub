"""Agentic RAG System - Autonomous query planning and tool use.

This module provides agentic capabilities for the RAG system, including:
- Query planning with intent analysis and decomposition
- Tool registry for vector search, web search, and calculations
- Reflection and self-correction mechanisms
- Orchestration of multi-step reasoning workflows
"""

from src.agents.query_planner import (
    QueryPlanner,
    QueryPlan,
    QueryStep,
    IntentAnalysis,
    ToolSelection,
    QueryIntent,
    StepStatus,
)
from src.agents.tool_registry import (
    ToolRegistry,
    BaseTool,
    VectorSearchTool,
    WebSearchTool,
    CalculatorTool,
    ToolResult,
    ToolExecutionError,
    ToolMetadata,
)
from src.agents.reflection import (
    ReflectionEngine,
    AnswerQualityAssessment,
    CorrectionStrategy,
    ConfidenceScorer,
    ConfidenceScore,
    QualityDimension,
)
from src.agents.agentic_rag import (
    AgenticRAG,
    AgenticRAGConfig,
    AgenticRAGResponse,
    ExecutionTrace,
    ExecutionStep,
)
from src.agents.memory import ConversationMemory

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
    "ConversationMemory",
]
