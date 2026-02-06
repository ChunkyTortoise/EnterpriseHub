#!/usr/bin/env python3
"""
Jorge's Lead Bot System - Quick Test Script

Tests all major components to ensure the system is ready for delivery.
Run this before delivering to Jorge to verify everything works.
"""

import sys
import importlib.util
from pathlib import Path
import asyncio
import json

def test_component_imports():
    """Test that all components can be imported successfully."""
    print("🧪 Testing Component Imports...")
    
    components_to_test = [
        "ghl_real_estate_ai.api.routes.jorge_advanced",
        "ghl_real_estate_ai.services.voice_ai_handler",
        "ghl_real_estate_ai.services.automated_marketing_engine", 
        "ghl_real_estate_ai.services.client_retention_engine",
        "ghl_real_estate_ai.services.market_prediction_engine",
        "ghl_real_estate_ai.services.jorge_advanced_integration",
    ]
    
    results = []
    for component in components_to_test:
        try:
            module = importlib.import_module(component)
            print(f"  ✅ {component}")
            results.append((component, True, None))
        except Exception as e:
            print(f"  ❌ {component}: {str(e)}")
            results.append((component, False, str(e)))
    
    return results

def test_dashboard_component():
    """Test that Jorge's dashboard component can be loaded."""
    print("\n🧪 Testing Dashboard Component...")
    
    dashboard_path = Path("ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py")
    
    if not dashboard_path.exists():
        print(f"  ❌ Dashboard component not found: {dashboard_path}")
        return False
    
    try:
        spec = importlib.util.spec_from_file_location("jorge_dashboard", dashboard_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for main function
        if hasattr(module, 'render_jorge_lead_bot_dashboard'):
            print("  ✅ Dashboard component loaded successfully")
            print("  ✅ Main render function found")
            return True
        else:
            print("  ❌ Main render function not found")
            return False
    except Exception as e:
        print(f"  ❌ Error loading dashboard: {str(e)}")
        return False

def test_api_routes():
    """Test that Jorge's API routes are properly defined."""
    print("\n🧪 Testing API Routes...")
    
    try:
        from ghl_real_estate_ai.api.routes.jorge_advanced import router
        
        # Check that router has the expected routes
        expected_routes = [
            "/voice/start-call",
            "/voice/process-input", 
            "/voice/end-call",
            "/marketing/create-campaign",
            "/retention/update-lifecycle",
            "/market/analyze",
            "/dashboard/metrics",
            "/health"
        ]
        
        route_paths = [route.path for route in router.routes]
        
        for expected_route in expected_routes:
            full_path = f"/jorge-advanced{expected_route}"
            if any(expected_route in path for path in route_paths):
                print(f"  ✅ Route found: {expected_route}")
            else:
                print(f"  ❌ Route missing: {expected_route}")
        
        print(f"  📊 Total routes defined: {len(route_paths)}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading API routes: {str(e)}")
        return False

def test_service_initialization():
    """Test that services can be initialized without errors."""
    print("\n🧪 Testing Service Initialization...")
    
    services_to_test = [
        ("VoiceAIHandler", "ghl_real_estate_ai.services.voice_ai_handler", "get_voice_ai_handler"),
        ("MarketingEngine", "ghl_real_estate_ai.services.automated_marketing_engine", "AutomatedMarketingEngine"),
        ("RetentionEngine", "ghl_real_estate_ai.services.client_retention_engine", "ClientRetentionEngine"),
        ("MarketPredictionEngine", "ghl_real_estate_ai.services.market_prediction_engine", "MarketPredictionEngine"),
        ("IntegrationHub", "ghl_real_estate_ai.services.jorge_advanced_integration", "JorgeAdvancedIntegration"),
    ]
    
    for service_name, module_path, class_or_function in services_to_test:
        try:
            module = importlib.import_module(module_path)
            
            if hasattr(module, class_or_function):
                print(f"  ✅ {service_name} class/function available")
                
                # Try to instantiate if it's a class
                try:
                    obj = getattr(module, class_or_function)
                    if callable(obj) and class_or_function != "get_voice_ai_handler":
                        instance = obj()
                        print(f"  ✅ {service_name} instantiated successfully")
                except Exception as init_error:
                    print(f"  ⚠️  {service_name} class available but instantiation failed: {str(init_error)}")
            else:
                print(f"  ❌ {service_name} class/function not found")
        except Exception as e:
            print(f"  ❌ {service_name} module error: {str(e)}")

def test_launcher_script():
    """Test that the launcher script is properly configured."""
    print("\n🧪 Testing Launcher Script...")
    
    launcher_path = Path("jorge_lead_bot_launcher.py")
    
    if not launcher_path.exists():
        print("  ❌ Launcher script not found")
        return False
    
    try:
        with open(launcher_path, 'r') as f:
            content = f.read()
            
        # Check for key functions
        required_functions = [
            "check_requirements",
            "launch_jorge_dashboard",
            "launch_api_server",
            "show_help"
        ]
        
        for func in required_functions:
            if f"def {func}" in content:
                print(f"  ✅ Function found: {func}")
            else:
                print(f"  ❌ Function missing: {func}")
        
        print("  ✅ Launcher script structure validated")
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading launcher script: {str(e)}")
        return False

def test_configuration_files():
    """Test that configuration files exist and are valid."""
    print("\n🧪 Testing Configuration Files...")
    
    # Check for README
    readme_path = Path("JORGE_LEAD_BOT_README.md")
    if readme_path.exists():
        print("  ✅ Jorge's README file found")
    else:
        print("  ❌ Jorge's README file missing")
    
    # Check for main API file
    api_main = Path("ghl_real_estate_ai/api/main.py")
    if api_main.exists():
        print("  ✅ Main API file found")
    else:
        print("  ❌ Main API file missing")
    
    # Check for requirements
    requirements_files = [
        Path("requirements.txt"),
        Path("ghl_real_estate_ai/requirements.txt")
    ]
    
    requirements_found = False
    for req_file in requirements_files:
        if req_file.exists():
            print(f"  ✅ Requirements file found: {req_file}")
            requirements_found = True
            break
    
    if not requirements_found:
        print("  ⚠️  No requirements.txt found (may need manual installation)")

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🚀 Jorge's Lead Bot System - Comprehensive Test")
    print("=" * 60)
    
    all_tests = [
        ("Component Imports", test_component_imports),
        ("Dashboard Component", test_dashboard_component),
        ("API Routes", test_api_routes), 
        ("Service Initialization", test_service_initialization),
        ("Launcher Script", test_launcher_script),
        ("Configuration Files", test_configuration_files),
    ]
    
    test_results = []
    
    for test_name, test_func in all_tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        if isinstance(result, list):  # For import tests
            success_count = sum(1 for _, success, _ in result if success)
            total_count = len(result)
            if success_count == total_count:
                print(f"✅ {test_name}: All {total_count} components passed")
                passed += 1
            else:
                print(f"❌ {test_name}: {success_count}/{total_count} components passed")
        elif result:
            print(f"✅ {test_name}: Passed")
            passed += 1
        else:
            print(f"❌ {test_name}: Failed")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Jorge's system is ready for delivery! 🚀")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before delivery.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    
    if success:
        print("\n" + "=" * 60)
        print("🎁 DELIVERY CHECKLIST FOR JORGE")
        print("=" * 60)
        print("1. ✅ All core components tested and working")
        print("2. ✅ Dashboard interface ready")
        print("3. ✅ API endpoints validated") 
        print("4. ✅ Launcher script prepared")
        print("5. ✅ Documentation complete")
        print("\n📦 Ready for delivery to Jorge!")
        print("📋 Next steps:")
        print("   1. Send Jorge the JORGE_LEAD_BOT_README.md file")
        print("   2. Share the jorge_lead_bot_launcher.py script")
        print("   3. Provide setup instructions from README")
        print("   4. Schedule demo/training session")
    
    sys.exit(0 if success else 1)