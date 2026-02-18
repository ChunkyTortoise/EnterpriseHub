#!/usr/bin/env python3
"""Lemon Squeezy REST API client for product management.

Usage:
    python scripts/lemonsqueezy_api.py --list-stores
    python scripts/lemonsqueezy_api.py --list-products
    python scripts/lemonsqueezy_api.py --list-products --store-id=12345
    python scripts/lemonsqueezy_api.py --get-product --product-id=67890
    python scripts/lemonsqueezy_api.py --create-product --store-id=123 --name="Product" --description="Desc"
    python scripts/lemonsqueezy_api.py --update-product --product-id=67890 --name="New Name"
    python scripts/lemonsqueezy_api.py --create-variant --product-id=67890 --variant-name="Pro" --price-cents=9900
    python scripts/lemonsqueezy_api.py --list-variants
    python scripts/lemonsqueezy_api.py --list-variants --product-id=67890

Auth: Set LEMONSQUEEZY_API_KEY environment variable.
"""

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class LemonSqueezyError(Exception):
    """API error with status code and response body."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"LemonSqueezy API error {status}: {body}")


class LemonSqueezyClient:
    """Lemon Squeezy REST API client using only stdlib (no external deps).

    Implements JSON:API v1 format as required by Lemon Squeezy.
    See: https://docs.lemonsqueezy.com/api
    """

    BASE_URL = "https://api.lemonsqueezy.com/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("LEMONSQUEEZY_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "LEMONSQUEEZY_API_KEY required. "
                "Set it as an environment variable or pass it to the constructor."
            )

    def _request(self, method: str, path: str, data: dict[str, Any] | None = None) -> dict:
        """Execute an HTTP request against the Lemon Squeezy API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            path: API path relative to BASE_URL (e.g., "/stores").
            data: Optional JSON:API payload dict for POST/PATCH requests.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            LemonSqueezyError: On non-2xx HTTP responses.
        """
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")

        request = Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urlopen(request) as response:
                response_body = response.read().decode("utf-8")
                if response_body:
                    return json.loads(response_body)
                return {}
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            raise LemonSqueezyError(e.code, error_body) from e

    # ── Store operations ─────────────────────────────────────────────────

    def list_stores(self) -> dict:
        """List all stores associated with the authenticated account.

        Returns:
            JSON:API response containing store objects.
        """
        return self._request("GET", "/stores")

    # ── Product operations ───────────────────────────────────────────────

    def list_products(self, store_id: str | None = None) -> dict:
        """List products, optionally filtered by store.

        Args:
            store_id: If provided, only return products belonging to this store.

        Returns:
            JSON:API response containing product objects.
        """
        path = "/products"
        if store_id:
            path = f"/products?filter[store_id]={store_id}"
        return self._request("GET", path)

    def get_product(self, product_id: str) -> dict:
        """Retrieve a single product by ID.

        Args:
            product_id: The Lemon Squeezy product ID.

        Returns:
            JSON:API response containing the product object.
        """
        return self._request("GET", f"/products/{product_id}")

    def create_product(
        self,
        store_id: str,
        name: str,
        description: str,
        **kwargs: Any,
    ) -> dict:
        """Create a new product in a store.

        Args:
            store_id: The store to create the product in.
            name: Product name.
            description: Product description (HTML supported).
            **kwargs: Additional product attributes. Common options:
                - status (str): "draft" or "published" (default: "draft")
                - slug (str): URL slug for the product page
                - thumb_url (str): Thumbnail image URL
                - large_thumb_url (str): Large thumbnail URL
                - price (int): Price in cents (set on variant, not product)

        Returns:
            JSON:API response containing the created product.
        """
        attributes: dict[str, Any] = {
            "name": name,
            "description": description,
        }
        attributes.update(kwargs)

        payload = {
            "data": {
                "type": "products",
                "attributes": attributes,
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": str(store_id),
                        }
                    }
                },
            }
        }
        return self._request("POST", "/products", data=payload)

    def update_product(self, product_id: str, **kwargs: Any) -> dict:
        """Update an existing product.

        Args:
            product_id: The Lemon Squeezy product ID to update.
            **kwargs: Product attributes to update. Common options:
                - name (str): New product name
                - description (str): New description
                - status (str): "draft" or "published"
                - slug (str): URL slug

        Returns:
            JSON:API response containing the updated product.
        """
        if not kwargs:
            raise ValueError("At least one attribute to update is required.")

        payload = {
            "data": {
                "type": "products",
                "id": str(product_id),
                "attributes": kwargs,
            }
        }
        return self._request("PATCH", f"/products/{product_id}", data=payload)

    # ── Variant operations ───────────────────────────────────────────────

    def create_variant(
        self,
        product_id: str,
        name: str,
        price_cents: int,
        **kwargs: Any,
    ) -> dict:
        """Create a pricing variant for a product.

        Args:
            product_id: The product to add the variant to.
            name: Variant name (e.g., "Starter", "Pro", "Enterprise").
            price_cents: Price in cents (e.g., 4900 for $49.00).
            **kwargs: Additional variant attributes. Common options:
                - sort (int): Display order
                - is_subscription (bool): Whether this is a recurring payment
                - interval (str): Billing interval ("day", "week", "month", "year")
                - interval_count (int): Number of intervals between billings
                - has_free_trial (bool): Whether variant includes a free trial
                - trial_interval (str): Trial period interval
                - trial_interval_count (int): Number of trial intervals
                - has_license_keys (bool): Generate license keys on purchase
                - license_activation_limit (int): Max activations per key
                - description (str): Variant description

        Returns:
            JSON:API response containing the created variant.
        """
        attributes: dict[str, Any] = {
            "name": name,
            "price": price_cents,
        }
        attributes.update(kwargs)

        payload = {
            "data": {
                "type": "variants",
                "attributes": attributes,
                "relationships": {
                    "product": {
                        "data": {
                            "type": "products",
                            "id": str(product_id),
                        }
                    }
                },
            }
        }
        return self._request("POST", "/variants", data=payload)

    def list_variants(self, product_id: str | None = None) -> dict:
        """List variants, optionally filtered by product.

        Args:
            product_id: If provided, only return variants belonging to this product.

        Returns:
            JSON:API response containing variant objects.
        """
        path = "/variants"
        if product_id:
            path = f"/variants?filter[product_id]={product_id}"
        return self._request("GET", path)


# ── Pretty-print helpers ─────────────────────────────────────────────────


def _print_json(data: dict) -> None:
    """Pretty-print a JSON:API response to stdout."""
    print(json.dumps(data, indent=2))


def _print_table(data: dict, resource_type: str) -> None:
    """Print a JSON:API response as a readable table.

    Handles both single-resource and collection responses.
    """
    items = data.get("data", [])
    if isinstance(items, dict):
        items = [items]

    if not items:
        print(f"No {resource_type} found.")
        return

    print(f"\n{'=' * 70}")
    print(f" {resource_type.upper()} ({len(items)} total)")
    print(f"{'=' * 70}")

    for item in items:
        attrs = item.get("attributes", {})
        item_id = item.get("id", "?")
        name = attrs.get("name", attrs.get("slug", "Unnamed"))
        status = attrs.get("status", "")
        created = attrs.get("created_at", "")[:10]

        print(f"\n  ID:      {item_id}")
        print(f"  Name:    {name}")
        if status:
            print(f"  Status:  {status}")
        if created:
            print(f"  Created: {created}")

        # Show price for variants
        price = attrs.get("price")
        if price is not None:
            price_formatted = attrs.get("price_formatted", f"${price / 100:.2f}")
            print(f"  Price:   {price_formatted}")

        # Show description preview (first 80 chars)
        desc = attrs.get("description", "")
        if desc:
            desc_clean = desc.replace("\n", " ").strip()
            if len(desc_clean) > 80:
                desc_clean = desc_clean[:77] + "..."
            print(f"  Desc:    {desc_clean}")

    print(f"\n{'=' * 70}\n")


# ── CLI ───────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with all supported operations."""
    parser = argparse.ArgumentParser(
        description="Lemon Squeezy REST API client for product management.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-stores
  %(prog)s --list-products --store-id 12345
  %(prog)s --get-product --product-id 67890
  %(prog)s --create-product --store-id 123 --name "My Product" --description "Great product"
  %(prog)s --update-product --product-id 67890 --name "New Name" --status published
  %(prog)s --create-variant --product-id 67890 --variant-name "Pro" --price-cents 9900
  %(prog)s --list-variants --product-id 67890

Environment:
  LEMONSQUEEZY_API_KEY    Required. Your Lemon Squeezy API key.
        """,
    )

    # Operation flags (mutually exclusive)
    ops = parser.add_mutually_exclusive_group(required=True)
    ops.add_argument("--list-stores", action="store_true", help="List all stores")
    ops.add_argument("--list-products", action="store_true", help="List products")
    ops.add_argument("--get-product", action="store_true", help="Get a single product")
    ops.add_argument("--create-product", action="store_true", help="Create a new product")
    ops.add_argument("--update-product", action="store_true", help="Update an existing product")
    ops.add_argument("--create-variant", action="store_true", help="Create a pricing variant")
    ops.add_argument("--list-variants", action="store_true", help="List variants")

    # Common parameters
    parser.add_argument("--store-id", type=str, help="Store ID for filtering or creating")
    parser.add_argument("--product-id", type=str, help="Product ID for get/update/variant ops")
    parser.add_argument("--name", type=str, help="Product name (create/update)")
    parser.add_argument("--description", type=str, help="Product description (create/update)")
    parser.add_argument(
        "--status",
        type=str,
        choices=["draft", "published"],
        help="Product status (create/update)",
    )
    parser.add_argument("--slug", type=str, help="URL slug (create/update)")

    # Variant parameters
    parser.add_argument("--variant-name", type=str, help="Variant name (create-variant)")
    parser.add_argument("--price-cents", type=int, help="Price in cents (create-variant)")

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON instead of formatted table",
    )

    return parser


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on error."""
    parser = build_parser()
    args = parser.parse_args()

    # Initialize client
    try:
        client = LemonSqueezyClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_fn = _print_json if args.json else _print_table

    try:
        # ── List stores ──────────────────────────────────────────────
        if args.list_stores:
            result = client.list_stores()
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "stores")

        # ── List products ────────────────────────────────────────────
        elif args.list_products:
            result = client.list_products(store_id=args.store_id)
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "products")

        # ── Get product ──────────────────────────────────────────────
        elif args.get_product:
            if not args.product_id:
                print("Error: --product-id is required for --get-product", file=sys.stderr)
                return 1
            result = client.get_product(args.product_id)
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "product")

        # ── Create product ───────────────────────────────────────────
        elif args.create_product:
            if not args.store_id:
                print("Error: --store-id is required for --create-product", file=sys.stderr)
                return 1
            if not args.name:
                print("Error: --name is required for --create-product", file=sys.stderr)
                return 1
            if not args.description:
                print("Error: --description is required for --create-product", file=sys.stderr)
                return 1

            extra_attrs: dict[str, Any] = {}
            if args.status:
                extra_attrs["status"] = args.status
            if args.slug:
                extra_attrs["slug"] = args.slug

            result = client.create_product(
                store_id=args.store_id,
                name=args.name,
                description=args.description,
                **extra_attrs,
            )
            print("Product created successfully!")
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "product")

        # ── Update product ───────────────────────────────────────────
        elif args.update_product:
            if not args.product_id:
                print("Error: --product-id is required for --update-product", file=sys.stderr)
                return 1

            update_attrs: dict[str, Any] = {}
            if args.name:
                update_attrs["name"] = args.name
            if args.description:
                update_attrs["description"] = args.description
            if args.status:
                update_attrs["status"] = args.status
            if args.slug:
                update_attrs["slug"] = args.slug

            if not update_attrs:
                print(
                    "Error: at least one attribute (--name, --description, --status, --slug) "
                    "is required for --update-product",
                    file=sys.stderr,
                )
                return 1

            result = client.update_product(args.product_id, **update_attrs)
            print("Product updated successfully!")
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "product")

        # ── Create variant ───────────────────────────────────────────
        elif args.create_variant:
            if not args.product_id:
                print("Error: --product-id is required for --create-variant", file=sys.stderr)
                return 1
            if not args.variant_name:
                print("Error: --variant-name is required for --create-variant", file=sys.stderr)
                return 1
            if args.price_cents is None:
                print("Error: --price-cents is required for --create-variant", file=sys.stderr)
                return 1

            result = client.create_variant(
                product_id=args.product_id,
                name=args.variant_name,
                price_cents=args.price_cents,
            )
            print("Variant created successfully!")
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "variant")

        # ── List variants ────────────────────────────────────────────
        elif args.list_variants:
            result = client.list_variants(product_id=args.product_id)
            if args.json:
                _print_json(result)
            else:
                _print_table(result, "variants")

    except LemonSqueezyError as e:
        print(f"API Error (HTTP {e.status}): {e.body}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
