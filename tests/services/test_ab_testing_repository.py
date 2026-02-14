import pytest
pytestmark = pytest.mark.integration

"""Tests for ABTestingRepository — the PostgreSQL persistence layer.

Since tests run without a real database, all asyncpg calls are mocked
via a FakeDBManager that records calls and returns plausible results.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_repository import (

    ABTestingRepository,
)

# ── Fake DB Manager ────────────────────────────────────────────────────


class FakeRecord(dict):
    """Dict-like object that also supports attribute access (like asyncpg.Record)."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


class FakeTransaction:
    """Async context manager that yields a mock connection."""

    def __init__(self):
        self.conn = AsyncMock()

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, *args):
        pass


class FakeDBManager:
    """Minimal mock of DatabaseConnectionManager for repository tests."""

    def __init__(self):
        self._execute_query_results = []
        self._execute_fetchrow_result = None
        self._execute_command_result = "INSERT 0 1"
        self._transaction_conn = AsyncMock()

    async def execute_query(self, sql, *args, **kwargs):
        return self._execute_query_results

    async def execute_fetchrow(self, sql, *args, **kwargs):
        return self._execute_fetchrow_result

    async def execute_command(self, sql, *args, **kwargs):
        return self._execute_command_result

    def transaction(self):
        return FakeTransaction()


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def db():
    return FakeDBManager()


@pytest.fixture
def repo(db):
    return ABTestingRepository(db)


# ── Tests ──────────────────────────────────────────────────────────────


class TestCreateExperiment:
    @pytest.mark.asyncio
    async def test_create_returns_metadata(self, repo):
        result = await repo.create_experiment(
            experiment_name="test_exp",
            variants=["a", "b"],
            traffic_split={"a": 0.5, "b": 0.5},
        )

        assert result["experiment_name"] == "test_exp"
        assert result["variants"] == ["a", "b"]
        assert result["status"] == "active"
        assert "experiment_id" in result

    @pytest.mark.asyncio
    async def test_create_with_optional_fields(self, repo):
        result = await repo.create_experiment(
            experiment_name="detailed_exp",
            variants=["x", "y", "z"],
            traffic_split={"x": 0.5, "y": 0.3, "z": 0.2},
            description="A test",
            target_bot="lead",
            metric_type="engagement",
            minimum_sample_size=200,
            created_by="test_user",
        )

        assert result["experiment_name"] == "detailed_exp"
        assert len(result["variants"]) == 3


