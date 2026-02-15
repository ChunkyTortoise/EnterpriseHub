#!/usr/bin/env python3
"""
Upwork AI Job Scorer & Proposal Drafter

Uses Claude Haiku to evaluate job fit and auto-draft proposals for P1 matches.
Designed to run as a post-processing step after upwork_job_monitor.py finds new jobs.

Usage:
    # Score a single job from JSON
    ./upwork_ai_scorer.py --job job.json

    # Score all P1/P2 jobs from the monitor's latest output
    ./upwork_ai_scorer.py --from-log jobs/new-jobs.md

    # Score from stdin (pipe from monitor)
    echo '{"title": "...", "description": "..."}' | ./upwork_ai_scorer.py

    # Score and draft proposal for P1
    ./upwork_ai_scorer.py --job job.json --draft

Env vars:
    ANTHROPIC_API_KEY — Required for Claude API calls
    UPWORK_SLACK_WEBHOOK_URL — Optional, sends Slack alert with proposal preview

Cost: ~$0.01-0.03 per job scored (Haiku)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS_SCORE = 1024
MAX_TOKENS_DRAFT = 2048

TARGET_RATE = "$65-75/hr"
TECH_STACK = [
    "Python", "FastAPI", "RAG", "Claude API", "multi-agent systems",
    "Streamlit", "PostgreSQL", "Redis", "LangChain", "vector databases",
    "async/await", "Docker", "Celery", "Pydantic",
]

PORTFOLIO_PROOF_POINTS = """
- EnterpriseHub: Real estate AI platform with 8,500+ tests, 89% cost reduction, $50M+ pipeline managed
- Jorge Bots: 3 AI chatbots (lead/buyer/seller) with handoff orchestration, 157 passing tests
- RAG Pipeline: 4.3M dispatches/sec, L1/L2/L3 caching, <200ms overhead
- AgentForge: Multi-agent orchestration framework
- DocQA Engine: Production RAG system for document Q&A
- Data Dashboard: Streamlit BI with Monte Carlo simulations, sentiment analysis
"""

PROPOSALS_DIR = Path(__file__).parent.parent / "content" / "upwork" / "proposals"
PROOF_POINTS_FILE = Path(__file__).parent.parent / "content" / "upwork-proposal-system" / "PROOF_POINTS.md"

# ---------------------------------------------------------------------------
# AI Scoring
# ---------------------------------------------------------------------------

SCORING_PROMPT = """You are an expert freelance consultant evaluating Upwork job postings for an AI/ML engineer.

**Freelancer Profile:**
- Specialties: {tech_stack}
- Target rate: {target_rate}
- Portfolio highlights: {proof_points}

**Evaluate this job posting and return a JSON response:**

Job Title: {title}
Job Description: {description}
Extracted Budget: {budget}

**Score each dimension (0-10) and provide reasoning:**

1. **budget_alignment**: How well does the budget match {target_rate}? (0=way below, 10=premium match)
2. **tech_match**: How many of the freelancer's core skills are needed? (0=none, 10=perfect fit)
3. **client_quality**: Based on available signals (spend, verification, rating). Default 5 if unknown.
4. **portfolio_showcase**: Can the freelancer demo existing work (EnterpriseHub, bots, RAG)? (0=no overlap, 10=perfect showcase)
5. **scope_clarity**: Are deliverables clear and well-defined? (0=vague, 10=crystal clear)

Return ONLY valid JSON:
{{
    "scores": {{
        "budget_alignment": <0-10>,
        "tech_match": <0-10>,
        "client_quality": <0-10>,
        "portfolio_showcase": <0-10>,
        "scope_clarity": <0-10>
    }},
    "overall_score": <weighted average, 0-10>,
    "priority": "P1" | "P2" | "Skip",
    "reasoning": "<2-3 sentence explanation>",
    "key_selling_points": ["<point1>", "<point2>", "<point3>"],
    "risks": ["<risk1>", "<risk2>"]
}}
"""

PROPOSAL_PROMPT = """You are writing a winning Upwork proposal for an AI/ML engineer.

**Freelancer Profile:**
- Rate: {target_rate}
- Key proof points: {proof_points}
- Scoring analysis: {scoring_analysis}

**Job Details:**
- Title: {title}
- Description: {description}
- Key selling points identified: {selling_points}

**Write a 3-paragraph proposal (150-250 words total):**

Paragraph 1: Acknowledge the client's specific need. Show you read the posting carefully. Reference their domain/problem.

Paragraph 2: Provide ONE concrete proof point from the portfolio that directly maps to their need. Include a specific metric (e.g., "89% cost reduction", "8,500+ tests", "4.3M dispatches/sec").

Paragraph 3: Propose a clear next step (15-min call, quick architecture sketch, or POC outline). Be specific about what you'd discuss.

