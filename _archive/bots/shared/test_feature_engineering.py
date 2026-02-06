#!/usr/bin/env python3
"""
Comprehensive Test Suite for Jorge Feature Engineering Pipeline

Tests all 28 ML features, performance targets, and sklearn compatibility.
Validates integration with LeadIntelligenceOptimized and JorgeBusinessRules.

Author: Claude Code Assistant
Created: January 23, 2026
"""

import unittest
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import warnings

# Suppress warnings during testing
warnings.filterwarnings("ignore")

# Import the feature engineering system
from feature_engineering import (
    FeatureEngineering, 
    JorgeFeaturePipeline,
    FeatureSchema,
    AdvancedTextAnalyzer,
    MarketContextAnalyzer,
    FeatureMetadata,
    FeatureCategory,
    create_sample_lead_data,
    benchmark_feature_extraction
)


class TestFeatureSchema(unittest.TestCase):
    """Test feature schema definition and validation"""
    
    def setUp(self):
        self.schema = FeatureSchema()
    
    def test_feature_count(self):
        """Test that exactly 28 features are defined"""
        all_features = self.schema.get_all_features()
        self.assertEqual(len(all_features), 28, "Should have exactly 28 features")
    
    def test_feature_type_counts(self):
        """Test feature type distribution (8 numerical, 12 categorical, 8 boolean)"""
        numerical = self.schema.get_features_by_type('numerical')
        categorical = self.schema.get_features_by_type('categorical') 
        boolean = self.schema.get_features_by_type('boolean')
        
        self.assertEqual(len(numerical), 8, "Should have 8 numerical features")
        self.assertEqual(len(categorical), 12, "Should have 12 categorical features")
        self.assertEqual(len(boolean), 8, "Should have 8 boolean features")
    
    def test_feature_names_unique(self):
        """Test that all feature names are unique"""
        names = self.schema.get_feature_names()
        self.assertEqual(len(names), len(set(names)), "Feature names should be unique")
    
    def test_feature_metadata_completeness(self):
        """Test that all features have complete metadata"""
        for feature in self.schema.get_all_features():
            self.assertIsNotNone(feature.name, "Feature name required")
            self.assertIsNotNone(feature.feature_type, "Feature type required")
            self.assertIsNotNone(feature.category, "Feature category required")
            self.assertIsNotNone(feature.description, "Feature description required")
            self.assertIn(feature.feature_type, ['numerical', 'categorical', 'boolean'])
    
    def test_feature_categories(self):
        """Test that features are properly categorized"""
        categories = set()
        for feature in self.schema.get_all_features():
            categories.add(feature.category)
        
        # Should have features across multiple categories
        self.assertGreater(len(categories), 3, "Should have diverse feature categories")


class TestAdvancedTextAnalyzer(unittest.TestCase):
    """Test advanced text analysis functionality"""
    
    def setUp(self):
        self.analyzer = AdvancedTextAnalyzer()
    
    def test_communication_style_analysis(self):
        """Test communication style detection"""
        # Formal communication
        formal_text = "Dear Sir, I would like to inquire about properties. Thank you for your assistance."
        formal_result = self.analyzer.analyze_communication_style(formal_text)
        self.assertEqual(formal_result['style'], 'formal')
        self.assertGreater(formal_result['formality_score'], 0.6)
        
        # Casual communication
        casual_text = "Hey! Looking for a place, nothing too fancy. Let me know what you got."
        casual_result = self.analyzer.analyze_communication_style(casual_text)
        self.assertEqual(casual_result['style'], 'casual')
        self.assertLess(casual_result['formality_score'], 0.4)
    
    def test_urgency_signal_extraction(self):
        """Test urgency signal detection"""
        # High urgency
        urgent_text = "URGENT! Need to find a house immediately, ASAP!"
        urgent_result = self.analyzer.extract_urgency_signals(urgent_text)
        self.assertTrue(urgent_result['has_urgency_signals'])
        self.assertGreater(urgent_result['urgency_score'], 0.5)
        
        # No urgency
        calm_text = "Just browsing properties when I have time."
        calm_result = self.analyzer.extract_urgency_signals(calm_text)
        self.assertFalse(calm_result['has_urgency_signals'])
        self.assertLess(calm_result['urgency_score'], 0.3)
    
    def test_decision_stage_identification(self):
        """Test decision stage identification"""
        test_cases = [
            ("Looking at different neighborhoods", "exploration"),
            ("Comparing prices and features", "evaluation"), 
            ("Ready to make an offer", "commitment"),
            ("Negotiating the final terms", "negotiation")
        ]
        
        for text, expected_stage in test_cases:
            stage = self.analyzer.identify_decision_stage(text)
            self.assertEqual(stage, expected_stage, f"Failed for text: '{text}'")
    
    def test_empty_text_handling(self):
        """Test handling of empty or None text"""
        results = self.analyzer.analyze_communication_style(None)
        self.assertEqual(results['style'], 'unknown')
        
        urgency = self.analyzer.extract_urgency_signals("")
        self.assertEqual(urgency['urgency_score'], 0.0)
        
        stage = self.analyzer.identify_decision_stage("")
        self.assertEqual(stage, 'unknown')


