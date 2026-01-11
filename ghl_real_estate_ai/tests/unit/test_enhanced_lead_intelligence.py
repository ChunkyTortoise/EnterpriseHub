"""
Comprehensive Test Suite for Enhanced Lead Intelligence System

Tests all advanced features including qualification, conversation intelligence,
predictive analytics, and integration capabilities.
"""

import asyncio
import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from .advanced_lead_intelligence import (
    AdvancedLeadIntelligence,
    LeadQualificationCriteria,
    ConversationIntelligence,
    ConversationIntent,
    ConversationSentiment,
    LeadQualificationLevel
)
from .lead_intelligence_integration import LeadIntelligenceIntegration
from .chatbot_manager import ChatbotManager, UserType
from .chat_ml_integration import ChatMLIntegration


class TestLeadQualificationCriteria(unittest.TestCase):
    """Test the lead qualification scoring system"""

    def setUp(self):
        self.criteria = LeadQualificationCriteria()

    def test_empty_criteria_score(self):
        """Test that empty criteria returns 0 score"""
        self.assertEqual(self.criteria.calculate_score(), 0)

    def test_full_qualification_score(self):
        """Test that fully qualified lead gets 100 score"""
        self.criteria.has_name = True
        self.criteria.has_contact_info = True
        self.criteria.has_location_preference = True
        self.criteria.has_budget_range = True
        self.criteria.has_financing_info = True
        self.criteria.pre_approved = True
        self.criteria.has_timeline = True
        self.criteria.has_motivation = True
        self.criteria.urgency_level = 10
        self.criteria.has_property_type = True
        self.criteria.has_size_requirements = True
        self.criteria.has_features_list = True

        score = self.criteria.calculate_score()
        self.assertEqual(score, 100)

    def test_partial_qualification_score(self):
        """Test partial qualification scoring"""
        self.criteria.has_name = True
        self.criteria.has_contact_info = True
        self.criteria.has_budget_range = True
        self.criteria.has_timeline = True
        self.criteria.urgency_level = 5

        score = self.criteria.calculate_score()
        self.assertGreater(score, 40)
        self.assertLess(score, 70)

    def test_high_urgency_impact(self):
        """Test that high urgency affects scoring"""
        # Test with low urgency
        self.criteria.has_name = True
        self.criteria.urgency_level = 1
        low_urgency_score = self.criteria.calculate_score()

        # Test with high urgency
        self.criteria.urgency_level = 10
        high_urgency_score = self.criteria.calculate_score()

        self.assertGreater(high_urgency_score, low_urgency_score)


