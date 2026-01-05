#!/usr/bin/env python3
"""
Interactive Partner Onboarding CLI Tool for GHL Real Estate AI.

This tool allows the agency to register new real estate partners/tenants
with their own API credentials in a secure, guided manner.

Usage:
    python scripts/onboard_partner.py

Features:
    - Interactive prompts for all required information
    - Input validation for API keys and IDs
    - Duplicate tenant detection
    - Optional calendar integration
    - Clear success/error messaging
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "ghl-real-estate-ai"))

from ghl_real_estate_ai.services.tenant_service import TenantService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# ANSI Color Codes for terminal output
class Colors:
    """Terminal color codes for better UX."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """Print welcome header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  GHL Real Estate AI - Partner Onboarding System{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")
    print(f"{Colors.OKCYAN}This tool will register a new real estate partner/tenant.{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Each partner gets their own API credentials and isolated system.{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message."""
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ {message}{Colors.ENDC}\n")


def print_error(message: str):
    """Print error message."""
    print(f"\n{Colors.FAIL}{Colors.BOLD}✗ {message}{Colors.ENDC}\n")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def validate_partner_name(name: str) -> bool:
    """
    Validate partner/tenant name.

    Args:
        name: Partner name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name or not name.strip():
        return False

    # Must be at least 3 characters
    if len(name.strip()) < 3:
        return False

    return True


def validate_location_id(location_id: str) -> bool:
    """
    Validate GHL Location ID.

    Args:
        location_id: GHL Location ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not location_id or not location_id.strip():
        return False

    # Must be at least 5 characters (reasonable minimum for IDs)
    if len(location_id.strip()) < 5:
        return False

    return True


def validate_api_key(api_key: str, key_type: str) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key to validate
        key_type: Type of key ('anthropic' or 'ghl')

    Returns:
        True if valid, False otherwise
    """
    if not api_key or not api_key.strip():
        return False

    api_key = api_key.strip()

    if key_type == "anthropic":
        # Anthropic keys start with 'sk-ant-' and must be at least 15 characters
        # Examples: sk-ant-api03-*, sk-ant-api02-*, sk-ant-sid01-*
        if not api_key.startswith("sk-ant-"):
            return False
        # Reasonable minimum length (sk-ant- prefix is 7 chars, need at least 8 more)
        if len(api_key) < 15:
            return False

    elif key_type == "ghl":
        # GHL keys can be various formats (JWT, API keys, etc.)
        # Just check minimum length
        if len(api_key) < 10:
            return False

    return True


def check_duplicate_tenant(location_id: str, tenants_dir: Path) -> bool:
    """
    Check if a tenant with this location_id already exists.

    Args:
        location_id: GHL Location ID to check
        tenants_dir: Path to tenants directory

    Returns:
        True if duplicate exists, False otherwise
    """
    tenant_file = tenants_dir / f"{location_id}.json"
    return tenant_file.exists()


def get_input_with_validation(
    prompt: str,
    validator_func,
    error_message: str,
    allow_empty: bool = False
) -> str:
    """
    Get user input with validation and retry logic.

    Args:
        prompt: Prompt message to display
        validator_func: Function to validate input
        error_message: Error message to show on validation failure
        allow_empty: Whether to allow empty input

    Returns:
        Validated user input
    """
    while True:
        user_input = input(f"{Colors.OKBLUE}{prompt}{Colors.ENDC}").strip()

        # Handle empty input
        if not user_input:
            if allow_empty:
                return user_input
            print_error("Input cannot be empty. Please try again.")
            continue

        # Validate input
        if validator_func(user_input):
            return user_input
        else:
            print_error(error_message)


async def interactive_onboard() -> bool:
    """
    Run interactive onboarding process.

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If duplicate tenant detected
        Exception: If tenant service fails
    """
    print_header()

    # Initialize tenant service
    tenant_service = TenantService()
    tenants_dir = Path("data/tenants")

    # Step 1: Partner Name
    print(f"{Colors.BOLD}Step 1: Partner Information{Colors.ENDC}")
    partner_name = get_input_with_validation(
        "Enter Partner/Tenant Name (e.g., 'Acme Real Estate'): ",
        validate_partner_name,
        "Partner name must be at least 3 characters long."
    )
    print_success(f"Partner Name: {partner_name}")

    # Step 2: GHL Location ID
    print(f"{Colors.BOLD}Step 2: GHL Configuration{Colors.ENDC}")
    while True:
        location_id = get_input_with_validation(
            "Enter GHL Location ID: ",
            validate_location_id,
            "Location ID must be at least 5 characters long."
        )

        # Check for duplicates
        if check_duplicate_tenant(location_id, tenants_dir):
            print_error(f"A tenant with Location ID '{location_id}' already exists!")
            print_warning("Please use a different Location ID or update the existing tenant manually.")
            retry = input(f"{Colors.OKBLUE}Try a different Location ID? (y/n): {Colors.ENDC}").lower()
            if retry != 'y':
                raise ValueError(f"Tenant with location_id '{location_id}' already exists")
        else:
            break

    print_success(f"Location ID: {location_id}")

    # Step 3: Anthropic API Key
    print(f"{Colors.BOLD}Step 3: Anthropic API Configuration{Colors.ENDC}")
    print(f"{Colors.OKCYAN}This key will be charged for this tenant's AI usage.{Colors.ENDC}")
    anthropic_key = get_input_with_validation(
        "Enter Anthropic API Key (starts with 'sk-ant-'): ",
        lambda k: validate_api_key(k, "anthropic"),
        "Invalid Anthropic API key. Must start with 'sk-ant-' and be at least 20 characters."
    )
    print_success("Anthropic API Key validated")

    # Step 4: GHL API Key
    print(f"{Colors.BOLD}Step 4: GHL API Key{Colors.ENDC}")
    print(f"{Colors.OKCYAN}This key provides access to this tenant's GHL location.{Colors.ENDC}")
    ghl_key = get_input_with_validation(
        "Enter GHL API Key or OAuth Token: ",
        lambda k: validate_api_key(k, "ghl"),
        "Invalid GHL API key. Must be at least 10 characters."
    )
    print_success("GHL API Key validated")

    # Step 5: Calendar ID (Optional)
    print(f"{Colors.BOLD}Step 5: Calendar Integration (Optional){Colors.ENDC}")
    print(f"{Colors.OKCYAN}Leave empty to skip calendar integration.{Colors.ENDC}")
    calendar_id = input(f"{Colors.OKBLUE}Enter GHL Calendar ID (optional): {Colors.ENDC}").strip()

    if calendar_id:
        print_success(f"Calendar ID: {calendar_id}")
    else:
        print_warning("Skipping calendar integration")
        calendar_id = None

    # Step 6: Confirmation
    print(f"\n{Colors.BOLD}{Colors.HEADER}Summary:{Colors.ENDC}")
    print(f"  Partner Name:     {partner_name}")
    print(f"  Location ID:      {location_id}")
    print(f"  Anthropic Key:    {'*' * 10}{anthropic_key[-4:]}")
    print(f"  GHL Key:          {'*' * 10}{ghl_key[-4:]}")
    print(f"  Calendar ID:      {calendar_id or 'Not configured'}")

    confirmation = input(f"\n{Colors.OKBLUE}Confirm registration? (y/n): {Colors.ENDC}").lower()

    if confirmation != 'y':
        print_warning("Registration cancelled by user.")
        return False

    # Step 7: Save configuration
    print(f"\n{Colors.OKCYAN}Saving tenant configuration...{Colors.ENDC}")

    try:
        await tenant_service.save_tenant_config(
            location_id=location_id,
            anthropic_api_key=anthropic_key,
            ghl_api_key=ghl_key,
            ghl_calendar_id=calendar_id
        )

        tenant_file = tenants_dir / f"{location_id}.json"

        print_success("Registration Complete!")
        print(f"\n{Colors.OKGREEN}Partner '{partner_name}' has been successfully onboarded.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Configuration saved to: {tenant_file}{Colors.ENDC}")
        print(f"\n{Colors.OKCYAN}Next Steps:{Colors.ENDC}")
        print(f"  1. Share the Location ID with the partner: {Colors.BOLD}{location_id}{Colors.ENDC}")
        print(f"  2. Configure their GHL webhook to point to your bot")
        print(f"  3. Test the integration with a sample message")
        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

        return True

    except Exception as e:
        logger.error(f"Failed to save tenant configuration: {e}")
        print_error(f"Failed to save configuration: {str(e)}")
        raise


async def main():
    """Main entry point for the CLI tool."""
    try:
        success = await interactive_onboard()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nOnboarding cancelled by user (Ctrl+C)")
        sys.exit(1)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during onboarding")
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
