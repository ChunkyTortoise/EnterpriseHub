"""
Comprehensive test suite for Predictive Analytics Engine

Tests cover:
- A/B testing framework functionality  
- Behavioral pattern discovery
- Anomaly detection system
- Content personalization engine
- Market timing optimization
- Error handling and fallback behavior
- Performance requirements
- Silent failure detection
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ghl_real_estate_ai.services.predictive_analytics_engine import (
    PredictiveAnalyticsEngine,
    ABTestingFramework,
    BehavioralPatternDiscovery,
    AnomalyDetectionSystem,
    ContentPersonalizationEngine,
    MarketTimingOptimizer,
    BehavioralPattern,
    AnomalyDetection,
    ABTestResult,
    ContentPersonalization,
    MarketTimingAnalysis,
    create_predictive_analytics_engine
)


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        "id": "lead_123",
        "first_name": "Sarah",
        "last_name": "Johnson", 
        "email": "sarah@example.com",
        "source": "website",
        "created_at": datetime.now() - timedelta(days=5),
        "interactions": [
            {
                "type": "email_open",
                "timestamp": datetime.now() - timedelta(days=4),
                "content_type": "property_newsletter"
            },
            {
                "type": "website_visit",
                "timestamp": datetime.now() - timedelta(days=3),
                "page": "property_search",
                "duration": 180
            },
            {
                "type": "email_click",
                "timestamp": datetime.now() - timedelta(days=2),
                "link": "property_details"
            }
        ],
        "demographics": {
            "age_range": "30-40",
            "income_bracket": "high",
            "family_status": "married_with_children"
        },
        "preferences": {
            "property_type": "house",
            "price_range": "500k-800k",
            "location": "downtown",
            "bedrooms": 3
        }
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for A/B testing"""
    return {
        "campaign_id": "campaign_123",
        "name": "Property Newsletter Optimization",
        "description": "Testing subject line variations",
        "variants": [
            {
                "id": "variant_a",
                "name": "Control - Standard Subject",
                "config": {"subject_line": "New Properties Available"}
            },
            {
                "id": "variant_b", 
                "name": "Test - Urgency Subject",
                "config": {"subject_line": "Limited Time: Exclusive Properties"}
            }
        ],
        "target_metric": "email_open_rate",
        "start_date": datetime.now() - timedelta(days=14),
        "end_date": datetime.now() + timedelta(days=14)
    }


class TestPredictiveAnalyticsEngine:
    """Test suite for the main Predictive Analytics Engine"""

    @pytest.fixture
    def engine(self):
        """Create engine instance for testing"""
        return PredictiveAnalyticsEngine()

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine.pattern_discovery is not None
        assert engine.anomaly_detection is not None
        assert engine.ab_testing is not None
        assert engine.content_personalization is not None
        assert engine.market_timing is not None
        assert engine.cache is not None

    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, engine, sample_lead_data):
        """Test comprehensive analytics analysis"""
        result = await engine.run_comprehensive_analysis("lead_123", sample_lead_data)
        
        assert isinstance(result, dict)
        
        # Verify all analysis components are present
        assert "behavioral_patterns" in result
        assert "anomalies" in result
        assert "personalization" in result
        assert "market_timing" in result
        assert "insights" in result
        
        # Verify structure of each component
        assert isinstance(result["behavioral_patterns"], list)
        assert isinstance(result["anomalies"], list) 
        assert isinstance(result["personalization"], ContentPersonalization)
        assert isinstance(result["market_timing"], MarketTimingAnalysis)
        assert isinstance(result["insights"], dict)

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_performance(self, engine, sample_lead_data):
        """Test analysis completes within performance requirements"""
        start_time = time.time()
        result = await engine.run_comprehensive_analysis("lead_perf", sample_lead_data)
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time (<2 seconds)
        assert execution_time < 2.0, f"Analysis took {execution_time:.2f}s, should be <2s"
        
        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_error_handling_invalid_data(self, engine):
        """Test error handling with invalid lead data"""
        invalid_data = {
            "id": None,
            "invalid_field": "corrupted_data",
            "interactions": "not_a_list"
        }
        
        # Should handle gracefully, not raise exception
        result = await engine.run_comprehensive_analysis("lead_invalid", invalid_data)
        
        assert isinstance(result, dict)
        # Should contain fallback/empty results
        assert "behavioral_patterns" in result
        assert "anomalies" in result

    @pytest.mark.asyncio
    async def test_caching_behavior(self, engine, sample_lead_data):
        """Test results are cached properly"""
        with patch.object(engine.cache, 'set') as mock_cache_set:
            await engine.run_comprehensive_analysis("lead_cache", sample_lead_data)
            
            # Verify caching was attempted
            mock_cache_set.assert_called()

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, engine, sample_lead_data):
        """Test performance metrics are tracked"""
        metrics_before = engine.get_performance_metrics()
        
        await engine.run_comprehensive_analysis("lead_metrics", sample_lead_data)
        
        metrics_after = engine.get_performance_metrics()
        
        # Metrics should be updated
        assert "total_analyses" in metrics_after
        assert "average_processing_time" in metrics_after
        assert "component_performance" in metrics_after


