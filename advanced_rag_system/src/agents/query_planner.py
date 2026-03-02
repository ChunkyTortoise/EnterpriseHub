"""Query planning agent for intent analysis and query decomposition.

This module provides intelligent query planning capabilities including:
- Intent analysis and classification
- Query decomposition into sub-queries
- Tool selection based on query characteristics
- Multi-step reasoning planning
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryIntent(str, Enum):
    """Enumeration of query intents for routing optimization."""

    RETRIEVAL = "retrieval"  # Information retrieval from vector store
    CALCULATION = "calculation"  # Mathematical/computational tasks
    COMPARISON = "comparison"  # Comparing multiple items/concepts
    SYNTHESIS = "synthesis"  # Combining information from multiple sources
    FACT_CHECKING = "fact_checking"  # Verifying factual claims
    EXPLORATORY = "exploratory"  # Open-ended exploration
    DEFINITION = "definition"  # Defining terms/concepts
    PROCEDURAL = "procedural"  # How-to/step-by-step instructions


class StepStatus(str, Enum):
    """Status of a query step in the execution plan."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class IntentAnalysis(BaseModel):
    """Result of intent analysis for a query.

    Attributes:
        intent: Primary query intent
        confidence: Confidence score (0.0-1.0)
        secondary_intents: Additional detected intents
        entities: Named entities extracted from query
        keywords: Key terms for retrieval
        requires_calculation: Whether query needs calculation
        requires_comparison: Whether query needs comparison
        temporal_references: Time-related references
    """

    model_config = ConfigDict(extra="forbid")

    intent: QueryIntent
    confidence: float = Field(..., ge=0.0, le=1.0)
    secondary_intents: List[QueryIntent] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    requires_calculation: bool = False
    requires_comparison: bool = False
    temporal_references: List[str] = Field(default_factory=list)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class ToolSelection(BaseModel):
    """Tool selection with confidence and parameters.

    Attributes:
        tool_name: Name of the selected tool
        confidence: Confidence in tool selection (0.0-1.0)
        parameters: Parameters for tool execution
        reason: Reason for selecting this tool
        fallback_tools: Alternative tools if primary fails
    """

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    fallback_tools: List[str] = Field(default_factory=list)


