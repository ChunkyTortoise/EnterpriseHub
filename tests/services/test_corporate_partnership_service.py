"""
Test Suite for Corporate Partnership Service

Comprehensive tests for Fortune 500 corporate partnership functionality
including partnership creation, relocation management, and analytics.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from ghl_real_estate_ai.services.corporate_partnership_service import (
    CorporatePartnershipService,
    CorporatePartnershipError,
    PartnershipTier
)


@pytest.fixture
def partnership_service():
    """Fixture for CorporatePartnershipService instance."""
    return CorporatePartnershipService()


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock()
    mock_cache.set = AsyncMock()
    mock_cache.delete = AsyncMock()
    return mock_cache


@pytest.fixture
def valid_company_data():
    """Valid company data for partnership creation."""
    return {
        "company_name": "TechCorp Industries",
        "contact_email": "partnerships@techcorp.com",
        "contact_name": "Sarah Johnson",
        "company_size": "Enterprise",
        "industry": "Technology",
        "headquarters_location": "San Francisco, CA",
        "expected_volume": 250,
        "preferred_tier": "gold"
    }


@pytest.fixture
def valid_relocation_batch():
    """Valid relocation batch for testing."""
    return [
        {
            "employee_email": "john.doe@techcorp.com",
            "employee_name": "John Doe",
            "destination_city": "Austin",
            "destination_state": "TX",
            "housing_budget": 3500.00,
            "preferred_housing_type": "apartment",
            "start_date": datetime.now(timezone.utc) + timedelta(days=30)
        },
        {
            "employee_email": "jane.smith@techcorp.com",
            "employee_name": "Jane Smith",
            "destination_city": "Denver",
            "destination_state": "CO",
            "housing_budget": 4000.00,
            "preferred_housing_type": "house",
            "start_date": datetime.now(timezone.utc) + timedelta(days=45)
        }
    ]


class TestCorporatePartnershipService:
    """Test suite for CorporatePartnershipService."""

    @pytest.mark.asyncio
    async def test_create_corporate_partnership_success(self, partnership_service, mock_cache_service, valid_company_data):
        """Test successful corporate partnership creation."""
        # Mock cache service
        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            # Mock setup fee invoice creation
            partnership_service._create_setup_fee_invoice = AsyncMock(return_value={
                "invoice_id": "inv_123",
                "amount": Decimal("15000.00")
            })

            # Mock partnership proposal sending
            partnership_service._send_partnership_proposal = AsyncMock()

            result = await partnership_service.create_corporate_partnership(valid_company_data)

            # Assertions
            assert result["success"] is True
            assert "partnership_id" in result
            assert result["partnership_data"]["company_name"] == "TechCorp Industries"
            assert result["partnership_data"]["tier"] == "gold"
            assert result["partnership_data"]["expected_annual_volume"] == 250
            assert result["partnership_data"]["status"] == "pending_approval"

            # Verify cache was called
            mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_partnership_missing_required_fields(self, partnership_service):
        """Test partnership creation with missing required fields."""
        invalid_data = {
            "company_name": "TechCorp",
            # Missing required fields
        }

        with pytest.raises(CorporatePartnershipError) as exc_info:
            await partnership_service.create_corporate_partnership(invalid_data)

        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELDS"
        assert "contact_email" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_partnership_volume_below_minimum(self, partnership_service, valid_company_data):
        """Test partnership creation with volume below minimum threshold."""
        valid_company_data["expected_volume"] = 5  # Below minimum of 10

        with pytest.raises(CorporatePartnershipError) as exc_info:
            await partnership_service.create_corporate_partnership(valid_company_data)

        assert exc_info.value.error_code == "VOLUME_BELOW_MINIMUM"

    @pytest.mark.asyncio
    async def test_get_partnership_existing(self, partnership_service, mock_cache_service):
        """Test retrieving existing partnership."""
        partnership_id = "partnership_123"
        expected_data = {
            "partnership_id": partnership_id,
            "company_name": "TechCorp",
            "status": "active",
            "total_relocations": 50,
            "total_revenue": Decimal("75000.00")
        }

        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            # Mock cache returning partnership data
            mock_cache_service.get.return_value = expected_data

            # Mock metrics
            partnership_service._get_partnership_metrics = AsyncMock(return_value={
                "active_relocations": 5,
                "completed_relocations": 45
            })

            result = await partnership_service.get_partnership(partnership_id)

            assert result is not None
            assert result["partnership_id"] == partnership_id
            assert result["company_name"] == "TechCorp"
            assert "metrics" in result

    @pytest.mark.asyncio
    async def test_get_partnership_not_found(self, partnership_service, mock_cache_service):
        """Test retrieving non-existent partnership."""
        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            mock_cache_service.get.return_value = None

            result = await partnership_service.get_partnership("nonexistent_id")
            assert result is None

    @pytest.mark.asyncio
    async def test_approve_partnership_success(self, partnership_service, mock_cache_service):
        """Test successful partnership approval."""
        partnership_id = "partnership_123"
        partnership_data = {
            "partnership_id": partnership_id,
            "company_name": "TechCorp",
            "tier": "gold",
            "tier_config": PartnershipTier.GOLD,
            "status": "pending_approval"
        }

        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            # Mock get_partnership
            partnership_service.get_partnership = AsyncMock(return_value=partnership_data)

            # Mock enterprise subscription creation
            partnership_service._create_enterprise_subscription = AsyncMock(return_value={"id": "sub_123"})

            # Mock custom integration setup
            partnership_service._initialize_custom_integration = AsyncMock(return_value={"status": "pending"})

            # Mock notification sending
            partnership_service._send_partnership_activation_notice = AsyncMock()

            result = await partnership_service.approve_partnership(
                partnership_id, "manager@company.com", 24
            )

            assert result["success"] is True
            assert result["partnership_id"] == partnership_id
            assert result["status"] == "active"
            assert result["enterprise_features_enabled"] is True

    @pytest.mark.asyncio
    async def test_approve_partnership_not_found(self, partnership_service):
        """Test approving non-existent partnership."""
        with patch.object(partnership_service, 'get_partnership', AsyncMock(return_value=None)):
            with pytest.raises(CorporatePartnershipError) as exc_info:
                await partnership_service.approve_partnership("nonexistent", "manager@company.com")

            assert exc_info.value.error_code == "PARTNERSHIP_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_process_bulk_relocation_success(self, partnership_service, mock_cache_service, valid_relocation_batch):
        """Test successful bulk relocation processing."""
        partnership_id = "partnership_123"
        active_partnership = {
            "partnership_id": partnership_id,
            "status": "active",
            "company_name": "TechCorp"
        }

        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            # Mock get_partnership
            partnership_service.get_partnership = AsyncMock(return_value=active_partnership)

            # Mock single relocation processing
            partnership_service._process_single_relocation = AsyncMock(side_effect=[
                {
                    "relocation_index": 0,
                    "relocation_id": "rel_1",
                    "employee_email": "john.doe@techcorp.com",
                    "status": "success",
                    "estimated_revenue": Decimal("1500.00")
                },
                {
                    "relocation_index": 1,
                    "relocation_id": "rel_2",
                    "employee_email": "jane.smith@techcorp.com",
                    "status": "success",
                    "estimated_revenue": Decimal("1500.00")
                }
            ])

            # Mock metrics update
            partnership_service._update_partnership_volume_metrics = AsyncMock()

            result = await partnership_service.process_bulk_relocation_request(
                partnership_id, valid_relocation_batch
            )

            assert result["success"] is True
            assert "batch_id" in result
            assert result["summary"]["total_requests"] == 2
            assert result["summary"]["successful_requests"] == 2
            assert result["summary"]["total_estimated_revenue"] == Decimal("3000.00")

    @pytest.mark.asyncio
    async def test_process_bulk_relocation_partnership_not_active(self, partnership_service):
        """Test bulk relocation with inactive partnership."""
        partnership_id = "partnership_123"
        inactive_partnership = {
            "partnership_id": partnership_id,
            "status": "pending_approval"
        }

        with patch.object(partnership_service, 'get_partnership', AsyncMock(return_value=inactive_partnership)):
            with pytest.raises(CorporatePartnershipError) as exc_info:
                await partnership_service.process_bulk_relocation_request(
                    partnership_id, [{"employee_email": "test@company.com"}]
                )

            assert exc_info.value.error_code == "PARTNERSHIP_NOT_ACTIVE"

    @pytest.mark.asyncio
    async def test_process_bulk_relocation_batch_size_exceeded(self, partnership_service):
        """Test bulk relocation with oversized batch."""
        partnership_id = "partnership_123"
        active_partnership = {
            "partnership_id": partnership_id,
            "status": "active"
        }

        # Create oversized batch (101 relocations)
        oversized_batch = [{"employee_email": f"employee{i}@company.com"} for i in range(101)]

        with patch.object(partnership_service, 'get_partnership', AsyncMock(return_value=active_partnership)):
            with pytest.raises(CorporatePartnershipError) as exc_info:
                await partnership_service.process_bulk_relocation_request(
                    partnership_id, oversized_batch
                )

            assert exc_info.value.error_code == "BATCH_SIZE_EXCEEDED"

    @pytest.mark.asyncio
    async def test_track_relocation_progress_found(self, partnership_service, mock_cache_service):
        """Test tracking existing relocation progress."""
        partnership_id = "partnership_123"
        employee_email = "john.doe@company.com"

        relocation_data = {
            "relocation_id": "rel_123",
            "employee_email": employee_email,
            "status": "in_progress",
            "destination_city": "Austin"
        }

        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            mock_cache_service.get.return_value = relocation_data

            # Mock real-time status
            partnership_service._get_realtime_relocation_status = AsyncMock(return_value={
                "status": "property_search",
                "completion_percentage": 60
            })

            # Mock progress calculation
            partnership_service._calculate_relocation_progress = MagicMock(return_value=60)
            partnership_service._estimate_relocation_completion = MagicMock(
                return_value=datetime.now(timezone.utc) + timedelta(days=20)
            )

            result = await partnership_service.track_relocation_progress(
                partnership_id, employee_email
            )

            assert result["found"] is True
            assert result["relocation_data"]["relocation_id"] == "rel_123"
            assert result["progress_percentage"] == 60

    @pytest.mark.asyncio
    async def test_track_relocation_progress_not_found(self, partnership_service, mock_cache_service):
        """Test tracking non-existent relocation progress."""
        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            mock_cache_service.get.return_value = None

            result = await partnership_service.track_relocation_progress(
                "partnership_123", "nonexistent@company.com"
            )

            assert result["found"] is False

    @pytest.mark.asyncio
    async def test_calculate_partnership_revenue_success(self, partnership_service, mock_cache_service):
        """Test successful partnership revenue calculation."""
        partnership_id = "partnership_123"
        partnership_data = {
            "partnership_id": partnership_id,
            "tier": "gold",
            "tier_config": PartnershipTier.GOLD
        }

        period_start = datetime.now(timezone.utc) - timedelta(days=30)
        period_end = datetime.now(timezone.utc)

        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            # Mock get_partnership
            partnership_service.get_partnership = AsyncMock(return_value=partnership_data)

            # Mock metrics
            partnership_service._get_partnership_period_metrics = AsyncMock(return_value={
                "total_relocations": 25,
                "avg_transaction_value": Decimal("1500.00")
            })

            # Mock volume discount calculation
            partnership_service._calculate_volume_discount = MagicMock(return_value=0.25)

            # Mock additional fees
            partnership_service._calculate_additional_fees = AsyncMock(return_value=Decimal("2500.00"))

            result = await partnership_service.calculate_partnership_revenue(
                partnership_id, period_start, period_end
            )

            assert result["partnership_id"] == partnership_id
            assert "total_revenue" in result
            assert "relocation_count" in result
            assert result["relocation_count"] == 25
            assert isinstance(result["total_revenue"], Decimal)

    @pytest.mark.asyncio
    async def test_calculate_partnership_revenue_not_found(self, partnership_service):
        """Test revenue calculation for non-existent partnership."""
        period_start = datetime.now(timezone.utc) - timedelta(days=30)
        period_end = datetime.now(timezone.utc)

        with patch.object(partnership_service, 'get_partnership', AsyncMock(return_value=None)):
            with pytest.raises(CorporatePartnershipError) as exc_info:
                await partnership_service.calculate_partnership_revenue(
                    "nonexistent", period_start, period_end
                )

            assert exc_info.value.error_code == "PARTNERSHIP_NOT_FOUND"

    def test_determine_partnership_tier_volume_based(self, partnership_service):
        """Test partnership tier determination based on volume."""
        # Test platinum tier (500+ volume)
        assert partnership_service._determine_partnership_tier(750) == "platinum"

        # Test gold tier (200-499 volume)
        assert partnership_service._determine_partnership_tier(300) == "gold"

        # Test silver tier (50-199 volume)
        assert partnership_service._determine_partnership_tier(100) == "silver"

        # Test volume below minimum
        with pytest.raises(CorporatePartnershipError) as exc_info:
            partnership_service._determine_partnership_tier(25)
        assert exc_info.value.error_code == "VOLUME_BELOW_MINIMUM"

    def test_determine_partnership_tier_preferred_valid(self, partnership_service):
        """Test partnership tier with valid preferred tier."""
        # Valid preferred tier with sufficient volume
        assert partnership_service._determine_partnership_tier(600, "platinum") == "platinum"

        # Invalid preferred tier due to insufficient volume - falls back to volume-based tier
        assert partnership_service._determine_partnership_tier(150, "platinum") == "silver"

    @pytest.mark.asyncio
    async def test_calculate_partnership_pricing(self, partnership_service):
        """Test partnership pricing calculation."""
        volume = 200
        tier_config = PartnershipTier.GOLD

        pricing = await partnership_service._calculate_partnership_pricing(volume, tier_config)

        assert "base_rate_per_relocation" in pricing
        assert "volume_discount_percentage" in pricing
        assert "discounted_rate_per_relocation" in pricing
        assert "estimated_annual_revenue" in pricing
        assert pricing["estimated_annual_revenue"] > 0

    @pytest.mark.asyncio
    async def test_process_single_relocation_success(self, partnership_service, mock_cache_service):
        """Test successful single relocation processing."""
        partnership_id = "partnership_123"
        relocation_request = {
            "employee_email": "john.doe@company.com",
            "employee_name": "John Doe",
            "destination_city": "Austin",
            "destination_state": "TX",
            "housing_budget": 3500.00,
            "start_date": datetime.now(timezone.utc) + timedelta(days=30)
        }

        with patch.object(partnership_service, 'cache_service', mock_cache_service):
            result = await partnership_service._process_single_relocation(
                partnership_id, relocation_request, "batch_123", 0
            )

            assert result["status"] == "success"
            assert result["employee_email"] == "john.doe@company.com"
            assert "relocation_id" in result
            assert result["estimated_revenue"] == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_process_single_relocation_missing_fields(self, partnership_service):
        """Test single relocation processing with missing required fields."""
        partnership_id = "partnership_123"
        invalid_request = {
            "employee_email": "john.doe@company.com"
            # Missing required fields
        }

        with pytest.raises(ValueError) as exc_info:
            await partnership_service._process_single_relocation(
                partnership_id, invalid_request, "batch_123", 0
            )

        assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_partnership_roi_report_success(self, partnership_service):
        """Test successful ROI report generation."""
        partnership_id = "partnership_123"
        partnership_data = {
            "partnership_id": partnership_id,
            "company_name": "TechCorp",
            "tier": "gold",
            "contract_start_date": datetime.now(timezone.utc) - timedelta(days=90)
        }

        with patch.object(partnership_service, 'get_partnership', AsyncMock(return_value=partnership_data)):
            # Mock revenue analysis
            partnership_service.calculate_partnership_revenue = AsyncMock(return_value={
                "total_revenue": Decimal("150000.00"),
                "relocation_count": 100
            })

            # Mock cost analysis
            partnership_service._calculate_partnership_costs = AsyncMock(return_value={
                "total_costs": Decimal("100000.00")
            })

            # Mock benchmarks
            partnership_service._get_partnership_benchmarks = AsyncMock(return_value={
                "avg_roi": 35.0
            })

            # Mock recommendations
            partnership_service._generate_partnership_recommendations = AsyncMock(return_value=[
                "Consider tier upgrade for better margins"
            ])

            result = await partnership_service.generate_partnership_roi_report(partnership_id)

            assert result["partnership_id"] == partnership_id
            assert result["company_name"] == "TechCorp"
            assert "financial_summary" in result
            assert result["financial_summary"]["roi_percentage"] == 50.0  # (150k - 100k) / 100k * 100
            assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_generate_roi_report_not_activated(self, partnership_service):
        """Test ROI report generation for non-activated partnership."""
        partnership_id = "partnership_123"
        partnership_data = {
            "partnership_id": partnership_id,
            "contract_start_date": None  # Not activated
        }

        with patch.object(partnership_service, 'get_partnership', AsyncMock(return_value=partnership_data)):
            with pytest.raises(CorporatePartnershipError) as exc_info:
                await partnership_service.generate_partnership_roi_report(partnership_id)

            assert exc_info.value.error_code == "PARTNERSHIP_NOT_ACTIVATED"


class TestPartnershipTierConfiguration:
    """Test partnership tier configurations."""

    def test_silver_tier_configuration(self):
        """Test silver tier configuration values."""
        silver_config = PartnershipTier.SILVER

        assert silver_config["name"] == "Silver Partnership"
        assert silver_config["minimum_volume"] == 50
        assert silver_config["volume_discount"] == 0.15
        assert silver_config["revenue_share"] == Decimal("0.25")
        assert silver_config["dedicated_support"] is True

    def test_gold_tier_configuration(self):
        """Test gold tier configuration values."""
        gold_config = PartnershipTier.GOLD

        assert gold_config["name"] == "Gold Partnership"
        assert gold_config["minimum_volume"] == 200
        assert gold_config["volume_discount"] == 0.25
        assert gold_config["revenue_share"] == Decimal("0.35")
        assert gold_config["custom_integration"] is True
        assert gold_config["white_label"] is True

    def test_platinum_tier_configuration(self):
        """Test platinum tier configuration values."""
        platinum_config = PartnershipTier.PLATINUM

        assert platinum_config["name"] == "Platinum Partnership"
        assert platinum_config["minimum_volume"] == 500
        assert platinum_config["volume_discount"] == 0.40
        assert platinum_config["revenue_share"] == Decimal("0.50")
        assert platinum_config["setup_fee"] == Decimal("25000.00")


@pytest.mark.asyncio
async def test_service_initialization():
    """Test proper service initialization."""
    service = CorporatePartnershipService()

    assert service.cache_service is not None
    assert service.billing_service is not None
    assert service.subscription_manager is not None
    assert "silver" in service.partnership_tiers
    assert "gold" in service.partnership_tiers
    assert "platinum" in service.partnership_tiers


# Integration tests (would require actual services in full integration test environment)
class TestPartnershipServiceIntegration:
    """Integration tests for partnership service."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_partnership_flow(self):
        """Test complete partnership creation and management flow."""
        # This would be implemented in a full integration test environment
        # with actual cache service, billing service, and database connections
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_bulk_relocation_performance(self):
        """Test bulk relocation processing performance."""
        # Performance test for processing large batches of relocations
        pass