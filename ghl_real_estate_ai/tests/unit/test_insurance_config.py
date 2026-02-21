"""Tests for insurance industry vertical configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "industries" / "insurance.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


@pytest.mark.unit
def test_yaml_loads_without_error():
    """Insurance YAML loads and contains all required top-level keys."""
    config = _load_config()
    for key in ("industry", "bant_qualification", "temperature_thresholds", "compliance_rules"):
        assert key in config, f"Missing required key: {key}"
    assert config["industry"] == "insurance"


@pytest.mark.unit
def test_all_bant_dimensions_defined():
    """All four BANT dimensions are present in bant_qualification."""
    config = _load_config()
    bant = config["bant_qualification"]
    for dimension in ("budget", "authority", "need", "timeline"):
        assert dimension in bant, f"Missing BANT dimension: {dimension}"
        assert "question" in bant[dimension], f"Missing question for {dimension}"


@pytest.mark.unit
def test_temperature_thresholds_ordered():
    """Temperature thresholds are properly ordered: hot > warm > cold."""
    config = _load_config()
    thresholds = config["temperature_thresholds"]
    assert thresholds["hot"] == 75
    assert thresholds["warm"] == 50
    assert thresholds["cold"] == 25
    assert thresholds["hot"] > thresholds["warm"] > thresholds["cold"]


@pytest.mark.unit
def test_compliance_rules_non_empty():
    """At least 3 compliance rules are defined."""
    config = _load_config()
    rules = config["compliance_rules"]
    assert isinstance(rules, list)
    assert len(rules) >= 3, f"Expected at least 3 compliance rules, got {len(rules)}"


@pytest.mark.unit
def test_demo_flow_runs_without_error():
    """Insurance demo flow runs end-to-end and produces a positive BANT score."""
    from examples.insurance_flow import run_demo

    result = run_demo()
    assert result.total > 0, "Expected BANT total > 0 from demo conversation"
    assert len(result.signals_detected) > 0, "Expected at least one signal detected"
