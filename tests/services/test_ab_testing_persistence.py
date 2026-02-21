import pytest

pytestmark = pytest.mark.integration

"""Tests for ABTestingService write-through DB persistence.

Verifies that when a repository is attached, mutations are written
through to the database, and that DB failures don't block in-memory ops.
"""

from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import (
    ABTestingService,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure a fresh singleton for every test."""
    ABTestingService.reset()
    yield
    ABTestingService.reset()


@pytest.fixture
def service():
    return ABTestingService()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_or_create_assignment = AsyncMock(
        return_value={
            "experiment_name": "test",
            "user_id": "c1",
            "variant_name": "a",
            "bucket_value": 0.5,
        }
    )
    repo.record_outcome = AsyncMock(
        return_value={
            "metric_id": "m1",
            "experiment_name": "test",
            "user_id": "c1",
            "event_type": "conversion",
            "value": 1.0,
        }
    )
    repo.list_active_experiments = AsyncMock(return_value=[])
    repo.get_experiment = AsyncMock(return_value=None)
    repo.create_experiment = AsyncMock(
        return_value={
            "experiment_id": "id1",
            "experiment_name": "test",
            "variants": ["a", "b"],
            "status": "active",
        }
    )
    return repo


class TestSetRepository:
    def test_set_repository_attaches(self, service, mock_repo):
        service.set_repository(mock_repo)
        assert service._repository is mock_repo

    def test_set_repository_none_disables(self, service, mock_repo):
        service.set_repository(mock_repo)
        service.set_repository(None)
        assert service._repository is None


class TestWriteThroughAssignment:
    @pytest.mark.asyncio
    async def test_get_variant_persists_to_db(self, service, mock_repo):
        service.set_repository(mock_repo)
        service.create_experiment("exp1", ["a", "b"])

        variant = await service.get_variant("exp1", "contact_1")

        mock_repo.get_or_create_assignment.assert_called_once()
        call_kwargs = mock_repo.get_or_create_assignment.call_args
        assert call_kwargs.kwargs["experiment_name"] == "exp1"
        assert call_kwargs.kwargs["user_id"] == "contact_1"
        assert call_kwargs.kwargs["variant_name"] == variant

    @pytest.mark.asyncio
    async def test_get_variant_deduplicates_db_writes(self, service, mock_repo):
        service.set_repository(mock_repo)
        service.create_experiment("exp1", ["a", "b"])

        # First call: new assignment
        await service.get_variant("exp1", "contact_1")
        assert mock_repo.get_or_create_assignment.call_count == 1

        # Second call: same contact, should not write again
        await service.get_variant("exp1", "contact_1")
        assert mock_repo.get_or_create_assignment.call_count == 1

    @pytest.mark.asyncio
    async def test_get_variant_works_without_repo(self, service):
        """Verify in-memory-only mode still works fine."""
        service.create_experiment("exp1", ["a", "b"])
        variant = await service.get_variant("exp1", "contact_1")
        assert variant in ("a", "b")

    @pytest.mark.asyncio
    async def test_get_variant_survives_db_failure(self, service, mock_repo):
        service.set_repository(mock_repo)
        service.create_experiment("exp1", ["a", "b"])

        mock_repo.get_or_create_assignment.side_effect = Exception("DB connection lost")

        # Should still return a variant (in-memory works)
        variant = await service.get_variant("exp1", "contact_1")
        assert variant in ("a", "b")


class TestWriteThroughOutcome:
    @pytest.mark.asyncio
    async def test_record_outcome_persists_to_db(self, service, mock_repo):
        service.set_repository(mock_repo)
        service.create_experiment("exp1", ["a", "b"])

        variant = await service.get_variant("exp1", "contact_1")
        await service.record_outcome("exp1", "contact_1", variant, "conversion")

        mock_repo.record_outcome.assert_called_once()
        call_kwargs = mock_repo.record_outcome.call_args
        assert call_kwargs.kwargs["experiment_name"] == "exp1"
        assert call_kwargs.kwargs["event_type"] == "conversion"

    @pytest.mark.asyncio
    async def test_record_outcome_works_without_repo(self, service):
        service.create_experiment("exp1", ["a", "b"])
        variant = await service.get_variant("exp1", "contact_1")

        result = await service.record_outcome("exp1", "contact_1", variant, "conversion")
        assert result["outcome"] == "conversion"

    @pytest.mark.asyncio
    async def test_record_outcome_survives_db_failure(self, service, mock_repo):
        service.set_repository(mock_repo)
        service.create_experiment("exp1", ["a", "b"])

        mock_repo.record_outcome.side_effect = Exception("DB timeout")

        variant = await service.get_variant("exp1", "contact_1")
        result = await service.record_outcome("exp1", "contact_1", variant, "conversion")

        # In-memory recording still succeeds
        assert result["outcome"] == "conversion"


class TestLoadFromDB:
    @pytest.mark.asyncio
    async def test_load_returns_zero_without_repo(self, service):
        loaded = await service.load_from_db()
        assert loaded == 0

    @pytest.mark.asyncio
    async def test_load_hydrates_from_db(self, service, mock_repo):
        mock_repo.list_active_experiments.return_value = [
            {"experiment_name": "db_exp1"},
        ]
        mock_repo.get_experiment.return_value = {
            "id": "some-uuid",
            "experiment_name": "db_exp1",
            "status": "active",
            "default_traffic_split": '{"x": 0.5, "y": 0.5}',
            "variants": [
                {"variant_name": "x"},
                {"variant_name": "y"},
            ],
        }

        service.set_repository(mock_repo)
        loaded = await service.load_from_db()

        assert loaded == 1
        # Verify experiment is usable in-memory
        variant = await service.get_variant("db_exp1", "contact_1")
        assert variant in ("x", "y")

    @pytest.mark.asyncio
    async def test_load_syncs_memory_to_db(self, service, mock_repo):
        """In-memory experiments that don't exist in DB get created."""
        service.create_experiment("mem_only", ["a", "b"])

        mock_repo.list_active_experiments.return_value = []
        mock_repo.get_experiment.return_value = None

        service.set_repository(mock_repo)
        await service.load_from_db()

        # Should have tried to create mem_only in DB
        mock_repo.create_experiment.assert_called_once()
        call_kwargs = mock_repo.create_experiment.call_args
        assert call_kwargs.kwargs["experiment_name"] == "mem_only"

    @pytest.mark.asyncio
    async def test_load_skips_existing_in_memory(self, service, mock_repo):
        """Experiments already in memory are not overwritten."""
        service.create_experiment("shared_exp", ["a", "b"])

        mock_repo.list_active_experiments.return_value = [
            {"experiment_name": "shared_exp"},
        ]

        service.set_repository(mock_repo)
        loaded = await service.load_from_db()

        # Should not load (already in memory)
        assert loaded == 0

    @pytest.mark.asyncio
    async def test_load_survives_db_failure(self, service, mock_repo):
        mock_repo.list_active_experiments.side_effect = Exception("DB unreachable")

        service.set_repository(mock_repo)
        loaded = await service.load_from_db()

        # Graceful degradation
        assert loaded == 0


class TestResetClearsRepository:
    def test_reset_clears_repository(self, service, mock_repo):
        service.set_repository(mock_repo)
        ABTestingService.reset()

        new_service = ABTestingService()
        assert new_service._repository is None
