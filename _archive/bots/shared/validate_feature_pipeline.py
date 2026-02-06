#!/usr/bin/env python3
"""
Feature Engineering Pipeline Validation Script

This script validates the complete feature engineering pipeline integration
with Jorge's existing components and demonstrates production readiness.

Author: Claude Code Assistant
Created: January 23, 2026
"""

import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_imports():
    """Validate all required imports are available"""
    print("🔍 Validating imports...")
    
    import_results = {}
    
    # Core feature engineering
    try:
        from feature_engineering import FeatureEngineering, JorgeFeaturePipeline, benchmark_feature_extraction
        import_results['feature_engineering'] = "✅ Available"
    except ImportError as e:
        import_results['feature_engineering'] = f"❌ Error: {e}"
    
    # Business rules integration
    try:
        from business_rules import JorgeBusinessRulesEngine, integrate_with_feature_engineering
        import_results['business_rules'] = "✅ Available"
    except ImportError as e:
        import_results['business_rules'] = f"❌ Error: {e}"
    
    # Jorge existing components (if available)
    try:
        from jorge_deployment_package.lead_intelligence_optimized import get_enhanced_lead_intelligence
        import_results['lead_intelligence'] = "✅ Available"
    except ImportError as e:
        import_results['lead_intelligence'] = f"⚠️  Not found (expected in separate package): {e}"
    
    try:
        from jorge_deployment_package.jorge_claude_intelligence import JorgeBusinessRules
        import_results['jorge_business_rules'] = "✅ Available"
    except ImportError as e:
        import_results['jorge_business_rules'] = f"⚠️  Not found (expected in separate package): {e}"
    
    # ML dependencies
    try:
        import sklearn
        import_results['sklearn'] = f"✅ Available (v{sklearn.__version__})"
    except ImportError as e:
        import_results['sklearn'] = f"❌ Required: {e}"
    
    try:
        import numpy as np
        import_results['numpy'] = f"✅ Available (v{np.__version__})"
    except ImportError as e:
        import_results['numpy'] = f"❌ Required: {e}"
    
    try:
        import pandas as pd
        import_results['pandas'] = f"✅ Available (v{pd.__version__})"
    except ImportError as e:
        import_results['pandas'] = f"❌ Required: {e}"
    
    # Print results
    for component, status in import_results.items():
        print(f"   - {component}: {status}")
    
    # Check if critical components are missing
    critical_missing = [k for k, v in import_results.items() 
                       if k in ['feature_engineering', 'business_rules', 'sklearn', 'numpy', 'pandas'] 
                       and v.startswith('❌')]
    
    if critical_missing:
        print(f"\n❌ CRITICAL: Missing required components: {critical_missing}")
        return False
    
    print("\n✅ All critical imports validated!")
    return True


def validate_feature_schema():
    """Validate feature schema completeness"""
    print("\n📋 Validating feature schema...")
    
    try:
        from feature_engineering import FeatureSchema
        
        schema = FeatureSchema()
        all_features = schema.get_all_features()
        
        print(f"   - Total features: {len(all_features)}")
        
        # Count by type
        by_type = {}
        for feature in all_features:
            if feature.feature_type not in by_type:
                by_type[feature.feature_type] = 0
            by_type[feature.feature_type] += 1
        
        print(f"   - Numerical: {by_type.get('numerical', 0)}")
        print(f"   - Categorical: {by_type.get('categorical', 0)}")
        print(f"   - Boolean: {by_type.get('boolean', 0)}")
        
        # Validate target counts
        if (len(all_features) == 28 and 
            by_type.get('numerical', 0) == 8 and
            by_type.get('categorical', 0) == 12 and 
            by_type.get('boolean', 0) == 8):
            print("✅ Feature schema matches specification!")
            return True
        else:
            print("❌ Feature schema doesn't match 8/12/8 specification")
            return False
            
    except Exception as e:
        print(f"❌ Error validating schema: {e}")
        return False


def validate_performance():
    """Validate performance targets"""
    print("\n⏱️  Validating performance targets...")
    
    try:
        from feature_engineering import benchmark_feature_extraction
        
        # Run benchmark with moderate sample size
        results = benchmark_feature_extraction(num_samples=50)
        
        print(f"   - Average extraction time: {results['avg_time_per_lead_ms']:.1f}ms")
        print(f"   - Throughput: {results['throughput_per_second']:.1f} leads/sec")
        print(f"   - Feature count: {results['feature_count']}")
        print(f"   - Cache hit rate: {results['cache_hit_rate']:.1%}")
        
        # Check 30ms target
        meets_target = results['meets_30ms_target']
        if meets_target:
            print("✅ Meets <30ms performance target!")
        else:
            print(f"⚠️  Performance target missed: {results['avg_time_per_lead_ms']:.1f}ms > 30ms")
        
        return meets_target
        
    except Exception as e:
        print(f"❌ Error validating performance: {e}")
        return False


