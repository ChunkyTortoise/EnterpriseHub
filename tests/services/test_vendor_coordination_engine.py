import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Vendor Coordination Engine.
Tests cover vendor management, scheduling, performance tracking, and automation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.vendor_coordination_engine import (

    AppointmentStatus,
    ServiceRequest,
    ServiceType,
    VendorAppointment,
    VendorCoordinationEngine,
    VendorProfile,
    VendorRecommendation,
    VendorStatus,
    VendorType,
)


class TestVendorProfile:
    """Test VendorProfile dataclass functionality."""

    def test_vendor_profile_creation(self):
        """Test vendor profile creation with all fields."""
        profile = VendorProfile(
            vendor_id="vendor_001",
            name="Elite Home Inspections",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION, ServiceType.PEST_INSPECTION],
            contact_info={"phone": "(555) 123-4567", "email": "contact@eliteinspections.com"},
            rating=4.8,
            total_jobs=150,
            completed_jobs=145,
            on_time_percentage=95.2,
            response_time_hours=2.0,
            average_cost_index=1.05,
            status=VendorStatus.PREFERRED,
            service_areas=["91701", "91702", "91703"],
            minimum_notice_hours=24,
            maximum_distance_miles=30,
            license_number="LIC123456",
            insurance_verified=True,
            background_check=True,
            certifications=["TREC", "NAHI"],
            years_experience=8,
        )

        assert profile.vendor_id == "vendor_001"
        assert profile.vendor_type == VendorType.HOME_INSPECTOR
        assert profile.rating == 4.8
        assert len(profile.service_areas) == 3
        assert profile.on_time_percentage == 95.2
        assert ServiceType.COMPREHENSIVE_INSPECTION in profile.services

    def test_vendor_profile_serialization(self):
        """Test vendor profile serialization."""
        profile = VendorProfile(
            vendor_id="vendor_002",
            name="Quick Appraisals LLC",
            vendor_type=VendorType.APPRAISER,
            services=[ServiceType.PROPERTY_APPRAISAL],
            contact_info={"phone": "(555) 987-6543", "email": "info@quickappraisals.com"},
            rating=4.6,
            total_jobs=89,
            completed_jobs=85,
            on_time_percentage=95.0,
            years_experience=12,
        )

        profile_dict = profile.__dict__
        assert profile_dict["vendor_id"] == "vendor_002"
        assert profile_dict["vendor_type"] == VendorType.APPRAISER
        assert isinstance(profile_dict["contact_info"], dict)


class TestVendorAppointment:
    """Test VendorAppointment dataclass functionality."""

    def test_appointment_creation(self):
        """Test appointment creation with all fields."""
        vendor_profile = VendorProfile(
            vendor_id="vendor_123",
            name="Test Inspector",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 111-2222"},
        )

        appointment = VendorAppointment(
            appointment_id="appt_001",
            request_id="req_001",
            transaction_id="deal_456",
            vendor_id="vendor_123",
            vendor_profile=vendor_profile,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            scheduled_date=datetime.now() + timedelta(days=2),
            duration_minutes=180,
            status=AppointmentStatus.SCHEDULED,
            property_address="789 Pine Street, Rancho Cucamonga, CA",
            special_instructions="Check HVAC system thoroughly",
            quoted_price=475.00,
        )

        assert appointment.appointment_id == "appt_001"
        assert appointment.vendor_id == "vendor_123"
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.duration_minutes == 180
        assert appointment.quoted_price == 475.00

    def test_appointment_status_progression(self):
        """Test appointment status can be updated."""
        vendor_profile = VendorProfile(
            vendor_id="vendor_789",
            name="Test Appraiser",
            vendor_type=VendorType.APPRAISER,
            services=[ServiceType.PROPERTY_APPRAISAL],
            contact_info={"phone": "(555) 333-4444"},
        )

        appointment = VendorAppointment(
            appointment_id="appt_002",
            request_id="req_002",
            transaction_id="deal_101",
            vendor_id="vendor_789",
            vendor_profile=vendor_profile,
            service_type=ServiceType.PROPERTY_APPRAISAL,
            scheduled_date=datetime.now() + timedelta(days=1),
            duration_minutes=120,
            status=AppointmentStatus.PENDING,
            property_address="456 Oak Avenue, Rancho Cucamonga, CA",
        )

        # Simulate status progression
        appointment.status = AppointmentStatus.CONFIRMED
        assert appointment.status == AppointmentStatus.CONFIRMED

        appointment.status = AppointmentStatus.IN_PROGRESS
        assert appointment.status == AppointmentStatus.IN_PROGRESS

        appointment.status = AppointmentStatus.COMPLETED
        assert appointment.status == AppointmentStatus.COMPLETED


