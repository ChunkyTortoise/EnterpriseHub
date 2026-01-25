#!/usr/bin/env python3
"""
Jorge Buyer Bot Intelligence Integration Test
===========================================

Tests Phase 3.3 intelligence enhancements for Jorge Buyer Bot.
Validates intelligence middleware integration, performance metrics,
and enhanced buyer consultation capabilities.

Integration Points:
- Bot Intelligence Middleware integration
- Buyer-focused intelligence context gathering
- Enhanced property matching with market intelligence
- Performance metrics tracking
- Factory method validation

Author: Jorge's Real Estate AI Platform - Phase 3.3 Testing
"""

import asyncio
import sys
import os
import logging
from typing import Dict, List, Any
from datetime import datetime, timezone

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestJorgeBuyerBotIntelligence:
    """Test suite for Jorge Buyer Bot Phase 3.3 intelligence enhancements."""

    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def run_all_tests(self):
        """Run comprehensive test suite for buyer bot intelligence integration."""
        logger.info("🧪 Starting Jorge Buyer Bot Intelligence Integration Tests...")

        try:
            # Test 1: Bot Intelligence Import and Availability
            await self._test_intelligence_imports()

            # Test 2: Buyer Bot Initialization with Intelligence
            await self._test_buyer_bot_initialization()

            # Test 3: Intelligence Context Gathering
            await self._test_intelligence_context_gathering()

            # Test 4: Buyer Workflow with Intelligence
            await self._test_buyer_workflow_with_intelligence()

            # Test 5: Performance Metrics
            await self._test_performance_metrics()

            # Test 6: Factory Methods
            await self._test_factory_methods()

            # Final Results
            self._print_test_results()

        except Exception as e:
            logger.error(f"Critical test failure: {e}")
            self.test_results["errors"].append(f"Critical failure: {str(e)}")

    async def _test_intelligence_imports(self):
        """Test intelligence middleware imports and availability."""
        self.test_results["total_tests"] += 1

        try:
            # Test bot intelligence imports
            from ghl_real_estate_ai.agents.jorge_buyer_bot import BOT_INTELLIGENCE_AVAILABLE, JorgeBuyerBot

            logger.info(f"✅ Bot Intelligence Available: {BOT_INTELLIGENCE_AVAILABLE}")

            if BOT_INTELLIGENCE_AVAILABLE:
                from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext
                logger.info("✅ BotIntelligenceContext import successful")

            self.test_results["passed"] += 1
            logger.info("✅ Test 1 PASSED: Intelligence imports successful")

        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"Intelligence imports failed: {str(e)}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"❌ Test 1 FAILED: {error_msg}")

    async def _test_buyer_bot_initialization(self):
        """Test buyer bot initialization with intelligence features."""
        self.test_results["total_tests"] += 1

        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            # Test with intelligence enabled
            buyer_bot = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=True)

            # Validate initialization
            assert buyer_bot.enable_bot_intelligence == True
            assert hasattr(buyer_bot, 'intelligence_middleware')
            assert hasattr(buyer_bot, 'workflow_stats')
            assert 'intelligence_enhancements' in buyer_bot.workflow_stats

            logger.info("✅ Buyer bot initialized with intelligence features")

            # Test without intelligence (fallback behavior)
            buyer_bot_no_intel = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=False)
            assert buyer_bot_no_intel.enable_bot_intelligence == False

            logger.info("✅ Buyer bot initialized without intelligence (fallback)")

            self.test_results["passed"] += 1
            logger.info("✅ Test 2 PASSED: Buyer bot initialization successful")

        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"Buyer bot initialization failed: {str(e)}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"❌ Test 2 FAILED: {error_msg}")

    async def _test_intelligence_context_gathering(self):
        """Test buyer intelligence context gathering method."""
        self.test_results["total_tests"] += 1

        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
            from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState

            buyer_bot = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=True)

            # Create test buyer state
            test_conversation = [
                {"role": "user", "content": "I'm looking for a 3 bedroom house under 500k in Austin"},
                {"role": "assistant", "content": "Great! Let me help you find the perfect home."}
            ]

            test_state = BuyerBotState(
                buyer_id="test_buyer_001",
                buyer_name="Test Buyer",
                target_areas=["Austin"],
                conversation_history=test_conversation,
                intent_profile=None,
                budget_range={"min": 400000, "max": 500000},
                financing_status="pre_approved",
                urgency_level="3_months",
                property_preferences={"bedrooms": 3, "property_type": "house"},
                current_qualification_step="preferences",
                objection_detected=False,
                detected_objection_type=None,
                next_action="match_properties",
                response_content="",
                matched_properties=[],
                financial_readiness_score=75.0,
                buying_motivation_score=80.0,
                is_qualified=True,
                current_journey_stage="qualification",
                properties_viewed_count=0,
                last_action_timestamp=datetime.now(timezone.utc)
            )

            # Test intelligence gathering (will gracefully handle mock/missing middleware)
            result = await buyer_bot.gather_buyer_intelligence(test_state)

            # Validate result structure
            assert 'intelligence_context' in result
            assert 'intelligence_performance_ms' in result
            assert 'intelligence_available' in result

            logger.info("✅ Intelligence context gathering method executed successfully")

            # Test preference extraction
            preferences = buyer_bot._extract_buyer_preferences_from_conversation(test_conversation)
            assert isinstance(preferences, dict)
            logger.info(f"✅ Buyer preferences extracted: {preferences}")

            self.test_results["passed"] += 1
            logger.info("✅ Test 3 PASSED: Intelligence context gathering successful")

        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"Intelligence context gathering failed: {str(e)}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"❌ Test 3 FAILED: {error_msg}")

    async def _test_buyer_workflow_with_intelligence(self):
        """Test full buyer workflow with intelligence enhancements."""
        self.test_results["total_tests"] += 1

        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            buyer_bot = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=True)

            # Test conversation scenario
            test_conversation = [
                {"role": "user", "content": "Hi, I'm looking to buy a home in Austin"},
                {"role": "assistant", "content": "Hi! I'd love to help you find your perfect home."},
                {"role": "user", "content": "I need a 3 bedroom house, budget is around 450k"}
            ]

            # Process buyer conversation (will handle missing dependencies gracefully)
            result = await buyer_bot.process_buyer_conversation(
                buyer_id="test_buyer_002",
                buyer_name="Test Buyer 2",
                conversation_history=test_conversation
            )

            # Validate workflow completion
            assert 'buyer_id' in result
            assert result['buyer_id'] == "test_buyer_002"

            logger.info("✅ Buyer workflow completed with intelligence features")

            # Check performance tracking
            metrics = await buyer_bot.get_performance_metrics()
            assert 'workflow_statistics' in metrics
            assert 'features_enabled' in metrics
            assert metrics['workflow_statistics']['total_interactions'] > 0

            logger.info(f"✅ Performance metrics tracked: {metrics['workflow_statistics']}")

            self.test_results["passed"] += 1
            logger.info("✅ Test 4 PASSED: Buyer workflow with intelligence successful")

        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"Buyer workflow with intelligence failed: {str(e)}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"❌ Test 4 FAILED: {error_msg}")

    async def _test_performance_metrics(self):
        """Test performance metrics collection and reporting."""
        self.test_results["total_tests"] += 1

        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            buyer_bot = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=True)

            # Test metrics before any operations
            metrics_before = await buyer_bot.get_performance_metrics()
            assert 'workflow_statistics' in metrics_before
            assert 'features_enabled' in metrics_before

            logger.info("✅ Initial performance metrics collected")

            # Simulate some operations by updating stats
            buyer_bot.workflow_stats["total_interactions"] += 3
            buyer_bot.workflow_stats["intelligence_enhancements"] += 2
            buyer_bot.workflow_stats["intelligence_cache_hits"] += 1

            # Test metrics after operations
            metrics_after = await buyer_bot.get_performance_metrics()

            if buyer_bot.enable_bot_intelligence:
                assert 'bot_intelligence' in metrics_after
                assert metrics_after['bot_intelligence']['total_enhancements'] == 2
                assert metrics_after['bot_intelligence']['cache_hits'] == 1
                assert metrics_after['bot_intelligence']['cache_hit_rate'] == 50.0  # 1/2 * 100

            logger.info("✅ Performance metrics update correctly")

            self.test_results["passed"] += 1
            logger.info("✅ Test 5 PASSED: Performance metrics successful")

        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"Performance metrics failed: {str(e)}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"❌ Test 5 FAILED: {error_msg}")

    async def _test_factory_methods(self):
        """Test factory methods for buyer bot creation."""
        self.test_results["total_tests"] += 1

        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            # Test enhanced buyer bot factory method
            enhanced_bot = JorgeBuyerBot.create_enhanced_buyer_bot(tenant_id="enhanced_test")

            assert enhanced_bot.enable_bot_intelligence == True
            assert hasattr(enhanced_bot, 'intelligence_middleware')
            assert hasattr(enhanced_bot, 'workflow_stats')

            logger.info("✅ Enhanced buyer bot factory method successful")

            # Test performance metrics from factory-created bot
            factory_metrics = await enhanced_bot.get_performance_metrics()
            assert 'features_enabled' in factory_metrics
            assert factory_metrics['features_enabled']['bot_intelligence'] == True

            logger.info("✅ Factory-created bot has correct intelligence features")

            self.test_results["passed"] += 1
            logger.info("✅ Test 6 PASSED: Factory methods successful")

        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"Factory methods failed: {str(e)}"
            self.test_results["errors"].append(error_msg)
            logger.error(f"❌ Test 6 FAILED: {error_msg}")

    def _print_test_results(self):
        """Print comprehensive test results."""
        logger.info("\n" + "="*60)
        logger.info("🧪 JORGE BUYER BOT INTELLIGENCE TEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")

        if self.test_results['failed'] > 0:
            logger.info("\n❌ FAILED TESTS:")
            for error in self.test_results['errors']:
                logger.info(f"   - {error}")

        success_rate = (self.test_results['passed'] / self.test_results['total_tests']) * 100
        logger.info(f"\n✅ Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            logger.info("🎯 PHASE 3.3 BUYER BOT INTELLIGENCE INTEGRATION: SUCCESS")
            logger.info("✅ Ready for Jorge Buyer Bot intelligence-enhanced conversations")
        else:
            logger.info("⚠️  PHASE 3.3 BUYER BOT INTELLIGENCE INTEGRATION: NEEDS ATTENTION")
            logger.info("❗ Review failed tests before deploying intelligence features")


async def main():
    """Run Jorge Buyer Bot intelligence integration tests."""
    logger.info("🚀 Starting Jorge Buyer Bot Phase 3.3 Intelligence Integration Tests...")

    test_runner = TestJorgeBuyerBotIntelligence()
    await test_runner.run_all_tests()

    logger.info("🏁 Jorge Buyer Bot Intelligence Integration Tests Complete!")


if __name__ == "__main__":
    asyncio.run(main())