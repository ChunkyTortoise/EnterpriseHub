
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
