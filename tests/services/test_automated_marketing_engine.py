import pytest
pytestmark = pytest.mark.integration

"""
Test suite for Automated Marketing Engine - AI-powered marketing campaign generator
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.automated_marketing_engine import (
    AutomatedMarketingEngine,
    CampaignBrief,
    CampaignPerformance,
    CampaignPriority,
    CampaignType,
    ContentFormat,
    GeneratedContent,
    get_automated_marketing_engine,
)


@pytest.fixture
def marketing_engine():
    """Create marketing engine instance for testing"""
    return AutomatedMarketingEngine()


@pytest.fixture
def sample_listing_data():
    """Sample listing data for testing"""
    return {
        "address": "123 Main St, Rancho Cucamonga, CA",
        "price": 725000,
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2100,
        "neighborhood": "etiwanda",
        "property_type": "single_family",
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        "median_price": 700000,
        "price_trend": "increasing",
        "inventory_months": 2.1,
        "days_on_market": 22,
        "market_conditions": "balanced",
    }


class TestAutomatedMarketingEngine:
    """Test cases for Automated Marketing Engine"""

    async def test_engine_initialization(self, marketing_engine):
        """Test marketing engine initializes correctly"""
        assert marketing_engine is not None
        assert hasattr(marketing_engine, "llm_client")
        assert hasattr(marketing_engine, "rc_assistant")
        assert hasattr(marketing_engine, "campaign_templates")
        assert hasattr(marketing_engine, "content_frameworks")

    async def test_jorge_brand_voice_loading(self, marketing_engine):
        """Test Jorge's brand voice configuration"""
        brand_voice = marketing_engine.jorge_brand_voice

        assert "Inland Empire" in str(brand_voice["key_messages"])
        assert "Logistics and healthcare" in str(brand_voice["key_messages"])
        assert "professional_friendly" in brand_voice["tone_guidelines"]

    async def test_campaign_templates_loading(self, marketing_engine):
        """Test campaign templates are properly loaded"""
        templates = marketing_engine.campaign_templates

        assert "new_listing" in templates
        assert "market_update" in templates
        assert "seasonal_campaign" in templates
        assert "success_story" in templates

        new_listing = templates["new_listing"]
        assert new_listing["objective"]
        assert new_listing["target_audience"]
        assert new_listing["content_focus"]

    async def test_content_frameworks_loading(self, marketing_engine):
        """Test content frameworks are properly loaded"""
        frameworks = marketing_engine.content_frameworks

        assert "facebook_post" in frameworks
        assert "instagram_post" in frameworks
        assert "linkedin_post" in frameworks
        assert "email_newsletter" in frameworks

        facebook = frameworks["facebook_post"]
        assert facebook["max_length"] == 240
        assert facebook["image_required"] is True

    async def test_create_listing_campaign(self, marketing_engine, sample_listing_data):
        """Test creation of new listing campaign"""
        campaign = await marketing_engine.create_campaign_from_trigger("new_listing", sample_listing_data)

        assert isinstance(campaign, CampaignBrief)
        assert campaign.campaign_type == CampaignType.LISTING_PROMOTION
        assert campaign.priority == CampaignPriority.URGENT
        assert ContentFormat.FACEBOOK_POST in campaign.content_formats
        assert ContentFormat.INSTAGRAM_POST in campaign.content_formats
        assert "etiwanda" in campaign.target_neighborhoods

    async def test_create_market_update_campaign(self, marketing_engine, sample_market_data):
        """Test creation of market update campaign"""
        campaign = await marketing_engine.create_campaign_from_trigger("market_milestone", sample_market_data)

        assert isinstance(campaign, CampaignBrief)
        assert campaign.campaign_type == CampaignType.MARKET_UPDATE
        assert campaign.priority == CampaignPriority.HIGH
        assert ContentFormat.EMAIL_HTML in campaign.content_formats
        assert ContentFormat.BLOG_POST in campaign.content_formats

    async def test_create_seasonal_campaign(self, marketing_engine):
        """Test creation of seasonal campaign"""
        seasonal_data = {
            "season": "spring",
            "opportunities": ["New inventory", "Family relocations"],
            "urgency_factors": ["Competition increases"],
        }

        campaign = await marketing_engine.create_campaign_from_trigger("seasonal_opportunity", seasonal_data)

        assert isinstance(campaign, CampaignBrief)
        assert campaign.campaign_type == CampaignType.SEASONAL
        assert campaign.priority == CampaignPriority.HIGH
        assert campaign.tone == "urgent"

    async def test_create_success_story_campaign(self, marketing_engine):
        """Test creation of success story campaign"""
        closing_data = {
            "client_name": "John & Jane Smith",
            "property_address": "123 Oak St, Etiwanda",
            "sale_price": 750000,
            "days_to_close": 18,
        }

        campaign = await marketing_engine.create_campaign_from_trigger("successful_closing", closing_data)

        assert isinstance(campaign, CampaignBrief)
        assert campaign.campaign_type == CampaignType.SUCCESS_STORY
        assert campaign.tone == "celebratory"
        assert ContentFormat.FACEBOOK_POST in campaign.content_formats

    async def test_create_lead_magnet_campaign(self, marketing_engine):
        """Test creation of lead magnet campaign"""
        magnet_data = {"type": "buyer_guide", "title": "First-Time Buyer Guide to RC", "target": "first_time_buyers"}

        campaign = await marketing_engine.create_campaign_from_trigger("lead_magnet_request", magnet_data)

        assert isinstance(campaign, CampaignBrief)
        assert campaign.campaign_type == CampaignType.LEAD_MAGNET
        assert campaign.tone == "educational"
        assert ContentFormat.PDF_GUIDE in campaign.content_formats

    async def test_generate_campaign_content(self, marketing_engine, sample_listing_data):
        """Test content generation for campaigns"""
        # Create campaign
        campaign = await marketing_engine.create_campaign_from_trigger("new_listing", sample_listing_data)

        # Mock AI response
        ai_response = {
            "title": "Beautiful 4BR Home in Etiwanda - Perfect for Families!",
            "body": "Discover this stunning 4-bedroom, 3-bathroom home in the prestigious Etiwanda neighborhood. With 2,100 sq ft of living space and proximity to top-rated schools, this property offers the perfect blend of comfort and convenience.",
            "hashtags": ["#RanchoCucamonga", "#Etiwanda", "#RealEstate", "#JorgeRealEstate"],
            "call_to_action": "Schedule your private showing today!",
            "image_description": "Professional exterior photo of the home",
            "design_elements": ["Jorge's branding", "Property highlights"],
        }

        import json as _json

        with patch.object(marketing_engine.llm_client, "agenerate") as mock_agenerate:
            mock_agenerate.return_value = Mock(content=_json.dumps(ai_response))

            content = await marketing_engine.generate_campaign_content(campaign.campaign_id)

            assert len(content) > 0
            assert all(isinstance(c, GeneratedContent) for c in content)

    async def test_content_variant_generation(self, marketing_engine):
        """Test A/B test variant generation"""
        campaign = CampaignBrief(
            campaign_id="test-123",
            campaign_type=CampaignType.MARKET_UPDATE,
            target_audience="homeowners",
            objective="educate market",
            content_formats=[ContentFormat.FACEBOOK_POST],
            priority=CampaignPriority.MEDIUM,
            deadline=datetime.now() + timedelta(days=2),
        )

        with patch.object(marketing_engine, "_generate_single_content_piece") as mock_generate:

            def make_variant_content(*args, **kwargs):
                # The fourth positional arg is variant letter, or pick from kwargs
                variant_letter = args[2] if len(args) > 2 else kwargs.get("variant", "A")
                return GeneratedContent(
                    content_id=f"test-content-{variant_letter}",
                    campaign_id="test-123",
                    content_format=ContentFormat.FACEBOOK_POST,
                    title="Test Title",
                    body="Test body content",
                    hashtags=["#test"],
                    call_to_action="Contact Jorge",
                    variant=variant_letter,
                )

            mock_generate.side_effect = make_variant_content

            variants = await marketing_engine._generate_content_variants(
                campaign, ContentFormat.FACEBOOK_POST, variant_count=2
            )

            assert len(variants) == 2
            assert variants[0].variant == "A"
            assert variants[1].variant == "B"

    async def test_content_personalization(self, marketing_engine):
        """Test AI-powered content personalization"""
        campaign = CampaignBrief(
            campaign_id="test-456",
            campaign_type=CampaignType.MARKET_UPDATE,
            target_audience="tech workers",
            objective="market education",
            content_formats=[ContentFormat.LINKEDIN_POST],
            priority=CampaignPriority.MEDIUM,
            deadline=datetime.now() + timedelta(days=3),
            target_demographics=["tech_workers"],
            market_data={"appreciation": 8.2},
        )

        variant_approach = {
            "focus": "data_driven",
            "emotion": "trust",
            "structure": "evidence_based",
            "cta_style": "consultative",
        }

        with patch.object(marketing_engine.llm_client, "agenerate") as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"title": "Data Shows Strong IE Market Growth", "body": "Recent analysis reveals 8.2% appreciation in the Inland Empire tech corridor.", "hashtags": ["#InlandEmpire", "#TechWorkers"], "call_to_action": "Get your personalized market analysis", "image_description": "Market data visualization"}'
            )

            content = await marketing_engine._generate_single_content_piece(
                campaign, ContentFormat.LINKEDIN_POST, "A", variant_approach
            )

            assert content.title
            assert content.body
            assert len(content.hashtags) > 0
            assert "market analysis" in content.call_to_action.lower()

    async def test_seasonal_campaigns_creation(self, marketing_engine):
        """Test automated seasonal campaign creation"""
        with patch("datetime.datetime") as mock_datetime:
            # Mock spring season (March)
            mock_datetime.now.return_value = datetime(2024, 3, 15)

            campaigns = await marketing_engine.create_seasonal_campaigns()

            assert len(campaigns) > 0
            spring_campaign = campaigns[0]
            assert spring_campaign.campaign_type == CampaignType.SEASONAL

    async def test_lead_magnets_creation(self, marketing_engine):
        """Test automated lead magnet creation"""
        lead_magnets = await marketing_engine.create_lead_magnets()

        assert len(lead_magnets) >= 3

        # Check for target audiences - all lead magnets use the same demographics
        targets = [lm.target_demographics for lm in lead_magnets]
        assert any("first_time_buyers" in target for target in targets)
        assert any("relocating_professionals" in target for target in targets)

    async def test_campaign_performance_tracking(self, marketing_engine):
        """Test campaign performance tracking and analytics"""
        performance_data = {
            "impressions": 10000,
            "clicks": 500,
            "leads_generated": 15,
            "appointments_scheduled": 8,
            "cost_per_lead": 35.50,
            "roi_percentage": 240.0,
            "engagement_rate": 0.05,
        }

        performance = await marketing_engine.track_campaign_performance("test-campaign-123", performance_data)

        assert isinstance(performance, CampaignPerformance)
        assert performance.campaign_id == "test-campaign-123"
        assert performance.impressions == 10000
        assert performance.leads_generated == 15
        assert performance.roi_percentage == 240.0

    async def test_ab_test_analysis(self, marketing_engine):
        """Test A/B test results analysis"""
        performance_data = {
            "impressions": 5000,
            "clicks": 250,
            "leads_generated": 10,
            "variants": [
                {"variant": "A", "conversion_rate": 0.04, "clicks": 120},
                {"variant": "B", "conversion_rate": 0.06, "clicks": 130},
            ],
        }

        performance = await marketing_engine.track_campaign_performance("test-ab-campaign", performance_data)

        assert performance.winning_variant == "B"
        assert performance.confidence_level > 0.5

    async def test_campaign_analytics(self, marketing_engine):
        """Test comprehensive campaign analytics"""
        analytics = await marketing_engine.get_campaign_analytics()

        assert "total_campaigns" in analytics
        assert "total_content_pieces" in analytics
        assert "content_performance" in analytics
        assert "ab_test_insights" in analytics

    async def test_content_parsing_error_handling(self, marketing_engine):
        """Test error handling in content parsing"""
        # Test with invalid JSON response
        with patch.object(marketing_engine.llm_client, "agenerate") as mock_agenerate:
            mock_agenerate.return_value = Mock(content="Invalid JSON content")

            parsed = await marketing_engine._parse_generated_content(
                "Invalid JSON content", ContentFormat.FACEBOOK_POST
            )

            # Should return fallback content
            assert parsed["title"]
            assert parsed["body"]
            assert parsed["hashtags"]
            assert parsed["call_to_action"]

    async def test_campaign_brief_caching(self, marketing_engine):
        """Test campaign brief caching functionality"""
        campaign = CampaignBrief(
            campaign_id="test-cache-123",
            campaign_type=CampaignType.MARKET_UPDATE,
            target_audience="test audience",
            objective="test objective",
            content_formats=[ContentFormat.EMAIL_HTML],
            priority=CampaignPriority.MEDIUM,
            deadline=datetime.now() + timedelta(days=1),
        )

        with patch.object(marketing_engine.cache, "set") as mock_set:
            await marketing_engine._cache_campaign_brief(campaign)
            mock_set.assert_called_once()

    async def test_error_handling_invalid_trigger(self, marketing_engine):
        """Test error handling for invalid trigger types"""
        with pytest.raises(ValueError):
            await marketing_engine.create_campaign_from_trigger("invalid_trigger_type", {})

    async def test_singleton_pattern(self):
        """Test singleton pattern implementation"""
        engine1 = get_automated_marketing_engine()
        engine2 = get_automated_marketing_engine()

        assert engine1 is engine2


