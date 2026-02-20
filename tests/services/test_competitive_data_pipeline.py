import pytest

pytestmark = pytest.mark.integration

"""
Comprehensive Tests for Competitive Intelligence Data Pipeline

Tests cover:
1. Multi-source data collection and aggregation
2. Real-time competitor monitoring
3. Data quality validation and enrichment
4. Threat detection algorithms
5. Market trend analysis
6. Cache integration and performance
7. Error handling and recovery
8. Data privacy and security
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.competitive_data_pipeline import (
    CompetitiveDataPipeline,
    CompetitorDataPoint,
    DataQualityScore,
    DataSource,
    MarketInsight,
    ThreatAssessment,
    get_competitive_data_pipeline,
)


class TestCompetitiveDataPipeline:
    """Test suite for competitive intelligence data pipeline"""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.get_by_pattern.return_value = []
        return mock_cache

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for AI analysis"""
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Competitive analysis completed successfully"
        mock_llm.generate.return_value = mock_response
        return mock_llm

    @pytest.fixture
    def data_pipeline(self, mock_cache_service, mock_llm_client):
        """Create data pipeline with mocked dependencies"""
        pipeline = CompetitiveDataPipeline()
        pipeline.cache = mock_cache_service
        pipeline.llm_client = mock_llm_client
        return pipeline

    @pytest.fixture
    def sample_competitor_data(self):
        """Sample competitor data for testing"""
        return {
            "competitor_id": "competitor_001",
            "name": "Elite Properties",
            "website": "https://eliteprops.com",
            "market_areas": ["Rancho Cucamonga", "Upland"],
            "specialties": ["luxury_homes", "investment"],
            "pricing": {"base_commission": 0.025, "premium_commission": 0.03, "discount_rate": 0.1},
            "social_metrics": {"followers": 5500, "engagement_rate": 0.045, "posting_frequency": 12},
            "performance_metrics": {"listings_per_month": 8, "avg_days_on_market": 28, "price_to_list_ratio": 0.98},
        }

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing"""
        return {
            "market_area": "Rancho Cucamonga",
            "price_trends": {"median_price": 750000, "price_change_30d": 0.03, "price_change_90d": 0.08},
            "inventory_metrics": {"total_listings": 245, "new_listings_week": 18, "inventory_change": -0.05},
            "activity_metrics": {"sales_volume": 156, "avg_days_on_market": 32, "price_reductions": 0.15},
        }

    @pytest.mark.asyncio
    async def test_data_collection_initialization(self, data_pipeline):
        """Test data collection system initialization"""
        await data_pipeline.initialize()

        # Verify collectors are registered
        assert len(data_pipeline.data_collectors) > 0
        assert DataSource.MLS_DATA in [collector.source_type for collector in data_pipeline.data_collectors.values()]
        assert DataSource.SOCIAL_MEDIA in [
            collector.source_type for collector in data_pipeline.data_collectors.values()
        ]

    @pytest.mark.asyncio
    async def test_competitor_data_collection(self, data_pipeline, sample_competitor_data):
        """Test competitor data collection from multiple sources"""
        competitor_id = "competitor_001"

        # Mock data collectors to return test data
        mock_collector = AsyncMock()
        mock_collector.source_type = DataSource.MLS_DATA
        mock_collector.collect_data = AsyncMock(
            return_value=[
                CompetitorDataPoint(
                    competitor_id=competitor_id,
                    data_source=DataSource.MLS_DATA,
                    data_type="pricing",
                    raw_data=sample_competitor_data["pricing"],
                    collected_at=datetime.now(),
                    confidence_score=0.9,
                )
            ]
        )
        data_pipeline.data_collectors = {"mls": mock_collector}

        data_points = await data_pipeline.collect_competitor_data(competitor_id, data_sources=[DataSource.MLS_DATA])

        assert len(data_points) > 0
        assert data_points[0].competitor_id == competitor_id
        assert data_points[0].confidence_score >= 0.8

    @pytest.mark.asyncio
    async def test_market_trend_analysis(self, data_pipeline, sample_market_data):
        """Test market trend analysis and insight generation"""
        market_area = "Rancho Cucamonga"

        insights = await data_pipeline.analyze_market_trends(market_area=market_area, time_period=30)

        assert isinstance(insights, list)
        assert len(insights) > 0

        # Verify insight structure
        for insight in insights:
            assert hasattr(insight, "insight_type")
            assert hasattr(insight, "confidence_score")
            assert hasattr(insight, "market_area")
            assert insight.confidence_score >= 0.0
            assert insight.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_threat_detection_algorithms(self, data_pipeline, sample_competitor_data):
        """Test competitive threat detection algorithms"""
        competitor_data = [
            CompetitorDataPoint(
                competitor_id="comp_001",
                data_source=DataSource.PRICE_MONITORING,
                data_type="pricing_change",
                raw_data={"price_reduction": 0.15, "urgency": "high"},
                collected_at=datetime.now(),
                confidence_score=0.95,
            )
        ]

        threats = await data_pipeline.detect_competitive_threats(competitor_data)

        assert isinstance(threats, list)
        for threat in threats:
            assert hasattr(threat, "threat_level")
            assert hasattr(threat, "competitor_id")
            assert hasattr(threat, "threat_description")
            assert hasattr(threat, "recommended_response")

    @pytest.mark.asyncio
    async def test_data_quality_validation(self, data_pipeline):
        """Test data quality validation and scoring"""
        # Test high quality data
        high_quality_data = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.MLS_DATA,
            data_type="pricing",
            raw_data={"commission": 0.025, "verified": True},
            collected_at=datetime.now(),
            confidence_score=0.95,
        )

        quality_score = await data_pipeline.validate_data_quality(high_quality_data)

        assert isinstance(quality_score, DataQualityScore)
        assert quality_score.overall_score >= 0.8
        assert quality_score.accuracy_score > 0.7
        assert quality_score.completeness_score > 0.7

    @pytest.mark.asyncio
    async def test_data_enrichment_pipeline(self, data_pipeline, sample_competitor_data):
        """Test data enrichment with AI analysis"""
        raw_data = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.SOCIAL_MEDIA,
            data_type="social_activity",
            raw_data=sample_competitor_data["social_metrics"],
            collected_at=datetime.now(),
            confidence_score=0.8,
        )

        enriched_data = await data_pipeline.enrich_data_with_ai(raw_data)

        assert enriched_data.competitor_id == raw_data.competitor_id
        assert hasattr(enriched_data, "ai_insights")
        assert enriched_data.confidence_score >= raw_data.confidence_score

    @pytest.mark.asyncio
    async def test_real_time_monitoring_setup(self, data_pipeline):
        """Test real-time monitoring configuration"""
        competitors = ["comp_001", "comp_002", "comp_003"]

        monitoring_active = await data_pipeline.start_real_time_monitoring(competitors)

        assert monitoring_active is True
        assert data_pipeline.monitoring_active is True
        assert len(data_pipeline.monitored_competitors) == len(competitors)

    @pytest.mark.asyncio
    async def test_cache_integration(self, data_pipeline):
        """Test cache integration for performance optimization"""
        cache_key = "competitor_data:comp_001:pricing"
        test_data = {"commission": 0.025, "last_updated": datetime.now().isoformat()}

        # Test cache set
        await data_pipeline.cache_competitor_data(cache_key, test_data, ttl=3600)
        data_pipeline.cache.set.assert_called_with(cache_key, test_data, ttl=3600)

        # Test cache get
        data_pipeline.cache.get.return_value = test_data
        cached_data = await data_pipeline.get_cached_competitor_data(cache_key)

        assert cached_data == test_data

    @pytest.mark.asyncio
    async def test_batch_data_processing(self, data_pipeline):
        """Test batch processing of multiple data sources"""
        batch_size = 50
        data_points = [
            CompetitorDataPoint(
                competitor_id=f"comp_{i:03d}",
                data_source=DataSource.WEB_SCRAPING,
                data_type="general_info",
                raw_data={"index": i},
                collected_at=datetime.now(),
                confidence_score=0.8,
            )
            for i in range(batch_size)
        ]

        processed_results = await data_pipeline.process_data_batch(data_points)

        assert len(processed_results) == batch_size
        assert all(result.get("processed", False) for result in processed_results)

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, data_pipeline):
        """Test error handling during data collection"""
        # Simulate collection failure by making collectors raise
        mock_collector = AsyncMock()
        mock_collector.source_type = DataSource.MLS_DATA
        mock_collector.collect_data = AsyncMock(side_effect=Exception("Collection failed"))
        data_pipeline.data_collectors = {"mls": mock_collector}

        # Should not raise exception, should handle gracefully
        data_points = await data_pipeline.collect_competitor_data(
            "invalid_competitor", data_sources=[DataSource.MLS_DATA]
        )

        # Should return empty list or error indication
        assert isinstance(data_points, list)

    @pytest.mark.asyncio
    async def test_data_aggregation_pipeline(self, data_pipeline):
        """Test data aggregation across multiple sources and time periods"""
        competitor_id = "comp_001"
        time_range = timedelta(days=30)

        aggregated_data = await data_pipeline.aggregate_competitor_data(
            competitor_id=competitor_id, time_range=time_range, aggregation_methods=["average", "trend", "variance"]
        )

        assert "competitor_id" in aggregated_data
        assert "time_range" in aggregated_data
        assert "aggregated_metrics" in aggregated_data
        assert isinstance(aggregated_data["aggregated_metrics"], dict)

    @pytest.mark.asyncio
    async def test_market_comparison_analysis(self, data_pipeline, sample_market_data):
        """Test market comparison and competitive positioning analysis"""
        our_performance = {"market_share": 0.15, "avg_commission": 0.025, "client_satisfaction": 0.92}

        comparison_analysis = await data_pipeline.compare_market_position(
            our_metrics=our_performance, market_data=sample_market_data, competitors=["comp_001", "comp_002"]
        )

        assert "positioning_score" in comparison_analysis
        assert "competitive_advantages" in comparison_analysis
        assert "improvement_areas" in comparison_analysis
        assert isinstance(comparison_analysis["positioning_score"], (int, float))

    @pytest.mark.asyncio
    async def test_data_privacy_compliance(self, data_pipeline):
        """Test data privacy and security compliance"""
        sensitive_data = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.CUSTOMER_FEEDBACK,
            data_type="customer_data",
            raw_data={
                "customer_email": "customer@example.com",
                "phone_number": "+1234567890",
                "review_content": "Great service from competitor",
            },
            collected_at=datetime.now(),
            confidence_score=0.9,
        )

        sanitized_data = await data_pipeline.sanitize_sensitive_data(sensitive_data)

        # Should remove or mask sensitive information
        assert "customer_email" not in str(sanitized_data.raw_data)
        assert "phone_number" not in str(sanitized_data.raw_data)
        # Review content should be preserved but anonymized
        assert sanitized_data.raw_data.get("has_review_content", False)

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, data_pipeline):
        """Test collection and tracking of pipeline performance metrics"""
        metrics = await data_pipeline.get_pipeline_performance_metrics()

        expected_metrics = [
            "data_points_collected_24h",
            "collection_success_rate",
            "average_processing_time",
            "cache_hit_rate",
            "error_rate",
            "data_quality_score",
        ]

        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))

    @pytest.mark.asyncio
    async def test_concurrent_data_collection(self, data_pipeline):
        """Test concurrent data collection from multiple sources"""
        competitors = ["comp_001", "comp_002", "comp_003", "comp_004", "comp_005"]

        # Mock concurrent collection
        with patch.object(data_pipeline, "collect_competitor_data") as mock_collect:
            mock_collect.return_value = [
                CompetitorDataPoint(
                    competitor_id="test",
                    data_source=DataSource.MLS_DATA,
                    data_type="test",
                    raw_data={},
                    collected_at=datetime.now(),
                    confidence_score=0.8,
                )
            ]

            # Run concurrent collection
            tasks = [data_pipeline.collect_competitor_data(comp_id) for comp_id in competitors]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All collections should complete
            assert len(results) == len(competitors)
            assert not any(isinstance(result, Exception) for result in results)

    def test_singleton_pattern(self):
        """Test singleton pattern for data pipeline"""
        pipeline1 = get_competitive_data_pipeline()
        pipeline2 = get_competitive_data_pipeline()

        assert pipeline1 is pipeline2

    @pytest.mark.asyncio
    async def test_data_retention_policies(self, data_pipeline):
        """Test data retention and cleanup policies"""
        # Test data older than retention period
        old_timestamp = datetime.now() - timedelta(days=90)

        cleanup_result = await data_pipeline.cleanup_expired_data(retention_days=30)

        assert "cleaned_records" in cleanup_result
        assert "retained_records" in cleanup_result
        assert isinstance(cleanup_result["cleaned_records"], int)

    @pytest.mark.asyncio
    async def test_alert_generation_integration(self, data_pipeline):
        """Test integration with alert generation system"""
        # High-impact competitive change
        critical_data = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.PRICE_MONITORING,
            data_type="major_price_drop",
            raw_data={
                "price_change": -0.25,  # 25% price drop
                "market_impact": "high",
                "urgency": "immediate",
            },
            collected_at=datetime.now(),
            confidence_score=0.98,
        )

        alert_triggered = await data_pipeline.check_alert_conditions(critical_data)

        assert alert_triggered is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])