def validate_sklearn_compatibility():
    """Validate sklearn pipeline compatibility"""
    print("\n🔧 Validating sklearn compatibility...")
    
    try:
        from feature_engineering import FeatureEngineering, create_sample_lead_data
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        
        # Create test data
        sample_leads = create_sample_lead_data()
        
        # Test basic transformer interface
        feature_engineer = FeatureEngineering()
        
        # Test fit method
        fitted = feature_engineer.fit(sample_leads)
        assert fitted is feature_engineer, "fit() should return self"
        
        # Test transform method
        transformed = feature_engineer.transform(sample_leads)
        assert isinstance(transformed, np.ndarray), "transform() should return numpy array"
        assert transformed.shape == (len(sample_leads), 28), f"Expected shape ({len(sample_leads)}, 28), got {transformed.shape}"
        
        # Test sklearn pipeline integration
        pipeline = Pipeline([
            ('feature_engineering', FeatureEngineering()),
            ('scaler', StandardScaler())
        ])
        
        # Fit pipeline
        X_transformed = pipeline.fit_transform(sample_leads)
        assert X_transformed.shape == (len(sample_leads), 28), "Pipeline should maintain feature count"
        
        print("✅ sklearn compatibility validated!")
        return True
        
    except Exception as e:
        print(f"❌ Error validating sklearn compatibility: {e}")
        return False


def validate_business_rules_integration():
    """Validate Jorge business rules integration"""
    print("\n🏢 Validating business rules integration...")
    
    try:
        from business_rules import JorgeBusinessRulesEngine, integrate_with_feature_engineering
        
        # Mock lead intelligence data
        sample_intelligence = {
            'lead_score': 78.5,
            'budget_max': 550000,
            'timeline_analysis': '2_months',
            'location_analysis': ['Plano', 'Frisco'],
            'financing_analysis': 'pre_approved',
            'has_specific_budget': True,
            'has_location_preference': True,
            'is_pre_approved': True,
            'urgency': 0.7
        }
        
        # Initialize rules engine
        rules_engine = JorgeBusinessRulesEngine()
        
        # Qualify lead
        qualification = rules_engine.qualify_lead_for_jorge(sample_intelligence)
        
        print(f"   - Qualification Score: {qualification.qualification_score:.1f}/100")
        print(f"   - Priority: {qualification.priority.value}")
        print(f"   - Meets Criteria: {'✅' if qualification.meets_criteria else '❌'}")
        print(f"   - Service Area: {qualification.service_area.value}")
        print(f"   - Commission: ${qualification.estimated_commission:,.0f}")
        
        # Test feature integration
        feature_data = integrate_with_feature_engineering(qualification)
        print(f"   - Feature integration keys: {len(feature_data)}")
        
        print("✅ Business rules integration validated!")
        return True
        
    except Exception as e:
        print(f"❌ Error validating business rules: {e}")
        return False


def validate_end_to_end_workflow():
    """Validate complete end-to-end workflow"""
    print("\n🔄 Validating end-to-end workflow...")
    
    try:
        from feature_engineering import JorgeFeaturePipeline, create_sample_lead_data
        import pandas as pd
        
        # Create test leads
        test_leads = [
            {
                'message': "Pre-approved for $600k, looking in Plano within 30 days for 4BR house",
                'timestamp': datetime.now(),
                'source': 'website_form',
                'contact_history': [
                    {'direction': 'inbound', 'timestamp': datetime.now().isoformat(), 'body': 'Initial inquiry'},
                    {'direction': 'outbound', 'timestamp': (datetime.now() + timedelta(minutes=5)).isoformat(), 'body': 'Quick response'}
                ]
            },
            {
                'message': "Just browsing homes in Dallas area. Budget flexible, maybe next year.",
                'timestamp': datetime.now(),
                'source': 'social_media',
                'contact_history': []
            },
            {
                'message': "URGENT! Cash buyer $750k ready to close in 2 weeks in Frisco area",
                'timestamp': datetime.now(),
                'source': 'referral',
                'contact_history': [
                    {'direction': 'inbound', 'timestamp': datetime.now().isoformat(), 'body': 'Urgent inquiry'}
                ]
            }
        ]
        
        # Initialize pipeline
        pipeline = JorgeFeaturePipeline()
        
        # Process leads
        start_time = time.time()
        features_df = pipeline.extract_features_batch(test_leads)
        processing_time = time.time() - start_time
        
        print(f"   - Processed {len(test_leads)} leads in {processing_time*1000:.1f}ms")
        print(f"   - Features shape: {features_df.shape}")
        print(f"   - Average per lead: {processing_time/len(test_leads)*1000:.1f}ms")
        
        # Validate feature ranges
        print(f"   - Feature ranges valid: {_validate_feature_ranges(features_df)}")
        
        # Test training data preparation
        features_matrix, feature_names = pipeline.prepare_training_data(test_leads)
        print(f"   - Training matrix shape: {features_matrix.shape}")
        print(f"   - Feature names count: {len(feature_names)}")
        
        print("✅ End-to-end workflow validated!")
        return True
        
    except Exception as e:
        print(f"❌ Error in end-to-end validation: {e}")
        return False


