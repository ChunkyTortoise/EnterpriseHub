"""Reflection and self-correction engine for agentic RAG.

This module provides capabilities for:
- Answer quality assessment
- Self-correction loops
- Confidence scoring
- Gap identification and correction strategies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.agents.query_planner import QueryIntent, QueryPlan
from src.agents.tool_registry import ToolResult


class QualityDimension(str, Enum):
    """Dimensions of answer quality."""

    COMPLETENESS = "completeness"  # All aspects of query addressed
    ACCURACY = "accuracy"  # Information is correct
    RELEVANCE = "relevance"  # Information matches query intent
    COHERENCE = "coherence"  # Answer is well-structured
    CITATIONS = "citations"  # Sources properly attributed
    CURRENCY = "currency"  # Information is up-to-date
    CONCISENESS = "conciseness"  # Answer is appropriately brief


class ConfidenceScore(BaseModel):
    """Multi-factor confidence score.

    Attributes:
        overall: Overall confidence score (0.0-1.0)
        source_reliability: Confidence in source reliability
        result_diversity: Confidence from diverse sources
        completeness: Confidence in information completeness
        tool_success_rate: Confidence from tool execution success
        factors: Dictionary of individual factor scores
    """

    model_config = ConfigDict(extra="forbid")

    overall: float = Field(..., ge=0.0, le=1.0)
    source_reliability: float = Field(default=0.0, ge=0.0, le=1.0)
    result_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    tool_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    factors: Dict[str, float] = Field(default_factory=dict)

    @field_validator("overall")
    @classmethod
    def validate_overall(cls, v: float) -> float:
        """Ensure overall is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Overall confidence must be between 0.0 and 1.0")
        return v

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if confidence is above threshold.

        Args:
            threshold: Minimum confidence threshold

        Returns:
            True if confidence is high enough
        """
        return self.overall >= threshold

    def get_weakest_factor(self) -> Tuple[str, float]:
        """Get the weakest confidence factor.

        Returns:
            Tuple of (factor_name, score)
        """
        all_factors = {
            "source_reliability": self.source_reliability,
            "result_diversity": self.result_diversity,
            "completeness": self.completeness,
            "tool_success_rate": self.tool_success_rate,
            **self.factors,
        }
        return min(all_factors.items(), key=lambda x: x[1])


class AnswerQualityAssessment(BaseModel):
    """Assessment of answer quality across multiple dimensions.

    Attributes:
        overall_score: Overall quality score (0.0-1.0)
        dimension_scores: Scores for each quality dimension
        strengths: Identified strengths
        weaknesses: Identified weaknesses
        gaps: Information gaps detected
        recommendations: Recommendations for improvement
        requires_iteration: Whether another iteration is needed
    """

    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(..., ge=0.0, le=1.0)
    dimension_scores: Dict[QualityDimension, float] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    requires_iteration: bool = False

    @field_validator("overall_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v

    def get_lowest_dimension(self) -> Tuple[QualityDimension, float]:
        """Get the lowest scoring dimension.

        Returns:
            Tuple of (dimension, score)
        """
        if not self.dimension_scores:
            return (QualityDimension.COMPLETENESS, 0.0)
        return min(self.dimension_scores.items(), key=lambda x: x[1])

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Check if quality is acceptable.

        Args:
            threshold: Minimum acceptable score

        Returns:
            True if quality is acceptable
        """
        return self.overall_score >= threshold