class TestABTestingFramework:
    """Test suite for A/B Testing Framework"""

    @pytest.fixture
    def ab_framework(self):
        """Create A/B testing framework instance"""
        return ABTestingFramework()

    @pytest.mark.asyncio
    async def test_create_experiment(self, ab_framework, sample_campaign_data):
        """Test experiment creation"""
        experiment_id = await ab_framework.create_nurture_experiment(sample_campaign_data)
        
        assert isinstance(experiment_id, str)
        assert len(experiment_id) > 0
        
        # Verify experiment is stored
        assert experiment_id in ab_framework.experiments

    @pytest.mark.asyncio
    async def test_assign_lead_to_experiment(self, ab_framework, sample_campaign_data):
        """Test lead assignment to experiment variants"""
        experiment_id = await ab_framework.create_nurture_experiment(sample_campaign_data)
        
        # Assign multiple leads
        assignments = []
        for i in range(100):
            assignment = await ab_framework.assign_lead_to_experiment(
                experiment_id, f"lead_{i}"
            )
            assignments.append(assignment)
        
        # Verify assignments
        assert len(assignments) == 100
        variant_counts = {}
        
        for assignment in assignments:
            assert "variant_id" in assignment
            assert "lead_id" in assignment
            variant_id = assignment["variant_id"]
            variant_counts[variant_id] = variant_counts.get(variant_id, 0) + 1
        
        # Should have roughly even distribution (within reasonable variance)
        assert len(variant_counts) == 2  # Two variants
        for count in variant_counts.values():
            assert 35 <= count <= 65  # Allow 30% variance from 50/50 split

    @pytest.mark.asyncio
    async def test_record_conversion(self, ab_framework, sample_campaign_data):
        """Test conversion recording"""
        experiment_id = await ab_framework.create_nurture_experiment(sample_campaign_data)
        
        # Assign and convert lead
        assignment = await ab_framework.assign_lead_to_experiment(experiment_id, "lead_convert")
        
        success = await ab_framework.record_conversion(
            experiment_id, "lead_convert", "email_open", 0.8
        )
        
        assert success is True
        
        # Verify conversion is recorded
        experiment = ab_framework.experiments[experiment_id]
        assert "lead_convert" in experiment["conversions"]

    @pytest.mark.asyncio 
    async def test_analyze_experiment_results(self, ab_framework, sample_campaign_data):
        """Test experiment results analysis"""
        experiment_id = await ab_framework.create_nurture_experiment(sample_campaign_data)
        
        # Simulate experiment data
        # Variant A: 45 assignments, 15 conversions (33% rate)
        for i in range(45):
            assignment = await ab_framework.assign_lead_to_experiment(
                experiment_id, f"lead_a_{i}", force_variant="variant_a"
            )
            if i < 15:  # First 15 convert
                await ab_framework.record_conversion(
                    experiment_id, f"lead_a_{i}", "email_open", 1.0
                )
        
        # Variant B: 55 assignments, 25 conversions (45% rate) 
        for i in range(55):
            assignment = await ab_framework.assign_lead_to_experiment(
                experiment_id, f"lead_b_{i}", force_variant="variant_b"
            )
            if i < 25:  # First 25 convert
                await ab_framework.record_conversion(
                    experiment_id, f"lead_b_{i}", "email_open", 1.0
                )
        
        results = await ab_framework.analyze_experiment_results(experiment_id)
        
        assert isinstance(results, ABTestResult)
        assert results.experiment_id == experiment_id
        assert results.status == "completed"
        assert len(results.variant_results) == 2
        
        # Verify statistical calculations
        variant_a_result = next(r for r in results.variant_results if r["variant_id"] == "variant_a")
        variant_b_result = next(r for r in results.variant_results if r["variant_id"] == "variant_b")
        
        assert abs(variant_a_result["conversion_rate"] - 0.333) < 0.01  # ~33%
        assert abs(variant_b_result["conversion_rate"] - 0.455) < 0.01  # ~45%
        
        # Winner should be variant B
        assert results.winning_variant == "variant_b"

    @pytest.mark.asyncio
    async def test_statistical_significance_calculation(self, ab_framework):
        """Test statistical significance calculation"""
        # Test with clear significant difference
        is_significant = ab_framework._calculate_significance(
            conversions_a=10, total_a=100,  # 10% rate
            conversions_b=20, total_b=100   # 20% rate
        )
        
        assert isinstance(is_significant, dict)
        assert "is_significant" in is_significant
        assert "p_value" in is_significant
        assert "confidence_interval" in is_significant

    @pytest.mark.asyncio
    async def test_experiment_error_handling(self, ab_framework):
        """Test error handling with invalid experiment operations"""
        # Try to assign to non-existent experiment
        assignment = await ab_framework.assign_lead_to_experiment(
            "invalid_experiment", "lead_test"
        )
        
        assert assignment is None
        
        # Try to record conversion for non-existent experiment
        success = await ab_framework.record_conversion(
            "invalid_experiment", "lead_test", "email_open", 1.0
        )
        
        assert success is False


