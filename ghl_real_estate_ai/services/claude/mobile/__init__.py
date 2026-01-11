"""
Mobile Claude Services (Phase 5: Advanced AI Features Integration)

Comprehensive mobile-optimized Claude integration services including:
- Voice and real-time features (Phase 4)
- Advanced multi-language support (Phase 5)
- Behavioral predictions for mobile (Phase 5)
- Touch-optimized interfaces (Phase 5)
- Battery-efficient AI processing (Phase 5)
- Offline-capable advanced features (Phase 5)
- Cross-platform synchronization (Phase 5)
"""

from .voice_integration_service import VoiceIntegrationService
from .mobile_coaching_service import MobileCoachingService
from .offline_sync_service import OfflineSyncService

# Phase 5 Advanced Mobile Services
from .advanced_mobile_integration import (
    AdvancedMobileIntegrationService,
    MobileAdvancedFeatureType,
    MobilePlatformMode,
    MobileDeviceCapability,
    MobileAdvancedContext,
    MobileAdvancedResponse,
    MobilePersonalizationProfile
)
from .mobile_advanced_features import (
    MobileAdvancedFeaturesService,
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

__all__ = [
    # Phase 4 Services
    "VoiceIntegrationService",
    "MobileCoachingService",
    "OfflineSyncService",

    # Phase 5 Advanced Services
    "AdvancedMobileIntegrationService",
    "MobileAdvancedFeaturesService",

    # Phase 5 Data Classes
    "MobileAdvancedFeatureType",
    "MobilePlatformMode",
    "MobileDeviceCapability",
    "MobileAdvancedContext",
    "MobileAdvancedResponse",
    "MobilePersonalizationProfile",
    "TouchGestureType",
    "VoiceCommandType",
    "MobileNotificationType",
    "TouchGestureEvent",
    "VoiceCommandEvent",
    "MobileNotification",
    "TouchOptimizedUI",
    "OfflineCapability",
    "OfflineCapabilityLevel"
]
