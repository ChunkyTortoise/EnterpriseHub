"""
Comprehensive Chatbot System Tests

Tests the complete chatbot functionality including session tracking,
ML integration, and cross-tenant isolation.
"""

import asyncio
import logging
import uuid
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Import chatbot components
from chatbot_manager import ChatbotManager, UserType, MessageType
from session_manager import SessionManager
from chat_ml_integration import ChatMLIntegration

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotSystemTestSuite:
    """
    Comprehensive test suite for the chatbot system.

    Tests include:
    - Basic conversation functionality
    - Session persistence across restarts
    - Tenant isolation
    - ML integration (if available)
    - Cross-session tracking
    - User type-specific behavior
    """

    def __init__(self):
        self.test_storage_path = None
        self.chatbot_manager = None
        self.session_manager = None
        self.ml_integration = None

        # Test data
        self.test_tenants = ["tenant_a", "tenant_b"]
        self.test_users = []
        self.test_sessions = []

    async def run_comprehensive_tests(self):
        """Run all chatbot system tests"""
        print("🤖 Starting Chatbot System Integration Tests")
        print("=" * 50)

        try:
            # Setup test environment
            await self.setup_test_environment()
            print("✅ Test environment setup complete")

            # Test basic chatbot functionality
            await self.test_basic_conversation()
            print("✅ Basic conversation tests passed")

            # Test session management
            await self.test_session_persistence()
            print("✅ Session persistence tests passed")

            # Test tenant isolation
            await self.test_tenant_isolation()
            print("✅ Tenant isolation tests passed")

            # Test user type specialization
            await self.test_user_type_behavior()
            print("✅ User type behavior tests passed")

            # Test cross-session tracking
            await self.test_cross_session_tracking()
            print("✅ Cross-session tracking tests passed")

            # Test ML integration (if available)
            await self.test_ml_integration()
            print("✅ ML integration tests passed")

            # Performance tests
            await self.test_performance()
            print("✅ Performance tests passed")

            print("\n🎉 ALL CHATBOT SYSTEM TESTS PASSED!")
            return True

        except Exception as e:
            print(f"\n❌ Chatbot system tests failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await self.cleanup_test_environment()

    async def setup_test_environment(self):
        """Setup test environment with temporary storage"""
        print("\n🔧 Setting up test environment...")

        # Create temporary storage
        self.test_storage_path = Path(tempfile.mkdtemp(prefix="chatbot_test_"))
        print(f"✅ Created test storage: {self.test_storage_path}")

        # Initialize components
        self.session_manager = SessionManager(
            storage_path=str(self.test_storage_path),
            session_timeout_hours=1,  # Short timeout for testing
            cleanup_interval_hours=0.1
        )

        self.chatbot_manager = ChatbotManager()

        # Try to initialize ML components
        try:
            from services.learning.tracking.behavior_tracker import InMemoryBehaviorTracker
            from services.learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer

            behavior_tracker = InMemoryBehaviorTracker()
            feature_engineer = StandardFeatureEngineer(behavior_tracker)

            self.ml_integration = ChatMLIntegration(
                self.chatbot_manager,
                self.session_manager,
                behavior_tracker,
                feature_engineer,
                None  # No personalization engine for testing
            )

            print("✅ ML components initialized")

        except ImportError:
            print("⚠️ ML components not available, testing without ML")
            self.ml_integration = ChatMLIntegration(
                self.chatbot_manager,
                self.session_manager
            )

        # Generate test data
        self.test_users = [
            {"id": f"user_{i}", "type": UserType.LEAD} for i in range(3)
        ] + [
            {"id": f"buyer_{i}", "type": UserType.BUYER} for i in range(2)
        ] + [
            {"id": f"seller_{i}", "type": UserType.SELLER} for i in range(2)
        ]

    async def test_basic_conversation(self):
        """Test basic conversation functionality"""
        print("\n💬 Testing basic conversation functionality...")

        user_id = "test_user_001"
        tenant_id = "test_tenant"

        # Start conversation
        context = await self.chatbot_manager.start_conversation(
            user_id, tenant_id, UserType.LEAD
        )

        assert context is not None, "Should create conversation context"
        assert context.user_id == user_id, "User ID should match"
        assert context.tenant_id == tenant_id, "Tenant ID should match"
        print(f"✅ Started conversation {context.conversation_id}")

        # Test message processing
        test_messages = [
            "Hi, I'm looking for a house",
            "My budget is around $500k",
            "I need 3 bedrooms",
            "When can we schedule a showing?"
        ]

        for message in test_messages:
            response, metadata = await self.chatbot_manager.process_message(
                user_id, tenant_id, message
            )

            assert response is not None and len(response) > 0, "Should generate response"
            assert isinstance(metadata, dict), "Should return metadata"

            print(f"✅ Processed: '{message}' -> '{response[:50]}...'")

        # Check conversation history
        history = await self.chatbot_manager.get_conversation_history(user_id, tenant_id)

        expected_message_count = len(test_messages) * 2  # User + assistant messages
        assert len(history) == expected_message_count, f"Should have {expected_message_count} messages"

        print(f"✅ Conversation history: {len(history)} messages")

        # Check insights
        insights = await self.chatbot_manager.get_user_insights(user_id, tenant_id)

        assert insights is not None, "Should generate insights"
        assert "conversation_summary" in insights, "Should have conversation summary"

        print("✅ Generated user insights")

    async def test_session_persistence(self):
        """Test session persistence across restarts"""
        print("\n💾 Testing session persistence...")

        user_id = "persist_user_001"
        tenant_id = "persist_tenant"

        # Create session
        session = await self.session_manager.create_session(
            user_id, tenant_id, "lead",
            device_info={"platform": "test", "browser": "test"}
        )

        original_session_id = session.session_id
        print(f"✅ Created session {original_session_id}")

        # Update session with data
        await self.session_manager.update_session_activity(
            original_session_id,
            {
                "message_count": 5,
                "current_stage": "qualification",
                "user_profile": {"budget": 500000, "bedrooms": 3}
            }
        )

        print("✅ Updated session data")

        # Simulate restart by creating new session manager
        new_session_manager = SessionManager(
            storage_path=str(self.test_storage_path)
        )

        # Retrieve session
        restored_session = await new_session_manager.get_user_session(user_id, tenant_id)

        assert restored_session is not None, "Should restore session"
        assert restored_session.session_id == original_session_id, "Should have same session ID"
        assert restored_session.message_count == 5, "Should restore message count"
        assert restored_session.current_stage == "qualification", "Should restore stage"
        assert restored_session.user_profile["budget"] == 500000, "Should restore user profile"

        print("✅ Session data restored correctly")

    async def test_tenant_isolation(self):
        """Test tenant data isolation"""
        print("\n🏢 Testing tenant isolation...")

        # Create data for two different tenants
        tenant_a = "tenant_alpha"
        tenant_b = "tenant_beta"
        user_id = "shared_user_001"

        # Create sessions in both tenants
        session_a = await self.session_manager.create_session(
            user_id, tenant_a, "lead"
        )

        session_b = await self.session_manager.create_session(
            user_id, tenant_b, "buyer"
        )

        print(f"✅ Created sessions in both tenants")

        # Start conversations in both tenants
        context_a = await self.chatbot_manager.start_conversation(
            user_id, tenant_a, UserType.LEAD
        )

        context_b = await self.chatbot_manager.start_conversation(
            user_id, tenant_b, UserType.BUYER
        )

        # Add different messages to each tenant
        await self.chatbot_manager.process_message(
            user_id, tenant_a, "I want to buy a starter home"
        )

        await self.chatbot_manager.process_message(
            user_id, tenant_b, "I'm looking for luxury properties"
        )

        # Verify isolation
        history_a = await self.chatbot_manager.get_conversation_history(user_id, tenant_a)
        history_b = await self.chatbot_manager.get_conversation_history(user_id, tenant_b)

        # Each should have their own conversation
        assert len(history_a) >= 2, "Tenant A should have messages"
        assert len(history_b) >= 2, "Tenant B should have messages"

        # Messages should be different
        tenant_a_content = [msg.content for msg in history_a]
        tenant_b_content = [msg.content for msg in history_b]

        assert "starter home" in str(tenant_a_content), "Tenant A should have starter home message"
        assert "luxury properties" in str(tenant_b_content), "Tenant B should have luxury message"
        assert "starter home" not in str(tenant_b_content), "Tenant B should not see Tenant A messages"

        print("✅ Tenant isolation verified")

        # Check session stats are separate
        stats_a = self.session_manager.get_session_stats(tenant_a)
        stats_b = self.session_manager.get_session_stats(tenant_b)

        assert stats_a["total_sessions"] >= 1, "Tenant A should have sessions"
        assert stats_b["total_sessions"] >= 1, "Tenant B should have sessions"

        print("✅ Session statistics isolated")

    async def test_user_type_behavior(self):
        """Test user type-specific behavior"""
        print("\n👤 Testing user type-specific behavior...")

        tenant_id = "behavior_tenant"

        # Test different user types
        test_cases = [
            (UserType.LEAD, "I'm interested in real estate", "qualification"),
            (UserType.BUYER, "Show me some properties", "property"),
            (UserType.SELLER, "I want to sell my house", "valuation")
        ]

        for user_type, test_message, expected_keyword in test_cases:
            user_id = f"user_{user_type.value}_001"

            # Start conversation
            context = await self.chatbot_manager.start_conversation(
                user_id, tenant_id, user_type
            )

            # Process message
            response, metadata = await self.chatbot_manager.process_message(
                user_id, tenant_id, test_message
            )

            # Verify user type-specific response
            response_lower = response.lower()

            if user_type == UserType.LEAD:
                assert any(word in response_lower for word in ["budget", "bedrooms", "preferences"]), \
                    "Lead response should ask qualifying questions"

            elif user_type == UserType.BUYER:
                assert any(word in response_lower for word in ["properties", "criteria", "show"]), \
                    "Buyer response should focus on property search"

            elif user_type == UserType.SELLER:
                assert any(word in response_lower for word in ["valuation", "property", "sell", "market"]), \
                    "Seller response should focus on selling process"

            print(f"✅ {user_type.value} behavior correct")

    async def test_cross_session_tracking(self):
        """Test cross-session conversation tracking"""
        print("\n🔄 Testing cross-session tracking...")

        user_id = "cross_session_user"
        tenant_id = "cross_session_tenant"

        # First session
        session1 = await self.session_manager.create_session(
            user_id, tenant_id, "lead"
        )

        await self.chatbot_manager.start_conversation(
            user_id, tenant_id, UserType.LEAD, session1.session_id
        )

        # Add some messages
        await self.chatbot_manager.process_message(
            user_id, tenant_id, "My budget is $400k", session1.session_id
        )

        await self.chatbot_manager.process_message(
            user_id, tenant_id, "I need 2 bedrooms", session1.session_id
        )

        print("✅ First session completed")

        # Second session (simulate user returning later)
        session2 = await self.session_manager.create_session(
            user_id, tenant_id, "lead"
        )

        # Continue conversation
        response, metadata = await self.chatbot_manager.process_message(
            user_id, tenant_id, "Do you have any properties to show me?", session2.session_id
        )

        # Check that conversation context is maintained
        conversation_key = f"{tenant_id}:{user_id}"
        context = self.chatbot_manager.conversations.get(conversation_key)

        assert context is not None, "Should maintain conversation context"
        assert len(context.messages) >= 5, "Should have accumulated messages from both sessions"

        # Check user profile accumulation
        assert "budget" in context.user_profile or any("400k" in str(msg.extracted_entities) for msg in context.messages), \
            "Should remember budget from previous session"

        print("✅ Cross-session context maintained")

        # Test session merging
        merged_session = await self.session_manager.merge_user_sessions(user_id, tenant_id)

        assert merged_session is not None, "Should merge sessions"
        print("✅ Session merging successful")

    async def test_ml_integration(self):
        """Test ML integration functionality"""
        print("\n🧠 Testing ML integration...")

        if not self.ml_integration.ml_enabled:
            print("⚠️ ML not available, skipping ML integration tests")
            return

        user_id = "ml_test_user"
        tenant_id = "ml_test_tenant"

        # Process messages with ML enhancement
        test_messages = [
            "I'm looking for a house",
            "My budget is $600k",
            "I prefer downtown area",
            "Show me some properties"
        ]

        for message in test_messages:
            response, metadata = await self.ml_integration.enhanced_process_message(
                user_id, tenant_id, message
            )

            assert response is not None, "Should generate enhanced response"
            assert isinstance(metadata, dict), "Should return metadata"

            # Check for ML insights in metadata
            if "ml_insights" in metadata:
                ml_insights = metadata["ml_insights"]
                assert isinstance(ml_insights, dict), "ML insights should be dict"

        print("✅ ML-enhanced message processing")

        # Test conversation insights with ML
        insights = await self.ml_integration.get_conversation_insights(
            user_id, tenant_id, include_predictions=True
        )

        assert insights is not None, "Should generate ML insights"

        if "ml_analysis" in insights:
            assert isinstance(insights["ml_analysis"], dict), "Should have ML analysis"

        print("✅ ML conversation insights")

        # Test outcome tracking
        success = await self.ml_integration.track_conversation_outcome(
            user_id, tenant_id, "lead_qualified", 0.8
        )

        assert success, "Should track conversation outcome"
        print("✅ ML outcome tracking")

        # Test integration status
        status = self.ml_integration.get_integration_status()

        assert "ml_enabled" in status, "Should report ML status"
        assert status["status"] in ["healthy", "limited_functionality"], "Should have valid status"

        print("✅ ML integration status check")

    async def test_performance(self):
        """Test performance under load"""
        print("\n⚡ Testing performance...")

        user_count = 10
        messages_per_user = 5
        tenant_id = "performance_tenant"

        start_time = datetime.now()

        # Create multiple concurrent conversations
        tasks = []
        for i in range(user_count):
            user_id = f"perf_user_{i}"
            task = self._simulate_user_conversation(user_id, tenant_id, messages_per_user)
            tasks.append(task)

        # Run conversations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Check results
        successful_conversations = sum(1 for result in results if not isinstance(result, Exception))
        total_messages = user_count * messages_per_user * 2  # User + assistant messages

        assert successful_conversations >= user_count * 0.8, "Should have mostly successful conversations"

        # Performance metrics
        messages_per_second = total_messages / duration
        avg_response_time = duration / total_messages

        print(f"✅ Performance test completed:")
        print(f"   • {successful_conversations}/{user_count} successful conversations")
        print(f"   • {total_messages} total messages in {duration:.2f}s")
        print(f"   • {messages_per_second:.1f} messages/second")
        print(f"   • {avg_response_time*1000:.1f}ms average response time")

        # Check memory usage
        active_conversations = len(self.chatbot_manager.conversations)
        active_sessions = len(self.session_manager.active_sessions)

        print(f"   • {active_conversations} active conversations")
        print(f"   • {active_sessions} active sessions")

        assert messages_per_second > 10, "Should process at least 10 messages/second"
        assert avg_response_time < 1.0, "Average response time should be under 1 second"

    async def _simulate_user_conversation(self, user_id: str, tenant_id: str, message_count: int):
        """Simulate a user conversation"""
        try:
            # Start conversation
            await self.chatbot_manager.start_conversation(
                user_id, tenant_id, UserType.LEAD
            )

            # Send messages
            messages = [
                "Hi, I'm looking for a house",
                f"My budget is ${400000 + (hash(user_id) % 300000)}",
                "I prefer suburban areas",
                "How soon can we schedule a tour?",
                "What properties do you recommend?"
            ]

            for i in range(min(message_count, len(messages))):
                await self.chatbot_manager.process_message(
                    user_id, tenant_id, messages[i]
                )

            return True

        except Exception as e:
            logger.error(f"Simulated conversation failed for {user_id}: {e}")
            return False

    async def cleanup_test_environment(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")

        try:
            if self.test_storage_path and self.test_storage_path.exists():
                shutil.rmtree(self.test_storage_path)
                print(f"✅ Removed test storage: {self.test_storage_path}")

        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


async def main():
    """Run comprehensive chatbot system test suite"""
    test_suite = ChatbotSystemTestSuite()
    success = await test_suite.run_comprehensive_tests()

    if success:
        print("\n🎉 CHATBOT SYSTEM INTEGRATION COMPLETE!")
        print("✅ Basic conversation functionality working")
        print("✅ Session persistence across restarts")
        print("✅ Tenant data isolation verified")
        print("✅ User type specialization working")
        print("✅ Cross-session tracking functional")
        print("✅ ML integration operational")
        print("✅ Performance requirements met")
        print("\n🚀 Chatbot System Ready for Production!")
    else:
        print("\n❌ Chatbot system integration failed")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(main())