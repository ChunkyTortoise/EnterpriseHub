#!/usr/bin/env python3
"""
Verify Screenshot Setup - Diagnostic Script

Checks if all prerequisites are installed and configured correctly
for automated screenshot capture.

Usage:
    python3 assets/verify_screenshot_setup.py
"""

import socket
import sys
from pathlib import Path


def check_playwright():
    """Check if Playwright is installed."""
    print("🔍 Checking Playwright installation...")
    try:
        import playwright  # noqa: F401

        # Try to get version, but don't fail if not available
        try:
            from playwright import __version__

            print(f"  ✓ Playwright installed: v{__version__}")
        except (ImportError, AttributeError):
            print("  ✓ Playwright installed")
        return True
    except ImportError:
        print("  ✗ Playwright not installed")
        print("    Install with: pip install playwright")
        return False


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print("\n🔍 Checking Playwright browsers...")
    try:
        import subprocess

        result = subprocess.run(
            ["playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # If dry-run succeeds, browsers are likely installed
        if result.returncode == 0:
            print("  ✓ Playwright browsers installed")
            return True
        else:
            print("  ⚠️  Browsers may not be installed")
            print("    Install with: playwright install chromium")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not verify: {e}")
        print("    Install with: playwright install chromium")
        return False


def check_streamlit():
    """Check if Streamlit is installed."""
    print("\n🔍 Checking Streamlit installation...")
    try:
        import streamlit

        try:
            print(f"  ✓ Streamlit installed: v{streamlit.__version__}")
        except AttributeError:
            print("  ✓ Streamlit installed")
        return True
    except ImportError:
        print("  ✗ Streamlit not installed")
        print("    Install with: pip install streamlit")
        return False


def check_streamlit_running():
    """Check if Streamlit app is running."""
    print("\n🔍 Checking if Streamlit is running...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", 8501))
    sock.close()

    if result == 0:
        print("  ✓ Streamlit is running on port 8501")
        return True
    else:
        print("  ✗ Streamlit is not running")
        print("    Start with: streamlit run app.py")
        return False


def check_output_directory():
    """Check if output directory exists."""
    print("\n🔍 Checking output directory...")
    output_dir = Path("docs/screenshots")

    if output_dir.exists() and output_dir.is_dir():
        print(f"  ✓ Output directory exists: {output_dir.absolute()}")
        return True
    else:
        print("  ⚠️  Output directory does not exist")
        print(f"    Creating: {output_dir.absolute()}")
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            print("  ✓ Output directory created")
            return True
        except Exception as e:
            print(f"  ✗ Could not create directory: {e}")
            return False


def check_scripts():
    """Check if screenshot scripts exist."""
    print("\n🔍 Checking screenshot scripts...")

    scripts = [
        "assets/capture_screenshots_simple.py",
        "assets/capture_screenshots.py",
        "assets/selenium_screenshot.py",
    ]

    all_exist = True
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ✗ {script} not found")
            all_exist = False

    return all_exist


def check_documentation():
    """Check if documentation exists."""
    print("\n🔍 Checking documentation...")

    docs = [
        "docs/SCREENSHOTS.md",
        "docs/SCREENSHOT_GUIDE.md",
        "assets/README.md",
        "QUICK_START_SCREENSHOTS.md",
    ]

    all_exist = True
    for doc in docs:
        doc_path = Path(doc)
        if doc_path.exists():
            print(f"  ✓ {doc}")
        else:
            print(f"  ✗ {doc} not found")
            all_exist = False

    return all_exist


def main():
    """Run all checks."""
    print("=" * 70)
    print("Screenshot Setup Verification")
    print("=" * 70 + "\n")

    results = {
        "Playwright": check_playwright(),
        "Playwright Browsers": check_playwright_browsers(),
        "Streamlit": check_streamlit(),
        "Streamlit Running": check_streamlit_running(),
        "Output Directory": check_output_directory(),
        "Scripts": check_scripts(),
        "Documentation": check_documentation(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70 + "\n")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {name}")

    print(f"\n{passed}/{total} checks passed")

    # Recommendations
    print("\n" + "=" * 70)
    print("Next Steps")
    print("=" * 70 + "\n")

    if not results["Playwright"]:
        print("1. Install Playwright:")
        print("   pip install playwright\n")

    if not results["Playwright Browsers"]:
        print("2. Install Playwright browsers:")
        print("   playwright install chromium\n")

    if not results["Streamlit Running"]:
        print("3. Start Streamlit app:")
        print("   streamlit run app.py\n")

    if all(results.values()):
        print("✅ All checks passed! Ready to capture screenshots.")
        print("\nRun screenshot capture:")
        print("   python3 assets/capture_screenshots_simple.py\n")
        return 0
    else:
        print("⚠️  Some checks failed. Fix issues above and try again.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
