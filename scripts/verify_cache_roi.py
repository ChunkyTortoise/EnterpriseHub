"""
Diagnostic Script: Verify Cache ROI.
Executes high-context queries to verify Anthropic Prompt Caching performance.
Reference: GEMINI_WORKFLOW_OPTIMIZATION.md
"""
import asyncio
import os
import pandas as pd
from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.core.gemini_logger import get_metrics_summary

async def verify_cache_roi():
    print("🚀 Initializing Cache Burn-in Test...")
    client = LLMClient(provider="claude", model="claude-3-5-sonnet-20241022")
    
    # High-context system prompt (> 2000 chars to ensure caching trigger) 
    system_prompt = "You are an elite Real Estate AI specialized in the Austin, Texas market. " * 50
    system_prompt += "\nYour knowledge includes deep zoning laws, neighborhood psychographics, and 2026 investment trends."
    
    print(f"System Prompt Length: {len(system_prompt)} characters.")
    
    queries = [
        "What is the investment outlook for South Lamar in 2026?",
        "How do zoning changes in East Austin affect multi-family development?",
        "Compare Teravista and Steiner Ranch for tech families.",
        "What are the top 3 luxury zip codes in Austin right now?",
        "Analyze the impact of the new tech corridor on Manor property values.",
        "Is Del Valle a good spot for short-term rentals in 2026?",
        "Explain the tax benefits of 1031 exchanges for Austin properties.",
        "What is the average price per square foot in Tarrytown?",
        "How has the recent interest rate shift affected Austin buyer sentiment?",
        "Give me a closing pitch for a high-intent buyer in West Lake Hills."
    ]
    
    results = []
    
    print("\n--- Starting Query Sequence ---")
    for i, query in enumerate(queries):
        print(f"Executing Query {i+1}/10...")
        response = await client.agenerate(
            prompt=query,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        results.append({
            "query": query,
            "tokens": response.input_tokens,
            "cache_read": getattr(response, 'cache_read_input_tokens', 0),
            "cost": response.tokens_used # This is just token count, logger handles USD
        })
        
        # Small delay to ensure logging completes
        await asyncio.sleep(0.5) 
        
    print("\n--- Test Complete ---")
    
    # Verify CSV recording
    if os.path.exists("gemini_metrics.csv"):
        df = pd.read_csv("gemini_metrics.csv").tail(10)
        print("\nRecent Metrics from gemini_metrics.csv:")
        print(df[["timestamp", "input_tokens", "cache_read_input_tokens", "cost_usd"]])
        
        first_cost = df.iloc[0]["cost_usd"]
        last_cost = df.iloc[-1]["cost_usd"]
        
        if last_cost < first_cost:
            savings = (1 - (last_cost / first_cost)) * 100
            print(f"\n✅ CACHE SUCCESS: Cost dropped from ${first_cost:.4f} to ${last_cost:.4f} ({savings:.1f}% savings)")
        else:
            print("\n⚠️ CACHE WARNING: No significant cost drop detected. Check Anthropic beta headers and prompt length.")
    else:
        print("\n❌ ERROR: gemini_metrics.csv not found.")

if __name__ == "__main__":
    asyncio.run(verify_cache_roi())
