"""
Unit tests for LeadScorer service.

Tests lead quality scoring based on qualifying questions answered:
- Question count methodology (Jorge's requirement)
- Hot/Warm/Cold lead classification
- Seller vs buyer scoring
- Cache integration
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


class TestLeadScorerInit:
    """Tests for LeadScorer initialization."""

    def test_init_loads_thresholds_from_settings(self):
        """Thresholds are loaded from settings."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()

            assert scorer.hot_threshold == 3
            assert scorer.warm_threshold == 2

    def test_init_initializes_cache_service(self):
        """Cache service is initialized."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()

            assert scorer.cache is not None


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_generate_cache_key_is_stable(self):
        """Same input produces same cache key."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()
            data = {"key1": "value1", "key2": "value2"}

            key1 = scorer._generate_cache_key("prefix", data)
            key2 = scorer._generate_cache_key("prefix", data)

            assert key1 == key2

    def test_generate_cache_key_different_for_different_data(self):
        """Different data produces different cache keys."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()

            key1 = scorer._generate_cache_key("prefix", {"key": "value1"})
            key2 = scorer._generate_cache_key("prefix", {"key": "value2"})

            assert key1 != key2

    def test_generate_cache_key_ignores_key_order(self):
        """Key order doesn't affect cache key (sorted keys)."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()

            key1 = scorer._generate_cache_key("prefix", {"a": 1, "b": 2})
            key2 = scorer._generate_cache_key("prefix", {"b": 2, "a": 1})

            assert key1 == key2

    def test_generate_cache_key_includes_prefix(self):
        """Prefix is included in cache key."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()

            key = scorer._generate_cache_key("my_prefix", {"data": "value"})

            assert "my_prefix" in key


class TestBuyerLeadScoring:
    """Tests for buyer lead scoring."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer with mocked cache."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()
            scorer.cache = MagicMock()
            scorer.cache.get = AsyncMock(return_value=None)
            scorer.cache.set = AsyncMock()
            return scorer

    @pytest.mark.asyncio
    async def test_null_context_returns_zero(self, scorer):
        """Null context returns score of 0."""
        result = await scorer.calculate(None)
        assert result == 0

    @pytest.mark.asyncio
    async def test_empty_context_returns_zero(self, scorer):
        """Empty context returns score of 0."""
        result = await scorer.calculate({})
        assert result == 0

    @pytest.mark.asyncio
    async def test_budget_confirmed_counts_as_question(self, scorer):
        """Budget confirmed counts as 1 question answered."""
        context = {
            "extracted_preferences": {
                "budget_confirmed": True,
                "budget_min": 400000,
                "budget_max": 500000,
            }
        }

        result = await scorer.calculate(context)
        assert result >= 1

    @pytest.mark.asyncio
    async def test_location_specified_counts_as_question(self, scorer):
        """Location specified counts as 1 question answered."""
        context = {
            "extracted_preferences": {
                "location": "Rancho Cucamonga",
                "neighborhoods": ["Victoria Gardens"],
            }
        }

        result = await scorer.calculate(context)
        assert result >= 1

    @pytest.mark.asyncio
    async def test_timeline_confirmed_counts_as_question(self, scorer):
        """Timeline confirmed counts as 1 question answered."""
        context = {
            "extracted_preferences": {
                "timeline": "30-60 days",
                "move_in_date": "March 2026",
            }
        }

        result = await scorer.calculate(context)
        assert result >= 1

    @pytest.mark.asyncio
    async def test_property_requirements_count_as_question(self, scorer):
        """Property requirements (beds/baths) count as 1 question answered."""
        context = {
            "extracted_preferences": {
                "bedrooms": 3,
                "bathrooms": 2,
                "must_haves": ["pool", "garage"],
            }
        }

        result = await scorer.calculate(context)
        assert result >= 1

    @pytest.mark.asyncio
    async def test_financing_status_counts_as_question(self, scorer):
        """Financing status counts as 1 question answered."""
        context = {
            "extracted_preferences": {
                "financing": "pre-approved",
                "down_payment": "20%",
            }
        }

        result = await scorer.calculate(context)
        assert result >= 1

    @pytest.mark.asyncio
    async def test_motivation_counts_as_question(self, scorer):
        """Motivation counts as 1 question answered."""
        context = {
            "extracted_preferences": {
                "motivation": "relocating for work",
                "urgency": "high",
            }
        }

        result = await scorer.calculate(context)
        assert result >= 1

    @pytest.mark.asyncio
    async def test_multiple_questions_sum_correctly(self, scorer):
        """Multiple answered questions sum correctly."""
        context = {
            "extracted_preferences": {
                "budget_confirmed": True,
                "location": "Rancho Cucamonga",
                "timeline": "30-60 days",
                "bedrooms": 3,
                "financing": "pre-approved",
                "motivation": "relocating",
            }
        }

        result = await scorer.calculate(context)
        # Should have at least 5 questions answered
        assert result >= 5


