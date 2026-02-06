import asyncio
import json
from ghl_real_estate_ai.agent_system.v2.conductor import process_request

async def main():
    print("🚀 Testing V2 Pipeline with Phase 7 & Service 6...")
    address = "123 maple st, Rancho Cucamonga, CA"
    market = "Rancho Cucamonga"
    
    result = await process_request(address, "full_pipeline", market)
    
    print("\n--- Pipeline Results ---")
    print(f"Status: {result.get('status')}")
    print(f"Errors: {result.get('errors')}")
    
    analysis = result.get("analysis_results", {})
    comp = analysis.get("competitive_landscape")
    print(f"\nPhase 7 Competitive Landscape: {comp}")
    
    s6 = result.get("service6_insights", {})
    print(f"\nService 6 Lead Recovery: {s6}")
    
    evals = result.get("evaluations", {})
    print(f"\nEvaluations: {evals}")

if __name__ == "__main__":
    asyncio.run(main())