class TestBehavioralPatternDiscovery:
    """Test suite for Behavioral Pattern Discovery"""

    @pytest.fixture
    def pattern_discovery(self):
        """Create behavioral pattern discovery instance"""
        return BehavioralPatternDiscovery()

    @pytest.mark.asyncio
    async def test_discover_conversion_patterns(self, pattern_discovery, sample_lead_data):
        """Test conversion pattern discovery"""
        patterns = await pattern_discovery.discover_conversion_patterns([sample_lead_data])
        
        assert isinstance(patterns, list)
        
        for pattern in patterns:
            assert isinstance(pattern, BehavioralPattern)
            assert pattern.pattern_type in ["engagement", "timeline", "communication", "seasonal"]
            assert pattern.confidence > 0
            assert pattern.lead_ids is not None
            assert len(pattern.description) > 0

    @pytest.mark.asyncio
    async def test_engagement_pattern_discovery(self, pattern_discovery):
        """Test specific engagement pattern discovery"""
        # Create leads with similar engagement patterns
        leads_data = []
        for i in range(10):
            lead = {
                "id": f"lead_{i}",
                "interactions": [
                    {"type": "email_open", "timestamp": datetime.now() - timedelta(days=1)},
                    {"type": "website_visit", "timestamp": datetime.now() - timedelta(hours=12)},
                    {"type": "email_click", "timestamp": datetime.now() - timedelta(hours=6)}
                ]
            }
            leads_data.append(lead)
        
        patterns = await pattern_discovery.discover_conversion_patterns(leads_data)
        
        # Should discover engagement patterns
        engagement_patterns = [p for p in patterns if p.pattern_type == "engagement"]
        assert len(engagement_patterns) > 0

    @pytest.mark.asyncio
    async def test_timeline_pattern_discovery(self, pattern_discovery):
        """Test timeline pattern discovery"""
        # Create leads with similar timeline patterns
        leads_data = []
        for i in range(8):
            lead = {
                "id": f"timeline_lead_{i}",
                "created_at": datetime.now() - timedelta(days=14),
                "interactions": [
                    {"type": "inquiry", "timestamp": datetime.now() - timedelta(days=14)},
                    {"type": "property_view", "timestamp": datetime.now() - timedelta(days=10)},
                    {"type": "conversion", "timestamp": datetime.now() - timedelta(days=7)}
                ]
            }
            leads_data.append(lead)
        
        patterns = await pattern_discovery.discover_conversion_patterns(leads_data)
        
        # Should discover timeline patterns
        timeline_patterns = [p for p in patterns if p.pattern_type == "timeline"]
        assert len(timeline_patterns) > 0

    @pytest.mark.asyncio
    async def test_pattern_discovery_empty_data(self, pattern_discovery):
        """Test pattern discovery with empty data"""
        patterns = await pattern_discovery.discover_conversion_patterns([])
        
        assert isinstance(patterns, list)
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_pattern_discovery_insufficient_data(self, pattern_discovery):
        """Test pattern discovery with insufficient data"""
        minimal_leads = [{"id": "lead_1", "interactions": []}]
        
        patterns = await pattern_discovery.discover_conversion_patterns(minimal_leads)
        
        assert isinstance(patterns, list)
        # May return empty list or low-confidence patterns


