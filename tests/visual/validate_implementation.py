#!/usr/bin/env python3
"""
Visual Testing Implementation Validator

Validates that the visual regression testing infrastructure is correctly
implemented and ready for use.

Usage:
    python tests/visual/validate_implementation.py

Checks:
- Required files exist
- Dependencies are installed
- Playwright is configured
- Test files are valid Python
- Snapshots directory exists
- GitHub Actions workflow exists
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def log_info(msg: str) -> None:
    """Log info message."""
    print(f"{BLUE}ℹ {msg}{NC}")


def log_success(msg: str) -> None:
    """Log success message."""
    print(f"{GREEN}✓ {msg}{NC}")


def log_error(msg: str) -> None:
    """Log error message."""
    print(f"{RED}✗ {msg}{NC}")


def log_warning(msg: str) -> None:
    """Log warning message."""
    print(f"{YELLOW}⚠ {msg}{NC}")


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        log_success(f"{description} exists: {file_path}")
        return True
    else:
        log_error(f"{description} missing: {file_path}")
        return False


def check_directory_exists(dir_path: Path, description: str) -> bool:
    """Check if a directory exists."""
    if dir_path.exists() and dir_path.is_dir():
        log_success(f"{description} exists: {dir_path}")
        return True
    else:
        log_error(f"{description} missing: {dir_path}")
        return False


def check_python_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        log_success(f"Valid Python syntax: {file_path.name}")
        return True
    except SyntaxError as e:
        log_error(f"Syntax error in {file_path.name}: {e}")
        return False


def check_dependency_installed(package: str) -> bool:
    """Check if a Python package is installed."""
    try:
        __import__(package.replace('-', '_'))
        log_success(f"Package installed: {package}")
        return True
    except ImportError:
        log_error(f"Package not installed: {package}")
        return False


def check_playwright_browser() -> bool:
    """Check if Playwright Chromium is installed."""
    try:
        result = subprocess.run(
            ['playwright', 'install', '--dry-run', 'chromium'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if 'chromium' in result.stdout.lower():
            log_success("Playwright Chromium browser is installed")
            return True
        else:
            log_warning("Playwright Chromium may not be installed. Run: playwright install chromium")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log_warning("Could not verify Playwright installation. Run: playwright install chromium")
        return False


def count_components_in_test_file(test_file: Path) -> int:
    """Count number of components in COMPONENTS list."""
    try:
        with open(test_file, 'r') as f:
            content = f.read()

        # Find COMPONENTS list
        if 'COMPONENTS = [' not in content:
            return 0

        # Extract COMPONENTS list
        start = content.index('COMPONENTS = [')
        end = content.index(']', start) + 1
        components_str = content[start:end]

        # Count quoted strings (component IDs)
        import re
        components = re.findall(r"'([^']+)'", components_str)

        return len(components)
    except Exception as e:
        log_warning(f"Could not count components: {e}")
        return 0


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("Visual Testing Implementation Validator")
    print("=" * 70 + "\n")

    # Get project root
    project_root = Path(__file__).parent.parent.parent
    visual_tests_dir = project_root / "tests" / "visual"

    checks_passed = 0
    checks_failed = 0

    # ========================================================================
    # Check Directory Structure
    # ========================================================================
    log_info("Checking directory structure...")

    if check_directory_exists(visual_tests_dir, "Visual tests directory"):
        checks_passed += 1
    else:
        checks_failed += 1

    if check_directory_exists(visual_tests_dir / "snapshots", "Snapshots directory"):
        checks_passed += 1
    else:
        checks_failed += 1

    # ========================================================================
    # Check Required Files
    # ========================================================================
    log_info("\nChecking required files...")

    required_files = [
        (visual_tests_dir / "__init__.py", "Package init"),
        (visual_tests_dir / "conftest.py", "Pytest fixtures"),
        (visual_tests_dir / "test_component_snapshots.py", "Visual regression tests"),
        (visual_tests_dir / "test_accessibility.py", "Accessibility tests"),
        (visual_tests_dir / "README.md", "README documentation"),
        (visual_tests_dir / "QUICK_REFERENCE.md", "Quick reference"),
        (visual_tests_dir / "IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
        (visual_tests_dir / "setup_visual_tests.sh", "Setup script"),
        (visual_tests_dir / "pytest.ini", "Pytest configuration"),
        (visual_tests_dir / ".gitignore", "Git ignore rules"),
        (project_root / ".github" / "workflows" / "visual-regression.yml", "GitHub Actions workflow"),
    ]

    for file_path, description in required_files:
        if check_file_exists(file_path, description):
            checks_passed += 1
        else:
            checks_failed += 1

    # ========================================================================
    # Check Python Syntax
    # ========================================================================
    log_info("\nChecking Python syntax...")

    python_files = [
        visual_tests_dir / "__init__.py",
        visual_tests_dir / "conftest.py",
        visual_tests_dir / "test_component_snapshots.py",
        visual_tests_dir / "test_accessibility.py",
    ]

    for file_path in python_files:
        if file_path.exists():
            if check_python_syntax(file_path):
                checks_passed += 1
            else:
                checks_failed += 1

    # ========================================================================
    # Check Dependencies
    # ========================================================================
    log_info("\nChecking Python dependencies...")

    dependencies = [
        'playwright',
        'pytest',
        'axe_playwright',
    ]

    for dep in dependencies:
        if check_dependency_installed(dep):
            checks_passed += 1
        else:
            checks_failed += 1
            log_info(f"  Install with: pip install {dep}")

    # ========================================================================
    # Check Playwright Browser
    # ========================================================================
    log_info("\nChecking Playwright browsers...")

    if check_playwright_browser():
        checks_passed += 1
    else:
        checks_failed += 1

    # ========================================================================
    # Check Component Coverage
    # ========================================================================
    log_info("\nChecking component coverage...")

    test_file = visual_tests_dir / "test_component_snapshots.py"
    component_count = count_components_in_test_file(test_file)

    if component_count > 0:
        log_success(f"Found {component_count} components in test file")
        checks_passed += 1

        if component_count >= 57:
            log_success("All 57+ components are covered")
            checks_passed += 1
        else:
            log_warning(f"Expected 57+ components, found {component_count}")
            checks_failed += 1
    else:
        log_error("Could not find COMPONENTS list in test file")
        checks_failed += 1

    # ========================================================================
    # Check Requirements.txt
    # ========================================================================
    log_info("\nChecking requirements.txt...")

    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            requirements = f.read()

        required_packages = [
            'pytest-playwright',
            'playwright',
            'axe-playwright',
            'pixelmatch',
        ]

        all_found = True
        for package in required_packages:
            if package in requirements:
                log_success(f"Found {package} in requirements.txt")
                checks_passed += 1
            else:
                log_error(f"Missing {package} in requirements.txt")
                checks_failed += 1
                all_found = False
    else:
        log_error("requirements.txt not found")
        checks_failed += 1

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70 + "\n")

    total_checks = checks_passed + checks_failed
    success_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

    print(f"Total Checks: {total_checks}")
    print(f"Passed: {GREEN}{checks_passed}{NC}")
    print(f"Failed: {RED}{checks_failed}{NC}")
    print(f"Success Rate: {success_rate:.1f}%")

    print("\n" + "=" * 70)

    if checks_failed == 0:
        log_success("\n🎉 All checks passed! Visual testing infrastructure is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Playwright: playwright install chromium")
        print("3. Start Streamlit: streamlit run ghl_real_estate_ai/streamlit_demo/app.py")
        print("4. Run tests: pytest tests/visual/ --screenshot=on -v")
        return 0
    else:
        log_error(f"\n❌ {checks_failed} check(s) failed. Please fix the issues above.")
        print("\nRun the setup script to fix common issues:")
        print("  ./tests/visual/setup_visual_tests.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
