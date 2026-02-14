#!/usr/bin/env python3
"""
Rate Intelligence Script - Analyze market rates for AI/ML freelancers

Usage:
    ./rate_intelligence.py                    # Generate full report
    ./rate_intelligence.py --json             # JSON output
    ./rate_intelligence.py --rate 85          # Check specific rate
    ./rate_intelligence.py --no-scrape        # Use fallback data only

Features:
    - Scrapes Bonsai Rate Explorer for AI/ML/Python rates
    - Calculates percentile positioning for target rates
    - Generates market rate report with recommendations
    - Saves to reports/rate-intelligence-{date}.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


# Fallback market data from research (Feb 2026)
MARKET_DATA_FALLBACK = {
    'AI/ML Junior': {'low': 40, 'mid': 52, 'high': 65},
    'AI/ML Mid-Level': {'low': 65, 'mid': 82, 'high': 100},
    'AI/ML Senior': {'low': 100, 'mid': 125, 'high': 150},
    'AI/ML Expert': {'low': 150, 'mid': 200, 'high': 250},
    'Python Developer': {'low': 50, 'mid': 75, 'high': 100},
    'RAG Specialist': {'low': 100, 'mid': 137, 'high': 175},
    'Multi-Agent Systems': {'low': 125, 'mid': 162, 'high': 200},
    'FastAPI Developer': {'low': 75, 'mid': 100, 'high': 125},
    'Chatbot Developer': {'low': 80, 'mid': 110, 'high': 140},
    'Dashboard Developer': {'low': 60, 'mid': 85, 'high': 110}
}


class BonsaiRateParser(HTMLParser):
    """Parse Bonsai Rate Explorer HTML."""

    def __init__(self):
        super().__init__()
        self.rates = {}
        self.current_role = None
        self.in_rate_section = False

    def handle_starttag(self, tag, attrs):
        # Implement basic parsing logic
        # Note: This is a placeholder - actual implementation would need
        # to inspect Bonsai's HTML structure
        pass

    def handle_data(self, data):
        # Extract rate data from text content
        pass


def scrape_bonsai_rates() -> Optional[Dict]:
    """
    Attempt to scrape Bonsai Rate Explorer.

    Note: This is a best-effort scraping attempt. Bonsai may block scrapers
    or change their HTML structure. Fallback data will be used if scraping fails.
    """
    url = 'https://www.hellobonsai.com/rates/ai-machine-learning'

    try:
        # Add user-agent to avoid basic bot detection
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        with urlopen(req, timeout=10) as response:
            if response.status != 200:
                return None

            html = response.read().decode('utf-8')

            # Simple regex-based extraction as HTMLParser may be too brittle
            # Look for common patterns like "$XX - $YY / hour"
            import re

            rates = {}

            # Pattern: "Role: $XX - $YY/hour" or similar
            # This is a simplified example - actual patterns depend on Bonsai's HTML
            rate_patterns = [
                r'(\w+[\w\s]+?):\s*\$(\d+)\s*-\s*\$(\d+)',
                r'<span[^>]*>(\w+[\w\s]+?)</span>.*?\$(\d+).*?\$(\d+)',
            ]

            for pattern in rate_patterns:
                matches = re.finditer(pattern, html, re.IGNORECASE)
                for match in matches:
                    role = match.group(1).strip()
                    low = int(match.group(2))
                    high = int(match.group(3))
                    mid = (low + high) / 2

                    rates[role] = {'low': low, 'mid': mid, 'high': high}

            return rates if rates else None

    except (URLError, HTTPError, TimeoutError) as e:
        print(f"{Colors.YELLOW}Scraping failed: {e}{Colors.END}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"{Colors.YELLOW}Unexpected error during scraping: {e}{Colors.END}", file=sys.stderr)
        return None


def calculate_percentile(rate: float, market_data: Dict) -> Dict[str, float]:
    """
    Calculate percentile positioning for given rate across all roles.

    Returns dict with percentile for each role category.
    """
    percentiles = {}

    for role, rates in market_data.items():
        low = rates['low']
        high = rates['high']

        if rate < low:
            percentile = 0
        elif rate > high:
            percentile = 100
        else:
            # Linear interpolation
            percentile = ((rate - low) / (high - low)) * 100

        percentiles[role] = round(percentile, 1)

    return percentiles


def categorize_rate(rate: float, market_data: Dict) -> str:
    """Determine experience level category for given rate."""
    # Check which level the rate falls into most commonly
    matches = []

    for role, rates in market_data.items():
        if rates['low'] <= rate <= rates['high']:
            if 'Junior' in role:
                matches.append('Junior')
            elif 'Mid' in role:
                matches.append('Mid-Level')
            elif 'Senior' in role:
                matches.append('Senior')
            elif 'Expert' in role:
                matches.append('Expert')
            else:
                matches.append('Mid-Level')  # Default

    if not matches:
        # Rate doesn't fit standard ranges
        if rate < 50:
            return 'Below Junior'
        elif rate > 200:
            return 'Above Expert'
        else:
            return 'Mid-Level'

    # Return most common match
    return max(set(matches), key=matches.count)


def generate_recommendations(rate: float, percentiles: Dict, market_data: Dict) -> List[str]:
    """Generate rate recommendations based on positioning."""
    recommendations = []

    avg_percentile = sum(percentiles.values()) / len(percentiles)

    if avg_percentile < 30:
        recommendations.append(f"{Colors.RED}Your rate (${rate}/hr) is below the 30th percentile for AI/ML work.{Colors.END}")
        recommendations.append("Consider raising your rate to $85-100/hr to match mid-level market rates.")
        recommendations.append("Focus on P1 jobs ($80+/hr) to build higher-paying portfolio.")

    elif avg_percentile < 50:
        recommendations.append(f"{Colors.YELLOW}Your rate (${rate}/hr) is competitive but below median for specialized work.{Colors.END}")
        recommendations.append("You're positioned well for mid-level roles.")
        recommendations.append("Emphasize specialized skills (RAG, multi-agent) to justify $100+/hr rates.")

    elif avg_percentile < 75:
        recommendations.append(f"{Colors.GREEN}Your rate (${rate}/hr) is above median for most AI/ML work.{Colors.END}")
        recommendations.append("You're competitive for senior-level projects.")
        recommendations.append("Target enterprise clients and complex projects ($100-150/hr).")

    else:
        recommendations.append(f"{Colors.GREEN}Your rate (${rate}/hr) is in the top quartile for AI/ML freelancers.{Colors.END}")
        recommendations.append("Position yourself as an expert/specialist.")
        recommendations.append("Focus on high-value projects: architecture, optimization, compliance.")

    # Specialty positioning
    if 'RAG Specialist' in market_data:
        rag_rates = market_data['RAG Specialist']
        if rag_rates['low'] <= rate <= rag_rates['high']:
            recommendations.append(f"\n{Colors.BLUE}RAG Positioning:{Colors.END} Your rate aligns with RAG specialist market.")
            recommendations.append("Emphasize RAG portfolio (docqa-engine, EnterpriseHub) in proposals.")

    if 'Multi-Agent Systems' in market_data:
        agent_rates = market_data['Multi-Agent Systems']
        if agent_rates['low'] <= rate <= agent_rates['high']:
            recommendations.append(f"\n{Colors.BLUE}Multi-Agent Positioning:{Colors.END} Your rate aligns with multi-agent specialists.")
            recommendations.append("Highlight jorge_real_estate_bots and ai-orchestrator in proposals.")

    return recommendations


def format_markdown_report(rate: float, percentiles: Dict, market_data: Dict,
                          recommendations: List[str], data_source: str) -> str:
    """Generate markdown report."""
    timestamp = datetime.now().strftime('%Y-%m-%d')

    report = f"""# Rate Intelligence Report