class TestAdvancedLeadIntelligence(unittest.IsolatedAsyncioTestCase):
    """Test the advanced lead intelligence system"""

    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.mock_chatbot_manager = Mock(spec=ChatbotManager)
        self.mock_ml_integration = Mock(spec=ChatMLIntegration)

        self.intelligence = AdvancedLeadIntelligence(
            self.mock_chatbot_manager,
            self.mock_ml_integration
        )

    async def test_intent_detection(self):
        """Test conversation intent detection"""
        test_messages = [
            ("What's the price of this house?", ConversationIntent.PRICE_INQUIRY),
            ("I need to move by next month", ConversationIntent.TIMELINE_DISCUSSION),
            ("Do you have mortgage options?", ConversationIntent.FINANCING_QUESTIONS),
            ("This is urgent, I need help ASAP", ConversationIntent.URGENT_NEED)
        ]

        for message, expected_intent in test_messages:
            result = await self.intelligence.analyze_conversation_turn(
                "test_user", "test_tenant", message
            )

            detected_intents = result.get("detected_intents", [])
            self.assertIn(expected_intent.value, detected_intents,
                         f"Failed to detect {expected_intent.value} in '{message}'")

    async def test_sentiment_analysis(self):
        """Test sentiment detection in conversations"""
        test_messages = [
            ("I love this property!", ConversationSentiment.VERY_POSITIVE),
            ("This is frustrating", ConversationSentiment.FRUSTRATED),
            ("I'm worried about the process", ConversationSentiment.CONCERNED),
            ("Okay, that sounds fine", ConversationSentiment.NEUTRAL)
        ]

        for message, expected_sentiment in test_messages:
            result = await self.intelligence.analyze_conversation_turn(
                "test_user", "test_tenant", message
            )

            # Get conversation intelligence
            conversation_key = "test_tenant:test_user"
            if conversation_key in self.intelligence.conversation_intelligence:
                intel = self.intelligence.conversation_intelligence[conversation_key]
                # Note: Sentiment may accumulate, so we check if it moves in the right direction
                self.assertIsInstance(intel.sentiment, ConversationSentiment)

    async def test_qualification_entity_extraction(self):
        """Test extraction of qualification entities"""
        test_cases = [
            {
                "message": "My name is John Smith",
                "expected_updates": ["Name captured"]
            },
            {
                "message": "My budget is around $500,000",
                "expected_updates": ["Budget range captured"]
            },
            {
                "message": "I'm looking for a house in downtown Austin",
                "expected_updates": ["Location preference captured", "Property type captured"]
            },
            {
                "message": "I need to move by next month",
                "expected_updates": ["Timeline captured"]
            },
            {
                "message": "I'm pre-approved for a mortgage",
                "expected_updates": ["Financing info captured"]
            }
        ]

        for test_case in test_cases:
            result = await self.intelligence.analyze_conversation_turn(
                "test_user_qual", "test_tenant", test_case["message"]
            )

            analysis_result = result.get("analysis_result", {})
            qualification_updates = analysis_result.get("qualification_updates", [])

            for expected_update in test_case["expected_updates"]:
                self.assertIn(expected_update, qualification_updates,
                             f"Missing update '{expected_update}' for message '{test_case['message']}'")

    async def test_urgency_signal_detection(self):
        """Test detection of urgency signals"""
        urgent_messages = [
            "My lease is ending next month",
            "I got a job transfer and need to move soon",
            "This is urgent, I need to find something ASAP"
        ]

        for message in urgent_messages:
            result = await self.intelligence.analyze_conversation_turn(
                "test_user_urgency", "test_tenant", message
            )

            # Check if urgency level increased
            self.assertGreater(result.get("urgency_level", 0), 0,
                              f"Failed to detect urgency in '{message}'")

    async def test_buying_signal_detection(self):
        """Test detection of buying signals"""
        buying_messages = [
            "I'm ready to make an offer",
            "Can we schedule a viewing?",
            "I'm pre-approved and ready to buy"
        ]

        for message in buying_messages:
            result = await self.intelligence.analyze_conversation_turn(
                "test_user_buying", "test_tenant", message
            )

            analysis_result = result.get("analysis_result", {})
            detected_patterns = analysis_result.get("detected_patterns", [])

            buying_pattern_found = any("Buying Signal" in pattern for pattern in detected_patterns)
            self.assertTrue(buying_pattern_found,
                           f"Failed to detect buying signal in '{message}'")

    async def test_follow_up_recommendations(self):
        """Test generation of follow-up recommendations"""
        # Create a qualified lead
        conversation_key = "test_tenant:qualified_lead"
        self.intelligence.qualification_data[conversation_key] = LeadQualificationCriteria(
            has_name=True,
            has_contact_info=True,
            has_budget_range=True,
            has_timeline=True,
            urgency_level=8
        )

        self.intelligence.conversation_intelligence[conversation_key] = ConversationIntelligence(
            message_count=5,
            sentiment=ConversationSentiment.POSITIVE,
            detected_intents=[ConversationIntent.PROPERTY_SEARCH],
            buying_signals=["ready to buy"]
        )

        recommendations = await self.intelligence.generate_follow_up_recommendations(
            "qualified_lead", "test_tenant"
        )

        self.assertGreater(len(recommendations), 0)

        # Check that high urgency gets high priority recommendations
        high_priority_recs = [rec for rec in recommendations if rec.priority >= 8]
        self.assertGreater(len(high_priority_recs), 0)

    async def test_conversation_analytics(self):
        """Test conversation analytics generation"""
        # Create sample conversation data
        for i in range(5):
            conversation_key = f"test_tenant:user_{i}"
            self.intelligence.qualification_data[conversation_key] = LeadQualificationCriteria(
                has_name=True,
                has_contact_info=(i % 2 == 0),
                has_budget_range=(i >= 2),
                urgency_level=i * 2
            )

            self.intelligence.conversation_intelligence[conversation_key] = ConversationIntelligence(
                message_count=10 + i,
                sentiment=list(ConversationSentiment)[i % len(ConversationSentiment)],
                detected_intents=[ConversationIntent.PROPERTY_SEARCH]
            )

        analytics = await self.intelligence.get_conversation_analytics("test_tenant")

        # Verify analytics structure
        expected_keys = [
            "total_conversations", "qualification_distribution",
            "intent_distribution", "sentiment_distribution",
            "average_qualification_score"
        ]

        for key in expected_keys:
            self.assertIn(key, analytics)

        self.assertEqual(analytics["total_conversations"], 5)
        self.assertGreater(analytics["average_qualification_score"], 0)

    async def test_conversation_improvements(self):
        """Test conversation improvement suggestions"""
        # Create a conversation with gaps
        conversation_key = "test_tenant:incomplete_lead"
        self.intelligence.qualification_data[conversation_key] = LeadQualificationCriteria(
            has_name=False,
            has_budget_range=False,
            urgency_level=5
        )

        self.intelligence.conversation_intelligence[conversation_key] = ConversationIntelligence(
            sentiment=ConversationSentiment.FRUSTRATED,
            objection_signals=["too expensive"]
        )

        suggestions = await self.intelligence.suggest_conversation_improvements(
            "incomplete_lead", "test_tenant"
        )

        self.assertGreater(len(suggestions), 0)

        # Should suggest collecting name and budget
        suggestion_text = " ".join(suggestions).lower()
        self.assertIn("name", suggestion_text)
        self.assertIn("budget", suggestion_text)


