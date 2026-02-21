"""Tests for MarketIntelligenceLoader."""

import os
from pathlib import Path

import pytest

from ghl_real_estate_ai.config.market_intelligence_loader import MarketIntelligenceLoader


def test_loads_default_market():
    loader = MarketIntelligenceLoader()
    market = loader.get_active_market()
    assert market["display_name"] == "Rancho Cucamonga"
    assert "91730" in market["zip_codes"]
    assert "Alta Loma" in market["neighborhoods"]["luxury"]


def test_env_var_overrides_active_market(monkeypatch, tmp_path):
    # Create a minimal config with two markets
    config = tmp_path / "market_intelligence.json"
    config.write_text(
        '{"active_market": "rancho_cucamonga", "markets": {'
        '"rancho_cucamonga": {"display_name": "RC", "city": "Rancho Cucamonga", "zip_codes": [], '
        '"neighborhoods": {"luxury": [], "mid_market": [], "entry_level": []}, '
        '"market_dynamics": {"avg_dom": 28, "median_price": 750000, '
        '"price_range_entry": [300000, 500000], "price_range_mid": [500000, 1000000], '
        '"price_range_luxury": [1000000, 5000000]}}, '
        '"phoenix": {"display_name": "Phoenix", "city": "Phoenix", "zip_codes": ["85001"], '
        '"neighborhoods": {"luxury": ["Scottsdale"], "mid_market": [], "entry_level": []}, '
        '"market_dynamics": {"avg_dom": 30, "median_price": 400000, '
        '"price_range_entry": [200000, 350000], "price_range_mid": [350000, 700000], '
        '"price_range_luxury": [700000, 3000000]}}}}'
    )
    monkeypatch.setenv("JORGE_MARKET", "phoenix")
    loader = MarketIntelligenceLoader(config_path=config)
    market = loader.get_active_market()
    assert market["display_name"] == "Phoenix"


def test_fallback_to_default_on_missing_market(monkeypatch):
    monkeypatch.setenv("JORGE_MARKET", "nonexistent_market")
    loader = MarketIntelligenceLoader()
    market = loader.get_active_market()
    assert market["display_name"] == "Rancho Cucamonga"


def test_no_bare_rancho_cucamonga_in_refactored_files():
    """Assert no bare 'Rancho Cucamonga' strings remain in MIC-refactored files."""
    project_root = Path(__file__).parent.parent

    # Only check the files we explicitly refactored in the MIC layer task
    refactored_files = [
        "services/cache_warming_service.py",
        "agents/jorge_seller_bot.py",
    ]

    violations = []
    for rel_path in refactored_files:
        py_file = project_root / rel_path
        if not py_file.exists():
            continue
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if "Rancho Cucamonga" in content:
            violations.append(rel_path)

    assert violations == [], f"Bare 'Rancho Cucamonga' strings found in MIC-refactored files: {violations}"
