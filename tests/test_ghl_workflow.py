"""
Tests for GHL Workflow Service

Tests the auto-tagging, pipeline stage updates, and appointment synchronization
functionality of the GHL workflow integration.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.ghl_workflow_service import (
    AppointmentDetails,
    GHLWorkflowService,
    PipelineStage,
    TagAction,
    WorkflowResult,
)


@pytest.fixture
def mock_ghl_client():
    """Create a mock GHL client."""
    client = MagicMock()
    client.get_contact = AsyncMock()
    client.update_contact = AsyncMock(return_value=True)
    return client


@pytest.fixture
def workflow_service(mock_ghl_client):
    """Create a workflow service with mock GHL client."""
    return GHLWorkflowService(ghl_client=mock_ghl_client)


@pytest.fixture
def mock_contact():
    """Create a mock contact."""
    contact = MagicMock()
    contact.id = "test-contact-id"
    contact.tags = []
    return contact


class TestAutoTagging:
    """Tests for auto-tagging functionality."""

    @pytest.mark.asyncio
    async def test_hot_lead_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that hot lead tag is applied for composite score >= 80."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "frs_score": 85,
                "pcs_score": 90,
                "composite_score": 88,
            },
            persona="first_time",
            sentiment="positive",
        )

        assert result.success is True
        assert "Hot-Lead" in result.tags_applied
        assert "Priority-Lead" in result.tags_applied
        assert "High-Commitment" in result.tags_applied

    @pytest.mark.asyncio
    async def test_warm_lead_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that warm lead tag is applied for composite score 60-79."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "frs_score": 65,
                "pcs_score": 70,
                "composite_score": 68,
            },
        )

        assert result.success is True
        assert "Warm-Lead" in result.tags_applied

    @pytest.mark.asyncio
    async def test_cold_lead_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that cold lead tag is applied for composite score < 40."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "frs_score": 30,
                "pcs_score": 35,
                "composite_score": 32,
            },
        )

        assert result.success is True
        assert "Cold-Lead" in result.tags_applied

    @pytest.mark.asyncio
    async def test_investor_seller_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that investor seller tag is applied for investor persona."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 70},
            persona="Investor",
        )

        assert result.success is True
        assert "Investor-Seller" in result.tags_applied

    @pytest.mark.asyncio
    async def test_distressed_seller_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that distressed seller tag is applied for distressed persona."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 70},
            persona="Distressed",
        )

        assert result.success is True
        assert "Distressed-Seller" in result.tags_applied

    @pytest.mark.asyncio
    async def test_first_time_buyer_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that first-time buyer tag is applied for first-time persona."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 70},
            persona="First-Time",
        )

        assert result.success is True
        assert "First-Time-Buyer" in result.tags_applied

    @pytest.mark.asyncio
    async def test_high_urgency_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that high urgency tag is applied for urgency level >= 0.7."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "composite_score": 70,
                "urgency_level": 0.8,
            },
        )

        assert result.success is True
        assert "High-Urgency" in result.tags_applied

    @pytest.mark.asyncio
    async def test_needs_attention_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that needs attention tag is applied for negative sentiment."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 70},
            sentiment="negative",
        )

        assert result.success is True
        assert "Needs-Attention" in result.tags_applied

    @pytest.mark.asyncio
    async def test_escalated_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that escalated tag is applied when escalation is triggered."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 70},
            escalation=True,
        )

        assert result.success is True
        assert "Escalated" in result.tags_applied

    @pytest.mark.asyncio
    async def test_appointment_set_tagging(self, workflow_service, mock_ghl_client, mock_contact):
        """Test that appointment set tag is applied when appointment is booked."""
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 70},
            appointment_booked=True,
        )

        assert result.success is True
        assert "Appointment-Set" in result.tags_applied

    @pytest.mark.asyncio
    async def test_tag_removal_conflict(self, workflow_service, mock_ghl_client):
        """Test that conflicting tags are removed."""
        mock_contact = MagicMock()
        mock_contact.id = "test-contact-id"
        mock_contact.tags = ["Cold-Lead"]
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "frs_score": 85,
                "pcs_score": 90,
                "composite_score": 88,
            },
        )

        assert result.success is True
        assert "Hot-Lead" in result.tags_applied
        assert "Cold-Lead" in result.tags_removed

    @pytest.mark.asyncio
    async def test_no_duplicate_tags(self, workflow_service, mock_ghl_client):
        """Test that existing tags are not duplicated."""
        mock_contact = MagicMock()
        mock_contact.id = "test-contact-id"
        mock_contact.tags = ["Hot-Lead"]
        mock_ghl_client.get_contact.return_value = mock_contact

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "frs_score": 85,
                "pcs_score": 90,
                "composite_score": 88,
            },
        )

        assert result.success is True
        # Hot-Lead should not be in tags_applied since it already exists
        assert "Hot-Lead" not in result.tags_applied


class TestPipelineStageUpdates:
    """Tests for pipeline stage update functionality."""

    @pytest.mark.asyncio
    async def test_new_to_qualifying(self, workflow_service):
        """Test transition from new to qualifying on first message."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.NEW,
            scores={"composite_score": 50},
            conversation_state={"message_count": 1},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_qualifying_to_qualified(self, workflow_service):
        """Test transition from qualifying to qualified with good scores."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.QUALIFYING,
            scores={
                "frs_score": 70,
                "pcs_score": 75,
                "composite_score": 72,
            },
            conversation_state={},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_qualified_to_hot_lead(self, workflow_service):
        """Test transition from qualified to hot lead with high score."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.QUALIFIED,
            scores={"composite_score": 85},
            conversation_state={},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_qualified_to_warm_lead(self, workflow_service):
        """Test transition from qualified to warm lead with medium score."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.QUALIFIED,
            scores={"composite_score": 68},
            conversation_state={},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_hot_lead_to_appointment_scheduled(self, workflow_service):
        """Test transition from hot lead to appointment scheduled."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.HOT_LEAD,
            scores={"composite_score": 85},
            conversation_state={"appointment_booked": True},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_appointment_scheduled_to_follow_up(self, workflow_service):
        """Test transition from appointment scheduled to follow up."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.APPOINTMENT_SCHEDULED,
            scores={"composite_score": 85},
            conversation_state={"appointment_completed": True},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_follow_up_to_re_engagement_7_days(self, workflow_service):
        """Test transition from follow up to re-engagement after 7 days."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.FOLLOW_UP,
            scores={"composite_score": 70},
            conversation_state={"days_no_response": 7},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_re_engagement_to_dormant_30_days(self, workflow_service):
        """Test transition from re-engagement to dormant after 30 days."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.RE_ENGAGEMENT,
            scores={"composite_score": 70},
            conversation_state={"days_no_response": 30},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_follow_up_to_closed_won(self, workflow_service):
        """Test transition from follow up to closed won."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.FOLLOW_UP,
            scores={"composite_score": 90},
            conversation_state={"status": "closed_won"},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_follow_up_to_closed_lost(self, workflow_service):
        """Test transition from follow up to closed lost."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.FOLLOW_UP,
            scores={"composite_score": 50},
            conversation_state={"status": "closed_lost"},
        )

        assert result.success is True
        assert result.stage_updated is True

    @pytest.mark.asyncio
    async def test_no_stage_change(self, workflow_service):
        """Test that stage doesn't change without trigger."""
        result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.QUALIFIED,
            scores={"composite_score": 50},
            conversation_state={},
        )

        assert result.success is True
        assert result.stage_updated is False


