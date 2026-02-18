#!/usr/bin/env python3
"""Create Stripe products and prices from parsed_products.json.

Usage:
    STRIPE_SECRET_KEY=sk_test_... python scripts/create_stripe_products.py

Idempotent: skips products whose metadata.slug already exists in Stripe.
Outputs: scripts/stripe_price_ids.json with {slug: stripe_price_id} mapping.
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import stripe
except ImportError:
    print("ERROR: stripe package not installed. Run: pip install stripe")
    sys.exit(1)


def parse_price_cents(price_str: str) -> int:
    match = re.search(r"\$([0-9,]+)", price_str)
    if not match:
        return 0
    return int(match.group(1).replace(",", "")) * 100


def parse_slug(slug_str: str) -> str:
    return slug_str.strip("`").strip()


def main() -> None:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        print("ERROR: Set STRIPE_SECRET_KEY environment variable")
        sys.exit(1)

    scripts_dir = Path(__file__).parent
    json_path = scripts_dir / "parsed_products.json"
    output_path = scripts_dir / "stripe_price_ids.json"

    with open(json_path) as f:
        products = json.load(f)

    # Load existing local mapping
    existing: dict[str, str] = {}
    if output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)

    # Discover products already in Stripe by metadata.slug
    print("Scanning existing Stripe products...")
    try:
        for p in stripe.Product.list(limit=100, active=True).auto_paging_iter():
            slug = p.metadata.get("slug")
            if slug and slug not in existing:
                prices = stripe.Price.list(product=p.id, active=True, limit=1)
                if prices.data:
                    existing[slug] = prices.data[0].id
    except stripe.error.StripeError as e:
        print(f"  Warning: Could not list existing products: {e}")

    price_ids = dict(existing)
    created = 0
    skipped = 0

    for product in products:
        if not product.get("url_slug") or not product.get("price"):
            print(f"  SKIP (incomplete): {product.get('spec_name', 'unknown')}")
            skipped += 1
            continue

        slug = parse_slug(product["url_slug"])

        if slug in price_ids:
            print(f"  SKIP (exists):     {slug} -> {price_ids[slug]}")
            skipped += 1
            continue

        price_cents = parse_price_cents(product["price"])
        if price_cents == 0:
            print(f"  SKIP (no price):   {slug}")
            skipped += 1
            continue

        name = product.get("title", product["spec_name"])
        description = product.get("short_description", "")[:500]

        try:
            stripe_product = stripe.Product.create(
                name=name,
                description=description,
                metadata={"slug": slug, "spec_name": product["spec_name"]},
            )
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=price_cents,
                currency="usd",
            )
            price_ids[slug] = stripe_price.id
            created += 1
            print(f"  CREATED:           {slug} -> {stripe_price.id} (${price_cents / 100:.0f})")
        except stripe.error.StripeError as e:
            print(f"  ERROR:             {slug} - {e}")

    with open(output_path, "w") as f:
        json.dump(price_ids, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"\nDone: {created} created, {skipped} skipped")
    print(f"Price IDs written to {output_path}")


if __name__ == "__main__":
    main()
