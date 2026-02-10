"""Tests for the reflection and self-correction engine."""

import pytest
from src.agents.query_planner import (
    IntentAnalysis,
    QueryIntent,
    QueryPlan,
    QueryStep,
    ToolSelection,
)
from src.agents.reflection import (
    AnswerQualityAssessment,
    ConfidenceScore,
    ConfidenceScorer,
    CorrectionStrategy,
    QualityDimension,
    ReflectionConfig,
    ReflectionEngine,
)
from src.agents.tool_registry import ToolResult

@pytest.mark.unit


def _make_tool_result(
    tool_name="vector_search",
    success=True,
    data=None,
):
    return ToolResult(
        tool_name=tool_name,
        success=success,
        data=data if data is not None else {"results": [{"content": "mock", "score": 0.9}]},
        execution_time_ms=10.0,
    )


def _make_query_plan(
    query="What is machine learning?",
    intent=QueryIntent.RETRIEVAL,
):
    return QueryPlan(
        original_query=query,
        intent_analysis=IntentAnalysis(
            intent=intent,
            confidence=0.9,
            entities=["machine learning"],
            keywords=["machine", "learning"],
        ),
        steps=[
            QueryStep(
                step_number=1,
                description="Search for info",
                sub_query=query,
                tool_selection=ToolSelection(
                    tool_name="vector_search",
                    confidence=0.9,
                    parameters={"query": query},
                    reason="Primary retrieval",
                ),
            ),
        ],
    )


class TestConfidenceScore:
    def test_valid_score(self):
        score = ConfidenceScore(overall=0.85)
        assert score.overall == 0.85

    def test_boundary_values(self):
        assert ConfidenceScore(overall=0.0).overall == 0.0
        assert ConfidenceScore(overall=1.0).overall == 1.0

    def test_invalid_score_rejected(self):
        with pytest.raises(Exception):
            ConfidenceScore(overall=1.5)
        with pytest.raises(Exception):
            ConfidenceScore(overall=-0.1)

    def test_is_high_confidence(self):
        score = ConfidenceScore(overall=0.85)
        assert score.is_high_confidence(threshold=0.8) is True
        assert score.is_high_confidence(threshold=0.9) is False

    def test_get_weakest_factor(self):
        score = ConfidenceScore(
            overall=0.7,
            source_reliability=0.9,
            result_diversity=0.3,
            completeness=0.8,
            tool_success_rate=0.7,
        )
        name, val = score.get_weakest_factor()
        assert name == "result_diversity"
        assert val == 0.3


class TestConfidenceScorer:
    def test_empty_results(self):
        scorer = ConfidenceScorer()
        score = scorer.calculate([], QueryIntent.RETRIEVAL)
        assert score.overall == 0.0

    def test_single_successful_result(self):
        scorer = ConfidenceScorer()
        results = [_make_tool_result("vector_search")]
        score = scorer.calculate(results, QueryIntent.RETRIEVAL)
        assert 0.0 < score.overall <= 1.0
        assert score.tool_success_rate == 1.0

    def test_mixed_success_failure(self):
        scorer = ConfidenceScorer()
        results = [
            _make_tool_result("vector_search", success=True),
            _make_tool_result("web_search", success=False, data={}),
        ]
        score = scorer.calculate(results, QueryIntent.RETRIEVAL)
        assert score.tool_success_rate == 0.5

    def test_diverse_sources(self):
        scorer = ConfidenceScorer()
        results = [
            _make_tool_result("vector_search"),
            _make_tool_result("web_search"),
            _make_tool_result("calculator", data={"result": 42}),
        ]
        score = scorer.calculate(results, QueryIntent.SYNTHESIS)
        assert score.result_diversity >= 0.9

    def test_iteration_penalty(self):
        scorer = ConfidenceScorer()
        results = [_make_tool_result()]
        score_1 = scorer.calculate(results, QueryIntent.RETRIEVAL, iteration_count=1)
        score_3 = scorer.calculate(results, QueryIntent.RETRIEVAL, iteration_count=3)
        assert score_1.overall >= score_3.overall

    def test_source_reliability_weighting(self):
        scorer = ConfidenceScorer()
        calc = scorer.calculate(
            [_make_tool_result("calculator", data={"result": 42})],
            QueryIntent.CALCULATION,
        )
        web = scorer.calculate(
            [_make_tool_result("web_search")],
            QueryIntent.RETRIEVAL,
        )
        assert calc.source_reliability >= web.source_reliability

    def test_completeness_gap_detection(self):
        scorer = ConfidenceScorer()
        results = [_make_tool_result()]
        gaps = scorer.calculate(results, QueryIntent.RETRIEVAL, answer_text="This is unknown and incomplete.")
        clean = scorer.calculate(results, QueryIntent.RETRIEVAL, answer_text="ML is a subset of AI.")
        assert clean.completeness >= gaps.completeness

    def test_all_failed_results(self):
        scorer = ConfidenceScorer()
        results = [
            _make_tool_result("vector_search", success=False, data={}),
            _make_tool_result("web_search", success=False, data={}),
        ]
        score = scorer.calculate(results, QueryIntent.RETRIEVAL)
        assert score.tool_success_rate == 0.0
        assert score.source_reliability == 0.0