class TestAnomalyDetectionSystem:
    """Test suite for Anomaly Detection System"""

    @pytest.fixture
    def anomaly_detector(self):
        """Create anomaly detection system instance"""
        return AnomalyDetectionSystem()

    @pytest.mark.asyncio
    async def test_detect_lead_anomalies(self, anomaly_detector, sample_lead_data):
        """Test lead anomaly detection"""
        anomalies = await anomaly_detector.detect_lead_anomalies(sample_lead_data)
        
        assert isinstance(anomalies, list)
        
        for anomaly in anomalies:
            assert isinstance(anomaly, AnomalyDetection)
            assert anomaly.anomaly_type in ["statistical", "behavioral", "engagement"]
            assert 0 <= anomaly.severity_score <= 1
            assert len(anomaly.description) > 0
            assert isinstance(anomaly.recommended_actions, list)

    @pytest.mark.asyncio
    async def test_statistical_anomaly_detection(self, anomaly_detector):
        """Test statistical anomaly detection"""
        # Create lead with unusual statistics
        anomalous_lead = {
            "id": "anomaly_lead",
            "interactions": [
                {"type": "email_open", "timestamp": datetime.now()} for _ in range(100)
            ],  # Unusually high email opens
            "engagement_score": 0.99,  # Unusually high engagement
            "response_time": 0.5  # Unusually fast response
        }
        
        anomalies = await anomaly_detector.detect_lead_anomalies(anomalous_lead)
        
        # Should detect statistical anomalies
        statistical_anomalies = [a for a in anomalies if a.anomaly_type == "statistical"]
        assert len(statistical_anomalies) > 0

    @pytest.mark.asyncio
    async def test_behavioral_anomaly_detection(self, anomaly_detector):
        """Test behavioral anomaly detection"""
        # Create lead with unusual behavior
        behavioral_lead = {
            "id": "behavioral_lead",
            "interactions": [
                {"type": "website_visit", "timestamp": datetime.now() - timedelta(hours=i), 
                 "duration": 3600} for i in range(24)
            ],  # Visiting every hour for 24 hours (unusual)
            "browsing_pattern": "unusual"
        }
        
        anomalies = await anomaly_detector.detect_lead_anomalies(behavioral_lead)
        
        # Should detect behavioral anomalies
        behavioral_anomalies = [a for a in anomalies if a.anomaly_type == "behavioral"]
        assert len(behavioral_anomalies) > 0

    @pytest.mark.asyncio
    async def test_anomaly_detection_normal_lead(self, anomaly_detector, sample_lead_data):
        """Test anomaly detection on normal lead (should find few/no anomalies)"""
        anomalies = await anomaly_detector.detect_lead_anomalies(sample_lead_data)
        
        # Normal lead should have few or no high-severity anomalies
        high_severity_anomalies = [a for a in anomalies if a.severity_score > 0.7]
        assert len(high_severity_anomalies) <= 1


