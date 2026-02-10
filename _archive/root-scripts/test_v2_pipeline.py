import pytest

@pytest.mark.unit
"""
Test script for the V2 Agentic Pipeline.
Verifies Research -> Analysis -> Design -> Executive loop.
"""

import asyncio
import json
from ghl_real_estate_ai.agent_system.v2.conductor import process_request

async def main():
    print("🚀 Starting V2 Pipeline Test...")
    address = "123 Maple St, Austin, TX"
    request = "full_pipeline"
    market = "Austin, TX"
    
    try:
        result = await process_request(address, request, market)
        
        print("\n--- TEST RESULTS ---")
        print(f"Status: {result.get('status')}")
        print(f"Intent: {result.get('intent')}")
        
        if result.get('research_data'):
            print("✅ Research Data captured")
        else:
            print("❌ Research Data MISSING")
            
        if result.get('analysis_results'):
            print("✅ Analysis Results captured")
        else:
            print("❌ Analysis Results MISSING")
            
        if result.get('design_data'):
            print("✅ Design Data captured")
        else:
            print("❌ Design Data MISSING")
            
        if result.get('executive_summary'):
            print("✅ Executive Summary captured")
        else:
            print("❌ Executive Summary MISSING")
            
        if result.get('errors'):
            print(f"⚠️ Errors: {result.get('errors')}")
            
        # Optional: Save result to file for inspection
        with open("test_v2_results.json", "w") as f:
            # result contains things that might not be JSON serializable easily if they are Dict[str, Any] with complex types,
            # but here they are .dict() from Pydantic models so it should be fine.
            # However, some might be None.
            clean_result = {k: v for k, v in result.items() if k != "errors" or v}
            json.dump(clean_result, f, indent=2)
            
    except Exception as e:
        print(f"💥 Pipeline Test CRASHED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
