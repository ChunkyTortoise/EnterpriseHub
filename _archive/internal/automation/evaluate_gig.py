#!/usr/bin/env python3
"""
Upwork Gig Evaluator

This script takes a job description as input and uses Claude to evaluate it
against your specific profile, skills, and portfolio.

Usage:
    python automation/evaluate_gig.py
"""

import os
import sys
import time
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from anthropic import Anthropic, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  'anthropic' library not found. Please run: pip install anthropic")

def get_api_key() -> Optional[str]:
    """Get Anthropic API key from environment."""
    # Try environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Try loading from .env if not found
    if not api_key:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.strip().split("=", 1)[1].strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
            
    return api_key

def load_profile() -> str:
    """Load the user's Upwork profile."""
    profile_path = "portfolio/UPWORK_PROFILE.md"
    try:
        with open(profile_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find profile at {profile_path}")
        sys.exit(1)

def evaluate_gig(client: Anthropic, profile_content: str, job_description: str) -> None:
    """Evaluate the gig using Claude."""
    
    system_prompt = """
    You are an expert Upwork Job Evaluator and Business Manager for a freelancer.
    
    Your goal is to maximize the freelancer's earnings (ROI) while minimizing time wasted on bad leads.
    The freelancer has LIMITED Connects and DESPERATELY needs money immediately.
    
    You will be given:
    1. The Freelancer's Profile (Skills, Portfolio, Rate, Focus)
    2. A Job Description
    
    You must output a structured evaluation in the following format:
    
    # 🎯 MATCH SCORE: [0-100] / 100
    
    ## 🚦 RECOMMENDATION: [APPLY NOW / MAYBE / AVOID]
    
    ## 🚩 ANALYSIS
    - **Pros:** [Key reasons it fits]
    - **Cons:** [Red flags, low budget, bad fit]
    - **Competition:** [Estimate likely competition level: Low/Medium/High]
    
    ## 💰 BID STRATEGY
    - **Proposed Bid:** $[Amount] (Fixed) or $[Rate]/hr
    - **Why:** [Reasoning for this price]
    
    ## 📝 PROPOSAL HOOK (First 2 lines)
    [Draft the first 2 sentences of the proposal. Make it punchy, directly addressing their problem, and referencing a specific relevant portfolio piece.]
    
    ## 📋 KEY TALKING POINTS
    - [Point 1 to mention]
    - [Point 2 to mention]
    - [Point 3 to mention]
    """
    
    user_message = f"""
    --- FREELANCER PROFILE ---
    {profile_content}
    
    --- JOB DESCRIPTION ---
    {job_description}
    
    Evaluate this gig now. Be critical. If it's a low-budget waste of time, say AVOID.
    """
    
    print("\n🧠 Analyzing gig with Claude 3.5 Sonnet...\n")
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        print(response.content[0].text)
        
    except APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if not ANTHROPIC_AVAILABLE:
        return

    api_key = get_api_key()
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment or .env file.")
        print("Please export it: export ANTHROPIC_API_KEY='sk-ant-...' ")
        return

    print("\n--------------------------------------------------")
    print("       UPWORK GIG EVALUATOR (AI-POWERED)       ")
    print("--------------------------------------------------")
    
    profile_content = load_profile()
    print("✅ Profile loaded successfully.")
    
    client = Anthropic(api_key=api_key)
    
    print("\n📋 PASTE THE JOB DESCRIPTION BELOW (Press Ctrl+D on empty line to finish):")
    print("--------------------------------------------------")
    
    # Read multi-line input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
        
    job_description = "\n".join(lines)
    
    if not job_description.strip():
        print("❌ Error: No job description provided.")
        return

    evaluate_gig(client, profile_content, job_description)

if __name__ == "__main__":
    main()