class TestContentPersonalizationEngine:
    """Test suite for Content Personalization Engine"""

    @pytest.fixture
    def personalization_engine(self):
        """Create content personalization engine instance"""
        return ContentPersonalizationEngine()

    @pytest.mark.asyncio
    async def test_generate_personalized_content(self, personalization_engine, sample_lead_data):
        """Test personalized content generation"""
        result = await personalization_engine.generate_personalized_content(
            "lead_123", sample_lead_data, "email_newsletter"
        )
        
        assert isinstance(result, ContentPersonalization)
        assert result.lead_id == "lead_123"
        assert result.content_type == "email_newsletter"
        assert len(result.personalized_content) > 0
        assert 0 <= result.relevance_score <= 1
        assert isinstance(result.personalization_factors, list)
        assert result.optimal_send_time is not None

    @pytest.mark.asyncio
    async def test_personalization_factors_analysis(self, personalization_engine, sample_lead_data):
        """Test personalization factors are correctly identified"""
        result = await personalization_engine.generate_personalized_content(
            "lead_123", sample_lead_data, "property_recommendation"
        )
        
        factors = result.personalization_factors
        
        # Should identify key personalization factors
        factor_types = [factor["factor"] for factor in factors]
        expected_factors = ["demographics", "preferences", "behavior", "timing"]
        
        assert any(factor in factor_types for factor in expected_factors)

    @pytest.mark.asyncio
    async def test_optimal_timing_calculation(self, personalization_engine, sample_lead_data):
        """Test optimal content timing calculation"""
        result = await personalization_engine.generate_personalized_content(
            "lead_123", sample_lead_data, "follow_up_email"
        )
        
        optimal_time = result.optimal_send_time
        
        assert isinstance(optimal_time, datetime)
        # Should be a reasonable future time (within next 7 days)
        assert optimal_time > datetime.now()
        assert optimal_time < datetime.now() + timedelta(days=7)

    @pytest.mark.asyncio
    async def test_content_personalization_with_claude_integration(self, personalization_engine):
        """Test content personalization with Claude AI integration"""
        with patch.object(personalization_engine, '_generate_content_with_claude') as mock_claude:
            mock_claude.return_value = {
                "content": "Personalized property recommendations for your family",
                "reasoning": "Based on family status and location preferences"
            }
            
            lead_data = {
                "id": "claude_test",
                "preferences": {"property_type": "house", "bedrooms": 3}
            }
            
            result = await personalization_engine.generate_personalized_content(
                "claude_test", lead_data, "property_email"
            )
            
            assert "family" in result.personalized_content.lower()
            mock_claude.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_content_generation(self, personalization_engine):
        """Test fallback when Claude AI is unavailable"""
        with patch.object(personalization_engine, '_generate_content_with_claude') as mock_claude:
            mock_claude.side_effect = Exception("Claude AI unavailable")
            
            lead_data = {"id": "fallback_test", "preferences": {}}
            
            result = await personalization_engine.generate_personalized_content(
                "fallback_test", lead_data, "email"
            )
            
            # Should still generate content using fallback
            assert isinstance(result, ContentPersonalization)
            assert len(result.personalized_content) > 0
            assert result.relevance_score < 0.7  # Lower score for fallback


class TestMarketTimingOptimizer:
    """Test suite for Market Timing Optimizer"""

    @pytest.fixture
    def market_optimizer(self):
        """Create market timing optimizer instance"""
        return MarketTimingOptimizer()

    @pytest.mark.asyncio
    async def test_analyze_market_timing(self, market_optimizer, sample_lead_data):
        """Test market timing analysis"""
        analysis = await market_optimizer.analyze_market_timing(
            "lead_123", sample_lead_data, "buyer"
        )
        
        assert isinstance(analysis, MarketTimingAnalysis)
        assert analysis.lead_id == "lead_123"
        assert analysis.market_role in ["buyer", "seller"]
        assert 0 <= analysis.timing_score <= 1
        assert analysis.optimal_action_window is not None
        assert isinstance(analysis.market_indicators, dict)
        assert isinstance(analysis.recommendations, list)
        assert len(analysis.recommendations) > 0

    @pytest.mark.asyncio
    async def test_buyer_timing_analysis(self, market_optimizer):
        """Test timing analysis for buyers"""
        buyer_data = {
            "id": "buyer_123",
            "preferences": {"price_range": "500k-700k", "location": "downtown"},
            "urgency": "high",
            "financing": "approved"
        }
        
        analysis = await market_optimizer.analyze_market_timing(
            "buyer_123", buyer_data, "buyer"
        )
        
        assert analysis.market_role == "buyer"
        
        # Should have buyer-specific recommendations
        recommendations_text = " ".join(analysis.recommendations).lower()
        buyer_keywords = ["buy", "offer", "properties", "market"]
        assert any(keyword in recommendations_text for keyword in buyer_keywords)

    @pytest.mark.asyncio
    async def test_seller_timing_analysis(self, market_optimizer):
        """Test timing analysis for sellers"""
        seller_data = {
            "id": "seller_123",
            "property_type": "house",
            "location": "suburbs", 
            "current_value": 650000,
            "urgency": "moderate"
        }
        
        analysis = await market_optimizer.analyze_market_timing(
            "seller_123", seller_data, "seller"
        )
        
        assert analysis.market_role == "seller"
        
        # Should have seller-specific recommendations
        recommendations_text = " ".join(analysis.recommendations).lower()
        seller_keywords = ["sell", "list", "price", "marketing"]
        assert any(keyword in recommendations_text for keyword in seller_keywords)

    @pytest.mark.asyncio
    async def test_market_indicators_analysis(self, market_optimizer, sample_lead_data):
        """Test market indicators are properly analyzed"""
        analysis = await market_optimizer.analyze_market_timing(
            "indicators_test", sample_lead_data, "buyer"
        )
        
        indicators = analysis.market_indicators
        
        # Should include key market indicators
        expected_indicators = ["inventory_levels", "price_trends", "interest_rates", "season"]
        assert any(indicator in indicators for indicator in expected_indicators)
        
        # Indicator values should be reasonable
        for value in indicators.values():
            if isinstance(value, (int, float)):
                assert -1 <= value <= 1  # Normalized indicators


class TestPredictiveAnalyticsPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    async def test_concurrent_analytics_processing(self, sample_lead_data):
        """Test concurrent analytics processing"""
        engine = PredictiveAnalyticsEngine()
        
        # Process 10 concurrent analytics requests
        tasks = []
        for i in range(10):
            lead_data = {**sample_lead_data, "id": f"concurrent_{i}"}
            task = engine.run_comprehensive_analysis(f"concurrent_{i}", lead_data)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found {len(exceptions)} exceptions during concurrent processing"
        
        # Should complete in reasonable time
        assert total_time < 10.0, f"Concurrent processing took {total_time:.2f}s, should be <10s"
        
        # All results should be valid
        for result in results:
            assert isinstance(result, dict)
            assert "behavioral_patterns" in result

    @pytest.mark.asyncio
    async def test_large_dataset_processing(self):
        """Test processing large datasets"""
        pattern_discovery = BehavioralPatternDiscovery()
        
        # Generate large dataset
        large_dataset = []
        for i in range(1000):
            lead = {
                "id": f"large_dataset_lead_{i}",
                "created_at": datetime.now() - timedelta(days=i % 30),
                "interactions": [
                    {"type": "email_open", "timestamp": datetime.now() - timedelta(days=i % 10)},
                    {"type": "website_visit", "timestamp": datetime.now() - timedelta(days=i % 5)}
                ]
            }
            large_dataset.append(lead)
        
        start_time = time.time()
        patterns = await pattern_discovery.discover_conversion_patterns(large_dataset)
        processing_time = time.time() - start_time
        
        # Should complete in reasonable time (<30s for 1000 leads)
        assert processing_time < 30.0, f"Large dataset processing took {processing_time:.2f}s, should be <30s"
        
        assert isinstance(patterns, list)
        # Should discover some patterns from large dataset
        assert len(patterns) > 0


class TestPredictiveAnalyticsIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates engine correctly"""
        engine = await create_predictive_analytics_engine()
        
        assert isinstance(engine, PredictiveAnalyticsEngine)
        assert engine.pattern_discovery is not None
        assert engine.ab_testing is not None

    @pytest.mark.asyncio
    async def test_cache_service_integration(self):
        """Test integration with cache service"""
        from ghl_real_estate_ai.services.cache_service import CacheService
        
        engine = PredictiveAnalyticsEngine()
        assert isinstance(engine.cache, CacheService)

    @pytest.mark.asyncio
    async def test_memory_service_integration(self, sample_lead_data):
        """Test integration with memory service"""
        engine = PredictiveAnalyticsEngine()
        
        # Mock memory service for historical data
        with patch('ghl_real_estate_ai.services.memory_service.MemoryService') as mock_memory:
            mock_memory.return_value.get_behavioral_history.return_value = []
            
            result = await engine.run_comprehensive_analysis("integration_test", sample_lead_data)
            assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])