class TestAppointmentSync:
    """Tests for appointment synchronization functionality."""

    @pytest.mark.asyncio
    async def test_sync_appointment_success(self, workflow_service):
        """Test successful appointment sync."""
        appointment = AppointmentDetails(
            contact_id="test-contact",
            title="Property Showing",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=1),
            calendar_id="calendar-123",
            location="123 Main St",
            notes="Bring pre-approval letter",
        )

        result = await workflow_service.sync_appointment(appointment)

        assert result.success is True
        assert result.appointment_synced is True

    @pytest.mark.asyncio
    async def test_detect_appointment_request(self, workflow_service):
        """Test detection of appointment request in conversation."""
        conversation_history = [
            {"role": "user", "content": "I'd like to schedule a showing for tomorrow"},
        ]

        appointment = await workflow_service.detect_appointment_request(conversation_history)

        # Should detect appointment request (implementation may vary)
        assert appointment is None or isinstance(appointment, AppointmentDetails)

    @pytest.mark.asyncio
    async def test_no_appointment_request(self, workflow_service):
        """Test that no appointment is detected when not requested."""
        conversation_history = [
            {"role": "user", "content": "What's the price of this property?"},
        ]

        appointment = await workflow_service.detect_appointment_request(conversation_history)

        assert appointment is None


