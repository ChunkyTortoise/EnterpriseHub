# Mobile-First Agent Experience API

## Overview

The Mobile-First Agent Experience API is a comprehensive mobile backend designed specifically for Jorge's Revenue Acceleration Platform. It provides native iOS and Android applications with powerful real estate tools including AR/VR property visualization, voice-enabled AI assistance, and mobile-optimized data management.

**Business Impact Target**: $250K+ annual revenue through enhanced mobile agent productivity and client engagement.

## Features

### 🔐 Advanced Mobile Authentication
- **JWT Authentication** with extended mobile token validity (7 days)
- **Biometric Support** for fingerprint, Face ID, and voice print authentication
- **Device Registration** for secure biometric enablement
- **Rate Limiting** and security event logging
- **Session Management** with device-specific tokens

### 🥽 AR/VR Property Visualization
- **AR Overlays** for property information, pricing, and AI insights
- **Virtual Tours** with 360° waypoints and interactive hotspots
- **3D Models** with LOD optimization for mobile performance
- **Spatial Anchoring** for persistent AR content across sessions
- **Device Capability Detection** for optimal AR/VR settings

### 🎤 Voice-Enabled AI Assistant
- **Speech-to-Text** processing with multi-language support
- **Intent Classification** for real estate-specific voice commands
- **AI Response Generation** using Claude with market context
- **Text-to-Speech** synthesis (optional)
- **Session Context** management for conversational continuity

### 📱 Mobile-Optimized Data APIs
- **Property Search** with GPS-based filtering and pagination
- **Lead Management** with location-based discovery
- **Analytics Dashboard** with mobile-friendly metrics
- **Offline Sync** capabilities with conflict resolution
- **Push Notifications** for real-time updates

## API Endpoints

### Authentication (`/api/mobile/auth/*`)

#### POST `/api/mobile/auth/login`
Mobile login with device registration and extended token validity.

**Request:**
```json
{
  "username": "jorge",
  "password": "demo123",
  "device_info": {
    "device_id": "unique_device_id",
    "device_type": "ios",
    "app_version": "1.0.0",
    "os_version": "17.0",
    "biometric_capabilities": ["fingerprint", "face_id"],
    "push_token": "apns_token_here"
  },
  "remember_device": true
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "expires_in": 604800,
  "user_info": {
    "user_id": "jorge_001",
    "username": "jorge",
    "display_name": "Jorge Sales",
    "permissions": ["read", "write", "admin"],
    "location_id": "demo_location"
  },
  "device_registered": true,
  "biometric_enabled": true,
  "session_id": "session_12345"
}
```

#### POST `/api/mobile/auth/biometric/challenge`
Create biometric authentication challenge.

**Request:**
```json
{
  "device_id": "unique_device_id"
}
```

**Response:**
```json
{
  "challenge_token": "challenge_abc123",
  "expires_in": 300,
  "biometric_types": ["fingerprint", "face_id"],
  "device_trusted": true
}
```

#### POST `/api/mobile/auth/biometric/authenticate`
Authenticate using biometric data.

**Request:**
```json
{
  "device_id": "unique_device_id",
  "biometric_type": "fingerprint",
  "biometric_signature": "bio_encrypted_signature",
  "challenge_token": "challenge_abc123"
}
```

**Response:** Same as login response with `biometric_auth: true`

### AR/VR Integration (`/api/mobile/ar/*`)

#### POST `/api/mobile/ar/visualize/setup`
Set up AR/VR visualization for a property.

**Request:**
```json
{
  "property_id": "prop_austin_001",
  "user_location": {"latitude": 30.2672, "longitude": -97.7431},
  "device_capabilities": {
    "supports_ar": true,
    "supports_occlusion": true,
    "supports_realtime_lighting": false,
    "high_performance": true
  },
  "visualization_type": "mixed_reality",
  "quality_preference": "high"
}
```

