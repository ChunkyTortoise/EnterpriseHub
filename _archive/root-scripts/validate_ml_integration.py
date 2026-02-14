#!/usr/bin/env python3
"""
ML Integration Validation Script
Validates that all ML dependencies and services are working correctly
"""

import asyncio
import sys
import traceback
from datetime import datetime
from typing import Dict, Any

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "RESET": "\033[0m"
    }

    color = status_colors.get(status, "")
    reset = status_colors["RESET"]
    print(f"{color}[{timestamp}] {status}: {message}{reset}")

def test_ml_dependencies():
    """Test that all required ML dependencies are available"""
    print_status("Testing ML dependencies...")

    dependencies = [
        ("numpy", "1.26.2"),
        ("pandas", "2.1.3"),
        ("scikit-learn", "1.4.0"),
        ("joblib", "1.3.2"),
        ("shap", "0.43.0")
    ]

    for package, expected_version in dependencies:
        try:
            if package == "scikit-learn":
                import sklearn
                version = sklearn.__version__
                module_name = "sklearn"
            else:
                module = __import__(package)
                version = module.__version__
                module_name = package

            if version.startswith(expected_version.split('.')[0]):  # Major version match
                print_status(f"✓ {module_name} {version} (expected: {expected_version})", "SUCCESS")
            else:
                print_status(f"⚠ {module_name} {version} (expected: {expected_version})", "WARNING")

        except ImportError as e:
            print_status(f"✗ {package} not found: {e}", "ERROR")
            return False

    return True

def test_ml_event_models():
    """Test that ML event models can be imported and created"""
    print_status("Testing ML event models...")

    try:
        from ghl_real_estate_ai.events.ml_event_models import (
            MLEventType,
            LeadMLScoredEvent,
            LeadMLEscalatedEvent,
            LeadMLCacheHitEvent,
            MLEventPublisher,
            create_ml_event
        )

        # Test event creation
        scored_event = LeadMLScoredEvent(
            lead_id="test_123",
            lead_name="Test Lead",
            ml_score=75.0,
            ml_confidence=0.92,
            ml_classification="hot"
        )

        print_status(f"✓ LeadMLScoredEvent created: {scored_event.lead_name} - {scored_event.ml_score}%", "SUCCESS")

        # Test event factory
        escalated_event = create_ml_event(
            event_type="lead_ml_escalated",
            lead_id="test_456",
            lead_name="Test Lead 2",
            ml_score=45.0,
            ml_confidence=0.65,
            escalation_reason="Low confidence"
        )

        print_status(f"✓ Event factory working: {type(escalated_event).__name__}", "SUCCESS")

        # Test conversion to compliance event
        compliance_event = scored_event.to_compliance_event()
        print_status(f"✓ ComplianceEvent conversion: {compliance_event.event_type}", "SUCCESS")

        return True

    except Exception as e:
        print_status(f"✗ ML event models test failed: {e}", "ERROR")
        traceback.print_exc()
        return False

async def test_ml_lead_analyzer():
    """Test ML Lead Analyzer service"""
    print_status("Testing ML Lead Analyzer...")

    try:
        from ghl_real_estate_ai.services.ml_lead_analyzer import MLLeadPredictor, MLEnhancedLeadAnalyzer

        # Test ML predictor
        predictor = MLLeadPredictor()
        await predictor.load_model()
        print_status("✓ ML model loaded successfully", "SUCCESS")

        # Test prediction
        test_context = {
            "conversations": [
                {"timestamp": 1640995200, "content": "Hi, I'm looking for a 3 bedroom house in Rancho Cucamonga for around $400k"},
                {"timestamp": 1640995800, "content": "Yes, I'm pre-approved for financing and need to move by March"}
            ],
            "extracted_preferences": {
                "budget": 400000,
                "location": "Rancho Cucamonga",
                "bedrooms": 3
            }
        }

        score, confidence, features = await predictor.predict_lead_score(test_context)
        print_status(f"✓ ML prediction: score={score:.1f}%, confidence={confidence:.3f}", "SUCCESS")
        print_status(f"  Top features: {list(features.keys())[:3]}", "INFO")

        # Test enhanced analyzer
        analyzer = MLEnhancedLeadAnalyzer()
        await analyzer.initialize()
        print_status("✓ ML Enhanced Lead Analyzer initialized", "SUCCESS")

        # Test analysis
        result = await analyzer.get_comprehensive_lead_analysis(
            lead_name="Test Lead",
            lead_context=test_context
        )

        print_status(f"✓ Analysis complete: {result.final_score:.1f}% ({result.classification})", "SUCCESS")
        print_status(f"  Analysis time: {result.analysis_time_ms:.1f}ms", "INFO")
        print_status(f"  Source: {result.sources}", "INFO")

        # Test performance metrics
        metrics = analyzer.get_ml_performance_metrics()
        print_status(f"✓ Performance metrics: {metrics['total_analyses']} analyses", "SUCCESS")

        return True

    except Exception as e:
        print_status(f"✗ ML Lead Analyzer test failed: {e}", "ERROR")
        traceback.print_exc()
        return False

