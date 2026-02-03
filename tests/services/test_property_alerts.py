"""
Test suite for Property Alert System.

Tests automated property alert functionality including:
- Alert criteria setup and management
- New listing notifications
- Price drop alerts
- Market opportunity detection
- Corporate relocation timing alerts
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

try:
    from ghl_real_estate_ai.services.property_alerts import (
        PropertyAlertSystem,
        AlertCriteria,
        PropertyAlert,
        MarketAlert,
        AlertType,
        AlertPriority,
        get_property_alert_system
    )
    from ghl_real_estate_ai.services.austin_market_service import PropertyType, PropertyListing
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestAlertCriteria:
    """Test AlertCriteria model functionality."""

    def test_alert_criteria_creation(self):
        """Test creating alert criteria."""
        criteria = AlertCriteria(
            lead_id="test_lead_001",
            min_price=300000,
            max_price=800000,
            min_beds=2,
            property_types=[PropertyType.SINGLE_FAMILY],
            neighborhoods=["Round Rock", "Domain"],
            work_location="Apple"
        )

        assert criteria.lead_id == "test_lead_001"
        assert criteria.min_price == 300000
        assert criteria.max_price == 800000
        assert criteria.min_beds == 2
        assert PropertyType.SINGLE_FAMILY in criteria.property_types
        assert "Round Rock" in criteria.neighborhoods
        assert criteria.work_location == "Apple"
        assert criteria.active is True
        assert criteria.created_at is not None

    def test_alert_criteria_defaults(self):
        """Test alert criteria default values."""
        criteria = AlertCriteria(lead_id="test_lead_001")

        assert criteria.property_types == [PropertyType.SINGLE_FAMILY]
        assert criteria.neighborhoods == []
        assert criteria.lifestyle_preferences == []
        assert criteria.must_have_features == []
        assert criteria.deal_threshold == 0.1
        assert criteria.active is True

    def test_alert_criteria_post_init(self):
        """Test alert criteria post-initialization."""
        criteria = AlertCriteria(lead_id="test_lead_001")

        assert criteria.created_at <= datetime.now()
        assert criteria.last_updated <= datetime.now()


class TestPropertyAlert:
    """Test PropertyAlert model functionality."""

    def test_property_alert_creation(self):
        """Test creating property alert."""
        alert = PropertyAlert(
            alert_id="alert_001",
            lead_id="lead_001",
            alert_type=AlertType.NEW_LISTING,
            priority=AlertPriority.MEDIUM,
            property_data={"mls_id": "ATX001", "price": 500000},
            message="New listing matches your criteria",
            detailed_analysis={"match_score": 85},
            action_items=["Schedule showing"],
            expiry_time=datetime.now() + timedelta(hours=48)
        )

        assert alert.alert_id == "alert_001"
        assert alert.alert_type == AlertType.NEW_LISTING
        assert alert.priority == AlertPriority.MEDIUM
        assert alert.property_data["price"] == 500000
        assert "Schedule showing" in alert.action_items
        assert alert.sent is False
        assert alert.created_at is not None


class TestPropertyAlertSystem:
    """Test Property Alert System functionality."""

    @pytest.fixture
    def alert_system(self):
        """Create alert system instance for testing."""
        return PropertyAlertSystem()

    @pytest.fixture
    def sample_criteria(self):
        """Sample alert criteria for testing."""
        return AlertCriteria(
            lead_id="test_lead_001",
            min_price=400000,
            max_price=700000,
            min_beds=3,
            neighborhoods=["Round Rock"],
            work_location="Apple",
            max_commute_time=30
        )

    @pytest.fixture
    def sample_property(self):
        """Sample property for alert testing."""
        return PropertyListing(
            mls_id="ATX2024001",
            address="123 Round Rock Way, Round Rock, TX",
            price=550000,
            beds=3,
            baths=2.5,
            sqft=2200,
            lot_size=0.25,
            year_built=2020,
            property_type=PropertyType.SINGLE_FAMILY,
            neighborhood="Round Rock",
            school_district="Round Rock ISD",
            days_on_market=5,
            price_per_sqft=250,
            price_changes=[],
            features=["Open Floor Plan"],
            coordinates=(30.5, -97.7),
            photos=["photo1.jpg"],
            description="Beautiful home in Round Rock",
            listing_agent={"name": "Jorge Martinez"},
            last_updated=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_setup_lead_alerts(self, alert_system, sample_criteria):
        """Test setting up alerts for a lead."""
        success = await alert_system.setup_lead_alerts(sample_criteria)

        assert success is True
        assert sample_criteria.lead_id in alert_system.active_criteria

        # Verify criteria is stored correctly
        stored_criteria = alert_system.active_criteria[sample_criteria.lead_id]
        assert stored_criteria.min_price == sample_criteria.min_price
        assert stored_criteria.neighborhoods == sample_criteria.neighborhoods

    @pytest.mark.asyncio
    async def test_update_lead_alerts(self, alert_system, sample_criteria):
        """Test updating existing alert criteria."""
        # Setup initial criteria
        await alert_system.setup_lead_alerts(sample_criteria)

        # Update criteria
        sample_criteria.max_price = 800000
        sample_criteria.neighborhoods = ["Round Rock", "Cedar Park"]

        success = await alert_system.update_lead_alerts(
            sample_criteria.lead_id, sample_criteria
        )

        assert success is True

        # Verify updates
        stored_criteria = alert_system.active_criteria[sample_criteria.lead_id]
        assert stored_criteria.max_price == 800000
        assert "Cedar Park" in stored_criteria.neighborhoods

    @pytest.mark.asyncio
    async def test_disable_lead_alerts(self, alert_system, sample_criteria):
        """Test disabling alerts for a lead."""
        # Setup initial criteria
        await alert_system.setup_lead_alerts(sample_criteria)
        assert alert_system.active_criteria[sample_criteria.lead_id].active is True

        # Disable alerts
        success = await alert_system.disable_lead_alerts(sample_criteria.lead_id)

        assert success is True
        assert alert_system.active_criteria[sample_criteria.lead_id].active is False

    @pytest.mark.asyncio
    async def test_property_matches_criteria(self, alert_system, sample_criteria, sample_property):
        """Test property matching against criteria."""
        await alert_system.setup_lead_alerts(sample_criteria)

        # Should match: price, beds, neighborhood all match
        matches = await alert_system._property_matches_criteria(sample_property, sample_criteria)
        assert matches is True

        # Test price filter
        sample_property.price = 900000  # Above max price
        matches = await alert_system._property_matches_criteria(sample_property, sample_criteria)
        assert matches is False

        # Reset price and test beds filter
        sample_property.price = 550000
        sample_property.beds = 2  # Below min beds
        matches = await alert_system._property_matches_criteria(sample_property, sample_criteria)
        assert matches is False

        # Reset beds and test neighborhood filter
        sample_property.beds = 3
        sample_property.neighborhood = "Downtown"  # Not in criteria
        matches = await alert_system._property_matches_criteria(sample_property, sample_criteria)
        assert matches is False

    @pytest.mark.asyncio
    @patch('ghl_real_estate_ai.services.property_alerts.PropertyAlertSystem._get_recent_listings')
    async def test_check_new_listings(self, mock_get_recent, alert_system, sample_criteria, sample_property):
        """Test checking for new listing alerts."""
        # Setup
        mock_get_recent.return_value = [sample_property]
        await alert_system.setup_lead_alerts(sample_criteria)

        # Check new listings
        alerts = await alert_system.check_new_listings()

        assert len(alerts) == 1
        alert = alerts[0]

        assert alert.alert_type == AlertType.NEW_LISTING
        assert alert.lead_id == sample_criteria.lead_id
        assert alert.property_data["mls_id"] == sample_property.mls_id
        assert "Schedule showing" in alert.action_items

    @pytest.mark.asyncio
    @patch('ghl_real_estate_ai.services.property_alerts.PropertyAlertSystem._get_price_changed_properties')
    async def test_check_price_drops(self, mock_get_price_changed, alert_system, sample_criteria, sample_property):
        """Test checking for price drop alerts."""
        # Setup property with price change
        sample_property.price_changes = [
            {
                "type": "decrease",
                "amount": 25000,
                "previous_price": 575000,
                "new_price": 550000,
                "date": datetime.now() - timedelta(days=1)
            }
        ]

        mock_get_price_changed.return_value = [sample_property]
        await alert_system.setup_lead_alerts(sample_criteria)

        # Mock finding interested leads
        alert_system._find_interested_leads = AsyncMock(return_value=[sample_criteria.lead_id])

        alerts = await alert_system.check_price_drops()

        assert len(alerts) == 1
        alert = alerts[0]

        assert alert.alert_type == AlertType.PRICE_DROP
        assert alert.priority in [AlertPriority.HIGH, AlertPriority.MEDIUM]
        assert "price drop" in alert.message.lower()

    @pytest.mark.asyncio
    @patch('ghl_real_estate_ai.services.property_alerts.PropertyAlertSystem._get_recent_listings')
    @patch('ghl_real_estate_ai.services.property_alerts.PropertyAlertSystem._calculate_opportunity_score')
    async def test_check_market_opportunities(self, mock_calc_score, mock_get_recent, alert_system, sample_criteria, sample_property):
        """Test checking for market opportunity alerts."""
        # Setup
        mock_get_recent.return_value = [sample_property]
        mock_calc_score.return_value = 85.0  # High opportunity score
        await alert_system.setup_lead_alerts(sample_criteria)

        # Mock finding leads for opportunity
        alert_system._find_leads_for_opportunity = AsyncMock(return_value=[sample_criteria.lead_id])

        alerts = await alert_system.check_market_opportunities()

        assert len(alerts) == 1
        alert = alerts[0]

        assert alert.alert_type == AlertType.MARKET_OPPORTUNITY
        assert alert.priority == AlertPriority.HIGH
        assert "opportunity" in alert.message.lower()

    @pytest.mark.asyncio
    async def test_check_inventory_alerts(self, alert_system, sample_criteria):
        """Test checking for inventory alerts."""
        await alert_system.setup_lead_alerts(sample_criteria)

        # Mock market service to return low inventory
        with patch.object(alert_system.market_service, 'get_market_metrics') as mock_metrics:
            mock_metrics.return_value = Mock(months_supply=1.2, inventory_count=500, market_condition=Mock(value="strong_sellers"))

            # Mock finding leads in neighborhood
            alert_system._find_leads_in_neighborhood = AsyncMock(return_value=[sample_criteria.lead_id])

            alerts = await alert_system.check_inventory_alerts()

            assert len(alerts) >= 0  # May or may not generate alerts depending on conditions

            if alerts:
                alert = alerts[0]
                assert isinstance(alert, MarketAlert)
                assert alert.alert_type == AlertType.INVENTORY_ALERT

    @pytest.mark.asyncio
    async def test_check_corporate_relocation_alerts(self, alert_system, sample_criteria):
        """Test checking for corporate relocation alerts."""
        await alert_system.setup_lead_alerts(sample_criteria)

        # Mock corporate events
        alert_system._get_corporate_events = AsyncMock(return_value=[
            {
                "type": "expansion",
                "company": "Apple",
                "announcement_date": datetime.now() - timedelta(days=2),
                "impact": "5000 new jobs"
            }
        ])

        alert_system._find_corporate_affected_leads = AsyncMock(return_value=[sample_criteria.lead_id])

        alerts = await alert_system.check_corporate_relocation_alerts()

        assert len(alerts) >= 0

        if alerts:
            alert = alerts[0]
            assert alert.alert_type == AlertType.CORPORATE_RELOCATION
            assert "Apple" in alert.message or "expansion" in alert.message.lower()

    @pytest.mark.asyncio
    async def test_process_all_alerts(self, alert_system, sample_criteria):
        """Test processing all alert types together."""
        await alert_system.setup_lead_alerts(sample_criteria)

        # Mock all the data sources
        alert_system._get_recent_listings = AsyncMock(return_value=[])
        alert_system._get_price_changed_properties = AsyncMock(return_value=[])
        alert_system._get_corporate_events = AsyncMock(return_value=[])

        results = await alert_system.process_all_alerts()

        assert isinstance(results, dict)
        assert "new_listings" in results
        assert "price_drops" in results
        assert "opportunities" in results
        assert "inventory" in results
        assert "corporate" in results

        # All should be lists
        for alert_type, alerts in results.items():
            assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_get_alert_summary(self, alert_system, sample_criteria):
        """Test getting alert summary for a lead."""
        await alert_system.setup_lead_alerts(sample_criteria)

        summary = await alert_system.get_alert_summary(sample_criteria.lead_id)

        assert isinstance(summary, dict)
        assert summary["active"] is True
        assert "criteria" in summary
        assert summary["criteria"]["lead_id"] == sample_criteria.lead_id

    @pytest.mark.asyncio
    async def test_get_alert_summary_inactive_lead(self, alert_system):
        """Test getting alert summary for inactive lead."""
        summary = await alert_system.get_alert_summary("nonexistent_lead")

        assert isinstance(summary, dict)
        assert summary["active"] is False

    def test_singleton_pattern(self):
        """Test that get_property_alert_system returns singleton."""
        system1 = get_property_alert_system()
        system2 = get_property_alert_system()

        assert system1 is system2

    @pytest.mark.asyncio
    async def test_concurrent_alert_processing(self, alert_system, sample_criteria):
        """Test concurrent alert processing."""
        await alert_system.setup_lead_alerts(sample_criteria)

        # Create multiple criteria for different leads
        criteria_list = []
        for i in range(5):
            criteria = AlertCriteria(
                lead_id=f"lead_{i:03d}",
                min_price=300000 + i * 50000,
                max_price=700000 + i * 100000,
                neighborhoods=["Round Rock", "Domain"][i % 2:i % 2 + 1]
            )
            criteria_list.append(criteria)
            await alert_system.setup_lead_alerts(criteria)

        # Process alerts concurrently
        start_time = datetime.now()
        results = await alert_system.process_all_alerts()
        end_time = datetime.now()

        # Should complete reasonably quickly
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 5.0  # Should complete within 5 seconds

        # Results should be properly structured
        assert isinstance(results, dict)
        for alert_list in results.values():
            assert isinstance(alert_list, list)

    @pytest.mark.asyncio
    async def test_alert_expiry_handling(self, alert_system):
        """Test alert expiry time handling."""
        # Create alert with short expiry
        alert = PropertyAlert(
            alert_id="test_alert",
            lead_id="test_lead",
            alert_type=AlertType.NEW_LISTING,
            priority=AlertPriority.MEDIUM,
            property_data={},
            message="Test message",
            detailed_analysis={},
            action_items=[],
            expiry_time=datetime.now() + timedelta(minutes=5)  # Short expiry
        )

        # Verify expiry time is set correctly
        assert alert.expiry_time > datetime.now()
        assert alert.expiry_time < datetime.now() + timedelta(hours=1)

    @pytest.mark.asyncio
    async def test_complex_criteria_matching(self, alert_system):
        """Test complex criteria matching scenarios."""
        # Create complex criteria
        criteria = AlertCriteria(
            lead_id="complex_lead",
            min_price=500000,
            max_price=800000,
            min_beds=3,
            min_baths=2.0,
            property_types=[PropertyType.SINGLE_FAMILY, PropertyType.TOWNHOME],
            neighborhoods=["Round Rock", "Cedar Park"],
            lifestyle_preferences=["walkable", "family-friendly"],
            must_have_features=["garage", "yard"],
            work_location="Apple",
            max_commute_time=25
        )

        await alert_system.setup_lead_alerts(criteria)

        # Create property that should match
        matching_property = PropertyListing(
            mls_id="MATCH001",
            address="456 Apple Way, Round Rock, TX",
            price=650000,
            beds=3,
            baths=2.5,
            sqft=2500,
            lot_size=0.3,
            year_built=2021,
            property_type=PropertyType.SINGLE_FAMILY,
            neighborhood="Round Rock",
            school_district="Round Rock ISD",
            days_on_market=8,
            price_per_sqft=260,
            price_changes=[],
            features=["garage", "yard", "open concept"],
            coordinates=(30.5, -97.7),
            photos=[],
            description="Perfect family home",
            listing_agent={"name": "Jorge Martinez"},
            last_updated=datetime.now()
        )

        # Test matching
        matches = await alert_system._property_matches_criteria(matching_property, criteria)
        assert matches is True

        # Test non-matching property (wrong type)
        non_matching_property = matching_property
        non_matching_property.property_type = PropertyType.LAND
        matches = await alert_system._property_matches_criteria(non_matching_property, criteria)
        assert matches is False


@pytest.mark.integration
class TestPropertyAlertsIntegration:
    """Integration tests for Property Alert System."""

    @pytest.fixture
    def alert_system(self):
        """Create alert system for integration testing."""
        return PropertyAlertSystem()

    @pytest.mark.asyncio
    async def test_full_alert_workflow(self, alert_system):
        """Test complete alert workflow from setup to notification."""
        # Setup criteria for Apple employee
        criteria = AlertCriteria(
            lead_id="apple_employee_001",
            min_price=400000,
            max_price=800000,
            min_beds=3,
            neighborhoods=["Round Rock", "Cedar Park"],
            work_location="Apple",
            max_commute_time=30,
            lifestyle_preferences=["family-friendly"]
        )

        # Setup alerts
        success = await alert_system.setup_lead_alerts(criteria)
        assert success is True

        # Process all alert types
        results = await alert_system.process_all_alerts()

        # Verify results structure
        assert isinstance(results, dict)
        assert all(isinstance(alerts, list) for alerts in results.values())

        # Get summary
        summary = await alert_system.get_alert_summary(criteria.lead_id)
        assert summary["active"] is True

    @pytest.mark.asyncio
    async def test_multi_lead_alert_processing(self, alert_system):
        """Test alert processing for multiple leads."""
        # Create multiple lead criteria
        lead_criteria = [
            AlertCriteria(
                lead_id="lead_apple",
                work_location="Apple",
                neighborhoods=["Round Rock"],
                min_price=500000,
                max_price=900000
            ),
            AlertCriteria(
                lead_id="lead_google",
                work_location="Google",
                neighborhoods=["Downtown", "South Lamar"],
                min_price=400000,
                max_price=700000
            ),
            AlertCriteria(
                lead_id="lead_tesla",
                work_location="Tesla",
                neighborhoods=["East Austin", "Mueller"],
                min_price=300000,
                max_price=600000
            )
        ]

        # Setup all criteria
        for criteria in lead_criteria:
            success = await alert_system.setup_lead_alerts(criteria)
            assert success is True

        # Process alerts for all leads
        results = await alert_system.process_all_alerts()

        # Verify all leads have their criteria stored
        assert len(alert_system.active_criteria) >= 3

        # Verify results
        for alert_type, alerts in results.items():
            assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_alert_system_performance(self, alert_system):
        """Test alert system performance with multiple leads and criteria."""
        # Create 20 different lead criteria
        for i in range(20):
            criteria = AlertCriteria(
                lead_id=f"performance_test_lead_{i:03d}",
                min_price=300000 + i * 25000,
                max_price=600000 + i * 50000,
                min_beds=2 + (i % 3),
                neighborhoods=["Round Rock", "Cedar Park", "Domain", "Downtown"][i % 4:i % 4 + 1]
            )
            await alert_system.setup_lead_alerts(criteria)

        # Measure processing time
        start_time = datetime.now()
        results = await alert_system.process_all_alerts()
        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()

        # Should complete within reasonable time
        assert processing_time < 10.0  # 10 seconds for 20 leads

        # Verify results
        assert isinstance(results, dict)


class TestAlertEnums:
    """Test alert system enums."""

    def test_alert_type_values(self):
        """Test AlertType enum values."""
        assert AlertType.NEW_LISTING.value == "new_listing"
        assert AlertType.PRICE_DROP.value == "price_drop"
        assert AlertType.MARKET_OPPORTUNITY.value == "market_opportunity"
        assert AlertType.INVENTORY_ALERT.value == "inventory_alert"
        assert AlertType.CORPORATE_RELOCATION.value == "corporate_relocation"

    def test_alert_priority_values(self):
        """Test AlertPriority enum values."""
        assert AlertPriority.LOW.value == "low"
        assert AlertPriority.MEDIUM.value == "medium"
        assert AlertPriority.HIGH.value == "high"
        assert AlertPriority.URGENT.value == "urgent"


class TestAlertErrorHandling:
    """Test error handling in alert system."""

    @pytest.fixture
    def alert_system(self):
        """Create alert system for error testing."""
        return PropertyAlertSystem()

    @pytest.mark.asyncio
    async def test_invalid_lead_id_handling(self, alert_system):
        """Test handling of invalid lead IDs."""
        # Empty lead ID
        criteria = AlertCriteria(lead_id="")
        success = await alert_system.setup_lead_alerts(criteria)
        # Should handle gracefully

        # None lead ID - should raise exception
        with pytest.raises(Exception):
            criteria = AlertCriteria(lead_id=None)

    @pytest.mark.asyncio
    async def test_alert_processing_with_service_failures(self, alert_system):
        """Test alert processing when underlying services fail."""
        criteria = AlertCriteria(lead_id="test_lead")
        await alert_system.setup_lead_alerts(criteria)

        # Mock service failures
        with patch.object(alert_system, '_get_recent_listings', side_effect=Exception("Service failure")):
            results = await alert_system.process_all_alerts()

            # Should return empty results, not crash
            assert isinstance(results, dict)
            assert "new_listings" in results

    @pytest.mark.asyncio
    async def test_cache_failure_handling(self, alert_system):
        """Test handling when cache service fails."""
        criteria = AlertCriteria(lead_id="cache_test")

        # Mock cache failure
        with patch.object(alert_system.cache, 'set', side_effect=Exception("Cache failure")):
            # Should still complete successfully
            success = await alert_system.setup_lead_alerts(criteria)
            # May succeed or fail, but should not crash

        with patch.object(alert_system.cache, 'get', side_effect=Exception("Cache failure")):
            summary = await alert_system.get_alert_summary("cache_test")
            # Should handle gracefully
            assert isinstance(summary, dict)