**Response:**
```json
{
  "property_id": "prop_austin_001",
  "visualization_type": "mixed_reality",
  "visualization_data": {
    "ar_overlays": [
      {
        "overlay_id": "price_prop_austin_001",
        "overlay_type": "price",
        "position": {"x": 0.0, "y": 2.0, "z": 0.0},
        "content": {
          "price": 750000,
          "price_formatted": "$750,000",
          "market_comparison": "5% above market average"
        }
      }
    ],
    "vr_waypoints": [
      {
        "waypoint_id": "exterior_prop_austin_001",
        "name": "Exterior View",
        "position": {"x": 0.0, "y": 1.6, "z": 10.0},
        "panorama_url": "https://vr-content.example.com/prop_austin_001/exterior_360.jpg"
      }
    ]
  },
  "session_id": "ar_session_12345",
  "expires_at": "2024-01-18T14:30:00Z"
}
```

#### GET `/api/mobile/ar/property/{property_id}/model`
Get 3D model data for property visualization.

**Response:**
```json
{
  "model_id": "model_prop_austin_001_high",
  "property_id": "prop_austin_001",
  "model_format": "gltf",
  "model_url": "https://3d-models.example.com/prop_austin_001/high/model.gltf",
  "level_of_detail": [
    {
      "distance": 0.0,
      "polygon_count": 50000,
      "texture_resolution": 2048,
      "model_url": "https://3d-models.example.com/prop_austin_001/high/model_lod0.gltf"
    }
  ],
  "interactive_elements": [
    {
      "id": "front_door",
      "type": "door",
      "position": {"x": 0.0, "y": 0.0, "z": -10.0},
      "interaction": "tap_to_open"
    }
  ]
}
```

### Voice Assistant (`/api/mobile/voice/*`)

#### POST `/api/mobile/voice/process`
Process voice interaction with AI assistant.

**Request:**
```json
{
  "audio_data": "base64_encoded_audio_data",
  "audio_format": "wav",
  "duration_seconds": 3.5,
  "language": "en-US",
  "context": {"current_screen": "property_details"},
  "location": {
    "latitude": 30.2672,
    "longitude": -97.7431,
    "accuracy": 10.0
  },
  "device_info": {
    "device_id": "unique_device_id",
    "platform": "ios",
    "app_version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "session_id": "voice_session_12345",
  "transcription": "Show me properties under 800 thousand in Hill Country",
  "confidence": 0.95,
  "ai_response": "I found 12 properties in Hill Country under $800,000. The newest listing is a 4-bedroom home at $750,000 with excellent schools nearby. Would you like me to show you the details?",
  "interaction_type": "property_inquiry",
  "entities_extracted": {
    "price_mention": "800000",
    "location": "hill country",
    "bedrooms": 4
  },
  "suggested_actions": [
    {
      "action": "search_properties",
      "title": "Search Properties",
      "description": "Find matching properties based on criteria",
      "priority": "high"
    }
  ],
  "processing_time_ms": 1250
}
```

### Properties (`/api/mobile/properties/*`)

