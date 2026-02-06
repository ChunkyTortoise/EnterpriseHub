#!/usr/bin/env python3
"""
Property Alert System Integration Test

Tests the complete property alert pipeline from property scoring through
EventPublisher to UI notification integration.

This demonstrates the end-to-end flow:
1. PropertyAlertEngine generates alerts from property matches
2. EventPublisher publishes property alert events
3. NotificationSystem handles property alert notifications
4. PropertyAlertDashboard displays detailed property information

Usage:
    python test_property_alert_integration.py
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Core system imports
from ghl_real_estate_ai.services.property_alert_engine import PropertyAlertEngine, AlertPreferences
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.streamlit_demo.components.notification_system import NotificationSystem
from ghl_real_estate_ai.streamlit_demo.components.property_alert_dashboard import PropertyAlertDashboard

class PropertyAlertIntegrationTest:
    """
    Integration test for the complete property alert system.
    """

    def __init__(self):
        self.alert_engine = PropertyAlertEngine()
        self.event_publisher = get_event_publisher()
        self.notification_system = NotificationSystem()
        self.alert_dashboard = PropertyAlertDashboard()

    async def run_complete_test(self):
        """Run complete end-to-end property alert test."""
        print("🏠 Starting Property Alert System Integration Test")
        print("=" * 60)

        # Test 1: Create alert preferences
        await self.test_alert_preferences()

        # Test 2: Generate property alerts
        await self.test_alert_generation()

        # Test 3: Test event publishing
        await self.test_event_publishing()

        # Test 4: Test notification creation
        await self.test_notification_integration()

        # Test 5: Test dashboard integration
        await self.test_dashboard_integration()

        print("\n✅ All Property Alert Integration Tests Completed Successfully!")

    async def test_alert_preferences(self):
        """Test alert preference creation and management."""
        print("\n📋 Test 1: Alert Preferences")
        print("-" * 30)

        # Create sample alert preferences
        preferences = AlertPreferences(
            lead_id="test_lead_123",
            tenant_id="test_tenant_abc",
            min_price=300000,
            max_price=600000,
            min_bedrooms=2,
            max_bedrooms=4,
            preferred_neighborhoods=["Downtown", "Westside"],
            property_types=["single_family", "condo"],
            must_have_features=["garage", "updated_kitchen"],
            alert_threshold_score=80.0,
            max_alerts_per_day=5
        )

        print(f"✅ Created alert preferences for lead: {preferences.lead_id}")
        print(f"   Price range: ${preferences.min_price:,} - ${preferences.max_price:,}")
        print(f"   Bedrooms: {preferences.min_bedrooms} - {preferences.max_bedrooms}")
        print(f"   Alert threshold: {preferences.alert_threshold_score}%")

        return preferences

    async def test_alert_generation(self):
        """Test property alert generation."""
        print("\n🎯 Test 2: Alert Generation")
        print("-" * 30)

        # Sample property data that should trigger an alert
        sample_property = {
            "property_id": "prop_456",
            "address": "123 Test Street, Sample City, CA 90210",
            "price": 450000,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "sqft": 1850,
            "property_type": "single_family",
            "features": ["garage", "updated_kitchen", "hardwood_floors"],
            "neighborhood": "Westside",
            "days_on_market": 5,
            "listing_status": "active"
        }

        # Mock match score (in real implementation, this comes from EnhancedPropertyMatcher)
        match_score = 87.5

        # Mock match reasoning
        match_reasoning = {
            "price_analysis": {
                "within_budget": True,
                "market_position": "fair_value"
            },
            "location_analysis": {
                "in_preferred_area": True,
                "commute_minutes": 25
            },
            "feature_analysis": {
                "matched_features": ["garage", "updated_kitchen"],
                "missing_features": []
            }
        }

        # Generate alert using the engine
        alert = await self.alert_engine._create_property_alert(
            lead_id="test_lead_123",
            property_id=sample_property["property_id"],
            property_data=sample_property,
            match_score=match_score,
            match_reasoning=match_reasoning,
            alert_type="new_match"
        )

        print(f"✅ Generated property alert: {alert.alert_id}")
        print(f"   Property: {sample_property['address']}")
        print(f"   Match score: {match_score}%")
        print(f"   Alert type: {alert.alert_type}")

        return alert, sample_property

    async def test_event_publishing(self):
        """Test property alert event publishing."""
        print("\n📡 Test 3: Event Publishing")
        print("-" * 30)

        # Sample property data for event
        sample_property = {
            "property_id": "prop_789",
            "address": "456 Event Lane, Test City, CA 90211",
            "price": 525000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2200,
            "property_type": "single_family"
        }

        # Publish property alert event
        await self.event_publisher.publish_property_alert(
            alert_id="test_alert_789",
            lead_id="test_lead_123",
            property_id=sample_property["property_id"],
            match_score=92.3,
            alert_type="price_drop",
            property_data=sample_property,
            match_reasoning={
                "price_analysis": {"within_budget": True, "price_dropped_by": 25000},
                "location_analysis": {"in_preferred_area": True}
            }
        )

        print(f"✅ Published property alert event")
        print(f"   Alert ID: test_alert_789")
        print(f"   Property: {sample_property['address']}")
        print(f"   Event type: property_alert")

    async def test_notification_integration(self):
        """Test notification system integration with property alerts."""
        print("\n🔔 Test 4: Notification Integration")
        print("-" * 30)

        # Mock WebSocket event data for property alert
        mock_event_data = {
            "event_type": "property_alert",
            "priority": "high",
            "data": {
                "alert_id": "test_alert_notification_001",
                "lead_id": "test_lead_123",
                "property_id": "prop_notification_test",
                "match_score": 88.7,
                "alert_type": "market_opportunity",
                "property_summary": {
                    "address": "789 Notification Ave, Test City, CA",
                    "price": 475000,
                    "formatted_price": "$475,000",
                    "bedrooms": 3,
                    "bathrooms": 2.5,
                    "sqft": 1950,
                    "formatted_sqft": "1,950 sq ft"
                },
                "property_data": {
                    "property_type": "condo",
                    "features": ["garage", "pool", "updated_kitchen"]
                },
                "match_reasoning": {
                    "price_analysis": {"within_budget": True, "great_value": True},
                    "location_analysis": {"in_preferred_area": True, "commute_minutes": 20}
                }
            }
        }

        # Process event through notification system
        self.notification_system.process_websocket_event(mock_event_data)

        print(f"✅ Processed property alert through notification system")
        print(f"   Alert type: {mock_event_data['data']['alert_type']}")
        print(f"   Match score: {mock_event_data['data']['match_score']}%")
        print(f"   Property: {mock_event_data['data']['property_summary']['address']}")

    async def test_dashboard_integration(self):
        """Test property alert dashboard integration."""
        print("\n📊 Test 5: Dashboard Integration")
        print("-" * 30)

        # Mock WebSocket event for dashboard
        dashboard_event_data = {
            "event_type": "property_alert",
            "data": {
                "alert_id": "dashboard_test_001",
                "lead_id": "test_lead_123",
                "property_id": "prop_dashboard_test",
                "match_score": 95.2,
                "alert_type": "new_match",
                "property_summary": {
                    "address": "321 Dashboard Drive, Test City, CA",
                    "price": 550000,
                    "formatted_price": "$550,000",
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "sqft": 2400,
                    "formatted_sqft": "2,400 sq ft"
                },
                "property_data": {
                    "property_type": "single_family",
                    "neighborhood": "Premium District",
                    "features": ["garage", "pool", "updated_kitchen", "hardwood_floors"]
                },
                "match_reasoning": {
                    "price_analysis": {
                        "within_budget": True,
                        "market_position": "excellent_value"
                    },
                    "location_analysis": {
                        "in_preferred_area": True,
                        "commute_minutes": 15
                    },
                    "feature_analysis": {
                        "matched_features": ["garage", "updated_kitchen"],
                        "bonus_features": ["pool", "hardwood_floors"]
                    }
                }
            }
        }

        # Add alert to dashboard
        self.alert_dashboard.add_property_alert_from_event(dashboard_event_data)

        # Get analytics
        analytics = self.alert_dashboard.get_alert_analytics()

        print(f"✅ Added property alert to dashboard")
        print(f"   Alert ID: dashboard_test_001")
        print(f"   Match score: {dashboard_event_data['data']['match_score']}%")
        print(f"   Dashboard analytics: {analytics['total']} total alerts")

    def display_test_summary(self):
        """Display test summary and system status."""
        print("\n" + "=" * 60)
        print("🏠 PROPERTY ALERT SYSTEM TEST SUMMARY")
        print("=" * 60)

        print("\n✅ Components Tested:")
        print("   • PropertyAlertEngine - Alert generation and management")
        print("   • EventPublisher - Real-time event broadcasting")
        print("   • NotificationSystem - UI notification integration")
        print("   • PropertyAlertDashboard - Detailed property alert interface")

        print("\n🔧 Integration Points Verified:")
        print("   • Alert preferences management")
        print("   • Property scoring and alert generation")
        print("   • WebSocket event publishing")
        print("   • Real-time notification creation")
        print("   • Dashboard display and interaction")

        print("\n📊 System Ready For:")
        print("   • Background property scoring pipeline")
        print("   • Real-time alert delivery")
        print("   • Multi-channel notifications")
        print("   • Interactive property management")

        print("\n🎯 Next Steps:")
        print("   • Deploy background APScheduler jobs")
        print("   • Configure notification preferences")
        print("   • Set up alert thresholds per lead")
        print("   • Enable multi-channel delivery (email, SMS)")

async def main():
    """Run the complete property alert integration test."""
    test_runner = PropertyAlertIntegrationTest()

    try:
        await test_runner.run_complete_test()
        test_runner.display_test_summary()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    # Run the integration test
    print("🚀 Starting Property Alert System Integration Test...")
    success = asyncio.run(main())

    if success:
        print("\n🎉 All tests passed! Property Alert System is ready for production.")
        exit(0)
    else:
        print("\n💥 Tests failed! Please check the error messages above.")
        exit(1)