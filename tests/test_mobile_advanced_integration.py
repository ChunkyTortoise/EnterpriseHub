"""
Comprehensive Tests for Mobile Advanced Integration (Phase 5)

Tests for mobile platform integration including:
- Advanced mobile integration service
- Mobile advanced features service
- Touch gesture recognition
- Voice command processing
- Multi-language mobile support
- Behavioral predictions on mobile
- Performance optimization
- Offline capabilities
- Battery efficiency
- Cross-platform synchronization
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

# Import mobile services for testing
try:
    from ghl_real_estate_ai.services.claude.mobile import (
        AdvancedMobileIntegrationService,
        MobileAdvancedFeaturesService,
        MobileAdvancedFeatureType,
        MobilePlatformMode,
        MobileDeviceCapability,
        MobileAdvancedContext,
        MobileAdvancedResponse,
        MobilePersonalizationProfile,
        TouchGestureType,
        VoiceCommandType,
        MobileNotificationType,
        TouchGestureEvent,
        VoiceCommandEvent,
        MobileNotification,
        TouchOptimizedUI,
        OfflineCapability,
        OfflineCapabilityLevel
    )
    from ghl_real_estate_ai.services.claude.advanced.multi_language_voice_service import (
        SupportedLanguage, CulturalContext
    )
    from ghl_real_estate_ai.config.mobile.settings import (
        ADVANCED_MOBILE_CONFIG,
        TOUCH_GESTURE_CONFIG,
        VOICE_COMMAND_CONFIG
    )
    MOBILE_SERVICES_AVAILABLE = True
except ImportError:
    MOBILE_SERVICES_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not MOBILE_SERVICES_AVAILABLE,
    reason="Mobile services not available"
)


class TestAdvancedMobileIntegrationService:
    """Test Advanced Mobile Integration Service"""

    @pytest.fixture
    async def mobile_integration_service(self):
        """Create mobile integration service for testing"""
        service = AdvancedMobileIntegrationService()
        await service._initialize_mobile_platform()
        yield service

    @pytest.fixture
    def sample_mobile_context(self):
        """Create sample mobile context"""
        return MobileAdvancedContext(
            user_id="test_user_123",
            session_id="test_session_456",
            platform_mode=MobilePlatformMode.FULL_FEATURES,
            device_capability=MobileDeviceCapability.HIGH_END,
            preferred_language=SupportedLanguage.ENGLISH_US,
            cultural_context=CulturalContext.NORTH_AMERICAN,
            device_info={
                "model": "iPhone 15 Pro",
                "screen_size": "6.1 inches",
                "os_version": "iOS 17.2",
                "memory_gb": 8
            },
            network_info={
                "status": "wifi",
                "speed_mbps": 100,
                "latency_ms": 20
            },
            battery_info={
                "level": 0.75,
                "charging": False,
                "health": 0.95
            }
        )

    @pytest.mark.asyncio
    async def test_start_advanced_mobile_session(self, mobile_integration_service, sample_mobile_context):
        """Test starting advanced mobile session"""
        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        assert session_id is not None
        assert session_id.startswith("advanced_mobile_test_user_123_")
        assert session_id in mobile_integration_service.active_mobile_sessions

        session = mobile_integration_service.active_mobile_sessions[session_id]
        assert session['user_id'] == "test_user_123"
        assert session['context'] == sample_mobile_context
        assert session['platform_mode'] == MobilePlatformMode.FULL_FEATURES
        assert session['personalization_applied'] is True

    @pytest.mark.asyncio
    async def test_multi_language_mobile_integration(self, mobile_integration_service, sample_mobile_context):
        """Test multi-language mobile integration"""
        # Start session
        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        # Test multi-language coaching
        response = await mobile_integration_service.integrate_multi_language_mobile(
            session_id=session_id,
            conversation_context="Client asking about property prices",
            client_message="What's the price range for condos here?",
            target_language=SupportedLanguage.SPANISH_MX
        )

        assert isinstance(response, MobileAdvancedResponse)
        assert response.feature_type == MobileAdvancedFeatureType.MULTI_LANGUAGE_COACHING
        assert response.processing_time_ms < 200  # Performance target
        assert response.confidence_score > 0.8
        assert 'coaching_text' in response.response_data
        assert 'language' in response.response_data
        assert 'cultural_context' in response.response_data

    @pytest.mark.asyncio
    async def test_behavioral_predictions_mobile(self, mobile_integration_service, sample_mobile_context):
        """Test behavioral predictions mobile integration"""
        # Start session
        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        # Test behavioral predictions
        conversation_history = [
            {"speaker": "agent", "message": "Hi, how can I help you today?"},
            {"speaker": "client", "message": "I'm looking for a 3-bedroom house in downtown"},
            {"speaker": "agent", "message": "What's your budget range?"},
            {"speaker": "client", "message": "Around 500k, maybe a bit more for the right property"}
        ]

        interaction_data = {
            "property_views": 5,
            "page_views": 12,
            "engagement_score": 0.75,
            "qualification_score": 65
        }

        response = await mobile_integration_service.integrate_behavioral_predictions_mobile(
            session_id=session_id,
            conversation_history=conversation_history,
            interaction_data=interaction_data
        )

        assert isinstance(response, MobileAdvancedResponse)
        assert response.feature_type == MobileAdvancedFeatureType.BEHAVIORAL_PREDICTIONS
        assert response.processing_time_ms < 300  # Performance target
        assert 'predictions' in response.response_data
        assert len(response.response_data['predictions']) > 0

        # Verify prediction structure
        prediction = response.response_data['predictions'][0]
        assert 'type' in prediction
        assert 'score' in prediction
        assert 'confidence' in prediction
        assert 'top_factors' in prediction

    @pytest.mark.asyncio
    async def test_mobile_performance_optimization(self, mobile_integration_service, sample_mobile_context):
        """Test mobile performance optimization"""
        # Start session with low battery
        sample_mobile_context.battery_info['level'] = 0.25
        sample_mobile_context.network_info['status'] = 'cellular'

        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        # Test performance optimization
        performance_metrics = {
            'avg_response_time_ms': 150,
            'battery_usage_percent': 8.5,
            'data_usage_mb': 2.3,
            'cache_hit_rate': 0.65
        }

        response = await mobile_integration_service.optimize_for_mobile_performance(
            session_id=session_id,
            performance_metrics=performance_metrics
        )

        assert isinstance(response, MobileAdvancedResponse)
        assert response.feature_type == MobileAdvancedFeatureType.PERFORMANCE_OPTIMIZATION
        assert 'optimization_recommendations' in response.response_data
        assert 'mode_suggestions' in response.response_data

        # Check that battery optimization is suggested
        mode_suggestions = response.response_data['mode_suggestions']
        assert any('battery' in str(suggestion).lower() for suggestion in mode_suggestions)

    @pytest.mark.asyncio
    async def test_mobile_personalization_interface(self, mobile_integration_service, sample_mobile_context):
        """Test mobile personalization interface creation"""
        # Start session
        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        # Test personalization interface
        user_preferences = {
            'language_preferences': {SupportedLanguage.ENGLISH_US.value: 1.0},
            'coaching_preferences': {
                'frequency': 'high',
                'detail_level': 'detailed',
                'notification_style': 'immediate'
            },
            'accessibility_needs': {
                'font_size': 'large',
                'high_contrast': True
            }
        }

        response = await mobile_integration_service.create_mobile_personalization_interface(
            session_id=session_id,
            user_preferences=user_preferences
        )

        assert isinstance(response, MobileAdvancedResponse)
        assert response.feature_type == MobileAdvancedFeatureType.PERSONALIZATION_ENGINE
        assert 'user_profile' in response.response_data
        assert 'mobile_interface_config' in response.response_data
        assert 'quick_actions' in response.response_data
        assert 'coaching_preferences' in response.response_data

        # Verify personalization was applied
        assert response.personalization_applied is True
        interface_config = response.response_data['mobile_interface_config']
        assert interface_config['font_size'] == 'large'

    @pytest.mark.asyncio
    async def test_cache_optimization(self, mobile_integration_service, sample_mobile_context):
        """Test mobile cache optimization"""
        # Start session
        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        # Make identical requests to test caching
        request_params = {
            "session_id": session_id,
            "conversation_context": "Property inquiry",
            "client_message": "Tell me about this neighborhood"
        }

        # First request
        response1 = await mobile_integration_service.integrate_multi_language_mobile(**request_params)

        # Second request (should hit cache)
        response2 = await mobile_integration_service.integrate_multi_language_mobile(**request_params)

        # Verify caching worked
        assert response2.cache_used is True
        assert response2.processing_time_ms < response1.processing_time_ms

    @pytest.mark.asyncio
    async def test_battery_impact_calculation(self, mobile_integration_service, sample_mobile_context):
        """Test battery impact calculation"""
        # Start session
        session_id = await mobile_integration_service.start_advanced_mobile_session(
            "test_user_123", sample_mobile_context
        )

        # Test different feature types
        response = await mobile_integration_service.integrate_multi_language_mobile(
            session_id=session_id,
            conversation_context="Test",
            client_message="Test message"
        )

        # Verify battery impact is calculated and reasonable
        assert response.battery_impact_estimate > 0
        assert response.battery_impact_estimate < 0.1  # Should be less than 0.1% per operation

    @pytest.mark.asyncio
    async def test_session_cleanup(self, mobile_integration_service, sample_mobile_context):
        """Test session cleanup and memory management"""
        # Create multiple sessions
        session_ids = []
        for i in range(5):
            context = sample_mobile_context
            context.user_id = f"test_user_{i}"
            session_id = await mobile_integration_service.start_advanced_mobile_session(
                f"test_user_{i}", context
            )
            session_ids.append(session_id)

        # Verify sessions were created
        assert len(mobile_integration_service.active_mobile_sessions) == 5

        # Test session cleanup (would normally happen on session end)
        for session_id in session_ids[:3]:
            if session_id in mobile_integration_service.active_mobile_sessions:
                del mobile_integration_service.active_mobile_sessions[session_id]

        # Verify cleanup
        assert len(mobile_integration_service.active_mobile_sessions) == 2


class TestMobileAdvancedFeaturesService:
    """Test Mobile Advanced Features Service"""

    @pytest.fixture
    async def mobile_features_service(self):
        """Create mobile features service for testing"""
        service = MobileAdvancedFeaturesService()
        await service._initialize_mobile_features()
        yield service

    @pytest.fixture
    def sample_touch_gesture(self):
        """Create sample touch gesture event"""
        return TouchGestureEvent(
            gesture_type=TouchGestureType.TAP,
            coordinates=(200.0, 400.0),
            force=0.5,
            duration_ms=150.0,
            target_element="coaching_panel"
        )

    @pytest.fixture
    def sample_voice_command(self):
        """Create sample voice command event"""
        return VoiceCommandEvent(
            command_type=VoiceCommandType.NEXT_SUGGESTION,
            spoken_text="next suggestion",
            confidence=0.85,
            language=SupportedLanguage.ENGLISH_US
        )

    @pytest.mark.asyncio
    async def test_enable_touch_optimized_coaching(self, mobile_features_service):
        """Test enabling touch-optimized coaching interface"""
        ui_preferences = {
            'touch_target_size': 48.0,
            'haptic_feedback_enabled': True,
            'accessibility_mode': False,
            'dark_mode': True
        }

        result = await mobile_features_service.enable_touch_optimized_coaching(
            session_id="test_session",
            ui_preferences=ui_preferences
        )

        assert 'interface_layout' in result
        assert 'touch_session_id' in result
        assert result['gesture_recognition_active'] is True
        assert result['haptic_feedback_enabled'] is True

        # Verify session was created
        assert "test_session" in mobile_features_service.active_touch_sessions

        # Verify UI configuration was applied
        touch_session = mobile_features_service.active_touch_sessions["test_session"]
        assert touch_session['ui_config']['touch_target_size'] == 48.0
        assert touch_session['ui_config']['haptic_feedback_enabled'] is True

    @pytest.mark.asyncio
    async def test_process_touch_gesture(self, mobile_features_service, sample_touch_gesture):
        """Test processing touch gestures"""
        # Enable touch coaching first
        await mobile_features_service.enable_touch_optimized_coaching("test_session")

        # Process gesture
        result = await mobile_features_service.process_touch_gesture(
            session_id="test_session",
            gesture_event=sample_touch_gesture
        )

        assert 'action' in result
        assert 'processing_time_ms' in result
        assert result['gesture_type'] == TouchGestureType.TAP.value
        assert result['processing_time_ms'] < 50  # Performance target for gesture recognition

        # Verify gesture was recorded in history
        touch_session = mobile_features_service.active_touch_sessions["test_session"]
        assert len(touch_session['gesture_history']) == 1
        assert touch_session['gesture_history'][0]['gesture'] == TouchGestureType.TAP.value

    @pytest.mark.asyncio
    async def test_process_voice_command(self, mobile_features_service, sample_voice_command):
        """Test processing voice commands"""
        result = await mobile_features_service.process_voice_command(
            session_id="test_session",
            voice_command=sample_voice_command
        )

        assert 'action' in result
        assert 'processing_time_ms' in result
        assert result['command_type'] == VoiceCommandType.NEXT_SUGGESTION.value
        assert result['confidence'] == 0.85
        assert result['processing_time_ms'] < 200  # Performance target for voice commands

        # Verify voice command response times are tracked
        assert len(mobile_features_service.voice_command_times) > 0

    @pytest.mark.asyncio
    async def test_gesture_handlers(self, mobile_features_service):
        """Test individual gesture handlers"""
        # Enable touch coaching
        await mobile_features_service.enable_touch_optimized_coaching("test_session")

        # Test different gesture types
        gesture_tests = [
            (TouchGestureType.TAP, "tap_processed"),
            (TouchGestureType.DOUBLE_TAP, "double_tap_processed"),
            (TouchGestureType.LONG_PRESS, "long_press_processed"),
            (TouchGestureType.SWIPE_LEFT, "swipe_left_processed"),
            (TouchGestureType.SWIPE_RIGHT, "swipe_right_processed"),
            (TouchGestureType.PINCH_OUT, "pinch_out_processed")
        ]

        for gesture_type, expected_action in gesture_tests:
            gesture_event = TouchGestureEvent(
                gesture_type=gesture_type,
                coordinates=(200.0, 400.0)
            )

            result = await mobile_features_service.process_touch_gesture(
                session_id="test_session",
                gesture_event=gesture_event
            )

            assert result['action'] == expected_action
            assert 'haptic_pattern' in result

    @pytest.mark.asyncio
    async def test_voice_command_handlers(self, mobile_features_service):
        """Test individual voice command handlers"""
        # Test different voice command types
        command_tests = [
            (VoiceCommandType.NEXT_SUGGESTION, "next_suggestion"),
            (VoiceCommandType.TRANSLATE, "translate"),
            (VoiceCommandType.GET_PREDICTION, "get_prediction"),
            (VoiceCommandType.TAKE_NOTE, "take_note"),
            (VoiceCommandType.ENABLE_BATTERY_SAVER, "enable_battery_saver")
        ]

        for command_type, expected_action in command_tests:
            voice_command = VoiceCommandEvent(
                command_type=command_type,
                spoken_text=command_type.value.replace('_', ' '),
                confidence=0.9,
                language=SupportedLanguage.ENGLISH_US
            )

            result = await mobile_features_service.process_voice_command(
                session_id="test_session",
                voice_command=voice_command
            )

            assert result['action'] == expected_action
            assert result['voice_feedback'] is True

    @pytest.mark.asyncio
    async def test_mobile_notification_system(self, mobile_features_service):
        """Test mobile notification system"""
        notification = MobileNotification(
            id="test_notification_123",
            notification_type=MobileNotificationType.URGENT_COACHING,
            title="Urgent Coaching Alert",
            message="Client objection detected - immediate response suggested",
            priority="critical",
            actionable=True,
            actions=[
                {"id": "respond", "label": "Respond Now", "type": "button"},
                {"id": "dismiss", "label": "Dismiss", "type": "button"}
            ],
            haptic_pattern="urgent",
            sound_enabled=True
        )

        result = await mobile_features_service.send_mobile_notification(
            session_id="test_session",
            notification=notification
        )

        assert result['notification_sent'] is True
        assert result['notification_id'] == "test_notification_123"
        assert result['haptic_triggered'] is True
        assert result['processing_time_ms'] < 100  # Performance target

        # Verify notification was added to queue
        assert len(mobile_features_service.notification_queue) > 0
        queued_notification = mobile_features_service.notification_queue[-1]
        assert queued_notification.id == "test_notification_123"

    @pytest.mark.asyncio
    async def test_battery_optimization(self, mobile_features_service):
        """Test battery life optimization"""
        # Test different battery levels
        battery_tests = [
            (0.05, "critical", ["behavioral_predictions", "voice_intelligence", "anomaly_detection"]),
            (0.15, "aggressive", ["behavioral_predictions", "voice_intelligence"]),
            (0.35, "moderate", ["behavioral_predictions"]),
            (0.80, "none", [])
        ]

        for battery_level, expected_level, expected_disabled in battery_tests:
            result = await mobile_features_service.optimize_for_battery_life(
                session_id=f"test_session_{battery_level}",
                current_battery_level=battery_level
            )

            assert result['battery_level'] == battery_level
            assert result['optimization_level'] == expected_level
            assert set(result['features_disabled']) == set(expected_disabled)

            if battery_level < 0.20:
                assert result['background_processing'] is False
                assert result['ui_adjustments']['haptic_feedback'] is False
            else:
                assert result['background_processing'] is True

    @pytest.mark.asyncio
    async def test_offline_data_sync(self, mobile_features_service):
        """Test offline data synchronization"""
        # Test initial sync
        result = await mobile_features_service.sync_offline_data(
            session_id="test_session",
            force_sync=True
        )

        assert result['sync_completed'] is True
        assert 'sync_results' in result
        assert 'processing_time_ms' in result
        assert result['processing_time_ms'] < 500  # Performance target

        sync_results = result['sync_results']
        assert 'coaching_cache_updated' in sync_results
        assert 'personalization_synced' in sync_results
        assert isinstance(sync_results['coaching_cache_updated'], int)

        # Test sync skip (should skip if synced recently)
        result2 = await mobile_features_service.sync_offline_data(
            session_id="test_session",
            force_sync=False
        )

        assert result2['sync_skipped'] is True
        assert result2['reason'] == "Recently synced"

    @pytest.mark.asyncio
    async def test_performance_tracking(self, mobile_features_service):
        """Test performance metrics tracking"""
        # Generate some test activity
        await mobile_features_service.enable_touch_optimized_coaching("test_session")

        # Process several gestures to generate performance data
        for i in range(5):
            gesture_event = TouchGestureEvent(
                gesture_type=TouchGestureType.TAP,
                coordinates=(100.0 + i * 10, 200.0)
            )
            await mobile_features_service.process_touch_gesture("test_session", gesture_event)

        # Process some voice commands
        for i in range(3):
            voice_command = VoiceCommandEvent(
                command_type=VoiceCommandType.NEXT_SUGGESTION,
                spoken_text="next",
                confidence=0.8 + i * 0.05,
                language=SupportedLanguage.ENGLISH_US
            )
            await mobile_features_service.process_voice_command("test_session", voice_command)

        # Get performance metrics
        metrics = await mobile_features_service.get_mobile_features_performance_metrics()

        assert 'active_touch_sessions' in metrics
        assert 'performance_metrics' in metrics
        assert 'feature_optimization' in metrics
        assert 'offline_capabilities' in metrics

        # Verify performance data was tracked
        performance = metrics['performance_metrics']
        assert 'average_touch_response_ms' in performance
        assert 'average_voice_command_ms' in performance
        assert performance['touch_target_met'] is not None
        assert performance['voice_target_met'] is not None

    @pytest.mark.asyncio
    async def test_haptic_feedback_patterns(self, mobile_features_service):
        """Test haptic feedback pattern system"""
        # Test different haptic patterns
        haptic_patterns = ["success", "warning", "error", "notification", "urgent", "confirmation"]

        for pattern in haptic_patterns:
            # This would trigger actual haptic hardware in real implementation
            await mobile_features_service._trigger_haptic_feedback("test_session", pattern)

        # Verify patterns are defined
        for pattern in haptic_patterns:
            assert pattern in mobile_features_service.haptic_patterns
            assert isinstance(mobile_features_service.haptic_patterns[pattern], list)

    @pytest.mark.asyncio
    async def test_accessibility_features(self, mobile_features_service):
        """Test accessibility features"""
        # Enable accessibility mode
        ui_preferences = {
            'accessibility_mode': True,
            'touch_target_size': 60.0,  # Larger touch targets
            'haptic_feedback_enabled': True,
            'high_contrast': True
        }

        result = await mobile_features_service.enable_touch_optimized_coaching(
            session_id="accessibility_session",
            ui_preferences=ui_preferences
        )

        # Verify accessibility settings were applied
        touch_session = mobile_features_service.active_touch_sessions["accessibility_session"]
        assert touch_session['accessibility_enabled'] is True
        assert touch_session['ui_config']['touch_target_size'] == 60.0

        # Test two-finger tap for accessibility menu
        accessibility_gesture = TouchGestureEvent(
            gesture_type=TouchGestureType.TWO_FINGER_TAP,
            coordinates=(200.0, 400.0)
        )

        result = await mobile_features_service.process_touch_gesture(
            session_id="accessibility_session",
            gesture_event=accessibility_gesture
        )

        assert result['action'] == "two_finger_tap_processed"
        assert result['accessibility_menu_opened'] is True


class TestMobileIntegrationPerformance:
    """Test Mobile Integration Performance"""

    @pytest.mark.asyncio
    async def test_response_time_performance(self):
        """Test that mobile features meet response time targets"""
        mobile_service = AdvancedMobileIntegrationService()
        features_service = MobileAdvancedFeaturesService()

        # Test response time targets
        targets = {
            'touch_response_ms': 16,
            'voice_command_ms': 200,
            'multi_language_ms': 150,
            'behavioral_prediction_ms': 200,
            'performance_optimization_ms': 50
        }

        # Measure actual response times
        start_time = time.time()

        # Touch gesture processing
        gesture = TouchGestureEvent(
            gesture_type=TouchGestureType.TAP,
            coordinates=(100, 200)
        )
        await features_service.enable_touch_optimized_coaching("perf_test")
        result = await features_service.process_touch_gesture("perf_test", gesture)
        touch_time = result.get('processing_time_ms', 0)

        # Voice command processing
        voice_command = VoiceCommandEvent(
            command_type=VoiceCommandType.NEXT_SUGGESTION,
            spoken_text="next",
            confidence=0.9,
            language=SupportedLanguage.ENGLISH_US
        )
        result = await features_service.process_voice_command("perf_test", voice_command)
        voice_time = result.get('processing_time_ms', 0)

        # Verify performance targets
        assert touch_time <= targets['touch_response_ms'] * 3  # Allow 3x margin for test environment
        assert voice_time <= targets['voice_command_ms'] * 2  # Allow 2x margin for test environment

    @pytest.mark.asyncio
    async def test_battery_impact_measurement(self):
        """Test battery impact measurement accuracy"""
        mobile_service = AdvancedMobileIntegrationService()

        # Simulate battery impact measurement
        feature_types = [
            MobileAdvancedFeatureType.MULTI_LANGUAGE_COACHING,
            MobileAdvancedFeatureType.BEHAVIORAL_PREDICTIONS,
            MobileAdvancedFeatureType.VOICE_INTELLIGENCE
        ]

        for feature_type in feature_types:
            processing_time = 100.0  # ms
            cache_used = False

            battery_impact = mobile_service._calculate_battery_impact(
                feature_type, processing_time, cache_used
            )

            # Verify reasonable battery impact
            assert 0.001 <= battery_impact <= 0.1  # Between 0.001% and 0.1% per operation
            assert isinstance(battery_impact, float)

        # Test cache impact
        cache_impact = mobile_service._calculate_battery_impact(
            MobileAdvancedFeatureType.MULTI_LANGUAGE_COACHING, 100.0, True
        )
        no_cache_impact = mobile_service._calculate_battery_impact(
            MobileAdvancedFeatureType.MULTI_LANGUAGE_COACHING, 100.0, False
        )

        # Cached operations should have lower battery impact
        assert cache_impact < no_cache_impact

    @pytest.mark.asyncio
    async def test_data_usage_optimization(self):
        """Test data usage optimization effectiveness"""
        mobile_service = AdvancedMobileIntegrationService()

        # Test data usage tracking
        sample_response_data = {
            'coaching_text': "This is a sample coaching response with cultural adaptations.",
            'language': 'es-MX',
            'cultural_context': 'latin_american',
            'cultural_adaptations': ['formal_language', 'family_considerations'],
            'audio_available': False
        }

        data_usage = len(json.dumps(sample_response_data).encode('utf-8'))

        # Verify data usage is reasonable (should be optimized for mobile)
        assert data_usage < 1024  # Less than 1KB for typical response
        assert data_usage > 50    # But not unreasonably small

    @pytest.mark.asyncio
    async def test_offline_capability_coverage(self):
        """Test offline capability coverage percentage"""
        features_service = MobileAdvancedFeaturesService()

        # Test offline capability configuration
        offline_capability = features_service.default_offline_capability

        assert offline_capability.capability_level in [
            OfflineCapabilityLevel.FULL_OFFLINE,
            OfflineCapabilityLevel.CACHED_RESPONSES,
            OfflineCapabilityLevel.BASIC_FEATURES
        ]

        # Verify minimum offline feature coverage
        cached_features = offline_capability.cached_features
        total_features = len(list(MobileAdvancedFeatureType))
        coverage_percentage = len(cached_features) / total_features

        assert coverage_percentage >= 0.6  # At least 60% of features available offline


class TestMobileIntegrationEdgeCases:
    """Test Mobile Integration Edge Cases"""

    @pytest.mark.asyncio
    async def test_low_memory_conditions(self):
        """Test behavior under low memory conditions"""
        mobile_service = AdvancedMobileIntegrationService()

        # Simulate low memory by creating many sessions
        low_memory_context = MobileAdvancedContext(
            user_id="low_memory_test",
            session_id="low_memory_session",
            platform_mode=MobilePlatformMode.BATTERY_OPTIMIZED,
            device_capability=MobileDeviceCapability.LOW_END,
            preferred_language=SupportedLanguage.ENGLISH_US,
            cultural_context=CulturalContext.NORTH_AMERICAN,
            device_info={"memory_gb": 2},  # Low memory device
            network_info={"status": "cellular"},
            battery_info={"level": 0.3}
        )

        # Service should adapt to low-end device
        session_id = await mobile_service.start_advanced_mobile_session(
            "low_memory_test", low_memory_context
        )

        session = mobile_service.active_mobile_sessions[session_id]

        # Verify features were limited for low-end device
        intensive_features = [
            MobileAdvancedFeatureType.BEHAVIORAL_PREDICTIONS,
            MobileAdvancedFeatureType.VOICE_INTELLIGENCE
        ]

        for feature in intensive_features:
            assert feature not in session['active_features']

    @pytest.mark.asyncio
    async def test_network_disconnection(self):
        """Test behavior when network disconnects"""
        mobile_service = AdvancedMobileIntegrationService()

        offline_context = MobileAdvancedContext(
            user_id="offline_test",
            session_id="offline_session",
            platform_mode=MobilePlatformMode.OFFLINE_CAPABLE,
            device_capability=MobileDeviceCapability.MID_RANGE,
            preferred_language=SupportedLanguage.ENGLISH_US,
            cultural_context=CulturalContext.NORTH_AMERICAN,
            device_info={"memory_gb": 4},
            network_info={"status": "offline"},
            battery_info={"level": 0.6}
        )

        session_id = await mobile_service.start_advanced_mobile_session(
            "offline_test", offline_context
        )

        # Test offline-capable features
        response = await mobile_service.create_mobile_personalization_interface(
            session_id=session_id,
            user_preferences={'coaching_preferences': {'frequency': 'normal'}}
        )

        # Should work offline with cached data
        assert isinstance(response, MobileAdvancedResponse)
        assert response.feature_type == MobileAdvancedFeatureType.PERSONALIZATION_ENGINE

    @pytest.mark.asyncio
    async def test_gesture_recognition_errors(self):
        """Test gesture recognition error handling"""
        features_service = MobileAdvancedFeaturesService()

        # Test invalid gesture
        invalid_gesture = TouchGestureEvent(
            gesture_type=TouchGestureType.FORCE_TOUCH,  # May not be supported
            coordinates=(100, 200)
        )

        # Enable touch coaching
        await features_service.enable_touch_optimized_coaching("error_test")

        result = await features_service.process_touch_gesture(
            session_id="error_test",
            gesture_event=invalid_gesture
        )

        # Should handle gracefully
        assert 'action' in result or 'error' in result

        # Test non-existent session
        result_no_session = await features_service.process_touch_gesture(
            session_id="non_existent_session",
            gesture_event=invalid_gesture
        )

        assert 'error' in result_no_session
        assert "not found" in result_no_session['error'].lower()

    @pytest.mark.asyncio
    async def test_voice_command_low_confidence(self):
        """Test voice command handling with low confidence"""
        features_service = MobileAdvancedFeaturesService()

        # Test low confidence voice command
        low_confidence_command = VoiceCommandEvent(
            command_type=VoiceCommandType.NEXT_SUGGESTION,
            spoken_text="next suggestion maybe",
            confidence=0.4,  # Low confidence
            language=SupportedLanguage.ENGLISH_US
        )

        result = await features_service.process_voice_command(
            session_id="low_confidence_test",
            voice_command=low_confidence_command
        )

        # Should process but may include confidence warning
        assert 'action' in result or 'error' in result
        assert result['confidence'] == 0.4


# Performance benchmarks
@pytest.mark.benchmark
class TestMobileIntegrationBenchmarks:
    """Benchmark tests for mobile integration performance"""

    @pytest.mark.asyncio
    async def test_multi_language_response_time_benchmark(self, benchmark):
        """Benchmark multi-language response time"""
        mobile_service = AdvancedMobileIntegrationService()

        context = MobileAdvancedContext(
            user_id="benchmark_test",
            session_id="benchmark_session",
            platform_mode=MobilePlatformMode.FULL_FEATURES,
            device_capability=MobileDeviceCapability.HIGH_END,
            preferred_language=SupportedLanguage.SPANISH_MX,
            cultural_context=CulturalContext.LATIN_AMERICAN,
            device_info={"model": "iPhone 15 Pro"},
            network_info={"status": "wifi"},
            battery_info={"level": 0.8}
        )

        session_id = await mobile_service.start_advanced_mobile_session("benchmark_test", context)

        async def multi_language_request():
            return await mobile_service.integrate_multi_language_mobile(
                session_id=session_id,
                conversation_context="Property pricing discussion",
                client_message="¿Cuál es el precio de esta propiedad?"
            )

        # Benchmark the operation
        result = benchmark(asyncio.run, multi_language_request())

        # Verify performance target was met
        assert result.processing_time_ms < 150  # Target: 150ms

    @pytest.mark.asyncio
    async def test_touch_gesture_response_benchmark(self, benchmark):
        """Benchmark touch gesture response time"""
        features_service = MobileAdvancedFeaturesService()

        await features_service.enable_touch_optimized_coaching("benchmark_session")

        gesture = TouchGestureEvent(
            gesture_type=TouchGestureType.TAP,
            coordinates=(200, 400)
        )

        async def gesture_processing():
            return await features_service.process_touch_gesture("benchmark_session", gesture)

        # Benchmark the operation
        result = benchmark(asyncio.run, gesture_processing())

        # Verify performance target was met
        assert result['processing_time_ms'] < 16  # Target: 16ms (60fps)