**Generated**: {timestamp}
**Target Rate**: ${rate}/hr
**Data Source**: {data_source}

---

## Market Rate Benchmarks

| Role Category | Low | Mid | High | Your Position |
|---------------|-----|-----|------|---------------|
"""

    for role, rates in sorted(market_data.items()):
        percentile = percentiles.get(role, 0)
        position = f"{percentile}th percentile"

        if percentile < 30:
            indicator = "🔴 Below market"
        elif percentile < 50:
            indicator = "🟡 Competitive"
        elif percentile < 75:
            indicator = "🟢 Strong"
        else:
            indicator = "🔵 Expert tier"

        report += f"| {role} | ${rates['low']}/hr | ${rates['mid']:.0f}/hr | ${rates['high']}/hr | {position} {indicator} |\n"

    # Average positioning
    avg_percentile = sum(percentiles.values()) / len(percentiles)
    category = categorize_rate(rate, market_data)

    report += f"\n---\n\n## Overall Positioning\n\n"
    report += f"**Average Percentile**: {avg_percentile:.1f}th  \n"
    report += f"**Experience Level**: {category}  \n\n"

    # Recommendations
    report += "---\n\n## Recommendations\n\n"

    for rec in recommendations:
        # Strip color codes for markdown
        clean_rec = rec.replace(Colors.GREEN, '').replace(Colors.YELLOW, '').replace(Colors.RED, '')
        clean_rec = clean_rec.replace(Colors.BLUE, '').replace(Colors.CYAN, '').replace(Colors.END, '')
        report += f"{clean_rec}\n\n"

    # Rate strategy
    report += "---\n\n## Rate Strategy\n\n"

    if avg_percentile < 50:
        report += f"""
