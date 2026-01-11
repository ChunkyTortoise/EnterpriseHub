
"""
Mobile Development Configuration

Configuration settings specific to mobile optimization and voice integration.
"""

# Mobile Performance Targets
MOBILE_PERFORMANCE_TARGETS = {
    "voice_response_time": 100,  # milliseconds
    "claude_integration_time": 150,  # milliseconds
    "ui_render_time": 50,  # milliseconds
    "network_timeout": 5000,  # milliseconds
    "battery_optimization": True,
    "offline_mode_support": True
}

# Mobile Claude Integration Settings
MOBILE_CLAUDE_CONFIG = {
    "streaming_enabled": True,
    "compression_enabled": True,
    "cache_responses": True,
    "batch_requests": True,
    "max_concurrent_requests": 3,
    "response_streaming_chunk_size": 512
}

# Voice Integration Settings
VOICE_INTEGRATION_CONFIG = {
    "speech_to_text_provider": "native",  # or "openai", "google"
    "text_to_speech_provider": "native",
    "voice_activity_detection": True,
    "noise_cancellation": True,
    "auto_speech_detection": True,
    "voice_commands_enabled": True
}

# Mobile UI/UX Settings
MOBILE_UI_CONFIG = {
    "responsive_breakpoints": {
        "mobile": 768,
        "tablet": 1024,
        "desktop": 1200
    },
    "touch_optimization": True,
    "haptic_feedback": True,
    "gesture_navigation": True,
    "dark_mode_default": True
}

# Real-time Features
REALTIME_CONFIG = {
    "websocket_enabled": True,
    "push_notifications": True,
    "background_sync": True,
    "offline_queue": True,
    "real_time_coaching": True,
    "live_market_updates": True
}

# Phase 5 Advanced Mobile Configuration
ADVANCED_MOBILE_CONFIG = {
    # Multi-language mobile optimization
    "multi_language_cache_size_mb": 25,
    "cultural_adaptation_enabled": True,
    "real_time_translation": True,
    "language_auto_detection": True,

    # Behavioral predictions for mobile
    "behavioral_predictions_cache_size": 100,
    "prediction_offline_capable": True,
    "anomaly_detection_mobile": True,
    "intervention_notifications": True,

    # Touch optimization
    "gesture_recognition_enabled": True,
    "haptic_feedback_patterns": True,
    "force_touch_enabled": False,  # Device dependent
    "accessibility_touch_targets": True,
    "touch_sensitivity": 1.0,

    # Voice intelligence mobile
    "voice_commands_enabled": True,
    "voice_coaching_activation": True,
    "background_voice_listening": False,  # Privacy conscious
    "voice_language_switching": True,

    # Battery optimization
    "adaptive_performance_scaling": True,
    "battery_aware_features": True,
    "background_processing_limits": True,
    "power_efficient_algorithms": True,

    # Offline capabilities
    "offline_coaching_cache_mb": 50,
    "offline_personalization": True,
    "offline_behavioral_patterns": True,
    "sync_when_connected": True,

    # Performance thresholds
    "max_response_time_ms": 100,
    "touch_response_target_ms": 16,
    "voice_response_target_ms": 200,
    "battery_impact_per_hour_percent": 5.0,
    "data_usage_reduction_target_percent": 70
}

# Touch Gesture Configuration
TOUCH_GESTURE_CONFIG = {
    "tap": {
        "enabled": True,
        "action": "next_suggestion",
        "haptic": "confirmation"
    },
    "double_tap": {
        "enabled": True,
        "action": "quick_menu",
        "haptic": "notification"
    },
    "long_press": {
        "enabled": True,
        "action": "context_menu",
        "haptic": "success"
    },
    "swipe_left": {
        "enabled": True,
        "action": "previous_suggestion",
        "haptic": "gesture_complete"
    },
    "swipe_right": {
        "enabled": True,
        "action": "next_suggestion",
        "haptic": "gesture_complete"
    },
    "swipe_up": {
        "enabled": True,
        "action": "detailed_view",
        "haptic": "notification"
    },
    "swipe_down": {
        "enabled": True,
        "action": "minimize_panel",
        "haptic": "confirmation"
    },
    "pinch_in": {
        "enabled": True,
        "action": "zoom_out",
        "haptic": "gesture_complete"
    },
    "pinch_out": {
        "enabled": True,
        "action": "zoom_in",
        "haptic": "gesture_complete"
    },
    "two_finger_tap": {
        "enabled": True,
        "action": "accessibility_menu",
        "haptic": "notification"
    }
}

# Voice Command Configuration
VOICE_COMMAND_CONFIG = {
    "activation_phrase": "hey claude",
    "timeout_seconds": 5,
    "confidence_threshold": 0.7,
    "commands": {
        "next_suggestion": ["next", "next suggestion", "continue"],
        "previous_suggestion": ["previous", "go back", "last one"],
        "translate": ["translate", "translate this", "in spanish", "in chinese"],
        "summarize": ["summarize", "summary", "give me the gist"],
        "take_note": ["take note", "remember this", "add note"],
        "get_prediction": ["get prediction", "predict", "analyze behavior"],
        "battery_saver": ["battery saver", "save battery", "low power"],
        "switch_language": ["switch language", "change language"]
    }
}

# Mobile Notification Configuration
MOBILE_NOTIFICATION_CONFIG = {
    "enabled": True,
    "max_queue_size": 50,
    "default_expiry_minutes": 30,
    "priority_levels": {
        "critical": {
            "immediate_delivery": True,
            "override_silent_mode": True,
            "haptic_pattern": "urgent",
            "sound_enabled": True
        },
        "high": {
            "immediate_delivery": True,
            "override_silent_mode": False,
            "haptic_pattern": "notification",
            "sound_enabled": True
        },
        "medium": {
            "immediate_delivery": False,
            "batch_delivery": True,
            "haptic_pattern": "confirmation",
            "sound_enabled": False
        },
        "low": {
            "immediate_delivery": False,
            "batch_delivery": True,
            "haptic_pattern": None,
            "sound_enabled": False
        }
    }
}

# Offline Capability Configuration
OFFLINE_CAPABILITY_CONFIG = {
    "enabled": True,
    "database_path": "mobile_advanced_cache.db",
    "max_cache_size_mb": 100,
    "cache_expiry_hours": 24,
    "feature_availability": {
        "multi_language_coaching": 0.8,      # 80% available offline
        "behavioral_predictions": 0.6,       # 60% available offline
        "personalization_engine": 0.9,       # 90% available offline
        "voice_intelligence": 0.4,           # 40% available offline
        "performance_optimization": 1.0      # 100% available offline
    },
    "sync_frequency_minutes": 15,
    "wifi_only_sync": False,
    "background_sync_enabled": True
}
