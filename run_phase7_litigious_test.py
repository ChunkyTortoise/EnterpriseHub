
import asyncio
import logging
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.agent_system.dojo.runner import DojoRunner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_litigious_test():
    runner = DojoRunner()
    
    # Custom agent prompt for ROI Defense
    roi_defense_prompt = """
    You are an AI ROI Specialist for Jorge Salas.
    Your goal is to defend Jorge's financial valuations and ROI logic using data and market logic.
    When a lead is hostile or threatens legal action, remain calm but firm. 
    Explain that our valuations are based on objective market metrics, repair estimates, and required net yield for our investors.
    DO NOT break rapport, but DO NOT back down on the math.
    Be professional, direct, and confrontational when ROI is at stake.
    """
    
    print("\n" + "="*60)
    print("🥋 starting DOJO STRESS-TEST: ROI Specialist vs The Litigious Seller")
    print("="*60 + "\n")
    
    result = await runner.run_sparring_match(
        regimen_name="Conflict ROI Defense",
        persona_name="The Litigious Seller",
        max_turns=3,
        custom_agent_prompt=roi_defense_prompt
    )
    
    print("\n" + "-"*20 + " RESULTS " + "-"*20)
    print(f"Overall Score: {result.get('overall', 'N/A')}/10")
    
    breakdown = result.get('breakdown', {})
    print(f"Compliance Score: {breakdown.get('compliance', 'N/A')}/10")
    print(f"Empathy Score: {breakdown.get('empathy', 'N/A')}/10")
    print(f"Directness Score: {breakdown.get('directness', 'N/A')}/10")
    print("-" * 49)
    
    print("\n" + "-"*20 + " CONVERSATION " + "-"*20)
    for msg in result['history']:
        role = "🤖 BOT" if msg['role'] == 'assistant' else "👤 LEAD"
        print(f"{role}: {msg['content']}\n")
    print("-" * 54 + "\n")

if __name__ == "__main__":
    asyncio.run(run_litigious_test())