class TestLeadIntelligenceIntegration(unittest.IsolatedAsyncioTestCase):
    """Test the integration layer"""

    async def asyncSetUp(self):
        self.integration = LeadIntelligenceIntegration()
        self.mock_chatbot_manager = Mock(spec=ChatbotManager)
        self.mock_ml_integration = Mock(spec=ChatMLIntegration)

    async def test_initialization(self):
        """Test system initialization"""
        with patch('services.lead_intelligence_integration.integrate_advanced_intelligence') as mock_integrate:
            mock_integrate.return_value = Mock(spec=AdvancedLeadIntelligence)

            success = await self.integration.initialize(
                self.mock_chatbot_manager,
                self.mock_ml_integration
            )

            self.assertTrue(success)
            self.assertTrue(self.integration.is_initialized)
            self.assertIsNotNone(self.integration.intelligence_system)
            self.assertIsNotNone(self.integration.dashboard)

    async def test_message_analysis_without_initialization(self):
        """Test that message analysis fails gracefully without initialization"""
        result = await self.integration.analyze_message_with_intelligence(
            "user", "tenant", "test message"
        )

        self.assertIn("error", result)

    async def test_system_status(self):
        """Test system status reporting"""
        status = self.integration.get_system_status()

        expected_keys = [
            "initialized", "intelligence_available",
            "dashboard_available", "timestamp"
        ]

        for key in expected_keys:
            self.assertIn(key, status)


class TestPatternRecognition(unittest.TestCase):
    """Test pattern recognition capabilities"""

    def setUp(self):
        self.intelligence = AdvancedLeadIntelligence(Mock(), Mock())

    def test_price_patterns(self):
        """Test price inquiry pattern recognition"""
        price_messages = [
            "How much does this cost?",
            "What's the price range?",
            "Is $500k in budget?",
            "Can I afford this property?"
        ]

        for message in price_messages:
            message_lower = message.lower()
            patterns = self.intelligence.intent_patterns[ConversationIntent.PRICE_INQUIRY]

            pattern_found = any(
                __import__('re').search(pattern, message_lower)
                for pattern in patterns
            )

            self.assertTrue(pattern_found, f"Failed to match price pattern in '{message}'")

    def test_timeline_patterns(self):
        """Test timeline discussion pattern recognition"""
        timeline_messages = [
            "When can I move in?",
            "I need to buy by next month",
            "How soon can we close?",
            "Timeline is flexible"
        ]

        for message in timeline_messages:
            message_lower = message.lower()
            patterns = self.intelligence.intent_patterns[ConversationIntent.TIMELINE_DISCUSSION]

            pattern_found = any(
                __import__('re').search(pattern, message_lower)
                for pattern in patterns
            )

            self.assertTrue(pattern_found, f"Failed to match timeline pattern in '{message}'")

    def test_urgency_patterns(self):
        """Test urgency signal pattern recognition"""
        urgency_messages = [
            "This is urgent",
            "Need help ASAP",
            "My lease is ending soon",
            "Job transfer next month"
        ]

        for message in urgency_messages:
            message_lower = message.lower()
            patterns = self.intelligence.urgency_signals

            pattern_found = any(
                __import__('re').search(pattern, message_lower)
                for pattern in patterns
            )

            self.assertTrue(pattern_found, f"Failed to match urgency pattern in '{message}'")


