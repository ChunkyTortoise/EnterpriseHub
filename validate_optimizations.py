#!/usr/bin/env python3
"""
Phase 1 Optimization Validation Script
Validates that all optimization services can be imported and activated successfully
"""

import os
import sys
import traceback

def test_optimization_imports():
    """Test that all optimization services can be imported"""
    print("🔍 Testing optimization service imports...")
    
    try:
        # Test ConversationOptimizer
        from ghl_real_estate_ai.services.conversation_optimizer import ConversationOptimizer
        print("✅ ConversationOptimizer imported successfully")
        
        # Test EnhancedPromptCaching  
        from ghl_real_estate_ai.services.enhanced_prompt_caching import EnhancedPromptCaching
        print("✅ EnhancedPromptCaching imported successfully")
        
        # Test Claude Cost Tracking Dashboard
        from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import render_claude_cost_tracking_dashboard
        print("✅ Claude Cost Tracking Dashboard imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_service_initialization():
    """Test that optimization services can be initialized"""
    print("\n🔧 Testing service initialization...")
    
    try:
        # Initialize ConversationOptimizer
        from ghl_real_estate_ai.services.conversation_optimizer import ConversationOptimizer
        optimizer = ConversationOptimizer()
        print("✅ ConversationOptimizer initialized successfully")
        
        # Initialize EnhancedPromptCaching
        from ghl_real_estate_ai.services.enhanced_prompt_caching import EnhancedPromptCaching  
        caching = EnhancedPromptCaching()
        print("✅ EnhancedPromptCaching initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        traceback.print_exc()
        return False

def test_integration_points():
    """Test that integration points work with optimization flags"""
    print("\n🔗 Testing integration points...")
    
    try:
        # Enable optimization flags
        os.environ['ENABLE_CONVERSATION_OPTIMIZATION'] = 'true'
        os.environ['ENABLE_ENHANCED_CACHING'] = 'true'
        
        # Test ConversationManager integration
        from ghl_real_estate_ai.core.conversation_manager import ConversationManager
        cm = ConversationManager()
        print(f"✅ ConversationManager optimization enabled: {cm.optimization_enabled}")
        
        # Test LLMClient integration  
        from ghl_real_estate_ai.core.llm_client import LLMClient
        llm = LLMClient()
        print(f"✅ LLMClient enhanced caching enabled: {llm.enhanced_caching_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("🚀 Phase 1 Optimization Validation")
    print("=" * 50)
    
    # Run all validation tests
    tests_passed = 0
    total_tests = 3
    
    if test_optimization_imports():
        tests_passed += 1
        
    if test_service_initialization():
        tests_passed += 1
        
    if test_integration_points():
        tests_passed += 1
    
    print(f"\n📊 Validation Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All optimization services validated successfully!")
        print("\n🚀 Ready for Phase 1 activation with commands:")
        print("export ENABLE_CONVERSATION_OPTIMIZATION=true")
        print("export ENABLE_ENHANCED_CACHING=true")
        print("streamlit run ghl_real_estate_ai/streamlit_demo/app.py")
        return True
    else:
        print("⚠️ Some validation tests failed. Please review errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)