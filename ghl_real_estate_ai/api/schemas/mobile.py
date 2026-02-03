"""
Mobile API Schemas - Data models for mobile-specific endpoints
Optimized response formats and validation for iOS/Android applications.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from enum import Enum
import re

class MobileErrorCode(str, Enum):
    """Standardized error codes for mobile clients."""
    AUTHENTICATION_REQUIRED = "AUTH_REQUIRED"
    AUTHENTICATION_FAILED = "AUTH_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    DEVICE_NOT_REGISTERED = "DEVICE_NOT_REGISTERED"
    BIOMETRIC_NOT_AVAILABLE = "BIOMETRIC_NOT_AVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    NETWORK_ERROR = "NETWORK_ERROR"
    DATA_VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DEVICE_COMPATIBILITY_ERROR = "DEVICE_INCOMPATIBLE"
    LOCATION_PERMISSION_REQUIRED = "LOCATION_REQUIRED"
    CAMERA_PERMISSION_REQUIRED = "CAMERA_REQUIRED"
    MICROPHONE_PERMISSION_REQUIRED = "MICROPHONE_REQUIRED"
    STORAGE_PERMISSION_REQUIRED = "STORAGE_REQUIRED"

class MobilePlatform(str, Enum):
    """Supported mobile platforms."""
    IOS = "ios"
    ANDROID = "android"
    WEBAPP = "webapp"

class MobileResponseStatus(str, Enum):
    """Response status for mobile operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class MobileErrorResponse(BaseModel):
    """Standardized error response for mobile clients."""
    status: MobileResponseStatus = MobileResponseStatus.ERROR
    error_code: MobileErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
    support_id: Optional[str] = Field(None, description="Support reference ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "status": "error",
                "error_code": "AUTH_REQUIRED",
                "message": "Authentication required to access this resource",
                "details": {"required_permissions": ["read", "write"]},
                "retry_after": None,
                "support_id": "ERR_20240118_001",
                "timestamp": "2024-01-18T10:30:00Z"
            }
        })

class MobileSuccessResponse(BaseModel):
    """Standardized success response wrapper."""
    status: MobileResponseStatus = MobileResponseStatus.SUCCESS
    data: Dict[str, Any] = Field(..., description="Response data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
    timestamp: datetime = Field(default_factory=datetime.now)

class MobilePaginationMetadata(BaseModel):
    """Pagination metadata for mobile list responses."""
    current_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    total_count: int = Field(..., ge=0)
    page_size: int = Field(..., ge=1, le=100)
    has_next: bool = Field(...)
    has_previous: bool = Field(...)
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    previous_cursor: Optional[str] = Field(None, description="Cursor for previous page")

class MobileListResponse(BaseModel):
    """Paginated list response for mobile."""
    status: MobileResponseStatus = MobileResponseStatus.SUCCESS
    data: List[Dict[str, Any]] = Field(...)
    pagination: MobilePaginationMetadata = Field(...)
    filters_applied: Optional[Dict[str, Any]] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.now)

# Device and Location Models

