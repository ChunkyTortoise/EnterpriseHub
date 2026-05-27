"""Tests for PromptRegistry."""

from ghl_real_estate_ai.services.prompt_registry import REGISTRY_PATH, PromptRegistry


def test_registry_loads():
    reg = PromptRegistry()
    assert len(reg.all()) == 31


def test_get_known_entry():
    reg = PromptRegistry()
    entry = reg.get("jorge_seller_system", "1.0")
    assert entry is not None
    assert entry.model == "claude-sonnet-4-6"
    assert entry.eval_baseline_ref == "evals/baseline.json"


def test_category_filter():
    reg = PromptRegistry()
    sellers = reg.by_category("seller")
    assert len(sellers) >= 6


def test_missing_entry_returns_none():
    reg = PromptRegistry()
    assert reg.get("nonexistent", "9.9") is None


def test_all_entries_have_rationale():
    reg = PromptRegistry()
    for entry in reg.all():
        assert len(entry.rationale.strip()) > 20, f"{entry.name} rationale too short"
