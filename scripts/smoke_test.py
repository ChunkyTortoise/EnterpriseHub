
import asyncio
import json
import httpx
import jwt
from datetime import datetime, timedelta, timezone
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service, TenantRole
from ghl_real_estate_ai.services.cache_service import CacheService

async def generate_test_token():
    cache_service = CacheService()
    
    tenant_id = "test_tenant_id"
    user_email = "test@enterprise.com"
    
    tenant_config = {
        "tenant_id": tenant_id,
        "company_name": "Test Enterprise",
        "ontario_mills": "enterprise.com",
        "status": "active",
        "session_timeout_hours": 8
    }
    
    user = {
        "user_id": "test_user_id",
        "tenant_id": tenant_id,
        "email": user_email,
        "roles": [TenantRole.TENANT_ADMIN],
        "permissions": ["manage_tenant", "view_reports", "view_analytics"]
    }
    
    # Mock storage
    await cache_service.set(f"enterprise_tenant:{tenant_id}", tenant_config)
    await cache_service.set(f"enterprise_user:{tenant_id}:{user_email}", user)
    
    # Generate tokens
    tokens = await enterprise_auth_service._generate_enterprise_tokens(user, tenant_config)
    return tokens["access_token"]

async def run_smoke_test():
    print("🚀 Starting Production Smoke Test...")
    
    token = await generate_test_token()
    print(f"✅ Generated Test Token")
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8002") as client:
        # 1. Test Health Deep
        print("🔍 Checking /api/health/deep...")
        try:
            response = await client.get("/api/health/deep", headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Deep Status: {data.get('overall_status')}")
                for service in data.get("services", []):
                    res_time = service.get('response_time_ms')
                    res_time_str = f"{res_time:.2f}ms" if res_time is not None else "N/A"
                    print(f"   - {service['name']}: {service['status']} ({res_time_str})")
            else:
                print(f"❌ Health Deep Failed: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Connection error: {e}")

        # 2. Test Leads API
        print("🔍 Checking /api/leads...")
        try:
            response = await client.get("/api/leads")
            if response.status_code == 200:
                leads = response.json()
                print(f"✅ Fetched {len(leads)} leads")
                if leads:
                    print(f"   - Sample Lead Status: {leads[0].get('status')}")
                    print(f"   - Sample Lead Temperature: {leads[0].get('temperature')}")
            else:
                print(f"❌ Leads API Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

        # 3. Test Bot Streaming
        print("🔍 Checking /api/bots/jorge-seller-bot/chat (streaming)...")
        try:
            payload = {
                "content": "I want to sell my house in Rancho Cucamonga.",
                "leadId": "test_lead_123",
                "leadName": "John Rancho Cucamonga"
            }
            async with client.stream("POST", "/api/bots/jorge-seller-bot/chat", json=payload) as response:
                if response.status_code == 200:
                    print(f"✅ Streaming started")
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            if data.get("type") == "chunk":
                                chunk_count += 1
                            elif data.get("type") == "complete":
                                print(f"✅ Received complete response ({chunk_count} chunks)")
                            elif data.get("type") == "done":
                                break
                    if chunk_count > 0:
                        print(f"✅ Successfully received {chunk_count} SSE chunks")
                    else:
                        print(f"⚠️ No chunks received")
                else:
                    print(f"❌ Streaming failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
