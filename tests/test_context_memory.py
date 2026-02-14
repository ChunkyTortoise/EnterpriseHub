import pytest
pytestmark = pytest.mark.integration

"""Tests for hierarchical context memory (Phase 5A)."""

import pytest

from ghl_real_estate_ai.services.jorge.context_memory import (

    EntityFact,
    HierarchicalContextMemory,
)


@pytest.fixture
def memory():
    return HierarchicalContextMemory(max_short_term=5, max_medium_term=3, max_long_term=3)


class TestShortTermMemory:
    def test_add_and_retrieve_messages(self, memory):
        memory.add_message("c1", "user", "Hello")
        memory.add_message("c1", "assistant", "Hi there!")
        ctx = memory.get_context("c1")
        assert len(ctx.recent_messages) == 2
        assert ctx.recent_messages[0]["role"] == "user"
        assert ctx.recent_messages[1]["content"] == "Hi there!"

    def test_eviction_on_overflow(self, memory):
        for i in range(10):
            memory.add_message("c1", "user", f"Message {i}")
        ctx = memory.get_context("c1")
        # Should only keep max_short_term (5)
        assert len(ctx.recent_messages) == 5
        assert ctx.recent_messages[0]["content"] == "Message 5"

    def test_max_recent_limit(self, memory):
        for i in range(5):
            memory.add_message("c1", "user", f"Msg {i}")
        ctx = memory.get_context("c1", max_recent=2)
        assert len(ctx.recent_messages) == 2

    def test_clear_short_term(self, memory):
        memory.add_message("c1", "user", "Hello")
        memory.clear_short_term("c1")
        ctx = memory.get_context("c1")
        assert len(ctx.recent_messages) == 0


class TestMediumTermMemory:
    def test_add_and_retrieve_summaries(self, memory):
        memory.add_summary("c1", "Buyer interested in 3BR homes")
        ctx = memory.get_context("c1")
        assert "3BR" in ctx.conversation_summary

    def test_multiple_summaries_joined(self, memory):
        memory.add_summary("c1", "First session: explored budget")
        memory.add_summary("c1", "Second session: toured Victoria")
        ctx = memory.get_context("c1")
        assert "First session" in ctx.conversation_summary
        assert "Second session" in ctx.conversation_summary

    def test_summary_eviction(self, memory):
        for i in range(5):
            memory.add_summary("c1", f"Session {i}")
        # Only last 3 should remain (max_medium_term)
        summaries = memory._medium_term["c1"]
        assert len(summaries) == 3


class TestLongTermMemory:
    def test_set_and_retrieve_entity(self, memory):
        memory.set_entity_fact("c1", "budget", "$500K-$700K", confidence=0.9)
        ctx = memory.get_context("c1")
        assert "budget" in ctx.entity_facts
        assert ctx.entity_facts["budget"].value == "$500K-$700K"

    def test_higher_confidence_overwrites(self, memory):
        memory.set_entity_fact("c1", "budget", "$400K", confidence=0.5)
        memory.set_entity_fact("c1", "budget", "$600K", confidence=0.8)
        ctx = memory.get_context("c1")
        assert ctx.entity_facts["budget"].value == "$600K"

    def test_lower_confidence_does_not_overwrite(self, memory):
        memory.set_entity_fact("c1", "budget", "$600K", confidence=0.9)
        memory.set_entity_fact("c1", "budget", "$400K", confidence=0.3)
        ctx = memory.get_context("c1")
        assert ctx.entity_facts["budget"].value == "$600K"

    def test_entity_eviction_lowest_confidence(self, memory):
        memory.set_entity_fact("c1", "a", "val_a", confidence=0.5)
        memory.set_entity_fact("c1", "b", "val_b", confidence=0.9)
        memory.set_entity_fact("c1", "c", "val_c", confidence=0.7)
        memory.set_entity_fact("c1", "d", "val_d", confidence=0.8)
        # max_long_term=3, so lowest confidence ("a" at 0.5) should be evicted
        facts = memory._long_term["c1"]
        assert len(facts) == 3
        assert "a" not in facts


class TestClearAndStats:
    def test_clear_all(self, memory):
        memory.add_message("c1", "user", "Hello")
        memory.add_summary("c1", "Summary")
        memory.set_entity_fact("c1", "k", "v")
        memory.clear_all("c1")
        ctx = memory.get_context("c1")
        assert len(ctx.recent_messages) == 0
        assert ctx.conversation_summary == ""
        assert len(ctx.entity_facts) == 0

    def test_stats(self, memory):
        memory.add_message("c1", "user", "Hello")
        memory.add_summary("c1", "Summary")
        memory.set_entity_fact("c1", "budget", "$500K")
        stats = memory.get_stats("c1")
        assert stats == {"short_term": 1, "medium_term": 1, "long_term": 1}

    def test_stats_empty_contact(self, memory):
        stats = memory.get_stats("nonexistent")
        assert stats == {"short_term": 0, "medium_term": 0, "long_term": 0}