class TestMarketContextAnalyzer(unittest.TestCase):
    """Test market context analysis"""
    
    def setUp(self):
        self.analyzer = MarketContextAnalyzer()
    
    def test_seasonal_context(self):
        """Test seasonal market context analysis"""
        # Spring season (high activity)
        spring_date = datetime(2026, 4, 15)
        spring_context = self.analyzer.get_seasonal_context(spring_date)
        self.assertEqual(spring_context['season'], 'spring')
        self.assertTrue(spring_context['is_peak_season'])
        self.assertGreater(spring_context['seasonal_activity_score'], 0.8)
        
        # Winter season (low activity)
        winter_date = datetime(2026, 1, 15)
        winter_context = self.analyzer.get_seasonal_context(winter_date)
        self.assertEqual(winter_context['season'], 'winter')
        self.assertFalse(winter_context['is_peak_season'])
        self.assertLess(winter_context['seasonal_activity_score'], 0.8)
    
    def test_market_timing_assessment(self):
        """Test market timing assessment"""
        # Immediate timeline in peak season should score high
        immediate_score = self.analyzer.assess_market_timing('immediate')
        self.assertGreater(immediate_score, 0.7)
        
        # Flexible timeline should score lower
        flexible_score = self.analyzer.assess_market_timing('flexible')
        self.assertLess(flexible_score, 0.5)
    
    def test_default_timestamp(self):
        """Test default timestamp handling"""
        context = self.analyzer.get_seasonal_context()
        self.assertIsNotNone(context['season'])
        self.assertIsNotNone(context['seasonal_activity_score'])


