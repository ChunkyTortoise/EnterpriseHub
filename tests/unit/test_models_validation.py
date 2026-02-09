"""Unit tests for Pydantic model validation across the model layer.

Covers:
- analytics_models.py: RevenueForecast, FunnelMetrics, FunnelAnalysis, etc.
- ai_concierge_models.py: ProactiveInsight, CoachingOpportunity, StrategyRecommendation, etc.
- lead_scoring.py: MotivationSignals, FinancialReadinessScore, BuyerIntentProfile, etc.
- bot_handoff.py: BotType, TransitionReason, dataclass serialization round-trips

Tests Pydantic validation boundaries: missing required fields, wrong types, field
constraints (ge/le), enum validation, custom validators, and model_validator logic.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.unit


# ============================================================================
# Analytics Models — Enums
# ============================================================================


class TestAnalyticsEnums:
    """Tests for analytics model enumerations."""

    def test_forecast_horizon_values(self):
        from ghl_real_estate_ai.models.analytics_models import ForecastHorizon

        assert ForecastHorizon.WEEKLY.value == "weekly"
        assert ForecastHorizon.ANNUAL.value == "annual"

    def test_funnel_stage_values(self):
        from ghl_real_estate_ai.models.analytics_models import FunnelStage

        assert FunnelStage.NEW_LEAD.value == "new_lead"
        assert FunnelStage.CLOSED.value == "closed"

    def test_market_temperature_values(self):
        from ghl_real_estate_ai.models.analytics_models import MarketTemperature

        assert MarketTemperature.HOT.value == "hot"
        assert MarketTemperature.COLD.value == "cold"

    def test_competitive_pressure_values(self):
        from ghl_real_estate_ai.models.analytics_models import CompetitivePressure

        assert CompetitivePressure.LOW.value == "low"
        assert CompetitivePressure.VERY_HIGH.value == "very_high"


# ============================================================================
# Analytics Models — RevenueForecast
# ============================================================================


class TestRevenueForecast:
    """Tests for RevenueForecast Pydantic model."""

    def _valid_data(self, **overrides):
        base = {
            "forecasted_revenue": 150000.0,
            "confidence_lower": 120000.0,
            "confidence_upper": 180000.0,
            "confidence_level": 0.95,
            "forecast_horizon_days": 30,
            "predicted_conversions": 5,
            "avg_deal_value": 30000.0,
            "model_accuracy": 0.85,
            "historical_mape": 12.5,
            "key_assumptions": ["Market stable", "No policy changes"],
            "risk_factors": ["Interest rate hike"],
            "market_conditions": "hot",
            "model_version": "v2.1",
            "forecast_date": date(2026, 3, 1),
        }
        base.update(overrides)
        return base

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.analytics_models import RevenueForecast

        rf = RevenueForecast(**self._valid_data())
        assert rf.forecasted_revenue == 150000.0
        assert rf.confidence_level == 0.95

    def test_confidence_level_too_low(self):
        from ghl_real_estate_ai.models.analytics_models import RevenueForecast

        with pytest.raises(Exception):
            RevenueForecast(**self._valid_data(confidence_level=0.3))

    def test_confidence_level_too_high(self):
        from ghl_real_estate_ai.models.analytics_models import RevenueForecast

        with pytest.raises(Exception):
            RevenueForecast(**self._valid_data(confidence_level=1.5))

    def test_model_accuracy_boundary(self):
        from ghl_real_estate_ai.models.analytics_models import RevenueForecast

        rf = RevenueForecast(**self._valid_data(model_accuracy=0.0))
        assert rf.model_accuracy == 0.0
        rf2 = RevenueForecast(**self._valid_data(model_accuracy=1.0))
        assert rf2.model_accuracy == 1.0

    def test_model_accuracy_out_of_range(self):
        from ghl_real_estate_ai.models.analytics_models import RevenueForecast

        with pytest.raises(Exception):
            RevenueForecast(**self._valid_data(model_accuracy=1.5))


# ============================================================================
# Analytics Models — FunnelMetrics
# ============================================================================


class TestFunnelMetrics:
    """Tests for FunnelMetrics Pydantic model."""

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.analytics_models import FunnelMetrics, FunnelStage

        fm = FunnelMetrics(
            stage=FunnelStage.QUALIFIED,
            lead_count=100,
            conversion_rate=0.25,
            avg_time_in_stage_days=7.5,
            drop_off_count=75,
            drop_off_percentage=0.75,
        )
        assert fm.stage == FunnelStage.QUALIFIED
        assert fm.conversion_rate == 0.25

    def test_conversion_rate_boundary_zero(self):
        from ghl_real_estate_ai.models.analytics_models import FunnelMetrics, FunnelStage

        fm = FunnelMetrics(
            stage=FunnelStage.NEW_LEAD,
            lead_count=0,
            conversion_rate=0.0,
            avg_time_in_stage_days=0,
            drop_off_count=0,
            drop_off_percentage=0.0,
        )
        assert fm.conversion_rate == 0.0

    def test_conversion_rate_boundary_one(self):
        from ghl_real_estate_ai.models.analytics_models import FunnelMetrics, FunnelStage

        fm = FunnelMetrics(
            stage=FunnelStage.CLOSED,
            lead_count=10,
            conversion_rate=1.0,
            avg_time_in_stage_days=30,
            drop_off_count=0,
            drop_off_percentage=0.0,
        )
        assert fm.conversion_rate == 1.0

    def test_conversion_rate_above_one_rejected(self):
        from ghl_real_estate_ai.models.analytics_models import FunnelMetrics, FunnelStage

        with pytest.raises(Exception):
            FunnelMetrics(
                stage=FunnelStage.QUALIFIED,
                lead_count=10,
                conversion_rate=1.5,
                avg_time_in_stage_days=5,
                drop_off_count=0,
                drop_off_percentage=0.0,
            )


# ============================================================================
# AI Concierge Models — ProactiveInsight
# ============================================================================


class TestProactiveInsight:
    """Tests for ProactiveInsight — complex Pydantic validation."""

    def _valid_data(self, **overrides):
        now = datetime.utcnow()
        base = {
            "insight_type": "coaching",
            "priority": "medium",
            "title": "Coaching opportunity detected in conversation",
            "description": "The lead mentioned budget concerns twice — consider proactive value articulation.",
            "reasoning": "Pattern analysis shows recurring budget hesitation markers",
            "recommended_actions": ["Address value proposition", "Share success story"],
            "confidence_score": 0.75,
            "expected_impact": 0.6,
            "applicable_stage": "value_presentation",
            "created_at": now,
            "expires_at": now + timedelta(hours=2),
        }
        base.update(overrides)
        return base

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        insight = ProactiveInsight(**self._valid_data())
        assert insight.priority.value == "medium"
        assert insight.confidence_score == 0.75

    def test_title_too_short(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception):
            ProactiveInsight(**self._valid_data(title="Hi"))

    def test_description_too_short(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception):
            ProactiveInsight(**self._valid_data(description="Short"))

    def test_confidence_score_out_of_range(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception):
            ProactiveInsight(**self._valid_data(confidence_score=1.5))

    def test_confidence_score_negative(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception):
            ProactiveInsight(**self._valid_data(confidence_score=-0.1))

    def test_expires_before_created_rejected(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        now = datetime.utcnow()
        with pytest.raises(Exception):
            ProactiveInsight(**self._valid_data(
                created_at=now,
                expires_at=now - timedelta(hours=1),
            ))

    def test_critical_priority_requires_high_confidence(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception, match="confidence >= 0.8"):
            ProactiveInsight(**self._valid_data(
                priority="critical",
                confidence_score=0.5,
            ))

    def test_high_priority_requires_moderate_confidence(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception, match="confidence >= 0.7"):
            ProactiveInsight(**self._valid_data(
                priority="high",
                confidence_score=0.5,
            ))

    def test_critical_with_sufficient_confidence(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        insight = ProactiveInsight(**self._valid_data(
            priority="critical",
            confidence_score=0.9,
        ))
        assert insight.priority.value == "critical"

    def test_empty_actions_rejected(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        with pytest.raises(Exception):
            ProactiveInsight(**self._valid_data(recommended_actions=[]))

    def test_is_expired(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        insight = ProactiveInsight(**self._valid_data(
            expires_at=datetime.utcnow() - timedelta(seconds=1),
            created_at=datetime.utcnow() - timedelta(hours=3),
        ))
        assert insight.is_expired() is True

    def test_is_actionable(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        insight = ProactiveInsight(**self._valid_data())
        assert insight.is_actionable() is True

    def test_dismissed_not_actionable(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ProactiveInsight

        insight = ProactiveInsight(**self._valid_data(dismissed=True))
        assert insight.is_actionable() is False


# ============================================================================
# AI Concierge Models — CoachingOpportunity
# ============================================================================


class TestCoachingOpportunity:
    """Tests for CoachingOpportunity validation."""

    def _valid_data(self, **overrides):
        base = {
            "coaching_category": "objection_handling",
            "detected_pattern": "Lead raised price concern but agent didn't acknowledge emotion first",
            "missed_opportunity": "Could have validated concern before presenting value proposition",
            "coaching_insight": "Always acknowledge the emotional component of objections before addressing logical aspects of the concern",
            "recommended_technique": "Feel-Felt-Found method with empathy bridge",
            "example_response": "I understand price is a real concern — other successful sellers felt the same way initially.",
            "success_probability": 0.82,
            "skill_level_required": "intermediate",
            "immediate_application": True,
            "learning_objective": "Master empathetic objection handling for price concerns",
        }
        base.update(overrides)
        return base

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.ai_concierge_models import CoachingOpportunity

        co = CoachingOpportunity(**self._valid_data())
        assert co.coaching_category.value == "objection_handling"
        assert co.success_probability == 0.82

    def test_invalid_skill_level(self):
        from ghl_real_estate_ai.models.ai_concierge_models import CoachingOpportunity

        with pytest.raises(Exception):
            CoachingOpportunity(**self._valid_data(skill_level_required="expert"))

    def test_success_probability_out_of_range(self):
        from ghl_real_estate_ai.models.ai_concierge_models import CoachingOpportunity

        with pytest.raises(Exception):
            CoachingOpportunity(**self._valid_data(success_probability=1.5))

    def test_get_coaching_priority_high(self):
        from ghl_real_estate_ai.models.ai_concierge_models import CoachingOpportunity, InsightPriority

        co = CoachingOpportunity(**self._valid_data(
            immediate_application=True,
            success_probability=0.9,
        ))
        assert co.get_coaching_priority() == InsightPriority.HIGH

    def test_get_coaching_priority_medium(self):
        from ghl_real_estate_ai.models.ai_concierge_models import CoachingOpportunity, InsightPriority

        co = CoachingOpportunity(**self._valid_data(
            immediate_application=False,
            success_probability=0.75,
        ))
        assert co.get_coaching_priority() == InsightPriority.MEDIUM

    def test_get_coaching_priority_low(self):
        from ghl_real_estate_ai.models.ai_concierge_models import CoachingOpportunity, InsightPriority

        co = CoachingOpportunity(**self._valid_data(
            immediate_application=False,
            success_probability=0.3,
        ))
        assert co.get_coaching_priority() == InsightPriority.LOW


# ============================================================================
# AI Concierge Models — StrategyRecommendation
# ============================================================================


class TestStrategyRecommendation:
    """Tests for StrategyRecommendation validation."""

    def _valid_data(self, **overrides):
        base = {
            "strategy_type": "pivot_to_buyer",
            "strategy_title": "Shift conversation focus from seller to buyer interests",
            "strategy_description": "Lead signals buyer interest — ready to transition to buyer consultation mode for better outcome.",
            "rationale": "Lead asked about available properties twice and mentioned a moving timeline",
            "implementation_steps": [
                "Acknowledge seller interest completion",
                "Ask about next home purchase plans",
                "Transition to buyer consultation mode",
            ],
            "conversation_pivot": "Since we covered your selling timeline, I'm curious about your next move — have you started looking?",
            "expected_outcome": "Dual-side client with both listing and buyer representation",
            "impact_score": 0.85,
            "urgency_level": "soon",
            "trigger_conditions": ["Buyer questions asked (2x)", "Moving timeline mentioned"],
            "success_indicators": ["Lead engages with buyer questions", "Shares preferences"],
            "risk_level": "low",
        }
        base.update(overrides)
        return base

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.ai_concierge_models import StrategyRecommendation

        sr = StrategyRecommendation(**self._valid_data())
        assert sr.impact_score == 0.85

    def test_invalid_urgency_level(self):
        from ghl_real_estate_ai.models.ai_concierge_models import StrategyRecommendation

        with pytest.raises(Exception):
            StrategyRecommendation(**self._valid_data(urgency_level="asap"))

    def test_invalid_risk_level(self):
        from ghl_real_estate_ai.models.ai_concierge_models import StrategyRecommendation

        with pytest.raises(Exception):
            StrategyRecommendation(**self._valid_data(risk_level="extreme"))

    def test_implementation_steps_too_few(self):
        from ghl_real_estate_ai.models.ai_concierge_models import StrategyRecommendation

        with pytest.raises(Exception):
            StrategyRecommendation(**self._valid_data(implementation_steps=["Only one"]))

    def test_get_priority_critical(self):
        from ghl_real_estate_ai.models.ai_concierge_models import InsightPriority, StrategyRecommendation

        sr = StrategyRecommendation(**self._valid_data(
            urgency_level="immediate",
            impact_score=0.9,
        ))
        assert sr.get_priority() == InsightPriority.CRITICAL

    def test_get_priority_high(self):
        from ghl_real_estate_ai.models.ai_concierge_models import InsightPriority, StrategyRecommendation

        sr = StrategyRecommendation(**self._valid_data(
            urgency_level="soon",
            impact_score=0.7,
        ))
        assert sr.get_priority() == InsightPriority.HIGH


# ============================================================================
# AI Concierge Models — ConversationQualityScore
# ============================================================================


class TestConversationQualityScore:
    """Tests for ConversationQualityScore — model_validator logic."""

    def _valid_data(self, **overrides):
        now = datetime.utcnow()
        base = {
            "conversation_id": "conv-123",
            "engagement_score": 82.0,
            "rapport_score": 75.0,
            "needs_discovery_score": 80.0,
            "value_articulation_score": 85.0,
            "objection_handling_score": 70.0,
            "closing_effectiveness_score": 75.0,
            "conversation_length": 24,
            "response_time_avg": 1.2,
            "lead_participation_rate": 0.65,
            "strengths": ["Good rapport", "Strong value"],
            "improvement_areas": ["Objection handling"],
            "specific_recommendations": ["Use feel-felt-found"],
            "quality_trend": "improving",
            "stage_appropriateness": 0.85,
            "next_assessment_due": now + timedelta(hours=1),
        }
        base.update(overrides)
        return base

    def test_auto_calculates_overall_score(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        cqs = ConversationQualityScore(**self._valid_data())
        # Should have auto-calculated overall_score
        assert cqs.overall_score > 0

    def test_auto_assigns_grade(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        cqs = ConversationQualityScore(**self._valid_data())
        assert cqs.quality_grade in {"A", "B", "C", "D", "F"}

    def test_grade_a_for_high_scores(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        data = self._valid_data(
            overall_score=95.0,
            engagement_score=95.0,
            rapport_score=95.0,
            needs_discovery_score=95.0,
            value_articulation_score=95.0,
            objection_handling_score=95.0,
            closing_effectiveness_score=95.0,
        )
        cqs = ConversationQualityScore(**data)
        assert cqs.quality_grade == "A"

    def test_grade_f_for_low_scores(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        data = self._valid_data(
            overall_score=30.0,
            engagement_score=30.0,
            rapport_score=30.0,
            needs_discovery_score=30.0,
            value_articulation_score=30.0,
            objection_handling_score=30.0,
            closing_effectiveness_score=30.0,
        )
        cqs = ConversationQualityScore(**data)
        assert cqs.quality_grade == "F"

    def test_invalid_quality_trend(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        with pytest.raises(Exception):
            ConversationQualityScore(**self._valid_data(quality_trend="skyrocketing"))

    def test_lead_participation_rate_boundary(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        cqs = ConversationQualityScore(**self._valid_data(lead_participation_rate=0.0))
        assert cqs.lead_participation_rate == 0.0

    def test_lead_participation_rate_above_one_rejected(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore

        with pytest.raises(Exception):
            ConversationQualityScore(**self._valid_data(lead_participation_rate=1.5))

    def test_get_improvement_priority_high_for_low_score(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationQualityScore, InsightPriority

        cqs = ConversationQualityScore(**self._valid_data(
            overall_score=50.0,
            engagement_score=50.0,
            rapport_score=50.0,
            needs_discovery_score=50.0,
            value_articulation_score=50.0,
            objection_handling_score=50.0,
            closing_effectiveness_score=50.0,
        ))
        assert cqs.get_improvement_priority() == InsightPriority.HIGH


# ============================================================================
# AI Concierge Models — ConversationTrajectory
# ============================================================================


class TestConversationTrajectory:
    """Tests for ConversationTrajectory validation."""

    def _valid_data(self, **overrides):
        now = datetime.utcnow()
        base = {
            "conversation_id": "conv-456",
            "predicted_outcome": "schedule_meeting",
            "outcome_confidence": 0.78,
            "outcome_probabilities": {
                "schedule_meeting": 0.45,
                "nurture": 0.30,
                "conversion": 0.15,
                "disqualify": 0.10,
            },
            "estimated_time_to_decision": 48,
            "estimated_messages_remaining": 8,
            "optimal_follow_up_timing": "24 hours if no response",
            "current_stage": "value_presentation",
            "stage_progression": ["value_presentation", "objection_handling", "closing"],
            "stall_probability": 0.25,
            "momentum_score": 0.75,
            "momentum_trend": "stable",
            "recommended_next_steps": ["Request meeting time", "Send calendar link"],
            "next_analysis_due": now + timedelta(hours=1),
        }
        base.update(overrides)
        return base

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationTrajectory

        ct = ConversationTrajectory(**self._valid_data())
        assert ct.predicted_outcome == "schedule_meeting"

    def test_probabilities_must_sum_to_one(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationTrajectory

        with pytest.raises(Exception, match="sum to approximately 1.0"):
            ConversationTrajectory(**self._valid_data(
                outcome_probabilities={"conversion": 0.5, "nurture": 0.1}
            ))

    def test_invalid_predicted_outcome(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationTrajectory

        with pytest.raises(Exception):
            ConversationTrajectory(**self._valid_data(predicted_outcome="magic"))

    def test_invalid_momentum_trend(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationTrajectory

        with pytest.raises(Exception):
            ConversationTrajectory(**self._valid_data(momentum_trend="exploding"))

    def test_get_urgency_critical_when_stall_high(self):
        from ghl_real_estate_ai.models.ai_concierge_models import ConversationTrajectory, InsightPriority

        ct = ConversationTrajectory(**self._valid_data(stall_probability=0.8))
        assert ct.get_urgency_level() == InsightPriority.CRITICAL


# ============================================================================
# Lead Scoring Models — MotivationSignals
# ============================================================================


class TestMotivationSignals:
    """Tests for MotivationSignals constrained int scoring."""

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.lead_scoring import MotivationSignals

        ms = MotivationSignals(
            score=75,
            detected_markers=["relocating", "growing family"],
            category="High Intent",
        )
        assert ms.score == 75
        assert len(ms.detected_markers) == 2

    def test_score_above_100_rejected(self):
        from ghl_real_estate_ai.models.lead_scoring import MotivationSignals

        with pytest.raises(Exception):
            MotivationSignals(score=150, category="High Intent")

    def test_score_below_zero_rejected(self):
        from ghl_real_estate_ai.models.lead_scoring import MotivationSignals

        with pytest.raises(Exception):
            MotivationSignals(score=-5, category="Low Intent")

    def test_score_boundary_zero(self):
        from ghl_real_estate_ai.models.lead_scoring import MotivationSignals

        ms = MotivationSignals(score=0, category="Low Intent")
        assert ms.score == 0

    def test_score_boundary_100(self):
        from ghl_real_estate_ai.models.lead_scoring import MotivationSignals

        ms = MotivationSignals(score=100, category="High Intent")
        assert ms.score == 100


# ============================================================================
# Lead Scoring Models — FinancialReadinessScore
# ============================================================================


class TestFinancialReadinessScore:
    """Tests for the composite FinancialReadinessScore model."""

    def _valid_data(self, **overrides):
        base = {
            "total_score": 72.5,
            "motivation": {
                "score": 80,
                "detected_markers": ["relocating"],
                "category": "High Intent",
            },
            "timeline": {
                "score": 70,
                "category": "Flexible",
            },
            "condition": {
                "score": 65,
                "category": "Negotiable",
            },
            "price": {
                "score": 60,
                "category": "Price-Aware",
            },
            "classification": "Warm",
        }
        base.update(overrides)
        return base

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.lead_scoring import FinancialReadinessScore

        frs = FinancialReadinessScore(**self._valid_data())
        assert frs.total_score == 72.5
        assert frs.classification == "Warm"
        assert frs.motivation.score == 80

    def test_nested_score_validation(self):
        from ghl_real_estate_ai.models.lead_scoring import FinancialReadinessScore

        with pytest.raises(Exception):
            data = self._valid_data()
            data["motivation"]["score"] = 200
            FinancialReadinessScore(**data)


# ============================================================================
# Lead Scoring Models — BuyerIntentProfile
# ============================================================================


class TestBuyerIntentProfile:
    """Tests for BuyerIntentProfile required fields."""

    def _valid_data(self):
        return {
            "financial_readiness": 75.0,
            "budget_clarity": 80.0,
            "financing_status_score": 70.0,
            "urgency_score": 65.0,
            "timeline_pressure": 60.0,
            "consequence_awareness": 55.0,
            "preference_clarity": 80.0,
            "market_realism": 70.0,
            "decision_authority": 90.0,
            "buyer_temperature": "warm",
            "confidence_level": 0.82,
            "conversation_turns": 12,
            "next_qualification_step": "financial_verification",
        }

    def test_valid_creation(self):
        from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

        bip = BuyerIntentProfile(**self._valid_data())
        assert bip.buyer_temperature == "warm"
        assert bip.financial_readiness == 75.0

    def test_missing_required_field(self):
        from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

        data = self._valid_data()
        del data["financial_readiness"]
        with pytest.raises(Exception):
            BuyerIntentProfile(**data)


# ============================================================================
# Bot Handoff Models — Enums
# ============================================================================


class TestBotHandoffEnums:
    """Tests for bot handoff enumerations."""

    def test_bot_type_values(self):
        from ghl_real_estate_ai.models.bot_handoff import BotType

        assert BotType.JORGE_SELLER.value == "jorge-seller"
        assert BotType.LEAD_BOT.value == "lead-bot"
        assert BotType.MANUAL_AGENT.value == "manual-agent"

    def test_transition_reason_values(self):
        from ghl_real_estate_ai.models.bot_handoff import TransitionReason

        assert TransitionReason.QUALIFIED_BUYER.value == "qualified_buyer"
        assert TransitionReason.ESCALATION_REQUESTED.value == "escalation"

    def test_handoff_status_values(self):
        from ghl_real_estate_ai.models.bot_handoff import HandoffStatus

        assert HandoffStatus.SUCCESS.value == "success"
        assert HandoffStatus.EXPIRED.value == "expired"


# ============================================================================
# Bot Handoff Models — Serialization Round-Trips
# ============================================================================


class TestBotHandoffSerialization:
    """Tests for bot handoff model serialization and deserialization."""

    def test_preserved_intelligence_round_trip(self):
        from ghl_real_estate_ai.models.bot_handoff import PreservedIntelligence

        pi = PreservedIntelligence(
            best_match_score=0.92,
            conversation_quality_score=85.0,
            overall_sentiment=0.7,
            urgency_level=0.8,
        )
        data = pi.to_dict()
        restored = PreservedIntelligence.from_dict(data)
        assert restored.best_match_score == 0.92
        assert restored.urgency_level == 0.8

    def test_preserved_intelligence_empty(self):
        from ghl_real_estate_ai.models.bot_handoff import PreservedIntelligence

        empty = PreservedIntelligence.create_empty()
        assert empty.best_match_score == 0.0
        assert empty.conversation_quality_score == 50.0

    def test_intelligence_snapshot_round_trip(self):
        from ghl_real_estate_ai.models.bot_handoff import (
            BotType,
            IntelligenceSnapshot,
            PreservedIntelligence,
            TransitionReason,
        )

        snapshot = IntelligenceSnapshot(
            snapshot_id="snap-1",
            lead_id="lead-1",
            location_id="loc-1",
            source_bot=BotType.LEAD_BOT,
            target_bot=BotType.JORGE_BUYER,
            snapshot_timestamp=datetime.now(timezone.utc),
            preserved_intelligence=PreservedIntelligence(best_match_score=0.88),
            conversation_summary="Active buyer conversation",
            transition_reason=TransitionReason.QUALIFIED_BUYER,
        )
        json_str = snapshot.to_json()
        restored = IntelligenceSnapshot.from_json(json_str)
        assert restored.snapshot_id == "snap-1"
        assert restored.source_bot == BotType.LEAD_BOT
        assert restored.preserved_intelligence.best_match_score == 0.88

    def test_intelligence_snapshot_empty_factory(self):
        from ghl_real_estate_ai.models.bot_handoff import BotType, IntelligenceSnapshot

        empty = IntelligenceSnapshot.create_empty("lead-2", "loc-2", BotType.JORGE_SELLER)
        assert empty.confidence_level == 0.0
        assert empty.data_completeness == 0.0
        assert "Fallback" in empty.handoff_message

    def test_bot_transition_round_trip(self):
        from ghl_real_estate_ai.models.bot_handoff import BotTransition, BotType, TransitionReason

        bt = BotTransition(
            transition_id="trans-1",
            lead_id="lead-1",
            location_id="loc-1",
            source_bot=BotType.JORGE_SELLER,
            target_bot=BotType.JORGE_BUYER,
            transition_reason=TransitionReason.QUALIFIED_BUYER,
            handoff_message="Lead wants to buy too",
            priority_level="high",
        )
        data = bt.to_dict()
        restored = BotTransition.from_dict(data)
        assert restored.transition_id == "trans-1"
        assert restored.source_bot == BotType.JORGE_SELLER
        assert restored.priority_level == "high"

    def test_context_handoff_success_factory(self):
        from ghl_real_estate_ai.models.bot_handoff import ContextHandoff, HandoffStatus

        ch = ContextHandoff.create_success(
            lead_id="lead-1",
            location_id="loc-1",
            intelligence_snapshot_id="snap-1",
            transition_id="trans-1",
            preservation_latency_ms=45.2,
            cache_key="handoff:lead-1",
        )
        assert ch.success is True
        assert ch.handoff_status == HandoffStatus.SUCCESS
        assert ch.preservation_latency_ms == 45.2
        assert ch.handoff_completed_at is not None

    def test_context_handoff_failure_factory(self):
        from ghl_real_estate_ai.models.bot_handoff import ContextHandoff, HandoffStatus

        ch = ContextHandoff.create_failure(
            lead_id="lead-1",
            location_id="loc-1",
            error_message="Redis connection timeout",
        )
        assert ch.success is False
        assert ch.handoff_status == HandoffStatus.FAILED
        assert ch.error_message == "Redis connection timeout"

    def test_transition_history_add_transition(self):
        from ghl_real_estate_ai.models.bot_handoff import (
            BotTransition,
            BotType,
            ContextHandoff,
            HandoffStatus,
            TransitionHistory,
            TransitionReason,
        )

        history = TransitionHistory.create_empty("lead-1", "loc-1")
        assert history.total_transitions == 0

        bt = BotTransition(
            transition_id="t1",
            lead_id="lead-1",
            location_id="loc-1",
            source_bot=BotType.LEAD_BOT,
            target_bot=BotType.JORGE_BUYER,
            transition_reason=TransitionReason.LEAD_ACTIVATED,
            handoff_message="Activating lead",
        )
        ch = ContextHandoff.create_success(
            lead_id="lead-1",
            location_id="loc-1",
            intelligence_snapshot_id="s1",
            transition_id="t1",
            preservation_latency_ms=30.0,
            cache_key="key-1",
        )
        history.add_transition(bt, ch)

        assert history.total_transitions == 1
        assert history.successful_handoffs == 1
        assert history.failed_handoffs == 0
        assert history.get_success_rate() == 1.0

    def test_transition_history_success_rate_with_failures(self):
        from ghl_real_estate_ai.models.bot_handoff import (
            BotTransition,
            BotType,
            ContextHandoff,
            TransitionHistory,
            TransitionReason,
        )

        history = TransitionHistory.create_empty("lead-1", "loc-1")

        for i in range(3):
            bt = BotTransition(
                transition_id=f"t{i}",
                lead_id="lead-1",
                location_id="loc-1",
                source_bot=BotType.LEAD_BOT,
                target_bot=BotType.JORGE_BUYER,
                transition_reason=TransitionReason.LEAD_ACTIVATED,
                handoff_message="Test",
            )
            if i < 2:
                ch = ContextHandoff.create_success(
                    lead_id="lead-1", location_id="loc-1",
                    intelligence_snapshot_id=f"s{i}", transition_id=f"t{i}",
                    preservation_latency_ms=25.0, cache_key=f"k{i}",
                )
            else:
                ch = ContextHandoff.create_failure(
                    lead_id="lead-1", location_id="loc-1",
                    error_message="Timeout",
                )
            history.add_transition(bt, ch)

        assert history.total_transitions == 3
        assert history.successful_handoffs == 2
        assert history.failed_handoffs == 1
        assert history.get_success_rate() == pytest.approx(2 / 3, abs=0.01)
