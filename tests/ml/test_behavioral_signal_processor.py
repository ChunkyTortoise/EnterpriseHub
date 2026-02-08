#!/usr/bin/env python3
"""
Tests for Behavioral Signal Processor

Comprehensive test suite for 50+ behavioral signal extraction.

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

from unittest.mock import Mock, patch

import pytest

from ghl_real_estate_ai.ml.behavioral_signal_processor import (
    BehavioralSignal,
    BehavioralSignalProcessor,
    EngagementPattern,
    SignalCategory,
)


class TestBehavioralSignalProcessor:
    """Test behavioral signal extraction functionality"""

    @pytest.fixture
    def processor(self):
        """Create processor instance for testing"""
        return BehavioralSignalProcessor()

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing"""
        return {
            "email_opens": 10,
            "email_clicks": 6,
            "emails_sent": 12,
            "page_views": 25,
            "session_duration_minutes": 35,
            "budget": 600000,
            "viewed_property_prices": [580000, 620000, 650000],
            "timeline": "immediate",
            "property_matches": 8,
            "source": "organic",
            "days_since_first_contact": 5,
            "unique_sessions": 7,
            "search_terms": ["Austin homes", "tech corridor properties", "home office space"],
        }

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing"""
        return [
            {
                "text": "Hi, I'm looking for a house in Austin with a good home office setup",
                "timestamp": "2026-01-15T10:00:00Z",
                "sender": "lead",
                "response_time_seconds": 1800,
            },
            {
                "text": "I'm pre-approved for $600K and work as a software engineer at Apple. Need to move ASAP for relocation.",
                "timestamp": "2026-01-15T10:30:00Z",
                "sender": "lead",
                "response_time_seconds": 900,
            },
            {
                "text": "Cash buyer option available if we find the right property quickly. When can we schedule viewings?",
                "timestamp": "2026-01-15T11:00:00Z",
                "sender": "lead",
                "response_time_seconds": 600,
            },
            {
                "text": "Also need fiber internet for remote work days. What areas have the best connectivity?",
                "timestamp": "2026-01-15T11:30:00Z",
                "sender": "lead",
                "response_time_seconds": 3600,
            },
        ]

    def test_processor_initialization(self, processor):
        """Test processor initialization"""
        assert processor is not None
        assert len(processor.signal_weights) > 0
        assert len(processor.financial_keywords) > 0
        assert len(processor.urgency_keywords) > 0

    def test_signal_extraction_comprehensive(self, processor, sample_lead_data, sample_conversation_history):
        """Test comprehensive signal extraction returns 50+ signals"""
        signals = processor.extract_signals(sample_lead_data, sample_conversation_history)

        # Should extract 50+ signals
        assert len(signals) >= 50

        # All signals should be normalized (0-1)
        for signal_name, signal_value in signals.items():
            assert 0 <= signal_value <= 1, f"Signal {signal_name} value {signal_value} not normalized"
            assert isinstance(signal_value, (int, float))

        # Should include major categories
        engagement_signals = [k for k in signals.keys() if "engagement" in k or "response" in k]
        financial_signals = [k for k in signals.keys() if "financial" in k or "cash" in k or "preapproval" in k]
        urgency_signals = [k for k in signals.keys() if "urgent" in k or "timeline" in k]

        assert len(engagement_signals) >= 3
        assert len(financial_signals) >= 3
        assert len(urgency_signals) >= 3

    def test_engagement_signal_extraction(self, processor, sample_lead_data, sample_conversation_history):
        """Test engagement signal extraction"""
        signals = processor._extract_engagement_signals(sample_lead_data, sample_conversation_history)

        # Email engagement
        assert "email_open_rate" in signals
        assert "email_click_rate" in signals
        expected_open_rate = 10 / 12  # opens / sent
        expected_click_rate = 6 / 12  # clicks / sent
        assert abs(signals["email_open_rate"] - expected_open_rate) < 0.1
        assert abs(signals["email_click_rate"] - expected_click_rate) < 0.1

        # Response velocity (should be good - decreasing response times)
        assert "response_velocity" in signals
        assert signals["response_velocity"] > 0.5  # Should detect good response pattern

        # Conversation frequency
        assert "conversation_frequency" in signals

        # Question frequency (sample has questions)
        assert "question_frequency" in signals
        assert signals["question_frequency"] > 0  # Should detect questions

        # Weekend engagement
        assert "weekend_engagement" in signals

    def test_financial_signal_extraction(self, processor, sample_lead_data, sample_conversation_history):
        """Test financial readiness signal extraction"""
        signals = processor._extract_financial_signals(sample_lead_data, sample_conversation_history)

        # Pre-approval mentions (should be detected)
        assert "preapproval_mentions" in signals
        assert signals["preapproval_mentions"] == 1.0  # "pre-approved" mentioned

        # Cash buyer indicators (should be detected)
        assert "cash_buyer_indicators" in signals
        assert signals["cash_buyer_indicators"] == 1.0  # "cash buyer" mentioned

        # Budget specificity
        assert "budget_specificity" in signals
        assert signals["budget_specificity"] > 0  # $600K mentioned

        # Down payment readiness
        assert "down_payment_readiness" in signals

        # Credit awareness
        assert "credit_awareness" in signals

        # Lender relationships
        assert "lender_relationships" in signals

    def test_urgency_signal_extraction(self, processor, sample_lead_data, sample_conversation_history):
        """Test urgency and timeline signal extraction"""
        signals = processor._extract_urgency_signals(sample_lead_data, sample_conversation_history)

        # Immediate timeline (should be detected)
        assert "immediate_timeline" in signals
        assert signals["immediate_timeline"] == 1.0  # "ASAP" mentioned

        # Relocation pressure (should be detected)
        assert "relocation_pressure" in signals
        assert signals["relocation_pressure"] == 1.0  # "relocation" mentioned

        # Market timing concern
        assert "market_timing_concern" in signals

        # Life event drivers
        assert "life_event_drivers" in signals

        # Viewing urgency (should be detected)
        assert "viewing_urgency" in signals
        assert signals["viewing_urgency"] == 1.0  # "schedule viewings" mentioned

    def test_objection_signal_extraction(self, processor, sample_conversation_history):
        """Test objection pattern detection"""
        # Add objection-heavy conversation
        objection_conversation = [
            {"text": "The price seems too expensive for what we're getting"},
            {"text": "The area is too far from work, commute would be terrible"},
            {"text": "House needs too much work and updating"},
            {"text": "Market seems overheated, maybe we should wait"},
        ]

        signals = processor._extract_objection_signals(objection_conversation)

        # Price objections
        assert "price_objections" in signals
        assert signals["price_objections"] == 1.0

        # Location concerns
        assert "location_concerns" in signals
        assert signals["location_concerns"] == 1.0

        # Condition concerns
        assert "condition_concerns" in signals
        assert signals["condition_concerns"] == 1.0

        # Market concerns
        assert "market_concerns" in signals
        assert signals["market_concerns"] == 1.0

    def test_communication_signal_extraction(self, processor, sample_conversation_history):
        """Test communication style analysis"""
        signals = processor._extract_communication_signals(sample_conversation_history)

        # Communication preference (text vs call)
        assert "prefers_text_communication" in signals

        # Formality level
        assert "formal_communication_style" in signals

        # Detail orientation (should be high - detailed messages)
        assert "detail_oriented" in signals
        assert signals["detail_oriented"] > 0.5  # Detailed questions about internet, etc.

        # Technical language usage (should be detected - tech terms used)
        assert "technical_language_usage" in signals
        assert signals["technical_language_usage"] > 0

        # Emotional language
        assert "emotional_language" in signals

    def test_decision_stage_signal_extraction(self, processor, sample_conversation_history):
        """Test decision-making stage detection"""
        signals = processor._extract_decision_stage_signals(sample_conversation_history)

        # Purchase intent (should be high - ready to schedule viewings)
        assert "purchase_intent" in signals
        assert signals["purchase_intent"] == 1.0  # "schedule viewings" indicates intent

        # Research stage
        assert "in_research_stage" in signals

        # Evaluation stage
        assert "in_evaluation_stage" in signals

        # Comparison shopping
        assert "comparison_shopping" in signals

        # Commitment signals
        assert "commitment_signals" in signals

    def test_lifestyle_signal_extraction(self, processor, sample_lead_data, sample_conversation_history):
        """Test lifestyle and demographic signal extraction"""
        signals = processor._extract_lifestyle_signals(sample_lead_data, sample_conversation_history)

        # Professional focus (should be high - software engineer mentioned)
        assert "professional_focus" in signals
        assert signals["professional_focus"] == 1.0

        # Family oriented
        assert "family_oriented" in signals

        # Investment mindset
        assert "investment_mindset" in signals

        # Luxury preferences
        assert "luxury_preferences" in signals

        # First-time buyer
        assert "first_time_buyer" in signals

        # Relocating (should be detected)
        assert "relocating" in signals

    def test_technical_signal_extraction(self, processor, sample_lead_data, sample_conversation_history):
        """Test technical and data-driven signal extraction"""
        signals = processor._extract_technical_signals(sample_lead_data, sample_conversation_history)

        # Digital engagement
        assert "digital_engagement" in signals
        expected_engagement = min(25 / 20.0, 1.0)  # page_views / 20
        assert abs(signals["digital_engagement"] - expected_engagement) < 0.1

        # Deep research
        assert "deep_research" in signals
        expected_research = min(35 / 30.0, 1.0)  # session_duration / 30
        assert abs(signals["deep_research"] - expected_research) < 0.1

        # Property view velocity
        assert "property_view_velocity" in signals

        # Search specificity
        assert "search_specificity" in signals
        # Should be high - search terms have multiple words
        assert signals["search_specificity"] > 0.8

        # Persistent interest
        assert "persistent_interest" in signals

        # Source quality
        assert "source_quality" in signals
        assert signals["source_quality"] == 0.9  # organic source

    def test_signal_normalization(self, processor):
        """Test signal normalization functionality"""
        test_signals = {
            "valid_signal": 0.75,
            "over_range": 1.5,  # Should be clamped to 1.0
            "under_range": -0.2,  # Should be clamped to 0.0
            "none_value": None,  # Should become 0.0
            "bool_true": True,  # Should become 1.0
            "bool_false": False,  # Should become 0.0
            "string_value": "invalid",  # Should become 0.0
        }

        normalized = processor._normalize_signals(test_signals)

        assert normalized["valid_signal"] == 0.75
        assert normalized["over_range"] == 1.0
        assert normalized["under_range"] == 0.0
        assert normalized["none_value"] == 0.0
        assert normalized["bool_true"] == 1.0
        assert normalized["bool_false"] == 0.0
        assert normalized["string_value"] == 0.0

    def test_default_signals(self, processor):
        """Test default signal values when extraction fails"""
        defaults = processor._get_default_signals()

        # Should have 50+ default signals
        assert len(defaults) >= 50

        # All defaults should be normalized
        for signal_name, signal_value in defaults.items():
            assert 0 <= signal_value <= 1
            assert isinstance(signal_value, (int, float))

    def test_signal_summary_generation(self, processor, sample_lead_data, sample_conversation_history):
        """Test signal summary generation"""
        signals = processor.extract_signals(sample_lead_data, sample_conversation_history)
        summary = processor.get_signal_summary(signals)

        # Should have category summaries
        expected_categories = ["engagement", "financial", "urgency", "technical"]
        for category in expected_categories:
            assert f"{category}_avg" in summary
            assert f"{category}_max" in summary
            assert f"{category}_count" in summary

        # Should have overall metrics
        assert "overall_signal_strength" in summary
        assert "strong_signals" in summary
        assert "weak_signals" in summary

        # Values should be reasonable
        assert 0 <= summary["overall_signal_strength"] <= 1
        assert summary["strong_signals"] >= 0
        assert summary["weak_signals"] >= 0

    def test_error_handling(self, processor):
        """Test error handling with invalid inputs"""
        # Empty inputs should not crash
        signals = processor.extract_signals({}, [])
        assert isinstance(signals, dict)
        assert len(signals) > 0  # Should return defaults

        # Invalid conversation history
        signals = processor.extract_signals({"budget": 500000}, [{"invalid": "data"}])
        assert isinstance(signals, dict)

    def test_performance_with_large_conversation(self, processor):
        """Test performance with large conversation history"""
        import time

        # Create large conversation history
        large_conversation = []
        for i in range(100):
            large_conversation.append(
                {
                    "text": f"Message {i} with various content about real estate and buying homes",
                    "timestamp": f"2026-01-15T{10 + i % 14:02d}:00:00Z",
                }
            )

        lead_data = {"budget": 500000, "email_opens": 5, "emails_sent": 10}

        start_time = time.time()
        signals = processor.extract_signals(lead_data, large_conversation)
        processing_time = time.time() - start_time

        # Should complete reasonably quickly (< 1 second)
        assert processing_time < 1.0
        assert len(signals) >= 50

    def test_keyword_matching_accuracy(self, processor):
        """Test accuracy of keyword-based signal detection"""
        # Test financial keywords
        conversation_with_financial = [
            {"text": "I am pre-approved for a mortgage and have excellent credit score"},
            {"text": "Cash buyer with 20% down payment ready"},
        ]

        financial_signals = processor._extract_financial_signals({}, conversation_with_financial)

        assert financial_signals["preapproval_mentions"] == 1.0
        assert financial_signals["cash_buyer_indicators"] == 1.0
        assert financial_signals["credit_awareness"] == 1.0
        assert financial_signals["down_payment_readiness"] == 1.0

        # Test urgency keywords
        conversation_with_urgency = [
            {"text": "Need to buy ASAP, relocating for work next month"},
            {"text": "Urgent timeline, lease expires in 2 weeks"},
        ]

        urgency_signals = processor._extract_urgency_signals({}, conversation_with_urgency)

        assert urgency_signals["immediate_timeline"] == 1.0
        assert urgency_signals["relocation_pressure"] == 1.0

    def test_signal_consistency(self, processor, sample_lead_data, sample_conversation_history):
        """Test that signal extraction is consistent across multiple runs"""
        signals1 = processor.extract_signals(sample_lead_data, sample_conversation_history)
        signals2 = processor.extract_signals(sample_lead_data, sample_conversation_history)

        # Results should be identical
        for signal_name in signals1:
            assert signal_name in signals2
            assert abs(signals1[signal_name] - signals2[signal_name]) < 0.001

    def test_edge_cases(self, processor):
        """Test edge cases and boundary conditions"""
        # Very short conversation
        short_conversation = [{"text": "Hi"}]
        signals = processor.extract_signals({"budget": 100000}, short_conversation)
        assert len(signals) >= 50  # Should still extract defaults

        # Very high budget
        high_budget_data = {"budget": 5000000, "email_opens": 100, "emails_sent": 10}
        signals = processor.extract_signals(high_budget_data, [])
        assert signals["source_quality"] >= 0  # Should handle gracefully

        # Missing common fields
        minimal_data = {"budget": 0}
        signals = processor.extract_signals(minimal_data, [])
        assert isinstance(signals, dict)
        assert len(signals) >= 50