class TestCampaignBrief:
    """Test CampaignBrief dataclass"""

    def test_brief_initialization(self):
        """Test brief initialization with defaults"""
        brief = CampaignBrief(
            campaign_id="test-123",
            campaign_type=CampaignType.SOCIAL_MEDIA,
            target_audience="homeowners",
            objective="engagement",
            content_formats=[ContentFormat.FACEBOOK_POST],
            priority=CampaignPriority.MEDIUM,
            deadline=datetime.now() + timedelta(days=1),
        )

        assert brief.campaign_id == "test-123"
        assert brief.tone == "professional_friendly"
        assert brief.status == "draft"
        assert brief.target_neighborhoods == []
        assert brief.created_at is not None

    def test_brief_with_custom_values(self):
        """Test brief with custom values"""
        deadline = datetime.now() + timedelta(days=2)

        brief = CampaignBrief(
            campaign_id="test-456",
            campaign_type=CampaignType.EMAIL_NEWSLETTER,
            target_audience="investors",
            objective="lead generation",
            content_formats=[ContentFormat.EMAIL_HTML, ContentFormat.PDF_GUIDE],
            priority=CampaignPriority.HIGH,
            deadline=deadline,
            tone="educational",
            target_neighborhoods=["etiwanda", "alta_loma"],
        )

        assert brief.tone == "educational"
        assert brief.deadline == deadline
        assert len(brief.target_neighborhoods) == 2
        assert brief.priority == CampaignPriority.HIGH


