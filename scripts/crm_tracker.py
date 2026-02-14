#!/usr/bin/env python3
"""
Freelance CRM Pipeline Tracker

Lightweight CLI for tracking freelance prospects and pipeline.
Uses JSON storage and colorized terminal output.

Setup:
    1. Make executable: chmod +x scripts/crm_tracker.py
    2. Run: ./scripts/crm_tracker.py --help

Commands:
    add         Add new prospect
    update      Update prospect status
    pipeline    Show funnel view
    stats       Show conversion metrics
    list        List all prospects with filtering
    export      Export to CSV

Examples:
    # Add prospect
    ./scripts/crm_tracker.py add "Acme Corp" --source=upwork --rate=150 --contact="John Doe"

    # Update status
    ./scripts/crm_tracker.py update "Acme Corp" --status=proposal_sent

    # View pipeline
    ./scripts/crm_tracker.py pipeline

    # Show stats
    ./scripts/crm_tracker.py stats

    # List prospects by status
    ./scripts/crm_tracker.py list --status=negotiation

    # Export to CSV
    ./scripts/crm_tracker.py export --output=pipeline.csv

Storage:
    ~/.freelance_crm.json

Author: EnterpriseHub Freelance Acceleration Plan
Date: 2026-02-14
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ANSI Color Codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Configuration
STORAGE_FILE = Path.home() / ".freelance_crm.json"

VALID_STATUSES = [
    'lead',
    'contacted',
    'proposal_sent',
    'negotiation',
    'won',
    'lost',
    'inactive'
]

STATUS_COLORS = {
    'lead': Colors.CYAN,
    'contacted': Colors.BLUE,
    'proposal_sent': Colors.YELLOW,
    'negotiation': Colors.YELLOW + Colors.BOLD,
    'won': Colors.GREEN,
    'lost': Colors.RED,
    'inactive': Colors.ENDC,
}


def load_data() -> Dict:
    """Load CRM data from storage."""
    if not STORAGE_FILE.exists():
        return {
            'prospects': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'version': '1.0'
            }
        }

    try:
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"{Colors.RED}ERROR: Corrupted data file{Colors.ENDC}")
        sys.exit(1)


def save_data(data: Dict) -> None:
    """Persist CRM data to storage."""
    data['metadata']['last_updated'] = datetime.now().isoformat()

    with open(STORAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def find_prospect(data: Dict, company: str) -> Optional[Dict]:
    """Find prospect by company name (case-insensitive)."""
    company_lower = company.lower()
    for prospect in data['prospects']:
        if prospect['company'].lower() == company_lower:
            return prospect
    return None


def cmd_add(args):
    """Add new prospect."""
    data = load_data()

    # Check for duplicates
    if find_prospect(data, args.company):
        print(f"{Colors.RED}ERROR: Prospect '{args.company}' already exists{Colors.ENDC}")
        sys.exit(1)

    prospect = {
        'company': args.company,
        'source': args.source,
        'rate': args.rate,
        'contact': args.contact or '',
        'status': 'lead',
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
        'notes': args.notes or '',
        'deal_size': args.deal_size or 0,
    }

    data['prospects'].append(prospect)
    save_data(data)

    print(f"{Colors.GREEN}✓ Added prospect:{Colors.ENDC} {Colors.BOLD}{args.company}{Colors.ENDC}")
    print(f"  Source: {args.source}")
    print(f"  Rate: ${args.rate}/hr")
    if args.contact:
        print(f"  Contact: {args.contact}")


def cmd_update(args):
    """Update prospect status."""
    data = load_data()

    prospect = find_prospect(data, args.company)
    if not prospect:
        print(f"{Colors.RED}ERROR: Prospect '{args.company}' not found{Colors.ENDC}")
        sys.exit(1)

    old_status = prospect['status']

    # Update fields
    if args.status:
        if args.status not in VALID_STATUSES:
            print(f"{Colors.RED}ERROR: Invalid status. Valid: {', '.join(VALID_STATUSES)}{Colors.ENDC}")
            sys.exit(1)
        prospect['status'] = args.status

    if args.rate:
        prospect['rate'] = args.rate

    if args.contact:
        prospect['contact'] = args.contact

    if args.notes:
        prospect['notes'] = args.notes

    if args.deal_size:
        prospect['deal_size'] = args.deal_size

    prospect['updated'] = datetime.now().isoformat()

    save_data(data)

    print(f"{Colors.GREEN}✓ Updated prospect:{Colors.ENDC} {Colors.BOLD}{args.company}{Colors.ENDC}")
    if args.status:
        print(f"  Status: {old_status} → {STATUS_COLORS.get(args.status, '')}{args.status}{Colors.ENDC}")


def cmd_pipeline(args):
    """Show funnel view."""
    data = load_data()

    if not data['prospects']:
        print(f"{Colors.YELLOW}No prospects in pipeline{Colors.ENDC}")
        return

    # Count by status
    counts = {status: 0 for status in VALID_STATUSES}
    total_value = {status: 0 for status in VALID_STATUSES}

    for prospect in data['prospects']:
        status = prospect['status']
        counts[status] = counts.get(status, 0) + 1
        total_value[status] = total_value.get(status, 0) + prospect.get('deal_size', 0)

    # Display pipeline
    print(f"\n{Colors.BOLD}{Colors.HEADER}FREELANCE PIPELINE{Colors.ENDC}\n")

    total_prospects = len(data['prospects'])
    total_pipeline_value = sum(total_value.values())

    print(f"Total Prospects: {total_prospects}")
    print(f"Pipeline Value: ${total_pipeline_value:,}\n")

    # Funnel visualization
    funnel_order = ['lead', 'contacted', 'proposal_sent', 'negotiation', 'won', 'lost', 'inactive']

    for status in funnel_order:
        count = counts.get(status, 0)
        value = total_value.get(status, 0)

        if count == 0 and status not in ['won', 'lost']:
            continue

        color = STATUS_COLORS.get(status, Colors.ENDC)
        bar_length = int((count / max(total_prospects, 1)) * 30)
        bar = '█' * bar_length

        status_display = status.replace('_', ' ').title()

        print(f"{color}{status_display:15}{Colors.ENDC} {bar} {count:3} ({value:>6,} USD)")

    # Conversion rate (lead → won)
    if counts.get('lead', 0) + counts.get('won', 0) > 0:
        conversion_rate = counts.get('won', 0) / (counts.get('lead', 0) + counts.get('won', 0) + counts.get('lost', 0)) * 100 if (counts.get('lead', 0) + counts.get('won', 0) + counts.get('lost', 0)) > 0 else 0
        print(f"\n{Colors.BOLD}Conversion Rate:{Colors.ENDC} {conversion_rate:.1f}%")


def cmd_stats(args):
    """Show conversion metrics."""
    data = load_data()

    if not data['prospects']:
        print(f"{Colors.YELLOW}No prospects to analyze{Colors.ENDC}")
        return

    prospects = data['prospects']

    # Calculate metrics
    total = len(prospects)
    won = len([p for p in prospects if p['status'] == 'won'])
    lost = len([p for p in prospects if p['status'] == 'lost'])
    active = total - won - lost

    won_deals = [p for p in prospects if p['status'] == 'won']
    total_revenue = sum(p.get('deal_size', 0) for p in won_deals)
    avg_deal_size = total_revenue / len(won_deals) if won_deals else 0

    pipeline_value = sum(p.get('deal_size', 0) for p in prospects if p['status'] not in ['won', 'lost', 'inactive'])

    # Conversion rates
    conversion_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0

    # Source breakdown
    sources = {}
    for p in prospects:
        source = p.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1

    # Display stats
    print(f"\n{Colors.BOLD}{Colors.HEADER}PIPELINE STATISTICS{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Overview{Colors.ENDC}")
    print(f"  Total Prospects: {total}")
    print(f"  Active: {Colors.YELLOW}{active}{Colors.ENDC}")
    print(f"  Won: {Colors.GREEN}{won}{Colors.ENDC}")
    print(f"  Lost: {Colors.RED}{lost}{Colors.ENDC}")
    print(f"  Conversion Rate: {Colors.BOLD}{conversion_rate:.1f}%{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Revenue{Colors.ENDC}")
    print(f"  Total Won: ${total_revenue:,}")
    print(f"  Avg Deal Size: ${avg_deal_size:,.0f}")
    print(f"  Pipeline Value: ${pipeline_value:,}\n")

    print(f"{Colors.BOLD}Source Breakdown{Colors.ENDC}")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source:15} {count:3} prospects")


def cmd_list(args):
    """List all prospects with filtering."""
    data = load_data()

    prospects = data['prospects']

    # Apply filters
    if args.status:
        prospects = [p for p in prospects if p['status'] == args.status]

    if args.source:
        prospects = [p for p in prospects if p.get('source', '').lower() == args.source.lower()]

    if not prospects:
        print(f"{Colors.YELLOW}No prospects match filters{Colors.ENDC}")
        return

    # Display
    print(f"\n{Colors.BOLD}{Colors.HEADER}PROSPECTS{Colors.ENDC}\n")

    for p in prospects:
        color = STATUS_COLORS.get(p['status'], Colors.ENDC)
        status_display = p['status'].replace('_', ' ').title()

        print(f"{Colors.BOLD}{p['company']}{Colors.ENDC}")
        print(f"  Status: {color}{status_display}{Colors.ENDC}")
        print(f"  Source: {p.get('source', 'N/A')}")
        print(f"  Rate: ${p.get('rate', 0)}/hr")

        if p.get('contact'):
            print(f"  Contact: {p['contact']}")

        if p.get('deal_size'):
            print(f"  Deal Size: ${p['deal_size']:,}")

        if p.get('notes'):
            print(f"  Notes: {p['notes']}")

        print(f"  Updated: {p.get('updated', 'N/A')[:10]}")
        print()


def cmd_export(args):
    """Export to CSV."""
    data = load_data()

    output_file = args.output or 'pipeline_export.csv'

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = [
            'company', 'status', 'source', 'rate', 'contact',
            'deal_size', 'created', 'updated', 'notes'
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for prospect in data['prospects']:
            row = {k: prospect.get(k, '') for k in fieldnames}
            writer.writerow(row)

    print(f"{Colors.GREEN}✓ Exported {len(data['prospects'])} prospects to {output_file}{Colors.ENDC}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Freelance CRM Pipeline Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add new prospect')
    add_parser.add_argument('company', help='Company name')
    add_parser.add_argument('--source', required=True, choices=['upwork', 'fiverr', 'referral', 'linkedin', 'direct'], help='Lead source')
    add_parser.add_argument('--rate', type=int, required=True, help='Hourly rate in USD')
    add_parser.add_argument('--contact', help='Contact person name')
    add_parser.add_argument('--notes', help='Additional notes')
    add_parser.add_argument('--deal-size', type=int, help='Expected deal size in USD')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update prospect')
    update_parser.add_argument('company', help='Company name')
    update_parser.add_argument('--status', choices=VALID_STATUSES, help='New status')
    update_parser.add_argument('--rate', type=int, help='Update hourly rate')
    update_parser.add_argument('--contact', help='Update contact person')
    update_parser.add_argument('--notes', help='Update notes')
    update_parser.add_argument('--deal-size', type=int, help='Update deal size')

    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Show funnel view')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show conversion metrics')

    # List command
    list_parser = subparsers.add_parser('list', help='List prospects')
    list_parser.add_argument('--status', choices=VALID_STATUSES, help='Filter by status')
    list_parser.add_argument('--source', help='Filter by source')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export to CSV')
    export_parser.add_argument('--output', help='Output CSV file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command handlers
    if args.command == 'add':
        cmd_add(args)
    elif args.command == 'update':
        cmd_update(args)
    elif args.command == 'pipeline':
        cmd_pipeline(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'export':
        cmd_export(args)


if __name__ == '__main__':
    main()
