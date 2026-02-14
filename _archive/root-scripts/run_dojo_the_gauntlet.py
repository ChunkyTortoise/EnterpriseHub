import asyncio
import logging
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.agent_system.dojo.runner import DojoRunner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_the_gauntlet_test():
    try:
        runner = DojoRunner()
        
        # Custom agent prompt for Elite Jorge Bot - MAX INTENSITY
        jorge_prompt = """
        You are an elite Real Estate AI Agent (Jorge Bot).
        Your goal is to qualify high-net-worth sellers with a confrontational, data-driven "Elite" tone.
        No emojis. No hyphens. Max 160 characters.
        Be professional, direct, and elite.
        
        GAUNTLET PROTOCOLS:
        1. ROI DEFENSE: Use hard market data to justify valuations against skeptic pushback.
        2. ARBITRAGE: Pitch yield spreads and pivot opportunities between London, Singapore, and Rancho Cucamonga.
        3. COMPLIANCE: Strict GDPR and PDPA adherence. Mention secure processing if questioned.
        4. TECHNICAL: Reference swap rates, cap rates, and net exit metrics.
        """
        
        print("\n" + "="*60)
        print("🥋 starting THE GAUNTLET: Jorge Bot vs The Sophisticated Arbitrageur")
        print("="*60 + "\n")
        
        result = await runner.run_sparring_match(
            regimen_name="The Gauntlet",
            persona_name="The Sophisticated Global Arbitrageur",
            max_turns=5,
            custom_agent_prompt=jorge_prompt
        )
        
        print("\n" + "-"*20 + " GAUNTLET RESULTS " + "-"*20)
        print(f"Overall Score: {result.get('overall', 'N/A')}/10")
        
        breakdown = result.get('breakdown', {})
        print(f"Tone Match Score: {breakdown.get('tone_match', 'N/A')}/10")
        print(f"Goal Pursuit Score: {breakdown.get('goal_pursuit', 'N/A')}/10")
        print(f"Compliance Score: {breakdown.get('compliance', 'N/A')}/10")
        print("-" * 58)
        
        print("\n" + "-"*20 + " CONVERSATION " + "-"*20)
        for msg in result['history']:
            role = "🤖 BOT" if msg['role'] == 'assistant' else "👤 LEAD"
            print(f"{role}: {msg['content']}\n")
        print("-" * 54 + "\n")

    except Exception as e:
        print(f"\n❌ GAUNTLET FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_the_gauntlet_test())