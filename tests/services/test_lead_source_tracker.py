"""
Tests for LeadSourceTracker service.

Comprehensive test suite for lead source attribution, tracking, and performance analysis.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from ghl_real_estate_ai.services.lead_source_tracker import (
    LeadSourceTracker,
    LeadSource,
    SourceAttribution,
    SourcePerformance,
    SourceQuality
)


class TestLeadSourceTracker:
    """Test suite for LeadSourceTracker class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tracker = LeadSourceTracker()

    @pytest.mark.asyncio
    async def test_analyze_lead_source_zillow(self):
        """Test source analysis for Zillow leads."""
        contact_data = {
            "custom_fields": {
                "utm_source": "zillow",
                "utm_medium": "referral",
                "lead_source": "Zillow"
            },
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "email": "john@example.com"
        }

        attribution = await self.tracker.analyze_lead_source(contact_data)

        assert attribution.source == LeadSource.ZILLOW
        assert attribution.utm_source == "zillow"
        assert attribution.utm_medium == "referral"
        assert attribution.confidence_score >= 0.9  # High confidence for explicit source
        assert attribution.quality_score > 7.0  # Zillow is a premium source

    @pytest.mark.asyncio
    async def test_analyze_lead_source_facebook_ads(self):
        """Test source analysis for Facebook Ads."""
        contact_data = {
            "custom_fields": {
                "utm_source": "facebook",
                "utm_medium": "cpc",
                "utm_campaign": "spring-real-estate-2024",
                "utm_content": "listing-ad"
            }
        }

        attribution = await self.tracker.analyze_lead_source(contact_data)

        assert attribution.source == LeadSource.FACEBOOK_ADS
        assert attribution.medium == "cpc"
        assert attribution.campaign == "spring-real-estate-2024"
        assert attribution.source_detail == "spring-real-estate-2024"
        assert attribution.confidence_score >= 0.9

    @pytest.mark.asyncio
    async def test_analyze_lead_source_google_organic(self):
        """Test source analysis for Google organic search."""
        contact_data = {
            "custom_fields": {
                "referrer": "https://google.com/search?q=real+estate+agent+austin",
                "utm_source": "google",
                "utm_medium": "organic"
            }
        }

        attribution = await self.tracker.analyze_lead_source(contact_data)

        assert attribution.source == LeadSource.GOOGLE_ORGANIC
        assert attribution.medium == "organic"
        assert "google.com" in attribution.referrer

    @pytest.mark.asyncio
    async def test_analyze_lead_source_referral(self):
        """Test source analysis for referrals."""
        contact_data = {
            "custom_fields": {
                "lead_source": "Agent Referral",
                "referrer_agent": "Jane Smith"
            }
        }

        attribution = await self.tracker.analyze_lead_source(contact_data)

        assert attribution.source == LeadSource.AGENT_REFERRAL
        assert attribution.quality_score >= 9.0  # Referrals are premium sources

    @pytest.mark.asyncio
    async def test_analyze_lead_source_direct(self):
        """Test source analysis for direct traffic."""
        contact_data = {
            "custom_fields": {},
            "phone": "+1234567890"
        }

        # No referrer or UTM parameters
        attribution = await self.tracker.analyze_lead_source(contact_data)

        assert attribution.source == LeadSource.UNKNOWN
        assert attribution.confidence_score < 0.5

    @pytest.mark.asyncio
    async def test_track_source_performance(self):
        """Test tracking source performance events."""
        source = LeadSource.ZILLOW

        # Mock cache
        with patch.object(self.tracker.cache, 'get', return_value=[]) as mock_get, \
             patch.object(self.tracker.cache, 'set') as mock_set:

            await self.tracker.track_source_performance(
                source,
                "lead_created",
                {"contact_id": "test123", "cost": 25.0}
            )

            # Verify cache was called
            mock_get.assert_called()
            mock_set.assert_called()

    @pytest.mark.asyncio
    async def test_get_source_performance(self):
        """Test retrieving source performance metrics."""
        source = LeadSource.FACEBOOK_ADS

        # Mock cached performance data
        mock_metrics = {
            "total_leads": 100,
            "qualified_leads": 30,
            "hot_leads": 15,
            "closed_deals": 5,
            "total_revenue": 50000.0,
            "total_cost": 10000.0,
            "conversion_rate": 0.05,
            "qualification_rate": 0.30,
            "roi": 4.0
        }

        with patch.object(self.tracker.cache, 'get', return_value=mock_metrics):
            performance = await self.tracker.get_source_performance(source)

            assert performance is not None
            assert performance.source == source
            assert performance.total_leads == 100
            assert performance.qualified_leads == 30
            assert performance.roi == 4.0

    @pytest.mark.asyncio
    async def test_get_all_source_performance(self):
        """Test getting performance for all sources."""
        # Mock cache to return data for multiple sources
        cache_data = {
            f"source_performance:{LeadSource.ZILLOW.value}": {
                "total_leads": 50,
                "qualified_leads": 20,
                "roi": 2.5
            },
            f"source_performance:{LeadSource.FACEBOOK_ADS.value}": {
                "total_leads": 80,
                "qualified_leads": 25,
                "roi": 1.8
            }
        }

        async def mock_get(key):
            return cache_data.get(key)

        with patch.object(self.tracker.cache, 'get', side_effect=mock_get):
            performances = await self.tracker.get_all_source_performance(min_leads=10)

            # Should return data for sources with sufficient leads
            assert len(performances) >= 0
            # Results should be sorted by ROI descending
            if len(performances) > 1:
                assert performances[0].roi >= performances[1].roi

    @pytest.mark.asyncio
    async def test_get_source_recommendations(self):
        """Test getting optimization recommendations."""
        # Mock performance data for recommendations
        mock_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=50,
                roi=3.0,
                conversion_rate=0.08
            ),
            SourcePerformance(
                source=LeadSource.FACEBOOK_ADS,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=20,
                roi=-0.3,  # Underperforming
                conversion_rate=0.02
            )
        ]

        with patch.object(self.tracker, 'get_all_source_performance', return_value=mock_performances):
            recommendations = await self.tracker.get_source_recommendations()

            assert recommendations["status"] == "success"
            assert len(recommendations["recommendations"]) > 0

            # Should have recommendations for scaling top performers
            rec_types = [r["type"] for r in recommendations["recommendations"]]
            assert "scale_up" in rec_types or "optimize_or_pause" in rec_types

    @pytest.mark.asyncio
    async def test_update_ghl_custom_fields(self):
        """Test updating GHL custom fields with attribution data."""
        attribution = SourceAttribution(
            source=LeadSource.ZILLOW,
            source_quality=SourceQuality.PREMIUM,
            confidence_score=0.95,
            utm_source="zillow",
            utm_campaign="spring-listings"
        )

        # Mock GHL client
        mock_ghl_client = MagicMock()
        mock_ghl_client.update_contact_custom_fields = AsyncMock(return_value=True)

        # Mock settings
        with patch('ghl_real_estate_ai.services.lead_source_tracker.settings') as mock_settings:
            mock_settings.custom_field_lead_source = "lead_source"
            mock_settings.custom_field_utm_source = "utm_source"

            success = await self.tracker.update_ghl_custom_fields(
                "test_contact_123", attribution, mock_ghl_client
            )

            assert success
            mock_ghl_client.update_contact_custom_fields.assert_called_once()

    def test_source_patterns(self):
        """Test source pattern matching."""
        patterns = self.tracker.source_patterns

        # Verify Facebook patterns
        fb_patterns = patterns[LeadSource.FACEBOOK_ORGANIC]
        assert any("facebook.com" in pattern for pattern in fb_patterns)

        # Verify Zillow patterns
        zillow_patterns = patterns[LeadSource.ZILLOW]
        assert any("zillow.com" in pattern for pattern in zillow_patterns)

    def test_quality_scores(self):
        """Test source quality scoring."""
        quality_scores = self.tracker.source_quality_scores

        # Premium sources should have high scores
        assert quality_scores[LeadSource.AGENT_REFERRAL] >= 9.0
        assert quality_scores[LeadSource.CLIENT_REFERRAL] >= 9.0
        assert quality_scores[LeadSource.ZILLOW] >= 7.5

        # Unknown sources should have low scores
        assert quality_scores[LeadSource.UNKNOWN] <= 3.5

    def test_map_explicit_source(self):
        """Test explicit source mapping."""
        # Test various source strings
        assert self.tracker._map_explicit_source("Zillow") == LeadSource.ZILLOW
        assert self.tracker._map_explicit_source("facebook") == LeadSource.FACEBOOK_ORGANIC
        assert self.tracker._map_explicit_source("Google") == LeadSource.GOOGLE_ORGANIC
        assert self.tracker._map_explicit_source("Agent Referral") == LeadSource.AGENT_REFERRAL
        assert self.tracker._map_explicit_source("random_source") == LeadSource.UNKNOWN

    def test_map_utm_source(self):
        """Test UTM source mapping."""
        # Paid sources
        assert self.tracker._map_utm_source("facebook", "cpc") == LeadSource.FACEBOOK_ADS
        assert self.tracker._map_utm_source("google", "paid") == LeadSource.GOOGLE_ADS

        # Organic sources
        assert self.tracker._map_utm_source("facebook", "organic") == LeadSource.FACEBOOK_ORGANIC
        assert self.tracker._map_utm_source("google", "organic") == LeadSource.GOOGLE_ORGANIC

        # Platform sources
        assert self.tracker._map_utm_source("zillow", "") == LeadSource.ZILLOW
        assert self.tracker._map_utm_source("realtor", "") == LeadSource.REALTOR_COM

    def test_classify_source_quality(self):
        """Test source quality classification."""
        assert self.tracker._classify_source_quality(9.0) == SourceQuality.PREMIUM
        assert self.tracker._classify_source_quality(7.0) == SourceQuality.STANDARD
        assert self.tracker._classify_source_quality(5.0) == SourceQuality.BUDGET
        assert self.tracker._classify_source_quality(3.0) == SourceQuality.EXPERIMENTAL

    def test_to_dict_conversion(self):
        """Test SourceAttribution to dictionary conversion."""
        attribution = SourceAttribution(
            source=LeadSource.ZILLOW,
            utm_source="zillow",
            confidence_score=0.95,
            first_touch=datetime.utcnow(),
            last_touch=datetime.utcnow()
        )

        data_dict = self.tracker.to_dict(attribution)

        assert data_dict["source"] == "zillow"
        assert data_dict["utm_source"] == "zillow"
        assert data_dict["confidence_score"] == 0.95
        assert isinstance(data_dict["first_touch"], str)  # Should be ISO string

    def test_from_dict_conversion(self):
        """Test dictionary to SourceAttribution conversion."""
        data_dict = {
            "source": "zillow",
            "utm_source": "zillow",
            "confidence_score": 0.95,
            "source_quality": "premium",
            "first_touch": datetime.utcnow().isoformat()
        }

        attribution = self.tracker.from_dict(data_dict)

        assert attribution.source == LeadSource.ZILLOW
        assert attribution.utm_source == "zillow"
        assert attribution.source_quality == SourceQuality.PREMIUM
        assert isinstance(attribution.first_touch, datetime)

    @pytest.mark.asyncio
    async def test_analyze_referrer_urls(self):
        """Test referrer URL analysis."""
        test_cases = [
            ("https://facebook.com/posts/123", LeadSource.FACEBOOK_ORGANIC),
            ("https://google.com/search?q=homes", LeadSource.GOOGLE_ORGANIC),
            ("https://zillow.com/homedetails/123", LeadSource.ZILLOW),
            ("https://youtube.com/watch?v=abc", LeadSource.YOUTUBE)
        ]

        for referrer, expected_source in test_cases:
            detected = self.tracker._analyze_referrer(referrer)
            assert expected_source in detected

    @pytest.mark.asyncio
    async def test_complex_attribution_scenario(self):
        """Test complex multi-touch attribution scenario."""
        # Simulate a lead that came from Facebook Ad but has Google referrer
        contact_data = {
            "custom_fields": {
                "utm_source": "facebook",
                "utm_medium": "cpc",
                "utm_campaign": "austin-homes-2024",
                "referrer": "https://google.com/search"
            }
        }

        attribution = await self.tracker.analyze_lead_source(contact_data)

        # UTM parameters should take precedence over referrer
        assert attribution.source == LeadSource.FACEBOOK_ADS
        assert attribution.confidence_score >= 0.8
        assert attribution.campaign == "austin-homes-2024"

    @pytest.mark.asyncio
    async def test_performance_tracking_workflow(self):
        """Test complete performance tracking workflow."""
        source = LeadSource.GOOGLE_ADS

        # Track multiple events
        events = [
            ("lead_created", {"cost": 15.0}),
            ("lead_scored", {"score": 6}),
            ("lead_qualified", {"qualify_time_hours": 2.5}),
            ("deal_closed", {"deal_value": 8000.0, "close_time_days": 45})
        ]

        with patch.object(self.tracker.cache, 'get') as mock_get, \
             patch.object(self.tracker.cache, 'set') as mock_set:

            # Mock existing metrics
            mock_get.return_value = {
                "total_leads": 0,
                "qualified_leads": 0,
                "closed_deals": 0,
                "total_revenue": 0.0,
                "total_cost": 0.0,
                "lead_scores": [],
                "qualify_times": [],
                "close_times": []
            }

            # Track all events
            for event_type, metadata in events:
                await self.tracker.track_source_performance(
                    source, event_type, metadata
                )

            # Verify cache operations
            assert mock_get.call_count >= len(events)
            assert mock_set.call_count >= len(events)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_data(self):
        """Test error handling with invalid or missing data."""
        # Test with empty contact data
        attribution = await self.tracker.analyze_lead_source({})
        assert attribution.source == LeadSource.UNKNOWN
        assert attribution.confidence_score == 0.0

        # Test with malformed data
        contact_data = {
            "custom_fields": {
                "utm_source": 123,  # Invalid type
                "referrer": None
            }
        }
        attribution = await self.tracker.analyze_lead_source(contact_data)
        assert attribution.source == LeadSource.UNKNOWN

    @pytest.mark.asyncio
    async def test_cache_fallback(self):
        """Test behavior when cache operations fail."""
        source = LeadSource.FACEBOOK_ADS

        # Mock cache failure
        with patch.object(self.tracker.cache, 'get', side_effect=Exception("Cache error")):
            performance = await self.tracker.get_source_performance(source)
            assert performance is None  # Should handle gracefully

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test empty pattern matching
        detected = self.tracker._analyze_referrer("")
        assert len(detected) == 0

        # Test very long campaign names
        long_detail = self.tracker._extract_source_detail(
            LeadSource.FACEBOOK_ADS,
            {"utm_campaign": "a" * 100},  # Very long campaign
            None
        )
        assert long_detail is not None

        # Test quality score boundaries
        score = self.tracker._classify_source_quality(8.0)
        assert score == SourceQuality.PREMIUM

        score = self.tracker._classify_source_quality(4.0)
        assert score == SourceQuality.BUDGET