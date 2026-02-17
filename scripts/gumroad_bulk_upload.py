#!/usr/bin/env python3
"""Bulk upload products to Gumroad via API using compiled UPLOAD_DATA.json."""

import json
import os
import sys
import time
import requests

API_BASE = "https://api.gumroad.com/v2"


def get_token():
    token = os.getenv("GUMROAD_ACCESS_TOKEN")
    if not token:
        print("ERROR: Set GUMROAD_ACCESS_TOKEN environment variable")
        sys.exit(1)
    return token


def list_existing_products(token):
    resp = requests.get(f"{API_BASE}/products", params={"access_token": token})
    data = resp.json()
    if not data.get("success"):
        print(f"Failed to list products: {data}")
        return []
    return data.get("products", [])


def create_product(token, product):
    """Create a single product via Gumroad API."""
    payload = {
        "access_token": token,
        "name": product["name"],
        "price": product["price_cents"],
        "description": product["description"],
        "preview_url": "",
        "require_shipping": "false",
        "published": "true",
    }

    # Add tags if present (Gumroad uses custom_fields or tags in URL)
    if product.get("tags"):
        payload["tags"] = ",".join(product["tags"][:5])  # Gumroad limits tags

    resp = requests.post(f"{API_BASE}/products", data=payload)
    result = resp.json()

    if result.get("success"):
        prod = result["product"]
        print(f"  CREATED: {product['name']} -> ${product['price_cents']/100:.0f} (ID: {prod['id']})")
        return prod
    else:
        print(f"  FAILED: {product['name']} -> {result.get('message', resp.text)}")
        return None


def upload_file_to_product(token, product_id, zip_path):
    """Upload a ZIP file to an existing product."""
    if not os.path.exists(zip_path):
        print(f"  SKIP FILE: {zip_path} not found")
        return False

    with open(zip_path, "rb") as f:
        resp = requests.put(
            f"{API_BASE}/products/{product_id}",
            data={"access_token": token},
            files={"product_file": (os.path.basename(zip_path), f, "application/zip")},
        )
    result = resp.json()
    if result.get("success"):
        print(f"  UPLOADED: {os.path.basename(zip_path)}")
        return True
    else:
        print(f"  FILE FAILED: {result.get('message', resp.text)}")
        return False


def main():
    token = get_token()

    # Load product data
    data_file = os.path.join(os.path.dirname(__file__), "..", "content", "gumroad", "UPLOAD_DATA.json")
    with open(data_file) as f:
        data = json.load(f)

    zip_dir = os.path.join(os.path.dirname(__file__), "..", "content", "gumroad", "zips")

    # Check existing products to avoid duplicates
    existing = list_existing_products(token)
    existing_names = {p["name"] for p in existing}
    print(f"\nFound {len(existing)} existing products on Gumroad")

    products = data.get("products", [])
    bundles = data.get("bundles", [])
    all_items = products + bundles

    print(f"Will upload {len(all_items)} items ({len(products)} products + {len(bundles)} bundles)\n")

    created = 0
    skipped = 0
    failed = 0

    for item in all_items:
        name = item["name"]
        if name in existing_names:
            print(f"  SKIP (exists): {name}")
            skipped += 1
            continue

        result = create_product(token, item)
        if result:
            created += 1
            # Try to upload the ZIP file
            zip_file = item.get("zip_file", "")
            if zip_file:
                zip_path = os.path.join(zip_dir, zip_file)
                upload_file_to_product(token, result["id"], zip_path)
        else:
            failed += 1

        # Rate limit: Gumroad allows ~10 req/s, be conservative
        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"RESULTS: {created} created, {skipped} skipped, {failed} failed")
    print(f"Total on Gumroad: {len(existing) + created}")


if __name__ == "__main__":
    main()