class TestGetExperiment:
    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self, repo, db):
        db._execute_fetchrow_result = None
        result = await repo.get_experiment("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_experiment_with_variants(self, repo, db):
        exp_id = uuid.uuid4()
        db._execute_fetchrow_result = FakeRecord(
            id=exp_id,
            experiment_name="tone_test",
            description="Test tones",
            target_bot=None,
            metric_type="conversion",
            minimum_sample_size=100,
            status="active",
            started_at=None,
            completed_at=None,
            default_traffic_split='{"formal": 0.5, "casual": 0.5}',
            winner_variant=None,
            statistical_significance=None,
            created_at=None,
            created_by=None,
        )
        var_id = uuid.uuid4()
        db._execute_query_results = [
            FakeRecord(
                id=var_id,
                variant_name="formal",
                traffic_weight=0.5,
                impressions=10,
                conversions=3,
                conversion_rate=0.3,
                total_value=3.0,
                confidence_interval_lower=0.1,
                confidence_interval_upper=0.5,
                is_control=True,
            ),
        ]

        result = await repo.get_experiment("tone_test")

        assert result is not None
        assert result["experiment_name"] == "tone_test"
        assert len(result["variants"]) == 1
        assert result["variants"][0]["variant_name"] == "formal"


class TestListActiveExperiments:
    @pytest.mark.asyncio
    async def test_returns_active_list(self, repo, db):
        db._execute_query_results = [
            FakeRecord(
                id=uuid.uuid4(),
                experiment_name="exp1",
                status="active",
                started_at=None,
                default_traffic_split=None,
                created_at=None,
                total_assignments=5,
            ),
        ]

        result = await repo.list_active_experiments()

        assert len(result) == 1
        assert result[0]["experiment_name"] == "exp1"
        assert result[0]["total_assignments"] == 5

    @pytest.mark.asyncio
    async def test_returns_empty_when_none(self, repo, db):
        db._execute_query_results = []
        result = await repo.list_active_experiments()
        assert result == []


class TestDeactivateExperiment:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self, repo, db):
        db._execute_command_result = "UPDATE 1"
        result = await repo.deactivate_experiment("test_exp")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self, repo, db):
        db._execute_command_result = "UPDATE 0"
        result = await repo.deactivate_experiment("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_accepts_winner_and_significance(self, repo, db):
        db._execute_command_result = "UPDATE 1"
        result = await repo.deactivate_experiment("test_exp", winner="variant_a", significance=0.03)
        assert result is True


class TestGetOrCreateAssignment:
    @pytest.mark.asyncio
    async def test_creates_assignment(self, repo, db):
        exp_id = uuid.uuid4()
        var_id = uuid.uuid4()

        call_count = 0

        async def mock_fetchrow(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FakeRecord(id=exp_id)
            elif call_count == 2:
                return FakeRecord(id=var_id)
            return None

        db.execute_fetchrow = mock_fetchrow

        result = await repo.get_or_create_assignment(
            experiment_name="test_exp",
            user_id="contact_123",
            variant_name="formal",
            bucket_value=0.42,
        )

        assert result["experiment_name"] == "test_exp"
        assert result["user_id"] == "contact_123"
        assert result["variant_name"] == "formal"
        assert result["bucket_value"] == 0.42

    @pytest.mark.asyncio
    async def test_raises_on_missing_experiment(self, repo, db):
        db._execute_fetchrow_result = None

        with pytest.raises(KeyError, match="not found in DB"):
            await repo.get_or_create_assignment(
                experiment_name="missing",
                user_id="contact_1",
                variant_name="a",
                bucket_value=0.5,
            )

    @pytest.mark.asyncio
    async def test_raises_on_missing_variant(self, repo, db):
        call_count = 0

        async def mock_fetchrow(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FakeRecord(id=uuid.uuid4())
            return None

        db.execute_fetchrow = mock_fetchrow

        with pytest.raises(KeyError, match="Variant.*not found"):
            await repo.get_or_create_assignment(
                experiment_name="test_exp",
                user_id="contact_1",
                variant_name="nonexistent",
                bucket_value=0.5,
            )


class TestRecordOutcome:
    @pytest.mark.asyncio
    async def test_records_outcome(self, repo, db):
        assignment_id = uuid.uuid4()
        experiment_id = uuid.uuid4()
        variant_id = uuid.uuid4()

        db._execute_fetchrow_result = FakeRecord(
            assignment_id=assignment_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
        )

        result = await repo.record_outcome(
            experiment_name="test_exp",
            user_id="contact_1",
            variant_name="formal",
            event_type="conversion",
            value=1.0,
        )

        assert result["experiment_name"] == "test_exp"
        assert result["event_type"] == "conversion"
        assert "metric_id" in result

    @pytest.mark.asyncio
    async def test_raises_on_missing_assignment(self, repo, db):
        db._execute_fetchrow_result = None

        with pytest.raises(KeyError, match="No assignment found"):
            await repo.record_outcome(
                experiment_name="test_exp",
                user_id="unassigned_user",
                variant_name="a",
                event_type="conversion",
            )


class TestGetExperimentResults:
    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self, repo, db):
        db._execute_fetchrow_result = None
        result = await repo.get_experiment_results("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_aggregated_stats(self, repo, db):
        exp_id = uuid.uuid4()

        # get_experiment calls fetchrow, then get_experiment_results
        # calls execute_query for variants twice (once in get_experiment,
        # once for the results query)
        call_count = {"fetchrow": 0, "query": 0}

        async def mock_fetchrow(sql, *args, **kwargs):
            call_count["fetchrow"] += 1
            return FakeRecord(
                id=exp_id,
                experiment_name="test_exp",
                description=None,
                target_bot=None,
                metric_type="conversion",
                minimum_sample_size=100,
                status="active",
                started_at=None,
                completed_at=None,
                default_traffic_split=None,
                winner_variant=None,
                statistical_significance=None,
                created_at=None,
                created_by=None,
            )

        async def mock_query(sql, *args, **kwargs):
            call_count["query"] += 1
            return [
                FakeRecord(
                    id=uuid.uuid4(),
                    variant_name="a",
                    traffic_weight=0.5,
                    impressions=50,
                    conversions=10,
                    conversion_rate=0.2,
                    total_value=10.0,
                    confidence_interval_lower=0.1,
                    confidence_interval_upper=0.3,
                    is_control=True,
                ),
                FakeRecord(
                    id=uuid.uuid4(),
                    variant_name="b",
                    traffic_weight=0.5,
                    impressions=50,
                    conversions=15,
                    conversion_rate=0.3,
                    total_value=15.0,
                    confidence_interval_lower=0.18,
                    confidence_interval_upper=0.42,
                    is_control=False,
                ),
            ]

        db.execute_fetchrow = mock_fetchrow
        db.execute_query = mock_query

        result = await repo.get_experiment_results("test_exp")

        assert result is not None
        assert result["total_impressions"] == 100
        assert result["total_conversions"] == 25
        assert len(result["variants"]) == 2


class TestSeedDefaultExperiments:
    @pytest.mark.asyncio
    async def test_seeds_when_empty(self, repo, db):
        # get_experiment returns None for all 4 defaults
        db._execute_fetchrow_result = None

        created = await repo.seed_default_experiments()

        assert len(created) == 4
        assert "response_tone" in created
        assert "followup_timing" in created
        assert "cta_style" in created
        assert "greeting_style" in created

    @pytest.mark.asyncio
    async def test_skips_existing(self, repo, db):
        # Simulate first experiment exists, rest don't
        call_count = 0

        async def mock_fetchrow(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # response_tone exists
                return FakeRecord(
                    id=uuid.uuid4(),
                    experiment_name="response_tone",
                    description=None,
                    target_bot=None,
                    metric_type="conversion",
                    minimum_sample_size=100,
                    status="active",
                    started_at=None,
                    completed_at=None,
                    default_traffic_split=None,
                    winner_variant=None,
                    statistical_significance=None,
                    created_at=None,
                    created_by=None,
                )
            return None  # rest don't exist

        # For the existing experiment, also mock execute_query for variants
        async def mock_query(sql, *args, **kwargs):
            return []

        db.execute_fetchrow = mock_fetchrow
        db.execute_query = mock_query

        created = await repo.seed_default_experiments()

        assert "response_tone" not in created
        assert len(created) == 3