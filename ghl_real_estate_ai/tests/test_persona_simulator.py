"""Test suite that runs the APS Simulator as a pytest test."""

import sys
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_all_personas_pass():
    """Run all 10 APS personas and assert 10/10 pass."""
    # Ensure project root is importable
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from ghl_real_estate_ai.scripts.simulate_personas import simulate_all_personas

    result = await simulate_all_personas()
    assert result is True, "Not all personas passed -- see console output for details"