class TestSellerLeadScoring:
    """Tests for seller lead scoring."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer with mocked cache."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()
            scorer.cache = MagicMock()
            scorer.cache.get = AsyncMock(return_value=None)
            scorer.cache.set = AsyncMock()
            return scorer

    @pytest.mark.asyncio
    async def test_seller_context_routes_to_seller_scoring(self, scorer):
        """Seller context uses seller scoring method."""
        context = {
            "conversation_type": "seller",
            "seller_preferences": {
                "property_address": "123 Main St",
                "timeline": "ASAP",
            },
        }

        result = await scorer.calculate(context)
        # Should process as seller
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_seller_temperature_triggers_seller_scoring(self, scorer):
        """Seller temperature triggers seller scoring."""
        context = {
            "seller_temperature": "hot",
            "seller_preferences": {
                "motivation": "downsizing",
            },
        }

        result = await scorer.calculate(context)
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_seller_home_condition_counts_as_question(self, scorer):
        """Home condition counts as a question for sellers."""
        context = {
            "conversation_type": "seller",
            "seller_preferences": {
                "home_condition": "excellent",
                "recent_upgrades": ["kitchen", "bathrooms"],
            },
        }

        result = await scorer.calculate(context)
        assert result >= 1


class TestLeadClassification:
    """Tests for lead classification (Hot/Warm/Cold)."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer with mocked cache."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()
            scorer.cache = MagicMock()
            scorer.cache.get = AsyncMock(return_value=None)
            scorer.cache.set = AsyncMock()
            return scorer

    def test_classify_hot_lead(self, scorer):
        """Score >= hot_threshold is classified as hot."""
        classification = scorer.classify_lead(4)
        assert classification == "hot"

    def test_classify_warm_lead(self, scorer):
        """Score >= warm_threshold but < hot_threshold is warm."""
        classification = scorer.classify_lead(2)
        assert classification == "warm"

    def test_classify_cold_lead(self, scorer):
        """Score < warm_threshold is cold."""
        classification = scorer.classify_lead(1)
        assert classification == "cold"

    def test_classify_zero_is_cold(self, scorer):
        """Score of 0 is cold."""
        classification = scorer.classify_lead(0)
        assert classification == "cold"


class TestCacheIntegration:
    """Tests for cache integration."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer with mocked cache."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()
            scorer.cache = MagicMock()
            scorer.cache.get = AsyncMock(return_value=None)
            scorer.cache.set = AsyncMock()
            return scorer

    @pytest.mark.asyncio
    async def test_calculate_checks_cache_first(self, scorer):
        """Calculate checks cache before computing."""
        context = {"extracted_preferences": {"budget_confirmed": True}}

        await scorer.calculate(context)

        # Cache.get should have been called
        scorer.cache.get.assert_called()

    @pytest.mark.asyncio
    async def test_calculate_returns_cached_result(self, scorer):
        """Cached result is returned without recomputation."""
        scorer.cache.get = AsyncMock(return_value=5)  # Cached score

        context = {"extracted_preferences": {"budget_confirmed": True}}
        result = await scorer.calculate(context)

        assert result == 5
        # Should not set cache since we got a hit
        scorer.cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_calculate_caches_result(self, scorer):
        """Computed result is cached."""
        scorer.cache.get = AsyncMock(return_value=None)

        context = {
            "extracted_preferences": {
                "budget_confirmed": True,
                "location": "Rancho Cucamonga",
                "timeline": "30 days",
            }
        }

        await scorer.calculate(context)

        # Result should be cached
        scorer.cache.set.assert_called_once()
        call_args = scorer.cache.set.call_args
        assert call_args[1]["ttl"] == 3600  # 1 hour TTL


class TestSellerScoreMethod:
    """Tests for calculate_seller_score method."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer with mocked cache."""
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer

        with patch("ghl_real_estate_ai.services.lead_scorer.settings") as mock_settings:
            mock_settings.hot_lead_threshold = 3
            mock_settings.warm_lead_threshold = 2

            scorer = LeadScorer()
            scorer.cache = MagicMock()
            return scorer

    def test_seller_score_returns_dict(self, scorer):
        """calculate_seller_score returns a dict with questions_answered."""
        result = scorer.calculate_seller_score({})

        assert isinstance(result, dict)
        assert "questions_answered" in result

    def test_seller_score_empty_preferences(self, scorer):
        """Empty preferences returns 0 questions answered."""
        result = scorer.calculate_seller_score({})

        assert result["questions_answered"] == 0

    def test_seller_score_counts_property_address(self, scorer):
        """Property address counts as a question."""
        result = scorer.calculate_seller_score({"property_address": "123 Main St, Rancho Cucamonga"})

        assert result["questions_answered"] >= 1

    def test_seller_score_counts_timeline(self, scorer):
        """Timeline counts as a question."""
        result = scorer.calculate_seller_score({"timeline": "60-90 days"})

        assert result["questions_answered"] >= 1

    def test_seller_score_counts_motivation(self, scorer):
        """Motivation counts as a question."""
        result = scorer.calculate_seller_score({"motivation": "relocating for work"})

        assert result["questions_answered"] >= 1

    def test_seller_score_counts_price_expectation(self, scorer):
        """Price expectation counts as a question."""
        result = scorer.calculate_seller_score({"expected_price": 650000})

        assert result["questions_answered"] >= 1

    def test_seller_score_counts_home_condition(self, scorer):
        """Home condition counts as a question."""
        result = scorer.calculate_seller_score({"home_condition": "good", "upgrades": "new roof 2023"})

        assert result["questions_answered"] >= 1
