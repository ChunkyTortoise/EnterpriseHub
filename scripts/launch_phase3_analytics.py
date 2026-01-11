#!/usr/bin/env python3
"""
Launch Phase 3 Business Analytics Dashboard
==========================================

Quick start script for Phase 3 business impact measurement system.

Usage:
    python scripts/launch_phase3_analytics.py

Author: EnterpriseHub Development Team
Created: January 2026
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def initialize_system():
    """Initialize Phase 3 business impact measurement system."""
    print("🚀 Initializing Phase 3 Business Impact Measurement System...")
    print("=" * 70)

    try:
        # Import services
        from ghl_real_estate_ai.services.feature_flag_manager import (
            get_feature_flag_manager,
            initialize_phase3_flags
        )
        from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
            get_business_impact_tracker
        )

        # Check Redis connection
        print("\n📡 Checking Redis connection...")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        print(f"   Redis URL: {redis_url}")

        # Initialize feature flag manager
        print("\n🚩 Initializing Feature Flag Manager...")
        flag_manager = await get_feature_flag_manager(redis_url)
        print("   ✅ Feature flag manager initialized")

        # Initialize Phase 3 feature flags
        print("\n🎯 Setting up Phase 3 feature flags...")
        success = await initialize_phase3_flags()
        if success:
            print("   ✅ Phase 3 flags configured:")
            flags = await flag_manager.get_all_flags()
            for flag in flags:
                if flag.feature_id in ['realtime_intelligence', 'property_intelligence',
                                      'churn_prevention', 'ai_coaching']:
                    print(f"      • {flag.name} ({flag.rollout_stage.value})")
        else:
            print("   ⚠️  Warning: Could not initialize all flags")

        # Initialize business impact tracker
        print("\n💰 Initializing Business Impact Tracker...")
        tracker = await get_business_impact_tracker(redis_url)
        print("   ✅ Business impact tracker initialized")

        # Check performance metrics
        print("\n⚡ Performance Check...")
        metrics = await flag_manager.get_performance_metrics()
        if metrics.get('total_lookups', 0) > 0:
            print(f"   Average lookup latency: {metrics.get('avg_latency_ms', 0):.2f}ms")
            print(f"   Cache size: {metrics.get('cache_size', 0)} flags")
        else:
            print("   No performance data yet")

        print("\n" + "=" * 70)
        print("✅ System Initialization Complete!")
        print("\n📊 Next Steps:")
        print("   1. Launch dashboard: streamlit run ghl_real_estate_ai/streamlit_components/phase3_business_analytics_dashboard.py")
        print("   2. Access at: http://localhost:8501")
        print("   3. See guide: PHASE3_BUSINESS_IMPACT_MEASUREMENT_GUIDE.md")
        print("\n💡 Quick Test:")
        print("   python scripts/test_phase3_system.py")
        print()

    except ImportError as e:
        print(f"\n❌ Error: Missing dependency - {e}")
        print("\n📦 Install required packages:")
        print("   pip install redis asyncio streamlit plotly pandas")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check Redis is running: redis-cli ping")
        print("   2. Verify Redis URL: echo $REDIS_URL")
        print("   3. Check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   Phase 3 Business Impact Measurement System")
    print("   EnterpriseHub - January 2026")
    print("=" * 70)

    asyncio.run(initialize_system())
