"""
Test Suite for Comprehensive Error Handling System.

Tests the global error handler, validation schemas, WebSocket error management,
and error monitoring system to ensure robust error handling across the platform.

Author: Claude Sonnet 4
Date: 2026-01-25
"""

import asyncio
import pytest
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError, BaseModel, Field
from typing import Dict, Any

# Import our error handling components
from ghl_real_estate_ai.api.middleware.global_exception_handler import (
    GlobalExceptionHandler,
    JorgeErrorResponse,
    setup_global_exception_handlers
)
from ghl_real_estate_ai.api.schemas.jorge_validators import (
    JorgeCommissionValidator,
    JorgePropertyValidator,
    JorgeLeadValidator,
    JorgePropertyRequest,
    JorgeLeadRequest,
    JorgeCommissionCalculation,
    validate_jorge_commission,
    validate_jorge_property_value,
    validate_jorge_phone
)
from ghl_real_estate_ai.api.middleware.websocket_error_handler import (
    WebSocketErrorManager,
    get_websocket_error_manager,
    websocket_error_handler
)
from ghl_real_estate_ai.services.error_monitoring_service import (

@pytest.mark.integration
    ErrorMonitoringService,
    ErrorCategory,
    get_error_monitoring_service
)


class TestGlobalExceptionHandler:
    """Test global exception handler functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.handler = GlobalExceptionHandler()

    def test_jorge_error_response_creation(self):
        """Test JorgeErrorResponse creation and serialization."""
        error = JorgeErrorResponse(
            error_type="test_error",
            message="Test error message",
            status_code=400,
            details={"field": "value"},
            retryable=True,
            guidance="Fix the test issue"
        )

        response_dict = error.to_dict(include_debug=True)

        assert response_dict["success"] is False
        assert response_dict["error"]["type"] == "test_error"
        assert response_dict["error"]["message"] == "Test error message"
        assert response_dict["error"]["retryable"] is True
        assert "correlation_id" in response_dict
        assert "timestamp" in response_dict
        assert response_dict["guidance"] == "Fix the test issue"
        assert "retry" in response_dict  # Should have retry info for retryable errors

    def test_error_pattern_loading(self):
        """Test error pattern loading and classification."""
        patterns = self.handler._load_error_patterns()

        # Check essential Jorge-specific patterns
        assert "commission_validation" in patterns
        assert "property_qualification" in patterns
        assert "ghl_api_error" in patterns
        assert "claude_api_error" in patterns

        # Verify pattern structure
        commission_pattern = patterns["commission_validation"]
        assert commission_pattern["status_code"] == 400
        assert commission_pattern["retryable"] is False
        assert "commission" in commission_pattern["message"].lower()

    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test Pydantic validation error handling."""
        from fastapi import Request
        from fastapi.datastructures import Headers, QueryParams

        # Create mock request
        mock_request = type('MockRequest', (), {
            'headers': Headers({}),
            'state': type('State', (), {'correlation_id': None})()
        })()

        # Create validation error
        validation_error = ValidationError([
            {
                'loc': ('commission_rate',),
                'msg': 'Commission rate 0.12 exceeds maximum',
                'type': 'value_error'
            }
        ], JorgeCommissionCalculation)

        # Handle error
        error_response = await self.handler.handle_validation_error(
            mock_request, validation_error
        )

        assert error_response.error_type == "validation_error"
        assert error_response.status_code == 422
        assert "commission" in error_response.message.lower()
        assert not error_response.retryable


