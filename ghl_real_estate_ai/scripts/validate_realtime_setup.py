#!/usr/bin/env python3
"""
Real-time Setup Validation Script

This script validates the WebSocket and Redis configuration for the
GHL Real Estate AI real-time features. Run this before starting the application
to ensure everything is properly configured.

Usage:
    python scripts/validate_realtime_setup.py
    python scripts/validate_realtime_setup.py --environment production
    python scripts/validate_realtime_setup.py --verbose
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ghl_real_estate_ai.services.realtime_config import (
        get_config_manager,
        validate_realtime_setup,
        REDIS_AVAILABLE,
        WEBSOCKETS_AVAILABLE,
        AIOREDIS_AVAILABLE
    )
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this script from the project root directory")
    print("and that all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE} {title:^56} {Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")


def check_dependencies():
    """Check if required dependencies are available"""
    print_header("Dependency Check")

    dependencies = [
        ("Redis", REDIS_AVAILABLE, "pip install redis>=5.0.0"),
        ("WebSockets", WEBSOCKETS_AVAILABLE, "pip install websockets>=12.0"),
        ("Async Redis", AIOREDIS_AVAILABLE, "pip install aioredis>=2.0.1")
    ]

    all_available = True
    for name, available, install_cmd in dependencies:
        if available:
            print_success(f"{name} library available")
        else:
            print_error(f"{name} library not available")
            print_info(f"Install with: {install_cmd}")
            all_available = False

    return all_available


def check_environment_variables():
    """Check if required environment variables are set"""
    print_header("Environment Variables Check")

    required_vars = [
        ("ANTHROPIC_API_KEY", "Anthropic Claude API key"),
        ("GHL_API_KEY", "GoHighLevel API key"),
        ("GHL_LOCATION_ID", "GoHighLevel Location ID")
    ]

    optional_vars = [
        ("REDIS_URL", "Redis connection URL", "redis://localhost:6379"),
        ("WEBSOCKET_HOST", "WebSocket host", "localhost"),
        ("WEBSOCKET_PORT", "WebSocket port", "8765"),
        ("REALTIME_ENABLED", "Enable real-time features", "true")
    ]

    # Check required variables
    missing_required = []
    for var, description in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: Set ({description})")
        else:
            print_error(f"{var}: Not set ({description})")
            missing_required.append(var)

    # Check optional variables
    print_info("Optional environment variables:")
    for var, description, default in optional_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value} ({description})")
        else:
            print_warning(f"{var}: Using default '{default}' ({description})")

    return len(missing_required) == 0, missing_required


async def check_connections():
    """Check Redis and WebSocket connections"""
    print_header("Connection Testing")

    try:
        manager = get_config_manager()
        results = await manager.test_all_connections()

        # Redis connection
        redis_result = results["redis"]
        if redis_result["success"]:
            print_success(f"Redis: {redis_result['message']}")
        else:
            print_error(f"Redis: {redis_result['message']}")

        # WebSocket connection
        ws_result = results["websocket"]
        if ws_result["success"]:
            print_success(f"WebSocket: {ws_result['message']}")
        else:
            if "refusing connections" in ws_result["message"]:
                print_warning(f"WebSocket: {ws_result['message']}")
                print_info("WebSocket server not running (this is normal for development)")
                print_info("Real-time features will fall back to polling mode")
            else:
                print_error(f"WebSocket: {ws_result['message']}")

        # Overall status
        overall = results["overall"]
        if overall["ready"]:
            print_success("Overall: Real-time system ready!")
        else:
            print_error("Overall: Real-time system not ready")

        if overall["fallback_mode"]:
            print_info("Running in fallback mode (polling instead of WebSocket)")

        return overall["ready"]

    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False


async def run_comprehensive_validation():
    """Run comprehensive validation"""
    print_header("Comprehensive Real-time Validation")

    try:
        result = await validate_realtime_setup()

        validation = result["validation"]
        connections = result["connections"]

        # Configuration validation
        if validation["valid"]:
            print_success("Configuration validation passed")
        else:
            print_error("Configuration validation failed")

        # Show errors
        if validation["errors"]:
            print_error("Configuration errors found:")
            for error in validation["errors"]:
                print(f"  • {error}")

        # Show warnings
        if validation["warnings"]:
            print_warning("Configuration warnings:")
            for warning in validation["warnings"]:
                print(f"  • {warning}")

        # Component status
        print_info("Component status:")
        components = validation["components"]
        for component, status in components.items():
            if status.get("available", True) and status.get("configured", True):
                print_success(f"  {component.capitalize()}: Available and configured")
            else:
                details = []
                if not status.get("available", True):
                    details.append("not available")
                if not status.get("configured", True):
                    details.append("not configured")
                print_warning(f"  {component.capitalize()}: {', '.join(details)}")

        # Production readiness
        if result["ready_for_production"]:
            print_success("System ready for production deployment! 🚀")
        else:
            print_warning("System needs attention before production deployment")

        return result["ready_for_production"]

    except Exception as e:
        print_error(f"Comprehensive validation failed: {e}")
        return False


def print_next_steps(all_good: bool):
    """Print next steps based on validation results"""
    print_header("Next Steps")

    if all_good:
        print_success("All checks passed! You're ready to go.")
        print_info("To start the application:")
        print("  1. streamlit run streamlit_demo/app.py")
        print("  2. Open your browser to http://localhost:8501")
        print("  3. Check the real-time dashboard for live updates")
    else:
        print_error("Some checks failed. Please address the issues above.")
        print_info("Common fixes:")
        print("  1. Install missing dependencies: pip install -r requirements.txt")
        print("  2. Start Redis server: brew services start redis")
        print("  3. Set required environment variables in .env file")
        print("  4. Check firewall settings for ports 6379 (Redis) and 8765 (WebSocket)")

    print_info("\nDocumentation:")
    print("  • Setup Guide: docs/REALTIME_SETUP_GUIDE.md")
    print("  • Configuration: services/realtime_config.py")
    print("  • Environment Template: .env.example")


async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate real-time setup for GHL Real Estate AI")
    parser.add_argument("--environment", "-e", default="development",
                       help="Environment to validate (development, staging, production)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run quick validation (skip connection tests)")

    args = parser.parse_args()

    # Set environment
    if args.environment:
        os.environ["ENVIRONMENT"] = args.environment
        print_info(f"Validating for environment: {args.environment}")

    print_header(f"GHL Real Estate AI - Real-time Setup Validation")
    print_info(f"Environment: {args.environment}")
    print_info(f"Python: {sys.version}")
    print_info(f"Script location: {Path(__file__).absolute()}")

    # Run validation steps
    all_checks_passed = True

    # 1. Check dependencies
    deps_ok = check_dependencies()
    all_checks_passed = all_checks_passed and deps_ok

    if not deps_ok:
        print_error("Cannot continue without required dependencies")
        sys.exit(1)

    # 2. Check environment variables
    env_ok, missing_vars = check_environment_variables()
    all_checks_passed = all_checks_passed and env_ok

    if not env_ok and not args.quick:
        print_warning(f"Missing required variables: {', '.join(missing_vars)}")
        print_info("Continuing with connection tests using defaults...")

    # 3. Check connections (unless quick mode)
    if not args.quick:
        conn_ok = await check_connections()
        all_checks_passed = all_checks_passed and conn_ok

        # 4. Run comprehensive validation
        comp_ok = await run_comprehensive_validation()
        all_checks_passed = all_checks_passed and comp_ok
    else:
        print_info("Skipping connection tests (quick mode)")

    # 5. Print summary and next steps
    print_next_steps(all_checks_passed)

    # Exit with appropriate code
    sys.exit(0 if all_checks_passed else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_info("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Validation script failed: {e}")
        sys.exit(1)