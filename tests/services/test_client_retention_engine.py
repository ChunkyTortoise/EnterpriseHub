import pytest

pytestmark = pytest.mark.integration

"""
Test suite for Client Retention Engine - Comprehensive client lifecycle management system
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from dateutil.relativedelta import relativedelta

from ghl_real_estate_ai.services.client_retention_engine import (
    ClientLifecycleStage,
    ClientProfile,
    ClientRetentionEngine,
    EngagementPlan,
    EngagementType,
    LifeEventType,
    ReferralOpportunity,
    get_client_retention_engine,
)


@pytest.fixture
def retention_engine():
    """Create retention engine instance for testing"""
    return ClientRetentionEngine()


@pytest.fixture
def sample_client_data():
    """Sample client data for testing"""
    return {
        "name": "John & Jane Smith",
        "email": "john.smith@email.com",
        "phone": "+19095551234",
        "property_address": "123 Oak Street, Etiwanda, CA 91739",
        "purchase_date": "2023-06-15",
        "purchase_price": 750000,
        "current_estimated_value": 780000,
        "neighborhood": "etiwanda",
        "property_type": "single_family",
        "family_size": 4,
        "employment_industry": "logistics",
    }


@pytest.fixture
def sample_client_profile():
    """Sample client profile for testing"""
    return ClientProfile(
        client_id="client-123",
        name="John & Jane Smith",
        email="john.smith@email.com",
        phone="+19095551234",
        property_address="123 Oak Street, Etiwanda, CA 91739",
        purchase_date=datetime(2023, 6, 15),
        purchase_price=750000,
        current_estimated_value=780000,
        neighborhood="etiwanda",
        property_type="single_family",
        family_size=4,
        employment_industry="logistics",
    )


@pytest.mark.asyncio
class TestClientRetentionEngine:
    """Test cases for Client Retention Engine"""

    async def test_engine_initialization(self, retention_engine):
        """Test retention engine initializes correctly"""
        assert retention_engine is not None
        assert hasattr(retention_engine, "llm_client")
        assert hasattr(retention_engine, "rc_assistant")
        assert hasattr(retention_engine, "engagement_templates")
        assert hasattr(retention_engine, "lifecycle_rules")

    async def test_engagement_templates_loading(self, retention_engine):
        """Test engagement templates are properly loaded"""
        templates = retention_engine.engagement_templates

        assert "anniversary_message" in templates
        assert "value_update" in templates
        assert "referral_request" in templates
        assert "review_request" in templates
        assert "life_event_outreach" in templates

        # Check template structure
        anniversary = templates["anniversary_message"]
        assert "subject_template" in anniversary
        assert "message_template" in anniversary
        assert "personalization_fields" in anniversary

    async def test_lifecycle_rules_loading(self, retention_engine):
        """Test lifecycle rules configuration"""
        rules = retention_engine.lifecycle_rules

        assert "recent_buyer" in rules
        assert "settled_client" in rules
        assert "established_client" in rules
        assert "long_term_client" in rules

        recent_buyer = rules["recent_buyer"]
        assert recent_buyer["engagement_frequency"] == "monthly"
        assert "referral_timing" in recent_buyer

    async def test_add_client_profile(self, retention_engine, sample_client_data):
        """Test adding new client profile"""
        with patch.object(retention_engine, "_create_initial_engagement_plan") as mock_plan:
            mock_plan.return_value = None

            profile = await retention_engine.add_client_profile(sample_client_data)

            assert isinstance(profile, ClientProfile)
            assert profile.name == "John & Jane Smith"
            assert profile.email == "john.smith@email.com"
            assert profile.neighborhood == "etiwanda"
            assert profile.lifecycle_stage == ClientLifecycleStage.ESTABLISHED_CLIENT  # ~964 days ago (2-5 years)

    async def test_lifecycle_stage_determination(self, retention_engine):
        """Test lifecycle stage determination based on purchase date"""
        # Recent buyer (2 months ago)
        recent_date = datetime.now() - timedelta(days=60)
        stage = retention_engine._determine_lifecycle_stage(recent_date)
        assert stage == ClientLifecycleStage.RECENT_BUYER

        # Settled client (1 year ago)
        settled_date = datetime.now() - timedelta(days=365)
        stage = retention_engine._determine_lifecycle_stage(settled_date)
        assert stage == ClientLifecycleStage.SETTLED_CLIENT

        # Established client (3 years ago)
        established_date = datetime.now() - timedelta(days=1095)
        stage = retention_engine._determine_lifecycle_stage(established_date)
        assert stage == ClientLifecycleStage.ESTABLISHED_CLIENT

        # Long-term client (6 years ago)
        longterm_date = datetime.now() - timedelta(days=2190)
        stage = retention_engine._determine_lifecycle_stage(longterm_date)
        assert stage == ClientLifecycleStage.LONG_TERM_CLIENT

    async def test_engagement_score_calculation(self, retention_engine, sample_client_profile):
        """Test client engagement score calculation"""
        # Set lifecycle to ESTABLISHED_CLIENT for lower base score to avoid 1.0 ceiling
        sample_client_profile.lifecycle_stage = ClientLifecycleStage.ESTABLISHED_CLIENT

        # Base score for established client (0.4)
        score = await retention_engine._calculate_engagement_score(sample_client_profile)
        assert 0.0 <= score <= 1.0

        # Score should increase with referrals
        sample_client_profile.referrals_provided = 2
        score_with_referrals = await retention_engine._calculate_engagement_score(sample_client_profile)
        assert score_with_referrals > score

        # Score should increase with reviews
        sample_client_profile.reviews_given = 1
        score_with_reviews = await retention_engine._calculate_engagement_score(sample_client_profile)
        assert score_with_reviews > score_with_referrals

    async def test_referral_probability_calculation(self, retention_engine, sample_client_profile):
        """Test referral probability calculation"""
        # Set lifecycle to ESTABLISHED_CLIENT for meaningful base probability (0.8)
        sample_client_profile.lifecycle_stage = ClientLifecycleStage.ESTABLISHED_CLIENT

        probability = await retention_engine._calculate_referral_probability(sample_client_profile)
        assert 0.0 <= probability <= 1.0

        # Probability should be higher for established clients (base 0.8)
        assert probability > 0.5

        # Should increase with past referrals
        sample_client_profile.referrals_provided = 1
        higher_prob = await retention_engine._calculate_referral_probability(sample_client_profile)
        assert higher_prob > probability

    async def test_property_value_update(self, retention_engine, sample_client_profile):
        """Test property value update and notification triggering"""
        client_id = sample_client_profile.client_id
        retention_engine.client_profiles[client_id] = sample_client_profile

        with patch.object(retention_engine, "_schedule_value_update_engagement") as mock_schedule:
            # Significant increase (>5%)
            new_value = 825000  # 10.4% increase
            await retention_engine.update_property_value(client_id, new_value, trigger_notification=True)

            mock_schedule.assert_called_once()
            assert sample_client_profile.current_estimated_value == new_value

    async def test_life_event_detection(self, retention_engine, sample_client_profile):
        """Test life event detection and response"""
        client_id = sample_client_profile.client_id
        retention_engine.client_profiles[client_id] = sample_client_profile

        with patch.object(retention_engine, "_schedule_life_event_engagement") as mock_schedule:
            await retention_engine.detect_life_event(
                client_id, LifeEventType.FAMILY_ADDITION, {"details": "New baby born"}
            )

            mock_schedule.assert_called_once()
            assert len(sample_client_profile.life_events) > 0

    async def test_referral_request_timing(self, retention_engine, sample_client_profile):
        """Test referral request timing logic"""
        # Recent buyer should not be good timing for referrals
        sample_client_profile.lifecycle_stage = ClientLifecycleStage.RECENT_BUYER
        sample_client_profile.purchase_date = datetime.now() - timedelta(days=30)
        is_good_timing = await retention_engine._is_good_referral_timing(sample_client_profile)
        assert is_good_timing is False

        # Settled client with high referral probability should be good timing
        sample_client_profile.lifecycle_stage = ClientLifecycleStage.SETTLED_CLIENT
        sample_client_profile.referral_probability = 0.8
        sample_client_profile.last_contact_date = datetime.now() - timedelta(days=45)
        is_good_timing = await retention_engine._is_good_referral_timing(sample_client_profile)
        assert is_good_timing is True

    async def test_request_referral(self, retention_engine, sample_client_profile):
        """Test referral request functionality"""
        client_id = sample_client_profile.client_id
        retention_engine.client_profiles[client_id] = sample_client_profile

        with patch.object(retention_engine, "_is_good_referral_timing") as mock_timing:
            with patch.object(retention_engine, "_schedule_referral_request_engagement") as mock_schedule:
                mock_timing.return_value = True

                success = await retention_engine.request_referral(
                    client_id, target_demographics=["logistics_workers", "healthcare_professionals"]
                )

                assert success is True
                mock_schedule.assert_called_once()

    async def test_engagement_personalization(self, retention_engine, sample_client_profile):
        """Test AI-powered engagement personalization"""
        engagement = EngagementPlan(
            plan_id="test-engagement-123",
            client_id=sample_client_profile.client_id,
            engagement_type=EngagementType.ANNIVERSARY_MESSAGE,
            scheduled_date=datetime.now() + timedelta(days=1),
            priority="medium",
            subject="Happy Anniversary!",
            message_template="anniversary_message",
            personalization_data={"anniversary_year": "1"},
            channel="email",
        )

        with patch.object(retention_engine.llm_client, "agenerate") as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"subject": "Happy 1 Year Anniversary in Your Etiwanda Home!", "message": "Hi John, can you believe it\'s been 1 year since you purchased your beautiful home at 123 Oak Street?", "personal_touches": ["Referenced specific address", "Used first name"]}'
            )

            personalized = await retention_engine._personalize_engagement(engagement, sample_client_profile)

            assert "Happy" in personalized["subject"]
            assert "John" in personalized["message"]
            assert len(personalized.get("personal_touches", [])) > 0

    async def test_engagement_execution(self, retention_engine, sample_client_profile):
        """Test engagement execution"""
        client_id = sample_client_profile.client_id
        retention_engine.client_profiles[client_id] = sample_client_profile

        engagement = EngagementPlan(
            plan_id="test-execution-123",
            client_id=client_id,
            engagement_type=EngagementType.CHECK_IN,
            scheduled_date=datetime.now(),
            priority="medium",
            subject="How are you settling in?",
            message_template="check_in",
            personalization_data={},
            channel="email",
        )

        with patch.object(retention_engine, "_personalize_engagement") as mock_personalize:
            with patch.object(retention_engine, "_send_engagement") as mock_send:
                mock_personalize.return_value = {
                    "subject": "How are you settling in?",
                    "message": "Hi John, hope you're loving your new home!",
                }

                await retention_engine._execute_engagement(engagement)

                assert engagement.status == "sent"
                assert engagement.sent_at is not None
                assert sample_client_profile.total_engagements > 0
                mock_send.assert_called_once()

    async def test_daily_engagement_processing(self, retention_engine):
        """Test daily engagement processing"""
        # Create engagement for today
        today_engagement = EngagementPlan(
            plan_id="today-123",
            client_id="client-123",
            engagement_type=EngagementType.VALUE_UPDATE,
            scheduled_date=datetime.now(),
            priority="medium",
            subject="Market Update",
            message_template="value_update",
            personalization_data={},
            channel="email",
        )

        retention_engine.engagement_plans[today_engagement.plan_id] = today_engagement

        with patch.object(retention_engine, "_execute_engagement") as mock_execute:
            with patch.object(retention_engine, "_generate_scheduled_engagements") as mock_generate:
                processed_count = await retention_engine.process_daily_engagements()

                assert processed_count >= 1
                mock_execute.assert_called()

    async def test_initial_engagement_plan_creation(self, retention_engine, sample_client_profile):
        """Test initial engagement plan creation for new clients"""
        await retention_engine._create_initial_engagement_plan(sample_client_profile)

        # Should have created multiple engagements
        client_engagements = [
            plan
            for plan in retention_engine.engagement_plans.values()
            if plan.client_id == sample_client_profile.client_id
        ]

        assert len(client_engagements) > 0

        # Should include key engagement types
        engagement_types = [plan.engagement_type for plan in client_engagements]
        assert EngagementType.CHECK_IN in engagement_types
        assert EngagementType.REVIEW_REQUEST in engagement_types

    async def test_template_substitution_fallback(self, retention_engine):
        """Test basic template substitution as AI fallback"""
        template_data = {
            "subject_template": "Happy {anniversary_year} Year Anniversary!",
            "message_template": "Hi {client_name}, it's been {anniversary_year} year since your purchase.",
        }

        context = {"client_name": "John", "anniversary_year": "2"}

        result = retention_engine._basic_template_substitution(template_data, context)

        assert "Happy 2 Year Anniversary!" == result["subject"]
        assert "Hi John, it's been 2 year since" in result["message"]

    async def test_retention_analytics(self, retention_engine, sample_client_profile):
        """Test retention analytics generation"""
        # Add client to engine
        retention_engine.client_profiles[sample_client_profile.client_id] = sample_client_profile

        analytics = await retention_engine.get_retention_analytics()

        assert "total_clients" in analytics
        assert "lifecycle_distribution" in analytics
        assert "engagement_metrics" in analytics
        assert "referral_metrics" in analytics
        assert "retention_trends" in analytics

        assert analytics["total_clients"] >= 1
        assert "recent_buyer" in analytics["lifecycle_distribution"]

    async def test_client_profile_caching(self, retention_engine, sample_client_profile):
        """Test client profile caching functionality"""
        with patch.object(retention_engine.cache, "set") as mock_set:
            await retention_engine._cache_client_profile(sample_client_profile)
            mock_set.assert_called_once()

    async def test_engagement_plan_caching(self, retention_engine):
        """Test engagement plan caching"""
        engagement = EngagementPlan(
            plan_id="cache-test-123",
            client_id="client-123",
            engagement_type=EngagementType.MARKET_UPDATE,
            scheduled_date=datetime.now() + timedelta(days=1),
            priority="medium",
            subject="Test Cache",
            message_template="market_update",
            personalization_data={},
            channel="email",
        )

        with patch.object(retention_engine.cache, "set") as mock_set:
            await retention_engine._cache_engagement_plan(engagement)
            mock_set.assert_called_once()

    async def test_error_handling_missing_client(self, retention_engine):
        """Test error handling for missing client"""
        # Should handle gracefully without throwing
        await retention_engine.update_property_value("nonexistent-client", 800000)

        # Should return False for referral request
        success = await retention_engine.request_referral("nonexistent-client")
        assert success is False

    async def test_singleton_pattern(self):
        """Test singleton pattern implementation"""
        engine1 = get_client_retention_engine()
        engine2 = get_client_retention_engine()

        assert engine1 is engine2


@pytest.mark.asyncio
class TestClientProfile:
    """Test ClientProfile dataclass"""

    def test_profile_initialization(self):
        """Test profile initialization with defaults"""
        profile = ClientProfile(
            client_id="test-123",
            name="Test Client",
            email="test@email.com",
            phone="+19095551234",
            property_address="123 Test St",
            purchase_date=datetime(2023, 6, 1),
            purchase_price=700000,
            current_estimated_value=720000,
            neighborhood="central_rc",
            property_type="single_family",
        )

        assert profile.client_id == "test-123"
        assert profile.family_size == 2
        assert profile.lifecycle_stage == ClientLifecycleStage.RECENT_BUYER
        assert profile.life_events == []
        assert profile.interests == []

    def test_profile_with_custom_values(self):
        """Test profile with custom values"""
        profile = ClientProfile(
            client_id="test-456",
            name="Custom Client",
            email="custom@email.com",
            phone="+19095555678",
            property_address="456 Custom Ave",
            purchase_date=datetime(2022, 1, 1),
            purchase_price=800000,
            current_estimated_value=850000,
            neighborhood="alta_loma",
            property_type="luxury",
            family_size=5,
            employment_industry="healthcare",
            referrals_provided=3,
            reviews_given=2,
        )

        assert profile.family_size == 5
        assert profile.employment_industry == "healthcare"
        assert profile.referrals_provided == 3
        assert profile.reviews_given == 2


@pytest.mark.asyncio
class TestEngagementPlan:
    """Test EngagementPlan dataclass"""

    def test_plan_initialization(self):
        """Test plan initialization"""
        plan = EngagementPlan(
            plan_id="plan-123",
            client_id="client-456",
            engagement_type=EngagementType.ANNIVERSARY_MESSAGE,
            scheduled_date=datetime.now() + timedelta(days=7),
            priority="high",
            subject="Happy Anniversary!",
            message_template="anniversary_message",
            personalization_data={"year": "2"},
            channel="email",
        )

        assert plan.plan_id == "plan-123"
        assert plan.status == "planned"
        assert plan.created_at is not None
        assert plan.response_received is False

    def test_plan_with_custom_status(self):
        """Test plan with custom status"""
        plan = EngagementPlan(
            plan_id="plan-789",
            client_id="client-123",
            engagement_type=EngagementType.REFERRAL_REQUEST,
            scheduled_date=datetime.now(),
            priority="medium",
            subject="Quick Favor",
            message_template="referral_request",
            personalization_data={},
            channel="email",
            status="sent",
            sent_at=datetime.now() - timedelta(hours=1),
        )

        assert plan.status == "sent"
        assert plan.sent_at is not None


@pytest.mark.asyncio
class TestReferralOpportunity:
    """Test ReferralOpportunity dataclass"""

    def test_opportunity_initialization(self):
        """Test opportunity initialization"""
        opportunity = ReferralOpportunity(
            opportunity_id="opp-123",
            referring_client_id="client-456",
            potential_referral_name="Jane Doe",
            potential_referral_contact="jane@email.com",
            referral_context="Co-worker",
            property_need="buying",
            timeline="3-6 months",
            confidence_level=0.7,
        )

        assert opportunity.opportunity_id == "opp-123"
        assert opportunity.status == "identified"
        assert opportunity.notes == []

    def test_opportunity_with_notes(self):
        """Test opportunity with notes"""
        opportunity = ReferralOpportunity(
            opportunity_id="opp-456",
            referring_client_id="client-789",
            potential_referral_name="Bob Smith",
            potential_referral_contact="+19095551234",
            referral_context="Neighbor",
            property_need="selling",
            timeline="immediate",
            confidence_level=0.9,
            notes=["Very interested", "Pre-approved"],
        )

        assert len(opportunity.notes) == 2
        assert "Very interested" in opportunity.notes


# Integration tests
@pytest.mark.integration
class TestClientRetentionIntegration:
    """Integration tests for Client Retention Engine"""

    @pytest.mark.asyncio
    async def test_complete_client_lifecycle(self, sample_client_data):
        """Test complete client lifecycle management"""
        engine = get_client_retention_engine()

        # Add client
        profile = await engine.add_client_profile(sample_client_data)
        assert profile.client_id

        # Update property value
        await engine.update_property_value(profile.client_id, 800000)
        assert engine.client_profiles[profile.client_id].current_estimated_value == 800000

        # Detect life event
        await engine.detect_life_event(profile.client_id, LifeEventType.JOB_CHANGE, {"new_company": "Amazon"})

        # Request referral
        with patch.object(engine, "_is_good_referral_timing") as mock_timing:
            mock_timing.return_value = True
            success = await engine.request_referral(profile.client_id)
            assert success is True

        # Process engagements
        with patch.object(engine, "_execute_engagement") as mock_execute:
            count = await engine.process_daily_engagements()
            assert count >= 0

    @pytest.mark.asyncio
    async def test_multi_client_management(self):
        """Test managing multiple clients"""
        engine = get_client_retention_engine()

        # Add multiple clients
        clients = []
        for i in range(3):
            client_data = {
                "name": f"Client {i}",
                "email": f"client{i}@email.com",
                "phone": f"+1909555{i:04d}",
                "property_address": f"123 Street {i}",
                "purchase_date": (datetime.now() - timedelta(days=365 * i)).isoformat(),
                "purchase_price": 700000 + (i * 50000),
                "current_estimated_value": 720000 + (i * 52000),
                "neighborhood": "etiwanda",
                "property_type": "single_family",
            }

            with patch.object(engine, "_create_initial_engagement_plan"):
                profile = await engine.add_client_profile(client_data)
                clients.append(profile)

        assert len(clients) == 3
        assert len(engine.client_profiles) >= 3

        # Test analytics with multiple clients
        analytics = await engine.get_retention_analytics()
        assert analytics["total_clients"] >= 3

    @pytest.mark.asyncio
    async def test_engagement_personalization_pipeline(self, sample_client_data):
        """Test complete engagement personalization pipeline"""
        engine = get_client_retention_engine()

        with patch.object(engine, "_create_initial_engagement_plan"):
            profile = await engine.add_client_profile(sample_client_data)

        # Create anniversary engagement
        engagement = EngagementPlan(
            plan_id="anniversary-test",
            client_id=profile.client_id,
            engagement_type=EngagementType.ANNIVERSARY_MESSAGE,
            scheduled_date=datetime.now(),
            priority="medium",
            subject="Anniversary",
            message_template="anniversary_message",
            personalization_data={"anniversary_year": "1"},
            channel="email",
        )

        engine.engagement_plans[engagement.plan_id] = engagement

        with patch.object(engine.llm_client, "agenerate") as mock_agenerate:
            with patch.object(engine, "_send_engagement") as mock_send:
                mock_agenerate.return_value = Mock(
                    content='{"subject": "Happy Anniversary!", "message": "Personalized message", "personal_touches": []}'
                )

                await engine._execute_engagement(engagement)

                assert engagement.status == "sent"
                mock_send.assert_called_once()
