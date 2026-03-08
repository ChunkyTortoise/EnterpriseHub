#!/usr/bin/env python3
"""
Demo environment seeder for portfolio showcase.

Generates bcrypt password hashes for demo credentials and prints the
environment variables you need to set (Render dashboard or .env).

Also verifies that the auth env vars are set in production.

Usage:
    python scripts/seed_demo.py              # generate hashes + print instructions
    python scripts/seed_demo.py --check      # verify env vars are present (used at startup)
    python scripts/seed_demo.py --generate   # generate and print env var export commands
"""

import argparse
import os
import sys


DEMO_USERNAME = "demo_user"
DEMO_PASSWORD = "Demo1234!"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin1234!"


def _hash(password: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    except ImportError:
        print("bcrypt not installed — falling back to hashlib (not for production)", file=sys.stderr)
        import hashlib, secrets as _secrets
        salt = _secrets.token_hex(16)
        return f"sha256:{salt}:{hashlib.sha256((salt + password).encode()).hexdigest()}"


def generate() -> None:
    demo_hash = _hash(DEMO_PASSWORD)
    admin_hash = _hash(ADMIN_PASSWORD)

    print()
    print("=" * 60)
    print("EnterpriseHub — Demo Credentials")
    print("=" * 60)
    print()
    print("Demo user:  demo_user / Demo1234!")
    print("Admin user: admin     / Admin1234!")
    print()
    print("Set these environment variables in Render (or .env):")
    print()
    print(f'  AUTH_DEMO_USER_HASH="{demo_hash}"')
    print(f'  AUTH_ADMIN_USER_HASH="{admin_hash}"')
    print()
    print("Or copy the export commands below:")
    print()
    print(f"export AUTH_DEMO_USER_HASH='{demo_hash}'")
    print(f"export AUTH_ADMIN_USER_HASH='{admin_hash}'")
    print()
    print("=" * 60)
    print()


def check() -> None:
    """Called at startup in production to ensure auth env vars are present."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    if env != "production":
        return  # Skip in dev/test

    missing = []
    if not os.environ.get("AUTH_DEMO_USER_HASH"):
        missing.append("AUTH_DEMO_USER_HASH")
    if not os.environ.get("AUTH_ADMIN_USER_HASH"):
        missing.append("AUTH_ADMIN_USER_HASH")

    if missing:
        print("ERROR: Missing auth env vars in production:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        print("Run: python scripts/seed_demo.py --generate", file=sys.stderr)
        sys.exit(1)

    print("✓ Auth env vars present")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo environment")
    parser.add_argument("--check", action="store_true", help="Check env vars at startup")
    parser.add_argument("--generate", action="store_true", help="Generate hashes and print export commands")
    args = parser.parse_args()

    if args.check:
        check()
    else:
        generate()


if __name__ == "__main__":
    main()
