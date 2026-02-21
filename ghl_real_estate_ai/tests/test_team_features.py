"""
Tests for Team Management Features (Phase 3)
"""

import pytest

from ghl_real_estate_ai.services.team_service import TeamManager


def test_add_agent():
    """Test adding an agent to a team."""
    manager = TeamManager("test_location_team")
    manager.add_agent(agent_id="agent_001", name="John Agent", email="john@example.com")

    agent = manager.get_agent("agent_001")
    assert agent is not None
    assert agent["name"] == "John Agent"
    assert agent["metrics"]["total_leads"] == 0


def test_assign_lead_round_robin():
    """Test round-robin lead assignment."""
    manager = TeamManager("test_location_round_robin")

    # Add two agents
    manager.add_agent("a1", "Agent 1", "a1@test.com")
    manager.add_agent("a2", "Agent 2", "a2@test.com")

    # Assign first lead
    agent1_id = manager.assign_lead("contact_1")
    assert agent1_id in ["a1", "a2"]

    # Assign second lead
    agent2_id = manager.assign_lead("contact_2")
    assert agent2_id in ["a1", "a2"]
    assert agent1_id != agent2_id

    # Assign third lead (should wrap back)
    agent3_id = manager.assign_lead("contact_3")
    assert agent3_id == agent1_id


def test_leaderboard():
    """Test leaderboard calculation."""
    import shutil
    from pathlib import Path

    # Clean up any existing test data
    test_dir = Path(__file__).parent.parent / "data" / "teams" / "test_location_leaderboard"
    if test_dir.exists():
        shutil.rmtree(test_dir)

    manager = TeamManager("test_location_leaderboard")

    manager.add_agent("a1", "Top Agent", "a1@test.com")
    manager.add_agent("a2", "New Agent", "a2@test.com")

    # Simulate performance
    manager.assign_lead("c1")  # a1 gets it
    manager.update_agent_performance("a1", conversion=True)  # 100% rate

    manager.assign_lead("c2")  # a2 gets it
    # No conversion for a2 # 0% rate

    leaderboard = manager.get_leaderboard()
    assert len(leaderboard) == 2
    assert leaderboard[0]["name"] == "Top Agent"
    assert leaderboard[0]["conversion_rate"] == 100.0
    assert leaderboard[1]["conversion_rate"] == 0.0
