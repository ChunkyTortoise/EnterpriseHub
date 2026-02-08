"""Tests for the Jorge handoff seed data CLI script."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    JorgeHandoffService,
)

SCRIPT_PATH = str(Path(__file__).resolve().parent.parent.parent / "scripts" / "seed_jorge_handoff_data.py")


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset handoff service state before each test."""
    JorgeHandoffService.reset_analytics()
    JorgeHandoffService._handoff_outcomes = {}
    JorgeHandoffService._handoff_history = {}
    yield
    JorgeHandoffService.reset_analytics()
    JorgeHandoffService._handoff_outcomes = {}
    JorgeHandoffService._handoff_history = {}


class TestSeedHistoricalData:
    """Tests for seed_historical_data + export/import round-trip."""

    def test_seed_creates_records(self):
        result = JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
        assert result["total_records"] == 40  # 10 per route * 4 routes
        assert len(result["routes_seeded"]) == 4

    def test_seed_deterministic_with_same_seed(self):
        r1 = JorgeHandoffService.seed_historical_data(num_samples=10, seed=99)
        data1 = JorgeHandoffService.export_seed_data()
        JorgeHandoffService.reset_analytics()

        r2 = JorgeHandoffService.seed_historical_data(num_samples=10, seed=99)
        data2 = JorgeHandoffService.export_seed_data()

        assert r1["total_records"] == r2["total_records"]
        assert len(data1) == len(data2)
        for a, b in zip(data1, data2):
            assert a["outcome"] == b["outcome"]
            assert a["route"] == b["route"]

    def test_seed_success_rates_reasonable(self):
        result = JorgeHandoffService.seed_historical_data(num_samples=20, seed=42)
        for route in result["routes_seeded"]:
            rate = result["per_route_success_rates"][route]
            assert 0.0 <= rate <= 1.0, f"{route} rate out of range: {rate}"

    def test_minimum_samples_raises_below_threshold(self):
        with pytest.raises(ValueError, match="num_samples must be >= "):
            JorgeHandoffService.seed_historical_data(num_samples=5)


class TestExportImport:
    """Tests for export_seed_data / import_seed_data round-trip."""

    def test_export_returns_list(self):
        JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
        data = JorgeHandoffService.export_seed_data()
        assert isinstance(data, list)
        assert len(data) == 40

    def test_export_record_schema(self):
        JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
        data = JorgeHandoffService.export_seed_data()
        record = data[0]
        assert "route" in record
        assert "contact_id" in record
        assert "outcome" in record
        assert "timestamp" in record
        assert "metadata" in record

    def test_export_empty_when_no_data(self):
        data = JorgeHandoffService.export_seed_data()
        assert data == []

    def test_import_loads_records(self):
        records = [
            {
                "route": "lead->buyer",
                "contact_id": "test_001",
                "outcome": "successful",
                "timestamp": 1700000000.0,
                "metadata": {"seeded": True},
            },
            {
                "route": "lead->seller",
                "contact_id": "test_002",
                "outcome": "failed",
                "timestamp": 1700000001.0,
                "metadata": {"seeded": True},
            },
        ]
        imported = JorgeHandoffService.import_seed_data(records)
        assert imported == 2

    def test_round_trip(self):
        JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
        exported = JorgeHandoffService.export_seed_data()
        JorgeHandoffService.reset_analytics()

        imported = JorgeHandoffService.import_seed_data(exported)
        assert imported == len(exported)

        re_exported = JorgeHandoffService.export_seed_data()
        assert len(re_exported) == len(exported)

    def test_json_serializable(self):
        JorgeHandoffService.seed_historical_data(num_samples=10, seed=42)
        data = JorgeHandoffService.export_seed_data()
        # Should not raise
        json_str = json.dumps(data)
        reloaded = json.loads(json_str)
        assert len(reloaded) == len(data)


class TestFixtureFile:
    """Tests using the pre-generated fixture file."""

    FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "jorge_handoff_seed_data.json"

    def test_fixture_exists(self):
        assert self.FIXTURE_PATH.exists(), f"Fixture not found: {self.FIXTURE_PATH}"

    def test_fixture_valid_json(self):
        with open(self.FIXTURE_PATH) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_fixture_records_have_required_fields(self):
        with open(self.FIXTURE_PATH) as f:
            data = json.load(f)
        for record in data:
            assert "route" in record
            assert "outcome" in record
            assert "timestamp" in record

    def test_fixture_importable(self):
        with open(self.FIXTURE_PATH) as f:
            data = json.load(f)
        imported = JorgeHandoffService.import_seed_data(data)
        assert imported == len(data)

    def test_fixture_has_all_routes(self):
        with open(self.FIXTURE_PATH) as f:
            data = json.load(f)
        routes = {r["route"] for r in data}
        expected = {"lead->buyer", "lead->seller", "buyer->seller", "seller->buyer"}
        assert routes == expected


class TestCLIScript:
    """Tests for the CLI script invocation."""

    def test_script_runs_successfully(self):
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, "--num-samples", "10", "--seed", "42"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Seeded" in result.stdout

    def test_script_export(self, tmp_path):
        export_file = tmp_path / "test_export.json"
        result = subprocess.run(
            [
                sys.executable, SCRIPT_PATH,
                "--num-samples", "10",
                "--seed", "42",
                "--export", str(export_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert export_file.exists()
        with open(export_file) as f:
            data = json.load(f)
        assert len(data) == 40

    def test_script_shows_learned_adjustments(self):
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, "--num-samples", "20", "--seed", "42"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Learned threshold adjustments" in result.stdout