#### GET `/api/mobile/properties`
Get mobile-optimized property listings with location-based filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Results per page (default: 20, max: 50)
- `location` (string): GPS coordinates as "lat,lng"
- `radius` (float): Search radius in miles (default: 25)
- `min_price` (int): Minimum price filter
- `max_price` (int): Maximum price filter
- `bedrooms` (int): Number of bedrooms
- `bathrooms` (float): Number of bathrooms
- `property_type` (string): Property type filter

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "property_id": "prop_austin_001",
      "address": "1234 Example Street",
      "price": 750000,
      "price_formatted": "$750,000",
      "bedrooms": 4,
      "bathrooms": 3.5,
      "sqft": 2500,
      "coordinates": {
        "latitude": 30.2672,
        "longitude": -97.7431
      },
      "distance_miles": 5.2,
      "primary_image_url": "https://images.example.com/prop_1_primary.jpg",
      "favorite": false
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 8,
    "total_count": 150,
    "page_size": 20,
    "has_next": true,
    "has_previous": false
  }
}
```

#### GET `/api/mobile/properties/{property_id}`
Get detailed property information optimized for mobile viewing.

**Response:**
```json
{
  "property_id": "prop_austin_001",
  "address": "1234 Hill Country Drive",
  "price": 750000,
  "price_formatted": "$750,000",
  "price_per_sqft": 300,
  "bedrooms": 4,
  "bathrooms": 3.5,
  "sqft": 2500,
  "images": [
    "https://images.example.com/prop_austin_001/exterior_1.jpg",
    "https://images.example.com/prop_austin_001/kitchen_1.jpg"
  ],
  "features": ["Open Floor Plan", "Updated Kitchen", "Hardwood Floors"],
  "neighborhood": "Hill Country",
  "school_district": "Lake Travis ISD",
  "nearby_schools": [
    {"name": "Lake Travis Elementary", "rating": 9, "distance": 0.5}
  ],
  "ai_insights": "This property shows strong potential in the current Austin market with excellent school ratings and recent appreciation trends.",
  "investment_score": 85,
  "market_trends": {
    "appreciation_1y": 8.5,
    "median_price_trend": "increasing",
    "inventory_level": "low"
  }
}
```

### Leads (`/api/mobile/leads/*`)

#### GET `/api/mobile/leads`
Get mobile-optimized lead listings with filtering and search.

**Query Parameters:**
- `page`, `limit`: Pagination
- `status_filter`: Filter by lead status
- `priority_filter`: Filter by priority level
- `search`: Search by name, phone, or email
- `location`: GPS coordinates for proximity search
- `radius`: Search radius in miles

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "lead_id": "lead_001",
      "name": "Sarah Chen",
      "phone": "512-555-2001",
      "email": "sarah.chen@example.com",
      "status": "qualified",
      "lead_score": 92,
      "last_contact": "2024-01-18T04:30:00Z",
      "next_followup": "2024-01-20T10:00:00Z",
      "priority": "high",
      "property_interest": "prop_austin_001",
      "estimated_budget": 800000,
      "distance_miles": 3.2,
      "unread_messages": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_count": 85,
    "page_size": 20,
    "has_next": true,
    "has_previous": false
  }
}
```

#### GET `/api/mobile/leads/{lead_id}`
Get detailed lead information with AI insights and recommendations.

**Response:**
```json
{
  "lead_id": "lead_001",
  "name": "Sarah Chen",
  "status": "qualified",
  "lead_score": 92,
  "qualification_status": "pre_approved",
  "property_preferences": {
    "min_bedrooms": 3,
    "max_price": 800000,
    "preferred_style": "modern"
  },
  "behavioral_insights": "High-engagement lead showing strong buying signals with excellent response rate.",
  "conversion_probability": 85,
  "recommended_properties": ["prop_austin_001", "prop_austin_015"],
  "recent_activities": [
    {
      "type": "property_view",
      "property_id": "prop_austin_001",
      "timestamp": "2024-01-18T08:30:00Z",
      "duration_minutes": 15
    }
  ]
}
```

## Authentication

### Token Types

1. **Access Token**: Short-lived JWT (7 days for mobile) containing user identity and permissions
2. **Refresh Token**: Long-lived token (30 days) for obtaining new access tokens
3. **Biometric Challenge Token**: Short-lived token (5 minutes) for biometric authentication flows

### Required Headers

```
Authorization: Bearer {access_token}
X-Device-ID: {unique_device_identifier}
X-App-Version: {mobile_app_version}
X-Platform: {ios|android}
```

### Biometric Authentication Flow

1. **Device Registration**: Occurs during first login with `remember_device: true`
2. **Challenge Creation**: Request biometric challenge with device ID
3. **Biometric Authentication**: Submit biometric signature with challenge token
4. **Token Issuance**: Receive full authentication tokens on successful verification

## Error Handling

All endpoints return standardized error responses:

```json
{
  "status": "error",
  "error_code": "AUTH_REQUIRED",
  "message": "Authentication required to access this resource",
  "details": {"required_permissions": ["read", "write"]},
  "retry_after": null,
  "support_id": "ERR_20240118_001",
  "timestamp": "2024-01-18T10:30:00Z"
}
```

### Error Codes

- `AUTH_REQUIRED`: Authentication required
- `AUTH_FAILED`: Authentication failed
- `TOKEN_EXPIRED`: Access token expired
- `DEVICE_NOT_REGISTERED`: Device not registered for biometric auth
- `BIOMETRIC_NOT_AVAILABLE`: Biometric authentication not available
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Request validation failed
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable

## Rate Limiting

- **Authentication endpoints**: 5 attempts per 15 minutes per device
- **General API**: 1000 requests per hour per authenticated user
- **Voice processing**: 50 requests per hour per user
- **AR/VR content**: 200 requests per hour per user

## Data Optimization

### Mobile Bandwidth Optimization

1. **Compressed Responses**: Gzip compression enabled for all responses
2. **Pagination**: Default 20 items per page, maximum 50
3. **Image Optimization**: Thumbnail URLs provided for list views
4. **Selective Fields**: Include only essential data in list responses
5. **Caching**: Aggressive caching with mobile-appropriate TTL values

### Offline Capabilities

- **Sync Endpoint**: `/api/mobile/sync` for offline data synchronization
- **Conflict Resolution**: Server-wins, client-wins, or merge strategies
- **Incremental Updates**: Only sync changed data since last sync
- **Batch Operations**: Process multiple offline operations atomically

## Security Features

### Mobile-Specific Security

1. **Device Fingerprinting**: Unique device identification and tracking
2. **Jailbreak/Root Detection**: Security warnings for compromised devices
3. **Certificate Pinning**: SSL certificate validation
4. **Request Signing**: Optional request signature validation
5. **Biometric Storage**: Secure biometric data handling

### Privacy Protection

- **Location Privacy**: GPS coordinates are never logged or stored permanently
- **Biometric Privacy**: Biometric templates stored only on device
- **Data Minimization**: Only collect necessary data for functionality
- **GDPR Compliance**: Data retention and deletion policies

## Performance Considerations

### AR/VR Optimization

1. **Level of Detail (LOD)**: Multiple model quality levels based on distance
2. **Occlusion Culling**: Hide models not visible to user
3. **Texture Streaming**: Progressive texture loading
4. **Spatial Indexing**: Efficient spatial queries for AR anchors

### Voice Processing Optimization

1. **Audio Compression**: Optimal audio encoding for bandwidth efficiency
2. **Streaming Recognition**: Real-time transcription for long audio
3. **Context Caching**: Cache conversation context to reduce processing time
4. **Model Optimization**: Use lightweight models for mobile inference

## Development Setup

### Prerequisites

- Python 3.11+
- FastAPI
- Redis (for caching and sessions)
- PostgreSQL (for persistent data)
- Speech Recognition libraries
- Mobile development tools (Xcode/Android Studio for app development)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export JWT_SECRET_KEY="your_secure_jwt_secret_key_min_32_chars"
export ANTHROPIC_API_KEY="your_claude_api_key"
export GHL_API_KEY="your_ghl_api_key"
export REDIS_URL="redis://localhost:6379"
```

3. Start the server:
```bash
uvicorn ghl_real_estate_ai.api.main:app --reload --port 8000
```

### Testing

Run the mobile API tests:
```bash
pytest tests/api/mobile/ -v
```

## Mobile App Integration

### iOS Integration

```swift
import Foundation

class MobileAPIClient {
    private let baseURL = "https://your-api.example.com/api/mobile"
    private var accessToken: String?
    
    func login(username: String, password: String, deviceInfo: DeviceInfo) async throws -> AuthResponse {
        // Implementation for iOS login
    }
    
    func authenticateWithBiometric() async throws -> AuthResponse {
        // Implementation for biometric authentication
    }
}
```

### Android Integration

```kotlin
class MobileAPIClient {
    private val baseUrl = "https://your-api.example.com/api/mobile"
    private var accessToken: String? = null
    
    suspend fun login(username: String, password: String, deviceInfo: DeviceInfo): AuthResponse {
        // Implementation for Android login
    }
    
    suspend fun authenticateWithBiometric(): AuthResponse {
        // Implementation for biometric authentication
    }
}
```

## Support

For API support and integration assistance:
- Email: support@jorge-platform.com
- Documentation: https://docs.jorge-platform.com/mobile-api
- Status Page: https://status.jorge-platform.com

## Changelog

### Version 1.0.0 (Initial Release)
- Mobile authentication with biometric support
- AR/VR property visualization
- Voice-enabled AI assistant
- Mobile-optimized property and lead APIs
- Offline sync capabilities
- Comprehensive security features

---

**Business Impact**: This Mobile-First Agent Experience API enables Jorge's real estate agents to deliver cutting-edge mobile experiences that increase client engagement, accelerate sales cycles, and provide competitive advantages in the market. The AR/VR property visualization and voice AI features position agents as technology leaders while the mobile optimization ensures seamless field operations.

**Revenue Enhancement**: $250K+ annually through increased agent productivity, improved client satisfaction, and faster deal closures enabled by mobile technology.