import pytest
pytestmark = pytest.mark.integration

"""
Tests for Corporate Relocation Service

Comprehensive test suite for Fortune 500 corporate relocation programs,
multi-city employee housing coordination, and volume pricing management.

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from ghl_real_estate_ai.services.corporate_relocation_service import (

    CorporateContract,
    CorporatePartnerTier,
    CorporateRelocationService,
    EmployeeLevel,
    MultiCityCoordination,
    RelocationRequest,
    RelocationStatus,
    get_corporate_relocation_service,
)


@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_claude_assistant():
    """Mock Claude assistant"""
    assistant = Mock()
    assistant.generate_welcome_message = AsyncMock(return_value="Welcome to our corporate relocation program!")
    return assistant


@pytest.fixture
def mock_national_registry():
    """Mock national market registry"""
    registry = Mock()
    registry.get_corporate_relocation_program = AsyncMock(
        return_value={
            "company_info": {"name": "Test Corp", "industry": "Technology"},
            "preferred_markets": ["denver", "seattle"],
            "relocation_program": {"annual_volume": 150, "average_budget": 75000},
        }
    )
    return registry


@pytest.fixture
def relocation_service(mock_cache_service, mock_claude_assistant, mock_national_registry):
    """Create relocation service with mocked dependencies"""
    with (
        patch(
            "ghl_real_estate_ai.services.corporate_relocation_service.get_cache_service",
            return_value=mock_cache_service,
        ),
        patch(
            "ghl_real_estate_ai.services.corporate_relocation_service.ClaudeAssistant",
            return_value=mock_claude_assistant,
        ),
        patch(
            "ghl_real_estate_ai.services.corporate_relocation_service.get_national_market_registry",
            return_value=mock_national_registry,
        ),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=False),
        patch("builtins.open", mock_open()),
    ):
        service = CorporateRelocationService()
        return service


@pytest.fixture
def sample_employee_details():
    """Sample employee details for testing"""
    return {
        "name": "John Smith",
        "email": "john.smith@company.com",
        "level": "vp_director",
        "current_location": "Rancho Cucamonga, CA",
        "family_size": 3,
    }


@pytest.fixture
def sample_relocation_requirements():
    """Sample relocation requirements for testing"""
    return {
        "target_market": "denver",
        "start_date": "2026-06-01",
        "timeline_requirement": "flexible",
        "budget_min": 500000,
        "budget_max": 800000,
        "special_requirements": ["spouse_career_assistance", "private_school_search"],
        "housing_preferences": {
            "property_type": "single_family",
            "bedrooms": 4,
            "school_rating_min": 8.5,
            "commute_max": 30,
        },
    }


class TestCorporateRelocationService:
    """Test suite for CorporateRelocationService class"""

    def test_initialization(self, relocation_service):
        """Test service initialization"""
        assert relocation_service.cache is not None
        assert relocation_service.claude_assistant is not None
        assert relocation_service.national_registry is not None
        assert isinstance(relocation_service.active_requests, dict)
        assert isinstance(relocation_service.corporate_contracts, dict)
        assert isinstance(relocation_service.multi_city_projects, dict)
        assert isinstance(relocation_service.service_tiers, dict)
        assert isinstance(relocation_service.pricing_structure, dict)

    def test_service_tiers_configuration(self, relocation_service):
        """Test service tiers are properly configured"""
        tiers = relocation_service.service_tiers

        # Verify all expected tiers exist
        expected_tiers = ["platinum_concierge", "gold_executive", "silver_professional", "bronze_standard"]
        for tier in expected_tiers:
            assert tier in tiers
            assert "features" in tiers[tier]
            assert "response_time_hours" in tiers[tier]
            assert "employee_levels" in tiers[tier]
            assert "base_fee" in tiers[tier]
            assert "commission_rate" in tiers[tier]

        # Verify response times are appropriate
        assert tiers["platinum_concierge"]["response_time_hours"] == 1
        assert tiers["gold_executive"]["response_time_hours"] == 4
        assert tiers["silver_professional"]["response_time_hours"] == 8
        assert tiers["bronze_standard"]["response_time_hours"] == 24

    def test_pricing_structure(self, relocation_service):
        """Test pricing structure configuration"""
        pricing = relocation_service.pricing_structure

        assert "base_relocation_fee" in pricing
        assert "volume_discounts" in pricing
        assert "rush_fees" in pricing
        assert "additional_services" in pricing

        # Verify volume discounts are progressive
        discounts = pricing["volume_discounts"]
        tier_discounts = [tier["discount"] for tier in discounts.values()]
        assert tier_discounts == sorted(tier_discounts)  # Should be ascending

    def test_determine_service_tier(self, relocation_service):
        """Test service tier determination based on employee level"""
        # Test C-suite gets platinum
        tier = relocation_service._determine_service_tier(EmployeeLevel.C_SUITE)
        assert tier == "platinum_concierge"

        # Test VP gets gold
        tier = relocation_service._determine_service_tier(EmployeeLevel.VP_DIRECTOR)
        assert tier == "gold_executive"

        # Test manager gets silver
        tier = relocation_service._determine_service_tier(EmployeeLevel.MANAGER)
        assert tier == "silver_professional"

        # Test IC gets bronze
        tier = relocation_service._determine_service_tier(EmployeeLevel.INDIVIDUAL_CONTRIBUTOR)
        assert tier == "bronze_standard"

    @pytest.mark.asyncio
    async def test_create_relocation_request(
        self, relocation_service, sample_employee_details, sample_relocation_requirements
    ):
        """Test creating a new relocation request"""
        company_name = "Test Corporation"

        with (
            patch.object(relocation_service, "_save_requests_data"),
            patch.object(relocation_service, "_save_contracts_data", create=True),
        ):
            request_id = await relocation_service.create_relocation_request(
                company_name, sample_employee_details, sample_relocation_requirements
            )

        # Verify request was created
        assert request_id is not None
        assert request_id.startswith("CR-")
        assert request_id in relocation_service.active_requests

        # Verify request details
        request = relocation_service.active_requests[request_id]
        assert request.company_name == company_name
        assert request.employee_name == sample_employee_details["name"]
        assert request.employee_email == sample_employee_details["email"]
        assert request.employee_level == EmployeeLevel.VP_DIRECTOR
        assert request.target_market == sample_relocation_requirements["target_market"]
        assert request.status == RelocationStatus.INITIATED
        assert request.relocation_package_tier == "gold_executive"  # VP level

    @pytest.mark.asyncio
    async def test_assign_relocation_specialist(self, relocation_service):
        """Test specialist assignment"""
        # Create a test request
        request = RelocationRequest(
            request_id="TEST-001",
            company_name="Test Corp",
            employee_name="Jane Doe",
            employee_email="jane@test.com",
            employee_level=EmployeeLevel.C_SUITE,
            source_location="Rancho Cucamonga",
            target_market="seattle",
            start_date=date(2026, 6, 1),
            timeline_requirement="flexible",
            budget_range=(800000, 1200000),
            family_size=2,
            special_requirements=[],
            housing_preferences={},
            relocation_package_tier="platinum_concierge",
            status=RelocationStatus.INITIATED,
            assigned_specialist=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completion_target=date(2026, 5, 1),
        )

        relocation_service.active_requests["TEST-001"] = request

        await relocation_service._assign_relocation_specialist("TEST-001")

        # Verify specialist was assigned
        updated_request = relocation_service.active_requests["TEST-001"]
        assert updated_request.assigned_specialist is not None
        assert "Senior Executive Specialist" in updated_request.assigned_specialist
        assert len(updated_request.notes) > 0
        assert updated_request.notes[-1]["type"] == "specialist_assignment"

    @pytest.mark.asyncio
    async def test_send_welcome_communication(self, relocation_service, mock_claude_assistant):
        """Test welcome communication generation"""
        # Create a test request
        request = RelocationRequest(
            request_id="TEST-002",
            company_name="Test Corp",
            employee_name="Bob Wilson",
            employee_email="bob@test.com",
            employee_level=EmployeeLevel.MANAGER,
            source_location="Houston",
            target_market="denver",
            start_date=date(2026, 7, 15),
            timeline_requirement="urgent",
            budget_range=(400000, 600000),
            family_size=4,
            special_requirements=["spouse_career_assistance"],
            housing_preferences={"bedrooms": 3},
            relocation_package_tier="silver_professional",
            status=RelocationStatus.INITIATED,
            assigned_specialist="Michael Chen (Executive Coordinator)",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completion_target=date(2026, 7, 1),
        )

        relocation_service.active_requests["TEST-002"] = request

        await relocation_service._send_welcome_communication("TEST-002")

        # Verify Claude was called
        mock_claude_assistant.generate_welcome_message.assert_called_once()

        # Verify communication note was added
        updated_request = relocation_service.active_requests["TEST-002"]
        assert len(updated_request.notes) > 0
        welcome_note = updated_request.notes[-1]
        assert welcome_note["type"] == "welcome_communication"
        assert "bob@test.com" in welcome_note["message"]

    @pytest.mark.asyncio
    async def test_get_relocation_status(self, relocation_service):
        """Test getting relocation status"""
        # Create a test request with some progress
        request = RelocationRequest(
            request_id="TEST-003",
            company_name="Test Corp",
            employee_name="Sarah Davis",
            employee_email="sarah@test.com",
            employee_level=EmployeeLevel.SENIOR_MANAGER,
            source_location="Dallas",
            target_market="phoenix",
            start_date=date(2026, 8, 1),
            timeline_requirement="flexible",
            budget_range=(500000, 750000),
            family_size=1,
            special_requirements=[],
            housing_preferences={},
            relocation_package_tier="gold_executive",
            status=RelocationStatus.MARKET_ANALYSIS,
            assigned_specialist="Jennifer Davis (Professional Coordinator)",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completion_target=date(2026, 7, 15),
            notes=[
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "status_update",
                    "message": "Market analysis completed",
                    "author": "System",
                }
            ],
        )

        relocation_service.active_requests["TEST-003"] = request

        status = await relocation_service.get_relocation_status("TEST-003")

        assert status is not None
        assert status["request_id"] == "TEST-003"
        assert status["status"] == RelocationStatus.MARKET_ANALYSIS.value
        assert status["progress_percentage"] == 30  # Based on status mapping
        assert "employee" in status
        assert "relocation_details" in status
        assert "service_details" in status
        assert "budget_information" in status
        assert "next_steps" in status

    def test_calculate_progress(self, relocation_service):
        """Test progress calculation"""
        # Test various status progress mappings
        test_cases = [
            (RelocationStatus.INITIATED, 5),
            (RelocationStatus.NEEDS_ASSESSMENT, 15),
            (RelocationStatus.MARKET_ANALYSIS, 30),
            (RelocationStatus.PROPERTY_SEARCH, 50),
            (RelocationStatus.VIEWING_SCHEDULED, 65),
            (RelocationStatus.OFFER_NEGOTIATION, 80),
            (RelocationStatus.CLOSING_PROCESS, 95),
            (RelocationStatus.COMPLETED, 100),
            (RelocationStatus.CANCELLED, 0),
        ]

        for status, expected_progress in test_cases:
            request = Mock()
            request.status = status
            progress = relocation_service._calculate_progress(request)
            assert progress == expected_progress

    def test_estimate_total_cost(self, relocation_service):
        """Test total cost estimation"""
        # Test normal timeline request
        normal_request = RelocationRequest(
            request_id="COST-001",
            company_name="Test Corp",
            employee_name="Cost Test",
            employee_email="cost@test.com",
            employee_level=EmployeeLevel.VP_DIRECTOR,
            source_location="Rancho Cucamonga",
            target_market="denver",
            start_date=date.today() + timedelta(days=90),  # Normal timeline
            timeline_requirement="flexible",
            budget_range=(500000, 800000),
            family_size=2,
            special_requirements=["spouse_career_assistance"],
            housing_preferences={},
            relocation_package_tier="gold_executive",
            status=RelocationStatus.INITIATED,
            assigned_specialist=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completion_target=date.today() + timedelta(days=60),
        )

        cost = relocation_service._estimate_total_cost(normal_request)
        expected_base = 12000  # Gold executive base fee
        expected_additional = 2500  # Spouse career assistance
        assert cost >= expected_base + expected_additional

        # Test urgent timeline (rush fee)
        urgent_request = RelocationRequest(
            request_id="COST-002",
            company_name="Test Corp",
            employee_name="Urgent Test",
            employee_email="urgent@test.com",
            employee_level=EmployeeLevel.C_SUITE,
            source_location="Houston",
            target_market="seattle",
            start_date=date.today() + timedelta(days=20),  # Urgent timeline
            timeline_requirement="urgent",
            budget_range=(800000, 1200000),
            family_size=3,
            special_requirements=[],
            housing_preferences={},
            relocation_package_tier="platinum_concierge",
            status=RelocationStatus.INITIATED,
            assigned_specialist=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completion_target=date.today() + timedelta(days=10),
        )

        urgent_cost = relocation_service._estimate_total_cost(urgent_request)
        platinum_base = 25000  # Platinum base fee
        rush_multiplier = 1.25  # 25% rush fee
        expected_urgent = platinum_base * rush_multiplier
        assert urgent_cost >= expected_urgent

    def test_generate_next_steps(self, relocation_service):
        """Test next steps generation"""
        test_cases = [
            RelocationStatus.INITIATED,
            RelocationStatus.NEEDS_ASSESSMENT,
            RelocationStatus.MARKET_ANALYSIS,
            RelocationStatus.PROPERTY_SEARCH,
            RelocationStatus.COMPLETED,
        ]

        for status in test_cases:
            request = Mock()
            request.status = status
            next_steps = relocation_service._generate_next_steps(request)

            assert isinstance(next_steps, list)
            assert len(next_steps) > 0
            assert all(isinstance(step, str) for step in next_steps)

    @pytest.mark.asyncio
    async def test_create_multi_city_coordination(self, relocation_service):
        """Test multi-city coordination project creation"""
        company_name = "Global Corp"
        project_details = {
            "project_name": "West Coast Expansion",
            "affected_markets": ["denver", "phoenix", "seattle"],
            "employee_count": 150,
            "coordination_type": "office_expansion",
            "timeline": {
                "project_start": "2026-03-01",
                "denver_completion": "2026-06-01",
                "phoenix_completion": "2026-07-01",
                "seattle_completion": "2026-08-01",
            },
            "budget_total": 15000000.0,
            "project_manager": "Alice Johnson",
        }

        with patch.object(relocation_service, "_save_coordination_data"):
            coordination_id = await relocation_service.create_multi_city_coordination(company_name, project_details)

        # Verify coordination was created
        assert coordination_id is not None
        assert coordination_id.startswith("MCP-")
        assert coordination_id in relocation_service.multi_city_projects

        # Verify coordination details
        coordination = relocation_service.multi_city_projects[coordination_id]
        assert coordination.company_name == company_name
        assert coordination.project_name == project_details["project_name"]
        assert coordination.affected_markets == project_details["affected_markets"]
        assert coordination.employee_count == project_details["employee_count"]
        assert coordination.budget_total == project_details["budget_total"]
        assert coordination.status == "initiated"

    @pytest.mark.asyncio
    async def test_get_corporate_dashboard(self, relocation_service):
        """Test corporate dashboard generation"""
        company_name = "Dashboard Corp"

        # Create sample data
        request1 = RelocationRequest(
            request_id="DASH-001",
            company_name=company_name,
            employee_name="Employee 1",
            employee_email="emp1@dash.com",
            employee_level=EmployeeLevel.MANAGER,
            source_location="Rancho Cucamonga",
            target_market="denver",
            start_date=date.today() + timedelta(days=60),
            timeline_requirement="flexible",
            budget_range=(400000, 600000),
            family_size=2,
            special_requirements=[],
            housing_preferences={},
            relocation_package_tier="silver_professional",
            status=RelocationStatus.PROPERTY_SEARCH,
            assigned_specialist="Test Specialist",
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now(),
            completion_target=date.today() + timedelta(days=30),
        )

        request2 = RelocationRequest(
            request_id="DASH-002",
            company_name=company_name,
            employee_name="Employee 2",
            employee_email="emp2@dash.com",
            employee_level=EmployeeLevel.VP_DIRECTOR,
            source_location="Houston",
            target_market="seattle",
            start_date=date.today() - timedelta(days=90),
            timeline_requirement="completed",
            budget_range=(600000, 900000),
            family_size=3,
            special_requirements=[],
            housing_preferences={},
            relocation_package_tier="gold_executive",
            status=RelocationStatus.COMPLETED,
            assigned_specialist="Test Specialist",
            created_at=datetime.now() - timedelta(days=120),
            updated_at=datetime.now() - timedelta(days=1),
            completion_target=date.today() - timedelta(days=90),
        )

        relocation_service.active_requests["DASH-001"] = request1
        relocation_service.active_requests["DASH-002"] = request2

        dashboard = await relocation_service.get_corporate_dashboard(company_name)

        assert "company_name" in dashboard
        assert "contract_details" in dashboard
        assert "relocation_metrics" in dashboard
        assert "active_requests" in dashboard
        assert "market_utilization" in dashboard
        assert "cost_summary" in dashboard

        metrics = dashboard["relocation_metrics"]
        assert metrics["total_relocations"] == 2
        assert metrics["completed_relocations"] == 1
        assert metrics["active_relocations"] == 1
        assert metrics["success_rate"] == 50.0

        # Verify active requests don't include completed ones
        active_requests = dashboard["active_requests"]
        assert len(active_requests) == 1
        assert active_requests[0]["request_id"] == "DASH-001"

    def test_calculate_market_utilization(self, relocation_service):
        """Test market utilization calculation"""
        requests = [
            Mock(target_market="denver"),
            Mock(target_market="seattle"),
            Mock(target_market="denver"),
            Mock(target_market="phoenix"),
            Mock(target_market="denver"),
        ]

        utilization = relocation_service._calculate_market_utilization(requests)

        assert utilization["denver"] == 3
        assert utilization["seattle"] == 1
        assert utilization["phoenix"] == 1

    def test_health_check(self, relocation_service):
        """Test service health check"""
        health = relocation_service.health_check()

        assert "status" in health
        assert "service" in health
        assert "metrics" in health
        assert "data_files" in health
        assert "last_check" in health

        assert health["service"] == "CorporateRelocationService"
        assert health["status"] == "healthy"
        assert isinstance(health["metrics"], dict)

    def test_singleton_pattern(self):
        """Test singleton pattern for global service instance"""
        with (
            patch("ghl_real_estate_ai.services.corporate_relocation_service.get_cache_service"),
            patch("ghl_real_estate_ai.services.corporate_relocation_service.ClaudeAssistant"),
            patch("ghl_real_estate_ai.services.corporate_relocation_service.get_national_market_registry"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", mock_open()),
        ):
            service1 = get_corporate_relocation_service()
            service2 = get_corporate_relocation_service()

            assert service1 is service2

    def test_find_corporate_contract(self, relocation_service):
        """Test finding corporate contracts"""
        # Create test contract
        test_contract = CorporateContract(
            contract_id="CONTRACT-001",
            company_name="Test Corporation",
            partnership_tier=CorporatePartnerTier.GOLD,
            annual_volume_commitment=100,
            volume_discount_percentage=0.10,
            service_level_agreement={},
            pricing_structure={},
            contract_start_date=date.today(),
            contract_end_date=date.today() + timedelta(days=365),
            auto_renewal=True,
            dedicated_specialist="Senior Coordinator",
            billing_contact={},
            performance_metrics={},
            last_review_date=datetime.now(),
        )

        relocation_service.corporate_contracts["CONTRACT-001"] = test_contract

        # Test finding by exact name
        found_contract = relocation_service._find_corporate_contract("Test Corporation")
        assert found_contract is not None
        assert found_contract.company_name == "Test Corporation"

        # Test case insensitive search
        found_contract = relocation_service._find_corporate_contract("test corporation")
        assert found_contract is not None

        # Test not found
        not_found = relocation_service._find_corporate_contract("Nonexistent Corp")
        assert not_found is None


@pytest.mark.asyncio
async def test_data_persistence():
    """Test data persistence and loading"""
    with (
        patch("ghl_real_estate_ai.services.corporate_relocation_service.get_cache_service"),
        patch("ghl_real_estate_ai.services.corporate_relocation_service.ClaudeAssistant"),
        patch("ghl_real_estate_ai.services.corporate_relocation_service.get_national_market_registry"),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        # Test that service attempts to load existing data
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.load", return_value={}):
                service = CorporateRelocationService()
                assert mock_file.called  # Verify files were attempted to be opened


if __name__ == "__main__":
    pytest.main([__file__])