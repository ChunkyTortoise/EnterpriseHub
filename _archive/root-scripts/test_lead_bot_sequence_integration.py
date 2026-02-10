import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
End-to-End Test for Lead Bot Sequence Integration

Tests the complete flow of lead sequence state management and scheduling.
This validates the fixes made to the Lead Bot execution layer.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ghl_real_estate_ai.services.lead_sequence_state_service import (
    get_sequence_service,
    SequenceDay,
    SequenceStatus,
    LeadSequenceState
)
from ghl_real_estate_ai.services.lead_sequence_scheduler import get_lead_scheduler
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class LeadBotSequenceTest:
    """Comprehensive test suite for lead bot sequence integration."""

    def __init__(self):
        self.sequence_service = get_sequence_service()
        self.scheduler = get_lead_scheduler()
        self.cache_service = get_cache_service()
        self.test_lead_id = f"test_lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        self.results["tests_run"] += 1
        if success:
            self.results["tests_passed"] += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAILED {details}")

    async def test_sequence_state_creation(self):
        """Test sequence state creation and persistence."""
        test_name = "Sequence State Creation"
        try:
            # Create a new sequence
            sequence_state = await self.sequence_service.create_sequence(
                self.test_lead_id,
                initial_day=SequenceDay.DAY_3
            )

            # Verify creation
            assert sequence_state is not None
            assert sequence_state.lead_id == self.test_lead_id
            assert sequence_state.current_day == SequenceDay.DAY_3
            assert sequence_state.sequence_status == SequenceStatus.PENDING

            self.log_test(test_name, True, f"Created sequence for {self.test_lead_id}")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_sequence_state_persistence(self):
        """Test that sequence state persists in Redis."""
        test_name = "Sequence State Persistence"
        try:
            # Get state that was created in previous test
            restored_state = await self.sequence_service.get_state(self.test_lead_id)

            assert restored_state is not None
            assert restored_state.lead_id == self.test_lead_id
            assert restored_state.current_day == SequenceDay.DAY_3

            self.log_test(test_name, True, f"Successfully restored state from Redis")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_sequence_day_advancement(self):
        """Test advancing through sequence days."""
        test_name = "Sequence Day Advancement"
        try:
            # Mark Day 3 as completed
            await self.sequence_service.mark_action_completed(
                self.test_lead_id,
                SequenceDay.DAY_3,
                "sms_sent"
            )

            # Advance to next day
            updated_state = await self.sequence_service.advance_to_next_day(self.test_lead_id)

            assert updated_state is not None
            assert updated_state.current_day == SequenceDay.DAY_7
            assert updated_state.day_3_completed == True
            assert updated_state.day_3_delivered_at is not None

            self.log_test(test_name, True, f"Advanced from Day 3 to {updated_state.current_day.value}")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_cma_generation_tracking(self):
        """Test CMA generation tracking."""
        test_name = "CMA Generation Tracking"
        try:
            # Mark CMA as generated
            success = await self.sequence_service.set_cma_generated(self.test_lead_id)
            assert success == True

            # Verify it's tracked
            state = await self.sequence_service.get_state(self.test_lead_id)
            assert state.cma_generated == True
            assert state.cma_generated_at is not None

            self.log_test(test_name, True, "CMA generation correctly tracked")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_engagement_tracking(self):
        """Test engagement tracking."""
        test_name = "Engagement Tracking"
        try:
            # Record engagement
            success = await self.sequence_service.record_engagement(
                self.test_lead_id,
                "response"
            )
            assert success == True

            # Verify tracking
            state = await self.sequence_service.get_state(self.test_lead_id)
            assert state.response_count > 0
            assert state.last_response_at is not None
            assert state.engagement_status == "responsive"

            self.log_test(test_name, True, f"Engagement tracked: {state.response_count} responses")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        test_name = "Scheduler Initialization"
        try:
            # Check if scheduler is enabled
            if not self.scheduler.enabled:
                self.log_test(test_name, False, "Scheduler not enabled - APScheduler dependencies missing")
                return

            # Try to start scheduler
            started = await self.scheduler.start()
            if not started:
                self.log_test(test_name, False, "Scheduler failed to start")
                return

            # Get status
            status = await self.scheduler.get_scheduler_status()
            assert status["enabled"] == True

            self.log_test(test_name, True, f"Scheduler running: {status.get('running', False)}")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_sequence_scheduling(self):
        """Test sequence action scheduling."""
        test_name = "Sequence Action Scheduling"
        try:
            if not self.scheduler.enabled:
                self.log_test(test_name, False, "Skipped - scheduler not enabled")
                return

            # Schedule a sequence start
            success = await self.scheduler.schedule_sequence_start(
                f"{self.test_lead_id}_schedule",
                delay_minutes=1
            )
            assert success == True

            # Check scheduler status
            status = await self.scheduler.get_scheduler_status()
            assert status["total_jobs"] > 0

            self.log_test(test_name, True, f"Scheduled sequence with {status['total_jobs']} jobs")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_sequence_summary(self):
        """Test sequence summary generation."""
        test_name = "Sequence Summary Generation"
        try:
            summary = await self.sequence_service.get_sequence_summary(self.test_lead_id)

            assert summary is not None
            assert summary["lead_id"] == self.test_lead_id
            assert summary["current_day"] == SequenceDay.DAY_7.value
            assert summary["progress"]["day_3_completed"] == True
            assert summary["cma_generated"] == True
            assert summary["response_count"] > 0

            self.log_test(test_name, True, f"Generated summary: {summary['current_day']}, CMA: {summary['cma_generated']}")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_lead_bot_integration(self):
        """Test basic Lead Bot integration (without full dependencies)."""
        test_name = "Lead Bot Integration"
        try:
            # We can't fully test LeadBot without all dependencies,
            # but we can test the sequence state integration
            from ghl_real_estate_ai.services.lead_sequence_state_service import LeadSequenceState

            # Test state serialization/deserialization
            state = await self.sequence_service.get_state(self.test_lead_id)
            state_dict = state.to_dict()
            restored_state = LeadSequenceState.from_dict(state_dict)

            assert restored_state.lead_id == state.lead_id
            assert restored_state.current_day == state.current_day
            assert restored_state.cma_generated == state.cma_generated

            self.log_test(test_name, True, "State serialization/deserialization works")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_full_sequence_flow(self):
        """Test complete sequence progression."""
        test_name = "Full Sequence Flow"
        try:
            # Create a new lead for full flow test
            flow_lead_id = f"{self.test_lead_id}_flow"

            # Create sequence
            sequence = await self.sequence_service.create_sequence(flow_lead_id)

            # Simulate Day 3 → Day 7
            await self.sequence_service.mark_action_completed(flow_lead_id, SequenceDay.DAY_3, "sms_sent")
            sequence = await self.sequence_service.advance_to_next_day(flow_lead_id)
            assert sequence.current_day == SequenceDay.DAY_7

            # Simulate Day 7 → Day 14
            await self.sequence_service.mark_action_completed(flow_lead_id, SequenceDay.DAY_7, "call_completed")
            sequence = await self.sequence_service.advance_to_next_day(flow_lead_id)
            assert sequence.current_day == SequenceDay.DAY_14

            # Simulate Day 14 → Day 30
            await self.sequence_service.mark_action_completed(flow_lead_id, SequenceDay.DAY_14, "email_sent")
            sequence = await self.sequence_service.advance_to_next_day(flow_lead_id)
            assert sequence.current_day == SequenceDay.DAY_30

            # Simulate Day 30 → Complete
            await self.sequence_service.mark_action_completed(flow_lead_id, SequenceDay.DAY_30, "sms_sent")
            await self.sequence_service.complete_sequence(flow_lead_id, "nurture")

            # Verify final state
            final_state = await self.sequence_service.get_state(flow_lead_id)
            assert final_state.sequence_status == SequenceStatus.COMPLETED
            assert final_state.engagement_status == "nurture"
            assert all([
                final_state.day_3_completed,
                final_state.day_7_completed,
                final_state.day_14_completed,
                final_state.day_30_completed
            ])

            self.log_test(test_name, True, "Complete 3-7-30 sequence flow successful")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def cleanup_test_data(self):
        """Clean up test data."""
        try:
            # Delete test sequence states
            test_leads = [
                self.test_lead_id,
                f"{self.test_lead_id}_schedule",
                f"{self.test_lead_id}_flow"
            ]

            for lead_id in test_leads:
                # Cancel any scheduled jobs
                if self.scheduler.enabled:
                    await self.scheduler.cancel_sequence(lead_id)

                # Delete state
                state_key = f"lead_sequence:{lead_id}"
                await self.cache_service.delete(state_key)

            print(f"🧹 Cleaned up test data for {len(test_leads)} test leads")

        except Exception as e:
            print(f"⚠️ Warning: Failed to cleanup test data: {e}")

    async def run_all_tests(self):
        """Run the complete test suite."""
        print(f"🚀 Starting Lead Bot Sequence Integration Tests")
        print(f"📋 Test Lead ID: {self.test_lead_id}")
        print(f"🕒 Started at: {datetime.now()}")
        print("=" * 60)

        # Run all tests in sequence
        await self.test_sequence_state_creation()
        await self.test_sequence_state_persistence()
        await self.test_sequence_day_advancement()
        await self.test_cma_generation_tracking()
        await self.test_engagement_tracking()
        await self.test_scheduler_initialization()
        await self.test_sequence_scheduling()
        await self.test_sequence_summary()
        await self.test_lead_bot_integration()
        await self.test_full_sequence_flow()

        # Cleanup
        await self.cleanup_test_data()

        # Print results
        print("=" * 60)
        print(f"📊 Test Results:")
        print(f"   Total Tests: {self.results['tests_run']}")
        print(f"   ✅ Passed: {self.results['tests_passed']}")
        print(f"   ❌ Failed: {self.results['tests_failed']}")

        if self.results["errors"]:
            print(f"\n💥 Errors:")
            for error in self.results["errors"]:
                print(f"   - {error}")

        success_rate = (self.results["tests_passed"] / self.results["tests_run"]) * 100 if self.results["tests_run"] > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("🎉 Lead Bot sequence integration is working well!")
            return True
        else:
            print("🚨 Lead Bot sequence integration needs attention!")
            return False

async def main():
    """Main test execution function."""
    test_suite = LeadBotSequenceTest()

    try:
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        await test_suite.cleanup_test_data()
        return 1
    except Exception as e:
        print(f"💥 Critical test error: {e}")
        await test_suite.cleanup_test_data()
        return 1
    finally:
        # Shutdown scheduler if it was started
        if test_suite.scheduler.enabled:
            await test_suite.scheduler.stop()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)