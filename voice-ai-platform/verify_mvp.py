#!/usr/bin/env python
"""Quick verification script to test Voice AI Platform MVP components."""

from __future__ import annotations

import asyncio
import sys


async def verify_imports():
    """Verify all critical imports work."""
    print("✓ Testing imports...")
    try:
        from voice_ai.main import create_app
        from voice_ai.models.call import Call, CallStatus, CallDirection
        from voice_ai.models.agent_persona import AgentPersona
        from voice_ai.telephony.call_manager import CallManager
        from voice_ai.telephony.twilio_handler import TwilioHandler
        from voice_ai.pipeline.voice_pipeline import VoicePipeline, PipelineState
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


async def verify_app_creation():
    """Verify FastAPI app can be created."""
    print("✓ Testing app creation...")
    try:
        from voice_ai.main import create_app

        app = create_app()
        assert app is not None
        assert app.title == "Voice AI Platform"
        print(f"  ✓ App created: {app.title} v{app.version}")
        return True
    except Exception as e:
        print(f"  ✗ App creation failed: {e}")
        return False


async def verify_models():
    """Verify SQLAlchemy models."""
    print("✓ Testing models...")
    try:
        import uuid
        from voice_ai.models.call import Call, CallStatus, CallDirection
        from voice_ai.models.agent_persona import AgentPersona

        # Create Call instance
        call = Call(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
            status=CallStatus.INITIATED,
            bot_type="lead",
        )
        assert call.status == CallStatus.INITIATED

        # Create AgentPersona instance
        persona = AgentPersona(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            name="Jorge Lead Bot",
            bot_type="lead",
            voice_id="test_voice",
        )
        assert persona.bot_type == "lead"

        print("  ✓ Models instantiate correctly")
        return True
    except Exception as e:
        print(f"  ✗ Model test failed: {e}")
        return False


async def verify_config():
    """Verify configuration loading."""
    print("✓ Testing configuration...")
    try:
        from voice_ai.config import get_settings

        settings = get_settings()
        assert settings.app_name is not None
        assert settings.database_url is not None
        print(f"  ✓ Config loaded: {settings.app_name}")
        return True
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        return False


async def verify_routes():
    """Verify API routes are registered."""
    print("✓ Testing API routes...")
    try:
        from voice_ai.main import create_app

        app = create_app()
        routes = [route.path for route in app.routes]

        required_routes = [
            "/health",
            "/api/v1/calls/inbound",
            "/api/v1/calls/outbound",
            "/api/v1/calls/{call_id}",
            "/api/v1/webhooks/twilio/status",
        ]

        for route in required_routes:
            assert route in routes, f"Missing route: {route}"

        print(f"  ✓ {len(routes)} routes registered")
        return True
    except Exception as e:
        print(f"  ✗ Route test failed: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Voice AI Platform - MVP Verification")
    print("=" * 60)

    checks = [
        verify_imports,
        verify_app_creation,
        verify_models,
        verify_config,
        verify_routes,
    ]

    results = []
    for check in checks:
        try:
            result = await check()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append(False)

    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} checks passed")
    print("=" * 60)

    if all(results):
        print("✓ MVP verification PASSED - Platform is ready!")
        return 0
    else:
        print("✗ MVP verification FAILED - See errors above")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