### Target Rates by Job Type

| Job Type | Suggested Rate | Rationale |
|----------|---------------|-----------|
| RAG Systems | $85-95/hr | Match mid-level RAG specialist market |
| Chatbots | $80-90/hr | Competitive for multi-agent work |
| Dashboards | $75-85/hr | Standard BI development rates |
| API Development | $80-90/hr | FastAPI + async expertise |
| Consulting | $100-125/hr | Architecture/strategy premium |

### Growth Path

1. **Short-term (3 months)**: Build portfolio at $85/hr, focus on P1 jobs
2. **Mid-term (6 months)**: Raise to $95-100/hr as case studies accumulate
3. **Long-term (12 months)**: Target $110-125/hr for specialized work (RAG, multi-agent)
"""
    else:
        report += f"""
### Maintain Premium Positioning

- **Current rate (${rate}/hr)** is competitive for senior/expert work
- Focus on high-value projects: enterprise, compliance, optimization
- Justify rate with portfolio metrics (8,500+ tests, 89% cost reduction, 4.3M dispatches/sec)

### Upsell Opportunities

- **Architecture consulting**: $125-150/hr for design/review work
- **Performance optimization**: $100-125/hr + success bonuses
- **Enterprise projects**: $100-150/hr for compliance-heavy work
"""

    report += "\n---\n\n"
    report += f"**Next Update**: {datetime.now().strftime('%Y-%m-%d')} + 30 days  \n"
    report += f"**Sources**: Bonsai Rate Explorer, Upwork market research, portfolio analysis\n"

    return report


def main():
    parser = argparse.ArgumentParser(
        description='Analyze market rates for AI/ML freelancers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./rate_intelligence.py                  # Generate full report
  ./rate_intelligence.py --json           # JSON output
  ./rate_intelligence.py --rate 85        # Check specific rate
  ./rate_intelligence.py --no-scrape      # Use fallback data only
        """
    )

    parser.add_argument('--rate', '-r', type=float, default=85,
                       help='Target hourly rate to analyze (default: $85/hr)')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON instead of markdown')
    parser.add_argument('--no-scrape', action='store_true',
                       help='Skip scraping, use fallback data only')
    parser.add_argument('--output', '-o',
                       help='Output file path (default: reports/rate-intelligence-{date}.md)')

    args = parser.parse_args()

    # Suppress header in JSON mode
    if not args.json:
        print(f"{Colors.BOLD}=== RATE INTELLIGENCE ANALYSIS ==={Colors.END}\n")
        print(f"Target Rate: {Colors.CYAN}${args.rate}/hr{Colors.END}\n")

    # Attempt to scrape or use fallback
    market_data = None

    if not args.no_scrape:
        if not args.json:
            print(f"{Colors.BLUE}Attempting to scrape Bonsai Rate Explorer...{Colors.END}")
        market_data = scrape_bonsai_rates()

    if market_data:
        if not args.json:
            print(f"{Colors.GREEN}✓ Scraped live market data{Colors.END}\n")
        data_source = "Bonsai Rate Explorer (scraped)"
    else:
        if not args.json:
            print(f"{Colors.YELLOW}Using fallback market data from research{Colors.END}\n")
        market_data = MARKET_DATA_FALLBACK
        data_source = "Research data (Feb 2026)"

    # Calculate percentiles
    percentiles = calculate_percentile(args.rate, market_data)

    # Generate recommendations
    recommendations = generate_recommendations(args.rate, percentiles, market_data)

    # Output results
    if args.json:
        # JSON output
        output = {
            'rate': args.rate,
            'data_source': data_source,
            'market_data': market_data,
            'percentiles': percentiles,
            'average_percentile': round(sum(percentiles.values()) / len(percentiles), 1),
            'category': categorize_rate(args.rate, market_data),
            'recommendations': [r.replace(Colors.GREEN, '').replace(Colors.YELLOW, '').replace(Colors.RED, '').replace(Colors.BLUE, '').replace(Colors.CYAN, '').replace(Colors.END, '') for r in recommendations]
        }

        print(json.dumps(output, indent=2))

    else:
        # Terminal output with colors
        print(f"{Colors.BOLD}Market Positioning:{Colors.END}\n")

        for role, percentile in sorted(percentiles.items(), key=lambda x: x[1], reverse=True):
            rates = market_data[role]

            if percentile < 30:
                color = Colors.RED
                indicator = "🔴"
            elif percentile < 50:
                color = Colors.YELLOW
                indicator = "🟡"
            elif percentile < 75:
                color = Colors.GREEN
                indicator = "🟢"
            else:
                color = Colors.CYAN
                indicator = "🔵"

            print(f"{indicator} {color}{role:30s}{Colors.END} "
                  f"${rates['low']:3.0f}-${rates['high']:3.0f}/hr → {percentile:5.1f}th percentile")

        avg_percentile = sum(percentiles.values()) / len(percentiles)
        category = categorize_rate(args.rate, market_data)

        print(f"\n{Colors.BOLD}Overall:{Colors.END} {avg_percentile:.1f}th percentile ({category})\n")

        print(f"{Colors.BOLD}Recommendations:{Colors.END}\n")
        for rec in recommendations:
            print(f"  {rec}")

        # Generate markdown report
        report = format_markdown_report(args.rate, percentiles, market_data,
                                       recommendations, data_source)

        # Save report
        if args.output:
            output_path = Path(args.output)
        else:
            reports_dir = Path(__file__).parent.parent / 'reports'
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d')
            output_path = reports_dir / f'rate-intelligence-{timestamp}.md'

        output_path.write_text(report)

        print(f"\n{Colors.GREEN}✓ Report saved: {output_path}{Colors.END}")

        # Print preview
        print(f"\n{Colors.BLUE}Report preview:{Colors.END}\n")
        print("-" * 80)
        print(report[:600] + "..." if len(report) > 600 else report)
        print("-" * 80)


if __name__ == '__main__':
    main()