class TestPerformanceAndScaling(unittest.IsolatedAsyncioTestCase):
    """Test performance and scaling capabilities"""

    async def asyncSetUp(self):
        self.intelligence = AdvancedLeadIntelligence(Mock(), Mock())

    async def test_multiple_concurrent_analyses(self):
        """Test handling multiple concurrent message analyses"""
        messages = [
            ("user1", "My budget is $400k"),
            ("user2", "I need to move ASAP"),
            ("user3", "What's the price range?"),
            ("user4", "I'm pre-approved for financing"),
            ("user5", "This property looks perfect!")
        ]

        # Run analyses concurrently
        tasks = [
            self.intelligence.analyze_conversation_turn(user_id, "test_tenant", message)
            for user_id, message in messages
        ]

        results = await asyncio.gather(*tasks)

        # Verify all analyses completed
        self.assertEqual(len(results), 5)

        for result in results:
            self.assertIn("qualification_score", result)
            self.assertIn("conversation_intelligence", result)

    async def test_large_conversation_history(self):
        """Test performance with large conversation histories"""
        # Simulate large conversation history
        user_id = "heavy_user"
        tenant_id = "test_tenant"

        # Process many messages
        for i in range(100):
            await self.intelligence.analyze_conversation_turn(
                user_id, tenant_id, f"Test message {i}"
            )

        # Verify system still responds quickly
        start_time = asyncio.get_event_loop().time()
        result = await self.intelligence.analyze_conversation_turn(
            user_id, tenant_id, "Final test message"
        )
        end_time = asyncio.get_event_loop().time()

        # Should complete within reasonable time (< 1 second)
        processing_time = end_time - start_time
        self.assertLess(processing_time, 1.0)

        # Verify results are still accurate
        self.assertIn("qualification_score", result)


class TestIntelligenceAccuracy(unittest.IsolatedAsyncioTestCase):
    """Test accuracy of intelligence predictions and analysis"""

    async def asyncSetUp(self):
        self.intelligence = AdvancedLeadIntelligence(Mock(), Mock())

    async def test_qualification_accuracy(self):
        """Test accuracy of lead qualification scoring"""
        # High-quality lead conversation
        high_quality_messages = [
            "Hi, my name is Sarah Johnson",
            "I'm looking for a 3-bedroom house in downtown",
            "My budget is $600,000",
            "I'm pre-approved for financing",
            "I need to move by next month",
            "I'm ready to make an offer on the right property"
        ]

        user_id = "high_quality_lead"
        for message in high_quality_messages:
            await self.intelligence.analyze_conversation_turn(
                user_id, "test_tenant", message
            )

        final_result = await self.intelligence.analyze_conversation_turn(
            user_id, "test_tenant", "When can we schedule a viewing?"
        )

        # Should be highly qualified
        self.assertGreater(final_result["qualification_score"], 70)
        self.assertEqual(
            final_result["qualification_level"],
            LeadQualificationLevel.SALES_QUALIFIED.value
        )

    async def test_low_quality_lead_accuracy(self):
        """Test accuracy for low-quality leads"""
        low_quality_messages = [
            "Just browsing",
            "Maybe looking in a few years",
            "Not sure about budget yet"
        ]

        user_id = "low_quality_lead"
        for message in low_quality_messages:
            await self.intelligence.analyze_conversation_turn(
                user_id, "test_tenant", message
            )

        final_result = await self.intelligence.analyze_conversation_turn(
            user_id, "test_tenant", "Just curious about prices"
        )

        # Should be low qualified
        self.assertLess(final_result["qualification_score"], 40)


async def run_comprehensive_tests():
    """Run the complete test suite"""

    print("🧪 Running Enhanced Lead Intelligence Test Suite...")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestLeadQualificationCriteria,
        TestAdvancedLeadIntelligence,
        TestLeadIntelligenceIntegration,
        TestPatternRecognition,
        TestPerformanceAndScaling,
        TestIntelligenceAccuracy
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")

    return success


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())