#!/usr/bin/env python3
"""
Debug Jorge's Lead Bot Dashboard

Simplified launcher to test the dashboard without complex dependencies.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    print("❌ Streamlit not available. Install with: pip install streamlit")
    STREAMLIT_AVAILABLE = False
    sys.exit(1)

# Mock the complex dependencies that might not be installed
class MockService:
    """Mock service for testing dashboard without full backend."""

    async def get_dashboard_metrics(self):
        return {
            "voice_ai": {
                "total_calls": 47,
                "qualified_leads": 23,
                "avg_call_duration": 285,
                "qualification_rate": 48.9,
                "transfer_rate": 12.8
            },
            "marketing": {
                "active_campaigns": 8,
                "total_impressions": 15420,
                "conversion_rate": 3.2,
                "cost_per_lead": 18.50,
                "roi": 340
            },
            "client_retention": {
                "total_clients": 156,
                "engagement_score": 84.2,
                "retention_rate": 92.1,
                "referrals_this_month": 12,
                "lifetime_value": 28500
            },
            "market_predictions": {
                "active_markets": 3,
                "prediction_accuracy": 87.6,
                "opportunities_found": 15,
                "avg_roi_potential": 22.3
            },
            "integration_health": {
                "ghl_status": "healthy",
                "claude_status": "healthy",
                "overall_uptime": 99.2
            }
        }

    async def start_voice_call(self, phone_number, caller_name=None):
        return {
            "call_id": "call_20260119_debug",
            "status": "active",
            "message": "Voice AI call started successfully (DEBUG MODE)"
        }

    async def get_voice_analytics(self, days=7):
        return {
            "period_days": days,
            "analytics": {
                "total_calls": 47,
                "successful_calls": 43,
                "qualified_leads": 23,
                "avg_qualification_score": 78.2,
                "top_lead_sources": ["Zillow", "Facebook", "Referral"],
                "call_outcomes": {
                    "Qualified Lead": 23,
                    "Follow-up Scheduled": 12,
                    "Not Interested": 8,
                    "Wrong Number": 4
                }
            }
        }

def test_dashboard_components():
    """Test the dashboard components individually."""
    print("🧪 Testing Jorge's Dashboard Components...")

    # Test basic imports that should work
    try:
        import streamlit as st
        import pandas as pd
        import json
        from datetime import datetime, timedelta
        print("✅ Core dashboard dependencies available")

        # Test mock service
        mock_service = MockService()
        print("✅ Mock service created")

        # Test async functionality
        import asyncio
        metrics = asyncio.run(mock_service.get_dashboard_metrics())
        print(f"✅ Mock metrics generated: {len(metrics)} modules")

        return True

    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

def launch_debug_dashboard():
    """Launch the dashboard in debug mode."""
    print("🚀 Launching Jorge's Dashboard (DEBUG MODE)...")

    # Test components first
    if not test_dashboard_components():
        print("❌ Component test failed, cannot launch dashboard")
        return

    # Try to run the dashboard component
    try:
        # Import the dashboard component
        dashboard_path = "ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py"

        print(f"📁 Loading dashboard from: {dashboard_path}")

        # Run with streamlit
        import subprocess
        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path,
               "--server.port", "8502", "--server.address", "localhost"]

        print("🌐 Starting Streamlit server on http://localhost:8502")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)

        subprocess.run(cmd)

    except Exception as e:
        print(f"❌ Failed to launch dashboard: {e}")
        print("\n🔧 DEBUGGING TIPS:")
        print("1. Install streamlit: pip install streamlit")
        print("2. Check file exists: ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py")
        print("3. Run manually: streamlit run ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py")

if __name__ == "__main__":
    print("🤖 Jorge's Lead Bot - Debug Mode")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Just run component tests
        success = test_dashboard_components()
        sys.exit(0 if success else 1)
    else:
        # Launch the dashboard
        launch_debug_dashboard()