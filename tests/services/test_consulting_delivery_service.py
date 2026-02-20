import pytest

pytestmark = pytest.mark.integration

"""
Test suite for Consulting Delivery Service.

Comprehensive testing for high-ticket consulting engagement management
supporting $25K-$100K project delivery.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

try:
    from ghl_real_estate_ai.services.consulting_delivery_service import (
        ConsultingDeliveryService,
        ConsultingEngagement,
        Deliverable,
        DeliverableStatus,
        EngagementStatus,
        EngagementTier,
        ROIMetrics,
        Stakeholder,
        StakeholderRole,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestConsultingDeliveryService:
    """Test suite for ConsultingDeliveryService."""

    @pytest.fixture
    def temp_service(self):
        """Create service with temporary storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ConsultingDeliveryService()
            # Override directories to use temp directory
            service.engagements_dir = Path(temp_dir) / "engagements"
            service.templates_dir = Path(temp_dir) / "templates"
            service.metrics_dir = Path(temp_dir) / "metrics"

            # Create directories
            service.engagements_dir.mkdir(parents=True, exist_ok=True)
            service.templates_dir.mkdir(parents=True, exist_ok=True)
            service.metrics_dir.mkdir(parents=True, exist_ok=True)

            yield service

    @pytest.fixture
    def sample_stakeholder(self):
        """Sample stakeholder for testing."""
        return Stakeholder(
            stakeholder_id="stake_001",
            name="John Smith",
            email="john.smith@example.com",
            role=StakeholderRole.EXECUTIVE_SPONSOR,
            department="Executive",
            influence_level=9,
            engagement_preference="email",
            availability={"monday": "9am-5pm", "tuesday": "9am-5pm"},
            decision_authority=["budget", "strategic"],
            notes="Primary decision maker",
        )

    @pytest.fixture
    def sample_deliverable(self):
        """Sample deliverable for testing."""
        return Deliverable(
            deliverable_id="del_test_01",
            name="AI Strategy Assessment",
            description="Comprehensive analysis of AI opportunities",
            category="strategic",
            estimated_hours=16,
            acceptance_criteria=["Current state analysis completed", "Opportunity matrix delivered"],
            client_value="Strategic clarity on $500K+ opportunities",
        )

    @pytest.fixture
    def sample_roi_metrics(self):
        """Sample ROI metrics for testing."""
        return ROIMetrics(
            engagement_id="test_engagement",
            measurement_date=datetime.utcnow().isoformat(),
            monthly_revenue_increase=125000,
            conversion_rate_improvement=25.0,
            hours_saved_per_week=45.5,
            customer_satisfaction_score=9.2,
            total_roi_percentage=284.5,
            payback_period_months=4.2,
        )

    @pytest.mark.asyncio
    async def test_create_engagement_accelerator(self, temp_service):
        """Test creating an Accelerator tier engagement."""
        engagement_id = await temp_service.create_engagement(
            client_name="John Doe",
            client_organization="Test Realty",
            tier=EngagementTier.ACCELERATOR,
            contract_value=30000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Sarah Johnson",
        )

        assert engagement_id.startswith("eng_accelerator_")
        assert len(engagement_id) > 20

        # Verify engagement was saved
        engagement = await temp_service.get_engagement(engagement_id)
        assert engagement is not None
        assert engagement.client_name == "John Doe"
        assert engagement.tier == EngagementTier.ACCELERATOR
        assert engagement.contract_value == 30000
        assert engagement.status == EngagementStatus.CONTRACTED

    @pytest.mark.asyncio
    async def test_create_engagement_platform(self, temp_service):
        """Test creating a Platform tier engagement."""
        engagement_id = await temp_service.create_engagement(
            client_name="Jane Smith",
            client_organization="Platform Corp",
            tier=EngagementTier.PLATFORM,
            contract_value=62500,
            start_date="2024-02-01T09:00:00",
            lead_consultant="Mike Wilson",
        )

        engagement = await temp_service.get_engagement(engagement_id)
        assert engagement.tier == EngagementTier.PLATFORM
        assert engagement.contract_value == 62500

        # Check that deliverables were loaded from template
        assert len(engagement.deliverables) > 0

        # Check payment schedule for Platform tier
        assert len(engagement.payment_schedule) == 4  # Platform has 4 milestones
        assert sum(p["amount"] for p in engagement.payment_schedule) == 62500

    @pytest.mark.asyncio
    async def test_create_engagement_innovation(self, temp_service):
        """Test creating an Innovation tier engagement."""
        engagement_id = await temp_service.create_engagement(
            client_name="Bob Johnson",
            client_organization="Innovation Inc",
            tier=EngagementTier.INNOVATION,
            contract_value=87500,
            start_date="2024-03-01T08:00:00",
            lead_consultant="Alice Brown",
        )

        engagement = await temp_service.get_engagement(engagement_id)
        assert engagement.tier == EngagementTier.INNOVATION
        assert engagement.contract_value == 87500

        # Check payment schedule for Innovation tier
        assert len(engagement.payment_schedule) == 5  # Innovation has 5 milestones

        # Check planned end date calculation (14 weeks for Innovation)
        start_date = datetime.fromisoformat(engagement.start_date)
        planned_end = datetime.fromisoformat(engagement.planned_end_date)
        weeks_diff = (planned_end - start_date).days / 7
        assert 13 <= weeks_diff <= 15  # Approximately 14 weeks

    @pytest.mark.asyncio
    async def test_get_nonexistent_engagement(self, temp_service):
        """Test retrieving non-existent engagement."""
        result = await temp_service.get_engagement("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_engagement_status(self, temp_service):
        """Test updating engagement status."""
        # Create engagement first
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.ACCELERATOR,
            contract_value=30000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        # Update status
        success = await temp_service.update_engagement_status(
            engagement_id, EngagementStatus.DISCOVERY, "Discovery phase initiated"
        )

        assert success is True

        # Verify update
        engagement = await temp_service.get_engagement(engagement_id)
        assert engagement.status == EngagementStatus.DISCOVERY
        assert len(engagement.communication_log) > 0
        assert "Discovery phase initiated" in engagement.communication_log[-1]["message"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_engagement_status(self, temp_service):
        """Test updating status of non-existent engagement."""
        success = await temp_service.update_engagement_status("nonexistent_id", EngagementStatus.DISCOVERY)

        assert success is False

    @pytest.mark.asyncio
    async def test_add_stakeholder(self, temp_service, sample_stakeholder):
        """Test adding stakeholder to engagement."""
        # Create engagement first
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.PLATFORM,
            contract_value=60000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        # Add stakeholder
        success = await temp_service.add_stakeholder(engagement_id, sample_stakeholder)
        assert success is True

        # Verify stakeholder was added
        engagement = await temp_service.get_engagement(engagement_id)
        assert len(engagement.stakeholders) == 1
        assert engagement.stakeholders[0].name == "John Smith"
        assert engagement.stakeholders[0].role == StakeholderRole.EXECUTIVE_SPONSOR

    @pytest.mark.asyncio
    async def test_add_duplicate_stakeholder(self, temp_service, sample_stakeholder):
        """Test adding duplicate stakeholder to engagement."""
        # Create engagement first
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.ACCELERATOR,
            contract_value=30000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        # Add stakeholder twice
        await temp_service.add_stakeholder(engagement_id, sample_stakeholder)
        success = await temp_service.add_stakeholder(engagement_id, sample_stakeholder)

        assert success is False  # Should fail on duplicate

        # Verify only one stakeholder exists
        engagement = await temp_service.get_engagement(engagement_id)
        assert len(engagement.stakeholders) == 1

    @pytest.mark.asyncio
    async def test_update_deliverable_status(self, temp_service):
        """Test updating deliverable status."""
        # Create engagement with deliverables
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.PLATFORM,
            contract_value=60000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        engagement = await temp_service.get_engagement(engagement_id)
        deliverable_id = engagement.deliverables[0].deliverable_id

        # Update deliverable status
        success = await temp_service.update_deliverable_status(
            engagement_id,
            deliverable_id,
            DeliverableStatus.IN_PROGRESS,
            actual_hours=8,
            notes="Work started on analysis",
        )

        assert success is True

        # Verify update
        updated_engagement = await temp_service.get_engagement(engagement_id)
        updated_deliverable = updated_engagement.deliverables[0]

        assert updated_deliverable.status == DeliverableStatus.IN_PROGRESS
        assert updated_deliverable.actual_hours == 8
        assert len(updated_engagement.communication_log) > 0

    @pytest.mark.asyncio
    async def test_update_deliverable_completion(self, temp_service):
        """Test updating deliverable to completed status."""
        # Create engagement
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.ACCELERATOR,
            contract_value=30000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        engagement = await temp_service.get_engagement(engagement_id)
        deliverable_id = engagement.deliverables[0].deliverable_id

        # Mark as approved (completed)
        success = await temp_service.update_deliverable_status(
            engagement_id, deliverable_id, DeliverableStatus.APPROVED, actual_hours=16
        )

        assert success is True

        # Verify completion date was set and overall completion updated
        updated_engagement = await temp_service.get_engagement(engagement_id)
        updated_deliverable = updated_engagement.deliverables[0]

        assert updated_deliverable.status == DeliverableStatus.APPROVED
        assert updated_deliverable.completed_date is not None
        assert updated_engagement.completion_percentage > 0

    @pytest.mark.asyncio
    async def test_track_roi_metrics(self, temp_service, sample_roi_metrics):
        """Test ROI metrics tracking."""
        # Create engagement first
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.PLATFORM,
            contract_value=60000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        # Track ROI metrics
        sample_roi_metrics.engagement_id = engagement_id
        success = await temp_service.track_roi_metrics(engagement_id, sample_roi_metrics)

        assert success is True

        # Verify metrics were saved
        metrics_file = temp_service.metrics_dir / f"{engagement_id}_roi.json"
        assert metrics_file.exists()

        with open(metrics_file, "r") as f:
            metrics_history = json.load(f)

        assert len(metrics_history) == 1
        assert metrics_history[0]["monthly_revenue_increase"] == 125000

        # Verify engagement was updated with latest metrics
        engagement = await temp_service.get_engagement(engagement_id)
        assert engagement.current_metrics["monthly_revenue_increase"] == 125000
        assert engagement.projected_roi == 284.5

    @pytest.mark.asyncio
    async def test_track_multiple_roi_measurements(self, temp_service):
        """Test tracking multiple ROI measurements over time."""
        engagement_id = await temp_service.create_engagement(
            client_name="Test Client",
            client_organization="Test Org",
            tier=EngagementTier.INNOVATION,
            contract_value=85000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Test Consultant",
        )

        # Track multiple measurements
        for i in range(3):
            metrics = ROIMetrics(
                engagement_id=engagement_id,
                measurement_date=(datetime.utcnow() - timedelta(days=30 * i)).isoformat(),
                monthly_revenue_increase=100000 + (i * 25000),
                total_roi_percentage=200 + (i * 50),
            )

            await temp_service.track_roi_metrics(engagement_id, metrics)

        # Verify all measurements were saved
        metrics_file = temp_service.metrics_dir / f"{engagement_id}_roi.json"
        with open(metrics_file, "r") as f:
            metrics_history = json.load(f)

        assert len(metrics_history) == 3
        assert metrics_history[0]["monthly_revenue_increase"] == 100000
        assert metrics_history[2]["monthly_revenue_increase"] == 150000

    @pytest.mark.asyncio
    async def test_get_engagement_dashboard(self, temp_service):
        """Test engagement dashboard generation."""
        # Create engagement with some progress
        engagement_id = await temp_service.create_engagement(
            client_name="Dashboard Client",
            client_organization="Dashboard Corp",
            tier=EngagementTier.PLATFORM,
            contract_value=65000,
            start_date="2024-01-15T10:00:00",
            lead_consultant="Dashboard Consultant",
        )

        # Add some progress
        engagement = await temp_service.get_engagement(engagement_id)
        deliverable_id = engagement.deliverables[0].deliverable_id

        await temp_service.update_deliverable_status(engagement_id, deliverable_id, DeliverableStatus.APPROVED)

        # Generate dashboard
        dashboard = await temp_service.get_engagement_dashboard(engagement_id)

        assert "engagement_info" in dashboard
        assert "progress" in dashboard
        assert "financial" in dashboard
        assert "timeline" in dashboard
        assert "team" in dashboard
        assert "risk" in dashboard

        # Verify engagement info
        assert dashboard["engagement_info"]["client"] == "Dashboard Corp"
        assert dashboard["engagement_info"]["tier"] == "platform"
        assert dashboard["engagement_info"]["contract_value"] == 65000

        # Verify progress calculation
        assert dashboard["progress"]["completed_deliverables"] >= 1
        assert dashboard["progress"]["completion_rate"] > 0

    @pytest.mark.asyncio
    async def test_generate_status_report(self, temp_service):
        """Test executive status report generation."""
        # Create engagement
        engagement_id = await temp_service.create_engagement(
            client_name="Report Client",
            client_organization="Report Corp",
            tier=EngagementTier.ACCELERATOR,
            contract_value=32000,
            start_date="2024-01-01T10:00:00",
            lead_consultant="Report Consultant",
        )

        # Generate status report
        report = await temp_service.generate_status_report(engagement_id)

        assert "report_generated" in report
        assert "engagement_id" in report
        assert "client" in report
        assert "executive_summary" in report
        assert "key_achievements" in report
        assert "upcoming_milestones" in report
        assert "financial_status" in report
        assert "risk_assessment" in report

        # Verify content
        assert report["client"] == "Report Corp"
        assert report["engagement_id"] == engagement_id
        assert "Week" in report["reporting_period"]

    @pytest.mark.asyncio
    async def test_get_dashboard_nonexistent_engagement(self, temp_service):
        """Test dashboard generation for non-existent engagement."""
        dashboard = await temp_service.get_engagement_dashboard("nonexistent_id")
        assert dashboard == {}

    def test_payment_schedule_generation_accelerator(self, temp_service):
        """Test payment schedule generation for Accelerator tier."""
        schedule = temp_service._generate_payment_schedule(30000, EngagementTier.ACCELERATOR)

        assert len(schedule) == 3  # Accelerator has 3 milestones
        assert schedule[0]["milestone"] == "Contract Signing"
        assert schedule[0]["amount"] == 9000  # 30% of 30000
        assert schedule[1]["amount"] == 9000  # 30%
        assert schedule[2]["amount"] == 12000  # 40%

        # Verify total adds up
        total = sum(p["amount"] for p in schedule)
        assert total == 30000

    def test_payment_schedule_generation_platform(self, temp_service):
        """Test payment schedule generation for Platform tier."""
        schedule = temp_service._generate_payment_schedule(60000, EngagementTier.PLATFORM)

        assert len(schedule) == 4  # Platform has 4 milestones
        total = sum(p["amount"] for p in schedule)
        assert total == 60000

    def test_payment_schedule_generation_innovation(self, temp_service):
        """Test payment schedule generation for Innovation tier."""
        schedule = temp_service._generate_payment_schedule(85000, EngagementTier.INNOVATION)

        assert len(schedule) == 5  # Innovation has 5 milestones
        total = sum(p["amount"] for p in schedule)
        assert total == 85000

    def test_tier_success_metrics(self, temp_service):
        """Test tier-specific success metrics generation."""
        # Test Accelerator metrics
        accelerator_metrics = temp_service._get_tier_success_metrics(EngagementTier.ACCELERATOR)
        assert "25% conversion rate improvement" in accelerator_metrics
        assert "85+ hours/month automation achieved" in accelerator_metrics

        # Test Platform metrics
        platform_metrics = temp_service._get_tier_success_metrics(EngagementTier.PLATFORM)
        assert "40% churn reduction achieved" in platform_metrics
        assert "$1M+ revenue retention demonstrated" in platform_metrics

        # Test Innovation metrics
        innovation_metrics = temp_service._get_tier_success_metrics(EngagementTier.INNOVATION)
        assert "Proprietary competitive advantage established" in innovation_metrics
        assert "Innovation lab delivering measurable results" in innovation_metrics

    def test_completion_percentage_calculation(self, temp_service):
        """Test engagement completion percentage calculation."""
        # Create sample engagement with deliverables
        deliverables = [
            Deliverable(
                deliverable_id="d1",
                name="D1",
                description="",
                category="",
                estimated_hours=10,
                status=DeliverableStatus.APPROVED,
            ),
            Deliverable(
                deliverable_id="d2",
                name="D2",
                description="",
                category="",
                estimated_hours=20,
                status=DeliverableStatus.IN_PROGRESS,
            ),
            Deliverable(
                deliverable_id="d3",
                name="D3",
                description="",
                category="",
                estimated_hours=30,
                status=DeliverableStatus.PLANNED,
            ),
        ]

        engagement = ConsultingEngagement(
            engagement_id="test",
            client_name="Test",
            client_organization="Test Org",
            tier=EngagementTier.ACCELERATOR,
            status=EngagementStatus.IMPLEMENTATION,
            contract_value=30000,
            payment_schedule=[],
            start_date="2024-01-01",
            planned_end_date="2024-03-01",
            lead_consultant="Test",
            deliverables=deliverables,
        )

        completion = temp_service._calculate_completion_percentage(engagement)
        expected = (10 / 60) * 100  # Only first deliverable (10 hours) is approved out of 60 total
        assert abs(completion - expected) < 0.1

    def test_completion_percentage_no_deliverables(self, temp_service):
        """Test completion percentage with no deliverables."""
        engagement = ConsultingEngagement(
            engagement_id="test",
            client_name="Test",
            client_organization="Test Org",
            tier=EngagementTier.ACCELERATOR,
            status=EngagementStatus.CONTRACTED,
            contract_value=30000,
            payment_schedule=[],
            start_date="2024-01-01",
            planned_end_date="2024-03-01",
            lead_consultant="Test",
            deliverables=[],
        )

        completion = temp_service._calculate_completion_percentage(engagement)
        assert completion == 0.0

    def test_days_remaining_calculation(self, temp_service):
        """Test days remaining calculation."""
        future_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        days = temp_service._calculate_days_remaining(future_date)
        assert 29 <= days <= 31  # Account for slight timing differences

        past_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
        days = temp_service._calculate_days_remaining(past_date)
        assert days < 0

    def test_project_week_calculation(self, temp_service):
        """Test project week calculation."""
        # Create engagement starting 2 weeks ago
        start_date = (datetime.utcnow() - timedelta(weeks=2)).isoformat()
        engagement = ConsultingEngagement(
            engagement_id="test",
            client_name="Test",
            client_organization="Test Org",
            tier=EngagementTier.ACCELERATOR,
            status=EngagementStatus.IMPLEMENTATION,
            contract_value=30000,
            payment_schedule=[],
            start_date=start_date,
            planned_end_date="2024-03-01",
            lead_consultant="Test",
        )

        week = temp_service._calculate_project_week(engagement)
        assert week == 3  # Should be in week 3

    def test_service_factory_function(self):
        """Test the get_consulting_delivery_service factory function."""
        from ghl_real_estate_ai.services.consulting_delivery_service import get_consulting_delivery_service

        service = get_consulting_delivery_service()
        assert isinstance(service, ConsultingDeliveryService)

    @pytest.mark.asyncio
    async def test_error_handling_engagement_creation(self, temp_service):
        """Test error handling during engagement creation."""
        # Test with invalid date format
        with pytest.raises(Exception):
            await temp_service.create_engagement(
                client_name="Test Client",
                client_organization="Test Org",
                tier=EngagementTier.ACCELERATOR,
                contract_value=30000,
                start_date="invalid-date-format",
                lead_consultant="Test Consultant",
            )

    def test_stakeholder_dataclass(self):
        """Test Stakeholder dataclass functionality."""
        stakeholder = Stakeholder(
            stakeholder_id="test_001",
            name="Test User",
            email="test@example.com",
            role=StakeholderRole.PROJECT_MANAGER,
            department="IT",
            influence_level=7,
            engagement_preference="phone",
            availability={"monday": "9-5"},
            decision_authority=["technical"],
        )

        assert stakeholder.name == "Test User"
        assert stakeholder.role == StakeholderRole.PROJECT_MANAGER
        assert stakeholder.influence_level == 7

    def test_deliverable_dataclass(self):
        """Test Deliverable dataclass functionality."""
        deliverable = Deliverable(
            deliverable_id="del_001",
            name="Test Deliverable",
            description="Test description",
            category="strategic",
            estimated_hours=20,
        )

        assert deliverable.name == "Test Deliverable"
        assert deliverable.status == DeliverableStatus.PLANNED  # Default
        assert deliverable.actual_hours == 0  # Default

    def test_roi_metrics_dataclass(self):
        """Test ROIMetrics dataclass functionality."""
        roi = ROIMetrics(
            engagement_id="test_eng",
            measurement_date="2024-01-15T10:00:00",
            monthly_revenue_increase=150000,
            conversion_rate_improvement=30.0,
            total_roi_percentage=320.5,
        )

        assert roi.engagement_id == "test_eng"
        assert roi.monthly_revenue_increase == 150000
        assert roi.total_roi_percentage == 320.5

    def test_enum_values(self):
        """Test enum value correctness."""
        # Test EngagementTier
        assert EngagementTier.ACCELERATOR.value == "accelerator"
        assert EngagementTier.PLATFORM.value == "platform"
        assert EngagementTier.INNOVATION.value == "innovation"

        # Test EngagementStatus
        assert EngagementStatus.CONTRACTED.value == "contracted"
        assert EngagementStatus.IMPLEMENTATION.value == "implementation"
        assert EngagementStatus.COMPLETED.value == "completed"

        # Test DeliverableStatus
        assert DeliverableStatus.PLANNED.value == "planned"
        assert DeliverableStatus.IN_PROGRESS.value == "in_progress"
        assert DeliverableStatus.APPROVED.value == "approved"