
import asyncio
import sys
import os
import json
import argparse

# Ensure current directory is in PYTHONPATH
sys.path.append(os.getcwd())

from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

async def run_search(query):
    """Simple web search via Perplexity."""
    researcher = PerplexityResearcher()
    print(f"🔍 Searching Perplexity for: {query}...")
    result = await researcher.research_topic(query)
    print("\n--- SEARCH RESULTS ---")
    print(result)

async def run_research(topic, context=None):
    """Deep research synthesized by Claude."""
    orchestrator = get_claude_orchestrator()
    print(f"🧠 Performing Deep Hybrid Research (Perplexity + Claude) on: {topic}...")
    response = await orchestrator.perform_research(topic, {"context": context} if context else None)
    print("\n--- STRATEGIC RESEARCH REPORT ---")
    print(response.content)

async def run_compare(items, category="properties"):
    """Compare multiple items using Perplexity and Claude."""
    orchestrator = get_claude_orchestrator()
    items_str = ", ".join(items)
    print(f"⚖️ Comparing {category}: {items_str}...")
    
    prompt = f"Perform a detailed side-by-side comparison of the following {category}: {items_str}."
    if category == "properties":
        prompt += " Focus on market value, neighborhood appreciation, school ratings, and investment potential."
    elif category == "markets":
        prompt += " Focus on inventory levels, median price trends, economic drivers, and rental yields."
        
    response = await orchestrator.perform_research(prompt)
    print(f"\n--- {category.upper()} COMPARISON ---")
    print(response.content)

def main():
    parser = argparse.ArgumentParser(description="EnterpriseHub Research & Intelligence Tools")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Simple web search")
    search_parser.add_argument("query", help="The search query")

    # Research command
    research_parser = subparsers.add_parser("research", help="Deep hybrid research")
    research_parser.add_argument("topic", help="The research topic")
    research_parser.add_argument("--context", help="Optional context")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Side-by-side comparison")
    compare_parser.add_argument("items", nargs="+", help="Items to compare")
    compare_parser.add_argument("--category", default="properties", help="Category of items (properties, markets, etc.)")

    args = parser.parse_args()

    if args.command == "search":
        asyncio.run(run_search(args.query))
    elif args.command == "research":
        asyncio.run(run_research(args.topic, args.context))
    elif args.command == "compare":
        asyncio.run(run_compare(args.items, args.category))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
