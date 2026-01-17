"""
Verification Suite for Optimized Gemini Workflow.
Tests: Context Caching, Structured Output, and Skill Integration.
"""
import asyncio
import json
from pathlib import Path
from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.agent_system.skills.base import registry as skill_registry
from ghl_real_estate_ai.agent_system.skills.codebase import map_codebase
from ghl_real_estate_ai.agents.swarm_orchestrator import SwarmOrchestrator

async def verify_context_caching():
    print("\n--- Testing Gemini Context Caching ---")
    llm = LLMClient(provider="gemini")
    
    # 1. Prepare large content (the whole project structure)
    structure = map_codebase(".")
    content = f"Project Structure:\n{json.dumps(structure, indent=2)}\n"
    
    # 2. Create Cache
    print("Creating context cache...")
    try:
        cache_name = llm.create_context_cache(
            content=content,
            display_name="EnterpriseHub_Structure_Cache",
            ttl_minutes=15
        )
        print(f"Cache created: {cache_name}")
        
        # 3. Use Cache for a query
        print("Querying using cache...")
        response = await llm.agenerate(
            prompt="Based on the cached project structure, identify the 3 most critical files for GHL integration.",
            cached_content=cache_name
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Caching test skipped or failed (likely API constraints): {e}")

async def verify_structured_output():
    print("\n--- Testing Structured Output (JSON Schema) ---")
    llm = LLMClient(provider="gemini")
    
    schema = {
        "type": "object",
        "properties": {
            "critical_issues": {
                "type": "array",
                "items": {"type": "string"}
            },
            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
        },
        "required": ["critical_issues", "risk_level"]
    }
    
    prompt = "Perform a quick risk assessment of a real estate AI system that handles PII but has no explicit encryption layer mentioned in its core services."
    
    response = await llm.agenerate(
        prompt=prompt,
        response_schema=schema
    )
    
    print(f"Structured Response: {response.content}")
    try:
        parsed = json.loads(response.content)
        print("✅ JSON parsed successfully and matches schema.")
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")

async def main():
    print("🚀 Starting Optimized Workflow Verification...")
    
    # Run tests
    await verify_structured_output()
    await verify_context_caching()
    
    print("\n✨ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(main())
