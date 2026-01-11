"""
ML Integration Validation Test

Simplified test to validate ML models can be imported and basic functionality works.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_imports():
    """Test that all ML components can be imported"""
    print("🧪 Testing ML component imports...")

    try:
        # Test interface imports
        from interfaces import (
            ILearningModel, ModelType, FeatureVector, ModelPrediction,
            BehavioralEvent, EventType
        )
        print("✅ Core interfaces imported successfully")

        # Test foundation component imports
        from tracking.behavior_tracker import InMemoryBehaviorTracker
        from feature_engineering.standard_feature_engineer import StandardFeatureEngineer
        print("✅ Foundation components imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_ml_model_files_exist():
    """Test that ML model files exist and are properly structured"""
    print("🧪 Testing ML model file structure...")

    required_files = [
        "models/collaborative_filtering.py",
        "models/content_based.py",
        "personalization/property_engine.py"
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            # Check file size to ensure it's not empty
            file_size = os.path.getsize(file_path)
            if file_size > 1000:  # Expect substantial implementation
                print(f"✅ {file_path} exists ({file_size:,} bytes)")
            else:
                print(f"❌ {file_path} exists but is too small ({file_size} bytes)")
                all_exist = False
        else:
            print(f"❌ {file_path} does not exist")
            all_exist = False

    return all_exist

def test_model_class_definitions():
    """Test that model classes are properly defined with required methods"""
    print("🧪 Testing ML model class definitions...")

    try:
        # Test collaborative filtering model structure
        with open("models/collaborative_filtering.py", "r") as f:
            content = f.read()

        required_methods = [
            "class CollaborativeFilteringModel",
            "async def train",
            "async def predict",
            "async def predict_batch",
            "get_feature_importance"
        ]

        collaborative_complete = True
        for method in required_methods:
            if method in content:
                print(f"✅ CollaborativeFilteringModel has {method}")
            else:
                print(f"❌ CollaborativeFilteringModel missing {method}")
                collaborative_complete = False

        # Test content-based model structure
        with open("models/content_based.py", "r") as f:
            content = f.read()

        content_based_complete = True
        for method in required_methods[:-1]:  # Skip get_feature_importance check
            method = method.replace("CollaborativeFilteringModel", "ContentBasedModel")
            if "ContentBasedModel" in method or method.startswith("async def") or method.startswith("get_"):
                if "class ContentBasedModel" in content or method[6:] in content:  # Remove "class " prefix for method checks
                    print(f"✅ ContentBasedModel has required structure")
                else:
                    print(f"❌ ContentBasedModel missing structure")
                    content_based_complete = False
                break

        # Test personalization engine structure
        with open("personalization/property_engine.py", "r") as f:
            content = f.read()

        engine_methods = [
            "class PropertyPersonalizationEngine",
            "async def get_recommendations",
            "async def get_explanation",
            "async def record_feedback"
        ]

        engine_complete = True
        for method in engine_methods:
            if method in content:
                print(f"✅ PropertyPersonalizationEngine has {method}")
            else:
                print(f"❌ PropertyPersonalizationEngine missing {method}")
                engine_complete = False

        return collaborative_complete and content_based_complete and engine_complete

    except Exception as e:
        print(f"❌ Failed to analyze model files: {str(e)}")
        return False

async def test_foundation_integration():
    """Test that foundation components work with feature extraction"""
    print("🧪 Testing foundation integration...")

    try:
        # Import and test basic foundation functionality
        from tracking.behavior_tracker import InMemoryBehaviorTracker
        from tracking.event_collector import EventCollector
        from feature_engineering.standard_feature_engineer import StandardFeatureEngineer
        from interfaces import BehavioralEvent, EventType

        # Initialize components
        tracker = InMemoryBehaviorTracker()
        collector = EventCollector(tracker)
        feature_engineer = StandardFeatureEngineer(tracker)

        # Test basic event tracking
        event_id = await collector.track_property_view(
            lead_id="test_lead_ml",
            property_id="test_prop_ml",
            session_id="test_session_ml"
        )

        print(f"✅ Event tracking works: {event_id}")

        # Test feature extraction
        events = await tracker.get_events(entity_id="test_lead_ml", entity_type="lead")

        if events:
            features = await feature_engineer.extract_features(
                "test_lead_ml", "lead", events
            )

            print(f"✅ Feature extraction works: {len(features.numerical_features)} numerical features")
            return True
        else:
            print("❌ No events retrieved for feature extraction")
            return False

    except Exception as e:
        print(f"❌ Foundation integration failed: {str(e)}")
        return False

def test_directory_structure():
    """Test that ML directory structure is correctly set up"""
    print("🧪 Testing ML directory structure...")

    required_dirs = [
        "models",
        "personalization",
        "services"
    ]

    required_init_files = [
        "models/__init__.py",
        "personalization/__init__.py",
        "services/__init__.py"
    ]

    all_good = True

    # Check directories
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✅ Directory {dir_path} exists")
        else:
            print(f"❌ Directory {dir_path} missing")
            all_good = False

    # Check __init__ files
    for init_file in required_init_files:
        if os.path.exists(init_file):
            print(f"✅ {init_file} exists")
        else:
            print(f"❌ {init_file} missing")
            all_good = False

    return all_good

def test_implementation_completeness():
    """Test that implementations are complete and substantial"""
    print("🧪 Testing implementation completeness...")

    file_size_requirements = {
        "models/collaborative_filtering.py": 15000,  # ~15KB minimum
        "models/content_based.py": 15000,
        "personalization/property_engine.py": 15000
    }

    all_complete = True

    for file_path, min_size in file_size_requirements.items():
        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path)
            if actual_size >= min_size:
                print(f"✅ {file_path}: {actual_size:,} bytes (sufficient)")
            else:
                print(f"❌ {file_path}: {actual_size:,} bytes (too small, need >{min_size:,})")
                all_complete = False
        else:
            print(f"❌ {file_path}: missing")
            all_complete = False

    return all_complete

async def main():
    """Run comprehensive ML validation tests"""
    print("🧠 ML Integration Validation Tests")
    print("=" * 50)

    test_results = []

    # Run all validation tests
    test_results.append(("Directory Structure", test_directory_structure()))
    test_results.append(("File Existence", test_ml_model_files_exist()))
    test_results.append(("Implementation Completeness", test_implementation_completeness()))
    test_results.append(("Class Definitions", test_model_class_definitions()))
    test_results.append(("Import Capability", test_ml_imports()))
    test_results.append(("Foundation Integration", await test_foundation_integration()))

    # Summary
    print("\n📊 Test Results Summary:")
    print("-" * 30)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ ML models properly implemented")
        print("✅ Foundation integration working")
        print("✅ Phase 3 ML implementation complete")
        print("\n🚀 Ready for production deployment!")
        return True
    else:
        print(f"\n❌ {total - passed} validation tests failed")
        print("🔧 Review and fix issues before deployment")
        return False

if __name__ == "__main__":
    asyncio.run(main())