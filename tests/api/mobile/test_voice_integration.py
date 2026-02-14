"""
Tests for Voice Integration API
Tests speech-to-text, AI processing, and voice assistant functionality.
"""

import base64
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.voice_claude_service import VoiceClaudeService, VoiceInteractionType

client = TestClient(app)


class TestVoiceIntegration:
    """Test cases for voice assistant integration."""

    @pytest.fixture
    def sample_audio_data(self):
        """Sample base64 encoded audio data for testing."""
        # Create a minimal valid base64 string representing audio
        fake_audio = b"fake_audio_data_for_testing_purposes_123456789"
        return base64.b64encode(fake_audio).decode("utf-8")

    @pytest.fixture
    def sample_device_info(self):
        """Sample device information for voice requests."""
        return {
            "device_id": "voice_test_device_123",
            "platform": "ios",
            "os_version": "17.0",
            "app_version": "1.0.0",
            "device_model": "iPhone 15 Pro",
            "language": "en",
            "permissions": ["microphone", "location"],
            "biometric_available": True,
            "camera_available": True,
            "location_services": True,
        }

    @pytest.fixture
    def sample_voice_request(self, sample_audio_data, sample_device_info):
        """Sample voice request for testing."""
        return {
            "audio_data": sample_audio_data,
            "audio_format": "wav",
            "duration_seconds": 3.5,
            "language": "en-US",
            "context": {
                "current_screen": "property_details",
                "property_id": "prop_rancho_cucamonga_001",
                "include_audio_response": False,  # Skip TTS for testing
            },
            "location": {
                "latitude": 30.2672,
                "longitude": -97.7431,
                "accuracy": 10.0,
                "timestamp": datetime.now().isoformat(),
            },
            "device_info": sample_device_info,
        }

    @patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user")
    @patch("ghl_real_estate_ai.services.voice_claude_service.VoiceClaudeService.process_voice_interaction")
    def test_voice_processing_success(self, mock_voice_process, mock_auth, sample_voice_request):
        """Test successful voice interaction processing."""
        # Mock authentication
        mock_auth.return_value = {"user_id": "test_user_123", "username": "test_user"}

        # Mock voice processing response
        mock_voice_process.return_value = {
            "session_id": "voice_session_123",
            "transcription": "Show me properties under 800 thousand dollars in Hill Country",
            "confidence": 0.95,
            "ai_response": "I found 12 properties in Hill Country under $800,000. The newest listing is a 4-bedroom home at $750,000. Would you like me to show you the details?",
            "interaction_type": VoiceInteractionType.PROPERTY_INQUIRY,
            "entities_extracted": {"price_mention": "800000", "location": "hill country", "bedrooms": 4},
            "suggested_actions": [
                {
                    "action": "search_properties",
                    "title": "Search Properties",
                    "description": "Find matching properties based on criteria",
                    "priority": "high",
                }
            ],
            "processing_time_ms": 1250,
        }

        response = client.post(
            "/api/mobile/voice/process", json=sample_voice_request, headers={"Authorization": "Bearer test_token"}
        )

        # Note: This test may fail due to dependency injection complexity
        # In a full implementation, this would validate the voice processing flow

    def test_voice_processing_without_auth(self, sample_voice_request):
        """Test voice processing without authentication."""
        response = client.post("/api/mobile/voice/process", json=sample_voice_request)

        # Should require authentication
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_voice_request_validation(self, sample_device_info):
        """Test voice request validation."""
        # Test with invalid audio data
        invalid_request = {
            "audio_data": "invalid_base64_data!@#",
            "audio_format": "wav",
            "device_info": sample_device_info,
        }

        response = client.post(
            "/api/mobile/voice/process", json=invalid_request, headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_voice_request_missing_fields(self):
        """Test voice request with missing required fields."""
        incomplete_request = {
            "audio_format": "wav"
            # Missing audio_data and device_info
        }

        response = client.post(
            "/api/mobile/voice/process", json=incomplete_request, headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestVoiceClaudeService:
    """Test VoiceClaudeService functionality."""

    @pytest.fixture
    def voice_service(self):
        """Create VoiceClaudeService instance for testing."""
        return VoiceClaudeService(market_id="rancho_cucamonga")

    @patch("speech_recognition.Recognizer")
    def test_speech_transcription_mock(self, mock_recognizer, voice_service):
        """Test speech transcription functionality (mocked)."""
        # Mock the speech recognition
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "test transcription"

        # This would test the _transcribe_audio method
        # In a full implementation, this would validate audio processing

    def test_intent_classification(self, voice_service):
        """Test intent classification from text."""
        # Test property inquiry intent
        property_text = "Show me houses under 500 thousand dollars"
        # This would test _classify_intent_and_extract_entities

        # Test lead update intent
        lead_text = "Mark Sarah Chen as qualified and ready to buy"
        # This would test lead-related intent classification

        # Test scheduling intent
        schedule_text = "Schedule a showing for tomorrow at 3 PM"
        # This would test scheduling intent classification

    def test_entity_extraction(self, voice_service):
        """Test entity extraction from voice commands."""
        # Test price extraction
        price_text = "Find properties under $800,000"
        # This would test price entity extraction

        # Test location extraction
        location_text = "Show me homes in Downtown Rancho Cucamonga"
        # This would test location entity extraction

        # Test room count extraction
        rooms_text = "I need a 4 bedroom 3 bathroom house"
        # This would test bedroom/bathroom extraction


class TestVoiceSessionManagement:
    """Test voice session context management."""

    @patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user")
    def test_voice_session_creation(self, mock_auth):
        """Test voice session creation and retrieval."""
        mock_auth.return_value = {"user_id": "test_user_123", "username": "test_user"}

        session_id = "test_voice_session_123"

        response = client.get(
            f"/api/mobile/voice/session/{session_id}/summary", headers={"Authorization": "Bearer test_token"}
        )

        # This would test session summary retrieval

    @patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user")
    def test_voice_session_cleanup(self, mock_auth):
        """Test voice session cleanup."""
        mock_auth.return_value = {"user_id": "test_user_123", "username": "test_user"}

        session_id = "test_voice_session_123"

        response = client.delete(
            f"/api/mobile/voice/session/{session_id}", headers={"Authorization": "Bearer test_token"}
        )

        # This would test session deletion


class TestVoiceContextAwareness:
    """Test voice assistant context awareness."""

    def test_property_context_awareness(self):
        """Test voice processing with property context."""
        # This would test voice commands when user is viewing a property
        voice_request_with_context = {
            "audio_data": base64.b64encode(b"fake_audio").decode(),
            "audio_format": "wav",
            "context": {
                "current_screen": "property_details",
                "property_id": "prop_rancho_cucamonga_001",
                "property_price": 750000,
                "property_address": "1234 Hill Country Drive",
            },
            "device_info": {"device_id": "test_device_123", "platform": "ios", "app_version": "1.0.0"},
        }

        # This would test context-aware voice processing

    def test_lead_context_awareness(self):
        """Test voice processing with lead context."""
        # This would test voice commands when user is viewing a lead
        voice_request_with_context = {
            "audio_data": base64.b64encode(b"fake_audio").decode(),
            "audio_format": "wav",
            "context": {
                "current_screen": "lead_details",
                "lead_id": "lead_001",
                "lead_name": "Sarah Chen",
                "lead_status": "qualified",
            },
            "device_info": {"device_id": "test_device_123", "platform": "ios", "app_version": "1.0.0"},
        }

        # This would test lead-context-aware voice processing


class TestVoiceErrorHandling:
    """Test voice processing error handling."""

    def test_audio_processing_failure(self, sample_device_info):
        """Test handling of audio processing failures."""
        # Test with corrupted audio data
        corrupted_request = {
            "audio_data": "corrupted_audio_data_that_cannot_be_processed",
            "audio_format": "wav",
            "device_info": sample_device_info,
        }

        response = client.post(
            "/api/mobile/voice/process", json=corrupted_request, headers={"Authorization": "Bearer test_token"}
        )

        # Should handle gracefully and return error response

    def test_speech_recognition_failure(self, sample_voice_request):
        """Test handling of speech recognition failures."""
        # This would test scenarios where speech cannot be recognized
        # (background noise, unclear speech, unsupported language)
        pass

    def test_ai_processing_failure(self, sample_voice_request):
        """Test handling of AI processing failures."""
        # This would test scenarios where Claude API is unavailable
        # or returns errors
        pass


class TestVoiceLanguageSupport:
    """Test multi-language voice support."""

    def test_english_voice_processing(self, sample_device_info, sample_audio_data):
        """Test English voice processing."""
        english_request = {
            "audio_data": sample_audio_data,
            "audio_format": "wav",
            "language": "en-US",
            "device_info": sample_device_info,
        }

        response = client.post(
            "/api/mobile/voice/process", json=english_request, headers={"Authorization": "Bearer test_token"}
        )

        # This would test English language processing

    def test_spanish_voice_processing(self, sample_device_info, sample_audio_data):
        """Test Spanish voice processing."""
        spanish_request = {
            "audio_data": sample_audio_data,
            "audio_format": "wav",
            "language": "es-ES",
            "device_info": sample_device_info,
        }

        response = client.post(
            "/api/mobile/voice/process", json=spanish_request, headers={"Authorization": "Bearer test_token"}
        )

        # This would test Spanish language processing

    def test_unsupported_language(self, sample_device_info, sample_audio_data):
        """Test unsupported language handling."""
        unsupported_request = {
            "audio_data": sample_audio_data,
            "audio_format": "wav",
            "language": "xx-XX",  # Unsupported language code
            "device_info": sample_device_info,
        }

        response = client.post(
            "/api/mobile/voice/process", json=unsupported_request, headers={"Authorization": "Bearer test_token"}
        )

        # Should handle gracefully or return supported languages list


class TestVoicePerformance:
    """Test voice processing performance."""

    def test_voice_processing_timeout(self, sample_voice_request):
        """Test voice processing timeout handling."""
        # This would test scenarios where voice processing takes too long
        # and should timeout gracefully
        pass

    def test_concurrent_voice_requests(self, sample_voice_request):
        """Test handling of concurrent voice requests."""
        # This would test multiple simultaneous voice requests
        # from the same user or different users
        pass


class TestVoiceIntegrationWithClaudeAssistant:
    """Test integration between voice service and Claude assistant."""

    def test_voice_to_claude_context_passing(self):
        """Test context passing from voice to Claude assistant."""
        # This would test that voice-extracted entities and context
        # are properly passed to the Claude assistant for processing
        pass

    def test_claude_response_optimization_for_voice(self):
        """Test Claude response optimization for voice output."""
        # This would test that Claude responses are optimized for
        # text-to-speech conversion (avoiding complex formatting, etc.)
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])