#!/usr/bin/env python3
"""
Test GHL Integration - Validates GHL client connectivity and contact information fetching.

Tests the enhanced GHL integration for Lead Bot sequence delivery.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.lead_sequence_scheduler import get_lead_scheduler
from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)

class GHLIntegrationTest:
    """Test suite for GHL integration functionality."""

    def __init__(self):
        self.ghl_client = GHLClient()
        self.scheduler = get_lead_scheduler()
        self.test_contact_id = "test_contact_001"  # You can replace with a real GHL contact ID

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

    async def test_ghl_client_health(self):
        """Test GHL client health check."""
        test_name = "GHL Client Health Check"
        try:
            health_response = self.ghl_client.check_health()
            success = health_response.status_code == 200

            if success:
                self.log_test(test_name, True, f"Health check returned {health_response.status_code}")
            else:
                self.log_test(test_name, False, f"Health check failed with status {health_response.status_code}")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_contact_information_fetching(self):
        """Test fetching contact information from GHL."""
        test_name = "Contact Information Fetching"
        try:
            # Test with the scheduler's contact info method
            contact_info = await self.scheduler._get_lead_contact_info(self.test_contact_id)

            if contact_info:
                required_fields = ["contact_id", "phone", "email", "full_name"]
                has_all_fields = all(field in contact_info for field in required_fields)

                if has_all_fields:
                    self.log_test(test_name, True, f"Contact info retrieved: {contact_info['full_name']}")
                else:
                    missing = [f for f in required_fields if f not in contact_info]
                    self.log_test(test_name, False, f"Missing fields: {missing}")
            else:
                self.log_test(test_name, False, "No contact information returned")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_contact_caching(self):
        """Test contact information caching."""
        test_name = "Contact Information Caching"
        try:
            # First call should fetch from API/fallback
            start_time = datetime.now()
            contact_info_1 = await self.scheduler._get_lead_contact_info(self.test_contact_id)
            first_call_duration = (datetime.now() - start_time).total_seconds()

            # Second call should use cache
            start_time = datetime.now()
            contact_info_2 = await self.scheduler._get_lead_contact_info(self.test_contact_id)
            second_call_duration = (datetime.now() - start_time).total_seconds()

            # Cache should be faster and return same data
            if (contact_info_1 == contact_info_2 and
                second_call_duration < first_call_duration and
                contact_info_1 is not None):
                self.log_test(test_name, True, f"Cache hit: {second_call_duration:.3f}s vs {first_call_duration:.3f}s")
            else:
                self.log_test(test_name, False, f"Cache miss or data mismatch")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_message_delivery_structure(self):
        """Test message delivery structure (without actually sending)."""
        test_name = "Message Delivery Structure"
        try:
            # Test SMS structure
            if settings.test_mode:
                # In test mode, we can safely call send_message
                sms_response = await self.ghl_client.send_message(
                    contact_id=self.test_contact_id,
                    message="Test SMS message",
                    channel=MessageType.SMS
                )

                email_response = await self.ghl_client.send_message(
                    contact_id=self.test_contact_id,
                    message="Test email message",
                    channel=MessageType.EMAIL
                )

                if (sms_response and sms_response.get("status") == "mocked" and
                    email_response and email_response.get("status") == "mocked"):
                    self.log_test(test_name, True, "Test mode message structure validated")
                else:
                    self.log_test(test_name, False, "Message structure validation failed")
            else:
                # In production mode, just verify the method exists and is callable
                assert callable(getattr(self.ghl_client, 'send_message', None))
                self.log_test(test_name, True, "send_message method is callable")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_scheduler_ghl_integration(self):
        """Test scheduler GHL client integration."""
        test_name = "Scheduler GHL Integration"
        try:
            # Verify scheduler has GHL client
            if hasattr(self.scheduler, 'ghl_client') and self.scheduler.ghl_client is not None:
                # Test that SMS delivery method exists
                assert callable(getattr(self.scheduler, '_send_sequence_sms', None))
                assert callable(getattr(self.scheduler, '_send_sequence_email', None))
                self.log_test(test_name, True, "Scheduler has GHL client and delivery methods")
            else:
                self.log_test(test_name, False, "Scheduler missing GHL client")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_error_handling(self):
        """Test error handling for invalid contact IDs."""
        test_name = "Error Handling"
        try:
            # Test with invalid contact ID
            invalid_contact_info = await self.scheduler._get_lead_contact_info("invalid_contact_999")

            # Should still return fallback info, not None
            if invalid_contact_info and invalid_contact_info.get("contact_id") == "invalid_contact_999":
                self.log_test(test_name, True, "Graceful fallback for invalid contact ID")
            else:
                self.log_test(test_name, False, "Error handling failed - no fallback provided")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def test_configuration_check(self):
        """Test GHL configuration."""
        test_name = "GHL Configuration Check"
        try:
            # Check if API key and location are configured
            has_api_key = bool(settings.ghl_api_key and settings.ghl_api_key != "dummy")
            has_location = bool(settings.ghl_location_id and settings.ghl_location_id != "dummy")

            config_status = f"API Key: {'✓' if has_api_key else '✗'}, Location: {'✓' if has_location else '✗'}"

            if has_api_key and has_location:
                self.log_test(test_name, True, f"Full configuration present - {config_status}")
            elif settings.test_mode:
                self.log_test(test_name, True, f"Test mode active - {config_status}")
            else:
                self.log_test(test_name, False, f"Missing configuration - {config_status}")

        except Exception as e:
            self.log_test(test_name, False, str(e))

    async def run_all_tests(self):
        """Run the complete test suite."""
        print(f"🚀 Starting GHL Integration Tests")
        print(f"📋 Test Contact ID: {self.test_contact_id}")
        print(f"🔧 Test Mode: {settings.test_mode}")
        print(f"🕒 Started at: {datetime.now()}")
        print("=" * 60)

        # Run all tests
        await self.test_ghl_client_health()
        await self.test_configuration_check()
        await self.test_contact_information_fetching()
        await self.test_contact_caching()
        await self.test_message_delivery_structure()
        await self.test_scheduler_ghl_integration()
        await self.test_error_handling()

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
            print("🎉 GHL integration is working well!")
            return True
        else:
            print("🚨 GHL integration needs attention!")
            return False

async def main():
    """Main test execution function."""
    test_suite = GHLIntegrationTest()

    try:
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"💥 Critical test error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    print(f"\n📝 Next Steps:")
    print(f"   1. Review test results above")
    print(f"   2. Configure GHL API credentials if needed")
    print(f"   3. Test with real GHL contact ID")
    print(f"   4. Validate message delivery in GHL dashboard")
    sys.exit(exit_code)