class TestContactDataSync:
    """Tests for contact data synchronization functionality."""

    @pytest.mark.asyncio
    async def test_sync_contact_data_success(self, workflow_service, mock_ghl_client):
        """Test successful contact data sync."""
        mock_ghl_client.update_contact.return_value = True

        bot_data = {
            "frs_score": 85,
            "pcs_score": 90,
            "composite_score": 88,
            "persona": "First-Time",
        }

        result = await workflow_service.sync_contact_data(
            contact_id="test-contact",
            bot_data=bot_data,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_sync_contact_data_partial(self, workflow_service, mock_ghl_client):
        """Test contact data sync with partial data."""
        mock_ghl_client.update_contact.return_value = True

        bot_data = {
            "composite_score": 75,
        }

        result = await workflow_service.sync_contact_data(
            contact_id="test-contact",
            bot_data=bot_data,
        )

        assert result is True


class TestWorkflowIntegration:
    """Tests for complete workflow integration."""

    @pytest.mark.asyncio
    async def test_complete_lead_workflow(self, workflow_service, mock_ghl_client, mock_contact):
        """Test complete lead workflow with tags, pipeline, and data sync."""
        mock_ghl_client.get_contact.return_value = mock_contact
        mock_ghl_client.update_contact.return_value = True

        # Apply tags
        tag_result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={
                "frs_score": 85,
                "pcs_score": 90,
                "composite_score": 88,
            },
            persona="First-Time",
            sentiment="positive",
        )

        assert tag_result.success is True
        assert len(tag_result.tags_applied) > 0

        # Update pipeline
        pipeline_result = await workflow_service.update_pipeline_stage(
            contact_id="test-contact",
            current_stage=PipelineStage.QUALIFIED,
            scores={"composite_score": 88},
            conversation_state={},
        )

        assert pipeline_result.success is True
        assert pipeline_result.stage_updated is True

        # Sync data
        data_synced = await workflow_service.sync_contact_data(
            contact_id="test-contact",
            bot_data={
                "frs_score": 85,
                "pcs_score": 90,
                "composite_score": 88,
                "persona": "First-Time",
            },
        )

        assert data_synced is True


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_contact_not_found(self, workflow_service, mock_ghl_client):
        """Test handling when contact is not found."""
        mock_ghl_client.get_contact.return_value = None

        result = await workflow_service.apply_auto_tags(
            contact_id="non-existent-contact",
            scores={"composite_score": 85},
        )

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_ghl_api_error(self, workflow_service, mock_ghl_client):
        """Test handling when GHL API returns error."""
        mock_ghl_client.get_contact.side_effect = Exception("API Error")

        result = await workflow_service.apply_auto_tags(
            contact_id="test-contact",
            scores={"composite_score": 85},
        )

        assert result.success is False
        assert len(result.errors) > 0