class TestAnswerQualityAssessment:
    def test_is_acceptable_above(self):
        a = AnswerQualityAssessment(overall_score=0.8)
        assert a.is_acceptable(0.7) is True

    def test_is_acceptable_below(self):
        a = AnswerQualityAssessment(overall_score=0.5)
        assert a.is_acceptable(0.7) is False

    def test_get_lowest_dimension_empty(self):
        a = AnswerQualityAssessment(overall_score=0.5)
        dim, score = a.get_lowest_dimension()
        assert dim == QualityDimension.COMPLETENESS
        assert score == 0.0

    def test_get_lowest_dimension(self):
        a = AnswerQualityAssessment(
            overall_score=0.6,
            dimension_scores={
                QualityDimension.COMPLETENESS: 0.8,
                QualityDimension.ACCURACY: 0.3,
                QualityDimension.RELEVANCE: 0.7,
            },
        )
        dim, score = a.get_lowest_dimension()
        assert dim == QualityDimension.ACCURACY
        assert score == 0.3

    def test_invalid_score_rejected(self):
        with pytest.raises(Exception):
            AnswerQualityAssessment(overall_score=1.5)


class TestReflectionEngine:
    def test_assess_quality_good_answer(self):
        engine = ReflectionEngine()
        plan = _make_query_plan()
        results = [_make_tool_result()]
        assessment = engine.assess_quality(
            answer=(
                "Machine learning is a subset of AI. "
                "According to sources, it enables learning from data. "
                "Therefore, it is widely used."
            ),
            query="What is machine learning?",
            tool_results=results,
            query_plan=plan,
        )
        assert assessment.overall_score > 0.0
        assert len(assessment.dimension_scores) == 7

    def test_assess_quality_empty_answer(self):
        engine = ReflectionEngine()
        assessment = engine.assess_quality(
            answer="",
            query="What is ML?",
            tool_results=[_make_tool_result()],
            query_plan=_make_query_plan(),
        )
        assert assessment.overall_score < 0.3

    def test_assess_quality_no_tools(self):
        engine = ReflectionEngine()
        assessment = engine.assess_quality(
            answer="Some answer.",
            query="What is ML?",
            tool_results=[],
            query_plan=_make_query_plan(),
        )
        assert assessment.dimension_scores[QualityDimension.ACCURACY] == 0.0

    def test_identify_gaps_missing_entities(self):
        engine = ReflectionEngine()
        plan = _make_query_plan(query="Explain deep learning and neural networks")
        plan.intent_analysis.entities = ["Deep Learning", "Neural Networks"]
        gaps = engine.identify_gaps(
            answer="This is about computing.",
            query="Explain deep learning and neural networks",
            query_plan=plan,
        )
        assert any("Deep Learning" in g for g in gaps) or any("Neural Networks" in g for g in gaps)

    def test_identify_gaps_uncertainty_keywords(self):
        engine = ReflectionEngine()
        gaps = engine.identify_gaps(
            answer="The answer is unknown and not available.",
            query="What is ML?",
            query_plan=_make_query_plan(),
        )
        assert any("unknown" in g for g in gaps)
        assert any("not available" in g for g in gaps)

    def test_generate_correction_low_completeness(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(
            overall_score=0.3,
            dimension_scores={
                QualityDimension.COMPLETENESS: 0.2,
                QualityDimension.ACCURACY: 0.9,
            },
            gaps=["Missing info"],
            recommendations=["Expand search"],
        )
        strategies = engine.generate_correction_strategies(assessment)
        assert len(strategies) > 0
        assert any(s.action_type == "expand_search" for s in strategies)

    def test_generate_correction_low_accuracy(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(
            overall_score=0.4,
            dimension_scores={
                QualityDimension.COMPLETENESS: 0.9,
                QualityDimension.ACCURACY: 0.2,
            },
            recommendations=["Verify"],
        )
        strategies = engine.generate_correction_strategies(assessment)
        assert any(s.action_type == "verify_sources" for s in strategies)

    def test_corrections_sorted_by_priority(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(
            overall_score=0.3,
            dimension_scores={QualityDimension.COMPLETENESS: 0.2},
            gaps=["gap1", "gap2"],
            recommendations=["Do something"],
        )
        strategies = engine.generate_correction_strategies(assessment)
        priorities = [s.priority for s in strategies]
        assert priorities == sorted(priorities, reverse=True)

    def test_should_iterate_true_below_threshold(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(overall_score=0.4, recommendations=["improve"])
        assert engine.should_iterate(assessment, 1) is True

    def test_should_iterate_false_above_threshold(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(overall_score=0.9, recommendations=["tweak"])
        assert engine.should_iterate(assessment, 1) is False

    def test_should_iterate_false_max_iterations(self):
        config = ReflectionConfig(max_iterations=2)
        engine = ReflectionEngine(config)
        assessment = AnswerQualityAssessment(overall_score=0.3, recommendations=["improve"])
        assert engine.should_iterate(assessment, 2) is False

    def test_should_iterate_false_disabled(self):
        config = ReflectionConfig(enable_self_correction=False)
        engine = ReflectionEngine(config)
        assessment = AnswerQualityAssessment(overall_score=0.3, recommendations=["improve"])
        assert engine.should_iterate(assessment, 1) is False

    def test_should_iterate_false_no_recommendations(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(overall_score=0.3, recommendations=[])
        assert engine.should_iterate(assessment, 1) is False

    def test_should_iterate_false_high_confidence(self):
        engine = ReflectionEngine()
        assessment = AnswerQualityAssessment(overall_score=0.5, recommendations=["improve"])
        assert engine.should_iterate(assessment, 1, ConfidenceScore(overall=0.95)) is False


class TestCorrectionStrategy:
    def test_create_strategy(self):
        strategy = CorrectionStrategy(
            target_dimension=QualityDimension.COMPLETENESS,
            description="Expand search",
            action_type="expand_search",
        )
        assert strategy.priority == 3
        assert strategy.expected_improvement == 0.1

    def test_strategy_priority_range(self):
        with pytest.raises(Exception):
            CorrectionStrategy(
                target_dimension=QualityDimension.ACCURACY,
                description="test",
                action_type="test",
                priority=6,
            )


class TestReflectionConfig:
    def test_default_config(self):
        config = ReflectionConfig()
        assert config.quality_threshold == 0.7
        assert config.max_iterations == 3
        assert config.enable_self_correction is True
        assert len(config.dimension_weights) == 7
        total = sum(config.dimension_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_custom_config(self):
        config = ReflectionConfig(quality_threshold=0.8, max_iterations=5)
        assert config.quality_threshold == 0.8
        assert config.max_iterations == 5