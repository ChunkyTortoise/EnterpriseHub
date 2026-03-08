#!/usr/bin/env python3
"""
Startup env var validator — exits with a clear message if critical vars are missing.
Run before the app starts to catch misconfigured deployments early.

Usage: python scripts/validate_env.py
"""

import os
import sys


def check() -> None:
    env = os.environ.get("ENVIRONMENT", "development").lower()
    demo_mode = os.environ.get("DEMO_MODE", "false").lower() == "true"

    errors: list[str] = []
    warnings: list[str] = []

    # --- Always required ---
    if not os.environ.get("JWT_SECRET_KEY"):
        errors.append("JWT_SECRET_KEY is not set. Generate with: openssl rand -hex 32")

    # --- Required in production ---
    if env == "production":
        required_prod = {
            "AUTH_DEMO_USER_HASH": "bcrypt hash for demo_user. Generate with scripts/seed_demo.py",
            "AUTH_ADMIN_USER_HASH": "bcrypt hash for admin user. Generate with scripts/seed_demo.py",
            "DATABASE_URL": "PostgreSQL connection string",
            "REDIS_URL": "Redis connection string",
            "ANTHROPIC_API_KEY": "Anthropic API key for Claude",
        }
        for key, hint in required_prod.items():
            if not os.environ.get(key):
                errors.append(f"{key} is not set — {hint}")

        if not demo_mode:
            stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
            if not stripe_key:
                warnings.append("STRIPE_SECRET_KEY not set — Stripe billing will be disabled")
            elif not stripe_key.startswith("sk_test_") and not stripe_key.startswith("sk_live_"):
                errors.append("STRIPE_SECRET_KEY looks invalid (expected sk_test_... or sk_live_...)")

    if errors:
        print("=" * 60, file=sys.stderr)
        print("STARTUP ERROR: Missing required environment variables", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Fix the above and restart.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

    if warnings:
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    print(f"✓ Environment validated (env={env}, demo_mode={demo_mode})")


if __name__ == "__main__":
    check()