class CorrectionStrategy(BaseModel):
    """Strategy for correcting answer quality issues.

    Attributes:
        id: Unique strategy identifier
        target_dimension: Quality dimension to improve
        description: Human-readable description
        action_type: Type of corrective action
        parameters: Parameters for the action
        expected_improvement: Expected improvement in score
        priority: Priority level (1-5, 5 being highest)
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    target_dimension: QualityDimension
    description: str
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_improvement: float = Field(default=0.1, ge=0.0, le=1.0)
    priority: int = Field(default=3, ge=1, le=5)


@dataclass
class ReflectionConfig:
    """Configuration for reflection engine.

    Attributes:
        quality_threshold: Minimum quality score for acceptance
        confidence_threshold: Minimum confidence for acceptance
        max_iterations: Maximum number of reflection iterations
        enable_self_correction: Whether to enable self-correction
        dimension_weights: Weights for quality dimensions
        gap_keywords: Keywords indicating information gaps
    """

    quality_threshold: float = 0.7
    confidence_threshold: float = 0.75
    max_iterations: int = 3
    enable_self_correction: bool = True
    dimension_weights: Dict[QualityDimension, float] = field(
        default_factory=lambda: {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.RELEVANCE: 0.20,
            QualityDimension.COHERENCE: 0.15,
            QualityDimension.CITATIONS: 0.10,
            QualityDimension.CURRENCY: 0.03,
            QualityDimension.CONCISENESS: 0.02,
        }
    )
    gap_keywords: Set[str] = field(
        default_factory=lambda: {
            "unknown",
            "unclear",
            "not mentioned",
            "not specified",
            "missing",
            "incomplete",
            "insufficient",
            "limited",
            "no information",
            "not available",
            "unavailable",
        }
    )


class ConfidenceScorer:
    """Calculate confidence scores based on multiple factors.

    This class evaluates confidence from:
    - Source reliability and diversity
    - Tool execution success rates
    - Information completeness
    - Result consistency

    Example:
        ```python
        scorer = ConfidenceScorer()

        score = scorer.calculate(
            tool_results=[result1, result2],
            query_intent=QueryIntent.RETRIEVAL,
            iteration_count=1
        )
        ```
    """

    def __init__(self, config: Optional[ReflectionConfig] = None) -> None:
        """Initialize confidence scorer.

        Args:
            config: Optional configuration
        """
        self.config = config or ReflectionConfig()

    def calculate(
        self,
        tool_results: List[ToolResult],
        query_intent: QueryIntent,
        iteration_count: int = 1,
        answer_text: Optional[str] = None,
    ) -> ConfidenceScore:
        """Calculate confidence score.

        Args:
            tool_results: Results from tool executions
            query_intent: Intent of the query
            iteration_count: Current iteration number
            answer_text: Generated answer text

        Returns:
            ConfidenceScore with all factors
        """
        # Calculate source reliability
        source_reliability = self._calculate_source_reliability(tool_results)

        # Calculate result diversity
        result_diversity = self._calculate_result_diversity(tool_results)

        # Calculate completeness
        completeness = self._calculate_completeness(tool_results, query_intent, answer_text)

        # Calculate tool success rate
        tool_success_rate = self._calculate_tool_success_rate(tool_results)

        # Calculate iteration penalty (confidence decreases with iterations)
        iteration_factor = max(0.5, 1.0 - (iteration_count - 1) * 0.15)

        # Calculate overall confidence
        overall = (
            source_reliability * 0.25 + result_diversity * 0.20 + completeness * 0.30 + tool_success_rate * 0.25
        ) * iteration_factor

        return ConfidenceScore(
            overall=min(overall, 1.0),
            source_reliability=source_reliability,
            result_diversity=result_diversity,
            completeness=completeness,
            tool_success_rate=tool_success_rate,
            factors={
                "iteration_factor": iteration_factor,
                "query_intent_match": 0.8 if query_intent else 0.5,
            },
        )

    def _calculate_source_reliability(self, tool_results: List[ToolResult]) -> float:
        """Calculate source reliability score.

        Args:
            tool_results: Tool execution results

        Returns:
            Reliability score (0.0-1.0)
        """
        if not tool_results:
            return 0.0

        # Weight different sources
        source_weights = {
            "vector_search": 0.9,  # Internal knowledge base
            "calculator": 1.0,  # Deterministic
            "web_search": 0.7,  # External, may vary
        }

        total_weight = 0.0
        weighted_score = 0.0

        for result in tool_results:
            if result.success:
                weight = source_weights.get(result.tool_name, 0.5)
                weighted_score += weight
                total_weight += 1.0

        if total_weight == 0:
            return 0.0

        return min(weighted_score / len(tool_results), 1.0)

    def _calculate_result_diversity(self, tool_results: List[ToolResult]) -> float:
        """Calculate result diversity score.

        Args:
            tool_results: Tool execution results

        Returns:
            Diversity score (0.0-1.0)
        """
        if not tool_results:
            return 0.0

        # Count unique sources
        unique_sources = set(r.tool_name for r in tool_results if r.success)

        # More unique sources = higher diversity
        diversity = min(len(unique_sources) / 3, 1.0)

        return diversity

    def _calculate_completeness(
        self,
        tool_results: List[ToolResult],
        query_intent: QueryIntent,
        answer_text: Optional[str],
    ) -> float:
        """Calculate information completeness score.

        Args:
            tool_results: Tool execution results
            query_intent: Query intent
            answer_text: Generated answer

        Returns:
            Completeness score (0.0-1.0)
        """
        if not tool_results:
            return 0.0

        # Check for results from each tool
        successful_tools = sum(1 for r in tool_results if r.success)
        tool_completeness = successful_tools / len(tool_results) if tool_results else 0

        # Check answer for gap indicators
        gap_score = 1.0
        if answer_text:
            answer_lower = answer_text.lower()
            gap_count = sum(1 for keyword in self.config.gap_keywords if keyword in answer_lower)
            gap_score = max(0.0, 1.0 - (gap_count * 0.1))

        # Weight by intent complexity
        intent_weights = {
            QueryIntent.RETRIEVAL: 0.8,
            QueryIntent.DEFINITION: 0.9,
            QueryIntent.CALCULATION: 1.0,
            QueryIntent.COMPARISON: 0.7,
            QueryIntent.SYNTHESIS: 0.6,
            QueryIntent.FACT_CHECKING: 0.85,
            QueryIntent.EXPLORATORY: 0.5,
            QueryIntent.PROCEDURAL: 0.75,
        }
        intent_factor = intent_weights.get(query_intent, 0.7)

        return min((tool_completeness * 0.5 + gap_score * 0.5) * intent_factor, 1.0)

    def _calculate_tool_success_rate(self, tool_results: List[ToolResult]) -> float:
        """Calculate tool execution success rate.

        Args:
            tool_results: Tool execution results

        Returns:
            Success rate (0.0-1.0)
        """
        if not tool_results:
            return 0.0

        successful = sum(1 for r in tool_results if r.success)
        return successful / len(tool_results)


class ReflectionEngine:
    """Engine for reflection and self-correction.

    This engine assesses answer quality, identifies gaps,
    and generates correction strategies.

    Example:
        ```python
        engine = ReflectionEngine()

        # Assess quality
        assessment = engine.assess_quality(
            answer="The capital of France is Paris.",
            query="What is the capital of France?",
            tool_results=[result1],
            query_plan=plan
        )

        # Check if iteration needed
        if assessment.requires_iteration:
            strategies = engine.generate_correction_strategies(assessment)
        ```
    """

    def __init__(self, config: Optional[ReflectionConfig] = None) -> None:
        """Initialize reflection engine.

        Args:
            config: Optional configuration
        """
        self.config = config or ReflectionConfig()
        self.confidence_scorer = ConfidenceScorer(config)

    def assess_quality(
        self,
        answer: str,
        query: str,
        tool_results: List[ToolResult],
        query_plan: QueryPlan,
        iteration_count: int = 1,
    ) -> AnswerQualityAssessment:
        """Assess the quality of an answer.

        Args:
            answer: Generated answer text
            query: Original query
            tool_results: Results from tool executions
            query_plan: Execution plan
            iteration_count: Current iteration

        Returns:
            AnswerQualityAssessment with scores and recommendations
        """
        dimension_scores = {}
        strengths = []
        weaknesses = []
        gaps = []
        recommendations = []

        # Assess completeness
        completeness = self._assess_completeness(answer, query, tool_results)
        dimension_scores[QualityDimension.COMPLETENESS] = completeness
        if completeness >= 0.8:
            strengths.append("Comprehensive coverage of query aspects")
        elif completeness < 0.5:
            weaknesses.append("Incomplete coverage of query")
            gaps.append("Missing information for parts of the query")
            recommendations.append("Expand search to cover all query aspects")

        # Assess accuracy (based on tool success)
        accuracy = self._assess_accuracy(tool_results)
        dimension_scores[QualityDimension.ACCURACY] = accuracy
        if accuracy >= 0.9:
            strengths.append("High confidence in source accuracy")
        elif accuracy < 0.6:
            weaknesses.append("Low confidence in accuracy")
            recommendations.append("Verify information with additional sources")

        # Assess relevance
        relevance = self._assess_relevance(answer, query, query_plan)
        dimension_scores[QualityDimension.RELEVANCE] = relevance
        if relevance >= 0.8:
            strengths.append("Highly relevant to query intent")
        elif relevance < 0.5:
            weaknesses.append("Low relevance to query")
            recommendations.append("Refine search to better match query intent")

        # Assess coherence
        coherence = self._assess_coherence(answer)
        dimension_scores[QualityDimension.COHERENCE] = coherence
        if coherence >= 0.8:
            strengths.append("Well-structured and coherent")

        # Assess citations
        citations = self._assess_citations(answer, tool_results)
        dimension_scores[QualityDimension.CITATIONS] = citations
        if citations >= 0.8:
            strengths.append("Properly cited sources")
        elif citations < 0.5:
            weaknesses.append("Insufficient source attribution")
            recommendations.append("Add source citations to answer")

        # Assess currency (for time-sensitive queries)
        currency = self._assess_currency(answer, query)
        dimension_scores[QualityDimension.CURRENCY] = currency

        # Assess conciseness
        conciseness = self._assess_conciseness(answer, query)
        dimension_scores[QualityDimension.CONCISENESS] = conciseness

        # Calculate overall score
        overall = sum(score * self.config.dimension_weights.get(dim, 0.1) for dim, score in dimension_scores.items())

        # Determine if iteration is needed
        requires_iteration = (
            overall < self.config.quality_threshold
            and iteration_count < self.config.max_iterations
            and self.config.enable_self_correction
            and len(recommendations) > 0
        )

        return AnswerQualityAssessment(
            overall_score=min(overall, 1.0),
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            gaps=gaps,
            recommendations=recommendations,
            requires_iteration=requires_iteration,
        )

    def identify_gaps(
        self,
        answer: str,
        query: str,
        query_plan: QueryPlan,
    ) -> List[str]:
        """Identify information gaps in the answer.

        Args:
            answer: Generated answer
            query: Original query
            query_plan: Execution plan

        Returns:
            List of identified gaps
        """
        gaps = []
        answer_lower = answer.lower()

        # Check for gap keywords in answer
        for keyword in self.config.gap_keywords:
            if keyword in answer_lower:
                gaps.append(f"Answer contains uncertainty indicator: '{keyword}'")

        # Check if all plan steps were addressed
        for step in query_plan.steps:
            step_keywords = step.sub_query.lower().split()
            keyword_matches = sum(1 for kw in step_keywords if len(kw) > 3 and kw in answer_lower)
            if keyword_matches < len(step_keywords) * 0.3:
                gaps.append(f"Step {step.step_number} not adequately addressed")

        # Check for missing entities from query
        entities = query_plan.intent_analysis.entities
        for entity in entities:
            if entity.lower() not in answer_lower:
                gaps.append(f"Entity '{entity}' not mentioned in answer")

        return gaps

    def generate_correction_strategies(
        self,
        assessment: AnswerQualityAssessment,
    ) -> List[CorrectionStrategy]:
        """Generate strategies to correct quality issues.

        Args:
            assessment: Quality assessment

        Returns:
            List of correction strategies
        """
        strategies = []

        # Generate strategy for lowest dimension
        lowest_dim, lowest_score = assessment.get_lowest_dimension()

        if lowest_score < self.config.quality_threshold:
            strategy_map = {
                QualityDimension.COMPLETENESS: CorrectionStrategy(
                    target_dimension=QualityDimension.COMPLETENESS,
                    description="Expand search to cover missing aspects",
                    action_type="expand_search",
                    parameters={"additional_queries": assessment.gaps},
                    expected_improvement=0.2,
                    priority=5,
                ),
                QualityDimension.ACCURACY: CorrectionStrategy(
                    target_dimension=QualityDimension.ACCURACY,
                    description="Verify with additional sources",
                    action_type="verify_sources",
                    parameters={"cross_reference": True},
                    expected_improvement=0.15,
                    priority=5,
                ),
                QualityDimension.RELEVANCE: CorrectionStrategy(
                    target_dimension=QualityDimension.RELEVANCE,
                    description="Refine query to better match intent",
                    action_type="refine_query",
                    parameters={"intent_focus": True},
                    expected_improvement=0.2,
                    priority=4,
                ),
                QualityDimension.COHERENCE: CorrectionStrategy(
                    target_dimension=QualityDimension.COHERENCE,
                    description="Reorganize answer structure",
                    action_type="restructure",
                    parameters={"logical_flow": True},
                    expected_improvement=0.1,
                    priority=3,
                ),
                QualityDimension.CITATIONS: CorrectionStrategy(
                    target_dimension=QualityDimension.CITATIONS,
                    description="Add source citations",
                    action_type="add_citations",
                    parameters={"include_sources": True},
                    expected_improvement=0.15,
                    priority=3,
                ),
                QualityDimension.CURRENCY: CorrectionStrategy(
                    target_dimension=QualityDimension.CURRENCY,
                    description="Search for more recent information",
                    action_type="update_search",
                    parameters={"recency_filter": "latest"},
                    expected_improvement=0.1,
                    priority=2,
                ),
                QualityDimension.CONCISENESS: CorrectionStrategy(
                    target_dimension=QualityDimension.CONCISENESS,
                    description="Condense answer while preserving key points",
                    action_type="summarize",
                    parameters={"max_length": 500},
                    expected_improvement=0.05,
                    priority=1,
                ),
            }

            strategy = strategy_map.get(lowest_dim)
            if strategy:
                strategies.append(strategy)

        # Add strategies for gaps
        for gap in assessment.gaps:
            strategies.append(
                CorrectionStrategy(
                    target_dimension=QualityDimension.COMPLETENESS,
                    description=f"Address gap: {gap}",
                    action_type="fill_gap",
                    parameters={"gap_description": gap},
                    expected_improvement=0.1,
                    priority=4,
                )
            )

        # Sort by priority (highest first)
        strategies.sort(key=lambda s: s.priority, reverse=True)

        return strategies

    def should_iterate(
        self,
        assessment: AnswerQualityAssessment,
        iteration_count: int,
        confidence_score: Optional[ConfidenceScore] = None,
    ) -> bool:
        """Determine if another iteration is needed.

        Args:
            assessment: Quality assessment
            iteration_count: Current iteration count
            confidence_score: Optional confidence score

        Returns:
            True if another iteration should be performed
        """
        # Check max iterations
        if iteration_count >= self.config.max_iterations:
            return False

        # Check if self-correction is enabled
        if not self.config.enable_self_correction:
            return False

        # Check quality threshold
        if assessment.overall_score >= self.config.quality_threshold:
            return False

        # Check confidence threshold
        if confidence_score and confidence_score.is_high_confidence(self.config.confidence_threshold):
            return False

        # Check if there are actionable recommendations
        if not assessment.recommendations:
            return False

        return True

    def _assess_completeness(
        self,
        answer: str,
        query: str,
        tool_results: List[ToolResult],
    ) -> float:
        """Assess completeness of answer."""
        if not answer or not tool_results:
            return 0.0

        # Check answer length relative to query complexity
        query_words = len(query.split())
        answer_words = len(answer.split())

        # Expect at least 5 words per query word for complex queries
        expected_length = max(20, query_words * 5)
        length_score = min(answer_words / expected_length, 1.0)

        # Check for tool results
        has_results = any(r.success and r.data for r in tool_results)

        return length_score * 0.5 + (1.0 if has_results else 0.0) * 0.5

    def _assess_accuracy(self, tool_results: List[ToolResult]) -> float:
        """Assess accuracy based on tool results."""
        if not tool_results:
            return 0.0

        successful = sum(1 for r in tool_results if r.success)
        return successful / len(tool_results)

    def _assess_relevance(
        self,
        answer: str,
        query: str,
        query_plan: QueryPlan,
    ) -> float:
        """Assess relevance of answer to query."""
        if not answer:
            return 0.0

        answer_lower = answer.lower()
        query_lower = query.lower()

        # Check keyword overlap
        query_keywords = set(query_lower.split())
        answer_keywords = set(answer_lower.split())

        if query_keywords:
            overlap = len(query_keywords & answer_keywords)
            keyword_score = overlap / len(query_keywords)
        else:
            keyword_score = 0.0

        # Check intent match
        intent_keywords = set(query_plan.intent_analysis.keywords)
        if intent_keywords:
            intent_overlap = len(intent_keywords & answer_keywords)
            intent_score = intent_overlap / len(intent_keywords)
        else:
            intent_score = 0.5

        return keyword_score * 0.6 + intent_score * 0.4

    def _assess_coherence(self, answer: str) -> float:
        """Assess coherence of answer."""
        if not answer:
            return 0.0

        # Check for proper sentence structure
        sentences = answer.split(".")
        valid_sentences = sum(1 for s in sentences if len(s.strip()) > 10)

        if not sentences:
            return 0.0

        sentence_score = valid_sentences / len(sentences)

        # Check for logical flow indicators
        flow_indicators = ["therefore", "because", "however", "additionally", "first", "second", "finally"]
        flow_score = min(sum(1 for indicator in flow_indicators if indicator in answer.lower()) / 3, 1.0)

        return sentence_score * 0.7 + flow_score * 0.3

    def _assess_citations(
        self,
        answer: str,
        tool_results: List[ToolResult],
    ) -> float:
        """Assess citation quality."""
        if not answer or not tool_results:
            return 0.0

        # Check for citation patterns
        citation_patterns = ["source:", "according to", "from", "[", "("]
        citation_count = sum(1 for pattern in citation_patterns if pattern in answer.lower())

        citation_score = min(citation_count / 2, 1.0)

        # Check if tools provided sources
        has_sources = any(r.success and r.data and isinstance(r.data, dict) for r in tool_results)

        return citation_score * 0.5 + (1.0 if has_sources else 0.0) * 0.5

    def _assess_currency(self, answer: str, query: str) -> float:
        """Assess currency of information."""
        # Default to high score unless query indicates time sensitivity
        time_sensitive_keywords = ["latest", "recent", "current", "today", "now", "2024", "2025"]

        query_lower = query.lower()
        is_time_sensitive = any(kw in query_lower for kw in time_sensitive_keywords)

        if not is_time_sensitive:
            return 0.9  # Not time-sensitive, assume current

        # Check for date references in answer
        date_patterns = ["2024", "2025", "january", "february", "march", "april", "may", "june"]
        has_date = any(pattern in answer.lower() for pattern in date_patterns)

        return 0.9 if has_date else 0.5

    def _assess_conciseness(self, answer: str, query: str) -> float:
        """Assess conciseness of answer."""
        if not answer:
            return 0.0

        word_count = len(answer.split())

        # Ideal length depends on query type
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["explain", "describe", "how"]):
            ideal_max = 300
        else:
            ideal_max = 150

        if word_count <= ideal_max:
            return 1.0
        elif word_count <= ideal_max * 2:
            return 0.7
        else:
            return 0.4
