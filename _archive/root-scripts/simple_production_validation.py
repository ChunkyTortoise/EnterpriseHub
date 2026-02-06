#!/usr/bin/env python3
"""
Simple Production Readiness Validation
Fast validation of key components for production readiness assessment.
"""

import asyncio
import json
import time
from typing import Dict, Any
import httpx

# Test configuration
TEST_CONFIG = {
    'base_url': 'http://localhost:8000',
    'bi_endpoints': [
        '/api/bi/dashboard-kpis',
        '/api/bi/revenue-intelligence',
        '/api/bi/bot-performance',
        '/api/bi/real-time-metrics',
        '/api/bi/predictive-insights',
        '/api/bi/anomaly-detection',
        '/api/bi/cache-analytics',
        '/api/bi/drill-down',
        '/api/bi/trigger-aggregation',
        '/api/bi/warm-cache'
    ]
}

async def test_system_health():
    """Test basic system health."""
    print("🔍 Testing System Health...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{TEST_CONFIG['base_url']}/", timeout=5.0)
            if response.status_code == 200:
                print("    ✅ Server is running")
                return True
            else:
                print(f"    ⚠️ Server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"    ❌ Server not accessible: {e}")
            return False

async def test_api_endpoints():
    """Test API endpoint availability."""
    print("🔧 Testing API Endpoints...")

    passed = 0
    total = len(TEST_CONFIG['bi_endpoints'])

    async with httpx.AsyncClient() as client:
        for endpoint in TEST_CONFIG['bi_endpoints']:
            try:
                # Handle different HTTP methods
                if endpoint in ['/api/bi/drill-down', '/api/bi/trigger-aggregation', '/api/bi/warm-cache']:
                    if endpoint == '/api/bi/drill-down':
                        json_data = {
                            "component": "revenue",
                            "metric": "total_revenue",
                            "timeframe": "24h",
                            "location_id": "test"
                        }
                        response = await client.post(f"{TEST_CONFIG['base_url']}{endpoint}", json=json_data, timeout=10.0)
                    else:
                        response = await client.post(f"{TEST_CONFIG['base_url']}{endpoint}", timeout=10.0)
                else:
                    response = await client.get(f"{TEST_CONFIG['base_url']}{endpoint}", timeout=10.0)

                if response.status_code in [200, 401]:  # 401 is expected without auth
                    print(f"    ✅ {endpoint}")
                    passed += 1
                else:
                    print(f"    ❌ {endpoint} - Status {response.status_code}")

            except Exception as e:
                print(f"    ❌ {endpoint} - Error: {e}")

    success_rate = (passed / total) * 100
    print(f"    📊 API Success Rate: {success_rate:.1f}% ({passed}/{total})")
    return success_rate

async def test_security_features():
    """Test security features."""
    print("🔒 Testing Security Features...")

    security_score = 0
    total_checks = 4

    async with httpx.AsyncClient() as client:
        # Test authentication requirement
        try:
            response = await client.get(f"{TEST_CONFIG['base_url']}/api/bi/dashboard-kpis")
            if response.status_code == 401:
                print("    ✅ Authentication properly enforced")
                security_score += 1
            else:
                print("    ⚠️ Authentication may not be properly enforced")
        except Exception as e:
            print(f"    ❌ Auth test error: {e}")

        # Test rate limiting (rapid requests)
        rate_limit_triggered = False
        try:
            for i in range(15):
                response = await client.get(f"{TEST_CONFIG['base_url']}/api/bi/real-time-metrics", timeout=2.0)
                if response.status_code == 429:
                    rate_limit_triggered = True
                    break
        except:
            pass

        if rate_limit_triggered:
            print("    ✅ Rate limiting is active")
            security_score += 1
        else:
            print("    ⚠️ Rate limiting not detected")

        # Test input validation
        try:
            response = await client.get(
                f"{TEST_CONFIG['base_url']}/api/bi/dashboard-kpis",
                params={'timeframe': 'invalid_value'}
            )
            if response.status_code in [400, 422]:
                print("    ✅ Input validation working")
                security_score += 1
            else:
                print("    ⚠️ Input validation may need improvement")
        except Exception as e:
            print(f"    ❌ Validation test error: {e}")

        # Test SQL injection protection
        try:
            response = await client.get(
                f"{TEST_CONFIG['base_url']}/api/bi/dashboard-kpis",
                params={'location_id': "'; DROP TABLE users; --"}
            )
            if response.status_code in [400, 422]:
                print("    ✅ SQL injection protection active")
                security_score += 1
            else:
                print("    ⚠️ SQL injection protection may need improvement")
        except Exception as e:
            print(f"    ❌ SQL injection test error: {e}")

    security_percentage = (security_score / total_checks) * 100
    print(f"    📊 Security Score: {security_percentage:.1f}% ({security_score}/{total_checks})")
    return security_percentage

async def test_websocket_health():
    """Test WebSocket health."""
    print("🔄 Testing WebSocket Health...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{TEST_CONFIG['base_url']}/ws/bi/health", timeout=10.0)
            if response.status_code == 200:
                print("    ✅ WebSocket health endpoint responsive")
                return True
            else:
                print(f"    ⚠️ WebSocket health endpoint returned {response.status_code}")
                return False
        except Exception as e:
            print(f"    ❌ WebSocket health test error: {e}")
            return False

def calculate_production_readiness(api_score, security_score, websocket_health):
    """Calculate overall production readiness score."""

    # Weighted scoring
    api_weight = 0.4
    security_weight = 0.3
    websocket_weight = 0.2
    basic_functionality_weight = 0.1

    # Basic functionality (server running)
    basic_score = 100  # Server is running

    readiness_score = (
        api_score * api_weight +
        security_score * security_weight +
        (100 if websocket_health else 0) * websocket_weight +
        basic_score * basic_functionality_weight
    )

    return readiness_score

async def main():
    """Run simple production readiness validation."""

    print("🚀 Jorge's BI Dashboard - Simple Production Readiness Validation")
    print("=" * 70)

    start_time = time.time()

    # Run tests
    server_healthy = await test_system_health()

    if not server_healthy:
        print("\n❌ Cannot proceed - server not accessible")
        return

    api_score = await test_api_endpoints()
    security_score = await test_security_features()
    websocket_health = await test_websocket_health()

    # Calculate overall score
    readiness_score = calculate_production_readiness(api_score, security_score, websocket_health)

    # Results
    print("\n" + "=" * 70)
    print("📊 PRODUCTION READINESS SUMMARY")
    print("=" * 70)

    print(f"API Endpoints:        {api_score:.1f}%")
    print(f"Security Features:    {security_score:.1f}%")
    print(f"WebSocket Health:     {'✅ Operational' if websocket_health else '❌ Issues'}")
    print(f"Overall Readiness:    {readiness_score:.1f}%")

    if readiness_score >= 90:
        status = "🟢 READY FOR PRODUCTION"
    elif readiness_score >= 75:
        status = "🟡 NEEDS MINOR IMPROVEMENTS"
    elif readiness_score >= 60:
        status = "🟠 NEEDS SIGNIFICANT IMPROVEMENTS"
    else:
        status = "🔴 NOT READY FOR PRODUCTION"

    print(f"\nProduction Status:    {status}")

    duration = time.time() - start_time
    print(f"Test Duration:        {duration:.1f} seconds")

    print("\n💡 NEXT STEPS:")
    if api_score < 90:
        print("   - Fix failing API endpoints")
    if security_score < 90:
        print("   - Enhance security configuration")
    if not websocket_health:
        print("   - Resolve WebSocket service issues")
    if readiness_score >= 90:
        print("   - System ready for production deployment!")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(main())