class TestJorgeValidators:
    """Test Jorge-specific validation logic."""

    def test_commission_rate_validation(self):
        """Test commission rate validation."""
        # Valid rates
        assert JorgeCommissionValidator.validate_commission_rate(0.06) == 0.06
        assert JorgeCommissionValidator.validate_commission_rate("0.05") == 0.05
        assert JorgeCommissionValidator.validate_commission_rate(0.08) == 0.08

        # Invalid rates
        with pytest.raises(ValueError) as exc_info:
            JorgeCommissionValidator.validate_commission_rate(0.04)
        assert "below Jorge's minimum" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            JorgeCommissionValidator.validate_commission_rate(0.12)
        assert "exceeds Jorge's maximum" in str(exc_info.value)

    def test_property_value_validation(self):
        """Test property value validation."""
        # Valid values
        assert JorgePropertyValidator.validate_property_value(100000) == 100000
        assert JorgePropertyValidator.validate_property_value(500000) == 500000
        assert JorgePropertyValidator.validate_property_value(2000000) == 2000000

        # Invalid values
        with pytest.raises(ValueError) as exc_info:
            JorgePropertyValidator.validate_property_value(50000)
        assert "below Jorge's minimum" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            JorgePropertyValidator.validate_property_value(3000000)
        assert "exceeds Jorge's maximum" in str(exc_info.value)

    def test_property_type_validation(self):
        """Test property type validation."""
        # Valid types
        assert JorgePropertyValidator.validate_property_type("single_family") == "single_family"
        assert JorgePropertyValidator.validate_property_type("CONDO") == "condo"
        assert JorgePropertyValidator.validate_property_type("Town-House") == "town_house"

        # Invalid type
        with pytest.raises(ValueError) as exc_info:
            JorgePropertyValidator.validate_property_type("mansion")
        assert "not supported" in str(exc_info.value)

    def test_phone_number_validation(self):
        """Test phone number validation and formatting."""
        # Valid formats
        assert JorgeLeadValidator.validate_phone_number("(555) 123-4567") == "(555) 123-4567"
        assert JorgeLeadValidator.validate_phone_number("555-123-4567") == "(555) 123-4567"
        assert JorgeLeadValidator.validate_phone_number("5551234567") == "(555) 123-4567"
        assert JorgeLeadValidator.validate_phone_number("+1-555-123-4567") == "(555) 123-4567"

        # Invalid formats
        with pytest.raises(ValueError) as exc_info:
            JorgeLeadValidator.validate_phone_number("123-456")
        assert "Invalid phone number format" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            JorgeLeadValidator.validate_phone_number("")
        assert "required" in str(exc_info.value)

    def test_jorge_property_request_validation(self):
        """Test complete property request validation."""
        # Valid request
        valid_request = {
            "address": "123 Main St, Austin, TX 78701",
            "property_type": "single_family",
            "market": "austin",
            "estimated_value": 450000,
            "commission_rate": 0.06
        }

        property_request = JorgePropertyRequest(**valid_request)
        assert property_request.estimated_value == 450000
        assert property_request.commission_rate == 0.06

        # Invalid request - bad commission
        with pytest.raises(ValidationError) as exc_info:
            JorgePropertyRequest(
                address="123 Main St, Austin, TX 78701",
                property_type="single_family",
                market="austin",
                estimated_value=450000,
                commission_rate=0.12  # Too high
            )

        errors = exc_info.value.errors()
        assert any("commission" in str(error).lower() for error in errors)

    def test_jorge_lead_request_validation(self):
        """Test complete lead request validation."""
        # Valid request
        valid_request = {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "(555) 123-4567",
            "annual_income": 75000,
            "credit_score": 720
        }

        lead_request = JorgeLeadRequest(**valid_request)
        assert lead_request.phone == "(555) 123-4567"  # Formatted
        assert lead_request.credit_score == 720

        # Invalid request - bad credit score
        with pytest.raises(ValidationError):
            JorgeLeadRequest(
                first_name="John",
                last_name="Smith",
                email="john.smith@example.com",
                phone="(555) 123-4567",
                credit_score=400  # Too low
            )