class GPSCoordinate(BaseModel):
    """GPS coordinate with accuracy information."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    timestamp: datetime = Field(default_factory=datetime.now)

class MobileDeviceInfo(BaseModel):
    """Extended device information for mobile apps."""
    device_id: str = Field(..., description="Unique device identifier")
    platform: MobilePlatform = Field(..., description="Mobile platform")
    os_version: str = Field(..., description="Operating system version")
    app_version: str = Field(..., description="Mobile app version")
    device_model: Optional[str] = Field(None, description="Device model")
    device_name: Optional[str] = Field(None, description="User-assigned device name")
    screen_size: Optional[Dict[str, int]] = Field(None, description="Screen dimensions")
    timezone: Optional[str] = Field(None, description="Device timezone")
    language: str = Field(default="en", description="Device language")
    push_token: Optional[str] = Field(None, description="Push notification token")
    permissions: List[str] = Field(default=[], description="Granted permissions")
    biometric_available: bool = Field(default=False)
    camera_available: bool = Field(default=True)
    location_services: bool = Field(default=False)
    
    @field_validator('device_id')
    @classmethod
    def validate_device_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Device ID must be at least 10 characters')
        return v

# Property Models Optimized for Mobile

class MobilePropertySummary(BaseModel):
    """Compact property summary for mobile lists."""
    property_id: str = Field(...)
    mls_id: Optional[str] = Field(None)
    address: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    zip_code: str = Field(...)
    price: int = Field(..., ge=0)
    price_formatted: str = Field(...)
    bedrooms: int = Field(..., ge=0)
    bathrooms: float = Field(..., ge=0)
    sqft: int = Field(..., ge=0)
    lot_size: Optional[str] = Field(None)
    property_type: str = Field(...)
    status: str = Field(default="active")
    days_on_market: int = Field(..., ge=0)
    primary_image_url: Optional[str] = Field(None)
    thumbnail_url: Optional[str] = Field(None)
    coordinates: Optional[GPSCoordinate] = Field(None)
    distance_miles: Optional[float] = Field(None, description="Distance from user")
    favorite: bool = Field(default=False)
    viewed_at: Optional[datetime] = Field(None)
    
    @field_validator('price_formatted')
    @classmethod
    def format_price(cls, v, info: ValidationInfo):
        if 'price' in info.data:
            return f"${info.data['price']:,}"
        return v

class MobilePropertyDetails(BaseModel):
    """Detailed property information for mobile detail view."""
    property_id: str = Field(...)
    mls_id: Optional[str] = Field(None)
    address: str = Field(...)
    city: str = Field(...)
    state: str = Field(...)
    zip_code: str = Field(...)
    coordinates: Optional[GPSCoordinate] = Field(None)
    price: int = Field(..., ge=0)
    price_formatted: str = Field(...)
    price_per_sqft: Optional[float] = Field(None)
    bedrooms: int = Field(..., ge=0)
    bathrooms: float = Field(..., ge=0)
    sqft: int = Field(..., ge=0)
    lot_size: Optional[str] = Field(None)
    year_built: Optional[int] = Field(None)
    property_type: str = Field(...)
    status: str = Field(default="active")
    days_on_market: int = Field(..., ge=0)
    
    # Media
    images: List[str] = Field(default=[])
    virtual_tour_url: Optional[str] = Field(None)
    video_url: Optional[str] = Field(None)
    
    # Features
    features: List[str] = Field(default=[])
    amenities: List[str] = Field(default=[])
    appliances: List[str] = Field(default=[])
    
    # Location details
    neighborhood: Optional[str] = Field(None)
    school_district: Optional[str] = Field(None)
    nearby_schools: List[Dict[str, Any]] = Field(default=[])
    walkability_score: Optional[int] = Field(None, ge=0, le=100)
    
    # Market data
    market_trends: Optional[Dict[str, Any]] = Field(None)
    comparable_sales: List[Dict[str, Any]] = Field(default=[])
    price_history: List[Dict[str, Any]] = Field(default=[])
    
    # AI insights
    ai_insights: Optional[str] = Field(None)
    investment_score: Optional[float] = Field(None, ge=0, le=100)
    
    # User specific
    favorite: bool = Field(default=False)
    notes: List[str] = Field(default=[])
    viewed_at: Optional[datetime] = Field(None)
    scheduled_showing: Optional[datetime] = Field(None)

# Lead Models for Mobile

class MobileLeadSummary(BaseModel):
    """Compact lead summary for mobile lists."""
    lead_id: str = Field(...)
    name: str = Field(...)
    phone: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    status: str = Field(...)
    lead_score: float = Field(..., ge=0, le=100)
    last_contact: Optional[datetime] = Field(None)
    next_followup: Optional[datetime] = Field(None)
    source: Optional[str] = Field(None)
    assigned_agent: Optional[str] = Field(None)
    priority: str = Field(default="medium")
    property_interest: Optional[str] = Field(None)
    estimated_budget: Optional[int] = Field(None)
    coordinates: Optional[GPSCoordinate] = Field(None)
    distance_miles: Optional[float] = Field(None)
    unread_messages: int = Field(default=0)
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if v.lower() not in valid_priorities:
            raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v.lower()

class MobileLeadDetails(BaseModel):
    """Detailed lead information for mobile detail view."""
    lead_id: str = Field(...)
    name: str = Field(...)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    address: Optional[str] = Field(None)
    coordinates: Optional[GPSCoordinate] = Field(None)
    
    # Lead status and scoring
    status: str = Field(...)
    lead_score: float = Field(..., ge=0, le=100)
    qualification_status: Optional[str] = Field(None)
    
    # Contact history
    last_contact: Optional[datetime] = Field(None)
    next_followup: Optional[datetime] = Field(None)
    contact_attempts: int = Field(default=0)
    response_rate: Optional[float] = Field(None, ge=0, le=100)
    
    # Preferences and interests
    property_preferences: Dict[str, Any] = Field(default={})
    price_range: Optional[Dict[str, int]] = Field(None)
    preferred_areas: List[str] = Field(default=[])
    must_have_features: List[str] = Field(default=[])
    
    # AI insights
    behavioral_insights: Optional[str] = Field(None)
    conversion_probability: Optional[float] = Field(None, ge=0, le=100)
    recommended_properties: List[str] = Field(default=[])
    
    # Activity
    recent_activities: List[Dict[str, Any]] = Field(default=[])
    message_threads: List[Dict[str, Any]] = Field(default=[])
    scheduled_appointments: List[Dict[str, Any]] = Field(default=[])
    
    # Agent management
    assigned_agent: Optional[str] = Field(None)
    source: Optional[str] = Field(None)
    tags: List[str] = Field(default=[])
    notes: List[Dict[str, Any]] = Field(default=[])

# Voice Interaction Models

class MobileVoiceRequest(BaseModel):
    """Mobile voice interaction request."""
    audio_data: str = Field(..., description="Base64 encoded audio")
    audio_format: str = Field(default="wav", description="Audio format")
    duration_seconds: Optional[float] = Field(None, ge=0, le=60)
    language: str = Field(default="en-US")
    context: Optional[Dict[str, Any]] = Field(None)
    location: Optional[GPSCoordinate] = Field(None)
    device_info: MobileDeviceInfo = Field(...)
    
    @field_validator('audio_data')
    @classmethod
    def validate_audio_data(cls, v):
        try:
            # Basic base64 validation
            import base64
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError('Invalid base64 audio data')

class MobileVoiceResponse(BaseModel):
    """Mobile voice interaction response."""
    session_id: str = Field(...)
    transcription: str = Field(...)
    confidence: float = Field(..., ge=0, le=1)
    ai_response: str = Field(...)
    audio_response: Optional[str] = Field(None, description="Base64 encoded audio")
    interaction_type: str = Field(...)
    entities_extracted: Dict[str, Any] = Field(default={})
    suggested_actions: List[Dict[str, str]] = Field(default=[])
    processing_time_ms: int = Field(..., ge=0)

# AR/VR Models for Mobile

class MobileARCapabilities(BaseModel):
    """Mobile AR capabilities and settings."""
    ar_supported: bool = Field(default=False)
    plane_detection: bool = Field(default=False)
    image_tracking: bool = Field(default=False)
    face_tracking: bool = Field(default=False)
    hand_tracking: bool = Field(default=False)
    occlusion_support: bool = Field(default=False)
    lighting_estimation: bool = Field(default=False)
    cloud_anchors: bool = Field(default=False)
    max_anchors: int = Field(default=0, ge=0)
    performance_tier: str = Field(default="low")  # low, medium, high, ultra

class MobileAROverlay(BaseModel):
    """AR overlay optimized for mobile rendering."""
    overlay_id: str = Field(...)
    property_id: str = Field(...)
    overlay_type: str = Field(...)  # price, info, highlight, virtual_staging
    position: Dict[str, float] = Field(...)  # x, y, z coordinates
    rotation: Optional[Dict[str, float]] = Field(None)
    scale: Optional[Dict[str, float]] = Field(None)
    content: Dict[str, Any] = Field(...)
    visibility_distance: float = Field(default=50.0, ge=0)
    auto_hide: bool = Field(default=True)
    interactive: bool = Field(default=False)
    animation: Optional[str] = Field(None)

# Analytics Models for Mobile

class MobileAnalyticsSummary(BaseModel):
    """Mobile-optimized analytics summary."""
    period: str = Field(...)  # day, week, month
    leads_summary: Dict[str, int] = Field(...)
    properties_summary: Dict[str, int] = Field(...)
    performance_metrics: Dict[str, float] = Field(...)
    top_performing_areas: List[Dict[str, Any]] = Field(default=[])
    recent_activities: List[Dict[str, Any]] = Field(default=[])
    alerts: List[Dict[str, str]] = Field(default=[])
    trend_indicators: Dict[str, str] = Field(default={})
    generated_at: datetime = Field(default_factory=datetime.now)

# Notification Models

class MobileNotification(BaseModel):
    """Mobile push notification model."""
    notification_id: str = Field(...)
    type: str = Field(...)  # lead_update, property_alert, appointment_reminder, market_update
    title: str = Field(...)
    body: str = Field(...)
    data: Optional[Dict[str, Any]] = Field(None)
    priority: str = Field(default="normal")  # low, normal, high
    badge_count: Optional[int] = Field(None)
    sound: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    deep_link: Optional[str] = Field(None)
    expires_at: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=datetime.now)

# Settings Models

class MobileAppSettings(BaseModel):
    """Mobile app settings and preferences."""
    user_id: str = Field(...)
    device_id: str = Field(...)
    
    # Notification preferences
    push_enabled: bool = Field(default=True)
    lead_notifications: bool = Field(default=True)
    property_alerts: bool = Field(default=True)
    appointment_reminders: bool = Field(default=True)
    market_updates: bool = Field(default=False)
    
    # App preferences
    default_search_radius: float = Field(default=25.0, ge=1, le=100)
    preferred_units: str = Field(default="imperial")  # imperial, metric
    map_type: str = Field(default="standard")  # standard, satellite, hybrid
    theme: str = Field(default="auto")  # light, dark, auto
    
    # Privacy settings
    location_sharing: bool = Field(default=True)
    analytics_enabled: bool = Field(default=True)
    crash_reporting: bool = Field(default=True)
    
    # Feature flags
    ar_enabled: bool = Field(default=False)
    voice_enabled: bool = Field(default=False)
    biometric_enabled: bool = Field(default=False)
    
    updated_at: datetime = Field(default_factory=datetime.now)

# Sync Models

class MobileSyncRequest(BaseModel):
    """Mobile offline sync request."""
    device_id: str = Field(...)
    last_sync: datetime = Field(...)
    pending_operations: List[Dict[str, Any]] = Field(default=[])
    conflict_resolution: str = Field(default="server_wins")  # server_wins, client_wins, merge
    batch_size: int = Field(default=100, ge=1, le=500)

class MobileSyncResponse(BaseModel):
    """Mobile offline sync response."""
    sync_id: str = Field(...)
    sync_timestamp: datetime = Field(default_factory=datetime.now)
    processed_operations: List[Dict[str, Any]] = Field(default=[])
    server_updates: List[Dict[str, Any]] = Field(default=[])
    conflicts: List[Dict[str, Any]] = Field(default=[])
    next_sync_recommended: datetime = Field(...)
    full_sync_required: bool = Field(default=False)

# Search Models

class MobileSearchRequest(BaseModel):
    """Mobile-optimized search request."""
    query: str = Field(..., min_length=1, max_length=200)
    search_type: str = Field(...)  # properties, leads, all
    filters: Optional[Dict[str, Any]] = Field(None)
    location: Optional[GPSCoordinate] = Field(None)
    radius: Optional[float] = Field(None, ge=1, le=100)
    sort_by: str = Field(default="relevance")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        # Remove extra whitespace and validate length
        cleaned = re.sub(r'\s+', ' ', v.strip())
        if len(cleaned) < 1:
            raise ValueError('Search query cannot be empty')
        return cleaned

class MobileSearchResponse(BaseModel):
    """Mobile search response with grouped results."""
    query: str = Field(...)
    results: Dict[str, List[Dict[str, Any]]] = Field(...)  # grouped by type
    total_count: int = Field(..., ge=0)
    search_time_ms: int = Field(..., ge=0)
    suggestions: List[str] = Field(default=[])
    filters_applied: Dict[str, Any] = Field(default={})
    pagination: MobilePaginationMetadata = Field(...)

# Response Builders

def build_mobile_error_response(
    error_code: MobileErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    retry_after: Optional[int] = None,
    support_id: Optional[str] = None
) -> MobileErrorResponse:
    """Build standardized mobile error response."""
    return MobileErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        retry_after=retry_after,
        support_id=support_id
    )

def build_mobile_success_response(
    data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> MobileSuccessResponse:
    """Build standardized mobile success response."""
    return MobileSuccessResponse(
        data=data,
        metadata=metadata
    )

def build_mobile_list_response(
    data: List[Dict[str, Any]],
    pagination: MobilePaginationMetadata,
    filters_applied: Optional[Dict[str, Any]] = None
) -> MobileListResponse:
    """Build standardized mobile list response."""
    return MobileListResponse(
        data=data,
        pagination=pagination,
        filters_applied=filters_applied
    )