class TestFeatureEngineering(unittest.TestCase):
    """Test the main feature engineering class"""
    
    def setUp(self):
        self.feature_engineer = FeatureEngineering()
        self.sample_leads = create_sample_lead_data()
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(len(self.feature_engineer.expected_features), 28)
        self.assertIsNotNone(self.feature_engineer.lead_scorer)
        self.assertIsNotNone(self.feature_engineer.text_analyzer)
        self.assertIsNotNone(self.feature_engineer.market_analyzer)
    
    def test_feature_extraction_performance(self):
        """Test performance target of <30ms"""
        lead_data = self.sample_leads[0]
        
        start_time = time.time()
        features = self.feature_engineer.extract_features_from_record(lead_data)
        extraction_time = time.time() - start_time
        
        self.assertLess(extraction_time, 0.03, "Should extract features in <30ms")
        self.assertEqual(len(features), 28, "Should return exactly 28 features")
    
    def test_feature_extraction_completeness(self):
        """Test that all 28 features are extracted"""
        lead_data = self.sample_leads[0]
        features = self.feature_engineer.extract_features_from_record(lead_data)
        
        self.assertEqual(len(features), 28, "Should extract exactly 28 features")
        self.assertTrue(all(isinstance(f, (int, float)) for f in features), 
                       "All features should be numeric")
    
    def test_sklearn_compatibility(self):
        """Test sklearn transformer interface"""
        # Test fit method
        fitted = self.feature_engineer.fit(self.sample_leads)
        self.assertEqual(fitted, self.feature_engineer, "fit() should return self")
        
        # Test transform method
        X = pd.DataFrame(self.sample_leads)
        transformed = self.feature_engineer.transform(X)
        
        self.assertEqual(transformed.shape[0], len(self.sample_leads))
        self.assertEqual(transformed.shape[1], 28)
        self.assertIsInstance(transformed, np.ndarray)
    
    def test_caching_functionality(self):
        """Test feature extraction caching"""
        lead_data = self.sample_leads[0]
        
        # First extraction
        start_time = time.time()
        features1 = self.feature_engineer.extract_features_from_record(lead_data)
        first_time = time.time() - start_time
        
        # Second extraction (should use cache)
        start_time = time.time()
        features2 = self.feature_engineer.extract_features_from_record(lead_data)
        second_time = time.time() - start_time
        
        # Results should be identical
        np.testing.assert_array_equal(features1, features2, "Cached results should match")
        
        # Second call should be faster (cache hit)
        self.assertLess(second_time, first_time * 0.5, "Cache should improve performance")
    
    def test_error_handling(self):
        """Test error handling and fallback behavior"""
        # Invalid input data
        invalid_data = {'invalid': 'data'}
        features = self.feature_engineer.extract_features_from_record(invalid_data)
        
        self.assertEqual(len(features), 28, "Should return default features on error")
        self.assertTrue(all(isinstance(f, (int, float)) for f in features))
    
    def test_feature_validation(self):
        """Test feature validation functionality"""
        lead_data = self.sample_leads[0]
        
        # Extract features as dict for validation testing
        with patch.object(self.feature_engineer, '_extract_all_features') as mock_extract:
            mock_features = {
                'avg_response_time_minutes': 5.5,
                'budget_specificity_score': 0.8,
                'has_specific_budget': True,
                'timeline_category': 'immediate',
                # Missing some features to test validation
            }
            mock_extract.return_value = mock_features
            
            features = self.feature_engineer.extract_features_from_record(lead_data)
            self.assertEqual(len(features), 28, "Should handle missing features")
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics collection"""
        for lead in self.sample_leads:
            self.feature_engineer.extract_features_from_record(lead)
        
        metrics = self.feature_engineer.get_performance_metrics()
        
        self.assertIn('total_extractions', metrics)
        self.assertIn('avg_extraction_time_ms', metrics)
        self.assertIn('performance_target_met', metrics)
        self.assertEqual(metrics['total_extractions'], len(self.sample_leads))


class TestJorgeFeaturePipeline(unittest.TestCase):
    """Test the complete Jorge feature pipeline"""
    
    def setUp(self):
        self.pipeline = JorgeFeaturePipeline()
        self.sample_leads = create_sample_lead_data()
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        self.assertIsNotNone(self.pipeline.feature_engineer)
        self.assertFalse(self.pipeline.is_fitted)
    
    def test_batch_feature_extraction(self):
        """Test batch processing of leads"""
        features_df = self.pipeline.extract_features_batch(self.sample_leads)
        
        self.assertEqual(len(features_df), len(self.sample_leads))
        self.assertEqual(len(features_df.columns), 28)
        self.assertIsInstance(features_df, pd.DataFrame)
    
    def test_training_data_preparation(self):
        """Test preparation of training data"""
        features_matrix, feature_names = self.pipeline.prepare_training_data(self.sample_leads)
        
        self.assertEqual(features_matrix.shape[0], len(self.sample_leads))
        self.assertEqual(features_matrix.shape[1], 28)
        self.assertEqual(len(feature_names), 28)
        self.assertIsInstance(features_matrix, np.ndarray)


class TestIntegrationWithJorgeComponents(unittest.TestCase):
    """Test integration with existing Jorge components"""
    
    def setUp(self):
        self.feature_engineer = FeatureEngineering()
    
    def test_lead_intelligence_integration(self):
        """Test integration with LeadIntelligenceOptimized"""
        lead_data = {
            'message': "Pre-approved for $550k, looking in Plano area ASAP",
            'timestamp': datetime.now(),
            'source': 'website_form'
        }
        
        features = self.feature_engineer.extract_features_from_record(lead_data)
        
        # Should extract meaningful features from Jorge's intelligence
        self.assertIsNotNone(features)
        self.assertEqual(len(features), 28)
    
    def test_jorge_business_rules_integration(self):
        """Test integration with Jorge's business rules"""
        high_value_lead = {
            'message': "Cash buyer with $600k budget for Plano home in 30 days",
            'timestamp': datetime.now(),
            'source': 'referral'
        }
        
        features = self.feature_engineer.extract_features_from_record(high_value_lead)
        
        # Jorge fit alignment should be high for this lead
        jorge_fit_index = self.feature_engineer.get_feature_names().index('jorge_fit_alignment')
        jorge_fit_score = features[jorge_fit_index]
        
        self.assertGreater(jorge_fit_score, 0.5, "High-value lead should have good Jorge fit")
    
    def test_market_context_integration(self):
        """Test market context features"""
        lead_data = {
            'message': "Looking for summer move-in",
            'timestamp': datetime(2026, 6, 15),  # Summer timing
            'source': 'social_media'
        }
        
        features = self.feature_engineer.extract_features_from_record(lead_data)
        
        # Should extract seasonal context
        seasonal_index = self.feature_engineer.get_feature_names().index('market_timing_optimal')
        seasonal_feature = features[seasonal_index]
        
        # Summer should be considered optimal timing
        self.assertEqual(seasonal_feature, 1.0, "Summer timing should be optimal")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Test performance benchmarks and scalability"""
    
    def test_30ms_performance_target(self):
        """Test 30ms extraction performance target"""
        benchmark = benchmark_feature_extraction(num_samples=50)
        
        self.assertLess(benchmark['avg_time_per_lead_ms'], 30, 
                       "Should meet 30ms performance target")
        self.assertTrue(benchmark['meets_30ms_target'])
    
    def test_batch_processing_scalability(self):
        """Test scalability with larger batches"""
        # Create larger batch
        large_batch = create_sample_lead_data() * 50  # 150 leads
        
        start_time = time.time()
        pipeline = JorgeFeaturePipeline()
        features_df = pipeline.extract_features_batch(large_batch)
        total_time = time.time() - start_time
        
        avg_time_per_lead = total_time / len(large_batch)
        
        self.assertLess(avg_time_per_lead, 0.05, "Should handle large batches efficiently")
        self.assertEqual(len(features_df), len(large_batch))
    
    def test_memory_usage(self):
        """Test memory efficiency"""
        # This is a basic test - in production would use memory profiling
        import sys
        
        initial_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # Process many leads
        feature_engineer = FeatureEngineering()
        for i in range(100):
            lead_data = {'message': f'Test lead {i}', 'timestamp': datetime.now()}
            features = feature_engineer.extract_features_from_record(lead_data)
        
        # Memory should not grow excessively
        final_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # This is a rough test - exact numbers depend on Python internals
        if final_objects > 0:
            growth_ratio = final_objects / max(initial_objects, 1)
            self.assertLess(growth_ratio, 2.0, "Memory usage should not grow excessively")


class TestFeatureQuality(unittest.TestCase):
    """Test quality and meaningfulness of extracted features"""
    
    def setUp(self):
        self.feature_engineer = FeatureEngineering()
    
    def test_numerical_feature_ranges(self):
        """Test that numerical features have sensible ranges"""
        leads = [
            {'message': 'Budget $400k, timeline 30 days', 'timestamp': datetime.now()},
            {'message': 'No specific budget, flexible timeline', 'timestamp': datetime.now()},
            {'message': 'Pre-approved $800k, need immediately', 'timestamp': datetime.now()}
        ]
        
        for lead in leads:
            features = self.feature_engineer.extract_features_from_record(lead)
            
            # All features should be finite numbers
            self.assertTrue(all(np.isfinite(f) for f in features), 
                           "All features should be finite numbers")
            
            # Most numerical features should be in reasonable ranges (0-1000)
            numerical_features = features[:8]  # First 8 are numerical
            self.assertTrue(all(0 <= f <= 1000 for f in numerical_features),
                           "Numerical features should be in reasonable ranges")
    
    def test_feature_discrimination(self):
        """Test that features can discriminate between different lead types"""
        high_value_lead = {
            'message': 'Pre-approved cash buyer, $700k budget, need house in Plano within 2 weeks',
            'timestamp': datetime.now(),
            'contact_history': [
                {'direction': 'inbound', 'timestamp': datetime.now().isoformat(), 'body': 'Initial'},
                {'direction': 'outbound', 'timestamp': (datetime.now() + timedelta(minutes=2)).isoformat(), 'body': 'Quick response'}
            ]
        }
        
        low_value_lead = {
            'message': 'Just browsing, maybe looking in a few years',
            'timestamp': datetime.now(),
            'contact_history': []
        }
        
        high_features = self.feature_engineer.extract_features_from_record(high_value_lead)
        low_features = self.feature_engineer.extract_features_from_record(low_value_lead)
        
        # Jorge fit alignment should differ significantly
        jorge_fit_idx = self.feature_engineer.get_feature_names().index('jorge_fit_alignment')
        self.assertGreater(high_features[jorge_fit_idx], low_features[jorge_fit_idx],
                          "Features should discriminate between lead quality")
    
    def test_feature_consistency(self):
        """Test feature extraction consistency"""
        lead_data = {
            'message': 'Looking for $500k home in Dallas area within 60 days',
            'timestamp': datetime.now(),
            'source': 'website'
        }
        
        # Extract features multiple times
        features_list = []
        for _ in range(5):
            features = self.feature_engineer.extract_features_from_record(lead_data)
            features_list.append(features)
        
        # Results should be identical (deterministic)
        for i in range(1, len(features_list)):
            np.testing.assert_array_equal(features_list[0], features_list[i],
                                        "Feature extraction should be deterministic")


def run_comprehensive_tests():
    """Run all test suites"""
    test_suites = [
        TestFeatureSchema,
        TestAdvancedTextAnalyzer,
        TestMarketContextAnalyzer,
        TestFeatureEngineering,
        TestJorgeFeaturePipeline,
        TestIntegrationWithJorgeComponents,
        TestPerformanceBenchmarks,
        TestFeatureQuality
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    print("🧪 Running Comprehensive Feature Engineering Test Suite")
    print("=" * 60)
    
    for test_suite in test_suites:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        
        print(f"\n{test_suite.__name__}: {result.testsRun} tests, "
              f"{len(result.failures)} failures, {len(result.errors)} errors")
    
    print("\n" + "=" * 60)
    print(f"📊 TOTAL RESULTS:")
    print(f"   Tests Run: {total_tests}")
    print(f"   Failures: {total_failures}")
    print(f"   Errors: {total_errors}")
    print(f"   Success Rate: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%")
    
    if total_failures + total_errors == 0:
        print("\n✅ ALL TESTS PASSED! Feature engineering pipeline ready for production.")
    else:
        print(f"\n❌ {total_failures + total_errors} test(s) failed. Review issues before deployment.")
    
    return total_failures + total_errors == 0


if __name__ == '__main__':
    # Import garbage collection if available for memory tests
    try:
        import gc
    except ImportError:
        pass
    
    # Run all tests
    success = run_comprehensive_tests()
    
    if success:
        print("\n🚀 Running performance benchmark...")
        benchmark = benchmark_feature_extraction(100)
        
        print("\n📈 Performance Results:")
        print(f"   - Average extraction time: {benchmark['avg_time_per_lead_ms']:.1f}ms")
        print(f"   - Meets 30ms target: {'✅' if benchmark['meets_30ms_target'] else '❌'}")
        print(f"   - Throughput: {benchmark['throughput_per_second']:.1f} leads/second")
        print(f"   - Feature count: {benchmark['feature_count']}")
        print(f"   - Cache hit rate: {benchmark['cache_hit_rate']:.1%}")
    
    exit(0 if success else 1)