
import asyncio
import sys
import os

# Ensure current directory is in PYTHONPATH
sys.path.append(os.getcwd())

from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/perplexity_search.py '<query>' [context]")
        sys.exit(1)
        
    query = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else None
    
    researcher = PerplexityResearcher()
    if not researcher.enabled:
        print("Error: PERPLEXITY_API_KEY not set.")
        sys.exit(1)
        
    print(f"Searching for: {query}...")
    result = await researcher.research_topic(query, context)
    print("\n--- RESULTS ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
