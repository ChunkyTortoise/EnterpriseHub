
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.event_bus import get_event_bus, EventType, EventPriority
from src.core.ai_client import AIClient
from src.core.swarm_orchestrator import IntelligenceSwarmOrchestrator
from src.core.specialized_agents import SupplyChainSwarmAgent, MAIntelligenceSwarmAgent, RegulatorySentinelSwarmAgent

class MockAIClient:
    """Mock LLM client for simulation."""
    def __init__(self):
        self.provider = "mock"
        self.model = "mock-model"

    async def generate_strategic_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        return f"SIMULATED STRATEGY: Defensive measures recommended for {prompt[:50]}..."

    async def agenerate(self, prompt: str, **kwargs) -> Any:
        class MockResponse:
            content = "Mocked AI Response Content"
        return MockResponse()

async def run_simulation():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Starting Hostile Takeover Simulation...")
    
    bus = get_event_bus()
    ai = MockAIClient() # Use mock
    orchestrator = IntelligenceSwarmOrchestrator(bus, ai)
    
    # 1. Register Agents
    ma_agent = MAIntelligenceSwarmAgent(ai, orchestrator)
    reg_agent = RegulatorySentinelSwarmAgent(ai, orchestrator)
    
    orchestrator.register_agent(ma_agent)
    orchestrator.register_agent(reg_agent)
    
    # 2. Set Autonomous Mode OFF for verification of the queue
    orchestrator.toggle_autonomous_mode(False)
    
    await orchestrator.start_swarm()
    
    print("📡 Publishing MA_THREAT_DETECTED event...")
    await bus.publish(
        event_type=EventType.MA_THREAT_DETECTED,
        data={
            "potential_acquirer": "Hostile Corp LLC",
            "detection_confidence": 0.95,
            "description": "Rapid accumulation of 4.9% stake detected along with aggressive call option buying."
        },
        source_system="threat_detector",
        priority=EventPriority.CRITICAL
    )
    
    # Give agents time to think
    print("🧠 Agents are thinking...")
    await asyncio.sleep(5)
    
    # 3. Verify Pending Actions
    print(f"📋 Pending Actions in Queue: {len(orchestrator.pending_actions)}")
    for action in orchestrator.pending_actions:
        print(f"  - [{action['status']}] {action['agent']}: {action['data']['event_type'].name}")
        
    # 4. Approve One Action
    if orchestrator.pending_actions:
        action_id = orchestrator.pending_actions[0]['id']
        print(f"✅ Approving action: {action_id}")
        await orchestrator.approve_action(action_id)
    
    # Give MAAgent time to process the regulatory assessment and synthesize final defense
    await asyncio.sleep(2)
    
    # Check if memory was updated
    memory_file = ".claude/memory/decisions/strategic_actions.jsonl"
    if os.path.exists(memory_file):
        print(f"💾 Memory file found: {memory_file}")
        with open(memory_file, 'r') as f:
            lines = f.readlines()
            print(f"📄 Memory entries: {len(lines)}")
            print(f"📝 Last entry: {lines[-1].strip()}")
    else:
        print("❌ Memory file NOT found!")

    await orchestrator.stop_swarm()
    print("🏁 Simulation Complete.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
