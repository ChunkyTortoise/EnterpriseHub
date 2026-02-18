import pytest
pytestmark = pytest.mark.integration

"""Tests for JorgeHandoffService seed data and DB persistence.

Validates seed_historical_data generation, export/import,
set_repository, load_from_database, and persist_seed_data.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (

    JorgeHandoffService,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Reset class-level state before each test."""
    JorgeHandoffService._handoff_outcomes = {}
    JorgeHandoffService._handoff_history = {}
    JorgeHandoffService._active_handoffs = {}
    JorgeHandoffService.reset_analytics()
    yield
    JorgeHandoffService._handoff_outcomes = {}
    JorgeHandoffService._handoff_history = {}
    JorgeHandoffService._active_handoffs = {}


@pytest.fixture
def service():
    return JorgeHandoffService()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.save_handoff_outcome = AsyncMock()
    repo.load_handoff_outcomes = AsyncMock(return_value=[])
    return repo


# ── seed_historical_data ──────────────────────────────────────────────


def test_seed_historical_data_generates_correct_routes():
    result = JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    assert result["routes_seeded"] == [
        "lead->buyer",
        "lead->seller",
        "buyer->seller",
        "seller->buyer",
    ]
    assert result["samples_per_route"] == 10
    assert result["total_records"] == 40


def test_seed_historical_data_populates_outcomes():
    JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    assert len(JorgeHandoffService._handoff_outcomes) == 4
    for route, outcomes in JorgeHandoffService._handoff_outcomes.items():
        assert len(outcomes) == 10
        for outcome in outcomes:
            assert "contact_id" in outcome
            assert outcome["outcome"] in {"successful", "failed", "reverted", "timeout"}
            assert "timestamp" in outcome
            assert outcome["metadata"]["seeded"] is True


def test_seed_historical_data_reproducible():
    result1 = JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    JorgeHandoffService._handoff_outcomes = {}
    result2 = JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    assert result1["per_route_success_rates"] == result2["per_route_success_rates"]


def test_seed_historical_data_min_samples_error():
    with pytest.raises(ValueError, match="num_samples must be >= 10"):
        JorgeHandoffService.seed_historical_data(num_samples=5)


def test_seed_historical_data_success_rates_reasonable():
    result = JorgeHandoffService.seed_historical_data(num_samples=100, seed=42)
    rates = result["per_route_success_rates"]
    # With 100 samples, rates should be within ~15% of configured probs
    assert 0.6 < rates["lead->buyer"] < 0.95
    assert 0.5 < rates["lead->seller"] < 0.85
    assert 0.4 < rates["buyer->seller"] < 0.8
    assert 0.55 < rates["seller->buyer"] < 0.9


# ── export_seed_data / import_seed_data ───────────────────────────────


def test_export_import_roundtrip():
    JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    exported = JorgeHandoffService.export_seed_data()
    assert len(exported) == 40

    JorgeHandoffService._handoff_outcomes = {}
    imported = JorgeHandoffService.import_seed_data(exported)
    assert imported == 40

    for route in ["lead->buyer", "lead->seller", "buyer->seller", "seller->buyer"]:
        assert len(JorgeHandoffService._handoff_outcomes[route]) == 10


# ── set_repository ────────────────────────────────────────────────────


def test_set_repository(service, mock_repo):
    service.set_repository(mock_repo)
    assert service._repository is mock_repo


def test_set_repository_none(service, mock_repo):
    service.set_repository(mock_repo)
    service.set_repository(None)
    assert service._repository is None


# ── load_from_database ────────────────────────────────────────────────


async def test_load_from_database_no_repo(service):
    result = await service.load_from_database()
    assert result == 0


async def test_load_from_database_loads_records(service, mock_repo):
    mock_repo.load_handoff_outcomes.return_value = [
        {
            "contact_id": "c001",
            "source_bot": "lead",
            "target_bot": "buyer",
            "outcome": "successful",
            "timestamp": time.time(),
            "metadata": {"test": True},
        },
        {
            "contact_id": "c002",
            "source_bot": "seller",
            "target_bot": "buyer",
            "outcome": "failed",
            "timestamp": time.time() - 100,
            "metadata": None,
        },
    ]
    service.set_repository(mock_repo)
    loaded = await service.load_from_database(since_minutes=60)
    assert loaded == 2
    assert "lead->buyer" in JorgeHandoffService._handoff_outcomes
    assert "seller->buyer" in JorgeHandoffService._handoff_outcomes


async def test_load_from_database_deduplicates(service, mock_repo):
    ts = time.time()
    # Pre-populate an outcome
    JorgeHandoffService._handoff_outcomes["lead->buyer"] = [
        {"contact_id": "c001", "outcome": "successful", "timestamp": ts, "metadata": {}}
    ]
    mock_repo.load_handoff_outcomes.return_value = [
        {
            "contact_id": "c001",
            "source_bot": "lead",
            "target_bot": "buyer",
            "outcome": "successful",
            "timestamp": ts,
            "metadata": {},
        },
    ]
    service.set_repository(mock_repo)
    loaded = await service.load_from_database()
    assert loaded == 0  # Already exists, should not duplicate


async def test_load_from_database_handles_errors(service, mock_repo):
    mock_repo.load_handoff_outcomes.side_effect = Exception("db error")
    service.set_repository(mock_repo)
    loaded = await service.load_from_database()
    assert loaded == 0


# ── persist_seed_data ─────────────────────────────────────────────────


async def test_persist_seed_data_no_repo(service):
    JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    result = await service.persist_seed_data()
    assert result == 0


async def test_persist_seed_data_writes_all_records(service, mock_repo):
    JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    service.set_repository(mock_repo)
    persisted = await service.persist_seed_data()
    assert persisted == 40
    assert mock_repo.save_handoff_outcome.await_count == 40


async def test_persist_seed_data_handles_partial_failures(service, mock_repo):
    JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
    # Fail every other call
    call_count = 0

    async def flaky_save(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 0:
            raise Exception("intermittent failure")

    mock_repo.save_handoff_outcome = flaky_save
    service.set_repository(mock_repo)
    persisted = await service.persist_seed_data()
    # Half should succeed
    assert persisted == 20


# ── record_handoff_outcome ────────────────────────────────────────────


def test_record_handoff_outcome_stores_in_memory():
    JorgeHandoffService.record_handoff_outcome(
        contact_id="c001",
        source_bot="lead",
        target_bot="buyer",
        outcome="successful",
    )
    assert len(JorgeHandoffService._handoff_outcomes["lead->buyer"]) == 1
    record = JorgeHandoffService._handoff_outcomes["lead->buyer"][0]
    assert record["contact_id"] == "c001"
    assert record["outcome"] == "successful"


def test_record_handoff_outcome_invalid_outcome():
    JorgeHandoffService.record_handoff_outcome(
        contact_id="c001",
        source_bot="lead",
        target_bot="buyer",
        outcome="invalid_status",
    )
    # Should not store invalid outcomes
    assert "lead->buyer" not in JorgeHandoffService._handoff_outcomes


def test_learned_adjustments_after_seeding():
    JorgeHandoffService.seed_historical_data(num_samples=20, seed=42)
    adjustments = JorgeHandoffService.get_learned_adjustments("lead", "buyer")
    assert adjustments["sample_size"] == 20
    assert adjustments["success_rate"] > 0.0
    assert adjustments["adjustment"] in {-0.05, 0.0, 0.1}