class TestGeneratedContent:
    """Test GeneratedContent dataclass"""

    def test_content_initialization(self):
        """Test content initialization"""
        content = GeneratedContent(
            content_id="content-123",
            campaign_id="campaign-456",
            content_format=ContentFormat.INSTAGRAM_POST,
            title="Test Title",
            body="Test body content",
            hashtags=["#test", "#content"],
            call_to_action="Contact us",
        )

        assert content.content_id == "content-123"
        assert content.campaign_id == "campaign-456"
        assert content.content_format == ContentFormat.INSTAGRAM_POST
        assert content.variant == "A"
        assert content.design_elements == []

    def test_content_with_performance_data(self):
        """Test content with performance metrics"""
        content = GeneratedContent(
            content_id="content-789",
            campaign_id="campaign-456",
            content_format=ContentFormat.FACEBOOK_POST,
            title="Performance Test",
            body="Test content",
            hashtags=["#performance"],
            call_to_action="Click here",
            engagement_score=0.85,
            conversion_rate=0.12,
            click_through_rate=0.08,
        )

        assert content.engagement_score == 0.85
        assert content.conversion_rate == 0.12
        assert content.click_through_rate == 0.08


# Integration tests
class TestMarketingEngineIntegration:
    """Integration tests for Marketing Engine"""

    @pytest.mark.asyncio
    async def test_full_campaign_lifecycle(self, sample_listing_data):
        """Test complete campaign lifecycle"""
        engine = get_automated_marketing_engine()

        # Create campaign
        campaign = await engine.create_campaign_from_trigger("new_listing", sample_listing_data)

        assert campaign.campaign_id

        # Generate content
        with patch.object(engine.llm_client, "agenerate") as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"title": "Test Title", "body": "Test body", "hashtags": ["#test"], "call_to_action": "Contact Jorge"}'
            )

            content = await engine.generate_campaign_content(campaign.campaign_id)
            assert len(content) > 0

        # Track performance
        performance = await engine.track_campaign_performance(
            campaign.campaign_id, {"impressions": 1000, "clicks": 50, "leads_generated": 3}
        )

        assert performance.campaign_id == campaign.campaign_id

    @pytest.mark.asyncio
    async def test_seasonal_automation(self):
        """Test seasonal campaign automation"""
        engine = get_automated_marketing_engine()

        # Test multiple seasons
        with patch("datetime.datetime") as mock_datetime:
            # Spring
            mock_datetime.now.return_value = datetime(2024, 4, 1)
            spring_campaigns = await engine.create_seasonal_campaigns()
            assert len(spring_campaigns) > 0

            # Fall
            mock_datetime.now.return_value = datetime(2024, 10, 1)
            fall_campaigns = await engine.create_seasonal_campaigns()
            assert len(fall_campaigns) > 0

    @pytest.mark.asyncio
    async def test_multi_format_content_generation(self):
        """Test content generation across multiple formats"""
        engine = get_automated_marketing_engine()

        campaign = CampaignBrief(
            campaign_id="multi-format-test",
            campaign_type=CampaignType.MARKET_UPDATE,
            target_audience="all clients",
            objective="education",
            content_formats=[
                ContentFormat.FACEBOOK_POST,
                ContentFormat.INSTAGRAM_POST,
                ContentFormat.LINKEDIN_POST,
                ContentFormat.EMAIL_HTML,
            ],
            priority=CampaignPriority.MEDIUM,
            deadline=datetime.now() + timedelta(days=1),
        )

        engine.active_campaigns[campaign.campaign_id] = campaign

        with patch.object(engine.llm_client, "agenerate") as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"title": "Multi-Format Test", "body": "Test content", "hashtags": ["#test"], "call_to_action": "Learn more"}'
            )

            content = await engine.generate_campaign_content(campaign.campaign_id)

            # Should have content for each format (A & B variants)
            assert len(content) == 8  # 4 formats × 2 variants
            formats = [c.content_format for c in content]
            assert ContentFormat.FACEBOOK_POST in formats
            assert ContentFormat.INSTAGRAM_POST in formats
            assert ContentFormat.LINKEDIN_POST in formats
            assert ContentFormat.EMAIL_HTML in formats