class TestVendorCoordinationEngine:
    """Test the main vendor coordination functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for vendor engine."""
        return {
            "cache_service": MagicMock(),
            "ghl_client": MagicMock(),
            "claude_assistant": MagicMock(),
        }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create vendor engine instance with mocked dependencies."""
        with (
            patch(
                "ghl_real_estate_ai.services.vendor_coordination_engine.ClaudeAssistant",
                return_value=mock_dependencies["claude_assistant"],
            ),
            patch(
                "ghl_real_estate_ai.services.vendor_coordination_engine.GHLClient",
                return_value=mock_dependencies["ghl_client"],
            ),
            patch(
                "ghl_real_estate_ai.services.vendor_coordination_engine.get_cache_service",
                return_value=mock_dependencies["cache_service"],
            ),
            patch("ghl_real_estate_ai.services.vendor_coordination_engine.get_llm_client") as mock_llm,
        ):
            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance
            engine = VendorCoordinationEngine(
                cache_service=mock_dependencies["cache_service"],
                ghl_client=mock_dependencies["ghl_client"],
                claude_assistant=mock_dependencies["claude_assistant"],
            )
            return engine

    @pytest.mark.asyncio
    async def test_request_vendor_service_success(self, engine):
        """Test successful vendor service request."""
        # Add a matching vendor to the engine
        vendor = VendorProfile(
            vendor_id="vendor_001",
            name="Elite Inspections",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 123-4567", "email": "elite@example.com"},
            rating=4.8,
            total_jobs=200,
            completed_jobs=195,
            on_time_percentage=97.0,
            response_time_hours=2.0,
            average_cost_index=1.0,
            status=VendorStatus.ACTIVE,
            service_areas=[],
            years_experience=8,
        )
        engine.vendor_profiles["vendor_001"] = vendor

        # Mock the LLM client for recommendation generation
        mock_response = MagicMock()
        mock_response.content = "Good vendor recommendation"
        engine.llm_client.generate = AsyncMock(return_value=mock_response)

        request_id = await engine.request_vendor_service(
            transaction_id="deal_123",
            vendor_type=VendorType.HOME_INSPECTOR,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            property_address="123 Main Street, Rancho Cucamonga, CA",
            preferences={"urgency": 3, "contact_person": "John Doe"},
        )

        assert request_id is not None
        assert request_id in engine.service_requests
        assert engine.metrics["total_requests"] >= 1

    @pytest.mark.asyncio
    async def test_request_vendor_service_with_preferences(self, engine):
        """Test vendor service request with all preferences."""
        # Mock the LLM so no actual calls are made
        mock_response = MagicMock()
        mock_response.content = "Recommendation"
        engine.llm_client.generate = AsyncMock(return_value=mock_response)

        preferences = {
            "preferred_dates": [datetime.now() + timedelta(days=3)],
            "urgency": 5,
            "budget_range": (300.0, 800.0),
            "instructions": "Check HVAC thoroughly",
            "contact_person": "Jane Smith",
            "contact_phone": "(555) 999-0000",
        }

        request_id = await engine.request_vendor_service(
            transaction_id="deal_456",
            vendor_type=VendorType.APPRAISER,
            service_type=ServiceType.PROPERTY_APPRAISAL,
            property_address="456 Oak Street, Rancho Cucamonga, CA",
            preferences=preferences,
        )

        assert request_id is not None
        request = engine.service_requests[request_id]
        assert request.urgency_level == 5
        assert request.contact_person == "Jane Smith"
        assert request.special_instructions == "Check HVAC thoroughly"

    @pytest.mark.asyncio
    async def test_get_vendor_recommendations_success(self, engine):
        """Test vendor recommendation algorithm."""
        # Create a service request first
        request = ServiceRequest(
            request_id="req_test",
            transaction_id="deal_test",
            vendor_type=VendorType.HOME_INSPECTOR,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            property_address="123 Test Street",
        )
        engine.service_requests["req_test"] = request

        # Add matching vendor
        vendor = VendorProfile(
            vendor_id="vendor_high_rating",
            name="Premium Inspections",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 111-1111", "email": "premium@example.com"},
            rating=4.9,
            total_jobs=300,
            completed_jobs=295,
            on_time_percentage=98.5,
            response_time_hours=1.0,
            average_cost_index=1.05,
            status=VendorStatus.PREFERRED,
            service_areas=[],
            years_experience=10,
        )
        engine.vendor_profiles["vendor_high_rating"] = vendor

        # Mock the LLM client
        mock_response = MagicMock()
        mock_response.content = "Excellent vendor match"
        engine.llm_client.generate = AsyncMock(return_value=mock_response)

        recommendations = await engine.get_vendor_recommendations("req_test")

        assert len(recommendations) > 0
        assert isinstance(recommendations[0], VendorRecommendation)
        assert recommendations[0].match_score > 0

    @pytest.mark.asyncio
    async def test_get_vendor_recommendations_no_request(self, engine):
        """Test vendor recommendations with non-existent request."""
        recommendations = await engine.get_vendor_recommendations("nonexistent_req")
        assert recommendations == []

    @pytest.mark.asyncio
    async def test_schedule_appointment_success(self, engine):
        """Test successful appointment scheduling."""
        # Create service request
        request = ServiceRequest(
            request_id="req_sched",
            transaction_id="deal_456",
            vendor_type=VendorType.HOME_INSPECTOR,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            property_address="789 Elm Street, Rancho Cucamonga, CA",
            contact_person="Jane Smith",
            contact_phone="(555) 333-4444",
        )
        engine.service_requests["req_sched"] = request

        # Add vendor
        vendor = VendorProfile(
            vendor_id="vendor_123",
            name="Reliable Inspections",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 555-5555", "email": "reliable@example.com"},
            rating=4.7,
            total_jobs=180,
            completed_jobs=175,
            on_time_percentage=96.0,
            average_cost_index=0.95,
            status=VendorStatus.ACTIVE,
            service_areas=[],
            years_experience=5,
            minimum_notice_hours=24,
        )
        engine.vendor_profiles["vendor_123"] = vendor

        # Schedule during business hours, far enough in the future
        preferred_dt = datetime.now() + timedelta(days=3)
        preferred_dt = preferred_dt.replace(hour=10, minute=0, second=0, microsecond=0)

        appointment_id = await engine.schedule_appointment(
            request_id="req_sched",
            vendor_id="vendor_123",
            preferred_datetime=preferred_dt,
        )

        assert appointment_id is not None
        assert appointment_id in engine.appointments
        assert engine.metrics["appointments_scheduled"] >= 1

    @pytest.mark.asyncio
    async def test_schedule_appointment_vendor_not_found(self, engine):
        """Test scheduling with non-existent vendor or request."""
        result = await engine.schedule_appointment(
            request_id="nonexistent_req",
            vendor_id="nonexistent_vendor",
            preferred_datetime=datetime.now() + timedelta(days=2),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_update_appointment_status(self, engine):
        """Test appointment status updates."""
        # Create an appointment directly
        vendor_profile = VendorProfile(
            vendor_id="vendor_456",
            name="Test Inspector",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 666-7777"},
        )

        appointment = VendorAppointment(
            appointment_id="appt_update_test",
            request_id="req_update",
            transaction_id="deal_789",
            vendor_id="vendor_456",
            vendor_profile=vendor_profile,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            scheduled_date=datetime.now() + timedelta(hours=2),
            status=AppointmentStatus.CONFIRMED,
            property_address="321 Pine Street, Rancho Cucamonga, CA",
        )

        engine.appointments["appt_update_test"] = appointment

        result = await engine.update_appointment_status(
            "appt_update_test",
            AppointmentStatus.IN_PROGRESS,
            notes="Vendor has arrived",
        )

        assert result is True
        assert engine.appointments["appt_update_test"].status == AppointmentStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_appointment_status_completed(self, engine):
        """Test appointment completion updates metrics."""
        vendor_profile = VendorProfile(
            vendor_id="vendor_comp",
            name="Test Inspector",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 888-9999"},
        )

        appointment = VendorAppointment(
            appointment_id="appt_comp",
            request_id="req_comp",
            transaction_id="deal_comp",
            vendor_id="vendor_comp",
            vendor_profile=vendor_profile,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            scheduled_date=datetime.now() - timedelta(hours=1),
            status=AppointmentStatus.IN_PROGRESS,
            property_address="100 Test Avenue",
        )

        engine.appointments["appt_comp"] = appointment
        initial_completed = engine.metrics["appointments_completed"]

        result = await engine.update_appointment_status("appt_comp", AppointmentStatus.COMPLETED)

        assert result is True
        assert engine.appointments["appt_comp"].status == AppointmentStatus.COMPLETED
        assert engine.metrics["appointments_completed"] == initial_completed + 1

    @pytest.mark.asyncio
    async def test_update_appointment_status_not_found(self, engine):
        """Test updating non-existent appointment."""
        result = await engine.update_appointment_status("nonexistent_appt", AppointmentStatus.COMPLETED)
        assert result is False

    @pytest.mark.asyncio
    async def test_submit_vendor_feedback(self, engine):
        """Test vendor feedback submission and rating update."""
        # Add vendor and appointment
        vendor = VendorProfile(
            vendor_id="vendor_feedback",
            name="Feedback Test Vendor",
            vendor_type=VendorType.HOME_INSPECTOR,
            services=[ServiceType.COMPREHENSIVE_INSPECTION],
            contact_info={"phone": "(555) 000-1111"},
            rating=4.0,
            total_jobs=10,
            completed_jobs=9,
        )
        engine.vendor_profiles["vendor_feedback"] = vendor

        appointment = VendorAppointment(
            appointment_id="appt_feedback",
            request_id="req_feedback",
            transaction_id="deal_feedback",
            vendor_id="vendor_feedback",
            vendor_profile=vendor,
            service_type=ServiceType.COMPREHENSIVE_INSPECTION,
            scheduled_date=datetime.now() - timedelta(hours=3),
            status=AppointmentStatus.COMPLETED,
            property_address="200 Feedback Lane",
        )
        engine.appointments["appt_feedback"] = appointment

        result = await engine.submit_vendor_feedback(
            appointment_id="appt_feedback",
            satisfaction_rating=5,
            feedback_text="Excellent service!",
        )

        assert result is True
        assert engine.vendor_profiles["vendor_feedback"].total_jobs == 11

    @pytest.mark.asyncio
    async def test_submit_vendor_feedback_not_found(self, engine):
        """Test feedback for non-existent appointment."""
        result = await engine.submit_vendor_feedback(
            appointment_id="nonexistent",
            satisfaction_rating=3,
        )
        assert result is False

    def test_get_coordination_status(self, engine):
        """Test coordination status reporting."""
        status = engine.get_coordination_status()

        assert "is_running" in status
        assert "total_vendors" in status
        assert "total_requests" in status
        assert "total_appointments" in status
        assert "appointments_by_status" in status
        assert "metrics" in status
        assert status["is_running"] is False

    @pytest.mark.asyncio
    async def test_start_and_stop_coordination(self, engine):
        """Test starting and stopping the coordination engine."""
        await engine.start_coordination()
        assert engine.is_running is True

        await engine.stop_coordination()
        assert engine.is_running is False

    def test_vendor_type_enum_values(self):
        """Test VendorType enum has expected values."""
        assert VendorType.HOME_INSPECTOR.value == "home_inspector"
        assert VendorType.APPRAISER.value == "appraiser"
        assert VendorType.TITLE_COMPANY.value == "title_company"
        assert VendorType.PHOTOGRAPHER.value == "photographer"
        assert VendorType.STRUCTURAL_ENGINEER.value == "structural_engineer"

    def test_service_type_enum_values(self):
        """Test ServiceType enum has expected values."""
        assert ServiceType.COMPREHENSIVE_INSPECTION.value == "comprehensive_inspection"
        assert ServiceType.PROPERTY_APPRAISAL.value == "property_appraisal"
        assert ServiceType.TITLE_SEARCH.value == "title_search"

    def test_appointment_status_enum_values(self):
        """Test AppointmentStatus enum has expected values."""
        assert AppointmentStatus.PENDING.value == "pending"
        assert AppointmentStatus.SCHEDULED.value == "scheduled"
        assert AppointmentStatus.CONFIRMED.value == "confirmed"
        assert AppointmentStatus.IN_PROGRESS.value == "in_progress"
        assert AppointmentStatus.COMPLETED.value == "completed"
        assert AppointmentStatus.CANCELLED.value == "cancelled"
        assert AppointmentStatus.NO_SHOW.value == "no_show"

    def test_initialized_sample_vendors(self, engine):
        """Test engine initializes with sample vendor database."""
        assert len(engine.vendor_profiles) >= 2
        assert "inspector_001" in engine.vendor_profiles
        assert "appraiser_001" in engine.vendor_profiles
        assert engine.vendor_profiles["inspector_001"].name == "Elite Home Inspections"


class TestVendorIntegration:
    """Integration tests for vendor coordination workflows."""

    @pytest.mark.asyncio
    async def test_complete_vendor_workflow(self):
        """Test complete vendor coordination workflow."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_multi_vendor_coordination(self):
        """Test coordination of multiple vendors for complex projects."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_vendor_performance_optimization(self):
        """Test vendor performance optimization algorithms."""
        # Integration test placeholder
        pass