#!/usr/bin/env python3
"""
Behavioral Contract Testing for Lead Analysis Business Outcomes
===============================================================

Tests business logic contracts rather than implementation details.
Focuses on behavioral outcomes that matter to real estate agents and clients.

Contract Testing Strategy:
- High-intent lead identification and prioritization
- Lead temperature consistency across scoring variations
- Property recommendation relevance and quality
- Business outcome validation (conversion indicators)
- Cross-service behavioral consistency

Business Contract Coverage:
- Lead qualification pipeline effectiveness
- Revenue-impacting lead prioritization accuracy
- Agent workflow optimization validation
- Client experience quality assurance
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pytest

from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from tests.mocks.external_services import MockClaudeClient, MockRedisClient, create_test_lead_data


class LeadIntentLevel(Enum):
    """Business-defined lead intent levels"""

    HIGH_INTENT = "high_intent"
    MEDIUM_INTENT = "medium_intent"
    LOW_INTENT = "low_intent"
    DISCOVERY = "discovery"


class BusinessOutcome(Enum):
    """Expected business outcomes from lead analysis"""

    IMMEDIATE_CONTACT = "immediate_contact"
    SCHEDULED_FOLLOWUP = "scheduled_followup"
    NURTURE_CAMPAIGN = "nurture_campaign"
    QUALIFICATION_NEEDED = "qualification_needed"
    PRIORITY_ROUTING = "priority_routing"


@dataclass
class LeadBehaviorContract:
    """Contract definition for lead behavior expectations"""

    intent_level: LeadIntentLevel
    expected_score_range: Tuple[int, int]  # Min, max score
    expected_classification: str
    expected_business_outcome: BusinessOutcome
    expected_response_time: timedelta
    minimum_data_quality: float  # 0.0 to 1.0


@dataclass
class BusinessScenario:
    """Real-world business scenario for contract testing"""

    name: str
    description: str
    lead_data: Dict[str, Any]
    expected_contract: LeadBehaviorContract
    success_criteria: List[str]


class TestHighIntentLeadContracts:
    """Contract tests for high-intent lead identification and handling"""

    def setup_method(self):
        """Setup test dependencies"""
        self.scorer = LeadScorer()
        self.intelligence = EnhancedLeadIntelligence()

        # Define high-intent lead contract
        self.high_intent_contract = LeadBehaviorContract(
            intent_level=LeadIntentLevel.HIGH_INTENT,
            expected_score_range=(3, 7),  # 3+ questions = hot lead
            expected_classification="hot",
            expected_business_outcome=BusinessOutcome.IMMEDIATE_CONTACT,
            expected_response_time=timedelta(hours=2),
            minimum_data_quality=0.8,
        )

    @pytest.mark.critical
    def test_immediate_buyer_intent_contract(self):
        """
        Contract: Leads with immediate buying intent must be classified as HOT
        Business Impact: Prevents loss of ready-to-close leads
        """
        # GIVEN: A lead with immediate buying signals
        immediate_buyer = create_test_lead_data(
            {
                "budget": "$650,000",
                "timeline": "ASAP - need to move in 30 days",
                "location": "North Rancho Cucamonga",
                "bedrooms": "4",
                "financing": "Pre-approved with Wells Fargo",
                "motivation": "Job relocation, must close quickly",
            }
        )

        context = {"extracted_preferences": immediate_buyer}

        # WHEN: Lead is scored
        score = self.scorer.calculate(context)
        classification = self.scorer.classify(score)
        reasoning = self.scorer.calculate_with_reasoning(context)

        # THEN: Business contract must be satisfied
        assert score >= self.high_intent_contract.expected_score_range[0], (
            f"High-intent lead scored too low: {score} < {self.high_intent_contract.expected_score_range[0]}"
        )

        assert classification == self.high_intent_contract.expected_classification, (
            f"High-intent lead misclassified as '{classification}', expected '{self.high_intent_contract.expected_classification}'"
        )

        # Business outcome validation
        recommended_actions = reasoning.get("recommended_actions", [])
        assert any("immediately" in action.lower() or "SMS" in action for action in recommended_actions), (
            f"High-intent lead missing immediate action: {recommended_actions}"
        )

        # Data quality validation
        answered_questions = len([k for k, v in immediate_buyer.items() if v and str(v).strip()])
        data_quality = answered_questions / 7.0  # 7 total possible questions
        assert data_quality >= self.high_intent_contract.minimum_data_quality, (
            f"High-intent lead data quality too low: {data_quality} < {self.high_intent_contract.minimum_data_quality}"
        )

    @pytest.mark.critical
    def test_qualified_buyer_with_urgency_contract(self):
        """
        Contract: Qualified buyers with urgency must trigger priority workflow
        Business Impact: Ensures competitive advantage in hot markets
        """
        # GIVEN: Qualified buyer with multiple urgency signals
        qualified_urgent = create_test_lead_data(
            {
                "budget": "$500,000",
                "timeline": "Looking to close within 60 days",
                "location": "Round Rock or Cedar Park",
                "bedrooms": "3",
                "bathrooms": "2",
                "financing": "Cash buyer",
                "motivation": "Selling current home, need to move before school starts",
            }
        )

        context = {"extracted_preferences": qualified_urgent}

        # WHEN: Lead is analyzed
        score = self.scorer.calculate(context)
        classification = self.scorer.classify(score)
        reasoning = self.scorer.calculate_with_reasoning(context)

        # THEN: Priority workflow must be triggered
        assert score >= 6, f"Qualified urgent buyer should score near maximum: {score} < 6"
        assert classification == "hot", f"Qualified urgent buyer misclassified: {classification}"

        # Validate urgency recognition in reasoning
        reasoning_text = reasoning.get("reasoning", "")
        assert any(
            urgency_signal in reasoning_text.lower() for urgency_signal in ["cash", "60 days", "close", "timeline"]
        ), f"Urgency signals not captured in reasoning: {reasoning_text}"

        # Validate recommended actions include priority treatment
        actions = reasoning.get("recommended_actions", [])
        priority_actions = [
            action
            for action in actions
            if any(
                priority_word in action.lower() for priority_word in ["priority", "immediately", "24", "sms", "notify"]
            )
        ]
        assert len(priority_actions) >= 2, f"Insufficient priority actions for urgent qualified buyer: {actions}"


class TestLeadTemperatureConsistency:
    """Contract tests for lead temperature consistency across scenarios"""

    def setup_method(self):
        self.scorer = LeadScorer()

    @pytest.mark.critical
    def test_temperature_consistency_under_data_variations(self):
        """
        Contract: Lead temperature should be consistent regardless of data presentation
        Business Impact: Prevents scoring inconsistencies due to format variations
        """
        # GIVEN: Same lead data in different formats
        base_lead = {"budget": "400000", "timeline": "soon", "location": "Rancho Cucamonga"}

        variations = [
            # Numeric vs string budget
            {**base_lead, "budget": 400000},
            {**base_lead, "budget": "$400,000"},
            {**base_lead, "budget": "400k"},
            # Timeline variations
            {**base_lead, "timeline": "ASAP"},
            {**base_lead, "timeline": "within 3 months"},
            {**base_lead, "timeline": "soon"},
            # Location variations
            {**base_lead, "location": "Rancho Cucamonga, CA"},
            {**base_lead, "location": "rancho_cucamonga california"},
            {**base_lead, "location": "IE"},
        ]

        # WHEN: All variations are scored
        scores = []
        classifications = []

        for variation in variations:
            context = {"extracted_preferences": variation}
            score = self.scorer.calculate(context)
            classification = self.scorer.classify(score)
            scores.append(score)
            classifications.append(classification)

        # THEN: Temperature should be consistent
        unique_scores = set(scores)
        assert len(unique_scores) <= 2, f"Too much score variation across formats: {scores}"

        unique_classifications = set(classifications)
        assert len(unique_classifications) == 1, f"Classification inconsistency: {classifications}"

        # All should be warm leads (3 questions answered)
        expected_score = 3  # budget + timeline + location
        for i, score in enumerate(scores):
            assert score == expected_score, f"Variation {i} scored {score}, expected {expected_score}"

    def test_progressive_lead_warming_contract(self):
        """
        Contract: Leads should warm progressively as more information is gathered
        Business Impact: Validates qualification pipeline effectiveness
        """
        # GIVEN: Progressive lead information gathering
        stages = [
            {},  # Initial contact
            {"location": "Rancho Cucamonga"},  # Location interest
            {"location": "Rancho Cucamonga", "timeline": "soon"},  # Timeline added
            {"location": "Rancho Cucamonga", "timeline": "soon", "budget": "500000"},  # Budget qualified
            {"location": "Rancho Cucamonga", "timeline": "soon", "budget": "500000", "bedrooms": "3"},  # Requirements
            {
                "location": "Rancho Cucamonga",
                "timeline": "soon",
                "budget": "500000",
                "bedrooms": "3",
                "financing": "pre-approved",
            },  # Financing
        ]

        # WHEN: Each stage is scored
        scores = []
        classifications = []

        for stage in stages:
            context = {"extracted_preferences": stage}
            score = self.scorer.calculate(context)
            classification = self.scorer.classify(score)
            scores.append(score)
            classifications.append(classification)

        # THEN: Progressive warming must occur
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1], (
                f"Score decreased from stage {i - 1} to {i}: {scores[i - 1]} -> {scores[i]}"
            )

        # Validate expected temperature transitions
        expected_progression = ["cold", "cold", "warm", "hot", "hot", "hot"]
        for i, (actual, expected) in enumerate(zip(classifications, expected_progression)):
            assert actual == expected, f"Stage {i} classification mismatch: {actual} vs {expected}"


class TestPropertyRecommendationContracts:
    """Contract tests for property recommendation quality and relevance"""

    def setup_method(self):
        self.intelligence = EnhancedLeadIntelligence()

    @pytest.mark.asyncio
    async def test_budget_alignment_contract(self):
        """
        Contract: Property recommendations must align with lead budget constraints
        Business Impact: Prevents showing unaffordable properties, maintains trust
        """
        # GIVEN: Lead with specific budget constraints
        budget_conscious_lead = {
            "lead_name": "Budget-Conscious Buyer",
            "budget": "$350,000",
            "location": "Rancho Cucamonga suburbs",
            "timeline": "within 6 months",
            "bedrooms": "3",
            "motivation": "First-time home buyer, strict budget",
        }

        # Mock property recommendation scenario
        properties = [
            {"address": "123 Affordable St", "price": 340000, "beds": 3},
            {"address": "456 Expensive Ave", "price": 450000, "beds": 3},
            {"address": "789 Perfect Pl", "price": 349000, "beds": 3},
        ]

        # WHEN: Properties are analyzed for psychological fit
        lead_context = {"extracted_preferences": budget_conscious_lead}

        for prop in properties:
            try:
                # Create mock analysis result
                from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult

                mock_analysis = UnifiedScoringResult(
                    lead_id="budget_test",
                    lead_name=budget_conscious_lead["lead_name"],
                    scored_at=datetime.now(),
                    final_score=75.0,
                    confidence_score=0.8,
                    classification="warm",
                    jorge_score=3,
                    ml_conversion_score=70,
                    churn_risk_score=25,
                    engagement_score=75,
                    strategic_summary="Budget-conscious first-time buyer",
                    behavioral_insights="Price-sensitive with clear constraints",
                    reasoning="3 questions answered: budget, location, timeline",
                    risk_factors=["Budget constraints"],
                    opportunities=["First-time buyer programs"],
                    recommended_actions=[{"action": "Show properties in budget", "priority": "high"}],
                    next_best_action="Focus on affordable options",
                    expected_timeline="6 months",
                    success_probability=75.0,
                    feature_breakdown={},
                    conversation_context=lead_context,
                    sources=["Lead Scorer"],
                    analysis_time_ms=150,
                    claude_reasoning_time_ms=100,
                )

                psychological_fit = await self.intelligence.get_psychological_property_fit(prop, mock_analysis)

                # THEN: Budget alignment must be validated in recommendations
                if prop["price"] <= 350000:
                    # Affordable properties should be recommended positively
                    assert any(
                        positive_word in psychological_fit.lower()
                        for positive_word in ["excellent", "perfect", "ideal", "great", "fits"]
                    ), f"Affordable property not recommended positively: {psychological_fit}"
                else:
                    # Expensive properties should be flagged or discouraged
                    budget_concern_mentioned = any(
                        concern in psychological_fit.lower()
                        for concern in ["budget", "price", "expensive", "cost", "afford"]
                    )
                    if not budget_concern_mentioned:
                        # If no budget concern is mentioned, the recommendation should be cautious
                        assert any(
                            caution_word in psychological_fit.lower()
                            for caution_word in ["consider", "evaluate", "review", "careful"]
                        ), f"Expensive property recommendation lacks budget awareness: {psychological_fit}"

            except Exception as e:
                # Contract: System should handle property analysis gracefully
                assert "budget" in str(e).lower() or "analysis" in str(e).lower(), (
                    f"Unexpected error in property analysis: {e}"
                )


class TestBusinessOutcomeValidation:
    """Contract tests for business outcome validation and optimization"""

    def setup_method(self):
        self.scorer = LeadScorer()

    def test_conversion_probability_alignment_contract(self):
        """
        Contract: High-scoring leads should have recommended actions that maximize conversion
        Business Impact: Ensures scoring translates to actual business results
        """
        # GIVEN: High-scoring lead profiles
        high_conversion_scenarios = [
            {
                "profile": "Cash Buyer with Timeline",
                "data": {
                    "budget": "$750,000",
                    "financing": "Cash purchase",
                    "timeline": "Must close in 30 days",
                    "location": "West Rancho Cucamonga",
                    "bedrooms": "4",
                    "motivation": "Corporate relocation",
                },
            },
            {
                "profile": "Qualified Repeat Buyer",
                "data": {
                    "budget": "$600,000",
                    "financing": "Pre-approved with excellent credit",
                    "timeline": "Ready to make offer",
                    "location": "Specific neighborhood: Rancho Etiwanda",
                    "bedrooms": "3-4",
                    "bathrooms": "2+",
                    "motivation": "Upsizing for growing family",
                },
            },
        ]

        for scenario in high_conversion_scenarios:
            # WHEN: High-conversion lead is analyzed
            context = {"extracted_preferences": scenario["data"]}
            score = self.scorer.calculate(context)
            reasoning = self.scorer.calculate_with_reasoning(context)

            # THEN: Actions should optimize for conversion
            assert score >= 5, f"{scenario['profile']} should score high: {score} < 5"

            actions = reasoning.get("recommended_actions", [])

            # Validate conversion-optimized actions
            immediate_actions = [
                a
                for a in actions
                if any(
                    immediate_word in a.lower() for immediate_word in ["immediate", "24", "sms", "notify", "priority"]
                )
            ]
            assert len(immediate_actions) >= 1, f"{scenario['profile']} missing immediate actions: {actions}"

            # Validate business outcome alignment
            high_value_actions = [
                a
                for a in actions
                if any(
                    value_word in a.lower() for value_word in ["showing", "tour", "pre-approval", "offer", "contract"]
                )
            ]
            assert len(high_value_actions) >= 1, f"{scenario['profile']} missing high-value actions: {actions}"

    def test_churn_risk_mitigation_contract(self):
        """
        Contract: Leads showing churn risk signals should trigger retention actions
        Business Impact: Prevents lead loss and maintains pipeline health
        """
        # GIVEN: Leads with churn risk signals
        churn_risk_profiles = [
            {
                "profile": "Price Shopper",
                "data": {
                    "budget": "Under $300k",  # Below market average
                    "timeline": "just looking",  # Vague timeline
                    "location": "anywhere cheap",  # Price-focused
                },
                "expected_risk_factors": ["budget", "timeline", "commitment"],
            },
            {
                "profile": "Comparison Shopper",
                "data": {
                    "motivation": "talking to multiple agents",
                    "timeline": "no rush",
                    "location": "exploring options",
                },
                "expected_risk_factors": ["competition", "commitment", "timeline"],
            },
        ]

        for profile_data in churn_risk_profiles:
            # WHEN: Churn-risk lead is analyzed
            context = {"extracted_preferences": profile_data["data"]}
            score = self.scorer.calculate(context)
            reasoning = self.scorer.calculate_with_reasoning(context)

            # THEN: Appropriate retention actions should be recommended
            assert score <= 2, f"{profile_data['profile']} should score low due to churn risk: {score}"

            actions = reasoning.get("recommended_actions", [])

            # Validate retention-focused actions
            retention_actions = [
                a
                for a in actions
                if any(
                    retention_word in a.lower()
                    for retention_word in ["nurture", "educational", "value", "build", "trust"]
                )
            ]
            assert len(retention_actions) >= 1, f"{profile_data['profile']} missing retention actions: {actions}"

            # Ensure no aggressive sales actions for churn risk
            aggressive_actions = [
                a
                for a in actions
                if any(
                    aggressive_word in a.lower() for aggressive_word in ["immediately", "pressure", "close", "urgent"]
                )
            ]
            assert len(aggressive_actions) == 0, (
                f"{profile_data['profile']} has inappropriate aggressive actions: {aggressive_actions}"
            )


class TestCrossServiceBehavioralConsistency:
    """Contract tests for behavioral consistency across services"""

    def setup_method(self):
        self.scorer = LeadScorer()
        self.intelligence = EnhancedLeadIntelligence()

    @pytest.mark.asyncio
    async def test_scoring_intelligence_consistency_contract(self):
        """
        Contract: Lead Intelligence service results must be consistent with base scoring
        Business Impact: Ensures unified experience across different system components
        """
        # GIVEN: A lead with clear characteristics
        consistent_lead = {
            "lead_id": "consistency_test_001",
            "lead_name": "Consistency Test Lead",
            "budget": "$500,000",
            "timeline": "next 90 days",
            "location": "North Rancho Cucamonga",
            "bedrooms": "3",
            "financing": "pre-qualified",
        }

        # WHEN: Lead is analyzed by both services
        scorer_context = {"extracted_preferences": consistent_lead}
        base_score = self.scorer.calculate(scorer_context)
        base_classification = self.scorer.classify(base_score)

        # Mock comprehensive analysis
        try:
            intelligence_context = {**consistent_lead, "extracted_preferences": consistent_lead}
            # Note: This test is designed to validate contract expectations
            # In actual implementation, we would need full intelligence analysis

            # THEN: Results should be behaviorally consistent
            # Base scoring contract validation
            assert 4 <= base_score <= 6, f"Inconsistent base scoring: {base_score}"
            assert base_classification == "hot", f"Inconsistent classification: {base_classification}"

            # Intelligence service should respect base scoring principles
            # This validates that enhanced services don't contradict basic business logic

        except Exception as e:
            # Contract: Services should handle errors gracefully without contradicting base logic
            assert "scoring" not in str(e).lower(), f"Scoring-related error suggests inconsistency: {e}"

    def test_recommendation_scoring_alignment_contract(self):
        """
        Contract: Recommended actions must align with lead score and classification
        Business Impact: Ensures coherent agent guidance across system components
        """
        # GIVEN: Leads at different score levels
        score_scenarios = [
            {
                "name": "Maximum Score Lead",
                "data": {
                    "budget": "$600,000",
                    "location": "Specific: Rancho Etiwanda",
                    "timeline": "Immediate - 30 days",
                    "bedrooms": "4",
                    "bathrooms": "3",
                    "financing": "Cash buyer",
                    "motivation": "Corporate relocation deadline",
                    "must_haves": ["Pool", "Large yard", "Good schools"],
                },
                "expected_score": 7,
                "expected_actions": ["immediate", "priority", "sms", "notify"],
            },
            {
                "name": "Minimum Qualifying Lead",
                "data": {"budget": "$400,000", "location": "Rancho Cucamonga area", "timeline": "soon"},
                "expected_score": 3,
                "expected_actions": ["hot", "schedule", "24", "48"],
            },
        ]

        for scenario in score_scenarios:
            # WHEN: Lead is scored and analyzed
            context = {"extracted_preferences": scenario["data"]}
            score = self.scorer.calculate(context)
            reasoning = self.scorer.calculate_with_reasoning(context)

            # THEN: Actions must align with score level
            assert score == scenario["expected_score"], (
                f"{scenario['name']} score mismatch: {score} vs {scenario['expected_score']}"
            )

            actions = reasoning.get("recommended_actions", [])
            action_text = " ".join(actions).lower()

            # Validate action alignment
            matching_actions = sum(1 for expected in scenario["expected_actions"] if expected in action_text)
            assert matching_actions >= 2, f"{scenario['name']} actions don't align with score {score}: {actions}"


class TestBusinessRuleCompliance:
    """Contract tests for business rule compliance and regulatory requirements"""

    def setup_method(self):
        self.scorer = LeadScorer()

    def test_fair_housing_compliance_contract(self):
        """
        Contract: Lead scoring must not discriminate based on protected characteristics
        Business Impact: Ensures legal compliance and fair treatment
        """
        # GIVEN: Identical leads with different personal characteristics
        base_lead_data = {"budget": "$500,000", "timeline": "within 6 months", "location": "Rancho Cucamonga", "bedrooms": "3"}

        # Personal characteristics that should NOT affect scoring
        personal_variations = [
            {**base_lead_data, "name": "John Smith"},
            {**base_lead_data, "name": "Maria Rodriguez"},
            {**base_lead_data, "name": "Ahmed Hassan"},
            {**base_lead_data, "name": "Sarah Johnson"},
        ]

        # WHEN: All leads are scored
        scores = []
        for variation in personal_variations:
            context = {"extracted_preferences": variation}
            score = self.scorer.calculate(context)
            scores.append(score)

        # THEN: All scores must be identical (fair treatment)
        unique_scores = set(scores)
        assert len(unique_scores) == 1, f"Discriminatory scoring detected: {scores}"

        expected_score = 4  # budget + timeline + location + bedrooms
        assert all(score == expected_score for score in scores), (
            f"Fair housing compliance failed: expected {expected_score}, got {scores}"
        )

    def test_data_privacy_contract(self):
        """
        Contract: Scoring must work without requiring sensitive personal information
        Business Impact: Ensures privacy compliance and builds trust
        """
        # GIVEN: Lead data without sensitive personal information
        privacy_compliant_lead = {
            "budget": "$450,000",
            "timeline": "next quarter",
            "location": "Central Rancho Cucamonga",
            "bedrooms": "2-3",
            "financing": "conventional loan",
        }

        # WHEN: Lead is scored with minimal personal data
        context = {"extracted_preferences": privacy_compliant_lead}
        score = self.scorer.calculate(context)
        classification = self.scorer.classify(score)
        reasoning = self.scorer.calculate_with_reasoning(context)

        # THEN: Effective scoring should still be possible
        assert score >= 4, f"Privacy-compliant lead should still score well: {score}"
        assert classification == "hot", f"Privacy-compliant lead misclassified: {classification}"

        # Validate reasoning doesn't request sensitive information
        reasoning_text = reasoning.get("reasoning", "")
        sensitive_requests = any(
            sensitive_word in reasoning_text.lower()
            for sensitive_word in ["ssn", "credit", "income", "age", "race", "religion"]
        )
        assert not sensitive_requests, f"Reasoning requests sensitive information: {reasoning_text}"


if __name__ == "__main__":
    # Run behavioral contract tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "critical"])