**Rules:**
- NO generic filler ("I'm excited about this opportunity")
- NO listing every skill you have
- Start with their problem, not your resume
- Keep it under 250 words
- Sound like a human, not a template
"""


def score_job_with_ai(
    title: str,
    description: str,
    budget: str = "Not specified",
) -> Optional[Dict]:
    """Score a job using Claude Haiku. Returns scoring dict or None on failure."""
    client = anthropic.Anthropic()

    proof_points = PORTFOLIO_PROOF_POINTS
    if PROOF_POINTS_FILE.exists():
        proof_points = PROOF_POINTS_FILE.read_text()[:2000]

    prompt = SCORING_PROMPT.format(
        tech_stack=", ".join(TECH_STACK),
        target_rate=TARGET_RATE,
        proof_points=proof_points,
        title=title,
        description=description[:3000],  # cap to control cost
        budget=budget,
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS_SCORE,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)

        # Add metadata
        result["model"] = MODEL
        result["input_tokens"] = response.usage.input_tokens
        result["output_tokens"] = response.usage.output_tokens
        cost = (response.usage.input_tokens * 0.80 + response.usage.output_tokens * 4.0) / 1_000_000
        result["estimated_cost"] = f"${cost:.4f}"

        return result

    except json.JSONDecodeError as e:
        print(f"Failed to parse AI response as JSON: {e}")
        print(f"Raw response: {text[:500]}")
        return None
    except anthropic.APIError as e:
        print(f"Claude API error: {e}")
        return None


def draft_proposal(
    title: str,
    description: str,
    scoring_result: Dict,
) -> Optional[str]:
    """Generate a proposal draft for P1 jobs using Claude Haiku."""
    client = anthropic.Anthropic()

    proof_points = PORTFOLIO_PROOF_POINTS
    if PROOF_POINTS_FILE.exists():
        proof_points = PROOF_POINTS_FILE.read_text()[:2000]

    prompt = PROPOSAL_PROMPT.format(
        target_rate=TARGET_RATE,
        proof_points=proof_points,
        scoring_analysis=scoring_result.get("reasoning", ""),
        title=title,
        description=description[:3000],
        selling_points=", ".join(scoring_result.get("key_selling_points", [])),
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS_DRAFT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except anthropic.APIError as e:
        print(f"Claude API error during proposal drafting: {e}")
        return None


def save_proposal(title: str, proposal: str, scoring: Dict) -> Path:
    """Save proposal draft to content/upwork/proposals/."""
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in title)[:50].strip()
    filename = f"ai-draft-{safe_title}-{timestamp}.md"

    content = f"""# Proposal Draft: {title}

**Generated**: {datetime.now().isoformat()}
**AI Score**: {scoring.get('overall_score', 'N/A')}/10 ({scoring.get('priority', 'N/A')})
**Cost**: {scoring.get('estimated_cost', 'N/A')}

## Scores
| Dimension | Score |
|-----------|-------|
| Budget Alignment | {scoring.get('scores', {}).get('budget_alignment', 'N/A')}/10 |
| Tech Match | {scoring.get('scores', {}).get('tech_match', 'N/A')}/10 |
| Client Quality | {scoring.get('scores', {}).get('client_quality', 'N/A')}/10 |
| Portfolio Showcase | {scoring.get('scores', {}).get('portfolio_showcase', 'N/A')}/10 |
| Scope Clarity | {scoring.get('scores', {}).get('scope_clarity', 'N/A')}/10 |

## Reasoning
{scoring.get('reasoning', 'N/A')}

## Key Selling Points
{chr(10).join('- ' + p for p in scoring.get('key_selling_points', []))}

## Risks
{chr(10).join('- ' + r for r in scoring.get('risks', []))}

---

## Proposal Draft

{proposal}

---

*Copy the proposal above. Review [CUSTOMIZE] sections before sending.*
"""

    filepath = PROPOSALS_DIR / filename
    filepath.write_text(content)
    return filepath


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI-powered Upwork job scoring and proposal drafting")
    parser.add_argument("--job", help="Path to job JSON file")
    parser.add_argument("--title", help="Job title (with --description)")
    parser.add_argument("--description", help="Job description text")
    parser.add_argument("--budget", default="Not specified", help="Extracted budget string")
    parser.add_argument("--draft", action="store_true", help="Also generate proposal draft for P1 jobs")
    parser.add_argument("--json-output", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    # Load job data
    if args.job:
        with open(args.job) as f:
            job = json.load(f)
        title = job.get("title", "")
        description = job.get("description", "")
        budget = job.get("budget", args.budget)
    elif args.title and args.description:
        title = args.title
        description = args.description
        budget = args.budget
    elif not sys.stdin.isatty():
        job = json.load(sys.stdin)
        title = job.get("title", "")
        description = job.get("description", "")
        budget = job.get("budget", args.budget)
    else:
        parser.print_help()
        sys.exit(1)

    if not title or not description:
        print("ERROR: title and description are required")
        sys.exit(1)

    # Score
    print(f"Scoring: {title[:80]}...")
    scoring = score_job_with_ai(title, description, budget)

    if not scoring:
        print("ERROR: AI scoring failed")
        sys.exit(1)

    if args.json_output:
        print(json.dumps(scoring, indent=2))
    else:
        print(f"\nAI Score: {scoring.get('overall_score', '?')}/10 ({scoring.get('priority', '?')})")
        print(f"Reasoning: {scoring.get('reasoning', 'N/A')}")
        scores = scoring.get("scores", {})
        for dim, val in scores.items():
            print(f"  {dim}: {val}/10")
        print(f"Cost: {scoring.get('estimated_cost', '?')}")

    # Draft proposal if P1 and --draft
    if args.draft and scoring.get("priority") == "P1":
        print("\nDrafting proposal...")
        proposal = draft_proposal(title, description, scoring)
        if proposal:
            filepath = save_proposal(title, proposal, scoring)
            print(f"Proposal saved: {filepath}")
            print(f"\n--- PROPOSAL PREVIEW ---\n{proposal[:500]}...")
        else:
            print("ERROR: Proposal drafting failed")
    elif args.draft and scoring.get("priority") != "P1":
        print(f"\nSkipping proposal draft (priority: {scoring.get('priority')}, need P1)")


if __name__ == "__main__":
    main()
