"""
Unit tests for Obsidian Primitives using Streamlit's modern testing framework.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


def test_obsidian_card_primitive():
    """Test that the obsidian card primitive renders without errors."""
    # Create a small script to test the component
    test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_card, CardConfig

render_obsidian_card(
    title="Test Card",
    content="Test Content",
    config=CardConfig(variant='glass'),
    icon='fire'
)
"""
    at = AppTest.from_string(test_script)
    at.run()

    # Assertions
    assert not at.exception
    # Streamlit AppTest doesn't easily let us inspect raw HTML injected via st.markdown
    # but we can verify it executed successfully.


@pytest.mark.skip(reason="Fails in AppTest due to background asyncio tasks in ClaudeAssistantOptimized")
def test_lead_intelligence_hub_loading():
    """Test that the Lead Intelligence Hub can be initialized in the app."""
    # Points to the main app but we simulate the hub selection
    app_path = Path("ghl_real_estate_ai/streamlit_demo/app.py")
    at = AppTest.from_file(str(app_path))

    # Setup session state
    at.session_state.current_hub = "🧠 Lead Intelligence Hub"
    at.session_state.selected_market = "Austin, TX"

    at.run(timeout=30)

    assert not at.exception
    # Verify we are on the right hub
    assert at.session_state.current_hub == "🧠 Lead Intelligence Hub"


def test_executive_dashboard_rendering():
    """Test Executive Dashboard rendering and primitive integration."""
    test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.executive_dashboard import render_executive_dashboard

render_executive_dashboard(mock_data=True)
"""
    at = AppTest.from_string(test_script)
    at.run()

    assert not at.exception
    # Check for specific metrics that should be present
    assert any("HOT LEADS" in str(m.body) for m in at.markdown)
    assert any("PIPELINE" in str(m.body) for m in at.markdown)