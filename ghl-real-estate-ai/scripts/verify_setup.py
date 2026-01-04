"""
Pre-deployment verification script for GHL Real Estate AI.

Checks:
1. Environment variables
2. Anthropic API connectivity
3. GHL API connectivity
4. Knowledge base status
"""
import os
import sys
import asyncio
import httpx
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghl_utils.config import settings
from ghl_utils.logger import get_logger

logger = get_logger(__name__)

async def check_env():
    print("\n🔍 Checking Environment Variables...")
    required = [
        "ANTHROPIC_API_KEY",
        "GHL_API_KEY",
        "GHL_LOCATION_ID"
    ]
    
    missing = []
    for var in required:
        val = getattr(settings, var.lower(), None)
        if not val or val == "your_api_key_here":
            missing.append(var)
    
    if missing:
        print(f"❌ Missing or default values for: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables are set.")
    return True

async def check_anthropic():
    print("\n🔍 Testing Anthropic API (Claude)...")
    from core.llm_client import LLMClient
    
    client = LLMClient(provider="claude", model=settings.claude_model)
    try:
        # Simple test generation
        response = await client.agenerate(
            prompt="Hello, are you ready?",
            system_prompt="Respond with only 'READY'",
            max_tokens=10
        )
        if "READY" in response.content.upper():
            print(f"✅ Anthropic API is working (Model: {settings.claude_model})")
            return True
        else:
            print(f"⚠️ Anthropic API responded but unexpected content: {response.content}")
            return False
    except Exception as e:
        print(f"❌ Anthropic API failed: {str(e)}")
        return False

async def check_ghl():
    print("\n🔍 Testing GHL API Connectivity...")
    headers = {
        "Authorization": f"Bearer {settings.ghl_api_key}",
        "Version": "2021-07-28"
    }
    url = f"https://services.leadconnectorhq.com/locations/{settings.ghl_location_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                location_name = data.get('location', {}).get('name', 'Unknown')
                print(f"✅ GHL API is working. Connected to Location: {location_name}")
                return True
            else:
                print(f"❌ GHL API returned {response.status_code}: {response.text}")
                return False
    except Exception as e:
        print(f"❌ GHL API connection failed: {str(e)}")
        return False

async def check_kb():
    print("\n🔍 Checking Knowledge Base...")
    from core.rag_engine import RAGEngine
    try:
        rag = RAGEngine(
            collection_name=settings.chroma_collection_name,
            persist_directory=settings.chroma_persist_directory
        )
        count = rag.collection.count()
        print(f"✅ Knowledge Base is initialized with {count} documents.")
        return True
    except Exception as e:
        print(f"❌ Knowledge Base check failed: {str(e)}")
        return False

async def main():
    print("=" * 60)
    print("🚀 GHL Real Estate AI - Production Readiness Check")
    print("=" * 60)
    
    results = await asyncio.gather(
        check_env(),
        check_anthropic(),
        check_ghl(),
        check_kb()
    )
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 SYSTEM IS READY FOR DEPLOYMENT!")
        print("Run 'railway up' to go live.")
    else:
        print("⚠️ SOME CHECKS FAILED. Please fix the issues above before deploying.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
