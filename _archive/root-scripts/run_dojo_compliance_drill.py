
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path.cwd()))

from ghl_real_estate_ai.agent_system.dojo.runner import run_regimen

async def main():
    print("🛡️ Starting Dojo Compliance Drill...")
    print("Scenario: 'The Fair Housing Trap' - Lead asking about neighborhood demographics.\n")
    
    # Run the compliance regimen
    results = await run_regimen("Compliance Drills", iterations=3)
    
    print(f"🏁 Drill Complete: {results['regimen']}")
    print(f"📊 Average Score: {results['average_score']:.2f}/5.0")
    
    for i, res in enumerate(results['results']):
        scores = res['scores']
        print(f"\nIteration {i+1} Breakdown:")
        print(f"  - Compliance: {scores['compliance']:.1f}")
        print(f"  - Empathy: {scores['empathy']:.1f}")
        print(f"  - Goal Pursuit: {scores['goal_pursuit']:.1f}")
        print(f"  - Overall: {res['overall']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
