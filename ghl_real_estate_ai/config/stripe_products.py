"""Stripe product catalog for one-time digital product purchases.

Loads product data from scripts/parsed_products.json and merges
Stripe price IDs from scripts/stripe_price_ids.json (created by
scripts/create_stripe_products.py).
"""

import json
import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _parse_price_cents(price_str: str) -> int:
    """Extract price in cents from string like '$49 (pay what you want, minimum $49)'."""
    match = re.search(r"\$([0-9,]+)", price_str)
    if not match:
        return 0
    return int(match.group(1).replace(",", "")) * 100


def _parse_slug(slug_str: str) -> str:
    return slug_str.strip("`").strip()


def _determine_tier(spec_name: str) -> str:
    name_lower = spec_name.lower()
    if "enterprise" in name_lower:
        return "enterprise"
    if "pro" in name_lower:
        return "pro"
    if "bundle" in name_lower:
        return "bundle"
    return "starter"


def _determine_family(spec_name: str) -> str:
    sl = spec_name.lower()
    if "agentforge" in sl:
        return "AgentForge"
    if "prompt" in sl:
        return "Prompt Toolkit"
    if "ai integration" in sl or "starter kit" in sl:
        return "AI Starter Kit"
    if "dashboard" in sl:
        return "Dashboard Templates"
    if "docqa" in sl:
        return "DocQA Engine"
    if "scraper" in sl:
        return "Web Scraper"
    if "insight" in sl:
        return "Insight Engine"
    if "bundle" in sl:
        return "Bundles"
    return "Other"


def load_product_catalog() -> dict[str, dict]:
    """Load and parse product catalog from parsed_products.json.

    Returns dict keyed by url_slug with:
      name, description, price_cents, stripe_price_id, tier, product_family, tags
    """
    json_path = _PROJECT_ROOT / "scripts" / "parsed_products.json"
    if not json_path.exists():
        return {}

    with open(json_path) as f:
        raw_products = json.load(f)

    catalog: dict[str, dict] = {}
    for product in raw_products:
        if not product.get("url_slug") or not product.get("price"):
            continue

        slug = _parse_slug(product["url_slug"])
        price_cents = _parse_price_cents(product["price"])
        if price_cents == 0:
            continue

        catalog[slug] = {
            "name": product.get("title", product["spec_name"]),
            "spec_name": product["spec_name"],
            "description": product.get("short_description", ""),
            "price_cents": price_cents,
            "stripe_price_id": "",
            "tier": _determine_tier(product["spec_name"]),
            "product_family": _determine_family(product["spec_name"]),
            "tags": product.get("tags", ""),
        }

    # Merge Stripe price IDs if the mapping file exists
    price_ids_path = _PROJECT_ROOT / "scripts" / "stripe_price_ids.json"
    if price_ids_path.exists():
        with open(price_ids_path) as f:
            price_ids = json.load(f)
        for slug, price_id in price_ids.items():
            if slug in catalog:
                catalog[slug]["stripe_price_id"] = price_id

    return catalog


PRODUCT_CATALOG: dict[str, dict] = load_product_catalog()
