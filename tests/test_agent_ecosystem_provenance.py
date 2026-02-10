from ghl_real_estate_ai.api.routes import agent_ecosystem


def test_mock_agent_data_has_provenance():
    agents = agent_ecosystem.generate_mock_agent_data()
    assert agents, "Expected mock agents"
    for agent in agents:
        assert agent.data_provenance is not None
        assert "source" in agent.data_provenance
        assert "demo_mode" in agent.data_provenance
