#!/usr/bin/env python3
"""
Proposal Speed CLI - Generate Upwork proposals in <5 minutes

Usage:
    ./proposal_generator.py                      # Interactive mode
    ./proposal_generator.py --input job.txt      # Load from file
    ./proposal_generator.py --score-only         # Quick triage
    ./proposal_generator.py --template rag       # Override template

Features:
    - Auto-scores jobs with qualification framework
    - Auto-detects best template from keywords
    - Assembles draft with proof points
    - Copies to clipboard (macOS) and saves to proposals/
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


# Scoring thresholds
SCORING_THRESHOLDS = {
    'budget': {
        3: lambda b: b >= 80 or b >= 3000,  # $80+/hr or $3K+ project
        2: lambda b: b >= 60 or b >= 1500,  # $60-80/hr or $1.5K-$3K
        1: lambda b: b >= 40 or b >= 800,   # $40-60/hr or $800-$1.5K
        0: lambda b: True                    # <$40/hr or <$800
    }
}

# Template keyword mappings
TEMPLATE_KEYWORDS = {
    'rag': [
        'rag', 'document', 'search', 'embedding', 'vector', 'semantic search',
        'knowledge base', 'q&a', 'qa', 'retrieval', 'pdf', 'contract'
    ],
    'chatbot': [
        'chatbot', 'conversational', 'chat', 'support bot', 'assistant',
        'dialogue', 'conversation', 'customer support', 'voice', 'llm'
    ],
    'dashboard': [
        'dashboard', 'visualization', 'analytics', 'bi', 'reporting',
        'streamlit', 'plotly', 'chart', 'graph', 'metric', 'kpi'
    ],
    'api': [
        'api', 'rest', 'fastapi', 'endpoint', 'backend', 'integration',
        'webhook', 'microservice', 'service'
    ],
    'consulting': [
        'consulting', 'architecture', 'design', 'strategy', 'advisory',
        'review', 'audit', 'optimization', 'roadmap'
    ]
}

# Red flag patterns
RED_FLAGS = {
    'no_payment': r'(payment.*not.*verified|no payment method)',
    'low_spend': r'(\$0.*spent|total spent.*\$[0-9]{1,3}[^0-9])',
    'test_project': r'(test project|small test|trial)',
    'urgent': r'(need.*today|asap|this weekend|urgent)',
    'off_platform': r'(pay.*outside|off.*platform|direct.*payment)',
    'vague_ai': r'(train.*ai|ai expert|machine learning expert)(?!.*\b(python|tensorflow|pytorch|api)\b)',
    'high_proposals': r'(10\+.*proposals|15\+.*proposals|20\+.*proposals)'
}


def parse_budget(description: str) -> Tuple[float, str]:
    """Extract budget from job description. Returns (amount, type)."""
    # Look for hourly rates
    hourly_match = re.search(r'\$(\d+)(?:-\$?(\d+))?[/\s]*(?:hr|hour)', description, re.IGNORECASE)
    if hourly_match:
        low = float(hourly_match.group(1))
        high = float(hourly_match.group(2)) if hourly_match.group(2) else low
        return (low + high) / 2, 'hourly'

    # Look for fixed price
    fixed_match = re.search(r'\$(\d{1,3}(?:,\d{3})*|\d+)(?:\s*(?:fixed|budget|project))', description, re.IGNORECASE)
    if fixed_match:
        amount = float(fixed_match.group(1).replace(',', ''))
        return amount, 'fixed'

    # Look for any dollar amount
    dollar_match = re.search(r'\$(\d{1,3}(?:,\d{3})*|\d+)', description)
    if dollar_match:
        amount = float(dollar_match.group(1).replace(',', ''))
        return amount, 'unknown'

    return 0, 'unknown'


def score_budget(description: str) -> int:
    """Score budget alignment (0-3 points)."""
    amount, budget_type = parse_budget(description)

    for score in [3, 2, 1, 0]:
        if SCORING_THRESHOLDS['budget'][score](amount):
            return score

    return 0


def score_client_history(description: str) -> int:
    """Score client history (0-3 points)."""
    score = 0

    # Check for payment verification
    if re.search(r'payment.*verified', description, re.IGNORECASE):
        score += 1

    # Check spending history
    spend_match = re.search(r'\$(\d{1,3}(?:,\d{3})*|\d+)(?:k?).*spent', description, re.IGNORECASE)
    if spend_match:
        spent = float(spend_match.group(1).replace(',', ''))
        if 'k' in spend_match.group(0).lower():
            spent *= 1000

        if spent >= 10000:
            score += 2
        elif spent >= 3000:
            score += 1

    # Check rating
    rating_match = re.search(r'(4\.[5-9]|5\.0).*star', description, re.IGNORECASE)
    if rating_match:
        score = min(score + 1, 3)

    return min(score, 3)


def score_scope_clarity(description: str) -> int:
    """Score scope clarity (0-2 points)."""
    score = 0

    # Check for tech stack mentions
    tech_keywords = [
        'python', 'fastapi', 'django', 'flask', 'postgresql', 'redis',
        'openai', 'claude', 'llm', 'api', 'docker', 'aws'
    ]

    if any(kw in description.lower() for kw in tech_keywords):
        score += 1

    # Check for deliverable mentions
    deliverable_keywords = [
        'deliverable', 'api endpoint', 'dashboard', 'report', 'documentation',
        'deployment', 'test', 'performance'
    ]

    if any(kw in description.lower() for kw in deliverable_keywords):
        score += 1

    return min(score, 2)


def score_tech_fit(description: str) -> int:
    """Score tech fit (0-2 points)."""
    desc_lower = description.lower()

    # Perfect match keywords
    perfect_match = [
        'python', 'fastapi', 'rag', 'chatbot', 'llm', 'streamlit',
        'postgresql', 'redis', 'claude', 'openai'
    ]

    # Partial match keywords
    partial_match = [
        'node.js', 'typescript', 'django', 'flask', 'react'
    ]

    if any(kw in desc_lower for kw in perfect_match):
        return 2
    elif any(kw in desc_lower for kw in partial_match):
        return 1

    return 0


def count_red_flags(description: str) -> Tuple[int, List[str]]:
    """Count red flags. Returns (count, list of flags)."""
    flags = []

    for flag_name, pattern in RED_FLAGS.items():
        if re.search(pattern, description, re.IGNORECASE):
            flags.append(flag_name.replace('_', ' ').title())

    return len(flags), flags


def calculate_score(description: str) -> Dict:
    """Calculate total score and breakdown."""
    budget_score = score_budget(description)
    client_score = score_client_history(description)
    scope_score = score_scope_clarity(description)
    tech_score = score_tech_fit(description)
    red_flag_count, red_flags = count_red_flags(description)

    total = budget_score + client_score + scope_score + tech_score - red_flag_count

    # Determine priority
    if total >= 8:
        priority = 'P1'
        color = Colors.GREEN
    elif total >= 5:
        priority = 'P2'
        color = Colors.YELLOW
    else:
        priority = 'Skip'
        color = Colors.RED

    return {
        'budget': budget_score,
        'client': client_score,
        'scope': scope_score,
        'tech_fit': tech_score,
        'red_flags': red_flag_count,
        'red_flag_list': red_flags,
        'total': total,
        'priority': priority,
        'color': color
    }


def detect_template(description: str) -> str:
    """Auto-detect best template from keywords."""
    desc_lower = description.lower()

    # Count matches for each template
    scores = {}
    for template_name, keywords in TEMPLATE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        scores[template_name] = score

    # Return template with highest score, default to consulting
    if max(scores.values()) == 0:
        return 'consulting'

    return max(scores, key=scores.get)


def load_template(template_type: str) -> Optional[str]:
    """Load template content from file."""
    template_path = Path(__file__).parent.parent / 'content' / 'upwork-proposal-system' / f'TEMPLATE_{template_type}.md'

    if not template_path.exists():
        print(f"{Colors.RED}Error: Template not found: {template_path}{Colors.END}")
        return None

    return template_path.read_text()


def load_proof_points() -> str:
    """Load proof points library."""
    proof_points_path = Path(__file__).parent.parent / 'content' / 'upwork-proposal-system' / 'PROOF_POINTS.md'

    if not proof_points_path.exists():
        return ""

    return proof_points_path.read_text()


def generate_proposal(job_description: str, template_type: str, client_name: str = "[CLIENT NAME]") -> str:
    """Generate proposal draft."""
    template_content = load_template(template_type)
    if not template_content:
        return ""

    # Extract template section
    template_match = re.search(r'## Template\n\n(.+?)(?=\n##|$)', template_content, re.DOTALL)
    if not template_match:
        return ""

    proposal = template_match.group(1).strip()

    # Replace client name
    proposal = proposal.replace('[CLIENT NAME]', client_name)

    # Mark customization points
    proposal = re.sub(r'\[([^\]]+)\]', r'[CUSTOMIZE: \1]', proposal)

    return proposal


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard (macOS only)."""
    try:
        subprocess.run(['pbcopy'], input=text.encode(), check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def save_proposal(proposal: str, template_type: str) -> Path:
    """Save proposal to file."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f'draft-{template_type}-{timestamp}.md'

    proposals_dir = Path(__file__).parent.parent / 'proposals'
    proposals_dir.mkdir(exist_ok=True)

    filepath = proposals_dir / filename
    filepath.write_text(proposal)

    return filepath


def print_score_report(score: Dict, budget_info: Tuple[float, str]):
    """Print formatted score report."""
    print(f"\n{Colors.BOLD}=== JOB QUALIFICATION SCORE ==={Colors.END}\n")

    print(f"Budget Alignment:  {score['budget']}/3")
    amount, budget_type = budget_info
    if amount > 0:
        print(f"  ({budget_type}: ${amount:,.0f})")

    print(f"Client History:    {score['client']}/3")
    print(f"Scope Clarity:     {score['scope']}/2")
    print(f"Tech Fit:          {score['tech_fit']}/2")
    print(f"Red Flags:         -{score['red_flags']}")

    if score['red_flag_list']:
        print(f"  Flags: {', '.join(score['red_flag_list'])}")

    print(f"\n{Colors.BOLD}TOTAL: {score['total']}/10{Colors.END}")
    print(f"{Colors.BOLD}Priority: {score['color']}{score['priority']}{Colors.END}\n")

    # Action recommendation
    if score['priority'] == 'P1':
        print(f"{Colors.GREEN}✓ Bid within 2 hours. Research client, customize heavily.{Colors.END}")
    elif score['priority'] == 'P2':
        print(f"{Colors.YELLOW}→ Batch for later. Send within 24 hours with light customization.{Colors.END}")
    else:
        print(f"{Colors.RED}✗ Skip. Not worth the time investment.{Colors.END}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Upwork proposals in <5 minutes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./proposal_generator.py                    # Interactive mode
  ./proposal_generator.py --input job.txt    # Load from file
  ./proposal_generator.py --score-only       # Quick triage
  ./proposal_generator.py --template rag     # Override template
        """
    )

    parser.add_argument('--input', '-i', help='Load job description from file')
    parser.add_argument('--score-only', '-s', action='store_true', help='Score only, no proposal')
    parser.add_argument('--template', '-t', choices=['rag', 'chatbot', 'dashboard', 'api', 'consulting'],
                       help='Override template selection')
    parser.add_argument('--client-name', '-c', default='[CLIENT NAME]', help='Client name for proposal')

    args = parser.parse_args()

    # Load job description
    if args.input:
        try:
            job_description = Path(args.input).read_text()
        except FileNotFoundError:
            print(f"{Colors.RED}Error: File not found: {args.input}{Colors.END}")
            sys.exit(1)
    else:
        print(f"{Colors.BLUE}Paste job description (press Ctrl+D when done):{Colors.END}\n")
        job_description = sys.stdin.read()

    if not job_description.strip():
        print(f"{Colors.RED}Error: No job description provided{Colors.END}")
        sys.exit(1)

    # Calculate score
    score = calculate_score(job_description)
    budget_info = parse_budget(job_description)

    # Print score report
    print_score_report(score, budget_info)

    # Exit if score-only mode
    if args.score_only:
        sys.exit(0)

    # Skip proposal generation for low scores
    if score['priority'] == 'Skip':
        print(f"\n{Colors.YELLOW}Skipping proposal generation for low-priority job.{Colors.END}")
        print(f"Use --template flag to override if you still want to generate a proposal.")
        sys.exit(0)

    # Detect or use specified template
    template_type = args.template or detect_template(job_description)

    print(f"\n{Colors.BOLD}=== PROPOSAL GENERATION ==={Colors.END}\n")
    print(f"Template: {Colors.BLUE}{template_type}{Colors.END}")

    # Generate proposal
    proposal = generate_proposal(job_description, template_type, args.client_name)

    if not proposal:
        print(f"{Colors.RED}Error: Failed to generate proposal{Colors.END}")
        sys.exit(1)

    # Save to file
    filepath = save_proposal(proposal, template_type)
    print(f"Saved: {Colors.GREEN}{filepath}{Colors.END}")

    # Copy to clipboard
    if copy_to_clipboard(proposal):
        print(f"{Colors.GREEN}✓ Copied to clipboard{Colors.END}")
    else:
        print(f"{Colors.YELLOW}! Could not copy to clipboard (pbcopy not available){Colors.END}")

    print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
    print(f"1. Review [CUSTOMIZE] sections in proposal")
    print(f"2. Research client (LinkedIn, company site)")
    print(f"3. Add specific architecture/approach details")
    print(f"4. Submit within priority timeframe ({score['priority']})")

    print(f"\n{Colors.BLUE}Proposal preview:{Colors.END}\n")
    print("-" * 80)
    print(proposal[:500] + "..." if len(proposal) > 500 else proposal)
    print("-" * 80)


if __name__ == '__main__':
    main()
