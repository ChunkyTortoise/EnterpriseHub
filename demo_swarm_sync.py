"""
Demo: Real-time Swarm Sync
Simulates a hot lead triggering a multi-channel swarm and updates the Elite Dashboard via AG-UI.
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.services.multi_channel_swarm_orchestrator import MultiChannelSwarmOrchestrator
from ghl_real_estate_ai.services.agent_state_sync import sync_service

async def run_demo():
    print("🚀 Starting Real-time Swarm Sync Demo...")
    print("Ensure your FastAPI server is running (uvicorn ghl_real_estate_ai.api.main:app)")
    
    orchestrator = MultiChannelSwarmOrchestrator()
    
    lead_data = {
        "id": "lead_123",
        "name": "Sarah Jenkins",
        "phone": "+15125550199",
        "email": "sarah.j@example.com",
        "interest": "Austin Luxury Condos"
    }
    
    # 1. Trigger the swarm (this will start recording thoughts)
    print("\n--- Triggering Swarm ---")
    await orchestrator.trigger_hot_lead_swarm("lead_123", lead_data)
    
    # 2. Simulate some KPI updates
    print("\n--- Updating KPIs ---")
    sync_service.update_state("kpis/total_leads", 12701)
    sync_service.update_state("kpis/response_rate", 98.5)
    
    # 3. Add a few more autonomous thoughts
    print("\n--- Recording Autonomous Thoughts ---")
    await asyncio.sleep(2)
    sync_service.record_agent_thought("LeadScorer", "Sarah Jenkins' behavior indicates 92% purchase probability.", "Success")
    
    await asyncio.sleep(2)
    sync_service.record_agent_thought("MarketBot", "Inventory in Austin zip 78701 is decreasing. Increasing urgency in Sarah's follow-up.", "Warning")
    
    print("\n✅ Demo sequence complete. Check your dashboard at http://localhost:3000/dashboard")

if __name__ == "__main__":
    asyncio.run(run_demo())
