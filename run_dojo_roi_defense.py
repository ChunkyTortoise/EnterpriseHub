
import asyncio
import logging
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.agent_system.dojo.runner import DojoRunner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_roi_defense_test():
    runner = DojoRunner()
    
    # Custom agent prompt for Elite Jorge Bot
    jorge_prompt = """
    You are an elite Real Estate AI Agent (Jorge Bot).
    Your goal is to qualify sellers with a confrontational, data-driven "Elite" tone.
    No emojis. No hyphens. Max 160 characters.
    Be professional, direct, and slightly confrontational.
    Focus on yield spreads, arbitrage, and net exit metrics.
    When a lead is firm on an unrealistic price, you MUST use Net Yield Justification
    to defend your valuation with hard market data.
    """
    
    print("\n" + "="*60)
    print("🥋 starting DOJO CONFLICT ROI DEFENSE: Jorge Bot vs The Litigious Seller")
    print("="*60 + "\n")
    
    # We'll use 'The Aggressive Investor' but instruct the runner to be litigious/difficult if that's what's available
    # Or we can check what personas are available.
    
    result = await runner.run_sparring_match(
        regimen_name="Conflict ROI Defense",
        persona_name="The Aggressive Investor", # Using most aggressive available
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
    asyncio.run(run_roi_defense_test())
