"""
Demo of Enhanced Agent System with Skills and Local Memory.
===========================================================

This script demonstrates:
1. Skill registration and discovery.
2. Local memory fallback.
3. Swarm orchestration using the new skills.
"""
import asyncio
import json
from ghl_real_estate_ai.agent_system.skills.base import registry
import ghl_real_estate_ai.agent_system.skills.real_estate
import ghl_real_estate_ai.agent_system.skills.monitoring
import ghl_real_estate_ai.agent_system.skills.codebase
from ghl_real_estate_ai.agent_system.memory.manager import memory_manager
from ghl_real_estate_ai.agents.swarm_orchestrator import SwarmOrchestrator
from pathlib import Path

async def demo():
    print("🚀 Initializing Enhanced Agent System Demo...")
    
    # 1. Skill Discovery
    print("\n--- 1. Skill Discovery ---")
    all_skills = registry.skills.keys()
    print(f"Registered Skills: {', '.join(all_skills)}")
    
    real_estate_skills = registry.find_relevant_skills("property")
    print(f"Relevant skills for 'property': {[s.name for s in real_estate_skills]}")

    # 2. Local Memory Persistence
    print("\n--- 2. Memory Layer ---")
    lead_id = "demo_lead_123"
    await memory_manager.save_interaction(lead_id, "I am looking for a 3-bedroom house in Austin with a budget of $600,000.", role="user")
    await memory_manager.save_interaction(lead_id, "I also hate houses with no backyard.", role="user")
    
    context = await memory_manager.retrieve_context(lead_id)
    print("Retrieved Context:")
    print(context)

    # 3. Swarm Orchestration with Skills
    print("\n--- 3. Swarm Execution (Mock) ---")
    # Using the SwarmOrchestrator to run a simple task
    orchestrator = SwarmOrchestrator(Path("."))
    
    # We'll mock a task execution that uses our new skills
    task_description = "Find a 3-bedroom house in Austin for $600k and prepare a pitch."
    print(f"Executing Swarm Task: {task_description}")
    
    # In a real run, the orchestrator would use LLM to pick tools.
    # Here we simulate the tool selection.
    search_skill = registry.get_skill("search_properties")
    pitch_skill = registry.get_skill("generate_property_pitch")
    
    if search_skill and pitch_skill:
        # Step 1: Search
        results = search_skill.execute(budget=600000, location="Austin", bedrooms=3)
        print(f"Found {len(results)} matches.")
        
        if results:
            # Step 2: Pitch for the first result
            prop = results[0]
            print(f"Generating pitch for: {prop.get('address')}")
            # Note: generate_property_pitch is async
            pitch = await pitch_skill.func(property_id=prop.get('id'), lead_preferences={"budget": 600000, "bedrooms": 3})
            print(f"\nFINAL PITCH:\n{pitch}")

if __name__ == "__main__":
    asyncio.run(demo())