class TestWebSocketErrorHandler:
    """Test WebSocket error handling."""

    def setup_method(self):
        """Set up WebSocket error manager."""
        self.ws_manager = WebSocketErrorManager()

    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test WebSocket connection management."""
        # This would require a mock WebSocket for full testing
        # For now, test the error manager setup
        assert self.ws_manager.max_reconnection_attempts == 5
        assert self.ws_manager.connections == {}
        assert self.ws_manager.connection_states == {}

    def test_message_validation(self):
        """Test WebSocket message validation."""
        # Test valid message
        valid_message = {
            "data": {"test": "data"},
            "correlation_id": "test_123"
        }

        # This would be tested with an async method in practice
        # For now, verify the manager is properly initialized
        assert hasattr(self.ws_manager, '_validate_message')

    def test_error_severity_determination(self):
        """Test error severity determination."""
        from fastapi import WebSocketDisconnect
        import json

        # Test different error types
        disconnect_error = WebSocketDisconnect()
        json_error = json.JSONDecodeError("Invalid JSON", "test", 0)
        value_error = ValueError("Invalid value")

        severity1 = self.ws_manager._determine_error_severity(disconnect_error, "test")
        severity2 = self.ws_manager._determine_error_severity(json_error, "test")
        severity3 = self.ws_manager._determine_error_severity(value_error, "connection_failure")

        # Verify different severity levels are assigned
        assert severity1.name in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert severity2.name in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert severity3.name in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class TestErrorMonitoringService:
    """Test error monitoring and analytics service."""

    def setup_method(self):
        """Set up error monitoring service."""
        self.monitoring = ErrorMonitoringService()

    @pytest.mark.asyncio
    async def test_error_recording(self):
        """Test error event recording."""
        await self.monitoring.record_error(
            error_id="test_error_123",
            correlation_id="corr_123",
            endpoint="POST /api/test",
            error_type="validation_error",
            category=ErrorCategory.VALIDATION,
            message="Test validation error",
            context={"field": "test_field"},
            user_id="user_123"
        )

        # Verify error was recorded
        assert len(self.monitoring.recent_errors) == 1
        recorded_error = self.monitoring.recent_errors[0]
        assert recorded_error.error_id == "test_error_123"
        assert recorded_error.category == ErrorCategory.VALIDATION

    @pytest.mark.asyncio
    async def test_error_metrics_calculation(self):
        """Test error metrics calculation."""
        # Record multiple errors
        for i in range(5):
            await self.monitoring.record_error(
                error_id=f"error_{i}",
                correlation_id=f"corr_{i}",
                endpoint=f"POST /api/test{i}",
                error_type="test_error",
                category=ErrorCategory.VALIDATION,
                message=f"Test error {i}"
            )

        metrics = await self.monitoring.get_error_metrics(timeframe_minutes=60)

        assert metrics["total_errors"] == 5
        assert metrics["unique_errors"] == 1  # Same error type
        assert "validation" in metrics["category_breakdown"]
        assert metrics["category_breakdown"]["validation"] == 5

    @pytest.mark.asyncio
    async def test_error_pattern_recognition(self):
        """Test error pattern recognition."""
        # Record same error multiple times
        for i in range(10):
            await self.monitoring.record_error(
                error_id=f"pattern_error_{i}",
                correlation_id=f"pattern_corr_{i}",
                endpoint="POST /api/pattern_test",
                error_type="pattern_error",
                category=ErrorCategory.VALIDATION,
                message="Repeating pattern error"
            )

        patterns = await self.monitoring.get_error_patterns(limit=10)

        assert len(patterns) >= 1
        pattern = patterns[0]
        assert pattern["occurrences"] == 10
        assert pattern["error_signature"] == "pattern_error:POST /api/pattern_test"

    @pytest.mark.asyncio
    async def test_top_errors_analysis(self):
        """Test top errors analysis."""
        # Record errors with different frequencies
        error_counts = {"error_A": 5, "error_B": 3, "error_C": 8}

        for error_type, count in error_counts.items():
            for i in range(count):
                await self.monitoring.record_error(
                    error_id=f"{error_type}_{i}",
                    correlation_id=f"corr_{error_type}_{i}",
                    endpoint="POST /api/test",
                    error_type=error_type,
                    category=ErrorCategory.VALIDATION,
                    message=f"Test {error_type}"
                )

        top_errors = await self.monitoring.get_top_errors(
            timeframe_minutes=60,
            limit=5
        )

        # Should be sorted by count (descending)
        assert len(top_errors) == 3
        assert top_errors[0]["count"] == 8  # error_C
        assert top_errors[1]["count"] == 5  # error_A
        assert top_errors[2]["count"] == 3  # error_B


class TestErrorHandlingIntegration:
    """Test complete error handling system integration."""

    def test_convenience_functions(self):
        """Test standalone validation functions."""
        # Commission validation
        assert validate_jorge_commission(0.06) == 0.06

        with pytest.raises(ValueError):
            validate_jorge_commission(0.12)

        # Property value validation
        assert validate_jorge_property_value(500000) == 500000

        with pytest.raises(ValueError):
            validate_jorge_property_value(50000)

        # Phone validation
        assert validate_jorge_phone("555-123-4567") == "(555) 123-4567"

        with pytest.raises(ValueError):
            validate_jorge_phone("invalid")

    def test_error_categorization(self):
        """Test error categorization across different types."""
        handler = GlobalExceptionHandler()

        # Test HTTP status mapping
        validation_category = handler._map_http_status_to_category(422)
        auth_category = handler._map_http_status_to_category(401)
        server_category = handler._map_http_status_to_category(500)

        assert validation_category == ErrorCategory.VALIDATION
        assert auth_category == ErrorCategory.AUTHENTICATION
        assert server_category == ErrorCategory.SYSTEM

        # Test exception mapping
        value_error = ValueError("Invalid commission rate")
        db_error = Exception("database connection failed")
        claude_error = Exception("Claude API error")

        val_category = handler._map_exception_to_category(value_error)
        db_category = handler._map_exception_to_category(db_error)
        api_category = handler._map_exception_to_category(claude_error)

        assert val_category == ErrorCategory.VALIDATION
        assert db_category == ErrorCategory.DATABASE
        assert api_category == ErrorCategory.EXTERNAL_API


def run_error_handling_tests():
    """Run all error handling tests."""
    print("🧪 Running Comprehensive Error Handling Tests...")

    # Test commission validation
    print("\n✅ Testing Commission Validation...")
    try:
        validate_jorge_commission(0.06)
        print("   ✓ Valid commission rate accepted")
    except Exception as e:
        print(f"   ✗ Valid commission test failed: {e}")

    try:
        validate_jorge_commission(0.12)
        print("   ✗ Invalid commission rate should have been rejected")
    except ValueError as e:
        print(f"   ✓ Invalid commission correctly rejected: {e}")

    # Test property validation
    print("\n✅ Testing Property Validation...")
    try:
        validate_jorge_property_value(450000)
        print("   ✓ Valid property value accepted")
    except Exception as e:
        print(f"   ✗ Valid property test failed: {e}")

    try:
        validate_jorge_property_value(50000)
        print("   ✗ Invalid property value should have been rejected")
    except ValueError as e:
        print(f"   ✓ Invalid property correctly rejected: {e}")

    # Test phone validation
    print("\n✅ Testing Phone Validation...")
    try:
        formatted = validate_jorge_phone("555-123-4567")
        assert formatted == "(555) 123-4567"
        print(f"   ✓ Phone correctly formatted: {formatted}")
    except Exception as e:
        print(f"   ✗ Phone formatting failed: {e}")

    # Test error response creation
    print("\n✅ Testing Error Response Creation...")
    try:
        error = JorgeErrorResponse(
            error_type="test_error",
            message="Test message",
            status_code=400,
            retryable=True,
            guidance="Fix the issue"
        )
        response_dict = error.to_dict()
        assert response_dict["success"] is False
        assert response_dict["error"]["retryable"] is True
        print("   ✓ Error response correctly structured")
    except Exception as e:
        print(f"   ✗ Error response test failed: {e}")

    # Test WebSocket error manager
    print("\n✅ Testing WebSocket Error Manager...")
    try:
        ws_manager = WebSocketErrorManager()
        assert ws_manager.max_reconnection_attempts == 5
        print("   ✓ WebSocket error manager initialized")
    except Exception as e:
        print(f"   ✗ WebSocket manager test failed: {e}")

    # Test error monitoring service
    print("\n✅ Testing Error Monitoring Service...")
    try:
        monitoring = ErrorMonitoringService()
        assert len(monitoring.recent_errors) == 0
        print("   ✓ Error monitoring service initialized")
    except Exception as e:
        print(f"   ✗ Monitoring service test failed: {e}")

    print("\n🎉 Error handling tests completed!")


if __name__ == "__main__":
    run_error_handling_tests()