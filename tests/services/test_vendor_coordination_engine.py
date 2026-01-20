"""
Comprehensive tests for Vendor Coordination Engine.
Tests cover vendor management, scheduling, performance tracking, and automation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any
from decimal import Decimal

from ghl_real_estate_ai.services.vendor_coordination_engine import (
    VendorCoordinationEngine,
    VendorType,
    AppointmentStatus,
    VendorProfile,
    VendorAppointment
)


class TestVendorProfile:
    """Test VendorProfile dataclass functionality."""

    def test_vendor_profile_creation(self):
        """Test vendor profile creation with all fields."""
        profile = VendorProfile(
            id="vendor_001",
            name="Elite Home Inspections",
            vendor_type=VendorType.INSPECTOR,
            contact_email="contact@eliteinspections.com",
            contact_phone="(555) 123-4567",
            license_number="LIC123456",
            service_area=["Austin", "Round Rock", "Cedar Park"],
            rating=4.8,
            total_jobs=150,
            average_completion_time=2.5,
            pricing={"base_rate": Decimal("450.00"), "rush_fee": Decimal("100.00")},
            availability_hours={"monday": "8:00-18:00", "tuesday": "8:00-18:00"},
            specializations=["structural", "electrical", "plumbing"],
            performance_metrics={
                "on_time_percentage": 95.2,
                "quality_score": 4.7,
                "communication_score": 4.9
            },
            metadata={"established_year": 2015, "team_size": 3}
        )

        assert profile.id == "vendor_001"
        assert profile.vendor_type == VendorType.INSPECTOR
        assert profile.rating == 4.8
        assert len(profile.service_area) == 3
        assert profile.pricing["base_rate"] == Decimal("450.00")
        assert profile.performance_metrics["on_time_percentage"] == 95.2

    def test_vendor_profile_serialization(self):
        """Test vendor profile serialization."""
        profile = VendorProfile(
            id="vendor_002",
            name="Quick Appraisals LLC",
            vendor_type=VendorType.APPRAISER,
            contact_email="info@quickappraisals.com",
            contact_phone="(555) 987-6543",
            license_number="APP789",
            service_area=["Travis County"],
            rating=4.6,
            total_jobs=89,
            average_completion_time=1.5,
            pricing={"appraisal_fee": Decimal("500.00")},
            availability_hours={"monday": "9:00-17:00"}
        )

        profile_dict = profile.__dict__
        assert profile_dict["id"] == "vendor_002"
        assert profile_dict["vendor_type"] == VendorType.APPRAISER
        assert isinstance(profile_dict["pricing"], dict)


class TestVendorAppointment:
    """Test VendorAppointment dataclass functionality."""

    def test_appointment_creation(self):
        """Test appointment creation with all fields."""
        appointment = VendorAppointment(
            id="appt_001",
            vendor_id="vendor_123",
            deal_id="deal_456",
            appointment_type=VendorType.INSPECTOR,
            scheduled_date=datetime.now() + timedelta(days=2),
            estimated_duration=180,  # 3 hours
            status=AppointmentStatus.SCHEDULED,
            property_address="789 Pine Street, Austin, TX",
            client_contact={"name": "John Doe", "phone": "(555) 111-2222"},
            special_instructions="Check HVAC system thoroughly",
            pricing_agreed=Decimal("475.00"),
            confirmation_details={
                "confirmed_by": "vendor",
                "confirmation_date": datetime.now().isoformat()
            }
        )

        assert appointment.id == "appt_001"
        assert appointment.vendor_id == "vendor_123"
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.estimated_duration == 180
        assert appointment.pricing_agreed == Decimal("475.00")

    def test_appointment_status_progression(self):
        """Test appointment status can be updated."""
        appointment = VendorAppointment(
            id="appt_002",
            vendor_id="vendor_789",
            deal_id="deal_101",
            appointment_type=VendorType.APPRAISER,
            scheduled_date=datetime.now() + timedelta(days=1),
            estimated_duration=120,
            status=AppointmentStatus.PENDING_CONFIRMATION,
            property_address="456 Oak Avenue, Austin, TX"
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
            'cache_service': AsyncMock(),
            'ghl_service': AsyncMock(),
            'claude_service': AsyncMock(),
            'calendar_service': AsyncMock(),
            'notification_service': AsyncMock()
        }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create vendor engine instance with mocked dependencies."""
        return VendorCoordinationEngine(
            cache_service=mock_dependencies['cache_service'],
            ghl_service=mock_dependencies['ghl_service'],
            claude_service=mock_dependencies['claude_service']
        )

    @pytest.mark.asyncio
    async def test_request_vendor_service_success(self, engine, mock_dependencies):
        """Test successful vendor service request."""
        service_request = {
            "deal_id": "deal_123",
            "vendor_type": "inspector",
            "property_address": "123 Main Street, Austin, TX",
            "preferred_date": "2024-01-25T10:00:00",
            "urgency": "standard",
            "special_requirements": ["pet_friendly", "evening_available"],
            "budget_range": {"min": 400, "max": 600}
        }

        # Mock vendor recommendations
        mock_vendors = [
            VendorProfile(
                id="vendor_001",
                name="Elite Inspections",
                vendor_type=VendorType.INSPECTOR,
                contact_email="elite@example.com",
                contact_phone="(555) 123-4567",
                license_number="LIC001",
                service_area=["Austin"],
                rating=4.8,
                total_jobs=200,
                average_completion_time=2.0,
                pricing={"base_rate": Decimal("450.00")},
                availability_hours={"monday": "8:00-18:00"}
            )
        ]

        with patch.object(engine, 'get_vendor_recommendations', return_value=mock_vendors):
            mock_dependencies['calendar_service'].check_availability.return_value = {
                "available": True,
                "suggested_times": ["2024-01-25T10:00:00", "2024-01-25T14:00:00"]
            }

            mock_dependencies['calendar_service'].create_appointment.return_value = {
                "success": True,
                "appointment_id": "appt_789",
                "confirmed_time": "2024-01-25T10:00:00"
            }

            result = await engine.request_vendor_service(service_request)

        assert result["success"] is True
        assert result["appointment_id"] == "appt_789"
        assert result["vendor_id"] == "vendor_001"
        assert "confirmed_time" in result

        # Verify service calls
        mock_dependencies['calendar_service'].create_appointment.assert_called_once()
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_request_vendor_service_no_availability(self, engine, mock_dependencies):
        """Test vendor service request when no vendors available."""
        service_request = {
            "deal_id": "deal_456",
            "vendor_type": "appraiser",
            "property_address": "456 Oak Street, Austin, TX",
            "preferred_date": "2024-01-20T09:00:00",
            "urgency": "rush"
        }

        # Mock no available vendors
        with patch.object(engine, 'get_vendor_recommendations', return_value=[]):
            mock_dependencies['calendar_service'].check_availability.return_value = {
                "available": False,
                "next_available": "2024-01-27T10:00:00"
            }

            result = await engine.request_vendor_service(service_request)

        assert result["success"] is False
        assert "no vendors available" in result["error"].lower()
        assert "next_available" in result

    @pytest.mark.asyncio
    async def test_get_vendor_recommendations_success(self, engine, mock_dependencies):
        """Test vendor recommendation algorithm."""
        criteria = {
            "vendor_type": VendorType.INSPECTOR,
            "service_area": "Austin",
            "min_rating": 4.5,
            "max_budget": 500,
            "required_date": datetime.now() + timedelta(days=3),
            "specializations": ["structural"]
        }

        # Mock vendor database
        mock_vendors = [
            VendorProfile(
                id="vendor_high_rating",
                name="Premium Inspections",
                vendor_type=VendorType.INSPECTOR,
                contact_email="premium@example.com",
                contact_phone="(555) 111-1111",
                license_number="LIC_HIGH",
                service_area=["Austin", "Round Rock"],
                rating=4.9,
                total_jobs=300,
                average_completion_time=2.0,
                pricing={"base_rate": Decimal("480.00")},
                availability_hours={"monday": "8:00-18:00"},
                specializations=["structural", "electrical"],
                performance_metrics={"on_time_percentage": 98.5}
            ),
            VendorProfile(
                id="vendor_budget",
                name="Budget Inspections",
                vendor_type=VendorType.INSPECTOR,
                contact_email="budget@example.com",
                contact_phone="(555) 222-2222",
                license_number="LIC_BUDGET",
                service_area=["Austin"],
                rating=4.3,  # Below min_rating
                total_jobs=150,
                average_completion_time=2.5,
                pricing={"base_rate": Decimal("350.00")},
                availability_hours={"monday": "9:00-17:00"}
            )
        ]

        mock_dependencies['cache_service'].get.return_value = mock_vendors

        result = await engine.get_vendor_recommendations(criteria)

        # Should only return vendors meeting criteria
        assert len(result) == 1
        assert result[0].id == "vendor_high_rating"
        assert result[0].rating >= 4.5
        assert "structural" in result[0].specializations

    @pytest.mark.asyncio
    async def test_schedule_appointment_success(self, engine, mock_dependencies):
        """Test successful appointment scheduling."""
        appointment_data = {
            "vendor_id": "vendor_123",
            "deal_id": "deal_456",
            "appointment_type": "inspection",
            "preferred_datetime": "2024-01-25T14:00:00",
            "property_address": "789 Elm Street, Austin, TX",
            "client_contact": {
                "name": "Jane Smith",
                "phone": "(555) 333-4444",
                "email": "jane@example.com"
            },
            "special_instructions": "Large dog on property - vendor should call ahead"
        }

        # Mock vendor profile
        mock_vendor = VendorProfile(
            id="vendor_123",
            name="Reliable Inspections",
            vendor_type=VendorType.INSPECTOR,
            contact_email="reliable@example.com",
            contact_phone="(555) 555-5555",
            license_number="LIC123",
            service_area=["Austin"],
            rating=4.7,
            total_jobs=180,
            average_completion_time=2.5,
            pricing={"base_rate": Decimal("425.00")},
            availability_hours={"friday": "8:00-16:00"}
        )

        mock_dependencies['cache_service'].get.return_value = mock_vendor

        # Mock calendar availability
        mock_dependencies['calendar_service'].check_vendor_availability.return_value = {
            "available": True,
            "confirmed_time": "2024-01-25T14:00:00"
        }

        # Mock appointment creation
        mock_dependencies['calendar_service'].create_vendor_appointment.return_value = {
            "success": True,
            "appointment_id": "appt_new_123",
            "calendar_event_id": "cal_event_456"
        }

        result = await engine.schedule_appointment(appointment_data)

        assert result["success"] is True
        assert result["appointment_id"] == "appt_new_123"
        assert result["vendor_name"] == "Reliable Inspections"
        assert result["scheduled_time"] == "2024-01-25T14:00:00"

        # Verify service calls
        mock_dependencies['calendar_service'].create_vendor_appointment.assert_called_once()
        mock_dependencies['notification_service'].send_appointment_confirmation.assert_called()

    @pytest.mark.asyncio
    async def test_update_appointment_status(self, engine, mock_dependencies):
        """Test appointment status updates."""
        appointment_id = "appt_update_test"
        new_status = AppointmentStatus.IN_PROGRESS

        # Mock existing appointment
        mock_appointment = VendorAppointment(
            id=appointment_id,
            vendor_id="vendor_456",
            deal_id="deal_789",
            appointment_type=VendorType.INSPECTOR,
            scheduled_date=datetime.now() + timedelta(hours=2),
            estimated_duration=180,
            status=AppointmentStatus.CONFIRMED,
            property_address="321 Pine Street, Austin, TX"
        )

        mock_dependencies['cache_service'].get.return_value = mock_appointment

        result = await engine.update_appointment_status(appointment_id, new_status,
                                                      {"started_at": datetime.now().isoformat()})

        assert result["success"] is True
        assert result["previous_status"] == AppointmentStatus.CONFIRMED.value
        assert result["new_status"] == AppointmentStatus.IN_PROGRESS.value

        # Verify cache update
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_track_vendor_performance(self, engine, mock_dependencies):
        """Test vendor performance tracking and metrics calculation."""
        vendor_id = "vendor_performance_test"

        # Mock completed appointments for performance calculation
        completed_appointments = [
            {
                "appointment_id": "appt_001",
                "scheduled_date": "2024-01-15T10:00:00",
                "actual_start": "2024-01-15T10:05:00",  # 5 min late
                "actual_end": "2024-01-15T12:30:00",
                "client_rating": 5,
                "completion_quality": "excellent"
            },
            {
                "appointment_id": "appt_002",
                "scheduled_date": "2024-01-18T14:00:00",
                "actual_start": "2024-01-18T13:58:00",  # 2 min early
                "actual_end": "2024-01-18T16:45:00",
                "client_rating": 4,
                "completion_quality": "good"
            }
        ]

        mock_dependencies['cache_service'].get.return_value = completed_appointments

        result = await engine.track_vendor_performance(vendor_id, period_days=30)

        assert result["vendor_id"] == vendor_id
        assert result["total_appointments"] == 2
        assert "average_rating" in result
        assert "on_time_percentage" in result
        assert "average_duration" in result

        # Performance should be calculated from mock data
        assert 4.0 <= result["average_rating"] <= 5.0

    @pytest.mark.asyncio
    async def test_handle_vendor_availability_conflict(self, engine, mock_dependencies):
        """Test handling of vendor scheduling conflicts."""
        conflict_data = {
            "appointment_id": "appt_conflict",
            "vendor_id": "vendor_busy",
            "new_requested_time": "2024-01-25T10:00:00",
            "reason": "emergency_inspection_required"
        }

        # Mock vendor with existing conflicts
        mock_dependencies['calendar_service'].check_vendor_availability.return_value = {
            "available": False,
            "conflicts": [
                {
                    "existing_appointment": "appt_existing",
                    "time": "2024-01-25T09:30:00",
                    "duration": 120
                }
            ],
            "alternative_slots": [
                "2024-01-25T13:00:00",
                "2024-01-26T10:00:00"
            ]
        }

        # Mock AI-powered conflict resolution
        mock_dependencies['claude_service'].generate_response.return_value = {
            "resolution_strategy": "reschedule_with_alternative",
            "recommended_time": "2024-01-26T10:00:00",
            "communication_message": "Due to an emergency inspection, we need to reschedule..."
        }

        result = await engine.handle_scheduling_conflict(conflict_data)

        assert result["conflict_resolved"] is True
        assert result["resolution_strategy"] == "reschedule_with_alternative"
        assert result["recommended_time"] == "2024-01-26T10:00:00"

    @pytest.mark.asyncio
    async def test_vendor_communication_automation(self, engine, mock_dependencies):
        """Test automated vendor communication workflows."""
        communication_request = {
            "vendor_id": "vendor_comm_test",
            "message_type": "appointment_reminder",
            "appointment_id": "appt_reminder",
            "send_time": datetime.now() + timedelta(hours=24),  # 24h before appointment
            "include_details": True
        }

        # Mock appointment details
        mock_appointment = VendorAppointment(
            id="appt_reminder",
            vendor_id="vendor_comm_test",
            deal_id="deal_reminder",
            appointment_type=VendorType.INSPECTOR,
            scheduled_date=datetime.now() + timedelta(days=2),
            estimated_duration=180,
            status=AppointmentStatus.CONFIRMED,
            property_address="555 Cedar Lane, Austin, TX",
            client_contact={"name": "Bob Johnson", "phone": "(555) 777-8888"}
        )

        mock_dependencies['cache_service'].get.return_value = mock_appointment

        # Mock communication service
        mock_dependencies['notification_service'].schedule_vendor_communication.return_value = {
            "success": True,
            "scheduled_message_id": "msg_scheduled_123",
            "delivery_time": communication_request["send_time"].isoformat()
        }

        result = await engine.schedule_vendor_communication(communication_request)

        assert result["success"] is True
        assert result["scheduled_message_id"] == "msg_scheduled_123"

        # Verify communication scheduling
        mock_dependencies['notification_service'].schedule_vendor_communication.assert_called_once()

    @pytest.mark.asyncio
    async def test_vendor_onboarding_workflow(self, engine, mock_dependencies):
        """Test vendor onboarding and verification workflow."""
        onboarding_data = {
            "vendor_name": "New Inspection Company",
            "vendor_type": "inspector",
            "contact_email": "contact@newinspections.com",
            "contact_phone": "(555) 999-0000",
            "license_number": "LIC_NEW_123",
            "service_areas": ["Austin", "Georgetown"],
            "specializations": ["residential", "commercial"],
            "pricing_structure": {
                "residential_base": 425.00,
                "commercial_base": 650.00,
                "rush_fee": 150.00
            },
            "availability_schedule": {
                "monday": "8:00-17:00",
                "tuesday": "8:00-17:00",
                "wednesday": "8:00-17:00",
                "thursday": "8:00-17:00",
                "friday": "8:00-16:00"
            }
        }

        # Mock license verification
        mock_dependencies['claude_service'].verify_vendor_credentials.return_value = {
            "license_valid": True,
            "license_expiry": "2025-12-31",
            "verification_score": 0.92
        }

        # Mock background check
        mock_dependencies['cache_service'].get.return_value = None  # No existing vendor

        result = await engine.onboard_new_vendor(onboarding_data)

        assert result["success"] is True
        assert result["vendor_id"] is not None
        assert result["verification_status"] == "verified"
        assert result["onboarding_stage"] == "completed"

        # Verify vendor profile creation
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_vendor_performance_analytics(self, engine, mock_dependencies):
        """Test vendor performance analytics and insights."""
        analytics_request = {
            "vendor_ids": ["vendor_001", "vendor_002", "vendor_003"],
            "time_period": "last_90_days",
            "metrics": ["completion_rate", "client_satisfaction", "punctuality", "quality"]
        }

        # Mock aggregated performance data
        mock_performance_data = {
            "vendor_001": {
                "total_jobs": 45,
                "completion_rate": 98.2,
                "average_rating": 4.8,
                "on_time_percentage": 96.7,
                "quality_score": 4.9
            },
            "vendor_002": {
                "total_jobs": 38,
                "completion_rate": 94.7,
                "average_rating": 4.5,
                "on_time_percentage": 89.5,
                "quality_score": 4.6
            },
            "vendor_003": {
                "total_jobs": 52,
                "completion_rate": 96.2,
                "average_rating": 4.7,
                "on_time_percentage": 94.2,
                "quality_score": 4.8
            }
        }

        mock_dependencies['cache_service'].get.return_value = mock_performance_data

        result = await engine.generate_vendor_analytics(analytics_request)

        assert len(result["vendor_analytics"]) == 3
        assert result["summary"]["top_performer"] == "vendor_001"  # Highest overall score
        assert result["summary"]["average_completion_rate"] > 90
        assert "performance_trends" in result

    @pytest.mark.asyncio
    async def test_emergency_vendor_coordination(self, engine, mock_dependencies):
        """Test emergency vendor coordination and rapid response."""
        emergency_request = {
            "deal_id": "deal_emergency",
            "emergency_type": "structural_damage_discovered",
            "urgency_level": "critical",
            "required_response_time": "within_2_hours",
            "property_address": "999 Emergency Lane, Austin, TX",
            "situation_description": "Potential foundation issues discovered during showing",
            "required_vendor_types": ["structural_engineer", "inspector"],
            "budget_authorization": "unlimited"
        }

        # Mock emergency vendor network
        emergency_vendors = [
            VendorProfile(
                id="vendor_emergency_001",
                name="Emergency Structural Solutions",
                vendor_type=VendorType.STRUCTURAL_ENGINEER,
                contact_email="emergency@structural.com",
                contact_phone="(555) 911-0000",
                license_number="STRUCT_EMG_001",
                service_area=["Austin", "Travis County"],
                rating=4.9,
                total_jobs=75,
                average_completion_time=1.0,  # Very fast response
                pricing={"emergency_rate": Decimal("750.00")},
                availability_hours={"24/7": "emergency_only"},
                specializations=["emergency_response", "foundation", "structural"]
            )
        ]

        with patch.object(engine, '_get_emergency_vendors', return_value=emergency_vendors):
            mock_dependencies['calendar_service'].create_emergency_appointment.return_value = {
                "success": True,
                "appointment_id": "appt_emergency_123",
                "response_time": "45_minutes",
                "vendor_eta": "2024-01-20T15:45:00"
            }

            result = await engine.coordinate_emergency_response(emergency_request)

        assert result["success"] is True
        assert result["response_time"] == "45_minutes"
        assert result["vendors_dispatched"] == 1
        assert result["emergency_protocol_activated"] is True

    def test_vendor_rating_calculation(self, engine):
        """Test vendor rating calculation algorithm."""
        # Mock rating data
        ratings = [5, 4, 5, 4, 5, 3, 4, 5, 4, 5]  # Average should be 4.4

        calculated_rating = engine._calculate_vendor_rating(ratings)

        assert 4.3 <= calculated_rating <= 4.5
        assert isinstance(calculated_rating, float)

    def test_service_area_matching(self, engine):
        """Test service area matching logic."""
        vendor_service_areas = ["Austin", "Round Rock", "Cedar Park"]
        property_location = "Round Rock, TX"

        is_match = engine._is_service_area_match(vendor_service_areas, property_location)

        assert is_match is True

        # Test non-matching area
        property_location_no_match = "Houston, TX"
        is_no_match = engine._is_service_area_match(vendor_service_areas, property_location_no_match)

        assert is_no_match is False

    def test_pricing_calculation(self, engine):
        """Test dynamic pricing calculation."""
        base_pricing = {"base_rate": Decimal("450.00"), "rush_fee": Decimal("100.00")}
        service_details = {
            "urgency": "rush",
            "property_size": "large",
            "complexity": "standard",
            "weekend_service": False
        }

        calculated_price = engine._calculate_service_pricing(base_pricing, service_details)

        # Should include rush fee
        expected_price = Decimal("550.00")  # 450 + 100 rush fee
        assert calculated_price == expected_price


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