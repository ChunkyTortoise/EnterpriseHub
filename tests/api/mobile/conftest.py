import base64
from datetime import datetime
from typing import Dict

import pytest
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


@pytest.fixture(autouse=True)
def override_mobile_auth_dependency():
    """
    Keep mobile API tests deterministic:
    - missing auth header -> 401
    - bearer test_token* -> authenticated mock user
    - any other token -> 401
    """
    bearer = HTTPBearer(auto_error=False)

    async def _test_mobile_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> Dict[str, str]:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        token = (credentials.credentials or "").strip()
        if token.startswith("test_token"):
            return {
                "user_id": "test_user_123",
                "username": "test_user",
                "location_id": "test_location_123",
                "is_active": True,
            }

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Import lazily so root conftest can set required env vars first.
    from ghl_real_estate_ai.api.main import app
    from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user

    app.dependency_overrides[get_current_user] = _test_mobile_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def sample_device_info():
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
def sample_audio_data():
    fake_audio = b"fake_audio_data_for_testing_purposes_123456789"
    return base64.b64encode(fake_audio).decode("utf-8")


@pytest.fixture
def sample_voice_request(sample_audio_data, sample_device_info):
    return {
        "audio_data": sample_audio_data,
        "audio_format": "wav",
        "duration_seconds": 3.5,
        "language": "en-US",
        "context": {
            "current_screen": "property_details",
            "property_id": "prop_austin_001",
            "include_audio_response": False,
        },
        "location": {
            "latitude": 30.2672,
            "longitude": -97.7431,
            "accuracy": 10.0,
            "timestamp": datetime.now().isoformat(),
        },
        "device_info": sample_device_info,
    }


@pytest.fixture
def sample_device_capabilities():
    return {
        "supports_ar": True,
        "supports_vr": True,
        "supports_occlusion": True,
        "supports_realtime_lighting": False,
        "supports_hand_tracking": True,
        "high_performance": True,
        "max_anchors": 100,
        "performance_tier": "high",
    }


@pytest.fixture
def sample_user_location():
    return {"latitude": 30.2672, "longitude": -97.7431}


@pytest.fixture
def sample_visualization_request(sample_device_capabilities, sample_user_location):
    return {
        "property_id": "prop_austin_001",
        "user_location": sample_user_location,
        "device_capabilities": sample_device_capabilities,
        "visualization_type": "mixed_reality",
        "quality_preference": "high",
        "include_ai_insights": True,
    }
