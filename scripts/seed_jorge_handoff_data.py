#!/usr/bin/env python3
"""Seed Jorge handoff history for pattern learning.

Generates deterministic handoff outcome records and optionally exports
them to a JSON fixture file for use in tests. Uses the existing
``JorgeHandoffService.seed_historical_data()`` method under the hood.

Usage:
    python scripts/seed_jorge_handoff_data.py
    python scripts/seed_jorge_handoff_data.py --num-samples 50 --seed 42
    python scripts/seed_jorge_handoff_data.py --export tests/fixtures/jorge_handoff_seed_data.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    JorgeHandoffService,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed Jorge handoff outcome history for pattern learning.",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=20,
        help="Number of outcome records per route (default: 20, min: 10).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible generation (default: None).",
    )
    parser.add_argument(
        "--routes",
        type=str,
        nargs="*",
        default=None,
        help="Specific routes to seed (e.g. lead->buyer). Default: all 4.",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export seeded data to a JSON file (e.g. tests/fixtures/handoff_seed.json).",
    )
    args = parser.parse_args()

    # Reset analytics state to start fresh
    JorgeHandoffService.reset_analytics()

    # Seed the data
    logger.info(
        "Seeding handoff data: num_samples=%d, seed=%s",
        args.num_samples,
        args.seed,
    )
    result = JorgeHandoffService.seed_historical_data(
        num_samples=args.num_samples,
        seed=args.seed,
    )

    # Print summary
    print(f"\nSeeded {result['total_records']} records across {len(result['routes_seeded'])} routes:")
    for route in result["routes_seeded"]:
        rate = result["per_route_success_rates"].get(route, 0.0)
        print(f"  {route}: {rate:.0%} success rate")

    # Export if requested
    if args.export:
        export_path = Path(args.export)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        records = JorgeHandoffService.export_seed_data()
        with open(export_path, "w") as f:
            json.dump(records, f, indent=2)

        print(f"\nExported {len(records)} records to {export_path}")

    # Show learned adjustments
    service = JorgeHandoffService()
    routes = [("lead", "buyer"), ("lead", "seller"), ("buyer", "seller"), ("seller", "buyer")]
    print("\nLearned threshold adjustments:")
    for source, target in routes:
        try:
            adj = service.get_learned_adjustments(source, target)
            print(f"  {source}->{target}: {adj:+.4f}")
        except Exception:
            print(f"  {source}->{target}: (not enough data)")


if __name__ == "__main__":
    main()
