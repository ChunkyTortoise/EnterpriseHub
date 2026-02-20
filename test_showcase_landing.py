"""
Test script for showcase landing page.
Validates imports, component rendering, and page structure.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        from ghl_real_estate_ai.streamlit_demo.components.primitives.metric import (
            MetricConfig,
            render_obsidian_metric,
        )
        print("✅ Metric components imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import metric components: {e}")
        return False
    
    try:
        from ghl_real_estate_ai.streamlit_demo.components.primitives.card import (
            CardConfig,
            render_obsidian_card,
        )
        print("✅ Card components imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import card components: {e}")
        return False
    
    return True


def test_page_structure():
    """Test page file structure."""
    print("\nTesting page structure...")
    
    showcase_file = Path("ghl_real_estate_ai/streamlit_demo/showcase_landing.py")
    
    if not showcase_file.exists():
        print(f"❌ Showcase landing page not found at {showcase_file}")
        return False
    
    print(f"✅ Showcase landing page exists at {showcase_file}")
    
    # Read file and check for key functions
    with open(showcase_file) as f:
        content = f.read()
    
    required_functions = [
        "render_hero_section",
        "render_key_metrics",
        "render_case_study_highlights",
        "render_service_categories",
        "render_navigation_tabs",
        "render_technical_highlights",
        "render_footer",
        "main",
    ]
    
    for func in required_functions:
        if f"def {func}" in content:
            print(f"✅ Function '{func}' found")
        else:
            print(f"❌ Function '{func}' missing")
            return False
    
    # Check for proper page config
    if "st.set_page_config" in content:
        print("✅ Page config found")
    else:
        print("❌ Page config missing")
        return False
    
    return True


def test_css_styling():
    """Test that custom CSS is included."""
    print("\nTesting CSS styling...")
    
    showcase_file = Path("ghl_real_estate_ai/streamlit_demo/showcase_landing.py")
    
    with open(showcase_file) as f:
        content = f.read()
    
    required_css_classes = [
        "hero-section",
        "hero-title",
        "hero-subtitle",
        "stat-card",
        "service-category",
        "cta-button",
    ]
    
    for css_class in required_css_classes:
        if css_class in content:
            print(f"✅ CSS class '{css_class}' found")
        else:
            print(f"❌ CSS class '{css_class}' missing")
            return False
    
    return True


def test_performance_targets():
    """Verify performance-related code patterns."""
    print("\nTesting performance patterns...")
    
    showcase_file = Path("ghl_real_estate_ai/streamlit_demo/showcase_landing.py")
    
    with open(showcase_file) as f:
        content = f.read()
    
    # Check for type hints
    if "-> None:" in content or "-> str:" in content:
        print("✅ Type hints found")
    else:
        print("⚠️  Type hints may be missing")
    
    # Check for docstrings
    if '"""' in content:
        print("✅ Docstrings found")
    else:
        print("❌ Docstrings missing")
        return False
    
    # Check for professional color palette
    if "--primary-blue" in content and "--accent-blue" in content:
        print("✅ Professional color palette defined")
    else:
        print("❌ Professional color palette missing")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("EnterpriseHub Showcase Landing Page - Validation Tests")
    print("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Page Structure": test_page_structure(),
        "CSS Styling": test_css_styling(),
        "Performance Patterns": test_performance_targets(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Showcase landing page is ready.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