def _validate_feature_ranges(features_df):
    """Helper to validate feature value ranges are reasonable"""
    try:
        # Check for NaN or infinite values
        if features_df.isnull().any().any():
            return False
        
        if not features_df.replace([float('inf'), float('-inf')], 0).notna().all().all():
            return False
        
        # Basic range checks (features should be reasonable numbers)
        numeric_cols = features_df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            values = features_df[col]
            if values.min() < -1000 or values.max() > 1000000:
                logger.warning(f"Feature {col} has extreme values: min={values.min()}, max={values.max()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating feature ranges: {e}")
        return False


def validate_error_handling():
    """Validate error handling and edge cases"""
    print("\n🛡️  Validating error handling...")
    
    try:
        from feature_engineering import FeatureEngineering
        
        feature_engineer = FeatureEngineering()
        
        # Test with invalid data
        invalid_cases = [
            {},  # Empty dict
            {'message': None},  # None message
            {'message': ''},  # Empty message
            {'invalid_field': 'test'},  # Wrong fields
            {'message': 'test', 'timestamp': 'invalid_date'},  # Invalid timestamp
        ]
        
        all_passed = True
        for i, invalid_data in enumerate(invalid_cases):
            try:
                features = feature_engineer.extract_features_from_record(invalid_data)
                if len(features) != 28:
                    print(f"   ❌ Invalid case {i}: Expected 28 features, got {len(features)}")
                    all_passed = False
                else:
                    print(f"   ✅ Invalid case {i}: Handled gracefully")
            except Exception as e:
                print(f"   ❌ Invalid case {i}: Unhandled exception: {e}")
                all_passed = False
        
        if all_passed:
            print("✅ Error handling validated!")
        else:
            print("❌ Error handling issues found")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")
        return False


def generate_validation_report():
    """Generate comprehensive validation report"""
    print("\n📊 FEATURE ENGINEERING PIPELINE VALIDATION REPORT")
    print("=" * 60)
    
    validation_results = {}
    
    # Run all validations
    validation_tests = [
        ("Import Validation", validate_imports),
        ("Feature Schema", validate_feature_schema),
        ("Performance Targets", validate_performance),
        ("Sklearn Compatibility", validate_sklearn_compatibility),
        ("Business Rules Integration", validate_business_rules_integration),
        ("End-to-End Workflow", validate_end_to_end_workflow),
        ("Error Handling", validate_error_handling),
    ]
    
    total_passed = 0
    total_tests = len(validation_tests)
    
    for test_name, test_func in validation_tests:
        try:
            result = test_func()
            validation_results[test_name] = result
            if result:
                total_passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            validation_results[test_name] = False
    
    # Generate summary
    print(f"\n" + "=" * 60)
    print(f"📋 VALIDATION SUMMARY")
    print(f"   Tests Passed: {total_passed}/{total_tests}")
    print(f"   Success Rate: {total_passed/total_tests*100:.1f}%")
    
    print(f"\n📝 DETAILED RESULTS:")
    for test_name, result in validation_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   - {test_name}: {status}")
    
    # Overall assessment
    if total_passed == total_tests:
        print(f"\n🎉 ALL VALIDATIONS PASSED!")
        print(f"✅ Feature Engineering Pipeline is PRODUCTION READY")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Deploy to staging environment")
        print(f"   2. Run load testing with production data")
        print(f"   3. Integrate with ML model training pipeline")
        print(f"   4. Set up monitoring and alerting")
        return True
    else:
        failed_tests = [name for name, result in validation_results.items() if not result]
        print(f"\n⚠️  VALIDATION ISSUES FOUND")
        print(f"❌ Failed tests: {failed_tests}")
        print(f"\n🔧 Required Actions:")
        print(f"   1. Fix failed validation tests")
        print(f"   2. Re-run validation script")
        print(f"   3. Review error logs for specific issues")
        return False


def main():
    """Main validation entry point"""
    print("🧪 Jorge Feature Engineering Pipeline Validation")
    print("🎯 Target: 28 ML features with <30ms extraction")
    print("🔗 Integration: LeadIntelligenceOptimized + JorgeBusinessRules")
    print("⚡ Performance: sklearn compatible, XGBoost ready")
    print()
    
    try:
        success = generate_validation_report()
        
        if success:
            # Run final performance demo
            print(f"\n🚀 PERFORMANCE DEMONSTRATION:")
            from feature_engineering import benchmark_feature_extraction
            demo_results = benchmark_feature_extraction(25)
            
            print(f"   📈 Benchmark Results (25 leads):")
            print(f"      - Avg time per lead: {demo_results['avg_time_per_lead_ms']:.1f}ms")
            print(f"      - Total throughput: {demo_results['throughput_per_second']:.1f} leads/sec")
            print(f"      - Performance target: {'✅ MET' if demo_results['meets_30ms_target'] else '❌ MISSED'}")
            print(f"      - Feature extraction: {demo_results['feature_count']} features")
            print(f"      - Cache efficiency: {demo_results['cache_hit_rate']:.1%}")
            
        return success
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during validation: {e}")
        logger.exception("Critical validation error")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)