class QueryStep(BaseModel):
    """Individual step in a query execution plan.

    Attributes:
        id: Unique step identifier
        step_number: Order in the execution plan
        description: Human-readable description
        sub_query: The specific sub-query for this step
        tool_selection: Selected tool for this step
        dependencies: IDs of steps that must complete first
        status: Current execution status
        result: Step execution result
        execution_time_ms: Time taken to execute
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    step_number: int = Field(..., ge=1)
    description: str
    sub_query: str
    tool_selection: ToolSelection
    dependencies: List[UUID] = Field(default_factory=list)
    status: StepStatus = Field(default=StepStatus.PENDING)
    result: Optional[Dict[str, Any]] = None
    execution_time_ms: float = Field(default=0.0, ge=0.0)


class QueryPlan(BaseModel):
    """Complete execution plan for processing a query.

    Attributes:
        id: Unique plan identifier
        original_query: The original user query
        intent_analysis: Intent analysis result
        steps: Ordered list of execution steps
        estimated_steps: Predicted number of steps
        parallelizable: Whether steps can run in parallel
        created_at: Plan creation timestamp
        completed_at: Plan completion timestamp
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    original_query: str
    intent_analysis: IntentAnalysis
    steps: List[QueryStep] = Field(default_factory=list)
    estimated_steps: int = Field(default=1, ge=1)
    parallelizable: bool = False
    created_at: str = Field(default_factory=lambda: str(uuid4()))
    completed_at: Optional[str] = None

    def get_ready_steps(self) -> List[QueryStep]:
        """Get steps that are ready to execute (dependencies met).

        Returns:
            List of steps with PENDING status and all dependencies completed.
        """
        completed_ids = {step.id for step in self.steps if step.status == StepStatus.COMPLETED}

        return [
            step
            for step in self.steps
            if step.status == StepStatus.PENDING and all(dep in completed_ids for dep in step.dependencies)
        ]

    def get_step_by_id(self, step_id: UUID) -> Optional[QueryStep]:
        """Find a step by its ID.

        Args:
            step_id: The step ID to find

        Returns:
            The matching step or None
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def update_step_status(self, step_id: UUID, status: StepStatus, result: Optional[Dict[str, Any]] = None) -> bool:
        """Update the status of a step.

        Args:
            step_id: The step to update
            status: New status
            result: Optional result data

        Returns:
            True if step was found and updated
        """
        for step in self.steps:
            if step.id == step_id:
                step.status = status
                if result is not None:
                    step.result = result
                return True
        return False

    def is_complete(self) -> bool:
        """Check if all steps are completed or failed.

        Returns:
            True if plan execution is complete
        """
        return all(step.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED) for step in self.steps)

    def get_completion_rate(self) -> float:
        """Calculate the completion rate of the plan.

        Returns:
            Percentage of completed steps (0.0-1.0)
        """
        if not self.steps:
            return 0.0
        completed = sum(1 for step in self.steps if step.status == StepStatus.COMPLETED)
        return completed / len(self.steps)


@dataclass
class QueryPlannerConfig:
    """Configuration for the query planner.

    Attributes:
        min_confidence_threshold: Minimum confidence for intent classification
        max_steps: Maximum number of steps in a plan
        enable_decomposition: Whether to decompose complex queries
        enable_parallelization: Whether to identify parallel steps
        calculation_keywords: Keywords indicating calculation needs
        comparison_keywords: Keywords indicating comparison needs
        custom_patterns: Custom regex patterns for intent detection
    """

    min_confidence_threshold: float = 0.6
    max_steps: int = 10
    enable_decomposition: bool = True
    enable_parallelization: bool = True
    calculation_keywords: Set[str] = field(
        default_factory=lambda: {
            "calculate",
            "compute",
            "sum",
            "total",
            "average",
            "mean",
            "median",
            "percentage",
            "ratio",
            "difference",
            "multiply",
            "divide",
            "add",
            "subtract",
            "how much",
            "how many",
            "cost",
            "price",
            "value",
            "worth",
            "budget",
            "expense",
        }
    )
    comparison_keywords: Set[str] = field(
        default_factory=lambda: {
            "compare",
            "versus",
            "vs",
            "difference between",
            "similarities",
            "better than",
            "worse than",
            "advantages",
            "disadvantages",
            "pros and cons",
            "which is",
            "which one",
            "or",
            "between",
        }
    )
    custom_patterns: Dict[str, List[str]] = field(default_factory=dict)


class QueryPlanner:
    """Intelligent query planner for agentic RAG.

    This class analyzes user queries, determines intent, decomposes
    complex queries into steps, and selects appropriate tools.

    Example:
        ```python
        planner = QueryPlanner()

        # Analyze intent
        intent = planner.analyze_intent(
            "What is the average price of houses in Rancho Cucamonga vs Dallas?"
        )
        # Intent: COMPARISON with CALCULATION

        # Create execution plan
        plan = planner.create_plan(
            "What is the average price of houses in Rancho Cucamonga vs Dallas?"
        )
        # Plan: 2 steps (retrieve Rancho Cucamonga prices, retrieve Dallas prices, compare)
        ```
    """

    # Intent detection patterns
    INTENT_PATTERNS: Dict[QueryIntent, List[str]] = {
        QueryIntent.DEFINITION: [
            r"^what is\s+\w+",
            r"^what are\s+\w+",
            r"^define\s+\w+",
            r"^explain\s+\w+",
            r"meaning of\s+\w+",
        ],
        QueryIntent.COMPARISON: [
            r"\bcompare\b",
            r"\bversus\b",
            r"\bvs\b",
            r"\bdifference between\b",
            r"\bsimilarities?\s+between\b",
            r"\bbetter than\b",
            r"\bworse than\b",
            r"\bwhich\s+(is|one)\b",
            r"\bor\b",
        ],
        QueryIntent.PROCEDURAL: [
            r"^how to\b",
            r"^how do\s+(i|you|we)\b",
            r"^how does\b",
            r"^steps?\s+to\b",
            r"^guide\s+(me|us)?\s+(to|on|for)\b",
            r"\bprocess\s+of\b",
            r"\bprocedure\s+for\b",
        ],
        QueryIntent.FACT_CHECKING: [
            r"\bis it true\b",
            r"\bis that true\b",
            r"\bcan you confirm\b",
            r"\bverify\b",
            r"\bvalidate\b",
            r"\bcheck if\b",
        ],
        QueryIntent.CALCULATION: [
            r"\bcalculate\b",
            r"\bcompute\b",
            r"\bhow much\b",
            r"\bhow many\b",
            r"\btotal\s+(cost|price|value)\b",
            r"\bsum\s+of\b",
            r"\baverage\s+(of|price|cost)\b",
        ],
        QueryIntent.EXPLORATORY: [
            r"\btell me about\b",
            r"\bwhat do you know about\b",
            r"\binformation about\b",
            r"\blearn about\b",
            r"\bdiscover\b",
        ],
    }

    def __init__(self, config: Optional[QueryPlannerConfig] = None):
        """Initialize the query planner.

        Args:
            config: Optional configuration object
        """
        self.config = config or QueryPlannerConfig()
        self._entity_pattern = re.compile(
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"  # Capitalized words
        )
        self._keyword_pattern = re.compile(
            r"\b\w{4,}\b"  # Words with 4+ characters
        )

    def analyze_intent(self, query: str) -> IntentAnalysis:
        """Analyze the intent of a user query.

        Uses pattern matching and keyword analysis to classify
        the query into one or more intent categories.

        Args:
            query: The user query string

        Returns:
            IntentAnalysis with classification results

        Raises:
            ValueError: If query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query_lower = query.lower().strip()
        scores: Dict[QueryIntent, float] = {}

        # Pattern-based scoring
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 0.6
            scores[intent] = min(score, 1.0)

        # Keyword-based scoring for calculation
        calc_keywords_found = sum(1 for kw in self.config.calculation_keywords if kw in query_lower)
        if calc_keywords_found > 0:
            scores[QueryIntent.CALCULATION] = scores.get(QueryIntent.CALCULATION, 0.0) + min(
                calc_keywords_found * 0.2, 0.5
            )

        # Keyword-based scoring for comparison
        comp_keywords_found = sum(1 for kw in self.config.comparison_keywords if kw in query_lower)
        if comp_keywords_found > 0:
            scores[QueryIntent.COMPARISON] = scores.get(QueryIntent.COMPARISON, 0.0) + min(
                comp_keywords_found * 0.2, 0.5
            )

        # Extract entities
        entities = self._extract_entities(query)

        # Extract keywords
        keywords = self._extract_keywords(query)

        # Determine primary intent
        if scores:
            primary_intent = max(scores, key=scores.get)
            confidence = scores[primary_intent]
        else:
            primary_intent = QueryIntent.RETRIEVAL
            confidence = 0.5

        # Get secondary intents (above threshold but not primary)
        secondary_intents = [
            intent
            for intent, score in scores.items()
            if score >= self.config.min_confidence_threshold and intent != primary_intent
        ]

        # Check for temporal references
        temporal_refs = self._extract_temporal_references(query_lower)

        return IntentAnalysis(
            intent=primary_intent,
            confidence=min(confidence, 1.0),
            secondary_intents=secondary_intents,
            entities=entities,
            keywords=keywords,
            requires_calculation=QueryIntent.CALCULATION in scores and scores[QueryIntent.CALCULATION] >= 0.3,
            requires_comparison=QueryIntent.COMPARISON in scores and scores[QueryIntent.COMPARISON] >= 0.3,
            temporal_references=temporal_refs,
        )

    def decompose_query(self, query: str, intent_analysis: Optional[IntentAnalysis] = None) -> List[str]:
        """Decompose a complex query into simpler sub-queries.

        Args:
            query: The original query
            intent_analysis: Optional pre-computed intent analysis

        Returns:
            List of sub-queries
        """
        if not self.config.enable_decomposition:
            return [query]

        if intent_analysis is None:
            intent_analysis = self.analyze_intent(query)

        sub_queries = []
        query_lower = query.lower()

        # Handle comparison queries
        if intent_analysis.requires_comparison:
            # Try to split on comparison keywords
            parts = re.split(r"\s+(?:versus|vs|compared to|or|and)\s+", query, flags=re.IGNORECASE)
            if len(parts) >= 2:
                # Create sub-queries for each item being compared
                for i, part in enumerate(parts):
                    sub_queries.append(f"Information about {part.strip()}")
                sub_queries.append(f"Comparison analysis: {query}")
                return sub_queries

        # Handle calculation queries
        if intent_analysis.requires_calculation:
            # Extract what needs to be calculated
            calc_pattern = re.search(r"(average|sum|total|calculate|compute)\s+(?:of\s+)?(.+?)(?:\?|$)", query_lower)
            if calc_pattern:
                metric = calc_pattern.group(1)
                target = calc_pattern.group(2).strip()
                sub_queries.append(f"Find {target} for calculation")
                sub_queries.append(f"Calculate {metric} of results")
                return sub_queries

        # Handle multi-part queries (indicated by "and", "also", etc.)
        conjunctions = r"\b(?:and|also|additionally|furthermore|moreover)\b"
        parts = re.split(conjunctions, query, flags=re.IGNORECASE)
        if len(parts) > 1:
            for part in parts:
                cleaned = part.strip()
                if cleaned and len(cleaned) > 10:
                    sub_queries.append(cleaned)
            if sub_queries:
                return sub_queries

        # Default: return original query
        return [query]

    def select_tools(self, query: str, intent_analysis: Optional[IntentAnalysis] = None) -> List[ToolSelection]:
        """Select appropriate tools for a query.

        Args:
            query: The user query
            intent_analysis: Optional pre-computed intent analysis

        Returns:
            List of tool selections with confidence scores
        """
        if intent_analysis is None:
            intent_analysis = self.analyze_intent(query)

        selections = []

        # Always include vector search for retrieval
        selections.append(
            ToolSelection(
                tool_name="vector_search",
                confidence=0.9,
                parameters={"query": query, "top_k": 10},
                reason="Primary retrieval tool for knowledge base",
                fallback_tools=["web_search"],
            )
        )

        # Add calculation tool if needed
        if intent_analysis.requires_calculation:
            selections.append(
                ToolSelection(
                    tool_name="calculator",
                    confidence=0.85,
                    parameters={"expression": query},
                    reason="Query requires mathematical computation",
                    fallback_tools=[],
                )
            )

        # Add web search for fact-checking or exploratory queries
        if intent_analysis.intent in (QueryIntent.FACT_CHECKING, QueryIntent.EXPLORATORY):
            selections.append(
                ToolSelection(
                    tool_name="web_search",
                    confidence=0.7,
                    parameters={"query": query, "num_results": 5},
                    reason="External verification needed",
                    fallback_tools=[],
                )
            )

        # Sort by confidence
        selections.sort(key=lambda x: x.confidence, reverse=True)

        return selections

    def create_plan(self, query: str) -> QueryPlan:
        """Create a complete execution plan for a query.

        Args:
            query: The user query

        Returns:
            QueryPlan with all execution steps
        """
        # Analyze intent
        intent_analysis = self.analyze_intent(query)

        # Decompose query
        sub_queries = self.decompose_query(query, intent_analysis)

        # Create steps
        steps = []
        for i, sub_query in enumerate(sub_queries[: self.config.max_steps], 1):
            # Select tools for this sub-query
            tool_selections = self.select_tools(sub_query, intent_analysis)

            # Use the highest confidence tool
            primary_tool = (
                tool_selections[0]
                if tool_selections
                else ToolSelection(
                    tool_name="vector_search",
                    confidence=0.5,
                    parameters={"query": sub_query},
                    reason="Default retrieval",
                    fallback_tools=[],
                )
            )

            # Determine dependencies
            dependencies = []
            if i > 1 and not self.config.enable_parallelization:
                # Sequential execution
                dependencies = [steps[-1].id]

            step = QueryStep(
                step_number=i,
                description=f"Execute: {sub_query[:50]}...",
                sub_query=sub_query,
                tool_selection=primary_tool,
                dependencies=dependencies,
            )
            steps.append(step)

        # Determine if plan is parallelizable
        parallelizable = (
            self.config.enable_parallelization and len(steps) > 1 and not any(step.dependencies for step in steps)
        )

        return QueryPlan(
            original_query=query,
            intent_analysis=intent_analysis,
            steps=steps,
            estimated_steps=len(steps),
            parallelizable=parallelizable,
        )

    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query.

        Args:
            query: The query string

        Returns:
            List of extracted entities
        """
        # Simple entity extraction based on capitalization
        matches = self._entity_pattern.findall(query)
        return list(set(matches))[:10]  # Limit to 10 unique entities

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key terms from query.

        Args:
            query: The query string

        Returns:
            List of extracted keywords
        """
        # Extract words with 4+ characters
        matches = self._keyword_pattern.findall(query.lower())
        # Filter out common stop words
        stop_words = {
            "what",
            "when",
            "where",
            "which",
            "who",
            "whom",
            "whose",
            "why",
            "how",
            "that",
            "with",
            "from",
            "they",
            "them",
            "have",
            "this",
            "will",
            "your",
            "about",
            "could",
            "would",
        }
        keywords = [w for w in matches if w not in stop_words]
        return list(set(keywords))[:15]  # Limit to 15 unique keywords

    def _extract_temporal_references(self, query_lower: str) -> List[str]:
        """Extract temporal references from query.

        Args:
            query_lower: Lowercase query string

        Returns:
            List of temporal references
        """
        temporal_patterns = [
            r"\b\d{4}\b",  # Years
            r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b",
            r"\b(?:last|next|this)\s+(?:year|month|week|day)\b",
            r"\b(?:yesterday|today|tomorrow)\b",
            r"\b\d{1,2}\s+(?:days?|weeks?|months?|years?)\s+(?:ago|from now)\b",
        ]

        references = []
        for pattern in temporal_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            references.extend(matches)

        return list(set(references))