def test_cache_service():
    """Test cache service integration"""
    print_status("Testing cache service integration...")

    try:
        from ghl_real_estate_ai.services.cache_service import get_cache_service

        cache = get_cache_service()
        print_status("✓ Cache service imported", "SUCCESS")

        return True

    except Exception as e:
        print_status(f"✗ Cache service test failed: {e}", "ERROR")
        return False

async def test_integration_flow():
    """Test complete ML integration flow"""
    print_status("Testing complete integration flow...")

    try:
        from ghl_real_estate_ai.services.ml_lead_analyzer import get_ml_enhanced_lead_analyzer_async

        # Get analyzer instance
        analyzer = await get_ml_enhanced_lead_analyzer_async()

        # Test high-confidence ML path
        high_confidence_context = {
            "conversations": [
                {"timestamp": 1640995200, "content": "I need to buy a house ASAP! Pre-approved for $500k"},
                {"timestamp": 1640995300, "content": "When can we see houses? I have cash down payment ready"}
            ],
            "extracted_preferences": {
                "budget": 500000,
                "location": "Rancho Cucamonga",
                "timeline": "urgent"
            }
        }

        result1 = await analyzer.get_comprehensive_lead_analysis(
            lead_name="High Confidence Test",
            lead_context=high_confidence_context
        )

        if "ML_RandomForest" in result1.sources:
            print_status("✓ High-confidence ML path working", "SUCCESS")
        else:
            print_status("! ML path used Claude escalation", "WARNING")

        # Test low-confidence escalation path
        low_confidence_context = {
            "conversations": [
                {"timestamp": 1640995200, "content": "Maybe interested"},
            ],
            "extracted_preferences": {}
        }

        result2 = await analyzer.get_comprehensive_lead_analysis(
            lead_name="Low Confidence Test",
            lead_context=low_confidence_context,
            force_refresh=True  # This should force Claude analysis
        )

        if result2.claude_reasoning_time_ms > 0:
            print_status("✓ Claude escalation path working", "SUCCESS")
        else:
            print_status("! Claude escalation may not have occurred", "WARNING")

        # Check metrics
        metrics = analyzer.get_ml_performance_metrics()
        print_status(f"✓ Integration metrics: {metrics['total_analyses']} total analyses", "SUCCESS")
        print_status(f"  ML usage: {metrics['ml_usage_rate_percent']:.1f}%", "INFO")
        print_status(f"  Claude escalation: {metrics['claude_escalation_rate_percent']:.1f}%", "INFO")

        return True

    except Exception as e:
        print_status(f"✗ Integration flow test failed: {e}", "ERROR")
        traceback.print_exc()
        return False

async def main():
    """Run all validation tests"""
    print_status("Starting ML Integration Validation", "INFO")
    print("=" * 60)

    tests = [
        ("ML Dependencies", test_ml_dependencies),
        ("ML Event Models", test_ml_event_models),
        ("Cache Service", test_cache_service),
        ("ML Lead Analyzer", test_ml_lead_analyzer),
        ("Integration Flow", test_integration_flow),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print_status(f"Running {test_name} tests...")

        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()

            results.append((test_name, success))

        except Exception as e:
            print_status(f"✗ {test_name} test crashed: {e}", "ERROR")
            results.append((test_name, False))

    # Summary
    print(f"\n{'=' * 60}")
    print_status("VALIDATION SUMMARY", "INFO")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        color = "SUCCESS" if success else "ERROR"
        print_status(f"{status}: {test_name}", color)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print_status("🎉 All ML integration tests PASSED!", "SUCCESS")
        return 0
    else:
        print_status(f"⚠ {total - passed} tests FAILED", "ERROR")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)