
import asyncio
import logging
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.agent_system.dojo.runner import DojoRunner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_international_compliance_test():
    runner = DojoRunner()
    
    # Custom agent prompt for Elite Jorge Bot with International Knowledge
    jorge_prompt = """
    You are an elite Real Estate AI Agent (Jorge Bot).
    Your goal is to qualify sellers with a confrontational, data-driven "Elite" tone.
    No emojis. No hyphens. Max 160 characters.
    Be professional, direct, and slightly confrontational.
    
    INTERNATIONAL COMPLIANCE:
    - GDPR: You must acknowledge data privacy and state that data is processed securely.
    - SINGAPORE: You must be aware of ABSD (Additional Buyer's Stamp Duty) and CEA regulations.
    - EMEA: You must follow local real estate disclosure standards.
    - SMS: Strictly <160 chars.
    """
    
    print("\n" + "="*60)
    print("🥋 starting DOJO INTERNATIONAL COMPLIANCE: Jorge Bot vs The Regulatory Skeptic")
    print("="*60 + "\n")
    
    result = await runner.run_sparring_match(
        regimen_name="International Compliance",
        persona_name="The International Regulatory Skeptic",
        max_turns=4,
        custom_agent_prompt=jorge_prompt
    )
    
    print("\n" + "-"*20 + " RESULTS " + "-"*20)
    print(f"Overall Score: {result.get('overall', 'N/A')}/10")
    
    breakdown = result.get('breakdown', {})
    print(f"Tone Match Score: {breakdown.get('tone_match', 'N/A')}/10")
    print(f"Goal Pursuit Score: {breakdown.get('goal_pursuit', 'N/A')}/10")
    print(f"Directness Score: {breakdown.get('directness', 'N/A')}/10")
    print("-" * 49)
    
    print("\n" + "-"*20 + " CONVERSATION " + "-"*20)
    for msg in result['history']:
        role = "🤖 BOT" if msg['role'] == 'assistant' else "👤 LEAD"
        print(f"{role}: {msg['content']}\n")
    print("-" * 54 + "\n")

if __name__ == "__main__":
    asyncio.run(run_international_compliance_test())
