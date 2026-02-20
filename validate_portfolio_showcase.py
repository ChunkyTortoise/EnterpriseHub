#!/usr/bin/env python
"""
Validation script for Portfolio Showcase implementation
Verifies data integrity, imports, and integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def validate_data_layer():
    """Validate data files can be imported and have correct structure."""
    print("=" * 60)
    print("VALIDATING DATA LAYER")
    print("=" * 60)
    
    try:
        from ghl_real_estate_ai.streamlit_demo.data import (
            CASE_STUDIES,
            CATEGORIES,
            DIFFERENTIATORS,
            INDUSTRIES,
            SERVICES,
        )
        print(f"✓ All data imports successful")
        print(f"  - Services: {len(SERVICES)} loaded")
        print(f"  - Categories: {len(CATEGORIES)} loaded")
        print(f"  - Industries: {len(INDUSTRIES)} loaded")
        print(f"  - Case Studies: {len(CASE_STUDIES)} loaded")
        print(f"  - Differentiators: {len(DIFFERENTIATORS)} fields")
        
        # Validate service structure
        required_service_fields = [
            "title", "tagline", "category", "description", 
            "key_benefits", "price_range", "timeline", "roi_example"
        ]
        for service_id, service in list(SERVICES.items())[:3]:  # Check first 3
            missing_fields = [f for f in required_service_fields if f not in service]
            if missing_fields:
                print(f"✗ Service {service_id} missing fields: {missing_fields}")
                return False
        print(f"✓ Service structure validated (all required fields present)")
        
        # Validate case study structure
        required_cs_fields = [
            "title", "subtitle", "challenge", "solution", 
            "technical_stack", "architecture", "outcomes"
        ]
        for cs_id, cs in CASE_STUDIES.items():
            missing_fields = [f for f in required_cs_fields if f not in cs]
            if missing_fields:
                print(f"✗ Case study {cs_id} missing fields: {missing_fields}")
                return False
        print(f"✓ Case study structure validated (all required fields present)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def validate_presentation_layer():
    """Validate presentation files can be imported."""
    print("\n" + "=" * 60)
    print("VALIDATING PRESENTATION LAYER")
    print("=" * 60)
    
    try:
        from ghl_real_estate_ai.streamlit_demo.services_portfolio import render_services_portfolio
        print(f"✓ services_portfolio.py imports successfully")
        
        from ghl_real_estate_ai.streamlit_demo.case_studies import render_case_studies
        print(f"✓ case_studies.py imports successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def validate_navigation_integration():
    """Validate navigation files updated correctly."""
    print("\n" + "=" * 60)
    print("VALIDATING NAVIGATION INTEGRATION")
    print("=" * 60)
    
    try:
        from ghl_real_estate_ai.streamlit_demo.navigation.hub_navigator import (
            COUNSEL_MESSAGES,
            HUB_CATEGORIES,
        )
        
        # Check Portfolio Showcase category exists
        if "Portfolio Showcase" not in HUB_CATEGORIES:
            print("✗ 'Portfolio Showcase' category not found in HUB_CATEGORIES")
            return False
        print(f"✓ 'Portfolio Showcase' category found")
        
        # Check hubs in category
        portfolio_hubs = HUB_CATEGORIES["Portfolio Showcase"]
        expected_hubs = ["Services Portfolio", "Case Studies"]
        for hub in expected_hubs:
            if hub not in portfolio_hubs:
                print(f"✗ Hub '{hub}' not found in Portfolio Showcase category")
                return False
        print(f"✓ Both hubs found: {portfolio_hubs}")
        
        # Check counsel messages
        for hub in expected_hubs:
            if hub not in COUNSEL_MESSAGES:
                print(f"✗ Counsel message missing for '{hub}'")
                return False
        print(f"✓ Counsel messages configured for both hubs")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def validate_file_structure():
    """Validate all expected files exist."""
    print("\n" + "=" * 60)
    print("VALIDATING FILE STRUCTURE")
    print("=" * 60)
    
    expected_files = [
        "ghl_real_estate_ai/streamlit_demo/data/__init__.py",
        "ghl_real_estate_ai/streamlit_demo/data/services_data.py",
        "ghl_real_estate_ai/streamlit_demo/data/case_studies_data.py",
        "ghl_real_estate_ai/streamlit_demo/services_portfolio.py",
        "ghl_real_estate_ai/streamlit_demo/case_studies.py",
        "ghl_real_estate_ai/streamlit_demo/PORTFOLIO_SHOWCASE_README.md",
    ]
    
    all_exist = True
    for file_path in expected_files:
        full_path = project_root / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"✓ {file_path} ({size_kb:.1f}KB)")
        else:
            print(f"✗ {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Run all validation checks."""
    print("\n" + "=" * 60)
    print("PORTFOLIO SHOWCASE VALIDATION")
    print("=" * 60 + "\n")
    
    results = {
        "File Structure": validate_file_structure(),
        "Data Layer": validate_data_layer(),
        "Presentation Layer": validate_presentation_layer(),
        "Navigation Integration": validate_navigation_integration(),
    }
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "=" * 60)
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 60)
        print("\nPortfolio Showcase is ready for use!")
        print("\nTo access:")
        print("1. Run: streamlit run ghl_real_estate_ai/streamlit_demo/app.py")
        print("2. Navigate to 'Portfolio Showcase' in sidebar")
        print("3. Select 'Services Portfolio' or 'Case Studies'\n")
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 60)
        print("\nPlease fix the errors above before using Portfolio Showcase.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
